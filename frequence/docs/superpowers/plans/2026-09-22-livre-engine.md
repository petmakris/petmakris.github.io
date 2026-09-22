# Vocabulaire illustré — Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the rendering engine that turns card JSON into a printable A4 PDF and a browsable HTML page, proven end-to-end on three real cards.

**Architecture:** Python generates a single self-contained HTML file from per-card JSON; headless Chromium (Playwright) prints it to A4 PDF. Icons are inlined SVG — OpenMoji for concrete words, 57 house-drawn glyphs for abstract ones. No reportlab.

**Tech Stack:** Python 3.14, Playwright (already installed), pytest 9.0.3, plain CSS grid. No new runtime dependencies.

**Spec:** `docs/superpowers/specs/2026-09-22-vocabulaire-illustre-design.md`

**Scope:** This is plan 1 of 3. It builds the engine and validates it on three cards. Content production (~450 icon decisions, 1,416 Greek glosses, ~50 headings and examples) is plan 2. The 1,332-phrase migration is plan 3. This plan produces working, testable software on its own.

## Global Constraints

- Page size **A4**, `prefer_css_page_size=True`, `print_background=True`.
- Font **Alegreya Sans** (Regular + Bold), from `frequence/jeu/fonts/`, inlined base64. Never a system font — Greek must render.
- Icons **26px**; French **14pt bold**; Greek gloss same size, regular weight, warm grey `#57544F`.
- **Density target: ≥50 items on a full A4 page.** This is a test, not an aspiration.
- Left rail **18%** of card width. Content grid **3 columns** (2 for groups under 7 items).
- Gender colours: `le` `#2166B0`, `la` `#B84066`, `l'`/`les` `#6B6B6B`. **Article only, never the noun.**
- Every card: `break-inside: avoid`.
- Greek appears only where the cover test says so (Task 6).
- Commit messages are **one line, no body, no trailers, no attribution**.
- Work in `~/projects/blog/frequence/livre/`. Commit and push directly to `main` (repo policy in `blog/CLAUDE.md`).

## Prototype source

Working prototype code to port from, in the session scratchpad:
`/private/tmp/claude-502/-Users-petros-makris-projects-env/2c792b95-e19f-43be-8d62-7472/`
— `build_c2.py` (122 lines, the accepted C2 layout), `glyphs_svg.py` (169 lines, the 57 glyphs), `topdf.py` (22 lines), `vocab/vocab.py` (215 lines, the 437-item vocabulary), `sets/openmoji-svg/` (1.5MB).

**Copy these in rather than rewriting.** They are proven. If the scratchpad has been cleared, the plan still stands but Tasks 3–4 become original work.

## File structure

| File | Responsibility |
|---|---|
| `livre/topdf.py` | Chromium render. HTML path in, PDF out. Nothing else. |
| `livre/cards.py` | Load and validate card JSON. |
| `livre/glyphs.py` | The 57 house glyphs, each a function returning an SVG string. |
| `livre/icons.py` | Resolve a vocabulary item to an inline SVG: OpenMoji, override, house glyph, or nothing. |
| `livre/greek.py` | The cover test — decide whether a row keeps its Greek. |
| `livre/render.py` | Row → card → document HTML. Owns all layout. |
| `livre/style.css` | The C2 stylesheet. |
| `livre/build.py` | CLI. Reads cards, writes HTML, calls topdf. |
| `livre/data/cards/*.json` | One file per card. Content only, never layout. |
| `livre/assets/fonts/` | AlegreyaSans Regular + Bold. |
| `livre/assets/openmoji/` | Only the icons actually referenced. |
| `livre/tests/` | pytest. |
| `livre/Makefile` | `make livre`, `make check`, `make clean`. |

---

### Task 1: Scaffold and the Chromium renderer

**Files:**
- Create: `frequence/livre/topdf.py`
- Create: `frequence/livre/tests/test_topdf.py`
- Create: `frequence/livre/Makefile`
- Create: `frequence/livre/assets/fonts/` (copy 2 TTFs from `frequence/jeu/fonts/`)

**Interfaces:**
- Consumes: nothing.
- Produces: `topdf.render(html_path: str, pdf_path: str) -> None`, and `topdf.page_count(pdf_path: str) -> int`.

- [ ] **Step 1: Create the directory and copy the fonts**

```bash
cd ~/projects/blog/frequence
mkdir -p livre/assets/fonts livre/assets/openmoji livre/data/cards livre/tests
cp jeu/fonts/AlegreyaSans-Regular.ttf jeu/fonts/AlegreyaSans-Bold.ttf livre/assets/fonts/
ls -la livre/assets/fonts/
```

Expected: two .ttf files, ~258KB and ~261KB.

- [ ] **Step 2: Write the failing test**

Create `frequence/livre/tests/test_topdf.py`:

```python
import os, tempfile
import topdf

A4_PT = (595, 842)

def test_renders_a4_pdf():
    html = '<!doctype html><html><head><meta charset="utf-8">' \
           '<style>@page{size:A4;margin:0}</style></head>' \
           '<body><p>bonjour · καλημέρα</p></body></html>'
    with tempfile.TemporaryDirectory() as d:
        h = os.path.join(d, "t.html")
        p = os.path.join(d, "t.pdf")
        open(h, "w", encoding="utf-8").write(html)
        topdf.render(h, p)
        assert os.path.getsize(p) > 500
        assert topdf.page_count(p) == 1

def test_page_count_counts_pages():
    html = '<!doctype html><html><head><meta charset="utf-8">' \
           '<style>@page{size:A4;margin:0}.b{break-after:page}</style></head>' \
           '<body><div class="b">un</div><div class="b">deux</div><div>trois</div></body></html>'
    with tempfile.TemporaryDirectory() as d:
        h = os.path.join(d, "t.html")
        p = os.path.join(d, "t.pdf")
        open(h, "w", encoding="utf-8").write(html)
        topdf.render(h, p)
        assert topdf.page_count(p) == 3
```

- [ ] **Step 3: Run the test to verify it fails**

```bash
cd ~/projects/blog/frequence/livre && python3 -m pytest tests/test_topdf.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'topdf'`.

- [ ] **Step 4: Write the implementation**

Create `frequence/livre/topdf.py`:

```python
#!/usr/bin/env python3
"""HTML -> A4 PDF via headless Chromium.

Chromium is the reference renderer because the HTML is also the artefact you
open in a browser, so the print must match what the browser shows. WeasyPrint
was evaluated and is degraded: it lacks color-mix(), so every tint vanishes.
"""
import asyncio
import os
import re
import sys


async def _render(html_path, pdf_path):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(f"file://{os.path.abspath(html_path)}")
        await page.emulate_media(media="print")
        await page.pdf(path=pdf_path, format="A4",
                       print_background=True, prefer_css_page_size=True)
        await browser.close()


def render(html_path, pdf_path):
    """Render one HTML file to A4 PDF. Overwrites pdf_path."""
    asyncio.run(_render(html_path, pdf_path))


def page_count(pdf_path):
    """Number of pages in a PDF, by counting page objects."""
    data = open(pdf_path, "rb").read()
    return len(re.findall(rb"/Type\s*/Page[^s]", data))


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        out = arg.replace(".html", ".pdf")
        render(arg, out)
        print(f"{out}  {os.path.getsize(out)//1024} KB  {page_count(out)} pages")
```

- [ ] **Step 5: Run the test to verify it passes**

```bash
cd ~/projects/blog/frequence/livre && python3 -m pytest tests/test_topdf.py -v
```

Expected: 2 passed.

- [ ] **Step 6: Write the Makefile**

Create `frequence/livre/Makefile`:

```make
# Vocabulaire illustré — build the textbook.
.DEFAULT_GOAL := help
.PHONY: livre check clean help

livre:   ## build out/livre.html and out/livre.pdf
	python3 build.py

check:   ## run the test suite
	python3 -m pytest tests -q

clean:   ## remove generated output
	rm -rf out

help:    ## list targets
	@grep -E '^[a-z]+:.*##' $(MAKEFILE_LIST) | sed -E 's/:[^#]*## / - /'
```

