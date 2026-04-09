(function () {
  function clamp(n, min, max) { return Math.max(min, Math.min(max, n)); }

  document.querySelectorAll('.cal-gauge').forEach(function (el) {
    var intake = parseFloat(el.dataset.intake || "0");
    var tdee   = parseFloat(el.dataset.tdee   || "1");
    var deficit= parseFloat(el.dataset.deficit|| "0");
    var active = parseFloat(el.dataset.active || "0");
    var weight = el.dataset.weight || "";

    // Main donut geometry
    var rMain = 56, cMain = 2 * Math.PI * rMain;
    var rAct  = 68, cAct  = 2 * Math.PI * rAct;

    // Progress vs TDEE
    var ratio = intake / tdee;
    var arc   = clamp(ratio, 0, 1.5);
    var dashMain = (cMain * arc), gapMain = cMain - dashMain;

    // Active calories ring
    var actRatio = clamp(active / tdee, 0, 1);
    var dashAct = (cAct * actRatio), gapAct = cAct - dashAct;

    // Set stroke dashes
    var intakeEl = el.querySelector('.intake');
    var activeEl = el.querySelector('.active');
    intakeEl.setAttribute('stroke-dasharray', dashMain + ' ' + gapMain);
    activeEl.setAttribute('stroke-dasharray', dashAct + ' ' + gapAct);

    // Color logic: positive deficit = good (green), negative = surplus (red)
    if (deficit > 0) {
      el.classList.add('deficit');
      intakeEl.style.stroke = '#10b981';
    } else if (deficit < 0) {
      el.classList.add('surplus');
      intakeEl.style.stroke = '#ef4444';
    } else {
      el.classList.add('deficit');
      intakeEl.style.stroke = '#94a3b8';
    }

    // Center label
    var sign = deficit > 0 ? '-' : (deficit < 0 ? '+' : '');
    el.querySelector('.labels .deficit').textContent = sign + Math.abs(deficit).toFixed(0) + ' kcal';

    // Pills (if they exist)
    var vIntake = el.querySelector('.v-intake');
    var vTdee = el.querySelector('.v-tdee');
    var vActive = el.querySelector('.v-active');
    var vWeight = el.querySelector('.v-weight');
    if (vIntake) vIntake.textContent = isFinite(intake) ? Math.round(intake) : '—';
    if (vTdee) vTdee.textContent = isFinite(tdee) ? Math.round(tdee) : '—';
    if (vActive) vActive.textContent = isFinite(active) ? Math.round(active) : '—';
    if (vWeight && weight) vWeight.textContent = weight;
  });
})();
