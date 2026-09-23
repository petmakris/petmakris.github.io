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


def test_gender_comes_from_the_article_when_the_article_shows_it():
    assert render.gender({"fr": "le billet"}) == "m"
    assert render.gender({"fr": "la gare"}) == "f"


def test_articles_that_hide_the_gender_give_no_pill_on_their_own():
    """`l'` elides it, `les` pluralises it away, and `un kilo` is never split
    off at all — none of the three can be guessed from the string."""
    for fr in ("l'épaule", "les CFF", "un kilo"):
        assert render.gender({"fr": fr}) == ""


def test_explicit_gender_wins_and_an_empty_one_opts_out():
    assert render.gender({"fr": "l'épaule", "g": "f"}) == "f"
    assert render.gender({"fr": "l'ongle", "g": "m"}) == "m"
    # «un Grec, une Grecque» teaches both genders at once, so it wears no
    # pill — and says so in the data rather than in a renderer special case.
    assert render.gender({"fr": "un Grec, une Grecque", "g": ""}) == ""
    # A stray value is not a pill class we have a colour for.
    assert render.gender({"fr": "le truc", "g": "n"}) == ""


def test_the_french_term_is_one_pilled_span():
    html = render.row_html({"fr": "la gare", "el": "ο σταθμός", "key": "station"},
                           ACCENT)
    assert '<span class="fr f">' in html
    assert '<span class="art la">la</span> <b>gare</b></span>' in html


def test_a_row_with_no_gender_still_gets_the_span_without_a_pill_class():
    """The span is unconditional so every French term sits on the same
    optical left edge, pill or no pill."""
    html = render.row_html({"fr": "marcher", "el": "περπατώ", "key": "walk"},
                           ACCENT)
    assert '<span class="fr">' in html


def test_elision_leaves_no_space_but_a_full_article_keeps_one():
    """French elides «l'» precisely so there is no gap. The flex gap that
    correctly separated «le» from «billet» was printing «l' épaule»."""
    elided = render.row_html({"fr": "l'épaule", "el": "ο ώμος", "g": "f",
                              "key": "body_shoulder"}, ACCENT)
    assert ">l&#x27;</span><b>épaule</b>" in elided
    full = render.row_html({"fr": "le billet", "el": "το εισιτήριο",
                            "key": "ticket"}, ACCENT)
    assert ">le</span> <b>billet</b>" in full
