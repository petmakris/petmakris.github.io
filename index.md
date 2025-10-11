---
layout: default
title: Home
---



<style>
  .summary-table {
    width: 100%;
    border-collapse: collapse;
    margin: 2rem 0;
    font-size: 0.95rem;
  }

  .summary-table thead th {
    background: linear-gradient(90deg, #e3f2fd 0%, #f0f7ff 100%);
    color: #094067;
    text-align: left;
    padding: 0.75rem;
    border-bottom: 2px solid #cfe0f5;
  }

  .summary-table tbody tr:nth-child(even) td {
    background-color: #f8fafc;
  }

  .summary-table tbody tr:hover td {
    background-color: #eef6ff;
  }

  .summary-table tbody tr.is-today td {
    background: linear-gradient(90deg, #fff4cc 0%, #ffeab0 100%);
    font-weight: 600;
  }

  .summary-table td {
    padding: 0.75rem;
    border-bottom: 1px solid #e5e7eb;
    vertical-align: middle;
  }

  .summary-table td.numeric {
    text-align: right;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }

  .summary-table td .date-link {
    display: inline-block;
    color: #0f4c81;
    font-weight: 700;
    text-decoration: none;
  }

  .summary-table td .date-link:hover,
  .summary-table td .date-link:focus {
    text-decoration: underline;
  }

  .summary-table td .date-meta {
    margin-top: 0.15rem;
    font-size: 0.85rem;
  }

  .badge {
    display: inline-block;
    min-width: 4.2rem;
    padding: 0.25rem 0.65rem;
    border-radius: 999px;
    font-weight: 700;
    text-align: center;
    color: #fff;
    font-variant-numeric: tabular-nums;
  }

  .badge-positive {
    background-color: #2da44e;
  }

  .badge-negative {
    background-color: #d73a49;
  }

  .badge-neutral {
    background-color: #6b7280;
  }
</style>

## Καθημερινά Στατιστικά

<table class="summary-table">
  <thead>
    <tr>
      <th>Ημέρα</th>
      <th class="numeric">Kgr</th>
      <th class="numeric">Intake</th>
      <th class="numeric">TDEE</th>
      <th class="numeric">Ενεργές</th>
      <th class="numeric">Deficit</th>
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
      <tr class="{% if post_ymd == today_ymd %}is-today{% endif %}">
        <td>
          <a class="date-link" href="{{ post.url | relative_url }}">
            <div class="date-meta">{{ post.date | date: "%Y-%m-%d" }}</div>
          </a>
        </td>
        <td class="numeric">
          {% if weight != nil %}
            {{ weight }}
          {% else %}
            —
          {% endif %}
        </td>
        <td class="numeric">
          {% if intake != nil %}
            {{ intake }} kcal
          {% else %}
            —
          {% endif %}
        </td>
        <td class="numeric">
          {% if tdee != nil %}
            {{ tdee }} kcal
          {% else %}
            —
          {% endif %}
        </td>
        <td class="numeric">
          {% if active != nil %}
            {{ active }} kcal
          {% else %}
            —
          {% endif %}
        </td>
        <td class="numeric">
          {% if deficit_raw != nil %}
            {% if deficit_value > 0 %}
              <span class="badge badge-positive">+{{ deficit_value }} kcal</span>
            {% elsif deficit_value < 0 %}
              <span class="badge badge-negative">{{ deficit_value }} kcal</span>
            {% else %}
              <span class="badge badge-neutral">0 kcal</span>
            {% endif %}
          {% else %}
            <span class="badge badge-neutral">—</span>
          {% endif %}
        </td>
      </tr>
    {% endfor %}
  </tbody>
</table>

# Κανόνες

- Χαμηλός γλυκαιμικός δείκτης, περιορισμένοι υδατάνθρακες (κυρίως σύνθετοι, εκτός από το μέλι)
- Υψηλή πρόσληψη πρωτεΐνης
- Περιορισμένα λιπαρά
- Όχι τηγανητών
- Όχι λάδι στο μαγείρεμα
- Ημερήσιος στόχος: θερμιδικό έλλειμμα 500 kcal.

RMR 1900 θερμίδες, Βάρος 100kg, 18 Αυγούστου 2025.


# Πίνακας συντομέυσεων

- αυγό: 80 kcal
- scoop πρωτείνης 115 kcal
- ομελέτα: 220 kcal (250ml ασπράδι 120 kcal + λαχανικά ή/και μανιτάρια 100 kcal)
- φρούτο: 120 kcal (πχ. μπανάνα)
- κουλούρι: Θεσσαλονίκης  225 kcal (80gr, με σουσάμι)
- κοτόπουλο: 300 kcal (ψημένο 180gr στή kcalος)
- ζωμός: 60 kcal (1 cup βοδινός λιπαρός)
- μπιφτέκι: 130 kcal (κοτόπουλο)
- σαλάτα: 100 kcal (με ξύδι, χωρίς λάδι)
- σαλάτα μεγάλη: 150 kcal (με ξύδι, χωρίς λάδι)
- ντάκος: 320 kcal (3 παξιμάδια 3x80 kcal = 240 kcal + 1 ντομάτα μεγάλη, βαλσάμικο)
- γιαούρτι: 140 kcal (200gr 2% λιπαρά)
- παξιμάδι: 80 kcal (ολικής/χαρουπιού)
- cottage 90 kcal (100gr)
- τσάνος: 27 kcal (κράκερ με υψηλό fiber)
- πατάτα: 140 kcal (150gr ψητή χωρίς λάδι)
- λάδι 60 kcal (ελαιόλαδο ωμό)
- μέλι: 40 kcal (1 κ.γ.)
- ταχίνι:  80 kcal (1 κ.γ.)
- βρώμη: 190 kcal (50gr ολικής τρίμα)
- αμυγδαλόγαλο: 60 kcal (250ml χωρίς προσ θήκη ζάχαρης)
- preworkout: 430 kcal (αμυγδαλόγαλο, βρώμη, 2x μέλι, ταχίνι)
- ρυζογκοφρέτα: 40 kcal (1 τεμάχιο)
- καρύδια: μεσαία χούφτα 250 kcal
- Φρυγανιά: 70 kcal
- χόρτα: 100 kcal
- πίτα: 190 kcal (ολικής)
