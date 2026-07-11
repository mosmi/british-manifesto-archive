---
type: runbook
title: Manifesto cover images
description: Required transparent A4 PNG cover convention for manifesto.pdf first pages.
tags: [pipelines, manifestos, covers, images]
timestamp: 2026-07-11T00:00:00Z
---

# Manifesto cover images

**Required format** whenever a new `manifesto.pdf` is added (or a cover is regenerated):

1. Render page 1 with `pdftoppm`.
2. Auto-orient (many archive scans have page rotation 90/270).
3. Fit the page **inside** an **A4-proportioned canvas** (1 : √2).
4. Centre it on a **transparent** PNG — **never** letterbox onto white/opaque fill.
5. Save as `cover.png` (Westminster / party cards). For European election folders that
   already reference `manifesto.png` in the election JSON, write that path too (same
   transparent A4 asset).

Canonical size used across the archive: **1191 × 1684** px
(`1191 × √2 ≈ 1684`).

Do **not** ship `cover.jpg` with baked-in white margins as the primary cover. JPEG
cannot carry transparency; cards try `cover.png` first then fall back to `cover.jpg`.

## Why this matters

Manifesto thumbnails use `aspect-ratio: 210 / 297` (A4). Opaque white letterboxing
shows as empty white slabs above/below short or square covers. Transparent padding
lets the card chrome show through and matches existing covers (e.g. many
`manifestos/**/cover.png` files are `srgba` with non-opaque corners).

## Recipe

```bash
W=1191
H=1684
DIR=manifestos/<electionId>/<partyId>

pdftoppm -png -f 1 -l 1 -r 200 "$DIR/manifesto.pdf" /tmp/page
SRC=$(ls /tmp/page*.png | head -1)

# Optional: opened booklet scans that show back|front side-by-side — keep the front:
# magick "$SRC" -auto-orient -gravity East -crop 50%x100%+0+0 +repage /tmp/prepared.png
magick "$SRC" -auto-orient /tmp/prepared.png

magick /tmp/prepared.png -resize "${W}x${H}" \
  \( +clone -size ${W}x${H} xc:none \) \
  +swap -gravity center -compose over -composite \
  PNG32:"$DIR/cover.png"
```

Verify:

```bash
identify -format '%f %[channels] %wx%h opaque=%[opaque]\n' "$DIR/cover.png"
# expect: srgba … 1191x1684 opaque=False
```

## Euro election covers

`data/devolved/euro/<year>.json` manifesto entries usually set
`"cover": "/manifestos/euro/<year>/<party>/manifesto.png"`. Generate that file with
the same transparent A4 recipe (often identical to `cover.png`).

## After generating covers

1. Bump `ASSETS_VERSION` / `?v=` so cached cover URLs refresh
   ([cache-busting](../architecture/cache-busting.md)).
2. No need to re-run `build-pdf-sizes.py` for cover-only changes.

## Related

- Checklist step in [manifestos-index](../data-model/manifestos-index.md)
- Brief note historically lived under [content-state](../content-state/index.md)
  — prefer this runbook as the source of truth
