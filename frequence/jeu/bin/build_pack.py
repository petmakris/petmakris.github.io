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
    c.setFillColorRGB(*K.NOIR)
    c.setFont(K.GRAS, 44)
    c.drawString(M, H - 150, "Cartes du Soir")
    c.setFillColorRGB(*K.VERT)
    c.setFont(K.REG, 21)
    c.drawString(M, H - 182, "Οι κάρτες του βραδιού")

    c.setStrokeColorRGB(*K.NOIR)
    c.setLineWidth(1.6)
    c.line(M, H - 204, W - M, H - 204)

    c.setFillColorRGB(*K.GRIS)
    c.setFont(K.REG, 12.5)
    y = H - 234
    for ligne in [
        "Δέκα λεπτά γαλλικά πριν τον ύπνο, για δύο παίκτες.",
        "Η ΜΥΡΤΩ παίζει πάντα τη ντόπια — τη φούρναρη, τη δασκάλα, τη γιατρό.",
        "Ο ΜΠΑΜΠΑΣ παίζει πάντα τον νεοφερμένο που δεν ξέρει ακόμα γαλλικά.",
        "",
        "Σε κάθε άνοιγμα: αριστερά ο διάλογος στα γαλλικά, δεξιά τι σημαίνει.",
        "Οι μπλε έντονες ατάκες είναι του μπαμπά, οι πράσινες της Μυρτώς.",
        "",
        "Η προφορά ακούγεται στο petmakris.github.io/cartes",
    ]:
        c.drawString(M, y, ligne)
        y -= 19

    c.setFillColorRGB(*K.NOIR)
    c.setFont(K.GRAS, 13)
    y -= 16
    c.drawString(M, y, "Οι σκηνές")
    y -= 8
    c.setLineWidth(0.5)
    c.setStrokeColorRGB(*K.GRIS_L)
    c.line(M, y, W - M, y)
    y -= 20

    col_w = (W - 2 * M) / 2
    for i, d in enumerate(scenes):
        x = M + (col_w if i >= (len(scenes) + 1) // 2 else 0)
        yy = y - (i % ((len(scenes) + 1) // 2)) * 17
        c.setFillColorRGB(*K.GRIS)
        c.setFont(K.REG, 9.5)
        c.drawString(x, yy, "%02d" % d["id"])
        c.setFillColorRGB(*K.NOIR)
        c.setFont(K.REG, 11.5)
        c.drawString(x + 20, yy, d["titre_fr"])
        c.setFillColorRGB(*K.GRIS)
        c.setFont(K.REG, 9.5)
        c.drawRightString(x + col_w - 16, yy, "σελ. %d" % (2 + 2 * i))

    c.setFillColorRGB(*K.GRIS)
    c.setFont(K.REG, 9.5)
    c.drawString(M, M + 12, "Τύπωσε διπλής όψης, δέσιμο στη μεγάλη πλευρά.")
    c.drawRightString(W - M, M + 12, "%d σκηνές · %d σελίδες" % (len(scenes), 2 + 2 * len(scenes)))
    c.showPage()


def fin(c):
    c.setFillColorRGB(*K.NOIR)
    c.setFont(K.GRAS, 26)
    c.drawString(M, H - 130, "Πώς παίζεται")
    c.setStrokeColorRGB(*K.NOIR)
    c.setLineWidth(1.6)
    c.line(M, H - 148, W - M, H - 148)

    y = H - 182
    for titre, texte in [
        ("1. Η Μυρτώ διαλέγει",
         "Τραβάει μια σκηνή, διαβάζει τον τίτλο, και λέει στον μπαμπά ποιος είναι απόψε."),
        ("2. Ακούστε πρώτα",
         "Στο petmakris.github.io/cartes, πατήστε τις ατάκες που δεν σας βγαίνουν."),
        ("3. Παίξτε τη σκηνή",
         "Ο μπαμπάς λέει τις μπλε, η Μυρτώ τις πράσινες. Η δεξιά σελίδα εξηγεί."),
        ("4. Εκείνη κρίνει",
         "Μία απόφαση στο τέλος: πέρασε, ή ξανά αύριο. Είναι η αυθεντία και το ξέρει."),
        ("5. Η σφραγίδα",
         "Μια σκηνή που πέρασε σφραγίζεται. Τίποτα άλλο δεν μετριέται, κανείς δεν κερδίζει."),
    ]:
        c.setFillColorRGB(*K.VERT)
        c.setFont(K.GRAS, 13)
        c.drawString(M, y, titre)
        c.setFillColorRGB(*K.GRIS)
        c.setFont(K.REG, 11.5)
        c.drawString(M + 14, y - 17, texte)
        y -= 48

    c.setFillColorRGB(*K.GRIS)
    c.setFont(K.REG, 9.5)
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
