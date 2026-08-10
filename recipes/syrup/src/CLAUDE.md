# CLAUDE.md

Single-purpose repo: generates a 2-page A4 PDF (Greek) — a recipe plus a
supermarket shopping list for Migros/Coop in Lausanne.

`build.py` is the whole thing. Run it, open the PDF, look at it. There is no
app, no server, no tests beyond the checks below.

```bash
pip install -r requirements.txt
python build.py                 # -> ./siropi-sokolatas-pralina-GR.pdf
python build.py /tmp/out.pdf    # custom output path
```

## Hard constraints — verify these after ANY edit

**1. The document must be exactly 2 pages.**
ReportLab silently reflows onto page 3 when content grows. Greek runs ~15%
longer than English, so there is very little slack. Always check:

```bash
python build.py /tmp/c.pdf && python -c "from pypdf import PdfReader; \
print(len(PdfReader('/tmp/c.pdf').pages))"
```

If it hits 3 pages, prefer *restructuring* over shrinking type — this is a
kitchen/supermarket document and it gets read at arm's length. The praline
card is shorter than the syrup card, and the warning card was moved into that
left-column dead space for exactly this reason. Reach for font-size reduction
last.

**2. Every glyph must exist in Roboto.**
The bundled TTFs were converted from the `roboto-fontface` npm package's WOFF
files. They cover Latin, Greek, French accents and `½ ¼ ⅛` — but **not** `→`
(U+2192) or `⇒`. ReportLab renders a missing glyph as *nothing*, silently, so
this does not show up as an error. Sweep after editing text:

```python
from pypdf import PdfReader
from fontTools.ttLib import TTFont
cmap = set()
for t in TTFont('fonts/Roboto-Regular.ttf')['cmap'].tables:
    cmap |= set(t.cmap.keys())
txt = ''.join(p.extract_text() for p in PdfReader('/tmp/c.pdf').pages)
print({c for c in txt if c.strip() and ord(c) not in cmap} or 'clean')
```

**3. QR codes must decode to the intended URL.**
Four products carry QR codes. The URLs are real, hand-verified Migros/Coop
product pages — do not invent or "tidy" them, and do not swap `/en/` for `/fr/`
on the Coop ones without re-checking that the page still resolves. Delete
`.qr-cache/` to force regeneration. Verify with:

```python
import cv2, glob
d = cv2.QRCodeDetector()
for f in sorted(glob.glob('.qr-cache/*.png')):
    print(f, d.detectAndDecode(cv2.imread(f))[0])
```

## Design system

Material Design, light, high contrast. Defined once at the top of `build.py`.

- `PRIMARY` Blue 800 `#1565C0` — app bars, step badges, section overlines
- `PRIM_DK` Blue 900 `#0D47A1` — table header rows
- `FRENCH` Teal 800 `#00695C` — **semantic, not decorative**
- Amber card = things that go wrong; red-tinted card = unavailability notices
- Body text `#111111`, not grey — it gets printed in mono and read in a shop

### The teal rule

Teal marks a French word the reader will physically encounter: printed on the
packaging (`sans sucre ajouté`, `carbonate de potassium`, `sucre vanillé`) or
on the aisle sign (`Pâtisserie`, `Épices`, `Fruits secs`). Use the `fr()`
helper, never a raw `<font color>`. Do not use teal for French words that are
merely translations — that dilutes the signal the whole document depends on.

Aisle names stay in French only. A Greek translation of "baking aisle" is
useless to someone standing in a Coop reading the sign.

## Content rules

- **Allulose is not mentioned anywhere.** It is not authorised for sale in
  Switzerland or the EU. The recipe uses erythritol plus a liquid sweetener,
  and 5 g of ordinary sugar for the caramel. Do not re-add explanatory notes
  about why allulose is absent.
- **Sugar is in the ingredients but not the shopping list** — deliberate, it is
  sourced elsewhere. It carries the tag `δεν είναι στη λίστα ψωνιών`. Step 2
  (caramelisation) depends on it, so do not remove it from the recipe.
- Erythritol must be described as needing full dissolution while hot. It
  recrystallises on cold yogurt otherwise, which is the recipe's main failure
  mode and the reason the warning card exists.

## Layout notes

- `card()` wraps a flowable in a Material outlined card; pass `accent=` for the
  coloured left edge.
- `Badge` and `CheckBox` are custom `Flowable`s drawn on the canvas.
- Rounded corners come from ReportLab's `ROUNDEDCORNERS` TableStyle command
  (requires ReportLab 4.x).
- Content width is 182 mm (A4 minus 14 mm margins), held in `CONTENT_W`.
  Column widths are derived from it — do not hardcode millimetres that should
  be relative.
