---
type: decision
title: Manifesto cover wall
description: Canonical /manifesto is a filterable cover index, not a fifth header slot. Built from manifesto-assets.json; missing covers say “No cover scan”.
tags: [design, ia, manifesto, browse]
timestamp: 2026-09-06T00:00:00Z
---

# Manifesto cover wall (`/manifesto`)

**Status:** implemented 6 September 2026. Completes the singular URL scheme;
not a Batch 6 item.

## What it is

One cover-led index of every folder in [`data/manifesto-assets.json`](../../data/manifesto-assets.json).
Rendered by route-loaded `js/manifestos-hub.js`. It does **not** load chamber
modules. Tiles use `.manifesto-browse-*` so they never restyle election-page
`.manifesto-card` / `.manifesto-grid`.

The kicker is the **wall row count** from that JSON, the same unique-folder
total as homepage `ARCHIVE_COUNTS.manifestos` (619). `scripts/build-seo-data.py`
emits one `DigitalDocument` per on-disk folder; London is not listed twice.
`scripts/build-archive-counts.py` counts unique folder keys, not raw nodes.

## What it is not

- **Not a fifth header slot.** Header stays Elections / Parties / Nations /
  About ([nations-vs-devolved](./nations-vs-devolved.md)). Discover via footer,
  home Manifestos count, 404 destinations, and the guessable URL.
- **Not full-text search.** The page filter is titles / parties / years. Point
  people at [`/search`](./search-browse.md) for transcribed text. Do not add a
  third “Search the archive” box.
- **Not “not yet digitised”.** A missing cover is **“No cover scan”**. Availability
  facets are only **Read online** (`md`) and **Original PDF**.
- **Not `/manifesto/all`.** One hub at `/manifesto`. `/manifestos` 301s here;
  the plural filesystem tree stays the asset store.

## Conventions

Reuse `/party/all` browse: `data-browse-*`, `replaceState` query strings,
load-more (60). Cards call `getPartyName(id, year)`; the party facet list may
use `getPartyName(id)` (id bucket). Decade chips carry the year on phones;
the density strip is a **calendar-scale** sparkline (desktop only, hides
below 900px). Axis ticks are every decade from 1950–2020, plus **1945** and
**2026** centred on their bars. Hover or focus a bar to
read **year · count**; click filters the wall. European Parliament tiles use
`manifesto.png` (the euro cover filename), not `cover.png`.

JSON-LD is a **breadcrumb only** — do not emit a 619-item `ItemList`. OG for
the hub is the default site image (no `og/hub/manifestos.jpg`).

See [url-scheme](../architecture/url-scheme.md) and
[manifesto-viewer](../page-rules/manifesto-viewer.md) (reader vs hub).
