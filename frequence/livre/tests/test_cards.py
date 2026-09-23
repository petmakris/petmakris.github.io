import json, os, tempfile
import pytest
import cards

GOOD = {
    "id": "prepositions", "tier": 1, "order": 2,
    "title_fr": "Où ? — les prépositions", "title_el": "θέσεις στον χώρο",
    "accent": "#B5531F",
    "example": "Le livre est sur la table.",
    "items": [
        {"fr": "sur", "el": "πάνω σε", "key": "on_box"},
        {"fr": "dans", "el": "μέσα σε", "key": "in_box"},
    ],
}

def _write(tmp, obj, name="c.json"):
    p = os.path.join(tmp, name)
    json.dump(obj, open(p, "w", encoding="utf-8"), ensure_ascii=False)
    return p

def test_loads_a_good_card():
    with tempfile.TemporaryDirectory() as d:
        c = cards.load_card(_write(d, GOOD))
        assert c["id"] == "prepositions"
        assert len(c["items"]) == 2
        assert c["items"][0]["fr"] == "sur"

def test_example_defaults_to_none():
    obj = dict(GOOD); obj.pop("example")
    with tempfile.TemporaryDirectory() as d:
        assert cards.load_card(_write(d, obj))["example"] is None

def test_missing_required_field_raises():
    obj = dict(GOOD); obj.pop("title_fr")
    with tempfile.TemporaryDirectory() as d:
        with pytest.raises(cards.CardError, match="title_fr"):
            cards.load_card(_write(d, obj))

def test_empty_items_raises():
    obj = dict(GOOD); obj["items"] = []
    with tempfile.TemporaryDirectory() as d:
        with pytest.raises(cards.CardError, match="items"):
            cards.load_card(_write(d, obj))

def test_item_missing_fr_raises():
    obj = json.loads(json.dumps(GOOD)); obj["items"][1].pop("fr")
    with tempfile.TemporaryDirectory() as d:
        with pytest.raises(cards.CardError, match="fr"):
            cards.load_card(_write(d, obj))

def test_bad_tier_raises():
    obj = dict(GOOD); obj["tier"] = 5
    with tempfile.TemporaryDirectory() as d:
        with pytest.raises(cards.CardError, match="tier"):
            cards.load_card(_write(d, obj))

def test_load_all_sorts_by_tier_then_order():
    a = dict(GOOD); a["id"] = "a"; a["tier"] = 2; a["order"] = 1
    b = dict(GOOD); b["id"] = "b"; b["tier"] = 1; b["order"] = 9
    c = dict(GOOD); c["id"] = "c"; c["tier"] = 1; c["order"] = 3
    with tempfile.TemporaryDirectory() as d:
        _write(d, a, "a.json"); _write(d, b, "b.json"); _write(d, c, "c.json")
        assert [x["id"] for x in cards.load_all(d)] == ["c", "b", "a"]
