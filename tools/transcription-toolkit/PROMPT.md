# Manifesto PDF → Markdown Transcription Prompt

Use this prompt when asking an AI agent to transcribe a political party manifesto from PDF to Markdown. Paste the full prompt below as the task instruction, replacing the `[PLACEHOLDERS]` as appropriate.

---

## The Prompt

You are transcribing the **[PARTY] [YEAR] manifesto** from PDF to Markdown. Your task is a **verbatim transcription** — every word in the PDF must appear in the Markdown output, in the correct order, with no omissions, summarising, or paraphrasing.

### Classify the PDF before you start

Before transcribing, open the PDF and spend a few minutes identifying which extraction mode applies. Different PDFs need different strategies — using the wrong one from the start wastes significant time.

**Mode 1 — Clean text-layer PDF**
The PDF has a readable text layer and a straightforward reading order (single column, or a consistent two-column layout). Use `extract_manifesto.py` normally. Even then, manually verify:
- the contents page
- cover and front matter pages
- chapter opener pages
- bullet lists near the left margin
- pages with pull-quotes or sidebars

**Mode 2 — Mixed-layout PDF**
The PDF has a usable text layer overall, but specific pages break extraction because of two- or three-column layouts, decorative standfirsts, sidebars or pull-quotes, subsection headings that splice into adjacent text, or clipped bullet starts. For these, do not trust the raw extractor uniformly across the whole document. Instead:
- inspect problematic pages individually
- reconstruct reading order visually, processing left-to-right by column
- exclude decorative elements that duplicate body text
- check whether bullets have lost their opening words
- rebuild contents pages manually if the PDF interleaves page numbers and headings badly

**Mode 3 — OCR / manual-rebuild PDF**
The text layer is poor or corrupted. Signs include widespread garbled words, headings split into nonsense fragments, missing whole lines despite reasonable word-count coverage, or paragraph order that remains wrong after column tuning. Switch to OCR or manual reconstruction early rather than repeatedly patching bad extraction. Page images are the source of truth.

**Practical rule:** if a page looks visually more complex than the rest of the document, trust the page image over the text layer.

### Core standard

- **Completeness overrides everything else.** Missing content is worse than imperfect formatting.
- Reproduce every word exactly as printed, including punctuation and capitalisation.
- Aim for ≥ 95% word coverage. Verify with: `pdftotext [file].pdf - | wc -w` vs `wc -w [output].md`. The result can legitimately sit either side of 100%: a slight *overcount* (~1–2%) is expected from Markdown syntax tokens (`##`, `---`, `*`); a slight *undercount* (~1–3%) is also normal when running headers and footers are correctly stripped, since `pdftotext` counts those words too.

### Heading hierarchy

- `# ` — manifesto title (once, at the top); also used for chapter titles if the PDF has a distinct chapter-level above sections
- `## ` — major section headings (large, prominent headings — typically the largest body font)
- `### ` — subsection headings within sections
- `#### ` — sub-subsection headings, if a fourth level exists in the PDF

Many manifestos need only three levels (`#`, `##`, `###`). Some — particularly those with a chapter → section → subsection hierarchy — need four. Match the number of levels to the PDF's actual typographic hierarchy, using font size and weight as the guide.

Use `---` on its own line to separate major page-level divisions where appropriate.

### Bullet points

Bullet items may appear in two forms depending on the PDF's typography:

**With a bold lead phrase** (common in Alliance, Conservative, and some other parties):
```
* **Bold lead sentence here.** Remainder of the bullet text continues here in regular weight.
```

**Plain bullets** (common in many single-font manifestos — the entire item is the same weight):
```
* Bullet text here.
```

Check the PDF to determine which pattern applies. Do not add bold markers where the PDF does not use them.

**Bullet lists are high-risk for silent truncation.** If a bullet appears to start mid-sentence, check the page image — the opening phrase may have been dropped because of a symbol font, a tight left margin, or column clipping. Preserve bold lead phrases only when the PDF genuinely uses them; convert decorative bullet glyphs to standard Markdown `* ` bullets.

The bullet character (`•`) may appear in two ways: as a Unicode `•` (U+2022) directly in a body font such as Myriad-CnBold, or encoded as the character `n` in the ZapfDingbats font. Both must be treated as bullet markers and converted to `* ` in the output. See the agent usage notes below for the force-split rule that both types require.

### Inline styling

Apply inline Markdown styling to match the PDF typography:

- `**bold**` — for bold text (e.g. bold lead sentences in bullets, bold subsection intro phrases)
- `_italic_` — for italic text (e.g. document titles, emphasis words, slogans printed in italics)
- Do **not** use styling for ordinary body text; only apply it where the PDF clearly uses a different typeface weight or slant.

### Two-column PDFs

Some manifestos are typeset in two columns. If the PDF has a two-column layout:

- Process the **left column top-to-bottom first**, then the **right column top-to-bottom** for each page.
- Do **not** interleave lines from the two columns (this is the default behaviour of `pdftotext` and must be avoided).
- Use the `extract_manifesto.py` script in this toolkit, which handles column splitting automatically.

### Paragraphs

- Separate paragraphs with a **single blank line**.
- Do not preserve the PDF's line breaks within a paragraph — flowing text should be joined into a single paragraph.
- A new paragraph begins when there is a visible gap between text blocks in the PDF (typically ≥ 18pt vertical gap between lines).

### What to exclude

Exclude the following if they appear on every page as repeated elements:

- **Running headers** — a section or chapter title repeated at the top of each page in the section. These typically sit in the top ~30pt of the page. Identify them by checking whether the text also appears as a genuine heading in the body of the page; if it does, the top-of-page version is the running header and should be dropped.
- **Running footers** — page numbers, party name, slogan, or website URL repeated at the bottom of each page, typically in the bottom ~50pt. These are often in a lighter or smaller font than body text. They are counted by `pdftotext` but should not appear in the Markdown, which accounts for a natural ~1–3% undercount in the word-coverage check.
- **Decorative pull-quotes** that repeat content already appearing in the body text.

Include page numbers **only** if they appear as part of a table of contents or structured list.

**Important:** Running headers and footers occupy specific y-coordinate zones at the top and bottom of each page. Do not strip content based solely on its y-position — check the font and content first, since continuation pages often have real content starting near the top margin.

### Formatting reference example

The following excerpt illustrates the expected formatting style:

```markdown
## Devolution and Power Sharing

Alliance has consistently argued for a genuine partnership government that is inclusive and
accountable. We believe that stable, inclusive government is only achievable through real
power-sharing, not the exclusion of any significant section of the community.

* **Alliance proposes that the Executive should be formed by negotiation among parties**
  endorsed by the Assembly, _voluntary_ power-sharing rather than mandatory coalition.

* **Alliance will support the creation of a Civic Forum** to give a voice to business,
  voluntary bodies and community groups on issues of public concern.

### Agenda for Democracy

Alliance's _Agenda for Democracy_ sets out a comprehensive programme of political and
institutional reform for Northern Ireland.
```

Key things this shows:
- Bullet lead sentences in bold (`**Alliance proposes...**`)
- Italic for document/programme titles (`_Agenda for Democracy_`, `_voluntary_`)
- Section heading in `###`
- Paragraphs joined to a single line, blank line between each

### Quality check

After completing the transcription:

1. Run `pdftotext [file].pdf - | wc -w` to count words in the PDF.
2. Run `wc -w [output].md` to count words in the Markdown.
3. Compute coverage: `markdown_words / pdf_words × 100`.
4. If coverage is below 95%, review which sections are missing and complete them.
5. **Interpreting the result:**
   - **95–103%**: Healthy range. Content is present; small delta is expected from Markdown syntax tokens and stripped footers.
   - **103–105%**: Can still be fine if Markdown markers, manually restored clipped text, or rebuilt headings increase the count slightly beyond 103%. Check for duplicated sections before accepting.
   - **97–100%**: Ideal. Small undercount is stripped footers; small overcount is Markdown syntax tokens.
   - **< 95%**: Something is likely missing — identify which pages extracted poorly and fill in the gaps.
   - **> 105%**: Check for duplicated sections, repeated headings, or pull-quote text that was included twice.
6. **Do not rely on total word-count coverage alone.** A file can sit near 100% and still contain truncated headings, duplicated pull-quotes, clipped bullet openings, or wrong column order. Also verify:
   - every major heading against the PDF
   - contents page headings and order
   - first and last bullets on each list
   - pages with unusually low extraction quality
   - pages with sidebars, pull-quotes, or large decorative text

