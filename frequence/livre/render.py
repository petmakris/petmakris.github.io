#!/usr/bin/env python3
"""Card HTML. This module owns ALL layout; card JSON owns only content."""
import base64
import functools
import html as _html
import os
import re

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


def gender(item):
    """'m', 'f', or '' — which gender pill this row wears.

    `le` and `la` say it themselves. The three articles that do NOT are
    exactly the ones a learner trips on: `l'` elides the gender away in front
    of a vowel, a plural hides it, and an indefinite `un kilo` is never split
    at all. Those rows carry an explicit `g` in the card JSON, and an explicit
    `g` always wins — which is also how a row naming BOTH genders
    («un Grec, une Grecque») opts out, by carrying an empty one.
    """
    g = item.get("g")
    if g is not None:
        return g if g in ("m", "f") else ""
    return {"le": "m", "la": "f"}.get(split_article(item["fr"])[0], "")


def row_html(item, accent, gutter=True):
    """One row: icon gutter, coloured article, French, Greek only if needed.

    gutter=False drops the icon column entirely. card_html turns it off for a
    card where most rows have no icon anyway (grammar sets, phrase cards) —
    there a reserved-but-empty gutter reads as a broken icon card rather than
    the word list it actually is, and it costs horizontal space the text wants.
    """
    svg, kind = icons.resolve(item, accent)
    art, noun = split_article(item["fr"])

    # A row with no icon at all gets an empty gutter, not the dashed
    # placeholder: icons.resolve() still returns that placeholder SVG (kept
    # for callers, like icons' own tests, that check "did this resolve to
    # nothing"), but drawing it on the page reads as a rendering failure
    # rather than the deliberate gap it is. The 26px gutter stays reserved
    # so columns still line up against rows that do have an icon.
    parts = []
    if gutter:
        icon_html = "" if kind == "none" else svg
        parts.append(f'<span class="ic">{icon_html}</span>')

    # Article and noun travel inside ONE span, which is what the gender pill
    # is painted on. It also fixes the space that used to sit between them:
    # the flex gap that correctly separates «le» from «billet» was also
    # separating «l'» from «épaule», and French elides precisely so that
    # there is no gap there.
    term = ""
    if art:
        sep = "" if art == "l'" else " "
        term += (f'<span class="art {_article_class(art)}">'
                 f'{_html.escape(art)}</span>{sep}')
    term += f'<b>{_html.escape(noun)}</b>'
    g = gender(item)
    parts.append(f'<span class="fr{" " + g if g else ""}">{term}</span>')

    # EVERY row that has a Greek gloss prints it. There used to be a "cover
    # test" here — cover the Greek, and if the icon alone recovers the word,
    # drop it — which silently hid 147 glosses. It optimised the wrong thing:
    # a reader does not experience a page as N independent rows, they
    # experience a column, and a column where some rows are translated and
    # some are not reads as an unfinished book, not an economical one. The
    # fix for a gloss that adds nothing is to write a better gloss, not to
    # hide it. See tests/test_render.py::test_every_gloss_prints.
    if (item.get("el") or "").strip():
        parts.append(f'<span class="el">{_html.escape(item["el"])}</span>')

    return f'<div class="wd">{"".join(parts)}</div>'


def _columns(n):
    return 2 if n < 7 else 3


def _example_html(text):
    """`**word**` -> `<strong>word</strong>`."""
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", _html.escape(text))


# Above this share of iconless rows, a card drops its icon gutter and renders
# as a plain word list. Measured over the real book, 54% of all rows resolve to
# no icon, and two grammar cards are 100% iconless — an icon was never plausible
# for a pronoun paradigm. 0.6 keeps the gutter wherever it is still earning it.
NO_GUTTER_ABOVE = 0.6


def _wants_gutter(card):
    items = card["items"]
    if not items:
        return True
    blank = sum(1 for i in items
                if icons.resolve(i, card["accent"])[1] == "none")
    return (blank / len(items)) <= NO_GUTTER_ABOVE


def card_html(card):
    accent = card["accent"]
    gutter = _wants_gutter(card)
    rows = "".join(row_html(i, accent, gutter) for i in card["items"])
    cols = _columns(len(card["items"]))

    ex = ""
    if card.get("example"):
        ex = f'<div class="ex">{_example_html(card["example"])}</div>'

    # A word card is a semantic group and must be seen whole — that is why
    # cards exist at all. A phrase card (tier 4) is just a list of sentences:
    # there is nothing to see whole, and forbidding the break left roughly a
    # third of every phrase page empty.
    flow = "" if card["tier"] < 4 else " flows"

    return (
        f'<section class="card{flow}" style="--accent:{accent}">'
        f'<div class="rail">'
        f'<h2>{_html.escape(card["title_fr"])}</h2>'
        f'<span class="el-sub">{_html.escape(card["title_el"])}</span>'
        f'<span class="count">{len(card["items"])}</span>'
        f'</div>'
        f'<div class="body"><div class="grid cols-{cols}'
        f'{"" if gutter else " nogut"}">{rows}</div>{ex}</div>'
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
