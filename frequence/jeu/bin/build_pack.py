#!/usr/bin/env python3
"""Το τυπώσιμο τεύχος, σελιδοποιημένο για εκτύπωση διπλής όψης.

Ο κανόνας που πρέπει να ισχύει στο τυπωμένο: **κάθε άνοιγμα δείχνει τα γαλλικά
αριστερά και τα ελληνικά δεξιά**. Σε τεύχος διπλής όψης, η αριστερή σελίδα ενός
ανοίγματος είναι η ΠΙΣΩ όψη του προηγούμενου φύλλου και η δεξιά η ΜΠΡΟΣΤΙΝΗ του
επόμενου. Άρα:

    σελίδα 1        εξώφυλλο            (μπροστά φύλλου 1)
    σελίδα 2        σκηνή 01 γαλλικά    (πίσω φύλλου 1)   ┐ άνοιγμα 1
    σελίδα 3        σκηνή 01 ελληνικά   (μπροστά φύλλου 2)┘
    σελίδα 4        σκηνή 02 γαλλικά    (πίσω φύλλου 2)   ┐ άνοιγμα 2
    σελίδα 5        σκηνή 02 ελληνικά   (μπροστά φύλλου 3)┘
    ...
    σελίδα 42       οδηγίες παιχνιδιού  (πίσω φύλλου 21)

Δηλαδή: **ζυγή σελίδα = γαλλικά, μονή = ελληνικά**, με το εξώφυλλο να κάνει τη
μετατόπιση. Το `--verifie` το ελέγχει και σκάει αν χαλάσει.

    python3 bin/build_pack.py            -> <blog>/cartes/cartes-du-soir.pdf
    python3 bin/build_pack.py --verifie   επιβεβαιώνει τη σελιδοποίηση
"""
import glob, importlib.util, json, os, sys

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

HERE = os.path.dirname(os.path.abspath(__file__))
JEU  = os.path.dirname(HERE)
BLOG = os.path.dirname(os.path.dirname(JEU))

spec = importlib.util.spec_from_file_location("cartes", os.path.join(HERE, "build_cards.py"))
K = importlib.util.module_from_spec(spec)
spec.loader.exec_module(K)

W, H = A4
M = K.M


def couverture(c, scenes):
    # τίτλος
    c.setFillColorRGB(*K.NOIR)
    c.setFont(K.TITRE, 42)
    c.drawString(M, H - 152, "Cartes du Soir")
    c.setFillColorRGB(*K.VERT)
    c.setFont(K.REG, 22)
    c.drawString(M, H - 180, "Οι κάρτες του βραδιού")
    c.setStrokeColorRGB(*K.AMBRE)
    c.setLineWidth(2.4)
    c.line(M, H - 198, W - M, H - 198)

    # πλαίσιο με τους ρόλους, στα χρώματα του παιχνιδιού
    y = H - 226
    c.setFillColorRGB(*K.AMBRE_BG)
    c.roundRect(M, y - 92, W - 2 * M, 92, 12, stroke=0, fill=1)
    c.setFillColorRGB(*K.NOIR)
    c.setFont(K.REG, 13)
    c.drawString(M + 20, y - 26, "Δέκα λεπτά γαλλικά πριν τον ύπνο, για δύο παίκτες.")
    for i, (coul, fond, qui, texte) in enumerate([
        (K.VERT, K.VERT_BG, "ΜΥΡΤΩ", "παίζει πάντα τη ντόπια — τη φούρναρη, τη δασκάλα, τη γιατρό."),
        (K.BLEU, K.BLEU_BG, "ΜΠΑΜΠΑΣ", "παίζει πάντα τον νεοφερμένο που δεν ξέρει ακόμα γαλλικά."),
    ]):
        yy = y - 50 - i * 24
        c.setFillColorRGB(*fond)
        larg = pdfmetrics.stringWidth(qui, K.REG, 10.5) + 26
        c.roundRect(M + 20, yy - 5, larg, 18, 9, stroke=0, fill=1)
        c.setFillColorRGB(*coul)
        c.circle(M + 31, yy + 4, 4, stroke=0, fill=1)
        c.setFont(K.REG, 10.5)
        c.drawString(M + 40, yy + 1, qui)
        c.setFillColorRGB(*K.GRIS)
        c.setFont(K.REG, 12)
        c.drawString(M + 20 + larg + 10, yy + 1, texte)

    y -= 116
    c.setFillColorRGB(*K.GRIS)
    c.setFont(K.REG, 12.5)
    for ligne in [
        "Σε κάθε άνοιγμα: αριστερά ο διάλογος στα γαλλικά, δεξιά τι σημαίνει.",
        "Οι δύο σελίδες έχουν ακριβώς την ίδια διάταξη — η τρίτη ατάκα είναι στο ίδιο ύψος.",
        "Η προφορά ακούγεται στο petmakris.github.io/cartes",
    ]:
        c.drawString(M, y, ligne)
        y -= 19

    # περιεχόμενα, με σήμα σκηνής όπως μέσα
    y -= 14
    c.setFillColorRGB(*K.NOIR)
    c.setFont(K.TITRE, 14)
    c.drawString(M, y, "Οι σκηνές")
    y -= 22

    moitie = (len(scenes) + 1) // 2
    col_w = (W - 2 * M) / 2
    for i, d in enumerate(scenes):
        x = M + (col_w if i >= moitie else 0)
        yy = y - (i % moitie) * 20
        c.setFillColorRGB(*K.AMBRE_BG)
        c.roundRect(x, yy - 4, 20, 16, 5, stroke=0, fill=1)
        c.setFillColorRGB(*K.AMBRE)
        c.setFont(K.TITRE, 8.5)
        c.drawCentredString(x + 10, yy + 0.5, "%02d" % d["id"])
        c.setFillColorRGB(*K.NOIR)
        c.setFont(K.REG, 12)
        c.drawString(x + 27, yy, d["titre_fr"])
        c.setFillColorRGB(*K.GRIS)
        c.setFont(K.REG, 9.5)
        c.drawRightString(x + col_w - 16, yy, "σελ. %d" % (2 + 2 * i))

    c.setFillColorRGB(*K.GRIS)
    c.setFont(K.REG, 10)
    c.drawString(M, M + 12, "Τύπωσε διπλής όψης, δέσιμο στη μεγάλη πλευρά.")
    c.drawRightString(W - M, M + 12, "%d σκηνές · %d σελίδες" % (len(scenes), 2 + 2 * len(scenes)))
    c.showPage()


