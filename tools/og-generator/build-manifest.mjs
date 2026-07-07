#!/usr/bin/env node
/**
 * build-manifest.mjs — derive pages.json for OG image generation from site data.
 *
 * Reads data/seo.json (run scripts/build-seo-data.py first) plus election results
 * and manifesto folders. Emits one { path, spec } entry per OG card.
 *
 * Usage:
 *   node tools/og-generator/build-manifest.mjs
 *   node tools/og-generator/build-manifest.mjs --only party,election
 *   node tools/og-generator/build-manifest.mjs --sample
 *   node tools/og-generator/build-manifest.mjs --out tools/og-generator/pages.json
 */

import { readFileSync, writeFileSync, readdirSync, existsSync, statSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..', '..');
const SEO_PATH = join(ROOT, 'data', 'seo.json');
const ELECTIONS_DIR = join(ROOT, 'data', 'elections');
const DEVOLVED_DIR = join(ROOT, 'data', 'devolved');
const MANIFESTOS_DIR = join(ROOT, 'manifestos');

const EURO_ALLIANCE_PARTIES = new Set([
  'sand', 'epp', 'renew', 'greensefa', 'guengl', 'ecr', 'uen', 'inddem',
  'identity', 'diem25', 'volt', 'ecpm',
]);

const ARENA_ORDER = ['westminster', 'holyrood', 'senedd', 'stormont', 'london', 'euro'];
const ARENA_LABELS = {
  westminster: 'Westminster',
  holyrood: 'Holyrood',
  senedd: 'Senedd',
  stormont: 'Assembly',
  london: 'London',
  euro: 'European',
};

const PORTAL_KICKER = {
  holyrood: 'SCOTTISH PARLIAMENT',
  senedd: 'WELSH PARLIAMENT',
  stormont: 'NORTHERN IRELAND ASSEMBLY',
  london: 'MAYOR & ASSEMBLY',
  euro: 'EUROPEAN PARLIAMENT',
};

const BODY_TITLE = {
  holyrood: 'Holyrood',
  senedd: 'Senedd',
  stormont: 'Stormont',
  london: 'London',
  euro: 'Brussels & Strasbourg',
};

const OTHER_PARTIES_SUB = {
  holyrood: 'Smaller parties & independents at Holyrood',
  senedd: 'Smaller parties & independents at the Senedd',
  stormont: 'Smaller parties & independents at Stormont',
  euro: 'Smaller & specialist parties at European elections',
};

const NATION_SUB = {
  scotland: 'Westminster results & devolved government',
  wales: 'Westminster results & devolved government',
  england: 'Westminster election results',
  'northern-ireland': 'Westminster results & devolved government',
  europe: 'European Parliament results for the UK',
};

const HUB_SPECS = [
  { slug: 'about', title: 'About the Archive', subtitle: 'Why it exists, where documents come from & how to help' },
  { slug: 'elections', title: 'General Elections', subtitle: null },
  { slug: 'devolved', title: 'Beyond Westminster', subtitle: 'Holyrood, the Senedd, Stormont, London & Europe' },
  { slug: 'nations', title: 'The Four Nations & Europe', subtitle: 'Results & manifestos by nation' },
  { slug: 'others', title: 'Other Parties', subtitle: 'Smaller parties & independents' },
  { slug: 'parties', title: 'The Parties', subtitle: 'Every party, every manifesto — 1945 to today' },
];

function listSubdirs(dir) {
  if (!existsSync(dir)) return [];
  return readdirSync(dir).filter((name) => {
    try {
      return statSync(join(dir, name)).isDirectory();
    } catch {
      return false;
    }
  });
}

function parseArgs(argv) {
  const opts = {
    only: new Set(['home', 'hub', 'election', 'party', 'manifesto', 'nation', 'devolved']),
    sample: false,
    out: join(__dirname, 'pages.json'),
  };
  for (let i = 2; i < argv.length; i++) {
    if (argv[i] === '--sample') opts.sample = true;
    else if (argv[i] === '--only' && argv[i + 1]) {
      opts.only = new Set(argv[++i].split(',').map((s) => s.trim()));
    } else if (argv[i] === '--out' && argv[i + 1]) {
      opts.out = argv[++i];
    }
  }
  return opts;
}

function readJson(path) {
  try {
    return JSON.parse(readFileSync(path, 'utf8'));
  } catch {
    return null;
  }
}

function push(pages, path, spec) {
  pages.push({ path, spec });
}

function buildHoldings(seo) {
  const holdings = {};
  for (const m of Object.values(seo.manifestos || {})) {
    const pid = m.partyId;
    if (!pid) continue;
    holdings[pid] ??= {};
    holdings[pid].westminster = (holdings[pid].westminster || 0) + 1;
  }
  for (const [key, items] of Object.entries(seo.devolvedManifestos || {})) {
    const portal = key.split('/')[0];
    if (!['holyrood', 'senedd', 'stormont', 'euro', 'london'].includes(portal)) continue;
    for (const item of items) {
      const pid = item.party;
      if (!pid) continue;
      holdings[pid] ??= {};
      holdings[pid][portal] = (holdings[pid][portal] || 0) + 1;
    }
  }
  return holdings;
}

function partySubtitle(pid, party, holdings) {
  if (pid === 'speaker') return 'Seeking re-election, by convention unopposed';
  if (pid === 'independent') return 'Independent candidates & their platforms';

  if (EURO_ALLIANCE_PARTIES.has(pid)) {
    const n = holdings[pid]?.euro || 0;
    return n > 0
      ? `Manifestos across *${n} European* election${n === 1 ? '' : 's'}`
      : 'Manifestos across European Parliament elections';
  }

  const h = holdings[pid] || {};
  const clauses = ARENA_ORDER
    .filter((a) => h[a] > 0)
    .map((a) => ({ arena: a, n: h[a], label: ARENA_LABELS[a] }));

  if (!clauses.length) return 'Party history & election results';

  if (clauses.length >= 3) {
    const total = clauses.reduce((s, c) => s + c.n, 0);
    return `Manifestos across *${total} elections* in ${clauses.length} chambers`;
  }

  const parts = clauses.map((c) => `*${c.n} ${c.label}*`);
  const electionWord = clauses.reduce((s, c) => s + c.n, 0) === 1 ? 'election' : 'elections';
  if (parts.length === 1) return `Manifestos across ${parts[0]} ${electionWord}`;
  return `Manifestos across ${parts[0]} & ${parts[1]} ${electionWord}`;
}

function seatStrip(results, parties, maxBars = 4) {
  if (!Array.isArray(results)) return null;
  const sorted = results
    .filter((r) => (r.seats || 0) > 0)
    .sort((a, b) => b.seats - a.seats)
    .slice(0, maxBars);
  if (!sorted.length) return null;
  const maxSeats = sorted[0].seats;
  return sorted.map((r) => {
    const color = (parties[r.party]?.color || '#6b7280').toLowerCase();
    const w = Math.max(8, Math.round((r.seats / maxSeats) * 26));
    return [color, w];
  });
}

function loadWestminsterResults(eid) {
  const data = readJson(join(ELECTIONS_DIR, `${eid}.json`));
  return data?.results || null;
}

function loadDevolvedResults(portal, sub) {
  const data = readJson(join(DEVOLVED_DIR, portal, `${sub}.json`));
  if (!data) return null;
  return data.parliament?.results || data.results || null;
}

function westminsterElectionTitle(eid, election) {
  if (eid === 'feb1974') return 'February 1974 Election';
  if (eid === 'oct1974') return 'October 1974 Election';
  return `${election.displayYear || eid} Election`;
}

function westminsterGhost(eid, election) {
  if (eid === 'feb1974' || eid === 'oct1974') return '74';
  const y = election.year || parseInt(String(eid).replace(/\D/g, ''), 10);
  return String(y).slice(-2);
}

function londonKicker(sub) {
  if (sub.startsWith('lcc-')) return 'LONDON COUNTY COUNCIL';
  if (sub.startsWith('glc-')) return 'GREATER LONDON COUNCIL';
  return 'MAYOR & ASSEMBLY';
}

function londonHasMap(sub) {
  return sub.startsWith('gla-');
}

function portalFirstYear(portal) {
  const indexPath = join(DEVOLVED_DIR, portal, 'index.json');
  const index = readJson(indexPath);
  if (!Array.isArray(index) || !index.length) return null;
  const years = index.map((e) => e.year || parseInt(String(e.id).replace(/\D/g, ''), 10)).filter(Boolean);
  return years.length ? Math.min(...years) : null;
}

function manifestoDocTitle(eid, pid) {
  const mdPath = join(MANIFESTOS_DIR, eid, pid, 'manifesto.md');
  if (!existsSync(mdPath)) return null;
  const text = readFileSync(mdPath, 'utf8');
  const body = text.replace(/^---[\s\S]*?---\s*/, '');
  const bold = body.match(/^\*\*(.+?)\*\*\s*$/m);
  if (bold && bold[1] !== body.match(/^#\s+(.+)/m)?.[1]) return bold[1];
  return null;
}

function manifestoSubtitle(eid, pid, partyName) {
  const docTitle = manifestoDocTitle(eid, pid);
  if (docTitle) return `Read the full manifesto — *${docTitle}*`;
  return 'Read the full manifesto';
}

function manifestoYearLabel(eid, election) {
  if (eid === 'feb1974') return 'FEB 1974';
  if (eid === 'oct1974') return 'OCT 1974';
  return election?.displayYear || eid;
}

function manifestoKicker(eid) {
  if (eid === 'feb1974') return 'GENERAL ELECTION · FEBRUARY 1974';
  if (eid === 'oct1974') return 'GENERAL ELECTION · OCTOBER 1974';
  return undefined;
}

function electionsHubSubtitle(seo) {
  const ids = Object.keys(seo.elections || {});
  const numeric = ids
    .map((id) => parseInt(String(id).replace(/\D/g, ''), 10))
    .filter((y) => y >= 1900);
  const latest = numeric.length ? Math.max(...numeric) : 2024;
  const count = ids.length;
  return `*${count} elections*, 1945 to ${latest}`;
}

function bodyHubSubtitle(portal) {
  const first = portalFirstYear(portal);
  if (portal === 'euro') return 'UK elections, results & manifestos *1979–2019*';
  if (portal === 'stormont') return first ? `Elections, results & manifestos since *${first}*` : 'Elections, results & manifestos';
  return first ? `Elections, results & manifestos since *${first}*` : 'Elections, results & manifestos';
}

function main() {
  const opts = parseArgs(process.argv);
  const seo = readJson(SEO_PATH);
  if (!seo) {
    console.error(`ERROR: ${SEO_PATH} not found — run python3 scripts/build-seo-data.py first`);
    process.exit(1);
  }

  const parties = seo.parties || {};
  const elections = seo.elections || {};
  const nations = seo.nations || {};
  const portals = seo.devolvedPortals || {};
  const holdings = buildHoldings(seo);
  const holdingsPath = join(ROOT, 'data', 'party-holdings.json');
  writeFileSync(holdingsPath, JSON.stringify(holdings, null, 2) + '\n', 'utf8');
  console.log(`Wrote ${Object.keys(holdings).length} party holdings to ${holdingsPath}`);

  const pages = [];

  if (opts.only.has('home')) {
    push(pages, 'og-image.jpg', { type: 'home' });
  }

  if (opts.only.has('hub')) {
    let hubs = HUB_SPECS.map((h) => ({
      ...h,
      subtitle: h.slug === 'elections' ? electionsHubSubtitle(seo) : h.subtitle,
    }));
    if (opts.sample) hubs = hubs.slice(0, 3);
    for (const h of hubs) {
      const path = `og/hub/${h.slug}.jpg`;
      if (h.slug === 'about') {
        // Dedicated about card — book-spines motif, kicker "ABOUT" (not generic index)
        push(pages, path, {
          type: 'about',
          title: h.title,
          subtitle: h.subtitle,
        });
      } else {
        push(pages, path, {
          type: 'index',
          slug: h.slug,
          title: h.title,
          subtitle: h.subtitle,
        });
      }
    }
  }

  if (opts.only.has('election')) {
    let eItems = Object.entries(elections);
    if (opts.sample) eItems = eItems.slice(0, 3);
    for (const [eid, e] of eItems) {
      const strip = seatStrip(loadWestminsterResults(eid), parties);
      push(pages, `og/election/${eid}.jpg`, {
        type: 'election',
        year: e.year || parseInt(String(eid).replace(/\D/g, ''), 10),
        ghost: westminsterGhost(eid, e),
        kicker: 'GENERAL ELECTION',
        title: westminsterElectionTitle(eid, e),
        subtitle: 'Results, maps & party manifestos',
        ...(strip ? { strip } : {}),
      });
    }
  }

  if (opts.only.has('party')) {
    let pItems = Object.entries(parties);
    if (opts.sample) pItems = pItems.slice(0, 3);
    for (const [pid, p] of pItems) {
      const spec = {
        type: 'party',
        slug: pid,
        title: p.name,
        subtitle: partySubtitle(pid, p, holdings),
      };
      if (EURO_ALLIANCE_PARTIES.has(pid)) spec.kicker = 'EUROPEAN GROUP';
      push(pages, `og/party/${pid}.jpg`, spec);
    }
  }

  if (opts.only.has('manifesto')) {
    let mItems = Object.entries(seo.manifestos || {});
    if (opts.sample) mItems = mItems.slice(0, 5);
    for (const [, m] of mItems) {
      const { electionId: eid, partyId: pid } = m;
      const party = parties[pid] || {};
      const election = elections[eid] || {};
      push(pages, `og/manifesto/${eid}/${pid}.jpg`, {
        type: 'manifesto',
        slug: pid,
        year: election.year || parseInt(String(eid).replace(/\D/g, ''), 10),
        yearLabel: manifestoYearLabel(eid, election),
        title: party.name || m.label || pid,
        subtitle: manifestoSubtitle(eid, pid, party.name),
        ...(manifestoKicker(eid) ? { kicker: manifestoKicker(eid) } : {}),
      });
    }
  }

  if (opts.only.has('nation')) {
    let nItems = Object.entries(nations);
    if (opts.sample) nItems = nItems.slice(0, 2);
    for (const [nid, rec] of nItems) {
      const name = typeof rec === 'object' ? rec.name : rec;
      push(pages, `og/nation/${nid}.jpg`, {
        type: 'nation',
        slug: nid,
        title: name || nid,
        subtitle: NATION_SUB[nid] || 'Westminster results & devolved government',
      });
    }
  }

  if (opts.only.has('devolved')) {
    let portalItems = Object.entries(portals);
    if (opts.sample) portalItems = portalItems.slice(0, 2);

    for (const [pid, portal] of portalItems) {
      const label = typeof portal === 'object' ? portal.label : portal;
      push(pages, `og/devolved/${pid}.jpg`, {
        type: 'body',
        slug: pid,
        title: BODY_TITLE[pid] || label || pid,
        subtitle: bodyHubSubtitle(pid),
      });
    }

    const otherPortals = opts.sample
      ? ['holyrood']
      : ['holyrood', 'senedd', 'stormont', 'euro'];
    for (const portal of otherPortals) {
      push(pages, `og/devolved/${portal}/other-parties.jpg`, {
        type: 'other-parties',
        body: portal,
        kicker: PORTAL_KICKER[portal],
        title: portal === 'euro' ? 'Other EP Parties' : 'Other Parties',
        subtitle: OTHER_PARTIES_SUB[portal],
      });
    }

    let electionKeys = Object.keys(seo.devolvedManifestos || {}).sort();
    if (opts.sample) electionKeys = electionKeys.slice(0, 4);
    for (const key of electionKeys) {
      const [portal, sub] = key.split('/');
      const yearMatch = sub.match(/(\d{4})/);
      const year = yearMatch ? parseInt(yearMatch[1], 10) : parseInt(sub, 10);
      const results = loadDevolvedResults(portal, sub);
      const strip = seatStrip(results, parties);
      const hasMap = portal === 'london' ? londonHasMap(sub) : portal !== 'london';
      const subtitle = hasMap
        ? 'Results, maps & party manifestos'
        : 'Results & party manifestos';
      const spec = {
        type: 'election',
        body: portal,
        year,
        ghost: String(year).slice(-2),
        kicker: portal === 'london' ? londonKicker(sub) : PORTAL_KICKER[portal],
        title: `${year} Election`,
        subtitle,
        ...(strip ? { strip } : {}),
      };
      push(pages, `og/devolved/${portal}/${sub}.jpg`, spec);
    }

    // Devolved election pages that exist as routes but may lack manifesto holdings.
    if (!opts.sample) {
      for (const portal of listSubdirs(DEVOLVED_DIR)) {
        const portalDir = join(DEVOLVED_DIR, portal);
        for (const file of readdirSync(portalDir)) {
          if (!file.endsWith('.json') || file === 'index.json') continue;
          const sub = file.replace(/\.json$/, '');
          const rel = `${portal}/${sub}`;
          if (pages.some((p) => p.path === `og/devolved/${rel}.jpg`)) continue;
          const yearMatch = sub.match(/(\d{4})/);
          if (!yearMatch) continue;
          const year = parseInt(yearMatch[1], 10);
          const results = loadDevolvedResults(portal, sub);
          const strip = seatStrip(results, parties);
          const hasMap = portal === 'london' ? londonHasMap(sub) : true;
          push(pages, `og/devolved/${portal}/${sub}.jpg`, {
            type: 'election',
            body: portal,
            year,
            ghost: String(year).slice(-2),
            kicker: portal === 'london' ? londonKicker(sub) : PORTAL_KICKER[portal],
            title: `${year} Election`,
            subtitle: hasMap ? 'Results, maps & party manifestos' : 'Results & party manifestos',
            ...(strip ? { strip } : {}),
          });
        }
      }
    }
  }

  writeFileSync(opts.out, JSON.stringify(pages, null, 2) + '\n', 'utf8');
  console.log(`Wrote ${pages.length} OG specs to ${opts.out}`);
}

main();
