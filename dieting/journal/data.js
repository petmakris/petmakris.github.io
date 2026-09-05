/* Diet journal data. This file IS the notebook the page reads, and it holds
 * only per-day totals: the meal-by-meal breakdown lives in log.md, which the
 * page never loads and never links to. Newest day last. The operating
 * procedure is in the repo skill .claude/skills/diet-journal/SKILL.md.
 *
 * Units: kcal everywhere. `eaten` is the day's total intake. `active` is the
 * Garmin "active calories" figure — when a day has none, the page uses
 * `plan.defaultActive` instead, so a missing Garmin reading is not treated
 * as a data gap. `maintenanceRest` is resting maintenance; burn =
 * maintenanceRest + active, and deficit = burn - eaten. Target: 600.
 *
 * The page renders in English. What language a stored note or exercise line
 * happens to be in does not matter — none of it is rendered.
 */
window.DIET = {
  plan: {
    start: "2026-08-27",        // day 1
    lengthDays: 90,             // three months → ends 2026-11-24
    deficitTarget: 600,         // kcal/day — the only sustainable number
    maintenanceRest: 1890,      // Mifflin-St Jeor: male, 100 kg, 176 cm, age 43
    startWeight: 100.0,         // kg on day 1 — weighed in 2026-08-27
    defaultActive: 450          // used when a day has no Garmin active figure — his Garmin stays consistent day to day, so this stands in rather than the day counting as a gap
  },
  days: [
    {
      date: "2026-08-27",
      eaten: 1930,
      active: 528,
      weight: 100.0,
      exercise: [],
      note: "Day 1 weigh-in 100.0 kg. Evening: apple, bread, salad, +100 unknown — he says that's it for today."
    },
    {
      date: "2026-08-28",
      eaten: 2460,
      active: null,
      weight: null,
      exercise: [],
      note: "Woke 5h00 (cat), ate a double portion of overnight oats + milk. Plans extra gym time to compensate."
    },
    {
      date: "2026-08-29",
      eaten: 4000,
      active: 400,
      weight: null,
      exercise: ["walking"],
      note: "Cat woke him early morning again (2nd morning in a row) and it triggered early-morning eating: yogurt with a lot of honey ~500 + ~500 other, ~1000 kcal before the day even started. Pattern: cat wake-up → early-morning eating. Lunch: yogurt + honey and biscoff cream, 550 kcal. Evening: 450 kcal, no items given. Extra +700 later, no items given — high-calorie day, he flagged it himself. Dinner +700, no items given. Late night ~23:50 (still before midnight, counted into this day): +600, no items given — high-calorie day overall, he flagged it himself and chose to keep tracking rather than skip logging it. Garmin active 400 kcal, mostly from walking."
    },
    {
      date: "2026-08-30",
      eaten: 1900,
      active: null,
      weight: null,
      exercise: [],
      note: "Day 4: eaten 1900, no items given."
    },
    {
      date: "2026-08-31",
      eaten: 3290,
      active: null,
      weight: null,
      exercise: [],
      note: "Day 5: banana 120, morning yogurt 500g+biscoff+honey 470, lunch IKEA 20 meatballs+cream sauce+legumes+potato puree ~1180, plus 4x70g chocolate bars 380 kcal each = 1520. He flagged the chocolate himself as unfortunate. High-calorie day, over target."
    },
    {
      date: "2026-09-01",
      eaten: 3010,
      active: 917,
      weight: null,
      exercise: ["leg day"],
      note: "Day 6: morning carbs 360, lunch chicken+couscous 600, chocolate 400, yogurt 350+honey 200+biscoff cream 400, evening +700 (no items given). He flagged it himself as a lot, feels bad about it. Leg day planned. He identified the cause: no salad available — plans more yogurt and salads from tomorrow."
    },
    {
      date: "2026-09-02",
      eaten: 3270,
      active: null,
      weight: null,
      exercise: [],
      note: "Day 7: planned in advance — yogurt 350, honey 120, salad 150, chicken+couscous 450. Planned chocolate 200 skipped. Lunch ran over with extra yogurt+honey 500. Evening +1100 (no items given). Late night +600 more, no items given. Heavy work day, limited capacity to diet strictly."
    },
    {
      date: "2026-09-03",
      eaten: 3500,
      active: 748,
      weight: null,
      exercise: [],
      note: "Day 8: breakfast+lunch 1300, evening 600, plus another 800 — no items given for any of them. He said he would skip dinner, then reported ~800 for dinner the next morning, so the day closed at 3500. Garmin active confirmed 748 (was ~447 mid-evening), consistent with the 45 min uphill walk he had planned, though he did not confirm the walk itself."
    },
    {
      date: "2026-09-04",
      eaten: 2700,
      active: null,
      weight: null,
      exercise: [],
      note: "Day 9: morning — 4 cookies 200, yogurt 350, 4 small pieces of chocolate 150; lunch 800; evening 1200, no items given. All figures given directly by him."
    },
    {
      date: "2026-09-05",
      eaten: 3150,
      active: null,
      weight: null,
      exercise: [],
      note: "Day 10: morning 500 (250 + 250), then 300, salad with cheese 350, then 2000 in sweets. All figures given directly by him except the salad, which he gave as \"around 350\". He planned a 10K run in the evening — not confirmed, so not recorded as exercise. He was hard on himself about the sweets."
    }
  ]
};
