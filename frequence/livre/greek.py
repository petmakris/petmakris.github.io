#!/usr/bin/env python3
"""The cover test.

  Cover the Greek. If the icon alone recovers the word, drop the Greek.
  If it does not, keep it.

The test is about the WORD, and a picture can only ever return the word. A
gloss that also explains — a gender warning, a Swiss/France contrast, what
the thing is used for, a homonym trap — is never recoverable from any icon,
however good, so it prints whatever the icon does. Those glosses announce
themselves: they carry a clause marker, or they simply run longer than the
one or two words plus an article that a bare translation needs.

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
    # 01c-famille.json: the girl emoji depicts a girl, so it recovers only
    # half of "la fille" — the family-card sense (κόρη, a daughter) is a
    # relation no picture of a child can carry. The split gloss is the whole
    # point of the entry, so it must print.
    "la fille",
    # 11-emotions.json: the icon shows an object instead of the feeling
    # (fier -> 1st-place medal, faim -> fork and knife, soif -> drink cup —
    # those depict winning, eating and drinking, not pride, hunger, thirst),
    # or a face too vague to tell from its neighbour on the same card (gêné
    # 1F605 and peur 1FAE3 are both an awkward grimace; inquiet 1F614
    # pensive and triste 1F622 crying are one register). Each is also an
    # "avoir/être + X" idiom answering to a plain Greek verb, and the gloss
    # is the only place that split — the card's whole question — is written.
    "être fier", "être gêné", "être inquiet",
    "avoir peur", "avoir faim", "avoir soif",
    # 09-couleurs.json: the coloured heart carries the colour perfectly well,
    # but not the homonym warning that is the point of these three rows —
    # «une orange» is the fruit, «une rose» the flower, «un marron» the
    # chestnut. No picture of a colour can say that, so the notes were being
    # authored on the card and then silently dropped from the page.
    "orange", "rose", "marron",
    # 07-meteo.json: the elided article hides the gender, and the gloss is the
    # only place «orage» is written as masculine — a storm cloud cannot carry
    # that, exactly as the girl emoji cannot carry «la fille».
    "l'orage",
    # 07-meteo.json: an ice cube is a noun (un glaçon) standing in for a verb.
    # Cover the Greek and the picture gives "ice", not "it is freezing" — the
    # same failure as travailler -> briefcase above.
    "il gèle",
    # 31-epeler.json: the writing hand gives "écrire", not "épeler" — the same
    # noun/verb miss as travailler -> briefcase. The speaking head cannot carry
    # the spelling-alphabet convention behind "M comme Marcel", the abacus
    # cannot carry the Swiss habit of dictating digits in pairs, 🔢 gives
    # "numbers" and not what NPA stands for, and the houses recover "town"
    # but not the rule that the localité is written AFTER the NPA. Every one
    # of those is the entry's whole point, and it lives only in the gloss.
    "épeler", "M comme Marcel", "deux par deux", "le NPA", "la localité",
})


# A bare Greek translation of one French word runs to about 26 characters —
# an article and one or two words, sometimes a second synonym after a comma.
# Past that, or once one of these marks appears, the gloss has started saying
# something the picture cannot: a parenthetical, a clause after a colon or an
# ano teleia, a dash, a quoted French form.
BARE_GLOSS_MAX = 26
EXPLAINS = "(\u00b7\u2014:;\u00ab"


def explains(el):
    """True if this gloss carries more than the word itself."""
    return len(el) > BARE_GLOSS_MAX or any(c in el for c in EXPLAINS)


def keeps_greek(fr, kind, el=""):
    """True if this row prints its Greek gloss."""
    if kind == "none":
        return True
    if kind == "glyph":
        return True
    if fr in SCHEMATIC:
        return True
    return explains(el)
