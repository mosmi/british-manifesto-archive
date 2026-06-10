#!/usr/bin/env python3
"""Apply display-name spelling corrections to all constituency JSON files."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "constituencies"


def load_import_module():
    spec = importlib.util.spec_from_file_location(
        "import_historical_hexmaps",
        ROOT / "scripts" / "import-historical-hexmaps.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    mod = load_import_module()
    changed_files = 0
    changed_seats = 0
    for path in sorted(OUT_DIR.glob("*.json")):
        if path.name == "index.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        constituencies = data.get("constituencies") or []
        before = [c.get("name", "") for c in constituencies]
        mod.fix_constituency_display_names(constituencies)
        after = [c.get("name", "") for c in constituencies]
        file_changes = sum(1 for a, b in zip(before, after) if a != b)
        if file_changes:
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            changed_files += 1
            changed_seats += file_changes
            print(f"  {path.stem}: {file_changes} names corrected")
    print(f"Done: {changed_seats} names in {changed_files} files")


if __name__ == "__main__":
    main()
