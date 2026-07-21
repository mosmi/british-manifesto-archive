---
type: rule
title: Manifesto reader page
description: Guardrails for /manifesto/:electionId/:partyId — TOC, cover panel, PDF actions, headings, find, cite.
tags: [page-rules, manifesto-viewer, frontend]
timestamp: 2026-07-21T00:00:00Z
---

# Manifesto reader (`/manifesto/<electionId>/<partyId>`)

Rendered by `renderManifesto()` in `js/app.js`.

## Heading hierarchy (I07)

- The chrome title (`.manifesto-viewer-title`) is the **sole `<h1>`**.
- `document.title` / `setPageMeta` must use the same string:
  `{displayName} Manifesto {displayYear}` →
  `Labour Manifesto 2024 — The British Manifesto Archive`.
- After Markdown parse, `enhanceManifestoHtml` demotes the first content `<h1>`
  (from `manifesto.md`) to `<p class="manifesto-doc-masthead">`, keeping the
  existing body-title styling. Do **not** edit source `.md` files for this.
- TOC still keys off `h2` only. Reference mock:
  [`sandbox/i07-manifesto-heading.html`](../../sandbox/i07-manifesto-heading.html).

## Contents sidebar (desktop)

- `.manifesto-toc` is `position: sticky` with
  `max-height: calc(100vh - var(--nav-h) - 3rem)`.
- The link list (`.manifesto-toc-list`) must **scroll** (`overflow-y: auto`); do not
  remove that when restyling — long TOCs (e.g. Labour 1983) otherwise clip.
- Label + meta stay outside the scrolling list (`flex: none`).
- **Find in this manifesto** (`setupManifestoFind`) sits above the TOC label;
  hidden on empty/unavailable states. `/` focuses find when not typing in another
  field. Native browser Find remains available.

## Citation strip (I10)

Below the header meta row: suggested citation, **Copy citation** / **Copy link**,
and a quiet link to About (sources / copyright). Keep visually quiet.

## Header cover + PDF (I06)

Top-right of the header shows a cover thumb when `cover.png` / `cover.jpg` loads
(same path convention as election cards). If a PDF exists (`hasManifestoPdf` /
`getPdfSize`):

- Cover thumb links to the PDF.
- Below it, compact CTA via shared `pdfCtaHtml({ compact: true })`:
  **`Original PDF · {size}`** (e.g. `Original PDF · 6.3 MB`).
- Election / devolved / London cards use the same helper with the longer subtitle
  (“PDF scan of original document · {size}”).

If neither cover nor PDF exists, the panel hides. Empty/error body states still use
`.manifesto-btn-ghost` / `.manifesto-btn-solid` for retry / PDF fallbacks.
Solid CTAs must beat `.manifesto-content a` (use `a.manifesto-btn-solid` /
`.manifesto-content a.manifesto-btn-solid` with `color: var(--field)`).

### Wholly missing (no PDF, no cover, no Markdown)

When `data/manifesto-assets.json` shows nothing on disk for that folder, do **not**
frame it as a load/connection error. Render the slim
**“Not yet in the archive”** state (`manifestoUnavailableHtml`): honest copy, links
to the election and party pages, `noindex`, and no TOC / cover placeholder / Try again.

Text-missing-but-PDF-present still uses “Text version not yet archived” with a PDF CTA.

Placeholder when a scan is expected but absent: **“Scan not yet archived”**.

## Covers must follow the pipeline

New or replaced reader covers must be transparent A4 PNGs — see
[pipelines/covers](../pipelines/covers.md).
