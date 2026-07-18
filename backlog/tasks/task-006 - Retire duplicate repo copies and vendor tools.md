---
id: task-006
title: Retire duplicate repo copies and vendor in the toolkits
status: in-review
priority: high
labels: [ops]
created: 2026-06-29
---

## Context
Five copies of the site exist. `~/Cursor/british-manifesto-archive` is canonical (git,
origin github.com/mosmi/british-manifesto-archive, newest content). The hexmaps and
transcription toolkits live in separate folders. Consolidate to one source of truth.

## Acceptance criteria
- [x] `diff -r` Cursor copy vs `~/Documents/Antigravity/.../british-manifesto-archive`;
      merge any unique changes, then retire the Antigravity copy
      (merge was already done; re-confirmed nothing unique of value — only git-ignored
      `data/cache`, `previews/*`, `scratch/__pycache__`. Copy was fully pushed to
      origin/main with no unpushed commits. Moved to Trash.)
- [x] Retire `~/Claude/claude-code/british-manifesto-archive` (stale, non-git) and the
      two backups (`backup 2026-04-19`, `-original`) — all moved to Trash (recoverable)
- [x] Move `~/Claude/claude-code/hexmaps` → `tools/hexmaps/`
- [x] Move `~/Claude/Projects/Manifestos/transcription-toolkit` → `tools/transcription-toolkit/`
- [x] Fix any path references in knowledge/pipelines/* once moved (pipeline docs already
      pointed at `tools/`; also fixed the hardcoded path in `scripts/apply-external-hexmaps.py`)
- [x] Commit; confirm AGENTS.md "single source of truth" statement is accurate (updated)

## Handoff log
- **2026-06-29 · Claude (Cursor)** — Reconciled the canonical repo with the Antigravity
  copy. Canonical `main` (`094de2f`) was a strict ancestor of Antigravity `main`
  (`a1c73bc`, already pushed to `origin/main`): fast-forwarded 16 commits, nothing unique
  to the Cursor side. Also pulled across Antigravity's uncommitted Holyrood constituency
  hexmap work (4 modified files + `data/hex/holyrood/`, `data/hex/holyrood-grid.json`,
  `scripts/build-holyrood-hex.py`). `diff -r` now shows the trees identical except for the
  Cursor-only knowledge base and git-ignored scratch. JS/JSON/py all validate; verified
  the new Constituencies tab renders on `/devolved/holyrood/2021`. Changes left
  uncommitted pending review. **Not yet done:** committing, physically retiring the
  Antigravity + Claude copies/backups, and vendoring the two toolkits into `tools/`.
- **2026-06-29 · Claude (Cursor)** — Completed the consolidation on branch
  `cursor/consolidate-repo-and-tools` (PR into `main`, not deployed).
  - **Vendored** both toolkits wholesale into `tools/` (`mv`, same volume). To keep git
    and the Cloudflare deploy lean, only the lean code + docs are tracked; the heavy /
    regenerable dirs are git-ignored: `tools/hexmaps/{sources(1.5GB),output,output copy,
    output_backup_pre_hungariant,preview,reference}` and
    `tools/transcription-toolkit/{lib(34MB),Markdown versions}` (plus the usual
    `__pycache__`/`.DS_Store`). ~38 files (<1 MB) now tracked under `tools/`.
  - **Deploy/limits**: added `tools/` to `.assetsignore` (excluded from the public
    site) and `"tools"` to `SKIP_DIRS` in `scripts/check-cloudflare-limits.py` so the
    physically-present 1.5 GB doesn't trip the local guard. Limits check: 1813 files, OK.
  - **Path fixes**: `scripts/apply-external-hexmaps.py` now imports `colour.py` from
    `tools/hexmaps/scripts/` (legacy `~/Claude` path kept only as a last-resort
    fallback). `knowledge/pipelines/{hexmaps,transcription}.md` already pointed at
    `tools/`. Updated AGENTS.md "single source of truth" section.
  - **Retired** (moved to macOS Trash, recoverable, dated): the Antigravity copy (3.6 GB,
    fully pushed, nothing unique), the stale non-git Claude copy (711 MB), and the two
    backups (`backup 2026-04-19` 428 MB, `-original` 128 KB).
  - **Note**: `knowledge/`, `backlog/`, `AGENTS.md` remain git-untracked (unchanged
    policy from PR #1/#3); their edits here are local. Only `tools/` + the three
    ignore/limits files are in the commit.
