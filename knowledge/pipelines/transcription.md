---
type: pipeline
title: Transcription toolkit
description: How manifesto PDFs are converted to clean, complete Markdown, with the QA workflow and known layout failure modes.
tags: [pipeline, transcription, pdf, markdown, qa]
timestamp: 2026-06-29T00:00:00Z
---

# Transcription toolkit

Converts political party manifesto PDFs into clean, complete Markdown
(`manifestos/<electionId>/<partyId>/manifesto.md`).

**Project home:** `tools/transcription-toolkit/` (was
`~/Claude/Projects/Manifestos/transcription-toolkit/`). The project README carries the
full, lengthy lessons-learned per manifesto series; this concept is the durable
summary.

## Workflow
0. **Page-ledger pipeline** — for difficult PDFs or retrospective review, start with
   `python transcribe_pipeline.py new|audit|repair|batch-audit ...`. This writes a
   human-gated ledger under `tools/transcription-toolkit/work/` and never overwrites
   published Markdown.
1. **Profile** — `python profile_pdf.py manifesto.pdf` (layout class, rotation, blank
   pages, header/footer cuts, font inventory, column hints).
2. **Compare extractors** — `python extract_compare.py manifesto.pdf` (tries
   pdftotext variants, MarkItDown, OCR; recommends the cleanest start).
3. **Extract** — `python extract_manifesto.py manifesto.pdf [--manifest …]`. For
   non-standard pages, create a YAML page manifest (`manifests/`) declaring per-page
   mode (`skip`, `full-width`, `summary-box`, `two-col`) and header/footer overrides.
4. **Spot check** — `python spot_check.py working.md --pdf manifesto.pdf`.
5. **QA** — `python qa_check.py working.md --pdf manifesto.pdf [--strict]`.
6. **Finalize** — `python finalize_manifesto.py …` (copies, verifies SHA-256, re-QAs).
7. **Log** — `python log_conversion.py write …` (writes `.conversion.json` sidecar).

`lib/` bundles pdfplumber + deps so it works offline. `pdftotext` (poppler) is a
system binary, installed separately.

## Completeness standard
Every word in the PDF should appear verbatim in the Markdown. **Word-count coverage is
necessary but not sufficient** — a file can sit near 100% and still have truncated
headings, duplicated pull-quotes, clipped bullets, or wrong column order. Target
95–103% coverage; always verify headings against the PDF.

If the source PDF has a Contents/Table of Contents section, retain it in Markdown as
a useful overview of document structure, but strip dotted leaders, standalone page
numbers, and trailing page references. These intentionally removed TOC page numbers
should not count as missing content in coverage checks.

## When an existing partial .md exists
Don't trust it. Run a fresh extract, `diff` against the existing file, and resolve
conflicts **in favour of the PDF** (silent heading truncation is invisible to
word-count checks). Then run `check_headings.py`.

For already-published Markdown, run `transcribe_pipeline.py audit
manifestos/<electionId>/<partyId>/manifesto.md`. Files with sibling
`manifesto.pdf` receive an `.audit.json` sidecar and a page-level ledger. Files
without a source PDF are marked `source-missing` until the original document is
located.

For pre-digital main-party manifestos, a PDF may not exist yet. Where an
authoritative text source exists (for example local Iain Dale splits such as
`/Users/mosmi/Claude/Projects/Manifestos/iain-dale/labour-1945.md`), use
`transcribe_pipeline.py audit ... --source-text ...` or `batch-audit-text`.
This verifies normalized content and headings, but does not make page-layout
claims.

## Recurring layout failure modes (QA codes)
- **I2** two-column foreword attribution interleaved → rewrite as separate `—Name, Title` lines
- **P3** chapter-opener/body paragraph repetition → `deduplicate_paragraphs()` (on by default)
- TOC page numbers left in → `--strip-toc-numbers`
- **I1** imprint/legal text mid-document → add the page to `skip_pages`
- Cover slogan text extracted as headings → add cover page to `skip_pages`
- Two-column PDFs: never trust `pdftotext` (it interleaves columns) — use pdfplumber
  column-aware extraction.

QA scanner codes span coverage (C1), encoding (E1–E3), headings (H1–H6), bullets
(B1–B3), paragraphs (P1–P4), spacing (S1–S3), and reading order (R-series). See the
project README for the full table.
