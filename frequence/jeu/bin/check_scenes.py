#!/usr/bin/env python3
"""Το φράγμα. Απορρίπτει σκηνές που δεν είναι πραγματικά επιπέδου A1.

Ο κανόνας των δύο επιπέδων: κάθε λέξη κάθε ατάκας είναι είτε μέσα στον
σκελετό (πρώτες 1.200 του fr_50k), είτε μία από τις δηλωμένες λέξεις του
τόπου της σκηνής — που με τη σειρά τους πρέπει να είναι μέσα στις πρώτες
5.000 ή στα data/vaud.txt και data/noms_propres.txt.

Δεν υπάρχει σταθερό όριο λέξεων τόπου ανά σκηνή. Μετριούνται μόνο όσες
είναι πρωτοεμφανιζόμενες με τη σειρά της τράπουλας, και τυπώνεται η
κατανομή· το κατώφλι μπαίνει αφού δούμε πραγματικά νούμερα.

    python3 bin/check_scenes.py            έλεγχος όλων
    python3 bin/check_scenes.py --suggere  τυπώνει τι λείπει από mots_du_lieu
"""
import glob, json, os, re, sys, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
JEU  = os.path.dirname(HERE)
SRC  = os.path.dirname(JEU)

# Επιφωνήματα και ήχοι: aaah, oh, euh, mmm. Δεν είναι λεξιλόγιο.
ONOMATOPEE = re.compile(r"^(a+h*|o+h*|e+u+h*|h+m+|m+h*|ou+f*|b+r+)$")

MIN_LIGNES, MAX_LIGNES = 15, 20
MAX_MOTS_PAR_LIGNE = 12

# Τα μόρια της έκθλιψης: j', l', d', n', s', c', qu', m', t'
ELISIONS = {"j", "l", "d", "n", "s", "c", "t", "m", "qu", "y"}

# Χρόνοι εκτός A1 — τύποι που δεν επιτρέπονται
INTERDITS = {
    "fusse", "fusses", "fût", "eusse", "eusses", "eût",
    "serais", "serait", "serions", "seriez", "seraient",
    "aurais", "aurait", "aurions", "auriez", "auraient",
    "était", "étaient", "étais", "avait", "avaient", "avais",
    "serai", "seras", "sera", "serons", "serez", "seront",
    "aurai", "auras", "aura", "aurons", "aurez", "auront",
}
# Οι μόνες παγιωμένες εξαιρέσεις δυνητικής
TOLERES = {"voudrais", "voudrait", "aimerais", "aimerait", "pourriez", "pourrais",
           "pourrait", "c'était", "était"}

# Γαλλικά της Γαλλίας που στο Βω είναι λάθος
SUISSE = {
    "soixante-dix": "septante", "quatre-vingt-dix": "nonante",
    "quatre-vingts": "huitante", "quatre-vingt": "huitante",
    "portable": "natel",
}


def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def tokens(txt):
    """Σπάει σε λέξεις, χωρίζοντας στις αποστρόφους και στα ενωτικά."""
    txt = txt.replace("’", "'")
    return [t for t in re.split(r"[^A-Za-zÀ-ÿ]+", txt.lower()) if t]


def load_list(name):
    p = os.path.join(JEU, "data", name)
    if not os.path.exists(p):
        return set()
    out = set()
    for line in open(p, encoding="utf-8"):
        line = line.split("#")[0].strip()
        if line:
            out.add(line.lower())
    return out


