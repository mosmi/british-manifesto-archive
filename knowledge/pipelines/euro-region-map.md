---
type: pipeline
title: European Parliament election maps
description: PR-era regional waffle maps (1999–2019) and FPTP-era constituency hexmaps (1979–1994) for UK EP election pages.
tags: [pipelines, euro, maps]
timestamp: 2026-08-09T12:00:00Z
---

# European Parliament election maps

UK European Parliament elections use two map models on the site, gated separately
in [`js/euro.js`](../../js/euro.js):

| Years | System | UI | Gate |
|---|---|---|---|
| **1979–1994** | GB FPTP + NI STV | Constituency hex cartogram | `euroHasConstituencyMap` |
| **1999–2019** | GB d’Hondt regions + NI STV | Geographic region + seat-square clusters | `euroHasRegionMap` |

Do **not** widen `euroHasRegionMap` to pre-1999, and do **not** reuse
[`js/euro-map.js`](../../js/euro-map.js) for FPTP years.

---

## PR era (1999–2019) — regional seat map

Twelve multi-member electoral regions. Shown as a geographic region map with
coloured **seat-square clusters**, not a Holyrood-style single-member hex
cartogram.

### Runtime assets

| Asset | Role |
|---|---|
| [`data/maps/euro-regions.json`](../../data/maps/euro-regions.json) | Simplified SVG paths + seat anchors (shared across PR years) |
| [`data/devolved/euro/regions/<year>.json`](../../data/devolved/euro/regions/) | Per-election MEPs, seat tallies, turnout |
| [`js/euro-map.js`](../../js/euro-map.js) | Renderer (paths + waffle clusters + MEP detail) |
| [`js/euro.js`](../../js/euro.js) | Election page tabs (Parliament / Electoral regions) |

### Build scripts

```bash
# 2019 regional results (Commons Library CBP 8600 spreadsheet)
python3 scripts/build-euro-regions.py

# 1999–2014 regional results (Commons Library RP PDFs)
python3 scripts/build-euro-regions-pr.py

# Geography (from ONS EER UGCB GeoJSON → simplified paths)
python3 scripts/build-euro-region-map.py
```

### Sources (tracked)

