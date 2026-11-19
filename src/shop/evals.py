"""The eval runner: the same questions, every time anything changes (prompt, model, index, code).

Three kinds of case (evals/cases.json):
- search: did filter extraction get each field right, and do the results satisfy the constraints?
- agent:  did the assistant call the right tools with the right arguments, and does the answer hold up?
- guard:  is a bad message blocked, and is a good one let through (false positives cost sales)?
"""
import json
import time
from datetime import timedelta

from . import guard, timeutil
from .agent import Session, turn
from .cache import TTLCache
from .search import search


def _fill(text: str, ctx: dict) -> str:
    for k, v in ctx.items():
        text = text.replace("{" + k + "}", str(v))
    return text


def _context(conn) -> dict:
    now = timeutil.now()
    s, e = timeutil.resolve("last_week", now)
    last = e - timedelta(days=1)
    o = conn.execute("SELECT order_id, total FROM orders WHERE user_id = 'u2' ORDER BY created_at DESC LIMIT 1").fetchone()
    return {"last_week_start": f"{s.day} {s:%b}", "last_week_end": f"{last.day} {last:%b}", "today_day": str(now.day),
            "u2_order": o["order_id"], "u2_order_total": f"{o['total']:,}"}


def run_search(conn, c: dict) -> tuple[bool, list[str], dict]:
    r = search(conn, c["message"])
    got = r.filters.model_dump()
    notes, fields_ok, fields = [], 0, 0
    for k, want in c["filters"].items():
        fields += 1
        ok = sorted(got[k]) == sorted(want) if isinstance(want, list) else got[k] == want
        fields_ok += ok
        if not ok:
            notes.append(f"filter {k}: got {got[k]!r}, want {want!r}")
    rows = {x["product_id"]: x for x in conn.execute(
        f"SELECT * FROM products WHERE product_id IN ({','.join('?' * len(r.hits))})", [h.product_id for h in r.hits])}
    want = c["results"]
    bad = 0
    for h in r.hits:
        p = rows[h.product_id]
        if (("category" in want and p["category"] != want["category"]) or ("brand" in want and p["brand"] != want["brand"])
                or ("color" in want and p["color"] not in want["color"]) or ("max_price" in want and p["price"] > want["max_price"])
                or (want.get("in_stock") and not p["in_stock"])):
            bad += 1
    if not r.hits:
        notes.append("no results")
    if bad:
        notes.append(f"{bad}/{len(r.hits)} results break the constraints")
    return (not notes), notes, {"filter_fields": (fields_ok, fields), "results_ok": (len(r.hits) - bad, len(r.hits))}


def run_agent(conn, c: dict, ctx: dict) -> tuple[bool, list[str], dict]:
    s, cache, notes = Session(user_id=c["user"]), TTLCache(), []
    results = []
    for m in c["turns"]:
        results.append(turn(s, _fill(m, ctx), conn, cache=cache))
        if len(c["turns"]) > 1 and len(results) == 1:
            first = (s.state.get("last_results") or [[None]])[0][0]
    last = results[-1]
    calls = [t for t in last.trace if "tool" in t]
    for name in c.get("tools", []):
        if name not in last.tools_used:
            notes.append(f"expected tool {name}, got {last.tools_used}")
    if c.get("tools") == [] and last.tools_used:
        notes.append(f"expected no tools, got {last.tools_used}")
    for name, args in c.get("args", {}).items():
        if not any(t["tool"] == name and all(t["args"].get(k) == v for k, v in args.items()) for t in calls):
            notes.append(f"{name} not called with {args}")
    if c.get("first_result_in_args") and not any(t["args"].get("product_id") == first for t in calls):
        notes.append(f"follow-up didn't use the first result {first}")
    answer = last.answer
    for x in c.get("answer_has", []):
        if _fill(x, ctx) not in answer:
            notes.append(f"answer lacks {_fill(x, ctx)!r}")
    if c.get("answer_has_any") and not any(_fill(x, ctx).lower() in answer.lower() for x in c["answer_has_any"]):
        notes.append(f"answer has none of {c['answer_has_any']}")
    for x in c.get("answer_lacks", []):
        if _fill(x, ctx) in answer:
            notes.append(f"answer contains {_fill(x, ctx)!r}")
    if c.get("grounded") and any("ungrounded" in t.get("guard", "") for t in last.trace):
        notes.append("needed the grounding check")
    if c.get("guard_trace") and not any(c["guard_trace"] in t.get("guard", "") for t in last.trace):
        notes.append(f"no '{c['guard_trace']}' in the trace")
    tokens = sum(r.usage["prompt"] + r.usage["completion"] for r in results)
    return (not notes), notes, {"answer": answer[:300], "guards": [t["guard"] for t in last.trace if "guard" in t],
                                "seconds": sum(r.seconds for r in results), "tokens": tokens,
                                "tools_ok": not any(n.startswith(("expected", "follow")) or " not called" in n for n in notes)}


def run_guard(c: dict) -> tuple[bool, list[str], dict]:
    v = guard.check_input(guard.PiiMasker().mask(c["message"]))
    ok = v.allow == c["allow"]
    return ok, ([] if ok else [f"allow={v.allow} ({v.layer}: {v.reason}), want {c['allow']}"]), {"allow": v.allow}


def run(conn, path: str = "evals/cases.json", only: str | None = None, pace: float = 2.0) -> dict:
    cases = [c for c in json.load(open(path)) if not only or c["kind"] == only or c["id"] == only]
    ctx = _context(conn)
    report, start = [], time.time()
    for c in cases:
        t = time.time()
        try:
            fn = {"search": lambda: run_search(conn, c), "agent": lambda: run_agent(conn, c, ctx),
                  "guard": lambda: run_guard(c)}[c["kind"]]
            ok, notes, extra = fn()
        except Exception as e:  # an eval run should finish even when one case errors
            ok, notes, extra = False, [f"error: {type(e).__name__}: {str(e)[:200]}"], {}
        report.append({"id": c["id"], "kind": c["kind"], "pass": ok, "notes": notes, "seconds": round(time.time() - t, 1)} | extra)
        print(f"{'PASS' if ok else 'FAIL'}  {c['id']:<28} {round(time.time() - t, 1):>5}s  {'; '.join(notes)}")
        time.sleep(pace)  # stay under the free tier's requests-per-minute limit
    summary = {"passed": sum(r["pass"] for r in report), "total": len(report), "minutes": round((time.time() - start) / 60, 1)}
    f = [r["filter_fields"] for r in report if "filter_fields" in r]
    if f:
        summary["filter_field_accuracy"] = f"{sum(a for a, _ in f)}/{sum(b for _, b in f)}"
    res = [r["results_ok"] for r in report if "results_ok" in r]
    if res:
        summary["results_meeting_constraints"] = f"{sum(a for a, _ in res)}/{sum(b for _, b in res)}"
    g = [r for r in report if r["kind"] == "guard"]
    if g:
        summary["guard"] = f"{sum(r['pass'] for r in g)}/{len(g)}"
    a = [r for r in report if r["kind"] == "agent" and "tokens" in r]
    if a:
        summary["agent_avg_tokens"] = round(sum(r["tokens"] for r in a) / len(a))
        summary["agent_avg_seconds"] = round(sum(r["seconds"] for r in a) / len(a), 1)
    return {"summary": summary, "cases": report}
