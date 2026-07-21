#!/usr/bin/env python3
"""
build-fulltext-index.py

Build data/fulltext-index.json — a compact inverted index over every
manifestos/**/manifesto.md transcription for client-side full-text search.

Also writes data/fulltext-meta.json (docCount + fingerprint) so the search
client can cache-bust the large index after rebuilds without a manual
ASSETS_VERSION bump for this file alone.

Usage:
  python3 scripts/build-fulltext-index.py           # rebuild
  python3 scripts/build-fulltext-index.py --check   # exit 1 if stale / missing

Run after adding or repairing transcribed manifesto Markdown (Phase 5 of the
transcription pipeline). The index walks the filesystem — every manifesto.md
is included even before it appears in manifestos-index.json (labels fall back
to "{partyId} {electionId}" until the catalogue entry exists).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFESTOS_DIR = ROOT / "manifestos"
INDEX_PATH = ROOT / "data" / "manifestos-index.json"
OUT = ROOT / "data" / "fulltext-index.json"
META = ROOT / "data" / "fulltext-meta.json"

MIN_TOKEN_LEN = 3
STOP = {
    "the", "and", "for", "that", "with", "this", "from", "have", "will",
    "are", "was", "were", "been", "being", "has", "had", "not", "but",
    "all", "can", "our", "their", "they", "them", "who", "which", "what",
    "when", "where", "how", "into", "than", "then", "also", "more", "most",
    "other", "such", "only", "over", "after", "before", "between", "through",
    "about", "would", "could", "should", "shall", "may", "might", "must",
    "your", "you", "its", "his", "her", "she", "him", "we", "us", "or",
    "an", "as", "at", "by", "on", "in", "to", "of", "a", "is", "be", "it",
    "do", "does", "did", "done", "so", "if", "any", "each", "few", "own",
    "same", "too", "very", "just", "now", "here", "there", "these", "those",
    "out", "up", "down", "off", "again", "further", "once", "both", "some",
}

FRONTMATTER_RE = re.compile(r"(?ms)\A---\s*\n.*?\n---\s*\n")
LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
MD_NOISE_RE = re.compile(r"[#>*_`~|]+")
SPACE_RE = re.compile(r"\s+")
TOKEN_RE = re.compile(r"[a-z0-9]{%d,}" % MIN_TOKEN_LEN)


def strip_markdown(text: str) -> str:
    text = FRONTMATTER_RE.sub("", text)
    text = IMAGE_RE.sub(" ", text)
    text = LINK_RE.sub(r"\1", text)
    text = MD_NOISE_RE.sub(" ", text)
    return SPACE_RE.sub(" ", text).strip().lower()


def load_labels() -> dict[tuple[str, str], str]:
    if not INDEX_PATH.exists():
        return {}
    labels: dict[tuple[str, str], str] = {}
    for row in json.loads(INDEX_PATH.read_text(encoding="utf-8")):
        labels[(row["electionId"], row["partyId"])] = row.get("label") or ""
    return labels


def iter_manifesto_paths() -> list[Path]:
    return sorted(MANIFESTOS_DIR.rglob("manifesto.md"))


def path_to_ids(path: Path) -> tuple[str, str]:
    parts = path.relative_to(MANIFESTOS_DIR).parts
    party_id = parts[-2]
    election_id = "/".join(parts[:-2])
    return election_id, party_id


def disk_fingerprint(paths: list[Path]) -> str:
    """Stable fingerprint of path + size + mtime for staleness checks."""
    h = hashlib.sha256()
    for path in paths:
        st = path.stat()
        rel = path.relative_to(MANIFESTOS_DIR).as_posix()
        h.update(f"{rel}\0{st.st_size}\0{int(st.st_mtime)}\n".encode())
    return h.hexdigest()[:16]


def build(paths: list[Path] | None = None) -> tuple[dict, dict]:
    paths = paths if paths is not None else iter_manifesto_paths()
    labels = load_labels()
    docs: list[dict] = []
    inv: dict[str, set[int]] = defaultdict(set)
    missing_labels = 0

    for path in paths:
        election_id, party_id = path_to_ids(path)
        raw = path.read_text(encoding="utf-8", errors="replace")
        plain = strip_markdown(raw)
        doc_index = len(docs)
        label = labels.get((election_id, party_id))
        if not label:
            missing_labels += 1
            label = f"{party_id} {election_id}"
        docs.append({
            "e": election_id,
            "p": party_id,
            "l": label,
        })
        for token in set(TOKEN_RE.findall(plain)):
            if token in STOP:
                continue
            inv[token].add(doc_index)

    cap = max(80, int(len(docs) * 0.92))
    inv_out = {
        token: sorted(ids)
        for token, ids in inv.items()
        if len(ids) <= cap
    }

    generated = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    fingerprint = disk_fingerprint(paths)
    payload = {
        "v": 1,
        "generated": generated,
        "docCount": len(docs),
        "tokenCount": len(inv_out),
        "docs": docs,
        "inv": inv_out,
    }
    meta = {
        "v": 1,
        "generated": generated,
        "docCount": len(docs),
        "tokenCount": len(inv_out),
        "fingerprint": fingerprint,
        "builtOn": date.today().isoformat(),
        "missingCatalogueLabels": missing_labels,
    }
    return payload, meta


def write_outputs(payload: dict, meta: dict) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    META.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


def check_stale() -> int:
    paths = iter_manifesto_paths()
    fp = disk_fingerprint(paths)
    if not OUT.exists() or not META.exists():
        print(
            f"STALE: missing index (found {len(paths)} manifesto.md on disk). "
            "Run: python3 scripts/build-fulltext-index.py",
            file=sys.stderr,
        )
        return 1
    meta = json.loads(META.read_text(encoding="utf-8"))
    reasons = []
    if meta.get("docCount") != len(paths):
        reasons.append(f"docCount {meta.get('docCount')} ≠ disk {len(paths)}")
    if meta.get("fingerprint") != fp:
        reasons.append("fingerprint mismatch (md added, removed, or edited)")
    if reasons:
        print("STALE: " + "; ".join(reasons), file=sys.stderr)
        print("Run: python3 scripts/build-fulltext-index.py", file=sys.stderr)
        return 1
    print(
        f"OK: full-text index matches {len(paths)} manifesto.md "
        f"(generated {meta.get('generated')})"
    )
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 0 if index matches disk; 1 if rebuild needed",
    )
    args = parser.parse_args()

    if args.check:
        raise SystemExit(check_stale())

    paths = iter_manifesto_paths()
    payload, meta = build(paths)
    write_outputs(payload, meta)
    size_kb = OUT.stat().st_size / 1024
    print(
        f"Wrote {OUT.relative_to(ROOT)} + {META.relative_to(ROOT)} — "
        f"{payload['docCount']} docs, {payload['tokenCount']} terms, "
        f"{size_kb:.0f} KB"
    )
    if meta["missingCatalogueLabels"]:
        print(
            f"Note: {meta['missingCatalogueLabels']} docs lack a "
            "manifestos-index.json label (fallback titles used). "
            "Add catalogue entries when ready."
        )
    print(
        "Full-text search will pick this up via fulltext-meta.json "
        "(no ASSETS_VERSION bump required for the index alone)."
    )


if __name__ == "__main__":
    main()
