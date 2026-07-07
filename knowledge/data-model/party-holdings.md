---
type: reference
title: Party manifesto holdings
description: Per-party manifesto counts by chamber, derived from the catalogue and used by OG cards and (planned) site party browse cards.
tags: [data-model, parties, manifestos, og]
timestamp: 2026-07-05T21:00:00Z
---

# Party manifesto holdings

**Holdings** are per-party counts of manifestos in the archive, broken down by
chamber (Westminster, Holyrood, Senedd, Stormont, European Parliament, London).

They power OG party-card subtitles today and will power site party-card holdings
lines after the [design refresh](../design/implementation-plan.md) (Phase 0 / 3).

## Source of truth

Counts are **derived**, not hand-edited. `buildHoldings()` in
`tools/og-generator/build-manifest.mjs` walks:

- `data/seo.json` → `manifestos` — increments `westminster` per `partyId`
- `data/seo.json` → `devolvedManifestos` — increments the portal key
  (`holyrood`, `senedd`, `stormont`, `euro`, `london`) per item `party`

A new Westminster or Holyrood manifesto in the catalogue increments the right slug
automatically on the next build. No manual edits to party cards are required when
holdings change.

## When to regenerate

Run holdings export **whenever `data/seo.json` or devolved manifest indexes change**,
alongside the existing OG manifest build:

```bash
python3 scripts/build-seo-data.py      # if manifestos-index or devolved data changed
python3 scripts/build-og-images.py       # runs build-manifest.mjs internally
```

Typical triggers: adding a manifesto (see [manifestos-index checklist](./manifestos-index.md)),
new devolved election imports, or party id fixes in SEO data.

## Output file

Exported on every `build-manifest.mjs` run to:

**`data/party-holdings.json`**

Shape (one object keyed by party slug):

```json
{
  "labour": { "westminster": 21, "holyrood": 7, "senedd": 7, "stormont": 0, "euro": 4, "london": 0 },
  "snp":    { "westminster": 21, "holyrood": 7 }
}
```

Only chambers with count > 0 need to be present; consumers treat missing keys as zero.

## Consumers

| Surface | Status | Notes |
|---|---|---|
| OG party cards (`build-manifest.mjs` → `partySubtitle()`) | **Live** | Subtitles like “Manifestos across *21 elections* in 3 chambers” |
| Site party browse cards | **Live** | Holdings line, e.g. “21 Westminster · 7 Holyrood manifestos” |
| `js/data.js` | **Planned** | Read JSON at runtime or inline at build time |

Both surfaces must read **`data/party-holdings.json`** — one file, one derivation.

## Related

- [manifestos-index](./manifestos-index.md) — catalogue entries that feed holdings
- [og-generator pipeline](../pipelines/og-generator.md) — where `buildHoldings()` runs
- [design implementation plan](../design/implementation-plan.md) — Phase 0 export + Phase 3 UI