7. **Verify every heading is verbatim.** Word-count coverage does not catch silent heading truncation. Run:
   ```bash
   python check_headings.py [file].pdf [output].md
   ```
   Review every item flagged as `TRUNCATED`, `ALTERED`, or `NOT FOUND` and correct the Markdown before finishing. If `check_headings.py` is not available, extract all PDF headings manually (look for the largest font sizes in each section) and compare them one by one against the Markdown. **Do not trust an existing partial file's headings without this check** — a heading that looks complete in isolation may still be missing words from the original.

---

## Usage notes for the agent

### Step 0: Check page orientation and dimensions first

Before anything else, inspect the first body page for orientation and actual dimensions:

```python
with pdfplumber.open("manifesto.pdf") as pdf:
    p = pdf.pages[1]
    print(f"width={p.width:.0f}  height={p.height:.0f}")
```

Portrait A4 is typically 595×842pt; landscape A4 is 842×595pt (may report ~884×637px in practice). This matters because:
- Footer cutoff `Y_FOOTER` must be derived from `page.height`, not a fixed constant
- Column split x-coordinates are relative to page width — a value that works on portrait breaks on landscape

### Step 0c: Use `extract_text(layout=True)` for known-problematic pages

If a specific page is known to be garbled in the extraction output — but the surrounding pages are fine — do not retune the global pipeline. Instead, run pdfplumber's layout-preserving extraction on that page alone:

```python
with pdfplumber.open("manifesto.pdf") as pdf:
    print(pdf.pages[16].extract_text(layout=True))   # 0-indexed page number
```

`layout=True` renders approximate x-positions as spaces, giving an ASCII-art view of the page. On complex two-column comparison or table pages (e.g. politician-quote vs. policy-result layouts), this makes the column structure immediately readable and allows accurate manual reconstruction without rewriting the extraction script. Use the PDF page image alongside the layout output for confirmation of any ambiguous fragments.

### Step 0b: Validate column boundaries before writing formatting logic

For any multi-column layout, run an x0 histogram on a representative body page **before** writing paragraph assembly code:

```python
with pdfplumber.open("manifesto.pdf") as pdf:
    page = pdf.pages[5]
    from collections import Counter
    x0_counts = Counter(round(c['x0'] / 5) * 5 for c in page.chars if c['text'].strip())
    for x, n in sorted(x0_counts.items()):
        if n > 2:
            print(f"x0≈{x:4d}  count={n}")
```

Look for contiguous zero-count ranges of ≥10px — these are column gaps. The midpoint of each gap is your split coordinate. A document with varying column counts (2-col, 3-col on different pages) will show different gap positions on different pages; in that case use **dynamic per-page gap detection** rather than a fixed split. See the README for the `find_column_splits()` pattern.

Confirm that the column start positions and inter-column gaps match your thresholds on several representative pages. A mis-set column boundary is the single most common cause of garbled output.

**The global histogram can be misleading when the PDF has mixed layout types.** If some pages have a narrow decorative left column (e.g. a standfirst or pull-quote column) and other pages have a wider left column, the two populations mix in a global histogram and the trough will appear in the wrong place. The fix is to sample pages of each type individually and compare — see the next section.

### Mixed-layout pages: per-page column detection

Some PDFs are typeset with two distinct page layouts that use *different gutter positions*:

- **Standfirst pages** — a narrow left column (x ≈ 34–140pt) containing a bold decorative quote or pull-out, and a wide right body column that starts at x ≈ 150–167pt. Gutter is around x=148.
- **Normal body pages** — a wide left body column (x ≈ 34–190pt, often justified to the full left column width), and a right column starting at x ≈ 210pt. Gutter is around x=202.

Using a single global `col_split` derived from a histogram across all pages will garble one layout type: if the split is set too wide (e.g. x=202) it lumps the standfirst decorative text together with the first half of the right body column, interleaving them. If set too narrow (e.g. x=148) it puts justified left-column text that reaches x=195 into the right column.

**Detection approach:** For each page, count the number of y-lines where the minimum x of text falls in a mid-page band (typically 100–200pt on A4). On standfirst pages the right body column starts at x≈150, so many lines score; on normal pages the right column starts at x≥210, so few do.

```python
from collections import defaultdict

def bucket(top, tol=4):
    return round(top / tol) * tol

def detect_page_col_split(page, header_cut=28, footer_cut=565,
                          mid_lo=100, mid_hi=200,
                          standfirst_threshold=4,
                          standfirst_split=148, normal_split=202):
    """
    Detect the correct column split for this individual page.
    Counts y-lines whose minimum text x falls in (mid_lo, mid_hi).
    If ≥ standfirst_threshold such lines exist, use standfirst_split;
    otherwise use normal_split.
    Calibrate mid_lo/mid_hi and the thresholds on your specific PDF.
    """
    chars_by_y = defaultdict(list)
    for c in page.chars:
        if c['text'].strip() and header_cut < c['top'] < footer_cut:
            chars_by_y[bucket(c['top'])].append(c)

    count = 0
    for chars in chars_by_y.values():
        min_x = min(c['x0'] for c in chars if c['text'].strip())
        if mid_lo < min_x < mid_hi:
            count += 1

    return standfirst_split if count >= standfirst_threshold else normal_split
```

**Calibration steps:**
1. Run the x0 histogram (Step 0b) on a standfirst page and a normal body page separately, and read off the gutter position for each.
2. Run `detect_page_col_split()` on 10–15 pages with default parameters and print the result alongside a visual description of each page to confirm the classification is correct.
3. Adjust `mid_lo`, `mid_hi`, and `standfirst_threshold` until all pages are classified correctly.

The `detect_page_col_split()` function is available in `extract_manifesto.py` and can be passed as a `col_split_fn` to `extract_page()` to override the global split on a per-page basis.

### Narrow standfirst vs. full-width left column: the x1 and body-start checks

The simple standfirst detection above works when the narrow strip is clearly narrower than the left body column. But some pages have a standfirst that occupies the **full width of the left column** — the bold introductory text runs all the way to the right edge of the left column (x≈180), with a gap, then body text starts in the right column (x≈210). This looks like a standfirst from the left margin but uses the regular column split, not a narrow one.

Two checks together reliably distinguish the two cases:

**Check 1 — x1 of SemiBold chars must stay within the narrow strip.** A true narrow standfirst has SemiBold text that both *starts* and *ends* within the strip. Look at chars whose `x0 < sb_strip` and verify `max(c['x1']) < sb_edge` (sb_edge ≈ sb_strip + 20). If SemiBold chars at x0 < 140 but x1 up to 143 — they just barely stay within the strip, so it's narrow. But on a full-width standfirst page the SemiBold chars continue across the strip boundary (x1 up to 178+), so an additional word starting at x0=160 would not even be caught by the x0 < sb_strip filter. This is why the x1 check alone is not enough.

**Check 2 — where does the Light (non-SemiBold) body text start on the standfirst rows?** If the right-column body text begins right after the standfirst strip (x≈148–153), sf_split correctly separates them. If the body text starts much further right (x≈210), the standfirst fills the full left column and the regular column split should be used instead. A gap of more than 30px past sf_split is the threshold:

```python
def standfirst_info(page, body_chars, sf_rows, sf_split):
    """After detecting sf_rows, verify they represent a TRUE narrow strip."""
    # 1. Reject if any SemiBold chars on sf_rows extend past sf_split
    #    (would mean the standfirst sentence continues into the right zone)
    # 2. Reject if Light body text on sf_rows starts far right of sf_split
    #    (would mean standfirst fills the full left column, not a narrow strip)
    light_on_sf = [c for c in body_chars
                   if 'SemiBold' not in c['fontname']
                   and bucket(c['top']) in sf_rows]
    if light_on_sf:
        body_start_x = min(c['x0'] for c in light_on_sf)
        if body_start_x > sf_split + 30:   # large gap → full-width standfirst
            return False   # fall back to regular col_split
    return True
```

When the sanity check fails, process those rows with the regular column split: standfirst text (left of regular_split) becomes a bold paragraph, and body text (right of regular_split) becomes a regular paragraph — exactly the right output.

**Dual col_split per y-row:** some pages have a standfirst at the top rows and a regular two-column layout below. Process them as two separate sets: standfirst rows use sf_split, non-standfirst rows use regular_split.

### Bold/SemiBold paragraph joining: use a wider effective para_gap

