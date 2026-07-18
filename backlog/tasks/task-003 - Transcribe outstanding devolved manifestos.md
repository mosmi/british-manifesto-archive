---
id: task-003
title: Transcribe outstanding devolved manifestos
status: todo
priority: high
labels: [transcription, content]
created: 2026-06-29
---

## Context
Devolved elections are the single biggest transcription gap (~40% coverage, 97
unmatched PDFs), concentrated in the NI Assembly. See
../../knowledge/content-state/manifesto-coverage.md and the transcription workflow in
../../knowledge/pipelines/transcription.md.

## Acceptance criteria
- [ ] Prioritise NI Assembly 2003–2016 (Greens NI, Sinn Féin variants, PUP, TUV, Workers')
- [ ] For each: profile → extract → QA (≥95% coverage, headings verified) → finalize
- [ ] Add files under manifestos/<electionId>/<partyId>/ and update manifestos-index.json
- [ ] Update the coverage figures in knowledge/content-state/manifesto-coverage.md

## Handoff log
- 2026-07-17 — Gemini 3.5 Flash: Completed full visual repair, cleanup, and finalization for all 47 London devolved election manifestos across all 7 available years (2024, 2021, 2016, 2012, 2008, 2004, and 2000). Set up automation batch script `batch_london_manifestos.py` and page-level visual repair helper `repair_manifestos_gemini.py` using `gemini-2.5-flash` API. Resolved 429 API credit issues, processed and visually verified all 47 manifestos, added canonical H1 titles and metadata frontmatter, finalized and copied them to the repo folders, and successfully rebuilt sitemaps, PDF sizes, site indexes, and latest-additions.
- 2026-07-16 — Gemini 3.5 Flash: Batch converted all 147 London devolved election PDFs under original documents to markdown versions using Microsoft's MarkItDown, saving them under 'Markdown versions/London' maintaining the mirrored subdirectory structure. Resolved unreadable outputs by applying a custom font-based shift decoder (+31/+32 character offset) to rebuild the scrambled 2004 Simon Hughes PDF, and cleaned up bullet/spacer CIDs in the 2008 Boris Johnson PDF. Transcribed the 6 scanned/image-only PDFs from the 2024 London election (including Susan Hall and Brian Rose) using Gemini's OCR vision endpoint.
- 2026-06-29 — Codex: added `tools/transcription-toolkit/transcribe_pipeline.py`
  as a human-gated page-ledger layer for new transcriptions, retrospective audits,
  conservative repair drafts, and batch audit reports. The workflow now explicitly
  retains Contents/Table of Contents sections while stripping page numbers.
- 2026-06-29 — Codex: extended the pipeline with `--source-text` and
  `batch-audit-text` for authoritative historical text sources such as the local
  Iain Dale Labour splits. Ran a no-sidecar Labour 1945-1992 pilot: 14 pairs found,
  6 passed, 8 need review. Ran a no-sidecar 12-file PDF pilot across 2005-2024;
  all were conservatively queued for human review, mainly due to complex layouts,
  TOC cleanup, heading verification, and reading-order warnings.
