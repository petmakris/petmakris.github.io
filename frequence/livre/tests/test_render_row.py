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
    assert "<b>main</b>" in html or ">main<" in html

def test_row_with_emoji_omits_greek():
    html = render.row_html({"fr": "le chien", "el": "ο σκύλος", "key": "dog"}, ACCENT)
    assert "ο σκύλος" not in html

def test_row_with_no_icon_prints_greek():
    html = render.row_html({"fr": "le coude", "el": "ο αγκώνας", "key": "elbow"}, ACCENT)
    assert "ο αγκώνας" in html

def test_schematic_row_prints_greek():
    html = render.row_html({"fr": "sur", "el": "πάνω σε", "key": "on_box"}, ACCENT)
    assert "πάνω σε" in html