SemiBold pull-quote text typically has wider inter-line spacing than body text. On A5 layouts, SemiBold inter-line gaps are often ~16pt — above a PARA_GAP of 14pt — causing each standfirst line to split into a separate bold paragraph. Fix by using a larger effective gap for SemiBold lines:

```python
effective_gap = 20 if stream == 'semibold' else para_gap
if gap >= effective_gap or stream != buf_stream or is_bullet:
    flush()
```

The exact value depends on the font leading. Check by printing the y-gaps between consecutive SemiBold words on a standfirst page and set effective_gap ≈ max(line gap) + 2pt.

### Post-processing: merge_unfinished_paras (terminal-punctuation merge)

`merge_lowercase_orphans` catches right-column fragments that start with a lowercase letter. But some fragment splits begin with an uppercase word (a proper noun or mid-sentence first-cap). Use terminal punctuation as the guard instead: if a paragraph's last character is not sentence-ending punctuation, it was probably cut mid-sentence and the next paragraph is a continuation.

```python
TERMINAL_PUNCT = set('.!?:;"\'»')

def merge_unfinished_paras(text):
    """Merge paragraphs where the previous ends without terminal punctuation.
    Guards:
      - Never merge after a heading (# / ## / ###) or a bold block (**...**)
      - Never merge into a heading, bullet (* ), or another bold block
    """
    paras = text.split('\n\n')
    result = []
    for para in paras:
        stripped = para.strip()
        if result and stripped:
            prev = result[-1].rstrip()
            prev_is_structural = (any(prev.startswith(p) for p in ('# ', '## ', '### '))
                                  or prev.endswith('**'))   # don't merge after a bold block
            curr_is_structural = any(stripped.startswith(p) for p in ('# ', '## ', '### ', '* '))
            if (not prev_is_structural
                    and not curr_is_structural
                    and prev and prev[-1] not in TERMINAL_PUNCT):
                result[-1] = prev + ' ' + stripped
                continue
        result.append(para)
    return '\n\n'.join(result)
```

Run this **after** `merge_lowercase_orphans`, then run `merge_lowercase_orphans` again — the two are complementary and together catch almost all false splits. The `prev.endswith('**')` guard is essential: without it, a standalone bold paragraph (like a standfirst) would absorb the body text that follows it.

**The gutter need not be near the centre of the page.** The current `detect_column_split()` only searches within ±80pt of the page centre. If your PDF has an asymmetric column layout — a narrow left column with the gutter well to the left of centre — the global auto-detection will fail entirely. In that case set `--col-split` manually or use per-page detection.

### Heading fragments spanning the column gutter

When a full-width section heading (e.g. `### NHS AND SOCIAL CARE`) is typeset at a larger font size and its character positions span the column gutter, pdfplumber assigns the left-side characters to the left column and the right-side characters to the right column. This produces two artefact headings in the output:

- A **left fragment** at the end of the left column (e.g. `### NHS AND SOCIAL`)
- A **right orphan** at the start of the right column (e.g. `### CARE`)

The correct fix is a two-step post-processing pass:

1. **Upgrade left fragments** — replace the partial left-fragment heading with the full heading text using a lookup table of known headings.
2. **Remove right orphans** — delete the orphan fragment heading that appears shortly after.

```python
# Step 1: upgrade partial left-column headings to the full heading
HEADING_FIXES = {
    '### NHS AND SOCIAL\n\n': '### NHS and Social Care\n\n',
    '### EDUCATION AND\n\n':  '### Education and Skills\n\n',
    # add one entry per split heading found in your PDF
}
for fragment, full in HEADING_FIXES.items():
    md_text = md_text.replace(fragment, full)

# Step 2: remove orphan right-column fragment headings
ORPHAN_FRAGMENTS = ['### CARE', '### SKILLS', '### SECURITY']
for frag in ORPHAN_FRAGMENTS:
    md_text = md_text.replace(f'\n\n{frag}\n\n', '\n\n')
```

**Finding which headings are split:** run the extraction, then grep for `^### ` in the output and compare against the headings in the original PDF. Any heading that appears truncated in the output, followed later by a short orphan heading matching its missing words, is a split heading.

**When the column split changes per page**, the split point within a heading changes too — so the fragments will be different for standfirst vs. normal pages. You may need separate fix entries for each layout type. The right orphan for the same heading may be `### CARE` on one page type and `### AND SOCIAL CARE` on another.

### Bullet handling: two distinct encodings, same force-split rule

Manifesto PDFs use two different bullet encodings that must both be handled:

1. **ZapfDingbats `n`** — the glyph `n` in the ZapfDingbats font renders as `•`. Replace it with a `§BULLET§` placeholder during character extraction, then convert to `* ` at output time.
2. **Unicode `•` (U+2022)** — a literal bullet character appearing directly in body fonts (e.g. Myriad-CnBold). Keep the character during extraction, then convert to `* ` at output time.

Both types require the same **force-split rule**: if an incoming line starts with a bullet marker (`§BULLET§` or `•`) and the y-gap to the current paragraph is below PARA_GAP, still force a new paragraph. Without this rule, consecutive bullet items whose y-gap is tight (common in two-column layouts) will be merged into one long paragraph.

Also add a catch-all in the output formatter: if the assembled paragraph text starts with `•` regardless of its dominant font, render it as `* body text`, not as plain body text. A bullet paragraph's dominant font is often the body continuation font (e.g. Myriad-Condensed), not the bold lead font, so font-conditional checks alone are not sufficient.

### Dominant font is unreliable for mixed-style paragraphs

When a paragraph starts with a bold lead (e.g. Myriad-CnBold for the bullet marker and first phrase) and continues in a regular body font (e.g. Myriad-Condensed), the dominant font across the whole paragraph will be the body font. Do not derive bullet or heading status solely from the dominant font of the assembled paragraph. Instead:

- Detect bullet/heading type from the **start** of the paragraph text (first word or first character).
- Use font inspection on the **first line** of the paragraph, not the whole paragraph.

### Mixed y-rows: heading chars and body chars at the same y-coordinate

In some PDFs, a sub-heading and adjacent body text sit on exactly the same typographic baseline (same `top` value). If you classify each y-row as a single type, you will either lose the heading or lose the body text. Instead, **partition each y-row by character type**:

```python
h_chars = [c for c in row if is_heading_char(c)]   # e.g. Bold sz 10.5–13.5
b_chars = [c for c in row if not is_heading_char(c) and ...]
```

Then assemble heading text and body text separately, emitting them in x-position order (whichever starts further left comes first). This is more reliable than any row-level font classification.

### is_heading_char: set both a lower and upper size bound

A check like `"Bold" in font and size >= 11` will also catch pull-quote text, attribution lines, or chapter titles in the same bold family at larger sizes (sz 16–52). Always set an **upper bound** matching the sub-heading size range you measured during diagnosis:

```python
def is_heading_char(c):
    return "Bold" in base_font(c) and 10.5 <= c["size"] <= 13.5
```

Also exclude "Medium" weight fonts — `DINOT-Medium` and similar are typically used for decorative pull-quotes, not body-level sub-headings.

### Distinguishing headings from bold callout sentences

At sub-heading size, some bold text is a genuine section heading ("CORPORATION TAX DODGING") and some is a bold sentence ("Both parties have failed on this issue."). Use an all-caps proportion check to tell them apart, and emit accordingly:

- **≥ 60% of words all-caps or known abbreviations** → `### HEADING`
- **Fewer than 60%** → `**Bold callout sentence.**`

Known abbreviations (NHS, EU, GDP, UK, UKIP, VAT, etc.) should count as "caps" in this check so that headings like "WHAT THE NHS NEEDS" are not misclassified.

### Multi-line headings: merge with a guard

Some headings wrap across two y-rows 12–20px apart. Merge adjacent heading rows — but **only if the new row also passes the heading test**. Without this guard, bold body sentences that happen to follow a heading within 20px will be absorbed into the heading line:

```python
if (prev_was_heading and abs(y - prev_head_y) <= 20
        and output[-1].startswith("### ")
        and looks_like_subheading(new_text)):    # ← the guard
    output[-1] += " " + new_text
else:
    emit_heading_or_bold(new_text)
```

### Word gap reconstruction: use size-relative threshold

When reconstructing words from `page.chars` by detecting inter-character gaps, the correct threshold is:

```python
threshold = max(1.5, prev_char_size * 0.15)
```

