#!/usr/bin/env python3
"""Build the textbook: card JSON -> one self-contained HTML -> A4 PDF.

The HTML is a first-class output, not an intermediate. It is what puts the
book on a phone instead of in a drawer.
"""
import argparse
import os

import cards
import icons
import render
import topdf

HERE = os.path.dirname(os.path.abspath(__file__))
TITLE = "Vocabulaire illustré"


def _check_strict(selected):
    """Fail loudly on a hand-picked `icon` that doesn't resolve.

    A legitimate placeholder (NO_ICON, or a keyword with no automatic match)
    must NOT fail this — only an explicit `icon` that was asked for by name
    and isn't a shipped SVG, which is otherwise a silent typo that quietly
    falls back to a different icon or to nothing.
    """
    problems = []
    for c in selected:
        for item in c["items"]:
            if icons.explicit_icon_missing(item):
                problems.append(
                    f"card {c['id']!r}, row {item['fr']!r}: "
                    f"icon {item['icon']!r} has no shipped SVG")
    if problems:
        raise SystemExit("strict mode: " + "; ".join(problems))


# The book is sorted by tier, which is also its running order: tier 0 is the
# pronunciation front matter (how the letters sound before any of them mean
# anything), tiers 1-3 the illustrated word cards, tier 4 the phrase cards
# migrated from the old deck. They live in two directories; the sort merges
# them.
PHRASES = os.path.join(HERE, "data", "phrases")


def build(cards_dir, out_dir, tiers=(0, 1, 2, 3, 4), title=TITLE, strict=False,
          phrases_dir=None):
    os.makedirs(out_dir, exist_ok=True)
    loaded = cards.load_all(cards_dir)
    if phrases_dir and os.path.isdir(phrases_dir):
        loaded += cards.load_all(phrases_dir)
    loaded.sort(key=lambda c: (c["tier"], c["order"]))
    selected = [c for c in loaded if c["tier"] in tiers]
    if not selected:
        raise SystemExit(f"no cards in {cards_dir} for tiers {tiers}")

    if strict:
        _check_strict(selected)

    html_path = os.path.join(out_dir, "livre.html")
    pdf_path = os.path.join(out_dir, "livre.pdf")
    open(html_path, "w", encoding="utf-8").write(
        render.document_html(selected, title))
    topdf.render(html_path, pdf_path)

    items = sum(len(c["items"]) for c in selected)
    pages = topdf.page_count(pdf_path)
    if pages:
        print(f"{len(selected)} cards, {items} items, {pages} pages "
              f"({items/pages:.0f}/page)  ->  {pdf_path}")
    else:
        # topdf.page_count counts /Type /Page objects by regex; a renderer
        # change that compresses the page tree (an object stream) makes that
        # regex find nothing. 0 pages is never real, so say so plainly
        # instead of dividing by it.
        print(f"{len(selected)} cards, {items} items, page count unreadable "
              f"(topdf.page_count found 0 — check for a renderer change)  "
              f"->  {pdf_path}")
    return html_path, pdf_path


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cards", default=os.path.join(HERE, "data", "cards"))
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    ap.add_argument("--tiers", default="0,1,2,3,4")
    ap.add_argument("--phrases", default=PHRASES)
    ap.add_argument("--strict", action="store_true",
                     help="fail the build if a hand-picked icon is missing")
    a = ap.parse_args()
    build(a.cards, a.out, tuple(int(t) for t in a.tiers.split(",")),
          strict=a.strict, phrases_dir=a.phrases)
