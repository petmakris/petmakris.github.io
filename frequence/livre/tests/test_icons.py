import json
import os

import glyphs
import icons

ACCENT = "#B5531F"


def test_glyph_key_resolves_to_house_glyph():
    svg, kind = icons.resolve({"fr": "sur", "key": "on_box"}, ACCENT)
    assert kind == "glyph"
    assert "<svg" in svg


def test_emoji_key_resolves_to_openmoji():
    svg, kind = icons.resolve({"fr": "le chien", "key": "dog"}, ACCENT)
    assert kind == "emoji"
    assert "<svg" in svg


def test_explicit_icon_override_wins():
    """A hand-picked icon beats the automatic keyword match."""
    svg, kind = icons.resolve(
        {"fr": "manger", "key": "eat", "icon": "1F37D"}, ACCENT)
    assert kind == "emoji"
    assert "<svg" in svg


def test_blacklisted_word_gets_no_icon():
    """The joints no icon set has. A wrong icon is worse than none."""
    svg, kind = icons.resolve({"fr": "le coude", "key": "elbow"}, ACCENT)
    assert kind == "none"
    assert "dashed" in svg or "stroke-dasharray" in svg


def test_blacklist_covers_the_known_joints():
    for word in ("le coude", "le genou", "la cheville", "la joue",
                 "le front", "l'épaule", "le poignet", "la hanche", "l'ongle"):
        assert word in icons.NO_ICON, word


def test_unknown_key_gets_placeholder_not_crash():
    svg, kind = icons.resolve({"fr": "zzz", "key": "no_such_thing"}, ACCENT)
    assert kind == "none"
    assert "<svg" in svg


def test_explicit_icon_overrides_blacklist():
    """A human pick is not the automatic matcher NO_ICON exists to stop."""
    svg, kind = icons.resolve(
        {"fr": "le genou", "key": "knee", "icon": "1F9B5"}, ACCENT)
    assert kind == "emoji"
    assert "<svg" in svg


def test_blacklisted_word_without_override_still_gets_no_icon():
    """Same word, no hand-picked icon: still the placeholder, not a guess."""
    svg, kind = icons.resolve({"fr": "le genou", "key": "knee"}, ACCENT)
    assert kind == "none"
    assert "dashed" in svg or "stroke-dasharray" in svg


def test_explicit_icon_missing_flags_a_bad_hand_pick():
    """A typo'd codepoint on an explicit `icon` must be catchable, not just
    silently fall through to the automatic matcher or a placeholder."""
    assert icons.explicit_icon_missing(
        {"fr": "manger", "key": "eat", "icon": "FFFFFF"}) is True


def test_explicit_icon_missing_passes_a_real_icon():
    assert icons.explicit_icon_missing(
        {"fr": "manger", "key": "eat", "icon": "1F37D"}) is False


def test_explicit_icon_missing_is_none_with_no_explicit_icon():
    """A legitimate placeholder (no `icon` key at all) is not a strict-mode
    failure — only an explicit `icon` that was asked for and not found is."""
    assert icons.explicit_icon_missing({"fr": "le coude", "key": "elbow"}) is None
    assert icons.explicit_icon_missing({"fr": "zzz", "key": "no_such_thing"}) is None


def test_glyph_and_openmoji_keys_are_disjoint():
    """glyphs.GLYPHS and the OpenMoji index share one namespace (icons.resolve
    tries the house glyph first), so a house glyph named e.g. `book` or
    `star` would silently steal every card row that uses that keyword for
    an OpenMoji emoji. Guard the two key sets stay disjoint."""
    with open(icons.INDEX_PATH, encoding="utf-8") as f:
        openmoji_keys = set(json.load(f))
    collisions = set(glyphs.GLYPHS) & openmoji_keys
    assert not collisions, collisions
