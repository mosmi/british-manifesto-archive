#!/usr/bin/env python3
"""Copy audit-missing PDFs into manifestos/ and generate transparent A4 covers."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = Path("/Users/mosmi/Claude/Projects/Manifestos/Original documents")

# (electionId, partyId, source relative to Original documents, index label)
# Skip 2019 Brexit Party — already published as reform.
ITEMS: list[tuple[str, str, str, str]] = [
    ("1979", "sdlp", "1979 General election/SDLP 1979 manifesto.pdf", "SDLP Manifesto 1979"),
    ("1992", "sdlp", "1992 General election/SDLP 1992 manifesto.pdf", "SDLP Manifesto 1992"),
    ("1997", "niwc", "1997 General election/Northern Ireland Women's Coalition 1997 manifesto.pdf", "Northern Ireland Women's Coalition Manifesto 1997"),
    ("1997", "pup", "1997 General election/PUP 1997 manifesto.pdf", "Progressive Unionist Party Manifesto 1997"),
    ("2001", "stuckist", "2001 General election/Stuckist 2001 manifesto.pdf", "Stuckist Party Manifesto 2001"),
    ("2001", "welshlibdem", "2001 General election/Liberal Democrats/Welsh Liberal Democrats 2001 manifesto.pdf", "Welsh Liberal Democrats Manifesto 2001"),
    ("2005", "cpa", "2005 General election/Christian Peoples Alliance 2005 manifesto.pdf", "Christian Peoples Alliance Manifesto 2005"),
    ("2005", "englishdemocrats", "2005 General election/English Democrats 2005 manifesto.pdf", "English Democrats Manifesto 2005"),
    ("2005", "forwardwales", "2005 General election/Forward Wales 2005 manifesto.pdf", "Forward Wales Manifesto 2005"),
    ("2005", "sea", "2005 General election/Socialist Environmental Alliance 2005 manifesto.pdf", "Socialist Environmental Alliance Manifesto 2005"),
    ("2005", "veritas", "2005 General election/Veritas 2005 manifesto.pdf", "Veritas Manifesto 2005"),
    ("2015", "animalpolitics", "2015 General election/Animal Welfare Party 2015 manifesto.pdf", "Animal Welfare Party Manifesto 2015"),
    ("2015", "nicon", "2015 General election/Conservatives NI 2015 manifesto.pdf", "NI Conservatives Manifesto 2015"),
    ("2015", "nha", "2015 General election/National Health Action Party 2015 manifesto.pdf", "National Health Action Manifesto 2015"),
    ("2015", "ssp", "2015 General election/Scottish Socialist Party 2015 manifesto.pdf", "Scottish Socialist Party Manifesto 2015"),
    ("2015", "socialistalternative", "2015 General election/Socialist Alternative 2015 manifesto.pdf", "Socialist Alternative Manifesto 2015"),
    ("2015", "tusc", "2015 General election/Trade Union and Socialist Coalition 2015 manifesto.pdf", "TUSC Manifesto 2015"),
    # NI Workers' Party (not Workers Party of Britain, founded 2019)
    ("2015", "workerspartyie", "2015 General election/Workers Party 2015 manifesto.pdf", "Workers' Party Manifesto 2015"),
    ("2017", "animalpolitics", "2017 General election/Animal Welfare Party 2017 manifesto.pdf", "Animal Welfare Party Manifesto 2017"),
    ("2017", "nicon", "2017 General election/Conservatives NI 2017 manifesto.pdf", "NI Conservatives Manifesto 2017"),
    ("2017", "scottishgrn", "2017 General election/Scottish Greens 2017 manifesto.pdf", "Scottish Greens Manifesto 2017"),
    ("2019", "animalpolitics", "2019 General election/Animal Welfare Party 2019 manifesto.pdf", "Animal Welfare Party Manifesto 2019"),
    ("2019", "cpa", "2019 General election/Christian Peoples Alliance 2019 manifesto.pdf", "Christian Peoples Alliance Manifesto 2019"),
    ("2019", "gwlad", "2019 General election/Gwlad Gwlad 2019 manifesto.pdf", "Gwlad Manifesto 2019"),
    ("2019", "sdp", "2019 General election/SDP-Policy-2019.pdf", "Social Democratic Party Manifesto 2019"),
    ("2019", "yorkshire", "2019 General election/Yorkshire Party 2019 manifesto.pdf", "Yorkshire Party Manifesto 2019"),
    ("2024", "animalpolitics", "2024 General election/Animal Welfare Party 2024 manifesto.pdf", "Animal Welfare Party Manifesto 2024"),
    ("2024", "aontu", "2024 General election/Aontu 2024 manifesto.pdf", "Aontú Manifesto 2024"),
    ("2024", "cpa", "2024 General election/Christian Peoples Alliance 2024 manifesto.pdf", "Christian Peoples Alliance Manifesto 2024"),
    ("2024", "communist", "2024 General election/Communist Party of Britain 2024 manifesto.pdf", "Communist Party of Britain Manifesto 2024"),
    ("2024", "nicon", "2024 General election/Northern Ireland Conservative Party cp_2024-07-04_ge_man.pdf", "NI Conservatives Manifesto 2024"),
    ("2024", "pbp", "2024 General election/People Before Profit 2024 manifesto.pdf", "People Before Profit Manifesto 2024"),
    ("2024", "rejoin", "2024 General election/Rejoin EU Party 2024 manifesto.pdf", "Rejoin EU Manifesto 2024"),
    ("2024", "sdp", "2024 General election/Social Democratic Party 2024 manifesto.pdf", "Social Democratic Party Manifesto 2024"),
    ("2024", "tusc", "2024 General election/Trade Unionist and Socialist Coalition 2024 manifesto.pdf", "TUSC Manifesto 2024"),
    ("2024", "walesgrn", "2024 General election/Wales Green Party 2024 manifesto.pdf", "Wales Green Party Manifesto 2024"),
    (
        "london/2008",
        "englishdemocrats",
        "Devolved Elections/London/2008 London Devolved Election/Matt OConnor English Democrats - EDP UK manifesto.pdf",
        "English Democrats Manifesto 2008 (London)",
    ),
]

W, H = 1191, 1684


def make_cover(pdf: Path, cover: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        prefix = tmp_path / "page"
        subprocess.run(
            ["pdftoppm", "-png", "-f", "1", "-l", "1", "-r", "200", str(pdf), str(prefix)],
            check=True,
        )
        pages = sorted(tmp_path.glob("page*.png"))
        if not pages:
            raise RuntimeError(f"pdftoppm produced no page for {pdf}")
        prepared = tmp_path / "prepared.png"
        subprocess.run(["magick", str(pages[0]), "-auto-orient", str(prepared)], check=True)
        # Transparent A4 canvas (contain) — see knowledge/pipelines/covers.md
        subprocess.run(
            [
                "magick",
                str(prepared),
                "-resize",
                f"{W}x{H}",
                "-background",
                "none",
                "-gravity",
                "center",
                "-extent",
                f"{W}x{H}",
                f"PNG32:{cover}",
            ],
            check=True,
        )


def dest_dir(election_id: str, party_id: str) -> Path:
    if election_id.startswith("london/"):
        return ROOT / "manifestos" / election_id / party_id
    return ROOT / "manifestos" / election_id / party_id


def main() -> None:
    for election_id, party_id, rel, _label in ITEMS:
        src = SRC_ROOT / rel
        if not src.is_file():
            raise FileNotFoundError(src)
        out = dest_dir(election_id, party_id)
        out.mkdir(parents=True, exist_ok=True)
        pdf = out / "manifesto.pdf"
        if not pdf.exists() or pdf.stat().st_size != src.stat().st_size:
            shutil.copy2(src, pdf)
            print(f"copied {election_id}/{party_id}")
        else:
            print(f"pdf ok {election_id}/{party_id}")
        cover = out / "cover.png"
        if not cover.exists():
            make_cover(pdf, cover)
            print(f"  cover {election_id}/{party_id}")
        else:
            print(f"  cover ok {election_id}/{party_id}")


if __name__ == "__main__":
    main()
