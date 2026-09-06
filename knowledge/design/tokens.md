---
type: concept
title: Design tokens
description: Type, space, radius and elevation custom properties in styles.css (Batch 3, Sep 2026).
tags: [design, css, tokens]
timestamp: 2026-09-06T00:00:00Z
---

# Design tokens

Defined on `:root` in `styles.css`. Colour tokens from the July refresh stay; this layer adds type, space, radius and elevation. Light theme overrides `--shadow-*` and gold.

## Type (`--fs-*`, `--lh-*`)

Eight UI steps, 11px floor (`--fs-2xs`). Display sizes use `--fs-display-*` clamps. Ghost numerals use `--fs-ghost`.

| Token | Size |
|---|---|
| `--fs-2xs` | 11px |
| `--fs-xs` | 12px |
| `--fs-sm` | 13px |
| `--fs-md` | 14px |
| `--fs-lg` | 16px (body) |
| `--fs-xl` | 18px |
| `--fs-2xl` | 20px |
| `--fs-3xl` | 24px |

`--lh-tight` 1.15 / `--lh-snug` 1.3 / `--lh-body` 1.7 / `--lh-loose` 1.75.

Tracked uppercase uses `--font-ui`, not Source Serif (`--font-body`). Display headings stay `--font-display`. CTA arrow is `--arrow-glyph` (`→`).

## Space (`--space-1` … `--space-8`)

0.25 / 0.375 / 0.5 / 0.75 / 1 / 1.5 / 2 / 3 rem. `gap` in `styles.css` maps to these (or `0`).

## Radius and elevation

`--radius-sm` 2px, `--radius-md` 4px, `--radius-lg` 8px, `--radius-xl` 12px, `--radius-pill` 999px. Circles stay `50%`.

`--shadow-1/2/3` include a cream hairline on dark so cards lift off navy. Light theme swaps them for ink-tinted shadows.

See [sep-2026-audit-plan](./sep-2026-audit-plan.md) Batch 3 (**1.2–1.6**, **1.4**).
