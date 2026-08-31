/* Diet journal data. This file IS the notebook the page reads, and it holds
 * only per-day totals: the meal-by-meal breakdown lives in log.md, which the
 * page never loads and never links to. Newest day last. The operating
 * procedure is in the repo skill .claude/skills/diet-journal/SKILL.md.
 *
 * Units: kcal everywhere. `eaten` is the day's total intake. `active` is the
 * Garmin "active calories" figure. `maintenanceRest` is resting maintenance;
 * burn = maintenanceRest + active, and deficit = burn - eaten. Target: 600.
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
    startWeight: 100.0          // kg on day 1 — weighed in 2026-08-27
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
      eaten: 590,
      active: null,
      weight: null,
      exercise: [],
      note: "Day 5 so far: banana 120, lunch yogurt 500g+biscoff+honey 470. Running total, more may come."
    }
  ]
};
