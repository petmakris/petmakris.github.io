---
name: diet-journal
description: Maintain Petros's diet journal at dieting/journal/ — log food and estimate its calories, record Garmin active calories and exercise, apply corrections, then commit and push so the phone dashboard updates. Use whenever he reports what he ate, gives a calorie figure or active-calorie number, describes a workout, says something on the journal page is wrong, or asks which day of the plan he is on.
---

# Diet journal

Petros tracks his diet conversationally in Claude Code. He says what he ate
(sometimes with calories, sometimes just ingredients), his Garmin **active
calories** at the end of the day, and any exercise. You estimate the calories
he did not give, write them into `dieting/journal/data.js`, and push, so the
page at `https://petmakris.github.io/dieting/journal/` updates. That page is a
widget on his phone: its top block must always show which day of the plan it
is and how today stands.

No app, no build step. Static HTML, one JS data file, and you as the input
method.

## The plan

- **Goal:** a sustained **600 kcal/day deficit** — deliberately modest,
  because anything bigger is not sustainable.
- **Duration:** 90 days, **2026-08-27 (day 1) through 2026-11-24 (day 90)**.
- **Model:** burn for a day = `maintenanceRest + active` (Garmin active
  calories); deficit = burn − eaten.
- **`maintenanceRest` = 1930 kcal**, from Mifflin-St Jeor for male, 104 kg,
  176 cm, age 43 (confirmed 2026-08-26). Recompute it as
  `10×kg + 6.25×cm − 5×age + 5` if his weight changes materially — a 5 kg
  loss is 50 kcal off the resting figure.
- 600 kcal/day ≈ 0.55 kg of fat per week; the page projects this.

## Files

Repo `petmakris/petmakris.github.io`, deployed as GitHub Pages from `main`.

| File | Role |
|---|---|
| `dieting/journal/data.js` | **The notebook.** All config + all days. The only file that changes on a normal prompt. |
| `dieting/journal/index.html` | The dashboard. Renders `data.js`; no server, no build. |
| `.claude/skills/diet-journal/SKILL.md` | This file. Update it if the rules themselves change. |

The page deliberately says nothing about how it is maintained — that is what
this skill is for. Do not add protocol text, repo links or "edited by Claude"
notes back onto the page.

## Data format (`data.js`)

```js
window.DIET = {
  plan: { start, lengthDays, deficitTarget, maintenanceRest },
  days: [
    {
      date: "YYYY-MM-DD",
      items: [ { name, kcal, note? } ],  // note = "estimate", portion basis, …
      active: 520 | null,                // Garmin active calories, end of day
      exercise: ["45 min brisk walk"],   // free text, may be empty
      note: ""                           // anything worth remembering
    }
  ]
};
```

Conventions: one entry per calendar date, oldest first; kcal are integers;
when you estimate, say so in the item's `note` and state the assumption in
chat so Petros can correct it. **Never delete history — correct it.**

## What the page shows

**The hero is the goal, not the day.** It shows the day number, then a bar
whose axis is kilos: the fill is what the deficits add up to so far, the green
tick is where the plan says he should be today, and the line underneath says
how far ahead or behind that puts him. Three tiles follow — ΣΥΝΕΠΕΙΑ (actual
deficit ÷ target, over the days that have data), ΚΑΤΑΓΡΑΦΗ (days with data ÷
days elapsed) and ΡΥΘΜΟΣ/ΕΒΔ. He asked for this on 2026-08-26: "όχι την
σύνοψη της ημέρας αλλά τον στόχο μου". Today's own numbers are not in the
hero any more — they are the top row of the table.

A day with no data counts as zero deficit in the ahead/behind figure, which is
why the verdict names how many days are missing. Do not "fix" that by dropping
unlogged days from the comparison: the schedule runs on calendar days.

**The goal in kilos is derived**, `deficitTarget × lengthDays ÷ 7700`. Change
`lengthDays` and the goal, the bar and the pace tick all follow. There is no
separate goal-weight field to keep in sync.

Three more blocks below, all derived from `data.js` too:

- **Τελευταίες 7 ημέρες** — averages over the last 7 logged days.
- **Ημέρα προς ημέρα** — one row per elapsed plan day: eaten, active,
  deficit, with a running total and the fat equivalent. Days he never logged
  appear as faint rows of dashes, on purpose: a gap must be visible as a gap.
  Today's row is marked in the accent colour.
