#!/usr/bin/env python3
"""
qa_check.py — Post-extraction QA scanner for manifesto Markdown files.

Run this AFTER extraction to catch artefacts before manual inspection.

Usage:
    python qa_check.py output.md
    python qa_check.py output.md --pdf manifesto.pdf
    python qa_check.py output.md --pdf manifesto.pdf --json
    python qa_check.py output.md --pdf manifesto.pdf --strict
    python qa_check.py output.md --allowlist qa_allowlist.yaml

Options:
    --pdf FILE          Original PDF (enables word-count coverage check and
                        per-section coverage drop detection)
    --json              Output machine-readable JSON
    --strict            Exit with code 1 if any errors or warnings found
    --no-colour         Disable ANSI colour output
    --allowlist FILE    YAML allowlist file to suppress known false positives
                        (default: looks for qa_allowlist.yaml next to this script)
    --no-allowlist      Disable allowlist loading entirely
    --merge-continuations
                        Pre-process bullets: merge lines that end with a dangling
                        preposition/article into the following continuation line
                        before running checks (useful to suppress false B4 warnings)

Checks performed:
  COVERAGE
    C1  Word-count coverage vs pdftotext baseline (requires --pdf)
  ENCODING
    E1  Unicode replacement characters (U+FFFD  →  '?')
    E2  Raw CID tokens still present: (cid:N)
    E3  Non-printing control characters
  HEADINGS
    H1  Heading starts with an opening/closing quotation mark
    H2  Heading starts with a lowercase letter
    H3  Heading is a sentence continuation (starts with lowercase or conjunction)
        [INFO — downgraded from warning; legitimate manifesto headings often start
        with articles such as "The" or conjunctions like "A"]
    H4  Heading starts with punctuation (, . : ; ! ? -)
    H5  Adjacent headings that could be merged (same level, very similar text)
    H6  Heading word count > 30 (likely body text promoted to heading)
  BULLETS / LISTS
    B1  Raw bullet glyph (•, ●, ◆) still present in paragraph text
    B2  Mid-sentence bullet: bullet char not at paragraph start
    B3  Orphaned single-word list item (common sidebar continuation artefact)
  PARAGRAPHS
    P1  Paragraph is a bare page number (1–3 digits, nothing else)
    P2  All-caps run of ≥ 5 words (possible un-spaced slogan from cover)
    P3  Repeated paragraph (exact duplicate appearing more than once)
    P4  Very short paragraph (< 4 words) that is not a heading or list item
  SPACING
    S1  Missing space after sentence-ending period: 'word.Word'
    S2  Missing space after comma: 'word,word'
    S3  Run-together ALL-CAPS words: 'ANDVOLUNTARY'
  IMPRINT / LAYOUT
    I2  Attribution block garbling — two-column foreword signatures merged
        into a single line (e.g. "Leader of the Leader of the"), a sign that
        a side-by-side author credit was read column-by-column instead of as
        two separate attributions
  SPACING (continued)
    S4  Repeated consecutive identical word ("of of", "the the") — common
        artefact at column or region boundaries during extraction
  BULLETS / LISTS (continued)
    B4  Bullet item ends with a dangling preposition, article, or conjunction
        ("support to the Scottish", "investment in") — probable truncation
        at a column or page boundary
  VERTICAL FRAGMENTS (new)
    V1  Repeated single-letter or two-letter fragments — likely vertical header
    V2  Paragraph composed only of spaced initials (e.g. "P y W b A m")
    V3  Improbable single-character paragraph
  READING ORDER (new — distinct from coverage)
    R1  Repeated adjacent words at likely column joins within a paragraph
        (same as S4 but reported in the reading-order section for clarity)
    R2  Bullet glyph embedded inside a prose paragraph (reading-order symptom)
    R3  Unusually high ratio of very-short orphan fragments to total paragraphs
        — suggests spread-column interleaving even when word coverage is healthy
"""

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ── Allowlist ─────────────────────────────────────────────────────────────────

