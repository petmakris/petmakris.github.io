const test = require('node:test');
const assert = require('node:assert/strict');
const { renderSequence } = require('../src/seqrender.js');

const spec = {
  alt: 'two actors',
  actors: [{ id: 'a', label: 'Alpha\nOne', tone: 'edge' }, { id: 'pool', label: 'Pool', tone: 'hot' }],
  rails: [{ actor: 'pool', from: 0, to: 1, tone: 'hot', label: 'held' }],
  steps: [
    { from: 'a', to: 'pool', arrow: 'request', label: 'BEGIN', sub: 'first touch', tone: 'hot', note: 'taken', phase: 'start' },
    { from: 'a', to: 'pool', arrow: 'request', label: 'COMMIT', tone: 'good', note: 'released' },
    { from: 'a', to: 'a', arrow: 'self', label: 'done' },
    { from: 'a', to: 'pool', arrow: 'band', label: 'a band' },
  ],
  legend: [{ tone: 'hot', label: 'holds' }],
};

test('renderSequence draws actors, rows, a rail, a phase and a legend', () => {
  const svg = renderSequence(spec);
  assert.ok(svg.startsWith('<svg class="seq"'));
  assert.ok(svg.endsWith('</svg>'));
  assert.ok(svg.includes('Alpha') && svg.includes('One'), 'two-line actor label');
  assert.ok(svg.includes('class="rail t-hot"'), 'rail on the pool');
  assert.ok(svg.includes('class="phase-label"') && svg.includes('start'));
  assert.ok(svg.includes('class="row-note t-hot"') && svg.includes('taken'));
  assert.ok(svg.includes('class="legend-text"') && svg.includes('holds'));
  assert.equal((svg.match(/class="row-num"/g) || []).length, 3, 'bands are not numbered');
});

test('renderSequence escapes labels', () => {
  const svg = renderSequence({ actors: [{ id: 'a', label: 'A' }, { id: 'b', label: 'B' }],
    steps: [{ from: 'a', to: 'b', arrow: 'request', label: '<script>' }] });
  assert.ok(!svg.includes('<script>'));
  assert.ok(svg.includes('&lt;script&gt;'));
});
