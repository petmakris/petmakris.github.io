---
name: diet-journal
description: Maintain Petros's diet journal at dieting/journal/ — log food and estimate its calories, record Garmin active calories and exercise, apply corrections, then commit and push so the phone dashboard updates. Use whenever he reports what he ate, gives a calorie figure or active-calorie number, describes a workout, says something on the journal page is wrong, or asks which day of the plan he is on.
---

# Diet journal

Petros tracks his diet conversationally in Claude Code. He says what he ate
(sometimes with calories, sometimes just ingredients), his Garmin **active
calories** at the end of the day, and any exercise. You estimate the calories
he did not give, write them into the two files below, and push, so the page at
`https://petmakris.github.io/dieting/journal/` updates. That page is a widget
on his phone: it must always show which day of the plan it is and how the plan
as a whole is going.

No app, no build step. Static HTML, a JS data file, a Markdown ledger, and you
as the input method.

## The plan

- **Goal:** a sustained **600 kcal/day deficit** — deliberately modest,
  because anything bigger is not sustainable.
- **Duration:** 90 days, **2026-08-27 (day 1) through 2026-11-24 (day 90)**.
- **Model:** burn for a day = `maintenanceRest + active` (Garmin active
  calories); deficit = burn − eaten.
- **Missing Garmin active calories default to `plan.defaultActive` (450
  kcal), not to a gap.** He confirmed on 2026-08-31 that his Garmin stays
  consistent day to day (recent averages sat around 433), so a day he doesn't
  report an active figure for still gets a burn/deficit computed with 450 —
  it does not fall back to grey "no data" the way a day with no `eaten`
  still does. This applies retroactively to every already-logged day with
  `active: null`, not just future ones, because the default lives in the
  page's math (`index.html`), not in `data.js` — keep recording `active` as
  `null` when he genuinely didn't give a figure; do not write 450 into
  `data.js` itself.
- **`maintenanceRest` = 1930 kcal**, from Mifflin-St Jeor for male, 104 kg,
  176 cm, age 43 (confirmed 2026-08-26). Recompute it as
  `10×kg + 6.25×cm − 5×age + 5` if his weight changes materially — a 5 kg
  loss is 50 kcal off the resting figure.
- 600 kcal/day ≈ 0.55 kg of fat per week, ≈ 7.0 kg over the 90 days.
- **Changing `maintenanceRest` rewrites history.** Every past day's deficit is
  recomputed from it, so the curve and the grid move retroactively. Only change
  it when his weight has genuinely shifted, and tell him the old and new
  figures when you do.

## Files

Repo `petmakris/petmakris.github.io`, deployed as GitHub Pages from `main`.

| File | Role |
|---|---|
| `dieting/journal/data.js` | **Totals.** Config + one line per day: how much he ate, not what. This is all the page loads. |
| `dieting/journal/log.md` | **The detail.** Every meal with its calories, day by day. Committed to the repo, never loaded and never linked. |
| `dieting/journal/index.html` | The dashboard. Renders `data.js`; no server, no build. |
| `dieting/journal/verify.mjs` | Checks `data.js` and `log.md` agree — see below. Run with `node dieting/journal/verify.mjs`. |
| `.claude/skills/diet-journal/SKILL.md` | This file. Update it if the rules themselves change. |
| `.claude/skills/diet-journal/references/original-instructions.md` | The verbatim voice transcript that started this project. Historical record only — never needs updating, so it lives outside the file that gets re-read every prompt. |
| `CLAUDE.md` (repo root) | Pre-authorizes pushing straight to `main` from any session — no branch, no PR. Applies to the whole repo, but it exists mainly for this project: he works from his phone and expects the page to update within the same turn. |

The page deliberately says nothing about how it is maintained — that is what
this skill is for. Do not add protocol text, repo links or "edited by Claude"
notes back onto the page, and **never link `log.md` from it**: he asked on
2026-08-26 for the detail to be kept but kept off the page, which is built for
his phone.

**Both files are written in the same move.** `data.js` gets the day's total,
`log.md` gets the items it is made of, and the two totals must agree. If he
corrects one item, fix the item in `log.md` and the total in `data.js`
together — a total that no longer matches its breakdown is the one failure
this split can produce. Run `node dieting/journal/verify.mjs` before every
push; it parses both files and fails loudly on any date that's missing from
one side or whose totals disagree, so a mismatch gets caught before it ships
instead of on the next careful read.

## Data format (`data.js`)

```js
window.DIET = {
  plan: { start, lengthDays, deficitTarget, maintenanceRest, startWeight },
  days: [
    {
      date: "YYYY-MM-DD",
      eaten: 1880 | null,                // total kcal for the day; breakdown in log.md
      active: 520 | null,                // Garmin active calories, end of day
      weight: 103.4 | null,              // scale reading, only when he gives one
      exercise: ["45 min brisk walk"],   // free text, may be empty
      note: ""                           // anything worth remembering
    }
  ]
};
```

Conventions: one entry per calendar date, oldest first; kcal are integers.
**Never delete history — correct it.**

## Data format (`log.md`)

One section per day, oldest first, appended at the end. A table of items with
their calories, a bold total row that must equal `eaten` in `data.js`, then
the Garmin figure, the exercise, the note, and a line naming which numbers
were estimates. Follow the section already there. Estimates also get stated in
chat, so Petros can correct them.

## What the page shows

