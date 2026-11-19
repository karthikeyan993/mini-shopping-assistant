import sqlite3

from shop import db, index


def test_embedding_job_is_incremental(tmp_path, monkeypatch):
    """Only models whose text changed are embedded again: that is what makes a 2M-product sync cheap."""
    import numpy as np
    calls = []
    monkeypatch.setattr(index, "embed", lambda texts: calls.append(len(texts)) or np.ones((len(texts), 4), dtype=np.float32))
    conn = db.connect(str(tmp_path / "t.db"))
    db.load(conn)
    n_models = conn.execute("SELECT COUNT(DISTINCT model_id) FROM products").fetchone()[0]
    assert index.run(conn, per_minute=10_000)["embedded"] == n_models
    assert index.run(conn, per_minute=10_000)["embedded"] == 0          # nothing changed → nothing to do
    conn.execute("UPDATE products SET description = 'new text' WHERE model_id = (SELECT MIN(model_id) FROM products)")
    assert index.run(conn, per_minute=10_000)["embedded"] == 1          # one model changed → one embedding
