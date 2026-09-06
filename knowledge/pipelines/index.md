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
- [euro-region-map](./euro-region-map.md) — UK EP maps (FPTP hex 1979–1994; regional waffle 1999–2019)
- [transcription](./transcription.md) — manifesto PDFs → `manifestos/**/manifesto.md`
- [covers](./covers.md) — transparent A4 PNG covers from `manifesto.pdf` page 1; WebP thumbs `cover-356.webp` / `cover-712.webp` beside the PNG
- [fonts](./fonts.md) — self-hosted Latin woff2 (Playfair, Public Sans, Source Serif 4)
- [pdf-sizes](./pdf-sizes.md) — `data/pdf-sizes.json` for download-link file sizes
- [manifesto-assets](./manifesto-assets.md) — `data/manifesto-assets.json` (pdf/md/cover flags; “Not yet digitised” placeholder)
- [manifesto-titles](./manifesto-titles.md) — published titles from `manifesto.md` → `data/manifesto-titles.json` (audit 5.2)
- [fulltext-index](./fulltext-index.md) — `data/fulltext-index.json` for manifesto full-text search
- [latest-additions](../content/latest-additions.md) — homepage carousel from catalogue + git dates
- Archive counts: `python3 scripts/build-archive-counts.py` → `data/archive-counts.json` (unique folder keys; also run at the end of `build-seo-data.py`)
- [og-generator](./og-generator.md) — Open Graph share cards in `/og/`

Toolkits live under `tools/`; most one-off import/build scripts live in `scripts/`.
Run `python3 scripts/build-seo-data.py` before OG generation or sitemap rebuilds
whenever parties, elections, or the manifesto index change. That script also
refreshes `data/archive-counts.json`; or run `python3 scripts/build-archive-counts.py`
on its own.