- [ ] **Step 7: Commit**

```bash
cd ~/projects/blog
git add frequence/livre
git commit -m "livre: Chromium HTML-to-PDF renderer and scaffold"
```

---

### Task 2: Card schema and loader

**Files:**
- Create: `frequence/livre/cards.py`
- Create: `frequence/livre/tests/test_cards.py`
- Create: `frequence/livre/data/cards/00-example.json`

**Interfaces:**
- Consumes: nothing.
- Produces: `cards.load_card(path: str) -> dict`, `cards.load_all(dirpath: str) -> list[dict]`, `cards.CardError`.
  A card dict has keys: `id` (str), `tier` (int 1-3), `order` (int), `title_fr` (str), `title_el` (str), `accent` (str, hex), `example` (str or None), `items` (list of dicts with `fr`, `el`, `key`, optional `icon`).

- [ ] **Step 1: Write the failing test**

Create `frequence/livre/tests/test_cards.py`:

```python
import json, os, tempfile
import pytest
import cards

GOOD = {
    "id": "prepositions", "tier": 1, "order": 2,
    "title_fr": "Où ? — les prépositions", "title_el": "θέσεις στον χώρο",
    "accent": "#B5531F",
    "example": "Le livre est sur la table.",
    "items": [
        {"fr": "sur", "el": "πάνω σε", "key": "on_box"},
        {"fr": "dans", "el": "μέσα σε", "key": "in_box"},
    ],
}

def _write(tmp, obj, name="c.json"):
    p = os.path.join(tmp, name)
    json.dump(obj, open(p, "w", encoding="utf-8"), ensure_ascii=False)
    return p

def test_loads_a_good_card():
    with tempfile.TemporaryDirectory() as d:
        c = cards.load_card(_write(d, GOOD))
        assert c["id"] == "prepositions"
        assert len(c["items"]) == 2
        assert c["items"][0]["fr"] == "sur"

def test_example_defaults_to_none():
    obj = dict(GOOD); obj.pop("example")
    with tempfile.TemporaryDirectory() as d:
        assert cards.load_card(_write(d, obj))["example"] is None

def test_missing_required_field_raises():
    obj = dict(GOOD); obj.pop("title_fr")
    with tempfile.TemporaryDirectory() as d:
        with pytest.raises(cards.CardError, match="title_fr"):
            cards.load_card(_write(d, obj))

def test_empty_items_raises():
    obj = dict(GOOD); obj["items"] = []
    with tempfile.TemporaryDirectory() as d:
        with pytest.raises(cards.CardError, match="items"):
            cards.load_card(_write(d, obj))

def test_item_missing_fr_raises():
    obj = json.loads(json.dumps(GOOD)); obj["items"][1].pop("fr")
    with tempfile.TemporaryDirectory() as d:
        with pytest.raises(cards.CardError, match="fr"):
            cards.load_card(_write(d, obj))

def test_bad_tier_raises():
    obj = dict(GOOD); obj["tier"] = 4
    with tempfile.TemporaryDirectory() as d:
        with pytest.raises(cards.CardError, match="tier"):
            cards.load_card(_write(d, obj))

def test_load_all_sorts_by_tier_then_order():
    a = dict(GOOD); a["id"] = "a"; a["tier"] = 2; a["order"] = 1
    b = dict(GOOD); b["id"] = "b"; b["tier"] = 1; b["order"] = 9
    c = dict(GOOD); c["id"] = "c"; c["tier"] = 1; c["order"] = 3
    with tempfile.TemporaryDirectory() as d:
        _write(d, a, "a.json"); _write(d, b, "b.json"); _write(d, c, "c.json")
        assert [x["id"] for x in cards.load_all(d)] == ["c", "b", "a"]
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd ~/projects/blog/frequence/livre && python3 -m pytest tests/test_cards.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'cards'`.

- [ ] **Step 3: Write the implementation**

Create `frequence/livre/cards.py`:

```python
#!/usr/bin/env python3
"""Load and validate card JSON.

A card declares CONTENT ONLY. Layout belongs to render.py — a card file never
says where anything goes on the paper.
"""
import glob
import json
import os

REQUIRED = ("id", "tier", "order", "title_fr", "title_el", "accent", "items")
ITEM_REQUIRED = ("fr", "key")


class CardError(Exception):
    pass


def load_card(path):
    """Read one card JSON file, validate it, return the dict."""
    try:
        card = json.load(open(path, encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise CardError(f"{path}: invalid JSON: {e}") from e

    for field in REQUIRED:
        if field not in card:
            raise CardError(f"{path}: missing required field {field!r}")

    if card["tier"] not in (1, 2, 3):
        raise CardError(f"{path}: tier must be 1, 2 or 3, got {card['tier']!r}")

    if not isinstance(card["items"], list) or not card["items"]:
        raise CardError(f"{path}: items must be a non-empty list")

    for i, item in enumerate(card["items"]):
        for field in ITEM_REQUIRED:
            if field not in item:
                raise CardError(f"{path}: item {i} missing {field!r}")
        item.setdefault("el", None)
        item.setdefault("icon", None)

    card.setdefault("example", None)
    return card


def load_all(dirpath):
    """Every card in a directory, sorted by tier then order."""
    out = [load_card(p) for p in sorted(glob.glob(os.path.join(dirpath, "*.json")))]
    return sorted(out, key=lambda c: (c["tier"], c["order"]))
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd ~/projects/blog/frequence/livre && python3 -m pytest tests/test_cards.py -v
```

Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
cd ~/projects/blog
git add frequence/livre/cards.py frequence/livre/tests/test_cards.py
git commit -m "livre: card JSON schema and loader"
```

---

### Task 3: House glyph library

**Files:**
- Create: `frequence/livre/glyphs.py` (port from prototype `glyphs_svg.py`)
- Create: `frequence/livre/tests/test_glyphs.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `glyphs.GLYPHS: dict[str, callable]` mapping a key such as `"on_box"` to a function `(accent: str) -> str` returning an SVG string; and `glyphs.render(key: str, accent: str) -> str | None`.

The grammar, which every glyph obeys: a **grey reference object** (box, track, frame) and a **coloured subject** (dot, fill, marker). Where the subject sits relative to the reference *is* the meaning.

- [ ] **Step 1: Write the failing test**

Create `frequence/livre/tests/test_glyphs.py`:

```python
import re
import glyphs

ACCENT = "#B5531F"

def test_has_the_full_set():
    assert len(glyphs.GLYPHS) >= 57

def test_every_glyph_returns_wellformed_svg():
    for key in glyphs.GLYPHS:
        svg = glyphs.render(key, ACCENT)
        assert svg.startswith("<svg"), key
        assert svg.rstrip().endswith("</svg>"), key
        assert 'viewBox="0 0 24 24"' in svg, key

def test_every_glyph_uses_the_accent():
    for key in glyphs.GLYPHS:
        assert ACCENT in glyphs.render(key, ACCENT), key

def test_core_prepositions_are_present():
    for key in ("on_box", "under_box", "in_box", "out_box",
                "front_box", "behind_box", "between_box"):
        assert key in glyphs.GLYPHS, key

def test_sur_and_dans_differ():
    assert glyphs.render("on_box", ACCENT) != glyphs.render("in_box", ACCENT)

def test_frequency_track_is_monotonic():
    """toujours is a full track, jamais an empty one — different SVG."""
    assert glyphs.render("freq_always", ACCENT) != glyphs.render("freq_never", ACCENT)

def test_unknown_key_returns_none():
    assert glyphs.render("no_such_glyph", ACCENT) is None
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd ~/projects/blog/frequence/livre && python3 -m pytest tests/test_glyphs.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'glyphs'`.

- [ ] **Step 3: Port the prototype glyph library**

```bash
P=/private/tmp/claude-502/-Users-petros-makris-projects-env/2c792b95-e19f-43be-8d62-7472
cp $P/glyphs_svg.py ~/projects/blog/frequence/livre/glyphs.py
```

