# Manifesto Transcription Toolkit

A set of tools for converting political party manifesto PDFs into clean, complete Markdown files.

---

## What's in this folder

| File/Folder | Purpose |
|-------------|---------|
| `PROMPT.md` | The refined prompt to give an AI agent when asking it to transcribe a manifesto |
| `extract_manifesto.py` | Python script that automates extraction using font-aware, column-aware PDF parsing |
| `extract_compare.py` | **Extraction strategy runner** — tries all available extractors (pdftotext variants, MarkItDown, OCR) and recommends the cleanest starting method |
| `check_headings.py` | Script to extract all headings from a PDF and verify they appear verbatim in the Markdown |
| `profile_pdf.py` | **Preflight profiler** — run before extraction to get page dimensions, rotation, layout class (including rotated-spread A3), word counts, column layout hints, font inventory, and suggested Y_HEADER/Y_FOOTER constants |
| `qa_check.py` | **Post-extraction QA scanner** — run after extraction to flag encoding errors, suspect headings, bullet artefacts, spacing issues, vertical fragments, reading-order problems, and coverage |
| `qa_allowlist.yaml` | Allowlist for suppressing known QA false positives (phrases, allowed heading starts, disabled codes) |
| `resolve_output.py` | **Output path helper** — infers the canonical destination path for a converted Markdown file from the PDF filename and party name |
| `finalize_manifesto.py` | **Finalization wrapper** — copies working file to destination, verifies SHA-256 hash, and runs QA on the destination |
| `spot_check.py` | **Spot checker** — extracts key snippets from both PDF and Markdown for quick side-by-side reading-order verification |
| `log_conversion.py` | **Conversion metadata logger** — writes and reads `.conversion.json` sidecar records (extractor, coverage, QA counts, notes) |
| `transcribe_pipeline.py` | **Human-gated orchestration layer** — page-ledger workflow for new transcriptions, retrospective audits, conservative repairs, batch audit reports, and (`checklist` subcommand) bounded human-review checklists generated from a ledger |
| `qa_audit_vision.py` | **Layer B vision-model audit (LEGACY/optional)** — sends a page image + its extracted text to a Claude vision model to classify structural discrepancies. Needs `ANTHROPIC_API_KEY`; superseded for gating by `flag_pages.py`. See `TRANSCRIPTION_PIPELINE.md` Sec.4 |
| `repair_manifestos_gemini.py` | **Tier-1 page transcription/repair (backend-agnostic despite the name)** — defaults to a local OCR VLM via LM Studio/oMLX (`--backend local --mode ocr`, no API key); `--backend gemini` is the legacy paid path. Writes `vlm-clean`/`gemini-clean` candidates, reassembles `draft.md`; `--reassemble-only` rebuilds the draft with no model calls. See `LOCAL_SETUP.md` |
| `flag_pages.py` | **Deterministic per-page QA gate** — checks model-transcribed pages (word coverage vs PDF text layer + per-page `qa_check.py`) and writes `flagged_pages.json` for tier-2 repair. No API key |
| `LOCAL_SETUP.md` | One-time LM Studio / DeepSeek-OCR setup, go/no-go quality check, and the two-tier per-manifesto workflow |
| `manifests/` | Per-PDF YAML sidecar files that declare per-page extraction mode, skip pages, and header/footer overrides — see `manifests/TEMPLATE.yaml` |
| `scripts/` | Bespoke per-manifesto extraction scripts for PDFs too complex for the generic extractor |
| `requirements.txt` | Python package dependencies |
| `lib/` | Pre-installed Python packages (pdfplumber and dependencies) — see below |
| `README.md` | This file |

---

## Pre-installed tools (`lib/` folder)

The `lib/` folder contains a pre-installed copy of **pdfplumber** (v0.11.9) and its dependencies (pdfminer, PIL/Pillow, wand, charset-normalizer, chardet, cryptography). These were installed from a Claude/Linux session so they work without network access in future sessions.

### Using the pre-installed packages

Add this at the top of any extraction script before importing pdfplumber:

```python
import sys, pathlib
# Use the toolkit's bundled pdfplumber if not already installed system-wide
try:
    import pdfplumber
except ImportError:
    sys.path.insert(0, str(pathlib.Path(__file__).parent / 'lib'))
    import pdfplumber
```

Or, to always prefer the bundled version:

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent / 'lib'))
import pdfplumber
```

### pdftotext (system binary)

`pdftotext` is **not** bundled here — it's a compiled binary linked against system libraries and cannot be copied portably. Install it via:

```bash
# macOS
brew install poppler

# Ubuntu / Debian (including Claude Linux sessions)
sudo apt install poppler-utils

# Check if already available (often pre-installed in Claude sessions)
which pdftotext
```

The extraction scripts will skip the word-count verification step gracefully if `pdftotext` is not installed.

### Adding new tools to `lib/`

If a future session needs additional Python packages, install them into `lib/` so they persist for future sessions:

```bash
pip install PACKAGE_NAME --target /path/to/transcription-toolkit/lib --break-system-packages
```

It is fine to install tools here for use in future manifesto work.

The `../Python scripts/` folder contains earlier, manifesto-specific extraction scripts (Conservative 2005, Labour 2024, etc.) that were the predecessors of the generalised script here. It also contains:

| File | Purpose |
|------|---------|
| `../Python scripts/manifesto_spacing_fixer.py` | Reusable post-processing utility for fixing spacing artefacts in extracted Markdown (missing spaces after periods/commas, run-together words, possessive apostrophes, etc.) — see the [Post-extraction spacing corrections](#post-extraction-spacing-corrections) section below |

---

## Quick start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

For word-count verification, also install `poppler-utils`:

```bash
# macOS
brew install poppler

# Ubuntu / Debian
sudo apt install poppler-utils
```

### 2. Run the extraction script

```bash
python extract_manifesto.py path/to/manifesto.pdf
```

---

## Recommended workflow for a new manifesto

For difficult PDFs, prefer the page-ledger pipeline first. It creates a
reviewable draft and records page-level extraction candidates, layout risks,
rendered page references, and selected local extraction methods without writing
to the public site:

```bash
python transcribe_pipeline.py new path/to/manifesto.pdf
```

The generated artifacts live under `tools/transcription-toolkit/work/` and are
ignored by git. The draft is intentionally human-gated; finalize only after all
high-risk pages are accepted or manually repaired.

### Step 1 — Profile the PDF

```bash
python profile_pdf.py manifesto.pdf
```

This reports the layout class (single-col, two-col, rotated-spread A3, etc.), rotation, blank pages, suggested header/footer cuts, and font inventory. For rotated A3 spread PDFs, it will warn against coordinate-based reconstruction.

### Step 2 — Compare extractors

```bash
python extract_compare.py manifesto.pdf --out-dir /tmp/extracts
```

This tries all available extractors and recommends the cleanest starting point. Output files are saved to `--out-dir` for manual inspection. For difficult PDFs, inspect the recommended file and the runner-up before committing to an approach.

### Step 3 — Extract

Run the generic extractor or a bespoke script, using the strategy recommended by `extract_compare.py`.

### Step 4 — Spot check

```bash
python spot_check.py working.md --pdf manifesto.pdf
```

Prints five key snippets side-by-side (PDF vs Markdown) so you can verify reading order without reviewing the whole file.

### Step 5 — QA

```bash
python qa_check.py working.md --pdf manifesto.pdf
```

For final audit, add `--strict` to fail on warnings:

```bash
python qa_check.py working.md --pdf manifesto.pdf --strict
```

To suppress known false positives, edit `qa_allowlist.yaml` and it will be picked up automatically. See the [QA allowlist](#qa-allowlist) section below.

### Step 6 — Finalize

```bash
python finalize_manifesto.py working.md "Markdown versions/scottish-labour-manifesto/2001-scottish-labour-manifesto.md" \
    --pdf manifesto.pdf
```

This copies the file, verifies the SHA-256 hash, and re-runs QA on the destination. Use `resolve_output.py` if you are unsure of the destination path:

```bash
python resolve_output.py --pdf manifesto.pdf --party "Scottish Labour"
```

### Step 7 — Log the conversion

```bash
python log_conversion.py write "Markdown versions/.../2001-scottish-labour-manifesto.md" \
    --pdf manifesto.pdf \
    --extractor markitdown \
    --run-qa \
    --notes "Rotated A3 spread; MarkItDown gave cleaner reading order than pdftotext."
```

This writes a `.conversion.json` sidecar alongside the Markdown file. To review all conversion records:

```bash
python log_conversion.py list "Markdown versions/"
```

---

## Optional extractors

### MarkItDown (Microsoft)

[MarkItDown](https://github.com/microsoft/markitdown) is an optional extractor that can produce cleaner reading order for some PDFs, particularly rotated A3 spreads where `pdftotext` interleaves columns.

Install it into `lib/` so it persists across sessions:

```bash
pip install markitdown --target transcription-toolkit/lib --break-system-packages
```

Once installed, `extract_compare.py` will include it automatically in its comparison. To use it directly:

```python
from markitdown import MarkItDown
md = MarkItDown()
result = md.convert("manifesto.pdf")
text = result.text_content
```

MarkItDown is **not** a hard dependency. The toolkit falls back to `pdftotext` and `pdfplumber` if it is not installed. Always compare it against other methods using `extract_compare.py` before relying on it — for some PDFs, plain `pdftotext` or `pdftotext -raw` gives cleaner output.

### OCR (Tesseract)

For image-only PDFs or PDFs with a damaged text layer, OCR can recover content that embedded-text extractors miss. Install the optional dependencies:

```bash
# System packages
brew install tesseract poppler       # macOS
sudo apt install tesseract-ocr poppler-utils  # Ubuntu/Debian

# Python packages
pip install pytesseract pdf2image --target transcription-toolkit/lib --break-system-packages
```

Then use `extract_compare.py --ocr` to include OCR in the comparison.

### Cloud OCR / document AI fallbacks

The page-ledger pipeline is designed for hybrid extraction: local tools first,
then paid/cloud OCR only for pages marked risky. The current orchestrator records
the preferred fallback order in its ledger (`Mistral OCR 4`, then `Qwen-OCR`) but
does not call those services yet. Wire API clients only after a small benchmark
shows which service handles manifesto layouts better.

Qwen3.7-Max should be treated as a review/repair orchestration model rather than
the primary OCR engine; use an OCR/document model for reading pages.

---

## Retrospective audit and repair

Existing `manifesto.md` files can be checked against sibling source PDFs without
overwriting published Markdown:

```bash
python transcribe_pipeline.py audit manifestos/2024/labour/manifesto.md
```

This writes:

- `<manifesto>.audit.json` next to the Markdown file
- `work/.../ledger.json`
- page-level local extraction candidates
- rendered page PNGs for single-file audits

Run a batch audit over source-backed Markdown files:

```bash
python transcribe_pipeline.py batch-audit --limit 10
```

Batch mode does not render page PNGs by default, to avoid producing large local
artifacts. Add `--render-pages` when you need visual evidence for every page.

Conservative repair mode only writes a reviewed draft and diff. It never edits
`manifesto.md` directly:

```bash
python transcribe_pipeline.py repair manifestos/2024/labour/manifesto.md
```

At present, automatic repair is deliberately limited to Contents/Table of
Contents cleanup: retain the Contents section as a structural overview, but
remove dotted leaders, standalone page numbers, and trailing page references.
Layout-sensitive issues remain `needs-human-review`.

For historical manifestos where there is no source PDF but there is an
authoritative text source, audit against that golden text instead:

```bash
python transcribe_pipeline.py audit manifestos/1945/labour/manifesto.md \
  --source-text /Users/mosmi/Claude/Projects/Manifestos/iain-dale/labour-1945.md
```

Run a batch golden-text audit for Iain Dale-style split files:

```bash
python transcribe_pipeline.py batch-audit-text \
  --source-dir /Users/mosmi/Claude/Projects/Manifestos/iain-dale \
  --party labour
```

Golden-text audit compares normalized words and Markdown headings. It does not
make page-layout claims, so use it for pre-digital source text verification
rather than PDF layout QA.

---

## QA allowlist

The `qa_allowlist.yaml` file suppresses known false positives from `qa_check.py` without disabling entire check codes.

```yaml
# Exact substrings to never flag
phrases:
  - "in in-work poverty"   # S4 false positive: "in" before "in-work"
  - "ECtHR"                # mixed-case abbreviation

# First words allowed at the start of headings (suppresses H3)
heading_starts_allowed:
  - "The"
  - "A"
  - "Our"

# Check codes to disable entirely (use sparingly)
disabled_codes: []
```

The allowlist is loaded automatically if `qa_allowlist.yaml` is in the same folder as `qa_check.py`. Pass `--allowlist path/to/file.yaml` to use a per-manifesto allowlist, or `--no-allowlist` to disable it.

**Reading-order QA:** `qa_check.py` now produces a three-line scorecard at the top of every report:

```
  ✓  Coverage               healthy
  !  Reading order          [R1] [R3]
  ✓  Markdown structure     looks OK
```

This makes it harder to accept a file just because word coverage looks good. R-series codes flag reading-order problems independently of the C1 coverage check.

This will:
- Auto-detect single- or two-column layout
- Extract text with font-aware bold/italic markers
- Reconstruct paragraphs using y-gap detection
- Write to `path/to/manifesto-extracted.md`
- Print a word-count coverage check at the end

### 3. Review and correct the output

The script produces a good first draft but always needs review. Common things to check:

- **Heading levels** — the script guesses `###` for short bold paragraphs, but you may need to promote some to `##` or `#`.
- **Missing sections** — image-heavy or graphically complex pages may extract poorly. Add those manually.
- **Style markers** — scan for `**` or `_` that look wrong (e.g. wrapped around a full paragraph rather than just a phrase).
- **Word coverage** — aim for ≥ 95% vs. the PDF word count. The script prints this at the end.

---

## Script options

```
python extract_manifesto.py input.pdf [output.md] [OPTIONS]

Options:
  --col-split N         Force a specific column split x-coordinate (default: auto-detect)
  --para-gap N          Min vertical gap (pt) to start a new paragraph (default: 18)
  --header-cut N        Strip running headers — ignore text with top < N pt (default: 65)
  --footer-cut N        Strip running footers — ignore text with top >= N pt (default: page height - 20)
  --skip-pages N,N      Comma-separated 0-indexed page numbers to skip entirely
  --single-col          Force single-column mode (skip auto-detect)
  --title TITLE         Set the H1 manifesto title (default: derived from filename)
  --manifest FILE       YAML page manifest for per-page mode, header/footer overrides (see manifests/)
  --no-verify           Skip the pdftotext word-count check at the end
  --anomaly-report      Print per-page anomaly report after extraction
  --no-dedup            Disable duplicate-paragraph removal. By default the extractor
                        removes paragraphs that appear twice within a 20-paragraph window,
                        catching the chapter-opener + body-page repetition pattern. Use
                        --no-dedup if the manifesto legitimately repeats passages.
  --strip-toc-numbers   Strip trailing page numbers from table-of-contents lines
                        (e.g. "Introduction 6" → "Introduction"). Off by default.
```

### Examples

