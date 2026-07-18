#!/usr/bin/env python3
"""Enrich devolved portal index.json files with compact seat results for election cards.

Reads each election JSON referenced by the portal index and writes:
  - results: [{ party, seats }, ...]  (seats > 0 only)
  - totalSeats
  - majorityThreshold (when present)

Sources:
  holyrood / senedd / stormont / euro → parliament.results
  london → assembly.results
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEVOLVED = ROOT / "data" / "devolved"

PORTALS = {
    "holyrood": "parliament",
    "senedd": "parliament",
    "stormont": "parliament",
    "euro": "parliament",
    "london": "assembly",
}


def compact_results(rows: list) -> list[dict]:
    out = []
    for r in rows or []:
        seats = r.get("seats") or 0
        party = r.get("party")
        if not party or seats <= 0:
            continue
        entry = {"party": party, "seats": seats}
        if r.get("partyLabel"):
            entry["partyLabel"] = r["partyLabel"]
        out.append(entry)
    return out


def sync_portal(portal: str, results_key: str) -> int:
    index_path = DEVOLVED / portal / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    updated = 0
    for entry in index:
        eid = entry["id"]
        election_path = DEVOLVED / portal / f"{eid}.json"
        if not election_path.exists():
            print(f"  WARN missing {election_path.relative_to(ROOT)}")
            continue
        election = json.loads(election_path.read_text(encoding="utf-8"))
        block = election.get(results_key) or {}
        results = compact_results(block.get("results") or [])
        entry["results"] = results
        if block.get("totalSeats") is not None:
            entry["totalSeats"] = block["totalSeats"]
        if block.get("majorityThreshold") is not None:
            entry["majorityThreshold"] = block["majorityThreshold"]
        updated += 1
    index_path.write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return updated


def main() -> None:
    total = 0
    for portal, key in PORTALS.items():
        n = sync_portal(portal, key)
        print(f"{portal}: {n} entries → {DEVOLVED / portal / 'index.json'}")
        total += n
    print(f"Synced seat summaries for {total} portal index entries.")


if __name__ == "__main__":
    main()
