---
type: index
title: Project knowledge base
description: Durable knowledge for the British Manifesto Archive — architecture, data model, pipelines, content state and page rules.
resource: https://www.manifestos.org.uk
tags: [index, overview]
timestamp: 2026-07-11T00:00:00Z
---

# Project knowledge base

Durable knowledge for the British Manifesto Archive — architecture, data model, pipelines, content state and page rules.

## Sections
- [architecture](./architecture/index.md) — how the site is built, deployed and cached
- [data-model](./data-model/index.md) — the shape of everything under `data/` and `manifestos/`
- [pipelines](./pipelines/index.md) — hexmaps, transcription, covers, fonts, PDF sizes, OG cards, manifesto titles
- [content-state](./content-state/index.md) — what's transcribed, what's missing, audit state
- [content/latest-additions](./content/latest-additions.md) — homepage Latest Additions carousel
- [page-rules](./page-rules/index.md) — special cases and guardrails for specific pages
- [design](./design/index.md) — visual/UX refresh and the [Sep 2026 audit batches](./design/sep-2026-audit-plan.md)
- [log](./log.md) — chronological project history

## One-paragraph orientation
The site is plain HTML/CSS/JS with no bundler (`index.html` + `styles.css` +
`js/*.js`), reading JSON from `data/` and serving manifesto files from
`manifestos/<electionId>/<partyId>/`. It deploys to Cloudflare from `main` on push.
Edge middleware (`functions/_middleware.js`) injects per-route SEO metadata and
Schema.org JSON-LD from `data/seo.json`.

Three satellite toolkits under [`tools/`](../tools) feed it:
- **hexmaps** — generates Westminster cartograms in `data/hex/`
- **transcription-toolkit** — turns manifesto PDFs into `manifestos/**/manifesto.md`
- **og-generator** — renders Open Graph share cards into `/og/` (see
  [pipelines/og-generator](./pipelines/og-generator.md))

Python maintenance scripts in `scripts/` build SEO data, sitemaps, OG images, and
import devolved/euro assets. To **regenerate all Open Graph share cards**, see
[pipelines/og-generator](./pipelines/og-generator.md#regenerating-all-og-images-runbook).
