#!/usr/bin/env python3
import sys
import os
import json
import re
from pathlib import Path

TOOLKIT_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLKIT_DIR.parents[1]

# Add process_manifestos path
sys.path.append(str(REPO_ROOT / "scripts"))
sys.path.append(str(TOOLKIT_DIR))
import process_manifestos

# Mappings of election -> candidate -> metadata
METADATA = {
    "gla-2024": {
        "sdp": {
            "party_name": "Social Democratic Party",
            "party_leader": "Amy Gallagher",
            "political_spectrum": "centre / social democratic",
            "victory": False,
            "government_outcome": "opposition"
        },
        "londonreal": {
            "party_name": "London Real Party",
            "party_leader": "Brian Rose",
            "political_spectrum": "other",
            "victory": False,
            "government_outcome": "opposition"
        },
        "binface": {
            "party_name": "Count Binface",
            "party_leader": "Count Binface",
            "political_spectrum": "satirical",
            "victory": False,
            "government_outcome": "opposition"
        },
        "awp": {
            "party_name": "Animal Welfare Party",
            "party_leader": "Femy Amin",
            "political_spectrum": "other",
            "victory": False,
            "government_outcome": "opposition"
        },
        "reform": {
            "party_name": "Reform UK",
            "party_leader": "Howard Cox",
            "political_spectrum": "right",
            "victory": False,
            "government_outcome": "opposition"
        },
        "conservative": {
            "party_name": "Conservative Party",
            "party_leader": "Susan Hall",
            "political_spectrum": "centre-right",
            "victory": False,
            "government_outcome": "opposition"
        },
        "michli": {
            "party_name": "Andreas Michli",
            "party_leader": "Andreas Michli",
            "political_spectrum": "other",
            "victory": False,
            "government_outcome": "opposition"
        },
        "campbell": {
            "party_name": "Natalie Campbell",
            "party_leader": "Natalie Campbell",
            "political_spectrum": "other",
            "victory": False,
            "government_outcome": "opposition"
        },
        "britainfirst": {
            "party_name": "Britain First",
            "party_leader": "Nick Scanlon",
            "political_spectrum": "right",
            "victory": False,
            "government_outcome": "opposition"
        },
        "libdem": {
            "party_name": "Liberal Democrats",
            "party_leader": "Rob Blackie",
            "political_spectrum": "centre",
            "victory": False,
            "government_outcome": "opposition"
        },
        "labour": {
            "party_name": "Labour Party",
            "party_leader": "Sadiq Khan",
            "political_spectrum": "centre-left",
            "victory": True,
            "government_outcome": "majority"
        },
        "ghulati": {
            "party_name": "Tarun Ghulati",
            "party_leader": "Tarun Ghulati",
            "political_spectrum": "other",
            "victory": False,
            "government_outcome": "opposition"
        },
        "green": {
            "party_name": "Green Party",
            "party_leader": "Zoe Garbett",
            "political_spectrum": "left",
            "victory": False,
            "government_outcome": "opposition"
        }
    },
    "gla-2021": {
        "labour": {
            "party_name": "Labour Party",
            "party_leader": "Sadiq Khan",
            "political_spectrum": "centre-left",
            "victory": True,
            "government_outcome": "majority"
        },
        "conservative": {
            "party_name": "Conservative Party",
            "party_leader": "Shaun Bailey",
            "political_spectrum": "centre-right",
            "victory": False,
            "government_outcome": "opposition"
        },
        "libdem": {
            "party_name": "Liberal Democrats",
            "party_leader": "Luisa Porritt",
            "political_spectrum": "centre",
            "victory": False,
            "government_outcome": "opposition"
        },
        "green": {
            "party_name": "Green Party",
            "party_leader": "Sian Berry",
            "political_spectrum": "left",
            "victory": False,
            "government_outcome": "opposition"
        },
        "londonreal": {
            "party_name": "London Real Party",
            "party_leader": "Brian Rose",
            "political_spectrum": "other",
            "victory": False,
            "government_outcome": "opposition"
        },
        "reclaim": {
            "party_name": "Reclaim Party",
            "party_leader": "Laurence Fox",
            "political_spectrum": "right",
            "victory": False,
            "government_outcome": "opposition"
        },
        "binface": {
            "party_name": "Count Binface",
            "party_leader": "Count Binface",
            "political_spectrum": "satirical",
            "victory": False,
            "government_outcome": "opposition"
        },
        "pierscorbyn": {
            "party_name": "Let London Live",
            "party_leader": "Piers Corbyn",
            "political_spectrum": "other",
            "victory": False,
            "government_outcome": "opposition"
        },
        "burningpink": {
            "party_name": "Burning Pink",
            "party_leader": "Valerie Brown",
            "political_spectrum": "left",
            "victory": False,
            "government_outcome": "opposition"
        },
        "maxfosh": {
            "party_name": "Independent",
            "party_leader": "Max Fosh",
            "political_spectrum": "satirical",
            "victory": False,
            "government_outcome": "opposition"
        }
    },
    "gla-2004": {
        "libdem": {
            "party_name": "Liberal Democrats",
            "party_leader": "Simon Hughes",
            "political_spectrum": "centre",
            "victory": False,
            "government_outcome": "opposition"
        },
        "green": {
            "party_name": "Green Party",
            "party_leader": "Darren Johnson",
            "political_spectrum": "left",
            "victory": False,
            "government_outcome": "opposition"
        },
        "cpa": {
            "party_name": "Christian Peoples Alliance",
            "party_leader": "Ram Gidoomal",
            "political_spectrum": "other",
            "victory": False,
            "government_outcome": "opposition"
        }
    },
    "gla-2016": {
        "labour": {
            "party_name": "Labour Party",
            "party_leader": "Sadiq Khan",
            "political_spectrum": "centre-left",
            "victory": True,
            "government_outcome": "majority"
        },
        "conservative": {
            "party_name": "Conservative Party",
            "party_leader": "Zac Goldsmith",
            "political_spectrum": "centre-right",
            "victory": False,
            "government_outcome": "opposition"
        },
        "libdem": {
            "party_name": "Liberal Democrats",
            "party_leader": "Caroline Pidgeon",
            "political_spectrum": "centre",
            "victory": False,
            "government_outcome": "opposition"
        },
        "green": {
            "party_name": "Green Party",
            "party_leader": "Siân Berry",
            "political_spectrum": "left",
            "victory": False,
            "government_outcome": "opposition"
        },
        "ukip": {
            "party_name": "UK Independence Party",
            "party_leader": "Peter Whittle",
            "political_spectrum": "right",
            "victory": False,
            "government_outcome": "opposition"
        },
        "respect": {
            "party_name": "Respect Party",
            "party_leader": "George Galloway",
            "political_spectrum": "left",
            "victory": False,
            "government_outcome": "opposition"
        },
        "wep": {
            "party_name": "Women's Equality Party",
            "party_leader": "Sophie Walker",
            "political_spectrum": "other",
            "victory": False,
            "government_outcome": "opposition"
        },
        "bnp": {
            "party_name": "British National Party",
            "party_leader": "David Furness",
            "political_spectrum": "right",
            "victory": False,
            "government_outcome": "opposition"
        },
        "onelove": {
            "party_name": "One Love Party",
            "party_leader": "Ankit Love",
            "political_spectrum": "other",
            "victory": False,
            "government_outcome": "opposition"
        }
    },
    "gla-2012": {
        "labour": {
            "party_name": "Labour Party",
            "party_leader": "Ken Livingstone",
            "political_spectrum": "centre-left",
            "victory": False,
            "government_outcome": "opposition"
        },
        "conservative": {
            "party_name": "Conservative Party",
            "party_leader": "Boris Johnson",
            "political_spectrum": "centre-right",
            "victory": True,
            "government_outcome": "majority"
        },
        "libdem": {
            "party_name": "Liberal Democrats",
            "party_leader": "Brian Paddick",
            "political_spectrum": "centre",
            "victory": False,
            "government_outcome": "opposition"
        },
        "green": {
            "party_name": "Green Party",
            "party_leader": "Jenny Jones",
            "political_spectrum": "left",
            "victory": False,
            "government_outcome": "opposition"
        },
        "bnp": {
            "party_name": "British National Party",
            "party_leader": "Carlos Cortiglia",
            "political_spectrum": "right",
            "victory": False,
            "government_outcome": "opposition"
        },
        "benita": {
            "party_name": "Independent",
            "party_leader": "Siobhan Benita",
            "political_spectrum": "other",
            "victory": False,
            "government_outcome": "opposition"
        }
    },
    "gla-2008": {
        "conservative": {
            "party_name": "Conservative Party",
            "party_leader": "Boris Johnson",
            "political_spectrum": "centre-right",
            "victory": True,
            "government_outcome": "majority"
        },
        "libdem": {
            "party_name": "Liberal Democrats",
            "party_leader": "Brian Paddick",
            "political_spectrum": "centre",
            "victory": False,
            "government_outcome": "opposition"
        },
        "cooperative": {
            "party_name": "Co-operative Party",
            "party_leader": "London Co-operative Party",
            "political_spectrum": "centre-left",
            "victory": False,
            "government_outcome": "opposition"
        },
        "green": {
            "party_name": "Green Party",
            "party_leader": "Siân Berry",
            "political_spectrum": "left",
            "victory": False,
            "government_outcome": "opposition"
        },
        "englishdemocrats": {
            "party_name": "English Democrats",
            "party_leader": "Matt O'Connor",
            "political_spectrum": "right",
            "victory": False,
            "government_outcome": "opposition"
        }
    },
    "gla-2000": {
        "livingstone": {
            "party_name": "Independent",
            "party_leader": "Ken Livingstone",
            "political_spectrum": "centre-left",
            "victory": True,
            "government_outcome": "majority"
        }
    }
}

