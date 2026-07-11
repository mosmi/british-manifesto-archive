# British Manifesto Archive — agent guide

Static archive of UK election manifestos, results and maps (1918–2024), live at
**www.manifestos.org.uk**. Plain HTML/CSS/JS, **no build step**, deployed to
Cloudflare from `main`.

This file is the entry point for any LLM working on the project (Claude, Gemini /
Antigravity, Cursor, Codex). `CLAUDE.md` and `GEMINI.md` are symlinks to it.

## Before you do anything
1. Read **`knowledge/index.md`** — the project knowledge base (architecture, data
   model, pipelines, content state, page rules).
2. Check **`backlog/tasks/`** for the current task and its acceptance criteria.

## While you work
- Put durable facts you discover into **`knowledge/`** — one concept per file, YAML
  frontmatter, cross-link with ordinary markdown links. Don't hoard them in
  tool-specific memory (`~/.gemini/.../brain`, chat history, etc.).
- Update the relevant task's **Handoff log** with your model name + what you changed,
  so the next model (or you, next session) picks up cleanly.
- Append anything notable to **`knowledge/log.md`**.

## Hard rules (full detail in knowledge/)
- **Deploy:** the domain must point at exactly ONE Cloudflare project (Workers *or*
  Pages, never both) — see `knowledge/architecture/deployment.md`.
- **Cache:** bump the `?v=` query string on `styles.css` / `js/*.js` when you change
  them — see `knowledge/architecture/cache-busting.md`.
- **Covers:** new manifesto covers are **transparent A4 PNGs** (never white
  letterboxed JPEGs) — see `knowledge/pipelines/covers.md`.
- **Co-operative Party:** only `/party/cooperative` may split Labour/Co-op out — see
  `knowledge/page-rules/cooperative-party.md`.
- **Party names:** pass election year into `getPartyName` (Liberal/Alliance/Lib Dem;
  Ecology Party before 1985) — see `knowledge/data-model/party-names.md`.

## This repo is the single source of truth
`~/Cursor/british-manifesto-archive` (git remote
`github.com/mosmi/british-manifesto-archive`) is canonical, and the former
duplicate copies have been retired (task-006). The hexmaps and transcription
toolkits now live in **`tools/`** (their lean code + docs are git-tracked; their
heavy/regenerable inputs and outputs are git-ignored — see `.gitignore` and
`knowledge/pipelines/`). Per-tool memories are **deprecated**. Work here.
