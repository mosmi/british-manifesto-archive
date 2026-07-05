/*
 * Cloudflare Pages Functions edge middleware for www.manifestos.org.uk
 *
 * The site is a client-rendered SPA whose raw HTML ships a homepage-pinned
 * canonical tag, default meta, and a 200 status for every path. Non-JS
 * crawlers (Google's first wave, Bing, social scrapers) therefore see every
 * page as a duplicate of the homepage. This middleware runs at the edge,
 * before the SPA boots, to:
 *
 *   1. Return a true HTTP 404 for unknown routes (validated against real data).
 *   2. Rewrite <title>, meta description, canonical, OG and Twitter tags
 *      per-path using the site's own data (data/seo.json).
 *   3. Inject Schema.org JSON-LD for manifestos, elections and parties.
 *
 * It fails safe: if seo.json can't be loaded, requests pass through untouched
 * and routes are treated as valid (never wrongly 404 a real page).
 */

const SITE_URL = 'https://www.manifestos.org.uk';
const SITE_NAME = 'The British Manifesto Archive';
const TITLE_SUFFIX = ` — ${SITE_NAME}`;
const DEFAULT_TITLE = `${SITE_NAME} — www.manifestos.org.uk`;
const DEFAULT_DESCRIPTION =
  'A comprehensive digital archive of general, devolved, regional, and ' +
  'European Parliament election manifestos, results, and maps in the UK.';

function truncateMetaDescription(text, maxLen = 155) {
  if (!text) return '';
  if (text.length <= maxLen) return text;
  const cut = text.slice(0, maxLen);
  const sp = cut.lastIndexOf(' ');
  return `${(sp > 80 ? cut.slice(0, sp) : cut).trimEnd()}…`;
}

function partyLedeText(description) {
  if (!description) return '';
  const m = description.match(/^[^.!?]+[.!?]/);
  if (m && m[0].length <= 180) return m[0].trim();
  return truncateMetaDescription(description, 155);
}

function chamberPartsFromCounts(counts, isAlliance = false) {
  if (!counts) return [];
  const parts = [];
  if (!isAlliance && counts.westminster) parts.push(`${counts.westminster} Westminster`);
  if (!isAlliance && counts.holyrood) parts.push(`${counts.holyrood} Holyrood`);
  if (!isAlliance && counts.senedd) parts.push(`${counts.senedd} Senedd`);
  if (!isAlliance && counts.stormont) parts.push(`${counts.stormont} Stormont`);
  if (counts.euro) parts.push(`${counts.euro} European Parliament`);
  return parts;
}

function buildPartyMetaDescription(party, chamberParts) {
  const lede = partyLedeText(party.description);
  if (!chamberParts || !chamberParts.length) {
    return truncateMetaDescription(
      party.description ||
        `Manifestos and election history for ${party.shortName || party.name}.`,
      155,
    );
  }
  return truncateMetaDescription(
    `${lede} Browse manifestos and results across ${chamberParts.join(', ')}.`,
    155,
  );
}

function nationMetaDescription(nationId, nationRec) {
  if (typeof nationRec === 'object' && nationRec && nationRec.description) {
    return truncateMetaDescription(nationRec.description, 155);
  }
  const nationName = typeof nationRec === 'string' ? nationRec : nationRec?.name;
  if (nationId === 'europe') {
    return 'Pan-European political families that contested European Parliament elections in the United Kingdom from 1979 to 2019.';
  }
  return `UK general election results, seat history, and manifestos for ${nationName}.`;
}

function nationDisplayName(nationRec) {
  if (typeof nationRec === 'string') return nationRec;
  return nationRec?.name || '';
}

