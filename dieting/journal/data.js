/* Diet journal data. This file IS the notebook: Claude edits it on every
 * prompt, the page just renders it. Newest day last. The operating procedure
 * lives in the repo skill .claude/skills/diet-journal/SKILL.md.
 *
 * Units: kcal everywhere. `active` is the Garmin "active calories" figure
 * for the day. `maintenanceRest` is resting maintenance (what the body burns
 * with zero recorded activity); total burn for a day = maintenanceRest +
 * active, and deficit = burn - consumed. Target deficit: 600 kcal/day.
 */
window.DIET = {
  plan: {
    start: "2026-08-27",        // day 1
    lengthDays: 90,             // three months → ends 2026-11-24
    deficitTarget: 600,         // kcal/day — the only sustainable number
    maintenanceRest: 1930       // Mifflin-St Jeor: male, 104 kg, 176 cm, age 43
  },
  days: [
    {
      date: "2026-08-26",
      items: [
        {name: "Greek yogurt 200g + honey",            kcal: 260, note: "sample"},
        {name: "Coffee with milk",                     kcal:  40, note: "sample"},
        {name: "Orange juice 250ml",                   kcal: 110, note: "sample"},
        {name: "Grilled chicken breast 180g",          kcal: 300, note: "sample"},
        {name: "Rice 150g cooked + salad, olive oil",  kcal: 330, note: "sample"},
        {name: "Apple",                                kcal:  95, note: "sample"},
        {name: "Almonds 25g",                          kcal: 145, note: "sample"},
        {name: "2 slices wholegrain bread + feta 60g", kcal: 400, note: "sample"},
        {name: "Banana",                               kcal:  90, note: "sample"},
        {name: "Dark chocolate 20g",                   kcal: 110, note: "sample"}
      ],
      active: 520,
      exercise: ["50 min brisk walk", "20 min bodyweight circuit"],
      note: "SAMPLE DAY — invented food, not eaten. Here only to show how a full day renders. The plan starts 2026-08-27; delete this entry then."
    }
  ]
};
