---
type: index
title: Data model
description: The shape of everything under data/ and manifestos/.
tags: [data-model]
timestamp: 2026-07-11T00:00:00Z
---

# Data model

All structured data lives under `data/` as JSON; manifesto documents live under
`manifestos/`. Concepts:

- [elections](./elections.md) — per-election metadata and results
- [constituencies](./constituencies.md) — per-year constituency data
- [devolved](./devolved.md) — Holyrood, Senedd, Stormont, London, European Parliament
- [manifestos-index](./manifestos-index.md) — the manifesto catalogue + file layout
- [party-colours](./party-colours.md) — canonical party ids, colours and eras
- [party-names](./party-names.md) — period-correct labels (Liberal/Alliance; Ecology/Green)
- [party-contests](./party-contests.md) — optional contests[] / status for `/parties/all`
- [party-holdings](./party-holdings.md) — per-party manifesto counts by chamber (derived)

## Quick map of `data/`
| Path | Contents |
|---|---|
| `data/elections/<id>.json` | Per-election metadata + results (`1945`…`2024`, `feb1974`, `oct1974`) |
| `data/constituencies/<id>.json` + `index.json` | Per-year constituency results |
| `data/devolved/{holyrood,senedd,stormont,london,euro}/` | Devolved & EP election data |
| `data/hex/` | Hex cartogram JSON (Westminster + devolved; see [pipelines/hexmaps](../pipelines/hexmaps.md)) |
| `data/manifestos-index.json` | Flat catalogue of available manifestos |
| `data/pdf-sizes.json` | URL path → human-readable PDF size ([pipelines/pdf-sizes](../pipelines/pdf-sizes.md)) |
| `data/election-vote-totals.json` | National vote totals/percentages by party by year |
| `data/seo.json` | Edge SEO feed: parties, elections, nations, devolved portals, manifesto metadata, chamber counts |
| `data/catalog.jsonld` | Public Schema.org `DataCatalog` feed (three `Dataset`s) |
| `data/archive-counts.json` | Unique folder totals for the hero (`scripts/build-archive-counts.py`) |
| `data/party-links.json` | Curated `sameAs` URLs per party (Wikipedia + official sites) |
| `data/party-colours.json` | Canonical party slug → hex palette |
| `data/party-colour-aliases.json` | Hexmap/OG display label → slug |
| `data/party-colour-overrides.json` | Hexmap-only label → hex overrides |
| `data/party-holdings.json` | Per-party manifesto counts by chamber (exported by `build-manifest.mjs`; see [party-holdings](./party-holdings.md)) |
| `data/sources/` | Source notes/citations |
| `data/cache/` | Cached scrapes (parlconst, wikipedia-hex, politicsresources) |
