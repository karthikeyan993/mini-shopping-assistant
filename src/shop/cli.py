"""Command line: `shop load`, `shop search "..."`, `shop explain-sql "..."`."""
import argparse
import json
import time

from . import db, index
from .config import DB_PATH, EMBED_MODEL, EMBED_PER_MINUTE, FAST_MODEL
from .cache import TTLCache
from .search import build_where, search

LOG_PATH = "data/turns.jsonl"


def cmd_load(args):
    conn = db.connect(DB_PATH)
    t = time.time()
    counts = db.load(conn)
    print(f"Loaded {counts['products']} products and {counts['orders']} orders into {DB_PATH} ({time.time() - t:.1f}s)")
    if not args.fresh:
        n = index.import_vectors(conn)
        if n:
            print(f"Imported {n} model vectors shipped in vectors/ (no API calls; use --fresh to embed yourself)")
    if not args.no_embed:
        print(f"Embedding what is missing or changed with {EMBED_MODEL} ...")
        print(index.run(conn, batch_size=args.batch, workers=args.workers, per_minute=args.per_minute or EMBED_PER_MINUTE, limit=args.limit))


def cmd_search(args):
    conn = db.connect(DB_PATH)
    t = time.time()
    r = search(conn, args.message, k=args.k)
    ms = (time.time() - t) * 1000
    f = r.filters.model_dump(exclude_defaults=True)
    print(f"\nFilters ({FAST_MODEL}): {json.dumps(f, ensure_ascii=False)}")
    if r.relaxed:
        print(f"No exact match. Relaxed: {', '.join(r.relaxed)}")
    print(f"SQL: {r.sql}   params={r.params}")
    print(f"{r.n_candidates} candidates after filters → top {len(r.hits)} after fusion and collapsing colours\n")
    for i, h in enumerate(r.hits, 1):
        stock = "in stock" if h.in_stock else "sold out"
        print(f"{i}. {h.name:<44} ฿{h.price:>6,}  {stock:<8}  {h.banner:<11} "
              f"rrf={h.score:.4f}  keyword#{h.keyword_rank or '-'}  vector#{h.vector_rank or '-'}")
    print(f"\n{ms:.0f} ms: " + ", ".join(f"{k} {v}" for k, v in r.timings_ms.items()))


def cmd_explain_sql(args):
    """Show the query plan SQLite picks for a filter combination: which index it uses."""
    from .query import Filters
    conn = db.connect(DB_PATH)
    f = Filters.model_validate_json(args.filters_json)
    where, params = build_where(f)
    for row in conn.execute(f"EXPLAIN QUERY PLAN SELECT product_id FROM products WHERE {where}", params):
        print(row["detail"])


def _print_turn(r):
    for t in r.trace:
        if "tool" in t:
            err = f"  ERROR {t['error']}" if t.get("error") else ""
            hit = "  (cache hit)" if t.get("cache") else ""
            print(f"  · {t['tool']}({json.dumps(t['args'], ensure_ascii=False)}) {t['ms']} ms{hit}{err}")
        else:
            print(f"  · {t}")
    print(f"\nAssistant: {r.answer}")
    print(f"  [{r.seconds}s · {r.usage['prompt']} prompt + {r.usage['completion']} completion tokens · "
          f"{len(r.models)} model calls ({', '.join(dict.fromkeys(r.models))})]\n")


def cmd_ask(args):
    """One or more messages as consecutive turns of one conversation."""
    from .agent import Session, turn
    conn = db.connect(DB_PATH)
    session, cache = Session(user_id=args.user), TTLCache()
    for m in args.messages:
        print(f"You ({args.user}): {m}")
        _print_turn(turn(session, m, conn, cache=cache, log_path=LOG_PATH))


def cmd_chat(args):
    from .agent import Session, turn
    conn = db.connect(DB_PATH)
    session, cache = Session(user_id=args.user), TTLCache()
    print(f"Chatting as {args.user}. Empty line to quit.")
    while (m := input("You: ").strip()):
        _print_turn(turn(session, m, conn, cache=cache, log_path=LOG_PATH))