Then adapt it to the interface above: a module-level `GLYPHS` dict and a `render(key, accent)` function. The prototype already draws all 57 on a 24×24 grid; the work is exposing them under stable keys. If the scratchpad is gone, write them fresh following this shape:

```python
GREY = "#9A9A96"

def _box(x, y, w, h):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" '
            f'stroke="{GREY}" stroke-width="1.6"/>')

def _dot(cx, cy, accent, r=2.6):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{accent}"/>'

def _svg(body):
    return f'<svg viewBox="0 0 24 24" width="24" height="24">{body}</svg>'

def on_box(accent):      # sur — dot resting on the box
    return _svg(_box(5, 12, 14, 9) + _dot(12, 8.5, accent))

def under_box(accent):   # sous — dot beneath the box
    return _svg(_box(5, 3, 14, 9) + _dot(12, 15.5, accent))

def in_box(accent):      # dans — dot inside the box
    return _svg(_box(4, 6, 16, 12) + _dot(12, 12, accent))

GLYPHS = {"on_box": on_box, "under_box": under_box, "in_box": in_box}


def render(key, accent):
    fn = GLYPHS.get(key)
    return fn(accent) if fn else None
```

The full set of 57 keys: prepositions (`on_box under_box in_box out_box front_box behind_box between_box beside_box around_box against_box toward_box through_box above_gap below_gap`), deixis (`here there_mid there_far near far everywhere nowhere somewhere`), quantity (`q_enough q_too_much q_little q_lots`), frequency (`freq_always freq_often freq_rarely freq_never`), comparatives (`cmp_big cmp_small cmp_high cmp_low cmp_strong cmp_weak cmp_heavy cmp_light`), direction (`dir_up dir_down dir_left dir_right dir_straight dir_back`), and the typographic tiles for days (`day_1`…`day_7`) and months (`month_1`…`month_12`).

**Why tiles for days and months:** a drawn 7-cell week strip was prototyped and is an illegible grey smudge at 14pt. Type survives any size. A tile is a rounded accent rect carrying `Lu` or `12`.

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd ~/projects/blog/frequence/livre && python3 -m pytest tests/test_glyphs.py -v
```

Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
cd ~/projects/blog
git add frequence/livre/glyphs.py frequence/livre/tests/test_glyphs.py
git commit -m "livre: 57 house glyphs for the words no emoji set has"
```

---

### Task 4: Icon resolution

**Files:**
- Create: `frequence/livre/icons.py`
- Create: `frequence/livre/tests/test_icons.py`
- Create: `frequence/livre/assets/openmoji/` (populate from prototype)

**Interfaces:**
- Consumes: `glyphs.render(key, accent)` from Task 3.
- Produces: `icons.resolve(item: dict, accent: str) -> tuple[str, str]` returning `(svg_or_placeholder, kind)` where `kind` is one of `"emoji"`, `"glyph"`, `"none"`. Also `icons.NO_ICON: frozenset[str]`.

- [ ] **Step 1: Copy the OpenMoji assets**

```bash
P=/private/tmp/claude-502/-Users-petros-makris-projects-env/2c792b95-e19f-43be-8d62-7472
cp -R $P/sets/openmoji-svg ~/projects/blog/frequence/livre/assets/openmoji
ls ~/projects/blog/frequence/livre/assets/openmoji | wc -l
```

Expected: 300+ SVG files, ~1.5MB total.

- [ ] **Step 2: Write the failing test**

Create `frequence/livre/tests/test_icons.py`:

```python
import icons

ACCENT = "#B5531F"

def test_glyph_key_resolves_to_house_glyph():
    svg, kind = icons.resolve({"fr": "sur", "key": "on_box"}, ACCENT)
    assert kind == "glyph"
    assert "<svg" in svg

def test_emoji_key_resolves_to_openmoji():
    svg, kind = icons.resolve({"fr": "le chien", "key": "dog"}, ACCENT)
    assert kind == "emoji"
    assert "<svg" in svg

def test_explicit_icon_override_wins():
    """A hand-picked icon beats the automatic keyword match."""
    svg, kind = icons.resolve(
        {"fr": "manger", "key": "eat", "icon": "1F37D"}, ACCENT)
    assert kind == "emoji"
    assert "<svg" in svg

def test_blacklisted_word_gets_no_icon():
    """The joints no icon set has. A wrong icon is worse than none."""
    svg, kind = icons.resolve({"fr": "le coude", "key": "elbow"}, ACCENT)
    assert kind == "none"
    assert "dashed" in svg or "stroke-dasharray" in svg

def test_blacklist_covers_the_known_joints():
    for word in ("le coude", "le genou", "la cheville", "la joue",
                 "le front", "l'épaule", "le poignet", "la hanche", "l'ongle"):
        assert word in icons.NO_ICON, word

def test_unknown_key_gets_placeholder_not_crash():
    svg, kind = icons.resolve({"fr": "zzz", "key": "no_such_thing"}, ACCENT)
    assert kind == "none"
    assert "<svg" in svg
```

- [ ] **Step 3: Run the test to verify it fails**

```bash
cd ~/projects/blog/frequence/livre && python3 -m pytest tests/test_icons.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'icons'`.

- [ ] **Step 4: Write the implementation**

Create `frequence/livre/icons.py`:

```python
#!/usr/bin/env python3
"""Resolve a vocabulary item to an inline SVG.

Order of precedence:
  1. an explicit hand-picked `icon` (an OpenMoji hex codepoint)
  2. a house glyph, if `key` names one
  3. an OpenMoji whose filename matches `key`
  4. nothing — a dashed placeholder

Rule 4 is deliberate and is why NO_ICON exists. The automatic keyword matcher
picks plausible-but-wrong glyphs (the knee got the leg emoji, the ankle got the
foot), and a wrong picture teaches a wrong word. An empty gutter is honest, and
the cover test in greek.py gives those rows their Greek instead.
"""
import os

import glyphs

HERE = os.path.dirname(os.path.abspath(__file__))
OPENMOJI = os.path.join(HERE, "assets", "openmoji")

# Words no icon set on earth has. Verified against OpenMoji, Twemoji, Apple,
# Fluent and MDI: joints and facial sub-parts are a universal gap.
NO_ICON = frozenset({
    "le coude", "le genou", "la cheville", "la joue", "le front",
    "l'épaule", "le poignet", "la hanche", "l'ongle", "l'orteil",
    "la nuque", "le mollet", "la cuisse",
})

_PLACEHOLDER = (
    '<svg viewBox="0 0 24 24" width="24" height="24">'
    '<circle cx="12" cy="12" r="8" fill="none" stroke="#C9C7C2" '
    'stroke-width="1.2" stroke-dasharray="2 2"/></svg>'
)

_KEY_TO_HEX = {}


def _index():
    """Map a plain keyword to an OpenMoji file, once."""
    if _KEY_TO_HEX:
        return _KEY_TO_HEX
    for name in os.listdir(OPENMOJI):
        if not name.endswith(".svg"):
            continue
        stem = name[:-4]
        _KEY_TO_HEX[stem.lower()] = name
    return _KEY_TO_HEX


def _read(filename):
    return open(os.path.join(OPENMOJI, filename), encoding="utf-8").read()


def resolve(item, accent):
    """Return (svg, kind) for one item. kind is emoji | glyph | none."""
    if item["fr"] in NO_ICON:
        return _PLACEHOLDER, "none"

    explicit = item.get("icon")
    if explicit:
        name = f"{explicit}.svg"
        if os.path.exists(os.path.join(OPENMOJI, name)):
            return _read(name), "emoji"

    key = item["key"]
    svg = glyphs.render(key, accent)
    if svg:
        return svg, "glyph"

    name = _index().get(key.lower())
    if name:
        return _read(name), "emoji"

    return _PLACEHOLDER, "none"
```

**Note on the OpenMoji filenames:** the set names files by hex codepoint (`1F436.svg`), not by keyword. If that is what the copied assets look like, build `_index()` from `sets/openmoji.json` in the prototype instead, which maps annotations to codepoints. Adapt `_index()` accordingly and keep the test unchanged by adding a `dog` entry to the map.

