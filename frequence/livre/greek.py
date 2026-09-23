#!/usr/bin/env python3
"""The cover test.

  Cover the Greek. If the icon alone recovers the word, drop the Greek.
  If it does not, keep it.

A house glyph is never enough on its own: it is a diagram (a grey reference
plus a coloured subject), not a depiction, so every glyph-kind row keeps its
Greek unconditionally — there is no word list to fall out of sync with the
glyph set as it grows. SCHEMATIC now does one job only: it is a hand-picked
override for words whose icon IS a depiction (an emoji, including a
hand-picked `icon`) that still fails the cover test — a noun standing in for
a verb, or a picture two entries can't be told apart by.
"""

# Emoji-side overrides: the icon resolved (kind == "emoji"), but it does not
# actually carry the word, so the Greek must print anyway.
SCHEMATIC = frozenset({
    # 05-verbes.json: these depict an object, not the action (travailler ->
    # briefcase, payer -> money bag, acheter -> trolley, manger -> plate,
    # attendre -> hourglass, lire -> book, écouter -> headphones, jouer ->
    # game controller), or a state rather than an action (ouvrir/fermer ->
    # padlocks). Candidates for a dedicated icon pass; until then the word
    # carries what the picture can't.
    "travailler", "payer", "acheter", "manger", "attendre", "lire",
    "écouter", "jouer", "ouvrir", "fermer",
})


def keeps_greek(fr, kind):
    """True if this row prints its Greek gloss."""
    if kind == "none":
        return True
    if kind == "glyph":
        return True
    if fr in SCHEMATIC:
        return True
    return False
