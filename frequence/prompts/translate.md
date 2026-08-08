# Translation pass prompt (one per 200-word batch)

Used to generate a sheet's glosses. Fan out 5 subagents, each covering a
200-line slice of `data/bandNN_words.txt` (written by `make slice BAND=N`).
Concatenate the results into `data/bandNN_translations.txt`, then append to the
master `data/translations.txt`. Fill in the band number and line range.

---

You are a precise French→English translator. Read the file
`data/bandNN_words.txt` — one French word per line. Translate ONLY lines
{START} through {END}.

These are frequency-ranked common French words from movie subtitles. For each
word give ONE concise, most-common English meaning (the gloss a learner needs):

- Function words: give the grammatical gloss (de = of/from, que = that).
- Verbs: English verb; infinitives as "to X", conjugated forms in matching sense
  (est = is, ai = have).
- Ambiguous tokens: best single common meaning.
- Keep each gloss SHORT (1–4 words). Use "/" for the 2 most common alternates
  only when truly needed.

Output ONLY lines in the exact format `french = english`, one per line, in the
SAME order as the file, for the requested range. No numbering, no commentary,
no markdown, no preamble.
