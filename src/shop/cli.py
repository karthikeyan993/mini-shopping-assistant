"""Command line: `shop load`, `shop search "..."`, `shop explain-sql "..."`."""
import argparse
import json
import time

from . import db, index
from .config import DB_PATH, EMBED_MODEL, FAST_MODEL
from .search import build_where, search


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
        print(index.run(conn, batch_size=args.batch, workers=args.workers, per_minute=args.per_minute, limit=args.limit))


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


def main():
    p = argparse.ArgumentParser(prog="shop")
    sub = p.add_subparsers(required=True)
    a = sub.add_parser("load", help="create the demo catalog and embed it")
    a.add_argument("--no-embed", action="store_true")
    a.add_argument("--fresh", action="store_true", help="ignore the shipped vectors and embed with your own key")
    a.add_argument("--batch", type=int, default=45)
    a.add_argument("--workers", type=int, default=2)
    a.add_argument("--per-minute", type=int, default=90, help="free tier allows 100 embedded texts a minute")
    a.add_argument("--limit", type=int, default=None, help="embed only this many (a quick test)")
    a.set_defaults(fn=cmd_load)
    s = sub.add_parser("search", help="search the catalog with a natural-language message")
    s.add_argument("message")
    s.add_argument("-k", type=int, default=5)
    s.set_defaults(fn=cmd_search)
    e = sub.add_parser("explain-sql", help='query plan for filters, e.g. \'{"category": "running shoes", "in_stock": true}\'')
    e.add_argument("filters_json")
    e.set_defaults(fn=cmd_explain_sql)
    x = sub.add_parser("export-vectors", help="write model vectors to vectors/model_vectors.npz")
    x.set_defaults(fn=lambda a: print(index.export_vectors(db.connect(DB_PATH)), "vectors exported"))
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
