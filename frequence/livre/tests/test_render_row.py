import render

ACCENT = "#B5531F"

def test_splits_masculine_article():
    assert render.split_article("le bras") == ("le", "bras")

def test_splits_feminine_article():
    assert render.split_article("la main") == ("la", "main")

def test_splits_elided_article():
    assert render.split_article("l'œil") == ("l'", "œil")

def test_splits_plural_article():
    assert render.split_article("les yeux") == ("les", "yeux")

def test_no_article_returns_empty():
    assert render.split_article("sur") == ("", "sur")

def test_multiword_noun_keeps_its_tail():
    assert render.split_article("la salle de bain") == ("la", "salle de bain")

def test_row_colours_the_article_not_the_noun():
    html = render.row_html({"fr": "la main", "el": "το χέρι", "key": "hand"}, ACCENT)
    assert 'class="art la"' in html
    # The noun must be a bare <b> with no class of its own, and not wrapped
    # in any extra span carrying a gender class — this exact substring fails
    # if either happens.
    assert "<b>main</b>" in html

def test_row_elided_article_gets_its_own_class():
    html = render.row_html({"fr": "l'œil", "el": "το μάτι", "key": "eye"}, ACCENT)
    assert 'class="art elid"' in html
    assert 'class="art el"' not in html

def test_every_gloss_prints_however_good_the_icon():
    """No row hides its Greek. The book was briefly built around a "cover
    test" — drop the gloss when the icon alone recovers the word — and it
    left a column where some rows were translated and some were not, which
    reads as an unfinished book rather than an economical one. A gloss that
    earns nothing is a gloss to rewrite, not one to hide."""
    html = render.row_html({"fr": "le chien", "el": "ο σκύλος", "key": "dog"}, ACCENT)
    assert "ο σκύλος" in html


def test_a_row_with_no_gloss_renders_no_empty_span():
    for el in (None, "", "   "):
        html = render.row_html({"fr": "le truc", "el": el, "key": "nope"}, ACCENT)
        assert 'class="el"' not in html

def test_row_with_no_icon_prints_greek():
    html = render.row_html({"fr": "le coude", "el": "ο αγκώνας", "key": "elbow"}, ACCENT)
    assert "ο αγκώνας" in html

def test_schematic_row_prints_greek():
    html = render.row_html({"fr": "sur", "el": "πάνω σε", "key": "on_box"}, ACCENT)
    assert "πάνω σε" in html

def test_row_with_no_icon_has_empty_gutter_not_dashed_placeholder():
    """A row with no icon at all gets an empty gutter — the 26px column
    stays reserved for alignment, but nothing is drawn in it. The dashed
    placeholder circle reads as a rendering failure, not a deliberate gap."""
    html = render.row_html({"fr": "le coude", "el": "ο αγκώνας", "key": "elbow"}, ACCENT)
    assert '<span class="ic"></span>' in html
    assert "dasharray" not in html
