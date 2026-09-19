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
    start: "2026-09-21",        // day 1 — Monday
    lengthDays: 90,             // three months → ends 2026-12-19
    deficitTarget: 600,         // kcal/day — the only sustainable number
    maintenanceRest: 1905,      // Mifflin-St Jeor: male, 101.5 kg, 176 cm, age 43
    startWeight: 101.5,         // PENDING: last real weigh-in (2026-09-07), standing in until he weighs in on day 1
    defaultActive: 450          // used when a day has no Garmin active figure — his Garmin stays consistent day to day, so this stands in rather than the day counting as a gap
  },
  days: [
  ]
};
