# Σιρόπι Σοκολάτας με Πραλίνα Φουντουκιού

Generates a 2-page A4 PDF: a Greek recipe for a near-zero-calorie chocolate
hazelnut praline syrup, plus a Migros/Coop shopping list with French shelf
names and QR codes to the actual product pages.

## Run

```bash
pip install -r requirements.txt
python build.py
open siropi-sokolatas-pralina-GR.pdf
```

Optional argument sets the output path: `python build.py /tmp/out.pdf`

## What's here

```
build.py           the entire generator — content and layout in one file
fonts/             Roboto TTF (Apache 2.0), covers Greek + French accents
requirements.txt
CLAUDE.md          constraints worth reading before editing
.qr-cache/         generated QR PNGs, safe to delete
```

## Editing

Content lives in plain Python lists near the middle of `build.py`:

| Variable  | What it drives                                  |
|-----------|-------------------------------------------------|
| `praline` | left ingredients card                            |
| `syrup`   | right ingredients card                           |
| `steps`   | the numbered method                              |
| `prods`   | the four QR product rows                         |
| `rest`    | the plain shopping table                         |

Wrap French shelf words in `fr()` so they pick up the teal colour coding.

After editing, confirm the PDF is still 2 pages and that no glyph silently
dropped out — both checks are in `CLAUDE.md`.

## Fonts

The bundled Roboto TTFs were converted from the `roboto-fontface` npm package.
To regenerate:

```bash
npm pack roboto-fontface && tar xzf roboto-fontface-*.tgz
python - <<'PY'
from fontTools.ttLib import TTFont
for n in ['Roboto-Regular','Roboto-Medium','Roboto-Bold','Roboto-RegularItalic']:
    f = TTFont(f'package/fonts/roboto/{n}.woff'); f.flavor = None
    f.save(f'fonts/{n}.ttf')
PY
```
