# UK Historical Election Hexmaps — Project Summary

A complete set of hex cartograms for every UK general election from 1945 to 2024, in [Open Innovations hexjson](https://open-innovations.org/projects/hexmaps/) format. Each election year gets its own file in `output/`, with every constituency coloured by its winning party and white region-boundary lines overlaid in the viewer.

---

## What was built

**22 hexjson files** — one per general election (including both February and October 1974):

| Year | Hexes | Match | Boundary set |
|------|-------|-------|--------------|
| 1945 | 598 | 100% | 1945 (22 multi-member/University seats excluded) |
| 1950 | 625 | 100% | 1950 |
| 1951 | 625 | 100% | 1950 |
| 1955 | 630 | 100% | 1955 |
| 1959 | 630 | 100% | 1955 |
| 1964 | 630 | 100% | 1955 |
| 1966 | 630 | 100% | 1955 |
| 1970 | 630 | 100% | 1955 (same boundaries; GLC 1965 changed admin areas not parliamentary ones) |
| Feb 1974 | 635 | 100% | 1974 |
| Oct 1974 | 635 | 100% | 1974 (same positions as Feb 1974; only colouring differs) |
| 1979 | 635 | 100% | 1974 (16 constituency names changed) |
| 1983 | 650 | 100% | 1983 |
| 1987 | 650 | 100% | 1983 |
| 1992 | 651 | 100% | 1983 + Milton Keynes NE/SW split applied |
| 1997 | 659 | 100% | 1997 |
| 2001 | 659 | 100% | 1997 |
| 2005 | 646 | 100% | 1997/2005 hybrid (Scotland on 2005 boundary) |
| 2010 | 650 | 100% | 2010 |
| 2015 | 650 | 100% | 2010 |
| 2017 | 650 | 100% | 2010 |
| 2019 | 650 | 100% | 2010 |
| 2024 | 650 | 100% | 2024 (OI reference positions used directly) |

Every hex across all 22 elections is matched and coloured. There are no unmatched grey hexes.

---

## Pipeline

### 1. GeoJSON sources (`sources/geojson/`)

Constituency boundary GeoJSON files assembled from [parlconst.org](https://parlconst.org), one combined file per boundary set (England + Scotland + Wales + Northern Ireland). Nine boundary sets cover the 22 elections.

### 2. Hexjson packing — `scripts/pack.py`

`pack.py` reads a combined GeoJSON, computes centroids, assigns each constituency to its ONS region (nearest-centroid matching against the authoritative 2024 OI hexjson for English regions; source-path matching for Scotland, Wales, NI), then packs each region's seats into that region's hex footprint.

**Mask adjustment:** each region's 2024 mask shrinks or grows to match the current year's seat count. Shrink preserves anchor cells (Cornwall tip, SE coast junctions, Berkshire/Bucks tier); SW and SE shrink northward-first to preserve coastal shape.

**Assignment:** South East uses **Hungarian matching** (Jonker-Volgenant O(n³) linear assignment, `_lap_solve`), applied for all years 1945–2019. The globally-optimal solution prevents the "Berkshire cascade" where Reading/Wokingham/Spelthorne fall into the Kent/Brighton corridor because London blocks their ideal cells. SE coast seats (Brighton cluster, East Sussex) are fixed into target cells before the solver runs. All other regions use a greedy Dijkstra search (project seat to ideal q/r point, expand outward until free cell found, r-axis weighted 4×).

**Post-pack adjustments:**
- South Wales +2q shift for r=−34 to −38 in 1945–1970 (closes 2-cell gap with SW England)
- South Wales +2q shift for r=−35 to −37 in 1983–2005 (closes separate 2-cell gap)
- Oct 1974 regeneration: seed `output/19741.hexjson` from `output/1974.hexjson` before colouring (pack.py has no GeoJSON for year 19741)

**Island seats** (Orkney, Western Isles/Na h-Eileanan an Iar, Anglesey/Ynys Môn, Isle of Wight) are placed at fixed detached hex positions. `fill_holes()` eliminates interior gaps; a connectivity-repair pass reconnects any isolated mainland seats.

### 3. Results joining — `scripts/colour.py`

Joins election results to packed hexjson via a six-tier name-matching cascade (exact → compass-expanded → directional-collapsed → crosswalk → sorted-words → suffix). 100% match on all 22 elections.

**Winner determination:** highest share among `con`, `lab`, `lib`, `natSW`, `oth` columns. `natSW` = SNP (Scotland) or Plaid Cymru (Wales). NI seats from 1974 onward use `ni_results.json` (CAIN + Parliament data). Speaker seats coloured black.

**MANUAL_OVERRIDES:** ~90 seat-level overrides correcting `oth`-bucket misidentification:
- 1945: 11 National Liberal, 4 Independent, 2 Ind. Liberal, 1 Independent Labour, 1 Labour (data fix)
- 1945–1970: Communist, Common Wealth, ILP, Irish Labour (NILP), Republican Labour, Nationalist/APL/Unity, Sinn Féin, Protestant Unionist
- 1974F: Lincoln → Democratic Labour (Taverne); Bodmin → Liberal (Paul Tyler, 9-vote win; both shares round to 0.44)
- 1974O: Dunbartonshire E → SNP (22-vote win; both shares round to 0.312)
- 1997–2005: various Independents (Bell, Taylor/KHHC, Law/Blaenau Gwent)
- 2005: Galloway → Respect; 2010–2019: Lucas → Green; 2015: Carswell → UKIP

### 4. Preview — `scripts/generate_preview.py`

Builds `preview/index.html`: ~2.9 MB self-contained HTML with inline SVG for all 22 elections, year-selector buttons, arrow-key navigation, party legend (updates per election), and white region-boundary lines between adjacent hexes in different ONS regions.

---

## Special cases

### Northern Ireland
- **Pre-1974:** UUP MPs took the Conservative whip; colour correctly from `con_share`. Non-Unionist NI seats overridden via `MANUAL_OVERRIDES` (APL/Nationalist, Republican Labour, Sinn Féin, etc.).
- **1974 onward:** All NI votes appear in `oth`. Winners from `ni_results.json`. Key entries: 1974F FST = UUP (Harry West, not Frank Maguire — Maguire first won in October 1974); 1974O/1979 FST = Independent Republican (Maguire, `#1A6B3C`).

### Feb 1974 Liberal: 14 seats (not 13)
Bodmin was Paul Tyler's narrow Liberal win (20,283 vs 20,274 Conservative; both round to 0.44 share). Restored via `MANUAL_OVERRIDE`. The correct total is 14 Liberal seats in February 1974.

### South Wales geographic adjustment
Two separate post-pack q-shifts close visible map gaps between Wales and England:
- **1945–1970:** All Wales cells r=−34 to −38 shifted +2q eastward. Newport W, Cardiff W, Abertillery etc. now border Hereford, Stroud etc. (gap=0 at r=−34 to −37; gap=1 at r=−38 = Severn Estuary, correct).
- **1983–2005:** Wales cells at r=−35 to −37 shifted +2q. Caerphilly, Newport W, Cardiff S & Penarth now border Wyre Forest, Hereford, Stroud. Bridgend and Vale of Glamorgan (r=−38) intentionally excluded.

### 1945 London/SE structure
The 2024 centroid classifier assigns ~112 constituencies to London for 1945 boundaries (including all of Middlesex, outer Surrey, outer Essex). Experimental test scripts explore layout alternatives:
- **v1** (`pack_test_1945.py`): London capped at 75, 37 outer seats reclassified to SE.
- **v2** (`pack_test_1945_v2.py`): historical Southern/South Eastern regional split.
- **v3** (`pack_test_1945_v3.py`): London capped at 75, SE northern wrap + joint Hungarian. Issue: fills Thames Estuary.
- **v4** (`pack_test_1945_v4.py`): best current version — London grows to full ~112 seats, SE shrinks to its natural ~48, custom SW/SE anchors prevent interior holes, GOR overrides correct misassigned constituency region labels. 0 interior holes; clean boundaries; Thames Estuary preserved. Comparison viewer at `preview/1945_compare.html` (Standard / v3 / v4).

### 2010-base layout (session 8)
`scripts/pack_1945_on_2010base.py` maps 1945 seats onto the [Open Innovations 2010 hexjson](https://raw.githubusercontent.com/odileeds/hexmaps/master/maps/constituencies.hexjson) (650 hexes, odd-r, q:−17→13), stored at `reference/constituencies_2010.hexjson`. Regional treatments:
- **Scotland** (67 seats): 2010 SC block (57 mainland cells) expanded via `grow_mask` to 67, then Hungarian-assigned. Orkney & Shetland and Western Isles snap to fixed 2010 island positions.
- **NI** (6 seats): Hungarian selects the best 6 of 18 available 2010 NI cells.
- **England+Wales** (521 seats): global Hungarian across remaining 573 cells (52 empty).
- **Known issue**: London (+39 over 2010 capacity), NW (+4), NE (+2) overflow into the joint pool, cascading SW seats into Hampshire/Wales. Fix pending: per-region `grow_mask` expansion for each overflow region. Comparison viewer at `preview/1945_vs_2010base.html`.

### 1945 excluded seats
22 multi-member borough/University seats excluded from the hexmap: Antrim, Blackburn, Bolton, Brighton, City of London (both entries), Derby, Down, Dundee, Fermanagh & Tyrone, Norwich, Oldham, Preston, Southampton, Stockport, Sunderland; plus 7 University seats. These are documented in `reference/1945_outside_boundary_brief.md`.

---

## File structure

```
hexmaps/
├── scripts/
│   ├── pack.py                  # GeoJSON → hexjson packing (Hungarian + Dijkstra)
│   ├── colour.py                # hexjson + results CSV → coloured hexjson
│   ├── generate_preview.py      # builds preview/index.html
│   ├── validate.py              # sanity checks
│   ├── pack_test_1945.py        # 1945 test v1: London capped at 75 seats
│   ├── pack_test_1945_v2.py     # 1945 test v2: historical Southern/SE regional split
│   ├── pack_test_1945_v3.py     # 1945 test v3: SE northern wrap + joint London/SE Hungarian
│   ├── pack_test_1945_v4.py     # 1945 test v4: full natural London, clean region boundaries
│   ├── compare_test_1945.py     # side-by-side comparison viewer (standard / v3 / v4)
│   ├── pack_1945_on_2010base.py # 1945 seats mapped onto 2010 hex layout
│   └── preview_1945_2010base.py # comparison viewer for 2010-base approach
├── reference/
│   ├── 1918-2019election_results.csv        # main results (1945–2019 incl. 1974O)
│   ├── HoC-GE2024-results-by-constituency.csv  # 2024 results
│   ├── ni_results.json          # NI winners 1974F–2024
│   ├── speaker_seats.json       # Speaker and seat per election 1945–2024
│   ├── uk-constituencies-2024.hexjson  # authoritative OI 2024 layout (anchor)
│   ├── election_results_by_party.md    # full seat counts for all 22 elections
│   └── ...
├── sources/
│   └── geojson/                 # combined GeoJSON per boundary set
├── output/
│   ├── 1945.hexjson             # coloured hexjson, one per election
│   ├── 19741.hexjson            # October 1974
│   ├── 1945_test.hexjson        # experimental v1 (London cap)
│   ├── 1945_test_v2.hexjson     # experimental v2 (historical regions)
│   ├── 1945_test_v3.hexjson     # experimental v3 (SE northern wrap + joint Hungarian)
│   ├── 1945_on_2010base.hexjson # experimental (1945 mapped onto 2010 layout)
│   └── YYYY_join_report.txt     # name-match report per election
├── reference/
│   └── constituencies_2010.hexjson  # OI 2010 hex layout (650 hexes, odd-r)
└── preview/
    ├── index.html               # self-contained viewer (~2.9 MB)
    ├── 1945_compare.html        # 1945 regional comparison (standard / v1 / v3)
    └── 1945_vs_2010base.html    # 1945 standard vs 2010-base comparison
```

---

## Known remaining gaps

- **Spelthorne (1997–2019):** Projects to q≈60 but London occupies q=59–67 at r=−40 for those years; forced to q=68 (east corridor). Correct latitude; wrong column. Not worth further fixing.
- **Monmouth (Wales):** ~1.7° too far west across all elections. Eastern Wales mask too narrow at that latitude.
- **1945 multi-member seats:** 22 excluded seats are documented but not shown as a separate annotated layer in the viewer.
- **1945 London/SE structure:** `pack_test_1945_v4.py` is the best current version (0 interior holes, Thames Estuary preserved, clean region boundaries) but not yet promoted to `output/1945.hexjson`. Minor remaining artefacts: Caerphilly 1 SW edge (Wales +2q shift), Watford at EM/EoE boundary.
- **2010-base regional overflow:** London (+39), NW (+4), NE (+2) overflow the joint England+Wales pool, displacing SW/SE seats. Per-region `grow_mask` fix pending.
