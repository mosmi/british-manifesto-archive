---
type: reference
title: Local preview
description: How to run an SPA-aware local preview so deep links work like production.
tags: [architecture, preview, spa, local-dev]
timestamp: 2026-07-20T00:00:00Z
---

# Local preview

Default local preview is **SPA-aware**: hard loads of client routes
(`/elections`, `/parties/all`, `/party/labour`, `/election/2024`, …) serve
`index.html` so the client router can boot. Plain `python3 -m http.server` does
**not** do this — deep links 404 even though in-app soft navigation works.

## Start

```bash
python3 scripts/serve-preview.py
```

Open [http://127.0.0.1:8888/](http://127.0.0.1:8888/). Optional: `--port 8890`,
`--host 0.0.0.0`.

## Behaviour

| Request | Result |
|---|---|
| Existing file (`/js/app.js`, `/manifestos/…/manifesto.pdf`, …) | Served as-is |
| SPA hubs / prefixes listed in [`_redirects`](../../_redirects) 200 rules | `index.html` |
| Other extensionless paths | `index.html` (client may render not-found) |
| Missing file with an extension (e.g. missing PDF) | Real **404** (not HTML) |

This mirrors Cloudflare’s intent: SPA shell for extensionless routes, real 404s
for missing assets. It does **not** run edge middleware
(`functions/_middleware.js`) — for SEO/JSON-LD parity use a Cloudflare preview
or `wrangler pages dev` when available.

## Why not bare `http.server`?

Documented earlier in [design/amendments-light-mode](../design/amendments-light-mode.md):
direct navigation to `/manifesto/…` on bare `python -m http.server` returns 404.
Always prefer `scripts/serve-preview.py` for QA of routing, search, and shareable
URLs.

## Related

- [site-structure](./site-structure.md) — `_redirects` SPA fallbacks
- [deployment](./deployment.md) — live Cloudflare setup
