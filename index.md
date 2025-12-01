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
        <h5 class="card-title text-center mb-3">Weight</h5>
        <canvas id="weightChart" style="max-height: 300px;"></canvas>
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
  const intakes = [];
  const tdees = [];
  const actives = [];
  
  {% for post in site.posts reversed %}
    {% assign metrics = post.cal %}
    {% if metrics.weight or metrics.deficit %}
      dates.push('{{ post.date | date: "%m/%d" }}');
      weights.push({{ metrics.weight | default: 'null' }});
      deficits.push({{ metrics.deficit | default: 'null' }});
      intakes.push({{ metrics.intake | default: 'null' }});
      tdees.push({{ metrics.tdee | default: 'null' }});
      actives.push({{ metrics.active | default: 'null' }});
    {% endif %}
  {% endfor %}
  
  // Weight Chart
  const weightCtx = document.getElementById('weightChart').getContext('2d');
  
  new Chart(weightCtx, {
    type: 'line',
    data: {
      labels: dates,
      datasets: [{
        label: 'Βάρος (kg)',
        data: weights,
        borderColor: '#4a90e2',
        backgroundColor: 'rgba(74, 144, 226, 0.1)',
        borderWidth: 1,
        tension: 0.4,
        fill: true,
        pointRadius: 1,
        pointHoverRadius: 1
      }]
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
          mode: 'index',
          intersect: false,
          callbacks: {
            label: function(context) {
              return context.dataset.label + ': ' + context.parsed.y.toFixed(1) + ' kg';
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: false,
          ticks: {
            callback: function(value) {
              return value.toFixed(1) + ' kg';
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
          order: 2
        },
        {
          type: 'bar',
          label: 'Ενεργές θερμίδες (kcal)',
          data: actives,
          backgroundColor: 'rgba(59, 130, 246, 0.6)',
          borderColor: '#3b82f6',
          borderWidth: 1,
          categoryPercentage: 0.8,
          barPercentage: 0.45,
          order: 1
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
              if (context.dataset.label.includes('Ενεργές')) {
                return context.dataset.label + ': ' + Math.round(value) + ' kcal';
              }
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
    {% endfor %}
    </tbody>
  </table>
</div>



