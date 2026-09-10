#!/usr/bin/env python3
"""Ηχογραφεί μία φορά κάθε ατάκα και τη βάζει στο web/audio/.

Το κλειδί είναι το hash του κειμένου, οπότε η επανεκτέλεση δεν ξαναφτιάχνει
τίποτα και οι επαναλήψεις («Bonjour, madame.») γράφονται μία φορά για όλες
τις σκηνές.

    python3 bin/build_audio.py             ό,τι λείπει
    python3 bin/build_audio.py --refaire   όλα από την αρχή
    VOIX=Jacques python3 bin/build_audio.py
"""
import glob, hashlib, json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
JEU  = os.path.dirname(HERE)
AUDIO = os.path.join(JEU, "web", "audio")
VOIX = os.environ.get("VOIX", "Thomas")


def cle(txt):
    return hashlib.sha1(txt.encode("utf-8")).hexdigest()[:12]


def dit(txt, sortie):
    """macOS `say` -> aiff -> aac. Σε Linux δοκιμάζει piper, μετά espeak-ng."""
    with tempfile.NamedTemporaryFile(suffix=".aiff", delete=False) as t:
        brut = t.name
    try:
        if sys.platform == "darwin":
            # Χωρίς --data-format: το say το απορρίπτει και γράφει άδειο αρχείο.
            subprocess.run(["say", "-v", VOIX, "-o", brut, txt], check=True)
            subprocess.run(["afconvert", brut, sortie, "-f", "m4af",
                            "-d", "aac", "-q", "127"], check=True,
                           stdout=subprocess.DEVNULL)
        else:
            subprocess.run(["espeak-ng", "-v", "fr", "-s", "150", "-w", brut, txt],
                           check=True)
            subprocess.run(["ffmpeg", "-y", "-i", brut, "-c:a", "aac", sortie],
                           check=True, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
    finally:
        os.path.exists(brut) and os.unlink(brut)


def main():
    refaire = "--refaire" in sys.argv
    os.makedirs(AUDIO, exist_ok=True)

    textes = []
    for f in sorted(glob.glob(os.path.join(JEU, "scenes", "*.json"))):
        for ln in json.load(open(f, encoding="utf-8"))["lignes"]:
            if ln["fr"] not in textes:
                textes.append(ln["fr"])

    index, neufs = {}, 0
    for txt in textes:
        k = cle(txt)
        index[txt] = k
        chemin = os.path.join(AUDIO, k + ".m4a")
        if refaire or not os.path.exists(chemin):
            dit(txt, chemin)
            neufs += 1
            print("  ♪ %s  %s" % (k, txt[:56]))

    with open(os.path.join(AUDIO, "index.json"), "w", encoding="utf-8") as fh:
        json.dump(index, fh, ensure_ascii=False, indent=1)

    total = sum(os.path.getsize(os.path.join(AUDIO, f))
                for f in os.listdir(AUDIO) if f.endswith(".m4a"))
    print("%d μοναδικές ατάκες (%d καινούριες) · φωνή %s · %.1f MB"
          % (len(textes), neufs, VOIX, total / 1e6))
    return 0


if __name__ == "__main__":
    sys.exit(main())
