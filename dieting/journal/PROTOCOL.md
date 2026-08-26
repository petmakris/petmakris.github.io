# Diet journal — operating protocol

This file exists so that a **brand-new Claude Code session** can pick up the
diet-tracking work with zero other context. If you are that session: read this
file and `data.js`, and you have everything. The history is the data file; the
rules are below; the original instructions are quoted verbatim at the end.

## What this is

Petros (petmakris@gmail.com) tracks his diet conversationally in Claude Code
sessions. He tells Claude what he ate (sometimes with calories, sometimes just
ingredients), his Garmin **active calories** at the end of the day, and any
exercise. Claude estimates calories where needed, keeps the notebook in
`dieting/journal/data.js`, and pushes to GitHub so the page at
`https://petmakris.github.io/dieting/journal/` updates. That page is also used
as a phone-widget dashboard, so its top block must always show **which day of
the plan it is** and how today stands.

There is no app and no build step. The page is static HTML; the data is a
single JS file; Claude is the input method.

## The plan

- **Goal:** a sustained **600 kcal/day deficit** — deliberately modest,
  because anything bigger is not sustainable.
- **Duration:** 90 days, **2026-08-26 (day 1) through 2026-11-23 (day 90)**.
- **Model:** total burn for a day = `maintenanceRest + active` (Garmin active
  calories); deficit = burn − eaten. `maintenanceRest` lives in
  `data.js → plan.maintenanceRest`. If it is still `null`, ask Petros for it
  (or estimate from sex/age/weight/height via Mifflin-St Jeor and confirm).
- 600 kcal/day ≈ 0.55 kg of fat per week; the page shows this projection.

## Files (repo `petmakris/petmakris.github.io`, deployed as GitHub Pages)

| File | Role |
|---|---|
| `dieting/journal/data.js` | **The notebook.** All config + all days. The only file that changes on a normal prompt. |
| `dieting/journal/index.html` | The dashboard. Renders `data.js`; no server, no build. |
| `dieting/journal/PROTOCOL.md` | This file. Update it if the rules themselves change. |

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

Conventions: one entry per calendar date; kcal are integers; when Claude
estimates, it says so in the item's `note` and states assumptions in chat so
Petros can correct them. Never delete history — correct it.

## The loop (what Claude does on every prompt)

1. Petros writes food / active calories / exercise / corrections in chat.
2. Claude estimates any missing calories (best effort, state assumptions).
3. Claude updates `data.js` — appending to today's entry, or creating it if
   the date rolled over.
4. Commit with a clear message and **push** so the page updates. Small,
   frequent pushes are the point — Petros checks the page from his phone.
5. If information is missing or ambiguous, ask; Petros answers; update again.
6. If Petros says something on the page is wrong, fix it and push.

Branch note: work happens on whatever branch the session designates; the page
serves from `main`, so changes reach the dashboard when they land there.

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
