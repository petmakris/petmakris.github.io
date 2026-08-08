# Diet page — design document

A static, single-page web app deployed on GitHub Pages. Two parts: a minimal
maintenance-calorie calculator, and an ordered list of expandable "golden rules"
for dieting. No backend, no persistence, no build step beyond Jekyll. Vanilla
HTML/CSS/JS.

The page is aimed at newcomers, so the look-and-feel should be calm and minimal.
Nothing that scares a first-time visitor.

---

## Open questions (resolve before implementation)

These are decisions the brief left open. Each one changes either UI fields or
copy, so pin them down before writing code.

1. **Height as a calculator input?** Two options below in "Calculator" — pick A
   (no height, simpler) or B (height, more accurate). Default recommendation: A.
2. **Target weight as a second input?** The brief says "ideally" — meaning it's
   nice-to-have, not required. Proposal: include it as an optional field.
   Confirm.
3. **Page location in the repo.** Two viable options:
   - `/diet/index.html` as a standalone HTML file with Jekyll front-matter `layout: null`, so the page bypasses the blog chrome entirely. Recommended.
   - A regular Jekyll page that inherits the blog's layout. Probably wrong for this — the page wants its own minimal shell.
4. **Wording for the menstrual-cycle rule.** Brief used the word "period" but
   flagged it as the wrong register. Proposed phrasing: "Time the cutting phase
   around your menstrual cycle — start it just after, finish it before the
   next one starts." Adjust if you prefer something else.
5. **How many rules total?** The brief lists ~7 rules plus a strategy/tracking
   section. Open to more being added later. Confirm the current set is the v1
   set, or signal what's still missing.
6. **Page title / heading?** Placeholder used below: "A practical guide to
   dieting." Pick a real title.

---

## Page layout

Single column, max-width ~720px, centered. Generous whitespace. System font
stack (already used in the existing `index.html`). Mobile-first; everything
stacks naturally.

Order from top to bottom:

```
┌─────────────────────────────────────────┐
│  Page title                             │
│  One-paragraph intro                    │
├─────────────────────────────────────────┤
│  Calculator                             │
│    [sex]  [age]  [weight]               │
│    [target weight (optional)]           │
│    →  Result card:                      │
│       "Maintenance: 2,140 kcal/day"     │
│       (if target set) "At target weight │
│       2,000 kcal/day"                   │
│    Callout: "Your deficit is the        │
│    calories you burn through activity"  │
├─────────────────────────────────────────┤
│  Golden rules                           │
│    ▸ 1. Keep insulin low                │
│    ▸ 2. Go low on carbs                 │
│    ▸ 3. ...                             │
│    ▸ ...                                │
├─────────────────────────────────────────┤
│  Strategy & calorie tracking            │
│    ▸ Prepare your food in advance       │
│    ▸ Track calories by food category    │
│    ▸ ...                                │
└─────────────────────────────────────────┘
```

No fixed nav, no sidebar, no footer beyond a small credit line.

---

## Calculator

### Inputs

| Field          | Type                              | Required |
|----------------|-----------------------------------|----------|
| Sex            | toggle: Male / Female             | yes      |
| Age            | number, years                     | yes      |
| Weight         | number, kg                        | yes      |
| Target weight  | number, kg                        | no       |

All weights in kilograms. No pounds anywhere — not even as a toggle.

