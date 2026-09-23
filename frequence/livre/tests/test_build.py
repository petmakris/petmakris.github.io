import json, os, tempfile
import build, topdf

CARD = {
    "id": "t", "tier": 1, "order": 1,
    "title_fr": "Test", "title_el": "δοκιμή", "accent": "#B5531F",
    "example": None,
    "items": [{"fr": "sur", "el": "πάνω σε", "key": "on_box"}],
}

def _fixture(d, **over):
    c = dict(CARD); c.update(over)
    json.dump(c, open(os.path.join(d, f"{c['id']}.json"), "w", encoding="utf-8"),
              ensure_ascii=False)

def test_build_writes_html_and_pdf():
    with tempfile.TemporaryDirectory() as d:
        cd = os.path.join(d, "cards"); os.makedirs(cd)
        _fixture(cd)
        h, p = build.build(cd, os.path.join(d, "out"))
        assert os.path.exists(h) and os.path.exists(p)
        assert topdf.page_count(p) >= 1

def test_html_is_self_contained():
    with tempfile.TemporaryDirectory() as d:
        cd = os.path.join(d, "cards"); os.makedirs(cd)
        _fixture(cd)
        h, _ = build.build(cd, os.path.join(d, "out"))
        src = open(h, encoding="utf-8").read()
        assert "<link" not in src
        assert "<img" not in src

def test_tier_filter_selects_cards():
    with tempfile.TemporaryDirectory() as d:
        cd = os.path.join(d, "cards"); os.makedirs(cd)
        _fixture(cd, id="a", tier=1)
        _fixture(cd, id="b", tier=3)
        h, _ = build.build(cd, os.path.join(d, "out"), tiers=(1,))
        assert open(h, encoding="utf-8").read().count('class="card"') == 1
