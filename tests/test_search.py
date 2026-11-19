"""Tests that need no network: the deterministic parts of search."""
from shop import catalog
from shop.query import Filters
from shop.search import build_where, collapse, diversify, fts_query, relax, rrf


def test_build_where_uses_parameters_not_string_formatting():
    where, params = build_where(Filters(category="running shoes", colors=["blue", "navy"], max_price=3000, in_stock=True))
    assert where == "category = ? AND color IN (?,?) AND price <= ? AND in_stock = 1"
    assert params == ["running shoes", "blue", "navy", 3000]


def test_no_filters_matches_everything():
    assert build_where(Filters()) == ("1=1", [])


def test_validators_drop_values_outside_the_catalog():
    f = Filters.model_validate({"category": "spaceships", "colors": ["blue", "ultraviolet"], "brand": "nike"})
    assert f.category is None and f.colors == ["blue"] and f.brand == "Nike"


def test_relax_order_price_then_colour():
    f = Filters(colors=["black"], max_price=1000)
    f1, note1 = relax(f)
    assert f1.max_price == 1200 and note1 == "price up to 1200"
    f2, note2 = relax(f1.model_copy(update={"max_price": None}))
    assert f2.colors == [] and note2 == "any colour"
    assert relax(Filters()) is None


def test_rrf_rewards_agreement_between_rankings():
    s = rrf(["a", "b", "c"], ["b", "a", "d"])
    assert max(s, key=s.get) in ("a", "b")
    assert s["a"] == s["b"] > s["c"] > 0 and s["d"] > 0


def test_collapse_keeps_best_row_per_model():
    model_of = {"SS-1-BLUE": "1", "SS-1-RED": "1", "CE-1-BLUE": "1", "SS-2-BLUE": "2"}
    assert collapse(["SS-1-BLUE", "SS-1-RED", "SS-2-BLUE", "CE-1-BLUE"], model_of) == ["SS-1-BLUE", "SS-2-BLUE"]


def test_diversify_caps_each_category():
    cat = {"a": "bottle", "b": "bottle", "c": "bottle", "d": "socks"}
    assert diversify(["a", "b", "c", "d"], cat, per_category=2) == ["a", "b", "d"]


def test_fts_query_quotes_words_so_user_input_cannot_inject_syntax():
    assert fts_query('blue OR "x" NEAR shoes') == '"blue" OR "or" OR "near" OR "shoes"'


def test_thai_is_segmented_into_words():
    assert fts_query("รองเท้าวิ่งสีน้ำเงิน") == '"รองเท้าวิ่ง" OR "สีน้ำเงิน"'


def test_catalog_is_deterministic_and_has_cross_banner_duplicates():
    a, b = catalog.products(), catalog.products()
    assert a == b and len(a) > 1500
    assert len({p["product_id"] for p in a}) == len(a)
    banners_per_model_colour = {}
    for p in a:
        banners_per_model_colour.setdefault((p["model_id"], p["color"]), set()).add(p["banner"])
    assert any(len(v) == 2 for v in banners_per_model_colour.values())
