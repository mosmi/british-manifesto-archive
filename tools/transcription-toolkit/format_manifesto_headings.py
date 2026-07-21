#!/usr/bin/env python3
"""
format_manifesto_headings.py — Automated heading & casing standardizer for manifesto draft.md files.

Rules applied:
1. Title (#): Single H1 for primary manifesto title in Title/Sentence Case.
2. Major Sections (##): H2 for Contents, Foreword, Introduction, Key Pledges, and major policy domain titles. Converts ALL-CAPS headers to Title/Sentence Case.
3. Subheadings (###): H3 for sub-questions, bold paragraph headers, and sub-policy topics.
4. Acronym Preservation: Keeps EU, NHS, UK, GPs, BAME, LGBTQ+, HS2, SNP, DUP, UUP, SDLP, WE, etc. in uppercase.
"""

import re
import sys
from pathlib import Path

# Acronyms to preserve in UPPERCASE
ACRONYMS = {
    'EU', 'NHS', 'UK', 'EEA', 'GPS', 'GP', 'BAME', 'LGBT', 'LGBTQ', 'LGBTQ+',
    'HS2', 'SNP', 'DUP', 'UUP', 'SDLP', 'WE', 'PBP', 'TUV', 'PUP', 'GPNI',
    'RSF', 'SEA', 'BNP', 'UKIP', 'OMRLP', 'TUSC', 'CPA', 'GDP', 'A&E', 'COVID'
}

def to_title_or_sentence_case(text: str) -> str:
    """Converts ALL-CAPS text to Title Case / Sentence Case while preserving known acronyms."""
    text = text.strip()
    if not text:
        return text

    # If it's not ALL-CAPS (has lowercase letters), keep existing mixed casing
    if re.search(r'[a-z]', text):
        return text

    words = text.split()
    converted_words = []

    for idx, w in enumerate(words):
        # Strip punctuation around word
        prefix = re.match(r'^[^\w]*', w).group(0)
        suffix = re.search(r'[^\w]*$', w).group(0)
        core = w[len(prefix):len(w)-len(suffix)] if len(w) >= len(prefix) + len(suffix) else w

        core_upper = core.upper()
        if core_upper in ACRONYMS:
            cased = core_upper
        else:
            lower = core.lower()
            # Minor words in lowercase if not first word
            if idx > 0 and lower in {'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 'to', 'from', 'by', 'of', 'in', 'with'}:
                cased = lower
            else:
                cased = lower.capitalize()

        converted_words.append(f"{prefix}{cased}{suffix}")

    # Ensure first word is always capitalized
    res = ' '.join(converted_words)
    if res and res[0].islower():
        res = res[0].upper() + res[1:]

    return res

def format_draft_headings(content: str) -> str:
    """Formats markdown headings and title casing according to project guidelines."""
    lines = content.splitlines()
    if not lines:
        return content

    new_lines = []
    h1_found = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Skip empty lines or horizontal rules
        if not stripped or stripped.startswith('---'):
            new_lines.append(line)
            continue

        # Rule 1: H1 Title
        if stripped.startswith('# ') and not h1_found:
            h1_found = True
            raw_title = stripped[2:].strip()
            cased_title = to_title_or_sentence_case(raw_title)
            new_lines.append(f"# {cased_title}")
            continue

        # Convert remaining H1s to H2s if more than one H1 exists
        if stripped.startswith('# ') and h1_found:
            raw_title = stripped[2:].strip()
            cased_title = to_title_or_sentence_case(raw_title)
            new_lines.append(f"## {cased_title}")
            continue

        # Rule 3: H3, H4, H5, H6 Sub-sections (preserve exact heading depth #)
        h_match = re.match(r'^(#{2,6})\s+(.+)$', stripped)
        if h_match:
            hashes = h_match.group(1)
            raw_title = h_match.group(2).strip()
            cased_title = to_title_or_sentence_case(raw_title)
            new_lines.append(f"{hashes} {cased_title}")
            continue

        # Standalone ALL-CAPS lines (likely un-headed section titles)
        if len(stripped) < 80 and not stripped.endswith('.') and not stripped.startswith('-') and not stripped.startswith('*') and not stripped.startswith('>'):
            # Check if line is ALL-CAPS (or mostly uppercase)
            letters = [c for c in stripped if c.isalpha()]
            if letters and all(c.isupper() for c in letters):
                # Standard section titles
                if any(kw in stripped for kw in ['CONTENTS', 'FOREWORD', 'INTRODUCTION', 'PLEDGES', 'SUMMARY', 'SECTION', 'PAYING', 'EQUAL', 'SERVICES', 'FOREIGN', 'IMMIGRATION', 'CLIMATE', 'DEAL', 'VIOLENCE', 'DATA', 'OUR', 'POLICY', 'HEALTH', 'EDUCATION', 'HOUSING', 'WELFARE', 'TRANSPORT', 'RURAL', 'ENVIRONMENT', 'CRIME', 'JUSTICE', 'CONSTITUTION']):
                    cased = to_title_or_sentence_case(stripped)
                    if not h1_found and i < 5:
                        h1_found = True
                        new_lines.append(f"# {cased}")
                    else:
                        new_lines.append(f"## {cased}")
                    continue

        # Bold standalone question or sub-header: **What is...** or **Why does...**
        bold_match = re.match(r'^\s*\*\*(.+?)\*\*\s*$', stripped)
        if bold_match:
            b_text = bold_match.group(1).strip()
            if b_text.endswith('?') or len(b_text.split()) < 12:
                cased = to_title_or_sentence_case(b_text)
                new_lines.append(f"### {cased}")
                continue

        # Unhandled regular line
        new_lines.append(line)

    result = '\n'.join(new_lines)
    result = re.sub(r'\n{3,}', '\n\n', result).strip() + '\n'
    return result

def main():
    script_dir = Path(__file__).resolve().parent
    work_dir = script_dir / 'work'
    drafts = list(work_dir.glob('*/draft.md'))

    print(f"Scanning {len(drafts)} draft.md files under {work_dir}...")
    updated_count = 0

    for d in sorted(drafts):
        old_txt = d.read_text(encoding='utf-8', errors='ignore')
        new_txt = format_draft_headings(old_txt)

        if new_txt != old_txt:
            d.write_text(new_txt, encoding='utf-8')
            updated_count += 1

    print(f"Successfully formatted headings & casing in {updated_count} / {len(drafts)} draft.md files!")

if __name__ == '__main__':
    main()
