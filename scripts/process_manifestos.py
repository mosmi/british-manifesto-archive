#!/usr/bin/env python3
"""
process_manifestos.py

Adds YAML frontmatter and normalises formatting for manifesto .md files.

By default it uses a local, deterministic cleaner (regex-based) that needs NO
API key and preserves all body text verbatim. The Claude API can still be used
for higher-fidelity cleaning via --use-api.

Usage:
  python process_manifestos.py --sample               # representative sample
  python process_manifestos.py --all                  # all files
  python process_manifestos.py --file path/to/file.md # single file
  python process_manifestos.py --sample --dry-run     # validate only, no writes
  python process_manifestos.py --sample --use-api     # use Claude API instead

Optional (only for --use-api):  ANTHROPIC_API_KEY environment variable
"""

import json
import os
import re
import sys
import time
import argparse
from pathlib import Path

try:
    import anthropic  # only needed for the optional --use-api path
except ImportError:
    anthropic = None


# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────

MANIFESTO_ROOT = Path(__file__).parent
REFERENCE_DATA_PATH = MANIFESTO_ROOT / "reference-data.json"

FOLDER_TO_PARTY_ID = {
    # GB-wide parties
    "conservative-manifesto":         "conservative",
    "labour-manifesto":               "labour",
    "lib-dem-manifesto":              "liberal",
    "green-manifesto":                "green",
    "loony-party-manifesto":          "loony",
    "bnp-manifesto":                  "bnp",
    "brexit-party-manifesto":         "brexit-party",
    "co-operative-party-manifesto":   "co-operative",
    "reform-manifesto":               "reform",
    "respect-manifesto":              "respect",
    "ukip-manifesto":                 "ukip",
    "pirate-manifesto":               "pirate",
    "nha-manifesto":                  "nha",
    "womens-equality-party-manifesto":"womens-equality",
    "workers-party-manifesto":        "workers-party",
    # Scottish parties
    "snp-manifesto":                  "snp",
    "scottish-conservative-manifesto":"scottish-conservative",
    "scottish-labour-manifesto":      "scottish-labour",
    "scottish-lib-dem-manifesto":     "scottish-lib-dem",
    "scottish-greens-manifesto":      "scottish-greens",
    "scottish-socialist-manifesto":   "scottish-socialist",
    # Welsh parties
    "plaid-manifesto":                "plaid",
    "gwlad-gwlad-manifesto":          "gwlad-gwlad",
    "welsh-conservative-manifesto":   "welsh-conservative",
    "welsh-labour-manifesto":         "welsh-labour",
    "welsh-lib-dem-manifesto":        "welsh-lib-dem",
    # Northern Ireland parties
    "alliance-manifesto":             "alliance",
    "dup-manifesto":                  "dup",
    "green-ni-manifesto":             "green-ni",
    "conservative-ni-manifesto":      "conservative-ni",
    "sdlp-manifesto":                 "sdlp",
    "sinn-fein-manifesto":            "sinn-fein",
    "tuv-manifesto":                  "tuv",
    "uup-manifesto":                  "uup",
}

# Months that appear in filenames for dual-election years
DUAL_ELECTION_MONTHS = {"january", "december", "february", "october"}

# Files matching any of these substrings (case-insensitive) are not general
# election manifestos and should be skipped.
EXCLUDE_FILENAME_SUBSTRINGS = [
    "assembly",
    "european",
    "qa-report",
    "qa_report",
    "google version",
    "google-version",
    "revised",
    "_fixed",
    "_from_page_",
    "_restart",
    " v2.",
    " v46.",
]

SECTIONS_TAXONOMY = [
    "economy",
    "taxation",
    "health",
    "education",
    "housing",
    "immigration",
    "defence",
    "foreign-policy",
    "environment",
    "transport",
    "law-and-order",
    "welfare",
    "democracy-and-constitution",
    "agriculture",
    "energy",
    "devolution",
    "science-and-technology",
    "local-government",
]

# Representative sample covering the full range of parties, eras, and formatting variation
SAMPLE_FILES = [
    # GB-wide — various eras and foreword styles
    "conservative-manifesto/2024-conservative-manifesto.md",
    "conservative-manifesto/1979-conservative-manifesto.md",
    "conservative-manifesto/1900-conservative-manifesto.md",
    "labour-manifesto/2017-labour-manifesto.md",
    "labour-manifesto/1945-labour-manifesto.md",
    "lib-dem-manifesto/2019-liberal-manifesto.md",   # has Table of Contents artefact
    "green-manifesto/2015-green-manifesto.md",
    "loony-party-manifesto/2015-monster-raving-loony-party-manifesto.md",
    # Regional / devolved parties
    "snp-manifesto/2015-snp-manifesto.md",
    "plaid-manifesto/2019-plaid-manifesto.md",
    # Northern Ireland parties
    "sinn-fein-manifesto/sinn_fein_2019_manifesto_english_only.md",  # underscore names
    "dup-manifesto/2017-dup-manifesto.md",
    # Non-standard party-first filename
    "respect-manifesto/respect-2005-manifesto.md",
]