```bash
# Basic extraction, auto-detect layout
python extract_manifesto.py "2024-labour-manifesto.pdf"

# Two-column PDF, known split at x=290, skipping cover pages 0–2
python extract_manifesto.py "2005-alliance-manifesto.pdf" \
    --col-split 290 \
    --skip-pages 0,1,2 \
    --title "Alliance Party Manifesto 2005"

# Single-column PDF, tighter paragraph gap
python extract_manifesto.py "2024-green-manifesto.pdf" \
    --single-col \
    --para-gap 14 \
    --title "Green Party Manifesto 2024"
```

---

## End-to-end workflow for complex PDFs

Word-count coverage is necessary but not sufficient.  A file can sit near 100% and still contain braided sidebars, false pull-quote headings, and orphaned summary-box continuations.  For any PDF that is not a straightforward single-column document, follow this eight-step workflow to make those failure modes mechanically visible before manual inspection.

### Step 1 — Run the preflight profiler

```bash
python profile_pdf.py path/to/manifesto.pdf
```

This takes 5–10 seconds and tells you: how many pages, their dimensions, which pages are likely blank or cover-only, what running header/footer text is repeated across pages, a suggested `Y_HEADER` / `Y_FOOTER`, and an x-coordinate histogram from sample pages so you can see column boundaries before writing any code.  For heavily designed PDFs, also run it with `--sample-pages` set to a few specific pages you want to inspect:

```bash
python profile_pdf.py manifesto.pdf --sample-pages 3,10,18,25
```

Use the output to set `Y_HEADER`, `Y_FOOTER`, `col_split`, `skip_pages`, and identify any pages that need special treatment (cover, divider, action page, summary box, blank).

### Step 2 — Create a page manifest for non-standard pages

For any page that is not normal body text — cover, divider, full-width action page, summary box, logo-only — create a YAML manifest file:

```bash
cp manifests/TEMPLATE.yaml manifests/my-manifesto-YYYY.yaml
# then edit it
```

Example:

```yaml
title: "Party Name Manifesto 2005"
header_cut: 65
footer_cut: 800
pages:
  0:
    mode: skip           # cover
  1:
    mode: skip           # near-blank back-of-cover
  18:
    mode: summary-box    # extracted as single-column; sidebar detection is future work
  21:
    mode: full-width     # divider page — no column split
  30:
    mode: full-width
    footer_cut: 826      # imprint zone sits higher on this page
  31:
    mode: skip           # logo-only
```

Saving these judgement calls in a manifest file keeps them visible, auditable, and reproducible.  Without a manifest, they end up buried in ad hoc `if page_num == 30` guards in per-script code.

### Step 3 — Run the extractor

```bash
python extract_manifesto.py manifesto.pdf output.md \
    --manifest manifests/my-manifesto-YYYY.yaml \
    --anomaly-report
```

The `--anomaly-report` flag prints a per-page table of low word counts and high fragment ratios immediately after extraction — a quick first signal of pages that extracted poorly.

### Step 4 — Run the QA scanner

```bash
python qa_check.py output.md --pdf manifesto.pdf
```

This checks for encoding errors (CID tokens, replacement characters), suspect headings (quote-mark starts, lowercase starts, adjacent heading fragments that should be merged), mid-sentence bullet glyphs, bare page numbers, imprint text, attribution-block garbling, and word-count coverage.  Fix everything flagged as an error or warning before moving on.

The two layout-specific checks added from recent conversion experience are:

- **I1 — Imprint/legal text (mid-document only)**: flags paragraphs containing publishing credits ("Published and promoted by…"), UK postcodes, or phone numbers — but only when they appear before the final 5% of the document. Imprint text at the very end of the markdown is expected and correct (that is where it legitimately belongs in a printed manifesto). The warning fires when the same content appears mid-document, which means the extractor picked it up from an inside-cover or colophon page that should have been added to `skip_pages` in the manifest.

- **I2 — Attribution block garbling**: flags paragraphs containing repeated leadership titles such as "Leader of the … Leader of the", a sign that two co-signing authors appeared in a side-by-side two-column layout and their name/title lines were read interleaved. The fix is manual: rewrite as two separate `—Name, Title` attribution lines.

For use in automated pipelines, `--json` outputs machine-readable results and `--strict` exits with code 1 if any errors or warnings are found:

```bash
python qa_check.py output.md --pdf manifesto.pdf --json > qa-report.json
python qa_check.py output.md --pdf manifesto.pdf --strict && echo "QA passed"
```

### Step 5 — Inspect flagged pages visually

Open the PDF alongside the Markdown and check each page that the anomaly report or QA scanner flagged.  Common things to look for: left and right column content braided together line-by-line (column split wrong), summary box content interleaved with body text (needs `mode: summary-box` in the manifest), pull-quote text promoted to a heading (needs manual demotion or exclusion), and orphaned single-word list items (sidebar continuation fragments).

### Step 6 — Verify headings

```bash
python check_headings.py manifesto.pdf output.md
```

Fix every `TRUNCATED`, `ALTERED`, or `NOT FOUND` issue before finishing.  Truncated headings are the hardest artefact to spot with word-count checks alone — a heading that loses half its words stays invisible in coverage metrics.

### Step 7 — Check coverage and accept a small undercount

Run the final coverage check:

```bash
pdftotext manifesto.pdf - | wc -w
wc -w output.md
```

An undercount of 2–5% is expected and correct when running headers, footers, contents pages, and cover text are properly stripped.  Accept this.  Do not try to close the gap by including footer text you correctly excluded.

**Coverage is necessary but not sufficient.**  Steps 4–6 are what turn a file with healthy coverage into one that is actually complete.

### Step 8 — Save custom overrides as a named script

If the generic extractor needed per-manifesto overrides beyond what the manifest covers (e.g. a bespoke CID decoder, a three-column layout, drop-cap merging), save those as a named script in `scripts/`:

```text
scripts/extract_party_year.py
```

Each script should import shared functions from the toolkit, define only the PDF path, output path, manifest, and local override rules, print final word coverage, and run the QA scanner.  This avoids losing hard-won layout fixes and makes later corrections reproducible.

---

## Known layout challenges

These are recurring failure modes identified across multiple conversion batches. Each has a recommended fix.

### 1. Two-column foreword attribution blocks

**What it looks like:** A joint foreword signed by two leaders (e.g. UK party leader + regional party leader) appears in a side-by-side two-column layout. The extractor reads it column-by-column and produces:

```
Nick Clegg Willie Rennie
**Leader of the Leader of the**
**Scottish Liberal Democrats**
**Liberal Democrats**
```

**QA flag:** I2.

**Fix:** Manual edit. Rewrite as two separate attribution lines:

```
— Nick Clegg, Leader of the Liberal Democrats
— Willie Rennie, Leader of the Scottish Liberal Democrats
```

If the PDF has many such signatures, consider setting the foreword pages to `mode: full-width` in the manifest to force single-column reading — this won't reconstruct the two attributions correctly on its own, but it will at least stop the interleaving.

---

### 2. Chapter-opener + body-page paragraph repetition

**What it looks like:** A chapter's title page contains introductory body text (a brief description of the chapter's theme). The following body page then repeats that same introductory paragraph as the first paragraph of the chapter's content. The result is the same sentence appearing twice, a few paragraphs apart.

**Automatic fix:** The extractor's `deduplicate_paragraphs()` step (on by default) removes paragraphs that appear more than once within a 20-paragraph sliding window. Each removal is logged to stdout. Use `--no-dedup` to skip if deliberate repetition is expected.

**QA flag:** P3 (repeated paragraph).

---

### 3. TOC page numbers left in output

**What it looks like:** The table of contents is extracted verbatim, leaving trailing page numbers on each entry:

```
Introduction by Nick Clegg & Willie Rennie 6
Britain in 2020: The Liberal Democrat vision 10
1 Responsible finances: 14
```

**Fix:** Pass `--strip-toc-numbers` to the extractor. This strips trailing 1–3 digit numbers from lines of 14 words or fewer, which catches all standard TOC entries without touching body text. Verify the output afterwards — lines with legitimate inline page references (e.g. "see page 12") are usually longer than 14 words and will be unaffected.

---

### 4. Imprint/legal text in body

**What it looks like:** Publishing credits from the back page or colophon appear in the extracted markdown:

```
Published and promoted by S Smith on behalf of the Welsh Liberal Democrats,
all at 38 The Parade, Cardiff, CF24 3AD.
```

**QA flag:** I1 — but only if the imprint appears mid-document. Imprint text at the end of the markdown is expected and correct, and the check is silent about it.

**Fix:** If I1 fires, the imprint has been extracted from the wrong place — an inside-cover page, a back-matter insert, or a page where the footer zone extends too low. Identify the page using `profile_pdf.py --sample-pages` and add it to `skip_pages` in the manifest.

---

### 5. Cover graphic tag-line text extracted as content

**What it looks like:** Cover pages with multi-column callout text or design-element slogans produce garbled headings at the top of the markdown:

```
#### Manifesto 2015 A stronger Wales Deliver Home Rule for Wales
#### Prosperity for all Balance the budget fairly invest to Fair taxes
```

**Fix:** Add the cover page (usually page 0, sometimes pages 0 and 1) to `skip_pages` in the manifest. Run `profile_pdf.py` first — it flags pages with ≤ 5 words as candidate skips, and cover pages typically appear there alongside logo-only pages.

---

### 6. Excessive horizontal rule separators

**What it looks like:** Bespoke extraction scripts that add a `---` separator between every page section produce cluttered markdown with a horizontal rule every 15–20 lines. This is not a problem for the general extractor (`extract_manifesto.py`), which does not insert `---` between pages, but can appear in custom scripts copied from early toolkit templates.

**Fix:** In custom scripts, replace `'\n\n---\n\n'.join(md_parts)` with `'\n\n'.join(md_parts)`. Reserve `---` for genuine major section breaks (chapter openers), as identified by the page manifest.

---

## `profile_pdf.py` — preflight layout profiler

Run before writing any extraction script.  Analyses the PDF and prints:

- page count, dimensions, and per-page word counts
- suggested `Y_HEADER` / `Y_FOOTER` constants derived from repeated edge text
- running header/footer strings (text repeated on ≥ 60% of pages)
- x-coordinate histogram (25pt buckets) from sample pages, to reveal column boundaries
- font inventory (names and size ranges) from sample pages
- minimum inter-word gap — if < 4pt, use `x_tolerance=2` in `extract_words()`
- suggested `SKIP_PAGES` from pages with ≤ 5 words

```bash
python profile_pdf.py manifesto.pdf
python profile_pdf.py manifesto.pdf --sample-pages 5,12,20   # specific pages for histogram
python profile_pdf.py manifesto.pdf --json > profile.json     # machine-readable output
python profile_pdf.py manifesto.pdf --quiet                   # suppress per-page table
```

---

## `qa_check.py` — post-extraction QA scanner

Run after extraction, before manual review.  Checks:

| Code | Check |
|------|-------|
| C1 | Word-count coverage vs pdftotext baseline (requires `--pdf`) |
| E1 | Unicode replacement characters (encoding error) |
| E2 | Raw `(cid:N)` tokens not decoded |
| E3 | Non-printing control characters |
| H1 | Heading starts with a quotation mark (likely a pull quote) |
| H2 | Heading starts with a lowercase letter |
| H3 | Heading starts with a conjunction or article (sentence continuation) |
| H4 | Heading starts with punctuation |
| H5 | Adjacent same-level headings that may be a split multi-line heading |
| H6 | Heading has > 30 words (body text likely promoted) |
| B1 | Raw bullet glyph in paragraph text |
| B2 | Bullet glyph appearing mid-sentence |
| B3 | Single-word bullet item (sidebar continuation orphan) |
| P1 | Paragraph is a bare page number |
| P2 | All-caps run of ≥ 5 words (un-spaced slogan from cover/imprint) |
| P3 | Duplicate paragraph (possible running header not stripped) |
| P4 | Very short paragraph (< 4 words) |
| S1 | Missing space after sentence-ending period |
| S2 | Missing space after comma |
| S3 | Possible fused ALL-CAPS words |

```bash
python qa_check.py output.md
python qa_check.py output.md --pdf manifesto.pdf   # enables C1 coverage check
python qa_check.py output.md --pdf manifesto.pdf --strict   # exit 1 if any errors/warnings
python qa_check.py output.md --pdf manifesto.pdf --json     # machine-readable output
python qa_check.py output.md --no-colour                    # plain text (for piping)
```

---

## Page manifests

A page manifest is a YAML sidecar file that records per-page extraction overrides for a specific PDF.  It lives in `manifests/` and is passed to `extract_manifesto.py` via `--manifest`.

Copy `manifests/TEMPLATE.yaml` to start a new manifest.  Recognised per-page modes:

| Mode | Effect |
|------|--------|
| `skip` | Page is skipped entirely |
| `full-width` | Single-column extraction (ignores global col_split) |
| `single-col` | Alias for `full-width` |
| `summary-box` | Alias for `full-width` (sidebar-aware extraction is future work) |
| `two-col` | Force two-column extraction using global col_split |

Per-page `header_cut` and `footer_cut` overrides accept a number (pt) or `null` (use default).

---

## Choose your extraction mode first

Before running the script or starting a manual transcription, spend a few minutes classifying the PDF. The right mode saves significant time; the wrong one leads to repeated patching of unfixable output.

### Mode 1 — Clean text-layer PDF
The PDF has a readable text layer and a consistent layout (single column or uniform two-column). Use `extract_manifesto.py` with its defaults. Even clean PDFs need targeted manual review of:
- the contents page
- cover and front matter pages
- chapter opener and quote pages
- bullet lists near the left margin (first and last item in each list)
- pages with pull-quotes or sidebars

### Mode 2 — Mixed-layout PDF
The text layer works for most pages, but specific pages break extraction because of two- or three-column layouts, decorative standfirsts, sidebars, or subsection headings that splice into adjacent text. Use the script as a starting point, then inspect each flagged page individually. Reconstruct reading order visually — left column top-to-bottom, then right — and check bullets carefully for clipped opening phrases.

### Mode 3 — OCR / manual-rebuild PDF
The text layer is poor or corrupted. Signs: widespread garbled words, headings in nonsense fragments, whole lines missing despite reasonable word-count coverage, or paragraph order that stays wrong after column tuning. Switch to OCR or manual reconstruction early. Repeatedly patching bad extraction output is slower than starting from page images.

**Practical rule:** if a page looks visually more complex than the rest of the document, trust the page image over the text layer.

---

## When to use the script vs. manual transcription

**Use the script** when:
- The PDF is Mode 1 or Mode 2 (readable text layer, standard layout)
- You need a first draft quickly to review and correct
- The PDF is long (50+ pages) and fully manual transcription would be very slow

**Use manual transcription** (with `PROMPT.md`) when:
- The script output is below 90% coverage after tuning
- The PDF has heavy graphic design, sidebars, or rotated text on most pages (Mode 3)
- You're correcting a script draft — use the prompt as a quality standard reference

**Use both** (recommended for complex PDFs):
1. Run the script to get a structural skeleton
2. Use `PROMPT.md` as the quality standard when reviewing and filling gaps

---

## Key technical concepts

### Font-aware styling

