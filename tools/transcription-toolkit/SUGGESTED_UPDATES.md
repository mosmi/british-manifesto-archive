# Suggested Transcription Toolkit Updates

These notes come from the recent Welsh Conservative manifesto conversions, especially the 2005 and 2010 PDFs. The toolkit already handles many clean and moderately complex PDFs well, but these conversions exposed some repeated failure modes that would be worth capturing as reusable tooling rather than solving manifesto by manifesto.

## 1. Add a preflight layout profiler

Before extraction, add a script or `--profile` mode that reports:

- page count, dimensions, rotation, and text-layer availability
- word-count baseline from `pdftotext`
- per-page word counts from `pdfplumber`
- likely blank/logo-only pages
- likely running header/footer zones, based on repeated text near page edges
- x-coordinate histograms for representative pages
- suggested reading mode per page: single-column, two-column, full-width, or manual review

The Welsh Conservative 2005 manifesto looked globally like a simple two-column PDF, but several pages were not normal body pages: cover, divider page, action-page, summary-box pages, and blank/logo pages. A per-page profile would have made those exceptions explicit before extraction.

Suggested output:

```text
page 0   cover/full-width        words=15    keep footer/slogan
page 1   blank/logo              words=0     skip
page 2   two-column              split≈304   normal body
page 18  summary box             words=41    include as bullets
page 21  divider/full-width      words=7     heading page
page 30  full-width action page  words=96    keep imprint zone
page 31  logo-only               words=3     skip
```

## 2. Replace global column detection with per-page region detection

The current extractor has useful global and per-page split helpers, but the Welsh Conservative PDFs showed that the important decision is often not just “what is the split x-coordinate?” It is “which page regions are body text, sidebars, pull quotes, summary boxes, or full-width content?”

The 2005 PDF needed this reading order:

1. preamble/full-width rows
2. left column top-to-bottom
3. right column top-to-bottom
4. special handling for pages that are not two-column body pages

A good generalisation would be:

- detect row groups from words, not only chars
- identify stable right-column starts by repeated x0 values
- only split rows below the first detected body-column row
- treat rows above the first detected column row as a full-width preamble
- let the page profile override extraction mode for cover, divider, action, blank, and logo-only pages

This would avoid the common bad output where left and right columns braid together line by line.

## 3. Add a page manifest option

For complex PDFs, a small sidecar YAML/JSON file would be cleaner than hard-coding skip pages and special pages in one-off scripts.

Example:

```yaml
title: Welsh Conservatives Election Manifesto 2005
footer_cut: 800
pages:
  0:
    mode: full-width
    footer_cut: null
  1:
    mode: skip
  18:
    mode: summary-box
  21:
    mode: full-width
    heading_level: 2
  30:
    mode: full-width
    footer_cut: 826
  31:
    mode: skip
```

Then the extractor can run:

```bash
python extract_manifesto.py manifesto.pdf output.md --manifest page-map.yaml
```

This keeps repeatable judgement calls visible and auditable.

## 4. Treat pull quotes as first-class objects

Pull quotes caused the most visible artefacts in the 2005 manifesto. They were often large/bold, so the extractor promoted fragments into headings:

```markdown
## “ People who work hard, pay thing should be rewarded, not
## their taxes and do the right punished
```

The toolkit should detect likely pull quotes and either:

- exclude them when they duplicate body text, or
- render them as blockquotes when they contain unique or useful text.

Useful heuristics:

- text starts or ends with quotation marks
- unusually large or bold text but split across non-contiguous row fragments
- short phrase fragments that appear near body text columns
- heading candidate starts with `“`, `”`, or a lowercase continuation
- quote text is a fuzzy duplicate of nearby body text

Add a QA rule that flags any heading beginning with a quote mark or lowercase continuation word. Those should almost never be accepted silently.

## 5. Detect sidebars and summary boxes

The Welsh Conservative PDFs regularly used summary boxes at the ends of sections. In `pdftotext`, these appeared interleaved into body paragraphs:

```text
... cutting the cost of the Lower Taxes regulations ... All new • Value for money regulation ...
```

