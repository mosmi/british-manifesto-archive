#!/usr/bin/env python3
"""Rebuild ELECTIONS.results in js/data.js from constituency MP data."""

from __future__ import annotations

import json
import unicodedata
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CON_DIR = ROOT / "data" / "constituencies"
HEX_1945 = ROOT / "data" / "hex" / "1945-outside-boundary.json"
DATA_JS = ROOT / "js" / "data.js"
VOTES_JSON = ROOT / "data" / "election-vote-totals.json"

# Wikipedia 1945 — authoritative seat breakdown (640 seats) + vote totals where listed
OVERRIDE_1945: list[tuple[str, int, int, float]] = [
    ("labour", 393, 11_967_746, 49.7),
    ("conservative", 197, 8_716_211, 36.2),
    ("libdem", 12, 2_177_938, 9.0),
    ("nationalliberal", 11, 686_652, 2.9),
    ("independent", 8, 133_191, 0.6),
    ("national", 2, 130_513, 0.5),
    ("commonwealth", 1, 110_634, 0.5),
    ("communist", 2, 97_945, 0.4),
    ("irishnationalist", 2, 92_819, 0.4),
    ("nationalindependent", 2, 65_171, 0.3),
    ("indlabour", 2, 63_135, 0.3),
    ("indconservative", 2, 57_823, 0.2),
    ("ilp", 3, 46_769, 0.2),
    ("indprogressive", 1, 45_967, 0.1),
    ("indliberal", 2, 30_450, 0.1),
]

ELECTION_BLOCK = re.compile(
    r"id: '(?P<eid>[^']+)', year: (?P<year>\d+).*?results: \[(?P<results>.*?)\n    \],",
    re.DOTALL,
)
RESULT_ROW = re.compile(
    r"\{ party: '([^']+)', seats: (\d+), votes: (\d+), percentage: ([\d.]+) \}",
)


