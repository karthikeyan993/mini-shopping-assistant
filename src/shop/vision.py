"""Photo search, path 1 of 2: a vision model reads the photo into catalog attributes, then step A's search runs.

    photo ──(Gemini sees it as image tokens)──► {category, colours, pattern, sleeve, ...} ──► Filters ──► search

Path 2, visual similarity (embed every catalog image and the photo in one image-text space, nearest neighbours),
needs product images, which this synthetic catalog doesn't have; the guide explains it.
"""
import base64
import mimetypes

from . import catalog
from .config import FAST_MODEL, client
from .llm import with_retries
from .query import CATEGORY_NAMES, Filters
from .search import search
import json

SCHEMA = {
    "type": "object",
    "properties": {
        "is_product_photo": {"type": "boolean"},
        "category": {"type": ["string", "null"], "enum": CATEGORY_NAMES + [None]},
        "colors": {"type": "array", "items": {"type": "string", "enum": catalog.COLORS}},
        "pattern": {"type": ["string", "null"], "enum": ["plain", "striped", "checked", "printed", "colour-block", None]},
        "sleeve": {"type": ["string", "null"], "enum": ["short", "long", "sleeveless", None]},
        "details": {"type": "string"},
        "visible_text": {"type": "string"},
    },
    "required": ["is_product_photo", "category", "colors", "pattern", "sleeve", "details", "visible_text"],
}

PROMPT = """A customer of a sports store uploaded this photo. Describe the main item so we can search our catalog.
- category: the closest allowed category, or null if none fits.
- colors: the item's main colours from the allowed list, most dominant first (at most 2).
- details: a few English keywords about style and features (e.g. "collar, buttons, sporty").
- visible_text: any brand or text you can actually read on the item, else "". Don't guess brands.
- is_product_photo: false if there is no clothing, shoe or sports item in the photo."""


def _data_url(path: str) -> str:
    mime = mimetypes.guess_type(path)[0] or "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(open(path, 'rb').read()).decode()}"


def read_photo(path: str, model: str = FAST_MODEL) -> dict:
    resp = with_retries(lambda: client().chat.completions.create(
        model=model, temperature=0,
        messages=[{"role": "user", "content": [{"type": "text", "text": PROMPT},
                                               {"type": "image_url", "image_url": {"url": _data_url(path)}}]}],
        response_format={"type": "json_schema", "json_schema": {"name": "photo", "schema": SCHEMA}}))
    out = json.loads(resp.choices[0].message.content)
    out["_tokens"] = resp.usage.prompt_tokens if resp.usage else None   # an image costs tokens, like text
    return out


def to_filters(attrs: dict) -> Filters:
    """Attributes → the same Filters as a typed message. Pattern and sleeve aren't catalog columns, so they go into
    the free text and help the keyword and vector ranking instead."""
    colors = attrs.get("colors", [])
    # A striped navy-and-white shirt has two colours; filtering on "navy OR white" lets white shirts win.
    # Filter on the dominant colour only; the others go into the text, where they still help ranking.
    words = " ".join(x for x in [attrs.get("pattern"), f"{attrs['sleeve']} sleeve" if attrs.get("sleeve") else None,
                                 " ".join(colors[1:]), attrs.get("details"), attrs.get("visible_text")] if x)
    return Filters.model_validate({"category": attrs.get("category"), "colors": colors[:1], "text": words})


def search_by_photo(conn, path: str, k: int = 5):
    attrs = read_photo(path)
    if not attrs["is_product_photo"]:
        return attrs, None
    return attrs, search(conn, attrs.get("details") or "sports item", k=k, filters=to_filters(attrs))
