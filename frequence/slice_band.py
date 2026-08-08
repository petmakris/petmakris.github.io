#!/usr/bin/env python3
"""Clean the French frequency corpus and emit one band's words.

The full corpus (fr_50k.txt) is cleaned ONCE — apostrophe fragments (j', qu'),
non-alphabetic tokens and stray single letters removed. `build_pdf.py` slices
this cleaned list into sheet-sized bands; this script exposes the same cleaning
and writes the words for a given band to `data/band<NN>_words.txt`, which is the
input for the translation + POS passes when generating a NEW band.

Usage:
    python3 slice_band.py 2      # -> data/band02_words.txt (ranks for sheet 2)
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "fr_50k.txt")

_FR = re.compile(r"^[a-zàâäçéèêëîïôöùûüÿœæ]+$")
_ONE_LETTER_OK = {"a", "y"}   # valid one-letter French words (a = has, y = there)


def clean_words(path):
    """Return the frequency-ordered list of learnable words from the corpus."""
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if len(parts) != 2:
                continue
            w = parts[0]
            if "'" in w or "’" in w:          # drop apostrophe fragments
                continue
            if not _FR.match(w):               # drop digits / punctuation / caps
                continue
            if len(w) == 1 and w not in _ONE_LETTER_OK:
                continue
            out.append(w)
    return out


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: python3 slice_band.py <band-number>")
    band = int(sys.argv[1])

    # band size comes from the layout (one sheet) — ask build_pdf.
    import build_pdf  # lazy import to avoid a cycle at module load
    words, start, end = build_pdf.band_words(band)
    if not words:
        sys.exit(f"band {band} is empty — corpus exhausted")

    os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
    out = os.path.join(HERE, "data", f"band{band:02d}_words.txt")
    with open(out, "w", encoding="utf-8") as o:
        o.write("\n".join(words) + "\n")

    print(f"band {band}: global ranks {start}–{end} ({len(words)} words) -> {out}")
    print("  first:", words[:5])
    print("  last: ", words[-5:])


if __name__ == "__main__":
    main()
