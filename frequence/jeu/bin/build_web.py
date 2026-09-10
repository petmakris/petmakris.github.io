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
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap">
<style>
:root{
  --paper:#fbf9f4; --card:#fff; --ink:#1b2430; --ink2:#55606f; --ink3:#8b93a0;
  --rule:#e4ded1; --rule2:#d6cfbe;
  --vaud:#1e7a4c; --vaud-bg:#e8f1ea; --vaud-line:#bfdccb;
  --bleu:#2a5580; --bleu-bg:#e7edf4; --bleu-line:#c3d3e4;
  --sans:"Inter",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  /* Μία κλίμακα για όλα τα μεγέθη: αλλάζει μία φορά ανά πλάτος οθόνης. */
  --t:19px;    /* η γαλλική ατάκα */
  --m:14px;    /* η ελληνική σημασία */
  --ic:30px;   /* το κουμπί αναπαραγωγής */
  --pad:16px;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){--paper:#12161d; --card:#1a1f28; --ink:#e9e5dc; --ink2:#a5aebb; --ink3:#6e7784;
    --rule:#2b323e; --rule2:#39414f; --vaud:#5fc28c; --vaud-bg:#16281f; --vaud-line:#2c4a38;
    --bleu:#89b4e0; --bleu-bg:#141f2c; --bleu-line:#2a3f55;}
}
:root[data-theme="dark"]{
  --paper:#12161d; --card:#1a1f28; --ink:#e9e5dc; --ink2:#a5aebb; --ink3:#6e7784;
  --rule:#2b323e; --rule2:#39414f; --vaud:#5fc28c; --vaud-bg:#16281f; --vaud-line:#2c4a38;
  --bleu:#89b4e0; --bleu-bg:#141f2c; --bleu-line:#2a3f55;
}
/* Τηλεόραση: από 1200 και πάνω όλα μεγαλώνουν μία φορά, και η σκηνή
   μοιράζεται σε δύο στήλες ώστε οι είκοσι ατάκες να χωράνε σε 1080 ύψος
   χωρίς κύλιση την ώρα του παιχνιδιού. */
@media (min-width:1200px){ :root{--t:25px; --m:17px; --ic:40px; --pad:26px} }
@media (min-width:1650px){ :root{--t:29px; --m:19px; --ic:46px; --pad:34px} }

*{box-sizing:border-box; -webkit-tap-highlight-color:transparent}
body{margin:0; background:var(--paper); color:var(--ink); font-family:var(--sans);
  font-size:17px; line-height:1.5; padding-bottom:env(safe-area-inset-bottom);
  font-feature-settings:"cv05","ss01"}
header{position:sticky; top:0; z-index:5; background:var(--paper);
  border-bottom:1px solid var(--rule); padding:14px var(--pad) 12px;
  padding-top:calc(14px + env(safe-area-inset-top))}
.hrow{display:flex; align-items:flex-end; gap:22px; flex-wrap:wrap;
  max-width:1760px; margin:0 auto; width:100%}
.sc{font-size:11px; letter-spacing:.14em; font-weight:600; color:var(--ink3)}
h1{font-size:calc(var(--t) * 1.15); font-weight:700; margin:1px 0 0; line-height:1.12;
  letter-spacing:-.02em}
h1 small{display:block; font-size:calc(var(--m) * .95); font-weight:400;
  color:var(--ink3); margin-top:2px; letter-spacing:0}
.bar{display:flex; gap:9px; flex-wrap:wrap; align-items:center; margin-inline-start:auto}
.bar button{font:inherit; font-family:var(--sans); font-weight:500;
  font-size:calc(var(--m) * .95); padding:9px 17px; border-radius:999px;
  border:1px solid var(--rule2); background:transparent; color:var(--ink2); cursor:pointer;
  transition:background .13s, border-color .13s, color .13s}
.bar button:hover{border-color:var(--vaud-line); color:var(--ink)}
.bar button[aria-pressed="true"]{background:var(--vaud-bg); border-color:var(--vaud);
  color:var(--vaud); font-weight:600}
.bar .back{margin-inline-end:auto; border-color:transparent; color:var(--vaud);
  padding-inline:4px; font-weight:600}
main{padding:0 var(--pad) 40px; max-width:1760px; margin:0 auto}

/* κατάλογος σκηνών: πλέγμα, όχι στήλη — στα 1920 μπαίνουν τέσσερις */
.scenes{display:grid; gap:14px; padding:18px 0;
  grid-template-columns:repeat(auto-fill,minmax(300px,1fr))}
.item{display:block; text-align:start; background:var(--card); color:inherit;
  border:1px solid var(--rule); border-radius:12px; padding:18px 20px;
  font:inherit; font-family:var(--sans); cursor:pointer;
  transition:border-color .14s, transform .14s}
