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