function ogImagePathForRoute(path) {
  if (!path || path === '/') return '/og-image.jpg';
  const parts = path.split('/').filter(Boolean);
  if (parts[0] === 'party' && parts[1]) return `/og/party/${parts[1]}.jpg`;
  if (parts[0] === 'election' && parts[1]) return `/og/election/${parts[1]}.jpg`;
  if (parts[0] === 'manifesto' && parts[1] && parts[2]) {
    return `/og/manifesto/${parts[1]}/${parts[2]}.jpg`;
  }
  if (parts[0] === 'nation' && parts[1]) return `/og/nation/${parts[1]}.jpg`;
  if (parts[0] === 'devolved' && parts[1]) {
    if (parts[2] === 'other-parties') {
      return `/og/devolved/${parts[1]}/other-parties.jpg`;
    }
    if (parts[2] && parts[2] !== 'other-parties') {
      return `/og/devolved/${parts[1]}/${parts[2]}.jpg`;
    }
    if (['holyrood', 'senedd', 'stormont', 'euro', 'london'].includes(parts[1])) {
      return `/og/devolved/${parts[1]}.jpg`;
    }
  }
  const hubSlugs = {
    '/about': 'about',
    '/elections': 'elections',
    '/parties': 'parties',
    '/devolved': 'devolved',
    '/nations': 'nations',
    '/others': 'others',
  };
  if (hubSlugs[path]) return `/og/hub/${hubSlugs[path]}.jpg`;
  return '/og-image.jpg';
}

// Static (non-parameterised) routes the SPA renders, with bespoke metadata.
const STATIC_ROUTES = {
  '/': { title: DEFAULT_TITLE, description: DEFAULT_DESCRIPTION },
  '/about': {
    title: `About${TITLE_SUFFIX}`,
    description: 'About The British Manifesto Archive: what it is, where the ' +
      'manifesto texts come from, and how to use the collection.',
  },
  '/elections': {
    title: `UK General Elections${TITLE_SUFFIX}`,
    description: 'Browse every UK general election from 1945 to 2024 with ' +
      'results, seat maps, and the party manifestos published for each.',
  },
  '/devolved': {
    title: `Beyond Westminster${TITLE_SUFFIX}`,
    description: 'Devolved legislatures of the United Kingdom — Scottish ' +
      'Parliament, Welsh Parliament, Northern Ireland Assembly, and London ' +
      'Mayor & Assembly.',
  },
  '/parties': {
    title: `Political Parties${TITLE_SUFFIX}`,
    description: 'Browse UK political parties and their historical general ' +
      'election manifestos in The British Manifesto Archive.',
  },
  '/nations': {
    title: `The Four Nations & Europe${TITLE_SUFFIX}`,
    description: 'Browse England, Wales, Scotland, Northern Ireland, and ' +
      'European political families — Westminster results and devolved government.',
  },
  '/others': {
    title: `Other Parties${TITLE_SUFFIX}`,
    description: 'Smaller and historical UK political parties and the ' +
      'manifestos they published.',
  },
};

// Cache the parsed SEO data on the warm isolate across requests.
let seoCache = null;

async function loadSeo(context) {
  if (seoCache) return seoCache;
  const { request, env } = context;
  const seoUrl = new URL('/data/seo.json', request.url);
  try {
    // Prefer the static-assets binding (no public round-trip); fall back to a
    // same-origin fetch if it isn't available in this environment.
    const res = env && env.ASSETS
      ? await env.ASSETS.fetch(seoUrl)
      : await fetch(seoUrl, { cf: { cacheTtl: 300, cacheEverything: true } });
    if (!res.ok) return null;
    seoCache = await res.json();
    return seoCache;
  } catch {
    return null;
  }
}

// Serialise JSON-LD safely so a stray "</script>" in any value can't break out.
function jsonLdScript(obj) {
  const json = JSON.stringify(obj).replace(/</g, '\\u003c');
  return `<script type="application/ld+json">${json}</script>`;
}

function canonicalFor(path) {
  return path === '/' ? `${SITE_URL}/` : `${SITE_URL}${path}`;
}

// ---------------------------------------------------------------------------
// Reusable Schema.org graph nodes. We emit a single <script> per page holding
// an "@graph" array so the document, its publisher, breadcrumbs and item lists
// reference each other by stable @id.
// ---------------------------------------------------------------------------

const ORG_ID = `${SITE_URL}/#organization`;
const WEBSITE_ID = `${SITE_URL}/#website`;
const CATALOG_ID = `${SITE_URL}/#catalog`;

function orgNode() {
  return {
    '@type': 'Organization',
    '@id': ORG_ID,
    name: SITE_NAME,
    url: `${SITE_URL}/`,
    logo: `${SITE_URL}/og-image.jpg`,
    description: DEFAULT_DESCRIPTION,
  };
}

