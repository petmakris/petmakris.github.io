import greek

def test_row_with_no_icon_keeps_greek():
    """An empty gutter is exactly where the Greek is needed most."""
    assert greek.keeps_greek("le coude", "none") is True

def test_concrete_noun_with_emoji_drops_greek():
    assert greek.keeps_greek("le chien", "emoji") is False
    assert greek.keeps_greek("la pluie", "emoji") is False

def test_schematic_glyph_word_keeps_greek():
    """A house glyph is a diagram, not a depiction — it needs a word."""
    assert greek.keeps_greek("sur", "glyph") is True
    assert greek.keeps_greek("au-dessus", "glyph") is True

def test_near_synonyms_keep_greek_even_with_an_icon():
    """loin and là-bas cannot be separated by any picture."""
    assert greek.keeps_greek("loin", "glyph") is True
    assert greek.keeps_greek("là-bas", "glyph") is True

def test_the_documented_collapsing_pairs_are_listed():
    for w in ("devant", "derrière", "au-dessus", "au-dessous",
              "sur", "contre", "loin", "là-bas", "près"):
        assert w in greek.SCHEMATIC or w in greek.NEAR_SYNONYM, w

def test_overall_rate_is_about_a_fifth():
    """The spec measured 19% across the 437-item vocabulary. Guard the order
    of magnitude so a careless edit to SCHEMATIC cannot silently restore
    Greek on every row."""
    sample = ([("le chien", "emoji")] * 80
              + [("sur", "glyph")] * 15
              + [("le coude", "none")] * 5)
    kept = sum(1 for fr, k in sample if greek.keeps_greek(fr, k))
    assert 10 <= kept <= 30
