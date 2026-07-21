---
type: reference
title: Party contests metadata
description: Optional contests[] on party records — chambers a party has fought, beyond documents on file.
tags: [data-model, parties, browse]
timestamp: 2026-07-20T22:00:00Z
---

# Party contests

`/parties/all` **Contested** filter merges three sources:

1. Optional curated `contests: ['westminster', 'holyrood', …]` on the party
   object in [`js/data.js`](../../js/data.js)
2. Appearances in bundled Westminster `ELECTIONS` results /
   `extraManifestoParties`
3. Chambers inferred from manifesto folders / PDFs already in the archive

## Chamber ids

| id | Meaning |
|---|---|
| `westminster` | UK general elections |
| `holyrood` | Scottish Parliament |
| `senedd` | Senedd Cymru |
| `stormont` | Northern Ireland Assembly |
| `london` | London Mayor / Assembly (and historic LCC/GLC where archived) |
| `euro` | European Parliament |

Territorial parties (`welshlibdem`, `scottishlab`, …) are **separate** party
ids from their federal counterparts — filter matches are per id, not by
family.

## When to set `contests`

Add or extend `contests` when a party fought a chamber but the archive does
not yet hold a manifesto (or results row) for it — e.g. SPGB still contests
elections despite sparse document coverage. Prefer curated truth over
guessing from old document decades.

## Status

Optional `status: 'active' | 'historical'` overrides the default heuristic
(dissolved wording in the description → historical; otherwise active;
`isPrimary` parties still surface under the Primary filter).
