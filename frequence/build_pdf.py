#!/usr/bin/env python3
"""Render one sheet (2 sides of A4) of the French frequency reference.

A "band" is sized to exactly fill one physical sheet — two A4 pages — so the
word count per band is derived from the layout, not a round number. Words are
laid out in striped sections (SECTION rows shaded, SECTION rows blank) for easy
visual targeting; there are no per-word rank numbers.

Data lives in a single master store keyed by word:
    data/translations.txt   `french = english` per line
    data/pos.txt            `french|POS|REG` per line
The word list itself is derived from fr_50k.txt by slice_band.clean_words().

Usage:
    python3 build_pdf.py            # band 1 (default)
    python3 build_pdf.py --band 2   # the next sheet
Output: out/french_<start>-<end>.pdf
"""
import argparse
import os

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth

from slice_band import clean_words, SRC

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- colours by part of speech ----
BLUE  = (0.13, 0.40, 0.69)   # verbs
BLACK = (0.10, 0.10, 0.10)   # nouns
GREEN = (0.16, 0.49, 0.22)   # adjectives
AMBER = (0.72, 0.50, 0.04)   # adverbs
GREYC = (0.55, 0.55, 0.55)   # function words / numbers / interjections / other
SLATE = (0.20, 0.23, 0.28)   # band range pill
DARK  = (0.0, 0.0, 0.0)
BAND_TINT = (0.910, 0.940, 0.990)   # soft blue section stripe


def word_color(p):
    return {"V": BLUE, "N": BLACK, "ADJ": GREEN, "ADV": AMBER}.get(p, GREYC)


def is_irregular(p, reg):
    return p == "V" and reg == "irr"


def tint(color, t=0.86):
    """Lighten a colour toward white for pill backgrounds."""
    return tuple(ch + (1 - ch) * t for ch in color)


# ---- layout constants ----
PAGE_W, PAGE_H = A4
M = 30            # outer margin
COLS = 6
GAP = 16          # gap between columns
TITLE_H = 64      # reserved on page 1 for the centred legend strip + breathing room
LINE_H = 13.4
SECTION = 10      # rows per shaded/blank stripe
F_FR, S_FR = "Helvetica-Bold", 8.2
F_EN, S_EN = "Helvetica", 7.8

col_w = (PAGE_W - 2 * M - (COLS - 1) * GAP) / COLS


def col_x(ci):
    return M + ci * (col_w + GAP)


