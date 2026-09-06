---
type: rule
title: Manifesto reader page
description: Guardrails for /manifesto/:electionId/:partyId — TOC, cover panel, PDF actions, headings, find, cite.
tags: [page-rules, manifesto-viewer, frontend]
timestamp: 2026-07-21T00:00:00Z
---

# Manifesto reader (`/manifesto/<electionId>/<partyId>`)

Rendered by `renderManifesto()` in `js/app.js`. The cover wall at
[`/manifesto`](../design/manifesto-hub.md) is a different page.

## Heading hierarchy (I07 / audit 5.2)

- The chrome title (`.manifesto-viewer-title`) is the **sole `<h1>`**.
- That H1 is the published title from `data/manifesto-titles.json` (Wikipedia
  slogan, cover line, or the document H1). If none of those exist, use
  `{Party} manifesto {Year}` — never “Published without a distinct title”.
- `document.title` / `setPageMeta`: `{Party} manifesto {Year}` first; append
  ` — {slogan}` only when the title is distinctive. See
  [manifesto-titles](../pipelines/manifesto-titles.md).
- After Markdown parse, `enhanceManifestoHtml` demotes the first content `<h1>`
  (from `manifesto.md`) to `<p class="manifesto-doc-masthead">`. Do **not** edit
  source `.md` files for this.
- TOC still keys off `h2` only. Title extraction: [manifesto-titles](../pipelines/manifesto-titles.md).

## Contents sidebar (desktop)

- `.manifesto-toc` is `position: sticky` with
  `max-height: calc(100vh - var(--nav-h) - 3rem)`.
- The link list (`.manifesto-toc-list`) must **scroll** (`overflow-y: auto`); do not
  remove that when restyling — long TOCs (e.g. Labour 1983) otherwise clip.
- Below 1199px the desktop aside hides; the open Contents list uses
  `max-height: min(60vh, …)` and `overflow-y: auto` so it scrolls inside the
  panel instead of trapping the page.
- Label + meta stay outside the scrolling list (`flex: none`).
- **Find in this manifesto** (`setupManifestoFind`) sits above the TOC label;
  hidden on empty/unavailable states. `/` focuses find when not typing in another
  field. Native browser Find remains available.

## Citation strip (I10 / audit 5.5)

Below the header meta row: Harvard-style citation with **access date** and the
published title (slogan or conventional party-and-year title), **Copy citation** /
**Copy Chicago** / **Copy BibTeX** / **Copy link**, provenance (source,
digitisation, copyright), and a quiet About link.

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

Placeholder when a scan is expected but absent: **“Not yet digitised”**.

## Covers must follow the pipeline

New or replaced reader covers must be transparent A4 PNGs — see
[pipelines/covers](../pipelines/covers.md).
