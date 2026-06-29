# Recommendations from Recent Manifesto Markdown Conversions

These recommendations come from converting the recent batch of Welsh Labour, Northern Ireland Conservative, Green Party NI, Scottish Conservative, and Scottish Labour manifesto PDFs into Markdown.

The toolkit has already absorbed several lessons from earlier Welsh Conservative work: profiling, page manifests, QA checks, and complex-PDF workflow guidance. The newer batch suggests a next layer of improvements: better extraction fallback selection, reusable conversion scaffolding, QA tuning, and stronger support for older spread-style PDFs.

## 1. Add an extraction strategy runner

The most useful manual pattern was trying several extractors quickly, then choosing the least damaged source for the final converter.

Recommended toolkit command:

```bash
python extract_compare.py manifesto.pdf --out-dir /tmp/manifesto-extracts
```

It should run, where available:

- `pdftotext`
- `pdftotext -layout`
- `pdftotext -raw`
- `pdftotext -fixed N`, perhaps with a few sensible widths
- `pdftotext -bbox-layout`
- MarkItDown, if installed
- OCR fallback for image-only or damaged text-layer PDFs

The output should include:

- word counts by method
- page counts and form-feed counts
- raw bullet glyph counts
- repeated-word artefact counts, such as `to to`, `and and`, `for for`
- mid-sentence bullet counts
- likely vertical-running-header fragments
- sample snippets from the first body page, a middle page, and the last page
- a recommended starting method

Why this matters: the Scottish Labour 2001 PDF had a text layer and looked extractable, but `pdftotext` braided spread columns. MarkItDown gave a much cleaner reading order for most pages. Other PDFs in the batch were the reverse: plain or layout `pdftotext` was easier to clean than richer extraction.

## 2. Treat rotated A3 spread PDFs as a named layout class

The 2001 Scottish Labour manifesto was an older A3 PDF with page rotation and two logical pages printed on each physical PDF page. This is different from an ordinary two-column page.

Add a profiler classification such as:

```text
layout_class: rotated_spread
physical_pages: 23
logical_pages_estimate: 45
rotation: 270
page_size: A3
```

For this class, the toolkit should not assume that splitting by x-coordinate will reconstruct reading order. It should instead:

- identify whether each physical PDF page contains one or two logical pages
- detect vertical running titles and ignore them
- compare method quality across `pdftotext -layout`, `-raw`, `-bbox-layout`, and MarkItDown
- flag when line-level extraction is grouping words from separate columns into one line
- warn that a near-100 percent word coverage score can still hide bad reading order

This would have prevented the failed coordinate-based reconstruction pass that preserved coverage while damaging prose order.

## 3. Add a reusable one-off converter template

For difficult PDFs, bespoke scripts are still the right tool. The toolkit should make this path explicit and fast.

Add:

```bash
python scripts/new_converter.py \
  --pdf "path/to/source.pdf" \
  --party "Scottish Labour" \
  --year 2001 \
  --slug scottish-labour-manifesto
```

It should create a script with:

- canonical input and output paths
- title and contents placeholders
- `normalize_line()` and `make_markdown()` hooks
- extraction-method selection
- heading map
- bullet cleanup
- optional page/section post-processing
- built-in QA invocation
- final destination path printed at the end

The recent conversions repeatedly used the same script shape. A template would make custom work reproducible without encouraging copy-paste drift.

## 4. Add output path and naming convention helpers

The Manifestos project has stable folder conventions:

```text
Markdown versions/<party-slug>/<year>-<party-slug>.md
```

The toolkit should include a helper that can infer or validate:

- party slug
- year
- destination folder
- output filename
- whether the target folder exists
- whether a same-year file already exists

Example command:

```bash
python resolve_output.py \
  --pdf "Original documents/2001 General election/Scottish Labour 2001 manifesto.pdf" \
  --party "Scottish Labour"
```

Expected output:

```text
Markdown versions/scottish-labour-manifesto/2001-scottish-labour-manifesto.md
```

This would reduce manual path handling and make batch conversions less error-prone.

## 5. Add source/destination verification to the standard workflow

After every conversion, the useful final checks were:

- file exists at the destination
- source and copied destination hashes match
- QA is run on the destination file, not only the working copy
- final word coverage is reported

Add a small wrapper:

```bash
python finalize_manifesto.py working.md destination.md --pdf source.pdf
```

It should:

- create the destination folder if needed
- copy the file
- print file size
- print SHA-256 hashes for working and destination files
- run `qa_check.py` on the destination
- fail non-zero on QA errors

This turns the "did it actually land in the right folder?" step into a repeatable check.

## 6. Tune QA severity and false positives

The QA checker is valuable, but the recent batch showed cases where warnings were technically correct pattern matches but not actual transcription problems.

Examples:

- `in in-work poverty` was flagged as repeated `in`
- `ECtHR` was flagged because mixed case looked suspicious
- headings beginning with `The` are often legitimate manifesto section titles
- short paragraphs are often legitimate captions, sidebar headings, or list continuations

Recommended changes:

- add a project-level allowlist file, for example `qa_allowlist.yaml`
- support phrase-level allow rules, not only rule disabling
- allow expected short headings by manifest
- downgrade "heading starts with article" to info unless combined with other evidence
- keep mid-sentence bullet glyphs and repeated adjacent words as warnings because they caught real extraction failures
- add a `--strict` mode for final audit and a calmer default for ordinary conversion iteration

Useful allowlist shape:

```yaml
phrases:
  - in in-work poverty
  - ECtHR
heading_starts_allowed:
  - The
  - A
```

## 7. Add QA for vertical text and decorative letter fragments

Older designed PDFs can produce fragments from vertical running headers. In the Scottish Labour 2001 extraction these appeared as tiny paragraphs such as:

```text
P y
W b
A m
S m m
```

Add QA checks for:

- repeated single-letter or two-letter fragments
- paragraphs made only of spaced initials
- repeated decorative fragments across pages
- improbable single-character paragraphs
- strings produced by vertical running titles

The checker should suggest either stripping these via repeated-text detection or adding them to a per-PDF cleanup rule.

## 8. Make reading-order QA distinct from coverage QA

Word coverage can be excellent while reading order is poor. This happened during the 2001 Scottish Labour experiment: one intermediate file had about 100 percent coverage but interleaved left and right columns.

Add reading-order checks such as:

- repeated adjacent words at likely column joins
- sudden topic jumps within one paragraph
- paragraph lines with alternating left/right x-origin in the source
- bullet glyphs embedded inside prose
- heading text appearing mid-paragraph
- unusually high count of short orphan fragments
- high coverage but high artefact count

The QA summary should distinguish:

```text
Coverage: healthy
Reading order: suspect
Markdown structure: needs review
```

This would make it harder to accept a file just because the word count looks good.

## 9. Add method-specific cleanup pipelines

Different extractors leave different scars:

- `pdftotext -layout` preserves columns but often needs split/region handling
- `pdftotext -raw` can preserve reading order but fuse words
- MarkItDown can improve reading order but may preserve decorative fragments
- OCR can recover image PDFs but needs spelling and line-join cleanup

The toolkit should let a converter declare:

```yaml
extraction_method: markitdown
cleanup_pipeline:
  - strip_vertical_fragments
  - normalize_bullets
  - merge_bullet_continuations
  - promote_known_headings
  - remove_page_numbers
```

This is cleaner than embedding a long series of bespoke `replace()` calls in each script.

## 10. Improve bullet continuation handling

Several QA warnings came from list items split across lines:

```markdown
* by offering a minimum wage of
£4.20 and an Employment Tax Credit
```

The converter should merge continuation lines when a bullet ends with:

- a preposition or article, such as `of`, `in`, `the`, `and`, `with`
- a dangling currency phrase
- a dangling hyphenated phrase
- a line that is followed by lowercase text or a currency amount

This should run before QA so warnings focus on genuinely broken lists.

## 11. Store batch conversion metadata

A small conversion log would help future maintenance. Each completed Markdown file could have a sidecar JSON record:

```json
{
  "source_pdf": ".../Scottish Labour 2001 manifesto.pdf",
  "output_md": ".../2001-scottish-labour-manifesto.md",
  "extractor": "markitdown",
  "coverage": 99.6,
  "qa_errors": 0,
  "qa_warnings": 0,
  "qa_info": 94,
  "notes": "Rotated A3 spread PDF; MarkItDown gave cleaner reading order than pdftotext."
}
```

This would make it easier to audit which files were OCR-derived, which used embedded text, and which had known residual quirks.

## 12. Add "known good snippets" spot checks

For long manifestos, full manual review is slow. Add a spot-check helper that extracts and compares a handful of stable snippets:

- first body paragraph
- first heading after contents
- one middle-section paragraph
- a bullet list
- last substantive paragraph

The tool could print source extraction beside Markdown output for quick inspection. This would catch many reading-order problems earlier than looking only at aggregate QA.

## 13. Keep MarkItDown optional, but documented

MarkItDown was useful for at least one difficult text-layer PDF, but it should not become a hard dependency unless the toolkit is ready to vendor it.

Recommended approach:

- document it as an optional extractor
- detect availability at runtime
- include it in `extract_compare.py` when installed
- record when it was used
- keep `pdftotext` and `pdfplumber` as the default portable path

## 14. Prioritised implementation list

Highest value:

1. `extract_compare.py` strategy runner
2. reusable custom converter template
3. destination/path finalizer with QA-on-destination
4. QA reading-order score separate from coverage
5. vertical fragment detection

Medium value:

1. QA allowlist support
2. method-specific cleanup pipelines
3. bullet continuation merger
4. rotated-spread profiler classification

Lower value, but useful for auditability:

1. conversion metadata sidecars
2. known-good snippet spot checks
3. optional MarkItDown documentation

## Suggested next step

Implement `extract_compare.py` first. It would have shortened the hardest recent conversion immediately, and it gives the rest of the toolkit better evidence before choosing whether to use the generic extractor, a page manifest, OCR, MarkItDown, or a bespoke converter.
