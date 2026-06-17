import os
import shutil
import subprocess
import re

SRC_DIR = "/Users/mosmi/Claude/Projects/Manifestos/Original documents/European Elections"
DEST_DIR = "/Users/mosmi/Documents/Antigravity/Projects/british-manifesto-archive/manifestos/euro"

PARTY_MAPPING = [
    (r"Labour.*Transforming", "labour"),
    (r"Scottish Labour", "scottishlab"),
    (r"Labour", "labour"),
    (r"Conservastive", "conservative"),
    (r"Scottish Conservatives", "scottishcon"),
    (r"Welsh Conservatives", "welshcon"),
    (r"Conservative", "conservative"),
    (r"Welsh Liberal Democrat", "welshlibdem"),
    (r"Liberal Democrat", "libdem"),
    (r"Green Party", "green"),
    (r"Scottish Greens", "scottishgrn"),
    (r"Greens NI", "gpni"),
    (r"Green", "green"),
    (r"UKIP", "ukip"),
    (r"DUP", "dup"),
    (r"SDLP", "sdlp"),
    (r"SNP", "snp"),
    (r"Sinn Fein", "sinnfein"),
    (r"Sein Fein", "sinnfein"),
    (r"UUP", "uup"),
    (r"PES", "pes"),
    (r"ELDR", "eldr"),
    (r"Alliance Party", "alliance"),
    (r"Animal Politics", "animalpolitics"),
    (r"Change UK", "changeuk"),
    (r"Plaid Cymru", "plaid"),
    (r"English Democrats", "englishdemocrats"),
    (r"Womens Equality", "wep"),
    (r"BNP", "bnp"),
    (r"TUV", "tuv"),
    (r"Scottish Socialist", "ssp"),
    (r"Socialist Environmental", "sea"),
    (r"Christian Party", "christian")
]

def get_party_id(filename):
    for pattern, party_id in PARTY_MAPPING:
        if re.search(pattern, filename, re.IGNORECASE):
            return party_id
    return None

def process_elections():
    for root, dirs, files in os.walk(SRC_DIR):
        # Determine the election year from the folder name
        # e.g., '1999 European Parliament election'
        dir_name = os.path.basename(root)
        year_match = re.search(r"(\d{4})", dir_name)
        if not year_match:
            # Let's check parent folder name if we are inside a subfolder
            parent_dir_name = os.path.basename(os.path.dirname(root))
            year_match = re.search(r"(\d{4})", parent_dir_name)
            if not year_match:
                continue
        
        year = year_match.group(1)
        
        for f in files:
            if not f.endswith(".pdf"):
                continue
            
            # Ignore general reference documents or candidate lists
            if f.startswith("z ") or "candidates" in root.lower() or "region" in root.lower():
                print(f"Skipping reference doc: {f}")
                continue
                
            party_id = get_party_id(f)
            if not party_id:
                print(f"Unknown party in filename: {f}")
                continue
                
            target_party_dir = os.path.join(DEST_DIR, year, party_id)
            os.makedirs(target_party_dir, exist_ok=True)
            
            # Prepare clean target name
            # Handle multiple parts for SDLP 2004
            clean_name = "manifesto.pdf"
            if "pt 1" in f.lower() or "pt1" in f.lower():
                clean_name = "manifesto-pt1.pdf"
            elif "pt 2" in f.lower() or "pt2" in f.lower():
                clean_name = "manifesto-pt2.pdf"
            elif "Transforming" in f:
                clean_name = "manifesto-transforming.pdf"
            elif "flyer" in f.lower():
                clean_name = "flyer.pdf"
                
            target_pdf_path = os.path.join(target_party_dir, clean_name)
            src_pdf_path = os.path.join(root, f)
            
            print(f"Copying {f} -> {year}/{party_id}/{clean_name}")
            shutil.copy2(src_pdf_path, target_pdf_path)
            
            # Generate cover image name matching the clean PDF name
            cover_name = clean_name.replace(".pdf", ".png")
            target_cover_path = os.path.join(target_party_dir, cover_name)
            
            # Execute ImageMagick command to extract the first page
            # density 150, quality 90, page [0]
            # e.g., magick -density 150 'input.pdf[0]' -quality 90 'output.png'
            try:
                cmd = ["magick", "-density", "150", f"{target_pdf_path}[0]", "-quality", "90", target_cover_path]
                print(f"Generating cover: {' '.join(cmd)}")
                subprocess.run(cmd, check=True)
            except Exception as e:
                print(f"Error generating cover for {target_pdf_path}: {e}")

if __name__ == "__main__":
    process_elections()