The toolkit should identify compact bullet/sidebar regions and extract them separately after the main body text for that page or section.

Useful heuristics:

- several bullet glyphs in a small x/y region
- heading-sized text followed by short bullet rows
- region text is much shorter line length than body text
- bullets are aligned at a different x-coordinate from body columns

Suggested Markdown:

```markdown
## Lower Taxes

- Value for money
- A lower tax economy
- Support for saving, dignity for pensioners
- Less regulation
- A stable economy with low interest rates
```

## 6. Improve heading verification

`check_headings.py` is useful, but on highly designed PDFs it currently produces too much noise because it treats many body rows as heading issues. It would be more actionable if it had modes:

- `--major-only`: check only text above a configurable font-size percentile
- `--markdown-headings-only`: compare PDF heading candidates to existing Markdown headings
- `--ignore-running`: ignore repeated header/footer strings
- `--json`: output machine-readable issues for review scripts
- `--min-words` and `--max-words`: avoid single-word decorative fragments

The most valuable heading check from these conversions was not “find every heading-like row.” It was “find obvious impossible Markdown headings,” such as:

- heading starts with opening/closing quote mark
- heading starts lowercase
- heading is a sentence continuation
- adjacent headings should be merged
- heading contains embedded body text or bullets

## 7. Add a post-extraction QA scanner

Create a `qa_manifesto.py` script that runs after extraction and flags common artefacts:

```bash
python qa_manifesto.py output.md --pdf manifesto.pdf
```

Checks worth adding:

- word-count coverage against `pdftotext`
- raw running footer/header strings still present
- raw bullet glyphs (`•`, `●`) still present
- replacement characters (`�`)
- page-number-only paragraphs
- repeated all-caps slogans without spacing, e.g. `AREYOUTHINKING...`
- headings that start with quote marks, lowercase words, or punctuation
- heading fragments repeated on adjacent lines
- paragraphs containing embedded bullet glyphs mid-sentence
- suspicious orphan lines after bullet lists, e.g. `tenants`, `friendly cars`
- large drops in per-page word coverage

This scanner would have caught nearly every remaining 2005 issue before manual inspection.

## 8. Preserve a reproducible custom-script path

When the general extractor needs manifesto-specific overrides, the toolkit should encourage saving them in `scripts/` rather than leaving them in temporary files. A useful pattern would be:

```text
scripts/
  extract_welsh_conservative_2005.py
  extract_welsh_conservative_2010.py
```

Each script should:

- import shared functions from the toolkit
- define only the PDF path, output path, page manifest, and local cleanup rules
- print final word coverage
- run the QA scanner

This avoids losing hard-won layout fixes and makes later corrections reproducible.

## 9. Add a small cleanup-rule framework

The one-off converters needed targeted post-processing, but the pattern was consistent:

- normalise common fused words from cover/imprint text
- convert malformed slogans into readable title case
- demote or remove false quote headings
- merge heading continuation lines
- merge action-page continuation fragments
- move interleaved summary-box bullets into proper lists

Instead of burying those in ad hoc `str.replace()` calls, add a small ordered cleanup framework:

```python
CleanupRule(
    name="demote_quote_headings",
    pattern=r"(?m)^## [“”](.*)$",
    replacement=r"> \1",
)
```

Support both generic rules and document-specific rules. Print a count of replacements per rule, so surprising cleanups are visible.

## 10. Update the README workflow

The README should recommend this end-to-end workflow for complex PDFs:

1. Run preflight profile.
2. Choose extraction mode per page, not only per document.
3. Run extractor with a page manifest.
4. Run QA scanner.
5. Inspect flagged pages visually.
6. Run heading verification in major-heading mode.
7. Compare word coverage, accepting a small undercount when repeated footers are stripped.
8. Save any custom overrides as a named script in `scripts/`.

The headline lesson is that word coverage is necessary but not sufficient. The 2005 output had healthy coverage while still containing braided sidebars, false pull-quote headings, and orphaned summary-box continuations. The toolkit should make those failure modes mechanically visible.

