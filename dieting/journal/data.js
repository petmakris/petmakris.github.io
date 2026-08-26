/* Diet journal data. This file IS the notebook the page reads, and it holds
 * only per-day totals: the meal-by-meal breakdown lives in log.md, which the
 * page never loads and never links to. Newest day last. The operating
 * procedure is in the repo skill .claude/skills/diet-journal/SKILL.md.
 *
 * Units: kcal everywhere. `eaten` is the day's total intake. `active` is the
 * Garmin "active calories" figure. `maintenanceRest` is resting maintenance;
 * burn = maintenanceRest + active, and deficit = burn - eaten. Target: 600.
 *
 * Everything that reaches the page is written in Greek. Only these comments
 * are English.
 */
window.DIET = {
  plan: {
    start: "2026-08-27",        // day 1
    lengthDays: 90,             // three months → ends 2026-11-24
    deficitTarget: 600,         // kcal/day — the only sustainable number
    maintenanceRest: 1930,      // Mifflin-St Jeor: male, 104 kg, 176 cm, age 43
    startWeight: 104            // kg on day 1 — the weight curve starts here
  },
  days: [
    {
      date: "2026-08-26",
      eaten: 1880,              // breakdown in log.md
      weight: null,             // scale reading, when he gives one
      active: 520,
      exercise: ["50΄ γρήγορο περπάτημα", "20΄ ασκήσεις με το βάρος του σώματος"],
      note: "ΔΕΙΓΜΑ — φαγητό επινοημένο, δεν καταναλώθηκε. Το πρόγραμμα ξεκινά 27/08/2026· τότε σβήνεται."
    }
  ]
};
