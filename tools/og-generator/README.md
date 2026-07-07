# OG image generator — The British Manifesto Archive

Renders the 1200×630 social/meta images designed in `OG Templates.dc.html`.

## Files
- `og.html` — self-contained renderer. `?spec=<urlencoded JSON>` renders one card;
  no params renders a QA gallery of every card type.
- `build-manifest.mjs` — derives `pages.json` from `data/seo.json` and site data.
- `generate-og.mjs` — Puppeteer batch script with hash-based incremental skip.
- `pages.sample.json` — example manifest covering every type & edge case.

## Run
```bash
npm install
npm approve-scripts          # if npm blocked puppeteer's install.mjs — approve it, then npm install again
python3 scripts/build-seo-data.py          # if seo.json is stale
python3 scripts/build-og-images.py         # full build (~400 cards)
python3 scripts/build-og-images.py --sample # preview a handful
```

If the build fails with `Failed to launch the browser process`, Puppeteer's Chrome
download was probably incomplete. Either rerun `python3 scripts/build-og-images.py`
(the wrapper now extracts the zip automatically), or install Google Chrome and
rerun — the renderer falls back to your system Chrome.

Or directly:
```bash
node tools/og-generator/build-manifest.mjs
node tools/og-generator/generate-og.mjs tools/og-generator/pages.json .
```

Writes one JPEG (quality 88) per entry, mirroring the site's `/og/…` URL structure.
Subtitles are computed from manifesto holdings and update on the next build when
content changes.

## Spec reference
Common fields: `title`, `subtitle` (use `*text*` for cream emphasis), `kicker` (override).

| type | fields | notes |
|---|---|---|
| `home` | — | flagship card, spectrum bar |
| `about` | — | book-spines motif |
| `index` | `slug`: elections \| devolved \| nations \| others \| parties | motif per slug |
| `election` | `year`, `ghost` (2-char override, e.g. "74"), `body` (omit for UK GE), `strip` (optional `[["#hex",width],…]` seat strip) | ghost numeral defaults to last 2 digits of year |
| `nation` | `slug`: scotland \| wales \| england \| northern-ireland \| europe | national colour + motif |
| `body` | `slug`: holyrood \| senedd \| stormont \| london \| euro | institutional motif |
| `other-parties` | `body` | chips motif, inherits body accent |
| `party` | `slug` (palette key) or `colour` ("#hex") | edge bar; kicker override for EP groups → "EUROPEAN GROUP" |
| `manifesto` | `slug`/`colour`, `year`, `yearLabel` (e.g. "FEB 1974") | party-colour spine |

## Colour system
Palette loaded from [`data/party-colours.json`](../../data/party-colours.json) via
`colour.py` (aliases + overrides). Derivation rules,
applied automatically to every colour:
- **surface** (spine/edge bar): raw colour; lifted to oklch L≈0.48 if too dark for the navy field; achromatic → slate
- **kicker text**: lightness clamped to ≥0.75, chroma capped; achromatic → `#aab3c0`
- **text on pale spines** (L≥0.7): navy `#090e1c`

Long titles auto-shrink (118px → 64px by length). Fonts load from Google Fonts at
render time; the script waits for `window.__ready` before capture.
