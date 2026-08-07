---
type: schema
title: Devolved elections data
description: Data for Holyrood, Senedd, Stormont, London and European Parliament elections under data/devolved/.
tags: [data-model, devolved, holyrood, senedd, stormont, london, euro]
timestamp: 2026-07-05T00:00:00Z
---

# Devolved (`data/devolved/`)

Subfolders per legislature / portal (see `DEVOLVED_PORTALS` in `js/data.js`):

| Folder | Portal | JS module |
|---|---|---|
| `holyrood/` | Scottish Parliament | `js/holyrood.js` |
| `senedd/` | Senedd Cymru | `js/senedd.js` |
| `stormont/` | Northern Ireland Assembly | `js/ni.js` |
| `london/` | Mayor & Assembly (+ LCC/GLC history) | `js/london.js` |
| `euro/` | European Parliament (UK, 1979–2019) | `js/euro.js` |

Each folder has an `index.json` (election list) and one JSON file per election
(e.g. `2021.json`, `2000.json`, `1955.json`). London uses **year-only** ids
(aligned with Holyrood/Senedd); era is carried by the `body` field
(`gla` | `glc` | `lcc`). Election files carry results, summaries, and (where
available) a `manifestos` array.

Hex cartograms for devolved legislatures live alongside under `data/hex/`
(e.g. `data/hex/stormont/`, `data/hex/holyrood/`).

Devolved manifestos are the largest remaining transcription gap (see
[content-state/manifesto-coverage](../content-state/manifesto-coverage.md)).

## London election ids & URLs
- Election JSON: `data/devolved/london/<YYYY>.json` with `"id": "<YYYY>"` and
  `"body": "gla"|"glc"|"lcc"`.
- Public URLs: `/devolved/london/2000`, `/manifesto/london/2000/livingstone`.
- Legacy prefixed URLs (`/devolved/london/gla-2000`, …) **301** to year-only
  via `_redirects` and `functions/_middleware.js`.

## London mayoral `manifestos[]` shape
Each GLA manifesto entry uses an explicit **`id`** equal to the folder name
under `manifestos/london/<YYYY>/`:
```json
{
  "id": "livingstone",
  "party": "independent",
  "candidate": "Ken Livingstone",
  "title": "Manifesto for London",
  "pdf": "/manifestos/london/2000/livingstone/manifesto.pdf",
  "cover": "/manifestos/london/2000/livingstone/cover.png"
}
```
| Field | Role |
|---|---|
| `id` | Canonical route + index `partyId` + folder (unique per election) |
| `party` | Affiliation for colour / results / party-page matching |
| `partyLabel` / `candidate` | Display (ballot label + mayoral name) |

Mayoral **results** rows in `mayor.candidates[]` use the same `party` /
`partyLabel` fields. When `party` resolves to a `PARTIES` id (via
`resolvePartyId`), the Mayoral Result table links the label to `/party/<id>`
through `londonPartyCell` → `devolvedPartyLink`. Label-only rows (no matching
party page) stay plain text.

Major parties: `id === party` (`libdem`, `labour`, …). Independents and personas:
`id` is the person/persona slug — never a colliding `independent` URL.
Cards and the viewer resolve via `londonManifestoRouteSlug` / `findDevolvedManifestoEntry`
in `js/london.js` and `js/app.js`. Text routes are registered in
[manifestos-index](./manifestos-index.md).

## European Parliament
`data/devolved/euro/` holds UK EP election results 1979–2019. Party groupings for
maps and navigation use **alliance families** (`sand`, `epp`, `renew`, `greensefa`,
`ecr`, …) defined in `js/data.js` (`EURO_ALLIANCE_PARTIES`). Individual minor
parties link to `/devolved/euro/other-parties`.

## Co-operative Party
Holyrood and Senedd Co-op representation counts have a strict display rule — see
[page-rules/cooperative-party](../page-rules/cooperative-party.md).
