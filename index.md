---
layout: default
title: Home
---

<!-- Chart.js CDN -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>

<!-- Charts Section -->
<div class="row g-4 mb-5">
  <div class="col-12">
    <div class="card shadow-sm">
      <div class="card-body">
        <h5 class="card-title text-center mb-1">7-day Rolling Average</h5>
        <p class="text-center text-muted small mb-3">Raw samples stay as faint dots so you can see the measurements behind the smoother trend.</p>
        <canvas id="rollingAvgChart" style="max-height: 320px;"></canvas>
      </div>
    </div>
  </div>
  
  <div class="col-12">
    <div class="card shadow-sm">
      <div class="card-body">
        <h5 class="card-title text-center mb-3">Calories</h5>
        <canvas id="deficitChart" style="max-height: 300px;"></canvas>
      </div>
    </div>
  </div>
</div>

<script>
  // Collect data from Jekyll posts
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
  
  const weightSeries = weights.map(value => {
    const numeric = Number(value);
    return Number.isFinite(numeric) ? numeric : null;
  });

  const formatKg = value => {
    return Number.isFinite(value) ? value.toFixed(1) + ' kg' : '-';
  };

  const weightTooltipLabel = context => {
    const yValue = context.parsed.y;
    return context.dataset.label + ': ' + formatKg(yValue);
  };

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
  
  const rollingAverageData = computeRollingAverage(weightSeries, 7);

  const rollingCtx = document.getElementById('rollingAvgChart').getContext('2d');
  new Chart(rollingCtx, {
    type: 'line',
    data: {
      labels: dates,
      datasets: [
        {
          label: 'Μετρήσεις',
          data: weightSeries,
          borderColor: '#4f46e5',
          borderWidth: 1,
          pointRadius: 3,
          pointHoverRadius: 5,
          pointBackgroundColor: 'rgba(79, 70, 229, 0.2)',
          pointBorderColor: '#4f46e5',
          pointStyle: 'rectRounded',
          showLine: false,
          spanGaps: true
        },
        {
          label: '7-day rolling avg',
          data: rollingAverageData,
          borderColor: '#2563eb',
          backgroundColor: 'rgba(37, 99, 235, 0.12)',
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 0,
          fill: true,
          tension: 0.35
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      interaction: {
        intersect: false,
        mode: 'index'
      },
      plugins: {
        legend: {
          display: true,
          position: 'top',
          labels: {
            usePointStyle: true
          }
        },
        tooltip: {
          callbacks: {
            label: weightTooltipLabel
          }
        }
      },
      scales: {
        y: {
          beginAtZero: false,
          ticks: {
            callback: function(value) {
              return formatKg(value);
            }
          }
        }
      }
    }
  });
  
  // Deficit Chart
  const deficitCtx = document.getElementById('deficitChart').getContext('2d');
  new Chart(deficitCtx, {
    type: 'bar',
    data: {
      labels: dates,
      datasets: [
        {
          label: 'Έλλειμμα/Πλεόνασμα (kcal)',
          data: deficits,
          backgroundColor: deficits.map(d => d >= 0 ? 'rgba(45, 164, 78, 0.8)' : 'rgba(215, 58, 73, 0.8)'),
          borderColor: deficits.map(d => d >= 0 ? '#2da44e' : '#d73a49'),
          borderWidth: 2,
          order: 1,
          categoryPercentage: 0.7,
          barPercentage: 0.65
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          display: true,
          position: 'top'
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const value = context.parsed.y;
              return value >= 0 ? 'Έλλειμμα: +' + Math.round(value) + ' kcal' : 'Πλεόνασμα: ' + Math.round(value) + ' kcal';
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: function(value) {
              return value + ' kcal';
            }
          },
          grid: {
            color: function(context) {
              if (context.tick.value === 0) {
                return '#000';
              }
              return 'rgba(0, 0, 0, 0.1)';
            },
            lineWidth: function(context) {
              if (context.tick.value === 0) {
                return 2;
              }
              return 1;
            }
          }
        }
      }
    }
  });
</script>

<!-- Data Table -->
<div class="table-responsive">
  <table class="table table-hover align-middle">
    <thead class="table-primary">
      <tr>
        <th></th>
        <th class="text-end d-none d-sm-table-cell">Kg</th>
        <th class="text-end">Intake</th>
        <th class="text-end d-none d-md-table-cell">TDEE</th>
        <th class="text-end d-none d-md-table-cell">Active</th>
        <th class="text-end">Deficit</th>
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
          <tr class="table-light text-center">
            <td colspan="6" class="text-muted small" style="color: #9ca3af;">
              Missed {{ missed_days }} {% if missed_days == 1 %}day{% else %}days{% endif %}
            </td>
          </tr>
        {% endif %}
      {% endif %}
      <tr {% if post_ymd == today_ymd %}class="table-warning fw-bold"{% endif %}>
        <td>
          <a href="{{ post.url | relative_url }}" class="text-decoration-none">
            {{ post.date | date: "%Y-%m-%d" }}
          </a>
        </td>
        <td class="text-end d-none d-sm-table-cell">
          {% if weight != nil %}
            {{ weight }}
          {% else %}
            —
          {% endif %}
        </td>
        <td class="text-end">
          {% if intake != nil %}
            {{ intake }} kcal
          {% else %}
            —
          {% endif %}
        </td>
        <td class="text-end d-none d-md-table-cell">
          {% if tdee != nil %}
            {{ tdee }} kcal
          {% else %}
            —
          {% endif %}
        </td>
        <td class="text-end d-none d-md-table-cell">
          {% if active != nil %}
            {{ active }} kcal
          {% else %}
            —
          {% endif %}
        </td>
        <td class="text-end">
          {% if deficit_raw != nil %}
            {% if deficit_value > 0 %}
              <span class="badge bg-success">{{ deficit_value }} kcal</span>
            {% elsif deficit_value < 0 %}
              <span class="badge bg-danger">{{ deficit_value | abs }} kcal</span>
            {% else %}
              <span class="badge bg-secondary">0 kcal</span>
            {% endif %}
          {% else %}
            <span class="badge bg-secondary">—</span>
          {% endif %}
        </td>
      </tr>
      {% assign previous_timestamp = post_timestamp %}
    {% endfor %}
    </tbody>
  </table>
</div>
