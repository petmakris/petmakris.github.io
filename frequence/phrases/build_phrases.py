#!/usr/bin/env python3
"""Render one sheet (2 sides of A4) of common French phrases — compact layout.

Same dense feel as the frequency word sheets: single-line entries (French phrase
+ English on one line), theme-coloured, striped sections, no checkboxes. Phrases
are curated (no frequency corpus) and grouped by theme.

Data: data/phrases.tsv — `french <TAB> english <TAB> theme` per line.

Usage:
    python3 build_phrases.py            # sheet 1
    python3 build_phrases.py --band 2   # next sheet
Output: out/phrases_sheet_NN.pdf
"""
import argparse
import os

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- themes & colours ----
THEMES = {
    "salutations": ((0.13, 0.40, 0.69), "salutations"),
    "questions":   ((0.72, 0.50, 0.04), "questions"),
    "quotidien":   ((0.16, 0.49, 0.22), "quotidien"),
    "opinions":    ((0.72, 0.25, 0.40), "opinions"),
    "connecteurs": ((0.50, 0.50, 0.52), "connecteurs"),
    "expressions": ((0.50, 0.30, 0.65), "expressions"),
}
GREYC = (0.50, 0.50, 0.52)
SLATE = (0.20, 0.23, 0.28)
DARK = (0.0, 0.0, 0.0)
BAND_TINT = (0.952, 0.958, 0.965)


def theme_color(t):
    return THEMES.get(t, (GREYC, t))[0]


def tint(color, t=0.86):
    return tuple(ch + (1 - ch) * t for ch in color)


# ---- layout (matches the word sheets' density) ----
PAGE_W, PAGE_H = A4
M = 26
COLS = 2
GAP = 14
TITLE_H = 54
LINE_H = 12.4
SECTION = 10          # rows per shaded/blank stripe
F_FR, S_FR = "Helvetica-Bold", 8.2
F_EN, S_EN = "Helvetica", 7.6

col_w = (PAGE_W - 2 * M - (COLS - 1) * GAP) / COLS


def col_x(ci):
    return M + ci * (col_w + GAP)


def rows_per(top_y):
    return int((top_y - M) // LINE_H)


def capacity():
    rows_p1 = rows_per(PAGE_H - M - TITLE_H)
    rows_p2 = rows_per(PAGE_H - M)
    return rows_p1, rows_p2, COLS * (rows_p1 + rows_p2)


def load_phrases():
    path = os.path.join(HERE, "data", "phrases.tsv")
    rows = []
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.rstrip("\n")
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) >= 3:
                rows.append((parts[0].strip(), parts[1].strip(), parts[2].strip()))
    return rows


def band_slice(band):
    rows = load_phrases()
    cap = capacity()[2]
    start = (band - 1) * cap
    chunk = rows[start:start + cap]
    return chunk, start + 1, start + len(chunk), len(rows)


def draw_header(c, sheet, n_sheets):
    fs1, ph1, pad1 = 9.0, 16.0, 12
    label = f"expressions courantes — feuille {sheet}/{n_sheets}"
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

    items = [(name, col) for (col, name) in THEMES.values()]
    fs, ph, pad_x, gap = 7.2, 13.5, 7, 6
    widths = [stringWidth(n, "Helvetica-Bold", fs) + 2 * pad_x for n, _ in items]
    total = sum(widths) + gap * (len(items) - 1)
    x = (PAGE_W - total) / 2
    y0 = y1 - 11 - ph
    text_y = y0 + (ph - fs) / 2 + 0.7
    for (name, col), w in zip(items, widths):
        c.setLineWidth(0.7)
        c.setFillColorRGB(*tint(col))
        c.setStrokeColorRGB(*col)
        c.roundRect(x, y0, w, ph, ph / 2, stroke=1, fill=1)
        c.setFillColorRGB(*col)
        c.setFont("Helvetica-Bold", fs)
        c.drawString(x + pad_x, text_y, name)
        x += w + gap
    c.setFillColorRGB(*DARK)
    c.setStrokeColorRGB(0, 0, 0)


def draw_entry(c, x, y, fr, en, theme):
    col = theme_color(theme)
    # french (bold, theme colour) — shrink to leave room for the gloss
    sz = S_FR
    while stringWidth(fr, F_FR, sz) > col_w * 0.66 and sz > 6.4:
        sz -= 0.2
    c.setFont(F_FR, sz)
    c.setFillColorRGB(*col)
    c.drawString(x, y, fr)
    fw = stringWidth(fr, F_FR, sz)
    en_x = x + fw + stringWidth("  ", F_EN, S_EN)
    avail = (x + col_w) - en_x
    esz = S_EN
    while stringWidth(en, F_EN, esz) > avail and esz > 5.2:
        esz -= 0.2
    c.setFont(F_EN, esz)
    c.setFillColorRGB(*GREYC)
    d = en
    while stringWidth(d, F_EN, esz) > avail and len(d) > 1:
        d = d[:-1]
    c.drawString(en_x, y, d)


def total_sheets():
    total = len(load_phrases())
    return max(1, -(-total // capacity()[2]))


def render_sheet(c, band, n_sheets):
    """Draw one sheet (up to 2 pages) onto canvas c; ends with a showPage."""
    rows = band_slice(band)[0]
    rows_p1, _, _ = capacity()
    draw_header(c, band, n_sheets)
    page = 1
    rows_this = rows_p1
    ci, row = 0, 0
    y = PAGE_H - M - TITLE_H
    for fr, en, theme in rows:
        if row >= rows_this:
            ci += 1
            row = 0
            if ci >= COLS:
                c.showPage()
                page += 1
                ci = 0
                rows_this = capacity()[1]
            y = (PAGE_H - M - TITLE_H) if page == 1 else (PAGE_H - M)
        x = col_x(ci)
        if row % SECTION == 0 and (row // SECTION) % 2 == 0:
            seg = min(SECTION, rows_this - row)
            ry = y - (seg - 1) * LINE_H - 3.0
            c.setFillColorRGB(*BAND_TINT)
            c.rect(x - 5, ry, col_w + 10, seg * LINE_H, stroke=0, fill=1)
        draw_entry(c, x, y, fr, en, theme)
        y -= LINE_H
        row += 1
    c.showPage()
    return len(rows)


def build(band):
    if not band_slice(band)[0]:
        raise SystemExit(f"sheet {band}: no phrases. Add to data/phrases.tsv")
    out = os.path.join(HERE, "out", f"phrases_sheet_{band:02d}.pdf")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    c = canvas.Canvas(out, pagesize=A4)
    n = render_sheet(c, band, total_sheets())
    c.save()
    print(f"wrote {out}  (sheet {band}, {n} phrases)")


def build_all():
    n_sheets = total_sheets()
    out = os.path.join(HERE, "out", "phrases_all.pdf")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    c = canvas.Canvas(out, pagesize=A4)
    for b in range(1, n_sheets + 1):
        render_sheet(c, b, n_sheets)
    c.save()
    print(f"wrote {out}  ({n_sheets} sheets, {len(load_phrases())} phrases, "
          f"{2 * n_sheets} pages max)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--band", type=int, default=1)
    ap.add_argument("--all", action="store_true", help="render all sheets into one PDF")
    args = ap.parse_args()
    build_all() if args.all else build(args.band)
