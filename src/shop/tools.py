"""The tools the model may call, and the code that runs them.

The model only proposes a call (a name + JSON arguments). This module validates the arguments, applies
permissions (the customer is whoever is logged in: `ctx.user_id`, never an argument), runs the query and
returns compact JSON.
"""
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Literal, Optional

from pydantic import BaseModel, Field, ValidationError

from . import catalog, timeutil
from .search import search


@dataclass
class Ctx:
    conn: object
    user_id: str                      # from the login session; the model can't change it
    now: datetime
    state: dict = field(default_factory=dict)   # conversation state: last results, product in focus
    cache: object = None              # step C: a TTL cache for search results


# ---- argument models: the JSON schema the model sees is generated from these ----

class SearchArgs(BaseModel):
    query: str = Field(description="A complete, standalone shopping request, rewritten from the conversation "
                                   "if needed, e.g. 'Nike Cloud Glide 2 running shoes in black'.")
    k: int = Field(5, ge=1, le=10, description="How many products to return.")


class ProductArgs(BaseModel):
    product_id: str = Field(description="A product_id from an earlier search result.")


class StockArgs(BaseModel):
    product_id: str = Field(description="A product_id from an earlier search result.")
    size: Optional[str] = Field(None, description="Size as listed for the product, e.g. '42' or 'M'.")
    store: Optional[Literal[tuple(catalog.STORES)]] = Field(None, description="One store, or omit for all stores.")


class OrdersArgs(BaseModel):
    period: Optional[Literal[tuple(timeutil.PERIODS)]] = Field(
        None, description="A named period; the tool works out the exact dates. Prefer this.")
    start_date: Optional[str] = Field(None, description="YYYY-MM-DD, only when the customer gave exact dates.")
    end_date: Optional[str] = Field(None, description="YYYY-MM-DD inclusive, only with start_date.")


class OrderArgs(BaseModel):
    order_id: str


# ---- implementations ----

def _product_card(r) -> dict:
    return {"product_id": r["product_id"], "name": r["name"], "price_thb": r["price"],
            "in_stock": bool(r["in_stock"]), "site": r["banner"]}


def search_products(ctx: Ctx, a: SearchArgs) -> dict:
    key = a.query.strip().lower()
    cached = ctx.cache.get(key) if ctx.cache else None
    if cached:
        result = cached | {"cache": "hit"}
    else:
        r = search(ctx.conn, a.query, k=a.k)
        rows = {x["product_id"]: x for x in ctx.conn.execute(
            f"SELECT * FROM products WHERE product_id IN ({','.join('?' * len(r.hits))})",
            [h.product_id for h in r.hits])} if r.hits else {}
        result = {"filters_understood": r.filters.model_dump(exclude_defaults=True),
                  "relaxed": r.relaxed, "results": [_product_card(rows[h.product_id]) for h in r.hits]}
        if ctx.cache:
            ctx.cache.set(key, result)
    ctx.state["last_results"] = [(p["product_id"], p["name"], p["price_thb"]) for p in result["results"]]
    return result


def get_product(ctx: Ctx, a: ProductArgs) -> dict:
    r = ctx.conn.execute("SELECT * FROM products WHERE product_id = ?", (a.product_id,)).fetchone()
    if not r:
        return {"error": f"No product {a.product_id}. Use a product_id from search results."}
    colours = [x["color"] for x in ctx.conn.execute(
        "SELECT DISTINCT color FROM products WHERE model_id = ? ORDER BY color", (r["model_id"],))]
    ctx.state["focus"] = (r["product_id"], r["name"])
    return _product_card(r) | {"brand": r["brand"], "category": r["category"], "sizes": r["sizes"].split(","),
                               "colours_available": colours, "description": r["description"]}


def check_stock(ctx: Ctx, a: StockArgs) -> dict:
    """Live stock: read at answer time, never from the search index or a cache."""
    r = ctx.conn.execute("SELECT name, sizes FROM products WHERE product_id = ?", (a.product_id,)).fetchone()
    if not r:
        return {"error": f"No product {a.product_id}."}
    if a.size and a.size not in r["sizes"].split(","):
        return {"error": f"Size {a.size} doesn't exist for this product. Sizes: {r['sizes']}."}
    q, params = "SELECT store, size, qty FROM stock WHERE product_id = ?", [a.product_id]
    if a.size:
        q += " AND size = ?"; params.append(a.size)
    if a.store:
        q += " AND store = ?"; params.append(a.store)
    rows = ctx.conn.execute(q + " ORDER BY store, size", params).fetchall()
    ctx.state["focus"] = (a.product_id, r["name"])
    return {"product": r["name"], "stock": [{"store": x["store"], "size": x["size"], "qty": x["qty"]} for x in rows
                                            if x["qty"] > 0 or a.size],
            "note": "Quantities are live." if rows else "No stock rows found."}


