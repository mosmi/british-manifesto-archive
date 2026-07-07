---
type: index
title: Architecture
description: How the British Manifesto Archive is structured, deployed and cached.
tags: [architecture]
timestamp: 2026-07-05T00:00:00Z
---

# Architecture

- [site-structure](./site-structure.md) — files, JS modules, routing
- [deployment](./deployment.md) — Cloudflare runbook and the one critical gotcha
- [cache-busting](./cache-busting.md) — the `?v=` versioning rule
- [structured-data](./structured-data.md) — edge SEO, Open Graph, Schema.org JSON-LD

The site has **no bundler or framework**: static files served as-is, with
client-side JS reading JSON from `data/`. Dynamic SEO metadata and JSON-LD are
edge-rendered by Cloudflare Functions before the SPA boots.