The script reads each character's `fontname` from the PDF (via pdfplumber's `page.chars`). Font names like `Georgia,Bold` trigger `**bold**` markers; `Georgia,Italic` triggers `_italic_`. This is more reliable than guessing from font size alone.

### Two-column layout

PDFs with two columns interleave left and right column rows when read naively (this is what `pdftotext` does, and why it produces garbled output for two-column PDFs). The script splits words by x-coordinate (at the detected or specified column split), processes each column independently top-to-bottom, then concatenates them.

### Paragraph reconstruction

Within a column, lines are joined into paragraphs when the vertical gap between them is less than `--para-gap` (default 18pt). Within-paragraph line gaps are typically 12–16pt; between-paragraph gaps are typically 20pt or more. This threshold is the most important tuning parameter.

### Running header stripping

Repeated section titles printed at the top of each page (a common design pattern) are stripped by ignoring any text with a `top` coordinate less than `--header-cut` (default 65pt from the top of the page).

---

## Completeness standard

A transcription is complete when every word in the PDF is reproduced verbatim in the Markdown output. The word-count ratio is a useful proxy, but **do not rely on it alone** — a file can sit near 100% and still contain truncated headings, duplicated pull-quotes, clipped bullet openings, or wrong column order.

### Coverage ranges

- **95–103%**: Healthy. Content is present; delta is expected from Markdown tokens and stripped footers.
- **103–105%**: Can be fine if manually restored clipped text, rebuilt headings, or Markdown markers push the count slightly above 103%. Check for duplicated sections before accepting.
- **97–100%**: Ideal. Small undercount is stripped footers; small overcount is Markdown syntax tokens.
- **< 95%**: Something is likely missing — identify which pages extracted poorly and fill the gaps.
- **> 105%**: Check for duplicated sections, repeated headings, or pull-quote text included twice.

### Always verify beyond word count

Even at healthy coverage, manually check:
- every major heading against the PDF
- the contents page (headings and order)
- the first and last bullet in each list
- pages with unusually low extraction quality
- pages with sidebars, pull-quotes, or large decorative text

Check coverage with:
```bash
pdftotext manifesto.pdf - | wc -w   # PDF word count
wc -w manifesto.md                  # Markdown word count
```

---

## Working from an existing partial file

Sometimes a partially-transcribed Markdown file already exists for a manifesto — either from a previous session or from another source. The instinct is to open it, check the word-count coverage, and patch whatever is missing. **This approach has a critical blind spot: it trusts the existing file's headings and body text without verifying them against the PDF.**

Silent truncation is hard to spot. A heading like "Victims Are Forgotten" looks complete in isolation; only a direct comparison against the PDF reveals it should read "Terrorists Rejoice as Victims Are Forgotten". Word-count coverage will not catch this — the markdown word count stays close to 100% while a heading has lost half its words.

### The correct workflow when an existing partial file exists

1. **Run `extract_manifesto.py` fresh** to produce an independent draft from the PDF, regardless of the existing file's apparent quality.

   ```bash
   python extract_manifesto.py path/to/manifesto.pdf
   # produces manifesto-extracted.md
   ```

2. **Diff the two files** before touching either one. The diff tells you which content is in the existing file but not the fresh extract (potential additions from the existing file worth keeping) and which is in the fresh extract but not the existing file (potential omissions or truncations in the existing file).

   ```bash
   diff --unified existing.md manifesto-extracted.md | less
   ```

3. **Resolve conflicts in favour of the PDF**, not the existing file. Where the two disagree on a heading or phrase, check the PDF directly (e.g. via pdfplumber char-level extraction or a PDF viewer) and use whatever the PDF says.

4. **Run the heading verifier** on whichever file you plan to commit:

   ```bash
   python check_headings.py manifesto.pdf output.md
   ```

   Fix every `TRUNCATED`, `ALTERED`, or `NOT FOUND` issue before finishing.

### Why not just patch the existing file directly?

- You cannot know which parts of the existing file are accurate without an independent reference. The diff gives you that reference.
- Heading truncations are invisible in a plain text review. Only a font-size-aware PDF extraction or a side-by-side comparison against the original will surface them.
- Body text alterations ("on to" → "onto", "ex terrorists" → "ex-terrorists") are similarly undetectable from the Markdown alone.

**Rule of thumb:** treat the existing partial file as a convenience starting point, not a source of truth. The PDF is the source of truth.

---

## Lessons learned (from Alliance manifesto series)

These insights shaped the design of the toolkit:

- **`pdftotext` garbles two-column PDFs** — it interleaves rows from both columns, producing nonsense. Always use pdfplumber directly for column-aware extraction.
- **para_gap=18 is a robust default** — within-paragraph gaps are ~12–16pt; between-paragraph gaps are ~20pt. A threshold of 18 catches the latter without false breaks on most UK party manifestos.
- **header_cut=65 handles most running headers** — the typical section-title strip at the top of each page occupies roughly the top 36–55pt. A cut at 65pt clears it safely.
- **Bold lead sentences on bullets** are a common formatting convention across multiple parties. The `* **Bold phrase.** Rest of text.` pattern should always be checked.
- **Italic is often used for document titles and proper nouns** (e.g. `_Good Friday Agreement_`, `_Agenda for Democracy_`). These are easy to miss in a plain-text pass.
- **Word count inflation from Markdown syntax is normal** — `wc -w` counts `##`, `---`, `*`, `**` as words. An overcount of 1–2% is expected and not a sign of added content.

---

## Lessons learned (from UKIP manifesto series)

The UKIP 2015 manifesto (76-page landscape PDF with a mixed 2-/3-column layout and a DIN-family type system) stress-tested every part of the toolkit. These additions complement the Alliance lessons above.

### Layout and page orientation

- **Check page dimensions before setting any y-cutoffs.** Portrait A4 pages are typically 842×595pt; landscape A4 is 595×842pt — but in practice many landscape PDFs report ~884×637px. Always inspect `page.height` and `page.width` on the first body page and derive `Y_FOOTER` from the actual height, not a constant.
- **Manifesto PDFs can have varying column counts page to page** (2-col, 3-col, and narrow-2-col all in the same document). A single fixed `--col-split` will mis-parse some pages. Use dynamic column detection (see below) rather than a single fixed split coordinate for visually complex PDFs.

### Dynamic column detection

Rather than a fixed split x-coordinate, scan each page's body-char x-distribution to find the column gap automatically:

```python
def find_column_splits(chars, y_footer, bucket_px=5, min_gap_width=10, max_chars_in_gap=2):
    body = [c for c in chars if c["size"] < 14 and c["text"].strip() and 0 < c["top"] < y_footer]
    if not body:
        return []
    bkt = defaultdict(int)
    for c in body:
        bkt[int(c["x0"] // bucket_px) * bucket_px] += 1
    x_vals = sorted(bkt.keys())
    splits, in_gap, gap_start = [], False, None
    for x in x_vals:
        if bkt[x] <= max_chars_in_gap and not in_gap:
            in_gap, gap_start = True, x
        elif bkt[x] > max_chars_in_gap and in_gap:
            in_gap = False
            w = x - gap_start
            if w >= min_gap_width:
                splits.append(gap_start + w // 2)
    return [s for s in splits if 150 < s < 750]  # ignore margin artefacts
```

The number of splits returned tells you the column count: 0 → single-column, 1 → two-column, 2 → three-column. Pages with the same layout often return the same split positions; pages with different layouts return different ones — handle both correctly by checking `len(splits)` per page.

### Word boundary reconstruction from `page.chars`

Some PDFs (particularly those with tightly-kerned sans-serif fonts) have character x-coordinates so close together that naive word reconstruction fails. The correct threshold for the gap between consecutive characters:

```python
threshold = max(1.5, prev_char_size * 0.15)
```

At size 9pt (typical body text), this gives a threshold of 1.8px, which correctly separates letter gaps (~0px) from word gaps (~2.3px). The old heuristic of `size * 0.45` (threshold 4.1px at sz=9) will miss word boundaries entirely — whole sentences collapse into a single token.

### Per-character font classification and mixed y-rows

The Alliance lessons already note that dominant-font classification is unreliable. The UKIP work shows this more precisely: **body text and sub-headings regularly share the same y-coordinate on the same line.** Classify each character individually, then partition each y-row into heading chars and body chars before assembling text:

```python
h_chars = [c for c in row if is_heading_char(c)]
b_chars = [c for c in row if not is_heading_char(c) and ...]
```

Emit heading chars and body chars separately, ordered by their x-position — do not merge them into one string first.

### Heading classification precision

- **Set both a lower and upper size bound** on `is_heading_char`. A check like `"Bold" in font and size >= 11` will catch attribution text, pull-quote text, or chapter titles in the same bold family at larger sizes. Instead use `"Bold" in font and 10.5 <= size <= 13.5` (or whatever size range corresponds to body-level sub-headings in that specific document).
- **Exclude "Medium" weight** from heading detection. Font names containing "Medium" (e.g. `DINOT-Medium`) are typically used for pull-quotes or decorative text at large sizes, not for body-level sub-headings.

### Distinguishing headings from bold callout text

At sub-heading size (sz≈11), some bold paragraphs are genuine section headings ("CORPORATION TAX DODGING") and some are bold callout sentences ("Both Labour and the Tories have failed on immigration"). Use an all-caps proportion heuristic to tell them apart:

```python
def looks_like_subheading(text, threshold=0.60):
    """True if ≥60% of words are ALL_CAPS, digits, or known abbreviations."""
    ABBREVS = {"NHS", "GP", "EU", "VAT", "UK", "UKIP", "UN", "NATO", "GDP", ...}
    words = [w for w in text.split() if w]
    if not words:
        return True
    caps = sum(1 for w in words
               if re.sub(r"[^A-Za-z0-9]", "", w).isupper()
               or re.sub(r"[^A-Za-z0-9]", "", w) in ABBREVS
               or re.match(r'^[\d£,\.%\-+]+$', w))
    return (caps / len(words)) >= threshold
```

Use this to decide `### HEADING` vs `**Bold callout.**`.

### Multi-line heading merging

Some headings split across two y-rows (12–20px apart). Merge them by tracking the y-position of the last heading emitted:

```python
if (prev_type == "heading" and prev_head_y is not None
        and abs(current_y - prev_head_y) <= 20
        and output[-1].startswith("### ")
        and looks_like_subheading(new_text)):   # ← crucial guard
    output[-1] += " " + new_text
else:
    emit_heading(new_text)
```

The `looks_like_subheading` guard is critical — without it, bold body sentences that immediately follow a heading (within 20px) get absorbed into the heading line.

### Two headings at the same y in different columns

When column detection fails for a page, two column headings at the same y-position are merged into one string by `chars_to_text`. Detect this by checking for a large internal x-gap in the heading chars:

```python
sorted_h = sorted(h_chars, key=lambda c: c["x0"])
groups = [[sorted_h[0]]]
for c in sorted_h[1:]:
    if c["x0"] - groups[-1][-1]["x1"] > 40:   # 40px gap = column boundary
        groups.append([])
    groups[-1].append(c)
# emit each group as a separate heading
```

### Section intro / chapter title pages

Manifesto PDFs often have dedicated chapter-opener pages with large decorative text (e.g. DIN-Black at sz≥50), a pull quote, and an attribution. Detect these pages by checking for the large title character early on the page (`top < 200`), then extract the three elements separately rather than treating them as body pages. The large title becomes a `## SECTION` heading, the pull quote becomes a block quote or bold paragraph, and the attribution becomes `**Name, Title**`.

### Deduplicating two-page spread headings

If a chapter opener spans two consecutive PDF pages (a design spread), `extract_page()` will emit the same `## SECTION TITLE` twice. Clean this up in post-processing:

```python
# Remove consecutive duplicate headings
md = re.sub(r"(^#{1,3} .+)(\n\n\1)+", r"\1", md, flags=re.M)
```

### PDF artefacts in font names

Some PDFs contain characters with corrupted or deliberately mixed-case font glyph representations (e.g. `DeFeNCe` instead of `DEFENCE`). These appear to come from how the original design software embedded glyphs. There is no general fix — add a specific substitution in `clean_markdown()` for any known artefacts discovered during review.

---

## Lessons learned (from UKIP 2017 manifesto)

The UKIP 2017 manifesto (64-page portrait PDF with a strict Raleway/Aileron type system and a varying 1-/2-column layout) introduced several techniques not covered by the 2015 work. See `../Python scripts/extract_ukip_2017.py` for the reference implementation (99.0% coverage).

### Use `page.extract_words()` instead of manual char reconstruction

The 2015 lessons document a word-boundary threshold (`max(1.5, prev_char_size * 0.15)`) for reconstructing words from `page.chars`. For most PDFs, `page.extract_words()` is simpler and equally reliable — it uses the same x-gap heuristic internally. Pass `extra_attrs=['fontname', 'size']` to include font metadata on each word:

```python
words = page.extract_words(keep_blank_chars=False, extra_attrs=['fontname', 'size'])
```

Then build a `char_lookup` (y-bucket → chars) from `page.chars` separately for font resolution at the character level. This gives clean word objects with position data, while keeping precise per-character font information for classification.

**When to fall back to `page.chars` directly:** if `extract_words()` merges words that should be separate (typically only in very tight-kerning display fonts), then manual reconstruction with the size-relative threshold is needed. For standard body fonts this is rare.

### Semantic word classification rather than inline style markers

The generic script (`extract_manifesto.py`) applies inline `**bold**` and `_italic_` markers to individual words based on font weight. For PDFs with a strict typographic system (where each font face has a fixed semantic role), it is more reliable to classify each word into a semantic type and render the whole paragraph accordingly:

```python
# Each word gets one of: chapter | attribution | subhead | intro | pullquote | body | bold_body
def classify_word(word, char_lookup):
    # resolve dominant font+size from char_lookup at this word's position
    ...
    if sz >= 22 and 'Raleway' in fn:      return 'chapter'
    if 'Raleway-SemiBold' in fn and sz >= 13: return 'attribution'
    if 'Raleway-SemiBold' in fn and 10 <= sz < 13: return 'subhead'
    if 'Raleway-Light' in fn and sz >= 11:   return 'intro'
    if fn == 'Raleway' and 11 <= sz < 22:    return 'pullquote'
    if 'Aileron-Light' in fn and sz <= 11:   return 'body'
    if 'Aileron-SemiBold' in fn and sz <= 11: return 'bold_body'
    if sz <= 11: return 'body'   # fallback: catches small-font pages (e.g. Contents)
    return 'other'
```

Each paragraph then gets a single type from its dominant word classification, and the Markdown renderer maps types to output format (`## chapter`, `### subhead`, `> pullquote`, `**attribution**`, etc.).

**Important:** the small-font fallback (`if sz <= 11: return 'body'`) is critical. Without it, legitimate small-body-font content — such as a Contents page using the heading font at sz=9 — will be misclassified if you add an explicit "footer" rule for small-font heading-family text. Y-coordinate cutoffs (`Y_HEADER`/`Y_FOOTER`) are sufficient to strip actual running headers and footers; do not add a font-size-based footer classification on top.

### Exclude full-width elements from column detection