function websiteNode() {
  return {
    '@type': 'WebSite',
    '@id': WEBSITE_ID,
    name: SITE_NAME,
    url: `${SITE_URL}/`,
    inLanguage: 'en-GB',
    description: DEFAULT_DESCRIPTION,
    publisher: { '@id': ORG_ID },
  };
}

function catalogNode() {
  return {
    '@type': 'DataCatalog',
    '@id': CATALOG_ID,
    name: `${SITE_NAME} — Catalogue`,
    url: `${SITE_URL}/`,
    description:
      'Machine-readable catalogue of UK election manifestos, results and maps ' +
      'held in The British Manifesto Archive.',
    inLanguage: 'en-GB',
    isAccessibleForFree: true,
    publisher: { '@id': ORG_ID },
  };
}

// Site-level graph for the homepage and /about.
function siteGraph(extra) {
  return [websiteNode(), orgNode(), catalogNode(), ...(extra || [])];
}

// crumbs: [{ name, path }] (path optional for the current page).
function breadcrumb(crumbs) {
  return {
    '@type': 'BreadcrumbList',
    itemListElement: crumbs.map((c, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      name: c.name,
      ...(c.path ? { item: canonicalFor(c.path) } : {}),
    })),
  };
}

// items: [{ name, url }] -> ItemList of links shown on the page.
function itemList(name, items) {
  return {
    '@type': 'ItemList',
    name,
    numberOfItems: items.length,
    itemListElement: items.map((it, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      name: it.name,
      url: it.url,
    })),
  };
}

// Manifestos belonging to a general election, in stable id order.
function manifestosForElection(seo, electionId) {
  const out = [];
  for (const [key, rec] of Object.entries(seo.manifestos || {})) {
    if (rec.electionId !== electionId) continue;
    const party = seo.parties[rec.partyId];
    out.push({
      name: rec.label || (party ? `${party.name} manifesto` : key),
      url: `${SITE_URL}/manifesto/${key}`,
    });
  }
  return out;
}

// A devolved / regional / mayoral election page: Event + breadcrumb + the
// manifestos listed on that page (ItemList).
function devolvedElection(seo, portal, sub, portalName, path, yearLabel) {
  const portalMeta = (seo.devolvedPortals && seo.devolvedPortals[portal]) || {};
  const title = `${yearLabel} ${portalName} Election${TITLE_SUFFIX}`;
  const description =
    `Results, seat maps and party manifestos from the ${yearLabel} ${portalName}` +
    `${portalMeta.subtitle ? ` (${portalMeta.subtitle})` : ''} election.`;
  const canonical = canonicalFor(path);
  const event = {
    '@type': 'Event',
    '@id': `${canonical}#event`,
    name: `${yearLabel} ${portalName} election`,
    description,
    url: canonical,
    eventAttendanceMode: 'https://schema.org/OfflineEventAttendanceMode',
    location: { '@type': 'Country', name: 'United Kingdom' },
    organizer: { '@id': ORG_ID },
  };
  const mans = (seo.devolvedManifestos && seo.devolvedManifestos[`${portal}/${sub}`]) || [];
  const items = mans
    .filter((m) => m && m.pdf)
    .map((m) => {
      const party = m.party && seo.parties[m.party];
      return {
        name: m.title || (party ? `${party.name} manifesto` : 'Manifesto'),
        url: `${SITE_URL}${m.pdf}`,
      };
    });
  const graph = [
    event,
    orgNode(),
    breadcrumb([
      { name: 'Home', path: '/' },
      { name: 'Devolved Elections', path: '/devolved' },
      { name: portalName, path: `/devolved/${portal}` },
      { name: yearLabel },
    ]),
    ...(items.length
      ? [itemList(`${yearLabel} ${portalName} manifestos`, items)]
      : []),
  ];
  return { valid: true, meta: { title, description }, graph, image: `/og/devolved/${portal}/${sub}.jpg` };
}

// Manifestos published by a party, across general elections.
function manifestosForParty(seo, partyId) {
  const out = [];
  for (const [key, rec] of Object.entries(seo.manifestos || {})) {
    if (rec.partyId !== partyId) continue;
    out.push({ name: rec.label || key, url: `${SITE_URL}/manifesto/${key}` });
  }
  return out;
}

