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
  'A comprehensive digital archive of UK general election manifestos from ' +
  '1945 to 2024. Browse party manifestos, election results, and ' +
  'constituency maps.';

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
    title: `Devolved Parliament & Assembly Elections${TITLE_SUFFIX}`,
    description: 'Manifestos and results from elections to the Scottish ' +
      'Parliament, Senedd Cymru, and Northern Ireland Assembly.',
  },
  '/parties': {
    title: `Political Parties${TITLE_SUFFIX}`,
    description: 'Browse UK political parties and their historical general ' +
      'election manifestos in The British Manifesto Archive.',
  },
  '/nations': {
    title: `Nations of the UK${TITLE_SUFFIX}`,
    description: 'Explore UK general election manifestos and results by ' +
      'nation: England, Scotland, Wales, and Northern Ireland.',
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

/*
 * Classify a request path. Returns:
 *   { valid: true,  meta: {title, description}, jsonLd? }  for known pages
 *   { valid: false }                                       for unknown pages
 *   { skip: true }                                         when data is missing
 */
function classify(path, seo) {
  if (Object.prototype.hasOwnProperty.call(STATIC_ROUTES, path)) {
    return { valid: true, meta: STATIC_ROUTES[path] };
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
    const jsonLd = {
      '@context': 'https://schema.org',
      '@type': 'DigitalDocument',
      name: label,
      description,
      url: canonicalFor(path),
      inLanguage: 'en-GB',
      ...(party ? { author: { '@type': 'Organization', name: party.name } } : {}),
      publisher: { '@type': 'Organization', name: SITE_NAME, url: SITE_URL },
      isPartOf: {
        '@type': 'CollectionPage',
        name: SITE_NAME,
        url: SITE_URL,
      },
    };
    return {
      valid: true,
      meta: { title: `${label}${TITLE_SUFFIX}`, description },
      jsonLd,
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
    const jsonLd = {
      '@context': 'https://schema.org',
      '@type': 'Event',
      name: `${year} UK General Election`,
      description,
      url: canonicalFor(path),
      eventAttendanceMode: 'https://schema.org/OfflineEventAttendanceMode',
      ...(election.isoDate ? { startDate: election.isoDate } : {}),
      location: { '@type': 'Country', name: 'United Kingdom' },
    };
    return {
      valid: true,
      meta: { title, description },
      jsonLd,
      image: `/og/election/${parts[1]}.jpg`,
    };
  }

  // /party/:id
  if (parts[0] === 'party' && parts.length === 2) {
    const party = seo.parties[parts[1]];
    if (!party) return { valid: false };
    const title = `${party.name} — Manifesto Archive${TITLE_SUFFIX}`;
    const description =
      `Browse the historical UK general election manifestos and campaign ` +
      `record of ${party.name}.`;
    const jsonLd = {
      '@context': 'https://schema.org',
      '@type': 'Organization',
      name: party.name,
      alternateName: party.shortName,
      url: canonicalFor(path),
    };
    return {
      valid: true,
      meta: { title, description },
      jsonLd,
      image: `/og/party/${parts[1]}.jpg`,
    };
  }

  // /nation/:id
  if (parts[0] === 'nation' && parts.length === 2) {
    const name = seo.nations && seo.nations[parts[1]];
    // Back-compat: if seo.json predates the nations list, accept slug-shaped
    // IDs (canonical fix only) rather than risk 404ing a real page.
    if (!seo.nations) return { valid: /^[a-z][a-z0-9-]*$/.test(parts[1]), meta: null };
    if (!name) return { valid: false };
    return {
      valid: true,
      meta: {
        title: `${name} — UK General Election Results${TITLE_SUFFIX}`,
        description: `UK general election results, seat history, and manifestos for ${name}.`,
      },
    };
  }

  // /devolved/:id
  if (parts[0] === 'devolved' && parts.length === 2) {
    const name = seo.devolved && seo.devolved[parts[1]];
    if (!seo.devolved) return { valid: /^[a-z][a-z0-9-]*$/.test(parts[1]), meta: null };
    if (!name) return { valid: false };
    return {
      valid: true,
      meta: {
        title: `${name} Elections${TITLE_SUFFIX}`,
        description: `Election results and party manifestos for the ${name}.`,
      },
    };
  }

  return { valid: false };
}

function buildRewriter({ meta, jsonLd, canonical, image, noindex }) {
  const rewriter = new HTMLRewriter();

  if (canonical) {
    rewriter.on('link[id="canonical-link"]', {
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
      if (jsonLd) {
        el.append(jsonLdScript(jsonLd), { html: true });
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
    jsonLd: result.jsonLd,
    canonical: canonicalFor(path),
    image: result.image,
    noindex: false,
  });
  return rewriter.transform(response);
}
