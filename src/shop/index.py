"""The embedding job: embed what changed, in batches, under the rate limit, safe to stop and re-run.

Three ideas that carry straight to 2 million products:
1. Embed the parent, not every variant. Colours and banners share one description, and colour is an exact filter,
   so we embed one text per model: 486 texts instead of 2,048 rows.
2. A content hash per model makes the job incremental (only changed text is re-embedded) and resumable
   (a crash loses at most the batches in flight).
3. A client-side rate limiter keeps us under the API quota instead of hammering into 429 errors.
"""
import hashlib
import os
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np

from .llm import embed

VECTORS_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "vectors", "model_vectors.npz")


def embed_text(row) -> str:
    """What the embedding sees: stable descriptive fields of the model. Never price, stock or colour:
    those change or are filters, handled exactly in SQL."""
    th = f" {row['description_th']}" if row["description_th"] else ""
    return f"{row['model_name']}. {row['brand']} {row['category']} for {row['sport']}, {row['gender']}. {row['description']}{th}"


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


class RateLimiter:
    """At most `per_minute` texts in any 60-second window, shared by all worker threads (a sliding window)."""

    def __init__(self, per_minute: int):
        self.per_minute, self.sent, self.lock = per_minute, deque(), threading.Lock()

    def acquire(self, n: int) -> None:
        while True:
            with self.lock:
                now = time.time()
                while self.sent and now - self.sent[0][0] > 60:
                    self.sent.popleft()
                used = sum(k for _, k in self.sent)
                if used + n <= self.per_minute:
                    self.sent.append((now, n))
                    return
                wait = 60 - (now - self.sent[0][0]) + 0.5
            print(f"  rate limit: {used}/{self.per_minute} texts in the last minute, waiting {wait:.0f}s")
            time.sleep(wait)


def pending(conn) -> list[tuple[str, str, str]]:
    """(model_id, text, hash) for every model whose text changed since it was embedded."""
    stored = {r["model_id"]: r["embed_hash"] for r in conn.execute("SELECT model_id, embed_hash FROM model_vectors")}
    out = []
    for row in conn.execute("SELECT * FROM products GROUP BY model_id"):
        t = embed_text(row)
        h = text_hash(t)
        if stored.get(row["model_id"]) != h:
            out.append((row["model_id"], t, h))
    return out


def run(conn, batch_size: int = 50, workers: int = 2, per_minute: int = 90, limit: int | None = None) -> dict:
    todo = pending(conn)[:limit] if limit else pending(conn)
    batches = [todo[i:i + batch_size] for i in range(0, len(todo), batch_size)]
    print(f"{len(todo)} models to embed in {len(batches)} batches of up to {batch_size}, "
          f"{workers} at a time, at most {per_minute} texts a minute")
    limiter = RateLimiter(per_minute)

    def job(b):
        limiter.acquire(len(b))
        return embed([t for _, t, _ in b])

    start, done = time.time(), 0
    # Threads, not async: the work is waiting on the network, and a pool is the simplest bounded concurrency.
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(job, b): b for b in batches}
        for fut in as_completed(futures):
            b = futures[fut]
            vecs = fut.result()
            # Writing each batch as it finishes is the checkpoint: a re-run skips models whose hash now matches.
            conn.executemany("INSERT OR REPLACE INTO model_vectors (model_id, embed_hash, embedding) VALUES (?,?,?)",
                             [(mid, h, v.astype(np.float32).tobytes()) for (mid, _, h), v in zip(b, vecs)])
            conn.commit()
            done += len(b)
            print(f"  {done}/{len(todo)} embedded")
    return {"embedded": done, "seconds": round(time.time() - start, 1)}


def export_vectors(conn, path: str = VECTORS_FILE) -> int:
    rows = conn.execute("SELECT model_id, embed_hash, embedding FROM model_vectors").fetchall()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    np.savez_compressed(path, model_id=np.array([r["model_id"] for r in rows]),
                        embed_hash=np.array([r["embed_hash"] for r in rows]),
                        vectors=np.stack([np.frombuffer(r["embedding"], dtype=np.float32) for r in rows]))
    return len(rows)


def import_vectors(conn, path: str = VECTORS_FILE) -> int:
    """Load the vectors shipped in the repo. Their hashes are checked by `pending`, so a model whose text
    changed since the export is still re-embedded."""
    if not os.path.exists(path):
        return 0
    d = np.load(path)
    conn.executemany("INSERT OR REPLACE INTO model_vectors (model_id, embed_hash, embedding) VALUES (?,?,?)",
                     [(str(m), str(h), v.astype(np.float32).tobytes())
                      for m, h, v in zip(d["model_id"], d["embed_hash"], d["vectors"])])
    conn.commit()
    return len(d["model_id"])


def load_matrix(conn, product_ids: list[str]) -> np.ndarray:
    """One vector per product id, in order: each product uses its model's vector (zeros if not embedded)."""
    model_of = {}
    for i in range(0, len(product_ids), 900):  # SQLite limits the number of ? placeholders
        chunk = product_ids[i:i + 900]
        q = f"SELECT product_id, model_id FROM products WHERE product_id IN ({','.join('?' * len(chunk))})"
        model_of.update({r["product_id"]: r["model_id"] for r in conn.execute(q, chunk)})
    vec = {r["model_id"]: np.frombuffer(r["embedding"], dtype=np.float32)
           for r in conn.execute("SELECT model_id, embedding FROM model_vectors")}
    dim = len(next(iter(vec.values()))) if vec else 1
    zero = np.zeros(dim, dtype=np.float32)
    return np.stack([vec.get(model_of.get(p), zero) for p in product_ids]) if product_ids else np.zeros((0, dim))
