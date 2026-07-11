---
type: schema
title: Elections data
description: Where general-election metadata lives (js/data.js + data/elections/*.json) and how manifesto extras are wired.
tags: [data-model, elections, schema]
timestamp: 2026-07-11T00:00:00Z
---

# Elections

## Two copies — keep in sync

| Source | Role |
|---|---|
| `js/data.js` → `ELECTIONS` | **Runtime** for SPA election / party / manifesto pages (`getElection`) |
| `data/elections/<id>.json` | Per-election JSON on disk; primed into cache / available for fetch; keep aligned with `ELECTIONS` |

**Election ids** are the year as a string (`"1945"`…`"2024"`), with the two 1974
elections as **`feb1974`** and **`oct1974`**.

When editing manifesto wiring or results, update **both** places (or regenerate one
from the other deliberately). SEO parsing reads `ELECTIONS` from `js/data.js`
(`scripts/build-seo-data.py`).

## Top-level fields (observed)
```json
{
  "id": "1966",
  "year": 1966,
  "displayYear": "1966",
  "date": "31 March 1966",
  "winner": "labour",
  "pm": "Harold Wilson",
  "outgoingPm": "Harold Wilson",
  "totalSeats": 630,
  "summary": "…",
  "highlights": ["…", "…"],
  "youtubeId": "",
  "extraManifestoParties": [],
  "partyResults": { },
  "results": [ … ]
}
```

- `winner`, `pm`, `outgoingPm` use **party ids / names**; party ids are canonical
  across the site (see [party-colours](./party-colours.md)).
- `extraManifestoParties` lists parties that have a manifesto on file but few/no seats
  (e.g. `green` for 1979/1983 Ecology Party scans) so they still surface in the
  manifesto grid. Adding one is a multi-touch change — see
  [manifestos-index](./manifestos-index.md).
- Display labels for cards must use `getPartyName(pid, election.year)` —
  [party-names](./party-names.md).
- `election-vote-totals.json` holds the **national** vote totals/percentages keyed by
  year then party id; keep it consistent with `results` seat counts.

## Related national tables
Per-nation Westminster results (England/Wales/Scotland/NI, 1918–2024) live in `data.js`
as `westminsterResults` arrays and render on `/nation/<name>` pages. Column structure
differs per nation (e.g. NI splits Unionist/Nationalist pre-1974, UUP/SDLP/DUP/Sinn
Féin from 1974). Sources: HC Library CBP-7529 (1918–2019) and CBP-10009 (2024).
