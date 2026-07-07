---
type: schema
title: Elections data
description: Schema of data/elections/<id>.json — per-election metadata and party results.
tags: [data-model, elections, schema]
timestamp: 2026-06-29T00:00:00Z
---

# Elections (`data/elections/<id>.json`)

One file per general election. **Election ids** are the year as a string
(`"1945"`…`"2024"`), with the two 1974 elections as **`feb1974`** and **`oct1974`**
(note: some older data/scripts use `1974 (1)`/`1974 (2)` or internal hex year
`19741` for October — see [pipelines/hexmaps](../pipelines/hexmaps.md)).

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
  "partyResults": [ … ]
}
```

- `winner`, `pm`, `outgoingPm` use **party ids / names**; party ids are canonical
  across the site (see [party-colours](./party-colours.md)).
- `extraManifestoParties` lists parties that have a manifesto on file but few/no seats
  (e.g. `respect`, `ssp` for 2005) so they still surface in the UI. Adding one of these
  is a multi-touch change — see the worked example in
  [content-state/manifesto-coverage](../content-state/manifesto-coverage.md) and the
  log entry for the Respect/SSP additions.
- `election-vote-totals.json` holds the **national** vote totals/percentages keyed by
  year then party id; keep it consistent with `partyResults` seat counts.

## Related national tables
Per-nation Westminster results (England/Wales/Scotland/NI, 1918–2024) live in `data.js`
as `westminsterResults` arrays and render on `/nation/<name>` pages. Column structure
differs per nation (e.g. NI splits Unionist/Nationalist pre-1974, UUP/SDLP/DUP/Sinn
Féin from 1974). Sources: HC Library CBP-7529 (1918–2019) and CBP-10009 (2024).
