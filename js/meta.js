/* Shared page metadata helpers — keep in sync with functions/_middleware.js */

const SITE_META = {
  name: 'The British Manifesto Archive',
  domain: 'www.manifestos.org.uk',
  url: 'https://www.manifestos.org.uk',
  titleSuffix: ' — The British Manifesto Archive',
  homeTitle: 'The British Manifesto Archive',
  defaultDescription:
    'A comprehensive digital archive of general, devolved, regional, and ' +
    'European Parliament election manifestos, results, and maps in the UK.',
  defaultOgImage: 'https://www.manifestos.org.uk/og-image.jpg',
  defaultOgImageWidth: 1200,
  defaultOgImageHeight: 630,
  defaultOgImageAlt:
    'The British Manifesto Archive — a digital repository of UK political party manifestos',
};

function formatDocumentTitle(pageTitle) {
  if (!pageTitle) return SITE_META.homeTitle;
  return `${pageTitle}${SITE_META.titleSuffix}`;
}

function westminsterElectionDescription(election) {
  const year = election.displayYear;
  const datePart = election.date ? ` held on ${election.date}` : '';
  return `Results, seat maps, and party manifestos from the ${year} UK general election${datePart}.`;
}

function devolvedElectionDescription(portalId, yearLabel, portal) {
  const name = portal?.label || portalId;
  const subtitle = portal?.subtitle ? ` (${portal.subtitle})` : '';
  return `Results, seat maps and party manifestos from the ${yearLabel} ${name}${subtitle} election.`;
}

/** Chamber slugs under `/election/…`. Westminster items stay year-only. */
const CHAMBER_SLUGS = ['holyrood', 'senedd', 'stormont', 'london', 'euro'];

/**
 * Byte-identical labels for nav, breadcrumb and hero (audit 2.3).
 * One string per node — do not paraphrase at the call site.
 */
const NODES = {
  home: 'Home',
  elections: 'Elections',
  allElections: 'All elections',
  generalElections: 'General elections (1945–2024)',
  westminster: 'Westminster',
  holyrood: 'Scottish Parliament',
  senedd: 'Welsh Parliament',
  stormont: 'Northern Ireland Assembly',
  london: 'London Mayor & Assembly',
  euro: 'European Parliament',
  parties: 'Parties',
  allParties: 'All parties A–Z',
  otherParties: 'Other parties',
  europeanGroups: 'European groups',
  manifestos: 'Manifestos',
  nations: 'The Four Nations',
  about: 'About',
  england: 'England',
  wales: 'Wales',
  scotland: 'Scotland',
  northernIreland: 'Northern Ireland',
};

const PARTY_HUB_SLUGS = ['all', 'other', 'european-groups'];

function chamberPath(slug, rest) {
  if (rest) return `/election/${slug}/${rest}`;
  return `/election/${slug}`;
}

function nodeLabel(key) {
  return NODES[key] || key;
}

/** Map legacy public paths onto the singular scheme. Identity if already canonical. */
function canonicalizeArchivePath(path) {
  let p = path || '/';
  if (p.length > 1 && p.endsWith('/')) p = p.slice(0, -1);

  let m = p.match(/^\/devolved\/london\/(gla|glc|lcc)-(\d{4})$/);
  if (m) return `/election/london/${m[2]}`;
  m = p.match(/^\/manifesto\/london\/(gla|glc|lcc)-(\d{4})\/([^/]+)$/);
  if (m) return `/manifesto/london/${m[2]}/${m[3]}`;

  if (p === '/elections') return '/election/westminster';
  if (p === '/parties') return '/party';
  if (p === '/parties/all') return '/party/all';
  if (p.startsWith('/parties/')) return `/party/${p.slice('/parties/'.length)}`;
  if (p === '/others') return '/party/other';
  if (p === '/nations') return '/nation';
  if (p === '/manifestos') return '/manifesto';
  if (p === '/nation/europe') return '/party/european-groups';
  if (p === '/devolved') return '/election';
  if (p.startsWith('/devolved/')) return `/election/${p.slice('/devolved/'.length)}`;
  if (p.startsWith('/election/westminster/')) {
    return `/election/${p.slice('/election/westminster/'.length)}`;
  }
  return p;
}

function ogImageForPath(path) {
  if (!path || path === '/') return SITE_META.defaultOgImage;
  const canonical = canonicalizeArchivePath(path);
  const parts = canonical.replace(/^\//, '').split('/').filter(Boolean);
  if (parts[0] === 'party') {
    if (parts[1] === 'european-groups') return `${SITE_META.url}/og/nation/europe.jpg`;
    if (parts[1] === 'other') return `${SITE_META.url}/og/hub/others.jpg`;
    if (parts[1] === 'all' || !parts[1]) return `${SITE_META.url}/og/hub/parties.jpg`;
    return `${SITE_META.url}/og/party/${parts[1]}.jpg`;
  }
  if (parts[0] === 'election') {
    if (!parts[1]) return `${SITE_META.url}/og/hub/devolved.jpg`;
    if (parts[1] === 'westminster') return `${SITE_META.url}/og/hub/elections.jpg`;
    if (CHAMBER_SLUGS.includes(parts[1])) {
      if (parts[2] === 'other-parties') {
        return `${SITE_META.url}/og/devolved/${parts[1]}/other-parties.jpg`;
      }
      if (parts[2]) return `${SITE_META.url}/og/devolved/${parts[1]}/${parts[2]}.jpg`;
      return `${SITE_META.url}/og/devolved/${parts[1]}.jpg`;
    }
    return `${SITE_META.url}/og/election/${parts[1]}.jpg`;
  }
  if (parts[0] === 'manifesto' && parts[1] && parts[2]) {
    const electionId = parts.length >= 4 ? `${parts[1]}/${parts[2]}` : parts[1];
    const partyId = parts.length >= 4 ? parts[3] : parts[2];
    return `${SITE_META.url}/og/manifesto/${electionId}/${partyId}.jpg`;
  }
  if (parts[0] === 'nation' && parts[1]) {
    return `${SITE_META.url}/og/nation/${parts[1]}.jpg`;
  }
  const hubSlugs = {
    '/nation': 'nations',
    '/about': 'about',
  };
  if (hubSlugs[canonical]) {
    return `${SITE_META.url}/og/hub/${hubSlugs[canonical]}.jpg`;
  }
  return SITE_META.defaultOgImage;
}

function ogImageAltForTitle(pageTitle) {
  return pageTitle ? formatDocumentTitle(pageTitle) : SITE_META.defaultOgImageAlt;
}