DEFAULT_MODEL = "claude-sonnet-4-6"
MAX_TOKENS    = 16000

# Nice display names for the canonical H1 title (falls back to party_name).
DISPLAY_NAMES = {
    "conservative":          "Conservative Party",
    "labour":                "Labour Party",
    "liberal":               "Liberal Democrats",
    "green":                 "Green Party",
    "loony":                 "Official Monster Raving Loony Party",
    "bnp":                   "British National Party",
    "brexit-party":          "Brexit Party",
    "co-operative":          "Co-operative Party",
    "reform":                "Reform UK",
    "respect":               "Respect Party",
    "ukip":                  "UK Independence Party",
    "pirate":                "Pirate Party UK",
    "nha":                   "National Health Action Party",
    "womens-equality":       "Women's Equality Party",
    "workers-party":         "Workers Party of Britain",
    "snp":                   "Scottish National Party",
    "scottish-conservative": "Scottish Conservative Party",
    "scottish-labour":       "Scottish Labour Party",
    "scottish-lib-dem":      "Scottish Liberal Democrats",
    "scottish-greens":       "Scottish Green Party",
    "scottish-socialist":    "Scottish Socialist Party",
    "plaid":                 "Plaid Cymru",
    "gwlad-gwlad":           "Gwlad",
    "welsh-conservative":    "Welsh Conservative Party",
    "welsh-labour":          "Welsh Labour",
    "welsh-lib-dem":         "Welsh Liberal Democrats",
    "alliance":              "Alliance Party",
    "dup":                   "Democratic Unionist Party",
    "green-ni":              "Green Party Northern Ireland",
    "conservative-ni":       "Northern Ireland Conservatives",
    "sdlp":                  "Social Democratic and Labour Party",
    "sinn-fein":             "Sinn Féin",
    "tuv":                   "Traditional Unionist Voice",
    "uup":                   "Ulster Unionist Party",
}

# Keyword sets used by the local (no-API) section tagger. A topic is tagged
# when its keywords occur often enough across the manifesto body.
SECTION_KEYWORDS = {
    "economy":                    ["economy", "economic", "growth", "gdp", "inflation", "deficit", "borrowing", "wages", "productivity", "business", "investment", "industry", "jobs", "employment", "trade", "fiscal"],
    "taxation":                   ["tax", "taxes", "taxation", "income tax", "vat", "national insurance", "corporation tax", "duty", "levy", "council tax", "capital gains", "inheritance tax"],
    "health":                     ["nhs", "health", "hospital", "gp", "doctors", "nurses", "patients", "mental health", "social care", "a&e", "ambulance", "waiting list"],
    "education":                  ["education", "schools", "pupils", "teachers", "students", "university", "universities", "tuition", "curriculum", "apprenticeship", "childcare", "nursery", "college", "skills"],
    "housing":                    ["housing", "homes", "house building", "homelessness", "rent", "renters", "mortgage", "affordable homes", "social housing", "landlords", "tenants", "planning"],
    "immigration":                ["immigration", "migrants", "migration", "asylum", "refugees", "borders", "visa", "deportation", "small boats", "citizenship"],
    "defence":                    ["defence", "armed forces", "military", "army", "navy", "raf", "nato", "nuclear deterrent", "trident", "veterans", "soldiers"],
    "foreign-policy":             ["foreign", "international", "diplomacy", "overseas", "aid", "united nations", "commonwealth", "europe", "european union", "brexit", "treaty", "sanctions", "embassy"],
    "environment":                ["environment", "climate", "carbon", "emissions", "pollution", "nature", "wildlife", "biodiversity", "recycling", "net zero", "conservation", "green"],
    "transport":                  ["transport", "railways", "rail", "roads", "buses", "cycling", "hs2", "motorway", "aviation", "airports", "public transport", "traffic"],
    "law-and-order":              ["crime", "police", "policing", "justice", "courts", "prison", "prisons", "sentencing", "antisocial", "terrorism", "law and order", "offenders"],
    "welfare":                    ["welfare", "benefits", "universal credit", "pensions", "pensioners", "poverty", "disability", "social security", "child benefit", "state pension", "unemployment benefit"],
    "democracy-and-constitution": ["democracy", "constitution", "parliament", "voting", "electoral", "referendum", "house of lords", "monarchy", "human rights", "freedom of", "electoral reform", "proportional representation"],
    "agriculture":                ["agriculture", "farming", "farmers", "farms", "rural", "fisheries", "fishing", "countryside", "food production", "livestock", "crops"],
    "energy":                     ["energy", "electricity", "gas", "oil", "renewable", "renewables", "wind power", "solar", "nuclear power", "fuel", "power stations", "energy bills"],
    "devolution":                 ["devolution", "devolved", "scottish parliament", "senedd", "welsh assembly", "stormont", "independence", "self-government", "home rule"],
    "science-and-technology":     ["science", "technology", "research", "innovation", "digital", "broadband", "artificial intelligence", "data", "internet", "tech", "cyber", "telecoms"],
    "local-government":           ["local government", "councils", "local authorities", "mayors", "devolved powers", "town halls", "council services", "local democracy", "communities"],
}


