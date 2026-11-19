"""Step D, offline: PDF table checks, size picking, photo attributes → filters, the classifier on committed data."""
from shop import intents, pdftable, vision

ROWS = [{"size": "S", "chest_min_cm": 88, "chest_max_cm": 96, "length_cm": 68},
        {"size": "M", "chest_min_cm": 96, "chest_max_cm": 104, "length_cm": 70},
        {"size": "L", "chest_min_cm": 104, "chest_max_cm": 112, "length_cm": 72}]


def test_pick_size_takes_the_larger_size_on_a_boundary():
    assert pdftable.pick_size(ROWS, 100) == "M"
    assert pdftable.pick_size(ROWS, 104) == "L"
    assert pdftable.pick_size(ROWS, 130) == "none"


def test_validate_catches_misread_digits():
    bad = [dict(ROWS[0]), dict(ROWS[1], chest_min_cm=196)]   # "96" misread as "196"
    assert pdftable.validate(bad)


def test_text_layer_regex_on_the_sample_pdf():
    rows = pdftable.rows_from_text(pdftable.text_layer("samples/size_chart.pdf"))
    assert [r["size"] for r in rows] == ["XS", "S", "M", "L", "XL", "XXL"] and not pdftable.validate(rows)


def test_photo_attributes_filter_on_the_dominant_colour_only():
    f = vision.to_filters({"category": "polo shirt", "colors": ["navy", "white"], "pattern": "striped",
                           "sleeve": "short", "details": "collar", "visible_text": ""})
    assert f.category == "polo shirt" and f.colors == ["navy"] and "white" in f.text and "striped" in f.text


def test_classifier_beats_chance_on_held_out_data():
    _, r = intents.train(features="tfidf")
    assert r["n_test"] >= 60 and r["macro_f1"] > 0.5   # chance with 9 balanced classes is about 0.11
