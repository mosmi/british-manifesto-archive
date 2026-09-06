---
type: runbook
title: Self-hosted Latin fonts
description: Local woff2 subset of Playfair Display, Public Sans and Source Serif 4.
tags: [pipelines, fonts, performance]
timestamp: 2026-09-06T00:00:00Z
---

# Self-hosted Latin fonts

The live site does **not** load Google Fonts. Latin woff2 files live in
[`fonts/`](../../fonts/) with `@font-face` rules in [`fonts/latin.css`](../../fonts/latin.css)
(`index.html` links that file with `?v=`).

Families (SIL Open Font License 1.1):

- Playfair Display (500, 600, italic 500)
- Public Sans (400, 500, 600)
- Source Serif 4 (400, 600, italic 400)

Regenerate after changing weights or the Latin unicode-range:

```bash
python3 scripts/vendor-fonts.py
```

Then bump `?v=` / `ASSETS_VERSION` ([cache-busting](../architecture/cache-busting.md)).
Font files are hashed in the filename; `/fonts/*` is `Cache-Control: immutable`.

## Related

- Forensic audit Batch 1 (**4.6**) in [sep-2026-audit-plan](../design/sep-2026-audit-plan.md)
