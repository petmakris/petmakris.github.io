import greek

def test_row_with_no_icon_keeps_greek():
    """An empty gutter is exactly where the Greek is needed most."""
    assert greek.keeps_greek("le coude", "none") is True

def test_concrete_noun_with_emoji_drops_greek():
    assert greek.keeps_greek("le chien", "emoji") is False
    assert greek.keeps_greek("la pluie", "emoji") is False

def test_every_glyph_keeps_greek_unconditionally():
    """A house glyph is a diagram, not a depiction — it needs its word,
    regardless of whether anyone remembered to list it. This is the fix:
    keying on `kind`, not on a word list that 40 of 82 glyphs were missing
    from (the clock dials among them)."""
    assert greek.keeps_greek("sur", "glyph") is True
    assert greek.keeps_greek("au-dessus", "glyph") is True
    # Real clock-card words that the old SCHEMATIC list never mentioned —
    # they were silently dropping Greek before this fix.
    assert greek.keeps_greek("pile", "glyph") is True
    assert greek.keeps_greek("quatorze heures", "glyph") is True
    assert greek.keeps_greek("midi", "glyph") is True

def test_schematic_is_an_emoji_side_override_only():
    """SCHEMATIC no longer gates glyphs (kind == "glyph" alone does that).
    Its only remaining job is overriding emoji rows whose picture doesn't
    carry the word — e.g. the noun-for-verb icons on 05-verbes.json."""
    for w in ("travailler", "payer", "acheter", "manger", "attendre",
              "lire", "écouter", "jouer", "ouvrir", "fermer"):
        assert w in greek.SCHEMATIC, w
        assert greek.keeps_greek(w, "emoji") is True

def test_overall_rate_rises_with_the_fix():
    """Mirrors the real mix: concrete emoji nouns that drop, an emoji-side
    SCHEMATIC override, plain schematic glyphs, a glyph word that was never
    in the old word list (quatorze heures — a real clock-card entry), and a
    no-icon row.

    Under the OLD code (glyph gated through SCHEMATIC membership) this exact
    sample kept 15/100: the 5 "none" rows plus the 10 "sur" rows, while the
    10 "quatorze heures" rows and the 5 "travailler" rows were silently
    dropped. Under the fix all of them keep, so the count rises to 30/100.
    Keep the bound wide — this guards the fix raised the rate at all and
    didn't overshoot to "keeps almost everything", not an exact figure."""
    sample = ([("le chien", "emoji")] * 70
              + [("travailler", "emoji")] * 5
              + [("sur", "glyph")] * 10
              + [("quatorze heures", "glyph")] * 10
              + [("le coude", "none")] * 5)
    kept = sum(1 for fr, k in sample if greek.keeps_greek(fr, k))
    assert kept == 30
    assert 20 <= kept <= 45


def test_a_bare_translation_is_dropped_next_to_an_emoji():
    """`με το λεωφορείο` beside a bus emoji is the noise the cover test
    exists to remove."""
    assert not greek.keeps_greek("en bus", "emoji", "με το λεωφορείο")


def test_an_explanatory_gloss_survives_its_emoji():
    """A picture returns the word and nothing else. Anything the gloss adds
    on top — a gender, a Swiss/France contrast, what the thing is for — is
    unrecoverable, so it prints however good the icon is. These three were
    all being authored and then thrown away."""
    for fr, el in (
        ("l'abonnement",
         "η κάρτα απεριορίστων διαδρομών, η συνδρομή (αρσενικό: un abonnement)"),
        ("les CFF", "οι ελβετικοί σιδηρόδρομοι, στη Γαλλία λέγονται SNCF"),
        ("en France", "στη Γαλλία· la France, θηλυκή"),
    ):
        assert greek.keeps_greek(fr, "emoji", el), fr


def test_a_glyph_keeps_its_greek_whatever_the_gloss():
    assert greek.keeps_greek("vingt", "glyph", "είκοσι")
