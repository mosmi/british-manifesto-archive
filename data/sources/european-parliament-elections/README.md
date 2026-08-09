# European Parliament election sources: United Kingdom, 1979–2019

Downloaded and indexed on 9 August 2026.

This bundle collects the official material found during research into UK European Parliament election results before 2019. It combines House of Commons Library workbooks and briefing links, Electoral Commission data, the European Parliament's historical CSV archive, and a Greater London Authority local-results dataset.

## Quick guide

| Folder / File | Contents | Coverage |
|---|---|---|
| `constituency-winners-1979-1994.json` | Single-member constituency winner lists and NI STV winners for FPTP-era EP elections | 1979–1994 |
| `westminster-to-ep/{1979,1984,1994}.json` | Westminster→EP constituency compositions + hex centroids (1989 reuses 1984) | 1979–1994 |
| `commons-library/` | The 2019 results briefing and Excel workbook; the Commons Library's historical elections workbook | 1979–2019 |
| `electoral-commission/` | Detailed 2014 electoral data workbook and accompanying report | 2014 |
| `european-parliament/` | UK, Great Britain and Northern Ireland CSV data; signatures; certificates | 1979–2019 |
| `other-official-sources/london-2009/` | GLA borough-level XLS/CSV data and report | 2009 |

## House of Commons Library

### Files saved locally

