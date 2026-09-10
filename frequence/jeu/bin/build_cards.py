#!/usr/bin/env python3
"""Τυπώνει τις κάρτες: δύο σελίδες A4 ανά σκηνή, ένα PDF ανά σκηνή.

    σελίδα 1   ο διάλογος στα γαλλικά — έντονες μπλε οι ατάκες του μπαμπά,
               πράσινες κανονικές της Μυρτώς· ένα φύλλο και για τους δύο
    σελίδα 2   «Τι σημαίνει» — τα ελληνικά

Οι δύο σελίδες είναι ΖΕΥΓΟΣ: στο τυπωμένο τεύχος η γαλλική πέφτει πάντα
αριστερά και η ελληνική δεξιά (δες το build_pack.py για τη σελιδοποίηση).

Το μέγεθος των γραμμάτων προσαρμόζεται ώστε η σκηνή να χωράει πάντα σε μία
σελίδα: δοκιμάζει από 20 στιγμές και κατεβαίνει μέχρι να χωρέσει.

    python3 bin/build_cards.py            όλες οι σκηνές -> out/cartes/
    python3 bin/build_cards.py 04         μόνο η σκηνή 04
"""
import glob, json, os, sys

from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HERE = os.path.dirname(os.path.abspath(__file__))
JEU  = os.path.dirname(HERE)

W, H = A4
M       = 44          # περιθώριο
TOP     = H - M
BLEU    = (0.165, 0.333, 0.502)
VERT    = (0.118, 0.478, 0.298)
BLEU_BG = (0.906, 0.929, 0.957)
VERT_BG = (0.910, 0.945, 0.918)
NOIR    = (0.106, 0.141, 0.188)
GRIS    = (0.42, 0.46, 0.51)
GRIS_L  = (0.80, 0.78, 0.74)

CANDIDATS = [
    ("Georgia",  "/System/Library/Fonts/Supplemental/Georgia.ttf",
                 "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"),
    ("Times",    "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
                 "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf"),
    ("DejaVu",   "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"),
]


def couvre_grec(path):
    """Η σελίδα 3 είναι ελληνική· η γραμματοσειρά πρέπει να έχει άλφα."""
    try:
        from fontTools.ttLib import TTFont as FT
        return any(0x03B1 in t.cmap for t in FT(path)["cmap"].tables)
    except Exception:
        return "Georgia" in path or "Times" in path or "DejaVu" in path


def enregistre():
    for nom, reg, gras in CANDIDATS:
        if os.path.exists(reg) and os.path.exists(gras) and couvre_grec(reg):
            pdfmetrics.registerFont(TTFont(nom, reg))
            pdfmetrics.registerFont(TTFont(nom + "-Bold", gras))
            return nom, nom + "-Bold"
    raise SystemExit("δεν βρέθηκε γραμματοσειρά με λατινικά και ελληνικά μαζί")


REG, GRAS = enregistre()


def entete(c, scene, titre, sous, couleur_r):
    c.setFillColorRGB(*GRIS)
    c.setFont(REG, 10)
    c.drawString(M, TOP - 10, scene)
    c.setFillColorRGB(*NOIR)
    c.setFont(GRAS, 25)
    c.drawString(M, TOP - 38, titre)
    c.setFillColorRGB(*GRIS)
    c.setFont(REG, 10.5)
    c.drawRightString(W - M, TOP - 10, sous)
    c.setStrokeColorRGB(*NOIR)
    c.setLineWidth(1.6)
    c.line(M, TOP - 50, W - M, TOP - 50)
    return TOP - 74


def pied(c, gauche, droite):
    c.setStrokeColorRGB(*NOIR)
    c.setLineWidth(1.6)
    c.line(M, M + 26, W - M, M + 26)
    c.setFillColorRGB(*GRIS)
    c.setFont(REG, 9.5)
    c.drawString(M, M + 12, gauche)
    c.drawRightString(W - M, M + 12, droite)


def mise_en_page(lignes, taille, largeur, cle="fr"):
    """Πόσο ύψος θέλει η σκηνή σε αυτό το μέγεθος."""
    inter, total, blocs = taille * 1.28, 0.0, []
    for ln in lignes:
        bouts = simpleSplit(ln[cle], REG, taille, largeur)
        h = len(bouts) * inter + taille * 0.85
        blocs.append((bouts, h))
        total += h
    return blocs, total