def load_allowlist(path: Optional[str]) -> dict:
    """
    Load a qa_allowlist.yaml file and return a normalised dict:
        {
          'phrases':               [str, ...],   # exact substrings to ignore
          'heading_starts_allowed': [str, ...],  # first words OK as heading starts
          'disabled_codes':        [str, ...],   # check codes to suppress entirely
        }
    Returns an empty allowlist (all checks active) if path is None or missing.
    """
    empty: dict = {'phrases': [], 'heading_starts_allowed': [], 'disabled_codes': []}
    if path is None:
        return empty

    p = Path(path)
    if not p.exists():
        return empty

    try:
        # Try PyYAML first; fall back to a minimal hand-rolled parser
        try:
            import yaml  # type: ignore
            data = yaml.safe_load(p.read_text(encoding='utf-8')) or {}
        except ImportError:
            # Minimal YAML parser: handles simple list-under-key structure only
            data = _parse_simple_yaml(p.read_text(encoding='utf-8'))
    except Exception:
        return empty

    return {
        'phrases':               [str(x) for x in (data.get('phrases') or [])],
        'heading_starts_allowed': [str(x).lower() for x in
                                   (data.get('heading_starts_allowed') or [])],
        'disabled_codes':        [str(x).upper() for x in
                                  (data.get('disabled_codes') or [])],
    }


def _parse_simple_yaml(text: str) -> dict:
    """
    Very minimal YAML list-under-key parser (no PyYAML dependency).
    Handles only:
        key:
          - value1
          - value2
    """
    result: dict = {}
    current_key: Optional[str] = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if stripped.endswith(':') and not stripped.startswith('-'):
            current_key = stripped[:-1].strip()
            result[current_key] = []
        elif stripped.startswith('- ') and current_key:
            result[current_key].append(stripped[2:].strip().strip('"\''))
    return result


def _is_allowlisted(text: str, allowlist: dict) -> bool:
    """Return True if the text matches any allowlist phrase."""
    for phrase in allowlist.get('phrases', []):
        if phrase in text:
            return True
    return False


# ── Bullet continuation merger ─────────────────────────────────────────────────

RE_CONTINUATION_TRIGGER = re.compile(
    r'\b(the|a|an|at|in|of|for|by|with|to|from|on|into|and|or|but|'
    r'its|our|their|this|these|those|which|that|who|whom)\s*$',
    re.IGNORECASE,
)
RE_DANGLING_CURRENCY = re.compile(r'[£$€]\s*$')
RE_CONTINUATION_NEXT = re.compile(r'^[a-z£$€\d]')


def merge_bullet_continuations(text: str) -> str:
    """
    Pre-processing pass: merge bullet list items that end with a dangling
    preposition, article, conjunction, or currency symbol into the following
    continuation line.

    Only merges when the NEXT line looks like a continuation (starts lowercase
    or with a currency amount) and is not itself a new bullet or heading.

    This runs before QA so B4 warnings focus on genuinely truncated lists.
    """
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Only attempt merging on bullet lines
        if (stripped.startswith('* ') or stripped.startswith('- ')):
            bullet_text = stripped[2:].strip()
            # Check for dangling end
            if (RE_CONTINUATION_TRIGGER.search(bullet_text)
                    or RE_DANGLING_CURRENCY.search(bullet_text)):
                # Look ahead for a non-empty continuation line
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines):
                    next_stripped = lines[j].strip()
                    # Merge only if next line is NOT a new bullet/heading/blank
                    if (next_stripped
                            and not next_stripped.startswith(('* ', '- ', '#'))
                            and RE_CONTINUATION_NEXT.match(next_stripped)):
                        prefix = stripped[:2]  # '* ' or '- '
                        merged = prefix + bullet_text + ' ' + next_stripped
                        out.append(merged)
                        # Skip any blank lines between and the consumed line
                        i = j + 1
                        continue
        out.append(line)
        i += 1
    return '\n'.join(out)


# ── Colours ───────────────────────────────────────────────────────────────────

USE_COLOUR = True

def red(s):    return f"\033[31m{s}\033[0m" if USE_COLOUR else s
def yellow(s): return f"\033[33m{s}\033[0m" if USE_COLOUR else s
def green(s):  return f"\033[32m{s}\033[0m" if USE_COLOUR else s
def bold(s):   return f"\033[1m{s}\033[0m"  if USE_COLOUR else s
def dim(s):    return f"\033[2m{s}\033[0m"  if USE_COLOUR else s