- [ ] **Step 5: Run the test to verify it passes**

```bash
cd ~/projects/blog/frequence/livre && python3 -m pytest tests/test_icons.py -v
```

Expected: 6 passed.

- [ ] **Step 6: Commit**

```bash
cd ~/projects/blog
git add frequence/livre/icons.py frequence/livre/tests/test_icons.py frequence/livre/assets/openmoji
git commit -m "livre: icon resolution with an honest no-icon blacklist"
```

---

### Task 5: The Greek cover test

**Files:**
- Create: `frequence/livre/greek.py`
- Create: `frequence/livre/tests/test_greek.py`

**Interfaces:**
- Consumes: `icons.resolve` kind from Task 4.
- Produces: `greek.keeps_greek(fr: str, kind: str) -> bool`, `greek.SCHEMATIC: frozenset[str]`, `greek.NEAR_SYNONYM: frozenset[str]`.

The rule, from the spec: *cover the Greek — if the icon alone recovers the word, drop it; if it does not, keep it.*

- [ ] **Step 1: Write the failing test**

Create `frequence/livre/tests/test_greek.py`:

```python
import greek

def test_row_with_no_icon_keeps_greek():
    """An empty gutter is exactly where the Greek is needed most."""
    assert greek.keeps_greek("le coude", "none") is True

def test_concrete_noun_with_emoji_drops_greek():
    assert greek.keeps_greek("le chien", "emoji") is False
    assert greek.keeps_greek("la pluie", "emoji") is False

def test_schematic_glyph_word_keeps_greek():
    """A house glyph is a diagram, not a depiction — it needs a word."""
    assert greek.keeps_greek("sur", "glyph") is True
    assert greek.keeps_greek("au-dessus", "glyph") is True

def test_near_synonyms_keep_greek_even_with_an_icon():
    """loin and là-bas cannot be separated by any picture."""
    assert greek.keeps_greek("loin", "glyph") is True
    assert greek.keeps_greek("là-bas", "glyph") is True

def test_the_documented_collapsing_pairs_are_listed():
    for w in ("devant", "derrière", "au-dessus", "au-dessous",
              "sur", "contre", "loin", "là-bas", "près"):
        assert w in greek.SCHEMATIC or w in greek.NEAR_SYNONYM, w

def test_overall_rate_is_about_a_fifth():
    """The spec measured 19% across the 437-item vocabulary. Guard the order
    of magnitude so a careless edit to SCHEMATIC cannot silently restore
    Greek on every row."""
    sample = ([("le chien", "emoji")] * 80
              + [("sur", "glyph")] * 15
              + [("le coude", "none")] * 5)
    kept = sum(1 for fr, k in sample if greek.keeps_greek(fr, k))
    assert 10 <= kept <= 30
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd ~/projects/blog/frequence/livre && python3 -m pytest tests/test_greek.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'greek'`.

- [ ] **Step 3: Write the implementation**

Create `frequence/livre/greek.py`:

```python
#!/usr/bin/env python3
"""The cover test.

  Cover the Greek. If the icon alone recovers the word, drop the Greek.
  If it does not, keep it.

Measured across the 437-item vocabulary this keeps Greek on 19% of rows — 84
glosses instead of 437. The side effect is better than the saving: the Greek
stops being noise on every row and becomes a signal that something is missing.
On the body card it lands on exactly the seven joints no icon set has, and the
eye goes straight to them.
"""

# Words whose icon is a house glyph: a diagram, not a depiction. A schematic
# box-and-dot cannot carry a word on its own.
SCHEMATIC = frozenset({
    "sur", "sous", "dans", "hors de", "devant", "derrière", "entre",
    "à côté de", "autour de", "contre", "parmi", "au milieu de",
    "en face de", "le long de", "vers", "à travers",
    "au-dessus", "au-dessous",
    "ici", "là", "là-bas", "près", "loin", "tout près", "très loin",
    "partout", "nulle part", "quelque part",
    "assez", "trop", "peu", "beaucoup",
    "toujours", "souvent", "rarement", "jamais",
    "en haut", "en bas", "à gauche", "à droite", "tout droit", "en arrière",
})

# Pairs no picture separates, even when both have an icon. Each of these was
# found to collapse visually at the 26px gutter size during prototyping.
NEAR_SYNONYM = frozenset({
    "devant", "derrière",          # box+dot, near-identical at 26px
    "au-dessus", "au-dessous",     # differ only by a dashed gap line
    "sur", "contre",               # both "resting on" without a gloss
    "loin", "là-bas",              # same dot-and-dash glyph
    "près", "peu",                 # both two dots
})


def keeps_greek(fr, kind):
    """True if this row prints its Greek gloss."""
    if kind == "none":
        return True
    if fr in SCHEMATIC or fr in NEAR_SYNONYM:
        return True
    return False
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd ~/projects/blog/frequence/livre && python3 -m pytest tests/test_greek.py -v
```

Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
cd ~/projects/blog
git add frequence/livre/greek.py frequence/livre/tests/test_greek.py
git commit -m "livre: the Greek cover test"
```

---

### Task 6: Row rendering and gender colouring

**Files:**
- Create: `frequence/livre/render.py`
- Create: `frequence/livre/tests/test_render_row.py`

**Interfaces:**
- Consumes: `icons.resolve`, `greek.keeps_greek`.
- Produces: `render.split_article(fr: str) -> tuple[str, str]` and `render.row_html(item: dict, accent: str) -> str`.

Gender is carried by the **article only**, never the noun. This does not collide with any other colour coding because it occupies a different glyph slot, and it carries real information only on `l'` and `les` — which is exactly the subset learners get wrong forever.

- [ ] **Step 1: Write the failing test**

Create `frequence/livre/tests/test_render_row.py`:

```python
import render

ACCENT = "#B5531F"

def test_splits_masculine_article():
    assert render.split_article("le bras") == ("le", "bras")

def test_splits_feminine_article():
    assert render.split_article("la main") == ("la", "main")

def test_splits_elided_article():
    assert render.split_article("l'œil") == ("l'", "œil")

def test_splits_plural_article():
    assert render.split_article("les yeux") == ("les", "yeux")

def test_no_article_returns_empty():
    assert render.split_article("sur") == ("", "sur")

def test_multiword_noun_keeps_its_tail():
    assert render.split_article("la salle de bain") == ("la", "salle de bain")

def test_row_colours_the_article_not_the_noun():
    html = render.row_html({"fr": "la main", "el": "το χέρι", "key": "hand"}, ACCENT)
    assert 'class="art la"' in html
    assert "<b>main</b>" in html or ">main<" in html

def test_row_with_emoji_omits_greek():
    html = render.row_html({"fr": "le chien", "el": "ο σκύλος", "key": "dog"}, ACCENT)
    assert "ο σκύλος" not in html

def test_row_with_no_icon_prints_greek():
    html = render.row_html({"fr": "le coude", "el": "ο αγκώνας", "key": "elbow"}, ACCENT)
    assert "ο αγκώνας" in html

def test_schematic_row_prints_greek():
    html = render.row_html({"fr": "sur", "el": "πάνω σε", "key": "on_box"}, ACCENT)
    assert "πάνω σε" in html
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd ~/projects/blog/frequence/livre && python3 -m pytest tests/test_render_row.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'render'`.

- [ ] **Step 3: Write the implementation**

Create `frequence/livre/render.py`:

```python
#!/usr/bin/env python3
"""Card HTML. This module owns ALL layout; card JSON owns only content."""
import html as _html

import greek
import icons

ARTICLES = ("les ", "le ", "la ", "l'")


def split_article(fr):
    """('la main') -> ('la', 'main'). No article -> ('', fr)."""
    for art in ARTICLES:
        if fr.startswith(art):
            return art.strip(), fr[len(art):]
    return "", fr


def _article_class(art):
    return {"le": "le", "la": "la", "l'": "el", "les": "les"}.get(art, "")


def row_html(item, accent):
    """One row: icon gutter, coloured article, French, Greek only if needed."""
    svg, kind = icons.resolve(item, accent)
    art, noun = split_article(item["fr"])

    parts = [f'<span class="ic">{svg}</span>']
    if art:
        parts.append(f'<span class="art {_article_class(art)}">'
                     f'{_html.escape(art)}</span>')
    parts.append(f'<b>{_html.escape(noun)}</b>')

    if item.get("el") and greek.keeps_greek(item["fr"], kind):
        parts.append(f'<span class="el">{_html.escape(item["el"])}</span>')

    return f'<div class="wd">{"".join(parts)}</div>'
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd ~/projects/blog/frequence/livre && python3 -m pytest tests/test_render_row.py -v
```

