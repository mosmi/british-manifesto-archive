---
type: runbook
title: Homepage Latest Additions
description: Auto-generated data/latest-additions.json from the manifesto catalogue, ordered by git first-add date.
tags: [content, homepage, manifestos, pipelines]
timestamp: 2026-07-11T00:00:00Z
---

# Latest Additions (homepage)

The homepage carousel is driven by **`data/latest-additions.json`**, which is
**generated** — not hand-edited.

```bash
python3 scripts/build-latest-additions.py
```

## How it works
1. Collect catalogue entries from:
   - [`data/manifestos-index.json`](../data-model/manifestos-index.md) (Westminster / SPA)
   - `data/devolved/*/*.json` → `manifestos[]` (euro, holyrood, senedd, stormont, london)
2. Resolve each to a folder under `manifestos/` (must have `manifesto.pdf` and/or
   `manifesto.md`).
3. Rank by **first git Add** of that folder’s PDF (else markdown/cover). Falls back
   to filesystem mtime when git history is missing (e.g. not yet committed).
4. Write the top **12** cards (newest first).

Westminster entries link to `/manifesto/<electionId>/<partyId>` (`isPdf: false`).
Devolved/euro entries link to the PDF (`isPdf: true`).

## When adding manifestos
After updating the index / election wiring and covering the PDF, run:

```bash
python3 scripts/build-pdf-sizes.py
python3 scripts/build-latest-additions.py
```

(also listed in the [manifestos-index checklist](../data-model/manifestos-index.md)).

Commit the regenerated `data/latest-additions.json` with the new PDFs so production
picks it up.

## Runtime
`js/app.js` → `loadLatestManifestos()` fetches the JSON. Party labels use
`getPartyName(partyId, year)` so Ecology/Green and Liberal/Alliance names stay
period-correct ([party-names](../data-model/party-names.md)).
