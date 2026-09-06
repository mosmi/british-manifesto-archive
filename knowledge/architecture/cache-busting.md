---
type: runbook
title: Cache busting
description: The ?v= query-string convention for forcing browsers to reload CSS/JS after a change.
tags: [deploy, cache, frontend]
timestamp: 2026-07-05T00:00:00Z
---

# Cache busting

Cloudflare and browsers cache aggressively. Two places control asset versioning:

## 1. `index.html` — `?v=` on every `<link>` and `<script>`
When you change `styles.css`, `fonts/latin.css`, or any `js/*.js`, bump the
`?v=` string on **all** stylesheet and script tags in `index.html` (and the
`catalog.jsonld` link). Self-hosted font files are hashed in the filename;
`/fonts/*` is `immutable`.

## 2. `js/data-loader.js` — `ASSETS_VERSION`
Lazy-loaded JSON and markdown fetches append `?v=${ASSETS_VERSION}`. Bump this
constant when you change anything under `data/` that the loader fetches at runtime
(election JSON, manifesto markdown, etc.). Keep it in sync with the `index.html`
version unless you deliberately want to bust only one layer.

**Rule of thumb:** after any deploy-worthy change, set both to the same new value
(e.g. `2026070518` → today's date + a sequence digit).

Versioned `/js/*` and `/styles.css` are served with `Cache-Control: immutable`
(long max-age). That is safe **only** because the URL changes when `?v=` changes.
Do not mark unversioned HTML or in-place PDF replacements the same way.

Without bumping, returning visitors keep old cached assets and won't see your change,
even after a successful deploy. After deploying, hard-refresh (Shift+Reload) or purge
the Cloudflare cache to confirm.

See also: [deployment](./deployment.md).
