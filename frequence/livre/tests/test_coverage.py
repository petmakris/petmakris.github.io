"""Icon coverage over the real book.

The bug this guards: the shipped OpenMoji set was picked by hand and the card
keys were authored as free English glosses, so 345 of 635 word rows resolved
to nothing. Above 60% iconless a card drops its gutter entirely (see
render.NO_GUTTER_ABOVE), which turned that into three fully icon-free pages —
a body page, a NUMBERS page with no numbers, and a transport page with no bus.
Neither the icon tests nor the render tests could see it: every unit passed on
a fixture while the book itself was half empty.
"""
import glob
import json
import os

import cards
import icons

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARDS = os.path.join(HERE, "data", "cards")
OPENMOJI = os.path.join(HERE, "assets", "openmoji")

# Cards whose every word is depictable — a body part, a numeral, a vehicle, a
# colour, a date, a typographic mark. A gap here is a missing icon, not an
# honest blank, so these are held at 100%.
FULLY_ILLUSTRATED = {
    "corps", "visage", "nombres", "calendrier", "couleurs", "transports",
    "destinations", "epeler", "meteo",
    # The pronunciation front matter answers a spelling with a SOUND, and the
    # sound is the icon — a row there without one has lost its answer.
    "voyelles", "nasales", "consonnes", "muettes", "liaison", "accents",
}

# Cards that are grammar: pronoun paradigms, conjunctions, relatives, question
# words. No icon set has a picture of `dont`, and inventing one would teach a
# wrong word. These render as plain word lists on purpose.
GRAMMAR = {
    "squelette", "indefinis", "questions", "conjonctions", "relatifs",
}


def _loaded():
    return {c["id"]: c for c in cards.load_all(CARDS)}


def _blank(card):
    return [i["fr"] for i in card["items"]
            if icons.resolve(i, card["accent"])[1] == "none"]


def test_the_illustrated_cards_have_no_empty_gutters():
    for cid, card in _loaded().items():
        if cid not in FULLY_ILLUSTRATED:
            continue
        assert not _blank(card), f"{cid}: {_blank(card)}"


def test_no_card_outside_the_grammar_set_is_wholly_iconless():
    """A card with no icon at all is the failure the reader sees first: it
    loses the gutter and stops looking like the rest of the book."""
    for cid, card in _loaded().items():
        if cid in GRAMMAR:
            continue
        assert len(_blank(card)) < len(card["items"]), cid


def test_most_of_the_book_is_illustrated():
    """A floor, not a target. It was 46% when the gap was found."""
    loaded = _loaded().values()
    total = sum(len(c["items"]) for c in loaded)
    blank = sum(len(_blank(c)) for c in loaded)
    assert (total - blank) / total >= 0.75, f"{blank}/{total} iconless"


def test_every_hand_picked_icon_is_shipped():
    """An `icon` naming an SVG that is not in assets/ falls back silently to
    a different picture or to none — a typo with no error message."""
    for path in glob.glob(os.path.join(HERE, "data", "*", "*.json")):
        with open(path, encoding="utf-8") as f:
            card = json.load(f)
        for item in card["items"]:
            code = item.get("icon")
            if code:
                assert os.path.exists(os.path.join(OPENMOJI, f"{code}.svg")), \
                    f"{card['id']}/{item['fr']}: {code}"