# ─────────────────────────────────────────────────────────────
# Reference data
# ─────────────────────────────────────────────────────────────

def load_reference_data() -> dict:
    with open(REFERENCE_DATA_PATH, encoding="utf-8") as f:
        records = json.load(f)
    return {(r["election_id"], r["party_id"]): r for r in records}


# ─────────────────────────────────────────────────────────────
# Filename parsing
# ─────────────────────────────────────────────────────────────

def is_excluded(path: Path) -> bool:
    """Return True if this file should be skipped (non-election or draft file)."""
    name_lower = path.name.lower()
    return any(sub in name_lower for sub in EXCLUDE_FILENAME_SUBSTRINGS)


def parse_filename(path: Path) -> tuple[str, str]:
    """
    Returns (election_id, party_id) from folder name and filename.

    Handles three filename conventions:
      Standard:    {year}-{party}-manifesto.md
                   e.g. 1974-february-labour-manifesto.md → ("1974-february", "labour")
      Party-first: {party}-{year}-manifesto.md
                   e.g. respect-2005-manifesto.md → ("2005", "respect")
      Underscore:  {party}_{year}_manifesto_{suffix}.md
                   e.g. sinn_fein_2019_manifesto_english_only.md → ("2019", "sinn-fein")
    """
    folder   = path.parent.name
    party_id = FOLDER_TO_PARTY_ID.get(folder)
    if party_id is None:
        raise ValueError(f"Unknown folder '{folder}' in path: {path}")

    # Normalise underscores to hyphens to unify parsing
    stem_normalised = path.stem.replace("_", "-")

    # Extract year using regex (works regardless of position in filename)
    year_match = re.search(r"\b(19|20)\d{2}\b", stem_normalised)
    if not year_match:
        raise ValueError(f"Could not find a 4-digit year in filename: {path.name}")
    year = year_match.group()

    # Check for a dual-election month immediately after the year
    # e.g. "1974-february-..." or "1910-january-..."
    after_year  = stem_normalised[year_match.end():]
    month_match = re.match(r"-(" + "|".join(DUAL_ELECTION_MONTHS) + r")\b", after_year)
    election_id = f"{year}-{month_match.group(1)}" if month_match else year

    return election_id, party_id


# ─────────────────────────────────────────────────────────────
# Prompt construction
# ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are a precise document formatter specialising in UK political manifestos. "
    "You return only valid JSON — no commentary, no markdown code fences around it."
)

