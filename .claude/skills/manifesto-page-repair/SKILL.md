---
name: manifesto-page-repair
description: Tier-2 repair of flagged manifesto transcription pages. Claude reads the flagged page images directly and rewrites the page Markdown, then gates acceptance on an independent in-session structural audit pass before marking a page reviewed — no API key or billed calls required. Use when the user asks to repair flagged pages, fix flagged transcriptions, or run tier-2 repair on a manifesto work directory.
---

# Manifesto page repair (tier 2, in-session vision)

You are the second tier of the two-tier transcription pipeline (see
`knowledge/pipelines/transcription.md`). Tier 1 is a local OCR VLM
(DeepSeek-OCR via LM Studio); `tools/transcription-toolkit/flag_pages.py`
has already identified the pages the local model got wrong. Your job is to
re-transcribe ONLY those pages by looking at the page images yourself.

## Inputs

Given a work directory `tools/transcription-toolkit/work/<slug>/`:

- `flagged_pages.json` — the pages to repair, with reasons. If it doesn't
  exist, run `/opt/homebrew/bin/python3.12 tools/transcription-toolkit/flag_pages.py <work_dir>/ledger.json` first.
- `ledger.json` — per-page records; each page lists candidate text files.
- `images/page-NN.png` — the page images (1-indexed filenames; ledger
  `page_index` is 0-indexed, so page_index 4 → `page-05.png`; try `page-5.png`,
  `page-05.png`, `page-005.png`).
- `pages/page-NNN.<method>.txt` — candidate texts (NNN is the 0-indexed
  page_index, zero-padded to 3).

## Procedure

For EACH page in `flagged_pages.json`:

1. Read the page image with the Read tool.
2. Read the currently selected candidate text (from the ledger's
   `selected_candidate` output_file) and the best deterministic candidate
   (e.g. `pdftotext`) as reference for exact wording.
3. Produce a clean Markdown transcription of the page, following these
   strict rules:
   - READING ORDER: multi-column layouts strictly linear — left column in
     its entirety, then right column. Never interleave lines.
   - HEADINGS: `#` only for the document's main title; `##` for main
     sections; `###` for sub-sections. Never promote body text to a heading.
   - BOILERPLATE: strip running headers/footers, page numbers, social-media
     links, donate buttons.
   - TEXT FIDELITY: every word, number, and policy verbatim. No summarising.
     Where the image is ambiguous, prefer the deterministic candidate's
     wording (it came from the PDF text layer).
   - FORMATTING: bold/italic/lists/tables as they appear visually.
4. Write the result to `pages/page-NNN.claude-clean.txt` (0-indexed NNN,
   zero-padded to 3; no surrounding code fences).
5. Update the page's record in `ledger.json`:
   - add or update a candidate `{"method": "claude-clean", "available": true,
     "word_count": <n>, "artifact_score": 0.0, "output_file": "<repo-relative path>",
     "error": null}`
   - set `selected_candidate` to `"claude-clean"`, `status` to `"pending-audit"`,
     `issues` to `[]`. Do NOT set `"reviewed"` yet — that only happens after
     the independent audit in step 7 passes. The candidate you just wrote and
     the audit below must not be the same model call grading its own work.

After all pages in the batch have a `claude-clean` candidate written:

6. Run an independent, in-session structural audit against exactly the
   repaired pages — no API key, no billed calls. For each repaired page,
   re-read the page image fresh (a distinct tool call, not reasoning from
   memory of writing it) and, as a deliberately skeptical second pass,
   classify discrepancies against the same taxonomy `qa_audit_vision.py`
   uses (still available as an optional, billed, truly-independent
   cross-check for high-stakes spot-checks, but not part of this default
   flow):
   - `missing_block` — text visible in the image entirely absent from the Markdown
   - `column_join_error` — two columns/blocks merged in the wrong reading order
   - `style_mismatch` — heading level/bold/italic/list formatting doesn't match the image
   - `spurious_text` — the Markdown contains text that isn't in the image at all
   - `ordering_error` — content present but in the wrong order
   Do not rewrite or correct the text during this pass — only note discrepancies.
   This is a weaker independence guarantee than a separate model call (same
   underlying judgment doing both the writing and the checking), but it
   preserves the no-API-cost property and still forces a distinct, adversarial
   look at the image instead of rubber-stamping step 3's output.
7. For each repaired page, write the audit result to a durable
   `page_rec["vision_audit"]` field — this is the field `flag_pages.py`
   reads (but never writes) so a real finding survives every future re-gate
   instead of being silently overwritten the instant the deterministic
   checks happen to pass:
   ```json
   "vision_audit": {
     "audited_at": "<iso timestamp>",
     "method": "in-session",
     "checked_candidate": "claude-clean",
     "discrepancies": [
       {"type": "missing_block", "locator": "short quote or location", "note": "one sentence"}
     ]
   }
   ```
   - No discrepancies found → `discrepancies: []`, set `status` to `"reviewed"`.
   - Any discrepancies → keep `discrepancies` populated, leave `status` as
     `"needs-review"`, and report it to the user rather than re-editing
     `claude-clean.txt` yourself to make it disappear. Note this audit
     catches structural mismatches (wrong order, a missing block, invented
     text) — it is not a word-for-word diff against a source of truth, so a
     clean pass is not a verbatim guarantee, only a structural one.
8. Rebuild the draft without any model calls:
   `/opt/homebrew/bin/python3.12 tools/transcription-toolkit/repair_manifestos_gemini.py <work_dir>/ledger.json --reassemble-only`
9. Re-run the gate to confirm the repairs pass:
   `/opt/homebrew/bin/python3.12 tools/transcription-toolkit/flag_pages.py <work_dir>/ledger.json`
   This regenerates `status`/`issues` from its own coverage/qa_check checks
   *and* folds in anything still sitting in `vision_audit.discrepancies` —
   it will keep re-flagging a page with a recorded discrepancy until that
   field is cleared by a clean re-audit, so a real finding can't quietly
   vanish just because the deterministic checks pass. If pages are still
   flagged, report them to the user rather than looping forever — some
   flags (e.g. coverage on heavily graphical pages) are legitimate false
   positives the user should adjudicate.
10. Summarise: pages repaired, audit discrepancies (if any) with the pages
    left at `needs-review`, pages still flagged by `flag_pages.py`, and the
    draft.md path.

## Batch etiquette

- Process manifestos one at a time; a typical manifesto has 0–10 flagged pages.
- If asked to repair a whole batch, iterate the work dirs and keep a running
  tally. Don't parallelise ledger writes within a single manifesto's ledger.
- Never modify `pages/page-NNN.<deterministic>.txt` files — only add
  `claude-clean` candidates.
