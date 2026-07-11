---
type: reference
title: Party ids, colours and eras
description: Canonical party identifiers and the authoritative historical colour table used across site, hexmaps and OG images.
tags: [data-model, parties, colours]
timestamp: 2026-07-05T00:00:00Z
---

# Party ids, colours and eras

Party **ids** are the canonical key used in `data/elections/*.json`,
`manifestos-index.json`, `manifestos/<id>/<partyId>/`, `data/seo.json` and
`js/data.js`. Examples: `conservative`, `labour`, `libdem`, `snp`, `dup`,
`scottishgrn`, `welshlab`, `sand`, `epp`, `renew`.

## Shared palette (single source)

| File | Role |
|---|---|
| **`data/party-colours.json`** | Canonical slug → hex — edit this when adding a party |
| `data/party-colour-aliases.json` | Hexmap/OG display labels → slug (e.g. `"Labour"` → `labour`) |
| `data/party-colour-overrides.json` | Hexmap-only labels with non-slug hex (e.g. `Other` → `#AAAAAA`) |

Regenerate compiled artefacts after editing slugs:

```bash
node scripts/build-party-colours.mjs
```

This writes `tools/og-generator/party-colours.embed.js` for the OG renderer.
The OG pipeline (`python3 scripts/build-og-images.py`) runs this automatically.

To rebuild aliases from a legacy inline dict (rare — only if `colour.py` still
contains one): `node scripts/build-party-colours.mjs --regenerate-aliases`

## Where colours are consumed

| Location | Used for |
|---|---|
| `data/party-colours.json` | **Source of truth** (slug → hex) |
| `js/data.js` → `PARTIES` | Site UI, maps, navigation |
| `js/colour.js` | OKLCH derivation for site UI |
| `data/seo.json` → `parties.<id>.color` | Edge SEO + OG manifest builder |
| `tools/hexmaps/scripts/colour.py` | Loads JSON + aliases + overrides at import |
| `tools/og-generator/og.html` | Loads `party-colours.embed.js` (generated from JSON) |

When adding a party:

1. Add slug + hex to `data/party-colours.json`.
2. Add display-label aliases to `party-colour-aliases.json` if hexmaps or OG use a long name.
3. Add to `party-colour-overrides.json` only if the hexmap colour must differ from the slug hex.
4. Update `js/data.js` → `PARTIES`, `data/seo.json` (via `build-seo-data.py`), and election data as usual.
5. Run `node scripts/build-party-colours.mjs` and rebuild OG images if needed.

## European Parliament alliance families

EP navigation and maps group parties into alliance ids (not individual UK parties):

`sand`, `epp`, `renew`, `greensefa`, `guengl`, `ecr`, `uen`, `inddem`, `identity`,
`diem25`, `volt`, `ecpm` — see `EURO_ALLIANCE_PARTIES` in `js/data.js`.

## Westminster historical colours (summary)

Core parties:

| Party | Colour | Era |
|---|---|---|
| Conservative | `#0087DC` | all |
| Labour | `#E4003B` | all |
| Liberal | `#FFD700` | pre-1983 |
| Alliance | `#FFD700` | 1983, 1987 |
| Liberal Democrats | `#FAA61A` | 1992+ |
| SNP | `#FDF38E` | 1970+ |
| Plaid Cymru | `#008672` | 1974+ |
| UKIP | `#6D3177` | 2015 |
| Green / Ecology | `#02A95B` / site `#00B140` | Ecology Party before 1985; Green thereafter — see [party-names](./party-names.md) |
| Reform UK | `#1EB8D0` | 2024 |
| DUP | `#D46A4C` | 1974+ |
| UUP | `#48A5EE` | 1974+ |
| Sinn Féin | `#326760` | 1955, 1983+ |
| SDLP | `#2AA82C` | 1974+ |
| Alliance NI | `#F6CB2F` | 2010+ |

(Full minor-party list and seat-level `MANUAL_OVERRIDES` are documented in
[pipelines/hexmaps](../pipelines/hexmaps.md).)

**Note:** hexmap `Other` uses `#AAAAAA` (override) while site `others` uses
`#6b7280`. Do not bulk-sync overrides without checking `MANUAL_OVERRIDES` impact.
