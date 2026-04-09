---
layout: default
title: Home
---

<!-- Chart.js CDN -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>

{% comment %} ========== Compute stats ========== {% endcomment %}

{% assign first_weight = nil %}
{% assign last_weight = nil %}
{% assign first_date = nil %}
{% assign last_date = nil %}
{% assign days_tracked = 0 %}
{% assign total_deficit = 0 %}
{% assign deficit_days = 0 %}

{% for post in site.posts reversed %}
  {% assign metrics = post.cal %}
  {% if metrics.weight %}
    {% if first_weight == nil %}
      {% assign first_weight = metrics.weight | plus: 0.0 %}
      {% assign first_date = post.date | date: "%b %d, %Y" %}
    {% endif %}
    {% assign last_weight = metrics.weight | plus: 0.0 %}
    {% assign last_date = post.date | date: "%b %d" %}
  {% endif %}
  {% if metrics.deficit %}
    {% assign days_tracked = days_tracked | plus: 1 %}
    {% assign total_deficit = total_deficit | plus: metrics.deficit %}
    {% if metrics.deficit > 0 %}
      {% assign deficit_days = deficit_days | plus: 1 %}
    {% endif %}
  {% endif %}
{% endfor %}

{% assign weight_change = last_weight | minus: first_weight %}
{% assign weight_change_abs = weight_change | abs %}
{% if days_tracked > 0 %}
  {% assign avg_deficit = total_deficit | divided_by: days_tracked %}
{% else %}
  {% assign avg_deficit = 0 %}
{% endif %}

<!-- ========== Hero Progress Section ========== -->
<div class="card-surface hero-progress">
  <div class="hero-label">Progress</div>
  {% if weight_change < 0 %}
    <div class="hero-value positive">-{{ weight_change_abs }} kg</div>
  {% elsif weight_change > 0 %}
    <div class="hero-value negative">+{{ weight_change_abs }} kg</div>
  {% else %}
    <div class="hero-value" style="color:var(--color-text-muted);">0 kg</div>
  {% endif %}
  <div class="hero-sub">{{ first_weight }} kg &rarr; {{ last_weight }} kg &middot; since {{ first_date }}</div>

  <div class="hero-stats">
    <div class="hero-stat">
      <div class="stat-value">{{ days_tracked }}</div>
      <div class="stat-label">Days tracked</div>
    </div>
    <div class="hero-stat">
      <div class="stat-value">{{ deficit_days }}</div>
      <div class="stat-label">Days on target</div>
    </div>
    <div class="hero-stat">
      <div class="stat-value">{{ avg_deficit }} kcal</div>
      <div class="stat-label">Avg deficit</div>
    </div>
  </div>
</div>

<!-- ========== Last 7 Days Strip ========== -->
<div class="section-header">Last 7 days</div>
<div class="day-strip">
{% assign pill_count = 0 %}
{% for post in site.posts %}
  {% if pill_count >= 7 %}{% break %}{% endif %}
  {% assign metrics = post.cal %}
  {% if metrics.deficit != nil %}
    {% assign d = metrics.deficit | plus: 0 %}
    {% if d > 0 %}
      {% assign dot_class = "deficit" %}
      {% assign dot_label = d | prepend: "-" %}
    {% elsif d < 0 %}
      {% assign dot_class = "surplus" %}
      {% assign dot_label = d | abs | prepend: "+" %}
    {% else %}
      {% assign dot_class = "neutral" %}
      {% assign dot_label = "0" %}
    {% endif %}
    <a class="day-pill" href="{{ post.url | relative_url }}">
      <div class="dot {{ dot_class }}">{{ dot_label }}</div>
      <div class="day-label">{{ post.date | date: "%m/%d" }}</div>
    </a>
    {% assign pill_count = pill_count | plus: 1 %}
  {% endif %}
{% endfor %}
</div>

<!-- ========== Weight Trend Chart ========== -->
<div class="card-surface chart-card">
  <div class="chart-title">Weight trend</div>
  <canvas id="rollingAvgChart" style="max-height: 280px;"></canvas>
</div>

