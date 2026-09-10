#!/usr/bin/env python3
"""Ενώνει τις κάρτες σε ένα τυπώσιμο πακέτο μέσα στην ενότητα του blog.

    <blog>/cartes/cartes-du-soir.pdf   όλες οι σκηνές, τρεις σελίδες η καθεμιά
"""
import glob, os, sys
from pypdf import PdfWriter

HERE = os.path.dirname(os.path.abspath(__file__))
JEU  = os.path.dirname(HERE)
BLOG = os.path.dirname(os.path.dirname(JEU))


def main():
    pdfs = sorted(glob.glob(os.path.join(JEU, "out", "cartes", "*.pdf")))
    if not pdfs:
        print("δεν υπάρχουν PDF — τρέξε πρώτα make cartes")
        return 1
    w = PdfWriter()
    for p in pdfs:
        w.append(p)
    os.makedirs(os.path.join(BLOG, "cartes"), exist_ok=True)
    out = os.path.join(BLOG, "cartes", "cartes-du-soir.pdf")
    with open(out, "wb") as fh:
        w.write(fh)
    print("%s · %d σκηνές, %d σελίδες, %.0f KB"
          % (out, len(pdfs), len(w.pages), os.path.getsize(out) / 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