At size 9pt (common body text), letter gaps are ~0–1px and word gaps are ~2.3px. A threshold of 1.8 (= 9 × 0.15) catches them correctly. The common heuristic `size * 0.45` gives a threshold of ~4px at sz=9, which is **too large** and will merge consecutive words into a single token.

### Step 0: Diagnose before extracting

Before running `extract_manifesto.py` or transcribing manually, spend a few lines of Python to understand the PDF's structure:

```python
import pdfplumber
from collections import defaultdict

def bucket(top, tol=4):
    return round(top / tol) * tol

with pdfplumber.open("manifesto.pdf") as pdf:
    page = pdf.pages[5]  # a typical body page
    chars_by_y = defaultdict(list)
    for c in page.chars:
        chars_by_y[bucket(c['top'])].append(c)
    for y in sorted(chars_by_y.keys()):
        chars = sorted(chars_by_y[y], key=lambda c: c['x0'])
        text  = ''.join(c['text'] for c in chars).strip()
        fonts = set(c['fontname'].split('+')[-1] for c in chars if c['text'].strip())
        if text:
            print(f"y={y:.0f} {fonts} {text[:60]!r}")
```

This tells you: what font names are used (and which correspond to headings vs. body), where running headers and footers sit (their y-coordinates), and whether the layout is single- or two-column. Use this to set `--header-cut`, `--footer-cut`, and `--col-split` correctly before running the full extraction.

### Running the script

- Before transcribing manually, try the `extract_manifesto.py` script in this folder — it handles two-column layouts, font detection, and paragraph reconstruction automatically.
- If the script produces a good first draft (≥ 90% coverage), review and correct the output rather than transcribing from scratch.
- If the generic script gives poor results for this PDF (wrong header cut, missed bullets, wrong column split), write a short targeted script using the diagnostic information above. The per-manifesto scripts in `../Python scripts/` show the pattern.
- If the PDF uses a complex layout (sidebars, tables, rotated text, mixed columns), the script output will need more editing. In that case, use the script output as a scaffold and fill in missing sections manually.
- Always read the PDF directly (via `pdfplumber`) rather than relying on copy-paste from a PDF viewer, which loses column order and introduces line-break artefacts.

### Section intro / chapter title pages

Many manifesto PDFs have dedicated chapter-opener pages with large decorative text, a pull quote, and an attribution. Detect these by looking for a very large character on the page. The threshold depends on the PDF's typographic scale — some PDFs use 54pt titles, others use as little as 38pt for the same semantic role. Start with ≥36pt as a safe lower bound and raise it if regular sub-headings (typically ≤24pt) trigger false positives:

```python
has_chapter_title = any(
    c["size"] >= 36 and c["text"].strip()   # raises to ≥40+ if sub-headings < 36pt
    for c in page.chars
)
```

**Calibration:** scan all pages and print the max font size per page alongside a one-line text sample. Any page with max_sz significantly above the body sub-heading size (typically 24pt) is a chapter opener. In practice, if your sub-headings are 24pt and chapter titles are 54pt, a threshold of 36 gives comfortable headroom. If a PDF has titles at only 38pt and sub-headings at 24pt, a threshold of 30 would still be safe.

Extract these pages separately: the large text becomes a `## SECTION` heading, any pull-quote becomes a bold paragraph, and the attribution (typically a medium-weight font at moderate size) becomes `**Name, Title**`. Do **not** pass these pages through your standard body-text pipeline.

### Deduplicating headings from two-page spreads

Chapter opener pages that span two consecutive PDF pages will produce the same `##` heading twice. Clean this up in post-processing:

```python
md = re.sub(r"(^#{1,3} .+)(\n\n\1)+", r"\1", md, flags=re.M)
```

### Fixing PDF glyph artefacts

Some PDFs contain characters with corrupted glyph representations in the font's encoding (e.g. a word appearing as `DeFeNCe` instead of `DEFENCE`). There is no general automated fix — add specific substitutions in a `clean_markdown()` post-processing step for any artefacts discovered during review.

### Heading text reconstruction: use extract_words(), not char concatenation

When reconstructing heading text from `page.chars`, naive concatenation of characters loses all word spacing — `"INTERNATIONAL SOLIDARITY"` becomes `"INTERNATIONALTSOLIDARITY"`. Two-step approach that works reliably:

1. **Identify heading y-rows** from `page.chars` using font name and size (chars have reliable size metadata).
2. **Reconstruct text** using `page.extract_words()` on those y-rows — words already have correct spacing.

```python
# Step 1: find y-rows that contain heading chars
heading_ys = set()
for c in page.chars:
    if 'HeadingFont' in base_font(c['fontname']) and c['size'] >= 20:
        heading_ys.add(bucket(c['top']))

# Step 2: get properly-spaced words on those rows
words = page.extract_words(keep_blank_chars=False)
words_by_y = defaultdict(list)
for w in words:
    if bucket(w['top']) in heading_ys:
        words_by_y[bucket(w['top'])].append(w)

for y in sorted(words_by_y):
    text = ' '.join(w['text'] for w in sorted(words_by_y[y], key=lambda w: w['x0']))
    print(f'### {text}')
```

This avoids the missing-space problem entirely because `extract_words()` handles inter-character gap detection using the font metrics.

### Prefer `page.extract_words()` over manual char reconstruction

For most PDFs, `page.extract_words()` is simpler and more reliable than reconstructing words manually from `page.chars`. Use:

```python
words = page.extract_words(keep_blank_chars=False, extra_attrs=['fontname', 'size'])
```

Then also build a `char_lookup` dict from `page.chars` for per-character font resolution:

```python
char_lookup = defaultdict(list)
for c in page.chars:
    char_lookup[bucket(c['top'])].append(c)
```

Use `char_lookup` to resolve the dominant font+size for each word during classification. Fall back to manual char reconstruction (with the `max(1.5, prev_char_size * 0.15)` threshold) only if `extract_words()` produces merged words on a specific page.

### When to use semantic classification vs. inline style markers

The generic `extract_manifesto.py` applies inline `**bold**`/`_italic_` markers word by word. This works well for documents where bold and italic are used freely for emphasis. For PDFs with a **strict typographic system** — where each font face has a fixed semantic role (headings, body, pull-quotes, attributions) — it is more effective to classify each word into a semantic type and render whole paragraphs consistently. See the UKIP 2017 section in README.md for the pattern. Signs you need semantic classification:

- The PDF uses distinct, named font families (Raleway, Aileron, DIN, etc.) for specific purposes rather than just bold/italic variants of one family
- Heading detection is unreliable because heading fonts also appear at body size in pull-quotes or attributions
- Column detection fails because certain font classes produce full-width lines that fill the column gap

### Two-column pages with full-width elements: three-pass extraction

Some two-column pages also contain full-width elements (chapter headings, intro paragraphs) that span both columns. Splitting naively at the column boundary will break headings across two `##` blocks and fragment intro paragraphs across columns. Use a three-pass approach:

1. **Identify full-width rows** — find y-positions where chapter or intro content crosses the column split (see `identify_full_width_rows()` in README.md)
2. **Preamble pass** — extract full-width rows only, using a wider `para_gap` suited to that font's inter-line spacing
3. **Column passes** — extract left and right columns from the remaining rows, using the normal body `para_gap`

```python
fw_ys    = identify_full_width_rows(content_words, col_split, char_lookup)
preamble = words_to_paragraphs(content_words, char_lookup, allowed_ys=fw_ys,  para_gap=25)
left     = words_to_paragraphs(content_words, char_lookup, x_max=col_split,   excluded_ys=fw_ys)
right    = words_to_paragraphs(content_words, char_lookup, x_min=col_split,   excluded_ys=fw_ys)
```

**Excluding full-width elements from column detection:** full-width content (large headings, wide intro paragraphs) fills the column gap in the x0 histogram, preventing detection. Filter to body-level words only when computing the gap — exclude any font class that produces full-width lines.

### Tune `para_gap` per content zone, not per document

Different font classes in the same PDF can have very different inter-line spacing. Intro paragraphs in a large, light font (e.g. Raleway-Light sz≈12) may have within-paragraph gaps of 16–20pt — well above the body-text `para_gap=14` — causing them to fragment into individual lines. Before finalising `para_gap`, inspect the actual line gaps for each content type on a representative page:

```python
with pdfplumber.open("manifesto.pdf") as pdf:
    page = pdf.pages[5]
    words = page.extract_words(keep_blank_chars=False, extra_attrs=['fontname', 'size'])
    tops = sorted(set(round(w['top'] / 4) * 4 for w in words if 'Raleway-Light' in w.get('fontname', '')))
    for a, b in zip(tops, tops[1:]):
        print(f"gap: {b - a:.1f}pt")
```

