# UK Historical Election Hexmaps — Project Overview

A complete set of hex cartograms for every UK general election from 1945 to 2024, in [Open Innovations hexjson](https://open-innovations.org/projects/hexmaps/) format. Each election gets its own file in `output/`, with every constituency coloured by its winning party and white region-boundary lines overlaid.

The viewer is a single self-contained HTML file (`preview/index.html`) with year buttons, keyboard navigation, and a party legend that updates per election.

---

## Elections covered

| Year | Hexes | Boundary set | Notes |
|------|-------|--------------|-------|
| 1945 | 598 | 1945 | 22 multi-member/University seats excluded (stored in reference/) |
| 1950 | 625 | 1950 | |
| 1951 | 625 | 1950 | |
| 1955 | 630 | 1955 | |
| 1959 | 630 | 1955 | |
| 1964 | 630 | 1955 | |
| 1966 | 630 | 1955 | |
| 1970 | 630 | 1955 | Same boundaries as 1955–1966; GLC (1965) changed admin areas, not parliamentary boundaries |
| Feb 1974 | 635 | 1974 | February election (CSV key: 1974F; internal year: 1974) |
| Oct 1974 | 635 | 1974 | October election (CSV key: 1974O; internal year: 19741); same positions as Feb 1974 |
| 1979 | 635 | 1974 | Same boundaries as 1974; 16 constituencies renamed |
| 1983 | 650 | 1983 | |
| 1987 | 650 | 1983 | |
| 1992 | 651 | 1983 + MK split | Milton Keynes NE + SW added mid-Parliament |
| 1997 | 659 | 1997 | |
| 2001 | 659 | 1997 | |
| 2005 | 646 | 1997/2005 hybrid | Scotland on 2005 boundary (59 seats, not 72) |
| 2010 | 650 | 2010 | |
| 2015 | 650 | 2010 | |
| 2017 | 650 | 2010 | |
| 2019 | 650 | 2010 | |
| 2024 | 650 | 2024 | OI reference positions used directly |

Every hex across all 22 elections is matched and coloured. There are no grey UNMATCHED hexes.

**October 1974 implementation note:** October 1974 uses the same GeoJSON source and packed hex positions as February 1974. Only the colouring differs. In code it is identified by the integer `19741` to distinguish it from the February election (integer `1974`). The preview button is labelled "Oct 1974".

---

## File structure

```
hexmaps/
├── scripts/
│   ├── pack.py            # GeoJSON → hexjson packing
│   ├── colour.py          # hexjson + results CSV → coloured hexjson
│   ├── validate.py        # sanity checks
│   └── generate_preview.py  # builds preview/index.html
├── reference/
│   ├── 1918-2019election_results.csv        # main results (1945–2019, incl. 1974O)
│   ├── HoC-GE2024-results-by-constituency.csv  # 2024 results
│   ├── ni_results.json        # NI constituency winners 1974F–2024 (CAIN + Parliament)
│   ├── speaker_seats.json     # Speaker and seat per election 1945–2024
│   ├── regional_skeleton.json # per-region q/r bounds from 2024 OI hexjson
│   ├── uk-constituencies-2024.hexjson  # authoritative OI 2024 layout (anchor)
│   └── election_results_by_party.md    # party seat counts across all 22 elections
├── sources/
│   └── geojson/            # combined GeoJSON per boundary set (from parlconst.org)
├── output/
│   ├── YYYY.hexjson        # coloured hexjson, one per election
│   ├── 19741.hexjson       # October 1974
│   └── YYYY_join_report.txt
└── preview/
    └── index.html          # self-contained viewer (~2.9 MB, 22 elections)
```

---

## Data pipeline

### 1 · GeoJSON sources (`sources/geojson/`)

Constituency boundary GeoJSON files sourced from [parlconst.org](https://parlconst.org), assembled into per-boundary-set combined files covering England, Scotland, Wales and Northern Ireland. Nine boundary sets cover the 22 elections.

### 2 · Packing (`scripts/pack.py`)

Converts a combined GeoJSON into a hexjson. Algorithm overview:

1. Load constituency features, compute centroids, deduplicate.
2. Assign each constituency to an ONS region using nearest-centroid matching against the 2024 OI reference (for English regions) or source attribution (Scotland, Wales, NI).
3. Build the per-region **mask** from the authoritative 2024 OI hexjson, then shrink or grow it to match the current year's seat count.
4. Assign constituencies to mask cells. **South East (all years)** uses a globally-optimal **Hungarian matching** (`_lap_solve`, pure-Python Jonker-Volgenant O(n³)): builds a cost matrix (Δq)²+4·(Δr)² for all seat×cell pairs and finds the minimum-cost one-to-one assignment. For all other regions, the original **Dijkstra continuous-distance** search is used (project each seat to its ideal q/r point, expand cells in distance order until a free cell is found, with r-axis weighted 4×). SE coast seats (Brighton cluster, East Sussex) are fixed into target cells **before** the solver runs so they don't pollute the global optimum. Post-assignment **South Wales q-shifts** correct geographic placement (see Special cases).
5. Append **island seats** at fixed detached positions.
6. Run **fill_holes** to eliminate any interior gaps, followed by a **connectivity-repair** pass to reconnect any isolated seats the chain-moves may have created.

Key constraints baked into the algorithm:
- `PERMANENT_GAPS` — cells that are always empty: Lough Neagh `(43,−17)` and the 2024 IoW West position `(53,−45)`
- `REGION_ANCHOR_CELLS` — cells that are the last removed when a region's mask shrinks; preserves SW Cornwall chain, northern SW (Gloucester/Hereford belt), SE Bucks/Berkshire tier, and SE coast/junction cells. **Year-conditional for SE:** anchors (59,−35), (60,−35) and (59,−43) are dropped for year < 1974, because London's classifier-inflated mask surrounds those cells, making them isolated islands.
- `SHRINK_PREFER_NORTH` — SW and SE shrink northward-first, preserving their southern coastal shape
- `LONDON_GROW_R_FLOOR = −43` — London's mask never grows south of its 2024 boundary
- **Assignment ordering (non-Hungarian regions)** — "most extreme from r-centre first": peripheral seats claim cells before the dense middle tier

**⚠ pipeline order:** `pack.py` writes geometry-only hexjson (no colour fields), overwriting any previously coloured file. Always run `colour.py` after any `pack.py` call, even a verification run, or the output maps will be blank. For Oct 1974 specifically, seed `output/19741.hexjson` from `output/1974.hexjson` before running `colour.py --year 19741`, since pack.py has no 19741 entry.

### 3 · Colouring (`scripts/colour.py`)

Joins election results to the packed hexjson. Name matching uses a six-tier cascade:

1. Exact normalised match
2. Compass-expanded match (`N→north`, `NE→north east`, etc.)
3. Directional-collapsed match (`eastern→east`, etc.) — handles 1945 county-prefix forms
4. Crosswalk — ~80 explicit mappings for typos, renamed constituencies, old burgh forms
5. Sorted-words match — handles prefix/suffix reorderings
6. Suffix match — handles county-prefixed old CSV names

**Winner determination** uses the highest share among `con`, `lab`, `lib`, `natSW`, `oth` columns. `natSW` resolves to SNP (Scotland) or Plaid Cymru (Wales). NI seats from 1974 onward use a separate lookup (`ni_results.json`). Speaker seats are detected by name-matching and coloured black.

**MANUAL_OVERRIDES** handle seats where the CSV's catch-all `oth_share` column misidentifies the actual winner — principally: minor-party wins in 1945–1970 (Communist, ILP, Nationalist, Republican Labour, etc.) and modern independents (Bell, Galloway, Taylor, Law).

### 4 · Preview (`scripts/generate_preview.py`)

Builds `preview/index.html`: a self-contained page with inline SVG for all 22 elections, year-selector buttons, arrow-key navigation, and a per-election party legend. Region boundaries are drawn as white lines between adjacent hexes in different ONS regions.

---

## Party colours

| Party | Colour | Era |
|-------|--------|-----|
| Conservative | `#0087DC` | all years |
| Labour | `#E4003B` | all years |
| Liberal | `#FFD700` | pre-1983 |
| Alliance | `#FFD700` | 1983, 1987 |
| Liberal Democrats | `#FAA61A` | 1992+ |
| SNP | `#FDF38E` | 1970+ |
| Plaid Cymru | `#008672` | 1974+ |
| UKIP | `#6D3177` | 2015 |
| Green | `#02A95B` | 2010+ |
| Reform UK | `#1EB8D0` | 2024 |
| National Liberal | `#C8B400` | 1945 (11 seats) |
| Communist | `#EF0000` | 1945 (2 seats) |
| Common Wealth | `#7A1F2E` | 1945 (1 seat) |
| ILP | `#BF0000` | 1945, 1951 |
| Irish Labour | `#E4003B` | 1945–1951 (NILP, Jack Beattie) |
| Republican Labour | `#CC0000` | 1966–1970 (Gerry Fitt) |
| Nationalist | `#009A44` | 1945–1970 (Anti-Partition League, Unity) |
| Protestant Unionist | `#003366` | 1970 (Paisley; DUP precursor) |
| Independent Labour | `#E4003B` | 1945, 1951, 1970, Feb 1974 |
| Respect | `#FF4500` | 2005 |
| DUP | `#D46A4C` | 1974+ |
| UUP | `#48A5EE` | 1974+ |
| Sinn Féin | `#326760` | 1955, 1983+ |
| SDLP | `#2AA82C` | 1974+ |
| Alliance NI | `#F6CB2F` | 2010+ |
| Vanguard | `#FF8C00` | 1974 (William Craig; 3 seats Feb, 2 Oct) |
| Ulster Popular Unionist | `#FFDEAD` | 1983–1992 (James Kilfedder) |
| UK Unionist Party | `#660066` | 1997 (Robert McCartney) |
| Independent Unionist | `#AADFFF` | 1979 (Kilfedder) |
| TUV | `#0C3A6B` | 2024 |
| Speaker | `#000000` | varies |
| Independent Republican | `#1A6B3C` | Oct 1974, 1979 (Maguire, FST) |
| Democratic Labour | `#B05080` | Feb 1974 (Taverne, Lincoln) |
| Independent | `#DCDCDC` | varies |

---

## Special cases

### Northern Ireland — pre-1974
Ulster Unionist MPs took the Conservative whip from 1922 until the Sunningdale collapse in early 1974. UUP seats colour Conservative from the `con_share` column. Non-Unionist seats (Nationalist, Republican Labour, Sinn Féin, etc.) are individually overridden via `MANUAL_OVERRIDES`:

| Period | Notable non-Unionist NI seats |
|--------|------------------------------|
| 1945–1951 | Armagh, Fermanagh & S Tyrone, Ulster Mid (Anti-Partition League/Nationalist); Belfast W (Jack Beattie, Irish Labour/NILP) |
| 1955 | Fermanagh & S Tyrone, Ulster Mid (Sinn Féin; Clarke and Mitchell won from prison, both disqualified) |
| 1966–1970 | Belfast W (Gerry Fitt, Republican Labour, co-founder of SDLP) |
| 1970 | Antrim N (Ian Paisley, Protestant Unionist — DUP precursor); Ulster Mid (Bernadette Devlin, People's Democracy); Fermanagh & S Tyrone (Frank McManus, Unity) |

### Northern Ireland — 1974 onward
All NI votes appear in the CSV's `oth` bucket with no party breakdown. Actual winners sourced from CAIN and Parliament records, stored in `ni_results.json`. Key corrections:
- **1974F Antrim N**: DUP (Ian Paisley's first Westminster win)
- **1974F Fermanagh & S Tyrone**: **UUP** (Harry West, 26,858 votes vs Frank McManus Unity 16,229 — a large majority, not close). Frank Maguire first won FST in October 1974.
- **1974O / 1979 Fermanagh & S Tyrone**: **Independent Republican** (Frank Maguire). Almost never attended Westminster; his death in 1981 triggered the by-election won by Bobby Sands (Sinn Féin). Previously labelled "Independent"; corrected to the historically accurate "Independent Republican".
- **1974O Belfast S**: Vanguard → UUP (Robert Bradford).

### Speaker seats
`reference/speaker_seats.json` records the Speaker and constituency for every election 1945–2024. Speaker seats are coloured black.

Years where the sitting Speaker stood as **their former party** (not as Speaker):
- **1951** — Morrison became Speaker after the election; stood as Conservative
- **1983** — Weatherill stood as Conservative; elected Speaker when the new Parliament assembled
- **1992** — Weatherill retired; Boothroyd stood as Labour in West Bromwich West

### October 1974
The second 1974 general election produced a small Labour majority (319 seats). Key results vs February: Labour +22, Conservative −24, Liberal unchanged (13), SNP +4, PC +1. Frank Maguire (Independent Republican, Fermanagh & S Tyrone) retained his seat; Dick Taverne (Democratic Labour, Lincoln) lost his.

Hex positions are identical to February 1974 (same boundaries; internal year `19741`, file `output/19741.hexjson`). **Pipeline note:** `pack.py` has no `19741` GeoJSON entry. To regenerate: run `pack.py --year 1974`, copy `output/1974.hexjson` → `output/19741.hexjson`, then run `colour.py --year 19741`.

### 1992 — Milton Keynes split
The 1983 boundaries applied to 1992, except Milton Keynes was divided mid-Parliament into **Milton Keynes North East** and **Milton Keynes South West**, raising the total to 651. Both seats were won by the Conservatives.

### 1979 — boundary/name mismatch
The 1979 election used the same constituency *boundaries* as February 1974, but 16 constituencies were renamed. The crosswalk maps the 1974-boundary hex names to the 1979 CSV names.

### CSV `oth_share` catch-all
The CSV has no separate columns for minor parties (UKIP, Green, Communist, ILP, Nationalist, etc.); all their votes appear in `oth_share`. When `oth_share` is the highest column, `colour.py` normally returns "Other". `MANUAL_OVERRIDES` identify specific seats where the actual winner is known:

| Category | Elections | Examples |
|----------|-----------|---------|
| National Liberal | 1945 | Morris-Jones (Denbigh), Macpherson (Dumfries), Henderson-Stewart (Fife E), Holmes (Harwich), Butcher (Holland with Boston), Renton (Huntingdonshire), Maclay (Montrose District), Medlicott (Norfolk E), Lambert (South Molton), Beechman (St Ives), Barlow (Eddisbury) |
| Liberal (Ind.) | 1945 | Macdonald (Inverness), MacLeod (Ross & Cromarty) — broke from National Liberal group |
| Communist (CPGB) | 1945 | Gallacher (Fife W), Piratin (Stepney Mile End) |
| Common Wealth | 1945 | Millington (Chelmsford) |
| ILP | 1945, 1951 | Maxton, Stephen, McGovern (Glasgow seats) |
| Irish Labour / NILP | 1945–1951 | Beattie (Belfast W) |
| Republican Labour | 1966–1970 | Fitt (Belfast W) |
| Nationalist / APL / Unity | 1945–1970 | various NI non-Unionist seats |
| Protestant Unionist | 1970 | Paisley (Antrim N) |
| Sinn Féin | 1955 | Clarke, Mitchell (both abstentionist, won from prison) |
| Independent Labour | 1945, 1951, 1970, 1974 | Pritt (Hammersmith N 1945), Davies (Merthyr Tydfil), Milne (Blyth) |
| Independent | 1945, 1974–2005 | Lipson (Cheltenham), Mackie (Galloway), Kendall (Grantham), Brown (Rugby); Taverne (Lincoln), Bell (Tatton), Taylor (Wyre Forest), Law (Blaenau Gwent) |
| Respect | 2005 | Galloway (Bethnal Green & Bow) |
| UKIP | 2015 | Carswell (Clacton) |
| Green | 2010–2019 | Lucas (Brighton Pavilion) |

**Rhondda East 1945 data fix:** Labour (Mainwaring) won with 48.4%; oth_share (51.6%) exceeded lab_share due to Communist (Pollitt, 45.5%) and Plaid Cymru votes pooled into oth. Fixed via MANUAL_OVERRIDE → Labour.

---

## Fixes applied in session 2 (May 2026)

### Data / colour fixes

**Issue 5 — Speaker hex missing from six elections.** The name-matching used raw `normalise()` on abbreviated hex names (e.g. "Cardiff W", "Croydon NE", "West Bromwich W") which never matched the full-form Speaker seat names. Fixed by applying `expand_compass()` to both sides of the comparison, plus crosswalk lookup for the 1964 "Westmister" typo. Added "1983" to `party_not_speaker`.

**Issue 3 — Brighton Pavilion showing as "Other" (2010–2019).** Caroline Lucas's Green wins appear as `oth_share` → "Other". Fixed via `MANUAL_OVERRIDES` → Green for all four elections.

**Issue 4 — 2015 party count wrong.** Clacton (UKIP, Carswell) and Hartlepool (Labour; UKIP vote inflation) both misclassified. Fixed via `MANUAL_OVERRIDES`. 2015 now shows Labour 232, Green 1, UKIP 1.

### Pack algorithm fixes

**Issue 1 — Lough Neagh gap filled.** `fill_holes()` filled the NI interior gap. Fixed by adding `(43,−17)` to `PERMANENT_GAPS`.

**Issue 6 — London seats on south coast.** London's `grow_mask` expanded southward into SE territory. Fixed by adding `r_floor = −43`.

**Issue 11 — Cornwall becoming stubby.** The Cornwall tip cells were removed first during SW shrink. Fixed by `prefer_remove_north=True` for SW plus Cornwall anchor cells.

**Issues 10 & 12 — Isolated Liverpool seats.** `fill_holes()` chain-moves left Liverpool seats isolated. Fixed by adding a connectivity-repair pass after `fill_holes()`.

**Dijkstra geographic assignment.** Replaced BFS hop-count with Dijkstra continuous-distance to prevent inland seats jumping to coastal cells.

---

## Fixes applied in session 3 (May 2026)

### Island and isolation fixes
- Islands (Orkney, Anglesey, Western Isles) were being joined to the mainland by the connectivity-repair pass. Fixed by passing `island_buffer` into `fill_holes()` and skipping island seats in the repair.
- IoW moved from `(55,−48)` to `(54,−45)` (matching the 2024 IoW East position).

### Geographic assignment overhaul
- **"Most extreme from centre first" ordering** — replaced south-to-north. Seats projecting to either the northern or southern edge of the mask claim their cells before the dense middle tier.
- **4× r-axis weight** in Dijkstra — prevents row-jumping.
- **Extended anchor cells** — SE northern tier `(59,−35)`,`(60,−35)`,`(56,−38)`,`(57,−38)` (Bucks/Berkshire); SW northern tier `(51,−35)`…`(53,−37)` (Gloucester/Hereford).

### Systematic geographic audit
74 → 43 issues (>1.5° threshold). Key fixes: Buckingham/Milton Keynes/Banbury no longer at Sussex coast; Hereford/Tewkesbury at correct Gloucester row; Hampshire coast (Gosport, Southampton, Portsmouth) correctly placed; Bristol Channel distortion resolved.

---

## Fixes applied in session 4 (May 2026)

### October 1974 election added
The October 1974 general election was absent from the dataset. It is now included as the 10th election (internal year `19741`, file `output/19741.hexjson`). Hex positions are identical to February 1974 (same boundaries); only the party colouring differs. Results: Labour 319, Conservative 277, Liberal 13, SNP 10, PC 3, UUP 7, Vanguard 2, DUP 1, SDLP 1, Speaker 1, Independent 1.

### Northern Ireland data corrections
- **1974F Antrim N**: corrected from UUP to **DUP** — Ian Paisley's first Westminster seat
- **1974F Fermanagh & South Tyrone**: corrected from UUP to **Independent** — Frank Maguire (Independent Republican)
- **1974O added** to `ni_results.json` with October 1974 NI results

### Historical party reclassifications (MANUAL_OVERRIDES)
Nineteen seat-level overrides added to `colour.py` to replace generic "Other" labels with historically accurate party names for 1945–2005. New parties and colours added to `PARTY_COLOURS`:

| New party | Hex | Seats covered |
|-----------|-----|---------------|
| Communist | `#EF0000` | Gallacher (Fife W 1945), Piratin (Stepney Mile End 1945) |
| Common Wealth | `#7A1F2E` | Millington (Chelmsford 1945) |
| ILP | `#BF0000` | Maxton, Stephen, McGovern (Glasgow 1945, 1951) |
| Irish Labour | `#E4003B` | Beattie (Belfast W 1945–1951) |
| Republican Labour | `#CC0000` | Fitt (Belfast W 1966–1970) |
| Nationalist | `#009A44` | APL/Unity NI seats 1945–1970 (McSparran, Healy, McManus, Devlin) |
| Protestant Unionist | `#003366` | Paisley (Antrim N 1970) |
| Independent Labour | `#E4003B` | Davies (Merthyr Tydfil 1951/1970), Milne (Blyth 1974F) |
| Respect | `#FF4500` | Galloway (Bethnal Green & Bow 2005) |

Additional CSV-zero overrides: Armagh 1945 (Nationalist), Liverpool Scotland 1945 (Irish Nationalist), Rhondda W 1945/Ebbw Vale 1951 (Labour), several NI Conservative/Unionist seats with all-zero CSV data.

Sinn Féin corrected for 1955 (Fermanagh & S Tyrone, Ulster Mid — Philip Clarke and Tom Mitchell, who won from prison).

NI pre-1974 corrections also applied to 1950 and 1951: Anti-Partition League wins in Fermanagh & S Tyrone and Ulster Mid.

### `liberal_party_for_year` fix
The integer `19741` (October 1974) was treated as post-1987 by the year comparison, causing Liberal seats to be coloured "Liberal Democrats". Fixed by mapping `19741 → 1974` before the comparison.

### Party legend ordering
`generate_preview.py` PARTY_ORDER updated to include the new historical parties (Communist, Common Wealth, ILP, Irish Labour, Republican Labour, Nationalist, Protestant Unionist, Independent Labour, Respect) in a logical position between the Celtic parties and the NI parties.

### Reference document
`reference/election_results_by_party.md` created — full seat-count tables for all 22 elections, broken out by main parties, NI parties, and historical minor parties, with notes on each notable independent or minor-party winner.

---

## Fixes applied in session 5 (May 2026)

### Data / colour fixes

**Oct 1974 SNP count corrected (10 → 11).** Dunbartonshire East was a 22-vote SNP win (Margaret Bain, 15,551 vs Conservative 15,529). Both shares rounded to 0.312 in the CSV, and Python's `max()` broke the tie in favour of the `"con"` bucket (first in dict insertion order). Fixed via `MANUAL_OVERRIDE` for `("1974O", "Dunbartonshire E")` → SNP. Conservative seat count drops from 277 to 276.

**1945 "Other" seats fully resolved (19 → 0).** All 19 seats previously labelled "Other" in 1945 identified and classified via `MANUAL_OVERRIDES`:

| Party | Count | Seats |
|-------|-------|-------|
| National Liberal | 11 | Morris-Jones (Denbigh), Macpherson (Dumfries), Barlow (Eddisbury), Henderson-Stewart (Fife E), Holmes (Harwich), Butcher (Holland with Boston), Renton (Huntingdonshire), Maclay (Montrose District), Medlicott (Norfolk E), Lambert (South Molton), Beechman (St Ives) |
| Independent | 4 | Lipson (Cheltenham, "National Independent"), Mackie (Galloway, Ind. Unionist), Kendall (Grantham), W.J. Brown (Rugby) |
| Liberal | 2 | Macdonald (Inverness, Ind. Liberal), MacLeod (Ross & Cromarty, Ind. Liberal) |
| Independent Labour | 1 | D.N. Pritt (Hammersmith N, expelled from Labour 1940) |
| Labour (data fix) | 1 | Rhondda E — Mainwaring (Labour) won 48.4%; oth_share inflated to 51.6% by Communist (Pollitt) + Plaid Cymru votes pooled into oth bucket |

**National Liberal** added as a new party colour (`#C8B400`, dark gold) to `PARTY_COLOURS` and `PARTY_ORDER` in `colour.py` and `generate_preview.py`.

### Pack algorithm fix — SE cascade partially resolved (1983–2019)

**Root cause identified:** In 1983–2019, London held 84 seats (vs 75 in 2024) and occupied q=58–68 at rows r=−37/−40, splitting SE into two disconnected corridors — west (q=53–57, Berkshire/Hampshire) and east (q=67–72, Kent). Berkshire/Surrey seats projecting to the blocked middle cascaded south to whatever coastal cells were available, landing alongside the East Sussex coast seats.

**Fix:** `pack.py` now runs a post-assignment swap for SE in year ≥ 1983. `geographic_assign_region` is called with all seats in the pool (preserving the lat/lon projection calibration), then Eastbourne, Lewes, Bexhill & Battle, Hastings & Rye are swapped to their 2024 OI positions — (69,−45), (68,−45), (70,−44), (70,−43) — with whichever cascade seat landed there displaced to the East Sussex seat's natural position. The four East Sussex coast seats now consistently sit below London's south-east corner, matching the 2024 layout, across all 1983–2019 elections.

**Remaining:** Berkshire cascade (Wokingham, Reading W, Newbury, Spelthorne) still occurs at q=67–69, displacing Dartford and other Kent seats. Full fix requires a globally-optimal (Hungarian) assignment.

### SE Berkshire cascade fully resolved (1983–2019)

**Root cause:** London's large mask (84 seats, 1983–1992; 73–74 seats, 1997–2019) occupies q=58–68 in the r=−37 to −43 rows, splitting SE into a west corridor (q=53–57) and east corridor (q=67–72). Berkshire/Surrey seats project to q=58–66 but those cells are all London-occupied. The greedy Dijkstra assignment processed seats in order of latitudinal extremeness, so Berkshire seats (middle latitude, processed last) found the west corridor already full and cascaded east into the Kent corridor — Spelthorne to Brighton row, Dartford to East Sussex.

**Fix 1 — Hungarian matching (`_lap_solve`, Jonker-Volgenant):** `geographic_assign_region` gains a `use_hungarian=True` mode that solves the linear assignment problem globally. Cost metric: (Δq)² + 4·(Δr)² from each seat's linearly-projected ideal cell — same as the existing Dijkstra metric. Applied to SE for years 1983–2019. With global optimisation, Berkshire seats (projecting to q≈58–62) are assigned to west-corridor cells at cost ~9 rather than cascading to Kent cells at cost ~100+.

**Fix 2 — Pre-assignments before Hungarian:** Brighton cluster (Hove, Brighton Pavilion, Brighton Kemptown, Sussex Mid) and East Sussex coast (Eastbourne, Lewes, Bexhill, Hastings) are locked into their target cells and removed from the Hungarian pool BEFORE running the solver. Previously, these were post-assignment swaps that created displacement chains; the new approach prevents them from polluting the global optimum.

**Fix 3 — Junction anchors:** Three new `REGION_ANCHOR_CELLS` for SE: (58,−42) (junction between SE west corridor and London's SE corner), (68,−42) (junction between SE east corridor and London), (67,−44) (East Sussex coast row junction). Without these, the 1983 shrink removes them, creating interior holes that fill_holes patches via chain-moves through (67,−44), leaving a gap in the coast row.

**Result (1983 example):**
- Before: Spelthorne (66,−44) [Brighton corridor]; Reading W (68,−44) [Kent corridor]; Dartford (69,−44) [Brighton corridor]; Wokingham (60,−33) [too far north]
- After: Newbury (54,−40), Reading E (55,−40), Spelthorne (57,−40), Reading W (54,−39), Wokingham (55,−39), Berkshire E (56,−39) — all west corridor; Dartford (70,−39), Erith (69,−39), Medway (71,−39) — all Kent corridor

---

## Fixes applied in session 6 (May 2026)

### Brighton cluster fixed for 1983–1992

**Root cause identified:** `shrink_mask` scores cells adjacent to growing London with high `adj_benefit`, preferring their removal from SE's mask even when London can never absorb them (LONDON_GROW_R_FLOOR=−43). Cells at r=−44 (the Brighton/Hove coast row) adjacent to London's r=−43 row were being systematically removed, forcing Brighton Pavilion and Hove west into Hampshire.

**Fix 1 — r_floor exclusion:** When computing `growing_region_cells`, London's r=−43 cells (its floor row) are excluded. SE cells at r=−44 adjacent to London's r=−43 boundary no longer receive adj_benefit scores and are no longer preferentially freed.

**Fix 2 — Anchor cells:** `REGION_ANCHOR_CELLS["E12000008"]` extended with (59,−43) [Havant slot, still removed by adj_benefit from London r=−42 Dulwich] and (63–66,−44) [Brighton corridor safety pins].

**Fix 3 — Brighton pre-assignments (1983–1992 only):** `BRIGHTON_PREASSIGN_1983` added to `SE_COASTAL_PREASSIGN` logic for years ≤ 1992. Pre-assigns: Hove→(62,−44), Brighton Pavilion→(63,−44), Brighton Kemptown→(64,−44), Sussex Mid→(65,−44). Applied only for 1983–1992 because for 1997+ London shrinks and releases r=−43 cells, creating interior holes that fill_holes patches by pulling coast seats north; the extended mask handles Brighton naturally for those years without explicit pre-assignment.

**Result:** For all 1983–1992 elections, the Sussex coast now reads west→east: Portsmouth S(58), Arundel(59), Worthing(60), Shoreham(61), **Hove(62), Brighton Pavilion(63), Brighton Kemptown(64)**, Sussex Mid(65) — all at r=−44, all adjacent.

**Remaining:** Berkshire cascade (Wokingham, Reading W, Newbury, Spelthorne, Berkshire E) — these seats project to the middle gap (q=58–66) blocked by London, cascade east to q=66–69 displacing Kent seats. Dartford ends up in the Brighton corridor. Full fix requires Hungarian matching.

### Investigation — 1970 London geometry (false alarm)

The known gap "London positions approximate 1955 centroids (pre-GLC redraw)" was investigated and **closed as a false alarm**. The Greater London Council (established by the London Government Act 1963, effective 1965) reorganised local government but did not redraw parliamentary constituency boundaries. The 1970 election used the same boundaries as 1955, 1959, 1964, and 1966. Confirmed: 1966 and 1970 hexjson are byte-for-byte identical; 98/99 London hexes match directly to 1955 GeoJSON feature names. The `pack.py` comment "hybrid — London splice not yet applied" was removed. Parliamentary boundaries were frozen until the 1969 Boundary Commission review took effect in February 1974.

---

## Fixes applied in session 7 (May 2026)

### SE Berkshire cascade extended to all years 1945–2019

The Hungarian matching fix (session 5/6) was originally applied to SE only for 1983–2019. The same London-blocked cascade affects 1945–1979: Reading S/N, Newbury, Wokingham, Spelthorne all landed in the Kent/East Sussex corridor. Extended `use_hungarian = (region == "E12000008")` to all years (no year guard). Result: 1950–1970 Berkshire/Reading seats now correctly land in the west corridor (r=−38 to −40), Dartford/Gravesend in the Kent corridor.

### Pre-1974 SE anchor cells made year-conditional

Anchor cells (59,−35), (60,−35) [Aylesbury/Buckingham tier] and (59,−43) [coast slot west of London] caused isolated islands in 1945–1970. Root cause: for pre-1974 elections the centroid classifier assigns ~99 seats to London (including all outer-London pre-1974 constituencies), inflating London's mask and surrounding those cells on all sides. Fix: these three anchors are dropped for `year < 1974` via `SE_PRE74_DROP` applied in `pack_year`. Aylesbury and Buckingham now land in the main SE body at r=−36 to −37; Portsmouth Langstone at r=−44.

### City of London (2) excluded from 1945

The 1945 multi-member filter (`OUTSIDE_BOUNDARY_1945`) matched `"city of london"` but the GeoJSON feature was named `"City of London (2)"`. Added `"city of london (2)"` to the set. 1945 now has 598 hexes (was 599).

### South Wales q-shifts

Two independent post-pack coordinate adjustments that close visible gaps between Wales and England:

**1945–1970** (`year < 1974`): All Wales cells at r=−34 to r=−38 shifted +2q (east). Closes a 2-cell gap between South Wales (Newport W, Cardiff S, Abertillery, etc.) and SW England (Hereford, Stroud, Gloucester). After shift: rows r=−34 to −37 flush with England (gap=0); r=−38 (Cardiff Bay / Severn Estuary) has gap=1 — geographically correct. Adjacency to unshifted r=−33 (Ebbw Vale, Brecon & Radnor, Carmarthen, Pembroke) is preserved.

**1983–2005** (`1983 ≤ year ≤ 2005`): Wales cells at r=−35 to r=−37 shifted +2q. Closes a 2-cell gap between Caerphilly/Newport W/Cardiff S & Penarth and Wyre Forest/Hereford/Stroud. r=−38 (Bridgend, Vale of Glamorgan) intentionally excluded and unchanged.

### Party data corrections (Feb 1974)

- **Lincoln → Democratic Labour** (`#B05080`): Dick Taverne resigned from Labour in 1972, won a by-election as Democratic Labour in 1973, and held the seat in February 1974. Previously labelled "Independent"; corrected.
- **Bodmin → Liberal** (`#FFD700`): Paul Tyler (Liberal) won by 9 votes (20,283 vs 20,274 Conservative). Both round to 0.44 share; Python's `max()` broke the tie in favour of `"con"`. Fixed via `MANUAL_OVERRIDE`. This restores the correct February 1974 Liberal total of **14 seats** (was showing 13 due to this rounding error).
- **FST Feb 1974 → UUP**: `ni_results.json` previously had "Independent" for 1974F FST. Corrected to UUP (Harry West, 26,858 votes, comfortable majority over Frank McManus).

### NI: Independent Republican (Oct 1974 & 1979 FST)

Frank Maguire's correct designation is "Independent Republican" not plain "Independent". Updated in `ni_results.json` for `1974O` and `1979`. New colour `#1A6B3C` (dark green). Added to `PARTY_ORDER` in generate_preview.py.

### 1945 regional structure — experimental test scripts

Test scripts in `scripts/` explore alternative regional structures for 1945:
- `pack_test_1945.py` — **v1**: caps London at 75 (2024 size) by reclassifying the 37 most-peripheral London-classified seats as SE. Produces a visible gap to the north/NW of London.
- `pack_test_1945_v2.py` — **v2**: splits London+SE into three historical regions: **London LCC** (~43 seats, innermost LCC boroughs), **Southern** (~59 seats: Middlesex + Berkshire + Bucks + Oxon + Hampshire + IoW), **South Eastern** (~58 seats: Surrey + Kent + Sussex + outer south/east London suburbs). Starting masks carved from the combined 2024 London+SE cell pool.
- `pack_test_1945_v3.py` — **v3**: starts from v1 (London capped at 75, 37 reclassified to SE = 85 SE seats), then wraps SE's mask northward by claiming ALL freed East of England cells (r=−29 to r=−36, ~24 cells) as SE territory. Runs a **joint Hungarian assignment** across the combined London (75) + SE (85) = 160-seat pool. Issue: fills the Thames Estuary (SE claims cells that should be open coast north of London).
- `pack_test_1945_v4.py` — **v4**: removes the London cap and SE northern wrap; see Session 9 below.
- `compare_test_1945.py` — side-by-side comparison (standard / v3 / v4) as `preview/1945_compare.html`.

---

## Session 9: 1945 v4 — clean regional boundaries (June 2026)

### Motivation

v3's SE northern wrap filled the Thames Estuary (SE claimed freed East of England cells north of London). v4 fixes this by allowing London to grow to its full 1945 size (~112 seats), which naturally occupies the outer-London/Middlesex zone and keeps SE confined to its correct southern territory.

### Key changes in `pack_test_1945_v4.py`

**No London cap.** London grows from the 2024 mask (75 cells) to its full natural count (~112 seats), expanding northward into freed EoE cells. This correctly represents 1945 London including all Middlesex constituencies, and the Thames Estuary gap opens naturally (SE never claims cells north of London).

**SE shrinks to its 1945 size (~48 seats).** Custom anchor cells ensure:
- South coast bridge at r=−44 (q=55–70): Hampshire↔Sussex↔Kent connected south of London.
- Inner corridor (q=54–57, r=−37 to −42): fills the SW/London junction zone that would otherwise become 46+ interior holes.
- Kent corridor (q=68–72, r=−39 to −42).

**SW anchors.** Cornwall tip pinned; junction zone (q=51–53, r=−35 to −42) anchored so SW keeps its full geographic extent from Cornwall to Gloucester without shrinking from the north.

**London growth hint.** The r=−33 to −36 zone is added to `growing_region_cells` before EoE shrinks, so EoE preferentially removes its London-adjacent cells first. This gives London a clean eastward boundary (no alternating London/EoE zigzag at r=−33/−34).

**GOR polygon overrides.** Three 1945 constituencies whose centroids fall just inside the wrong modern GOR polygon are overridden before region bucketing:
- Uxbridge → London (centroid in EoE polygon; Middlesex constituency)
- Rochester, Gillingham → SE (centroid in EoE polygon; Medway/Kent constituency)
- Brigg → East Midlands (centroid in YH polygon; Lincolnshire constituency)

**Hungarian for London.** London now uses Hungarian matching (was greedy Dijkstra in the standard approach), improving placement of the 112 outer-London/Middlesex seats.

### Results

- 0 interior holes (was 46 before anchor fixes)
- Thames Estuary gap preserved: no SE cells north of r=−37 in the eastern corridor
- Edmonton, Hackney N, Thurrock: 0 boundary edges (fully within their correct regions)
- Enfield: 2 boundary edges with Hertfordshire/Essex (correct geography)
- Rochester, Gillingham: placed in Kent corridor (SE), not London territory
- Brigg: placed at EM/YH boundary, not as an isolated YH cell

### Remaining issues in v4

- **Not yet promoted to main `1945.hexjson`.** The standard output still uses `pack.py` with greedy Dijkstra for London. Promotion requires reviewing whether the v4 mask changes affect other elections (pack.py is shared across all 22 years).
- **Caerphilly 1 SW edge.** The +2q Wales shift brings Wales cells into direct adjacency with SW (Barnstaple borders Caerphilly after the shift). Minor visual artefact.
- **Watford placement.** Watford (Herts, EoE) ends up adjacent to East Midlands cells at the EM/EoE boundary. Geographically borderline.

---

## Session 8: 2010-base approach (June 2026)

### New approach: 1945 election on 2010 hex layout

`scripts/pack_1945_on_2010base.py` and `scripts/preview_1945_2010base.py` implement a fundamentally different layout strategy: instead of deriving hex positions from GeoJSON geography, use the [Open Innovations 2010 constituency hexjson](https://raw.githubusercontent.com/odileeds/hexmaps/master/maps/constituencies.hexjson) as fixed tile positions and map 1945 seats onto them.

**Reference file:** `reference/constituencies_2010.hexjson` — 650 hexes, odd-r, q:−17→13, r:−16→28.

**Algorithm:**
1. Compute geographic centroids for 2010 constituencies from the 2010 GeoJSON (name-matching with compass-abbreviation expansion; fallback to token-overlap; last-resort grid-distance proximity for any remaining unmatched).
2. Classify each 1945 seat by ONS region using `assign_region`.
3. Three regional treatments:
   - **Scotland (S92000003, ~67 seats):** 2010 SC cells (57 mainland + 2 island = 59) expanded using `grow_mask` to 67 mainland cells, biased toward the Central Belt centroid. Orkney & Shetland snaps to (−5, 28); Western Isles to (−8, 26). Hungarian assignment for all 67 Scottish seats within the expanded pool. The 2010 SC layout already captures Scotland's geography well (Central Belt at r=16–19, Highlands at r=22–26), so the expansion simply adds cells for the extra urban seats of 1945 (Glasgow, Edinburgh, Lanarkshire).
   - **Northern Ireland (N92000002, 6 seats):** Hungarian assignment of 6 seats into the best 6 of 18 available 2010 NI cells (q:−17 to −13, r:11–15). Londonderry/Foyle maps west, Belfast cluster in the centre, Armagh south.
   - **England + Wales (521 seats):** Linear projection to 2010 hex space + global Jonker-Volgenant Hungarian across the remaining 573 cells. Leaves 52 cells empty.
4. Output: `output/1945_on_2010base.hexjson`. Comparison viewer: `preview/1945_vs_2010base.html`.

**Known issue — regional overflow in England+Wales:** Regions where 1945 had more seats than 2010 cells (London +39, NW +4, NE +2) overflow into the joint England+Wales pool. London's 39 extra seats (Middlesex, outer Essex/Surrey) cascade into EA/SE cells, which in turn push SW seats (Dorset, Devon) into Hampshire and Wales cells. Fix pending: per-region `grow_mask` expansion for each overflow region before the joint English+Welsh assignment (same pattern as the Scotland fix).

---

## Remaining known gaps

- **Spelthorne (1997–2019)** — minor residual: Spelthorne projects to q≈60 but London still occupies q=59–67 at r=−40 in 1997–2019 (73 seats), forcing it to q=68 in the east corridor. It lands at the correct latitude (r=−40, Berkshire/Surrey tier) unlike the old cascade to r=−44. No further fix planned.
- **Monmouth (Wales)** — Consistently ~1.7° west of its correct position. Eastern Wales has a narrow mask at that latitude and the seat projects beyond available eastern cells.
- **1945 multi-member seats** — The 22 excluded multi-member/University seats are not yet displayed as a separate annotated section in the viewer.
- **Richmond (A) audit false positive** — The geographic audit flags Richmond (A) at distance 3.4° in 1950–1979; this is a false positive: Richmond (A) is the Yorkshire seat correctly packed into NE England; the audit's partial-name match finds Surrey's centroid instead.
- **1945 London/SE regional structure** — The standard 2024 centroid classifier assigns ~112 seats to London for 1945 (including all of Middlesex, outer Surrey, outer Essex), making London dominate the SE area. `pack_test_1945_v4.py` is the most complete experimental version (0 holes, clean boundaries, Thames Estuary preserved) but is not yet promoted to the main `output/1945.hexjson`.
- **2010-base England+Wales regional overflow** — London (+39 seats vs 2010 cells), NW (+4), NE (+2) overflow into the joint pool, cascading SW/SE seats geographically. Fix: per-region `grow_mask` expansion for each overflow region (analogous to the Scotland treatment already implemented).
