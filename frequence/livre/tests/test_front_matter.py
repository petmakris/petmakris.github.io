"""The pronunciation section: tier 0, and it comes first.

Pronunciation is the one thing in the book that has to be read before
anything else in it can be said out loud, so it is its own tier rather than
an order number inside tier 1 — that way `--tiers` can still select the word
cards or the phrases alone without dragging it along or losing it.
"""
import os
import re

import cards

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARDS = os.path.join(HERE, "data", "cards")
FRONT = ["voyelles", "nasales", "consonnes", "muettes", "liaison", "accents"]


def test_tier_zero_is_a_legal_tier():
    card = cards.load_card(os.path.join(CARDS, "00a-voyelles.json"))
    assert card["tier"] == 0


def test_the_pronunciation_cards_open_the_book():
    loaded = cards.load_all(CARDS)
    assert [c["id"] for c in loaded[:len(FRONT)]] == FRONT


def test_the_nasal_vowels_are_written_with_a_real_tilde():
    """α̃, õ and ε̃ are a Greek vowel plus COMBINING TILDE (U+0303), which
    Alegreya Sans was checked to render before these cards were written. If
    an editor ever normalises it away, the nasal rows silently become the
    plain oral vowels they exist to contrast with."""
    card = cards.load_card(os.path.join(CARDS, "00b-nasales.json"))
    tilde = [i for i in card["items"] if "̃" in i["el"]]
    assert len(tilde) >= 5, [i["fr"] for i in card["items"]]


def test_the_french_column_stays_french():
    """Every other card puts French on the left and Greek on the right. A
    pronunciation card is the one place it is tempting to write «e (στο
    τέλος)» in the left column, and that is exactly where it would look like
    a mistake."""
    greek = re.compile(r"[Ͱ-Ͽἀ-῿]")
    for cid in FRONT:
        stem = next(f for f in os.listdir(CARDS) if f.endswith(f"-{cid}.json"))
        for item in cards.load_card(os.path.join(CARDS, stem))["items"]:
            assert not greek.search(item["fr"]), f"{cid}: {item['fr']}"
