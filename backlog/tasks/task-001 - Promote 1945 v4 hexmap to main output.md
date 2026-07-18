---
id: task-001
title: Promote 1945 v4 hexmap to main output
status: todo
priority: medium
labels: [hexmaps, data]
created: 2026-06-29
---

## Context
`pack_test_1945_v4.py` is the most complete 1945 layout (0 interior holes, clean
regional boundaries, Thames Estuary preserved), but the live `output/1945.hexjson`
still uses greedy-Dijkstra `pack.py`. See ../../knowledge/pipelines/hexmaps.md.

## Acceptance criteria
- [ ] Confirm v4 mask changes don't regress the other 21 elections (pack.py is shared)
- [ ] Regenerate `output/1945.hexjson` via the v4 path
- [ ] Re-run `colour.py` (pack.py writes geometry-only — maps go blank otherwise)
- [ ] Copy result into site `data/hex/`, bump `?v=`, verify deploy
- [ ] Update knowledge/pipelines/hexmaps.md "Known gaps" once resolved

## Handoff log
- (empty)
