# Recipes project — design

Date: 2026-08-10. Approved by Petros in session.

## What

A new self-contained project at `/recipes/` on petmakris.github.io holding both
source code and outcomes (the frequence pattern, with sources tucked into a
`src/` subfolder per recipe). First recipe: near-zero-calorie chocolate
hazelnut praline syrup, imported from the `syrup-doc` project (Claude-on-cloud
generated, arrived via `~/Downloads/files/syrup-doc.tar.gz`).

## Hard rules

- **Everything bilingual, Greek + French, no exceptions.** Side-by-side on the
  page: every section title, ingredient, and step shows both languages
  together. (Petros lives in Lausanne and is learning French.)
- **Mobile first.** The pages are primarily read on a phone (in a kitchen or a
  supermarket).

## Structure

```
recipes/
  index.html            hub page listing all recipes (bilingual cards)
  assets/style.css      one shared theme for all recipe pages
  README.md             what this project is, how to add a recipe
  syrup/
    index.html          the recipe page, GR+FR side-by-side
    siropi-sokolatas-pralina-GR.pdf     printable PDF, downloadable
    src/                the syrup-doc project unpacked as-is
      build.py  fonts/  requirements.txt  CLAUDE.md  README.md  .gitignore
```

## Decisions

- **Recipe pages are authored directly as HTML/CSS/JS** by Claude — no
  markdown pipeline, no build step for HTML. One shared stylesheet
  (`assets/style.css`) so all recipes read as one site.
- **Content source of truth for the syrup page** is the Python lists in
  `src/build.py` (`praline`, `syrup`, `steps`, `prods`, `rest`). French
  translations are written alongside the Greek. French shelf terms keep the
  teal semantic treatment from the PDF's design system.
- **Visual language** borrows from the PDF: Material, light, high contrast,
  Blue 800 `#1565C0` primary, Teal 800 `#00695C` reserved for French words the
  reader physically encounters in a Swiss shop (the "teal rule" from
  `src/CLAUDE.md`).
- The site root `index.html` and root `README.md` each gain one row
  for `/recipes/`.
- No build system at the site level; plain static files, `.nojekyll` stands.

## Out of scope (follow-ups)

- Making the PDF itself bilingual (would need `build.py` edits under its
  strict 2-page constraint). The current Greek PDF ships as-is.
- The English PDF variant in Downloads is not part of the site.

## Testing

Open hub and recipe page locally at desktop and mobile widths; check links,
PDF download, and that everything renders as plain static files.