- **Το ημερολόγιο** — the full cards, every item with its calories.

## The loop (every prompt)

1. Petros writes food / active calories / exercise / corrections.
2. Estimate any missing calories, best effort, and state your assumptions.
3. Update `data.js` — append to today's entry, or create it if the date
   rolled over.
4. Commit with a clear message and **push to `main`**. Small, frequent pushes
   are the point; he checks the page from his phone.
5. If something is missing or ambiguous, ask. He answers; update again.
6. If he says the page is wrong, fix it and push.

## Language: Greek only

This page is **Greek only** — he said so on 2026-08-26, in those words:
"ONLY GREEK. ΟΛΑ ΣΤΑ ΕΛΛΗΝΙΚΑ." That is a deliberate exception to his
standing Greek + French rule for the rest of the repo, so do not add French
here and do not "fix" it back to bilingual.

Everything that reaches the page goes in Greek: item names, item notes, the
day note, exercise. `lang="el"`, and dates and numbers are formatted with
`el-GR`, so figures read 1.880 and 0,53. Only the code comments in `data.js`
and `index.html` stay in English.

## Original instructions, verbatim (2026-08-26)

> trust you something that's very, very simple, and then pretty sure that we
> can achieve that. I have tried many times in the past to use a mobile phone
> or a notebook, a physical notebook, track my diet, and watch ended up more
> effective on anything in the world is to just do it within a closed session.
> So we will do just that. The only trick that we will do is that we... I will
> tell you what I'm meeting, my plan, my discussions, my considerations, and
> you will build up a very small application on my GitHub pages. I have
> already some applications there. You will need to include one more that
> is... I don't care if the information goes public. I don't care what people
> know about what I'm meeting. I don't expect any visitors. So what I want us
> to do is a very simple flow. I will be telling you here the a list of items,
> sometimes including summaries about calories, sometimes ingredients, and you
> will actually help me identify the calories. One we have enough information
> when we suite to a new day, you will push this information in a list style
> page, blog page. I don't know what this will be on on on my GitHub blog.
> Completely up to you what is the best way to capture this information. We're
> gonna start with something simple, and then we can integrate. I I really
> care about not losing track of what we're doing. One fancy stuff that we we
> would like to do is I will also tell you what are my active calories end of
> the day because I track them with my garment watch. And then, well,
> sometimes I might also tell you what kind of exercises I did for the day.
> Just you can track them down so the notebook format we're using will also,
> uh, must also be capable of tracking not only food and calories and the
> total calories, but also the active calories I'm consuming and burning
> through the day. Now let me tell you, uh, another thing is that... or every
> time I will tell you more information here where you will have to push this
> information into GitHub so I can see them updated. Now another constraint is
> that in this blog post, you will have to include all the information needed
> In case I will need to start someday fresh from a new quote called session
> because why not? I mean, uh, Claude session is something ephemeral. We will,
> uh, we have all the information needed there about the history, what we have
> been tracking, both consumed and expanded calories. Uh, but then we should
> capture the prompts exactly what I'm telling you right now. So this work can
> start when needed from a new session. from a new cloud code session. So we
> all... you... we'll also need to have a plan in mind so that you... we will
> follow. And the plan is that we'll aim into something like six hundred
> calories deficit. This is the only thing sustainable for a long period of
> time, and I want to start dieting from now and for the next three months. If
> we do for a bigger... if if I aim for a bigger deficit, it's not gonna work.
> And help me do that. You have all the information you need. It gives me a
> prototype. I'm telling you. Whenever I'm adding a new prompt in the closed
> session, you will be making the mask. We will be making the updates. Best
> effort. If you are not ready to ask me questions, I will pre... provide you
> the answers, and then you will update the page. If I see something wrong, I
> will tell you you will update it. It's very simple. We don't need an app. We
> don't need anything more other that you to use the GitHub pages have as a
> notebook for what we do and as a dashboard for me to be aware on which day I
> currently am. please stop building us, and I want to tell you that this
> page, I will make it a widget on my mobile phone to show me some
> dashboarding stats so I know on which day I am and try to be consistent.

(Transcribed speech — "what I'm meeting" = what I'm eating, "garment watch" =
Garmin watch, "closed session" / "quote called session" = Claude session,
"making the mask" = making the math.)
