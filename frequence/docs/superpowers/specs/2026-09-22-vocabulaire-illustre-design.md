# Vocabulaire illustré — design

**Date:** 2026-09-22
**Status:** design agreed, implementation not started
**Supersedes:** nothing. Extends `phrases/` into a full textbook.

## What this is

One printed textbook, in French and Greek, for Petros and Myrto. It has two
halves bound as one document:

- **Les mots** — closed sets of single words, one card per set, each word
  carrying a colour icon. New.
- **Les phrases** — the existing 1,332 curated phrases, re-rendered in the same
  visual language and grouped into cards. Migrated.

The existing `build_phrases.py` reportlab build is retired. Both halves render
from one HTML source through one pipeline.

## Who it is for

Petros — Greek, 45, six months in Lausanne, one class a week at ECAP, roughly
A1/A2, not studying between classes. Myrto — 7, Greek, treated for design
purposes as a near-beginner like her father.

The two read the same page differently and the page never says so. She reads the
icon and points; he reads the word and the gloss. The boundary is carried by
density and by picture, never by a heading — a label saying "the child's pages"
delights a six-year-old and is refused by a nine-year-old.

## The principle that bounds the book

The front half exists because some words cannot be taught one at a time, and the
two formats this repo already has both fail them.

> A word belongs in **Les mots** if it is a member of a set you cannot use one
> member of without knowing its neighbours — and the set is finite, enumerable
> today, and will not grow.

Three tests, all of which must pass:

1. **Closed and enumerable.** There is no eighth day. Contrast: food, clothing,
   jobs, furniture — open classes with no stopping point.
2. **Learned as a contrast, not individually.** `gauche` is meaningless without
   `droite`. Knowing four of the seven days is knowing nothing.
3. **Needed mid-sentence, where a lookup is not available.** You look up
   `déchèterie` the night before. You cannot look up `à gauche` while the man is
   pointing.

And a fourth signal that decides whether a set earns a picture rather than a
list: **a picture disambiguates it better than a gloss can.**

### Why the existing formats fail, measured

A closed set escapes this repo's other two artefacts for two opposite reasons,
and both are measurable against `fr_50k.txt`.

**Frequency ordering scatters them.** In dialogue people say *demain*, not
*mercredi*; *j'ai mal*, not *j'ai mal au genou*. So a subtitle corpus buries
exactly the sets a learner must hold whole:

| set | ranks |
|---|---|
| the seven days | `vendredi` 1755 … `mercredi` 3521 |
| the twelve months | `juillet` 4269, `janvier` 5609 |
| body parts | `genou` 4947, `poignet` 6083, `coude` 7843 |
| `avant-hier` / `après-demain` | 10,618 / 8,373 |

The proof that a frequency gate is the wrong instrument here: it accepts `été`
at rank 99 — which is the past participle of *être*. `étés`, unambiguously the
season, is rank 12,709. It rejects three of the four seasons and accepts the
fourth for the wrong reason. It also accepts `ouvert` (1,121) and rejects
`fermé` (1,734), severing an antonym pair.

**The phrase format dissolves them.** The opposite failure, and the more
valuable finding:

| word | rank | rows of its own in the 1,332-phrase deck |
|---|---|---|
| `que` | 6 | 0 |
| `et` | 13 | 0 |
| `qui` | 31 | 0 |
| `mais` | 32 | 0 |
| `si` | 38 | 0 |
| `quand` | 81 | 0 |

Nine of the hundred most frequent words in French have no row, not because they
are rare but because they exist only *between* two clauses. A deck of complete
utterances can display them a thousand times and teach them zero times.

### The consequence, stated plainly

The closed sets of a language number roughly eight hundred items. The principle
bounds the section; it was never going to make it small. **Les mots** is
therefore larger than **Les phrases**, and that is correct rather than a failure
of discipline.

## Inventory

~50 groups, ~819 items, in three tiers. Tiers are a statement about *use*, not
about difficulty.

### Tier 1 — «Ce qu'on montre» (shared, concrete, pointable)