def build_user_prompt(content: str, party_leader: str | None, taxonomy: list[str]) -> str:
    if party_leader:
        leader_note = f"The party leader for this manifesto is {party_leader}."
    else:
        leader_note = (
            "This party had no formal leader at this election "
            "(they used a principal speakers system). "
            "If principal speakers are named in the text, treat them as you would a leader."
        )

    taxonomy_json = json.dumps(taxonomy, indent=2)

    return f"""Clean and normalise the manifesto markdown below. Return a JSON object with exactly two fields:

1. "clean_body"  – The cleaned markdown string (plain text, not wrapped in code fences).
2. "sections"    – An array of strings chosen ONLY from the taxonomy. Pick every topic that is genuinely covered; omit topics that are absent.

SECTIONS TAXONOMY (choose only from this list):
{taxonomy_json}

═══════════════════════════════════════════
CLEANING RULES — apply all of the following
═══════════════════════════════════════════

── Boilerplate removal ──────────────────────────────────────────────────────
• Remove source URL lines          e.g. *Source: http://...*
• Remove unofficial site notices   e.g. "THIS IS AN UNOFFICIAL SITE..."
• Remove archive breadcrumbs       e.g. "Home > Conservative Party Manifestos > 1979 > ..."
• Remove horizontal rules (---) that are part of the boilerplate header block
• Remove Table of Contents sections (numbered or linked lists near the top that serve as navigation)
• Remove any preamble quotes or constitutional extracts that precede the actual manifesto text (e.g. a boxed Liberal Democrat constitution preamble)
• Remove duplicate H1 headings (keep exactly one H1)

── Document title (H1) ─────────────────────────────────────────────────────
• Exactly one H1, at the very top of the document
• Format: "# [Party Name] Manifesto [Year]"
  Examples: "# Conservative Party Manifesto 1979"
            "# Labour Party Manifesto 2024"
            "# Liberal Democrats Manifesto 2019"
• Do NOT include slogans, subtitles, or election mottos in the H1

── Foreword / leader introduction ───────────────────────────────────────────
• {leader_note}
• If there is a leader's introduction — a foreword, personal statement, open letter,
  or declaration written in the leader's own voice before the main policy content —
  give it the heading "## Foreword", regardless of its original heading.
• A foreword is characterised by first-person narrative addressed to voters,
  NOT by policy pledges or programme tables.
• Keep the foreword text exactly as written in the original.
• At the end of the foreword, preserve the leader's signoff:
    *[Name]*
    *[Job Title]*          ← include this line only if a job title appears in the original
• If the ENTIRE document is a leader's declaration with no separate policy sections
  (common in 1900–1920s manifestos), treat the whole body as the foreword.
• If there is no foreword, do not invent one.

── Heading hierarchy ────────────────────────────────────────────────────────
• H1 (#)   – Document title only (exactly one, at the top)
• H2 (##)  – Major policy sections (and "Foreword" if present)
• H3 (###) – Subsections within a major section
• H4 (####)– Sub-subsections if genuinely needed
• Demote or promote headings throughout the document to enforce this hierarchy.
• Convert ALL-CAPS headings to Title Case  e.g. "## ECONOMIC POLICY" → "## Economic Policy"
• Remove numeric prefixes from section headings unless numbering is part of the title
  e.g. "## 1. Economy" → "## Economy"   but   "## Article 50" stays as-is

── Preserve everything else ─────────────────────────────────────────────────
• Keep ALL original manifesto text verbatim — do not paraphrase, summarise, or drop content
• Keep bullet points, numbered lists, bold, italic, and other inline formatting unchanged
• Keep any tables unchanged

═══════════════════════
MANIFESTO CONTENT BELOW
═══════════════════════
{content}"""


# ─────────────────────────────────────────────────────────────
# YAML frontmatter
# ─────────────────────────────────────────────────────────────

def build_frontmatter(record: dict, sections: list[str]) -> str:
    def yaml_str(v):
        # Quote strings that contain special YAML characters
        if v is None:
            return "null"
        if any(c in str(v) for c in [':', '#', '[', ']', '{', '}', ',', '&', '*', '?', '|', '>', '!', "'", '"', '%', '@', '`']):
            return f'"{v}"'
        return str(v)

    lines = ["---"]
    lines.append(f"election_year: {record['election_year']}")
    if record.get("election_month"):
        lines.append(f"election_month: {record['election_month']}")
    lines.append(f"party_id: {record['party_id']}")
    lines.append(f"party_name: {yaml_str(record['party_name'])}")
    lines.append(f"party_leader: {yaml_str(record.get('party_leader'))}")
    lines.append(f"political_spectrum: {record['political_spectrum']}")
    lines.append(f"victory: {str(record['victory']).lower()}")
    lines.append(f"government_outcome: {record['government_outcome']}")
    lines.append("sections:")
    for s in sections:
        lines.append(f"  - {s}")
    lines.append("---")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# Local (no-API) cleaning
# ─────────────────────────────────────────────────────────────

# Small words kept lowercase when title-casing an ALL-CAPS heading.
_TITLE_SMALL = {"a", "an", "and", "as", "at", "but", "by", "for", "from", "in",
                "nor", "of", "on", "or", "per", "the", "to", "via", "vs", "with"}

# Acronyms kept uppercase when title-casing an ALL-CAPS heading.
_ACRONYMS = {"NHS", "UK", "EU", "US", "USA", "UN", "EEC", "NATO", "BBC", "VAT",
             "GP", "GPS", "MP", "MPS", "MSP", "AM", "AI", "ID", "HS2", "VAT",
             "PR", "GDP", "NI", "EV", "EVS", "CO2", "R&D", "STEM"}