/*
 * Classify a request path. Returns:
 *   { valid: true,  meta: {title, description}, graph? }   for known pages
 *   { valid: false }                                       for unknown pages
 *   { skip: true }                                         when data is missing
 */
function classify(path, seo) {
  if (Object.prototype.hasOwnProperty.call(STATIC_ROUTES, path)) {
    const meta = STATIC_ROUTES[path];
    let graph = null;

    if (path === '/') {
      graph = siteGraph();
    } else if (path === '/about') {
      graph = siteGraph([breadcrumb([
        { name: 'Home', path: '/' },
        { name: 'About' },
      ])]);
    } else if (path === '/elections') {
      const items = Object.entries(seo.elections || {})
        .sort((a, b) => b[1].year - a[1].year)
        .map(([id, e]) => ({
          name: `${e.displayYear} UK general election`,
          url: `${SITE_URL}/election/${id}`,
        }));
      graph = [
        breadcrumb([{ name: 'Home', path: '/' }, { name: 'UK General Elections' }]),
        itemList('UK general elections', items),
      ];
    } else if (path === '/parties') {
      const items = Object.entries(seo.parties || {})
        .map(([id, p]) => ({ name: p.name, url: `${SITE_URL}/party/${id}` }));
      graph = [
        breadcrumb([{ name: 'Home', path: '/' }, { name: 'Political Parties' }]),
        itemList('UK political parties', items),
      ];
    } else if (path === '/devolved') {
      const items = Object.entries(seo.devolvedPortals || seo.devolved || {})
        .map(([id, p]) => ({
          name: (p && p.label) || p,
          url: `${SITE_URL}/devolved/${id}`,
        }));
      graph = [
        breadcrumb([{ name: 'Home', path: '/' }, { name: 'Devolved Elections' }]),
        ...(items.length ? [itemList('Devolved & regional legislatures', items)] : []),
      ];
    } else {
      graph = [breadcrumb([{ name: 'Home', path: '/' }, { name: meta.title.replace(TITLE_SUFFIX, '') }])];
    }

    return { valid: true, meta, graph, image: ogImagePathForRoute(path) };
  }

  const parts = path.split('/').filter(Boolean);

  // /manifesto/:electionId/:partyId
  if (parts[0] === 'manifesto' && parts.length === 3) {
    const key = `${parts[1]}/${parts[2]}`;
    const rec = seo.manifestos[key];
    if (!rec) return { valid: false };
    const election = seo.elections[parts[1]];
    const party = seo.parties[parts[2]];
    const label = rec.label || `${parts[2]} ${parts[1]}`;
    const year = election ? election.displayYear : parts[1];
    const description =
      `Read and search the full text of the ${label} from the ${year} ` +
      `UK general election.`;
    const canonical = canonicalFor(path);
    const assetBase = `${SITE_URL}/manifestos/${parts[1]}/${parts[2]}`;
    const encoding = [
      {
        '@type': 'WebPage',
        encodingFormat: 'text/html',
        contentUrl: canonical,
      },
    ];
    if (rec.hasPdf) {
      encoding.push({
        '@type': 'MediaObject',
        encodingFormat: 'application/pdf',
        contentUrl: `${assetBase}/manifesto.pdf`,
        name: `${label} (PDF)`,
      });
    }
    if (rec.hasMarkdown) {
      encoding.push({
        '@type': 'MediaObject',
        encodingFormat: 'text/markdown',
        contentUrl: `${assetBase}/manifesto.md`,
        name: `${label} (Markdown)`,
      });
    }
    const partyNode = party
      ? {
          '@type': 'Organization',
          '@id': `${SITE_URL}/party/${parts[2]}#organization`,
          name: party.name,
          ...(party.shortName ? { alternateName: party.shortName } : {}),
          url: `${SITE_URL}/party/${parts[2]}`,
        }
      : null;
    const doc = {
      '@type': 'DigitalDocument',
      '@id': `${canonical}#document`,
      name: label,
      description,
      url: canonical,
      inLanguage: 'en-GB',
      isAccessibleForFree: true,
      ...(rec.hasCover ? { image: `${assetBase}/cover.jpg` } : {}),
      ...(rec.keywords && rec.keywords.length ? { keywords: rec.keywords } : {}),
      ...(election && election.isoDate ? { datePublished: election.isoDate } : {}),
      ...(partyNode ? { author: partyNode, copyrightHolder: partyNode } : {}),
      encoding,
      provider: { '@id': ORG_ID },
      publisher: { '@id': ORG_ID },
      ...(election
        ? {
            about: {
              '@type': 'Event',
              '@id': `${SITE_URL}/election/${parts[1]}#event`,
              name: `${year} UK General Election`,
              url: `${SITE_URL}/election/${parts[1]}`,
            },
          }
        : {}),
      isPartOf: { '@id': CATALOG_ID },
    };
    const graph = [
      doc,
      orgNode(),
      breadcrumb([
        { name: 'Home', path: '/' },
        { name: 'UK General Elections', path: '/elections' },
        { name: `${year}`, path: `/election/${parts[1]}` },
        { name: label },
      ]),
    ];
    return {
      valid: true,
      meta: { title: `${label}${TITLE_SUFFIX}`, description },
      graph,
      image: `/og/manifesto/${parts[1]}/${parts[2]}.jpg`,
    };
  }

  // /election/:id
  if (parts[0] === 'election' && parts.length === 2) {
    const election = seo.elections[parts[1]];
    if (!election) return { valid: false };
    const year = election.displayYear;
    const title = `${year} UK General Election Results & Manifestos${TITLE_SUFFIX}`;
    const description =
      `Results, seat maps, and party manifestos from the ${year} UK general ` +
      `election${election.date ? ` held on ${election.date}` : ''}.`;
    const event = {
      '@type': 'Event',
      '@id': `${canonicalFor(path)}#event`,
      name: `${year} UK General Election`,
      description,
      url: canonicalFor(path),
      eventAttendanceMode: 'https://schema.org/OfflineEventAttendanceMode',
      ...(election.isoDate ? { startDate: election.isoDate } : {}),
      location: { '@type': 'Country', name: 'United Kingdom' },
      organizer: { '@id': ORG_ID },
    };
    const manifestos = manifestosForElection(seo, parts[1]);
    const graph = [
      event,
      orgNode(),
      breadcrumb([
        { name: 'Home', path: '/' },
        { name: 'UK General Elections', path: '/elections' },
        { name: `${year}` },
      ]),
      ...(manifestos.length
        ? [itemList(`${year} UK general election manifestos`, manifestos)]
        : []),
    ];
    return {
      valid: true,
      meta: { title, description },
      graph,
      image: `/og/election/${parts[1]}.jpg`,
    };
  }

  // /party/:id
  if (parts[0] === 'party' && parts.length === 2) {
    const party = seo.parties[parts[1]];
    if (!party) return { valid: false };
    const chamberParts = chamberPartsFromCounts(party.chamberCounts);
    const title = `${party.shortName || party.name}${TITLE_SUFFIX}`;
    const description = buildPartyMetaDescription(party, chamberParts);
    const org = {
      '@type': 'Organization',
      '@id': `${canonicalFor(path)}#organization`,
      name: party.name,
      ...(party.shortName ? { alternateName: party.shortName } : {}),
      url: canonicalFor(path),
      ...(party.description ? { description: party.description } : {}),
      ...(party.sameAs && party.sameAs.length ? { sameAs: party.sameAs } : {}),
    };
    const manifestos = manifestosForParty(seo, parts[1]);
    const graph = [
      org,
      breadcrumb([
        { name: 'Home', path: '/' },
        { name: 'Political Parties', path: '/parties' },
        { name: party.name },
      ]),
      ...(manifestos.length
        ? [itemList(`${party.name} manifestos`, manifestos)]
        : []),
    ];
    return {
      valid: true,
      meta: { title, description },
      graph,
      image: `/og/party/${parts[1]}.jpg`,
    };
  }

  // /nation/:id
  if (parts[0] === 'nation' && parts.length === 2) {
    const nationRec = seo.nations && seo.nations[parts[1]];
    // Back-compat: if seo.json predates the nations list, accept slug-shaped
    // IDs (canonical fix only) rather than risk 404ing a real page.
    if (!seo.nations) return { valid: /^[a-z][a-z0-9-]*$/.test(parts[1]), meta: null };
    if (!nationRec) return { valid: false };
    const name = nationDisplayName(nationRec);
    const description = nationMetaDescription(parts[1], nationRec);
    return {
      valid: true,
      meta: {
        title: `${name} — UK General Election Results${TITLE_SUFFIX}`,
        description,
      },
      graph: [breadcrumb([
        { name: 'Home', path: '/' },
        { name: 'Nations of the UK', path: '/nations' },
        { name },
      ])],
      image: `/og/nation/${parts[1]}.jpg`,
    };
  }

  // /devolved/:portal/:sub (election pages, other-parties, etc.)
  if (parts[0] === 'devolved' && parts.length >= 3) {
    const portal = parts[1];
    const sub = parts[2];
    if (portal === 'holyrood' && sub === 'other-parties') {
      return {
        valid: true,
        meta: {
          title: `Other Scottish Parties${TITLE_SUFFIX}`,
          description: 'Smaller parties that have contested Scottish Parliament elections at Holyrood.',
        },
        image: '/og/devolved/holyrood/other-parties.jpg',
      };
    }
    if (portal === 'senedd' && sub === 'other-parties') {
      return {
        valid: true,
        meta: {
          title: `Other Welsh Parties${TITLE_SUFFIX}`,
          description: 'Smaller parties that have contested Senedd Cymru elections.',
        },
        image: '/og/devolved/senedd/other-parties.jpg',
      };
    }
    if (portal === 'stormont' && sub === 'other-parties') {
      return {
        valid: true,
        meta: {
          title: `Other Northern Irish Parties${TITLE_SUFFIX}`,
          description: 'Smaller parties that have contested Northern Ireland Assembly elections at Stormont.',
        },
        image: '/og/devolved/stormont/other-parties.jpg',
      };
    }
    if (portal === 'holyrood' || portal === 'senedd' || portal === 'stormont') {
      const portalName = seo.devolved && seo.devolved[portal];
      if (!portalName) return { valid: /^[a-z][a-z0-9-]*$/.test(sub), meta: null };
      if (!/^\d{4}$/.test(sub)) return { valid: false };
      return devolvedElection(seo, portal, sub, portalName, path, sub);
    }
    if (portal === 'london') {
      const portalName = seo.devolved && seo.devolved[portal];
      if (!portalName) return { valid: /^[a-z][a-z0-9-]*$/.test(sub), meta: null };
      if (!/^(gla|glc|lcc)-\d{4}$/.test(sub)) return { valid: false };
      const yearMatch = sub.match(/(\d{4})/);
      return devolvedElection(
        seo, portal, sub, portalName, path, yearMatch ? yearMatch[1] : sub);
    }
    if (portal === 'euro') {
      if (sub === 'other-parties') {
        return {
          valid: true,
          meta: {
            title: `Other EP Parties${TITLE_SUFFIX}`,
            description:
              'Smaller, regional, and specialist parties that have contested ' +
              'European Parliament elections in the UK.',
          },
          graph: [breadcrumb([
            { name: 'Home', path: '/' },
            { name: 'Devolved Elections', path: '/devolved' },
            { name: 'European Parliament', path: '/devolved/euro' },
            { name: 'Other EP parties' },
          ])],
          image: '/og/devolved/euro/other-parties.jpg',
        };
      }
      const portalName = seo.devolved && seo.devolved[portal];
      if (!portalName) return { valid: /^[a-z][a-z0-9-]*$/.test(sub), meta: null };
      if (!/^\d{4}$/.test(sub)) return { valid: false };
      return devolvedElection(seo, portal, sub, portalName, path, sub);
    }
    return { valid: false };
  }

  // /devolved/:id
  if (parts[0] === 'devolved' && parts.length === 2) {
    const name = seo.devolved && seo.devolved[parts[1]];
    if (!seo.devolved) return { valid: /^[a-z][a-z0-9-]*$/.test(parts[1]), meta: null };
    if (!name) return { valid: false };
    const years = Object.keys(seo.devolvedManifestos || {})
      .filter((k) => k.startsWith(`${parts[1]}/`))
      .map((k) => k.slice(parts[1].length + 1))
      .sort()
      .map((sub) => ({
        name: `${(sub.match(/(\d{4})/) || [sub])[0]} ${name} election`,
        url: `${SITE_URL}/devolved/${parts[1]}/${sub}`,
      }));
    const graph = [
      breadcrumb([
        { name: 'Home', path: '/' },
        { name: 'Devolved Elections', path: '/devolved' },
        { name },
      ]),
      ...(years.length ? [itemList(`${name} elections`, years)] : []),
    ];
    return {
      valid: true,
      meta: {
        title: `${name} Elections${TITLE_SUFFIX}`,
        description: `Election results and party manifestos for the ${name}.`,
      },
      graph,
      image: `/og/devolved/${parts[1]}.jpg`,
    };
  }

  return { valid: false };
}