## 11. Learnings from the Scottish Greens 2005–2024 QA session

These notes come from a QA pass over all five Scottish Greens manifestos (2005, 2010, 2015, 2019, 2024) and the subsequent reconstruction of the 2005 "Would you buy a used planet from these people?" section from the source PDF.

### `extract_text(layout=True)` as a one-off diagnostic

When a specific page is known to be garbled — but the rest of the document extracted cleanly — do not attempt to retune the global extraction pipeline. Instead, use pdfplumber's layout-preserving text extraction on that page alone:

```python
import pdfplumber

with pdfplumber.open("manifesto.pdf") as pdf:
    page = pdf.pages[16]   # 0-indexed
    print(page.extract_text(layout=True))
```

`layout=True` renders approximate x-positions as spaces, producing an ASCII-art approximation of the page layout. On a two-column comparison table (like the "Would you buy a used planet?" page in the 2005 Scottish Greens manifesto), this makes the column structure immediately visible and allows accurate manual reconstruction. The approach is much faster than rewriting the extractor when only one or two pages are affected.

**Practical steps:**

1. Identify the page index (0-indexed) from a visual inspection of the PDF.
2. Run `extract_text(layout=True)` on that page and print the raw output.
3. Read column boundaries from the ASCII layout — left column content typically starts near x-position 0–40 in the rendered string, right column content around x-position 50–80+.
4. Reconstruct the Markdown by hand from the layout output, referencing the PDF image for visual confirmation of any ambiguous fragments.

This approach found and corrected the six sub-sections of the 2005 comparison page (Climate Change, Transport, Sustainability, Corporate Accountability, Civil Liberties, Environment) that had been previously transcribed as garbled interleaved text.

### Repeated consecutive words (S4 check)

Column-boundary extraction sometimes produces a word repeated twice in a row: "of of", "the the", "in in". These are easy to overlook in manual review because the eye skips them. The new S4 check in `qa_check.py` detects them with a regex:

```python
RE_DOUBLE_WORD = re.compile(r'\b(\w{2,})\s+\1\b', re.IGNORECASE)
```

A confirmed instance from the 2024 manifesto: `"of of"` at a column boundary. The S4 check fires as a warning rather than an error because some natural-language phrases (e.g. "had had", "that that") are valid, and require human confirmation before remediation.

### Dangling preposition/article at bullet end (B4 check)

When a bullet item is truncated at a column or page boundary, the truncation often happens after a short function word — a preposition, article, or conjunction — leaving the bullet ending with "to the", "and", "in", or similar. These are harder to catch than mid-sentence truncations because the bullet text looks superficially complete.

The new B4 check in `qa_check.py` flags bullets that end with one of these function words:

```python
RE_DANGLING_END = re.compile(
    r'\b(the|a|an|at|in|of|for|by|with|to|from|on|into|and|or|but|'
    r'its|our|their|this|these|those|which|that|who|whom)\s*$',
    re.IGNORECASE,
)
```

A confirmed instance from the 2024 manifesto: a bullet ending with "to the Scottish" (continuation "Government" was missing). The B4 check fires as a warning, not an error, because some bullets legitimately end with a preposition (e.g. "...what we stand for").

### OCR close-word substitutions in older PDFs

Older scanned PDFs (pre-2010) are vulnerable to OCR close-word substitutions — words that look similar to the correct word and pass spell-check but are wrong. Examples found in the 2005 Scottish Greens manifesto: `"exploitaiton"` (simple typo, not OCR), and garbled proper-noun fragments in the comparison section.

There is no automated rule that reliably catches close-word substitutions without generating many false positives. The recommended approach is:

- Run `qa_check.py` and manually review all **warning** and **error** items
- Pay particular attention to proper nouns, party names, politician names, and quoted speech — these are the highest-risk areas for OCR substitution because they do not appear in any spell-checker dictionary
- For quoted speech sections, cross-reference against the source PDF page image rather than trusting the text layer alone

This is particularly important for manifestos that include extensive quotation material (politician statements, external references), as errors in quoted text are invisible to automated checkers.

