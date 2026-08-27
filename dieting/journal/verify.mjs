#!/usr/bin/env node
// Checks that every day.eaten in data.js matches its bold total row in
// log.md, and that the two files list exactly the same dates. Run before
// every push — see .claude/skills/diet-journal/SKILL.md.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const dir = dirname(fileURLToPath(import.meta.url));
const dataSrc = readFileSync(join(dir, "data.js"), "utf8");
const logSrc = readFileSync(join(dir, "log.md"), "utf8");

const literal = dataSrc.slice(dataSrc.indexOf("{"), dataSrc.lastIndexOf("}") + 1);
const DIET = new Function(`return (${literal})`)();

const dataTotals = new Map(DIET.days.map((d) => [d.date, d.eaten]));

const sectionHeads = [...logSrc.matchAll(/^## (\d{4}-\d{2}-\d{2})/gm)];
const logTotals = new Map();
for (let i = 0; i < sectionHeads.length; i++) {
  const date = sectionHeads[i][1];
  const start = sectionHeads[i].index;
  const end = i + 1 < sectionHeads.length ? sectionHeads[i + 1].index : logSrc.length;
  const body = logSrc.slice(start, end);
  const m = body.match(/\*\*Σύνολο\*\*\s*\|\s*\*\*([\d.]+)\*\*/);
  if (!m) {
    console.error(`log.md ${date}: no bold total row found`);
    process.exitCode = 1;
    continue;
  }
  logTotals.set(date, Number(m[1].replace(/\./g, "")));
}

for (const [date, eaten] of dataTotals) {
  if (eaten == null) continue; // no food logged yet for this day
  if (!logTotals.has(date)) {
    console.error(`${date}: in data.js (eaten=${eaten}) but no log.md section`);
    process.exitCode = 1;
  } else if (logTotals.get(date) !== eaten) {
    console.error(`${date}: data.js eaten=${eaten} but log.md total=${logTotals.get(date)}`);
    process.exitCode = 1;
  }
}

for (const date of logTotals.keys()) {
  if (!dataTotals.has(date)) {
    console.error(`${date}: in log.md but missing from data.js`);
    process.exitCode = 1;
  }
}

if (process.exitCode) {
  console.error("Diet journal totals mismatch — fix before pushing.");
} else {
  console.log(`OK — ${DIET.days.length} day(s) verified.`);
}
