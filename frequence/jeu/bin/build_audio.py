#!/usr/bin/env python3
"""Ηχογραφεί μία φορά κάθε ατάκα και τη βάζει στο web/audio/.

Δύο μηχανές:

    TTS=gemini   Gemini 2.5 TTS — η καλή. Θέλει GEMINI_API_KEY.
    TTS=say      macOS `say` — η φθηνή εφεδρεία, χωρίς κλειδί.

Δύο φωνές, μία ανά ρόλο, ώστε η σκηνή να ακούγεται σαν συνομιλία και όχι σαν
λίστα. Το κλειδί του αρχείου είναι hash της φωνής μαζί με το κείμενο, οπότε η
επανεκτέλεση δεν ξαναφτιάχνει τίποτα και οι επαναλήψεις γράφονται μία φορά.

    python3 bin/build_audio.py                  ό,τι λείπει
    python3 bin/build_audio.py --refaire        όλα από την αρχή
    python3 bin/build_audio.py --essai          μία ατάκα, για έλεγχο
"""
import base64, glob, hashlib, json, os, struct, subprocess, sys, tempfile, time
import urllib.request, urllib.error

HERE  = os.path.dirname(os.path.abspath(__file__))
JEU   = os.path.dirname(HERE)
BLOG  = os.path.dirname(os.path.dirname(JEU))
AUDIO = os.path.join(BLOG, "cartes", "audio")

MOTEUR = os.environ.get("TTS", "gemini").lower()
MODELE = os.environ.get("TTS_MODEL", "gemini-2.5-pro-preview-tts")

# Μία φωνή ανά ρόλο. Οι φωνές του Gemini δεν είναι δεμένες με γλώσσα.
VOIX_GEMINI = {"myrto": os.environ.get("VOIX_MYRTO", "Kore"),
               "papa":  os.environ.get("VOIX_PAPA",  "Charon")}
VOIX_SAY    = {"myrto": os.environ.get("VOIX_MYRTO_SAY", "Flo (French (France))"),
               "papa":  os.environ.get("VOIX_PAPA_SAY",  "Thomas")}

URL = ("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent")

# Το κλειδί δεν μπαίνει ΠΟΤΕ μέσα στο checkout — αυτό το repo δημοσιεύεται στο
# GitHub Pages. Ζει σε αρχείο κατάστασης, όπως κάνουν και τα devdomains και το
# config-browser.
FICHIER_CLE = os.path.expanduser("~/.config/cartes-du-soir/gemini.key")


def cle_api():
    k = os.environ.get("GEMINI_API_KEY", "").strip()
    if k:
        return k
    if os.path.exists(FICHIER_CLE):
        return open(FICHIER_CLE, encoding="utf-8").read().strip()
    return ""


def cle(voix, txt):
    return hashlib.sha1((voix + "|" + txt).encode("utf-8")).hexdigest()[:12]


def wav(pcm, taux=24000):
    """Το Gemini γυρίζει γυμνό PCM 16-bit mono· του βάζουμε κεφαλίδα WAV."""
    return (b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVEfmt " +
            struct.pack("<IHHIIHH", 16, 1, 1, taux, taux * 2, 2, 16) +
            b"data" + struct.pack("<I", len(pcm)) + pcm)


def gemini(txt, voix, cle_api):
    corps = json.dumps({
        "contents": [{"parts": [{"text": txt}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voix}}},
        },
    }).encode("utf-8")
    req = urllib.request.Request(
        URL % MODELE + "?key=" + cle_api, data=corps,
        headers={"Content-Type": "application/json"})
    for essai in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                d = json.load(r)
            cand = (d.get("candidates") or [{}])[0]
            # Το μοντέλο απαντάει μερικές φορές με υποψήφιο ΧΩΡΙΣ content, όταν
            # έκοψε για δικούς του λόγους. Είναι παροδικό: ξαναδοκιμάζεται.
            if "content" not in cand:
                raise ValueError("χωρίς περιεχόμενο (finishReason=%s)"
                                 % cand.get("finishReason", "?"))
            return wav(base64.b64decode(cand["content"]["parts"][0]["inlineData"]["data"]))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            if e.code in (429, 500, 503) and essai < 3:
                time.sleep(3 * (essai + 1))
                continue
            raise SystemExit("Gemini %s: %s" % (e.code, detail))
        except Exception as e:
            if essai < 3:
                time.sleep(3 * (essai + 1))
                continue
            raise RuntimeError("Gemini: %s" % e)
    raise RuntimeError("Gemini: δεν απάντησε")


