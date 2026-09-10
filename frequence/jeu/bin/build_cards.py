#!/usr/bin/env python3
"""Τυπώνει τις κάρτες: δύο σελίδες A4 ανά σκηνή, ένα PDF ανά σκηνή.

    σελίδα 1   ο διάλογος στα γαλλικά
    σελίδα 2   ο ίδιος διάλογος στα ελληνικά

**Οι δύο σελίδες έχουν ταυτόσημη διάταξη.** Η τρίτη ατάκα είναι στο ίδιο ύψος
αριστερά και δεξιά, στο ίδιο πλαίσιο, με το ίδιο χρώμα. Έτσι το μάτι πηγαίνει
οριζόντια από τα γαλλικά στα ελληνικά χωρίς να ψάχνει. Αυτό επιβάλλει δύο
πράγματα στον κώδικα: η κεφαλίδα έχει **σταθερό ύψος**, και το ύψος κάθε
γραμμής υπολογίζεται **μία φορά για τις δύο γλώσσες μαζί** — όσο θέλει η πιο
ψηλή από τις δύο.

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
M       = 42
TOP     = H - M
ENTETE  = 92          # σταθερό ύψος κεφαλίδας — αλλιώς οι σελίδες ξεχαρβαλώνουν
PIED    = 40

BLEU     = (0.157, 0.333, 0.502)
BLEU_BG  = (0.894, 0.929, 0.965)
VERT     = (0.118, 0.478, 0.298)
VERT_BG  = (0.894, 0.949, 0.910)
AMBRE    = (0.784, 0.463, 0.118)
AMBRE_BG = (0.996, 0.937, 0.847)
NOIR     = (0.106, 0.141, 0.188)
GRIS     = (0.42, 0.46, 0.51)
GRIS_L   = (0.87, 0.85, 0.82)
BLANC    = (1, 1, 1)

for nom, fichier in [("Jeu", "AlegreyaSans-Regular.ttf"),
                     ("Jeu-Bold", "AlegreyaSans-Bold.ttf"),
                     ("Jeu-Black", "AlegreyaSans-ExtraBold.ttf"),
                     ("Titre", "Comfortaa-Bold.ttf")]:
    pdfmetrics.registerFont(TTFont(nom, os.path.join(JEU, "fonts", fichier)))

REG, GRAS, NOIRE, TITRE = "Jeu", "Jeu-Bold", "Jeu-Black", "Titre"


def couleurs(qui):
    return (BLEU, BLEU_BG) if qui == "papa" else (VERT, VERT_BG)


def entete(c, d, titre, sous_titre, langue):
    """Σταθερού ύψους, ώστε η πρώτη ατάκα να ξεκινά στο ίδιο y και στις δύο."""
    y = TOP
    # σήμα σκηνής: στρογγυλό τετράγωνο σε ζεστό κεχριμπάρι
    c.setFillColorRGB(*AMBRE_BG)
    c.roundRect(M, y - 44, 46, 46, 11, stroke=0, fill=1)
    c.setFillColorRGB(*AMBRE)
    c.setFont(TITRE, 20)
    c.drawCentredString(M + 23, y - 30, "%02d" % d["id"])

    c.setFillColorRGB(*NOIR)
    c.setFont(TITRE, 25)
    c.drawString(M + 60, y - 24, titre)
    c.setFillColorRGB(*GRIS)
    c.setFont(REG, 12.5)
    c.drawString(M + 60, y - 41, sous_titre)

    c.setFillColorRGB(*GRIS)
    c.setFont(REG, 10.5)
    c.drawRightString(W - M, y - 12, langue)

    # οι δύο ρόλοι, με τα χρώματά τους
    yr = y - 66
    x = M
    for qui, cle in (("myrto", "myrto"), ("papa", "papa")):
        coul, fond = couleurs(qui)
        etiquette = "%s — %s" % ("ΜΥΡΤΩ" if qui == "myrto" else "ΜΠΑΜΠΑΣ", d["roles"][cle])
        larg = pdfmetrics.stringWidth(etiquette, REG, 10.5) + 26
        c.setFillColorRGB(*fond)
        c.roundRect(x, yr - 5, larg, 19, 9.5, stroke=0, fill=1)
        c.setFillColorRGB(*coul)
        c.circle(x + 11, yr + 4.5, 4, stroke=0, fill=1)
        c.setFont(REG, 10.5)
        c.drawString(x + 20, yr + 1, etiquette)
        x += larg + 10
    return TOP - ENTETE


def mesure(lignes, taille, largeur):
    """Ύψος ανά ατάκα, κοινό για τις δύο γλώσσες: όσο θέλει η πιο ψηλή."""
    inter = taille * 1.28
    blocs, total = [], 0.0
    for ln in lignes:
        fr = simpleSplit(ln["fr"], REG, taille, largeur)
        el = simpleSplit(ln["el"], REG, taille, largeur)
        h = max(len(fr), len(el)) * inter + taille * 0.86
        blocs.append({"fr": fr, "el": el, "h": h})
        total += h + 5
    return blocs, total, inter


def geometrie(d):
    """Η ΜΙΑ διάταξη που μοιράζονται και οι δύο σελίδες."""
    largeur = W - 2 * M - 46
    dispo = (TOP - ENTETE) - (M + PIED)
    for taille in (20, 19, 18, 17, 16, 15, 14, 13, 12, 11):
        blocs, total, inter = mesure(d["lignes"], taille, largeur)
        if total <= dispo:
            return taille, inter, blocs
    return 11, 11 * 1.28, mesure(d["lignes"], 11, largeur)[0]


def page(c, d, langue, num_page):
    """langue = 'fr' ή 'el'. Ίδια γεωμετρία, άλλο κείμενο."""
    grec = langue == "el"
    y = entete(c, d,
               d["titre_el"] if grec else d["titre_fr"],
               d["titre_fr"] if grec else d["titre_el"],
               "ΕΛΛΗΝΙΚΑ" if grec else "FRANÇAIS")
    taille, inter, blocs = geometrie(d)

    for ln, b in zip(d["lignes"], blocs):
        coul, fond = couleurs(ln["qui"])
        h = b["h"]
        c.setFillColorRGB(*fond)
        c.roundRect(M, y - h, W - 2 * M, h, 8, stroke=0, fill=1)
        c.setFillColorRGB(*coul)
        c.circle(M + 17, y - taille * 0.72, 8.5, stroke=0, fill=1)
        c.setFillColorRGB(*BLANC)
        c.setFont(TITRE, 8)
        c.drawCentredString(M + 17, y - taille * 0.72 - 3,
                            "M" if ln["qui"] == "myrto" else "P")

        c.setFillColorRGB(*NOIR)
        c.setFont(GRAS if ln["qui"] == "papa" else REG, taille)
        yy = y - taille * 0.28
        for bout in b[langue]:
            c.drawString(M + 34, yy - taille * 0.86, bout)
            yy -= inter
        y -= h + 5

    c.setStrokeColorRGB(*GRIS_L)
    c.setLineWidth(1)
    c.line(M, M + 26, W - M, M + 26)
    c.setFillColorRGB(*GRIS)
    c.setFont(REG, 10)
    c.drawString(M, M + 11,
                 "Πράσινο η Μυρτώ · μπλε και έντονα ο μπαμπάς"
                 if grec else "MYRTO en vert · PAPA en bleu et gras")
    c.drawRightString(W - M, M + 11, "%d ατάκες · %s" % (len(d["lignes"]), num_page)
                      if grec else "%d lignes · %s" % (len(d["lignes"]), num_page))
    c.showPage()


def page_dialogue(c, d, moi=None, num_page="1 / 2", total=2):
    page(c, d, "fr", num_page)


def page_sens(c, d, num_page="2 / 2"):
    page(c, d, "el", num_page)


def main():
    filtre = sys.argv[1] if len(sys.argv) > 1 else None
    dossier = os.path.join(JEU, "out", "cartes")
    os.makedirs(dossier, exist_ok=True)

    faits = 0
    for f in sorted(glob.glob(os.path.join(JEU, "scenes", "*.json"))):
        base = os.path.basename(f)[:-5]
        if filtre and not base.startswith(filtre):
            continue
        d = json.load(open(f, encoding="utf-8"))
        sortie = os.path.join(dossier, base + ".pdf")
        c = canvas.Canvas(sortie, pagesize=A4)
        c.setTitle("%s — Cartes du Soir" % d["titre_fr"])
        page(c, d, "fr", "1 / 2")
        page(c, d, "el", "2 / 2")
        c.save()
        print("%s  ·  %d ατάκες" % (sortie, len(d["lignes"])))
        faits += 1
    if not faits:
        print("καμία σκηνή δεν ταίριαξε")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
