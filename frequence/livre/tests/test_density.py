"""Guards for the two properties the C2 layout exists to hold:

1. Density: a page must carry enough items to not read as an
   undifferentiated wall (108/page, rejected) nor as sparse (20/page,
   rejected). 53/page is the agreed target, 50 is the guarded floor.
2. No-split: a card is a semantic group. If its rows are ever divided
   across a page boundary, the group stops being seen whole, which is
   the entire reason the card layout exists over a flat list.
"""
import json
import os
import tempfile

import build
import topdf


def _card(idx, n_items):
    return {
        "id": f"c{idx}", "tier": 1, "order": idx,
        "title_fr": f"Groupe {idx}", "title_el": "ομάδα",
        "accent": "#B5531F", "example": None,
        "items": [{"fr": f"mot{idx}_{i}", "el": None, "key": "on_box"}
                  for i in range(n_items)],
    }


def _write_cards(cards_dir, card_sizes):
    for i, n in enumerate(card_sizes):
        c = _card(i, n)
        json.dump(c, open(os.path.join(cards_dir, f"{i:02d}.json"), "w",
                          encoding="utf-8"), ensure_ascii=False)


def test_a_full_page_carries_at_least_fifty_items():
    """The agreed target is 53/A4. Guard the floor at 50.

    This must be measured over a large fixture, not a handful of cards.
    With only 3-4 cards the set straddles a single page boundary, so the
    trailing page is nearly empty and the average is dragged down by
    packing loss rather than by how tightly rows actually sit on a full
    page. 20+ cards let that packing loss wash out, which is what makes
    this an amortised, steady-state density measurement instead of an
    artefact of fixture size. (Measured ~70-96/page over 20-42 cards of
    24 items each, comfortably above the 50 floor either way.)
    """
    with tempfile.TemporaryDirectory() as d:
        cd = os.path.join(d, "cards"); os.makedirs(cd)
        n_cards, n_items = 20, 24
        _write_cards(cd, [n_items] * n_cards)
        _, pdf = build.build(cd, os.path.join(d, "out"))
        items = n_cards * n_items
        pages = topdf.page_count(pdf)
        assert items / pages >= 50, f"{items/pages:.0f}/page, want >=50"


def test_a_card_is_never_split_across_pages():
    """Prove break-inside:avoid is actually doing something, not just present.

    Counting pages on the real build can't show a card was kept whole —
    a page count is consistent with both "cards never split" and "cards
    split and it happened not to change the total". So this builds the
    real (avoid) PDF, then takes the exact same self-contained HTML and
    flips only the two `avoid` declarations to `auto`, re-rendering that
    as a second (split-allowed) PDF.

    If disallowing splits ever pushes a whole card onto a fresh page
    that a split would have let bleed across (using the tail space on
    the earlier page instead), the avoid build needs strictly MORE pages
    than the split-allowed build for identical content. That is exactly
    what this fixture is sized to trigger: 25 cards of 20 items land on
    9 pages with splitting disallowed and 8 pages with it allowed, and
    (Retuned when the left rail was removed: wider cards changed the
    packing, and 25x20 stopped straddling a boundary. 25 cards of 26
    items now gives 9 pages against 8.) This holds stably across
    repeated renders (checked manually, not
    just once here, since headless Chromium layout is deterministic for
    fixed content). A regression that let cards split again would
    collapse the avoid build down to 6 pages too, which this test would
    catch as a spurious "improvement" in packing that isn't legitimate
    for content whose per-card grouping is supposed to be inviolable.
    """
    with tempfile.TemporaryDirectory() as d:
        cd = os.path.join(d, "cards"); os.makedirs(cd)
        n_cards, n_items = 25, 26
        _write_cards(cd, [n_items] * n_cards)
        html_path, pdf_path = build.build(cd, os.path.join(d, "out"))
        pages_avoid = topdf.page_count(pdf_path)

        src = open(html_path, encoding="utf-8").read()
        assert "break-inside: avoid;" in src
        split_src = (src.replace("break-inside: avoid;", "break-inside: auto;")
                        .replace("page-break-inside: avoid;",
                                 "page-break-inside: auto;"))
        split_html = os.path.join(d, "split.html")
        split_pdf = os.path.join(d, "split.pdf")
        open(split_html, "w", encoding="utf-8").write(split_src)
        topdf.render(split_html, split_pdf)
        pages_split = topdf.page_count(split_pdf)

        assert pages_split < pages_avoid, (
            f"split-allowed build used {pages_split} pages, avoid build "
            f"used {pages_avoid}; expected avoid to cost strictly more "
            "pages by keeping cards whole instead of letting them bleed "
            "across the boundary"
        )