# ── Issue dataclass ───────────────────────────────────────────────────────────

@dataclass
class Issue:
    code:    str           # e.g. "H1"
    line:    int           # 1-indexed line number in the markdown file
    excerpt: str           # short excerpt of the offending text
    detail:  str = ''      # additional detail

    def severity(self) -> str:
        if self.code.startswith('C'):
            # C1 with healthy coverage is informational, not an error
            if 'Coverage looks healthy' in self.detail:
                return 'info'
            return 'error'
        if self.code.startswith('E'):
            return 'error'
        # H3 (heading starts with article/conjunction) is downgraded to info:
        # many legitimate manifesto section headings begin with "The", "A", etc.
        if self.code == 'H3':
            return 'info'
        # V1/V2/V3 vertical fragment checks are warnings
        if self.code in ('V1', 'V2', 'V3'):
            return 'warning'
        # R3 (orphan fragment ratio) is info; R1/R2 are warnings
        if self.code == 'R3':
            return 'info'
        if self.code in ('R1', 'R2'):
            return 'warning'
        if self.code in ('H1', 'H2', 'H4', 'B2', 'B4', 'S3', 'S4', 'P2', 'I2'):
            return 'warning'
        return 'info'


# ── Regex patterns ────────────────────────────────────────────────────────────

RE_OPEN_QUOTE   = re.compile(u'[\u201c\u201d\u2018\u2019\u00ab\u2039]')
RE_LOWER_START  = re.compile(r'^[a-z]')
RE_PUNCT_START  = re.compile(r'^[,.:;!?\-–—]')
RE_PAGE_NUMBER  = re.compile(r'^\d{1,3}$')
RE_CAPS_RUN     = re.compile(r'\b[A-Z]{2,}(?:\s+[A-Z]{2,}){4,}\b')
RE_MISSING_SP_P = re.compile(r'[a-z]\.[A-Z]')         # word.Word
RE_MISSING_SP_C = re.compile(r'[a-z],[a-zA-Z]')       # word,word
RE_CAPS_FUSED   = re.compile(r'[A-Z]{2,}[a-z][A-Z]{2,}')  # e.g. ANDVoluntary
RE_CID          = re.compile(r'\(cid:\d+\)')
RE_CONTROL      = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')
RE_BULLET_GLYPH = re.compile(r'[•●◆◉▪▸►]')
RE_DOUBLE_WORD  = re.compile(r'\b(\w{2,})\s+\1\b', re.IGNORECASE)
RE_DANGLING_END = re.compile(
    r'\b(the|a|an|at|in|of|for|by|with|to|from|on|into|and|or|but|'
    r'its|our|their|this|these|those|which|that|who|whom)\s*$',
    re.IGNORECASE,
)
CONJUNCTIONS    = {'and', 'or', 'but', 'nor', 'so', 'yet', 'for',
                   'although', 'because', 'since', 'while', 'that',
                   'which', 'who', 'whom', 'whose', 'where', 'when',
                   'if', 'unless', 'until', 'than', 'as', 'of', 'in',
                   'to', 'a', 'an', 'the', 'with', 'at', 'by', 'from'}

# ── Imprint / layout patterns ─────────────────────────────────────────────────

# I2 — attribution block garbling: two-column author credits read as one line
# Catches "Leader of the Leader of the", "MP for ... MP for ...", etc.
RE_ATTR_DOUBLE = re.compile(
    r'(?i)'
    r'(leader\s+of\s+the\s+.{1,60}leader\s+of\s+the'
    r'|\bmp\s+for\s+\w.{1,40}\bmp\s+for\s+\w'
    r'|party\s+leader\s+.{1,60}party\s+leader'
    r')',
)


def trunc(s: str, n: int = 80) -> str:
    """Truncate string to n chars for display."""
    s = s.replace('\n', ' ')
    return s[:n] + '…' if len(s) > n else s


# ── Markdown parser ───────────────────────────────────────────────────────────

