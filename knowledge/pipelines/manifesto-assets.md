---
type: reference
title: Manifesto asset inventory
description: data/manifesto-assets.json flags for PDF, Markdown, and cover presence per manifesto folder.
tags: [pipeline, manifestos, covers]
timestamp: 2026-07-20T22:25:00Z
---

# Manifesto asset inventory

[`data/manifesto-assets.json`](../../data/manifesto-assets.json) lists every
`manifestos/<electionId>/<partyId>/` folder that has at least one of
`manifesto.pdf`, `manifesto.md`, `cover.png`, or `cover.jpg`, with boolean flags:

```json
{
  "1992/bnp": { "pdf": false, "md": true, "cover": false },
  "2024/labour": { "pdf": true, "md": true, "cover": true }
}
```

## Runtime use

Loaded once at startup (`initManifestoAssets` in `js/app.js`):

- **`hasManifestoPdf` / `hasManifestoContent`** — prefer these flags over guessing
- **`hasManifestoCover`** — when `cover` is false, manifesto cards and the reader
  show the **“Scan not yet archived”** placeholder immediately (no broken-image
  flicker). When `cover` is true, the cover image is shown even if there is no PDF
  (common for early text editions that have a cover scan but no archived PDF yet)

## Rebuild

```bash
python3 scripts/build-manifesto-assets.py
```

Run after adding/removing PDFs, Markdown, or covers. Part of transcription
Phase 5 alongside `build-pdf-sizes.py` and `build-fulltext-index.py`.

## Related

- [covers](./covers.md) — transparent A4 PNG convention
- [pdf-sizes](./pdf-sizes.md) — download size strings
- [fulltext-index](./fulltext-index.md) — full-text search over `.md`
