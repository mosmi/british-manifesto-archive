/* ============================================================
   Party colour derivation — shared OKLCH rules (OG + site)
   ============================================================ */

const COLOUR_FIELD = '#090e1c';
const COLOUR_PAPER = '#f7f3ea';

function hexToRgb(hex) {
  const h = hex.replace('#', '');
  const n = parseInt(h.length === 3 ? h.split('').map(c => c + c).join('') : h, 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255].map(v => v / 255);
}

function srgbToLinear(c) { return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); }
function linearToSrgb(c) { return c <= 0.0031308 ? 12.92 * c : 1.055 * Math.pow(c, 1 / 2.4) - 0.055; }

function rgbToOklch(rgb) {
  const [r, g, b] = rgb.map(srgbToLinear);
  const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b);
  const m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b);
  const s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
  const L = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s;
  const a = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s;
  const bb = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s;
  const C = Math.sqrt(a * a + bb * bb);
  let H = Math.atan2(bb, a) * 180 / Math.PI;
  if (H < 0) H += 360;
  return { L, C, H };
}

function oklchToHex({ L, C, H }) {
  const hr = H * Math.PI / 180;
  const a = C * Math.cos(hr);
  const bb = C * Math.sin(hr);
  const l = Math.pow(L + 0.3963377774 * a + 0.2158037573 * bb, 3);
  const m = Math.pow(L - 0.1055613458 * a - 0.0638541728 * bb, 3);
  const s = Math.pow(L - 0.0894841775 * a - 1.2914855480 * bb, 3);
  let r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s;
  let g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s;
  let b = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s;
  const clamp = v => Math.max(0, Math.min(1, linearToSrgb(v)));
  return '#' + [r, g, b].map(v => Math.round(clamp(v) * 255).toString(16).padStart(2, '0')).join('');
}

function rgbaHex(hex, a) {
  const [r, g, b] = hexToRgb(hex).map(v => Math.round(v * 255));
  return `rgba(${r},${g},${b},${a})`;
}

function deriveColour(hex, theme) {
  if (!hex) hex = '#6b7280';
  const lch = rgbToOklch(hexToRgb(hex));
  const achromatic = lch.C < 0.02;
  const isLight = theme === 'light';

  let kicker;
  let surface;

  if (isLight) {
    kicker = achromatic ? '#5b6478'
      : oklchToHex({ L: Math.min(lch.L, 0.55), C: Math.min(lch.C, 0.15), H: lch.H });
    if (lch.L >= 0.82 && !achromatic) {
      surface = oklchToHex({ L: 0.68, C: Math.max(lch.C, 0.12), H: lch.H });
    } else if (lch.L >= 0.30) {
      surface = hex;
    } else {
      surface = achromatic ? '#5b6478'
        : oklchToHex({ L: 0.48, C: Math.max(lch.C, 0.10), H: lch.H });
    }
  } else {
    kicker = achromatic ? '#aab3c0'
      : oklchToHex({ L: Math.max(lch.L, 0.75), C: Math.min(lch.C, 0.15), H: lch.H });
    surface = lch.L >= 0.30 ? hex
      : (achromatic ? '#3d4654' : oklchToHex({ L: 0.48, C: Math.max(lch.C, 0.10), H: lch.H }));
  }

  const surfL = rgbToOklch(hexToRgb(surface)).L;
  return {
    raw: hex,
    surface,
    kicker,
    border: rgbaHex(kicker, 0.35),
    onSurface: surfL >= 0.70 ? COLOUR_FIELD : 'rgba(255,255,255,0.85)',
  };
}

function kickerOnPaper(hex) {
  if (!hex) hex = '#6b7280';
  const lch = rgbToOklch(hexToRgb(hex));
  const achromatic = lch.C < 0.02;
  return achromatic ? '#5b6478'
    : oklchToHex({ L: Math.min(lch.L, 0.55), C: Math.min(lch.C, 0.18), H: lch.H });
}

function surfaceColour(hex, theme) {
  return deriveColour(hex, theme).surface;
}

function kickerTextColour(hex, theme) {
  return deriveColour(hex, theme).kicker;
}

function onSurfaceColour(hex, theme) {
  return deriveColour(hex, theme).onSurface;
}

function partyAccentDerived(partyId, theme) {
  const resolvedTheme = theme || getCurrentTheme();
  const raw = typeof getPartyColor === 'function'
    ? getPartyColor(partyId)
    : (typeof PARTIES !== 'undefined' && PARTIES[partyId]?.color) || '#6b7280';
  return deriveColour(raw, resolvedTheme);
}

function partyAccentDerivedForYear(partyId, year, theme) {
  const resolvedTheme = theme || getCurrentTheme();
  const raw = typeof getPartyColor === 'function'
    ? getPartyColor(partyId, year)
    : partyAccentDerived(partyId, resolvedTheme).raw;
  return deriveColour(raw, resolvedTheme);
}

function getCurrentTheme() {
  return document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
}

function dotColour(hex, theme) {
  const resolvedTheme = theme || getCurrentTheme();
  const fill = surfaceColour(hex, resolvedTheme);
  const lch = rgbToOklch(hexToRgb(hex));
  const needsOutline = resolvedTheme === 'light' && lch.L >= 0.7;
  return { fill, needsOutline };
}

function dotStyle(hex, theme) {
  const { fill, needsOutline } = dotColour(hex, theme);
  return needsOutline
    ? `background:${fill};box-shadow:inset 0 0 0 1px rgba(20,32,58,0.25)`
    : `background:${fill}`;
}

function ghostTint(hex, theme) {
  const surface = surfaceColour(hex, theme || getCurrentTheme());
  const opacity = (theme || getCurrentTheme()) === 'light' ? 0.14 : 0.07;
  return rgbaHex(surface, opacity);
}

function barColour(hex, theme) {
  const resolvedTheme = theme || getCurrentTheme();
  const lch = rgbToOklch(hexToRgb(hex));
  if (resolvedTheme === 'light' && lch.L >= 0.85) {
    return surfaceColour(hex, resolvedTheme);
  }
  return hex;
}

function partyTextColour(partyId, year, theme) {
  const raw = typeof getPartyColor === 'function'
    ? getPartyColor(partyId, year)
    : (typeof PARTIES !== 'undefined' && PARTIES[partyId]?.color) || '#6b7280';
  return kickerTextColour(raw, theme || getCurrentTheme());
}

function formatPartyHoldingsLine(pid) {
  const h = PARTY_HOLDINGS[pid] || {};
  const labels = {
    westminster: 'Westminster',
    holyrood: 'Holyrood',
    senedd: 'Senedd',
    stormont: 'Assembly',
    euro: 'European Parliament',
    london: 'London',
  };
  const order = ['westminster', 'holyrood', 'senedd', 'stormont', 'euro', 'london'];
  const parts = order
    .filter(k => h[k] > 0)
    .map(k => `<span class="party-holdings-count">${h[k]}</span> ${labels[k]}`);
  if (!parts.length) return '';
  return parts.join(' · ') + ' manifestos';
}

let PARTY_HOLDINGS = {};

async function loadPartyHoldings() {
  try {
    const res = await fetch('/data/party-holdings.json', { cache: 'no-cache' });
    if (res.ok && (res.headers.get('content-type') || '').includes('json')) {
      PARTY_HOLDINGS = await res.json();
    }
  } catch (_) {
    PARTY_HOLDINGS = {};
  }
  return PARTY_HOLDINGS;
}

loadPartyHoldings();
