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
