---
type: index
title: Content state
description: What's transcribed, what's missing, and audit state across the archive.
tags: [content-state]
timestamp: 2026-06-29T00:00:00Z
---

# Content state

Living record of what the archive contains and what's still outstanding.

- [manifesto-coverage](./manifesto-coverage.md) — PDF→Markdown coverage by election category
- [european-elections-audit](./european-elections-audit.md) — the 2026-06-16 European audit

## Source trackers (outside this repo)
- **Physical holdings:** `Original documents/Manifesto coverage.xlsx` — a year×party
  matrix of which physical manifestos exist (original / photocopy / textbook). Two
  sheets: "UK General elections" and "Northern Irish Assembly".
- The `Original documents/` tree holds the master PDF archive organised by election
  type (General, Devolved, European, Local Government).

## Cover images
Front covers are processed with ImageMagick; where needed the source is composited
centred on a transparent A4-proportioned (1:√2) PNG canvas. Generate from a PDF's
first page with `pdftoppm`. (See the 2026-04-30 session notes in [log](../log.md).)