def parse_markdown(text: str) -> list[dict]:
    """
    Parse markdown into a list of block records:
      {'type': 'heading'|'bullet'|'paragraph', 'level': int|None,
       'text': str, 'line': int}
    """
    blocks = []
    for lineno, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith('#'):
            m = re.match(r'^(#{1,6})\s+(.*)', stripped)
            if m:
                blocks.append({
                    'type':  'heading',
                    'level': len(m.group(1)),
                    'text':  m.group(2).strip(),
                    'line':  lineno,
                })
        elif stripped.startswith('* ') or stripped.startswith('- '):
            blocks.append({
                'type':  'bullet',
                'level': None,
                'text':  stripped[2:].strip(),
                'line':  lineno,
            })
        else:
            blocks.append({
                'type':  'paragraph',
                'level': None,
                'text':  stripped,
                'line':  lineno,
            })
    return blocks


# ── Individual checks ─────────────────────────────────────────────────────────

def check_headings(blocks: list[dict]) -> list[Issue]:
    issues = []
    prev_heading = None

    for b in blocks:
        if b['type'] != 'heading':
            prev_heading = None
            continue

        text = b['text']
        line = b['line']

        # H1 — starts with quote mark
        if RE_OPEN_QUOTE.match(text):
            issues.append(Issue('H1', line, trunc(text),
                                 'Heading starts with quotation mark — likely a pull quote'))

        # H2 — starts lowercase
        elif RE_LOWER_START.match(text):
            issues.append(Issue('H2', line, trunc(text),
                                 'Heading starts with lowercase letter'))

        # H3 — starts with conjunction/article (sentence continuation)
        first_word = text.split()[0].lower().rstrip('.,;:') if text.split() else ''
        if first_word in CONJUNCTIONS and not RE_OPEN_QUOTE.match(text):
            issues.append(Issue('H3', line, trunc(text),
                                 f'Heading starts with conjunction/article "{first_word}" — possible continuation fragment'))

        # H4 — starts with punctuation
        if RE_PUNCT_START.match(text):
            issues.append(Issue('H4', line, trunc(text),
                                 'Heading starts with punctuation'))

        # H5 — adjacent same-level headings that look like they should be merged
        if (prev_heading and prev_heading['level'] == b['level']
                and b['line'] - prev_heading['line'] <= 3):
            prev_text = prev_heading['text']
            # Flag if previous heading ended without terminal punctuation
            if prev_text and prev_text[-1] not in '.!?:':
                issues.append(Issue('H5', prev_heading['line'],
                                     trunc(prev_text + '  →  ' + text),
                                     'Adjacent same-level headings — possible multi-line heading split'))

        # H6 — suspiciously long heading
        word_count = len(text.split())
        if word_count > 30:
            issues.append(Issue('H6', line, trunc(text),
                                 f'Heading has {word_count} words — possible body text promoted to heading'))

        prev_heading = b

    return issues


def check_bullets(blocks: list[dict]) -> list[Issue]:
    issues = []
    for b in blocks:
        text = b['text']
        line = b['line']

        if b['type'] == 'bullet':
            # B3 — orphaned single-word item
            if len(text.split()) == 1 and text.isalpha():
                issues.append(Issue('B3', line, trunc(text),
                                     'Single-word bullet item — possible orphaned sidebar continuation'))

            # B4 — bullet ends with a dangling preposition/article (probable truncation)
            # Only flag items long enough to be a genuine sentence (> 5 words),
            # to avoid false positives on short label-style bullets.
            if len(text.split()) > 5 and RE_DANGLING_END.search(text):
                issues.append(Issue('B4', line, trunc(text),
                                     'Bullet ends with preposition/article/conjunction'
                                     ' — probable sentence truncation at column or page boundary'))

        elif b['type'] == 'paragraph':
            # B1 — raw bullet glyph in paragraph
            if RE_BULLET_GLYPH.search(text):
                issues.append(Issue('B1', line, trunc(text),
                                     'Raw bullet glyph in paragraph text — may not have been converted to markdown list'))

            # B2 — mid-sentence bullet
            m = RE_BULLET_GLYPH.search(text)
            if m and m.start() > 0:
                issues.append(Issue('B2', line, trunc(text),
                                     'Bullet glyph appears mid-sentence'))

    return issues


