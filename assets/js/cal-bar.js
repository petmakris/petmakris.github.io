(function () {
  function clamp(n, min, max) { return Math.max(min, Math.min(max, n)); }
  function pct(part, whole) { return whole > 0 ? (part / whole) * 100 : 0; }

  document.querySelectorAll('.cal-bar').forEach(function (el) {
    var intake = parseFloat(el.dataset.intake || "0");
    var tdee = parseFloat(el.dataset.tdee || "1");
    var active = parseFloat(el.dataset.active || "0");
    var rmr = Math.max(tdee - active, 0);

    // Build segments
    var bar = el.querySelector('.bar');

    // remove old if re-rendering
    bar.innerHTML = '';

    // RMR segment
    var segR = document.createElement('div');
    segR.className = 'seg rmr';
    segR.style.width = clamp(pct(rmr, tdee), 0, 100) + '%';
    bar.appendChild(segR);

    // Active segment
    var segA = document.createElement('div');
    segA.className = 'seg active';
    segA.style.left = clamp(pct(rmr, tdee), 0, 100) + '%';
    segA.style.width = clamp(pct(active, tdee), 0, 100) + '%';
    bar.appendChild(segA);

    // Decide deficit vs surplus
    var deficit = tdee - intake;
    if (deficit >= 0) {
      // DEFICIT: green gap inside right edge
      var segG = document.createElement('div');
      segG.className = 'seg gap';
      segG.style.width = clamp(pct(deficit, tdee), 0, 100) + '%';
      bar.appendChild(segG);
      el.classList.add('is-deficit');
      el.querySelector('.chip-balance').style.color = '#16a34a';
    } else {
      // SURPLUS: red cap overlay INSIDE the fixed track
      var cap = document.createElement('div');
      cap.className = 'surplus-cap';
      var surplusPct = clamp(pct(-deficit, tdee), 0, 100); // cap at 100% of track
      cap.style.width = surplusPct + '%';
      bar.appendChild(cap);
      el.classList.remove('is-deficit');
      el.querySelector('.chip-balance').style.color = '#dc2626';
    }


    // Legend numbers
    el.querySelector('.v-intake').textContent = Math.round(intake);
    el.querySelector('.v-tdee').textContent = Math.round(tdee);
    el.querySelector('.v-rmr').textContent = Math.round(rmr);
    el.querySelector('.v-active').textContent = Math.round(active);

    var bType = el.querySelector('.v-btype');
    var bVal = el.querySelector('.v-bval');
    if (deficit >= 0) {
      bType.textContent = 'Deficit';
      bVal.textContent = Math.round(deficit);
      // color the chip text subtly green
      el.querySelector('.chip-balance').style.color = '#16a34a';
    } else {
      bType.textContent = 'Surplus';
      bVal.textContent = Math.round(-deficit);
      el.querySelector('.chip-balance').style.color = '#dc2626';
    }

    // ARIA label for screen readers
    bar.setAttribute(
      'aria-label',
      'RMR ' + Math.round(rmr) + ' kcal, Active ' + Math.round(active) +
      ' kcal, TDEE ' + Math.round(tdee) + ' kcal, Intake ' + Math.round(intake) +
      ' kcal, ' + (deficit >= 0 ? 'Deficit ' + Math.round(deficit) : 'Surplus ' + Math.round(-deficit)) + ' kcal'
    );
  });
})();
