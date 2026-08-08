# Part-of-speech pass prompt (one per 200-word batch)

Used to generate a sheet's POS tags. Fan out 5 subagents, each covering a
200-line slice of `data/bandNN_translations.txt` (use translations, not the bare
word list — the gloss disambiguates POS). Concatenate into `data/bandNN_pos.txt`,
then append to the master `data/pos.txt`. Fill in band number + line range.

---

You are a French linguistics tagger. Read `data/bandNN_translations.txt` — each
line is `french = english_gloss`. Tag ONLY lines {START} through {END}.

For each word output exactly one line: `french|POS|REG`

POS is ONE of: V (verb, incl. conjugated forms & infinitives), N (noun),
ADJ (adjective), ADV (adverb), PRON (pronoun), DET (determiner/article),
PREP (preposition), CONJ (conjunction), INTJ (interjection/filler — oh, ah, hé,
ben, euh, merci, salut, bonjour, oui, non, ok), NUM (number), OTHER.

REG applies ONLY to verbs (V): `irr` if the verb's infinitive is IRREGULAR,
`reg` if it is a regular 1st-group -er verb (parler, donner, aimer…) or regular
2nd-group -ir verb (finir, choisir…). For NON-verbs put `-`.

Irregular = anything not a clean regular -er/-ir(-iss-) verb: être, avoir, aller
(irregular despite -er), faire, dire, voir, pouvoir, vouloir, devoir, savoir,
venir, tenir, prendre, mettre, partir, sortir, dormir, sentir, boire, croire,
lire, écrire, vivre, suivre, connaître, falloir, valoir, etc. Tag CONJUGATED
forms by their lemma's regularity (est→V|irr, parle→V|reg, arrive→V|reg).

Use the english gloss to disambiguate where a French form could be more than one
part of speech. Output ONLY the lines `french|POS|REG`, same order as the file,
no header, no commentary, no markdown, no preamble.