def check_paragraphs(blocks: list[dict]) -> list[Issue]:
    issues = []
    seen_paragraphs: Counter = Counter()

    for b in blocks:
        text = b['text']
        line = b['line']

        if b['type'] == 'paragraph':
            # P1 — bare page number
            if RE_PAGE_NUMBER.match(text):
                issues.append(Issue('P1', line, text,
                                     'Paragraph is a bare page number'))

            # P2 — all-caps run
            if RE_CAPS_RUN.search(text):
                issues.append(Issue('P2', line, trunc(text),
                                     'Long all-caps run — possible un-spaced slogan from cover/imprint'))

            # P3 — repeated paragraph (track after first occurrence)
            key = text[:100]
            seen_paragraphs[key] += 1
            if seen_paragraphs[key] == 2:
                issues.append(Issue('P3', line, trunc(text),
                                     'Paragraph appears more than once (possible running header not stripped)'))

            # P4 — very short paragraph
            # Exempt trailing-colon lines ("We will:", "We want to:") — these are
            # legitimate bullet-list intro sentences, not orphan fragments.
            wc = len(text.split())
            if 1 < wc < 4 and not text.rstrip().endswith(':'):
                issues.append(Issue('P4', line, trunc(text),
                                     f'Very short paragraph ({wc} words) — possible orphaned fragment'))

    return issues


def check_encoding(lines: list[str]) -> list[Issue]:
    issues = []
    for lineno, line in enumerate(lines, 1):
        # E1 — replacement character
        if '�' in line:
            issues.append(Issue('E1', lineno, trunc(line),
                                 'Unicode replacement character (U+FFFD) — encoding error in source'))

        # E2 — raw CID token
        if RE_CID.search(line):
            issues.append(Issue('E2', lineno, trunc(line),
                                 'Raw (cid:N) token not decoded'))

        # E3 — control character
        if RE_CONTROL.search(line):
            issues.append(Issue('E3', lineno, trunc(line),
                                 'Non-printing control character'))

    return issues


def check_spacing(blocks: list[dict]) -> list[Issue]:
    issues = []
    for b in blocks:
        if b['type'] not in ('paragraph', 'bullet'):
            continue
        text = b['text']
        line = b['line']

        if RE_MISSING_SP_P.search(text):
            issues.append(Issue('S1', line, trunc(text),
                                 'Missing space after sentence-ending period'))

        if RE_MISSING_SP_C.search(text):
            issues.append(Issue('S2', line, trunc(text),
                                 'Missing space after comma'))

        if RE_CAPS_FUSED.search(text):
            issues.append(Issue('S3', line, trunc(text),
                                 'Possible fused ALL-CAPS words'))

        m = RE_DOUBLE_WORD.search(text)
        if m:
            issues.append(Issue('S4', line, trunc(text),
                                 f'Repeated consecutive word: "{m.group(1)} {m.group(1)}"'
                                 ' — common column-boundary extraction artefact'))

    return issues


def check_imprint_and_layout(blocks: list[dict]) -> list[Issue]:
    """
    I2 — Attribution block garbling: two-column foreword signatures collapsed
         into a single line.  When two authors sign a joint foreword side-by-side,
         a naive two-column extractor reads their roles interleaved, producing
         strings like "Leader of the Leader of the" or "Deputy Leader Deputy Leader".
    """
    issues = []
    for b in blocks:
        if b['type'] not in ('paragraph', 'bullet', 'heading'):
            continue
        if RE_ATTR_DOUBLE.search(b['text']):
            issues.append(Issue('I2', b['line'], trunc(b['text']),
                                 'Repeated leadership title in one line — two-column foreword signature '
                                 'likely garbled (two authors merged into one paragraph)'))
    return issues


