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

def test_verbs_card_drops_greek_on_unambiguous_action_icons():
    """These four show the action itself (a walking, sleeping, swimming,
    dancing figure) — the picture genuinely carries the word."""
    c = cards.load_card(os.path.join(CARDS, "05-verbes.json"))
    h = render.card_html(c)
    for fr in ("marcher", "dormir", "nager", "danser"):
        item = next(i for i in c["items"] if i["fr"] == fr)
        assert item["el"] not in h, fr

def test_verbs_card_keeps_greek_on_noun_standing_for_verb_icons():
    """These icons depict an object or a state, not the action (briefcase
    for travailler, money bag for payer, a trolley for acheter, a plate
    for manger, an hourglass for attendre, a book for lire, headphones for
    écouter, a game controller for jouer, two padlocks for ouvrir/fermer).
    Until a dedicated icon pass replaces them, the word must print — see
    greek.SCHEMATIC."""
    c = cards.load_card(os.path.join(CARDS, "05-verbes.json"))
    h = render.card_html(c)
    for fr in ("travailler", "payer", "acheter", "manger", "attendre",
               "lire", "écouter", "jouer", "ouvrir", "fermer"):
        item = next(i for i in c["items"] if i["fr"] == fr)
        assert item["el"] in h, fr
