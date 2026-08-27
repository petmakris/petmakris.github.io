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
    maintenanceRest: 1930,      // Mifflin-St Jeor: male, 104 kg, 176 cm, age 43
    startWeight: 104            // kg on day 1 — the weight curve starts here
  },
  days: []
};