def norm(label: str) -> str:
    s = unicodedata.normalize("NFKD", label or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


LABEL_TO_PARTY: dict[str, str] = {
    # Labour / Co-op
    "labour": "labour",
    "labour party": "labour",
    "labour ind": "labour",
    "labour and co operative party": "labour",
    "labour co op": "labour",
    "labour co operative": "labour",
    "labour co operative party": "labour",
    "labour co operative": "labour",
    # Conservatives
    "conservative": "conservative",
    "conservative and unionist party": "conservative",
    "conservative nat lib": "conservative",
    "conservative lib": "conservative",
    "conservative and nat lib": "conservative",
    "conservative national liberal": "conservative",
    "conservative and nat liberal": "conservative",
    # Liberals / Alliance / Social Democrat
    "liberal": "libdem",
    "libdem": "libdem",
    "liberal democrat": "libdem",
    "liberal democrats": "libdem",
    "sdp liberal alliance": "libdem",
    "social democrat": "libdem",
    # National Liberals
    "liberal national": "nationalliberal",
    "national liberal": "nationalliberal",
    "nat liberal": "nationalliberal",
    "nat lib conservative": "natlibconservative",
    "nat lib and conservative": "natlibconservative",
    "nat liberal and conservative": "natlibconservative",
    "lib conservative": "natlibconservative",
    "lib and conservative": "natlibconservative",
    # Other GB parties
    "common wealth": "commonwealth",
    "communist": "communist",
    "green": "green",
    "green party": "green",
    "ukip": "ukip",
    "reform uk": "reform",
    "alliance": "alliance",
    "alliance alliance party of northern ireland": "alliance",
    "alliance party": "alliance",
    "apni": "alliance",
    "vanguard": "vanguard",
    "tuv": "tuv",
    "traditional unionist voice tuv": "tuv",
    "plaid cymru": "plaid",
    "plaid cymru the party of wales": "plaid",
    "snp": "snp",
    "scottish national party": "snp",
    "scottish national party snp": "snp",
    "scottish nationalist": "snp",
    # Northern Ireland
    "ulster unionist": "uup",
    "official ulster unionist": "uup",
    "official unionist party": "uup",
    "uup": "uup",
    "democratic unionist": "dup",
    "democratic unionist party": "dup",
    "democratic unionist party d u p": "dup",
    "dup": "dup",
    "sinn fein": "sinnfein",
    "provisional sinn fein": "sinnfein",
    "sdlp": "sdlp",
    "sdlp social democratic and labour party": "sdlp",
    "social democratic and labour": "sdlp",
    "social democratic and labour party": "sdlp",
    "social democratic labour party": "sdlp",
    "social democratic labour": "sdlp",
    "irish labour": "irishlabour",
    "irish republican": "irishrepublican",
    "irish nationalist": "irishnationalist",
    "nationalist": "irishnationalist",
    "anti partition": "antipartition",
    "republican labour": "republicanlabour",
    "protestant unionist": "protestantunionist",
    "unity": "unity",
    "ind unity": "unity",
    "united ulster unionist": "uuuc",
    "ukup": "ukup",
    "ulster popular unionist": "ulsterpopularunionist",
    # Independents / minor labels
    "ind labour party": "ilp",
    "independent labour party": "ilp",
    "ind labour": "indlabour",
    "independent labour": "indlabour",
    "ind conservative": "indconservative",
    "independent conservative": "indconservative",
    "ind liberal": "indliberal",
    "independent liberal": "indliberal",
    "ind progressive": "indprogressive",
    "independent progressive": "indprogressive",
    "ind ulster unionist": "indunionist",
    "independent unionist": "indunionist",
    "ind": "independent",
    "independent": "independent",
    "national": "national",
    "national independent": "nationalindependent",
    # Speaker
    "speaker": "speaker",
    "spk": "speaker",
    "speaker seeking re election": "speaker",
    # Misc
    "respect": "respect",
    "ikhc": "healthconcern",
    "health concern": "healthconcern",
    "other": "others",
}


def label_to_party(label: str, party_field: str | None = None) -> str:
    key = norm(label)
    if key in LABEL_TO_PARTY:
        return LABEL_TO_PARTY[key]
    if party_field and party_field != "others":
        return party_field
    return "others"


def load_constituency_file(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict) or "constituencies" not in data:
        return None
    return data


def count_constituency_seats(election_id: str) -> Counter[str]:
    path = CON_DIR / f"{election_id}.json"
    data = load_constituency_file(path)
    if not data:
        return Counter()
    counts: Counter[str] = Counter()
    for row in data["constituencies"]:
        if not isinstance(row, dict):
            continue
        pid = label_to_party(row.get("partyLabel", ""), row.get("party"))
        counts[pid] += 1
    return counts


def count_1945_outside_boundary() -> Counter[str]:
    if not HEX_1945.exists():
        return Counter()
    data = json.loads(HEX_1945.read_text(encoding="utf-8"))
    counts: Counter[str] = Counter()
    for group in data.get("groups", []):
        for seat in group.get("seats", []):
            for member in seat.get("members", []):
                party_name = member.get("party") or member.get("partyLabel") or ""
                counts[label_to_party(party_name, member.get("party"))] += 1
    return counts


def elections_section(content: str) -> str:
    start = content.find("const ELECTIONS = [")
    if start == -1:
        raise RuntimeError("const ELECTIONS not found in data.js")
    end = content.find("\n];", start)
    if end == -1:
        raise RuntimeError("ELECTIONS array end not found in data.js")
    return content[start:end + 3]


def parse_existing_votes(elections_blob: str) -> dict[str, dict[str, dict]]:
    out: dict[str, dict[str, dict]] = {}
    for m in ELECTION_BLOCK.finditer(elections_blob):
        eid = m.group("eid")
        parties: dict[str, dict] = {}
        for rm in RESULT_ROW.finditer(m.group("results")):
            parties[rm.group(1)] = {
                "seats": int(rm.group(2)),
                "votes": int(rm.group(3)),
                "percentage": float(rm.group(4)),
            }
        out[eid] = parties
    return out


def build_results(
    election_id: str,
    existing: dict[str, dict],
    vote_totals: dict[str, dict[str, dict]],
) -> list[dict]:
    if election_id == "1945":
        hex_counts = count_1945_outside_boundary()
        const_counts = count_constituency_seats("1945")
        combined = const_counts + hex_counts
        wiki_total = sum(s for _, s, _, _ in OVERRIDE_1945)
        if combined and sum(combined.values()) != wiki_total:
            print(
                f"  note: 1945 constituency+hex seats={sum(combined.values())} "
                f"(using Wikipedia override {wiki_total})",
                flush=True,
            )
        return [
            {"party": p, "seats": s, "votes": v, "percentage": pct}
            for p, s, v, pct in OVERRIDE_1945
        ]

    counts = count_constituency_seats(election_id)
    if not counts:
        return []

    vote_lookup = vote_totals.get(election_id, {})
    rows: list[dict] = []
    for party, seats in counts.most_common():
        if seats <= 0:
            continue
        if party == "others" and seats <= 0:
            continue
        prev = existing.get(party)
        if party in vote_lookup:
            votes = vote_lookup[party]["votes"]
            percentage = vote_lookup[party]["percentage"]
        elif prev is not None and prev.get("votes", 0) > 0:
            votes = prev["votes"]
            percentage = prev["percentage"]
        else:
            votes = 0
            percentage = 0.0
        rows.append(
            {
                "party": party,
                "seats": seats,
                "votes": votes,
                "percentage": percentage,
            }
        )

    rows = [r for r in rows if not (r["party"] == "others" and r["seats"] == 0)]
    return rows


def format_results(rows: list[dict]) -> str:
    lines = []
    for r in rows:
        party = r["party"]
        seats = r["seats"]
        votes = r["votes"]
        pct = r["percentage"]
        if isinstance(pct, float) and pct == int(pct):
            pct_str = f"{int(pct)}"
        else:
            pct_str = f"{pct:.1f}".rstrip("0").rstrip(".")
        lines.append(
            f"      {{ party: '{party}', seats: {seats:3d}, votes: {votes}, percentage: {pct_str}  }},"
        )
    return "\n".join(lines)


def patch_election_results(content: str, eid: str, rows: list[dict]) -> str:
    formatted = format_results(rows)
    pattern = (
        rf"(id: '{re.escape(eid)}', year: \d+.*?results: \[)\n"
        rf"(?:.*?\n)*?"
        rf"(    \],)"
    )
    repl = rf"\1\n{formatted}\n\2"
    new_content, n = re.subn(pattern, repl, content, count=1, flags=re.DOTALL)
    if n != 1:
        raise RuntimeError(f"Failed to patch election {eid} (matches={n})")
    return new_content


def list_election_ids(constituency_paths: list[Path], existing: dict[str, dict]) -> list[str]:
    from_files = {
        p.stem
        for p in constituency_paths
        if p.stem not in ("index",) and load_constituency_file(p) is not None
    }
    return sorted(from_files | set(existing.keys()), key=lambda x: (not x.isdigit(), x))


def main() -> None:
    content = DATA_JS.read_text(encoding="utf-8")
    elections_blob = elections_section(content)
    existing_all = parse_existing_votes(elections_blob)

    vote_totals = json.loads(VOTES_JSON.read_text(encoding="utf-8")) if VOTES_JSON.exists() else {}

    constituency_paths = list(CON_DIR.glob("*.json"))
    election_ids = list_election_ids(constituency_paths, existing_all)

    all_results: dict[str, list[dict]] = {}
    print(f"{'Election':<12} {'Seats':>5}  Parties")
    print("-" * 60)

    for eid in election_ids:
        if eid not in existing_all:
            continue
        rows = build_results(eid, existing_all.get(eid, {}), vote_totals)
        all_results[eid] = rows
        total = sum(r["seats"] for r in rows)
        parties = len(rows)
        print(f"{eid:<12} {total:5d}  {parties} parties")

    patched = content
    for eid, rows in all_results.items():
        patched = patch_election_results(patched, eid, rows)

    DATA_JS.write_text(patched, encoding="utf-8")
    print(f"\nUpdated {DATA_JS}")


if __name__ == "__main__":
    main()