**Intentionally omitted:**
- Body fat % (friction; people don't know it; brief explicitly rejected v1).
- Activity-level dropdown (brief explicitly rejected — "people lie about how
  active they are, and it sabotages the result").
- Height (see formula choice below — option A is height-free).

### Output

A single result card showing:

- **Maintenance calories at current weight** — the headline number. Large font.
- **Maintenance calories at target weight** — if a target was entered, shown
  underneath in smaller font.
- A short callout below the numbers, explaining the philosophy:

  > Eat your maintenance calories. The deficit comes from the calories you burn
  > through movement and exercise — not from eating less than your body needs.
  > Aim to do your cutting phase in 2–3 week blocks, not as a permanent state.

No "calculate" button needed — recompute live as inputs change. Empty/invalid
inputs hide the result card; no error toasts.

### Formula — pick one

**Option A — kcal/kg heuristic (no height required).** Recommended for the
"newcomer-friendly, minimal" tone.

```
maintenance_kcal_per_day = weight_kg × k

where k depends on sex and age band:
  Male,   18–30: 32
  Male,   31–50: 30
  Male,   51+:   28
  Female, 18–30: 28
  Female, 31–50: 26
  Female, 51+:   24
```

This is a deliberately simple sedentary-ish estimate. It will be off by
±100–200 kcal compared to a height-aware formula, which is fine for the page's
purpose — the user is meant to refine the number against their own scale
trend, not trust it as gospel.

**Option B — Mifflin–St Jeor BMR × 1.2 (requires height).**

```
BMR_male   = 10·weight_kg + 6.25·height_cm − 5·age − 5 ·  −161 [+5 for male]
maintenance_kcal = BMR × 1.2   (sedentary multiplier baked in)
```

More accurate but adds a height field, which the brief didn't ask for. Only
pick this if you want the extra input.

---

## Golden rules — content & order

Rules are sorted by importance. Each rule renders as a collapsible accordion
item: title visible by default, expanded content shows on click. Only one open
at a time (radio-style) — optional, can be multi-open if simpler to build.

For each rule below: **title** is what the user sees collapsed, **summary** is
a one-line tagline shown next to the title, and **details** is what unfolds
when expanded.

---

### Rule 1 — Keep your insulin low

**Summary:** The single most important lever for losing fat. Almost every
other rule on this list is a way to achieve this one.

**Details:**

Insulin is the hormone that tells your body to store energy. When insulin is
high, your body has almost no reason to burn stored fat — it's busy storing
incoming energy instead. To lose fat, you want long stretches of the day where
insulin stays low.

What spikes insulin: refined carbohydrates (white bread, pasta, rice, sweets,
soft drinks), large quantities of any carbs, sugary drinks (including juice).

What keeps insulin low:
- Eat protein-forward meals.
- Combine carbs with fiber — fiber slows the absorption of glucose.
- Leave longer gaps between meals (see Rule 4).
- Don't snack on sugar between meals.

If you only do one thing on this list, do this one. It quietly takes care of
80% of the other rules.

---

### Rule 2 — Go low on carbs

**Summary:** Low carbs → low insulin → your body can actually use stored fat.

**Details:**

A direct corollary of Rule 1, important enough to call out on its own. When
carbs are low, insulin stays low, and your body switches into a mode where it
will actually pull energy from fat cells instead of from your last meal.

The first few days of going lower-carb, you'll drop a couple of kilos of water
weight. That's not fat loss yet — but it's the doorway to it. After that
initial drop, you start actually burning fat.

"Low carbs" doesn't mean zero — it means modest portions, and away from
refined sources. Whole vegetables, beans, a small portion of oats — fine. A
plate of pasta or a pastry — not during the cutting phase.

---

### Rule 3 — Go high on protein

**Summary:** High protein, moderate fat, low carbs, lots of fiber.

**Details:**

Protein keeps you full, protects muscle while you're in a deficit, and barely
moves insulin. Aim to anchor every meal with a protein source: eggs, Greek
yogurt, chicken, fish, cottage cheese, tofu.

The full macro picture for a cutting phase:
- **Protein**: high.
- **Fat**: moderate, and from good sources — olive oil, avocado, nuts, fatty
  fish.
- **Carbs**: low, and from whole sources.
- **Fiber**: high — it stretches the stomach, slows absorption, and quietly
  reduces appetite.

---

### Rule 4 — Manage hunger by extending the morning fast

**Summary:** Longer gaps between meals regulate hunger hormones. The easiest
gap to extend is the overnight one.

**Details:**

Hunger is a hormonal signal — and it gets retrained by your eating schedule.
If you eat the moment you wake up, your body learns to expect that. If you
push breakfast later, your body adapts.

The word "breakfast" literally means *break the fast*. Skipping or pushing
breakfast a few hours is the simplest form of intermittent fasting and tends
to be much easier than people expect after a few days.

What helps you ride out hunger:
- Plenty of fiber at the previous meal.
- Good fats (avocado, olive oil, nuts) — they're satiating and don't move
  insulin.
- Water, coffee, or tea in the morning.
- Knowing that the hunger spike passes in 15–20 minutes if you don't act on it.

---

### Rule 5 — Don't overdo cardio while cutting

**Summary:** A 30-minute run can drive your appetite up by more calories than
it burns. During the cutting phase, walk more, run less.

**Details:**

Intense cardio during a deficit is a trap. The 300–400 kcal you burn jogging
for half an hour can come back as a 600 kcal increase in appetite later in the
day — and it almost always does.

Better: stay generally active all day. Walking. Taking stairs. Standing more.
Errands on foot. A baseline active lifestyle burns more in aggregate than a
single hard cardio session, without spiking your hunger.

This isn't an argument against exercise — it's an argument for moving the
calorie deficit to come from low-intensity, all-day activity rather than from
hard cardio sessions that backfire.

---

### Rule 6 — Cut in short, time-boxed phases

**Summary:** Diet in 2–3 week blocks with a clear end date. Then return to
maintenance. Don't try to be in a deficit indefinitely.

**Details:**

Patience runs out. If you tell yourself "I'm now in a permanent state of
eating less," you will quit within weeks and overcorrect afterward. If you
tell yourself "I'm in a cutting phase for the next 3 weeks, then I go back to
maintenance," the discomfort becomes finite and tolerable.

A useful comparison: quitting smoking. The withdrawal is rough for 2–3 weeks
and then eases. People who know that beforehand make it through. People who
think the discomfort is the rest of their life don't.

So:
- Plan a 2–3 week cutting block (4 weeks max).
- Target ~1–1.5 kg of loss across the block.
- At the end of the block, go back to maintenance calories.
- Repeat after a few weeks if needed.

---

### Rule 7 — For women: time the cut around your cycle

**Summary:** Start the cutting phase just after your period, finish it before
the next one starts. The week of your period acts as a built-in refeed.

**Details:**

Hormonal changes during the menstrual cycle affect hunger, water retention,
and cravings. Trying to maintain a strict deficit through that window is
fighting your body for no reward.

A natural rhythm:
- **Day after period ends → ~3 weeks later**: cutting phase.
- **Period week**: eat at maintenance (or slightly above). Don't track
  strictly. Treat it as a planned refeed.

This isn't about willpower. It's about scheduling the deficit when your body
is most cooperative.

> Open question: confirm the wording — happy to soften further if "menstrual
> cycle" / "period" feels too direct.

---

## Strategy & calorie tracking

These aren't really standalone rules — they're the practical scaffolding that
makes the rules above actually work. Renders as its own section below the
rules list, with its own accordion items.

### Prepare your food in advance

**Details:**

The single highest-leverage thing you can do is have the right food ready
when you're hungry. If you have to *decide* what to eat while hungry, you
will lose — supermarkets, bakeries, and convenience stores have already won
that fight. So decide and prep when you are *not* hungry.

What this looks like:
- The night before, portion out the next day's chicken, salad, yogurt.
- Keep a small repertoire of fast, low-calorie recipes you can make in 10
  minutes from staples (eggs + vegetables, yogurt-based bowls, etc.).
- Have a "safe snack" in the fridge for moments of weakness — usually
  yogurt-based.

### A few low-effort tricks

**Details:**

- **Yogurt + cocoa + sweetener (+ fruit)** — high-protein, low-sugar,
  scratches the "dessert" itch without breaking the diet.
- **Banana-based "cakes"** — banana + a little sweetener + vanilla extract,
  baked. Low calorie, feels like a treat.
- Keep these in rotation so the cutting phase doesn't feel like deprivation.

### Track calories — by food category, not by item

**Details:**

For the first 1–3 weeks, weigh your food and track calories. Not forever —
just long enough to internalize the numbers.

The trick that makes tracking sustainable: stop tracking individual foods.
Track *food categories*.

Rough mental model:
- **Carbs (oats, bread, rice, etc.)**: ~400 kcal per 100 g, dry weight.
- **A palm-sized fruit**: ~100 kcal. Banana ~120, apple ~80.
- **Chicken breast**: ~165 kcal per 100 g cooked.
- **Greek yogurt (full fat)**: ~100 kcal per 100 g.

Once these are in your head, you can eyeball most meals without weighing.

This is also why processed food is harder to diet on: the calorie counts on
prepared meals don't fit clean mental categories, so you can't eyeball.
Cooking from raw ingredients makes tracking effectively free.

---

## Notes for implementation

- Single HTML file, vanilla JS, no framework, no bundler.
- Accordion: native `<details>`/`<summary>` is the simplest path and is
  accessible by default. Style it to remove the default disclosure triangle if
  desired.
- Calculator state: just listen to `input` events on the form fields and
  recompute. No reactive framework needed.
- Live recompute, no submit button.
- Test on mobile first — that's where most readers will hit it.

