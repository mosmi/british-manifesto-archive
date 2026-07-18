---
type: schema
title: Manifestos index and file layout
description: data/manifestos-index.json schema and the manifestos/ directory convention.
tags: [data-model, manifestos, schema]
timestamp: 2026-07-11T00:00:00Z
---

# Manifestos index & files

## Catalogue: `data/manifestos-index.json`
A flat JSON array, one entry per available **Westminster** (and other SPA-routed)
manifesto with a text/PDF folder under `manifestos/<electionId>/<partyId>/`:
```json
[
  { "electionId": "2024", "partyId": "conservative", "label": "Conservatives Manifesto 2024" },
  { "electionId": "2024", "partyId": "cooperative",  "label": "Co-operative Party Manifesto 2024" }
]
```
- `electionId` matches an [elections](./elections.md) id (`2024`, `feb1974`, …).
- `partyId` matches a canonical party id (see [party-colours](./party-colours.md)).
- `label` is the human-facing title (use period-correct names — see
  [party-names](./party-names.md)).

European Parliament manifesto cards are primarily listed in
`data/devolved/euro/<year>.json` → `manifestos[]` (not always duplicated here).
SEO/devolved catalogue builders read those arrays separately.

### London (GLA) entries
London mayoral text routes also live in this index, with a composite
`electionId` (year-only) and a **folder slug** as `partyId`:
```json
{ "electionId": "london/2000", "partyId": "livingstone", "label": "Ken Livingstone Manifesto 2000" }
```
- URL: `/manifesto/london/2000/livingstone`
- `partyId` is the on-disk folder under `manifestos/london/<YYYY>/` — **not**
  the ballot affiliation. Independents use a candidate slug (`livingstone`,
  `benita`, `campbell`), never a shared `independent` key.
- Election JSON `manifestos[]` entries carry a matching `id` field (see
  [devolved](./devolved.md)).
- Legacy `london/gla-*` / `glc-*` / `lcc-*` keys redirect to year-only.

## Files: `manifestos/<electionId>/<partyId>/`
Each manifesto lives in its own folder, e.g. `manifestos/2024/labour/`:
- `manifesto.pdf` — the source PDF
- `manifesto.md` — the transcription (produced by the
  [transcription toolkit](../pipelines/transcription.md)); optional if PDF-only for now
- `cover.png` — **required** front-cover image: transparent A4 PNG (see
  [pipelines/covers](../pipelines/covers.md))
- Euro folders may also expose `manifesto.png` when the euro election JSON `cover`
  field points there (same transparent A4 asset)

### Frontmatter: `party_leader`
Use the party’s head **on polling day**. Co-operative Party → NEC **Chair**. Where the
party had dual Principal Speakers (Green E&W before 2008), join both names with
`and`. If the formal post was vacant, prefer the acting head with `(acting)`. Use
YAML `null` only when no head of party existed (the YAML parser treats `null`/`~`
as empty so the Leader chip is omitted).

## Adding a manifesto — checklist
1. Drop `manifesto.pdf` into `manifestos/<electionId>/<partyId>/` (or
   `manifestos/euro/<year>/<partyId>/` for EP).
2. Generate **`cover.png`** as a **transparent A4 PNG** — follow
   [pipelines/covers](../pipelines/covers.md). Do not leave white letterboxed JPEGs.
3. Transcribe → `manifesto.md` when ready (see [transcription](../pipelines/transcription.md)).
4. Add an entry to `data/manifestos-index.json` (Westminster / SPA manifesto routes).
5. Wire the election:
   - Westminster: `extraManifestoParties` in **both** `js/data.js` → `ELECTIONS` and
     `data/elections/<id>.json` (keep them in sync), plus any needed party lists.
   - European: append to `manifestos[]` in `data/devolved/euro/<year>.json`.
6. Run:
   ```bash
   python3 scripts/build-pdf-sizes.py
   python3 scripts/build-latest-additions.py
   python3 scripts/build-seo-data.py
   python3 scripts/build-sitemap.py
   ```
   (Carousel: [latest-additions](../content/latest-additions.md); sizes:
   [pdf-sizes](../pipelines/pdf-sizes.md).)
7. Update `data/party-holdings.json` chamber counts (or regenerate via the OG/holdings
   path — see [party-holdings](./party-holdings.md)).
8. Bump `?v=` / `ASSETS_VERSION` when JS/CSS/covers change
   ([cache-busting](../architecture/cache-busting.md)).