def get_orders(ctx: Ctx, a: OrdersArgs) -> dict:
    if a.period:
        start, end = timeutil.resolve(a.period, ctx.now)
    elif a.start_date:
        start = timeutil.parse_date(a.start_date)
        end = timeutil.parse_date(a.end_date or a.start_date) + timedelta(days=1)  # end date is inclusive
    else:
        start, end = timeutil.resolve("last_30_days", ctx.now)
    rows = ctx.conn.execute(
        "SELECT * FROM orders WHERE user_id = ? AND created_at >= ? AND created_at < ? ORDER BY created_at DESC",
        (ctx.user_id, timeutil.to_utc_iso(start), timeutil.to_utc_iso(end))).fetchall()
    return {"range": timeutil.describe(start, end) + " (Bangkok time)",
            "orders": [_order(ctx, o) for o in rows]}


def get_order(ctx: Ctx, a: OrderArgs) -> dict:
    o = ctx.conn.execute("SELECT * FROM orders WHERE order_id = ? AND user_id = ?", (a.order_id, ctx.user_id)).fetchone()
    # Same answer whether the order doesn't exist or belongs to someone else: don't confirm other people's orders.
    return _order(ctx, o) if o else {"error": "No order with that number on this account."}


def _order(ctx: Ctx, o) -> dict:
    local = datetime.fromisoformat(o["created_at"]).astimezone(timeutil.TZ)
    items = [{"name": i["name"], "size": i["size"], "qty": i["qty"], "price_thb": i["price"]} for i in ctx.conn.execute(
        "SELECT p.name, oi.size, oi.qty, oi.price FROM order_items oi JOIN products p USING (product_id)"
        " WHERE oi.order_id = ?", (o["order_id"],))]
    return {"order_id": o["order_id"], "date": f"{local:%a %d %b %Y %H:%M}", "status": o["status"],
            "total_thb": o["total"], "items": items}


# ---- registry: name → (argument model, function, description) ----

REGISTRY = {
    "search_products": (SearchArgs, search_products, "Search the catalog. Use for any request to find or compare products."),
    "get_product": (ProductArgs, get_product, "Details of one product: sizes, colours available, description."),
    "check_stock": (StockArgs, check_stock, "Live stock of a product by store and size."),
    "get_orders": (OrdersArgs, get_orders, "The logged-in customer's orders in a period."),
    "get_order": (OrderArgs, get_order, "One order of the logged-in customer, by order number."),
}


def _simplify(prop: dict) -> dict:
    """pydantic writes Optional[X] as anyOf [X, null]; write it as a nullable X, which every provider accepts."""
    prop.pop("title", None)
    if "anyOf" in prop:
        kinds = [k for k in prop.pop("anyOf") if k.get("type") != "null"]
        prop.update(kinds[0])
        prop["type"] = [prop.get("type", "string"), "null"]
    return prop


def specs() -> list[dict]:
    """Tool definitions in the OpenAI format (Gemini's compatible endpoint accepts the same)."""
    out = []
    for name, (model, _, desc) in REGISTRY.items():
        schema = model.model_json_schema()
        schema.pop("title", None)
        schema["properties"] = {k: _simplify(v) for k, v in schema.get("properties", {}).items()}
        out.append({"type": "function", "function": {"name": name, "description": desc, "parameters": schema}})
    return out


def run(ctx: Ctx, name: str, arguments: str) -> dict:
    """Validate and execute one tool call. Errors come back as data the model can act on."""
    if name not in REGISTRY:
        return {"error": f"Unknown tool {name}."}
    model, fn, _ = REGISTRY[name]
    try:
        args = model.model_validate(json.loads(arguments or "{}"))
    except (ValidationError, json.JSONDecodeError) as e:
        return {"error": f"Invalid arguments: {str(e)[:300]}"}
    return fn(ctx, args)
