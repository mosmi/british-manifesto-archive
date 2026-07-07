---
type: schema
title: Manifestos index and file layout
description: data/manifestos-index.json schema and the manifestos/ directory convention.
tags: [data-model, manifestos, schema]
timestamp: 2026-06-29T00:00:00Z
---

# Manifestos index & files

## Catalogue: `data/manifestos-index.json`
A flat JSON array, one entry per available manifesto:
```json
[
  { "electionId": "2024", "partyId": "conservative", "label": "Conservatives Manifesto 2024" },
  { "electionId": "2024", "partyId": "cooperative",  "label": "Co-operative Party Manifesto 2024" }
]
```
- `electionId` matches an [elections](./elections.md) id (`2024`, `feb1974`, …).
- `partyId` matches a canonical party id (see [party-colours](./party-colours.md)).
- `label` is the human-facing title.

## Files: `manifestos/<electionId>/<partyId>/`
Each manifesto lives in its own folder, e.g. `manifestos/2024/labour/`:
- `manifesto.pdf` — the source PDF
- `manifesto.md` — the transcription (produced by the
  [transcription toolkit](../pipelines/transcription.md))
- `cover.png` or `cover.jpg` — front-cover image (often A4-canvas-normalised; see the
  cover-processing notes in [content-state](../content-state/index.md))

## Adding a manifesto — checklist
1. Drop `manifesto.pdf` into `manifestos/<electionId>/<partyId>/`.
2. Transcribe → `manifesto.md` (see [transcription](../pipelines/transcription.md)).
3. Generate `cover.png` (e.g. `pdftoppm` first page; normalise to A4 canvas if needed).
4. Run `python3 scripts/build-pdf-sizes.py` so download links show the PDF size (see
   [pdf-sizes pipeline](../pipelines/pdf-sizes.md)).
5. Add an entry to `data/manifestos-index.json`.
6. If the party is new to that election, also update `extraManifestoParties` in the
   election file and the party lists in `data.js` (`SPECTRUM_ORDER`, `OTHERS_PARTIES`).
7. Run `python3 scripts/build-seo-data.py` and `python3 scripts/build-sitemap.py`.
8. Re-run `python3 scripts/build-og-images.py` for the affected party/manifesto cards
   (this refreshes derived [party holdings](./party-holdings.md) used in OG subtitles
   and, once exported, `data/party-holdings.json` for site party cards).
9. Bump `?v=` in `index.html` and `ASSETS_VERSION` in `data-loader.js` if you touched JS/CSS.
