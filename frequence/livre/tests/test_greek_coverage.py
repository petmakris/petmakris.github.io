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


def test_every_noun_whose_article_hides_its_gender_declares_one():
    """The pill must not go mixed. `le`/`la` speak for themselves; `l'`,
    `les` and an unsplit `un`/`une` cannot, so those rows carry an explicit
    `g` — including an empty one where the row names both genders. A new card
    that forgets it would silently lose the pill on exactly the words a
    learner most needs it for."""
    import re
    import render
    undeclared = []
    for card in cards.load_all(os.path.join(HERE, "data", "cards")):
        for item in card["items"]:
            art = render.split_article(item["fr"])[0]
            hides = art in ("l'", "les") or re.match(r"^(un|une) ", item["fr"])
            if hides and "g" not in item:
                undeclared.append(f"{card['id']}/{item['fr']}")
    assert not undeclared, undeclared