Use a narrower `para_gap` for body columns (typically 14–18pt) and a wider one for intro/preamble zones (typically 22–28pt). Pass different values to each extraction call.

### Don't classify small text as "footer"

Running headers and footers are already excluded by y-coordinate cutoffs (`Y_HEADER` / `Y_FOOTER`). Do **not** add a separate font-size-based "footer" classification (e.g. `if sz <= 9.5 and 'Raleway' in fn: return 'footer'`). Small-body-font content such as a Contents page often uses the same font family as headings but at a small size (sz≈9), and an explicit font+size footer rule will strip it. Instead, add a small-font fallback to your body classification:

```python
if sz <= 11: return 'body'   # catches any small text in the y-content zone, including Contents pages
return 'other'
```

### Post-processing: merge attribution + role lines

Speaker attributions are often printed on two consecutive lines: the name (larger, bolder) followed by a short role description (same or lighter font). These should be merged in post-processing rather than left as two separate paragraphs. A short-word-count guard (`<= 6 words`) prevents accidentally merging a following body sentence:

```python
if p['type'] == 'attribution' and len(next_para['text'].split()) <= 6:
    merged_text = p['text'] + ', ' + next_para['text']
    # emit as a single attribution paragraph: **Name, Role**
```

### Font family at multiple sizes: measure first, threshold second

Do not assume that a font family name alone identifies a semantic role. A single family (e.g. Formata, DIN, Raleway) can appear at three or four distinct size levels serving completely different purposes — category labels, decorative text, sub-headings, and major section headings. Writing `if 'Formata' in fn: return 'heading'` will misclassify decorative or label text that happens to use the same family.

Before writing any classification rule, run a font size survey on a representative body page:

```python
from collections import Counter
with pdfplumber.open("manifesto.pdf") as pdf:
    page = pdf.pages[5]
    words = page.extract_words(keep_blank_chars=False, extra_attrs=['fontname', 'size'])
    for w in words:
        if 'Formata' in w.get('fontname', ''):   # replace with the family under investigation
            print(f"sz={w['size']:.1f}  x0={w['x0']:.0f}  y={w['top']:.0f}  {w['text']!r}")
```

Then set a minimum size threshold matched to the smallest genuine heading in that family:

```python
if 'Formata' in fn and word.get('size', 0) >= 18:
    return 'heading'
# sizes below 18 fall through to 'body'
```

### Decorative mid-page elements: identify and exclude by font name

Y-coordinate cutoffs (`Y_HEADER` / `Y_FOOTER`) only catch elements in the top or bottom margins. Some PDFs include a recurring decorative element — a URL strip, page number pair, or design flourish — in the middle of the page, within the normal content zone. These cannot be stripped by position alone.

To detect them: look for any font that appears on every page but whose text is never part of the body content you want to keep. Italic variants of the body bold font are a common signal (e.g. `CnBoldItalic` used decoratively alongside `CnBold` used for content). Add an explicit exclusion:

```python
DECORATIVE_FONTS = {'CnBoldItalic', 'CnSemiboldItalic'}   # fill from your diagnosis

def is_decorative(word):
    fn = base_font(word.get('fontname', ''))
    return any(d in fn for d in DECORATIVE_FONTS)
```

Filter these words out before building line maps, not in post-processing — mid-page decorative lines can otherwise corrupt paragraph buffers.

### Bullet detection must happen at the assembled line level

`classify_word()` sees one word at a time. When a bold font (e.g. Myriad-CnBold) is used for both subsection headings and dash-prefixed bullet items, the dash marker appears only on the first word of the bullet line. The remaining words in the same line are classified as `'subheading'` by font, so the line's dominant class stays `'subheading'` even when it should be a bullet.

Always check for bullet markers on the **assembled line text**, not on individual words:

```python
# After joining line_words into line_text:
if dom == 'subheading' and line_text.startswith('-'):
    dom = 'bullet'
    line_text = line_text[1:].strip()   # strip the leading dash
```

Similarly, a line whose dominant font is a body font but whose assembled text starts with `•` should always be treated as a bullet, regardless of font classification.

### Bullet items: flush on each bullet marker, not just on type-change

A "flush when type changes" rule will merge consecutive bullet items into one paragraph when their y-gaps are small (< PARA_GAP) — which is common in compact two-column layouts. The correct rule is to flush before each new bullet *marker* (a `•` character or a dash-prefix), while allowing genuine text-wrapping continuation lines to stay in the current buffer:

```python
if dom == 'bullet':
    # new_item is True when a fresh marker is present, or when switching from non-bullet,
    # or when the gap is large enough to signal a paragraph break
    new_item = has_bullet_char or has_dash_prefix or buf_type != 'bullet' or gap >= PARA_GAP
    if new_item:
        flush()
    buf_text.append(line_text)
    buf_type = 'bullet'
```

This separates items even at tight y-gaps while still joining a wrapped second line (same font, no marker, small gap) into the current item.

### Post-processing: fix drop-cap artifacts

PDFs using decorative drop caps emit the oversized first letter as a separate word at a slightly offset y-position. Every paragraph opener becomes e.g. `N orthern Ireland`, `G rowing`, `T he DUP`. Fix in a single post-processing pass:

```python
# Drop-cap artefacts at paragraph starts: "N orthern" → "Northern", "T he" → "The"
# Excludes 'A' and 'I': these are common standalone words ("A budget", "I believe")
# that would be incorrectly merged ("Abudget", "Ibelieve") by a [A-Z] pattern.
text = re.sub(r'(?m)^([B-HJ-Z]) ([a-z])', r'\1\2', text)
```

`(?m)` makes `^` match the start of each line. The character class `[B-HJ-Z]` excludes 'A' (article) and 'I' (pronoun), which can legitimately start a paragraph line as standalone words. All other 24 uppercase letters are safe to match — no common English word consists of a single letter other than 'A' and 'I'.

### Post-processing: run the spacing fixer

After any extraction — script-based or manual — run **`manifesto_spacing_fixer.py`** (in `../Python scripts/`) as a final pass before saving the Markdown file. It fixes a family of systematic spacing artefacts that occur across parties and years, including:

- Missing space after a sentence-ending period: `Party.Today` → `Party. Today`
- Missing space after a comma: `economy,public` → `economy, public`
- Missing space after a plural possessive apostrophe: `taxpayers'money` → `taxpayers' money`
- Run-together words from condensed fonts: `positiveUnionist` → `positive Unionist`

```bash
# Always inspect the diff first before writing — use --dry-run:
python ../Python\ scripts/manifesto_spacing_fixer.py path/to/manifesto.md --dry-run

# Conservative (safe for any file — apply after reviewing dry-run):
python ../Python\ scripts/manifesto_spacing_fixer.py path/to/manifesto.md

# Aggressive (also fixes run-together words):
python ../Python\ scripts/manifesto_spacing_fixer.py path/to/manifesto.md --aggressive
```

**Important:** the `--aggressive` mode fixes patterns like "A word" → "Aword" (stray internal space from drop-cap). If the extractor already handles drop-caps by prepending captured characters during extraction (rather than relying on the fixer), `--aggressive` may incorrectly merge legitimate sentence-starting "A " — turning "A mandate" → "Amandate". Always run `--dry-run` first and inspect the full diff before applying, especially when the extractor has drop-cap handling built in.

All fixes are idempotent — running the tool on already-clean text changes nothing. See the README's [Post-extraction spacing corrections](README.md#post-extraction-spacing-corrections) section for the full list of patterns and module usage.

### Mid-page section headings: three-zone extraction

The three-pass approach (preamble + left + right) handles full-width elements at the **top** of a page. But some two-column PDFs place a `##` section heading **mid-page** — between two blocks of column content. Extracting headings first and columns second will misorder the content, emitting the new-section heading before the column content that precedes it on the same page.

The fix is a three-**zone** approach keyed on the section heading's y-position:

