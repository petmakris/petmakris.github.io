# Fréquence — word-frequency vocabulary project

All the word-frequency work lives here:

- the **web game** (multi-language flashcards) served at the site root as
  `../index.html` → https://petmakris.github.io/
- the **French PDF reference** sheets (`build_pdf.py`)
- a small **phrases** sub-project (`phrases/`)

The source corpora are the per-language 50k frequency lists from the 2018
[FrequencyWords](https://github.com/hermitdave/FrequencyWords) subtitle dataset
(`*_50k.txt`, `word count` per line, ranked).

## Web game

```sh
make game          # or: python3 build_game.py   -> ../index.html
```

`build_game.py` bakes the per-language word lists (`data/translations*.txt`) into
the template and writes the Pages root `index.html`. It stamps a content hash
(`BUILD`, used for the page's self-update check) and an incremental `BUILD_NO`
(stored in `build_number.json`, bumps only when content changes). After building,
commit + push from the repo root; open tabs auto-reload to the new build.

```
game.template.html      the page (HTML/CSS/JS); __DATA__/__BUILD__/__BUILDNO__ placeholders
build_game.py           bakes data + template -> ../index.html
build_number.json       monotonic build counter + content hash (committed; don't hand-edit)
data/translations*.txt  `word = english` per line, frequency-ordered (fr/es/el/it)
```

## French PDF reference

Dense, colour-coded A4 sheets of the most common French words, ranked by
frequency — two A4 pages per "sheet" (~666 words), learned most-frequent-first.

```sh
make build           # sheet 1 -> out/french_0001-0666.pdf  (BAND=1 default)
make build BAND=2    # later sheets (need their data — see below)
make slice BAND=2    # write data/bandNN_words.txt for the data passes
make clean           # remove generated PDFs
```

Words are derived from `fr_50k.txt` on the fly (`slice_band.clean_words`); only
the generated glosses (`data/translations.txt`) and POS tags (`data/pos.txt`),
keyed by French word, are stored — so the game and the PDF share the one French
`translations.txt`.

**Producing the next sheet:** `make slice BAND=N`, then run `prompts/translate.md`
and `prompts/postag.md` over the emitted words (5 batches of 200), append the
results to `data/translations.txt` / `data/pos.txt`, then `make build BAND=N`.
`build_pdf.py` renders `?`/grey `OTHER` for any word missing from `data/`, so an
incomplete sheet still builds.

Encoding: Verb = blue (irregular underlined), Noun = black, Adjective = green,
Adverb = amber, Grammar/other = grey. Every 10 rows are striped for navigation.

## Layout

```
frequence/
  game.template.html  build_game.py  build_number.json   # web game
  build_pdf.py  slice_band.py  Makefile                  # French PDF tooling
  *_50k.txt                                               # source corpora (fr/es/el/it)
  data/         translations*.txt, pos.txt                # generated glosses + POS
  prompts/      translate.md, postag.md                   # LLM passes for new sheets
  phrases/      build_phrases.py + data + out             # phrases sub-project
  out/          rendered French PDFs
```
