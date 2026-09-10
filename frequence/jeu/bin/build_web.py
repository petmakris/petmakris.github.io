#!/usr/bin/env python3
"""Ψήνει τη σελίδα προφοράς σε ένα αυτοτελές web/index.html.

Ένα αρχείο, όλα τα δεδομένα μέσα του, ο ήχος δίπλα στο web/audio/.
Ανοίγει στο κινητό δίπλα στις κάρτες: κάθε ατάκα πατιέται και ακούγεται.
"""
import base64, glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
JEU  = os.path.dirname(HERE)
BLOG = os.path.dirname(os.path.dirname(JEU))
# Η ενότητα του blog είναι ο ΜΟΝΟΣ τόπος του παραγόμενου: ό,τι χτίζεται
# σερβίρεται κατευθείαν από το GitHub Pages, χωρίς δεύτερο αντίγραφο του ήχου.
SECTION = os.path.join(BLOG, "cartes")

GABARIT = """<!doctype html>
<html lang="el">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#1b2430">
<title>Cartes du Soir</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><text y='26' font-size='26'>&#127856;</text></svg>">
<style>
:root{
  --paper:#fbf9f4; --card:#fff; --ink:#1b2430; --ink2:#55606f; --ink3:#8b93a0;
  --rule:#e4ded1; --rule2:#d6cfbe;
  --vaud:#1e7a4c; --vaud-bg:#e8f1ea; --vaud-line:#bfdccb;
  --bleu:#2a5580; --bleu-bg:#e7edf4;
  --serif:Georgia,"Times New Roman",serif;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){--paper:#12161d; --card:#1a1f28; --ink:#e9e5dc; --ink2:#a5aebb; --ink3:#6e7784;
    --rule:#2b323e; --rule2:#39414f; --vaud:#5fc28c; --vaud-bg:#16281f; --vaud-line:#2c4a38;
    --bleu:#89b4e0; --bleu-bg:#141f2c;}
}
:root[data-theme="dark"]{
  --paper:#12161d; --card:#1a1f28; --ink:#e9e5dc; --ink2:#a5aebb; --ink3:#6e7784;
  --rule:#2b323e; --rule2:#39414f; --vaud:#5fc28c; --vaud-bg:#16281f; --vaud-line:#2c4a38;
  --bleu:#89b4e0; --bleu-bg:#141f2c;
}
*{box-sizing:border-box; -webkit-tap-highlight-color:transparent}
body{margin:0; background:var(--paper); color:var(--ink); font-family:var(--sans);
  font-size:17px; line-height:1.5; padding-bottom:env(safe-area-inset-bottom)}
header{position:sticky; top:0; z-index:5; background:var(--paper);
  border-bottom:1px solid var(--rule); padding:14px 18px 12px;
  padding-top:calc(14px + env(safe-area-inset-top))}
.sc{font-size:11px; letter-spacing:.12em; color:var(--ink3); font-family:var(--sans)}
h1{font-family:var(--serif); font-size:24px; font-weight:700; margin:2px 0 0; line-height:1.15}
h1 small{display:block; font-family:var(--sans); font-size:13px; font-weight:400;
  color:var(--ink3); margin-top:3px; letter-spacing:0}
.bar{display:flex; gap:7px; margin-top:11px; flex-wrap:wrap; align-items:center}
.bar button{font:inherit; font-size:13px; padding:6px 13px; border-radius:15px;
  border:1px solid var(--rule2); background:transparent; color:var(--ink3); cursor:pointer}
.bar button[aria-pressed="true"]{background:var(--vaud-bg); border-color:var(--vaud); color:var(--vaud)}
.bar .back{margin-inline-end:auto; border-color:transparent; color:var(--vaud); padding-inline:0}
main{padding:0 0 40px}
.scenes{padding:8px 18px}
.item{display:block; width:100%; text-align:start; background:var(--card); color:inherit;
  border:1px solid var(--rule); border-radius:9px; padding:15px 17px; margin:10px 0;
  font:inherit; cursor:pointer}
.item b{display:block; font-family:var(--serif); font-size:21px; font-weight:700; line-height:1.2}
.item i{display:block; font-style:normal; font-size:14px; color:var(--ink3); margin-top:3px}
.item u{display:block; text-decoration:none; font-size:12px; color:var(--vaud); margin-top:7px}
.ln{display:flex; gap:13px; align-items:flex-start; width:100%; text-align:start;
  background:transparent; border:0; border-bottom:1px solid var(--rule);
  padding:14px 18px; font:inherit; color:inherit; cursor:pointer}
.ln:last-child{border-bottom:0}
.ln.papa{border-left:3px solid var(--bleu); background:var(--bleu-bg)}
.ln.myrto{border-left:3px solid var(--vaud-line)}
.ln .ic{flex:0 0 auto; width:29px; height:29px; border-radius:50%; margin-top:2px;
  border:1px solid var(--vaud-line); background:var(--vaud-bg); color:var(--vaud);
  display:grid; place-items:center; font-size:10px}
.ln .who{position:absolute; opacity:0; pointer-events:none}
.ln .t{font-family:var(--serif); font-size:19px; line-height:1.32; display:block}
.ln.papa .t{font-weight:700; color:var(--ink)}
.ln.myrto .t{font-weight:400; color:var(--ink2)}
.ln .m{display:none; font-size:13.5px; color:var(--ink3); margin-top:3px; line-height:1.4}
body.sens .ln .m{display:block}
.ln.on{background:var(--vaud-bg); border-left-color:var(--vaud)}
.ln.on .ic{background:var(--vaud); color:#fff; border-color:var(--vaud)}
.roles{padding:12px 18px 4px; font-size:13px; color:var(--ink3)}
.roles span{display:inline-flex; align-items:center; gap:6px; margin-inline-end:14px}
.dot{width:9px; height:9px; border-radius:50%}
.dot.p{background:var(--bleu)} .dot.m{background:var(--vaud)}
footer{padding:26px 18px 40px; color:var(--ink3); font-size:12.5px; line-height:1.7;
  border-top:1px solid var(--rule); margin-top:24px}
footer a{color:var(--vaud)}
[hidden]{display:none!important}
</style>
</head>
<body>
<header>
  <div class="sc">CARTES DU SOIR</div>
  <h1 id="titre">Οι κάρτες του βραδιού<small id="soustitre">Πάτα μια σκηνή</small></h1>
  <div class="bar" id="bar" hidden>
    <button type="button" class="back" id="back">&#8592; Σκηνές</button>
    <button type="button" id="lent" aria-pressed="false">Αργά</button>
    <button type="button" id="sens" aria-pressed="false">Τι σημαίνει</button>
  </div>
</header>
<main>
  <div class="scenes" id="liste"></div>
  <div id="scene" hidden></div>
</main>
<footer>
  Ο ήχος είναι ηχογραφημένος από πριν, μία φορά ανά ατάκα, μία φωνή ανά ρόλο.<br>
  <a href="cartes-du-soir.pdf">Τύπωσε τις κάρτες</a> — τρεις σελίδες ανά σκηνή.
  Αυτή η σελίδα δεν αντικαθιστά το χαρτί· λέει μόνο την προφορά.
</footer>
<script>
const SCENES = __DONNEES__;
const AUDIO  = __INDEX__;
const SONS   = __SONS__;   // κενό όταν ο ήχος είναι δίπλα σε αρχεία
const SRC = c => SONS[c] ? 'data:audio/mp4;base64,' + SONS[c] : 'audio/' + c + '.m4a';

const liste = document.getElementById('liste');
const vue   = document.getElementById('scene');
const bar   = document.getElementById('bar');
const titre = document.getElementById('titre');
const sous  = document.getElementById('soustitre');
let lent = false, encours = null, courant = null;

function esc(s){ return s.replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }

SCENES.forEach((s, i) => {
  const b = document.createElement('button');
  b.className = 'item'; b.type = 'button';
  b.innerHTML = '<b>' + esc(s.titre_fr) + '</b><i>' + esc(s.titre_el) + '</i>' +
                '<u>' + s.lignes.length + ' ατάκες · ' + esc(s.roles.myrto) + ' / ' + esc(s.roles.papa) + '</u>';
  b.addEventListener('click', () => ouvre(i));
  liste.appendChild(b);
});

function ouvre(i){
  const s = SCENES[i];
  courant = i;
  titre.firstChild.textContent = s.titre_fr;
  sous.textContent = s.titre_el;
  vue.innerHTML = '<div class="roles">' +
    '<span><i class="dot m"></i>ΜΥΡΤΩ — ' + esc(s.roles.myrto) + '</span>' +
    '<span><i class="dot p"></i>ΜΠΑΜΠΑΣ — ' + esc(s.roles.papa) + '</span></div>' +
    s.lignes.map(l =>
      '<button class="ln ' + l.qui + '" type="button" data-qui="' + l.qui +
      '" data-fr="' + esc(l.fr) + '">' +
        '<span class="ic">&#9654;</span>' +
        '<span><span class="t">' + esc(l.fr) + '</span>' +
        '<span class="m">' + esc(l.el) + '</span></span></button>').join('');
  liste.hidden = true; vue.hidden = false; bar.hidden = false;
  window.scrollTo(0, 0);
}

document.getElementById('back').addEventListener('click', () => {
  stop();
  titre.firstChild.textContent = 'Οι κάρτες του βραδιού';
  sous.textContent = 'Πάτα μια σκηνή';
  vue.hidden = true; bar.hidden = true; liste.hidden = false;
});

function bascule(id, fn){
  const b = document.getElementById(id);
  b.addEventListener('click', () => {
    const on = b.getAttribute('aria-pressed') !== 'true';
    b.setAttribute('aria-pressed', on ? 'true' : 'false');
    fn(on);
  });
}
bascule('lent', on => { lent = on; if (encours) encours.playbackRate = on ? 0.72 : 1; });
bascule('sens', on => document.body.classList.toggle('sens', on));

function stop(){
  if (encours){ encours.pause(); encours = null; }
  document.querySelectorAll('.ln.on').forEach(e => e.classList.remove('on'));
}

vue.addEventListener('click', e => {
  const btn = e.target.closest('.ln');
  if (!btn) return;
  const etait = btn.classList.contains('on');
  stop();
  if (etait) return;
  const cle = AUDIO[btn.dataset.qui + '|' + btn.dataset.fr];
  if (!cle) return;
  const a = new Audio(SRC(cle));
  a.playbackRate = lent ? 0.72 : 1;
  btn.classList.add('on');
  a.addEventListener('ended', () => { btn.classList.remove('on'); encours = null; });
  a.addEventListener('error', () => { btn.classList.remove('on'); encours = null; });
  encours = a;
  a.play().catch(() => { btn.classList.remove('on'); encours = null; });
});
</script>
</body>
</html>
"""


