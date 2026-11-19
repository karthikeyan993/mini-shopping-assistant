"""Turn a shopper's message into structured filters plus a free-text part.

"In stock and blue under 3,000 baht" is a filter, not a similarity: the model extracts it, SQL applies it exactly,
and only the fuzzy remainder ("comfortable for long runs") goes to keyword and vector search.
"""
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from . import catalog
from .config import FAST_MODEL
from .llm import json_call

CATEGORY_NAMES = [c[0] for c in catalog.CATEGORIES]
SPORTS = sorted({c[1] for c in catalog.CATEGORIES})
GENDERS = ["men", "women", "unisex"]


class Filters(BaseModel):
    category: Optional[str] = None
    sport: Optional[str] = None
    colors: list[str] = Field(default_factory=list)
    brand: Optional[str] = None
    gender: Optional[str] = None
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    in_stock: bool = False
    size: Optional[str] = None
    text: str = ""  # the fuzzy part, in English, for keyword + vector search

    # Validation is the guardrail on the model's output: anything outside the catalog's values is dropped,
    # so a hallucinated category can never reach SQL.
    @field_validator("category")
    @classmethod
    def _cat(cls, v):
        return v if v in CATEGORY_NAMES else None

    @field_validator("sport")
    @classmethod
    def _sport(cls, v):
        return v if v in SPORTS else None

    @field_validator("colors")
    @classmethod
    def _colors(cls, v):
        return [c for c in v if c in catalog.COLORS]

    @field_validator("gender")
    @classmethod
    def _gender(cls, v):
        return v if v in GENDERS else None

    @field_validator("brand")
    @classmethod
    def _brand(cls, v):
        known = {b.lower(): b for b in catalog.BRAND_TH}
        return known.get((v or "").lower())


def _nullable(t: str, **extra) -> dict:
    return {"type": [t, "null"], **extra}


# Written by hand rather than generated from the pydantic model: short, explicit, and every field
# is something the provider's structured-output mode supports.
SCHEMA = {
    "type": "object",
    "properties": {
        "category": _nullable("string", enum=CATEGORY_NAMES + [None]),
        "sport": _nullable("string", enum=SPORTS + [None]),
        "colors": {"type": "array", "items": {"type": "string", "enum": catalog.COLORS}},
        "brand": _nullable("string"),
        "gender": _nullable("string", enum=GENDERS + [None]),
        "min_price": _nullable("integer"),
        "max_price": _nullable("integer"),
        "in_stock": {"type": "boolean"},
        "size": _nullable("string"),
        "text": {"type": "string"},
    },
    "required": ["category", "sport", "colors", "brand", "gender", "min_price", "max_price", "in_stock", "size", "text"],
}

SYSTEM = f"""You turn a shopper's message for a Thai sports store into search filters. The message may be Thai, English or both.
Rules:
- Fill a field only when the shopper said it. Otherwise null (or [] for colors, false for in_stock).
- category: one of the allowed values, only if it clearly matches. sport likewise.
- colors: map colour words to the allowed list (e.g. "dark blue" -> navy, "สีดำ" -> black).
- Prices are Thai baht. "under 3000" -> max_price 3000. "around 2000" -> min_price 1500, max_price 2500.
- in_stock: true only if they ask for something available now ("in stock", "มีของ", "available").
- brand: as written in English (ไนกี้ -> Nike).
- text: the remaining wishes in short English keywords (e.g. "cushioned long runs flat feet"); "" if nothing is left.
Allowed categories: {", ".join(CATEGORY_NAMES)}."""


def parse(message: str) -> Filters:
    raw = json_call(FAST_MODEL, SYSTEM, message, SCHEMA, name="filters")
    return Filters.model_validate(raw)