```python
min_sy = min(sec_ys)   # y-bucket of the topmost section heading row
max_sy = max(sec_ys)   # y-bucket of the bottommost section heading row

pre_l  = extract_col(words, 0,         col_split, sec_ys, y_hi=min_sy)  # content above heading
pre_r  = extract_col(words, col_split, page_w,    sec_ys, y_hi=min_sy)
heading = extract_section_lines(words, sec_ys)                           # the heading itself
post_l = extract_col(words, 0,         col_split, sec_ys, y_lo=max_sy)  # content below heading
post_r = extract_col(words, col_split, page_w,    sec_ys, y_lo=max_sy)

paras = (lines_to_paras(pre_l) + lines_to_paras(pre_r)
       + lines_to_paras(heading)
       + lines_to_paras(post_l) + lines_to_paras(post_r))
```

When the heading is at the very top of the page, the pre-zones are empty — the logic degrades gracefully to the standard case. Apply this unconditionally to every page that has a section heading, rather than special-casing mid-page instances.

### Visual grid pages: detect and hand-craft

Some back pages (summary spreads, plan grids) present multiple section-level items in a visual grid where two column headings share exactly the same y-coordinate. The section-row detector will pick up both and merge them into one garbled `##` line.

**Detection indicator:** multiple words classified as `'section'` by font appear on the same y-row in **both** columns (x0 < col_split AND x0 ≥ col_split). On a normal body page, a section heading appears only once per y-row.

**Strategy:** add these pages to the skip set, extract their content once manually from the raw word data (group left and right columns separately, read top-to-bottom), write a hand-crafted string constant, and inject it at the right position in the output. This is more reliable than attempting to untangle a visual grid programmatically and typically requires one diagnostic inspection pass.

### section_ys: classify by font, not by x-span

When identifying which y-rows contain section headings, test whether any word on the row is classified as `'section'` by your font classifier — do not use a spatial check (e.g. "words span both columns"). On any normal two-column body page, both columns contain words at the same y-coordinate, so a spatial check incorrectly flags every row as full-width:

```python
def section_ys(words):
    ys = set()
    for w in words:
        if classify(w) == 'section':   # font-based, not position-based
            ys.add(bkt(w['top']))
    return ys
```

### Unicode Private Use Area ligatures

Some PDFs — particularly those using modern OpenType fonts (e.g. Bliss, Myriad Pro) — encode typographic ligatures as Unicode Private Use Area (PUA) codepoints rather than `(cid:XXX)` codes. pdfplumber returns them as literal Unicode characters that appear correct in some text editors but corrupt search and word-count. Fix them before any downstream processing:

```python
def fix_lig(t):
    return (t.replace('\ufb01', 'fi').replace('\ufb02', 'fl')
             .replace('\ufb03', 'ffi').replace('\ufb04', 'ffl')
             .replace('\u00ad', '')    # soft hyphen — delete
             .replace('\u200b', ''))  # zero-width space — delete
```

Apply `fix_lig()` to every word's text immediately after extracting it from the PDF, before building lines or paragraphs. Without this, words like "first", "office", "official", and "different" will contain invisible non-ASCII bytes that silently inflate the word count and corrupt downstream search.

### Post-processing: inspect `(cid:XXX)` codes before stripping

If `(cid:\d+)` codes appear in the extracted text, do not blindly strip them — this silently removes letters from words (e.g. "official" → "ocial"). Instead, build a substitution table by identifying which codes correspond to common ligature characters:

```python
CID_MAP = {
    '563': 'fi',  '564': 'fl',  '565': 'fl',  '566': 'fi',
    '572': 'ff',  '573': 'fi',  '574': 'ffi', '575': 'ffl',
}

def resolve_cid(text):
    def replace(m):
        return CID_MAP.get(m.group(1), '')  # empty string for any unknown code
    return re.sub(r'\(cid:(\d+)\)', replace, text)
```

CID numbers vary by font and PDF. To find the right mappings for a specific document, look for words you know contain ligatures (e.g. "official", "different", "conflict") and note which `(cid:XXX)` codes appear in those positions. Any codes not in the table should be logged rather than silently dropped, so you can extend the table rather than accrue invisible data loss.

### Post-processing: detect and discard garbage lines

Column extraction failures produce lines of space-separated individual letters that look plausible in a word-count check but corrupt the text. After extraction, scan for and discard them:

```python
def is_garbage_line(text):
    """True if the line looks like a column-extraction failure artefact."""
    tokens = text.split()
    if len(tokens) < 3:
        return False
    short = sum(1 for t in tokens if len(re.sub(r'[^A-Za-z]', '', t)) <= 2)
    return short / len(tokens) > 0.6 and len(text) < 60

lines = [l for l in lines if not is_garbage_line(l)]
```

Log every discarded line and review the log — the threshold is a heuristic, and occasionally a legitimate short line (e.g. a label like "A. Tax") will be near the boundary.

### Post-processing: rejoin truncated paragraphs

A paragraph that runs to the end of a column or page is often split: the first fragment ends mid-sentence, and the next paragraph begins with a lowercase continuation. Fix in post-processing:

```python
_DANGLING = re.compile(
    r'\b(the|a|an|at|in|of|for|by|with|to|from|on|into|and|or|but|'
    r'its|our|their|this|these|those|which|that|who|whom)\s*$',
    re.I
)

def rejoin_truncated_paragraphs(paragraphs):
    result = []
    i = 0
    while i < len(paragraphs):
        p = paragraphs[i]
        # Headings: never rejoin
        if p.startswith('#'):
            result.append(p); i += 1; continue
        # Consecutive bold-only fragments (e.g. back-page slogans split across lines)
        if p.startswith('**') and p.endswith('**'):
            body = p[2:-2]
            while (i + 1 < len(paragraphs)
                   and not re.search(r'[.?!:]\s*$', body)
                   and paragraphs[i + 1].startswith('**')
                   and paragraphs[i + 1].endswith('**')):
                i += 1; body = body.rstrip() + ' ' + paragraphs[i][2:-2].lstrip()
            result.append(f'**{body}**'); i += 1; continue
        # Bullet items: rejoin lowercase continuation lines
        if p.startswith('* '):
            body = p[2:]
            while (i + 1 < len(paragraphs)
                   and not re.search(r'[.?!:]\s*$', body.rstrip('*_'))
                   and not paragraphs[i + 1].startswith('#')
                   and not paragraphs[i + 1].startswith('* ')
                   and paragraphs[i + 1][:1].islower()):
                i += 1; body = body.rstrip() + ' ' + paragraphs[i].lstrip()
            result.append('* ' + body); i += 1; continue
        # Normal paragraphs: rejoin if ends without punctuation AND next starts lowercase
        # OR ends with a dangling word (preposition/article) even if next starts uppercase
        while (i + 1 < len(paragraphs)
               and not re.search(r'[.?!:]\s*$', p.rstrip('*_'))
               and not paragraphs[i + 1].startswith('#')
               and not paragraphs[i + 1].startswith('* ')
               and (paragraphs[i + 1][:1].islower()
                    or _DANGLING.search(p.rstrip('*_')))):
            i += 1; p = p.rstrip() + ' ' + paragraphs[i].lstrip()
        result.append(p)
        i += 1
    return result
```

Key improvements over the basic version:
- **Bullet continuation**: bullet items whose text wraps to a second (non-bullet) line are rejoined correctly
- **Dangling-word detection**: fragments ending with a preposition, article, or conjunction are rejoined even when the continuation starts with an uppercase proper noun (e.g. "...and the Scottish" + "Government..." or "...Change at" + "Westminster...")
- **Bold fragment merging**: consecutive bold-only lines (e.g. a decorative slogan split across visual lines on a back page) are merged into one bold paragraph
- **Run this globally**: call `rejoin_truncated_paragraphs()` once per column AND once more on the combined `all_sections` list, to catch fragments split at column boundaries

Add specific proper nouns or acronyms to `_DANGLING` that are common mid-sentence continuations in your specific manifesto.

### pdfplumber is pre-installed in the toolkit

The `lib/` subfolder of this toolkit contains a pre-installed copy of pdfplumber (v0.11.9). Import it at the top of any new extraction script:

```python
import sys, pathlib
try:
    import pdfplumber
except ImportError:
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / 'transcription-toolkit' / 'lib'))
    import pdfplumber
```

`pdftotext` is not bundled — check for it with `which pdftotext` and install via `brew install poppler` (macOS) or `sudo apt install poppler-utils` (Linux) if needed. It is optional — extraction scripts work without it, only skipping the word-count verification step.

### Coverage caveat for heavily designed PDFs

For PDFs with many decorative elements, `pdftotext | wc -w` overstates the true content word count, making your coverage look artificially low. `pdftotext` extracts tiny (2–7pt) sidebar text, callout boxes, photo captions in non-standard fonts, and other non-body elements that your extraction script correctly ignores. A reported 85–88% against `pdftotext` can correspond to 100%+ of the actual prose content. When in doubt, calculate effective coverage by excluding decorative words from the denominator — see the README's Scottish Greens lessons for the technique.

