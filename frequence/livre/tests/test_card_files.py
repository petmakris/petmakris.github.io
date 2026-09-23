import glob, os
import cards, icons, render

HERE = os.path.dirname(os.path.abspath(__file__))
CARDS = os.path.join(HERE, "..", "data", "cards")

def test_every_card_file_is_valid():
    files = glob.glob(os.path.join(CARDS, "*.json"))
    assert files, "no card files yet"
    for f in files:
        cards.load_card(f)

def test_every_card_renders():
    for c in cards.load_all(CARDS):
        assert render.card_html(c)

def test_no_card_has_duplicate_french():
    for c in cards.load_all(CARDS):
        words = [i["fr"] for i in c["items"]]
        assert len(words) == len(set(words)), f"{c['id']}: duplicate entries"

def test_clock_card_exists_and_covers_the_quarters():
    c = cards.load_card(os.path.join(CARDS, "03-heure.json"))
    words = " ".join(i["fr"] for i in c["items"])
    for needed in ("et quart", "et demie", "moins le quart", "midi", "minuit"):
        assert needed in words, needed

def test_clock_card_has_an_example():
    c = cards.load_card(os.path.join(CARDS, "03-heure.json"))
    assert c["example"]

def test_space_card_keeps_greek_on_every_row():
    """All house glyphs — schematic, so every row needs its word."""
    c = cards.load_card(os.path.join(CARDS, "02-espace.json"))
    h = render.card_html(c)
    for item in c["items"]:
        assert item["el"] in h, item["fr"]

def test_verbs_card_drops_greek_on_every_row():
    """All emoji — the picture carries it, so no Greek at all."""
    c = cards.load_card(os.path.join(CARDS, "05-verbes.json"))
    h = render.card_html(c)
    for item in c["items"]:
        assert item["el"] not in h, item["fr"]