function buildRewriter({ meta, graph, canonical, image, noindex }) {
  const rewriter = new HTMLRewriter();

  if (canonical) {
    rewriter.on('link[id="canonical-link"]', {
      element(el) { el.setAttribute('href', canonical); },
    });
    rewriter.on('link[id="hreflang-link"]', {
      element(el) { el.setAttribute('href', canonical); },
    });
    rewriter.on('meta[id="og-url"]', {
      element(el) { el.setAttribute('content', canonical); },
    });
  }

  if (image) {
    const absolute = `${SITE_URL}${image}`;
    rewriter.on('meta[id="og-image"]', {
      element(el) { el.setAttribute('content', absolute); },
    });
    rewriter.on('meta[id="twitter-image"]', {
      element(el) { el.setAttribute('content', absolute); },
    });
    rewriter.on('meta[id="og-image-width"]', {
      element(el) { el.setAttribute('content', '1200'); },
    });
    rewriter.on('meta[id="og-image-height"]', {
      element(el) { el.setAttribute('content', '630'); },
    });
    if (meta && meta.title) {
      rewriter.on('meta[id="og-image-alt"]', {
        element(el) { el.setAttribute('content', meta.title); },
      });
    }
  }

  if (meta) {
    rewriter.on('title', {
      element(el) { el.setInnerContent(meta.title); },
    });
    for (const id of ['meta-description', 'og-description', 'twitter-description']) {
      rewriter.on(`meta[id="${id}"]`, {
        element(el) { el.setAttribute('content', meta.description); },
      });
    }
    for (const id of ['og-title', 'twitter-title']) {
      rewriter.on(`meta[id="${id}"]`, {
        element(el) { el.setAttribute('content', meta.title); },
      });
    }
  }

  rewriter.on('head', {
    element(el) {
      if (noindex) {
        el.append('<meta name="robots" content="noindex">', { html: true });
      }
      if (graph && graph.length) {
        el.append(jsonLdScript({
          '@context': 'https://schema.org',
          '@graph': graph,
        }), { html: true });
      }
    },
  });

  return rewriter;
}

