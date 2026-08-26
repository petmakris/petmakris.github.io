/* Diet journal data. This file IS the notebook: Claude edits it on every
 * prompt, the page just renders it. Newest day last. See PROTOCOL.md for
 * the full operating procedure (how to resume from a fresh Claude session).
 *
 * Units: kcal everywhere. `active` is the Garmin "active calories" figure
 * for the day. `maintenanceRest` is resting maintenance (what the body burns
 * with zero recorded activity); total burn for a day = maintenanceRest +
 * active, and deficit = burn - consumed. Target deficit: 600 kcal/day.
 */
window.DIET = {
  plan: {
    start: "2026-08-26",        // day 1
    lengthDays: 90,             // three months → ends 2026-11-23
    deficitTarget: 600,         // kcal/day — the only sustainable number
    maintenanceRest: null       // kcal/day at rest — NOT YET PROVIDED, ask Petros
  },
  days: [
    {
      date: "2026-08-26",
      items: [
        // {name: "Greek yogurt 200g + honey", kcal: 260, note: "estimate"}
      ],
      active: null,             // Garmin active calories, filled end of day
      exercise: [],             // e.g. ["45 min brisk walk"]
      note: "Day 1 — journal opened, nothing logged yet."
    }
  ]
};
