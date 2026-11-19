"""SQLite storage: products with a precomputed in-stock flag, live stock per store, orders, and an FTS5 keyword index.

Why SQLite for a learning build: zero setup, real SQL indexes, and FTS5 gives BM25 keyword ranking. The production
version of the same design is PostgreSQL + pgvector (README, "Production version").
"""
import os
import sqlite3

from . import catalog
from .thai import segment

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    product_id TEXT PRIMARY KEY, model_id TEXT NOT NULL, model_name TEXT, banner TEXT, name TEXT, brand TEXT,
    category TEXT, category_th TEXT, sport TEXT, gender TEXT, color TEXT, price INTEGER,
    sizes TEXT, description TEXT, description_th TEXT,
    in_stock INTEGER NOT NULL DEFAULT 0       -- flag kept up to date from the stock table (the "flagging" idea)
);
-- One vector per model (the parent), shared by its colours and banners. The hash of the embedded text
-- decides whether a model needs re-embedding.
CREATE TABLE IF NOT EXISTS model_vectors (model_id TEXT PRIMARY KEY, embed_hash TEXT NOT NULL, embedding BLOB NOT NULL);
-- Composite index for the commonest filter combination, then single-column ones.
CREATE INDEX IF NOT EXISTS idx_cat_stock_price ON products(category, in_stock, price);
CREATE INDEX IF NOT EXISTS idx_color ON products(color);
CREATE INDEX IF NOT EXISTS idx_brand ON products(brand);
CREATE INDEX IF NOT EXISTS idx_model ON products(model_id);

CREATE TABLE IF NOT EXISTS stock (
    product_id TEXT, size TEXT, store TEXT, qty INTEGER, PRIMARY KEY (product_id, size, store)
);
CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, created_at TEXT NOT NULL, status TEXT, total INTEGER
);
CREATE INDEX IF NOT EXISTS idx_orders_user_time ON orders(user_id, created_at);
CREATE TABLE IF NOT EXISTS order_items (order_id TEXT, product_id TEXT, size TEXT, qty INTEGER, price INTEGER);

-- Keyword index. Thai text is segmented into words before it goes in (thai.segment).
CREATE VIRTUAL TABLE IF NOT EXISTS products_fts USING fts5(product_id UNINDEXED, body, tokenize='unicode61');
"""


def connect(path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def keyword_text(p: dict) -> str:
    """What the keyword index sees: names, attributes, both languages, Thai brand spellings."""
    parts = [p["name"], p["brand"], catalog.BRAND_TH.get(p["brand"], ""), p["category"], p["category_th"],
             p["sport"], p["gender"], p["color"], catalog.COLOR_TH.get(p["color"], ""), p["description"],
             p["description_th"]]
    return segment(" ".join(x for x in parts if x))


def load(conn: sqlite3.Connection) -> dict:
    """(Re)create the demo data. Vectors live in model_vectors and survive a reload."""
    rows = catalog.products()
    conn.executescript("DELETE FROM products; DELETE FROM stock; DELETE FROM orders; DELETE FROM order_items;"
                       "DELETE FROM products_fts;")
    conn.executemany(
        "INSERT INTO products (product_id, model_id, model_name, banner, name, brand, category, category_th, sport,"
        " gender, color, price, sizes, description, description_th) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [(p["product_id"], p["model_id"], p["model_name"], p["banner"], p["name"], p["brand"], p["category"],
          p["category_th"], p["sport"], p["gender"], p["color"], p["price"], ",".join(p["sizes"]), p["description"],
          p["description_th"]) for p in rows])
    conn.executemany("INSERT INTO stock VALUES (?,?,?,?)", catalog.stock(rows))
    refresh_stock_flags(conn)
    o, items = catalog.orders(rows)
    conn.executemany("INSERT INTO orders VALUES (?,?,?,?,?)", o)
    conn.executemany("INSERT INTO order_items VALUES (?,?,?,?,?)", items)
    conn.executemany("INSERT INTO products_fts (product_id, body) VALUES (?, ?)",
                     [(p["product_id"], keyword_text(p)) for p in rows])
    conn.commit()
    return {"products": len(rows), "orders": len(o)}


def refresh_stock_flags(conn: sqlite3.Connection) -> None:
    """Recompute products.in_stock from live stock. In production a stock-change event updates one row's flag."""
    conn.execute("UPDATE products SET in_stock = EXISTS (SELECT 1 FROM stock s WHERE s.product_id = products.product_id"
                 " AND s.qty > 0)")
