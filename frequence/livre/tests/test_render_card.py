import render

CARD = {
    "id": "prep", "tier": 1, "order": 1,
    "title_fr": "Où ? — les prépositions", "title_el": "θέσεις στον χώρο",
    "accent": "#B5531F", "example": "Le livre est **sur** la table.",
    "items": [{"fr": "sur", "el": "πάνω σε", "key": "on_box"},
              {"fr": "dans", "el": "μέσα σε", "key": "in_box"}],
}

def test_card_has_a_rail_with_both_titles():
    h = render.card_html(CARD)
    assert "Où ? — les prépositions" in h
    assert "θέσεις στον χώρο" in h

def test_card_shows_the_item_count():
    assert ">2<" in render.card_html(CARD)

def test_card_uses_its_accent():
    assert "#B5531F" in render.card_html(CARD)

def test_card_renders_every_item():
    h = render.card_html(CARD)
    assert h.count('class="wd"') == 2

def test_example_is_rendered_with_bold_markers_expanded():
    h = render.card_html(CARD)
    assert "<strong>sur</strong>" in h
    assert "**" not in h

def test_card_without_example_omits_the_footer():
    c = dict(CARD); c["example"] = None
    assert 'class="ex"' not in render.card_html(c)

def test_small_group_gets_two_columns():
    c = dict(CARD)
    c["items"] = [{"fr": f"m{i}", "el": None, "key": "x"} for i in range(5)]
    assert "cols-2" in render.card_html(c)

def test_large_group_gets_three_columns():
    c = dict(CARD)
    c["items"] = [{"fr": f"m{i}", "el": None, "key": "x"} for i in range(18)]
    assert "cols-3" in render.card_html(c)

def test_document_inlines_the_font_and_the_stylesheet():
    doc = render.document_html([CARD], "Vocabulaire illustré")
    assert "@font-face" in doc
    assert "base64," in doc
    assert "<link" not in doc          # self-contained: nothing external

def test_document_sets_lang_and_charset():
    doc = render.document_html([CARD], "T")
    assert 'charset="utf-8"' in doc
    assert 'lang="fr"' in doc

def test_elided_article_is_not_shrunk_by_the_greek_gloss_class():
    # class="art elid" must not collide with the .el (Greek gloss) selector,
    # which would apply font-size: 11pt and shrink l' relative to le/la.
    c = dict(CARD)
    c["items"] = [
        {"fr": "l'œil", "el": None, "key": "eye"},
        {"fr": "le nez", "el": None, "key": "nose"},
    ]
    h = render.card_html(c)
    assert 'class="art elid"' in h

def test_stylesheet_colours_elid_not_the_greek_gloss_size():
    css = open(render.__file__.replace("render.py", "style.css"), encoding="utf-8").read()
    assert ".art.elid" in css
    assert ".art.el," not in css  # old, colliding selector must be gone

# The six design values below were settled by the owner from printed output.
# They must never drift silently; the spacing/padding/margin numbers around
# them are deliberately NOT pinned here, since those stay free to tune for
# density.

def _css():
    return open(render.__file__.replace("render.py", "style.css"), encoding="utf-8").read()

def test_card_heading_is_full_width_not_a_side_rail():
    """The heading sits in a bar above the content. An earlier design put it in
    an 18% left rail, which spent a fifth of every page on two words; the owner
    asked for it gone. Guard against it coming back."""
    css = _css()
    assert "18% 1fr" not in css
    assert "grid-template-columns: 18%" not in css

def test_icons_are_26px():
    css = _css()
    assert "width: 26px; height: 26px; flex: 0 0 26px;" in css

def test_french_is_14pt_bold():
    css = _css()
    assert "font-size: 14pt; font-weight: 700;" in css

def test_greek_is_11pt():
    assert "font-size: 11pt;" in _css()

def test_card_never_splits_across_a_page():
    assert "break-inside: avoid;" in _css()