Body · head · family · ailments — two drawings
Space: prepositions, vertical axis, deixis, direction, movement verbs, compass
Numbers · the hour · money — clock grid
Calendar: now-line, week strip, month-and-season wheel, Vaud holidays
Weather
Showable verbs · antonym pairs · colours · animals
Emotions (organised by `être` vs `avoir`, which is the hard part)
The table · the meal · rooms of the house
Transport (organised by `à` vs `en`)
Destinations

### Tier 2 — «La machine» (adult, abstract, studied daily)

Oui · non · **si** · peut-être
The skeleton: pronouns, question words, negation, quantity, articles and the
partitive, existentials
**The indefinites grid** — a 4×4 paradigm, the grid *is* the graphic
**Conjunctions** and **relatives** (`qui / que / où / dont`)
Frequency · comparison · sequence · certainty · manner · the senses · body
positions · inside-outside · possessives · demonstratives
Adult verbs · abstract time

### Tier 3 — «Le résident» (consulted at an event, never studied)

Nationalities, countries and languages
**Spelling and dictating** — how to say `é accent aigu`, `ç cédille`, `M comme
Marcel`, and how to read a Swiss phone number in pairs
Swiss form fields
Market quantities
`L'immeuble` — the Swiss apartment building
Emergencies and health
Vaud practical · `le tri`

Tier 3 is bound as an appendix rather than studied in sequence, with two
exceptions duplicated into the main body because they are pointable and urgent:
the **flag tiles** and the **emergency numbers**, the latter printed large on the
inside back cover.

### Notable groups and why they are in

**The indefinites grid** — the highest yield per gloss in the book. Greek has the
same 4×4 paradigm (`κάποιος/κάτι/κάπου/κάποτε` · `κανένας/τίποτα/πουθενά/ποτέ`),
so a Greek speaker learns sixteen French words by learning a table shape he
already owns.

**Relatives** — the single largest Greek collapse in the language. Greek `που`
does the work of `qui`, `que`, `où` and much of `dont` single-handedly, and the
`qui`/`que` choice is subject-versus-object, which is grammatical, invisible, and
wrong half the time by chance.

**Spelling and dictating** — a Greek with a Greek surname in a French-speaking
canton spells his name several times a week, forever. `épeler` ranks 15,028 and
the phrase deck has zero coverage. The card is self-illustrating: set `é è ê ë ç`
at 48pt and the glyph is the content.

**Swiss form fields** — Greek `όνομα` is the *first* name; French `nom` is the
surname on every form. He has probably already written "Petros" in the wrong box.

### Deliberately excluded

Food, clothing, jobs, furniture, sports, shapes, materials, `siècle`, `tiers`,
and the narrative life-events arc (`naître / grandir / vieillir / mourir`). All
fail closedness or test 3. Named here so they are visibly rejected rather than
forgotten. Open-class vocabulary is already handled by the `jeu`'s
`mots_du_lieu` mechanism.

## Page design

One card per semantic group, never split across a page.

- **Card:** accent rule across the top, a **18%-width left rail** carrying the
  group name, a Greek subtitle and a count pill, then a hairline, then the
  content grid.
- **Grid:** three columns (two for groups under seven items). Row is
  `[icon] [article] [French] [Greek, only if needed]`.
- **Icons:** 26px. **Type:** Alegreya Sans, French 14pt bold.
- **Footer:** one example sentence per card, full width, in the group's accent
  colour, with the card's own words bolded. This supplies the one thing a grid
  structurally cannot — the words governed by something — and it costs no pages.
- **Density: 53 items per A4.** Measured, not estimated.

Rejected along the way, with reasons on the record: a full-page labelled figure
with leader lines (28pt per item, and the drawing was not good enough); a
two-column continuous flow with 10-row stripes (the stripes mark rows, not
meaning, so groups broke across columns arbitrarily); a 31.8% golden-ratio rail
(bought nothing — the rail was never the vertical constraint).

### Gender

