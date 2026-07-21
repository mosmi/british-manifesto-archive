---
type: reference
title: Full-text search index
description: How data/fulltext-index.json is built and kept in sync when manifesto.md files change.
tags: [pipeline, search, fulltext]
timestamp: 2026-07-20T22:20:00Z
---

# Full-text search index

Client **Full text** search (search overlay mode) uses a precomputed inverted
index over every `manifestos/**/manifesto.md` transcription.

## Artefacts

| File | Role |
|---|---|
| [`data/fulltext-index.json`](../../data/fulltext-index.json) | Inverted index (~2 MB): `docs[]` + `inv` |
| [`data/fulltext-meta.json`](../../data/fulltext-meta.json) | Small `{ generated, docCount, fingerprint }` for cache-bust + staleness |

The search client loads **meta first**, then
`fulltext-index.json?v=<generated>`, so a rebuild is picked up without bumping
`ASSETS_VERSION` for this data alone. Snippets are fetched live from the matching
`.md` files for the top hits (not stored in the index).

## What gets indexed

The builder **walks the filesystem** (`manifestos/**/manifesto.md`). New or
edited transcriptions are included on the next rebuild even before you add a
[`manifestos-index.json`](../data-model/manifestos-index.md) row.

**Catalogue labels improve titles when present.** Each index hit stores
`l` from `manifestos-index.json`’s `label` when the `(electionId, partyId)` pair
matches. Without a catalogue row, the builder falls back to
`{partyId} {electionId}` (e.g. `bnp 1992`). Catalogue (title) search and party
pages still need the catalogue entry for proper listing; full-text mode only
needs the `.md` file on disk plus an index rebuild.

The build report prints `missingCatalogueLabels` when any fallback titles were
used — a handy reminder to finish wiring.

## Rebuild (required after transcription changes)

```bash
python3 scripts/build-fulltext-index.py
```

Check whether a rebuild is needed (exit `1` = stale):

```bash
python3 scripts/build-fulltext-index.py --check
```

This is part of transcription **Phase 5** — see
[transcription](./transcription.md#phase-5-site-rebuild--indexing) and the
[manifestos checklist](../data-model/manifestos-index.md#adding-a-manifesto--checklist).

Typical batch finish line:

```bash
python3 scripts/build-pdf-sizes.py
python3 scripts/build-latest-additions.py
python3 scripts/build-seo-data.py
python3 scripts/build-sitemap.py
python3 scripts/build-fulltext-index.py   # ← full-text mode
```

Commit both `fulltext-index.json` and `fulltext-meta.json` with the new
`manifesto.md` files.

## Related

- [design/search-browse](../design/search-browse.md) — Catalogue vs Full text modes
- [transcription](./transcription.md) — producing `manifesto.md`
