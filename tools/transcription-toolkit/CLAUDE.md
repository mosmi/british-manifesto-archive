# Before touching manifesto text in this directory

**Never directly rewrite or retype manifesto text by reading a page image**,
even when asked to "fix" a flagged issue. This toolkit exists specifically
to avoid that pattern — see `TRANSCRIPTION_PIPELINE.md` §0.1/§1 for the
incident that motivated it (a prior project's chat-LLM-transcribes-images
approach triggered a recitation filter, and the adversarial workaround for
that corrupted the output). The rule survives even when a rewrite happens
to be accurate: it isn't verifiable without independently re-checking every
word against the image, and nothing catches a fluent-sounding but wrong
version.

If you're asked to fix an OCR/transcription problem on a flagged page:

1. **Check `work/<slug>/pages/page-NNN.*.txt` first.** Every local
   extraction candidate for that page is already sitting there
   (`pdftotext`, `pdftotext-layout`, `pdftotext-raw`, `pdfplumber`,
   `pdfplumber-layout`, `marker-ocr` where applicable). One of them may
   already be correct — a candidate-selection fix (updating
   `transcribe_pipeline.py`'s selection logic) is safer than any rewrite.
2. **Don't assume a candidate is correct because it looks clean.** Column
   order bugs can be entirely internally coherent and still be wrong —
   e.g. `pdftotext` on this document's Foreword page reads column two
   before column one, splitting a sentence across the wrong location, with
   each half individually fluent. Verify structurally: trace whether
   sentences that start in one block actually continue in the next one you
   plan to use, not just whether the prose reads smoothly.
3. **If no candidate is usable** (e.g. a genuinely image-only page with no
   text layer at all), vision transcription of *short, low-stakes* text
   (a headline, a slogan) is a defensible last resort — but it must be
   disclosed inline with an HTML comment (`<!-- transcribed from image via
   vision QA -->`) and still gets the same human review as everything else
   in the pipeline (see §4 Layer C in the plan doc). Never silently blend
   vision-transcribed text in as if it came from OCR.
4. **`qa_audit_vision.py` is classification-only, on purpose.** It reports
   discrepancy types and locators; it never touches `draft.md` or any
   `manifesto.md`. Don't extend it to also emit corrected text, and don't
   let "fix the issues it found" become an instruction to a fresh session
   to re-transcribe from images — that fresh session won't have this
   context unless it reads this file and `TRANSCRIPTION_PIPELINE.md` first.
5. **`qa_audit_vision.py` audits the ledger's selected candidate file for
   each page, not `draft.md`.** If you hand-edit `draft.md` (or a candidate
   `.txt` file), a subsequent audit run on that page reports against
   whatever it was auditing before your edit, until the ledger is
   regenerated. This isn't a bug to "fix" by making it read `draft.md`
   instead — the candidate file is the actual audit unit the ledger tracks;
   just don't be surprised when a report doesn't reflect a manual edit.
6. **It costs real money per page — check `--dry-run` and the per-page cost
   printed in the report before running `--force` at scale.** Default model
   is `claude-sonnet-5`; `claude-haiku-4-5` is ~3x cheaper for this
   classification-only task and worth using as the default once you've
   spot-checked its quality against a few Sonnet-audited pages. Images are
   downsampled to 1568px on the long edge by default (`--max-image-dim`) to
   cut vision-token cost — pass `--max-image-dim 0` only if you need
   full-resolution fidelity for some reason. Reruns merge into the existing
   report by page index; you don't need to re-audit everything just to fix
   a few pages.