Expected: 10 passed.

- [ ] **Step 5: Commit**

```bash
cd ~/projects/blog
git add frequence/livre/render.py frequence/livre/tests/test_render_row.py
git commit -m "livre: row rendering with gender on the article only"
```

---

### Task 7: Card rendering and the stylesheet

**Files:**
- Modify: `frequence/livre/render.py` (add `card_html`, `document_html`)
- Create: `frequence/livre/style.css`
- Create: `frequence/livre/tests/test_render_card.py`

**Interfaces:**
- Consumes: `render.row_html` from Task 6.
- Produces: `render.card_html(card: dict) -> str`, `render.document_html(cards: list[dict], title: str) -> str`.

- [ ] **Step 1: Write the failing test**

Create `frequence/livre/tests/test_render_card.py`:

```python
import render

CARD = {
    "id": "prep", "tier": 1, "order": 1,
    "title_fr": "Où ? — les prépositions", "title_el": "θέσεις στον χώρο",
    "accent": "#B5531F", "example": "Le livre est **sur** la table.",
    "items": [{"fr": "sur", "el": "πάνω σε", "key": "on_box"},
              {"fr": "dans", "el": "μέσα σε", "key": "in_box"}],
}

def test_card_has_a_rail_with_both_titles():
    h = render.card_html(CARD)
    assert "Où ? — les prépositions" in h
    assert "θέσεις στον χώρο" in h

def test_card_shows_the_item_count():
    assert ">2<" in render.card_html(CARD)

def test_card_uses_its_accent():
    assert "#B5531F" in render.card_html(CARD)

def test_card_renders_every_item():
    h = render.card_html(CARD)
    assert h.count('class="wd"') == 2

def test_example_is_rendered_with_bold_markers_expanded():
    h = render.card_html(CARD)
    assert "<strong>sur</strong>" in h
    assert "**" not in h

def test_card_without_example_omits_the_footer():
    c = dict(CARD); c["example"] = None
    assert 'class="ex"' not in render.card_html(c)

def test_small_group_gets_two_columns():
    c = dict(CARD)
    c["items"] = [{"fr": f"m{i}", "el": None, "key": "x"} for i in range(5)]
    assert "cols-2" in render.card_html(c)

def test_large_group_gets_three_columns():
    c = dict(CARD)
    c["items"] = [{"fr": f"m{i}", "el": None, "key": "x"} for i in range(18)]
    assert "cols-3" in render.card_html(c)

def test_document_inlines_the_font_and_the_stylesheet():
    doc = render.document_html([CARD], "Vocabulaire illustré")
    assert "@font-face" in doc
    assert "base64," in doc
    assert "<link" not in doc          # self-contained: nothing external

def test_document_sets_lang_and_charset():
    doc = render.document_html([CARD], "T")
    assert 'charset="utf-8"' in doc
    assert 'lang="fr"' in doc
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd ~/projects/blog/frequence/livre && python3 -m pytest tests/test_render_card.py -v
```

Expected: FAIL — `AttributeError: module 'render' has no attribute 'card_html'`.

- [ ] **Step 3: Write the stylesheet**

Create `frequence/livre/style.css`:

```css
/* Vocabulaire illustré — the C2 layout.
   Rail 18%, three-column grid, cards never split. Density target >=50/A4. */
@page { size: A4; margin: 12mm 12mm 10mm; }

:root {
  --ink:   #1A1A18;
  --grey:  #57544F;
  --faint: #C9C7C2;
  --le:    #2166B0;
  --la:    #B84066;
  --neut:  #6B6B6B;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  font-family: "Alegreya Sans", system-ui, sans-serif;
  color: var(--ink);
  background: #fff;
}

.doc-head { display: flex; align-items: baseline; gap: 8px;
            border-bottom: 1px solid var(--faint);
            padding-bottom: 3mm; margin-bottom: 5mm; }
.doc-head h1 { font-size: 19pt; margin: 0; }
.doc-head .sub { font-size: 12pt; color: var(--grey); }

/* A card is a group. It is never split across a page. */
.card {
  break-inside: avoid;
  page-break-inside: avoid;
  display: grid;
  grid-template-columns: 18% 1fr;
  border-top: 2.5px solid var(--accent);
  margin-bottom: 6mm;
}

.rail { padding: 2mm 3mm 2mm 0;
        background: linear-gradient(180deg,
          color-mix(in srgb, var(--accent) 6%, #fff), #fff); }
.rail h2 { font-size: 13pt; margin: 0 0 1mm; color: var(--accent);
           hyphens: manual; word-break: keep-all; }
.rail .el-sub { font-size: 8.5pt; color: var(--grey); display: block; }
.rail .count { display: inline-block; margin-top: 2mm; padding: 0 5px;
               border: 1px solid var(--faint); border-radius: 7px;
               font-size: 7pt; color: var(--grey); }

.body { border-left: 1px solid var(--faint); padding-left: 4mm; }

.grid { display: grid; gap: 0.6mm 4mm; }
.grid.cols-3 { grid-template-columns: repeat(3, 1fr); }
.grid.cols-2 { grid-template-columns: repeat(2, 1fr); }

/* One row. flex-wrap is what lets a long Greek gloss drop under its French
   on that row alone, instead of forcing the whole card down to two columns. */
.wd { display: flex; flex-wrap: wrap; align-items: center;
      gap: 0 4px; min-height: 7.3mm; padding: 0.7mm 0; }
.wd .ic { width: 26px; height: 26px; flex: 0 0 26px; }
.wd .ic svg { width: 26px; height: 26px; display: block; }
.wd b  { font-size: 14pt; font-weight: 700; }
.wd .art { font-size: 14pt; font-weight: 700; }
.wd .art.le  { color: var(--le); }
.wd .art.la  { color: var(--la); }
.wd .art.el, .wd .art.les { color: var(--neut); }
.wd .el { font-size: 11pt; color: var(--grey); }

/* One example sentence per card. It supplies the only thing a grid cannot:
   the words governed by something. Costs one line, costs no pages. */
.ex { margin-top: 2mm; padding-top: 1.5mm;
      border-top: 1px dotted var(--faint);
      font-size: 10.5pt; color: var(--accent); }
.ex strong { font-weight: 700; }
```

- [ ] **Step 4: Add the card and document renderers**

Append to `frequence/livre/render.py`:

```python
import base64
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "assets", "fonts")


def _columns(n):
    return 2 if n < 7 else 3


def _example_html(text):
    """`**word**` -> `<strong>word</strong>`."""
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", _html.escape(text))


def card_html(card):
    accent = card["accent"]
    rows = "".join(row_html(i, accent) for i in card["items"])
    cols = _columns(len(card["items"]))

    ex = ""
    if card.get("example"):
        ex = f'<div class="ex">{_example_html(card["example"])}</div>'

    return (
        f'<section class="card" style="--accent:{accent}">'
        f'<div class="rail">'
        f'<h2>{_html.escape(card["title_fr"])}</h2>'
        f'<span class="el-sub">{_html.escape(card["title_el"])}</span>'
        f'<span class="count">{len(card["items"])}</span>'
        f'</div>'
        f'<div class="body"><div class="grid cols-{cols}">{rows}</div>{ex}</div>'
        f'</section>'
    )


def _font_face():
    """Inline both weights so the HTML is self-contained."""
    out = []
    for fname, weight in (("AlegreyaSans-Regular.ttf", 400),
                          ("AlegreyaSans-Bold.ttf", 700)):
        b64 = base64.b64encode(open(os.path.join(FONTS, fname), "rb").read()).decode()
        out.append(
            '@font-face{font-family:"Alegreya Sans";'
            f'font-weight:{weight};font-style:normal;'
            f'src:url(data:font/ttf;base64,{b64}) format("truetype");}}'
        )
    return "".join(out)


def document_html(cards, title, subtitle="εικονογραφημένο λεξιλόγιο"):
    css = open(os.path.join(HERE, "style.css"), encoding="utf-8").read()
    body = "".join(card_html(c) for c in cards)
    return (
        '<!doctype html><html lang="fr"><head><meta charset="utf-8">'
        f"<title>{_html.escape(title)}</title>"
        f"<style>{_font_face()}{css}</style></head><body>"
        f'<header class="doc-head"><h1>{_html.escape(title)}</h1>'
        f'<span class="sub">{_html.escape(subtitle)}</span></header>'
        f"{body}</body></html>"
    )
```

