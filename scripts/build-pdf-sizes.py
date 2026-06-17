#!/usr/bin/env python3
"""
build-pdf-sizes.py

Walks the manifestos/ directory tree, finds every manifesto.pdf, and
writes data/pdf-sizes.json — a flat mapping of URL path → human-readable
size string (e.g. "4.7 MB").

Run whenever a new manifesto PDF is added to the archive:
  python3 scripts/build-pdf-sizes.py

The resulting data/pdf-sizes.json is loaded once at runtime by js/app.js
(via window.getPdfSize) so PDF links can display accurate file sizes
without any live HEAD requests.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFESTOS_DIR = ROOT / "manifestos"
OUT = ROOT / "data" / "pdf-sizes.json"


def human_size(num_bytes: int) -> str:
    """Return a compact human-readable size string, e.g. '4.7 MB'."""
    if num_bytes < 1024:
        return f"{num_bytes} B"
    kb = num_bytes / 1024
    if kb < 1024:
        return f"{kb:.0f} KB"
    mb = kb / 1024
    if mb < 10:
        return f"{mb:.1f} MB"
    return f"{mb:.0f} MB"


def build_pdf_sizes() -> dict[str, str]:
    sizes: dict[str, str] = {}

    for pdf_path in sorted(MANIFESTOS_DIR.rglob("manifesto.pdf")):
        try:
            byte_size = pdf_path.stat().st_size
        except OSError:
            continue

        # Convert filesystem path to URL path, relative to ROOT
        rel = pdf_path.relative_to(ROOT)
        url_path = "/" + str(rel).replace("\\", "/")  # Windows-safe

        sizes[url_path] = human_size(byte_size)

    return sizes


def main() -> None:
    sizes = build_pdf_sizes()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(sizes, f, indent=2, sort_keys=True)
        f.write("\n")

    print(f"✅  Wrote {len(sizes)} entries to {OUT.relative_to(ROOT)}")

    # Show a few examples
    sample = list(sizes.items())[:5]
    for path, size in sample:
        print(f"   {path}: {size}")
    if len(sizes) > 5:
        print(f"   … and {len(sizes) - 5} more")


if __name__ == "__main__":
    main()
