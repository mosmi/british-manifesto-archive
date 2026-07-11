---
type: index
title: Pipelines
description: Build scripts and toolkits — hexmaps, transcription, covers, PDF sizes, OG cards.
tags: [pipelines]
timestamp: 2026-07-11T00:00:00Z
---

# Pipelines

Scripts and satellite toolkits that generate content consumed by the site.

- [hexmaps](./hexmaps.md) — Westminster hex cartograms in `data/hex/`
- [transcription](./transcription.md) — manifesto PDFs → `manifestos/**/manifesto.md`
- [covers](./covers.md) — transparent A4 PNG covers from `manifesto.pdf` page 1
- [pdf-sizes](./pdf-sizes.md) — `data/pdf-sizes.json` for download-link file sizes
- [latest-additions](../content/latest-additions.md) — homepage carousel from catalogue + git dates
- [og-generator](./og-generator.md) — Open Graph share cards in `/og/`

Toolkits live under `tools/`; most one-off import/build scripts live in `scripts/`.
Run `python3 scripts/build-seo-data.py` before OG generation or sitemap rebuilds
whenever parties, elections, or the manifesto index change.
