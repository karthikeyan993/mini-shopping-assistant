"""An intent classifier: route a message without an LLM call.

The ladder (guide §7): LLM few-shot → embeddings + logistic regression → fine-tuned small encoder → small LLM.
This is the cheapest useful rung below embeddings: character n-gram TF-IDF + logistic regression. Character n-grams
work for Thai without word segmentation, it trains in about a second on a laptop, and a prediction costs nothing.
"""
import json
import random
from collections import Counter
from pathlib import Path

from .config import FAST_MODEL
from .llm import json_call

DATA = Path(__file__).resolve().parents[2] / "evals" / "intents.jsonl"

INTENTS = {
    "product_search": "looking for a product to buy (type, brand, colour, budget, sport)",
    "product_question": "a question about a specific product (material, fit, features, comparison)",
    "order_status": "where is my order, delivery date, order history",
    "return_refund": "returns, exchanges, refunds, wrong or damaged item",
    "store_stock": "is something available in a store or size right now, store opening hours or location",
    "promotion": "discounts, promo codes, sales, member points",
    "human_agent": "wants to talk to a person or complains strongly",
    "chitchat": "greetings, thanks, small talk",
    "out_of_scope": "anything unrelated to shopping at a sports store (coding, politics, homework, medical advice)",
}


def generate(per_intent: int = 36, seed: int = 1) -> int:
    """One-time dataset generation with Gemini (distillation-style labels). The output is committed, and in real
    work a person checks it: generated data is a starting point, not ground truth."""
    schema = {"type": "object", "properties": {"messages": {"type": "array", "items": {"type": "string"}}},
              "required": ["messages"]}
    rows = []
    for intent, desc in INTENTS.items():
        out = json_call(FAST_MODEL, "You write realistic customer chat messages for a Thai sports retailer.",
                        f"Write {per_intent} different messages whose intent is '{intent}': {desc}. "
                        "Mix: half English, a third Thai, the rest Thai-English mixed. Vary length and tone; "
                        "include a few typos and very short ones. Return JSON {\"messages\": [...]}.",
                        schema, name="messages")
        rows += [{"text": m.strip(), "intent": intent} for m in dict.fromkeys(out["messages"]) if m.strip()]
    random.Random(seed).shuffle(rows)
    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
    return len(rows)


def load() -> list[dict]:
    return [json.loads(line) for line in DATA.read_text().splitlines() if line.strip()]


VECTORS = DATA.with_name("intents_vectors.npz")


class Embedder:
    """sklearn-style transformer: text → Gemini embedding. Vectors for the dataset are cached in the repo, so
    re-training costs no API calls; new texts (predictions) are embedded live."""

    def __init__(self):
        import numpy as np
        self.np, self.cache = np, {}
        if VECTORS.exists():
            d = np.load(VECTORS)
            self.cache = dict(zip(d["text"].tolist(), d["vectors"]))

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        from .index import RateLimiter
        from .llm import embed
        missing = [x for x in dict.fromkeys(X) if x not in self.cache]
        from .config import EMBED_PER_MINUTE
        limiter = RateLimiter(EMBED_PER_MINUTE)
        for i in range(0, len(missing), 45):
            batch = missing[i:i + 45]
            limiter.acquire(len(batch))
            self.cache.update(zip(batch, embed(batch)))
            self.save()  # checkpoint after every batch: a quota error loses nothing already embedded
            print(f"  embedded {min(i + 45, len(missing))}/{len(missing)}")
        return self.np.stack([self.cache[x] for x in X])

    def save(self):
        texts = list(self.cache)
        self.np.savez_compressed(VECTORS, text=self.np.array(texts), vectors=self.np.stack([self.cache[t] for t in texts]))


def train(rows: list[dict] | None = None, seed: int = 0, features: str = "tfidf"):
    """Stratified 80/20 split, fit, and a report on the held-out 20%.
    features="tfidf": character n-grams, no API calls. features="embed": Gemini embeddings (meaning, not spelling)."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import classification_report, confusion_matrix, f1_score
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import make_pipeline

    rows = rows or load()
    X, y = [r["text"] for r in rows], [r["intent"] for r in rows]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=seed)
    if features == "embed":
        emb = Embedder()
        emb.transform(X)          # embed the whole dataset once; cached in evals/intents_vectors.npz
        model = make_pipeline(emb, LogisticRegression(max_iter=2000, class_weight="balanced", C=10.0))
    else:
        model = make_pipeline(
            TfidfVectorizer(analyzer="char_wb", ngram_range=(1, 4), sublinear_tf=True, min_df=1),
            LogisticRegression(max_iter=2000, class_weight="balanced", C=5.0),
        )
    model.fit(Xtr, ytr)
    pred = model.predict(Xte)
    labels = list(INTENTS)
    return model, {
        "n_train": len(Xtr), "n_test": len(Xte), "counts": dict(Counter(y)),
        "macro_f1": round(f1_score(yte, pred, average="macro"), 3),
        "report": classification_report(yte, pred, labels=labels, zero_division=0),
        "confusion": confusion_matrix(yte, pred, labels=labels).tolist(), "labels": labels,
        "errors": [(x, t, p) for x, t, p in zip(Xte, yte, pred) if t != p],
    }


def predict(model, text: str, threshold: float = 0.45) -> tuple[str, float]:
    """Label + confidence. Below the threshold the router should not trust it: ask the LLM or the customer."""
    proba = model.predict_proba([text])[0]
    i = proba.argmax()
    label = model.classes_[i]
    return (label if proba[i] >= threshold else "unsure"), round(float(proba[i]), 2)
