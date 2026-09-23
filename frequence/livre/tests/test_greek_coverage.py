"""Every vocabulary row in the finished book carries a Greek gloss."""
import os, sys
import cards

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_no_row_anywhere_is_missing_its_greek():
    blank = []
    for sub in ("cards", "phrases"):
        for card in cards.load_all(os.path.join(HERE, "data", sub)):
            for item in card["items"]:
                if not (item.get("el") or "").strip():
                    blank.append(f"{card['id']}/{item['fr']}")
    assert not blank, f"{len(blank)} rows with no Greek: {blank[:20]}"