- [ ] **Step 5: Run the test to verify it passes**

```bash
cd ~/projects/blog/frequence/livre && python3 -m pytest tests/test_render_card.py -v
```

Expected: 10 passed.

- [ ] **Step 6: Commit**

```bash
cd ~/projects/blog
git add frequence/livre/render.py frequence/livre/style.css frequence/livre/tests/test_render_card.py
git commit -m "livre: card layout and self-contained document rendering"
```

---

### Task 8: The build CLI

**Files:**
- Create: `frequence/livre/build.py`
- Create: `frequence/livre/tests/test_build.py`

**Interfaces:**
- Consumes: `cards.load_all`, `render.document_html`, `topdf.render`.
- Produces: `build.build(cards_dir: str, out_dir: str, tiers: tuple[int, ...] = (1, 2, 3)) -> tuple[str, str]` returning `(html_path, pdf_path)`.

- [ ] **Step 1: Write the failing test**

Create `frequence/livre/tests/test_build.py`:

```python
import json, os, tempfile
import build, topdf

CARD = {
    "id": "t", "tier": 1, "order": 1,
    "title_fr": "Test", "title_el": "δοκιμή", "accent": "#B5531F",
    "example": None,
    "items": [{"fr": "sur", "el": "πάνω σε", "key": "on_box"}],
}

def _fixture(d, **over):
    c = dict(CARD); c.update(over)
    json.dump(c, open(os.path.join(d, f"{c['id']}.json"), "w", encoding="utf-8"),
              ensure_ascii=False)

def test_build_writes_html_and_pdf():
    with tempfile.TemporaryDirectory() as d:
        cd = os.path.join(d, "cards"); os.makedirs(cd)
        _fixture(cd)
        h, p = build.build(cd, os.path.join(d, "out"))
        assert os.path.exists(h) and os.path.exists(p)
        assert topdf.page_count(p) >= 1

def test_html_is_self_contained():
    with tempfile.TemporaryDirectory() as d:
        cd = os.path.join(d, "cards"); os.makedirs(cd)
        _fixture(cd)
        h, _ = build.build(cd, os.path.join(d, "out"))
        src = open(h, encoding="utf-8").read()
        assert "<link" not in src
        assert "<img" not in src

def test_tier_filter_selects_cards():
    with tempfile.TemporaryDirectory() as d:
        cd = os.path.join(d, "cards"); os.makedirs(cd)
        _fixture(cd, id="a", tier=1)
        _fixture(cd, id="b", tier=3)
        h, _ = build.build(cd, os.path.join(d, "out"), tiers=(1,))
        assert open(h, encoding="utf-8").read().count('class="card"') == 1
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd ~/projects/blog/frequence/livre && python3 -m pytest tests/test_build.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'build'`.

- [ ] **Step 3: Write the implementation**

Create `frequence/livre/build.py`:

```python
#!/usr/bin/env python3
"""Build the textbook: card JSON -> one self-contained HTML -> A4 PDF.

The HTML is a first-class output, not an intermediate. It is what puts the
book on a phone instead of in a drawer.
"""
import argparse
import os

import cards
import render
import topdf

HERE = os.path.dirname(os.path.abspath(__file__))
TITLE = "Vocabulaire illustré"


def build(cards_dir, out_dir, tiers=(1, 2, 3), title=TITLE):
    os.makedirs(out_dir, exist_ok=True)
    selected = [c for c in cards.load_all(cards_dir) if c["tier"] in tiers]
    if not selected:
        raise SystemExit(f"no cards in {cards_dir} for tiers {tiers}")

    html_path = os.path.join(out_dir, "livre.html")
    pdf_path = os.path.join(out_dir, "livre.pdf")
    open(html_path, "w", encoding="utf-8").write(
        render.document_html(selected, title))
    topdf.render(html_path, pdf_path)

    items = sum(len(c["items"]) for c in selected)
    pages = topdf.page_count(pdf_path)
    print(f"{len(selected)} cards, {items} items, {pages} pages "
          f"({items/pages:.0f}/page)  ->  {pdf_path}")
    return html_path, pdf_path


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cards", default=os.path.join(HERE, "data", "cards"))
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    ap.add_argument("--tiers", default="1,2,3")
    a = ap.parse_args()
    build(a.cards, a.out, tuple(int(t) for t in a.tiers.split(",")))
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd ~/projects/blog/frequence/livre && python3 -m pytest tests/test_build.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
cd ~/projects/blog
git add frequence/livre/build.py frequence/livre/tests/test_build.py
git commit -m "livre: build CLI"
```

---

### Task 9: The clock card — first real content

**Files:**
- Create: `frequence/livre/data/cards/03-heure.json`
- Create: `frequence/livre/tests/test_card_files.py`

The spec says build this first. *A dial showing 3:15 cannot mean anything else, in any language, at any age* — it is the only block in the book that is unambiguous by construction, it is the highest-value page for a seven-year-old, and it is the cheapest validation of the whole pipeline.

**Interfaces:**
- Consumes: the schema from Task 2, the glyph keys from Task 3.
- Produces: `data/cards/03-heure.json`, the first real card.

- [ ] **Step 1: Write the failing test**

Create `frequence/livre/tests/test_card_files.py`:

```python
import glob, os
import cards, icons, render

HERE = os.path.dirname(os.path.abspath(__file__))
CARDS = os.path.join(HERE, "..", "data", "cards")

def test_every_card_file_is_valid():
    files = glob.glob(os.path.join(CARDS, "*.json"))
    assert files, "no card files yet"
    for f in files:
        cards.load_card(f)

def test_every_card_renders():
    for c in cards.load_all(CARDS):
        assert render.card_html(c)

def test_no_card_has_duplicate_french():
    for c in cards.load_all(CARDS):
        words = [i["fr"] for i in c["items"]]
        assert len(words) == len(set(words)), f"{c['id']}: duplicate entries"

def test_clock_card_exists_and_covers_the_quarters():
    c = cards.load_card(os.path.join(CARDS, "03-heure.json"))
    words = " ".join(i["fr"] for i in c["items"])
    for needed in ("et quart", "et demie", "moins le quart", "midi", "minuit"):
        assert needed in words, needed

def test_clock_card_has_an_example():
    c = cards.load_card(os.path.join(CARDS, "03-heure.json"))
    assert c["example"]
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd ~/projects/blog/frequence/livre && python3 -m pytest tests/test_card_files.py -v
```

Expected: FAIL — no card files.

- [ ] **Step 3: Write the card**

Create `frequence/livre/data/cards/03-heure.json`:

