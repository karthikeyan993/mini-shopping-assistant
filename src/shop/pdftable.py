"""Reading a table in a PDF: a size chart into rows, then code (not the model) picks the size.

Two ways to read it, compared side by side:
1. The text layer (pypdf): fast, free, exact characters, but the table structure is gone.
2. A vision model on the page: sees the layout, returns rows in a schema. Can misread digits, so we validate.
"""
import base64
import json
import re

from pypdf import PdfReader

from .config import FAST_MODEL, client
from .llm import with_retries

SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "rows": {"type": "array", "items": {
            "type": "object",
            "properties": {"size": {"type": "string"}, "chest_min_cm": {"type": "number"},
                           "chest_max_cm": {"type": "number"}, "length_cm": {"type": ["number", "null"]}},
            "required": ["size", "chest_min_cm", "chest_max_cm", "length_cm"]}},
    },
    "required": ["title", "rows"],
}

PROMPT = "Extract the size table from this document. One row per size, numbers in centimetres, ranges split into min and max."


def text_layer(path: str) -> str:
    return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)


def page_images(path: str, scale: float = 2.0) -> list[str]:
    """Render each page to a PNG data URL. Gemini's native API accepts a PDF and does this itself (each page
    becomes an image plus its text); the OpenAI-compatible endpoint rejected a PDF part with a 400, so we do it."""
    import io

    import pypdfium2 as pdfium
    urls = []
    for page in pdfium.PdfDocument(path):
        buf = io.BytesIO()
        page.render(scale=scale).to_pil().save(buf, format="PNG")
        urls.append("data:image/png;base64," + base64.b64encode(buf.getvalue()).decode())
    return urls


def read_with_model(path: str, model: str = FAST_MODEL) -> dict:
    """Show the model the page images (and the text layer, as Gemini does) and ask for rows in a schema."""
    content = [{"type": "text", "text": PROMPT + "\n\nText layer of the document:\n" + text_layer(path)}]
    content += [{"type": "image_url", "image_url": {"url": u}} for u in page_images(path)]
    resp = with_retries(lambda: client().chat.completions.create(
        model=model, temperature=0,
        messages=[{"role": "user", "content": content}],
        response_format={"type": "json_schema", "json_schema": {"name": "size_table", "schema": SCHEMA}}))
    return json.loads(resp.choices[0].message.content)


def validate(rows: list[dict]) -> list[str]:
    """Checks a human would do at a glance: ranges are ranges, sizes go up, numbers are plausible for a chest."""
    problems = []
    for r in rows:
        if not (50 <= r["chest_min_cm"] < r["chest_max_cm"] <= 180):
            problems.append(f"{r['size']}: implausible chest range {r['chest_min_cm']}-{r['chest_max_cm']}")
    for a, b in zip(rows, rows[1:]):
        if b["chest_min_cm"] < a["chest_min_cm"]:
            problems.append(f"{b['size']} starts below {a['size']}")
    return problems


def pick_size(rows: list[dict], chest_cm: float) -> str:
    """Deterministic: the first size whose range contains the measurement. On a boundary the larger size wins,
    as the chart's note says ("between sizes? choose the larger")."""
    fits = [r["size"] for r in rows if r["chest_min_cm"] <= chest_cm <= r["chest_max_cm"]]
    if not fits:
        return "none" if chest_cm > rows[-1]["chest_max_cm"] or chest_cm < rows[0]["chest_min_cm"] else rows[-1]["size"]
    return fits[-1]


def rows_from_text(text: str) -> list[dict]:
    """The no-model path for a simple digital PDF: a regex over the text layer. Works here; breaks on the next
    supplier's layout. That brittleness is why teams reach for layout-aware parsers or a vision model."""
    rows = []
    for size, lo, hi, length in re.findall(r"\b(XXS|XS|S|M|L|XL|XXL)\s+(\d+)-(\d+)\s+(\d+)", text):
        rows.append({"size": size, "chest_min_cm": float(lo), "chest_max_cm": float(hi), "length_cm": float(length)})
    return rows
