# Before touching manifesto text in this directory

**The sanctioned way to fix a flagged transcription page is
`.claude/skills/manifesto-page-repair/SKILL.md`** (tier 2 of the two-tier
pipeline — see `knowledge/pipelines/transcription.md`). It has Claude read
the flagged page image directly and write a `claude-clean` candidate. That
*is* the current, deliberate design, not a shortcut to avoid — it's how
every Stormont-batch repair in `backlog/tasks/task-003...md` has been done.

An earlier version of this file blanket-banned ever reading a page image to
retype text, citing a recitation-filter corruption incident. That incident
is real, but per `TRANSCRIPTION_PIPELINE.md` §0.1 it never happened in this
repo — it happened in a separate, never-git-tracked Gemini/Antigravity fork.
There's no corrupted output here to clean up, and no ban to keep enforcing
on that basis. The underlying caution is still worth keeping, just not as an
outright ban: an image-read rewrite isn't automatically trustworthy just
because it reads fluently. The skill bakes two checks into its own procedure
to address that, rather than leaving it to a separate document to remember:

1. **Cross-check the deterministic candidate for exact wording** (skill
   step 2) — `pdftotext`/`pdftotext-layout`/etc. came straight from the
   PDF's text layer, so where the image is ambiguous, its wording wins over
   a guess.
2. **An independent, in-session structural audit before marking a page
   `reviewed`** (skill steps 6-7) — a distinct, skeptical re-read of the
   image classifying discrepancies (missing/duplicated/reordered/
   misformatted content), separate from the pass that wrote the
   transcription. This catches wrong reading order and dropped or
   hallucinated blocks (it has caught both, live, in this repo). It does
   **not** catch a subtly-wrong single word sitting inside an otherwise
   well-formed paragraph — that residual risk is real, and matters most on
   pages with no deterministic candidate to cross-check against at all
   (genuinely image-only, no text layer).

If you're picking up a flagged-page repair task, just follow the skill
file — it's self-contained. A few things worth knowing that aren't in it:

- **Check `work/<slug>/pages/page-NNN.*.txt` before assuming a rewrite is
  needed.** Every local extraction candidate for that page is already
  sitting there (`pdftotext`, `pdftotext-layout`, `pdftotext-raw`,
  `pdfplumber`, `pdfplumber-layout`, `marker-ocr` where applicable) —
  sometimes the actual defect is the ledger picking the wrong one, not any
  candidate being wrong.
- **A clean-reading candidate isn't automatically a correct one.** Column
  order bugs can be entirely internally coherent and still be wrong —
  e.g. `pdftotext` on this document's Foreword page reads column two
  before column one, splitting a sentence across the wrong location, with
  each half individually fluent. Verify structurally: trace whether a
  sentence that starts in one block actually continues in the block you
  plan to use next, not just whether the prose reads smoothly.
- **`qa_audit_vision.py` is an optional, billed, genuinely-independent
  cross-check — not part of the default flow.** It's classification-only
  by design (reports discrepancy types/locators, never touches
  `draft.md`/`manifesto.md`, never emits corrected text), which makes it a
  good choice for spot-checking a sample of pages when you want stronger
  assurance than the in-session audit gives, but it costs real money per
  page (check `--dry-run` and the per-page cost before running `--force`
  at scale; `claude-haiku-4-5` is ~3x cheaper than the sonnet default for
  this task) and requires `ANTHROPIC_API_KEY`/`GEMINI_API_KEY`. It audits
  the ledger's selected candidate file for each page, not `draft.md` — if
  you hand-edit `draft.md` directly, a subsequent audit on that page
  reports against whatever it audited before your edit until the ledger is
  regenerated.