```json
{
  "id": "heure",
  "tier": 1,
  "order": 3,
  "title_fr": "L'heure",
  "title_el": "η ώρα",
  "accent": "#2166B0",
  "example": "Il est **huit heures et quart**. On mange à **midi**. Le train part à **quatorze heures**.",
  "items": [
    {"fr": "il est une heure",        "el": "είναι μία η ώρα",     "key": "clock_1"},
    {"fr": "deux heures",             "el": null,                  "key": "clock_2"},
    {"fr": "trois heures",            "el": null,                  "key": "clock_3"},
    {"fr": "quatre heures",           "el": null,                  "key": "clock_4"},
    {"fr": "cinq heures",             "el": null,                  "key": "clock_5"},
    {"fr": "six heures",              "el": null,                  "key": "clock_6"},
    {"fr": "sept heures",             "el": null,                  "key": "clock_7"},
    {"fr": "huit heures",             "el": null,                  "key": "clock_8"},
    {"fr": "neuf heures",             "el": null,                  "key": "clock_9"},
    {"fr": "dix heures",              "el": null,                  "key": "clock_10"},
    {"fr": "onze heures",             "el": null,                  "key": "clock_11"},
    {"fr": "midi",                    "el": "μεσημέρι",            "key": "clock_12"},
    {"fr": "minuit",                  "el": "μεσάνυχτα",           "key": "clock_00"},
    {"fr": "et quart",                "el": "και τέταρτο",         "key": "clock_q15"},
    {"fr": "et demie",                "el": "και μισή",            "key": "clock_q30"},
    {"fr": "moins le quart",          "el": "παρά τέταρτο",        "key": "clock_q45"},
    {"fr": "moins dix",               "el": "παρά δέκα",           "key": "clock_m10"},
    {"fr": "pile",                    "el": "ακριβώς",             "key": "clock_sharp"},
    {"fr": "quatorze heures",         "el": "δύο το μεσημέρι (24ωρο)", "key": "clock_24"},
    {"fr": "il est tôt",              "el": "είναι νωρίς",         "key": "early"},
    {"fr": "il est tard",             "el": "είναι αργά",          "key": "late"},
    {"fr": "en retard",               "el": "καθυστερημένος",      "key": "late_person"},
    {"fr": "à l'heure",               "el": "στην ώρα",            "key": "on_time"},
    {"fr": "une demi-heure",          "el": "μισή ώρα",            "key": "half_hour"},
    {"fr": "un quart d'heure",        "el": "ένα τέταρτο",         "key": "quarter_hour"},
    {"fr": "une minute",              "el": null,                  "key": "minute"},
    {"fr": "une seconde",             "el": null,                  "key": "second"}
  ]
}
```

- [ ] **Step 4: Add the clock dial glyphs**

The `clock_*` keys need house glyphs — a dial is a circle with two hands, and a
dial showing a given time is generated, not hand-drawn. Append to
`frequence/livre/glyphs.py`:

```python
import math


def _dial(hour, minute, accent):
    """A clock face at a given time. The dial IS the meaning — this is the one
    glyph in the book that is unambiguous in every language at every age."""
    def hand(angle_deg, length, width):
        a = math.radians(angle_deg - 90)
        x = 12 + length * math.cos(a)
        y = 12 + length * math.sin(a)
        return (f'<line x1="12" y1="12" x2="{x:.2f}" y2="{y:.2f}" '
                f'stroke="{accent}" stroke-width="{width}" '
                f'stroke-linecap="round"/>')

    face = (f'<circle cx="12" cy="12" r="9.5" fill="none" '
            f'stroke="{GREY}" stroke-width="1.4"/>')
    ticks = "".join(
        f'<circle cx="{12 + 8 * math.cos(math.radians(t * 30 - 90)):.2f}" '
        f'cy="{12 + 8 * math.sin(math.radians(t * 30 - 90)):.2f}" '
        f'r="0.6" fill="{GREY}"/>' for t in range(12))
    h_ang = (hour % 12) * 30 + minute * 0.5
    return _svg(face + ticks + hand(h_ang, 4.6, 1.9) + hand(minute * 6, 7.0, 1.3))


for _h in range(1, 13):
    GLYPHS[f"clock_{_h}"] = (lambda h: lambda a: _dial(h, 0, a))(_h)
GLYPHS["clock_00"] = lambda a: _dial(12, 0, a)
GLYPHS["clock_q15"] = lambda a: _dial(3, 15, a)
GLYPHS["clock_q30"] = lambda a: _dial(3, 30, a)
GLYPHS["clock_q45"] = lambda a: _dial(3, 45, a)
GLYPHS["clock_m10"] = lambda a: _dial(3, 50, a)
GLYPHS["clock_sharp"] = lambda a: _dial(3, 0, a)
GLYPHS["clock_24"] = lambda a: _dial(2, 0, a)
```

- [ ] **Step 5: Run the tests to verify they pass**

```bash
cd ~/projects/blog/frequence/livre && python3 -m pytest tests -q
```

Expected: all tests pass, including the new card-file tests.

- [ ] **Step 6: Build it and look at it**

```bash
cd ~/projects/blog/frequence/livre && make livre && open out/livre.pdf out/livre.html
```

Expected: one card, 27 items, 1 page. Dials legible at 26px. Greek present only
on the rows the cover test keeps.

- [ ] **Step 7: Commit**

```bash
cd ~/projects/blog
git add frequence/livre
git commit -m "livre: the clock card, generated dials, first real content"
```

---

### Task 10: Density guard

**Files:**
- Create: `frequence/livre/tests/test_density.py`

The spec's density target is a requirement, not an aspiration. This test is what
stops a future styling change quietly turning a 53-item page into a 20-item one —
which is the exact regression this design already went through once.

**Interfaces:**
- Consumes: `build.build`, `topdf.page_count`.
- Produces: nothing; a guard.

- [ ] **Step 1: Write the failing test**

Create `frequence/livre/tests/test_density.py`:

```python
import json, os, tempfile
import build, topdf

def _card(idx, n_items):
    return {
        "id": f"c{idx}", "tier": 1, "order": idx,
        "title_fr": f"Groupe {idx}", "title_el": "ομάδα",
        "accent": "#B5531F", "example": None,
        "items": [{"fr": f"mot{idx}_{i}", "el": None, "key": "on_box"}
                  for i in range(n_items)],
    }

def test_a_full_page_carries_at_least_fifty_items():
    """The agreed target is 53/A4. Guard the floor at 50."""
    with tempfile.TemporaryDirectory() as d:
        cd = os.path.join(d, "cards"); os.makedirs(cd)
        for i in range(4):
            c = _card(i, 24)
            json.dump(c, open(os.path.join(cd, f"{i}.json"), "w",
                              encoding="utf-8"), ensure_ascii=False)
        _, pdf = build.build(cd, os.path.join(d, "out"))
        items = 4 * 24
        pages = topdf.page_count(pdf)
        assert items / pages >= 50, f"{items/pages:.0f}/page, want >=50"

def test_a_card_is_never_split_across_pages():
    """break-inside:avoid must hold, or a group stops being seen whole."""
    with tempfile.TemporaryDirectory() as d:
        cd = os.path.join(d, "cards"); os.makedirs(cd)
        for i in range(3):
            c = _card(i, 30)
            json.dump(c, open(os.path.join(cd, f"{i}.json"), "w",
                              encoding="utf-8"), ensure_ascii=False)
        _, pdf = build.build(cd, os.path.join(d, "out"))
        # 3 cards of 30 cannot fit on one page; with avoid they land on 2,
        # never 2-with-a-split (which would also be 2 but is visually broken).
        assert topdf.page_count(pdf) in (2, 3)
```

- [ ] **Step 2: Run the test**

```bash
cd ~/projects/blog/frequence/livre && python3 -m pytest tests/test_density.py -v
```

Expected: PASS if Task 7's CSS is correct. **If the density test fails, the CSS
is wrong, not the test** — reduce `.wd` `min-height` and the grid `gap` until it
passes, and do not touch the 26px icon or the 14pt French, which are fixed by
the spec.

- [ ] **Step 3: Commit**

```bash
cd ~/projects/blog
git add frequence/livre/tests/test_density.py
git commit -m "livre: density and no-split guards"
```

---

### Task 11: Two more cards, and the web output

**Files:**
- Create: `frequence/livre/data/cards/02-espace.json`
- Create: `frequence/livre/data/cards/05-verbes.json`
- Modify: `frequence/livre/Makefile`
- Modify: `frequence/livre/build.py` (publish target)

**Interfaces:**
- Consumes: everything above.
- Produces: `data/cards/02-espace.json` (14 items, all house glyphs, all keep
  Greek), `data/cards/05-verbes.json` (22 items, all OpenMoji, none keep Greek).

