import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

for year in [1999, 2003, 2007, 2011, 2016, 2021]:
    json_path = ROOT / "data" / "devolved" / "senedd" / f"{year}.json"
    hex_path = ROOT / "data" / "hex" / "senedd" / f"{year}.hexjson"
    
    if not json_path.exists() or not hex_path.exists():
        print(f"Year {year}: files missing")
        continue
        
    db_data = json.loads(json_path.read_text())
    hex_data = json.loads(hex_path.read_text())
    
    # DB results
    db_seats = {}
    for r in db_data["parliament"]["results"]:
        p_id = r.get("party", "others")
        db_seats[p_id] = r["seats"]
        
    # HexJSON results (FPTP constituencies + regional lists)
    hex_seats = {}
    for cell in hex_data["hexes"].values():
        p = cell.get("party", "others")
        hex_seats[p] = hex_seats.get(p, 0) + 1
        
    if "regional_list" in hex_data:
        for reg in hex_data["regional_list"]:
            for m in reg["members"]:
                p = m["party"]
                hex_seats[p] = hex_seats.get(p, 0) + 1
                
    # Compare
    print(f"=== Senedd {year} ===")
    all_parties = set(list(db_seats.keys()) + list(hex_seats.keys()))
    has_mismatch = False
    for p in sorted(all_parties):
        db_val = db_seats.get(p, 0)
        hex_val = hex_seats.get(p, 0)
        if db_val != hex_val:
            print(f"  Party '{p}': DB={db_val}, Hex={hex_val}  <-- MISMATCH")
            has_mismatch = True
        else:
            print(f"  Party '{p}': DB={db_val}, Hex={hex_val}")
    if not has_mismatch:
        print("  All match perfectly!")
