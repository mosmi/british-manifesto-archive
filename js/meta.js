/* Shared page metadata helpers — keep in sync with functions/_middleware.js */

const SITE_META = {
  name: 'The British Manifesto Archive',
  domain: 'www.manifestos.org.uk',
  url: 'https://www.manifestos.org.uk',
  titleSuffix: ' — The British Manifesto Archive',
  homeTitle: 'The British Manifesto Archive — www.manifestos.org.uk',
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

function ogImageForPath(path) {
  if (!path || path === '/') return SITE_META.defaultOgImage;
  const parts = path.replace(/^\//, '').split('/').filter(Boolean);
  if (parts[0] === 'party' && parts[1]) {
    return `${SITE_META.url}/og/party/${parts[1]}.jpg`;
  }
  if (parts[0] === 'election' && parts[1]) {
    return `${SITE_META.url}/og/election/${parts[1]}.jpg`;
  }
  if (parts[0] === 'manifesto' && parts[1] && parts[2]) {
    return `${SITE_META.url}/og/manifesto/${parts[1]}/${parts[2]}.jpg`;
  }
  if (parts[0] === 'nation' && parts[1]) {
    return `${SITE_META.url}/og/nation/${parts[1]}.jpg`;
  }
  if (parts[0] === 'devolved' && parts[1]) {
    if (parts[2] === 'other-parties') {
      return `${SITE_META.url}/og/devolved/${parts[1]}/other-parties.jpg`;
    }
    if (parts[2] && parts[2] !== 'other-parties') {
      return `${SITE_META.url}/og/devolved/${parts[1]}/${parts[2]}.jpg`;
    }
    const portal = parts[1];
    if (['holyrood', 'senedd', 'stormont', 'euro', 'london'].includes(portal)) {
      return `${SITE_META.url}/og/devolved/${portal}.jpg`;
    }
  }
  const hubSlugs = {
    '/elections': 'elections',
    '/parties': 'parties',
    '/devolved': 'devolved',
    '/nations': 'nations',
    '/others': 'others',
    '/about': 'about',
  };
  if (hubSlugs[path]) {
    return `${SITE_META.url}/og/hub/${hubSlugs[path]}.jpg`;
  }
  return SITE_META.defaultOgImage;
}

function ogImageAltForTitle(pageTitle) {
  return pageTitle ? formatDocumentTitle(pageTitle) : SITE_META.defaultOgImageAlt;
}