| Local file | Description | Original source |
|---|---|---|
| `commons-library/CBP-8600-European-Parliament-elections-2019.pdf` | *European Parliament elections 2019: results and analysis* | [Briefing page](https://commonslibrary.parliament.uk/research-briefings/cbp-8600/) · [PDF](https://researchbriefings.files.parliament.uk/documents/CBP-8600/CBP-8600.pdf) |
| `commons-library/CBP-8600-data.xlsx` | Detailed data workbook accompanying CBP-8600 | [Excel workbook](https://researchbriefings.files.parliament.uk/documents/CBP-8600/CBP_data.xlsx) |
| `commons-library/CBP-7529-EP-and-devolved-legislatures.xlsx` | Historical European Parliament and devolved-legislature election results. The `1. EP-GB` and `2. EP-NI` sheets give party votes, shares, seats and turnout for every European election from 1979 to 2019; Northern Ireland figures are first preferences. | [Briefing page](https://commonslibrary.parliament.uk/research-briefings/cbp-7529/) · [Excel workbook](https://researchbriefings.files.parliament.uk/documents/CBP-7529/EP-and-devolved-legislatures.xlsx) |

### Earlier results briefings

PDFs are stored under `commons-library/` (used by `scripts/build-euro-regions-pr.py` for the PR-era regional maps). Official links are retained below.

| Election(s) | Local file | Briefing page |
|---:|---|---|
| 2014 | `commons-library/RP14-32.pdf` | [RP14-32](https://commonslibrary.parliament.uk/research-briefings/rp14-32/) |
| 2009 | `commons-library/RP09-53.pdf` | [RP09-53](https://commonslibrary.parliament.uk/research-briefings/rp09-53/) |
| 2004 | `commons-library/RP04-50.pdf` | [RP04-50](https://commonslibrary.parliament.uk/research-briefings/rp04-50/) |
| 1999 | `commons-library/RP99-64.pdf` | [RP99-64](https://commonslibrary.parliament.uk/research-briefings/rp99-64/) |
| 1979–1994 | `commons-library/RP99-57.pdf` | [RP99-57](https://commonslibrary.parliament.uk/research-briefings/rp99-57/) |

## Electoral Commission: 2014

| Local file | Description | Original source |
|---|---|---|
| `electoral-commission/EPE-2014-Electoral-data.xlsx` | Detailed results and administration data. Sheets include `Results`, `Administration`, `Party names` and notes; the results are broken down by counting area. | [Excel workbook](https://www.electoralcommission.org.uk/sites/default/files/2019-07/EPE-2014-Electoral-data.xlsx) |
| `electoral-commission/European-Parliament-Elections-2014-Electoral-data-report.pdf` | Accompanying electoral data report | [PDF](https://www.electoralcommission.org.uk/sites/default/files/2019-07/European-Parliament-Elections-2014-Electoral-data-report.pdf) |

Dataset page: [Results and turnout at the 2014 European Parliamentary elections](https://www.electoralcommission.org.uk/research-reports-and-data/our-reports-and-data-past-elections-and-referendums/results-and-turnout-2014-european-parliamentary-elections).

## European Parliament historical results archive

Source: [Download historical result data](https://results.elections.europa.eu/en/tools/download-datasheets/).

The folders map election years to the European Parliament's parliamentary-term labels:

| Election year | Local folder | European Parliament period |
|---:|---|---|
| 1979 | `european-parliament/1979/` | 1979–1984 |
| 1984 | `european-parliament/1984/` | 1984–1989 |
| 1989 | `european-parliament/1989/` | 1989–1994 |
| 1994 | `european-parliament/1994/` | 1994–1999 |
| 1999 | `european-parliament/1999/` | 1999–2004 |
| 2004 | `european-parliament/2004/` | 2004–2009 |
| 2009 | `european-parliament/2009/` | 2009–2014 |
| 2014 | `european-parliament/2014/` | 2014–2019 |
| 2019 | `european-parliament/2019/` | 2019–2024 |

Each election-year folder contains:

| Filename pattern | Content |
|---|---|
| `groups.csv` | European political-group labels and metadata |
| `parties.csv` | National-party labels and metadata |
| `seats-breakdown-groups-{uk,gb,ni}.csv` | Seats by European political group |
| `seats-breakdown-parties-{uk,gb,ni}.csv` | Seats by national party |
| `results-parties-{uk,gb,ni}.csv` | Vote percentages by national party |
| `*.sig` | European Parliament cryptographic signature corresponding to each CSV |

The `common/` folder contains `labels.csv`, EU- and country-level turnout series, their signatures, and the certificate files supplied by the European Parliament.

The CSV files use semicolons as separators. Vote-percentage rows exist for all periods, but the European Parliament leaves the percentage field blank for some earlier elections; the seat-breakdown files still contain the historical seat data. UK, GB and NI variants are retained even where rows overlap so that the archive mirrors the website's available national selections.

Example page supplied during the research: [United Kingdom, 1979 constitutive session](https://results.elections.europa.eu/en/national-results/united-kingdom/1979-1984/constitutive-session/).

## Greater London Authority: 2009 local results

| Local file | Description | Original source |
|---|---|---|
| `other-official-sources/london-2009/european-elections-votes-party-borough-2009.xls` | Party votes by London borough | [XLS](https://data.london.gov.uk/download/vqnmn/8999a5a5-effb-4e02-8550-7e016f37f847/european-elections-votes-party-borough-2009.xls) |
| `other-official-sources/london-2009/european-elections-votes-party-borough-2009.csv` | CSV version of the borough results | [CSV](https://data.london.gov.uk/download/vqnmn/6974bb4d-6b6e-4426-91b3-eefe91854efb/european-elections-votes-party-borough-2009.csv) |
| `other-official-sources/london-2009/European-elections-2009-London-report.pdf` | GLA report, *2009 European election results for London* | [PDF](https://data.london.gov.uk/download/vqnmn/70e692b0-d621-4740-b338-fa343587914c/European-elections-2009.pdf) |

Dataset page: [European Election Results 2009 — London Datastore](https://data.london.gov.uk/dataset/european-election-results-2009-vqnmn/).

## FPTP constituency maps (site pipeline)

Site hexmaps for 1979–1994 are built from this folder:

```bash
python3 scripts/build-euro-fptp-crosswalk.py   # compositions + centroids
python3 scripts/build-euro-fptp-hex.py         # → data/hex/euro/{1979,1984,1989,1994}.hexjson
```

See [knowledge/pipelines/euro-region-map.md](../../../knowledge/pipelines/euro-region-map.md).

## Practical coverage note

For a consistent UK-wide series, start with the Commons Library historical workbook. For detailed 2014 counting-area results, use the Electoral Commission workbook. The European Parliament CSV archive is best for consistent national party/seat metadata across all nine elections. The GLA files add borough-level detail for London in 2009. Constituency winners for the FPTP era live in `constituency-winners-1979-1994.json` (cross-checked against RP99-57 / EUI constituency results).