def cmd_eval(args):
    from . import evals
    conn = db.connect(DB_PATH)
    out = evals.run(conn, only=args.only, pace=args.pace)
    print("\n" + json.dumps(out["summary"], ensure_ascii=False))
    with open("data/eval_report.json", "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("Full report: data/eval_report.json")


def cmd_photo(args):
    from . import vision
    conn = db.connect(DB_PATH)
    attrs, r = vision.search_by_photo(conn, args.path, k=args.k)
    tokens = attrs.pop("_tokens", None)
    print(f"Read from the photo ({tokens} prompt tokens): {json.dumps(attrs, ensure_ascii=False)}")
    if r is None:
        print("Not a product photo.")
        return
    print(f"Filters: {json.dumps(r.filters.model_dump(exclude_defaults=True), ensure_ascii=False)}"
          + (f"  relaxed: {', '.join(r.relaxed)}" if r.relaxed else ""))
    for i, h in enumerate(r.hits, 1):
        print(f"{i}. {h.name:<44} ฿{h.price:>6,}  {'in stock' if h.in_stock else 'sold out'}")


def cmd_size_chart(args):
    from . import pdftable
    text = pdftable.text_layer(args.path)
    print("Text layer (pypdf), structure lost:\n  " + text.replace("\n", "\n  ")[:600])
    regex_rows = pdftable.rows_from_text(text)
    print(f"\nRegex over the text layer found {len(regex_rows)} rows")
    out = pdftable.read_with_model(args.path)
    print(f"Vision model read {len(out['rows'])} rows from the page image: {out['title']}")
    for r in out["rows"]:
        print(f"  {r['size']:<4} chest {r['chest_min_cm']:g}-{r['chest_max_cm']:g} cm  length {r['length_cm']}")
    problems = pdftable.validate(out["rows"])
    print("Validation: " + ("ok" if not problems else "; ".join(problems)))
    print(f"Regex and model agree: {regex_rows == out['rows']}")
    if args.chest:
        print(f"\nChest {args.chest} cm → size {pdftable.pick_size(out['rows'], args.chest)} (picked by code, not the model)")


def cmd_intents(args):
    from . import intents
    if args.action == "generate":
        print(intents.generate(), "messages written to", intents.DATA)
        return
    model, r = intents.train(features=args.features)
    print(f"Features: {args.features}. Trained on {r['n_train']}, tested on {r['n_test']} held-out messages. "
          f"Macro F1 {r['macro_f1']}\n")
    print(r["report"])
    short = [l[:8] for l in r["labels"]]
    print("Confusion matrix (rows = true intent, columns = predicted):\n" + " " * 9 + " ".join(f"{l:>8}" for l in short))
    for l, row in zip(short, r["confusion"]):
        print(f"{l:>8} " + " ".join(f"{v:>8}" for v in row))
    for m in args.messages or []:
        print(f"\n{m!r} → {intents.predict(model, m)}")


def main():
    p = argparse.ArgumentParser(prog="shop")
    sub = p.add_subparsers(required=True)
    a = sub.add_parser("load", help="create the demo catalog and embed it")
    a.add_argument("--no-embed", action="store_true")
    a.add_argument("--fresh", action="store_true", help="ignore the shipped vectors and embed with your own key")
    a.add_argument("--batch", type=int, default=45)
    a.add_argument("--workers", type=int, default=2)
    a.add_argument("--per-minute", type=int, default=None, help="texts per minute (default: EMBED_PER_MINUTE)")
    a.add_argument("--limit", type=int, default=None, help="embed only this many (a quick test)")
    a.set_defaults(fn=cmd_load)
    s = sub.add_parser("search", help="search the catalog with a natural-language message")
    s.add_argument("message")
    s.add_argument("-k", type=int, default=5)
    s.set_defaults(fn=cmd_search)
    e = sub.add_parser("explain-sql", help='query plan for filters, e.g. \'{"category": "running shoes", "in_stock": true}\'')
    e.add_argument("filters_json")
    e.set_defaults(fn=cmd_explain_sql)
    q = sub.add_parser("ask", help="send messages to the assistant as consecutive turns")
    q.add_argument("messages", nargs="+")
    q.add_argument("--user", default="u1", help="the logged-in customer (u1, u2, u3)")
    q.set_defaults(fn=cmd_ask)
    c = sub.add_parser("chat", help="interactive chat with the assistant")
    c.add_argument("--user", default="u1")
    c.set_defaults(fn=cmd_chat)
    v = sub.add_parser("eval", help="run evals/cases.json")
    v.add_argument("--only", help="a kind (search, agent, guard) or a case id")
    v.add_argument("--pace", type=float, default=2.0, help="seconds between cases (free-tier rate limits)")
    v.set_defaults(fn=cmd_eval)
    ph = sub.add_parser("photo", help="search the catalog with a product photo")
    ph.add_argument("path")
    ph.add_argument("-k", type=int, default=5)
    ph.set_defaults(fn=cmd_photo)
    sc = sub.add_parser("size-chart", help="read a size table from a PDF and pick a size")
    sc.add_argument("path")
    sc.add_argument("--chest", type=float)
    sc.set_defaults(fn=cmd_size_chart)
    it = sub.add_parser("intents", help="train and evaluate the intent classifier")
    it.add_argument("action", choices=["train", "generate"], nargs="?", default="train")
    it.add_argument("--features", choices=["tfidf", "embed"], default="tfidf")
    it.add_argument("messages", nargs="*", help="messages to classify after training")
    it.set_defaults(fn=cmd_intents)
    x = sub.add_parser("export-vectors", help="write model vectors to vectors/model_vectors.npz")
    x.set_defaults(fn=lambda a: print(index.export_vectors(db.connect(DB_PATH)), "vectors exported"))
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
