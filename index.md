---
layout: default
title: Home
---

<!-- Chart.js CDN -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>

{% include dashboard.html mode="current" %}

<!-- ========== Archive Link ========== -->
<div style="text-align:center; margin-top:2rem;">
  <a href="{{ '/archive/' | relative_url }}" style="color:var(--color-text-muted); font-size:0.85rem; text-decoration:none;">
    <i class="bi bi-archive"></i> View archive
  </a>
</div>