Column detection works by finding a gap in the x0 histogram of word positions. Full-width elements — large chapter headings and intro paragraphs in a distinct font (Raleway-Light) that span both columns — fill the column gap and prevent correct detection. Filter to body-level words only before computing the histogram:

```python
def should_include_for_col_detect(word):
    fn = base_font(word.get('fontname', ''))
    sz = word.get('size', 0)
    if 'Aileron' in fn and sz <= 11: return True
    if 'Raleway-SemiBold' in fn and sz <= 13: return True
    if fn == 'Raleway' and 10 <= sz <= 13: return True
    return False  # excludes Raleway-Light (intro), large chapter headings
```

Apply this filter before passing words to the x0 histogram/gap detection function.

### Three-pass column extraction: preamble + left + right

Two-column pages often also contain full-width elements (a chapter heading and intro paragraph) that span both columns. Naively splitting at the column boundary will:

- Break a multi-word chapter heading across two `##` blocks (`"Brexit Britain:"` + `"The Key Tests"`)
- Fragment intro paragraphs across left and right column passes

The fix is a three-pass approach:

1. **Identify full-width rows** — find y-buckets where chapter or intro content crosses the column split:

```python
def identify_full_width_rows(words, col_split, char_lookup):
    line_map = defaultdict(list)
    for w in words:
        line_map[bucket(w['top'])].append(w)
    full_width_ys = set()
    for y, row_words in line_map.items():
        cls_list = [classify_word(w, char_lookup) for w in row_words]
        has_chapter = any(cls == 'chapter' for cls in cls_list)
        has_intro   = any(cls == 'intro' for cls in cls_list)
        if not (has_chapter or has_intro):
            continue
        x0_vals = [w['x0'] for w in row_words]
        min_x, max_x = min(x0_vals), max(x0_vals)
        if (min_x < col_split - 20 and max_x > col_split + 20):
            full_width_ys.add(y)
        elif has_chapter and min_x < col_split - 60:
            full_width_ys.add(y)  # chapter starting well to the left counts too
    return full_width_ys
```

2. **Extract in three passes**, using `allowed_ys` / `excluded_ys` parameters to route rows to the correct pass:

```python
fw_ys    = identify_full_width_rows(content_words, col_split, char_lookup)
preamble = words_to_paragraphs(content_words, char_lookup, allowed_ys=fw_ys,  para_gap=25)
left     = words_to_paragraphs(content_words, char_lookup, x_max=col_split,   excluded_ys=fw_ys)
right    = words_to_paragraphs(content_words, char_lookup, x_min=col_split,   excluded_ys=fw_ys)
all_paras.extend(preamble + left + right)
```

The preamble comes first so that chapter headings and intro paragraphs appear before the two-column body text they introduce.

### Differentiated `para_gap` by content zone

A single `para_gap` value does not fit all content types in the same document. For the UKIP 2017 type system:

| Zone | Font | Inter-line gap within para | Between-para gap | Correct `para_gap` |
|------|------|---------------------------|-----------------|-------------------|
| Body columns | Aileron-Light | ~10–12pt | ~18–22pt | 14 |
| Preamble (intro) | Raleway-Light | ~16–20pt | ~40pt+ | 25 |

Using `para_gap=14` for the preamble pass fragments Raleway-Light intro paragraphs into individual lines. Using `para_gap=25` for body columns merges separate paragraphs. Pass different values to each call:

```python
preamble = words_to_paragraphs(..., allowed_ys=fw_ys, para_gap=25)  # wider gap for intro text
left     = words_to_paragraphs(..., x_max=col_split,  para_gap=14)  # tight gap for body columns
right    = words_to_paragraphs(..., x_min=col_split,  para_gap=14)
```

Before fixing this, always inspect the actual inter-line gaps for intro text on a few section-opener pages. Raleway-Light at sz=11–13 in the 2017 UKIP manifesto has within-paragraph gaps of 16–20pt, well above the body `para_gap=14`.

### Pull-quote vs. subheading at the same font and size

The same font+size combination (Raleway-SemiBold at sz≈11) was used for both `### section headings` and `> pull-quotes`. The 2015 lesson describes the all-caps heuristic in general; the precise implementation that worked for 2017:

```python
def is_pullquote(text):
    t = text.strip()
    if t.startswith(('"', "'", '\u201c')):   # opening quote mark → always a pull-quote
        return True
    words = [w for w in t.split() if w]
    ABBREVS = {'NHS', 'GP', 'EU', 'VAT', 'UK', 'UKIP', ...}  # known acronyms count as caps
    caps_count = sum(
        1 for w in words
        if re.sub(r'[^A-Za-z]', '', w).isupper()
        or re.sub(r'[^A-Za-z0-9]', '', w) in ABBREVS
        or re.match(r'^[\d£€$,\.%\-+:]+$', w)
    )
    return (caps_count / len(words)) < 0.55   # <55% caps → pull-quote
```

Classify blocks with ≥55% caps as `### subhead`; those with <55% caps as `> pullquote`. A threshold of 0.55 (not 0.60 as in some earlier notes) was found to be more reliable across the 2017 manifesto. Tune this per-document.

### Attribution + role merging

Speaker attributions appear on two consecutive lines: the name (Raleway-SemiBold ≥13pt) and a short role line (often the same or a neighbouring font class). Merge them in post-processing:

```python
def merge_attribution_role(paras):
    result = []
    i = 0
    while i < len(paras):
        p = paras[i]
        if (p['type'] == 'attribution' and i + 1 < len(paras)
                and len(paras[i+1]['text'].split()) <= 6):
            merged = p['text'] + ', ' + paras[i+1]['text']
            result.append({'type': 'attribution', 'text': merged})
            i += 2
        else:
            result.append(p)
            i += 1
    return result
```

The `<= 6 words` guard prevents accidentally merging a full body sentence into the attribution line. The result renders as `**Gerard Batten MEP, Brexit Spokesman**`.

---

## Lessons learned (from DUP 2010 manifesto)

The DUP 2010 manifesto (37-page portrait PDF using a Myriad/Formata type system with a consistent two-column layout) introduced several challenges not covered by earlier work: font size ambiguity within a single family, mid-page decorative elements outside the header/footer zone, and bullet classification where heading and bullet fonts are identical. See `../Python scripts/extract_dup_2010.py` for the reference implementation (94.3% reported coverage; ~99% effective content coverage after accounting for correctly excluded running headers, decorative URL strips, and skipped non-content pages).

### Same font family at different sizes: always add a size threshold

A single font family can serve several distinct semantic roles depending on point size. In the DUP 2010 manifesto, the Formata family appears at four size levels:

| Size (pt) | Role |
|-----------|------|
| ≈11 | Category labels in the "Key Goals at a glance" table (body context) |
| ≈14 | Decorative campaign-theme text in the party leader letter (body context) |
| ≈18.7 | Section intro sub-headings (e.g. "BY PARTY LEADER Rt Hon Peter Robinson") |
| 37–62 | Main section headings (Economy, Business, Education…) |

A naive `if 'Formata' in fn: return 'heading'` rule misclassifies the sz≈14 decorative text as a `## section heading`. The fix is a size threshold matched to the smallest genuine heading:

```python
if 'Formata' in fn and word.get('size', 0) >= 18:
    return 'heading'
# falls through to 'body' for sz < 18
```

The general principle: whenever a font family appears at more than two size levels, measure the actual sizes on a few diagnostic pages before writing the classification rule, then set a minimum (and where needed, maximum) size bound rather than checking font name alone.

### Decorative mid-page elements: strip by font name, not y-coordinate

Some PDFs have a recurring decorative element that sits in the middle of the page — within the content y-zone — rather than at the top or bottom. In the DUP 2010 manifesto, each two-page spread contains a URL and page number strip (e.g. `www.dupwin.com 14 15`) in `Myriad-CnBoldItalic` and `Myriad-CnSemiboldItalic`, appearing at y≈280–300 (roughly page centre). Y-coordinate cutoffs (`Y_HEADER`, `Y_FOOTER`) cannot reach this.

The fix: identify which font names are used exclusively for decorative purposes and exclude them explicitly:

```python
def is_decorative(word):
    fn = base_font(word.get('fontname', ''))
    return 'CnBoldItalic' in fn or 'CnSemiboldItalic' in fn
```

To discover the right font names, run a font frequency diagnosis on a few pages and look for any font that appears on every page but never in body content you want to keep. Italic variants of the body bold font are a common signal: `CnBold` is used for content; `CnBoldItalic` is decorative.

### Same bold font for headings and bullets: detect at the assembled line level

When one font (e.g. Myriad-CnBold) is used for both `###` subsection headings and dash-prefixed bullet items (e.g. `-unionist unity`), `classify_word()` — which sees one word at a time — cannot distinguish them: only the first word of a bullet item starts with `-`, so the line's dominant class remains `'subheading'`.

Fix this after assembling the full line text, not at the word level:

```python
# After joining line_words into line_text:
if dom == 'subheading' and line_text.startswith('-'):
    dom = 'bullet'
    line_text = line_text[1:].strip()   # remove the leading dash
```

The general lesson: bullet detection requires seeing the whole assembled line. Font classification alone is insufficient when the same typeface is reused across semantic roles.

### Bullet flush logic: flush on each marker, not on type-change

When consecutive bullet items have small y-gaps (common in compact two-column layouts), a standard "flush when type changes" buffer merges all items into one paragraph. The correct rule is to flush before each new bullet marker — a `•` character or a dash-prefix line — while still allowing genuine text-wrapping continuation lines to accumulate:

```python
if dom == 'bullet':
    new_item = has_bullet_char or has_dash_prefix or buf_type != 'bullet' or gap >= PARA_GAP
    if new_item:
        flush()
    buf_text.append(line_text)
    buf_type = 'bullet'
```

This correctly separates `•` items and dash-prefix items even when their y-gaps are tight, while still joining a wrapped second line (same font, no marker, small gap) into the current buffer.

### Drop-cap artifacts: fix with a regex in post-processing

PDFs using decorative drop caps emit the oversized first letter as a separate word at a slightly different y-position, so pdfplumber returns e.g. `N` + `orthern`, `G` + `rowing`, `T` + `he` for every paragraph opener. Fix in post-processing:

```python
# Drop-cap artefacts at paragraph starts: "N orthern" → "Northern"
text = re.sub(r'(?m)^([B-HJ-Z]) ([a-z])', r'\1\2', text)
```

`(?m)` makes `^` match the start of each line. The character class `[B-HJ-Z]` excludes 'A' (article — "A budget...") and 'I' (pronoun — "I believe..."), which are legitimate standalone word starts. Using `[A-Z]` would incorrectly merge these: "A budget" → "Abudget". All other uppercase letters are safe to match, as no common English word is a single letter other than 'A' and 'I'.

### PARA_GAP must exceed the largest within-paragraph line gap

At body text sz≈9pt with generous leading, within-paragraph line gaps can reach 16pt. A PARA_GAP of 15 will then incorrectly split those paragraphs into individual lines. Always measure actual gaps before setting PARA_GAP:

```python
with pdfplumber.open("manifesto.pdf") as pdf:
    page = pdf.pages[5]
    words = page.extract_words(keep_blank_chars=False, extra_attrs=['fontname'])
    tops = sorted(set(round(w['top'] / 2) * 2 for w in words
                      if 'Condensed' in w.get('fontname', '')))
    for a, b in zip(tops, tops[1:]):
        if b - a < 30:   # ignore page-level jumps
            print(f"gap: {b - a:.1f}pt")
```

In the DUP 2010 manifesto, within-paragraph gaps are 12–16pt and between-paragraph gaps are 18–20pt; PARA_GAP=17 sits cleanly between them. A value of 15 caused false splits on lines with 16pt gaps.

---

## Lessons learned (from DUP 2015 manifesto)

The DUP 2015 manifesto (17-page landscape 1251×902pt PDF using the Gotham font family, 4-column layout) is the first case in the archive requiring a 4-column landscape-page extractor. The generic script produced only 68.8% coverage. The final bespoke script reached 96.2% coverage. See `../Python scripts/extract_dup_2015.py` for the reference implementation.

### 4-column landscape layout with wide-boundary large text

The 4-column layout divides each page into four equal-width strips (split boundaries at x≈315, 630, 915; column left margins at ≈73, 342, 668, 937). This is the same column detection used for UKIP 2015, but the landscape orientation (width 1251pt, height 902pt) means all y-cutoffs must be derived from `page.height`, not portrait-page constants.

**Large intro text** (Gotham-Book/Bold, sz≥13) spans the full width of two adjacent columns — its lines run from the left edge of col1 all the way to the right edge of col2. Applying the strict 315pt column boundary cuts these lines in half and loses the right portion. Handle this with a wide-boundary mode per font size:

- **Col1** captures: strict body text (x=0–315) **plus** all sz≥13 text from x=0–630
- **Col2** captures: strict body text only (x=315–630); sz≥13 excluded (already in col1)
- **Col3/col4** follow the same pattern for the right half (split at x=630)

```python
w1 = _words_for_col(words, x_min=0, x_max=C1_MAX,
                    x_min_large=0, x_max_large=WIDE_LEFT_MAX,
                    exclude_heading2=True)
w2 = _words_for_col(words, x_min=C1_MAX, x_max=C2_MAX,
                    exclude_large=True, exclude_heading2=True)
```

This avoids duplicating large-text words while keeping small body text within its correct narrow column.

### Dingbat bullet markers at y-offset: increase Y_TOL

Webdings and Wingdings bullet markers often appear at a slightly different y-position than adjacent body text — typically 2–3pt below the text baseline. With a standard Y_TOL of 4pt, the marker and its text fall in different y-buckets, producing an orphaned marker row with no text.

**Fix:** increase Y_TOL to 6pt:

```python
Y_TOL = 6   # was 4 — increased to keep Webdings markers in the same row as their text
```

Verify by checking the actual y-positions of a bullet marker and its adjacent body word on a diagnostic page. If the observed offset exceeds `Y_TOL/2`, increase Y_TOL by 2pt and re-run.

### Use raw y-coordinates for paragraph gap calculation, not bucket y

Y-bucketing groups words into rows by rounding each word's `top` coordinate — but using the **bucket y-value** for inter-row gap measurement introduces rounding artifacts. Example: two lines at y=681.0 and y=694.0 (actual whitespace: 13pt) bucket to y=678 and y=696 (bucket gap: 18pt). If PARA_GAP=18, the bucket-based check fires and incorrectly splits a paragraph that should stay joined.

**Fix:** track raw `y_min` and `y_max` per assembled row, and calculate the gap from actual word coordinates:

```python
y_raw_min = min(w['top'] for w in row)
y_raw_max = max(w['top'] for w in row)
# ...
gap = current_y_raw_min - prev_y_raw_max   # actual whitespace between rows
```

This eliminates false paragraph breaks caused purely by bucketing rounding at exactly-PARA_GAP distances.

### Row-level bullet detection: check leftmost word, not per-word

Checking each word's x-coordinate against the column margin + indent threshold produces wrong results when a heading-style line contains words naturally spread further right (as all heading lines do). For example, "Rt. Hon. Peter Robinson MLA" — "Rt." sits at the column margin, but "Hon." is ~15pt further right and would incorrectly trigger the bullet classification.

**Fix:** check only the **leftmost word's x-coordinate** in the row:

```python
leftmost_x = min(w['x0'] for w in row)
row_is_indented = (leftmost_x > nearest_col_margin(leftmost_x) + BULLET_INDENT)
```

If the leftmost word is at the column margin, the row is a heading regardless of where subsequent words fall.

### Column-aware header zone extraction

When processing large heading text (heading2 words) in the header zone, a single pass across all columns will merge left- and right-column headings that happen to share a similar y-coordinate — common in 4-column layouts where independent section titles appear side-by-side.

**Fix:** process each column's header zone independently with a per-column gap threshold:

```python
col_bounds = [(0, C1_MAX), (C1_MAX, C2_MAX), (C2_MAX, C3_MAX), (C3_MAX, float('inf'))]
for x_min, x_max in col_bounds:
    col_words = [w for w in zone if x_min <= w['x0'] < x_max]
    # assemble headings within this column only, with ~50pt inter-heading gap
```

A 50pt gap threshold (within each column) handles multi-line titles in the same column zone without merging across column boundaries.

### Body content in the header y-zone: use y_min=Y_META with exclusion

Many extractors define a `Y_BODY` cutoff — content above this y-coordinate is assumed to be the chapter-heading zone and is excluded from the body pass. This breaks on:

- **Continuation pages** where body text starts near the top with no chapter heading
- **Section label rows** (e.g. "WHERE WE ARE / FROM WESTMINSTER, WE WANT:") that sit just above Y_BODY

**Fix:** set body column `y_min=Y_META` (just below the top printer margin, typically ~20pt) and add `exclude_heading2=True` to avoid double-counting the large titles already emitted by the header zone pass:

```python
# Instead of: y_min=Y_BODY (which silently drops near-top content)
# Use:        y_min=Y_META, exclude_heading2=True
words_for_col(..., y_min=Y_META, exclude_heading2=True)
```

Also exclude dingbat bullet markers in the `exclude_heading2` branch — they have no text content and have already been consumed when assembling their row.

### Multi-line bullet items: use gap threshold, not unconditional break

A paragraph-assembly rule that forces a new paragraph on every transition into `'bullet'` role incorrectly splits bullet items that wrap to a second line. In compact layouts the wrapped line appears just one line-height (< PARA_GAP) below the bullet marker.

**Fix:** start a new bullet paragraph only when the gap meets the threshold:

```python
new_para = (
    prev_y is None
    or role != buf_role
    or gap >= effective_gap
    or (role == 'bullet' and gap >= PARA_GAP)   # ← not: or role == 'bullet'
)
```

A wrapped continuation line (same bullet, gap < PARA_GAP) then accumulates into the current buffer rather than starting a fresh bullet item.

### Drop-cap regex: exclude 'A' and 'I'

The standard post-processing drop-cap regex `re.sub(r'(?m)^([A-Z]) ([a-z])', r'\1\2', text)` is not universally safe. The letters 'A' (article) and 'I' (pronoun) are common standalone words that can legitimately begin a paragraph: "A budget proposal..." or "I believe that...". The regex incorrectly merges these: "A budget" → "Abudget".

**Fix:** exclude 'A' and 'I' from the character class:

```python
text = re.sub(r'(?m)^([B-HJ-Z]) ([a-z])', r'\1\2', text)
```

This still catches all 24 other uppercase letters, which are never standalone article or pronoun words at the start of a paragraph in English. The DUP 2010 section of this README documents the original regex as matching `[A-Z]` — that entry should be considered superseded by this correction.

---

## Lessons learned (from Welsh manifesto series)

The Welsh manifesto series (Welsh Conservative 2019, Welsh Labour 2017, 2015, and 2010) introduced a cluster of challenges that don't appear together in any other series in the archive: CID-encoded fonts, bilingual PDFs, multi-column extraction with tight x-tolerances, drop-cap merging, and numbered-list paragraph detection. Each extractor reached ≥96% effective coverage; the scripts live at `../scripts/extract_welsh_*.py`.

---

### CID-encoded fonts: +29 offset with per-token exceptions

PDFs that embed a custom font subset without a standard encoding table report characters as `(cid:N)` tokens rather than Unicode. The Welsh Labour 2017 manifesto is the only CID-encoded file in the archive so far.

**The +29 rule:** Most printable CID values map to ASCII by `chr(cid + 29)`. This works for the bulk of the alphabet but has documented exceptions.

```python
CID_MAP = {
    # exceptions to the +29 rule — map to explicit Unicode or '' to suppress
    57:  '8',    # digit '8'
    58:  '9',    # digit '9'
    514: '',     # silent artifact — suppress entirely
    581: '',     # paragraph-level marker — suppress entirely
}

def decode_cid(token: str) -> str:
    m = re.match(r'\(cid:(\d+)\)', token)
    if not m:
        return token
    n = int(m.group(1))
    if n in CID_MAP:
        return CID_MAP[n]
    c = chr(n + 29)
    return c if c.isprintable() else ''
```

**Silent CID artifacts:** Two CID values (`514` and `581`) appeared as typographic artifacts — `cid:514` mid-sentence (visually invisible in the PDF) and `cid:581` as a paragraph-level spacer. Both were initially decoded as `•` (bullet character) because they passed the +29 rule, producing spurious mid-sentence bullets and false paragraph splits. Mapping them to `''` suppressed them entirely.

**Diagnostic step:** Before writing a CID extractor, dump all unique CID values from the PDF and verify each one independently against the rendered PDF:

```python
import re, pdfplumber
with pdfplumber.open('manifesto.pdf') as pdf:
    for pg in pdf.pages[:10]:
        for c in pg.chars:
            if c['text'].startswith('(cid:'):
                print(c['text'], repr(chr(int(re.search(r'\d+', c['text']).group()) + 29)))
```

Never assume the +29 rule is universal — test every CID token before shipping.

---

### Bilingual PDFs: filter by page range, not font

The Welsh Labour 2017 manifesto is bilingual: pages 1–114 are in Welsh, pages 116–231 are in English (with a title page at 115). Both language sections use identical fonts and layouts, making font-based filtering impossible.

**Fix:** hard-code the English page range as constants and slice the pages list accordingly:

```python
ENGLISH_START = 115   # 0-indexed first English page
ENGLISH_END   = 229   # 0-indexed last English page (inclusive)
# ...
for pg_num in range(ENGLISH_START, ENGLISH_END + 1):
    ...
```

To locate the boundary, find the dividing title page visually in a PDF viewer and record its 0-indexed page number. Check the last few English pages to confirm `ENGLISH_END` before the back matter.

---

### Three-column extraction: always tune x_tolerance first

The Welsh Labour 2010 manifesto (three-column A4 portrait, NeoSansPro + Baskerville) uses tight inter-word kerning: gaps between adjacent words are ~3pt at 12pt body size. pdfplumber's default `x_tolerance=5` merges consecutive words into runs.

**Fix:** pass `x_tolerance=2` to `extract_words()`:

```python
words = page.extract_words(
    keep_blank_chars=False,
    y_tolerance=3,
    x_tolerance=2,        # ← critical: default 5 merges words at this font/size
    extra_attrs=['size', 'fontname'],
)
```

**Diagnostic step:** before setting constants, examine a sample page with `x_tolerance=5` (default) and `x_tolerance=2` and compare the word counts. A page that yields 30 "words" at x_tolerance=5 but 90 at x_tolerance=2 is a clear signal that the default is wrong.

**Column boundaries** for a three-column A4 portrait layout should be measured from the PDF directly (examine the x-coordinates of the first word in each column across 2–3 sample pages), not guessed. The 2010 constants were:

```python
COL1_END = 215   # left column:   x0 < 215
COL2_END = 382   # middle column: 215 ≤ x0 < 382
                 # right column:  x0 ≥ 382
```

Process each column's words independently top-to-bottom; never merge words from different columns before paragraph assembly.

---

### Drop-cap merging: merge at the word list level, not post-processing

Several Welsh manifesto PDFs (Welsh Labour 2015, 2017) render the first letter of chapter-intro paragraphs as an oversized drop-cap at a different y-position and font size than the rest of the paragraph.

**Detection:** the drop-cap word has `size ≥ 25` (or `≥ 60` on full splash pages), while the continuation text is at normal body size.

**Fix:** locate the drop-cap word, find the first body word whose y-bucket matches the drop-cap's y-bucket, and merge them in the word list before calling `words_to_paras()`:

```python
if dropcap_ws:
    dropcap_letter = clean(dropcap_ws[0]['text'])
    dropcap_y = bucket(dropcap_ws[0]['top'])
    for i, w in enumerate(body_ws):
        if abs(bucket(w['top']) - dropcap_y) < 8:
            merged = dict(w, text=dropcap_letter + w['text'])
            body_ws[i] = merged
            break
```

This is cleaner than the post-processing regex approach (documented in the DUP sections) because it handles cases where the dropcap letter is not at the very start of a line after paragraph assembly.

---

### Splash pages with body text: always extract both the title and the body

A "splash page" (large title only) does not always mean the page has no body text. In the Welsh Labour 2015 manifesto, the two foreword splash pages each had 300+ body words at normal body size below the drop-cap title. These were silently lost because the splash handler only called `extract_splash_title()` and never inspected the body zone.

**Rule:** for every splash page, check whether any body-size words exist below the title, and if so, pass them through the normal paragraph assembler:

```python
# After emitting the splash title heading:
body_paras = extract_splash_body(page)   # extract_words filtered to sz < 12
all_paras.extend(body_paras)
```

A splash page with zero body words is fine — `extract_splash_body()` will return `[]`. The cost of calling it is negligible; the cost of skipping it is missing several hundred words per foreword page.

---

### Multi-line heading merge: track last-added y, not first-group y

When merging consecutive heading rows that belong to the same multi-line heading (e.g. "Improving productivity and a new industrial / strategy"), the comparison must be against the **last row added to the current group**, not the first row in that group.

**The bug:** the naive implementation stores the representative y of the group's first row and compares against it. For a three-line heading at y-buckets 288, 312, 332: the first comparison (312 − 288 = 24) exceeds a 20pt threshold, so all three rows are emitted as separate `###` headings.

**Fix:** update the high-water y to the most-recently-added row's y after each merge:

```python
merged = []
for y in ys_sorted:
    if merged and (y - merged[-1][0]) < 20:
        merged[-1][0] = y          # ← advance to last-added y, not first-group y
        merged[-1][1].extend(by_y[y])
    else:
        merged.append([y, list(by_y[y])])
```

This is corrected from an earlier version of the DUP 2010 section; treat this as the canonical pattern for multi-line heading merging throughout the archive.

---

### Numbered list items: detect as paragraph starters

The Welsh Labour 2010 "100 promises" section is a numbered list where each item starts with a marker like `"14)"`, `"38)"`, `"100)"`. These items have the same 14pt line spacing as within-item continuation text, so `para_gap` alone cannot separate them — no vertical gap distinguishes the end of item 13 from the start of item 14.

**Fix:** detect the numbered marker pattern with a regex and treat it as a hard paragraph boundary, the same way bullet characters are treated:

```python
RE_NUMBERED = re.compile(r'^\d{1,3}\)$')

# In words_to_paras():
is_numitem = bool(RE_NUMBERED.match(raw))
if prev_top is not None and (gap >= para_gap or is_bul or is_numitem):
    flush()
```

The regex `^\d{1,3}\)$` matches `"1)"` through `"999)"` and nothing else. The closing `)` is a strong signal that distinguishes list markers from ordinary numeric text.

---

### Possessive apostrophes: exclude from TERMINAL_PUNCT

The `merge_unfinished_paras()` post-processing step joins paragraph fragments that end without terminal punctuation. If the TERMINAL_PUNCT set contains `'` or `'` (curly/straight single quote), then a sentence ending with a possessive plural — e.g. `"workers'"` — is treated as terminated, and the next fragment is not merged into it even though it should be.

**Fix:** omit single quotes entirely from TERMINAL_PUNCT:

```python
TERMINAL_PUNCT = set('.!?:;"»')   # no ' or '
```

The risk of over-merging at a sentence boundary ending with a single quote is very low in manifesto text. The risk of under-merging after a possessive is near-certain in any policy document discussing "workers' rights", "taxpayers' money", etc.

---

### Running footer identification: font name subset tag

Standard y-coordinate cutoffs (`Y_HEADER`, `Y_FOOTER`) catch header/footer text only if it reliably sits outside the body zone. The Welsh Labour 2015 manifesto has a running footer rendered in `OpenSans-Light-SC700` — the `SC700` suffix is pdfplumber's rendering of the font subset tag. This font appears throughout the page y-range on some pages.

**Fix:** exclude by font name substring rather than (or in addition to) y-coordinate:

```python
def is_excluded(w) -> bool:
    if 'SC700' in w.get('fontname', ''):
        return True
    ...
```

To discover which font name corresponds to the running footer, run a font-frequency diagnostic on a page known to have footer text and look for any font that appears on every page but carries text you don't want in the output.

---

## Post-extraction spacing corrections

Even after a well-tuned extraction, many manifesto Markdown files contain systematic spacing artefacts introduced by the PDF's text encoding or pdfplumber's word-boundary reconstruction. These are not errors in the extractor logic — they are inherent properties of how the source PDFs were typeset — and they occur consistently across parties and years.

The utility script **`../Python scripts/manifesto_spacing_fixer.py`** captures all known patterns and can be applied to any extracted Markdown file as a final post-processing step.

### When to use it

Run the spacing fixer after any extraction — script-based or manual — before committing a Markdown file to the archive. It is safe to run on already-clean text (all fixes are idempotent).

### What it fixes

| Pattern | Example (before → after) | Notes |
|---------|--------------------------|-------|
| Missing space after sentence-ending period | `Party.Today` → `Party. Today` | Occurs when the PDF encodes two sentences with no inter-word space at the paragraph boundary |
| Missing space after comma | `economy,public` → `economy, public` | Very common in condensed-font list items and summary lines |
| Missing space after plural possessive apostrophe | `taxpayers'money` → `taxpayers' money` | Safe: no English contraction uses the `s'[letter]` pattern |
| Missing space in `e.g.` / `i.e.` abbreviations | `e.g.rates` → `e.g. rates` | Scoped to these two abbreviations only |
| Run-together words (lower→UPPER) | `positiveUnionist` → `positive Unionist` | Aggressive mode only — use for first-pass extraction review |
| Run-together ALL-CAPS words | `ANDVOLUNTARY` → `AND VOLUNTARY` | Aggressive mode only — uses a closed list of common function words |
| Run-together CAPS→Title | `THEBritish` → `THE British` | Aggressive mode only |
| Stray internal space from drop-cap | `P olicing` → `Policing` | Complements the drop-cap regex; catches cases where the extra space wasn't at line start |

### Usage

**As a standalone CLI tool** (safe default — conservative fixes only):

```bash
python ../Python\ scripts/manifesto_spacing_fixer.py path/to/manifesto.md
```

**Dry run** (prints a diff without writing):

```bash
python ../Python\ scripts/manifesto_spacing_fixer.py path/to/manifesto.md --dry-run
```

**Aggressive mode** (also fixes run-together words — recommended for first-pass review of new extractions):

