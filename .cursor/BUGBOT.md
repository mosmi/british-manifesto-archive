# Bugbot review guide — British Manifesto Archive

Static archive of UK election manifestos, results and maps (1918–2024), live at
**www.manifestos.org.uk**. Plain HTML/CSS/JS, **no build step / no framework**,
deployed to Cloudflare from `main`. `AGENTS.md` is the full agent guide; the
durable facts live in `knowledge/`.

Focus reviews on the things that actually break this project:

## Cache-busting (high priority)
- Whenever a PR changes `styles.css` or any `js/*.js`, the matching `?v=` query
  string in `index.html` **must** be bumped, and `ASSETS_VERSION` in
  `js/data-loader.js` should match. Flag any changed CSS/JS asset whose `?v=`
  cache-busting version was not updated — stale caches are a recurring bug here.
  See `knowledge/architecture/cache-busting.md`.

## No build step
- This is hand-written HTML/CSS/JS with **no bundler, transpiler, or framework**.
  Flag any introduction of a build tool, npm runtime dependency, JSX, TypeScript,
  or framework imports. Browser-native ES that runs as-is only.

## Deployment
- The domain must point at exactly **one** Cloudflare project (Workers *or*
  Pages, never both). Flag changes that would introduce a second deploy target
  or conflicting config. See `knowledge/architecture/deployment.md`.

## Generated data — don't hand-edit
- `data/hex/holyrood/*.hexjson` and `data/hex/holyrood-grid.json` are **generated**
  by `scripts/build-holyrood-grid.py` and `scripts/build-holyrood-hex.py`. Flag
  manual edits to these JSON files that aren't reflected in the generator scripts.
- The hex generators hard-fail on unmapped constituencies or coordinate
  collisions; flag changes that weaken or remove those validations.

## Hexmaps
- Layout is `odd-r` / pointy-top axial coords (north = higher `r`, east = higher
  `q`), matching `js/hexmap.js`. Flag coordinate logic that breaks this convention.
- Hex tooltips/labels should display the human constituency name (`cell.n`), not
  the internal slug key. Data lookups into `hexjson.hexes` should use the `key`
  field, not the display name.

## Page rules
- Only `/party/cooperative` may split Labour/Co-op results out. Flag any other
  page that double-counts or re-attributes Co-op seats. See
  `knowledge/page-rules/cooperative-party.md`.

## General
- Vanilla JS: watch for missing `null`/`undefined` guards on `fetch`/JSON data,
  unescaped user-facing strings inserted via `innerHTML`, and accessibility
  regressions (missing `aria-*` / keyboard handling) on interactive widgets.