# Substrings (case-insensitive) that mark a whole line as archive boilerplate.
_BOILERPLATE_SUBSTRINGS = [
    "unofficial site",
    "not connected in any way",
    "seeking the official site",
    "manifesto text in a single long file",
]

_BREADCRUMB_RE   = re.compile(r"^\s*(home|.*\bmanifestos?)\s*>\s*$", re.IGNORECASE)
_YEAR_CRUMB_RE   = re.compile(r"^\s*(19|20)\d{2}\s*>", re.IGNORECASE)
_SOURCE_RE       = re.compile(r"^\s*[*_]*\s*source\s*:\s*https?://", re.IGNORECASE)
_ARCHIVE_RE      = re.compile(r"^\s*\*\*archive of .*manifestos\*\*\s*$", re.IGNORECASE)
_BARE_DOMAIN_RE  = re.compile(r"^\s*(www\.|https?://)\S+\s*$", re.IGNORECASE)
_PUBLISHER_RE    = re.compile(r"^\s*(published by|printed by|promoted by)\b", re.IGNORECASE)
_SYMBOL_LINE_RE  = re.compile(r"^\s*[*_~=]{2,}\s*$")
_HEADING_RE      = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
_HR_RE           = re.compile(r"^\s*([-*_])(?:\s*\1){2,}\s*$")
# Leading enumerators on headings, e.g. "1.", "1)", "I.", "a)", "4.1 -", "3 –".
_HEADING_PREFIX_RE = re.compile(
    r"^\s*(?:\d+(?:\.\d+)*|[ivxlcdm]+|[a-z])\s*[-–—.)]\s+", re.IGNORECASE)


def _is_title_h1(text: str) -> bool:
    """True if an H1's text looks like a manifesto title (vs a real section)."""
    t = text.strip().lower()
    if "manifesto" in t or "general election" in t:
        return True
    if re.match(r"^(19|20)\d{2}\b", t):
        return True
    return False

# Heading words that, on their own, indicate a leader's foreword/introduction.
_FOREWORD_HINTS = ["foreword", "introduction", "message from", "a message",
                   "letter from", "my vision", "preface", "leader's",
                   "leaders introduction", "opening statement"]


def _is_boilerplate_line(line: str) -> bool:
    low = line.lower()
    if any(sub in low for sub in _BOILERPLATE_SUBSTRINGS):
        return True
    if _SOURCE_RE.match(line) or _ARCHIVE_RE.match(line):
        return True
    if _BREADCRUMB_RE.match(line) or _YEAR_CRUMB_RE.match(line):
        return True
    if _BARE_DOMAIN_RE.match(line) or _PUBLISHER_RE.match(line):
        return True
    if _SYMBOL_LINE_RE.match(line):  # stray '****' / '___' artifacts
        return True
    return False


def _title_case_heading(text: str) -> str:
    """Title-case a heading only if it is essentially ALL CAPS."""
    letters = [c for c in text if c.isalpha()]
    if not letters or not all(c.isupper() for c in letters):
        return text  # leave mixed-case headings untouched

    words = text.split(" ")
    out = []
    for i, w in enumerate(words):
        if not w:
            out.append(w)
            continue
        low = w.lower()
        core = low.strip(".,:;!?()[]'\"")
        if core.upper() in _ACRONYMS:
            out.append(w.upper())
        elif core in _TITLE_SMALL and 0 < i < len(words) - 1:
            out.append(low)
        else:
            out.append(low[:1].upper() + low[1:])
    return " ".join(out)


def _strip_heading_prefix(text: str) -> str:
    """Drop a leading enumerator like '1.', 'I.', 'A)' from a heading."""
    stripped = _HEADING_PREFIX_RE.sub("", text, count=1)
    return stripped if stripped else text


def _surnames(leader: str | None) -> list[str]:
    if not leader:
        return []
    drop = {"the", "rt", "hon", "mr", "mrs", "ms", "dr", "sir", "dame", "td",
            "mp", "lord", "lady", "baroness", "rev"}
    parts = [p.strip(".,") for p in leader.split()]
    return [p for p in parts if len(p) > 2 and p.lower() not in drop]


