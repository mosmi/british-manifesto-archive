---
type: pipeline
title: Hexmaps pipeline
description: How the UK historical hex cartograms (1945–2024) are packed, coloured and previewed; algorithm decisions and known gaps.
resource: https://open-innovations.org/projects/hexmaps/
tags: [pipeline, hexmaps, maps, data]
timestamp: 2026-06-29T00:00:00Z
---

# Hexmaps pipeline

Generates hex cartograms for every UK general election **1945–2024** in
[Open Innovations hexjson](https://open-innovations.org/projects/hexmaps/) format
(odd-r, pointy-top), one file per election, each constituency coloured by winning
party with white region-boundary lines. Output feeds `data/hex/`.

**Project home:** `tools/hexmaps/` (was `~/Claude/claude-code/hexmaps/`). The full,
authoritative, session-by-session engineering log is in that project's `OVERVIEW.md` —
this concept is the durable summary; consult `OVERVIEW.md` for the deep detail.

> Note: an older snapshot of this knowledge existed at
> `~/Claude/.../geojson/memory/project_hexmaps.md` (dated 2026-05-28). It is
> **superseded** by the project's `OVERVIEW.md` (sessions through June 2026) and this
> concept. Don't rely on the old snapshot.

## Pipeline stages (`tools/hexmaps/scripts/`)
1. **`pack.py`** — GeoJSON → geometry-only hexjson. Region masks derived from the
   authoritative 2024 OI layout, grown/shrunk to each year's seat count. South East
   uses globally-optimal **Hungarian matching** (`_lap_solve`, Jonker-Volgenant);
   other regions use a Dijkstra continuous-distance search (r-axis weighted 4×).
2. **`colour.py`** — joins results CSV to packed hexjson via a **six-tier name-match
   cascade** (exact → compass-expanded → directional-collapsed → crosswalk →
   sorted-words → suffix). Winner = highest share among `con/lab/lib/natSW/oth`;
   `natSW` → SNP (Scotland) or Plaid (Wales); NI from 1974 uses `ni_results.json`.
3. **`validate.py`** — sanity checks.
4. **`generate_preview.py`** — self-contained `preview/index.html` viewer.
   `PARTY_ORDER` includes EP alliance families for legend ordering when those
   parties appear on preview maps.

## ⚠ Pipeline-order trap
`pack.py` writes geometry-only hexjson and **overwrites colour fields**. Always run
`colour.py` after any `pack.py` run, even a verification run, or maps render blank.
For **October 1974** specifically: pack.py has no `19741` entry — run `pack.py
--year 1974`, copy `output/1974.hexjson` → `output/19741.hexjson`, then `colour.py
--year 19741`.

## Boundary sets
Nine boundary sets cover the 22 elections (1945, 1950, 1955, 1974, 1983, 1992 w/ MK
split, 1997, 2005 hybrid, 2010, 2024). Feb & Oct 1974 share positions (internal year
`1974` vs `19741`); only colouring differs.

## Minor/historical parties
The results CSV pools minor parties into an `oth` bucket. `MANUAL_OVERRIDES` in
`colour.py` reclassify specific seats to their true winner (National Liberal,
Communist, Common Wealth, ILP, Irish Labour, Republican Labour, Nationalist,
Protestant Unionist, Independent Labour, Respect, UKIP Clacton, Green Brighton
Pavilion, etc.). Party colours are loaded from [`data/party-colours.json`](../../data/party-colours.json)
plus [`party-colour-aliases.json`](../../data/party-colour-aliases.json) and
[`party-colour-overrides.json`](../../data/party-colour-overrides.json) at import in
`colour.py` — devolved, NI, minor and EP alliance parties (by display name and party id).
NI pre-1974 UUP seats colour Conservative (took the Tory whip until
1974); non-Unionist NI seats are individually overridden.

## Known gaps (candidates for `backlog/`)
- **1945 v4 not promoted:** `pack_test_1945_v4.py` is the cleanest 1945 layout (0
  interior holes, clean boundaries, Thames Estuary preserved) but the live
  `output/1945.hexjson` still uses greedy-Dijkstra `pack.py`. Promotion needs a
  cross-check that shared `pack.py` mask changes don't regress the other 21 years.
- **Spelthorne (1997–2019):** minor residual cascade (correct latitude, wrong corridor).
- **Monmouth (Wales):** consistently ~1.7° west of correct position.
- **1945 multi-member/University seats (22):** excluded; not yet shown as an annotated
  section in the viewer.
- **2010-base England+Wales overflow:** London (+39 vs 2010 cells), NW (+4), NE (+2)
  overflow the joint pool; fix = per-region `grow_mask` expansion.
