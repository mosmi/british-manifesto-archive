---
type: runbook
title: PDF file-size index
description: How manifesto download links show PDF sizes via data/pdf-sizes.json and scripts/build-pdf-sizes.py.
tags: [pipelines, manifestos, frontend, pdf]
timestamp: 2026-07-03T20:16:00Z
---

# PDF file-size index

Manifesto download buttons show a human-readable file size (e.g. `PDF document · 936 KB`)
without making live HTTP `HEAD` requests. Sizes are pre-computed into a static JSON index.

## Runtime

- **Index:** [`data/pdf-sizes.json`](../../data/pdf-sizes.json) — flat map of URL path → size string.
- **Loader:** [`js/app.js`](../../js/app.js) — `initPdfSizes()` fetches the index once at startup;
  `getPdfSize(path)` returns the string or `''` if unknown. Exposed as `window.getPdfSize` so
  devolved modules can use it.
- **Consumers:** any manifesto card or download link that calls `getPdfSize`, including:
  - [`js/app.js`](../../js/app.js) — Westminster election pages (`buildManifestoCard`, manifesto reader)
  - [`js/euro.js`](../../js/euro.js) — European Parliament election pages
  - [`js/holyrood.js`](../../js/holyrood.js), [`js/senedd.js`](../../js/senedd.js),
    [`js/ni.js`](../../js/ni.js), [`js/london.js`](../../js/london.js) — devolved pages

If a path is missing from the index, the UI still renders the link but **omits the size**
(e.g. `PDF document` with no `· 936 KB` suffix). This is what happened for newly added
2019 EU manifestos (Brexit Party, Conservatives, DUP) before the index was regenerated.

## Build script

[`scripts/build-pdf-sizes.py`](../../scripts/build-pdf-sizes.py) walks `manifestos/**/manifesto.pdf`,
reads each file's byte size from disk, and rewrites `data/pdf-sizes.json`.

```bash
python3 scripts/build-pdf-sizes.py
```

Run this **whenever a manifesto PDF is added, replaced or removed**. No other build step
picks this up automatically.

### Size formatting

| Range | Example |
|---|---|
| &lt; 1 KB | `512 B` |
| &lt; 1 MB | `936 KB` (rounded to whole KB) |
| &lt; 10 MB | `4.7 MB` (one decimal) |
| ≥ 10 MB | `10 MB` (whole MB) |

URL keys always use the site path form: `/manifestos/<…>/manifesto.pdf` (leading slash,
forward slashes).

## Checklist hook

When adding a manifesto, step 4 in
[manifestos-index](../data-model/manifestos-index.md) is **run `build-pdf-sizes.py`** after
placing the PDF. Commit the updated `data/pdf-sizes.json` with the new manifesto assets.

## Cache / deploy

`pdf-sizes.json` is fetched with `cache: 'no-cache'` — no `?v=` bump is required for size
text alone. Bumping `ASSETS_VERSION` in `index.html` / `js/data-loader.js` is still needed
when covers or JS change (see [cache-busting](../architecture/cache-busting.md)).

## Related

- [Manifestos index & file layout](../data-model/manifestos-index.md) — PDF folder convention
- [Devolved data](../data-model/devolved.md) — EU elections under `data/devolved/euro/`
