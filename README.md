# petmakris.github.io

A static site hosting a few small things, at <https://petmakris.github.io>.
No build system at the top level, no Jekyll (`.nojekyll` is deliberate) — the
root `index.html` is a hand-written hub and every project is a folder under it.

| Path | What | Source |
|---|---|---|
| `/` | The hub. Edit `index.html` directly. | here |
| `/french/` | Παραμύθια στα γαλλικά — French bedtime picture books with Greek pronunciation and audio. | `~/projects/personal/French` |
| `/english/` | The English Play Deck — 28 scripted scenes for a TV, with audio. The older printable pack is alongside as a PDF. | `~/projects/personal/English` |
| `/frequence/` | Fréquence — the 10 000 most frequent words in four languages, as a game. | `frequence/` |
| `/dieting/el/`, `/dieting/fr/` | A practical guide to dieting, in Greek and French. | here |

## Deploying

**Fréquence** builds from source inside this repo:

```sh
cd frequence && make game        # writes ../frequence/index.html
```

**The French books** and **the English Play Pack** live in another repo and are
built into this one:

```sh
cd ~/projects/personal/French  && make deploy   # writes ./french/
cd ~/projects/personal/English && make deploy   # writes ./english/
```

The English pack is built twice from one script. The private build names the
child, the parent and the home address, because that is what makes the role-play
work at the kitchen table; `make deploy` runs `--public`, which substitutes a
placeholder child, "Papa", and drops the street address. **Only the public build
is ever copied here.**

That deploy emits a small `french/index.html` plus `french/assets/` — the audio
and artwork as separate files. They are *not* inlined on purpose: the same app
also builds as a single 21 MB file for AirDropping to a phone, but over the
network that would mean downloading everything before reading page one. As
separate files the browser fetches only the page you are on and caches the rest,
so the site opens in about 560 KB.

Then, from here:

```sh
git add -A && git commit -m "…" && git push
```

Pages redeploys in a minute or so. Refresh on the tablet and it is there.

## Progress

Every project keeps its state in the browser's `localStorage` on the device
reading it — which page of which book you are on, which words you have learned.
Nothing is stored server-side, so a deploy never disturbs it, and the tablet and
the laptop keep their own separate places.