<!-- ========== Heatmap Calendar ========== -->
<div class="card-surface chart-card">
  <div class="chart-title">Daily balance</div>
  <div class="heatmap">
    <div class="heatmap-grid">
      {% for post in site.posts reversed %}
        {% assign metrics = post.cal %}
        {% if metrics.deficit != nil %}
          {% assign d = metrics.deficit | plus: 0 %}
          {% if d >= 500 %}
            {% assign cell_class = "deficit-strong" %}
          {% elsif d >= 200 %}
            {% assign cell_class = "deficit-medium" %}
          {% elsif d > 0 %}
            {% assign cell_class = "deficit-light" %}
          {% elsif d <= -500 %}
            {% assign cell_class = "surplus-strong" %}
          {% elsif d <= -200 %}
            {% assign cell_class = "surplus-medium" %}
          {% elsif d < 0 %}
            {% assign cell_class = "surplus-light" %}
          {% else %}
            {% assign cell_class = "missed" %}
          {% endif %}
          <a href="{{ post.url | relative_url }}" title="{{ post.date | date: '%Y-%m-%d' }}: {{ d }} kcal" class="heatmap-cell {{ cell_class }}"></a>
        {% endif %}
      {% endfor %}
    </div>
    <div class="heatmap-legend">
      <span>surplus</span>
      <span class="swatch" style="background:#ef4444;"></span>
      <span class="swatch" style="background:#fca5a5;"></span>
      <span class="swatch" style="background:#fee2e2;"></span>
      <span class="swatch" style="background:#f5f5f4;"></span>
      <span class="swatch" style="background:#dcfce7;"></span>
      <span class="swatch" style="background:#86efac;"></span>
      <span class="swatch" style="background:#22c55e;"></span>
      <span>deficit</span>
    </div>
  </div>
</div>

