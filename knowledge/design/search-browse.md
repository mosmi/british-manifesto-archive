---
type: plan
title: Search and browse roadmap
description: Phased catalogue search and party browse work following the July 2026 UX audit.
tags: [design, search, ux]
timestamp: 2026-07-20T22:15:00Z
---

# Search and browse roadmap

## Phase 1 (done 2026-07-20)
Honest catalogue search overlay:
- Copy clarifies titles/metadata only (not full-text)
- Exact party-name boost + grouped results
- Example queries, richer zero-results, keyboard hints
- Footer link → [`/party/all`](https://www.manifestos.org.uk/party/all)
- Also fixed `/elections` hard-navigation 308→`/` recovery in middleware
  (superseded in Batch 4: `/elections` 301s to `/election/westminster`)

## Phase 2 (updated 2026-07-20)
Filterable party browse on **`/party/all`**:
- Hue spectrum strip (hover expands a bar and names the party)
- Page search box + try chips
- Left sidebar filters: colour, Nation / Europe (no “Others”), Party founded,
  Status, Contested, Documents
- Contested merges curated `contests[]`, Westminster results, and archive docs —
  see [party-contests](../data-model/party-contests.md)
- Shareable query params (`?q=Reform&colour=teal&founded=2010…`)
- Hub intros use about-style **inline prose links** (not arrow CTAs)

## Phase 3 (done 2026-07-20)
Labelled **Full text** mode in the search overlay (distinct from Catalogue):
- Mode toggle: Catalogue | Full text (session-sticky)
- Lazy-loads [`data/fulltext-index.json`](../pipelines/fulltext-index.md) (inverted index over `manifesto.md`)
- Results link to manifesto readers with excerpts fetched for top hits
- Honest empty states that cross-link between modes
- Rebuild: `python3 scripts/build-fulltext-index.py` after transcription changes;
  `python3 scripts/build-fulltext-index.py --check` reports if the index is stale.
  Meta file cache-busts the large index without an assets bump.

## Phase 4 (done 2026-07-21) — UX audit Wave 1 search polish
- Catalogue zero-results: **Did you mean…?** chips from lightweight edit-distance
  matches on party / election / portal / nation titles and aliases (tokens ≥4 chars;
  distance 1–2). Full-text mode is not fuzzy-matched.
- `/elections` hub: middleware **short-circuits** to the SPA shell (asset layer
  still 308→`/` on live until deploy); `_redirects` keeps `/elections` and
  `/elections/` → `/index.html` 200.

## Phase 5 (2026-09-06) — crawlable `/search` (audit 2.7)

Shareable `/search?q=` (+ `mode=fulltext`) as a first-class SPA page. One
Catalogue / Full text toggle lives in the page form (the overlay keeps its own).
⌘K remains for quick lookup; its footer links to the search page. Full-text
snippets keep original case. `SearchAction` is on the site graph once this
route exists. See [structured-data](../architecture/structured-data.md).

The cover wall at [`/manifesto`](./manifesto-hub.md) is a **filter** of titles,
parties and years, not a second search box. Full-text stays on `/search`.
