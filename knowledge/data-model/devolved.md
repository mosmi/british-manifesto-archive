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
(e.g. `2021.json`, `gla-2024.json`, `lcc-1955.json`). Election files carry
results, summaries, and (where available) a `manifestos` array.

Hex cartograms for devolved legislatures live alongside under `data/hex/`
(e.g. `data/hex/stormont/`, `data/hex/holyrood/`).

Devolved manifestos are the largest remaining transcription gap (see
[content-state/manifesto-coverage](../content-state/manifesto-coverage.md)).

## European Parliament
`data/devolved/euro/` holds UK EP election results 1979–2019. Party groupings for
maps and navigation use **alliance families** (`sand`, `epp`, `renew`, `greensefa`,
`ecr`, …) defined in `js/data.js` (`EURO_ALLIANCE_PARTIES`). Individual minor
parties link to `/devolved/euro/other-parties`.

## Co-operative Party
Holyrood and Senedd Co-op representation counts have a strict display rule — see
[page-rules/cooperative-party](../page-rules/cooperative-party.md).
