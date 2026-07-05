#!/usr/bin/env python3
"""
transcribe_pipeline.py - Page-ledger transcription, audit, and repair runner.

This is the orchestration layer for two related workflows:

  1. Forward transcription of new PDFs into a reviewable draft.
  2. Retrospective audit of existing manifesto.md files against source PDFs.

It is intentionally human-gated. The script writes work artifacts, ledgers,
reports, reviewed drafts, and diffs, but it does not overwrite published
manifesto.md files.

Examples:
    python transcribe_pipeline.py audit manifestos/2024/labour/manifesto.md
    python transcribe_pipeline.py audit manifestos/1945/labour/manifesto.md --source-text /path/to/labour-1945.md
    python transcribe_pipeline.py repair manifestos/2024/labour/manifesto.md
    python transcribe_pipeline.py batch-audit --limit 10
    python transcribe_pipeline.py batch-audit-text --source-dir /path/to/iain-dale --party labour
    python transcribe_pipeline.py new manifestos/2024/labour/manifesto.pdf
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TOOLKIT_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLKIT_DIR.parents[1]
DEFAULT_WORK_ROOT = TOOLKIT_DIR / "work"

try:
    import pdfplumber  # type: ignore
except ImportError:
    sys.path.insert(0, str(TOOLKIT_DIR / "lib"))
    try:
        import pdfplumber  # type: ignore
    except ImportError:
        pdfplumber = None


# -----------------------------------------------------------------------------
# Regexes and simple text helpers

RE_MD_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
RE_TOC_HEADING = re.compile(r"^(contents|table of contents|index)\b", re.I)
RE_DOTTED_LEADER = re.compile(r"\.{2,}")
RE_TRAILING_PAGE_REF = re.compile(
    r"(?P<title>.*?)"
    r"(?:\s*\.{2,}\s*|\s{2,}|\s+)"
    r"(?P<page>\d{1,4})\s*$",
)
RE_INLINE_PAGE_REF = re.compile(r"\s+\d{1,4}\s+(?=[A-Z])")
RE_STANDALONE_PAGE = re.compile(r"^\s*\d{1,4}\s*$")
RE_BULLET = re.compile(r"[•●◆◉▪▸►]|\*\s+|-\s+")
RE_DOUBLE_WORD = re.compile(r"\b(\w{2,})\s+\1\b", re.I)
RE_DANGLING_END = re.compile(
    r"\b(the|a|an|at|in|of|for|by|with|to|from|on|into|and|or|but|"
    r"its|our|their|this|these|those|which|that|who|whom)\s*$",
    re.I,
)


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except Exception:
        return str(path)


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_cmd(cmd: list[str], timeout: int = 120) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError as e:
        return 127, "", str(e)
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"


def strip_frontmatter(md: str) -> tuple[str, str]:
    if md.startswith("---\n"):
        end = md.find("\n---", 4)
        if end != -1:
            fm_end = md.find("\n", end + 4)
            if fm_end != -1:
                return md[: fm_end + 1], md[fm_end + 1 :]
    return "", md


def normalize_words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9']+", text.lower())


def word_count(text: str) -> int:
    return len(text.split())


def clean_toc_line(line: str) -> str:
    """
    Remove page numbers and dotted leaders from one Contents/Table of Contents line.

    Keeps the item text because the Contents section is a useful overview of
    document structure. Examples:
      "Health and social care .......... 14" -> "Health and social care"
      "4. Education 22" -> "4. Education"
    """
    stripped = line.rstrip()
    prefix = ""
    body = stripped
    bullet = re.match(r"^(\s*(?:[-*]|\d+[.)])\s+)(.+)$", stripped)
    if bullet:
        prefix, body = bullet.group(1), bullet.group(2)

    if RE_STANDALONE_PAGE.match(body):
        return ""

    body = RE_DOTTED_LEADER.sub(" ", body).strip()
    body = RE_INLINE_PAGE_REF.sub("\n", body)
    cleaned_parts = []
    for part in body.splitlines():
        part = part.strip()
        m = RE_TRAILING_PAGE_REF.match(part)
        if m:
            title = m.group("title").rstrip(" .\t")
            if title and len(title.split()) <= 20:
                part = title
        cleaned_parts.append(part)
    body = "\n".join(p for p in cleaned_parts if p)
    return (prefix + body).rstrip()


def _toc_key(text: str) -> str:
    text = re.sub(r"^#{1,6}\s+", "", text.strip())
    text = re.sub(r"[*_`]+", "", text)
    text = clean_toc_line(text)
    text = re.sub(r"[^a-z0-9 ]+", " ", text.lower())
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_contents_sections(md_text: str) -> tuple[str, list[dict[str, Any]]]:
    """
    Return Markdown with Contents section page references stripped.

    Only edits lines in a section headed Contents/Table of Contents/Index.
    The section ends at the next heading at the same or higher level.
    """
    lines = md_text.splitlines()
    out = list(lines)
    changes: list[dict[str, Any]] = []
    in_toc = False
    toc_seen_titles: set[str] = set()
    toc_body_lines = 0

    for i, line in enumerate(lines):
        hm = RE_MD_HEADING.match(line.strip())
        if hm:
            title = hm.group(2).strip().strip("# ").strip()
            key = _toc_key(title)
            if in_toc and toc_body_lines >= 5 and key and key in toc_seen_titles:
                in_toc = False
            if RE_TOC_HEADING.match(title):
                in_toc = True
                toc_seen_titles = set()
                toc_body_lines = 0
                continue

        if not in_toc:
            continue

        cleaned = clean_toc_line(line)
        if cleaned != line.rstrip():
            out[i] = cleaned
            changes.append({
                "line": i + 1,
                "before": line,
                "after": cleaned,
            })
        key = _toc_key(cleaned or line)
        if key and not RE_TOC_HEADING.match(key):
            toc_seen_titles.add(key)
        if line.strip():
            toc_body_lines += 1

    return "\n".join(out).rstrip() + "\n", changes


def md_has_contents(md_text: str) -> bool:
    return any(
        RE_MD_HEADING.match(line.strip())
        and RE_TOC_HEADING.match(RE_MD_HEADING.match(line.strip()).group(2).strip())
        for line in md_text.splitlines()
    )


def extract_markdown_headings(md_text: str) -> list[str]:
    headings = []
    for line in md_text.splitlines():
        m = RE_MD_HEADING.match(line.strip())
        if m:
            headings.append(m.group(2).strip())
    return headings


def strip_markdown_syntax(text: str) -> str:
    text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.M)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"_(.*?)_", r"\1", text)
    text = re.sub(r"^\s*[-*]\s+", "", text, flags=re.M)
    return text


def heading_key(text: str) -> str:
    text = re.sub(r"[^a-z0-9 ]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def heading_matches_source(source_heading: str, md_heading_keys: set[str]) -> bool:
    key = heading_key(source_heading)
    if not key:
        return True
    if key in md_heading_keys:
        return True
    # Treat document title variants as equivalent:
    # "Labour Party General Election Manifesto 1945" vs
    # "Labour Party Manifesto 1945".
    year = re.search(r"\b(1[89]\d{2}|20\d{2})\b", key)
    if "manifesto" in key and year:
        for md_key in md_heading_keys:
            if "manifesto" in md_key and year.group(1) in md_key:
                source_words = set(key.split())
                md_words = set(md_key.split())
                if {"manifesto", year.group(1)} <= md_words and len(source_words & md_words) >= 3:
                    return True
    return False


def md_contents_page_number_clutter(md_text: str) -> list[dict[str, Any]]:
    _cleaned, changes = clean_contents_sections(md_text)
    return [c for c in changes if c["before"].strip()]


# -----------------------------------------------------------------------------
# PDF extraction and page profiling


@dataclass
class Candidate:
    method: str
    available: bool
    word_count: int = 0
    artifact_score: float = 0.0
    output_file: str | None = None
    error: str | None = None


@dataclass
class PageRecord:
    page_index: int
    width: float | None
    height: float | None
    rotation: int | None
    text_layer_words: int
    layout_class: str
    image_path: str | None
    candidates: list[Candidate]
    selected_candidate: str | None
    confidence: float
    status: str
    issues: list[dict[str, Any]]


def pdftotext_page(pdf: Path, page_index: int, flag: str | None = None) -> tuple[bool, str, str]:
    if shutil.which("pdftotext") is None:
        return False, "", "pdftotext not found"
    cmd = ["pdftotext", "-f", str(page_index + 1), "-l", str(page_index + 1)]
    if flag:
        cmd.append(flag)
    cmd += [str(pdf), "-"]
    code, out, err = run_cmd(cmd, timeout=60)
    return code == 0, out, err


def pdftotext_document(pdf: Path) -> str:
    if shutil.which("pdftotext") is None:
        return ""
    code, out, _err = run_cmd(["pdftotext", str(pdf), "-"], timeout=180)
    return out if code == 0 else ""


def pdfplumber_page_text(page: Any, layout: bool = False) -> str:
    if page is None:
        return ""
    try:
        return page.extract_text(layout=layout) or ""
    except Exception:
        return ""


def artifact_score(text: str) -> float:
    words = max(word_count(text), 1)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    double_words = len(RE_DOUBLE_WORD.findall(text))
    bullet_mid = sum(1 for ln in lines if RE_BULLET.search(ln[1:]))
    singletons = sum(1 for ln in lines if len(ln.split()) == 1 and len(ln) <= 3)
    raw_bullets = len(RE_BULLET.findall(text))
    return round(
        (double_words / words) * 5000
        + (bullet_mid / words) * 2000
        + (singletons / max(len(lines), 1)) * 20
        + (raw_bullets / words) * 100,
        2,
    )


def classify_page(page: Any, words: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    if page is None:
        return "blocked", [{"code": "PDF", "detail": "pdfplumber page unavailable"}]

    width = float(page.width)
    height = float(page.height)
    rotation = int(page.rotation or 0)
    word_total = len(words)

    if word_total == 0:
        return "image-only", [{"code": "TEXT_LAYER", "detail": "No extractable words on page"}]
    if word_total <= 5:
        return "sparse", [{"code": "SPARSE", "detail": "Very few extractable words on page"}]

    if rotation in (90, 270) or width > height * 1.35:
        issues.append({"code": "SPREAD", "detail": "Landscape/rotated page may contain spread or complex layout"})

    # Count large non-white rectangles as a sidebar/table/box hint.
    colored_boxes = 0
    for rect in getattr(page, "rects", []):
        fill = rect.get("non_stroking_color")
        if not fill:
            continue
        if (float(rect.get("x1", 0)) - float(rect.get("x0", 0)) < 50
                or float(rect.get("y1", 0)) - float(rect.get("y0", 0)) < 35):
            continue
        if isinstance(fill, (int, float)):
            vals = [float(fill)] * 3
        elif isinstance(fill, tuple) and len(fill) >= 3:
            vals = [float(fill[0]), float(fill[1]), float(fill[2])]
        else:
            vals = [1, 1, 1]
        if sum(vals) / len(vals) < 0.95:
            colored_boxes += 1
    if colored_boxes:
        issues.append({"code": "BOXES", "detail": f"{colored_boxes} large colored/sidebar-like rectangles detected"})

    buckets = Counter(int(w["x0"] // 25) * 25 for w in words if str(w.get("text", "")).strip())
    significant = [x for x, n in buckets.items() if n >= max(3, word_total * 0.025)]
    significant.sort()
    groups: list[list[int]] = []
    for x in significant:
        if not groups or x - groups[-1][-1] > 50:
            groups.append([x])
        else:
            groups[-1].append(x)

    layout = "single-column"
    if len(groups) >= 3:
        layout = "three-column"
        issues.append({"code": "THREE_COLUMN", "detail": "Three or more x-origin clusters detected"})
    elif len(groups) == 2:
        layout = "two-column"

    if colored_boxes and layout == "single-column":
        layout = "sidebar-or-table"
    if issues and any(i["code"] == "SPREAD" for i in issues):
        layout = "spread-or-landscape"

    return layout, issues


def render_pdf_pages(pdf: Path, image_dir: Path, dpi: int = 144) -> list[Path]:
    image_dir.mkdir(parents=True, exist_ok=True)
    if shutil.which("pdftoppm") is None:
        return []
    prefix = image_dir / "page"
    code, _out, _err = run_cmd(["pdftoppm", "-png", "-r", str(dpi), str(pdf), str(prefix)], timeout=300)
    if code != 0:
        return []
    return sorted(image_dir.glob("page-*.png"))


def build_page_records(pdf: Path, work_dir: Path, render_pages: bool = True) -> list[PageRecord]:
    candidate_dir = work_dir / "pages"
    candidate_dir.mkdir(parents=True, exist_ok=True)
    images = render_pdf_pages(pdf, work_dir / "images") if render_pages else []
    image_by_index = {i: p for i, p in enumerate(images)}

    if pdfplumber is None:
        return [PageRecord(
            page_index=0,
            width=None,
            height=None,
            rotation=None,
            text_layer_words=0,
            layout_class="blocked",
            image_path=None,
            candidates=[],
            selected_candidate=None,
            confidence=0,
            status="blocked",
            issues=[{"code": "DEPENDENCY", "detail": "pdfplumber is not installed"}],
        )]

    records: list[PageRecord] = []
    with pdfplumber.open(str(pdf)) as doc:
        for idx, page in enumerate(doc.pages):
            try:
                words = page.extract_words(keep_blank_chars=False, y_tolerance=3, x_tolerance=3)
            except Exception:
                words = []

            layout, issues = classify_page(page, words)
            candidates: list[Candidate] = []
            raw_texts: dict[str, str] = {}

            for method, flag in [
                ("pdftotext", None),
                ("pdftotext-layout", "-layout"),
                ("pdftotext-raw", "-raw"),
            ]:
                ok, text, err = pdftotext_page(pdf, idx, flag)
                if ok:
                    out = candidate_dir / f"page-{idx:03d}.{method}.txt"
                    out.write_text(text, encoding="utf-8")
                    raw_texts[method] = text
                    candidates.append(Candidate(method, True, word_count(text), artifact_score(text), rel(out)))
                else:
                    candidates.append(Candidate(method, False, error=err[:200]))

            for method, layout_flag in [("pdfplumber", False), ("pdfplumber-layout", True)]:
                text = pdfplumber_page_text(page, layout=layout_flag)
                out = candidate_dir / f"page-{idx:03d}.{method}.txt"
                out.write_text(text, encoding="utf-8")
                raw_texts[method] = text
                candidates.append(Candidate(method, True, word_count(text), artifact_score(text), rel(out)))

            available = [c for c in candidates if c.available and c.word_count > 0]
            selected = min(available, key=lambda c: (c.artifact_score, abs(c.word_count - len(words)))) if available else None
            confidence = 0.0
            status = "accepted"
            if selected:
                confidence = max(0.0, min(1.0, 1.0 - selected.artifact_score / 50.0))
            else:
                status = "blocked"
                issues.append({"code": "NO_CANDIDATE", "detail": "No local text candidate produced words"})

            if layout in {"three-column", "spread-or-landscape", "sidebar-or-table", "image-only", "blocked"}:
                status = "needs-human"
            if selected and available:
                counts = [c.word_count for c in available]
                if max(counts) > 0 and min(counts) / max(counts) < 0.70:
                    status = "needs-human"
                    issues.append({"code": "CANDIDATE_DISAGREEMENT", "detail": "Candidate word counts differ by more than 30%"})
            if selected and selected.artifact_score >= 8:
                status = "needs-human"
                issues.append({"code": "ARTIFACT_SCORE", "detail": f"Selected candidate artifact score is {selected.artifact_score}"})

            records.append(PageRecord(
                page_index=idx,
                width=float(page.width),
                height=float(page.height),
                rotation=int(page.rotation or 0),
                text_layer_words=len(words),
                layout_class=layout,
                image_path=rel(image_by_index[idx]) if idx in image_by_index else None,
                candidates=candidates,
                selected_candidate=selected.method if selected else None,
                confidence=round(confidence, 3),
                status=status,
                issues=issues,
            ))

    return records


def assemble_new_draft(pdf: Path, page_records: list[PageRecord], work_dir: Path) -> Path:
    chunks: list[str] = []
    for page in page_records:
        selected = page.selected_candidate
        if not selected:
            chunks.append(f"\n<!-- Page {page.page_index + 1}: no selected text candidate -->\n")
            continue
        candidate = work_dir / "pages" / f"page-{page.page_index:03d}.{selected}.txt"
        text = read_text(candidate).strip() if candidate.exists() else ""
        if text:
            chunks.append(text)
    draft = work_dir / "draft.md"
    draft.write_text("\n\n".join(chunks).strip() + "\n", encoding="utf-8")
    return draft


# -----------------------------------------------------------------------------
# Audit checks


def run_qa_json(md: Path, pdf: Path | None) -> list[dict[str, Any]]:
    qa_script = TOOLKIT_DIR / "qa_check.py"
    cmd = [sys.executable, str(qa_script), str(md), "--json"]
    if pdf:
        cmd += ["--pdf", str(pdf)]
    code, out, _err = run_cmd(cmd, timeout=180)
    try:
        return json.loads(out)
    except Exception:
        return [{"code": "QA", "severity": "error", "line": 0, "excerpt": "", "detail": f"qa_check.py returned {code} but did not emit JSON"}]


def run_heading_check(pdf: Path, md: Path) -> dict[str, Any]:
    script = TOOLKIT_DIR / "check_headings.py"
    code, out, err = run_cmd(
        [sys.executable, str(script), str(pdf), str(md), "--size-threshold", "12"],
        timeout=180,
    )
    problems = []
    for line in out.splitlines():
        if any(marker in line for marker in ("TRUNCATED", "ALTERED", "NOT FOUND")):
            problems.append(line.strip())
    return {
        "exit_code": code,
        "problem_count": len(problems),
        "problems": problems[:200],
        "stdout_excerpt": out[-4000:],
        "stderr": err[-1000:],
    }


def detect_pdf_contents(pdf: Path) -> dict[str, Any]:
    result = {
        "present": False,
        "pages": [],
        "page_number_like_lines": 0,
        "error": None,
    }
    if pdfplumber is None:
        result["error"] = "pdfplumber unavailable"
        return result
    try:
        with pdfplumber.open(str(pdf)) as doc:
            for idx, page in enumerate(doc.pages[:8]):
                text = pdfplumber_page_text(page, layout=True)
                lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
                joined = "\n".join(lines)
                has_heading = bool(re.search(r"\b(contents|table of contents)\b", joined, re.I))
                numberish = sum(1 for ln in lines if clean_toc_line(ln) != ln.rstrip())
                if has_heading or numberish >= 4:
                    result["present"] = True
                    result["pages"].append(idx)
                    result["page_number_like_lines"] += numberish
    except Exception as e:
        result["error"] = str(e)
    return result


def summarize_status(issues: list[dict[str, Any]], page_records: list[PageRecord], repaired_possible: bool) -> str:
    if any(i.get("severity") == "error" for i in issues):
        return "blocked"
    if repaired_possible and not any(p.status in {"needs-human", "blocked"} for p in page_records):
        return "minor-auto-repair"
    if any(p.status in {"needs-human", "blocked"} for p in page_records):
        return "needs-human-review"
    if any(i.get("severity") == "warning" for i in issues):
        return "needs-human-review"
    return "passed"


def audit_text_source(
    md: Path,
    source_text: Path,
    work_root: Path = DEFAULT_WORK_ROOT,
    write_sidecar: bool = True,
) -> dict[str, Any]:
    md = md.resolve()
    source_text = source_text.resolve()
    if not md.exists():
        raise FileNotFoundError(f"Markdown file not found: {md}")
    if not source_text.exists():
        raise FileNotFoundError(f"Source text file not found: {source_text}")

    work_dir = work_dir_for(md, work_root)
    work_dir.mkdir(parents=True, exist_ok=True)

    md_raw = read_text(md)
    source_raw = read_text(source_text)
    _md_frontmatter, md_body = strip_frontmatter(md_raw)
    md_plain = strip_markdown_syntax(md_body)
    source_plain = strip_markdown_syntax(source_raw)

    md_words = normalize_words(md_plain)
    source_words = normalize_words(source_plain)
    md_counts = Counter(md_words)
    source_counts = Counter(source_words)
    overlap = sum((md_counts & source_counts).values())
    source_count = len(source_words)
    md_count = len(md_words)
    source_coverage = round(overlap / source_count * 100, 1) if source_count else None
    length_ratio = round(md_count / source_count * 100, 1) if source_count else None

    md_heading_keys = {heading_key(h) for h in extract_markdown_headings(md_body)}
    source_headings = extract_markdown_headings(source_raw)
    missing_headings = [h for h in source_headings if not heading_matches_source(h, md_heading_keys)]

    issues: list[dict[str, Any]] = []
    if source_coverage is None:
        issues.append({
            "code": "SOURCE_EMPTY",
            "severity": "error",
            "detail": "Source text contained no words after normalization.",
        })
    elif source_coverage < 98:
        issues.append({
            "code": "TEXT_SOURCE_COVERAGE",
            "severity": "warning",
            "detail": f"Only {source_coverage}% of normalized source words overlap with Markdown.",
        })
    if length_ratio is not None and not (95 <= length_ratio <= 105):
        issues.append({
            "code": "TEXT_LENGTH_RATIO",
            "severity": "warning",
            "detail": f"Markdown/source normalized word ratio is {length_ratio}% (target 95-105%).",
        })
    if missing_headings:
        issues.append({
            "code": "TEXT_SOURCE_HEADINGS",
            "severity": "warning",
            "detail": f"{len(missing_headings)} source headings are not present as Markdown headings.",
            "examples": missing_headings[:20],
        })

    status = "blocked" if any(i["severity"] == "error" for i in issues) else ("needs-human-review" if issues else "passed")
    ledger = {
        "schema_version": 1,
        "mode": "audit-text",
        "source_type": "golden-text",
        "status": status,
        "created_at": now_iso(),
        "markdown_path": rel(md),
        "source_text": rel(source_text),
        "work_dir": rel(work_dir),
        "markdown_sha256": sha256(md),
        "source_text_sha256": sha256(source_text),
        "word_counts": {
            "markdown_normalized": md_count,
            "source_normalized": source_count,
            "source_word_overlap": overlap,
            "source_coverage_percent": source_coverage,
            "markdown_to_source_ratio_percent": length_ratio,
        },
        "heading_check": {
            "source_heading_count": len(source_headings),
            "missing_heading_count": len(missing_headings),
            "missing_heading_examples": missing_headings[:100],
        },
        "issues": issues,
        "note": "Golden text audit compares normalized textual content, not page layout. Use for historical pre-PDF sources such as Iain Dale manifesto text.",
    }
    write_json(work_dir / "ledger.json", ledger)
    if write_sidecar:
        write_json(md.with_suffix(".audit.json"), ledger)
    return ledger


def work_dir_for(path: Path, work_root: Path) -> Path:
    try:
        key = path.resolve().relative_to(REPO_ROOT)
    except Exception:
        key = path.resolve()
    slug = "__".join(key.with_suffix("").parts)
    return work_root / slug


def audit_markdown(
    md: Path,
    pdf: Path | None = None,
    work_root: Path = DEFAULT_WORK_ROOT,
    render_pages: bool = True,
    write_sidecar: bool = True,
) -> dict[str, Any]:
    md = md.resolve()
    if pdf is None:
        pdf = md.with_name("manifesto.pdf")
    else:
        pdf = pdf.resolve()

    if not md.exists():
        raise FileNotFoundError(f"Markdown file not found: {md}")

    if not pdf.exists():
        ledger = {
            "schema_version": 1,
            "mode": "audit",
            "status": "source-missing",
            "created_at": now_iso(),
            "markdown_path": rel(md),
            "source_pdf": rel(pdf),
            "markdown_sha256": sha256(md),
            "source_pdf_sha256": None,
            "issues": [{
                "code": "SOURCE_MISSING",
                "severity": "error",
                "detail": "No sibling source PDF found; original document must be located before audit.",
            }],
            "pages": [],
        }
        if write_sidecar:
            write_json(md.with_suffix(".audit.json"), ledger)
        return ledger

    work_dir = work_dir_for(md, work_root)
    work_dir.mkdir(parents=True, exist_ok=True)

    page_records = build_page_records(pdf, work_dir, render_pages=render_pages)
    md_text = read_text(md)
    pdf_text = pdftotext_document(pdf)
    adjusted_pdf_text = pdf_text
    # Remove simple standalone TOC page-number tokens for adjusted coverage.
    adjusted_pdf_text = "\n".join(
        "" if RE_STANDALONE_PAGE.match(ln.strip()) else clean_toc_line(ln)
        for ln in adjusted_pdf_text.splitlines()
    )
    md_wc = word_count(md_text)
    pdf_wc = word_count(pdf_text)
    adjusted_pdf_wc = word_count(adjusted_pdf_text)
    adjusted_coverage = round(md_wc / adjusted_pdf_wc * 100, 1) if adjusted_pdf_wc else None

    qa_issues = run_qa_json(md, pdf)
    heading_check = run_heading_check(pdf, md)
    pdf_contents = detect_pdf_contents(pdf)
    toc_clutter = md_contents_page_number_clutter(md_text)
    toc_cleaned, toc_changes = clean_contents_sections(md_text)

    issues: list[dict[str, Any]] = []
    for issue in qa_issues:
        if issue.get("code") == "C1":
            continue
        if issue.get("severity") in {"error", "warning"}:
            issues.append({
                "code": issue.get("code"),
                "severity": issue.get("severity"),
                "line": issue.get("line"),
                "detail": issue.get("detail"),
                "excerpt": issue.get("excerpt"),
            })

    if heading_check["problem_count"]:
        issues.append({
            "code": "HEADING_VERIFY",
            "severity": "warning",
            "detail": f"{heading_check['problem_count']} PDF heading candidates were missing, altered, or truncated in Markdown.",
        })
    if pdf_contents["present"] and not md_has_contents(md_text):
        issues.append({
            "code": "TOC_MISSING",
            "severity": "warning",
            "detail": "Source appears to include a Contents/Table of Contents section, but Markdown has no Contents heading.",
        })
    if toc_clutter:
        issues.append({
            "code": "TOC_PAGE_NUMBERS",
            "severity": "warning",
            "detail": f"{len(toc_clutter)} Contents lines appear to contain page numbers or dotted leaders.",
        })
    if adjusted_coverage is not None and not (95 <= adjusted_coverage <= 103):
        issues.append({
            "code": "ADJUSTED_COVERAGE",
            "severity": "warning",
            "detail": f"Adjusted coverage is {adjusted_coverage}% (target 95-103%).",
        })

    repaired_possible = bool(toc_changes) and all(
        i["code"] == "TOC_PAGE_NUMBERS" for i in issues if i.get("severity") == "warning"
    )
    status = summarize_status(issues, page_records, repaired_possible)

    ledger = {
        "schema_version": 1,
        "mode": "audit",
        "status": status,
        "created_at": now_iso(),
        "markdown_path": rel(md),
        "source_pdf": rel(pdf),
        "work_dir": rel(work_dir),
        "markdown_sha256": sha256(md),
        "source_pdf_sha256": sha256(pdf),
        "word_counts": {
            "markdown": md_wc,
            "pdf_pdftotext": pdf_wc,
            "pdf_adjusted": adjusted_pdf_wc,
            "adjusted_coverage_percent": adjusted_coverage,
        },
        "contents": {
            "source_detected": pdf_contents,
            "markdown_has_contents": md_has_contents(md_text),
            "page_number_clutter_count": len(toc_clutter),
            "auto_cleanable_changes": toc_changes[:200],
        },
        "heading_check": heading_check,
        "qa_issue_count": len(qa_issues),
        "issues": issues,
        "pages": [asdict(p) for p in page_records],
        "cloud_ocr": {
            "status": "not-configured",
            "preferred_order": ["mistral-ocr-4", "qwen-ocr"],
            "note": "Cloud OCR is intentionally a fallback for risky pages; wire API clients only after benchmark approval.",
        },
    }

    write_json(work_dir / "ledger.json", ledger)
    if write_sidecar:
        write_json(md.with_suffix(".audit.json"), ledger)
    return ledger


def repair_markdown(
    md: Path,
    pdf: Path | None = None,
    work_root: Path = DEFAULT_WORK_ROOT,
    render_pages: bool = True,
) -> dict[str, Any]:
    ledger = audit_markdown(md, pdf=pdf, work_root=work_root, render_pages=render_pages, write_sidecar=False)
    md = md.resolve()
    work_dir = Path(REPO_ROOT / ledger["work_dir"]) if not Path(ledger["work_dir"]).is_absolute() else Path(ledger["work_dir"])
    original = read_text(md)
    repaired, toc_changes = clean_contents_sections(original)
    reviewed = work_dir / "reviewed.md"
    reviewed.write_text(repaired, encoding="utf-8")
    diff_text = "\n".join(difflib.unified_diff(
        original.splitlines(),
        repaired.splitlines(),
        fromfile=rel(md),
        tofile=rel(reviewed),
        lineterm="",
    )) + "\n"
    diff_path = work_dir / "reviewed.diff"
    diff_path.write_text(diff_text, encoding="utf-8")
    repair_report = {
        "schema_version": 1,
        "mode": "repair",
        "created_at": now_iso(),
        "status": "draft-written" if toc_changes else "no-automatic-repair",
        "markdown_path": rel(md),
        "reviewed_draft": rel(reviewed),
        "diff": rel(diff_path),
        "automatic_repairs": {
            "contents_page_number_cleanup": toc_changes,
        },
        "audit_status": ledger["status"],
        "audit_issues": ledger["issues"],
        "note": "Published Markdown was not overwritten. Review the diff before finalizing manually.",
    }
    write_json(work_dir / "repair-report.json", repair_report)
    return repair_report


def new_transcription(pdf: Path, work_root: Path = DEFAULT_WORK_ROOT, render_pages: bool = True) -> dict[str, Any]:
    if not pdf.exists():
        raise FileNotFoundError(f"PDF not found: {pdf}")
    work_dir = work_dir_for(pdf, work_root)
    work_dir.mkdir(parents=True, exist_ok=True)
    page_records = build_page_records(pdf, work_dir, render_pages=render_pages)
    draft = assemble_new_draft(pdf, page_records, work_dir)
    ledger = {
        "schema_version": 1,
        "mode": "new",
        "status": "needs-human-review" if any(p.status != "accepted" for p in page_records) else "draft-written",
        "created_at": now_iso(),
        "source_pdf": rel(pdf),
        "source_pdf_sha256": sha256(pdf),
        "work_dir": rel(work_dir),
        "draft": rel(draft),
        "pages": [asdict(p) for p in page_records],
        "cloud_ocr": {
            "status": "not-configured",
            "preferred_order": ["mistral-ocr-4", "qwen-ocr"],
        },
    }
    write_json(work_dir / "ledger.json", ledger)
    return ledger


def iter_manifesto_markdown(root: Path) -> list[Path]:
    return sorted(root.glob("manifestos/**/manifesto.md"))


def batch_audit(
    root: Path,
    work_root: Path,
    limit: int | None,
    include_source_missing: bool,
    render_pages: bool,
) -> dict[str, Any]:
    records = []
    counts: Counter = Counter()
    for md in iter_manifesto_markdown(root):
        pdf = md.with_name("manifesto.pdf")
        if not pdf.exists() and not include_source_missing:
            continue
        ledger = audit_markdown(md, pdf=pdf, work_root=work_root, render_pages=render_pages, write_sidecar=True)
        records.append({
            "markdown_path": ledger["markdown_path"],
            "source_pdf": ledger["source_pdf"],
            "status": ledger["status"],
            "issue_count": len(ledger.get("issues", [])),
            "adjusted_coverage_percent": ledger.get("word_counts", {}).get("adjusted_coverage_percent"),
            "work_dir": ledger.get("work_dir"),
        })
        counts[ledger["status"]] += 1
        if limit is not None and len(records) >= limit:
            break

    report = {
        "schema_version": 1,
        "mode": "batch-audit",
        "created_at": now_iso(),
        "root": rel(root),
        "render_pages": render_pages,
        "include_source_missing": include_source_missing,
        "limit": limit,
        "counts": dict(counts),
        "records": records,
    }
    report_path = work_root / "batch-audit-report.json"
    write_json(report_path, report)
    report["report_path"] = rel(report_path)
    return report


def _source_slug_to_manifesto_path(source_file: Path, party: str) -> Path | None:
    year_slug = _source_year_slug(source_file, party)
    if not year_slug:
        return None
    election_id = {
        "1974-feb": "feb1974",
        "feb-1974": "feb1974",
        "1974-oct": "oct1974",
        "oct-1974": "oct1974",
    }.get(year_slug, year_slug)
    return REPO_ROOT / "manifestos" / election_id / party.lower() / "manifesto.md"


def _source_year_slug(source_file: Path, party: str) -> str | None:
    stem = source_file.stem.lower()
    prefix = f"{party.lower()}-"
    if stem.startswith(prefix):
        return stem[len(prefix):]
    m = re.search(r"\b(1[89]\d{2}|20\d{2})\b", stem)
    if m and party.lower() in stem:
        return m.group(1)
    return None


def _source_word_count(source_file: Path) -> int:
    try:
        return len(normalize_words(strip_markdown_syntax(read_text(source_file))))
    except Exception:
        return 0


def collect_text_sources(source_dir: Path, party: str) -> list[Path]:
    """
    Return one source text per election slug, preferring fuller duplicate files.

    This handles local Iain Dale experiments where most files are named
    labour-1945.md but an occasional fuller duplicate may be named like
    "Labour Party General Election Manifesto 1992.md".
    """
    by_slug: dict[str, Path] = {}
    for p in sorted(source_dir.glob("*.md")):
        slug = _source_year_slug(p, party)
        if not slug:
            continue
        if slug not in by_slug or _source_word_count(p) > _source_word_count(by_slug[slug]):
            by_slug[slug] = p
    return [by_slug[k] for k in sorted(by_slug)]


def batch_audit_text(
    source_dir: Path,
    party: str,
    work_root: Path,
    limit: int | None,
    write_sidecars: bool,
) -> dict[str, Any]:
    records = []
    counts: Counter = Counter()
    source_files = collect_text_sources(source_dir, party)
    for source_file in source_files:
        md = _source_slug_to_manifesto_path(source_file, party)
        if md is None:
            continue
        if not md.exists():
            record = {
                "source_text": str(source_file),
                "markdown_path": rel(md),
                "status": "target-missing",
                "issue_count": 1,
            }
            records.append(record)
            counts["target-missing"] += 1
        else:
            ledger = audit_text_source(md, source_file, work_root=work_root, write_sidecar=write_sidecars)
            records.append({
                "markdown_path": ledger["markdown_path"],
                "source_text": ledger["source_text"],
                "status": ledger["status"],
                "issue_count": len(ledger.get("issues", [])),
                "source_coverage_percent": ledger.get("word_counts", {}).get("source_coverage_percent"),
                "markdown_to_source_ratio_percent": ledger.get("word_counts", {}).get("markdown_to_source_ratio_percent"),
                "work_dir": ledger.get("work_dir"),
            })
            counts[ledger["status"]] += 1
        if limit is not None and len(records) >= limit:
            break

    report = {
        "schema_version": 1,
        "mode": "batch-audit-text",
        "created_at": now_iso(),
        "source_dir": str(source_dir),
        "party": party,
        "limit": limit,
        "write_sidecars": write_sidecars,
        "counts": dict(counts),
        "records": records,
    }
    report_path = work_root / f"batch-audit-text-{party.lower()}-report.json"
    write_json(report_path, report)
    report["report_path"] = rel(report_path)
    return report


def print_summary(result: dict[str, Any]) -> None:
    print(json.dumps({
        k: result.get(k)
        for k in ("mode", "source_type", "status", "markdown_path", "source_pdf", "source_text", "draft", "reviewed_draft", "diff", "work_dir", "word_counts", "counts", "report_path")
        if k in result
    }, ensure_ascii=False, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--work-root", default=str(DEFAULT_WORK_ROOT), help="Directory for generated ledgers, candidates, images, drafts, and reports.")
    sub = parser.add_subparsers(dest="mode", required=True)

    p_new = sub.add_parser("new", help="Create a reviewable draft from a source PDF.")
    p_new.add_argument("pdf")
    p_new.add_argument("--no-render", action="store_true", help="Do not render page PNGs.")

    p_audit = sub.add_parser("audit", help="Audit an existing manifesto.md against its source PDF.")
    p_audit.add_argument("markdown")
    p_audit.add_argument("--pdf", help="Override source PDF path; default is sibling manifesto.pdf.")
    p_audit.add_argument("--source-text", help="Audit against a golden text/Markdown source instead of a PDF.")
    p_audit.add_argument("--no-render", action="store_true", help="Do not render page PNGs.")
    p_audit.add_argument("--no-sidecar", action="store_true", help="Do not write <manifesto>.audit.json next to the Markdown file.")

    p_repair = sub.add_parser("repair", help="Write a reviewed draft and diff; never overwrites manifesto.md.")
    p_repair.add_argument("markdown")
    p_repair.add_argument("--pdf", help="Override source PDF path; default is sibling manifesto.pdf.")
    p_repair.add_argument("--no-render", action="store_true", help="Do not render page PNGs.")

    p_batch = sub.add_parser("batch-audit", help="Audit source-backed manifesto.md files in the repo.")
    p_batch.add_argument("--limit", type=int, help="Maximum files to audit.")
    p_batch.add_argument("--include-source-missing", action="store_true", help="Also ledger Markdown files without sibling PDFs.")
    p_batch.add_argument("--render-pages", action="store_true", help="Render page PNGs during batch audit. Disabled by default to avoid large local output.")

    p_batch_text = sub.add_parser("batch-audit-text", help="Audit historical Markdown against golden text sources such as Iain Dale splits.")
    p_batch_text.add_argument("--source-dir", required=True, help="Directory containing files named like labour-1945.md.")
    p_batch_text.add_argument("--party", required=True, help="Party slug used in source filenames and manifestos/<year>/<party>/ paths, e.g. labour.")
    p_batch_text.add_argument("--limit", type=int, help="Maximum source files to audit.")
    p_batch_text.add_argument("--no-sidecars", action="store_true", help="Do not write <manifesto>.audit.json sidecars next to Markdown files.")

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    work_root = Path(args.work_root)

    try:
        if args.mode == "new":
            result = new_transcription(Path(args.pdf), work_root=work_root, render_pages=not args.no_render)
        elif args.mode == "audit":
            if args.source_text:
                result = audit_text_source(
                    Path(args.markdown),
                    Path(args.source_text),
                    work_root=work_root,
                    write_sidecar=not args.no_sidecar,
                )
            else:
                result = audit_markdown(
                    Path(args.markdown),
                    pdf=Path(args.pdf) if args.pdf else None,
                    work_root=work_root,
                    render_pages=not args.no_render,
                    write_sidecar=not args.no_sidecar,
                )
        elif args.mode == "repair":
            result = repair_markdown(
                Path(args.markdown),
                pdf=Path(args.pdf) if args.pdf else None,
                work_root=work_root,
                render_pages=not args.no_render,
            )
        elif args.mode == "batch-audit":
            result = batch_audit(
                REPO_ROOT,
                work_root=work_root,
                limit=args.limit,
                include_source_missing=args.include_source_missing,
                render_pages=args.render_pages,
            )
        elif args.mode == "batch-audit-text":
            result = batch_audit_text(
                Path(args.source_dir),
                party=args.party,
                work_root=work_root,
                limit=args.limit,
                write_sidecars=not args.no_sidecars,
            )
        else:
            raise ValueError(args.mode)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    print_summary(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
