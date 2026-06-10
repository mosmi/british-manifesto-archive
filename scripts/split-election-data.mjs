#!/usr/bin/env node
/**
 * Extracts ELECTIONS from js/data.js into data/elections/*.json
 * Run from british-manifesto-archive/: node scripts/split-election-data.mjs
 */
import fs from 'fs';
import path from 'path';
import vm from 'vm';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, '..');
const dataJs = fs.readFileSync(path.join(root, 'js/data.js'), 'utf8');

const sandbox = {};
vm.runInNewContext(
  dataJs + '\nthis.PARTIES=PARTIES;this.ELECTIONS=ELECTIONS;this.NATIONS=NATIONS;',
  sandbox
);

const { ELECTIONS } = sandbox;
if (!ELECTIONS?.length) {
  console.error('Could not read ELECTIONS from data.js');
  process.exit(1);
}

const outDir = path.join(root, 'data/elections');
fs.mkdirSync(outDir, { recursive: true });

const index = ELECTIONS.map(e => ({
  id: e.id,
  year: e.year,
  displayYear: e.displayYear,
  date: e.date,
  winner: e.winner,
  pm: e.pm,
  totalSeats: e.totalSeats,
}));

ELECTIONS.forEach(e => {
  fs.writeFileSync(
    path.join(outDir, `${e.id}.json`),
    JSON.stringify(e, null, 2) + '\n'
  );
});

fs.writeFileSync(
  path.join(outDir, 'index.json'),
  JSON.stringify(index, null, 2) + '\n'
);

console.log(`Wrote ${ELECTIONS.length} election files + index.json`);