BATCH_PARTIES = {
    "1": ("gla-2024", ["sdp", "londonreal", "binface", "awp", "reform", "conservative"]),
    "2": ("gla-2024", ["michli", "campbell", "britainfirst", "libdem", "labour", "ghulati", "green"]),
    "3": ("gla-2021", ["labour", "conservative", "libdem", "green", "londonreal", "reclaim", "binface", "pierscorbyn", "burningpink", "maxfosh"]),
    "4": ("gla-2004", ["libdem", "green", "cpa"]),
    "5": ("gla-2016", ["labour", "conservative", "libdem", "green", "ukip", "respect", "wep", "bnp", "onelove"]),
    "6": ("gla-2012", ["labour", "conservative", "libdem", "green", "bnp", "benita"]),
    "7": ("gla-2008", ["conservative", "libdem", "cooperative", "green", "englishdemocrats"]),
    "8": ("gla-2000", ["livingstone"])
}

def detect_sections_from_text(text: str) -> list[str]:
    sections = []
    text_lower = text.lower()
    for topic, keywords in process_manifestos.SECTION_KEYWORDS.items():
        for kw in keywords:
            if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
                sections.append(topic)
                break
    return [s for s in sections if s in process_manifestos.SECTIONS_TAXONOMY]

def finalize_manifesto(party_id: str, election_id: str):
    # work slug format: manifestos__london__gla-2024__sdp__manifesto
    slug = f"manifestos__london__{election_id}__{party_id}__manifesto"
    draft_path = TOOLKIT_DIR / "work" / slug / "draft.md"
    if not draft_path.exists():
        print(f"Draft not found for {party_id} ({election_id}): {draft_path}")
        return False

    meta = METADATA[election_id][party_id]
    year = election_id.split("-")[1]
    
    # Read draft markdown
    body = draft_path.read_text(encoding="utf-8").strip()

    # Pre-process body to clean headers/first lines
    lines = body.splitlines()
    if lines and (lines[0].startswith("#") or "manifesto" in lines[0].lower() or meta["party_leader"].lower() in lines[0].lower()):
        idx = 1
        while idx < len(lines) and lines[idx].strip() == "":
            idx += 1
        body = "\n".join(lines[idx:]).strip()

    # Get display name of the party
    display = process_manifestos.DISPLAY_NAMES.get(party_id) or meta["party_name"]

    # Canonical H1
    canonical_h1 = f"# {display} London Mayoral Manifesto {year}"
    body = canonical_h1 + "\n\n" + body

    # Detect sections
    sections = detect_sections_from_text(body)

    # Build record
    record = {
        "election_id": election_id,
        "election_year": int(year),
        "party_id": party_id,
        "party_name": display,
        "party_leader": meta["party_leader"],
        "political_spectrum": meta["political_spectrum"],
        "victory": meta["victory"],
        "government_outcome": meta["government_outcome"]
    }

    # Build frontmatter
    frontmatter = process_manifestos.build_frontmatter(record, sections)
    final_content = frontmatter + "\n\n" + body + "\n"

    # Write output to repo
    dest_dir = REPO_ROOT / f"manifestos/london/{election_id}/{party_id}"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / "manifesto.md"

    dest_file.write_text(final_content, encoding="utf-8")
    print(f"Successfully finalized and wrote to {dest_file}")
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python finalize_london_batch.py <batch_number>")
        print("Available batches: 1, 2, 3, 4, 5, 6, 7, 8")
        sys.exit(1)

    batch_num = sys.argv[1]
    if batch_num not in BATCH_PARTIES:
        print(f"Unknown batch number: {batch_num}")
        sys.exit(1)

    election_id, parties = BATCH_PARTIES[batch_num]
    print(f"Finalizing Batch {batch_num} London manifestos ({election_id})...")
    
    success = 0
    for party_id in parties:
        # Check if draft exists first
        slug = f"manifestos__london__{election_id}__{party_id}__manifesto"
        draft_path = TOOLKIT_DIR / "work" / slug / "draft.md"
        if not draft_path.exists():
            print(f"Skipping {party_id} (no draft.md found at {draft_path.name})")
            continue
        if finalize_manifesto(party_id, election_id):
            success += 1
            
    print(f"Completed! Finalized {success} manifestos.")

if __name__ == "__main__":
    main()
