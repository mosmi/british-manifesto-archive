#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path

TOOLKIT_DIR = Path(__file__).resolve().parent

BATCH_SLUGS = {
    "1": [
        "manifestos__london__2024__sdp__manifesto",
        "manifestos__london__2024__binface__manifesto",
        "manifestos__london__2024__reform__manifesto",
        "manifestos__london__2024__awp__manifesto",
        "manifestos__london__2024__conservative__manifesto",
        "manifestos__london__2024__londonreal__manifesto"
    ],
    "2": [
        "manifestos__london__2024__michli__manifesto",
        "manifestos__london__2024__campbell__manifesto",
        "manifestos__london__2024__britainfirst__manifesto",
        "manifestos__london__2024__libdem__manifesto",
        "manifestos__london__2024__labour__manifesto",
        "manifestos__london__2024__ghulati__manifesto",
        "manifestos__london__2024__green__manifesto"
    ],
    "3": [
        "manifestos__london__2021__labour__manifesto",
        "manifestos__london__2021__conservative__manifesto",
        "manifestos__london__2021__libdem__manifesto",
        "manifestos__london__2021__green__manifesto",
        "manifestos__london__2021__londonreal__manifesto",
        "manifestos__london__2021__reclaim__manifesto",
        "manifestos__london__2021__binface__manifesto",
        "manifestos__london__2021__pierscorbyn__manifesto",
        "manifestos__london__2021__burningpink__manifesto",
        "manifestos__london__2021__maxfosh__manifesto"
    ],
    "4": [
        "manifestos__london__2004__libdem__manifesto",
        "manifestos__london__2004__green__manifesto",
        "manifestos__london__2004__cpa__manifesto"
    ],
    "5": [
        "manifestos__london__2016__labour__manifesto",
        "manifestos__london__2016__conservative__manifesto",
        "manifestos__london__2016__libdem__manifesto",
        "manifestos__london__2016__green__manifesto",
        "manifestos__london__2016__ukip__manifesto",
        "manifestos__london__2016__respect__manifesto",
        "manifestos__london__2016__wep__manifesto",
        "manifestos__london__2016__bnp__manifesto",
        "manifestos__london__2016__onelove__manifesto"
    ],
    "6": [
        "manifestos__london__2012__labour__manifesto",
        "manifestos__london__2012__conservative__manifesto",
        "manifestos__london__2012__libdem__manifesto",
        "manifestos__london__2012__green__manifesto",
        "manifestos__london__2012__bnp__manifesto",
        "manifestos__london__2012__benita__manifesto"
    ],
    "7": [
        "manifestos__london__2008__conservative__manifesto",
        "manifestos__london__2008__libdem__manifesto",
        "manifestos__london__2008__cooperative__manifesto",
        "manifestos__london__2008__green__manifesto",
        "manifestos__london__2008__englishdemocrats__manifesto"
    ],
    "8": [
        "manifestos__london__2000__livingstone__manifesto"
    ]
}

def main():
    if len(sys.argv) < 2:
        print("Usage: python batch_repair_london.py <batch_number> [--only-flagged]")
        print("Available batches: 1, 2, 3, 4, 5, 6, 7, 8")
        sys.exit(1)

    batch_num = sys.argv[1]
    if batch_num not in BATCH_SLUGS:
        print(f"Unknown batch number: {batch_num}")
        sys.exit(1)

    only_flagged = "--only-flagged" in sys.argv

    slugs = BATCH_SLUGS[batch_num]
    print(f"Starting visual page-by-page repair for Batch {batch_num} ({len(slugs)} manifestos)...")
    
    for slug in slugs:
        ledger_path = TOOLKIT_DIR / "work" / slug / "ledger.json"
        if not ledger_path.exists():
            print(f"Ledger not found for {slug}. Skipping.")
            continue
        
        print(f"\n==========================================")
        print(f"Repairing {slug}...")
        print(f"==========================================")
        
        # Run repair_manifestos_gemini.py
        cmd = [
            sys.executable,
            str(TOOLKIT_DIR / "repair_manifestos_gemini.py"),
            str(ledger_path)
        ]
        if only_flagged:
            cmd.append("--only-flagged")
            
        print(f"Running: {' '.join(cmd)}")
        res = subprocess.run(cmd)
        if res.returncode != 0:
            print(f"ERROR: repair script failed for {slug} with code {res.returncode}")
        else:
            print(f"Successfully repaired {slug}!")

    print(f"\nBatch {batch_num} repairs complete!")

if __name__ == "__main__":
    main()
