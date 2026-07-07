#!/usr/bin/env node
/**
 * build-party-colours.mjs — compile shared palette artefacts from data/party-colours.json
 *
 * Default: validates JSON sources and regenerates tools/og-generator/party-colours.embed.js
 *
 *   node scripts/build-party-colours.mjs
 *   node scripts/build-party-colours.mjs --regenerate-aliases   # one-off: rebuild aliases from colour.py legacy dict (if still present)
 *
 * When adding a party: edit data/party-colours.json (+ aliases/overrides if needed), then re-run.
 */

import { readFileSync, writeFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const SLUGS_PATH = join(ROOT, 'data', 'party-colours.json');
const ALIASES_PATH = join(ROOT, 'data', 'party-colour-aliases.json');
const OVERRIDES_PATH = join(ROOT, 'data', 'party-colour-overrides.json');
const EMBED_PATH = join(ROOT, 'tools', 'og-generator', 'party-colours.embed.js');
const COLOUR_PY = join(ROOT, 'tools', 'hexmaps', 'scripts', 'colour.py');

const FIXED_ALIASES = {
  Conservative: 'conservative',
  Labour: 'labour',
  Liberal: 'liberal',
  Alliance: 'alliance',
  'Liberal Democrats': 'libdem',
  SNP: 'snp',
  'Plaid Cymru': 'plaid',
  UKIP: 'ukip',
  'Brexit Party': 'brexit',
  'Reform UK': 'reform',
  Green: 'green',
  DUP: 'dup',
  UUP: 'uup',
  'Sinn Féin': 'sinnfein',
  SDLP: 'sdlp',
  Speaker: 'speaker',
  Independent: 'independent',
  Others: 'others',
  'UK Unionist Party': 'ukup',
  'Independent Unionist': 'indunionist',
  'Alliance NI': 'allianceni',
  'Independent Republican': 'independentrepublican',
  'Democratic Labour': 'democraticlabour',
  Nationalist: 'nationalist',
  "Workers' Party": 'workerspartyie',
};

const FIXED_OVERRIDES = {
  'Ind. Labour': '#C84B5C',
  Other: '#AAAAAA',
};

function loadLegacyPyEntries() {
  const py = readFileSync(COLOUR_PY, 'utf8');
  if (!py.includes('PARTY_COLOURS = {')) return null;
  const m = py.match(/PARTY_COLOURS = \{([\s\S]*?)\n\}/);
  if (!m) return null;
  const entries = {};
  for (const line of m[1].split('\n')) {
    const mm = line.match(/^\s*"([^"]+)":\s*"([^"]+)"/);
    if (mm) entries[mm[1]] = mm[2];
  }
  return entries;
}

function buildAliasesFromLegacy(slugs, legacy) {
  const aliases = { ...FIXED_ALIASES };
  const slugKeys = new Set(Object.keys(slugs));
  for (const [name, hex] of Object.entries(legacy)) {
    if (slugKeys.has(name) || aliases[name]) continue;
    const norm = name.toLowerCase().replace(/[^a-z0-9]/g, '');
    if (slugKeys.has(norm) && slugs[norm].toUpperCase() === hex.toUpperCase()) {
      aliases[name] = norm;
      continue;
    }
    const slugMatch = Object.keys(slugs).find(
      (s) => legacy[s] && legacy[s].toUpperCase() === hex.toUpperCase()
        && slugs[s].toUpperCase() === hex.toUpperCase(),
    );
    if (slugMatch) aliases[name] = slugMatch;
  }
  return aliases;
}

function buildOverridesFromLegacy(slugs, aliases, legacy) {
  const overrides = { ...FIXED_OVERRIDES };
  for (const [name, hex] of Object.entries(legacy)) {
    if (name === 'Other') {
      overrides.Other = hex;
      continue;
    }
    const slug = aliases[name];
    if (slug && slugs[slug]?.toUpperCase() === hex.toUpperCase()) continue;
    if (slugs[name]?.toUpperCase() === hex.toUpperCase()) continue;
    if (!slug && !slugs[name] && !overrides[name]) overrides[name] = hex;
  }
  return overrides;
}

function resolveColour(name, slugs, aliases, overrides) {
  if (overrides[name]) return overrides[name];
  if (slugs[name]) return slugs[name];
  if (aliases[name]) return slugs[aliases[name]];
  return null;
}

function readJson(path) {
  return JSON.parse(readFileSync(path, 'utf8'));
}

function main() {
  const regenerate = process.argv.includes('--regenerate-aliases');
  const slugs = readJson(SLUGS_PATH);

  let aliases;
  let overrides;

  if (regenerate) {
    const legacy = loadLegacyPyEntries();
    if (!legacy) {
      console.error('No inline PARTY_COLOURS dict in colour.py — cannot regenerate aliases.');
      process.exit(1);
    }
    aliases = buildAliasesFromLegacy(slugs, legacy);
    overrides = buildOverridesFromLegacy(slugs, aliases, legacy);
    const missing = Object.entries(legacy).filter(
      ([name, hex]) => resolveColour(name, slugs, aliases, overrides)?.toUpperCase() !== hex.toUpperCase(),
    );
    if (missing.length) {
      console.error('Unresolved legacy entries:', missing.slice(0, 5));
      process.exit(1);
    }
    writeFileSync(ALIASES_PATH, `${JSON.stringify(aliases, null, 2)}\n`, 'utf8');
    writeFileSync(OVERRIDES_PATH, `${JSON.stringify(overrides, null, 2)}\n`, 'utf8');
  } else {
    if (!existsSync(ALIASES_PATH) || !existsSync(OVERRIDES_PATH)) {
      console.error('Missing aliases/overrides JSON — run with --regenerate-aliases once.');
      process.exit(1);
    }
    aliases = readJson(ALIASES_PATH);
    overrides = readJson(OVERRIDES_PATH);
  }

  for (const slug of Object.keys(FIXED_ALIASES)) {
    if (!aliases[slug] && FIXED_ALIASES[slug]) aliases[slug] = FIXED_ALIASES[slug];
  }
  for (const [name, hex] of Object.entries(FIXED_OVERRIDES)) {
    overrides[name] = hex;
  }

  const embed = `/* AUTO-GENERATED by scripts/build-party-colours.mjs — do not edit */\nconst PARTY_COLOURS = ${JSON.stringify(slugs, null, 2)};\n`;
  writeFileSync(EMBED_PATH, embed, 'utf8');

  console.log(`Palette: ${Object.keys(slugs).length} slugs, ${Object.keys(aliases).length} aliases, ${Object.keys(overrides).length} overrides`);
  console.log(`Wrote OG embed → ${EMBED_PATH}`);
  if (regenerate) {
    console.log(`Wrote ${ALIASES_PATH}`);
    console.log(`Wrote ${OVERRIDES_PATH}`);
  }
}

main();
