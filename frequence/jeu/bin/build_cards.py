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

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HERE = os.path.dirname(os.path.abspath(__file__))
JEU  = os.path.dirname(HERE)

W, H = A4
M       = 42
URL     = "https://petmakris.github.io/cartes/"
TOP     = H - M
ENTETE  = 92          # σταθερό ύψος κεφαλίδας — αλλιώς οι σελίδες ξεχαρβαλώνουν
PIED    = 40

# Το χαρτί μένει λευκό. Χρώμα υπάρχει ΜΟΝΟ στις δύο κουκκίδες των παικτών και
# σε δυο λεπτές γραμμές — ένα τεύχος 42 σελίδων τυπώνεται σε εταιρικό εκτυπωτή.
UN       = (0.157, 0.333, 0.502)   # παίκτης ①
DEUX     = (0.118, 0.478, 0.298)   # παίκτης ②
NOIR     = (0.106, 0.141, 0.188)
GRIS     = (0.42, 0.46, 0.51)
GRIS_L   = (0.84, 0.82, 0.79)
BLANC    = (1, 1, 1)

# Συμβατότητα με το build_pack.py
BLEU, VERT = UN, DEUX
BLEU_BG = VERT_BG = AMBRE_BG = (1, 1, 1)
AMBRE = GRIS

for nom, fichier in [("Jeu", "AlegreyaSans-Regular.ttf"),
                     ("Jeu-Bold", "AlegreyaSans-Bold.ttf"),
                     ("Jeu-Black", "AlegreyaSans-ExtraBold.ttf"),
                     ("Titre", "Comfortaa-Bold.ttf")]:
    pdfmetrics.registerFont(TTFont(nom, os.path.join(JEU, "fonts", fichier)))

REG, GRAS, NOIRE, TITRE = "Jeu", "Jeu-Bold", "Jeu-Black", "Titre"


def couleurs(qui):
    """Ο πρώτος ομιλητής της σκηνής είναι ο ① — ο ρόλος δεν είναι δεμένος με πρόσωπο."""
    return UN if qui == "papa" else DEUX


def numero(qui):
    return "1" if qui == "papa" else "2"


def entete(c, d, titre, sous_titre, langue):
    """Σταθερού ύψους, ώστε η πρώτη ατάκα να ξεκινά στο ίδιο y και στις δύο."""
    y = TOP
    # σήμα σκηνής: μόνο περίγραμμα
    c.setStrokeColorRGB(*GRIS_L)
    c.setLineWidth(1)
    c.roundRect(M, y - 44, 46, 46, 11, stroke=1, fill=0)
    c.setFillColorRGB(*NOIR)
    c.setFont(TITRE, 20)
    c.drawCentredString(M + 23, y - 30, "%02d" % d["id"])

    c.setFillColorRGB(*NOIR)
    c.setFont(TITRE, 25)
    c.drawString(M + 60, y - 24, titre)
    c.setFillColorRGB(*GRIS)
    c.setFont(REG, 12.5)
    c.drawString(M + 60, y - 41, sous_titre)

    c.setFillColorRGB(*GRIS)
    c.setFont(REG, 10)
    c.drawRightString(W - M - 46, y - 12, langue)

    # κυκλάκι για τη σφραγίδα, μόνο περίγραμμα
    c.setStrokeColorRGB(*GRIS_L)
    c.setLineWidth(1)
    c.circle(W - M - 15, y - 22, 15, stroke=1, fill=0)
    c.setFillColorRGB(*GRIS_L)
    c.setFont(REG, 12)
    c.drawCentredString(W - M - 15, y - 26, "✓")

    # ποιος παίζει τι: ο αριθμός είναι σταθερός, ο ρόλος όχι
    yr = y - 66
    x = M
    for qui in ("papa", "myrto"):
        coul = couleurs(qui)
        c.setFillColorRGB(*coul)
        c.circle(x + 6, yr + 4, 6, stroke=0, fill=1)
        c.setFillColorRGB(*BLANC)
        c.setFont(TITRE, 7)
        c.drawCentredString(x + 6, yr + 1.6, numero(qui))
        c.setFillColorRGB(*NOIR)
        c.setFont(REG, 10.5)
        etiquette = d["roles"][qui]
        c.drawString(x + 17, yr + 1, etiquette)
        x += 17 + pdfmetrics.stringWidth(etiquette, REG, 10.5) + 22
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
    largeur = W - 2 * M - 50
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

    for n, (ln, b) in enumerate(zip(d["lignes"], blocs), start=1):
        coul = couleurs(ln["qui"])
        h = b["h"]
        yc = y - taille * 0.72

        # αριθμός ατάκας: ο ίδιος αριστερά και δεξιά, ώστε να λες «γραμμή 12»
        c.setFillColorRGB(*GRIS)
        c.setFont(REG, taille * 0.6)
        c.drawRightString(M + 15, yc - taille * 0.18, str(n))

        # η μόνη κουκκίδα χρώματος της γραμμής
        c.setFillColorRGB(*coul)
        c.circle(M + 31, yc, 6.5, stroke=0, fill=1)
        c.setFillColorRGB(*BLANC)
        c.setFont(TITRE, 7)
        c.drawCentredString(M + 31, yc - 2.4, numero(ln["qui"]))

        c.setFillColorRGB(*NOIR)
        c.setFont(GRAS if ln["qui"] == "papa" else REG, taille)
        yy = y - taille * 0.28
        for bout in b[langue]:
            c.drawString(M + 46, yy - taille * 0.86, bout)
            yy -= inter
        y -= h + 5
        c.setStrokeColorRGB(*GRIS_L)
        c.setLineWidth(0.4)
        c.line(M + 46, y + 3, W - M, y + 3)

    # QR μόνο στη γαλλική: ανοίγει αυτή τη σκηνή στο κινητό, χωρίς ψάξιμο
    if not grec:
        code = qr.QrCodeWidget(URL + "#%02d" % d["id"], barLevel="M")
        b = code.getBounds()
        cote = 46
        dessin = Drawing(cote, cote,
                         transform=[cote / (b[2] - b[0]), 0, 0, cote / (b[3] - b[1]),
                                    -b[0] * cote / (b[2] - b[0]), -b[1] * cote / (b[3] - b[1])])
        dessin.add(code)
        renderPDF.draw(dessin, c, W - M - cote, M + 22)
        c.setFillColorRGB(*GRIS)
        c.setFont(REG, 7.5)
        c.drawCentredString(W - M - cote / 2, M + 13, "écoutez la scène")

    c.setStrokeColorRGB(*GRIS_L)
    c.setLineWidth(0.8)
    c.line(M, M + 78, W - M, M + 78)
    c.setFillColorRGB(*GRIS)
    c.setFont(REG, 10)
    c.drawString(M, M + 63,
                 "Ξαναπαίξτε τη σκηνή αλλάζοντας ρόλους: ο 1 γίνεται 2."
                 if grec else "Rejouez la scène en échangeant les rôles.")
    c.setFont(REG, 9)
    c.drawString(M, M + 48,
                 ("%d ατάκες · %s" if grec else "%d lignes · %s")
                 % (len(d["lignes"]), num_page))
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
