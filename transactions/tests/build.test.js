const test = require('node:test');
const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.join(__dirname, '..');

test('build.py bakes src into index.html with a build hash', () => {
  execFileSync('python3', ['build.py'], { cwd: ROOT });
  const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
  assert.ok(!html.includes('__SCRIPTS__'), 'scripts placeholder replaced');
  assert.ok(!html.includes('__BUILD__'), 'build placeholder replaced');
  assert.match(html, /<meta name="build" content="[0-9a-f]{12}">/);
  assert.ok(html.includes('root.TxPlay = Object.assign'), 'src files inlined');
});
