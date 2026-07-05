# Hexmaps handoff — updated output

This note responds to your match-rate report and describes the fixes made. The revised `output/` directory is attached.

---

## What was fixed

### 1. Southend West missing from 1997–2005 (was: 658–645/659–646)

The parlconst.org 1997 boundary GeoJSON had one feature with `Name: null`. It was always geometrically present — its centroid is at lon=0.650, lat=51.552, which is Southend-on-Sea. It has been identified as Southend West and renamed `Southend W` in the source GeoJSON and in the 1997, 2001, and 2005 hexjsons. Those three years now match 100%.

### 2. Morecambe & Lunesdale misspelled in 2010–2019 (was: 649/650)

The 2010 parlconst.org GeoJSON spelled the constituency `Morcambe & Lunesdale` (missing 'e'). Our own joining code handled this silently via a crosswalk entry, so the hexjsons were always correctly coloured — but the hex *name* carried the typo, which is why your matcher couldn't find it. The source GeoJSON and all 2010, 2015, 2017, and 2019 hexjsons have been corrected to `Morecambe & Lunesdale`. Those years continue at 100%.

### 3. Milton Keynes 1992 — geometry fix applied (was: 649/650 with wrong seat count)

The 1992 election was fought on the 1983 boundaries except that Milton Keynes was split mid-term into two seats: **Milton Keynes North East** and **Milton Keynes South West** (UK total: 651 seats, not 650). The previous hexjson had a single `Milton Keynes` hex, which was wrong both in seat count and in being uncoloured.

Fix applied:
- Wellingborough shifted one step west `(60,−32) → (59,−32)` into a free cell
- Northampton N shifted one step west `(61,−32) → (60,−32)` into the vacated slot
- `Milton Keynes SW` placed at the original MK position `(61,−33)`
- `Milton Keynes NE` placed at `(61,−32)`, directly north of SW — geographically consistent with the North East / South West naming

Both seats colour **Conservative** (51.6% and 46.6% Con share respectively). 1992 now matches 651/651 (100%).

### 4. Derby South missing from 1950 and 1951 (was: 624/625)

Derby South was not listed in the 1918–2019 results CSV for either election. Results were sourced from the Parliament API (election IDs 15044 and 15669): Labour hold both years, won by Philip Noel-Baker. The hex is now coloured Labour (`#E4003B`). A `MANUAL_OVERRIDES` entry in `colour.py` ensures this survives future re-runs of the colouring script. Both years now match 625/625 (100%).

---

## Current state of all output files

| Year | Hexes | Match | Notes |
|------|-------|-------|-------|
| 1945 | 599 | 100% | Single-member territorial seats only; 22 multi-member/University seats not in hexjson |
| 1950 | 625 | 100% | Derby S sourced from Parliament API (Labour hold) |
| 1951 | 625 | 100% | Derby S sourced from Parliament API (Labour hold) |
| 1955 | 630 | 100% | |
| 1959 | 630 | 100% | |
| 1964 | 630 | 100% | |
| 1966 | 630 | 100% | |
| 1970 | 630 | 100% | |
| 1974 | 635 | 100% | Feb 1974 (election key: 1974F) |
| 1979 | 635 | 100% | |
| 1983 | 650 | 100% | |
| 1987 | 650 | 100% | |
| 1992 | **651** | 100% | MK split applied — NE at (61,−32), SW at (61,−33) |
| 1997 | 659 | 100% | Southend W fixed |
| 2001 | 659 | 100% | Southend W fixed |
| 2005 | 646 | 100% | Southend W fixed; Scotland on 2005 boundary (59 seats not 72) |
| 2010 | 650 | 100% | Morecambe fixed |
| 2015 | 650 | 100% | Morecambe fixed |
| 2017 | 650 | 100% | Morecambe fixed |
| 2019 | 650 | 100% | Morecambe fixed |
| 2024 | 650 | 100% | Sourced from HoC Library CSV (separate from the 1918–2019 CSV) |

Every hex across all 21 elections is now matched and coloured. There are no grey `UNMATCHED` hexes.

---

## Hex data schema

Each hex in the hexjson has:

```json
{
  "q": 61,
  "r": -33,
  "n": "Milton Keynes",
  "region": "E12000004",
  "colour": "#0087DC",
  "party": "Conservative"
}
```

- `q`, `r` — odd-r offset coordinates, pointy-top
- `n` — internal name from the source GeoJSON (may differ from the hex key — ignore `n`, use the key)
- `region` — ONS region code (E12000001–E12000009 for English regions, W92000004 Wales, S92000003 Scotland, N92000002 Northern Ireland)
- `colour` — hex colour string, Wikipedia party colour convention
- `party` — canonical party name (see list below)

**Party names used:**

| Party | Colour |
|-------|--------|
| Conservative | #0087DC |
| Labour | #E4003B |
| Liberal | #FFD700 |
| Alliance | #FFD700 |
| Liberal Democrats | #FAA61A |
| SNP | #FDF38E |
| Plaid Cymru | #008672 |
| UKIP | #6D3177 |
| Reform UK | #1EB8D0 |
| Green | #02A95B |
| DUP | #D46A4C |
| UUP | #48A5EE |
| Sinn Féin | #326760 |
| SDLP | #2AA82C |
| Alliance NI | #F6CB2F |
| Vanguard | #FF8C00 |
| Ulster Popular Unionist | #FFDEAD |
| UK Unionist Party | #660066 |
| Independent Unionist | #AADFFF |
| TUV | #0C3A6B |
| Speaker | #000000 |
| Independent | #DCDCDC |
| Other | #AAAAAA |
`Liberal` = pre-1983; `Alliance` = 1983 and 1987; `Liberal Democrats` = 1992 onward.

---

## Boundary set per election (which hexjson to use for shared boundaries)

| Election(s) | Boundary | Hexes |
|---|---|---|
| 1945 | 1945 | 599 |
| 1950, 1951 | 1950 | 625 |
| 1955, 1959, 1964, 1966, 1970 | 1955 | 630 |
| 1974 (Feb), 1979 | 1974 | 635 |
| 1983, 1987 | 1983 | 650 |
| 1992 | 1983 + MK split | 651 |
| 1997, 2001 | 1997 | 659 |
| 2005 | 1997/2005 hybrid | 646 |
| 2010, 2015, 2017, 2019 | 2010 | 650 |
| 2024 | 2024 | 650 |

Elections sharing a boundary have identical hex positions — only `colour` and `party` change between them.
