---
type: runbook
title: Manifesto titles
description: Resolve published manifesto titles into data/manifesto-titles.json. Slogan years use Wikipedia for the three main Westminster parties; otherwise the document heading. Never use “Published without a distinct title”.
tags: [pipelines, titles, citation]
timestamp: 2026-09-06T00:00:00Z
---

# Manifesto titles

Audit **5.2**: reader H1, citations, catalogue search, and `llms.txt` use a
**real title**. Distinctive slogans appear as a second line on cards.
`<title>` / SEO lead with `{Party} manifesto {Year}` so “Labour 2019 manifesto”
matches; the slogan follows after an em dash when it is distinctive.

## Sources (first match wins)

1. YAML `document_title:` on `manifesto.md`
2. Curated Westminster titles in
   [`data/manifesto-titles-curated.json`](../../data/manifesto-titles-curated.json)
   — Labour, Conservative, and Liberal/Alliance/Lib Dem slogan years from
   Wikipedia’s manifesto lists. **1979 Conservative** uses the cover line
   *The Conservative manifesto 1979*, not Wikipedia’s generic catalogue heading.
   If the markdown heading is the same words, keep the document’s casing.
3. Distinctive `#` / opening italic / bold / first non-generic `##` in
   `manifesto.md`
4. The document’s own generic H1 (`Natural Law Party Manifesto 1997`)
5. `{party_name} Manifesto {year}` from YAML

Never output “Published without a distinct title”.

Wikipedia lists (three main parties only — not territorial siblings):

- [Labour](https://en.wikipedia.org/wiki/List_of_Labour_Party_(UK)_general_election_manifestos)
- [Conservative](https://en.wikipedia.org/wiki/List_of_Conservative_Party_(UK)_general_election_manifestos)
- [Liberal / Lib Dem](https://en.wikipedia.org/wiki/List_of_Liberal_Party_and_Liberal_Democrats_(UK)_general_election_manifestos)

## Generator

```
python3 scripts/build-manifesto-titles.py
python3 scripts/build-manifesto-titles.py --stats
```

Writes [`data/manifesto-titles.json`](../../data/manifesto-titles.json):

```json
{ "title": "The New Hope for Britain", "source": "wikipedia", "distinctive": true }
```

`distinctive: false` means a conventional party-and-year title (H1 or cover).
Cards omit that extra line; the reader H1 still uses it.

Run this **before** `build-seo-data.py` and `build-latest-additions.py`. The SPA
loads the JSON at boot (`initManifestoTitles` in `js/app.js`).

## Explicit overrides

Add `document_title: "…"` to YAML when Wikipedia and the cover/text disagree
and you are not adding a curated row. Do not invent slogans that never appeared
on the document.