def rows_per(top_y):
    return int((top_y - M) // LINE_H)


def capacity():
    """Words that fill one sheet: page 1 (with header) + page 2 (full)."""
    rows_p1 = rows_per(PAGE_H - M - TITLE_H)
    rows_p2 = rows_per(PAGE_H - M)
    return rows_p1, rows_p2, COLS * (rows_p1 + rows_p2)


def band_words(band):
    """Return (words, start_rank, end_rank) for the given sheet-sized band."""
    words = clean_words(SRC)
    cap = capacity()[2]
    start = (band - 1) * cap
    chunk = words[start:start + cap]
    return chunk, start + 1, start + len(chunk)


def load_data():
    gloss, pos = {}, {}
    tp = os.path.join(HERE, "data", "translations.txt")
    pp = os.path.join(HERE, "data", "pos.txt")
    if os.path.exists(tp):
        for line in open(tp, encoding="utf-8"):
            if "=" in line:
                fr, en = line.split("=", 1)
                gloss[fr.strip()] = en.strip()
    if os.path.exists(pp):
        for line in open(pp, encoding="utf-8"):
            line = line.strip()
            if line:
                fr, p, reg = (line.split("|") + ["-", "-"])[:3]
                pos[fr] = (p, reg)
    return gloss, pos


def draw_header(c, start_rank, end_rank):
    """Centred range pill (row 1) above a centred colour legend (row 2)."""
    fs1, ph1, pad1 = 8.5, 15.0, 11
    label = f"mots {start_rank}–{end_rank}"
    tw = stringWidth(label, "Helvetica-Bold", fs1)
    pw = tw + 2 * pad1
    x = (PAGE_W - pw) / 2
    y1 = PAGE_H - M - ph1
    c.setLineWidth(0.7)
    c.setFillColorRGB(*SLATE)
    c.setStrokeColorRGB(*SLATE)
    c.roundRect(x, y1, pw, ph1, ph1 / 2, stroke=1, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", fs1)
    c.drawString(x + pad1, y1 + (ph1 - fs1) / 2 + 0.8, label)

    items = [
        ("verbe", BLUE, False),
        ("verbe irrégulier", BLUE, True),
        ("nom", BLACK, False),
        ("adjectif", GREEN, False),
        ("adverbe", AMBER, False),
        ("grammaire", GREYC, False),
    ]
    fs, ph, pad_x, gap = 7.6, 14.0, 8, 7
    widths = [stringWidth(l, "Helvetica-Bold", fs) + 2 * pad_x for l, _, _ in items]
    total = sum(widths) + gap * (len(items) - 1)
    x = (PAGE_W - total) / 2
    y0 = y1 - 12 - ph
    text_y = y0 + (ph - fs) / 2 + 0.7
    for (lab, color, ul), w in zip(items, widths):
        c.setLineWidth(0.7)
        c.setFillColorRGB(*tint(color))
        c.setStrokeColorRGB(*color)
        c.roundRect(x, y0, w, ph, ph / 2, stroke=1, fill=1)
        c.setFillColorRGB(*color)
        c.setFont("Helvetica-Bold", fs)
        tw2 = stringWidth(lab, "Helvetica-Bold", fs)
        c.drawString(x + pad_x, text_y, lab)
        if ul:
            c.setStrokeColorRGB(*color)
            c.setLineWidth(0.6)
            c.line(x + pad_x, text_y - 1.7, x + pad_x + tw2, text_y - 1.7)
        x += w + gap

    c.setFillColorRGB(*DARK)
    c.setStrokeColorRGB(0, 0, 0)


def draw_word(c, x, y, fr, en, p, reg):
    wc = word_color(p)
    c.setFont(F_FR, S_FR)
    c.setFillColorRGB(*wc)
    c.drawString(x, y, fr)
    fw = stringWidth(fr, F_FR, S_FR)
    if is_irregular(p, reg):
        c.setStrokeColorRGB(*wc)
        c.setLineWidth(0.45)
        c.line(x, y - 1.7, x + fw, y - 1.7)
    en_x = x + fw + stringWidth("  ", F_EN, S_EN)
    avail = (x + col_w) - en_x
    sz = S_EN
    while stringWidth(en, F_EN, sz) > avail and sz > 4.2:
        sz -= 0.2
    c.setFont(F_EN, sz)
    c.setFillColorRGB(*GREYC)
    d = en
    while stringWidth(d, F_EN, sz) > avail and len(d) > 1:
        d = d[:-1]
    c.drawString(en_x, y, d)


def build(band):
    words, start_rank, end_rank = band_words(band)
    gloss, pos = load_data()
    entries = [(w, gloss.get(w, "?"), *pos.get(w, ("OTHER", "-"))) for w in words]
    missing = sum(1 for e in entries if e[1] == "?")

    out_path = os.path.join(HERE, "out", f"french_{start_rank:04d}-{end_rank:04d}.pdf")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    c = canvas.Canvas(out_path, pagesize=A4)

    rows_p1, rows_p2, _ = capacity()
    draw_header(c, start_rank, end_rank)
    page = 1
    rows_this = rows_p1
    ci, row = 0, 0
    y = PAGE_H - M - TITLE_H

    for w, en, p, reg in entries:
        if row >= rows_this:
            ci += 1
            row = 0
            if ci >= COLS:
                c.showPage()
                page += 1
                ci = 0
                rows_this = rows_p2
            y = (PAGE_H - M - TITLE_H) if page == 1 else (PAGE_H - M)
        x = col_x(ci)
        # one rectangle per shaded section so stripes tile seamlessly
        if row % SECTION == 0 and (row // SECTION) % 2 == 0:
            seg = min(SECTION, rows_this - row)
            ry = y - (seg - 1) * LINE_H - 3.0
            c.setFillColorRGB(*BAND_TINT)
            c.rect(x - 4, ry, col_w + 8, seg * LINE_H, stroke=0, fill=1)
        draw_word(c, x, y, w, en, p, reg)
        y -= LINE_H
        row += 1

    c.showPage()
    c.save()
    print(f"wrote {out_path}  (band {band}, ranks {start_rank}-{end_rank}, "
          f"{page} pages, {len(entries)} words, {missing} missing glosses)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--band", type=int, default=1, help="sheet-sized band number")
    build(ap.parse_args().band)
