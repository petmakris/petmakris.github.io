import re
import glyphs

ACCENT = "#B5531F"

def test_has_the_full_set():
    assert len(glyphs.GLYPHS) >= 200

def test_every_glyph_returns_wellformed_svg():
    for key in glyphs.GLYPHS:
        svg = glyphs.render(key, ACCENT)
        assert svg.startswith("<svg"), key
        assert svg.rstrip().endswith("</svg>"), key
        assert 'viewBox="0 0 24 24"' in svg, key

def test_every_glyph_uses_the_accent():
    """Every glyph is tinted by its card — except the colour swatches, which
    are the one family whose subject IS a colour. Painting `rouge` in the
    card's accent would make the picture contradict the word, so col_* is
    exempt by design, and the exemption is spelled out here rather than
    silently skipped."""
    for key in glyphs.GLYPHS:
        if key.startswith("col_"):
            continue
        assert ACCENT in glyphs.render(key, ACCENT), key


def test_colour_swatches_paint_their_own_colour():
    """The flip side of the exemption above: a swatch must show the colour it
    names, whatever card it lands on, and must keep the grey keyline that is
    the only reason col_blanc is visible on white paper."""
    for key, col in (("col_rouge", "#D5352B"), ("col_blanc", "#FFFFFF"),
                     ("col_vert", "#3E8E41")):
        svg = glyphs.render(key, ACCENT)
        assert col in svg, key
        assert glyphs.GREY in svg, key
        assert ACCENT not in svg, key

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

def test_dir_straight_is_not_dir_up():
    """dir_straight must read as forward-along-a-path, not as an up arrow —
    check more than string inequality: dir_straight draws a receding road
    (a <path> element) that dir_up has no reason to contain."""
    straight = glyphs.render("dir_straight", ACCENT)
    up = glyphs.render("dir_up", ACCENT)
    assert straight != up
    assert "<path" in straight
    assert "<path" not in up

def test_clock_glyphs_are_all_distinct():
    """midi/minuit and deux heures/quatorze heures were once byte-identical
    — a bare analogue face can't encode AM/PM, so those pairs need a
    day/night marker on the dial itself. Guard every clock_* key at once."""
    clock_keys = [k for k in glyphs.GLYPHS if k.startswith("clock_")]
    rendered = {k: glyphs.render(k, ACCENT) for k in clock_keys}
    seen = {}
    for key, svg in rendered.items():
        assert svg not in seen.values(), f"{key} renders identically to {[k for k, v in seen.items() if v == svg]}"
        seen[key] = svg

def test_no_two_glyphs_render_identically():
    """Generalises the clock check to the whole library: two different
    vocabulary keys must never produce the same picture, or a learner has
    no way to tell them apart. A failure here names a real collision to
    fix, not a test to delete."""
    rendered = {}
    collisions = []
    for key in glyphs.GLYPHS:
        svg = glyphs.render(key, ACCENT)
        for other_key, other_svg in rendered.items():
            if svg == other_svg:
                collisions.append((key, other_key))
        rendered[key] = svg
    assert not collisions, f"identical glyphs: {collisions}"

def test_minute_expression_dials_have_separated_hands():
    """et quart / et demie / moins le quart / moins dix must show two
    clearly separate hands, not a near-coincident or near-opposite blur.
    Computed independently from hour/minute here, not from rendered pixels
    — a future edit that quietly moves one of these times back toward a
    uniform 3 o'clock must fail this before anyone looks at a rendering."""
    for key, (hour, minute) in glyphs.MINUTE_DIALS.items():
        h_ang = (hour % 12) * 30 + minute * 0.5
        m_ang = minute * 6
        sep = abs(h_ang - m_ang) % 360
        sep = min(sep, 360 - sep)
        assert 45 <= sep <= 135, f"{key}: hands only {sep}deg apart"