def _mark_foreword(lines: list[str], leader: str | None) -> list[str]:
    """
    Heuristically label the leader's introduction as '## Foreword'.

    Two cases are handled conservatively:
      1. An existing heading that names a foreword/introduction (or the leader).
      2. An untitled intro block before the first H2 that ends in the leader's
         italic signoff (common in modern manifestos).
    Returns the (possibly) modified list. Never drops content.
    """
    surnames = _surnames(leader)

    # Case 1: relabel an existing heading.
    for i, line in enumerate(lines):
        m = _HEADING_RE.match(line)
        if not m or len(m.group(1)) == 1:
            continue
        htext = m.group(2).lower()
        hit = any(h in htext for h in _FOREWORD_HINTS) or \
              any(s.lower() in htext for s in surnames)
        if hit:
            return lines[:i] + ["## Foreword"] + lines[i + 1:]

    # Case 2: untitled intro ending in the leader's signoff before any heading.
    # Restricted to a signoff near the top so cover/preamble blocks (which push
    # the real foreword far down) don't trigger a misplaced heading.
    if surnames:
        first_heading = next((i for i, l in enumerate(lines)
                              if _HEADING_RE.match(l)), len(lines))
        limit = min(first_heading, 60)
        for i in range(limit):
            stripped = lines[i].strip()
            is_signoff = (stripped.startswith("*") or stripped.startswith("_")) and \
                         any(s.lower() in stripped.lower() for s in surnames)
            if is_signoff:
                # Insert a Foreword heading at the start of the intro block.
                insert_at = 0
                for j in range(i):
                    if lines[j].strip():
                        insert_at = j
                        break
                return lines[:insert_at] + ["## Foreword", ""] + lines[insert_at:]
    return lines


def _collapse_blanks(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text)


def local_clean(content: str, record: dict) -> tuple[str, list[str]]:
    """
    Deterministically clean a manifesto body and tag sections WITHOUT any API.

    Body paragraphs, lists, and tables pass through verbatim; only boilerplate
    lines are removed and heading lines are normalised. Returns (clean_body,
    sections).
    """
    party_id = record["party_id"]
    year     = record["election_year"]
    leader   = record.get("party_leader")
    display  = DISPLAY_NAMES.get(party_id) or record["party_name"]
    canonical_h1 = f"# {display} Manifesto {year}"

    lines = content.splitlines()

    # Pass 1: drop boilerplate lines.
    lines = [l for l in lines if not _is_boilerplate_line(l)]

    # NOTE: Tables of Contents are intentionally KEPT — they're a useful at-a-
    # glance overview of the manifesto's contents.

    # Pass 3: remove only title-like H1s (keep section H1s for now).
    def _is_title_line(l: str) -> bool:
        m = _HEADING_RE.match(l)
        return bool(m) and len(m.group(1)) == 1 and _is_title_h1(m.group(2))
    lines = [l for l in lines if not _is_title_line(l)]

    # Determine a level shift so the top body heading becomes H2. Some
    # manifestos use H1 for major sections; others use H2. Demote or promote
    # uniformly to enforce: major sections = H2, subsections = H3+.
    levels = [len(m.group(1)) for l in lines if (m := _HEADING_RE.match(l))]
    shift = (2 - min(levels)) if levels else 0

    # Pass 4: normalise headings (shift level, strip enumerator, title-case
    # ALL-CAPS) and drop header-zone horizontal rules.
    kept: list[str] = []
    reached_body = False
    for line in lines:
        m = _HEADING_RE.match(line)
        if m:
            level = min(6, max(2, len(m.group(1)) + shift))
            htext = _title_case_heading(_strip_heading_prefix(m.group(2)))
            kept.append("#" * level + " " + htext)
            reached_body = True
            continue

        if _HR_RE.match(line) and not reached_body:
            continue

        if line.strip():
            reached_body = True
        kept.append(line)

    # Pass 5: foreword labelling.
    kept = _mark_foreword(kept, leader)

    body = _collapse_blanks("\n".join(kept)).strip()
    clean_body = canonical_h1 + "\n\n" + body

    sections = _detect_sections(clean_body)
    return clean_body, sections


def _detect_sections(body: str) -> list[str]:
    """
    Tag taxonomy topics by keyword evidence across the body.

    A topic is tagged only when it is referenced by several DISTINCT keywords
    (not just one word repeated) and clears a frequency threshold that scales
    with document length, so long manifestos do not get tagged with everything.
    """
    low = body.lower()
    words = max(len(low.split()), 1)
    # Frequency threshold grows slowly with length: ~4 for short docs, more for
    # very long ones.
    freq_threshold = max(4, round(words / 1200))

    scored = []
    for topic in SECTIONS_TAXONOMY:
        total = 0
        distinct = 0
        for kw in SECTION_KEYWORDS.get(topic, []):
            c = low.count(kw)
            if c:
                distinct += 1
                total += c
        if distinct >= 2 and total >= freq_threshold:
            scored.append((topic, total))

    # Fallback for short / narrow manifestos: keep the strongest signals.
    if not scored:
        loose = [(t, sum(low.count(kw) for kw in SECTION_KEYWORDS.get(t, [])))
                 for t in SECTIONS_TAXONOMY]
        loose = [(t, s) for t, s in loose if s > 0]
        loose.sort(key=lambda x: x[1], reverse=True)
        scored = loose[:5]

    selected = {t for t, _ in scored}
    return [t for t in SECTIONS_TAXONOMY if t in selected]


