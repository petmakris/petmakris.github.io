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
      active: 850,
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
      eaten: 1000,
      active: null,
      weight: null,
      exercise: [],
      note: "Cat woke him mid-night again (2nd night in a row) and it triggered night eating: yogurt with a lot of honey ~500 + ~500 other, ~1000 kcal before the day even started. Pattern: cat wake-up → night eating."
    }
  ]
};
