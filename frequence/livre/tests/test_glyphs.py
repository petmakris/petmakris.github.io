import re
import glyphs

ACCENT = "#B5531F"

def test_has_the_full_set():
    assert len(glyphs.GLYPHS) >= 57

def test_every_glyph_returns_wellformed_svg():
    for key in glyphs.GLYPHS:
        svg = glyphs.render(key, ACCENT)
        assert svg.startswith("<svg"), key
        assert svg.rstrip().endswith("</svg>"), key
        assert 'viewBox="0 0 24 24"' in svg, key

def test_every_glyph_uses_the_accent():
    for key in glyphs.GLYPHS:
        assert ACCENT in glyphs.render(key, ACCENT), key

def test_core_prepositions_are_present():
    for key in ("on_box", "under_box", "in_box", "out_box",
                "front_box", "behind_box", "between_box"):
        assert key in glyphs.GLYPHS, key

def test_sur_and_dans_differ():
    assert glyphs.render("on_box", ACCENT) != glyphs.render("in_box", ACCENT)

def test_frequency_track_is_monotonic():
    """toujours is a full track, jamais an empty one — different SVG."""
    assert glyphs.render("freq_always", ACCENT) != glyphs.render("freq_never", ACCENT)

def test_unknown_key_returns_none():
    assert glyphs.render("no_such_glyph", ACCENT) is None