def check_vertical_fragments(blocks: list[dict]) -> list[Issue]:
    """
    V-series: detect artefacts from vertical running headers and decorative
    letter fragments that older designed PDFs produce.

    V1  Repeated single/double-letter paragraph (likely vertical header char)
    V2  Paragraph composed entirely of spaced single characters ("P y W b A m")
    V3  Improbable single-character standalone paragraph
    """
    issues: list[Issue] = []
    # Track single/double-letter paragraphs for repetition check
    short_letter_counts: Counter = Counter()

    RE_SPACED_INITIALS = re.compile(r'^([A-Za-z]\s){2,}[A-Za-z]?\s*$')
    RE_SINGLE_CHAR = re.compile(r'^[A-Za-z]$')

    for b in blocks:
        if b['type'] != 'paragraph':
            continue
        text = b['text'].strip()
        line = b['line']

        # V3 — single character paragraph
        if RE_SINGLE_CHAR.match(text):
            issues.append(Issue('V3', line, text,
                                 'Improbable single-character paragraph — likely vertical header fragment'))
            short_letter_counts[text] += 1
            continue

        # V2 — spaced initials pattern: "P y W b A m S m m"
        if RE_SPACED_INITIALS.match(text) and len(text.split()) >= 3:
            issues.append(Issue('V2', line, trunc(text),
                                 'Paragraph composed of spaced single characters — '
                                 'likely vertical running title extracted character-by-character'))
            continue

        # Track 1–2 letter words as possible V1 candidates
        words = text.split()
        if len(words) <= 2 and all(len(w) <= 2 and w.isalpha() for w in words):
            short_letter_counts[text] += 1

    # V1 — repeated short-letter paragraphs (appears 3+ times)
    for frag, count in short_letter_counts.items():
        if count >= 3:
            issues.append(Issue('V1', 0, repr(frag),
                                 f'Short letter fragment appears {count} times — '
                                 'likely a repeating vertical running-header character'))

    return issues


# Reading-order constants
_ORPHAN_RATIO_THRESHOLD = 0.20   # > 20% orphan fragments → suspect reading order


def check_reading_order(blocks: list[dict]) -> list[Issue]:
    """
    R-series: checks that distinguish reading-order quality from coverage.

    A file can have 100% word coverage but still have poor reading order
    (e.g. interleaved left/right columns from a spread PDF).

    R1  Repeated adjacent words within a single paragraph at likely column join
        (same underlying data as S4 but surfaced here as a reading-order signal)
    R2  Bullet glyph embedded mid-prose paragraph
        (same underlying data as B2 but surfaced in reading-order section)
    R3  High ratio of very-short orphan fragments to total paragraphs
        (≥ 20% orphans suggests column interleaving even if word count is healthy)
    """
    issues: list[Issue] = []

    total_paras  = sum(1 for b in blocks if b['type'] == 'paragraph')
    orphan_count = 0

    for b in blocks:
        text = b['text']
        line = b['line']

        if b['type'] == 'paragraph':
            # R1 — repeated adjacent words within paragraph (column join artefact)
            m = RE_DOUBLE_WORD.search(text)
            if m:
                issues.append(Issue('R1', line, trunc(text),
                                     f'Repeated word "{m.group(1)}" in paragraph — '
                                     'possible column-join reading-order artefact'))

            # R2 — bullet glyph mid-prose
            gm = RE_BULLET_GLYPH.search(text)
            if gm and gm.start() > 0:
                issues.append(Issue('R2', line, trunc(text),
                                     'Bullet glyph appears mid-prose — '
                                     'possible reading-order interleaving from spread PDF'))

            # Count orphan fragments for R3
            wc = len(text.split())
            if 1 <= wc <= 2 and not text.rstrip().endswith(':'):
                orphan_count += 1

    # R3 — orphan ratio
    if total_paras > 20 and orphan_count / total_paras >= _ORPHAN_RATIO_THRESHOLD:
        pct = orphan_count / total_paras * 100
        issues.append(Issue('R3', 0,
                             f'{orphan_count} orphan fragments / {total_paras} paragraphs ({pct:.0f}%)',
                             'High orphan-fragment ratio — likely reading-order problem '
                             '(check for interleaved columns even if word coverage looks healthy)'))

    return issues


