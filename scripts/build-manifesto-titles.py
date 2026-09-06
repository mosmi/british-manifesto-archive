#!/usr/bin/env python3
"""
build-manifesto-titles.py

Resolve a display title for each manifesto.md.

Priority:
  1. YAML document_title:
  2. Curated Westminster titles (Wikipedia lists for Labour / Conservative /
     Liberal–Lib Dem; 1979 Conservative uses the cover line)
  3. Distinctive heading / opening italic / bold / first non-generic H2
  4. The document's own generic H1 ("Natural Law Party Manifesto 1997")
  5. "{party_name} Manifesto {year}" from YAML — never "Published without a
     distinct title"

Writes data/manifesto-titles.json keyed by filesystem folder:

  { "title": "…", "source": "wikipedia"|"cover"|"yaml"|"h1"|…, "distinctive": true }

Usage:
  python3 scripts/build-manifesto-titles.py
  python3 scripts/build-manifesto-titles.py --stats
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFESTOS_DIR = ROOT / "manifestos"
CURATED = ROOT / "data" / "manifesto-titles-curated.json"
OUT = ROOT / "data" / "manifesto-titles.json"
YAML_PARTY_RE = re.compile(r"(?m)^party_name:\s*(?:['\"](.+?)['\"]|(.+?))\s*$")
YAML_YEAR_RE = re.compile(r"(?m)^election_year:\s*['\"]?(\d{4})")

FRONTMATTER_RE = re.compile(r"(?ms)\A---\s*\n(.*?)\n---\s*\n")
YAML_TITLE_RE = re.compile(
    r"(?m)^document_title:\s*(?:['\"](.+?)['\"]|(.+?))\s*$"
)
H1_RE = re.compile(r"(?m)^#\s+(.+?)\s*$")
H2_RE = re.compile(r"(?m)^##\s+(.+?)\s*$")
ITALIC_LINE_RE = re.compile(r"(?m)^\*(?!\*)([^*\n]+)\*\s*$")
BOLD_LINE_RE = re.compile(r"(?m)^\*\*(?!\*)([^*\n]+)\*\*\s*$")
GENERIC_MANIFESTO_H1_RE = re.compile(
    r"""(?ix)
    ^(?:the\s+)?
    .{0,80}?
    (?:party\s+)?manifesto
    (?:\s+(?:for|of|to))?\s+
    (?:the\s+)?
    (?:general\s+election\s+)?
    (?:february|feb|october|oct|june|may|july|december|dec)?\s*
    \d{4}
    \s*$
    """
)
GENERIC_H1_ALT_RE = re.compile(
    r"""(?ix)
    ^(?:general\s+election\s+)?manifesto(?:\s+of\s+the)?\s+.{0,60}?\d{4}\s*$
    |^\d{4}\s+.{0,60}?manifesto\s*$
    """
)

GENERIC_SECTIONS = {
    "foreword",
    "foreward",
    "preface",
    "introduction",
    "contents",
    "contents page",
    "cover page",
    "table of contents",
    "acknowledgements",
    "acknowledgments",
    "executive summary",
    "summary",
    "index",
    "glossary",
    "appendix",
    "notes",
    "endnotes",
    "bibliography",
    "references",
    "about this manifesto",
    "our pledges",
    "our pledge",
    "chapter 1",
    "chapter one",
    "part 1",
    "part i",
    "part one",
    "section 1",
    "section one",
    "peace",
    "economy",
    "environment",
    "education",
    "health",
    "housing",
    "defence",
    "defense",
    "welfare",
    "transport",
    "agriculture",
    "energy",
    "taxation",
    "immigration",
    "videos",
    "take",
    "home",
    "menu",
    "next",
    "back",
}

GENERIC_SECTION_PREFIXES = (
    "a message from",
    "message from",
    "contents",
    "chapter ",
    "part ",
    "section ",
    "appendix ",
)

JUNK_TITLE_RE = re.compile(
    r"""(?ix)
    liberal\s*/\s*sdp
    |published\s+(?:in\s+)?(?:january|february|march|april|may|june|july|august|september|october|november|december)
    |cover\s+page
    |general\s+election\s+(?:programme|program|manifesto)\s+of
    |(?:party\s+)?general\s+election\s+manifesto\s*$
    """
)


def strip_md_inline(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = text.replace("**", "").replace("__", "").replace("*", "").replace("_", "")
    return re.sub(r"\s+", " ", text).strip()


def is_generic_h1(text: str) -> bool:
    t = strip_md_inline(text)
    if not t:
        return True
    if GENERIC_MANIFESTO_H1_RE.match(t) or GENERIC_H1_ALT_RE.match(t):
        return True
    return False


def tidy_title(text: str) -> str:
    t = strip_md_inline(text).strip(" \t-:–—")
    t = re.sub(r"\s+", " ", t)
    m = re.match(r"(?i)^forew[oa]rd\s*[-–:]\s*(.+)$", t)
    if m:
        t = m.group(1).strip()
    return t


def is_junk_title(text: str) -> bool:
    t = tidy_title(text)
    if not t:
        return True
    if JUNK_TITLE_RE.search(t):
        return True
    if t.isupper() and len(t.split()) <= 2 and len(t) <= 12:
        return True
    return False


def is_generic_section(text: str) -> bool:
    t = tidy_title(text).lower().rstrip(".")
    if not t or t in GENERIC_SECTIONS:
        return True
    if any(t.startswith(p) for p in GENERIC_SECTION_PREFIXES):
        return True
    if re.match(r"^\d+\.(?:\d+\.)*\s+\S", t):
        return True
    if len(t.split()) > 18:
        return True
    return False


def opening_body(body: str) -> str:
    """Text between the first H1 (if any) and the first H2, else the first 40 lines."""
    h1 = H1_RE.search(body)
    start = h1.end() if h1 else 0
    h2 = H2_RE.search(body, start)
    chunk = body[start : h2.start() if h2 else start + 2500]
    return chunk


def accept(title: str | None) -> str | None:
    if not title or is_junk_title(title):
        return None
    return tidy_title(title) or None


def title_tokens(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r"[a-z0-9]+", (text or "").lower()))


def load_curated() -> dict[str, dict]:
    if not CURATED.is_file():
        return {}
    try:
        data = json.loads(CURATED.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    titles = data.get("titles") if isinstance(data, dict) else None
    return titles if isinstance(titles, dict) else {}


def yaml_field(fm: str, pattern: re.Pattern) -> str:
    m = pattern.search(fm)
    if not m:
        return ""
    return tidy_title(next((g for g in m.groups() if g), "") or "")


def extract_from_markdown(raw: str) -> tuple[str | None, str | None, bool]:
    fm = FRONTMATTER_RE.search(raw)
    body = raw
    party_name = ""
    year = ""
    if fm:
        yaml_title = YAML_TITLE_RE.search(fm.group(1))
        if yaml_title:
            title = accept(yaml_title.group(1) or yaml_title.group(2) or "")
            if title:
                return title, "yaml", not is_generic_h1(title)
        party_name = yaml_field(fm.group(1), YAML_PARTY_RE)
        year = yaml_field(fm.group(1), YAML_YEAR_RE)
        body = raw[fm.end() :]

    h1 = H1_RE.search(body)
    if h1:
        title = accept(h1.group(1))
        if title and not is_generic_h1(title) and not is_generic_section(title):
            return title, "h1", True

    open_chunk = opening_body(body)
    italic = ITALIC_LINE_RE.search(open_chunk)
    if italic:
        title = accept(italic.group(1))
        if title and not is_generic_section(title) and not is_generic_h1(title):
            return title, "italic", True

    bold = BOLD_LINE_RE.search(open_chunk)
    if bold:
        title = accept(bold.group(1))
        if title and not is_generic_section(title) and not is_generic_h1(title):
            return title, "bold", True

    h2 = H2_RE.search(body)
    if h2:
        title = accept(h2.group(1))
        if title and not is_generic_section(title):
            h3 = re.search(r"(?m)^###\s+(.+?)\s*$", body[h2.end() : h2.end() + 400])
            if h2.group(1).rstrip().endswith(":") and h3:
                extra = accept(h3.group(1))
                if extra:
                    title = f"{title}: {extra}"
            return title, "h2", True

    if h1:
        generic = accept(h1.group(1))
        if generic and is_generic_h1(generic):
            return generic, "h1", False

    if party_name and year:
        return f"{party_name} Manifesto {year}", "constructed", False
    return None, None, False


def extract_title(raw: str, key: str, curated: dict[str, dict]) -> tuple[str | None, str | None, bool]:
    md_title, md_source, md_dist = extract_from_markdown(raw)
    if md_source == "yaml" and md_title:
        return md_title, md_source, md_dist

    cur = curated.get(key) if key else None
    ctitle = accept((cur or {}).get("title") or "")
    if ctitle:
        csrc = str(cur.get("source") or "wikipedia")
        cdist = not is_generic_h1(ctitle)
        if md_title and md_dist and title_tokens(md_title) == title_tokens(ctitle):
            return md_title, md_source, True
        if cdist:
            return ctitle, csrc, True
        if md_title and md_dist:
            return md_title, md_source, True
        return ctitle, csrc, False

    return md_title, md_source, md_dist


def iter_manifesto_md() -> list[Path]:
    return sorted(MANIFESTOS_DIR.rglob("manifesto.md"))


def key_for(path: Path) -> str:
    return str(path.parent.relative_to(MANIFESTOS_DIR)).replace("\\", "/")


def build() -> dict[str, dict]:
    curated = load_curated()
    out: dict[str, dict] = {}
    for path in iter_manifesto_md():
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError:
            continue
        key = key_for(path)
        title, source, distinctive = extract_title(raw, key, curated)
        out[key] = {
            "title": title,
            "source": source,
            "distinctive": bool(title) and bool(distinctive),
        }
    return out


def print_stats(data: dict[str, dict]) -> None:
    counts = Counter(v["source"] or "untitled" for v in data.values())
    titled = sum(1 for v in data.values() if v["title"])
    print(f"{len(data)} markdown files; {titled} titled; {len(data) - titled} untitled")
    for src, n in counts.most_common():
        print(f"  {src}: {n}")
    print("\nSample titled:")
    shown = 0
    for key, rec in data.items():
        if rec["title"]:
            print(f"  [{rec['source']}] {key}: {rec['title']}")
            shown += 1
            if shown >= 12:
                break
    print("\nSample untitled:")
    shown = 0
    for key, rec in data.items():
        if not rec["title"]:
            print(f"  {key}")
            shown += 1
            if shown >= 8:
                break


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stats", action="store_true")
    args = parser.parse_args()
    data = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(data)} records to {OUT.relative_to(ROOT)}")
    if args.stats:
        print_stats(data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