def main():
    suggere = "--suggere" in sys.argv
    lex = json.load(open(os.path.join(JEU, "data", "lexique.json"), encoding="utf-8"))
    rangs, SKEL, LARGE = lex["rangs"], lex["squelette"], lex["large"]
    formes = set(lex.get("formes", []))
    vaud, propres = load_list("vaud.txt"), load_list("noms_propres.txt")
    nombres = load_list("nombres.txt")
    permis_hors = vaud | propres | nombres

    atteste = set()
    with open(os.path.join(SRC, "fr_50k.txt"), encoding="utf-8") as fh:
        for line in fh:
            p = line.split()
            if p:
                atteste.add(p[0])

    fichiers = sorted(glob.glob(os.path.join(JEU, "scenes", "*.json")))
    if not fichiers:
        print("καμία σκηνή στο scenes/"); return 1

    erreurs, vus, stats = [], set(), []

    for f in fichiers:
        nom = os.path.basename(f)
        d = json.load(open(f, encoding="utf-8"))
        E = lambda m: erreurs.append("%s: %s" % (nom, m))
        lieu = {w.lower() for w in d.get("mots_du_lieu", [])}

        n = len(d.get("lignes", []))
        if not (MIN_LIGNES <= n <= MAX_LIGNES):
            E("%d ατάκες, εκτός %d–%d" % (n, MIN_LIGNES, MAX_LIGNES))

        # οι λέξεις τόπου πρέπει να δικαιολογούνται
        # Οι λέξεις τόπου δεν κρίνονται από συχνότητα — το «croissant» είναι
        # στη θέση 14.652 και είναι απολύτως σωστό σε φούρνο. Κρίνονται από το
        # αν είναι υπαρκτές γαλλικές λέξεις: πρέπει να μαρτυρούνται κάπου μέσα
        # στις 50.000 του καταλόγου, ή να είναι στις χειρόγραφες λίστες.
        for w in sorted(lieu):
            if w not in permis_hors and w not in atteste:
                E("λέξη τόπου που δεν μαρτυρείται στον κατάλογο 50k: %s" % w)

        hors = set()
        for i, ln in enumerate(d.get("lignes", []), 1):
            fr, el = ln.get("fr", ""), ln.get("el", "")
            if not el.strip():
                E("ατάκα %d χωρίς ελληνική μετάφραση" % i)
            if ln.get("qui") not in ("papa", "myrto"):
                E("ατάκα %d: άγνωστος ομιλητής %r" % (i, ln.get("qui")))

            mots = tokens(fr)
            if len(mots) > MAX_MOTS_PAR_LIGNE:
                E("ατάκα %d: %d λέξεις (όριο %d) — %s" % (i, len(mots), MAX_MOTS_PAR_LIGNE, fr))

            plat = strip_accents(fr.lower())
            for fx, bon in SUISSE.items():
                if strip_accents(fx) in plat:
                    E("ατάκα %d: «%s» — στο Βω λέγεται «%s»" % (i, fx, bon))

            for m in mots:
                if m in ELISIONS or len(m) == 1 or ONOMATOPEE.match(m):
                    continue
                if m in INTERDITS and m not in TOLERES:
                    E("ατάκα %d: χρόνος εκτός A1 — %s" % (i, m))
                if m in lieu or m in permis_hors:
                    continue
                if rangs.get(m, 10 ** 9) <= SKEL or m in formes:
                    continue
                hors.add(m)

        if hors:
            if suggere:
                print("%s → πρόσθεσε στο mots_du_lieu: %s" % (nom, ", ".join(sorted(hors))))
            else:
                for w in sorted(hors):
                    r = rangs.get(w)
                    E("εκτός σκελετού και αδήλωτη: %s (θέση %s)" % (w, r if r else "εκτός 5.000"))

        neufs = sorted(lieu - vus)
        vus |= lieu
        stats.append((nom, len(lieu), len(neufs)))

    print("\nΛέξεις τόπου με τη σειρά της τράπουλας")
    print("%-34s %8s %10s" % ("σκηνή", "σύνολο", "καινούριες"))
    for nom, tot, neuf in stats:
        print("%-34s %8d %10d" % (nom, tot, neuf))
    med = sorted(s[2] for s in stats)[len(stats) // 2]
    print("διάμεσος καινούριων: %d" % med)

    if erreurs:
        print("\n%d σφάλματα:" % len(erreurs))
        for e in erreurs:
            print("  ✗ " + e)
        return 1
    print("\n✓ %d σκηνές, όλες περνούν" % len(fichiers))
    return 0


if __name__ == "__main__":
    sys.exit(main())