### Capitalisation post-processing: check early and treat as mandatory

Some publishers use intentionally lowercase styling throughout their PDFs — sentence-starting words in body paragraphs are lowercased, proper nouns are lowercased, and abbreviations appear in unexpected case. The extraction pipeline preserves this faithfully, so the raw output will need a capitalisation cleanup pass before the Markdown is usable.

**Check during diagnosis, not at the end.** Scan a few body paragraphs early to see whether sentence starts and known proper nouns are correctly cased. If they are not, flag this as a mandatory post-processing step before investing time in the full extraction.

The three categories to fix:

1. **Sentence starts** — the first word of each sentence within body paragraphs. A regex pass over `. ` boundaries handles most cases; manually review sentence starts after question marks and exclamation marks too.

2. **Proper nouns** — place names (Scotland, England, Aberdeen, Faslane), party names (Scottish Greens, Labour, SNP), organisation names (NHS, ScotRail, NATO), legislation names (Human Rights Act, Health and Social Care Act), international bodies (EU, UN, Syriza), and named initiatives (Green New Deal, Smith Commission).

3. **Abbreviations** — NHS, EU, NATO, UN, GDP, CEO, TTIP, and any others appearing in the document. These often appear fully lowercase in the PDF even when they should be all-caps.

Apply a targeted `re.sub()` pass using word-boundary anchors (`r'\b[Nn][Hh][Ss]\b'` → `'NHS'`) for each known item. The list is document-specific — build it by scanning the markdown output for obvious mismatches against the PDF.

### Multi-column candidates lists: column midpoints, per-page processing, look-ahead splitting

