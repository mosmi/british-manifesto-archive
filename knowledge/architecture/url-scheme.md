---
type: decision
title: Singular URL scheme
description: Canonical public URLs use singular hubs (election, party, nation, manifesto). Westminster items stay year-only; other chambers are prefixed. Implemented 6 September 2026.
tags: [architecture, urls, redirects, ia]
timestamp: 2026-09-06T00:00:00Z
---

# Singular URL scheme

**Status:** implemented 6 September 2026 (Batch 4). `_redirects` 301s, regenerated `sitemap.xml` / `data/seo.json` / `catalog.jsonld`, SPA + middleware routes, and the four-slot header shipped together. The `/manifesto` cover wall shipped the same day ([manifesto-hub](../design/manifesto-hub.md)) — not a fifth header item.

Overrides the Sep 2026 forensic audit’s *plural* normalisation
(`/elections/1997`, `/parties/labour`). Pillar words are **singular**:
`election`, `party`, `nation`, `manifesto`.

Filesystem `/manifestos/<electionId>/<partyId>/` stays **plural**. That is the
asset tree, not a page URL.

This path scheme ships with the four-slot header in
[nations-vs-devolved](../design/nations-vs-devolved.md): Elections, Parties,
Nations, About. `/devolved` 301s onto `/election/…`.

## Westminster stays unmarked

Do **not** make `/election/westminster/1997` the canonical UK general-election
URL.

| Shape | Role |
|---|---|
| `/election/1997` | Canonical GE item (also `feb1974`, `oct1974`) |
| `/election/westminster` | GE **index** (today’s `/elections` timeline) |
| `/election/westminster/1997` | Alias only → 301 `/election/1997` |
| `/election/holyrood/2021` | Canonical chamber item |

Year-only GE ids never collide with chamber slugs (`holyrood`, `senedd`,
`stormont`, `london`, `euro`, plus index slug `westminster`). The router rule
is: known chamber slug → chamber routes; otherwise a Westminster election id.

Prefixing every GE would 301 the most-cited URLs on the site, and would force
`/manifesto/westminster/1997/labour` to match. Manifesto pages already use the
same unmarked/prefixed split (`/manifesto/1997/labour` vs
`/manifesto/london/2000/livingstone`). Keep that parallel.

## Canonical map

| Today | Canonical | Notes |
|---|---|---|
| `/elections` | `/election/westminster` | Same GE timeline content |
| `/election/1997` | **unchanged** | Unmarked Westminster item |
| `/election/feb1974`, `/election/oct1974` | **unchanged** | Not a four-digit year |
| `/devolved` | `/election` | Merged all-chambers hub |
| `/devolved/holyrood` | `/election/holyrood` | Chamber portal |
| `/devolved/holyrood/2021` | `/election/holyrood/2021` | |
| `/devolved/holyrood/other-parties` | `/election/holyrood/other-parties` | Same for senedd, stormont, euro |
| `/devolved/senedd/…` | `/election/senedd/…` | |
| `/devolved/stormont/…` | `/election/stormont/…` | |
| `/devolved/london/2000` | `/election/london/2000` | Year-only London ids already |
| `/devolved/euro/…` | `/election/euro/…` | Keep data id `euro` |
| `/parties` | `/party` | Hub |
| `/parties/all` | `/party/all` | Filterable index; collapsing into `/party` is a later call (audit 2.9) |
| `/party/labour` | **unchanged** | |
| `/others` | `/party/other` | |
| `/nation/europe` | `/party/european-groups` | Europe is not a nation (audit 2.5) |
| `/nations` | `/nation` | Hub |
| `/nation/england` (and wales, scotland, `northern-ireland`) | **unchanged** | |
| `/manifestos` | `/manifesto` | Cover wall; not `/manifesto/all` |
| `/manifesto/1997/labour` | **unchanged** | |
| `/manifesto/london/2000/livingstone` | **unchanged** | |
| `/about` | **unchanged** | |

Optional alias (same release): `/election/westminster/:id` → `/election/:id`.

Planned **new** route (not a rename): `/search` (audit 2.7). Implemented in
Batch 5 (`/search?q=` + `mode=catalogue|fulltext`).

The `/manifesto` cover wall is also a **new** route (not a rename of the
reader). Implemented with [manifesto-hub](../design/manifesto-hub.md).
`/manifestos` (no trailing asset path) 301s onto it.

### Chamber slugs

| Slug | Legislature |
|---|---|
| `westminster` | UK House of Commons (index only; items are year-only) |
| `holyrood` | Scottish Parliament |
| `senedd` | Senedd Cymru |
| `stormont` | Northern Ireland Assembly |
| `london` | Mayor & Assembly (and LCC/GLC history) |
| `euro` | European Parliament (UK, 1979–2019) |

`european-groups` is a party-taxonomy page, not an election chamber.

## `_redirects` (301s before SPA 200s)

301s must sit **above** the existing 200 SPA fallbacks, same pattern as the
London `gla-`/`glc-`/`lcc-` rationalisation. Retarget those London legacy
lines in the same commit so they hop **once** to `/election/london/<year>`,
not via `/devolved/london/<year>`.

Keep `/party/brexit` → `/party/reform`.

```
# Singular hubs — 301s (once, with sitemap + seo.json)
/elections                      /election/westminster          301
/elections/                     /election/westminster          301
/election/westminster/*         /election/:splat               301
/parties/all                    /party/all                     301
/parties                        /party                         301
/parties/                       /party                         301
/parties/*                      /party/:splat                  301
/others                         /party/other                   301
/nations                        /nation                        301
/nations/                       /nation                        301
/manifestos                     /manifesto                     301
/manifestos/                    /manifesto                     301
/nation/europe                  /party/european-groups         301
/devolved                       /election                      301
/devolved/                      /election                      301
/devolved/*                     /election/:splat               301
```

Then SPA 200s for the new hubs (replace today’s `/elections`, `/parties`,
`/devolved`, `/nations`, `/others` 200s):

```
/election        /index.html  200
/election/       /index.html  200
/election/*      /index.html  200
/party           /index.html  200
/party/          /index.html  200
/party/*         /index.html  200
/nation          /index.html  200
/nation/         /index.html  200
/nation/*        /index.html  200
/manifesto       /index.html  200
/manifesto/      /index.html  200
/manifesto/*     /index.html  200
/about           /index.html  200
```

`/election/westminster/*` 301 must remain **above** `/election/*` 200.

## Same-commit checklist (when implementing)

- `js/app.js` router + every in-app `href`
- `functions/_middleware.js` path classification and SEO
- `scripts/build-sitemap.py`, `scripts/build-seo-data.py`
- `_redirects` (301s then 200s); local preview must mirror them
- London one-hop legacy 301s (pages, `/manifestos/london/gla-*` assets already year-only)
- OG **page** canonicals; `/og/devolved/…` files may stay until the
  [og-generator](../pipelines/og-generator.md) runbook is updated
- Do not rename on-disk `data/devolved/` or `manifestos/` in this pass
