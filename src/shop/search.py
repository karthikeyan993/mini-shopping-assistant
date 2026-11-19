"""Hybrid product search: SQL filters → keyword (BM25) and vector ranking → fusion → one result per model.

    message ──parse──► filters + text
    filters ──SQL WHERE──► candidates (exact: category, colour, price, in stock)
    text ──FTS5 BM25──► keyword ranks ┐
    text ──embedding──► vector ranks  ┴─ Reciprocal Rank Fusion ─► collapse colours/banners ─► top k
"""
import re
import time
from dataclasses import dataclass, field

import numpy as np

from .index import load_matrix
from .llm import embed
from .query import Filters, parse
from .thai import segment

RRF_K = 60  # the usual constant; it damps the difference between rank 1 and rank 2


@dataclass
class Hit:
    product_id: str
    model_id: str
    name: str
    price: int
    in_stock: bool
    banner: str
    score: float
    keyword_rank: int | None = None
    vector_rank: int | None = None


@dataclass
class Result:
    filters: Filters
    sql: str
    params: list
    n_candidates: int
    hits: list[Hit]
    relaxed: list[str] = field(default_factory=list)
    timings_ms: dict[str, int] = field(default_factory=dict)


def build_where(f: Filters) -> tuple[str, list]:
    """Filters → a parameterised WHERE clause. Values always go in as ? parameters, never into the SQL text."""
    clauses, params = [], []
    if f.category:
        clauses.append("category = ?"); params.append(f.category)
    if f.sport:
        clauses.append("sport = ?"); params.append(f.sport)
    if f.colors:
        clauses.append(f"color IN ({','.join('?' * len(f.colors))})"); params += f.colors
    if f.brand:
        clauses.append("brand = ?"); params.append(f.brand)
    if f.gender:
        clauses.append("gender IN (?, 'unisex')"); params.append(f.gender)
    if f.min_price is not None:
        clauses.append("price >= ?"); params.append(f.min_price)
    if f.max_price is not None:
        clauses.append("price <= ?"); params.append(f.max_price)
    if f.in_stock:
        clauses.append("in_stock = 1")
    if f.size:
        clauses.append("(',' || sizes || ',') LIKE ?"); params.append(f"%,{f.size},%")
    return (" AND ".join(clauses) or "1=1"), params


def relax(f: Filters) -> tuple[Filters, str] | None:
    """One step looser, least important filter first. Returns None when nothing is left to relax."""
    if f.max_price is not None:
        return f.model_copy(update={"max_price": int(f.max_price * 1.2)}), f"price up to {int(f.max_price * 1.2)}"
    if f.colors:
        return f.model_copy(update={"colors": []}), "any colour"
    if f.size:
        return f.model_copy(update={"size": None}), "any size"
    if f.brand:
        return f.model_copy(update={"brand": None}), "any brand"
    return None


def rrf(*rankings: list[str], k: int = RRF_K) -> dict[str, float]:
    """Reciprocal Rank Fusion: score = Σ 1/(k + rank). Only ranks matter, so BM25 and cosine scores,
    which are on different scales, can be combined without tuning weights."""
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, pid in enumerate(ranking, start=1):
            scores[pid] = scores.get(pid, 0.0) + 1.0 / (k + rank)
    return scores


def collapse(ordered: list[str], model_of: dict[str, str]) -> list[str]:
    """Keep the best-ranked row per model, so five colours of one shoe (or the same shoe on two sites)
    don't fill the whole result list."""
    seen, out = set(), []
    for pid in ordered:
        m = model_of[pid]
        if m not in seen:
            seen.add(m)
            out.append(pid)
    return out


def diversify(ordered: list[str], category_of: dict[str, str], per_category: int = 2) -> list[str]:
    """At most `per_category` results from one category, for open requests ("a gift for my dad who hikes")
    that would otherwise return five water bottles. A simple cousin of MMR."""
    count: dict[str, int] = {}
    out = []
    for pid in ordered:
        c = category_of[pid]
        if count.get(c, 0) < per_category:
            count[c] = count.get(c, 0) + 1
            out.append(pid)
    return out


def fts_query(text: str) -> str:
    """Words → an FTS5 query that matches any of them (each quoted, so user input can't inject FTS syntax)."""
    words = [w for w in re.split(r"[^\w฀-๿]+", segment(text)) if len(w) > 1]
    return " OR ".join(f'"{w}"' for w in words)


def keyword_ranking(conn, text: str, candidates: set[str]) -> list[str]:
    q = fts_query(text)
    if not q:
        return []
    rows = conn.execute("SELECT product_id FROM products_fts WHERE products_fts MATCH ? ORDER BY bm25(products_fts)", (q,))
    return [r["product_id"] for r in rows if r["product_id"] in candidates]


def vector_ranking(conn, text: str, candidates: list[str], top: int = 200) -> list[str]:
    """Exact cosine over the candidates. Fine for thousands; at millions this is an ANN index (HNSW)."""
    if not candidates:
        return []
    m = load_matrix(conn, candidates)
    q = embed([text])[0]
    sims = m @ q  # unit vectors: dot product = cosine similarity
    order = np.argsort(-sims)[:top]
    return [candidates[i] for i in order]


def search(conn, message: str, k: int = 5, filters: Filters | None = None) -> Result:
    t0 = time.perf_counter()
    f = filters or parse(message)
    t1 = time.perf_counter()
    relaxed: list[str] = []
    while True:
        where, params = build_where(f)
        rows = conn.execute(f"SELECT product_id, model_id, category FROM products WHERE {where}", params).fetchall()
        if rows:
            break
        step = relax(f)
        if step is None:
            break
        f, note = step
        relaxed.append(note)
    cand = [r["product_id"] for r in rows]
    model_of = {r["product_id"]: r["model_id"] for r in rows}
    category_of = {r["product_id"]: r["category"] for r in rows}
    text = f.text or message  # nothing fuzzy left → rank by the whole message
    t2 = time.perf_counter()
    kw = keyword_ranking(conn, text, set(cand))
    t3 = time.perf_counter()
    vec = vector_ranking(conn, text, cand)
    t4 = time.perf_counter()
    fused = rrf(kw, vec)
    ordered = sorted(fused, key=fused.get, reverse=True)
    top = collapse(ordered, model_of)
    if not f.category:  # an open request: spread the results over categories
        top = diversify(top, category_of)
    top = top[:k]
    info = {r["product_id"]: r for r in conn.execute(
        f"SELECT product_id, model_id, name, price, in_stock, banner FROM products WHERE product_id IN "
        f"({','.join('?' * len(top))})", top)} if top else {}
    kw_pos = {p: i + 1 for i, p in enumerate(kw)}
    vec_pos = {p: i + 1 for i, p in enumerate(vec)}
    hits = [Hit(p, info[p]["model_id"], info[p]["name"], info[p]["price"], bool(info[p]["in_stock"]),
                info[p]["banner"], round(fused[p], 4), kw_pos.get(p), vec_pos.get(p)) for p in top]
    ms = lambda a, b: int((b - a) * 1000)
    timings = {"filter extraction (LLM)": ms(t0, t1), "SQL filters": ms(t1, t2), "keyword BM25": ms(t2, t3),
               "query embedding + cosine": ms(t3, t4)}
    return Result(f, f"SELECT ... FROM products WHERE {where}", params, len(cand), hits, relaxed, timings)