These two are chosen deliberately: together they exercise both ends of the cover
test in one build, so a regression in either direction shows up immediately.

- [ ] **Step 1: Write the space card**

Create `frequence/livre/data/cards/02-espace.json`:

```json
{
  "id": "espace", "tier": 1, "order": 2,
  "title_fr": "Où ? — les prépositions", "title_el": "θέσεις στον χώρο",
  "accent": "#B5531F",
  "example": "Le livre est **sur** la table, le chat dort **sous** la chaise, et la clé est **dans** le sac.",
  "items": [
    {"fr": "sur",         "el": "πάνω σε",              "key": "on_box"},
    {"fr": "sous",        "el": "κάτω από",             "key": "under_box"},
    {"fr": "dans",        "el": "μέσα σε",              "key": "in_box"},
    {"fr": "hors de",     "el": "έξω από",              "key": "out_box"},
    {"fr": "devant",      "el": "μπροστά από",          "key": "front_box"},
    {"fr": "derrière",    "el": "πίσω από",             "key": "behind_box"},
    {"fr": "entre",       "el": "ανάμεσα σε δύο",       "key": "between_box"},
    {"fr": "à côté de",   "el": "δίπλα σε",             "key": "beside_box"},
    {"fr": "autour de",   "el": "γύρω από",             "key": "around_box"},
    {"fr": "contre",      "el": "ακουμπά σε",           "key": "against_box"},
    {"fr": "au-dessus",   "el": "ψηλότερα, χωρίς επαφή", "key": "above_gap"},
    {"fr": "au-dessous",  "el": "χαμηλότερα, χωρίς επαφή", "key": "below_gap"},
    {"fr": "à travers",   "el": "μέσα από",             "key": "through_box"},
    {"fr": "vers",        "el": "προς",                 "key": "toward_box"}
  ]
}
```

Note `contre` is glossed `ακουμπά σε`, not `πάνω στο`. The prototype had `sur`
and `contre` both glossed with πάνω, which reads as the same word.

- [ ] **Step 2: Write the verbs card**

Create `frequence/livre/data/cards/05-verbes.json`:

```json
{
  "id": "verbes", "tier": 1, "order": 5,
  "title_fr": "Les verbes de tous les jours", "title_el": "καθημερινά ρήματα",
  "accent": "#1E7A5A",
  "example": "Le matin je **cours**, le soir je **lis** ; il **mange**, il **boit**, puis il **dort**.",
  "items": [
    {"fr": "marcher",   "el": "περπατώ",  "key": "walk"},
    {"fr": "courir",    "el": "τρέχω",    "key": "run",   "icon": "1F3C3"},
    {"fr": "dormir",    "el": "κοιμάμαι", "key": "sleep"},
    {"fr": "manger",    "el": "τρώω",     "key": "eat",   "icon": "1F37D"},
    {"fr": "boire",     "el": "πίνω",     "key": "drink"},
    {"fr": "pleurer",   "el": "κλαίω",    "key": "cry"},
    {"fr": "rire",      "el": "γελώ",     "key": "laugh", "icon": "1F602"},
    {"fr": "parler",    "el": "μιλώ",     "key": "speak"},
    {"fr": "écouter",   "el": "ακούω",    "key": "listen"},
    {"fr": "regarder",  "el": "κοιτάζω",  "key": "look"},
    {"fr": "lire",      "el": "διαβάζω",  "key": "read"},
    {"fr": "écrire",    "el": "γράφω",    "key": "write"},
    {"fr": "travailler","el": "δουλεύω",  "key": "work"},
    {"fr": "nager",     "el": "κολυμπώ",  "key": "swim"},
    {"fr": "danser",    "el": "χορεύω",   "key": "dance"},
    {"fr": "chanter",   "el": "τραγουδώ", "key": "sing"},
    {"fr": "jouer",     "el": "παίζω",    "key": "play"},
    {"fr": "acheter",   "el": "αγοράζω",  "key": "buy"},
    {"fr": "payer",     "el": "πληρώνω",  "key": "pay"},
    {"fr": "ouvrir",    "el": "ανοίγω",   "key": "open"},
    {"fr": "fermer",    "el": "κλείνω",   "key": "close"},
    {"fr": "attendre",  "el": "περιμένω", "key": "wait"}
  ]
}
```

The three `icon` overrides are real corrections found by eye in the prototype:
the automatic matcher gave `courir` a wind-puff, `manger` a bare apple and
`rire` a **cat face**. This is what the ~450-item icon pass in plan 2 looks like.

- [ ] **Step 3: Add a test that both ends of the cover test hold**

Append to `frequence/livre/tests/test_card_files.py`:

```python
def test_space_card_keeps_greek_on_every_row():
    """All house glyphs — schematic, so every row needs its word."""
    c = cards.load_card(os.path.join(CARDS, "02-espace.json"))
    h = render.card_html(c)
    for item in c["items"]:
        assert item["el"] in h, item["fr"]

def test_verbs_card_drops_greek_on_every_row():
    """All emoji — the picture carries it, so no Greek at all."""
    c = cards.load_card(os.path.join(CARDS, "05-verbes.json"))
    h = render.card_html(c)
    for item in c["items"]:
        assert item["el"] not in h, item["fr"]
```

- [ ] **Step 4: Run the full suite**

```bash
cd ~/projects/blog/frequence/livre && python3 -m pytest tests -q
```

Expected: all pass. **If `test_verbs_card_drops_greek_on_every_row` fails**, an
entry has landed in `greek.SCHEMATIC` that should not be there.

- [ ] **Step 5: Add the publish target**

Append to `frequence/livre/Makefile`:

```make
publish: livre  ## copy the HTML to the site root for GitHub Pages
	mkdir -p ../../livre
	cp out/livre.html ../../livre/index.html
	@echo "published -> blog/livre/index.html"
```

- [ ] **Step 6: Build, look, publish**

```bash
cd ~/projects/blog/frequence/livre && make livre && open out/livre.pdf
make publish
```

Expected: 3 cards, 63 items, 2 pages. Greek on all 14 space rows, none on the 22
verb rows, and on the clock only where the gloss is doing work.

- [ ] **Step 7: Commit and push**

```bash
cd ~/projects/blog
git add -A
git commit -m "livre: space and verb cards, web publish target"
git push origin main
```

---

## Self-review

**Spec coverage.** Pipeline (Task 1) · card data model (2) · house glyphs incl.
the day/month tiles (3) · OpenMoji + overrides + the no-icon blacklist (4) ·
the Greek cover test (5) · gender on the article only (6) · the C2 card layout,
18% rail, 3 columns, example footer (7) · build and tier filter (8) · the clock
card first, as the spec directs (9) · the 53/page density target as an
executable guard (10) · both ends of the cover test exercised, and the HTML web
output (11).

**Deferred to later plans, by design:** the remaining ~47 cards and their
content (plan 2: ~450 icon decisions, 84 Greek glosses, ~50 headings and
examples); the 1,332-phrase segmentation, Greek translation and rendering (plan
3); retiring `build_phrases.py` and binding the two halves, which cannot happen
until plan 3 lands.

**Not covered, and named so it is not forgotten:** `phrases.tsv:348`
(`composter` is SNCF, meaningless on CFF) and lines 450/452 (`un sac` should
offer `un cornet`) still need a judgement call; and
`jeu/data/noms_propres.txt` still files the days and months as proper nouns,
which should move to a new `ensembles_fermes.txt`.

**Type consistency.** `render(html_path, pdf_path)` and `page_count(pdf_path)`
are used identically in Tasks 1, 8, 10. `resolve(item, accent) -> (svg, kind)`
with `kind in {emoji, glyph, none}` is produced in Task 4 and consumed in 5 and
6. `keeps_greek(fr, kind)` matches. `GLYPHS`/`render(key, accent)` from Task 3
are used in Task 4 and extended in Task 9. Card keys (`id tier order title_fr
title_el accent example items`) are identical in Tasks 2, 7, 8, 9, 10, 11.
