---
type: reference
title: Period-correct party display names
description: How getPartyName() maps Liberal/Alliance/Lib Dem and Ecology/Green labels by election year.
tags: [data-model, parties, naming]
timestamp: 2026-07-11T00:00:00Z
---

# Period-correct party names

Canonical **party ids** stay stable (`libdem`, `green`, …). UI labels change with
election **year** via `getPartyName(id, year)` in `js/data.js`.

Always pass the election year into `getPartyName` / `partyLink` / manifesto cards.
Omitting `year` returns the modern `shortName`.

## Liberal lineage (`libdem`, `welshlibdem`, `scottishlibdem`)

| Years | Label |
|---|---|
| before 1983 | Liberal |
| 1983, 1987 | Alliance |
| 1988 onward | Liberal Democrats (or Welsh/Scottish Liberal Democrats) |

Pre-1988 seat colour also shifts to Liberal yellow (`#FFD700`) via `getPartyColor`.

## Green / Ecology lineage (`green`)

The Ecology Party is the organisational predecessor of today’s Green Party of
England and Wales. Same party id: `green`.

| Years | Label |
|---|---|
| before 1985 | Ecology Party |
| 1985 onward | Green Party |

Party page hero still uses the modern full name
(`Green Party of England and Wales`). Founded year on the party record is **1975**
(Ecology Party), with description covering PEOPLE → Ecology → Green Party → GPEW.

## Reform UK / Brexit Party lineage (`reform`)

The 2019 general-election manifesto is stored under party id `reform` (same
organisation after the 2021 relaunch). Period label:

| Years | Label |
|---|---|
| before 2021 | Brexit Party |
| 2021 onward | Reform UK |

Election pages may also set `manifestoPartyLabels: { reform: 'Brexit Party' }` as an
explicit override; `getPartyName` should make that redundant for year-aware UI.

The EP folder slug `manifestos/euro/2019/brexit/` is retained on disk, but
`PARTY_ALIASES.brexit → reform` so `/party/brexit` resolves to the Reform UK page
(and Cloudflare `_redirects` 301s it). Do not reintroduce a separate `PARTIES.brexit`
record.

### Centralised party (not territorial Lib Dem-style)

Unlike Labour/Conservative/Lib Dem territorial editions (`scottishlab`, `welshlibdem`,
…), **Reform UK keeps a single party id** (`reform`) for Westminster, Holyrood, and
Senedd. Mega-menu labels may read **Reform UK** / **Reform UK Scotland** /
**Reform UK Wales** but all three link to `/party/reform`. Do not invent
`scottishreform` / `welshreform` records.

Party breadcrumbs omit a nation crumb when `nation === 'england'` — that field is
the mega-menu **England & UK-wide** bucket (Labour, Conservatives, Reform UK, …),
not “England-only”. Territorial parties (`nation: scotland|wales|northern-ireland`)
still show `Home › Parties › {Nation} › {Party}`.

## Adding another lineage

1. Add a map beside `LIBERAL_LINEAGE_NAMES` / `GREEN_LINEAGE_NAMES` in `js/data.js`.
2. Branch inside `getPartyName`.
3. Document the cutover years here.
4. Use period-correct labels in `data/manifestos-index.json` entries for those years
   (e.g. `"Ecology Party Manifesto 1979"`).