The **article** is coloured, never the noun: `le` deck blue, `la` deck rose,
`l'` and `les` neutral grey. This does not collide with any other colour coding
because it occupies a different glyph slot. It carries real information only on
`l'` and `les`, which is exactly the subset learners get wrong forever.

## Greek — the cover test

> Cover the Greek. If the icon alone recovers the word, drop the Greek. If it
> does not, keep it.

Implemented as code, not as taste. Greek is kept where the icon is schematic
rather than depictive (all house-glyph words), where two entries are
near-synonyms an icon cannot separate (`devant`/`derrière`,
`au-dessus`/`au-dessous`, `loin`/`là-bas`), and on every row whose gutter is
empty.

**Result: 19% of rows keep Greek** — 84 glosses instead of 437. The side effect
is better than the saving: the Greek stopped being noise on every row and became
a signal that something is missing. On the body card it appears on exactly the
seven joints no icon set has, and the eye goes straight to them.

**Les phrases** is the exception: no icon can carry a sentence, so all 1,332
phrases keep a gloss, and that gloss is Greek. This is the largest single task in
the project.

### Where Greek fails, and the mechanism

Greek is a better pivot than English for this material — `librairie`/βιβλιοπωλείο,
`assister à`/παρακολουθώ, `rester`/μένω, `sensible`/ευαίσθητος are all English
traps that do not exist for a Greek speaker, and `ici/là/là-bas` maps 1:1 onto
εδώ/εκεί/εκεί πέρα where English collapses two.

It fails in three ways, each with its own treatment and no third column:

- **One Greek word, several French** — qualify inside the Greek cell. πόδι →
  `pied` / `jambe`, χέρι → `main` / `bras`, σε → `à`/`dans`/`en`/`sur`/`chez`,
  ξέρω → `savoir`/`connaître`.
- **One French word, several Greek** — print both. `fille` → κόρη / κορίτσι,
  `droit(e)` → δεξιά / ίσια / δικαίωμα.
- **No Greek equivalent at all** — a short Greek prose box, not a row. `on`,
  `y`/`en`, the partitive, `si` contradicting a negative, two-part negation, and
  the `να`-versus-bare-infinitive rule.

## Technical

**Pipeline: HTML + CSS → PDF via headless Chromium (Playwright).** Already
installed; zero new dependencies; 0.10s per render. WeasyPrint was tested and is
a degraded fallback only — it produces five pages where Chromium produces two,
and every tint vanishes because it lacks `color-mix()`. The decisive argument for
Chromium is that the HTML is *also* the artefact opened in a browser, so the
print must match what the browser shows.

**The HTML is a first-class output.** Single file, font and icons inlined,
~820KB, opens with nothing beside it. This is what puts the book on a phone
instead of in a drawer.

**Icons: OpenMoji** for concrete words, **57 house-drawn glyphs** for abstract
ones. Both are flat line art on the same 24×24 grid, which is why they cohabit;
against Apple's glossy raster the house glyphs read as placeholders. Apple was
also 5× the asset weight and an 18× heavier output PDF. Coverage measured across
437 items: OpenMoji 79% alone, 89% with house glyphs, ~97% after hand overrides.

**House glyph grammar:** a grey **reference** object and a coloured **subject**.
Where the dot sits relative to the box *is* the preposition. Frequency is a
five-slot track; quantity is a glass filled to a dashed target line. Days and
months are typographic tiles (`Lu`, `Me`, `1`, `12`) — a drawn 7-cell week strip
was tried and is an illegible smudge at 14pt.

**Font: Alegreya Sans**, already in `jeu/fonts/`, OFL, static TTF, full French
and Greek. Mandatory rather than preferred: reportlab's built-in Helvetica fails
Greek *silently*, rendering unaccented Greek in Symbol and a solid black box for
every accented vowel — which is most of modern Greek.

**Data:** one JSON file per card, declaring content only; the builder owns
layout. The 437-item vocabulary already exists as `vocab/vocab.py` from the
prototype.

## Migrating Les phrases

