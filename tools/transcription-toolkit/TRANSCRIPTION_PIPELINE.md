# TRANSCRIPTION_PIPELINE.md

> **Purpose of this document.** A self-contained plan to add real OCR
> capability to the manifesto transcription + QA pipeline so scanned PDFs
> (currently unhandled) produce clean, high-fidelity Markdown, verified
> against the originals. Written to be handed to a fresh Claude Code session
> without reconstructing context.
>
> **Repo location:** `british-manifesto-archive/tools/transcription-toolkit`
> **Status:** Phases 1–4 implemented and validated against a real document
> (Alba 2021); three items remain before this is fully closed out — see
> §5's Phase 5 row.
> **Last updated:** 2026-07-11 (rewritten after a full ground-truth audit —
> the original version of this doc was written from a stale/wrong project
> summary; see §0 and §9 for what changed and why)

---

## 0. Context for a fresh session

We transcribe UK political party manifesto PDFs into consistent, structured
Markdown for the British Manifesto Archive. Two document classes exist:

1. **Digital PDFs** with an embedded text layer. Extraction problems here are
   *layout*: rotated margin slogans, running headers/footers, two-page
   landscape spreads, and mixed multi-column pages getting interleaved or
   merged into the body text. **This is already solved.** `extract_manifesto.py`
   is a mature, font-aware, column-aware `pdfplumber` extractor, tuned over
   ~26+ manifestos (Alliance, UKIP, DUP, Welsh series, Labour, Lib Dem,
   Scottish Greens — see `README.md`'s per-series lessons-learned sections),
   with a human-authored per-page override mechanism (`manifests/*.yaml`) for
   the pages the generic heuristics get wrong.
2. **Scanned PDFs** with no/negligible text layer. Example:
   `manifestos/holyrood/2021/alba/manifesto.pdf` (Alba, Holyrood 2021, 57pp).
   A plain text-layer extractor recovers very little (`pdftotext -layout`
   measures **1,502 words** — confirmed by direct measurement). **This is the
   real, unsolved gap.** No dedicated OCR engine has ever been run against
   this PDF inside this repo. See §0.2 for the corrected word-count picture.

### 0.1 Correction: the "recitation filter" story is not this repo's history

An earlier draft of this document said the previous iteration OCR'd scanned
pages by driving a **chat** LLM over page images, which triggered that
model's recitation filter, forcing an adversarial reversed-spelling
workaround that corrupted the text and required an extra repair script
(`extract_manifesto_ocr.py` + `clean_ocr_manifesto.py` + `audit_manifesto_llm.py`).

**That story is real, but it did not happen in this repo.** A full audit
(2026-07-11) found:

- None of `extract_manifesto_ocr.py`, `clean_ocr_manifesto.py`, or
  `audit_manifesto_llm.py` exist anywhere in
  `tools/transcription-toolkit/` (nor in the untracked, byte-identical
  backup at `tools/transcription-toolkit-archive/`).
- Zero mentions of "recitation" anywhere in this toolkit's code or docs.
- The actual files matching that story — including the literal prompt
  *"CRITICAL WORKAROUND: To bypass recitation filters, you MUST reverse the
  spelling of every single word..."* — live in a completely separate,
  never-git-tracked directory: `/Users/mosmi/Documents/Antigravity/Projects/transcription-toolkit/`.
  That is a **Gemini-API-based fork** (Google's Antigravity IDE) that shares
  this toolkit's lineage (same `README.md`/`PROMPT.md` base) but diverged
  onto its own path and never fed anything back into this repo.
- This repo's own toolkit took a different, already-fairly-sophisticated
  route instead: deterministic `pdfplumber` extraction + a human-gated
  **page-ledger** pipeline (`transcribe_pipeline.py`) with automatic
  per-page layout classification and a still-unconfigured cloud-OCR fallback
  stub (pointed at Mistral/Qwen, never wired up).

**Practical upshot:** there is no corrupted-OCR mess to clean up here, and
no filter-bypass hack to avoid reintroducing (the rule "never do that
again" still stands as good practice, it just isn't undoing anything in
*this* codebase). The job is additive: build the missing OCR tier and wire
it into the router/ledger/QA machinery that already exists, not replace or
repair anything.

### 0.2 Correction: Alba's "true word count" is unverified — don't trust the 11,900 figure

The original draft claimed ~11,900 "real" words for the Alba manifesto vs.
~1,700 extracted. Neither number holds up under a real audit:

- `pdftotext -layout` on the actual file measures **1,502 words** (close to
  the ~1,700 claim, so the "extraction recovers very little" premise is
  confirmed).
- The **only actual OCR run ever done** against this PDF (via the separate
  Gemini/Antigravity project, `test-alba.md` / `scratch_alba_extracted.md`)
  produced **1,760 words** — barely more than the plain text-layer
  extraction, and that run used the corrupted reversed-spelling workaround.
  It is not a trustworthy ground truth.
- No source in either project independently verifies an ~11,900-word true
  count. That number's origin is unknown and should be treated as
  **unverified** until Phase 1 produces a real OCR pass to check it against
  (e.g. spot-count words on a handful of representative pages and
  extrapolate, or trust whichever new-engine output looks complete and
  coherent on manual read-through).

Confirmed independently: **57 pages**, A4, not encrypted, no rotation
(`pdfinfo`).

---

## 1. Design principles

- **Use the right class of tool.** Document-parsing / OCR engines (Docling,
  Marker/Surya, olmOCR, Tesseract) do layout analysis and character
  recognition on pixels. They have no recitation/alignment filter to fight,
  so scanned-page transcription is clean and deterministic. Chat/vision LLMs
  are used **only** to verify and classify — never to (re)generate source
  text. (Tesseract is already available in this toolkit via
  `extract_compare.py --ocr`, but only as one option in a whole-document
  comparison run, not as a dedicated per-page tier feeding the ledger.)
- **Extend, don't rebuild.** `transcribe_pipeline.py` already has a working
  per-page router (`classify_page()`) and human-gated ledger workflow.
  `qa_check.py` already has a full deterministic structural-lint layer (18
  check codes). Neither needs to be rebuilt from scratch — see §2 and §4 for
  exactly what's reused vs. new.
- **One cleanup layer, not per-source hacks.** Domain-specific
  post-processing (bullet normalisation, header/footer stripping,
  margin-slogan removal) already lives in `extract_manifesto.py`
  (and `manifesto_spacing_fixer.py` in the sibling `Python scripts/` folder).
  New OCR-tier output must be routed through the same cleanup, not given its
  own bespoke post-processing.
- **LLMs verify, they never transcribe.** This is the load-bearing rule for
  avoiding hallucination in both extraction and QA — still true, still the
  main thing to protect against.
- **Deterministic checks first, expensive checks second.** `qa_check.py`
  (free, fast) runs on everything; a vision-model audit (new — see §4 Layer
  B) is reserved for pages it flags, or for the `image-only`/`sparse` pages
  `classify_page()` already identifies.
- **Thorough docs.** Every non-obvious decision is recorded in §7 so future
  sessions don't relitigate it.

---

## 2. Target architecture — extend the existing page-ledger pipeline

`transcribe_pipeline.py` already routes and tracks *per page*, which is
strictly better than the doc-level router this plan originally proposed
(handles mixed native+scanned PDFs for free — see the "mixed manifestos"
open question in §8, now answered). The work is filling in the one missing
piece: a real OCR engine behind the pages it already flags as untranscribable.

```
                ┌───────────────────────────┐
   PDF  ──────► │ classify_page() (EXISTS)  │
                │ per-page layout classifier│
                │ transcribe_pipeline.py:353│
                └──────────┬────────────────┘
        text-bearing pages │        │ image-only / sparse pages
                    ▼                         ▼
        ┌───────────────────┐   ┌─────────────────────────┐
 Tier 1 │ extract_manifesto  │   │  NEW: OCR tier           │ Tier 2
        │ .py (EXISTS)       │   │  Docling / Marker / Surya│
        │ font+column-aware  │   │  / olmOCR, replacing the │
        │                    │   │  unconfigured cloud_ocr  │
        │                    │   │  stub (ledger.json)      │
        └──────────┬─────────┘   └──────────┬───────────────┘
                    └────────────┬───────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │ Domain cleanup (EXISTS)  │
                    │ extract_manifesto.py     │
                    └────────────┬─────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │ QA (3 layers)            │
                    │ A: qa_check.py (EXISTS)  │
                    │ B: vision audit (NEW)    │
                    │ C: checklist (extend     │
                    │    transcribe_pipeline)  │
                    └────────────┬─────────────┘
                                 ▼
                        clean, verified .md
```

### Router — already exists: `classify_page()`

`transcribe_pipeline.py:353-413` inspects each page's `pdfplumber` word
geometry and colored-rect count and returns one of: `image-only` (0
extractable words — the scanned-page signature), `sparse` (≤5 words),
`single-column`, `two-column`, `three-column`, `sidebar-or-table`,
`spread-or-landscape`. This *is* the router. Nothing to build here — the new
OCR tier just needs to be the thing `image-only`/`sparse` pages get handed
to, instead of dead-ending as `not-configured` in the ledger.

### Tier 1 — native / digital PDFs: already solved, out of scope

`extract_manifesto.py` already handles multi-column reading order, drop
caps, CID/ligature decoding, margin-slogan filtering (`upright == False`),
header/footer stripping, and landscape-spread splitting — tuned across two
dozen real manifestos. **Do not replace this with Docling/Marker.** It works,
it's tuned, and a wholesale swap risks regressing every previously-verified
manifesto for no benefit (the actual gap is scanned PDFs, not native ones).
If a future session finds a *specific* native PDF this extractor handles
badly, that's a targeted `manifests/*.yaml` override or a bespoke
`scripts/extract_party_year.py`, not a reason to swap engines.

### Tier 2 — scanned PDFs (no text layer): the real gap, build this

For pages `classify_page()` marks `image-only`/`sparse`, run real OCR:
- **Docling** (IBM, MIT-licensed) — MLX acceleration on Apple Silicon, local
  VLM-quality layout analysis, no GPU needed. Primary candidate.
- **Marker** (Surya OCR under the hood) — strong multi-column reading-order
  reconstruction; has a `--use_llm` polish mode (see Tier 3).
- **olmOCR** — dedicated scanned-document OCR; good fallback for the hardest
  scans.
- **Tesseract** — already present in this toolkit (`extract_compare.py`
  `--ocr` flag, `pytesseract`+`pdf2image`), zero-dependency simplest
  fallback, but currently invoked only as a whole-document comparison
  option, not wired to per-page ledger status.

This should plug into the **existing** `cloud_ocr` ledger slot
(`transcribe_pipeline.py:845-849,916-919`, currently
`{"status": "not-configured", "preferred_order": ["mistral-ocr-4",
"qwen-ocr"]}`) — replace/extend that with the locally-run engine chosen in
Phase 1, rather than inventing a new ledger field. Output feeds the *same*
cleanup layer as Tier 1.

### Tier 3 — optional accuracy pass (flagged pages only)

For pages QA flags, run **Marker's `--use_llm`** mode (merges tables across
pages, formats tables, handles inline math). Because upstream text is
already clean, the model polishes rather than reconstructs. Not run on every
page. Unchanged from the original plan.

---

## 3. Shared cleanup layer — already exists, verify before touching

`extract_manifesto.py` already implements margin/rotated-slogan dropping,
header/footer stripping, landscape-spread splitting, list-prefix
normalisation, and whitespace/heading tidy — it's the accumulated product of
the per-series lessons-learned sections in `README.md`. There's also a
standalone `manifesto_spacing_fixer.py` (in the sibling `Python scripts/`
folder) for post-extraction spacing artefact repair.

**Task for Phase 2 is not "port cleanup logic verbatim" (there's nothing to
port from) — it's "make sure Tier 2 OCR output is piped through the same
functions Tier 1 already uses"**, and to check whether OCR engine output
(which won't have `pdfplumber` character-level geometry) breaks any
geometry-dependent step (e.g. `upright == False` slogan detection needs a
bounding-box-orientation fallback for OCR output, per the original plan's
caveat — still valid).

---

## 4. QA against the original — three layers

The principle throughout: **classify discrepancies, never re-transcribe.**

### Layer A — structural lint: already exists, this is `qa_check.py`

`qa_check.py` (873 lines) already implements exactly this layer, more
thoroughly than originally scoped: coverage ratio (C1, vs. `pdftotext`
baseline), heading sanity (H1-H6), bullet artefact detection (B1-B4),
paragraph artefacts (P1-P4), spacing (S1-S4), encoding (E1-E3),
imprint/layout (I1-I2), vertical fragments (V1-V3), and a **separate**
reading-order category (R1-R3) that explicitly distinguishes "coverage
healthy" from "reading order suspect" — precisely the goal this plan
originally set out to build. It already supports `--json`, `--strict`, and
`qa_allowlist.yaml` for suppressing known false positives.

**Nothing to build here.** Run it as-is against Tier 2 output; extend the
allowlist if OCR output trips new false-positive patterns.

### Layer B — vision-model audit: genuinely new, build this

Nothing implements this in this repo (the classification-only
`audit_manifesto_llm.py` mentioned in the original draft only exists in the
separate Antigravity/Gemini project, and even there it's a Gemini-specific
script not something to copy across). Build it fresh, using the audit
principle already established for this project:
- Render each page image (handle landscape spreads as already done
  elsewhere in the toolkit).
- Send page image **+** corresponding Markdown chunk to a vision-capable
  model.
- **Constrain the prompt to classification**, not transcription. Ask it to
  return a structured list of discrepancy *types*:
  `missing_block | column_join_error | style_mismatch | spurious_text |
  ordering_error`, each with a short locator. Do **not** ask it to output
  corrected text.
- Emit a structured `[md_basename]_audit_report.md`.

This can be a genuinely fresh Claude-based script — there's no existing
Claude vision-audit code in this repo to build from, and the Gemini version
in the Antigravity project isn't something to port (different model,
different project, and it was never proven reliable there).

### Layer C — bounded human spot-check: partially exists, extend it

`transcribe_pipeline.py` is already "intentionally human-gated" — the
ledger's per-page `status` field already distinguishes reviewed/needs-review
states, and `repair_markdown()` deliberately stops short of auto-fixing
anything beyond Contents/TOC cleanup, leaving everything else
`needs-human-review`. What's missing is a **generated checklist view**:
first page, last page, every page flagged by Layer A/B, plus a random ~10%
sample — extend `transcribe_pipeline.py` (or add a thin new script) to
render that from an existing ledger rather than building parallel state.

Given these are political documents where fidelity underpins the archive's
credibility, this lightweight human gate on flagged pages remains worth the
minutes.

---

## 5. Phased implementation plan

| Phase | Goal | Est. |
|-------|------|------|
| 1 | ~~**Spike + benchmark the OCR tier only.**~~ **Done 2026-07-11 — see §9.** Marker picked as primary engine. | ½ day |
| 2 | ~~**Wire Tier 2 into the existing ledger.**~~ **Done 2026-07-11 — see §10.** | 1–2 days |
| 3 | ~~**QA rework — Layer B and C only.**~~ **Done 2026-07-11 — see Sec.11.** | 1 day |
| 4 | ~~**Run Alba end-to-end.**~~ **Done 2026-07-11, one caveat.** Full `new` pipeline run confirmed clean (no filter workaround, ever — see Sec.0.1/Sec.7). `qa_check.py` run against the draft: 46 issues, sensible throughout — 1 genuine encoding artifact caught (U+FFFD before "Health and Care", a decorative glyph that didn't render), 1 expected false-positive (C1 coverage "764%", because its `pdftotext` baseline is meaningless on a document this scanned — not a real problem). Checklist (Layer C) confirmed on this document. **Vision audit (Layer B) could not be confirmed live** - no API credentials in this environment; structurally validated via `--dry-run` only (see Sec.11). | ½ day |
| 5 | **Document.** Kept current throughout rather than as a final pass — see Sec.0/Sec.9/Sec.10/Sec.11 for the running decision log. Remaining before this file can be considered "done": run Layer B for real once credentials are available and sanity-check its first report by hand (Sec.11); decide whether to manually transcribe the 5 photo-headline pages' slogans (Sec.10) or leave them flagged; the page-2 column-interleaving finding is intentionally left unfixed (Sec.10) pending more examples. | — |

---

## 6. File inventory

**Keep as-is (already correct, no changes needed)**
- `extract_manifesto.py` — mature Tier 1 extractor + cleanup layer. Don't
  touch unless Phase 2 finds a specific OCR-output-compatibility gap.
- `qa_check.py` — Layer A structural lint, fully implemented.
- `manifests/*.yaml` + `TEMPLATE.yaml` — human-authored per-page override
  mechanism, complementary to (not replaced by) `classify_page()`.
- `profile_pdf.py`, `extract_compare.py`, `spot_check.py`,
  `resolve_output.py`, `finalize_manifesto.py`, `log_conversion.py`,
  `check_headings.py` — all functioning, unrelated to the OCR gap.

**Extend**
- `transcribe_pipeline.py` — replace the unconfigured `cloud_ocr` stub with
  a real local-engine call (Phase 2); add a Layer C checklist generator
  (Phase 3).

**Retire**
- Nothing. The files the original draft named for retirement
  (`extract_manifesto_ocr.py`, `clean_ocr_manifesto.py`) don't exist in this
  repo — that cleanup already happened by simply never being built here.

**Create**
- A Tier 2 OCR wrapper (name TBD in Phase 1 — could be a new module or a
  function added to `transcribe_pipeline.py`, decide once the engine is
  chosen and its calling convention is known).
- `qa_audit_vision.py` (or similar) — Layer B vision classification script,
  Claude-based, built fresh.

---

## 7. Decisions & rationale

- **The recitation-filter/adversarial-workaround story is real but belongs
  to a separate project** (`/Users/mosmi/Documents/Antigravity/Projects/transcription-toolkit/`,
  Gemini-API-based, never git-tracked, never merged into this repo). See §0.1.
  The underlying lesson still applies — never drive a chat/vision LLM to
  *transcribe* page images, only to *classify* — but there is no corrupted
  output or bypass hack to clean up in this codebase.
- **Don't rebuild the router or Layer A.** `classify_page()` and
  `qa_check.py` already do this work, more thoroughly than the original
  draft assumed, and are exercised across ~26 real manifestos. Rebuilding
  either risks regressing already-verified output for no benefit.
- **Don't replace Tier 1.** `extract_manifesto.py` is mature and tuned.
  Docling/Marker evaluation is scoped to Tier 2 (scanned pages) only, not a
  wholesale native-PDF extractor swap.
- **Docling as primary candidate (Apple Silicon).** MLX acceleration gives
  local VLM-quality layout parsing without a GPU. Marker is the strong
  alternative and provides `--use_llm` for the Tier 3 polish pass. Final
  choice is made empirically in Phase 1 on the Alba benchmark, not from
  reputation.
- **LLM verifies, never transcribes.** Prevents hallucination in Layer B.
  All new model prompts are classification/diff prompts, never
  "transcribe this image."
- **The ~11,900-word Alba figure is unverified — do not treat it as ground
  truth.** Establish a real word count from Phase 1's OCR output plus manual
  spot-reading, per §0.2.

---

## 8. Open questions / to confirm in Phase 1

- ~~Whether any manifestos are *mixed* (some scanned pages, some native) and
  need per-page rather than per-document routing.~~ **Answered:**
  `classify_page()` already routes per-page, so mixed documents are handled
  for free once Tier 2 is wired in.
- Confirm the exact text-layer word threshold for `sparse` vs. genuinely
  readable — `classify_page()` currently uses ≤5 words as the `sparse`
  cutoff; validate this against real mixed-content pages once Tier 2 exists.
- ~~Docling vs Marker vs Tesseract-as-already-available — decide on Phase 1
  benchmark output quality specifically for Alba's 57 scanned pages.~~
  **Answered (2026-07-11):** Marker wins. See §9 for the full benchmark.
- ~~What is Alba's actual true word count?~~ **Answered:** ~11,400–11,500
  words. Tesseract (11,492) and Marker (11,466) landed within 0.2% of each
  other independently; both are close to the original unverified ~11,900
  estimate, which turns out to have been roughly right after all — it was
  the earlier *corrupted* Gemini-OCR run (1,760 words) that was the outlier,
  not the estimate.
- Licensing note: Marker code is GPL and its model weights use a modified
  Open-RAIL-M licence (free for personal/research use) — fine for this
  project, but record it here for completeness. **Relevant now that Marker
  is the Phase 1 pick** — confirm this is acceptable before Phase 2 wires it
  into `transcribe_pipeline.py` as a dependency.

---

## 9. Phase 1 results (2026-07-11) — benchmark against `manifesto.pdf` (Alba, 57pp)

All three engines run against the real file, no manifest overrides, no
LLM-polish pass (Tier 3 `--use_llm` not tested yet). Full outputs archived
in the scratchpad for this session; not copied into the repo since they're
raw benchmark artifacts, not a finished transcription.

| Engine | Word count | Wall time (incl. first-run model download) | Structure | Word-boundary accuracy |
|---|---|---|---|---|
| Tesseract (`pytesseract`, 300dpi) | 11,492 | ~144s | Raw — one line per visual line, needs paragraph-reflow cleanup that doesn't exist yet | Good |
| Docling (default pipeline, RapidOCR/CPU — **not** the MLX path) | 10,462 | ~650s (~11 min) | Good — real paragraph reflow, semantic headings (`## Foreword`) | Real failures: stylized/dense text blocks lost word boundaries entirely (e.g. a pull-quote rendered as `"...PrimeMinister,but asToryPrimeMinister againstScotland'sParliamentrepresenting..."`); pervasive soft-hyphen line-break artifacts (`time­ table`, `cour­ age`) left unjoined |
| **Marker** (`marker_single`, default settings) | 11,466 | ~23–25 min (includes one-time Surya model download; steady-state should be faster) | Best — paragraph reflow, correct heading text incl. spacing (`SHAKE THINGS UP`, not Docling's `SHAKETHINGSUP`) | Best — same dense pull-quote rendered correctly as `"First Minister against Prime Minister, but as Tory Prime Minister against Scotland's Parliament..."`; held up on manual spot-check through the health/education policy section (~55% into the document) |

**Fidelity check against the source image:** manually compared page 3
(the Foreword) against all three outputs. Two things that looked like
likely OCR errors turned out to be **verbatim in the original PDF**, not
engine mistakes: "Governor of Corton Vale" (all three engines agree; the
source itself prints "Corton Vale") and "we are standing be in a position"
(an apparent typo in ALBA's own manifesto, faithfully preserved by all
three engines rather than silently corrected). This is a good sign — it's
exactly the "verify, don't (re)generate" behaviour §1 requires, and a
useful reminder that some things that look like transcription errors on
review will need cross-checking against the actual page image before
assuming the OCR engine is wrong.

**Decision: Marker is the Phase 1 pick.** It matches Tesseract's word count
(within 0.2%) while producing structurally clean, LLM-polish-ready Markdown
that Tesseract's raw line-per-line output doesn't, and it doesn't share
Docling's word-boundary failures in dense/stylized text — which is a
correctness problem, not just a formatting inconvenience. Docling's slower
default pipeline also wasn't using its MLX acceleration path; that's worth
revisiting only if Marker turns out to be a bottleneck in practice, since
quality (not speed) was the deciding factor here.

**Not yet evaluated:** olmOCR (skipped — Marker already cleared the bar);
Marker's `--use_llm` Tier 3 polish pass (deferred to Phase 3, only run on
QA-flagged pages per §2); Docling's MLX-accelerated pipeline specifically
(the default CPU/RapidOCR path was tested, not the Apple-Silicon-optimized
one — if Docling is reconsidered later, this should be retested properly
configured).

---

## 10. Phase 2 results (2026-07-11) — Marker wired into `transcribe_pipeline.py`

### What changed

`build_page_records()` in `transcribe_pipeline.py` now runs in two phases:

1. **Phase 1** classifies every page via the existing `classify_page()`
   (cheap, `pdfplumber` word geometry only) and collects the
   `image-only`/`sparse` page indices.
2. If any exist, **Marker runs once** for the whole document — not once per
   page — via `marker_single --page_range <indices> --output_format chunks`.
   The `chunks` format was chosen deliberately: each output block carries
   its true 0-indexed page number in `block["id"]` (e.g. `/page/6/Text/2`),
   which is what makes it possible to attribute OCR text back to the right
   `PageRecord` at all. The plain `markdown` output format has no reliable
   per-page boundary marker (image filenames are the closest thing, and
   they're absent on pages with no figures) — `chunks` avoids that ambiguity
   entirely.
3. **Phase 2** builds local-extraction candidates exactly as before
   (`pdftotext` × 3 variants, `pdfplumber` × 2 variants), plus a new
   `marker-ocr` candidate on pages Marker covered, run through
   `extract_manifesto.py`'s existing `post_process()` cleanup per §3. For
   `image-only`/`sparse` pages, `marker-ocr` is now *preferred outright*
   over the generic artifact-score/word-count-proximity heuristic (that
   heuristic assumes a plausible local text layer to compare against, which
   by definition doesn't exist on these pages).

The `cloud_ocr` ledger field is no longer a static
`"not-configured"`/Mistral/Qwen stub — it reports the real engine, status,
and page counts for that run.

Degrades safely in every failure mode: no `image-only`/`sparse` pages →
Marker never invoked; `marker_single` not installed → `status: unavailable`,
falls through to prior behaviour; Marker runs but produces nothing parseable
→ `status: failed`, same fallback. No existing manifesto's processing can
regress from this change — the only new code path only activates on pages
that previously had no viable candidate at all.

### End-to-end validation run: `transcribe_pipeline.py new manifesto.pdf` on Alba

```
cloud_ocr: {"engine": "marker", "status": "ran", "pages_attempted": 54, "pages_succeeded": 49}
```

**Confirms a real finding from the router, not just the OCR tier:** Alba's
manifesto isn't purely scanned. Pages 2, 4, and 29 (0-indexed) classify as
`single-column` with genuine embedded text (589, 772, and 138 words
respectively) — `classify_page()`'s per-page routing correctly left them
alone and sent only the other 54 pages to Marker. This is the "mixed
manifestos handled per-page for free" behaviour §8 predicted, now observed
on a real document rather than theorized.

**Marker OCR quality on the pages it did cover matches the Phase 1
benchmark** — e.g. the "Delivering Independence" section (draft.md:232-268)
reads cleanly with correct headings and paragraph structure, consistent
with §9's findings.

**New finding: 5 of 54 attempted pages produced no text at all** (draft
indices 3, 5, 9, 25, 31). Inspected each against the source page image:
all five are full-bleed photo-background pages with a large stylized
headline overlaid (e.g. "SCOTLAND NEEDS A BIT OF GALLUS FOR WHAT COMES
NEXT", "THE TIME FOR TARGETS IS LONG PAST..."). Marker's layout model
classifies the entire page as a single `Figure` block and never runs OCR
on the overlaid text — confirmed by inspecting the raw `chunks` JSON, which
contains only `{"block_type": "Figure", "html": "<p><img .../></p>"}` for
each of these pages, no `Text`/`SectionHeader` blocks at all. **This is not
silent data loss** — `build_page_records()`'s existing `NO_CANDIDATE`
handling (unchanged) correctly leaves `selected_candidate: null` and
`status: needs-human` on these pages, and `assemble_new_draft()` (also
unchanged) writes a visible `<!-- Page N: no selected text candidate -->`
placeholder rather than dropping the page. A human reviewer working the
ledger will see exactly which 5 pages need manual transcription (in this
case, just a one-line slogan each). Worth a future follow-up (not done
here, out of scope for this pass): try Tesseract specifically as a fallback
on `Figure`/`Picture`-only pages, since Tesseract OCRs the whole rendered
page image indiscriminately rather than relying on Marker's layout
classification to decide what counts as OCR-able text in the first place.

**Separate finding, pre-existing, *not* caused by this change:** page 2 (the
Foreword) has a genuine text layer but its `pdfplumber`/`pdftotext`
candidates are badly column-interleaved (e.g. "ALBA a political party. Not
yet month old. is new one bitious..." — two columns read line-by-line
instead of column-by-column). This affects any multi-column native-text
page processed via `new`/`audit`, independent of the OCR work in this
phase.

**First fix attempt (2026-07-11) failed and was reverted — recorded here so
a future session doesn't repeat it.** The first instinct was to wire
`extract_manifesto.py`'s column-aware `extract_page()` in as another
candidate, force-preferred over the generic pool for `single-column`/
`two-column` pages, using `detect_column_split()` to auto-detect the
gutter x-coordinate once per document. **This made the draft worse, not
better, and was reverted in full** (`build_page_records()` is back to
exactly the Phase 2 state above; no `column-aware` candidate exists).
Two things went wrong:

1. `detect_column_split()` returned `None` for this document — most of its
   5-page sample is `image-only` (zero words), starving the x0 histogram it
   needs. With no split detected, `extract_page()` silently fell back to
   its single-column path (`get_styled_lines(page, 0, page_width, ...)`),
   which sorts words by y-position across the *full* page width — hitting
   the exact same cross-column interleaving as the naive candidates, now
   with confusing bold/italic markup layered on top from `word_style()`
   misfiring on this font.
2. More importantly, **the premise was wrong**: `pdftotext` (no flags) was
   already producing clean, correctly-ordered text for page 2 *and* was
   already the correctly-selected candidate for pages 4 and 29 before any
   of this started. The actual bug is narrower than "the candidate pool
   lacks a column-aware extractor" — it's that page 2's `artifact_score`
   narrowly favours the garbled `pdfplumber` candidate (16.37) over the
   already-clean `pdftotext` candidate (17.77), a 1.4-point gap that
   doesn't reflect the real quality difference between them. `extract_page()`
   was never actually necessary for this document; the fix (if there is one
   worth making) is more likely a small correction to `artifact_score()` or
   the tie-break logic, not a new extraction tier. `extract_manifesto.py`'s
   column model also isn't a drop-in, zero-config fix in general — per
   README/PROMPT.md, the 26 manifestos it's already been used on were
   hand-calibrated (`--col-split`, `manifests/*.yaml`), not auto-detected;
   treating it as a blind, always-safe upgrade was the core mistake here.

**Second investigation (2026-07-11, same day): checked the narrower
tie-break idea and rejected it too — recorded so a future session doesn't
retry it.** Broke down `artifact_score()`'s components for page 2's two
closest candidates:

| Candidate | double_words | bullet_mid | singletons | raw_bullets | **total** |
|---|---|---|---|---|---|
| `pdftotext` | 0 | 5 (→16.92) | 0 | 5 | **17.77** |
| `pdfplumber` | 1 (→8.49) | 2 (→6.79) | 3 | 3 | **16.37** |

Both scores turned out to be driven by **false positives, not real signal**.
`pdftotext`'s `bullet_mid` hits are all ordinary em-dashes in prose ("-
Scotland needs independence", "- but", "- we") that `RE_BULLET` (`-\s+`)
misreads as bullet glyphs — nothing to do with column order.
`pdfplumber`'s score is dominated by a single coincidental duplicate-word
match. Neither term actually measures reading-order coherence; on this
page it's pure chance that `pdftotext` came out ahead. A "prefer `pdftotext`
when scores are close" tie-break would be tuning to that coincidence, not
fixing anything, and there's no second multi-column native-text page in
this document to check whether it would even generalize (pages 4 and 29
are genuinely single-column and were never at risk). **No code change made.**

**What actually already handles this correctly: the human gate.** Page 2's
`pdfplumber` artifact score (16.37) already clears the existing
`ARTIFACT_SCORE >= 8` threshold, which already sets `status: needs-human`
regardless of which candidate is auto-selected as the draft starting point.
A reviewer opening the ledger has all 5 raw candidate files
(`pages/page-002.*.txt`) side by side and can pick the clean one by eye —
which is exactly what "intentionally human-gated" (the module's own
docstring) is for. The auto-selected candidate only matters as a *draft
starting point*, never as final output; this page was never going to reach
`manifesto.md` without a human looking at it either way.

**Verdict: this is not worth further automated fixing right now.** It's a
real but narrow, single-page, single-document finding, already caught by
the existing review gate. Revisit only if the same failure shows up on
other documents' multi-column native-text pages, with enough examples to
find a signal that isn't coincidental.

---

## 11. Phase 3 results (2026-07-11) — Layer C (checklist) and Layer B (vision audit)

### Layer C — `transcribe_pipeline.py checklist`

New subcommand, no new file needed (extends the existing orchestrator per
the plan). `generate_checklist()` reads any existing `ledger.json` and
selects: first page, last page, every page whose `status` is
`needs-human`/`blocked` (already computed by `build_page_records()` — no
new flagging logic needed), plus a seeded random ~10% sample of whatever's
left. Writes `checklist.json` (structured) and `checklist.md` (a literal
`- [ ]` Markdown checklist a human can work through) next to the ledger.

Tested against two real ledgers with very different shapes:
- **Alba** (57 pages, 56 flagged — this document is genuinely 95% scanned):
  `checklist_count: 57, flagged_count: 56, sample_count: 1`. Correct: with
  almost everything already flagged, there's almost nothing left to sample.
- **Labour 2024** (136 pages, 98 flagged, 38 clean): `checklist_count: 113,
  flagged_count: 98, sample_count: 14` — 14 is `round(136 * 0.10)`, showing
  the sampling logic actually engages correctly on a normal document where
  most pages *aren't* flagged, not just degenerately on Alba where nearly
  everything was already caught anyway.

### Layer B — `qa_audit_vision.py` (new file)

Sends a page's rendered image (reusing the PNG `build_page_records()`
already rendered - no re-rendering) plus the ledger's *selected candidate
text* for that page (not the final edited `manifesto.md`, which has no
reliable per-page boundary once a human has edited it - the page-level
candidate files are the correct, always-available unit to audit against)
to a Claude vision model. The prompt is deliberately classification-only:
explicit "never rewrite, correct, or reproduce the page's text yourself,
even partially, even to illustrate a point" instruction, locators capped
at ≤8 quoted words, and a closed five-type discrepancy vocabulary from
§4 (`missing_block`, `column_join_error`, `style_mismatch`, `spurious_text`,
`ordering_error`). Supports `--pages 0,5-10` or `--from-checklist` (reads
the sibling `checklist.json`, so Layer C's output feeds Layer B directly).
Guarded by `--max-pages` (default 25, since every page is a real billed API
call) requiring `--force` to exceed - Alba's 57-page checklist correctly
refused to run without it.

**Could not be tested against the live API in this session — no
`ANTHROPIC_API_KEY` is available in this sandbox.** Verified everything
short of that:
- `--dry-run` against real Alba pages confirmed correct page→image→text
  resolution, including the two most useful test cases in this document:
  page 2 (the still-garbled Foreword — a real `column_join_error` case for
  a live run to classify) and page 3 (a "no selected candidate" photo
  page — a real `missing_block` case).
- A real (non-dry-run) call without credentials failed exactly as
  expected: caught per-page rather than crashing the batch, surfaced as a
  clear `audit_error` finding in the report ("Could not resolve
  authentication method...") rather than a raw traceback.
- Whoever runs this for real needs `ANTHROPIC_API_KEY` set and should
  sanity-check the first real report by hand against the two pages above
  before trusting it on a full checklist.

### File inventory update

`qa_audit_vision.py` added to `README.md`'s tool table. No files were
retired or renamed.
