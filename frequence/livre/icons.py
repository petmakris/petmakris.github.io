#!/usr/bin/env python3
"""Resolve a vocabulary item to an inline SVG.

Order of precedence:
  1. an explicit hand-picked `icon` (an OpenMoji hex codepoint) — always wins,
     even for a NO_ICON word: a human pick is not the automatic matcher.
  2. a house glyph, if `key` names one
  3. an OpenMoji whose annotation keyword matches `key` — but NOT for a
     NO_ICON word: this step is the automatic matcher NO_ICON exists to stop.
  4. nothing — a dashed placeholder

NO_ICON exists to stop the AUTOMATIC keyword matcher (step 3) from picking
plausible-but-wrong glyphs (the knee got the leg emoji, the ankle got the
foot) — it says nothing about a hand-picked `icon`, which by definition is
not automatic. A wrong automatic picture teaches a wrong word, which is worse
than none; a human's own pick is not that failure mode. An empty gutter for a
NO_ICON word with no override is honest, and a later module gives that row
its Greek gloss instead.

The keyword index (assets/openmoji-index.json) maps a lowercase OpenMoji
annotation to a hex codepoint, but ONLY for codepoints that actually have an
SVG file in assets/openmoji/ — it was trimmed down from the 2.2MB upstream
openmoji.json, which is keyed by annotation/tags, not by filename: the
shipped SVGs are named by hex codepoint (`1F436.svg`), not by keyword.
"""
import json
import os

import glyphs

HERE = os.path.dirname(os.path.abspath(__file__))
OPENMOJI = os.path.join(HERE, "assets", "openmoji")
INDEX_PATH = os.path.join(HERE, "assets", "openmoji-index.json")

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
    """Map a plain keyword to an OpenMoji hex codepoint, once."""
    if _KEY_TO_HEX:
        return _KEY_TO_HEX
    with open(INDEX_PATH, encoding="utf-8") as f:
        _KEY_TO_HEX.update(json.load(f))
    return _KEY_TO_HEX


def _read(hexcode):
    path = os.path.join(OPENMOJI, f"{hexcode}.svg")
    return open(path, encoding="utf-8").read()


def explicit_icon_missing(item):
    """True if item has a hand-picked `icon` whose SVG is not shipped.

    None if the item has no explicit `icon` at all — that's not a failure,
    it's the normal automatic-matching or placeholder path, and callers
    (build's --strict) must not treat it as one.
    """
    explicit = item.get("icon")
    if not explicit:
        return None
    return not os.path.exists(os.path.join(OPENMOJI, f"{explicit}.svg"))


def resolve(item, accent):
    """Return (svg, kind) for one item. kind is emoji | glyph | none."""
    explicit = item.get("icon")
    if explicit:
        if os.path.exists(os.path.join(OPENMOJI, f"{explicit}.svg")):
            return _read(explicit), "emoji"

    key = item["key"]
    svg = glyphs.render(key, accent)
    if svg:
        return svg, "glyph"

    if item["fr"] not in NO_ICON:
        hexcode = _index().get(key.lower())
        if hexcode:
            return _read(hexcode), "emoji"

    return _PLACEHOLDER, "none"
