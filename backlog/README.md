# Backlog

Task tracker for the British Manifesto Archive. One markdown file per task in
`tasks/`, with YAML frontmatter (`id`, `title`, `status`, `priority`, `labels`).
This is the "what to do" layer; durable "what to know" lives in `../knowledge/`.

## Conventions
- Statuses: `todo` → `in-progress` → `done` (move done tasks to `archive/` when stale).
- Each task has **Acceptance criteria** and a **Handoff log**. Whichever model works a
  task appends to its Handoff log (model name + date + what changed) before stopping.
- Reference relevant knowledge with links, e.g. `../knowledge/pipelines/hexmaps.md`.

## Optional tooling
These are plain markdown and work with no tooling. If you want a board UI, install
[Backlog.md](https://github.com/MrLesk/Backlog.md) (`backlog board` / web view). If the
project later needs dependency-aware scheduling across parallel agents, the same tasks
can migrate to [Beads](https://github.com/steveyegge/beads).