# ─────────────────────────────────────────────────────────────
# Single-file processing
# ─────────────────────────────────────────────────────────────

def process_file(
    path: Path,
    ref_index: dict,
    client,
    model: str,
    dry_run: bool = False,
    use_api: bool = False,
) -> str:
    """Returns one of: 'ok', 'skipped', 'error', 'dry_run'."""

    content = path.read_text(encoding="utf-8")

    # Idempotency: skip files that already have frontmatter
    if content.lstrip().startswith("---"):
        print(f"  SKIP  already has frontmatter")
        return "skipped"

    # Parse election_id and party_id from path
    try:
        election_id, party_id = parse_filename(path)
    except ValueError as e:
        print(f"  ERROR  {e}")
        return "error"

    record = ref_index.get((election_id, party_id))
    if record is None:
        print(f"  ERROR  no reference data for election_id={election_id!r}, party_id={party_id!r}")
        return "error"

    print(f"  election_id={election_id}  party_id={party_id}  leader={record.get('party_leader')}")

    if dry_run:
        print(f"  DRY RUN  (no API call or file write)")
        return "dry_run"

    if use_api:
        clean_body, sections, err = _clean_via_api(content, record, client, model)
        if err:
            print(f"  ERROR  {err}")
            return "error"
    else:
        # Default: deterministic local cleaning (no API key required).
        clean_body, sections = local_clean(content, record)

    if not clean_body:
        print(f"  ERROR  empty clean_body")
        return "error"

    # Validate sections against taxonomy (drop any hallucinated values)
    valid_sections   = [s for s in sections if s in SECTIONS_TAXONOMY]
    invalid_sections = [s for s in sections if s not in SECTIONS_TAXONOMY]
    if invalid_sections:
        print(f"  WARN   dropped invalid section tags: {invalid_sections}")

    # ── Assemble and write ───────────────────────────────────
    frontmatter   = build_frontmatter(record, valid_sections)
    final_content = frontmatter + "\n\n" + clean_body.strip() + "\n"

    path.write_text(final_content, encoding="utf-8")
    print(f"  OK     sections: {valid_sections}")
    return "ok"