Many manifestos include a candidates list — a multi-column table with constituency names and candidate names. These require three techniques beyond standard column handling (see the README's Scottish Greens 2015 lessons for full code):

- **Column midpoint boundaries**: assign each word to a column using midpoints between adjacent column left-edges, not the left-edges themselves. Using left-edges means words near a column's right margin are misassigned to the next column.
- **Per-page processing**: process each page of the candidates section independently. Pooling words from multiple pages before sorting by y causes entries to interleave, because consecutive pages share the same y-coordinate ranges.
- **Look-ahead boundary detection**: a line is a new-entry boundary only if all remaining lines in the current block are continuation lines (ending with a comma, `&`, or ` and`). Without look-ahead, multi-word constituency names like "West Aberdeenshire & Kincardine" split prematurely.
- **Last-comma split**: to separate constituency name from candidate name, join all lines in the entry first, then find the last comma with `rfind(',')`. Do not attempt to detect the split line-by-line.

### Facing-pages (alternating margin) column layout

Printed manifestos typeset for double-sided printing use a *facing-pages* layout: odd (recto) pages have a wide inner margin on the right and odd columns start close to the left edge, while even (verso) pages are mirror-imaged. This means the column gutter position alternates between odd and even pages:

- **Odd pages**: left column x≈30–220pt, right column starts x≈300pt → col_split≈260
- **Even pages**: left column x≈100–285pt, right column starts x≈370pt → col_split≈345

A single fixed `col_split` will misassign an entire column on every other page. The fix is per-page auto-detection from the body text x0 histogram:

```python
from collections import Counter

def auto_col_split(page, body_font='Minion', y_lo=90, y_hi=803, fallback=330):
    """Detect column split x using body text character x0 histogram gap.
    Works for facing-pages layouts where the gutter alternates by page parity.
    Replace 'Minion' with your PDF's body font name fragment.
    """
    chars = [c for c in page.chars
             if body_font in c['fontname'] and c['text'].strip()
             and y_lo <= c['top'] <= y_hi]
    if len(chars) < 30:
        return fallback
    x_counts = Counter(round(c['x0'] / 10) * 10 for c in chars)
    occupied = sorted(k for k, v in x_counts.items() if v >= 2)
    best_gap, best_split = 0, fallback
    for i in range(1, len(occupied)):
        gap = occupied[i] - occupied[i-1]
        if gap > best_gap and occupied[i-1] > 60:   # exclude left margin noise
            best_gap = gap
            best_split = (occupied[i-1] + occupied[i]) // 2
    return best_split if best_gap > 25 else fallback
```

Call `auto_col_split(page)` on every page rather than using a global `col_split`. The 25pt gap threshold is conservative — for large-format PDFs with wide gutters, lower it to 15. For narrow-gutter PDFs, raise it to 40.

**When to suspect facing-pages layout:** if your first-pass extraction shows that right-column content is appearing in the left-column output on every other page, run `auto_col_split` on pages 2, 3, 4, 5 and compare the returned values. If odd and even pages return values differing by ≥40pt, you have a facing-pages layout.

### Pull-quote / standfirst exclusion by font name

Some two-column manifestos print a decorative pull-quote (standfirst) in the right column that **exactly repeats body text** from the same spread. These must be identified and excluded — they inflate word count and appear as duplicate paragraphs.

Standfirsts are typically:
- An italic variant of the heading font (e.g. `Humanist521BT-Italic`) at a noticeably larger size than body italic (≥14pt)
- NOT the light-italic body continuation font (e.g. `Humanist521BT-LightItalic`)
- Positioned in a specific column (usually the right), alongside body text

Exclusion pattern:

```python
def is_standfirst(fontname, size, sf_font='Humanist521BT-Italic',
                   not_sf_font='LightItalic', min_sz=14):
    """Return True for pull-quote standfirst text that duplicates body content."""
    bf = fontname.split('+')[-1]
    return sf_font in bf and not_sf_font not in bf and size >= min_sz
```

Identify the correct font name by running the Step 0 diagnosis on a page you know has a pull-quote, then filtering for words whose text appears verbatim in the body of the same page. Verify that `is_standfirst()` returns `True` for all pull-quote words and `False` for all body words before using it in the extraction loop.

**Note:** do not simply exclude all right-column italic text — the right column will also contain regular body italic (emphasis words, titles). The font name + size combination is the reliable discriminant.

### Mid-page section headings: empty heading_ys guard

The three-zone extraction approach (pre-heading body → heading → post-heading body) has a degenerate case: **pages with no section headings**. When `heading_ys` is empty, naïve min/max give sentinel values (e.g. `min=9999`, `max=0`), and both the pre-zone and post-zone cover the entire page — every body word is included in both, doubling the output.

Always guard against this case:

```python
def process_page(page, ...):
    heading_ys = find_heading_ys(all_words)
    headings   = extract_headings(all_words, heading_ys)

    if not heading_ys:
        # No headings — return all body as a single block (no pre/post split)
        all_left  = filter_body(all_words, 0,         col_split, Y_HEADER, Y_FOOTER)
        all_right = filter_body(all_words, col_split, 9999,      Y_HEADER, Y_FOOTER)
        return [], [], paragraphs(all_left) + paragraphs(all_right)

    min_hy = min(heading_ys)
    max_hy = max(heading_ys)

    pre_left   = filter_body(all_words, 0,         col_split, Y_HEADER, min_hy - 1)
    pre_right  = filter_body(all_words, col_split, 9999,      Y_HEADER, min_hy - 1)
    post_left  = filter_body(all_words, 0,         col_split, max_hy + 1, Y_FOOTER)
    post_right = filter_body(all_words, col_split, 9999,      max_hy + 1, Y_FOOTER)

    pre_paras  = paragraphs(pre_left)  + paragraphs(pre_right)
    post_paras = paragraphs(post_left) + paragraphs(post_right)
    return pre_paras, headings, post_paras
```

Without this guard, the word count in the output will be ~60% higher than expected (every word on heading-free pages counted twice), which is a clear signal to add the check.

### Full-width multi-line headings: apply hyphen-join fix after merging rows

When a heading that spans multiple typographic rows is assembled by merging consecutive y-buckets, a hyphenated compound word can be split across the join: `"barrier-"` ends the first row and `"free"` starts the next. The merged text becomes `"barrier- free"` — hyphen followed by a space.

The hyphen-join regex must be applied **to the fully-merged heading text**, not to each row independently:

```python
# WRONG: applied per-row before merging — misses end-of-row hyphen
for y in sorted(by_y.keys()):
    text = ' '.join(...)
    text = re.sub(r'(\w)- (\w)', r'\1-\2', text)   # ← doesn't fire on "barrier-" alone
    raw.append((y, cl, text))

# RIGHT: applied to each item after the merge loop
merged = []
for y, cl, text in raw:
    if merged and same_type_and_close(merged[-1], cl, y):
        merged[-1][2] += ' ' + text
    else:
        merged.append([y, cl, text])
for item in merged:
    item[2] = re.sub(r'(\w)- (\w)', r'\1-\2', item[2])   # ← now fires on "barrier- free"
```

Also ensure the post-processing line-break hyphen-join regex does **not** strip intentional compound-word hyphens. The line-break regex `re.sub(r'([a-z]{2,})- ([a-z])', r'\1\2', md)` removes the hyphen entirely. If a heading has already been corrected to `"barrier-free"` (no space), this regex won't match it. But if it still contains `"barrier- free"` (with space), it will produce `"barrierfree"`. The fix-after-merge step above prevents this.

### Condensed font word-split artefacts

Tightly-kerned condensed typefaces (e.g. Humanist521BT-Light Condensed, DIN Condensed) can cause pdfplumber's `extract_words()` to split a single word into multiple tokens because the inter-character gap in a condensed font exceeds the inter-word gap in a regular font at the same `x_tolerance`.

The symptom is words split mid-sequence with no visible space: `"par"` + `"t"` (from `"part"`), `"con"` + `"tent"` (from `"content"`), or `"over"` + `"all"` (from `"overall"`).

Two fixes:

1. **Increase `x_tolerance`** for `extract_words()` — try `x_tolerance=4` or `x_tolerance=6` for condensed fonts. Note this can merge words that are genuinely separate; check on a representative page.

2. **Post-processing regex** for known splits in your specific document:
```python
text = re.sub(r'\bpar t\b', 'part', text, flags=re.I)
text = re.sub(r'\bcon tent\b', 'content', text, flags=re.I)
# add other known splits discovered during review
```

To discover which words are affected: scan the extracted text for sequences of 2–4 short tokens (≤4 chars each) that form a known English word when concatenated, especially in headings where condensed fonts are most common.

### Sentence joining across column breaks: the highest-impact post-processing step

The single largest source of rough-vs-clean draft difference in two-column manifesto extraction is **mid-sentence column breaks**. A sentence that spans a column boundary produces two separate paragraphs: the first ending with an incomplete clause, the second beginning with a continuation fragment. In a typical two-column manifesto, there are ~250–350 such splits per document.

Validation from SSP 2005 (21,600 words): applying systematic sentence joining reduced the body line count by ~300 and blank line count by ~536 — roughly 30% of all paragraph boundaries were artefacts of the column layout, not genuine paragraph breaks.

The `rejoin_truncated_paragraphs()` function described above handles this, but must be applied **at the column level and again at the combined output level**:

```python
# After assembling each column's paragraphs:
left_paras  = rejoin_truncated_paragraphs(raw_left_paras)
right_paras = rejoin_truncated_paragraphs(raw_right_paras)

# After combining all pages into a flat list:
all_paras   = rejoin_truncated_paragraphs(combined_paras)
```

The two-pass approach catches:
- **Within-column splits**: a sentence broken at the bottom of a column block before the next heading
- **Cross-column splits**: a sentence whose first half ends the left column and second half starts the right column

**What the joining algorithm must check:**
1. The previous paragraph's last character is not sentence-ending punctuation (`.`, `!`, `?`, `:`, `"`, `'`, `»`)
2. The current paragraph does not start a new structural element (`#` heading, `* ` bullet, `_` italic block)
3. The previous paragraph does not end a structural element (heading, bold block)

Without condition 3, the joiner will absorb the body text that follows a bold standfirst into the standfirst itself — a common failure mode.

**Quick diagnosis**: after a first-pass extraction, run:
```python
import re
with open('output.md') as f:
    md = f.read()
frags = re.findall(r'\n\n([a-z][^\n]{0,60})\n\n', md)
print(f"{len(frags)} paragraphs starting with lowercase (likely continuation fragments)")
```
If this returns > 50, aggressive sentence joining is needed. If it returns < 10, the column layout is well-behaved and joining is low risk.

### Colored callout boxes: separate raw words before filtering

Some PDFs place content inside colored fill rectangles (callout boxes, foreword boxes, policy sidebars). These boxes must be handled before any other processing step — not after. The ordering matters for two reasons:

1. **Box words must be separated from main-body words before column detection.** If box words remain in the main pool, they extend the x0 range and fill the column gap in the histogram, preventing gap detection.
2. **Box words must be separated before Y_HEADER filtering.** Boxes often start near the top of the page (within the header zone). If you filter by Y_HEADER first, the opening lines of a box will be silently discarded.

The correct sequence is: extract raw words → separate box words → filter main-body words (including Y_HEADER strip) → filter box words (Y_HEADER-free) → detect columns from main-body only.

Use `get_colored_boxes()` and `separate_box_words()` from `extract_manifesto.py`:

```python
raw_words = page.extract_words(extra_attrs=['fontname','size'], x_tolerance=3, y_tolerance=3)
page_h    = float(page.height)

# Step 1: find colored fill rects
boxes = get_colored_boxes(page)           # from extract_manifesto.py

# Step 2: partition raw words BEFORE any filtering
main_raw, box_pools = separate_box_words(raw_words, boxes)

# Step 3: now filter each pool independently
main_body = filter_words(main_raw, page_h)          # full filter incl. Y_HEADER
box_pools_filtered = [filter_box_words(pool, page_h) for pool in box_pools]

# Step 4: detect columns from main-body only
col_split = find_column_split(main_body)
```

`get_colored_boxes()` handles both RGB and CMYK fill colors (normalising CMYK via `rv=(1-c)*(1-k)` etc.) and excludes near-white fills (all channels ≥ 0.95) and near-black fills (mean < 0.10). It returns boxes as `(x0, y_top, x1, y_bot)` tuples in screen coordinates (top-left origin).

**Worked example (2005 Scottish Liberal Democrats manifesto):** the foreword was in a blue fill box starting at y≈45. Y_HEADER was set to 98. Without box-first separation, the foreword's opening 50pt of text was silently stripped. After restructuring to separate box words before the Y_HEADER filter, the full foreword was recovered.

`profile_pdf.py` now reports colored rect counts per page. If the profiler flags pages with `colored_rects > 0`, apply this pattern in your extraction script.

### PARA_GAP calibration for small body fonts

The default `PARA_GAP = 18` is calibrated for 11–12pt body text with normal leading. For PDFs with smaller body text, this default will miss all paragraph breaks, causing the entire body to flow as one long paragraph.

**The rule:** paragraph gaps are roughly proportional to font size. For body text at size `s`, the within-paragraph line gap is approximately `s × 1.2` and the between-paragraph gap is typically `s × 1.4–1.6`. The effective discriminating gap (large enough to separate paragraphs, small enough not to split lines) is approximately:

```
PARA_GAP ≈ max(3, min(18, round(body_font_size × 0.5)))
```

This formula gives:
- 10pt body → PARA_GAP ≈ 5
- 11pt body → PARA_GAP ≈ 6
- 12pt body → PARA_GAP ≈ 6
- 14pt body → PARA_GAP ≈ 7
- 18pt body → PARA_GAP ≈ 9
- 36pt body → PARA_GAP = 18 (capped)

**Worked example (2005 Scottish Liberal Democrats manifesto):** body text was FrutigerLinotype at 10pt. With the default PARA_GAP=18, every paragraph break was missed — the entire document extracted as one block. Setting PARA_GAP=5 (= round(10 × 0.5)) produced correctly separated paragraphs.

**Diagnosis:** if the output word count is correct but the file has almost no blank lines, PARA_GAP is too large. Inspect a body page:

```python
with pdfplumber.open("manifesto.pdf") as pdf:
    page = pdf.pages[5]
    words = page.extract_words(extra_attrs=['fontname','size'])
    tops = sorted(set(round(w['top'] / 2) * 2 for w in words if 'BodyFont' in w.get('fontname', '')))
    for a, b in zip(tops, tops[1:]):
        if b - a > 2:
            print(f"gap: {b - a:.1f}pt")
```

Look for two clusters of gaps: small gaps (within-paragraph line spacing) and larger gaps (between-paragraph breaks). PARA_GAP should sit between the two clusters.

`profile_pdf.py` now suggests a PARA_GAP value based on the detected median body font size. Check the `## Hints` section of the profiler output when starting on a new PDF.