The six themes are chapters, not cards — `quotidien` alone has 383 members. But
the sub-groups already exist as **contiguous runs**, because the data was
generated by domain-specialised LLM passes, one per topic. Sampling `quotidien`
every 40 rows walks cleanly through language help → taxi → restaurant → hotel →
time → weather → emergency → food → appointments.

So the re-grouping is a **segmentation and labelling pass over existing runs**,
not a re-sort of 1,332 rows.

## Corrections to the existing deck

Applied 2026-09-22 in the same change as this spec:

| line | was | now |
|---|---|---|
| 826 | `Appelez le quinze !` | `Appelez le 144 !` — **15 is the French SAMU; Switzerland is 144** |
| 443 | `cinquante euros` | `cinquante francs` |
| 641 | `menu à vingt euros` | `menu à vingt francs` |
| 633 | `Prenez le RER jusqu'à Châtelet.` | `Prenez le m2 jusqu'à Ouchy.` |

Outstanding, needing a judgement call rather than a swap:

- line 348 `Je dois composter mon billet ?` — ticket-stamping is SNCF; CFF has no
  composteurs, so the question is meaningless here.
- lines 450, 452 `un sac` — at a Vaud till it is `un cornet`. Add the variant
  rather than replacing.

Separately, `jeu/data/noms_propres.txt` files all seven days and all twelve
months as proper nouns. They are not — they are lowercase in French. They were
put there to pass a frequency gate, and the file now encodes the exact
capitalisation error the calendar card has to correct. Move them to a new
`ensembles_fermes.txt` category.

## Swiss specifics

Vaud usage is the headword; the France form appears dim and parenthetical where
he will hear it. A reference is production *plus* recognition — he says
`huitante` and must understand `quatre-vingts`.

- `septante` / `huitante` / `nonante`. Note that Geneva and Neuchâtel say
  `quatre-vingts`, so this is a Vaud call. Greek `εβδομήντα/ογδόντα/ενενήντα` are
  regular, so these are *easier* for a Greek than for an English speaker.
  Minutes never exceed 59, so they never appear in clock times — but years, ages
  and prices use them, including the till contraction `trois nonante` for CHF 3.90.
- **Meals:** a 2×3 grid labelled `vaudois` / `français`, because `déjeuner /
  dîner / souper` against `petit-déjeuner / déjeuner / dîner` is one full meal out
  of step and both are live in Lausanne. The phrase deck uses the France set
  throughout; the grid explains why the halves differ.
- `natel`, `cornet`, `action` (= special offer), `service`, `ça joue`,
  `déchèterie`, `faire les commissions`, `le sac taxé`, CFF / Coop / Migros.
- Emergency numbers are Swiss: 144 / 117 / 118 / 112 / 145.
- Transport is Lausanne-specific: `tram` ranks 20,114 in a France corpus and the
  m1/m2 is the only metro in Switzerland. Add `le LEB`, `le funiculaire`,
  `Mobilis`, `le demi-tarif`.
- `la bise` — the cold north wind off the Léman, on every local forecast, and
  also a kiss on the cheek.

## Work plan

Three bulk jobs, all parallelisable:

1. **~450 icon decisions.** The automatic matcher reaches ~79%; the misses are
   plausible-but-wrong rather than absent (`courir` is a wind puff, `rire` is a
   cat face, `la main` is a face). Every row needs a human eye. Roughly 20–30% of
   auto-picked icons are wrong or weak.
2. **Greek glosses:** 84 for **Les mots** under the cover test, 1,332 for
   **Les phrases**. No French→Greek data exists anywhere in the repo —
   `translations.el.txt` is Greek→English for the web game.
3. **Card headings and one example sentence per card**, for ~50 word cards plus
   whatever **Les phrases** segments into.

Build order: the **clock card first**. It is unambiguous by construction — a dial
showing 3:15 cannot mean anything else, in any language, at any age — it is the
highest-value page for a seven-year-old, and it is the cheapest validation of the
whole pipeline.