def _clean_via_api(content, record, client, model):
    """Optional Claude API cleaning. Returns (clean_body, sections, error)."""
    prompt = build_user_prompt(content, record.get("party_leader"), SECTIONS_TAXONOMY)
    try:
        response = client.messages.create(
            model=model,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as e:
        return "", [], f"API call failed: {e}"

    raw = response.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*\n?", "", raw)
    raw = re.sub(r"\n?```\s*$", "", raw)
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        return "", [], f"JSON parse failed: {e} | first 400 chars: {raw[:400]!r}"

    return result.get("clean_body", "").strip(), result.get("sections", []), None


# ─────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Add YAML frontmatter and normalise formatting for manifesto .md files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--sample",  action="store_true",
                       help="Process the representative sample files")
    group.add_argument("--all",     action="store_true",
                       help="Process all manifesto files")
    group.add_argument("--file",    type=str, metavar="PATH",
                       help="Process a single file (relative to manifesto root or absolute)")
    group.add_argument("--show-record", type=str, metavar="PATH",
                       help="Print the deterministic reference record for a file as JSON "
                            "and exit (no API call). Used by the subagent pipeline.")
    group.add_argument("--assemble", type=str, metavar="PATH",
                       help="Assemble final file from a cleaned body + section tags, writing "
                            "deterministic YAML frontmatter (no API call). Requires --body-file "
                            "and --sections. Used by the subagent pipeline.")
    parser.add_argument("--body-file", type=str, metavar="PATH",
                        help="Path to the cleaned body text (used with --assemble)")
    parser.add_argument("--sections", type=str, default="",
                        help="Comma-separated section tags (used with --assemble)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate filenames and reference data without writing")
    parser.add_argument("--use-api", action="store_true",
                        help="Use the Claude API for cleaning instead of the default "
                             "local deterministic cleaner (requires ANTHROPIC_API_KEY)")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"Claude model to use with --api (default: {DEFAULT_MODEL})")
    parser.add_argument("--delay", type=float, default=0.5,
                        help="Seconds to wait between API calls (default: 0.5)")
    args = parser.parse_args()

    # Load reference data
    ref_index = load_reference_data()

    # ── No-API helper modes (used by the subagent pipeline) ──────────
    if args.show_record or args.assemble:
        target = Path(args.show_record or args.assemble)
        path = target if target.is_absolute() else MANIFESTO_ROOT / target
        try:
            election_id, party_id = parse_filename(path)
        except ValueError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)
        record = ref_index.get((election_id, party_id))
        if record is None:
            print(f"ERROR: no reference data for election_id={election_id!r}, "
                  f"party_id={party_id!r}", file=sys.stderr)
            sys.exit(1)

        if args.show_record:
            out = dict(record)
            out["election_id"] = election_id
            out["taxonomy"] = SECTIONS_TAXONOMY
            print(json.dumps(out, indent=2, ensure_ascii=False))
            return

        # --assemble
        if not args.body_file:
            print("ERROR: --assemble requires --body-file", file=sys.stderr)
            sys.exit(1)
        body = Path(args.body_file).read_text(encoding="utf-8").strip()
        if not body:
            print("ERROR: body file is empty", file=sys.stderr)
            sys.exit(1)
        requested = [s.strip() for s in args.sections.split(",") if s.strip()]
        valid_sections   = [s for s in requested if s in SECTIONS_TAXONOMY]
        invalid_sections = [s for s in requested if s not in SECTIONS_TAXONOMY]
        if invalid_sections:
            print(f"WARN: dropped invalid section tags: {invalid_sections}", file=sys.stderr)
        frontmatter = build_frontmatter(record, valid_sections)
        final_content = frontmatter + "\n\n" + body + "\n"
        path.write_text(final_content, encoding="utf-8")
        print(f"OK assembled {path}  sections={valid_sections}")
        return

    print(f"Loaded {len(ref_index)} reference records.\n")

    # Resolve file list
    if args.sample:
        files = [MANIFESTO_ROOT / f for f in SAMPLE_FILES]
    elif args.all:
        files = sorted(
            p for p in MANIFESTO_ROOT.rglob("*.md")
            if p.parent.name in FOLDER_TO_PARTY_ID
            and not is_excluded(p)
            # Skip anything inside a hidden directory (e.g. .backup_*, .git)
            # so backups placed in the tree are never processed.
            and not any(part.startswith(".") for part in p.relative_to(MANIFESTO_ROOT).parts)
        )
    else:
        p = Path(args.file)
        files = [p if p.is_absolute() else MANIFESTO_ROOT / p]

    print(f"Files to process: {len(files)}")
    if args.dry_run:
        print("(dry-run mode — no writes)\n")
    elif args.use_api:
        print("(cleaning mode: Claude API)\n")
    else:
        print("(cleaning mode: local deterministic — no API key needed)\n")

    # Initialise API client only when explicitly requested
    client = None
    if args.use_api and not args.dry_run:
        if anthropic is None:
            print("ERROR: --use-api requires the 'anthropic' package (pip install anthropic).")
            sys.exit(1)
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("ERROR: --use-api requires the ANTHROPIC_API_KEY environment variable.")
            sys.exit(1)
        client = anthropic.Anthropic(api_key=api_key)

    # Process
    counts = {"ok": 0, "skipped": 0, "error": 0, "dry_run": 0}
    errors = []

    for path in files:
        rel = path.relative_to(MANIFESTO_ROOT) if path.is_absolute() else path
        print(f"\n→ {rel}")

        if not path.exists():
            print(f"  ERROR  file not found: {path}")
            counts["error"] += 1
            errors.append(str(rel))
            continue

        result = process_file(path, ref_index, client, args.model,
                               dry_run=args.dry_run, use_api=args.use_api)
        counts[result] = counts.get(result, 0) + 1

        if result == "error":
            errors.append(str(rel))

        if result == "ok" and args.use_api and args.delay > 0:
            time.sleep(args.delay)

    # Summary
    print(f"\n{'─' * 50}")
    print(f"Done.  ok={counts['ok']}  skipped={counts['skipped']}  "
          f"error={counts['error']}  dry_run={counts['dry_run']}")
    if errors:
        print(f"\nFiles with errors:")
        for e in errors:
            print(f"  {e}")


if __name__ == "__main__":
    main()