export async function onRequest(context) {
  const { request, next } = context;

  // Only transform document navigations.
  if (request.method !== 'GET' && request.method !== 'HEAD') {
    return next();
  }

  const url = new URL(request.url);
  const path = url.pathname;

  // Bypass assets and anything with a file extension.
  if (
    path.startsWith('/js/') ||
    path.startsWith('/data/') ||
    path.startsWith('/manifestos/') ||
    path.startsWith('/previews/') ||
    path.includes('.')
  ) {
    return next();
  }

  const seo = await loadSeo(context);

  // Fail safe: without data we can still fix the canonical, but never 404.
  const result = seo ? classify(path, seo) : { valid: true, meta: null };

  const response = await next();
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('text/html')) {
    return response;
  }

  // Unknown route → true 404 with a noindex SPA shell.
  if (!result.valid) {
    const rewriter = buildRewriter({
      meta: { title: `Page Not Found${TITLE_SUFFIX}`, description: DEFAULT_DESCRIPTION },
      canonical: null,
      noindex: true,
    });
    const transformed = rewriter.transform(response);
    return new Response(transformed.body, {
      status: 404,
      statusText: 'Not Found',
      headers: transformed.headers,
    });
  }

  const rewriter = buildRewriter({
    meta: result.meta,
    graph: result.graph,
    canonical: canonicalFor(path),
    image: result.image,
    noindex: false,
  });
  return rewriter.transform(response);
}
