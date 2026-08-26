/* Diet journal data. This file IS the notebook: Claude edits it on every
 * prompt, the page just renders it. Newest day last. The operating procedure
 * lives in the repo skill .claude/skills/diet-journal/SKILL.md.
 *
 * Everything that reaches the page is written in Greek: item names, notes,
 * exercise. Only the code comments here are English.
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
        {name: "Γιαούρτι 200γρ + μέλι",                 kcal: 260, note: "δείγμα"},
        {name: "Καφές με γάλα",                         kcal:  40, note: "δείγμα"},
        {name: "Χυμός πορτοκάλι 250ml",                 kcal: 110, note: "δείγμα"},
        {name: "Στήθος κοτόπουλο ψητό 180γρ",           kcal: 300, note: "δείγμα"},
        {name: "Ρύζι 150γρ βρασμένο + σαλάτα, ελαιόλαδο", kcal: 330, note: "δείγμα"},
        {name: "Μήλο",                                  kcal:  95, note: "δείγμα"},
        {name: "Αμύγδαλα 25γρ",                         kcal: 145, note: "δείγμα"},
        {name: "2 φέτες ψωμί ολικής + φέτα 60γρ",       kcal: 400, note: "δείγμα"},
        {name: "Μπανάνα",                               kcal:  90, note: "δείγμα"},
        {name: "Μαύρη σοκολάτα 20γρ",                   kcal: 110, note: "δείγμα"}
      ],
      active: 520,
      exercise: ["50΄ γρήγορο περπάτημα", "20΄ ασκήσεις με το βάρος του σώματος"],
      note: "ΔΕΙΓΜΑ — φαγητό επινοημένο, δεν καταναλώθηκε. Υπάρχει μόνο για να φαίνεται πώς εμφανίζεται μια πλήρης ημέρα. Το πρόγραμμα ξεκινά 27/08/2026· τότε σβήνεται."
    }
  ]
};