def page_dialogue(c, d, moi=None, num_page=1, total=2):
    """Ένα φύλλο για τους δύο.

    Οι ατάκες του μπαμπά βγαίνουν έντονες με μπλε πλαϊνή γραμμή, της Μυρτώς
    πράσινες και κανονικού βάρους. Ο καθένας βρίσκει τις δικές του από το
    χρώμα, χωρίς να χρειάζονται δύο αντίγραφα του ίδιου διαλόγου.
    """
    roles = d["roles"]
    sous = "PAPA — %s   ·   MYRTO — %s" % (roles["papa"], roles["myrto"])
    y = entete(c, "SCÈNE %02d" % d["id"], d["titre_fr"], sous, None)
    bas = M + 40
    largeur = W - 2 * M - 26

    for taille in (20, 19, 18, 17, 16, 15, 14, 13, 12):
        blocs, total = mise_en_page(d["lignes"], taille, largeur)
        if total <= y - bas:
            break

    inter = taille * 1.28
    for ln, (bouts, h) in zip(d["lignes"], blocs):
        sien = ln["qui"] == "papa"
        coul, fond = (BLEU, BLEU_BG) if ln["qui"] == "papa" else (VERT, VERT_BG)
        if sien:
            c.setFillColorRGB(*fond)
            c.rect(M - 6, y - h + 6, W - 2 * M + 12, h, stroke=0, fill=1)
            c.setFillColorRGB(*coul)
            c.rect(M - 6, y - h + 6, 3, h, stroke=0, fill=1)
        c.setFillColorRGB(*coul)
        c.setFont(REG, 9.5)
        c.drawString(M + 4, y - taille * 0.82, "P" if ln["qui"] == "papa" else "M")
        c.setFillColorRGB(*(NOIR if sien else GRIS))
        c.setFont(GRAS if sien else REG, taille)
        yy = y
        for b in bouts:
            c.drawString(M + 26, yy - taille * 0.82, b)
            yy -= inter
        y -= h
        c.setStrokeColorRGB(*GRIS_L)
        c.setLineWidth(0.5)
        c.line(M, y + 4, W - M, y + 4)

    pied(c, "PAPA en bleu et gras  ·  MYRTO en vert",
         "FRANÇAIS  ·  %d lignes  ·  %s" % (len(d["lignes"]), num_page))
    c.showPage()


def page_sens(c, d, num_page="—"):
    y = entete(c, "ΣΚΗΝΗ %02d" % d["id"], d["titre_el"], "Τι σημαίνει", None)
    bas = M + 40
    largeur = W - 2 * M - 26

    # Κάθε ατάκα πιάνει τη γαλλική γραμμή (taille*0.98) συν το ελληνικό μπλοκ.
    for taille in (15, 14, 13, 12, 11, 10, 9):
        blocs, total = mise_en_page(d["lignes"], taille, largeur, cle="el")
        if total + len(d["lignes"]) * (taille * 0.98) <= y - bas:
            break

    inter = taille * 1.28
    for ln, (bouts, h) in zip(d["lignes"], blocs):
        coul = BLEU if ln["qui"] == "papa" else VERT
        c.setFillColorRGB(*coul)
        c.setFont(REG, 9)
        c.drawString(M + 4, y - taille * 0.82, "P" if ln["qui"] == "papa" else "M")
        c.setFillColorRGB(*GRIS)
        c.setFont(REG, taille * 0.72)
        c.drawString(M + 26, y - taille * 0.78, ln["fr"])
        y -= taille * 0.98
        c.setFillColorRGB(*NOIR)
        c.setFont(REG, taille)
        yy = y
        for b in bouts:
            c.drawString(M + 26, yy - taille * 0.82, b)
            yy -= inter
        y -= h
        c.setStrokeColorRGB(*GRIS_L)
        c.setLineWidth(0.5)
        c.line(M, y + 6, W - M, y + 6)

    pied(c, "Η σελίδα δίπλα, στα γαλλικά.",
         "ΕΛΛΗΝΙΚΑ  ·  %s" % num_page)
    c.showPage()


def main():
    filtre = sys.argv[1] if len(sys.argv) > 1 else None
    dossier = os.path.join(JEU, "out", "cartes")
    os.makedirs(dossier, exist_ok=True)

    fichiers = sorted(glob.glob(os.path.join(JEU, "scenes", "*.json")))
    faits = 0
    for f in fichiers:
        base = os.path.basename(f)[:-5]
        if filtre and not base.startswith(filtre):
            continue
        d = json.load(open(f, encoding="utf-8"))
        sortie = os.path.join(dossier, base + ".pdf")
        c = canvas.Canvas(sortie, pagesize=A4)
        c.setTitle("%s — Cartes du Soir" % d["titre_fr"])
        page_dialogue(c, d, num_page="1 / 2")
        page_sens(c, d, num_page="2 / 2")
        c.save()
        print("%s  ·  %d ατάκες" % (sortie, len(d["lignes"])))
        faits += 1
    if not faits:
        print("καμία σκηνή δεν ταίριαξε")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