| File | Origin |
|---|---|
| `data/sources/commons-library/CBP-8600-2019.xlsx` | House of Commons Library briefing [CBP 8600](https://commonslibrary.parliament.uk/research-briefings/cbp-8600/) accompanying data (`UK MEPs` + `Vote share by LA`) |
| `data/sources/european-parliament-elections/commons-library/RP14-32.pdf` | [RP14-32](https://commonslibrary.parliament.uk/research-briefings/rp14-32/) (2014) |
| `data/sources/european-parliament-elections/commons-library/RP09-53.pdf` | [RP09-53](https://commonslibrary.parliament.uk/research-briefings/rp09-53/) (2009) |
| `data/sources/european-parliament-elections/commons-library/RP04-50.pdf` | [RP04-50](https://commonslibrary.parliament.uk/research-briefings/rp04-50/) (2004) |
| `data/sources/european-parliament-elections/commons-library/RP99-64.pdf` | [RP99-64](https://commonslibrary.parliament.uk/research-briefings/rp99-64/) (1999) |
| `data/sources/commons-library/eer-2018-ugcb.geojson` | ONS European Electoral Regions (Dec 2018) UGCB via ArcGIS FeatureServer |

Party slugs in the spreadsheet (`brexit`, `ld`, `con`, `pc`, `sf`, …) are mapped
to site ids (`reform`, `libdem`, `conservative`, `plaid`, `sinnfein`, …). Period
labels (e.g. Brexit Party) use `partyLabel` / `getPartyName(…, year)`.

GB regional vote shares and turnout are aggregated from the LA sheet (share ×
votes). NI first-preference shares for seat-winning parties come from the
election JSON / CBP totals.

### UI behaviour

On `/election/euro/2019`, the viz panel mirrors Holyrood:

1. **Parliament** — existing UK MEP seating chart (default)
2. **Electoral regions** — lazy-loads layout + results; hover for seat tally;
   click for elected MEP list

London’s seat cluster is drawn as a callout to the east of the region with a
leader line (same idea as Commons Library graphics).

### Coverage

| Year | Seats | Builder | Primary source |
|---:|---:|---|---|
| 2019 | 73 | `build-euro-regions.py` | CBP 8600 XLSX |
| 2014 | 73 | `build-euro-regions-pr.py` | RP14-32 (+ EC 2014 XLSX available for LA votes) |
| 2009 | 72 | `build-euro-regions-pr.py` | RP09-53 |
| 2004 | 78 | `build-euro-regions-pr.py` | RP04-50 |
| 1999 | 87 | `build-euro-regions-pr.py` | RP99-64 |

Geography is shared (`euro-regions.json`). Seat magnitudes and waffle grids vary
by year (`euroSeatGridFor` in `js/euro-map.js`).

---

## FPTP era (1979–1994) — constituency hexmaps

GB used **single-member FPTP** European constituencies; NI elected **3 MEPs by STV**. The site shows **one hex per EP seat**, with GB FPTP single-member constituencies plus a 3-hex mini-cluster off the west coast for Northern Ireland representing its 3 elected MEPs (DUP, SDLP, UUP).

Raw crosswalk centroids sit in the ~650-seat Westminster coordinate frame, so
direct placement is sparse. The hex builder **compacts** them into a contiguous
UK outline (Holyrood / GE style) while keeping England / Scotland / Wales /
relative order, eliminating 1-hex pinch points, and detaching Highlands & Islands and NI.

### Runtime assets

| Asset | Role |
|---|---|
| [`data/hex/euro/<year>.hexjson`](../../data/hex/euro/) | Coloured hex cartogram (`odd-r`) for 1979, 1984, 1989, 1994 |
| [`js/hexmap.js`](../../js/hexmap.js) | Shared renderer (`hexjsonToDrawData` / `drawHexmap`) |
| [`js/euro.js`](../../js/euro.js) | Constituencies tab via `euroHasConstituencyMap` |

Boundary eras on disk: **1979** · **1984** (= **1989**) · **1994**.

### Source inputs

| Asset | Role |
|---|---|
| [`constituency-winners-1979-1994.json`](../../data/sources/european-parliament-elections/constituency-winners-1979-1994.json) | GB winners + NI STV panel |
| [`westminster-to-ep/{1979,1984,1994}.json`](../../data/sources/european-parliament-elections/westminster-to-ep/) | Compositions + precomputed `centroids` (mean GE hex `q,r`) |
| [`commons-library/RP99-57.pdf`](../../data/sources/european-parliament-elections/commons-library/RP99-57.pdf) | National FPTP-era summary ([RP99-57](https://commonslibrary.parliament.uk/research-briefings/rp99-57/)) |

### Build scripts

```bash
# Regenerable compositions/centroids (maintainer)
python3 scripts/build-euro-fptp-crosswalk.py

# Hexjson: winners + compacted centroid layout (NI seats_list)
python3 scripts/build-euro-fptp-hex.py
```

**Layout pipeline** (`scripts/build-euro-fptp-hex.py`):

1. Classify seats → England / Scotland / Wales / Highlands / NI
2. Per nation: scale centroids toward their mean → Hungarian snap to unique
   cells → merge connected components → fill interior holes **within the nation**
3. Assemble: Scotland north of England, Wales west; one contiguous GB mainland
   (do not run cross-nation hole-fill — that migrates Wales/Scotland into England)
4. Detach Highlands (north of Scotland) and NI (west), with a one-cell buffer
5. Assert party seat totals vs `data/devolved/euro/<year>.json` and mainland
   contiguity

NI colouring uses the three MEP winners (`seats_list`), not the Westminster seat
count on the crosswalk centroid.

### UI behaviour

On `/election/euro/1979` (and 1984 / 1989 / 1994):

1. **Parliament** — UK MEP seating chart (default)
2. **Constituencies** — lazy-loads `/data/hex/euro/<year>.hexjson`; GB click
   shows constituency + MEP; NI shows three seat dots and member names

### Coverage

| Year | Hexes | GB FPTP seats | NI |
|---:|---:|---:|---|
| 1979 | 79 | 78 | 1 hex · 3 MEPs |
| 1984 | 79 | 78 | 1 hex · 3 MEPs |
| 1989 | 79 | 78 | 1 hex · 3 MEPs (reuses 1984 layout) |
| 1994 | 85 | 84 | 1 hex · 3 MEPs |

---

## Cache busting

Bump `?v=` in `index.html` and `ASSETS_VERSION` in `js/data-loader.js` when
changing `euro-map.js`, `euro.js`, `hexmap.js`, `styles.css`, or assets under
`data/maps/`, `data/hex/euro/`, or `data/devolved/euro/regions/`. See
[cache-busting](../architecture/cache-busting.md).