def vers_m4a(brut, sortie):
    subprocess.run(["ffmpeg", "-y", "-i", brut, "-c:a", "aac", "-b:a", "64k", sortie],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def dit(txt, qui, sortie, cle_api):
    with tempfile.NamedTemporaryFile(
            suffix=".wav" if MOTEUR == "gemini" else ".aiff", delete=False) as t:
        brut = t.name
    try:
        if MOTEUR == "gemini":
            open(brut, "wb").write(gemini(txt, VOIX_GEMINI[qui], cle_api))
        else:
            # Χωρίς --data-format: το say το απορρίπτει και γράφει άδειο αρχείο.
            subprocess.run(["say", "-v", VOIX_SAY[qui], "-o", brut, txt], check=True)
        vers_m4a(brut, sortie)
    finally:
        os.path.exists(brut) and os.unlink(brut)


def voix_de(qui):
    return (VOIX_GEMINI if MOTEUR == "gemini" else VOIX_SAY)[qui]


def main():
    refaire = "--refaire" in sys.argv
    essai   = "--essai" in sys.argv
    os.makedirs(AUDIO, exist_ok=True)

    kapi = cle_api()
    if MOTEUR == "gemini" and not kapi:
        raise SystemExit(
            "λείπει το κλειδί. Γράψ' το στο %s\n"
            "  mkdir -p ~/.config/cartes-du-soir\n"
            "  echo 'AIza…' > %s\n"
            "ή τρέξε με TTS=say για τη δωρεάν φωνή." % (FICHIER_CLE, FICHIER_CLE))

    # (κείμενο, ρόλος) — ίδια ατάκα από άλλο ρόλο θέλει άλλη φωνή
    atakes = []
    for f in sorted(glob.glob(os.path.join(JEU, "scenes", "*.json"))):
        for ln in json.load(open(f, encoding="utf-8"))["lignes"]:
            couple = (ln["fr"], ln["qui"])
            if couple not in atakes:
                atakes.append(couple)
    if essai:
        atakes = atakes[:1]

    index, neufs, rates = {}, 0, []
    for txt, qui in atakes:
        voix = voix_de(qui)
        k = cle(voix, txt)
        chemin = os.path.join(AUDIO, k + ".m4a")
        if refaire or not os.path.exists(chemin):
            try:
                dit(txt, qui, chemin, kapi)
            except Exception as e:
                # Συνεχίζουμε: 300 καλές ηχογραφήσεις δεν πετιούνται για μία κακή.
                rates.append((txt, qui, str(e)))
                print("  ✗ %-13s %-8s %s  (%s)" % (k, voix, txt[:44], e))
                continue
            neufs += 1
            print("  ♪ %-13s %-8s %s" % (k, voix, txt[:52]))
        # Στο ευρετήριο μπαίνει μόνο ό,τι υπάρχει πράγματι σε αρχείο.
        if os.path.exists(chemin):
            index[qui + "|" + txt] = k

    if not essai:
        with open(os.path.join(AUDIO, "index.json"), "w", encoding="utf-8") as fh:
            json.dump(index, fh, ensure_ascii=False, indent=1)

    total = sum(os.path.getsize(os.path.join(AUDIO, f))
                for f in os.listdir(AUDIO) if f.endswith(".m4a"))
    if rates:
        print("\n%d ατάκες ΑΠΕΤΥΧΑΝ — ξανατρέξε την ίδια εντολή:" % len(rates))
        for txt, qui, e in rates:
            print("  · %s [%s] %s" % (txt[:60], qui, e))
    print("%d ατάκες (%d καινούριες) · %s%s · %s / %s · %.1f MB"
          % (len(atakes), neufs, MOTEUR,
             " " + MODELE if MOTEUR == "gemini" else "",
             voix_de("myrto"), voix_de("papa"), total / 1e6))
    return 1 if rates else 0


if __name__ == "__main__":
    sys.exit(main())