def fin(c):
    c.setFillColorRGB(*K.NOIR)
    c.setFont(K.TITRE, 28)
    c.drawString(M, H - 132, "Πώς παίζεται")
    c.setStrokeColorRGB(*K.AMBRE)
    c.setLineWidth(2.4)
    c.line(M, H - 152, W - M, H - 152)

    y = H - 190
    for n, (titre, texte) in enumerate([
        ("Η Μυρτώ διαλέγει",
         "Τραβάει μια σκηνή, διαβάζει τον τίτλο, και λέει στον μπαμπά ποιος είναι απόψε."),
        ("Ακούστε πρώτα",
         "Στο petmakris.github.io/cartes, πατήστε τις ατάκες που δεν σας βγαίνουν."),
        ("Παίξτε τη σκηνή",
         "Ο μπαμπάς λέει τις μπλε, η Μυρτώ τις πράσινες. Η δεξιά σελίδα εξηγεί."),
        ("Εκείνη κρίνει",
         "Μία απόφαση στο τέλος: πέρασε, ή ξανά αύριο. Είναι η αυθεντία και το ξέρει."),
        ("Η σφραγίδα",
         "Μια σκηνή που πέρασε σφραγίζεται. Τίποτα άλλο δεν μετριέται, κανείς δεν κερδίζει."),
    ], start=1):
        c.setFillColorRGB(*K.AMBRE_BG)
        c.circle(M + 13, y + 4, 13, stroke=0, fill=1)
        c.setFillColorRGB(*K.AMBRE)
        c.setFont(K.TITRE, 12)
        c.drawCentredString(M + 13, y, str(n))
        c.setFillColorRGB(*K.NOIR)
        c.setFont(K.TITRE, 13.5)
        c.drawString(M + 36, y + 4, titre)
        c.setFillColorRGB(*K.GRIS)
        c.setFont(K.REG, 12)
        c.drawString(M + 36, y - 13, texte)
        y -= 54

    c.setFillColorRGB(*K.GRIS)
    c.setFont(K.REG, 10)
    c.drawString(M, M + 12, "Το λεξιλόγιο βγαίνει από τις 1.200 συχνότερες γαλλικές λέξεις.")
    c.drawRightString(W - M, M + 12, "Cartes du Soir · Vaud")
    c.showPage()


def main():
    fichiers = sorted(glob.glob(os.path.join(JEU, "scenes", "*.json")))
    if not fichiers:
        print("δεν υπάρχουν σκηνές")
        return 1
    scenes = [json.load(open(f, encoding="utf-8")) for f in fichiers]

    os.makedirs(os.path.join(BLOG, "cartes"), exist_ok=True)
    out = os.path.join(BLOG, "cartes", "cartes-du-soir.pdf")
    c = canvas.Canvas(out, pagesize=A4)
    c.setTitle("Cartes du Soir — τεύχος για εκτύπωση διπλής όψης")

    ordre = []                       # τι είναι κάθε σελίδα, για την επαλήθευση
    couverture(c, scenes)
    ordre.append("couverture")
    for i, d in enumerate(scenes):
        gauche = 2 + 2 * i
        K.page_dialogue(c, d, num_page="σελ. %d" % gauche)
        ordre.append("fr")
        K.page_sens(c, d, num_page="σελ. %d" % (gauche + 1))
        ordre.append("el")
    fin(c)
    ordre.append("fin")
    c.save()

    # Ο κανόνας: ζυγή σελίδα γαλλικά, μονή ελληνικά. Σκάει αν χαλάσει.
    for n, quoi in enumerate(ordre, start=1):
        if quoi == "fr" and n % 2 != 0:
            raise SystemExit("ΣΕΛΙΔΟΠΟΙΗΣΗ: γαλλικά σε μονή σελίδα %d" % n)
        if quoi == "el" and n % 2 == 0:
            raise SystemExit("ΣΕΛΙΔΟΠΟΙΗΣΗ: ελληνικά σε ζυγή σελίδα %d" % n)

    print("%s · %d σκηνές, %d σελίδες (%d φύλλα διπλής όψης), %.0f KB"
          % (out, len(scenes), len(ordre), (len(ordre) + 1) // 2,
             os.path.getsize(out) / 1024))
    print("ανοίγματα: γαλλικά σελ. %s | ελληνικά σελ. %s  …και ούτω καθεξής"
          % (2, 3))
    return 0


if __name__ == "__main__":
    sys.exit(main())
