#!/usr/bin/env python3
"""Φτιάχνει το λεξικό A1 από τον κατάλογο συχνότητας του frequence.

Διαβάζει επιτόπου, χωρίς αντιγραφή:
    ../fr_50k.txt              γαλλικά κατά σειρά συχνότητας (υπότιτλοι 2018)
    ../data/translations.txt   γαλλικά = αγγλικά
    ../data/translations.el.txt γαλλικά = ελληνικά
    ../data/pos.txt            γαλλικά|POS|REG

Βγάζει data/lexique.json με δύο κατώφλια:
    squelette  οι πρώτες SKEL λέξεις — η δομή, το τι κάνει μια πρόταση A1
    large      οι πρώτες LARGE λέξεις — από εδώ επιτρέπονται τα ουσιαστικά του τόπου
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
JEU  = os.path.dirname(HERE)
SRC  = os.path.dirname(JEU)

SKEL  = 1200
LARGE = 5000


def read_pairs(path, sep=" = "):
    out = {}
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if sep in line:
                k, v = line.rstrip("\n").split(sep, 1)
                out[k.strip()] = v.strip()
    return out


def main():
    words = []
    with open(os.path.join(SRC, "fr_50k.txt"), encoding="utf-8") as fh:
        for line in fh:
            parts = line.split()
            if parts:
                words.append(parts[0])

    en = read_pairs(os.path.join(SRC, "data", "translations.txt"))
    el = read_pairs(os.path.join(SRC, "data", "translations.el.txt"))

    pos = {}
    p = os.path.join(SRC, "data", "pos.txt")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as fh:
            for line in fh:
                bits = line.rstrip("\n").split("|")
                if bits and bits[0]:
                    pos[bits[0]] = bits[1] if len(bits) > 1 else ""

    rangs = {w: i + 1 for i, w in enumerate(words[:LARGE])}

    # Γέφυρα ρηματικών τύπων. Ο κατάλογος είναι λίστα ΤΥΠΩΝ, όχι λημμάτων:
    # το «dors» είναι στους 1.200 και το «dormez» στους 6.180, αλλά το δεύτερο
    # δεν είναι δυσκολότερο από το πρώτο. Ένας τύπος μέσα στους LARGE γίνεται
    # δεκτός αν υπάρχει ρήμα στον σκελετό με το ίδιο τρίγραμμο θέμα.
    est_v = lambda w: pos.get(w, "").startswith("V")
    themes = {w[:3] for w in words[:SKEL] if est_v(w) and len(w) >= 3}
    formes = sorted(w for w in words[SKEL:LARGE]
                    if est_v(w) and len(w) >= 3 and w[:3] in themes)
    lex = {
        "source": "fr_50k.txt (FrequencyWords 2018, υπότιτλοι)",
        "squelette": SKEL,
        "large": LARGE,
        "rangs": rangs,
        "formes": formes,
        "sens": {w: {"en": en.get(w, ""), "el": el.get(w, ""), "pos": pos.get(w, "")}
                 for w in words[:SKEL]},
    }
    out = os.path.join(JEU, "data", "lexique.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(lex, fh, ensure_ascii=False)
    print("%s · σκελετός %d, ευρύ %d, γέφυρα ρημάτων %d τύποι"
          % (out, SKEL, LARGE, len(formes)))


if __name__ == "__main__":
    sys.exit(main())