.item:hover{border-color:var(--vaud); transform:translateY(-2px)}
.item .no{font-size:11px; font-weight:600; letter-spacing:.12em; color:var(--ink3)}
.item b{display:block; font-size:calc(var(--t) * .92); font-weight:700; line-height:1.2;
  margin-top:3px; letter-spacing:-.015em}
.item i{display:block; font-style:normal; font-size:var(--m); color:var(--ink3); margin-top:3px}
.item u{display:block; text-decoration:none; font-size:calc(var(--m) * .88);
  color:var(--vaud); margin-top:10px}

.roles{display:flex; gap:20px; flex-wrap:wrap; padding:14px 0 6px;
  font-size:var(--m); color:var(--ink3)}
.roles span{display:inline-flex; align-items:center; gap:9px}
.pion{width:19px; height:19px; border-radius:50%; color:#fff; font-size:11px;
  font-weight:700; display:grid; place-items:center; flex:0 0 auto}
.pion.p{background:var(--bleu)} .pion.m{background:var(--vaud)}

/* η σκηνή: μία στήλη στο κινητό, δύο στην τηλεόραση */
.lignes{column-gap:26px}
@media (min-width:1200px){ .lignes{columns:2} }
.ln{display:flex; gap:14px; align-items:flex-start; width:100%; text-align:start;
  background:transparent; border:0; border-left:3px solid transparent;
  padding:11px 14px; font:inherit; font-family:var(--sans); color:inherit; cursor:pointer;
  border-radius:8px; margin-bottom:5px; break-inside:avoid;
  transition:background .13s}
.ln.papa{border-left-color:var(--bleu); background:var(--bleu-bg)}
.ln.myrto{border-left-color:var(--vaud-line)}
.ln .no{flex:0 0 auto; width:2.1em; text-align:end; color:var(--ink3);
  font-size:calc(var(--m) * .92); font-variant-numeric:tabular-nums; margin-top:.28em}
.ln .ic{flex:0 0 auto; width:var(--ic); height:var(--ic); border-radius:50%; margin-top:1px;
  border:1px solid var(--vaud-line); background:var(--vaud-bg); color:var(--vaud);
  display:grid; place-items:center; font-size:calc(var(--ic) * .3)}