<!-- ========== Charts JS ========== -->
<script>
  const dates = [];
  const weights = [];
  const deficits = [];

  {% for post in site.posts reversed %}
    {% assign metrics = post.cal %}
    {% if metrics.weight or metrics.deficit %}
      dates.push('{{ post.date | date: "%m/%d" }}');
      weights.push({{ metrics.weight | default: 'null' }});
      deficits.push({{ metrics.deficit | default: 'null' }});
    {% endif %}
  {% endfor %}

  const weightSeries = weights.map(v => {
    const n = Number(v);
    return Number.isFinite(n) ? n : null;
  });

  function computeRollingAverage(data, windowSize) {
    const result = new Array(data.length).fill(null);
    const queue = [];
    let sum = 0;
    for (let i = 0; i < data.length; i++) {
      const value = data[i];
      if (Number.isFinite(value)) {
        queue.push({ index: i, value });
        sum += value;
      }
      while (queue.length && i - queue[0].index >= windowSize) {
        sum -= queue[0].value;
        queue.shift();
      }
      if (queue.length) {
        result[i] = sum / queue.length;
      }
    }
    return result;
  }

  const rollingAvg = computeRollingAverage(weightSeries, 7);

  // Weight trend chart
  new Chart(document.getElementById('rollingAvgChart'), {
    type: 'line',
    data: {
      labels: dates,
      datasets: [
        {
          label: 'Measurements',
          data: weightSeries,
          borderColor: 'rgba(37, 99, 235, 0.25)',
          borderWidth: 1,
          pointRadius: 2,
          pointHoverRadius: 4,
          pointBackgroundColor: 'rgba(37, 99, 235, 0.3)',
          pointBorderColor: 'rgba(37, 99, 235, 0.5)',
          showLine: false,
          spanGaps: true
        },
        {
          label: '7-day average',
          data: rollingAvg,
          borderColor: '#2563eb',
          backgroundColor: 'rgba(37, 99, 235, 0.06)',
          borderWidth: 2.5,
          pointRadius: 0,
          pointHoverRadius: 4,
          fill: true,
          tension: 0.4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      interaction: { intersect: false, mode: 'index' },
      plugins: {
        legend: {
          display: true,
          position: 'top',
          labels: {
            usePointStyle: true,
            font: { size: 11, family: 'Inter' },
            color: '#78716c'
          }
        },
        tooltip: {
          callbacks: {
            label: ctx => {
              const v = ctx.parsed.y;
              return ctx.dataset.label + ': ' + (Number.isFinite(v) ? v.toFixed(1) + ' kg' : '-');
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: false,
          grid: { color: 'rgba(0,0,0,0.04)' },
          ticks: {
            font: { size: 11, family: 'Inter' },
            color: '#a8a29e',
            callback: v => v.toFixed(1) + ' kg'
          }
        },
        x: {
          grid: { display: false },
          ticks: {
            font: { size: 10, family: 'Inter' },
            color: '#a8a29e',
            maxRotation: 45
          }
        }
      }
    }
  });
</script>

<!-- ========== Collapsible Data Table ========== -->
<button class="expand-toggle" onclick="toggleTable(this)" type="button">
  <span class="arrow"><i class="bi bi-chevron-down"></i></span>
  Show detailed log
</button>

<div id="dataTable" style="display:none;">
  <div class="table-responsive">
    <table class="data-table">
      <thead>
        <tr>
          <th>Date</th>
          <th class="text-end d-none d-sm-table-cell">Kg</th>
          <th class="text-end">Intake</th>
          <th class="text-end d-none d-md-table-cell">TDEE</th>
          <th class="text-end d-none d-md-table-cell">Active</th>
          <th class="text-end">Balance</th>
        </tr>
      </thead>
      <tbody>
      {% assign today_ymd = site.time | date: "%Y-%m-%d" %}
      {% assign previous_timestamp = nil %}

      {% for post in site.posts %}
        {% assign post_ymd = post.date | date: "%Y-%m-%d" %}
        {% assign metrics = post.cal %}
        {% assign weight = metrics.weight %}
        {% assign intake = metrics.intake %}
        {% assign tdee = metrics.tdee %}
        {% assign active = metrics.active %}
        {% assign deficit_raw = metrics.deficit %}
        {% if deficit_raw != nil %}
          {% assign deficit_value = deficit_raw | plus: 0 %}
        {% endif %}
        {% assign post_timestamp = post.date | date: "%s" %}

        {% if previous_timestamp %}
          {% assign seconds_diff = previous_timestamp | minus: post_timestamp %}
          {% assign days_between = seconds_diff | divided_by: 86400 %}
          {% assign missed_days = days_between | minus: 1 %}
          {% if missed_days > 0 %}
            <tr class="missed-row">
              <td colspan="6">
                Missed {{ missed_days }} {% if missed_days == 1 %}day{% else %}days{% endif %}
              </td>
            </tr>
          {% endif %}
        {% endif %}
        <tr {% if post_ymd == today_ymd %}class="is-today"{% endif %}>
          <td>
            <a href="{{ post.url | relative_url }}" class="date-link">
              {{ post.date | date: "%Y-%m-%d" }}
            </a>
          </td>
          <td class="text-end d-none d-sm-table-cell">
            {% if weight != nil %}{{ weight }}{% else %}&mdash;{% endif %}
          </td>
          <td class="text-end">
            {% if intake != nil %}{{ intake }}{% else %}&mdash;{% endif %}
          </td>
          <td class="text-end d-none d-md-table-cell">
            {% if tdee != nil %}{{ tdee }}{% else %}&mdash;{% endif %}
          </td>
          <td class="text-end d-none d-md-table-cell">
            {% if active != nil %}{{ active }}{% else %}&mdash;{% endif %}
          </td>
          <td class="text-end">
            {% if deficit_raw != nil %}
              {% if deficit_value > 0 %}
                <span class="badge-deficit positive">-{{ deficit_value }}</span>
              {% elsif deficit_value < 0 %}
                <span class="badge-deficit negative">+{{ deficit_value | abs }}</span>
              {% else %}
                <span class="badge-deficit zero">0</span>
              {% endif %}
            {% else %}
              <span class="badge-deficit zero">&mdash;</span>
            {% endif %}
          </td>
        </tr>
        {% assign previous_timestamp = post_timestamp %}
      {% endfor %}
      </tbody>
    </table>
  </div>
</div>

<script>
function toggleTable(btn) {
  const table = document.getElementById('dataTable');
  const isHidden = table.style.display === 'none';
  table.style.display = isHidden ? 'block' : 'none';
  btn.classList.toggle('open', isHidden);
  btn.querySelector('span:last-child, span.arrow + *')
  btn.childNodes.forEach(n => {
    if (n.nodeType === 3 && n.textContent.trim()) {
      n.textContent = isHidden ? ' Hide detailed log' : ' Show detailed log';
    }
  });
}
</script>