def check_coverage(md_path: str, pdf_path: str) -> list[Issue]:
    """Compare word count of markdown against pdftotext output."""
    issues = []
    try:
        res = subprocess.run(
            ['pdftotext', pdf_path, '-'],
            capture_output=True, text=True, timeout=60
        )
        if res.returncode != 0:
            return issues
        pdf_wc = len(res.stdout.split())
    except Exception:
        return issues

    md_text = Path(md_path).read_text(encoding='utf-8', errors='replace')
    md_wc   = len(md_text.split())

    if pdf_wc == 0:
        return issues

    coverage = md_wc / pdf_wc * 100
    detail   = f"markdown={md_wc:,} words, pdftotext={pdf_wc:,} words, coverage={coverage:.1f}%"

    if coverage < 70:
        issues.append(Issue('C1', 0, detail,
                             'Very low coverage — significant content may be missing'))
    elif coverage < 85:
        issues.append(Issue('C1', 0, detail,
                             'Low coverage — check for missing sections (note: footers/covers inflate pdftotext count)'))
    elif coverage > 150:
        issues.append(Issue('C1', 0, detail,
                             'Coverage exceeds 150% — possible double extraction or document contains '
                             'duplicated content (e.g. a reprint of another manifesto alongside Welsh content). '
                             'Note: pdftotext may under-count if fonts use custom encoding.'))
    else:
        # Healthy coverage — report as info only
        issues.append(Issue('C1', 0, detail, 'Coverage looks healthy'))

    return issues


# ── Main runner ───────────────────────────────────────────────────────────────

def run_qa(md_path: str, pdf_path: str | None = None,
           as_json: bool = False, strict: bool = False,
           allowlist: dict | None = None,
           merge_continuations: bool = False) -> int:
    """Run all checks and print results.  Returns exit code (0=ok, 1=issues)."""

    if allowlist is None:
        allowlist = {'phrases': [], 'heading_starts_allowed': [], 'disabled_codes': []}

    path = Path(md_path)
    if not path.exists():
        print(f"ERROR: markdown file not found: {md_path}", file=sys.stderr)
        return 2

    text  = path.read_text(encoding='utf-8', errors='replace')

    # Optional pre-processing: merge bullet continuation lines
    if merge_continuations:
        text = merge_bullet_continuations(text)

    lines  = text.splitlines()
    blocks = parse_markdown(text)

    disabled = set(allowlist.get('disabled_codes', []))
    all_issues: list[Issue] = []

    def _add(issues: list[Issue]):
        for iss in issues:
            # Skip entirely disabled codes
            if iss.code in disabled:
                continue
            # Skip if the excerpt matches an allowlisted phrase
            if _is_allowlisted(iss.excerpt, allowlist):
                continue
            # For H3, also check if the offending first word is explicitly allowed
            if iss.code == 'H3':
                first_word = iss.excerpt.split()[0].lower().rstrip('.,;:') if iss.excerpt.split() else ''
                if first_word in allowlist.get('heading_starts_allowed', []):
                    continue
            all_issues.append(iss)

    _add(check_encoding(lines))
    _add(check_headings(blocks))
    _add(check_bullets(blocks))
    _add(check_paragraphs(blocks))
    _add(check_spacing(blocks))
    _add(check_imprint_and_layout(blocks))
    _add(check_vertical_fragments(blocks))
    _add(check_reading_order(blocks))

    if pdf_path:
        _add(check_coverage(md_path, pdf_path))

    # ── JSON output ───────────────────────────────────────────────────────────
    if as_json:
        output = [
            {
                'code':     i.code,
                'severity': i.severity(),
                'line':     i.line,
                'excerpt':  i.excerpt,
                'detail':   i.detail,
            }
            for i in all_issues
        ]
        print(json.dumps(output, indent=2))
        return 1 if strict and any(i.severity() in ('error', 'warning') for i in all_issues) else 0

    # ── Human-readable output ─────────────────────────────────────────────────
    errors   = [i for i in all_issues if i.severity() == 'error']
    warnings = [i for i in all_issues if i.severity() == 'warning']
    infos    = [i for i in all_issues if i.severity() == 'info']

    # Reading-order summary (separate dimension from coverage)
    coverage_issues = [i for i in all_issues if i.code == 'C1']
    ro_issues       = [i for i in all_issues if i.code.startswith('R')]
    struct_issues   = [i for i in all_issues
                       if not i.code.startswith('R') and not i.code == 'C1']

    print(f"\n{bold('QA report:')} {path.name}")
    print(f"{'─'*70}")

    # ── Reading-order scorecard ───────────────────────────────────────────────
    def _scorecard_line(label: str, issues: list[Issue], good_msg: str):
        if not issues:
            print(f"  {green('✓')}  {label:22}  {green(good_msg)}")
        else:
            worst = max(issues, key=lambda i: ['info','warning','error'].index(i.severity()))
            sym   = red('✗') if worst.severity() == 'error' else yellow('!')
            codes = ', '.join(f"[{i.code}]" for i in issues[:4])
            print(f"  {sym}  {label:22}  {codes}")

    cov_issues_real = [i for i in coverage_issues if 'healthy' not in i.detail]
    _scorecard_line("Coverage",      cov_issues_real, "healthy")
    _scorecard_line("Reading order", ro_issues,       "looks OK")
    struct_warn_err = [i for i in struct_issues if i.severity() in ('error','warning')]
    _scorecard_line("Markdown structure", struct_warn_err, "looks OK")
    print()

    if not all_issues:
        print(green("  ✓ No issues found"))
        print()
        return 0

    def print_group(label: str, colour_fn, issues: list[Issue]):
        if not issues:
            return
        print(f"\n  {colour_fn(bold(label))}  ({len(issues)})")
        for i in sorted(issues, key=lambda x: x.line):
            loc  = f"line {i.line}" if i.line > 0 else "overall"
            code = f"[{i.code}]"
            print(f"    {colour_fn(code)}  {dim(loc)}")
            print(f"         {trunc(i.excerpt, 100)}")
            if i.detail:
                print(f"         {dim(i.detail)}")

    print_group('ERRORS',   red,    errors)
    print_group('WARNINGS', yellow, warnings)
    print_group('INFO',     dim,    infos)

    print(f"\n{'─'*70}")
    total = len(all_issues)
    summary_parts = []
    if errors:   summary_parts.append(red(f"{len(errors)} error{'s' if len(errors)>1 else ''}"))
    if warnings: summary_parts.append(yellow(f"{len(warnings)} warning{'s' if len(warnings)>1 else ''}"))
    if infos:    summary_parts.append(f"{len(infos)} info")
    print(f"  {total} issue{'s' if total != 1 else ''}:  {',  '.join(summary_parts)}")
    print()

    has_actionable = bool(errors or warnings)
    return 1 if (strict and has_actionable) else 0