def main():
    scenes = []
    for f in sorted(glob.glob(os.path.join(JEU, "scenes", "*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        scenes.append({k: d[k] for k in
                       ("id", "slug", "titre_fr", "titre_el", "roles", "lignes")})

    idx_path = os.path.join(SECTION, "audio", "index.json")
    index = json.load(open(idx_path, encoding="utf-8")) if os.path.exists(idx_path) else {}

    # --embarque: ο ήχος μπαίνει μέσα στο HTML ως data URI, ώστε η σελίδα να
    # είναι ΕΝΑ αρχείο που ανοίγει από παντού — για δοκιμή με σκέτο link.
    sons = {}
    if "--embarque" in sys.argv:
        for c in set(index.values()):
            p = os.path.join(SECTION, "audio", c + ".m4a")
            if os.path.exists(p):
                sons[c] = base64.b64encode(open(p, "rb").read()).decode("ascii")

    html = (GABARIT
            .replace("__DONNEES__", json.dumps(scenes, ensure_ascii=False))
            .replace("__INDEX__", json.dumps(index, ensure_ascii=False))
            .replace("__SONS__", json.dumps(sons)))

    if "--embarque" in sys.argv:
        os.makedirs(os.path.join(JEU, "out"), exist_ok=True)
        out = os.path.join(JEU, "out", "autonome.html")
    else:
        os.makedirs(SECTION, exist_ok=True)
        out = os.path.join(SECTION, "index.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)

    manquants = [l["fr"] for s in scenes for l in s["lignes"]
                 if (l["qui"] + "|" + l["fr"]) not in index]
    if manquants:
        print("προσοχή: %d ατάκες χωρίς ήχο (τρέξε build_audio.py)" % len(manquants))
    print("%s · %d σκηνές, %d ατάκες, %d ήχοι μέσα, %.1f MB"
          % (out, len(scenes), sum(len(s["lignes"]) for s in scenes),
             len(sons), len(html) / 1e6))
    return 0


if __name__ == "__main__":
    sys.exit(main())