```bash
python ../Python\ scripts/manifesto_spacing_fixer.py path/to/manifesto.md --aggressive
```

**As a module** (called from within an extractor script):

```python
from manifesto_spacing_fixer import fix_spacing

md = fix_spacing(raw_markdown, aggressive=True)
```

This is the pattern used in `extract_dup_2010.py`, where `fix_spacing(aggressive=True)` is called at the end of `post_process()`.

### Origins

These patterns were identified during a manual review of the 2010 DUP Westminster manifesto — the first manifesto where the spacing artefacts were systematically catalogued rather than corrected one-off. The `manifesto_spacing_fixer.py` module was written to capture all of them in one reusable place, so that future extractors and manual corrections benefit automatically.

---

## Lessons learned (from Labour 2017 manifesto)

The Labour 2017 manifesto (two-column portrait PDF, Freight Sans type system, CID-encoded ligatures) introduced several post-extraction text-quality problems that are invisible to a word-count coverage check. See `../Python scripts/convert_2017_labour.py` and `convert_2017_labour_v2.py` for the reference implementations.

### CID ligature recovery vs. blind stripping

Many PDFs encode typographic ligatures (fi, fl, ffi, ffl) as `(cid:XXX)` codes rather than Unicode characters. Stripping them with `re.sub(r'\(cid:\d+\)', '', text)` silently removes letters from words — "official" becomes "ocial", "conflict" becomes "conict". A lookup table recovers the characters instead:

```python
CID_MAP = {
    '563': 'fi',  '564': 'fl',  '565': 'fl',  '566': 'fi',
    '572': 'ff',  '573': 'fi',  '574': 'ffi', '575': 'ffl',
}

def resolve_cid(text):
    def replace(m):
        return CID_MAP.get(m.group(1), '')  # empty string for unknown codes
    return re.sub(r'\(cid:(\d+)\)', replace, text)
```

CID numbers are font-specific — they vary between PDFs. Before writing a substitution table, find several words in the PDF that are known to contain ligatures (e.g. "official", "conflict", "affect", "different") and map the CID codes that appear in those positions. Any unknown codes left after applying the table should be logged, not silently discarded.

### Straddling words at the column boundary

With a fixed column split, a word whose characters span the split x-coordinate is extracted twice — the left portion in the left-column pass, the right portion in the right. This silently corrupts rare words rather than producing visible errors.

To detect whether straddling words are present on a representative page before writing the full extraction:

```python
def has_straddling_words(chars, col_split, tol=3):
    """Return True if any character sits within `tol` pt of the column boundary."""
    return any(
        abs(c['x0'] - col_split) < tol or abs(c['x1'] - col_split) < tol
        for c in chars if c['text'].strip()
    )
```

If straddling words are present, widen the dead-zone around the split (exclude characters with `col_split - tol < x0 < col_split + tol`) or use per-page dynamic gap detection to find a split coordinate that falls cleanly inside the gutter.

### Heading fragments split across page breaks

A section heading that falls at the very bottom of a page is often split: the first part emits as `## Opening words`, then the second part — at the top of the next page — emits as another `## of the heading`. Fix in post-processing:

```python
def merge_split_headings(lines):
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('## ') or line.startswith('### '):
            # Look ahead, tolerating one blank line (the page break)
            j = i + 1
            if j < len(lines) and lines[j].strip() == '':
                j += 1
            if (j < len(lines)
                    and (lines[j].startswith('## ') or lines[j].startswith('### '))
                    and len(lines[j].lstrip('#').split()) <= 6):  # short = likely a fragment
                merged = line.rstrip() + ' ' + lines[j].lstrip('#').strip()
                result.append(merged)
                i = j + 1
                continue
        result.append(line)
        i += 1
    return result
```

The `<= 6 words` guard prevents merging two genuinely separate short headings that happen to appear on consecutive pages.

### Column-overflow garbage detection

When column extraction fails for a page or a region, pdfplumber may produce lines of space-separated individual letters (`"m e s, e g ees ew en h"`). These are invisible to a word-count coverage check — the count still looks plausible — but they corrupt the text. Detect and discard them:

```python
def is_garbage_line(text):
    """True if the line looks like a column-extraction failure artefact."""
    tokens = text.split()
    if len(tokens) < 3:
        return False
    short = sum(1 for t in tokens if len(re.sub(r'[^A-Za-z]', '', t)) <= 2)
    return short / len(tokens) > 0.6 and len(text) < 60
```

Log any lines removed by this check and review them manually — occasionally a legitimate short line (e.g. a subheading like "A. Tax") will be near the threshold.

### Truncated paragraph rejoining

When a paragraph runs to the end of a column or page, its last sentence is often incomplete. The next extraction pass begins a new paragraph mid-sentence. Fix in post-processing by joining consecutive paragraphs where the boundary looks like a mid-sentence split:

```python
def rejoin_truncated_paragraphs(paragraphs):
    """Join a paragraph to the next if it ends without sentence punctuation
    and the next starts with a lowercase letter."""
    result = []
    i = 0
    while i < len(paragraphs):
        p = paragraphs[i]
        while (i + 1 < len(paragraphs)
               and not re.search(r'[.?!:]\s*$', p)    # no sentence-ending punctuation
               and paragraphs[i + 1][:1].islower()):   # next paragraph starts lowercase
            i += 1
            p = p.rstrip() + ' ' + paragraphs[i].lstrip()
        result.append(p)
        i += 1
    return result
```

This is a heuristic — it will occasionally join two genuinely separate short paragraphs. Always scan the output for any suspicious joins before committing the file.

---

## Lessons learned (from Labour 2019 manifesto)

The Labour 2019 manifesto (A5 portrait, two-column, mixed page types) introduced techniques for handling documents where chapter-opener pages have a fundamentally different structure to body pages. See `../Python scripts/extract_2019_manifesto.py` and `extract_2019_proper.py` for the reference implementations.

### Section divider page detection by maximum character size

The existing approach detects chapter-opener pages by looking for large characters near the top of the page (`sz >= 50 and top < 200`). Labour 2019 requires a complementary check that is more robust when chapter titles do not sit near the top: scan all characters on the page and check whether *any* reaches a display size threshold:

```python
def is_divider_page(page, size_threshold=35):
    """True if the page contains a display-size character — likely a chapter opener."""
    return any(
        c['size'] >= size_threshold
        for c in page.chars
        if c['text'].strip()
    )
```

A threshold of 35pt catches most chapter openers without false-positives on body pages that merely contain a large subheading; 50pt is safer but may miss some openers. Always validate the threshold against a handful of known divider pages before using it in a full extraction.

Divider pages have a different structure to body pages and should be routed to a separate extraction function: the large display text becomes a `##` heading, any pull-quote becomes a blockquote, and attributions (typically a medium-weight font at moderate size) become `**Name, Role**`. Do not pass divider pages through the standard body-text pipeline.

### Sidebar intro detection for chapter-opener pages

Chapter-opener pages sometimes contain a full-width intro paragraph in a prominent font (SemiBold at body size, or a larger light weight) that spans both columns, sitting above the two-column body content. A reliable heuristic: if the first three or more consecutive lines in the leading column are in the "intro" font class, treat them as a blockquoted intro rather than regular body text:

```python
def is_intro_block(lines, intro_font_class, min_consecutive=3):
    """True if enough consecutive leading lines look like intro text."""
    count = sum(
        1 for line in lines[:min_consecutive]
        if line.get('type') == intro_font_class
    )
    return count >= min_consecutive
```

The `>= 3` guard prevents single-word subheadings from being misclassified as intros. If fewer than `min_consecutive` lines match, treat them as regular body text or subheadings.

---

## Lessons learned (from Lib Dem 2017 manifesto)

The Lib Dem 2017 manifesto revealed a bullet-encoding problem that is distinct from, and complements, the ZapfDingbats and Unicode bullet issues already covered. See `../Python scripts/convert_2017.py` for the reference implementation.

### Orphaned bullet marker merging

Some PDFs emit the bullet character (`•`) on its own line, separated from the actual bullet text by a small y-gap. Processed naively, this produces an empty `* ` bullet item followed by an orphaned body paragraph with no bullet marker. The fix: if a line has a bullet type but no text content, peek at the next line and — if the y-gap is small (≤ 4pt) — merge them:

```python
def merge_orphaned_bullets(paragraphs):
    """Merge a lone bullet marker line with the following paragraph."""
    result = []
    i = 0
    while i < len(paragraphs):
        p = paragraphs[i]
        if (p.get('type') == 'bullet'
                and not p.get('text', '').strip()
                and i + 1 < len(paragraphs)
                and paragraphs[i + 1].get('top', 999) - p.get('top', 0) <= 4):
            next_p = paragraphs[i + 1]
            result.append({'type': 'bullet', 'text': next_p['text'], 'top': p['top']})
            i += 2
        else:
            result.append(p)
            i += 1
    return result
```

This is a different problem to the "flush on each bullet marker" rule in the extraction loop. That rule keeps consecutive *complete* items separate; this rule re-attaches a marker that was accidentally placed on its own line by the PDF's character encoding.

---

## Lessons learned (from DUP 2019 manifesto)

The DUP 2019 manifesto (28-page portrait A4 PDF using the Bliss and Effra font families, strict two-column layout) required a fully bespoke per-manifesto extractor. The generic script produced only 68.5% coverage. The final bespoke script reached 97.6% coverage. See `../Python scripts/extract_dup_2019_final.py` for the reference implementation.

### Font family with two semantic weight roles: classify by both weight and size

The Bliss font family is used at multiple size levels for distinct semantic purposes. A rule that checks font weight alone is insufficient:

| Font weight | Size (pt) | Role |
|-------------|-----------|------|
| Bliss-Heavy | sz ≥ 40, single char | Decorative drop-cap (first letter of section opener) |
| Bliss-Medium | sz ≥ 20 | `##` section heading |
| Bliss-Heavy | sz ≥ 16 | `##` section heading (alternate heading weight) |
| Bliss-Heavy | sz ≤ 15 | `###` bold subsection heading |
| Bliss-Light | any | Body text |
| Effra | any | Running footer (exclude) |

The same font weight (Bliss-Heavy) thus serves as both `##` heading and `###` bold subheading depending on size. The boundary at 16pt was confirmed by measuring actual word sizes on representative pages. Always run a font size survey before writing any classification rule:

```python
with pdfplumber.open("manifesto.pdf") as pdf:
    page = pdf.pages[7]   # a representative body page
    words = page.extract_words(keep_blank_chars=False, extra_attrs=['fontname','size'])
    for w in words:
        fn = w.get('fontname', '').split('+')[-1]
        if 'Heavy' in fn or 'Medium' in fn:
            print(f"sz={w['size']:.1f}  x0={w['x0']:.0f}  {repr(w['text'])}")
```

### Ligature substitution before any other processing

The Bliss font encodes typographic ligatures as Unicode Private Use Area characters rather than `(cid:XXX)` codes. They appear as literal Unicode values that pdfplumber returns directly:

| Unicode | Character | Replacement |
|---------|-----------|-------------|
| `\ufb01` | fi ligature | `fi` |
| `\ufb02` | fl ligature | `fl` |
| `\ufb03` | ffi ligature | `ffi` |
| `\ufb04` | ffl ligature | `ffl` |
| `\u00ad` | soft hyphen | `` (delete) |
| `\u200b` | zero-width space | `` (delete) |

Apply a `fix_lig()` function to every word text before any downstream processing:

```python
def fix_lig(t):
    return (t.replace('\ufb01', 'fi').replace('\ufb02', 'fl')
             .replace('\ufb03', 'ffi').replace('\ufb04', 'ffl')
             .replace('\u00ad', '').replace('\u200b', ''))
```

Without this step, words like "first", "office", "official" will contain invisible non-ASCII characters that silently corrupt the text.

### Drop-cap detection by y-proximity, not y-bucket merger

Some PDFs emit decorative drop-caps at a y-position that is several buckets above the body text they introduce — the oversized letter sits at e.g. `top=80` while the paragraph starts at `top=100`. The standard post-processing regex `re.sub(r'(?m)^([A-Z]) ([a-z])', r'\1\2', text)` assumes the cap and its continuation word appear on the same line; it will not help when they are well-separated vertically.

The correct fix is to capture drop-cap characters during extraction (keyed by their y-bucket) and prepend them to the first body word found within a proximity window:

```python
dropcaps = {}
body = []
for w in col_words:
    c = classify(w)
    if c == 'dropcap':
        dropcaps[bkt(w['top'])] = w['text'].strip()
    elif c != 'footer':
        body.append((w, c))

# When assembling each line, check if there is a dropcap within 24pt above:
for yb, dom, text in lines:
    for dy in range(0, 25, Y_TOL):
        k = bkt(yb - dy)
        if k in dropcaps:
            text = dropcaps.pop(k) + text
            break
```

The `pop()` ensures each dropcap is only used once even if multiple body lines fall within its proximity window.

### Section heading rows: classify by font, not by x-span

An early attempt at identifying "full-width" section heading rows used a spatial check — if words on a given y-row span both columns (min x0 < col_split AND max x0 ≥ col_split) — that row must be a full-width heading. This is incorrect: on any normal two-column body page, both columns contain words at the same y-coordinate, so every body row passes this test.

The correct approach: a row is a section heading row only if it contains at least one word classified as `'section'` by font inspection:

```python
def section_ys(words):
    ys = set()
    for w in words:
        if classify(w) == 'section':
            ys.add(bkt(w['top']))
    return ys
```

Once the section y-positions are identified, extract those rows using full-page width (not column-split) so that section headings spanning both columns are assembled correctly.

### Mid-page section headings: pre/post zone splitting

When a section heading appears mid-page (not at the top), extracting headings first and body columns second misorders the content. For example, if a heading at y=276 divides a page with bullets above and new section content below, "headings first" would emit the section heading before the bullets that precede it.

The fix is to split each page into three zones based on the y-coordinate of section headings:

```python
min_sy = min(sec_ys)
max_sy = max(sec_ys)

pre_l  = extract_col(words, 0,         col_split,  sec_ys, y_hi=min_sy)  # above heading
pre_r  = extract_col(words, col_split,  page.width, sec_ys, y_hi=min_sy)
sec_lines = extract_section_lines(words, sec_ys)                          # the heading(s)
post_l = extract_col(words, 0,         col_split,  sec_ys, y_lo=max_sy)  # below heading
post_r = extract_col(words, col_split,  page.width, sec_ys, y_lo=max_sy)

paras = (lines_to_paras(pre_l) + lines_to_paras(pre_r)
       + lines_to_paras(sec_lines)
       + lines_to_paras(post_l) + lines_to_paras(post_r))
```

This applies on every page, not just the page where the mid-page case was first noticed. Pages where the section heading is at the very top have an empty pre-zone and the post-zone contains everything — which is correct.

### Multi-line section headings: merge in post-processing

Long section headings (e.g. "Leaving the European Union as One United Kingdom") often wrap across two y-rows. Each row produces a separate `##` heading line. Merge consecutive `##` lines in post-processing:

```python
def merge_consecutive_h2(text):
    out = []
    for line in text.split('\n'):
        if line.startswith('## '):
            merged = False
            for j in range(len(out) - 1, -1, -1):
                if out[j].strip():
                    if out[j].startswith('## '):
                        out[j] = out[j] + ' ' + line[3:]
                        merged = True
                    break
            if not merged:
                out.append(line)
        else:
            out.append(line)
    return '\n'.join(out)
```

Similarly, if a section heading word falls in the right column (x0 ≥ col_split) while the rest of the heading is in the left column, the extract_section_lines function correctly re-assembles it by collecting ALL words at the section y-row regardless of x-position — sorting by x0 restores left-to-right word order.

### Complex visual-grid pages: add to skip list and hand-craft

When back pages contain a multi-item grid layout — e.g. a "12 Point Plan" spread with numbered items arranged in a 3×2 visual grid, where item headings in both columns share the same y-coordinate — the section-heading detector picks up both column headings and merges them into one garbled `##` line.

The reliable indicator of such a page: multiple words classified as `'section'` appear at the same y-bucket but span the full page width (left column AND right column). On a normal body page, section headings appear only once per page in one column.

Detection:

```python
def has_grid_layout(words, col_split):
    """True if section-class words appear in both columns on the same y-row."""
    by_y = defaultdict(lambda: {'left': False, 'right': False})
    for w in words:
        if classify(w) == 'section':
            yb = bkt(w['top'])
            if w['x0'] < col_split:
                by_y[yb]['left'] = True
            else:
                by_y[yb]['right'] = True
    return any(d['left'] and d['right'] for d in by_y.values())
```

When a grid-layout page is detected, add it to the skip set and provide hand-crafted markdown. Extract the content once manually from the word data (grouping left and right columns separately and reading them top-to-bottom), then hard-code it as a constant string injected at the right point in the output. This is more reliable than attempting to untangle a complex visual grid programmatically.

### Spacing fixer: always dry-run first when extractor handles drop-caps explicitly

The `manifesto_spacing_fixer.py --aggressive` mode applies patterns to join single-letter words with the following word (e.g. "P olicing" → "Policing"). When the extractor already handles drop-caps by prepending the captured letter to the following word (producing "The DUP" not "T he DUP"), the aggressive fixer may then incorrectly re-merge legitimate "A " beginnings — turning "A mandate" → "Amandate".

Always run `--dry-run` first and inspect the diff. If the aggressive mode is re-introducing problems the extractor has already fixed, skip `--aggressive` and use the conservative default instead.

```bash
# Always inspect the diff before committing
python manifesto_spacing_fixer.py manifesto.md --dry-run
```

### Integer arithmetic in bc: use Python for coverage calculations

`echo "scale=1; 9988 / 10106 * 100" | bc` produces `90.0` — wrong — because `bc` evaluates left-to-right and performs integer division on `9988 / 10106` before multiplying by 100, yielding `0 * 100 = 0.0` (displayed as `90.0` due to a rounding artefact). Use Python for any coverage calculation:

```bash
python3 -c "print(f'{9988/10106*100:.1f}%')"   # → 98.8%
```

---

## Handling plain-text (non-PDF) source files

Not every manifesto is available as a PDF. Some parties publish plain-text or rich-text exports. The toolkit's PDF-centric extraction tools do not apply in these cases, but the post-processing steps (spacing fixer, paragraph rejoining, garbage detection) still do.

### Windows-1252 / CP1252 encoding

Plain-text files exported from Windows word processors are often encoded in CP1252 rather than UTF-8. Open them explicitly, then map the Windows-specific control-character range to Unicode:

```python
with open('manifesto.txt', encoding='cp1252') as f:
    raw = f.read()
```

| Code | Replacement |
|------|-------------|
| `\x85` | `…` (ellipsis) |
| `\x91` | `'` (left single quote) |
| `\x92` | `'` (right single quote / apostrophe) |
| `\x93` | `"` (left double quote) |
| `\x94` | `"` (right double quote) |
| `\x96` | `–` (en-dash) |
| `\x97` | `—` (em-dash) |

Apply these substitutions before any other processing.

### Bullet detection in plain text

Plain-text files encode bullets as indentation patterns rather than Unicode bullet characters. Common patterns:

```python
text = re.sub(r'(?m)^[ \t]{6,}\*\s+', '* ', text)   # indented asterisk
text = re.sub(r'(?m)^[ \t]{6,}-\s+',  '* ', text)   # indented hyphen
text = re.sub(r'(?m)^[ \t]{6,}•\s+',  '* ', text)   # indented bullet
```

The 6-space threshold avoids falsely treating lightly-indented continuation lines as new bullet items. Inspect the actual indentation widths in the source file and adjust accordingly.

### TOC and content boundary detection

Plain-text files often include a table of contents and back-matter that should not appear in the Markdown output. Skip the TOC by pattern-matching its entries, and limit processing to the main body by finding known anchor phrases:

```python
TOC_LINE = re.compile(r'^\d{1,2}\s{3,}[A-Z].+\d+\s*$')

def find_content_bounds(lines, start_phrase, end_phrase):
    start = next((i for i, l in enumerate(lines) if start_phrase in l), 0)
    end   = next((i for i, l in enumerate(lines) if end_phrase   in l), len(lines))
    return start, end
```

---

## Lessons learned (from Scottish Greens 2019 manifesto)

The Scottish Greens 2019 manifesto (15-page landscape PDF using ConfigCondensed-BlackItalic section headings, MuseoSans body text, and Wingdings bullet markers) introduced several new challenges. See `../Python scripts/extract_scottish_greens_2019_v2.py` for the reference implementation (101% effective content coverage).

### Do a font inventory before writing any extraction logic

Before setting size thresholds or exclusion rules, enumerate every font and size combination that appears in the body of the PDF:

```python
with pdfplumber.open(PDF) as pdf:
    from collections import Counter
    counts = Counter()
    for page in pdf.pages:
        for w in page.extract_words(keep_blank_chars=False, extra_attrs=['fontname', 'size']):
            fn = w['fontname'].split('+')[-1]
            sz = round(w['size'])
            counts[f'{fn}@{sz}pt'] += 1
    for k, v in sorted(counts.items(), key=lambda x: -x[1])[:30]:
        print(f'  {v:5d}x  {k}')
```

This instantly reveals which fonts are body text, which are headings, which are decorative, and which are page numbers — before you accidentally filter out content or include noise.

### MIN_FONT_SIZE: filter by y-position, not size, for page numbers

The instinct is to set `MIN_FONT_SIZE` high enough to exclude page numbers. But page numbers typically sit at `top < 15pt` (above the `header_cut`) and are **already excluded by the y-position filter**. Setting `MIN_FONT_SIZE` too high (e.g. 11) will accidentally drop legitimate small-body content like a 10pt candidates list.

**Better approach:** set `MIN_FONT_SIZE = 9.5` and rely on `header_cut` (e.g. 15pt) to exclude page numbers. This correctly includes 10pt content while page numbers at `top ≈ 10pt` are already filtered.

### Non-standard font families indicate decorative/infographic content

When you see a font family that is different from the document's main body and heading fonts (e.g. `AmsiPro` in a MuseoSans document), it is almost certainly used in an info-graphic callout box or decorative element. Exclude it explicitly:

```python
def is_decorative(w):
    fn = base_font(w.get('fontname', ''))
    sz = w.get('size', 0)
    # Heading font at small sizes = decorative callout
    if SECTION_FONT in fn and sz < SECTION_MIN_SIZE:
        return True
    # Non-standard font families = info-graphic boxes
    if 'AmsiPro' in fn:  # or whatever the alien font is in your document
        return True
    return False
```

Add the non-standard font family name after inspecting the font inventory.

### Wingdings bullet markers need special handling

When bullet markers are encoded in the Wingdings font (common in many UK party manifestos), `page.extract_words()` returns them as words — at the body font size, causing duplicate empty bullet markers. Exclude them from the word stream and detect them instead from `page.chars`:

```python
WINGDING_BULLET = '\uf0ab'  # the specific Wingdings glyph used

def is_wingding_bullet(c):
    return 'Wingdings' in c.get('fontname', '') and c.get('text', '') == WINGDING_BULLET

def is_wingding_word(w):
    return 'Wingdings' in w.get('fontname', '')

# In extract_lines():
bullet_ys = set()
for c in chars:
    if is_wingding_bullet(c) and in_column(c):
        y = bkt(c['top'])
        for dy in range(-4, 12, Y_TOL):  # covers first text line of bullet
            bullet_ys.add(y + dy)

# Exclude Wingding words from the body word stream
col_words = [w for w in words if ... and not is_wingding_word(w)]
```

Then mark lines as `is_bullet=True` when their bucketed y is in `bullet_ys`.

### check_headings.py is unreliable for special-kerning fonts

The `check_headings.py` script concatenates characters without gap detection, so fonts with special kerning or wide tracking (like ConfigCondensed-BlackItalic) will produce run-together heading strings like `"AGreen NewDeal"` instead of `"A Green New Deal"`. The tool will report all headings as NOT FOUND even when they are correctly present.

For such PDFs, **verify headings manually**: extract them with the custom script's `extract_section_titles()` function (which uses gap-based space detection) and compare against the PDF directly.

### Coverage against pdftotext is misleading for heavily designed PDFs

`pdftotext` extracts *everything*, including tiny (2–7pt) decorative sidebar text, callout box text, and other non-content elements. For a heavily designed manifesto, the reported `pdftotext` word count can be 10–30% higher than the actual content word count, making your coverage look worse than it is.

**Better approach:** calculate real content coverage by excluding decorative words:

```python
real_content_wc = sum(
    1 for page in pdf.pages
    for w in page.extract_words(keep_blank_chars=False, extra_attrs=['fontname', 'size'])
    if w['size'] >= MIN_FONT_SIZE
    and w['top'] > header_cut
    and not is_decorative(w)
)
```

Compare your markdown word count against `real_content_wc` rather than the raw `pdftotext` total.

### Bullet continuation lines need rejoining in post-processing

When a bullet item wraps to a second line, the continuation line is a normal body line (not marked as a bullet). If the between-line gap exceeds `PARA_GAP`, it becomes a separate paragraph instead of continuing the bullet. Fix this in `rejoin_truncated_paragraphs()` by also processing bullet paragraphs:

```python
if p.startswith('* '):
    body = p[2:]  # strip '* '
    while (i + 1 < len(paragraphs)
           and not re.search(r'[.?!:]\s*$', body.rstrip('*_'))
           and not paragraphs[i + 1].startswith('#')
           and not paragraphs[i + 1].startswith('* ')
           and paragraphs[i + 1][:1].islower()):
        i += 1
        body = body.rstrip() + ' ' + paragraphs[i].lstrip()
    result.append('* ' + body)
    i += 1
    continue
```

### Cross-column paragraph splits: use a global rejoin pass

When columns are processed independently and then concatenated, paragraphs that wrap from the bottom of one column to the top of the next become two separate items in `all_sections`. A second call to `rejoin_truncated_paragraphs()` on the complete list (after columns are merged) catches these.

For cases where the continuation starts with an uppercase word (proper noun, named place, etc.), also check for **dangling words** at the end of the first fragment — articles, prepositions, and conjunctions cannot grammatically end a sentence:

```python
_DANGLING = re.compile(
    r'\b(the|a|an|at|in|of|for|by|with|to|from|on|into|and|or|but|'
    r'its|our|their|this|these|those|which|that|who|whom|Scottish|UK|EU|NHS)\s*$',
    re.I
)

# In rejoin loop for normal paragraphs:
and (paragraphs[i + 1][:1].islower() or _DANGLING.search(p.rstrip('*_')))
```

Extend the word list with any proper nouns or acronyms that frequently appear mid-sentence in your specific document.

### Sub-threshold headings: lower the gap-detection factor

Some section headings fall just below the `SECTION_MIN_SIZE` threshold (e.g. "Our Candidates" at 31.5pt when the threshold is 36pt). For gap-based space detection in these sub-threshold headings, lower the factor from `0.15` to `0.12`:

```python
threshold = max(1.5, prev_sz * 0.12)  # not 0.15
```

At 31.5pt, a factor of `0.15` gives a threshold of 4.72pt. A factor of `0.12` gives 3.78pt, correctly detecting a 4.4pt inter-word gap as a space.

### Tabular "column within a column": split by x-coordinate

When the right column of a two-column page is itself structured as a table (e.g. a candidates list with region names, constituency names, and candidate names in three horizontal positions), the generic column extractor will jumble everything onto one line.

Detect this case and use a dedicated x-split extractor:

```python
def extract_candidates_list(page):
    cand_words = [w for w in page.extract_words(...) if in_right_column(w) and is_10pt(w)]
    by_y = defaultdict(list)
    for w in cand_words:
        by_y[bkt(w['top'])].append(w)

    CAND_X_SPLIT = 640  # empirically: constituencies end before x=640, names start at x≈649
    for y in sorted(by_y.keys()):
        row = sorted(by_y[y], key=lambda w: w['x0'])
        if all(is_bold(w['fontname']) for w in row):
            yield f'**{join(row)}**'       # region header
        else:
            left  = join(w for w in row if w['x0'] < CAND_X_SPLIT)
            right = join(w for w in row if w['x0'] >= CAND_X_SPLIT)
            yield f'{left} — {right}'      # constituency — candidate
```

Inspect the actual x0 values for a few rows to find the correct `CAND_X_SPLIT`.

### Section heading ordering in mixed-column pages

When a page has a new section heading in one column while the other column continues the previous section, the order of emission matters. The general rule: emit the section heading between the two columns — after extracting the column that precedes the heading, and before extracting the column the heading introduces. Do not emit all headings first and all body content second.

The anchor phrases are document-specific — look for the first real body heading and the last substantial sentence of the manifesto text.

---

## Lessons learned (from Scottish Greens 2015 manifesto)

The Scottish Greens 2015 manifesto (18-page landscape PDF using the MuseoSans font family with a four-column candidates section across pages 17–18) reached 97.3% coverage. The main challenges were a complex multi-column candidates list that required several novel parsing techniques, and capitalisation post-processing for a publisher that used intentionally lowercase styling throughout.

### Column midpoint boundaries for multi-column tables

When assigning words to columns in a multi-column list (e.g. a candidates table), use **column midpoint boundaries** — not the column left-edge positions. If the four column left edges are at x≈28, 122, 215, 309, the assignment boundaries should be at the midpoints between adjacent starts: x≈75, 168, 262.

Using left-edge positions directly means a word whose x0 value is just below the next column's left edge (e.g. x=121.9, which is just below 122) is wrongly assigned to column 0 instead of column 1. Midpoints eliminate this edge case:

```python
CAND_COL_BOUNDS = [75, 168, 262, 999]   # midpoints between col starts [28, 122, 215, 309]

def assign_candidate_col(x0):
    for c, right in enumerate(CAND_COL_BOUNDS):
        if x0 < right:
            return c
    return len(CAND_COL_BOUNDS) - 1
```

### Per-page processing for multi-column candidates lists

Never pool words from multiple pages before processing a multi-column list. Two consecutive pages share the same y-coordinate ranges (both starting at y≈130), so merging all words and sorting by y causes entries from different pages to interleave unpredictably.

Process each page in a separate loop iteration and concatenate results afterwards:

```python
results = []
for page in cand_pages:
    words = page.extract_words(extra_attrs=['fontname', 'size'], keep_blank_chars=True)
    # ... process this page's words independently ...
    results.extend(page_results)
```

### Look-ahead boundary detection for constituency/candidate entries

In a candidates list, you cannot use "two or more words with no comma" as the sole rule to start a new entry boundary. Constituency names like "West Aberdeenshire & Kincardine" contain multiple words and no comma, yet they continue across several lines before the candidate name appears.

The fix is a **look-ahead rule**: a line is only treated as a new-entry boundary if all remaining lines in the current block are continuation lines (ending with a comma, "&", or " and"). If any remaining line is also a potential boundary line, the current line is still accumulating a multi-part constituency name.

```python
def is_continuation_line(text):
    t = text.rstrip()
    return t.endswith(',') or t.endswith('&') or t.endswith(' and') or t == 'and'

def is_boundary_line(text):
    if is_continuation_line(text):
        return False
    if ',' in text:
        return False
    return len(text.split()) >= 2

# In the entry-splitting loop:
if is_boundary_line(text):
    remaining = block[i + 1:]
    if not remaining or all(is_continuation_line(t) for t in remaining):
        entries.append(cur_entry[:])
        cur_entry = []
```

### `is_continuation_line` must include bare "and" endings

Constituency names like "Inverness, Nairn, Badenoch and Strathspey" wrap across lines, with the last line ending in just the word "and". The continuation predicate must cover both ` and` at the end of a longer line and the standalone token `and` on its own line:

```python
return t.endswith(',') or t.endswith('&') or t.endswith(' and') or t == 'and'
```

### Last-comma split as the constituency/candidate separator

Once all lines for an entry are joined into a single string, the split point between constituency name and candidate name is reliably the **last comma** in the joined text. Do not attempt to detect the split line-by-line — join first, then `rfind(',')`:

```python
def split_constituency_candidate(lines):
    joined = ' '.join(lines).strip()
    last_comma = joined.rfind(',')
    if last_comma == -1 or last_comma == len(joined) - 1:
        return (joined.rstrip(',').strip(), '')
    constituency = joined[:last_comma].strip()
    candidate = joined[last_comma + 1:].strip()
    candidate = re.sub(r'-\s+', '-', candidate)   # fix hyphen+space from line-wrap
    return (constituency, candidate)
```

The `re.sub(r'-\s+', '-', candidate)` fix handles cases where a hyphenated name (e.g. "Beattie-Smith") wrapped at the hyphen: the line-joining produces "Beattie- Smith" and the regex restores the correct form.

### Cross-page paragraph joining

Body paragraphs that break across a page boundary produce false paragraph splits. The canonical fix is a post-processing merge pass: if a body or intro block ends without terminal punctuation (not in `.?!:`) and the immediately following block of the same type starts with a lowercase character, merge them into one block:

```python
SENTENCE_END = set('.?!:')
JOINABLE_TYPES = {'body', 'intro'}
merged = []
i = 0
while i < len(all_blocks):
    b = all_blocks[i]
    if (b['type'] in JOINABLE_TYPES and i + 1 < len(all_blocks)
            and all_blocks[i + 1]['type'] in JOINABLE_TYPES):
        nxt = all_blocks[i + 1]
        last_char = b['text'].rstrip()[-1] if b['text'].rstrip() else ''
        first_char = nxt['text'].lstrip()[0] if nxt['text'].lstrip() else ''
        if last_char not in SENTENCE_END and first_char.islower():
            merged.append({'type': b['type'],
                           'text': b['text'].rstrip() + ' ' + nxt['text'].lstrip(),
                           'top': b['top']})
            i += 2
            continue
    merged.append(b)
    i += 1
all_blocks = merged
```

Run this pass once after assembling all pages, before rendering to Markdown.

### Multi-line subsection heading accumulation

If two consecutive subsection-type lines appear within the normal paragraph gap (`PARA_GAP`), they are almost certainly a single heading that wrapped across two lines in the PDF. Accumulate them rather than emitting two separate `###` blocks:

```python
elif ltype == 'subsection':
    if cur_type == 'subsection' and gap < PARA_GAP:
        cur_text += ' ' + text   # join continuation line to current heading
    else:
        flush()
        cur_type = 'subsection'
        cur_text = text
        cur_top = top
```

Without this, a heading like "JOIN THOUSANDS OF PEOPLE VOTING GREEN / ON 7 MAY 2015." produces two separate `###` blocks.

### Capitalisation post-processing for lowercase-styled PDFs

Some publishers (including the Scottish Greens in 2015) use intentionally lowercase styling throughout their PDF — sentence-starting words in body paragraphs are lowercased, proper nouns are lowercased, and abbreviations may be in unexpected case. The extraction pipeline preserves this faithfully, but the output is not usable without a capitalisation cleanup pass.

Treat capitalisation post-processing as a **mandatory step** when the source PDF uses non-standard capitalisation, not something to discover at the end of the process. Check a few body paragraphs early during extraction to see whether the PDF's styling is conventional, and flag it before investing time in a full extraction if not.

The categories to fix are:
- **Sentence starts** — the first letter of each sentence in a paragraph
- **Proper nouns** — place names, party names, organisation names, legislation names, named bodies
- **Abbreviations** — NHS, EU, NATO, UN, CEO, GDP, and any others appearing in the document

Maintain a document-specific list of proper nouns and abbreviations and apply it with a targeted `re.sub()` pass (using word boundary anchors: `r'\b[Nn][Hh][Ss]\b'` → `'NHS'`, etc.) after the main extraction. The spacing fixer already handles sentence-end capitalisation to some extent; a separate noun/abbreviation list handles the rest.

### Private Use Area ligature substitution

The MuseoSans font encodes typographic ligatures as Unicode Private Use Area characters — specifically `ﬁ` (fi), `ﬀ` (ff), and `ﬃ` (ffi). Apply substitution before any downstream processing:

```python
def clean_text(t):
    return (t.replace('\ufb01', 'fi')   # ﬁ ligature
             .replace('\ufb00', 'ff')   # ﬀ ligature
             .replace('\ufb03', 'ffi')  # ﬃ ligature
             .replace('\ufb02', 'fl')   # ﬂ ligature
             .replace('\ufb04', 'ffl')) # ﬄ ligature
```

Apply `clean_text()` to every word's text immediately after extraction. Without this, words like "office", "affiliation", and "different" contain invisible non-ASCII bytes.

## Lessons learned (from Scottish Greens 2005 manifesto)

The Scottish Greens 2005 Westminster manifesto is an A5-format two-column booklet (20 pages, Helvetica Neue font family, ZapfDingbats bullet markers). It reached 98%+ effective content coverage. The main challenges were font-size inflation from symbol characters, column-boundary character bleed, per-page layout variation, and interleaved pull quotes and sidebar boxes that required post-processing to separate.

### ZapfDingbats characters inflating heading classification

When a ZapfDingbats decorative character (bullet, ornament, or icon) appears at the same y-bucket as a real heading, pdfplumber returns that character with an extremely large font size (often 60–80pt). If you compute `max_size` over all characters in a y-bucket to classify the heading level, that one symbol character inflates `max_size` and causes the adjacent real text (at e.g. 24pt) to be misclassified as a `#` rather than a `##`.

**Fix:** exclude symbol-font characters from the `line_chars` list when computing `max_size` for heading detection:

```python
SYMBOL_KW = ('Symbol', 'Wingding', 'Zapf', 'Dingbat')

def font_flags(fontname):
    """Returns (is_bold, is_italic, is_symbol)."""
    bold   = any(k in fontname for k in ('Bold', 'Heavy', 'Black', 'SemiBold', 'Demi', 'Extra'))
    italic = any(k in fontname for k in ('Italic', 'Oblique'))
    symbol = any(k in fontname for k in SYMBOL_KW)
    return bold, italic, symbol

# When building line_chars, exclude symbol-font chars:
line_chars = [c for c in char_lut.get(top, [])
              if c['text'].strip() and not font_flags(c.get('fontname', ''))[2]]
```

Also skip any word whose entire character set is symbol-font glyphs when building styled words — these are decorative bullets, not content:

```python
wchars = [c for c in char_lut.get(top, []) if w['x0']-1 <= c['x0'] <= w['x1']+1]
if wchars and all(font_flags(c.get('fontname', ''))[2] for c in wchars):
    continue  # skip symbol-only words (ZapfDingbats bullets etc.)
```

### Column-boundary character bleed corrupting `all_bold` detection

In a two-column layout, a word that is hyphenated at a line break sometimes has its characters split across the column boundary in the PDF's internal coordinate space. The first syllable sits in column A, the second in column B. When you collect `line_chars` for a y-bucket without column filtering, the non-bold characters from the right column contaminate the `all_bold` metric for the left column's heading line — making a genuinely bold-only line appear mixed.

**Fix:** restrict `line_chars` to characters whose x0 falls within the x-ranges of the words you have already extracted for that line, rather than collecting all chars at that y-bucket regardless of x-position:

```python
word_ranges = [(w['x0'] - 2, w['x1'] + 2) for w in line_words]
line_chars = [c for c in char_lut.get(top, [])
              if c['text'].strip()
              and not font_flags(c.get('fontname', ''))[2]   # exclude symbol fonts
              and any(lo <= c['x0'] <= hi for lo, hi in word_ranges)]
```

This confines `line_chars` to the actual word spans in the current column, preventing bleed from the opposite column regardless of where the column boundary sits.

### Per-page column split and header-cut configuration

Some booklet-format PDFs use a consistent two-column layout but with small variations in the column gutter position from page to page (different typesetting choices for different sections). A single global `col_split` value will slightly misplace the boundary on some pages, causing words to appear in the wrong column.

**Fix:** use a per-page configuration dict mapping page index to `(col_split, header_cut)`:

```python
PAGE_CONFIG = {
    0:  None,          # cover — single column or skip
    1:  (296, 90),     # intro page — slightly wider left col
    2:  (254, 90),
    3:  (None, 30),    # single-col divider
    # ... body pages
    7:  (286, 30),     # needs special three-zone handling (see below)
}

for idx, page in enumerate(pdf.pages):
    cfg = PAGE_CONFIG.get(idx, (DEFAULT_COL_SPLIT, DEFAULT_HEADER_CUT))
    if cfg is None:
        # single-column page
        ...
    else:
        col_split, header_cut = cfg
```

Diagnose the correct split for each page by printing the x0 histogram and noting where the gap falls. A 5–10pt error in `col_split` is enough to misassign words near the gutter.

### Full-width heading strip plus two-column body on the same page

Some pages have a full-width section heading at the very top (y < ~30pt) and then two-column body text below it. The standard three-zone approach handles mid-page headings, but when a heading is at the absolute top of the body area (just below `header_cut`) it needs its own treatment: extract it as a full-width strip first, then process the remainder as two columns.

```python
elif idx == 17:   # example: page with full-width "Greens in Action Everywhere" at top
    Y_BODY = 30   # the heading occupies y < 30; body content is below
    head_lines  = get_styled_lines(page, 0,         page_width, header_cut, y_max=Y_BODY)
    left_lines  = get_styled_lines(page, 0,         col_split,  Y_BODY)
    right_lines = get_styled_lines(page, col_split,  page_width, Y_BODY)
    paras = (join_to_paragraphs(head_lines)
           + join_to_paragraphs(left_lines)
           + join_to_paragraphs(right_lines))
```

The key is that `get_styled_lines` accepts both `y_min` (the `header_cut` lower bound) and `y_max` (an upper ceiling), so you can slice out just the heading strip as a single-column element. Without this, a heading word that happens to fall in the right column's x-range will be lost from the heading and only appear in the right column's output.

### Soft hyphen line-break join post-processing

Two-column booklet PDFs typeset at narrow column widths produce many mid-word line breaks: "account-" ends one line and "ability" starts the next. pdfplumber joins words within a line but does not rejoin hyphenated line breaks across lines. The result is dozens of broken compound-looking tokens in the extracted text.

**Post-processing fix** — join hyphen-wrapped pairs, but preserve legitimate compound words:

```python
KEEP_HYPHENS = {
    'co-operation', 'well-being', 'long-term', 'short-term', 'decision-making',
    'free-range', 'fair-trade', 'means-tested', 'self-determination',
    # ... add any other legitimate compounds from the specific document
}

def join_hyphen_wraps(text, keep=KEEP_HYPHENS):
    """Join hyphenated line-break pairs, preserving legitimate compound words."""
    def replace(m):
        word1, word2 = m.group(1), m.group(2)
        joined = word1 + word2
        compound = word1 + '-' + word2
        if compound.lower() in keep:
            return compound  # preserve the hyphen
        return joined        # remove it
    # Match: word ending with hyphen-newline, followed by lowercase continuation
    return re.sub(r'(\w+)-\n(\w)', replace, text)
```

Build the `KEEP_HYPHENS` set by reviewing the output for cases where the joined form looks wrong. The set is document-specific; common entries include hyphenated prefixes (`co-`, `self-`, `non-`) and style-guide compounds (`well-being`, `long-term`).

### Photo credit removal

Graphic-design-heavy PDFs often embed photographer credits (typically a name alone, sometimes with "©") as short text runs near image boundaries. pdfplumber extracts these as standalone one- or two-word lines, which appear in the output as orphaned proper names with no context.

**Detect and remove** with a targeted regex in post-processing:

```python
# Remove lines that look like lone photographer credits
# (a proper-noun word or two, nothing else on the line)
content = re.sub(
    r'(?m)^\s*((?:[A-Z][a-z]+\s+){1,2}[A-Z][a-z]+)\s*$\n',
    '',
    content
)
```

Prefer a targeted list of known credit strings over a broad regex if you can identify them during diagnosis — the broad form risks removing legitimate short headings.

### Interleaved pull quotes and sidebar boxes: post-processing structural fix

When a two-column page contains a sidebar box or pull quote in the left column alongside body text in the right column, the extraction script emits both columns' content interleaved line-by-line. The result is a garbled paragraph mixing quote text and body text in alternating fragments.

The cleanest fix for small-scale manifestos is post-processing string replacement rather than trying to detect sidebar boxes at extraction time:

1. **Identify** interleaved sections by reading the raw output and comparing against the PDF.
2. **Write the corrected form** directly: separate the body text into clean prose and the sidebar/quote into a Markdown blockquote (`>`).
3. **Replace** the garbled string with the corrected form.

```python
old = (
    'body start sidebar-start body-cont sidebar-cont body-cont2 sidebar-end'
)
new = (
    'Cleaned body paragraph text.\n\n'
    '> Sidebar or pull-quote text.\n>\n'
    '> — Attribution\n\n'
    'Continuation of body text.'
)
content = content.replace(old, new)
```

**Critical:** run all structural string replacements **before** any other text transformations (hyphenation fixes, ligature joins, etc.). Earlier passes that patch individual hyphenated tokens will change the exact characters in the garbled section, causing subsequent `str.replace()` calls to fail with no match. If you discover structural fixes are needed after other transforms have already run, use `repr()` to inspect the exact current character sequence — including Unicode quotes (`\u201c`, `\u201d`), en-dashes (`\u2013`), and smart apostrophes (`\u2019`) — and match against those.
