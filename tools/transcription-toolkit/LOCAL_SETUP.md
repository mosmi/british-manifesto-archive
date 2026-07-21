# Local VLM setup (tier 1 of the two-tier pipeline)

One-time setup to run manifesto page transcription with **no API key and no
per-token cost**. Tier 1 is a local document-OCR model; tier 2 is a Claude
Code session (subscription-covered) repairing only the pages tier 1 got
wrong. Pipeline overview: `knowledge/pipelines/transcription.md`.

## 1. Install LM Studio

Download from <https://lmstudio.ai> (free, native Apple Silicon app with the
MLX backend). Alternative: [oMLX](https://github.com/jundot/omlx), a lighter
menu-bar MLX server that auto-detects OCR models — the scripts only need an
OpenAI-compatible endpoint, so either works.

## 2. Download the model

In LM Studio's search, get **`mlx-community/DeepSeek-OCR-8bit`** (~3.5 GB).
This is a ~3B document-OCR VLM: page image in, structured Markdown out, with
reading order and heading levels handled natively. 8-bit is the right
quality/size trade-off on a 24–36 GB machine; it uses well under 6 GB of
unified memory while running.

Fallback if DeepSeek-OCR disappoints on hard layouts: `dots.ocr` (~1.7B, MIT)
or a general VLM like Qwen-VL 8B with `--mode repair` instead of `--mode ocr`.

## 3. Start the server

In LM Studio: **Developer tab → Start Server** (default
`http://localhost:1234/v1`), and load the model. Note the model id shown in
the server UI (or run `lms ls`) — pass it as `--model` if it isn't exactly
`deepseek-ocr`.

Headless (e.g. for overnight batches):

```bash
lms server start
lms load mlx-community/DeepSeek-OCR-8bit
```

## 4. Go/no-go quality check (do this before committing to the model)

Re-run tier 1 against pages you already hand-fixed and compare — the London
work dirs still have the images and ledgers. Pick 2–3 manifestos whose
Gemini output needed the most manual fixing:

```bash
cd tools/transcription-toolkit

# Transcribe a few known-hard pages with the local model
python repair_manifestos_gemini.py work/<slug>/ledger.json --pages 3,4,5 --force

# Compare against what you shipped
diff work/<slug>/pages/page-003.vlm-clean.txt work/<slug>/pages/page-003.gemini-clean.txt
```

**Go** if the local output is comparable on reading order and headings (word
-level typos are caught by the gate). **No-go** if it consistently mangles
columns Gemini handled — then try dots.ocr, or fall back to running tier 2
(Claude) on more pages.

## 5. Normal per-manifesto workflow

```bash
cd tools/transcription-toolkit

# Phase 1 (unchanged, local): render images + deterministic candidates
python transcribe_pipeline.py new <path-to-pdf>

# Tier 1: local VLM transcribes every page (no key)
python repair_manifestos_gemini.py work/<slug>/ledger.json

# Layer A gate: deterministic QA, flags pages for tier 2 (no key)
python flag_pages.py work/<slug>/ledger.json

# Tier 2: in a Claude Code session in this repo:
#   "Repair the flagged pages in work/<slug>"  (uses the
#   manifesto-page-repair skill; Claude reads the page images itself)

# Then finalize + site rebuild as before (finalize_manifesto.py etc.)
```

Batch: `python batch_repair_london.py <n>` forwards extra args, e.g.
`python batch_repair_london.py 3 --model deepseek-ocr-8bit`.

## Notes

- **Always run the toolkit with `/opt/homebrew/bin/python3.12`**, not the
  system `python3` (which is pre-3.10 and crashes on the bundled pdfplumber),
  and note there is no bare `python` command on macOS.
- The gate's coverage check compares vlm-clean word counts against the
  **median** of the deterministic extractors. Don't switch it back to max:
  `pdfplumber`/`pdfplumber-layout` roughly double the word count on
  multi-column pages, which would flag every clean page as "coverage low".
- A harmless `qa_check` B2/R2 warning on the final page is usually just the
  imprint footer's bullet separators ("… W1W 5NT • Tel: … • Website: …"),
  not a real reading-order error.
- The old paid paths still work: `--backend gemini` (needs `GEMINI_API_KEY`)
  and `qa_audit_vision.py` (needs `ANTHROPIC_API_KEY`). Both are now
  optional; `flag_pages.py` replaces the paid vision audit for gating.
- Throughput: expect a few seconds per page on an M-series Mac via MLX —
  an average manifesto (~30 pp) in a couple of minutes, a full batch
  overnight without supervision.
- The server must be running before tier-1 commands; the error
  `Connection refused` on localhost:1234 means it isn't.