**The whole page is one widget.** He settled this on 2026-08-26 after looking
at five mockups: "όλη η σελίδα θα γίνει ένα απλό widget". There is no second
card, no weekly-averages block and no day-by-day table any more.

**It fills the phone screen — no floating card.** He asked for this on
2026-08-27: too much of the screen was empty paper-coloured margin around a
small centered card, and the type was too small to read at a glance. The
widget is now the full viewport (`100dvh`, edge to edge on a phone), the three
parts spread out with `justify-content: space-between` to use whatever height
the screen actually gives them instead of clumping at the top, and every
number and label is sized up from the original draft — the day number, the
weight figures, today's four stats, the grid legend, all of it. Keep this in
mind when adding anything new: it should read as one glance from arm's length,
not a document to zoom into. On a wide screen (desktop, checking the page from
a laptop) it caps at 560px and centers, so this only affects phones.

Above the three parts: `Day N of 90` once the plan is running, and under it
today's date and **how many days are left** — `Wed 19 Sep · 66 days left`,
then `1 day left`, then `last day`. Before day 1 the big line carries
**today's date** and the line under it counts down to the start (`Starts
tomorrow`, `Starts in 3 days · Thu 27 Aug`).

Both of those replaced fixed dates he already knew. Anything in this header
that does not change from one day to the next is not earning its place.

1. **The weight curve** — a chart whose axis is his real weight, descending.
   The dashed green line is the plan, drawn from `startWeight` on day 0 to the
   goal weight on day 90. The solid cream line is where the deficits have
   actually put him. Below it: today's weight, then the projection — where
   this pace lands him at day 90, green if it reaches the goal, amber if not,
   and a dash before day 1, when there is no pace to project.
   A day with no data adds no deficit, so the line goes flat for that day.
   That is the honest reading; do not interpolate over gaps.
2. **The 90-day grid** — one square per plan day, coloured against
   *maintenance* (zero deficit), not against the target, confirmed
   2026-08-31: green for a deficit, red for a surplus, grey within `±100`
   kcal of maintenance either way — strong green past `+target`, light green
   from `+100` to `+target`, light red from `−100` to `−target`, strong red
   past `−target`. At a 600 target that's strong green over +600, light
   green +100–600, grey ±100, light red −100 to −600, strong red past −600.
   Separately, grey also means "no data" for a day whose `eaten` is missing
   (near-invisible for a day that has not arrived yet). A missing `active`
   alone is no longer a gap here — see `defaultActive` above. Above the grid,
   the consistency figure and how many elapsed days actually have data. This
   is the part that answers "how well am I keeping to the plan" — gaps must
   stay visible as gaps.
3. **Today's figures** — EATEN, ACTIVE, BURN, DEFICIT, and nothing else.

**The goal weight is derived**, `startWeight − (deficitTarget × lengthDays ÷
7700)` — 104 − 7.01 = 97.0 kg. Change `lengthDays` or `deficitTarget` and the
goal, the dashed line and the projection all follow. There is no goal-weight
field to keep in sync.

**Weigh-ins are optional and welcome.** If he gives a scale reading, put it in
that day's `weight` and it appears as a small amber ring on the curve, and as
today's headline figure instead of the estimate. Without one the page says
"estimated today", because a weight computed from calories is an estimate and
must not be dressed up as a measurement.

**Numbers only, no prose.** Exercise and the day note are recorded in
`data.js` and `log.md` but never rendered. He asked for this on 2026-08-26:
"δεν χρειάζεται να ξέρει ο καθένας τι κάνω και τι τρώω με λεπτομέριες, μόνο
τα νούμερα" — the page is public and the detail of what he does and eats
stays off it. Keep recording both; just do not put them on the page.

**`data.js` is loaded with a timestamp query** so a phone never renders a
cached day. Missing numbers render as a dash rather than throwing — a single
`undefined` once blanked the entire widget, so keep new fields optional and
guarded.

## The loop (every prompt)

1. Petros writes food / active calories / exercise / corrections.
2. Estimate any missing calories, best effort, and state your assumptions.
3. Update **both** files — append to today's entry in `data.js` and to today's
   section in `log.md`, or create the day in each if the date rolled over.
4. Run `node dieting/journal/verify.mjs`. If it reports a mismatch, fix it
   before continuing — do not push on a failing check.
5. Commit with a clear message and **push to `main`**. Small, frequent pushes
   are the point; he checks the page from his phone.
6. If something is missing or ambiguous, ask. He answers; update again.
7. If he says the page is wrong, fix it and push.

## Language: he writes in either, the page is English

**He writes to you in Greek or English**, whichever comes to hand — often
Greek for foods he does not know the English name of. Take both. The language
he uses does not have to be the language you record in, and it does not have
to be consistent from one day to the next.

**The page is English.** He asked for this on 2026-08-26, reversing an earlier
Greek-only instruction he gave the same day: "θέλω να είναι αγγλικά".
`lang="en"`, and dates and numbers format with `en-GB`, so figures read 1,880
and 104.0. Every rendered string — labels, empty states, tooltips — is
English.

This is also an exception to his standing Greek + French rule for the rest of
the repo. Do not add French or Greek to this page, and do not "fix" the rest
of the repo to match it.

Stored prose — a day note, an exercise line, the item names in `log.md` — can
stay in whatever language it arrived in. None of it is rendered, so none of it
needs translating.

## Original instructions

The verbatim voice transcript that started this project (2026-08-26) is kept
in `references/original-instructions.md` — historical record only, nothing in
it overrides the rest of this file.
