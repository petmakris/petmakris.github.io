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
    var ratio = intake / tdee;               // e.g. 0.85 (85%)
    // show up to 150% of TDEE for visibility, cap the arc
    var arc   = clamp(ratio, 0, 1.5);
    var dashMain = (cMain * arc), gapMain = cMain - dashMain;

    // Active calories ring: scale relative to TDEE (cap at 100%)
    var actRatio = clamp(active / tdee, 0, 1);
    var dashAct = (cAct * actRatio), gapAct = cAct - dashAct;

    // Set stroke dashes
    var intakeEl = el.querySelector('.intake');
    var activeEl = el.querySelector('.active');
    intakeEl.setAttribute('stroke-dasharray', dashMain + ' ' + gapMain);
    activeEl.setAttribute('stroke-dasharray', dashAct + ' ' + gapAct);

    // Color logic: surplus (deficit > 0) → red
    if (deficit > 0) {
      el.classList.add('surplus');
      intakeEl.style.stroke = '#dc2626';
    } else {
      el.classList.add('deficit');
      intakeEl.style.stroke = '#16a34a';
    }

    // Center label
    var sign = deficit > 0 ? '+' : '';
    el.querySelector('.labels .deficit').textContent = sign + deficit.toFixed(0) + ' kcal';

    // Pills
    el.querySelector('.v-intake').textContent = isFinite(intake) ? Math.round(intake) : '—';
    el.querySelector('.v-tdee').textContent   = isFinite(tdee)   ? Math.round(tdee)   : '—';
    el.querySelector('.v-active').textContent = isFinite(active) ? Math.round(active) : '—';
    if (weight && el.querySelector('.v-weight')) {
      el.querySelector('.v-weight').textContent = weight;
    }
  });
})();
