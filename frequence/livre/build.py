#!/usr/bin/env python3
"""Build the textbook: card JSON -> one self-contained HTML -> A4 PDF.

The HTML is a first-class output, not an intermediate. It is what puts the
book on a phone instead of in a drawer.
"""
import argparse
import os

import cards
import render
import topdf

HERE = os.path.dirname(os.path.abspath(__file__))
TITLE = "Vocabulaire illustré"


def build(cards_dir, out_dir, tiers=(1, 2, 3), title=TITLE):
    os.makedirs(out_dir, exist_ok=True)
    selected = [c for c in cards.load_all(cards_dir) if c["tier"] in tiers]
    if not selected:
        raise SystemExit(f"no cards in {cards_dir} for tiers {tiers}")

    html_path = os.path.join(out_dir, "livre.html")
    pdf_path = os.path.join(out_dir, "livre.pdf")
    open(html_path, "w", encoding="utf-8").write(
        render.document_html(selected, title))
    topdf.render(html_path, pdf_path)

    items = sum(len(c["items"]) for c in selected)
    pages = topdf.page_count(pdf_path)
    print(f"{len(selected)} cards, {items} items, {pages} pages "
          f"({items/pages:.0f}/page)  ->  {pdf_path}")
    return html_path, pdf_path


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cards", default=os.path.join(HERE, "data", "cards"))
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    ap.add_argument("--tiers", default="1,2,3")
    a = ap.parse_args()
    build(a.cards, a.out, tuple(int(t) for t in a.tiers.split(",")))