.ln .t{font-size:var(--t); line-height:1.34; display:block; letter-spacing:-.01em}
.ln.papa .t{font-weight:700; color:var(--ink)}
.ln.myrto .t{font-weight:400; color:var(--ink2)}
.ln .m{display:none; font-size:var(--m); color:var(--ink3); margin-top:4px; line-height:1.4}
body.sens .ln .m{display:block}
.ln.on{background:var(--vaud-bg); border-left-color:var(--vaud)}
.ln.on .ic{background:var(--vaud); color:#fff; border-color:var(--vaud)}

footer{padding:26px var(--pad) 40px; color:var(--ink3); font-size:13px; line-height:1.7;
  border-top:1px solid var(--rule); margin-top:24px}
footer a{color:var(--vaud)}
/* Όσο παίζει μια σκηνή το υποσέλιδο φεύγει: χωρίς αυτό, οι σκηνές των 20
   ατάκων ξεπερνούσαν κατά 13 πίξελ το ύψος μιας οθόνης 1080 και εμφανιζόταν
   κύλιση ακριβώς την ώρα του παιχνιδιού. */
body.enjeu footer{display:none}
/* Ορατή εστίαση, για χειρισμό με βελάκια από απόσταση */
.ln:focus-visible, .item:focus-visible{outline:3px solid var(--vaud); outline-offset:2px}
[hidden]{display:none!important}
</style>
</head>
<body>
<header>
  <div class="hrow">
    <div>
      <div class="sc">CARTES DU SOIR</div>
      <h1 id="titre">Οι κάρτες του βραδιού<small id="soustitre">Διάλεξε μια σκηνή</small></h1>
    </div>
    <div class="bar" id="bar">
      <button type="button" class="back" id="back" hidden>&#8592; Σκηνές</button>
      <button type="button" id="lent" aria-pressed="false" hidden>Αργά</button>
      <button type="button" id="sens" aria-pressed="false" hidden>Τι σημαίνει</button>
      <button type="button" id="plein">Πλήρης οθόνη</button>
    </div>
  </div>
</header>
<main>
  <div class="scenes" id="liste"></div>
  <div id="scene" hidden></div>
</main>
<footer>
  Ο ήχος είναι ηχογραφημένος από πριν, μία φορά ανά ατάκα, μία φωνή ανά ρόλο.<br>
  <a href="cartes-du-soir.pdf">Τύπωσε τις κάρτες</a> — δύο σελίδες ανά σκηνή, γαλλικά και ελληνικά αντικριστά.
  Αυτή η σελίδα δεν αντικαθιστά το χαρτί· λέει μόνο την προφορά.
</footer>
<script>
const SCENES = __DONNEES__;
const AUDIO  = __INDEX__;
const SONS   = __SONS__;   // κενό όταν ο ήχος είναι δίπλα σε αρχεία
const SRC = c => SONS[c] ? 'data:audio/mp4;base64,' + SONS[c] : 'audio/' + c + '.m4a';

const liste = document.getElementById('liste');
const vue   = document.getElementById('scene');
const titre = document.getElementById('titre');
const sous  = document.getElementById('soustitre');
const enJeu = ['back','lent','sens'].map(i => document.getElementById(i));
let lent = false, encours = null;

function esc(s){ return s.replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }

SCENES.forEach((s, i) => {
  const b = document.createElement('button');
  b.className = 'item'; b.type = 'button';
  b.innerHTML = '<span class="no">' + String(s.id).padStart(2, '0') + '</span>' +
                '<b>' + esc(s.titre_fr) + '</b><i>' + esc(s.titre_el) + '</i>' +
                '<u>' + s.lignes.length + ' ατάκες · ' + esc(s.roles.myrto) + '</u>';
  b.addEventListener('click', () => ouvre(i));
  liste.appendChild(b);
});

function ouvre(i, silencieux){
  const s = SCENES[i];
  if (!silencieux) history.replaceState(null, '', '#' + String(s.id).padStart(2, '0'));
  titre.firstChild.textContent = s.titre_fr;
  sous.textContent = s.titre_el;
  vue.innerHTML = '<div class="roles">' +
    '<span><i class="pion p">1</i>' + esc(s.roles.papa) + '</span>' +
    '<span><i class="pion m">2</i>' + esc(s.roles.myrto) + '</span></div>' +
    '<div class="lignes">' + s.lignes.map((l, n) =>
      '<button class="ln ' + l.qui + '" type="button" data-qui="' + l.qui +
      '" data-fr="' + esc(l.fr) + '">' +
        '<span class="no">' + (n + 1) + '</span>' +
        '<span class="ic">&#9654;</span>' +
        '<span><span class="t">' + esc(l.fr) + '</span>' +
        '<span class="m">' + esc(l.el) + '</span></span></button>').join('') + '</div>';
  liste.hidden = true; vue.hidden = false;
  document.body.classList.add('enjeu');
  enJeu.forEach(b => b.hidden = false);
  window.scrollTo(0, 0);
  const p = vue.querySelector('.ln');
  if (p) p.focus({ preventScroll: true });
}

document.getElementById('back').addEventListener('click', () => {
  stop();
  history.replaceState(null, '', location.pathname);
  titre.firstChild.textContent = 'Οι κάρτες του βραδιού';
  sous.textContent = 'Διάλεξε μια σκηνή';
  vue.hidden = true; liste.hidden = false;
  document.body.classList.remove('enjeu');
  enJeu.forEach(b => b.hidden = true);
  const p = liste.querySelector('.item');
  if (p) p.focus({ preventScroll: true });
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

// Το QR κάθε τυπωμένης κάρτας δείχνει εδώ: petmakris.github.io/cartes/#07
function depuisAdresse(){
  const n = parseInt((location.hash || '').replace('#', ''), 10);
  if (!n) return;
  const i = SCENES.findIndex(s => s.id === n);
  if (i >= 0) ouvre(i, true);
}
depuisAdresse();
window.addEventListener('hashchange', depuisAdresse);

const plein = document.getElementById('plein');
plein.addEventListener('click', () => {
  if (document.fullscreenElement) document.exitFullscreen();
  else document.documentElement.requestFullscreen().catch(() => {});
});
document.addEventListener('fullscreenchange', () => {
  plein.textContent = document.fullscreenElement ? 'Έξοδος' : 'Πλήρης οθόνη';
});

// Πλοήγηση με βελάκια: δουλεύει με πληκτρολόγιο, με τηλεχειριστήριο Bluetooth,
// και με ό,τι στέλνει κανονικά πλήκτρα βελών. Enter ή διάστημα παίζει την ατάκα.
document.addEventListener('keydown', e => {
  const enJeuTora = !vue.hidden;
  const cibles = [...(enJeuTora ? vue.querySelectorAll('.ln') : liste.querySelectorAll('.item'))];
  if (!cibles.length) return;
  const i = cibles.indexOf(document.activeElement);
  const bouge = d => {
    e.preventDefault();
    cibles[Math.max(0, Math.min(cibles.length - 1, (i < 0 ? 0 : i + d)))]
      .focus({ preventScroll: false });
  };
  switch (e.key) {
    case 'ArrowDown': case 'ArrowRight': bouge(+1); break;
    case 'ArrowUp':   case 'ArrowLeft':  bouge(-1); break;
    case 'Home': e.preventDefault(); cibles[0].focus(); break;
    case 'End':  e.preventDefault(); cibles[cibles.length - 1].focus(); break;
    case 'Escape': case 'Backspace':
      if (enJeuTora) { e.preventDefault(); document.getElementById('back').click(); }
      break;
  }
});

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
