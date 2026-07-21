---
type: plan
title: Accessibility programme
description: AT pass checklist and PDF honesty work following the July 2026 UX audit (L3).
tags: [design, a11y, accessibility]
timestamp: 2026-07-21T00:30:00Z
---

# Accessibility programme (UX audit L3)

Follow-on to I01–I10 and Wave A polish (flag `aria-hidden`, table captions, contrast).

## Done in code (baseline)

- Skip link, focus-visible, search inert trap
- Hexmap / parliament SVGs: `role="img"` + `aria-label`
- Results table: `scope="col"`; election results `<caption class="sr-only">`
- Nation group headings: flag emoji in `<span aria-hidden="true">`
- Manifesto find: `aria-live` match count; Cite strip on readers
- Light-theme gold darkened to ≥4.5:1 on cream (`#7a5f24`)

## AT pass checklist (manual)

Run VoiceOver (macOS/iOS) and NVDA (Windows) on:

| Surface | Check |
|---------|--------|
| `/election/2024` results table | Caption announced; headers associated |
| Parliament chart + hexmap tabs | Tab panel names; map label; seat focus |
| `/manifesto/2024/labour` | Single H1; TOC links; find `/` + match count; cite buttons |
| Search overlay | Mode tabs; keyboard trap; grouped results |
| Parties mega-menu | Reform UK Scotland/Wales labels; focus order |

Log findings in [`log.md`](../log.md) and fix high-severity items before closing the programme.

## PDF accessibility honesty

Most archive PDFs are **scans**, not tagged accessible PDFs. Do **not** claim PDF/UA.

1. About page already frames PDFs as originals + optional text editions — keep that.
2. Prefer the online Markdown reader for keyboard/SR reading when `hasMarkdown`.
3. Future inventory (optional script): flag folders with PDF but no MD for “text not yet archived” prominence — already covered by reader empty states.

## Out of scope here

Mass remediation of historical scan PDFs; redesign of hexmap visuals beyond AT labels.