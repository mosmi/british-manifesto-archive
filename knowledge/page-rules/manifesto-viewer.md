---
type: rule
title: Manifesto reader page
description: Guardrails for /manifesto/:electionId/:partyId — TOC, cover panel, PDF actions.
tags: [page-rules, manifesto-viewer, frontend]
timestamp: 2026-07-11T00:00:00Z
---

# Manifesto reader (`/manifesto/<electionId>/<partyId>`)

Rendered by `renderManifesto()` in `js/app.js`.

## Contents sidebar (desktop)

- `.manifesto-toc` is `position: sticky` with
  `max-height: calc(100vh - var(--nav-h) - 3rem)`.
- The link list (`.manifesto-toc-list`) must **scroll** (`overflow-y: auto`); do not
  remove that when restyling — long TOCs (e.g. Labour 1983) otherwise clip.
- Label + meta stay outside the scrolling list (`flex: none`).

## Header cover + PDF

Top-right of the header shows a cover thumb when `cover.png` / `cover.jpg` loads
(same path convention as election cards). If a PDF exists (`hasManifestoPdf` /
`getPdfSize`):

- Cover thumb links to the PDF.
- Below it, a compact PDF link: **`PDF · {size}`** (e.g. `PDF · 6.3 MB`) — not the
  longer “Original Manifesto / PDF scan…” copy used on election cards.

If neither cover nor PDF exists, the panel hides. Empty/error body states still use
`.manifesto-btn-ghost` / `.manifesto-btn-solid` for retry / PDF fallbacks.

## Covers must follow the pipeline

New or replaced reader covers must be transparent A4 PNGs — see
[pipelines/covers](../pipelines/covers.md).
