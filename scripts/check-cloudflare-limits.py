#!/usr/bin/env python3
"""Fail if any deployable file exceeds Cloudflare Pages limits."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_FILE_BYTES = 25 * 1024 * 1024  # 25 MiB
MAX_FILES = 20_000

SKIP_DIRS = {
    ".git",
    ".venv-screenshot",
    "__pycache__",
    "previews",
    ".venv",
    "cache",
    # Vendored dev toolkits — excluded from the deploy via .assetsignore.
    "tools",
}


def is_ignored(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in SKIP_DIRS for part in rel.parts):
        return True
    name = rel.name
    if name == ".DS_Store":
        return True
    if name.startswith("General election ") and name.endswith(".pdf"):
        return True
    if name.startswith("Wikipedia") and name.endswith(".html"):
        return True
    return False


def main() -> int:
    files = [p for p in ROOT.rglob("*") if p.is_file() and not is_ignored(p)]
    oversized = [(p, p.stat().st_size) for p in files if p.stat().st_size > MAX_FILE_BYTES]

    print(f"Deployable files: {len(files)}")
    if len(files) > MAX_FILES:
        print(f"ERROR: file count {len(files)} exceeds Cloudflare free-plan limit ({MAX_FILES})")
        return 1

    if oversized:
        print("ERROR: files exceed 25 MiB Cloudflare Pages limit:")
        for path, size in sorted(oversized, key=lambda x: -x[1]):
            mib = size / (1024 * 1024)
            print(f"  {path.relative_to(ROOT)} ({mib:.2f} MiB)")
        return 1

    print("OK: within Cloudflare Pages file count and per-file size limits.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
