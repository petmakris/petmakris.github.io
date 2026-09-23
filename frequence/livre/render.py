#!/usr/bin/env python3
"""Card HTML. This module owns ALL layout; card JSON owns only content."""
import base64
import functools
import html as _html
import os
import re

import greek
import icons

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "assets", "fonts")

ARTICLES = ("les ", "le ", "la ", "l'")


def split_article(fr):
    """('la main') -> ('la', 'main'). No article -> ('', fr)."""
    for art in ARTICLES:
        if fr.startswith(art):
            return art.strip(), fr[len(art):]
    return "", fr


def _article_class(art):
    return {"le": "le", "la": "la", "l'": "elid", "les": "les"}.get(art, "")


def row_html(item, accent):
    """One row: icon gutter, coloured article, French, Greek only if needed."""
    svg, kind = icons.resolve(item, accent)
    art, noun = split_article(item["fr"])

    parts = [f'<span class="ic">{svg}</span>']
    if art:
        parts.append(f'<span class="art {_article_class(art)}">'
                     f'{_html.escape(art)}</span>')
    parts.append(f'<b>{_html.escape(noun)}</b>')

    if item.get("el") and greek.keeps_greek(item["fr"], kind):
        parts.append(f'<span class="el">{_html.escape(item["el"])}</span>')

    return f'<div class="wd">{"".join(parts)}</div>'


def _columns(n):
    return 2 if n < 7 else 3


def _example_html(text):
    """`**word**` -> `<strong>word</strong>`."""
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", _html.escape(text))


def card_html(card):
    accent = card["accent"]
    rows = "".join(row_html(i, accent) for i in card["items"])
    cols = _columns(len(card["items"]))

    ex = ""
    if card.get("example"):
        ex = f'<div class="ex">{_example_html(card["example"])}</div>'

    return (
        f'<section class="card" style="--accent:{accent}">'
        f'<div class="rail">'
        f'<h2>{_html.escape(card["title_fr"])}</h2>'
        f'<span class="el-sub">{_html.escape(card["title_el"])}</span>'
        f'<span class="count">{len(card["items"])}</span>'
        f'</div>'
        f'<div class="body"><div class="grid cols-{cols}">{rows}</div>{ex}</div>'
        f'</section>'
    )


@functools.lru_cache(maxsize=1)
def _font_face():
    """Inline both weights so the HTML is self-contained."""
    out = []
    for fname, weight in (("AlegreyaSans-Regular.ttf", 400),
                          ("AlegreyaSans-Bold.ttf", 700)):
        with open(os.path.join(FONTS, fname), "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        out.append(
            '@font-face{font-family:"Alegreya Sans";'
            f'font-weight:{weight};font-style:normal;'
            f'src:url(data:font/ttf;base64,{b64}) format("truetype");}}'
        )
    return "".join(out)


def document_html(cards, title, subtitle="εικονογραφημένο λεξιλόγιο"):
    with open(os.path.join(HERE, "style.css"), encoding="utf-8") as f:
        css = f.read()
    body = "".join(card_html(c) for c in cards)
    return (
        '<!doctype html><html lang="fr"><head><meta charset="utf-8">'
        f"<title>{_html.escape(title)}</title>"
        f"<style>{_font_face()}{css}</style></head><body>"
        f'<header class="doc-head"><h1>{_html.escape(title)}</h1>'
        f'<span class="sub">{_html.escape(subtitle)}</span></header>'
        f"{body}</body></html>"
    )