def main():
    global USE_COLOUR

    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('markdown', help='Path to extracted Markdown file')
    parser.add_argument('--pdf',    metavar='FILE',
                        help='Original PDF (enables coverage check)')
    parser.add_argument('--json',   dest='as_json', action='store_true',
                        help='Output JSON')
    parser.add_argument('--strict', action='store_true',
                        help='Exit with code 1 if any errors/warnings found')
    parser.add_argument('--no-colour', dest='no_colour', action='store_true',
                        help='Disable ANSI colour')
    parser.add_argument('--allowlist', metavar='FILE',
                        help='Path to qa_allowlist.yaml (default: looks for '
                             'qa_allowlist.yaml next to this script)')
    parser.add_argument('--no-allowlist', dest='no_allowlist', action='store_true',
                        help='Disable allowlist loading entirely')
    parser.add_argument('--merge-continuations', dest='merge_continuations',
                        action='store_true',
                        help='Pre-merge bullet continuation lines before running checks '
                             '(suppresses false B4 warnings on split list items)')
    args = parser.parse_args()

    if args.no_colour or args.as_json:
        USE_COLOUR = False

    # Resolve allowlist
    allowlist: dict = {'phrases': [], 'heading_starts_allowed': [], 'disabled_codes': []}
    if not args.no_allowlist:
        allowlist_path = args.allowlist
        if allowlist_path is None:
            # Auto-discover next to this script
            candidate = Path(__file__).parent / 'qa_allowlist.yaml'
            if candidate.exists():
                allowlist_path = str(candidate)
        allowlist = load_allowlist(allowlist_path)

    sys.exit(run_qa(args.markdown, pdf_path=args.pdf,
                    as_json=args.as_json, strict=args.strict,
                    allowlist=allowlist,
                    merge_continuations=args.merge_continuations))


if __name__ == '__main__':
    main()
