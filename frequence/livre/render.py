#!/usr/bin/env python3
"""Card HTML. This module owns ALL layout; card JSON owns only content."""
import html as _html

import greek
import icons

ARTICLES = ("les ", "le ", "la ", "l'")


def split_article(fr):
    """('la main') -> ('la', 'main'). No article -> ('', fr)."""
    for art in ARTICLES:
        if fr.startswith(art):
            return art.strip(), fr[len(art):]
    return "", fr


def _article_class(art):
    return {"le": "le", "la": "la", "l'": "el", "les": "les"}.get(art, "")


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
