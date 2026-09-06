---
id: task-008
title: Implement September 2026 forensic audit batches
status: todo
priority: high
labels: [a11y, performance, ia, design, frontend]
created: 2026-09-06
---

## Context
The 6 Sep 2026 live-site forensic audit (61 findings) is sequenced in
[`knowledge/design/sep-2026-audit-plan.md`](../../knowledge/design/sep-2026-audit-plan.md).
Singular URLs: [`knowledge/architecture/url-scheme.md`](../../knowledge/architecture/url-scheme.md).
Header: Elections / Parties / Nations / About
([nations-vs-devolved](../../knowledge/design/nations-vs-devolved.md)). Do **not**
implement the audit’s plural URL table.

Ship **one batch per PR**. Finding IDs in commit messages.

## Acceptance criteria
- [x] **Batch 0** — `_headers` on versioned JS/CSS; hero manifesto count; inline link underline; no bogus `role="menu"`; “Not yet digitised”; `aria-current`; brand wordmark (**1.1**, **3.1**, **3.2**, **3.8**, **4.4**, **5.1**, **5.9**)
- [x] **Batch 1** — cover 404s gone; WebP thumbs beside canonical PNGs; CLS dimensions; JSON dedupe; route-loaded JS + self-hosted `marked`; subset self-hosted fonts (**4.1–4.7**)
- [x] **Batch 2** — AA party tags; mobile results table shows votes; list/`h2` semantics; search trap re-checked; hit targets; forced-colors; hemicycle label; no duplicate card links (**3.3–3.7**, **3.9–3.11**)
- [x] **Batch 3** — `--fs-*` / spacing / radius tokens and the listed polish items; skip **1.9** glyph redesign (**1.2–1.8**, **1.10–1.14**)
- [x] **Batch 4** — singular URL scheme live (301s, sitemap, middleware, SPA); four-slot header (Elections, Parties, Nations, About); mobile nav matches desktop; Europe not a nation; NI flag; `/party/other`; related parties; smart 404s (**2.1–2.6**, **2.10–2.13**, **4C in the same PR**)
- [x] **Batch 5** — real titles, provenance, trust copy, citation styles, `/search`, sticky rails (**5.2–5.5**, **5.10**, **5.12**, **2.7**, **2.8**)
- [ ] **Batch 6** — RSS, dated additions, `/wanted`, reading-copy PDFs (**5.6–5.8**, **4.8**)

## Test plan
Per batch, follow the **Verify** section in the plan. After any JS/CSS/cover change, bump `?v=` / `ASSETS_VERSION`. After adding files, run `python3 scripts/check-cloudflare-limits.py`. UI batches: home, one election, one manifesto, one party, light and dark where relevant.

## Handoff log
- 2026-09-06 — Elections menu: drop 420px max-height so Westminster subtitle does not scroll (Cursor Grok). Assets `?v=2026090628`. User has not asked to commit.
- 2026-09-06 — Nav: England mega left rule + Elections Westminster subtitle (Cursor Grok). Assets `?v=2026090627`. User has not asked to commit.
- 2026-09-06 — Euro covers on `/manifesto` + axis padding (Cursor Grok). Assets `?v=2026090621`. Hub tiles use `manifesto.png` for European Parliament folders. 1945/2026 labels sit in side padding. User has not asked to commit.
- 2026-09-06 — Density axis labels 1950 and 2020 (Cursor Grok). Assets `?v=2026090620`. User has not asked to commit.
- 2026-09-06 — `/manifesto` density hover + calendar ticks (Cursor Grok). Assets `?v=2026090619`. Axis is decades on the timeline (not “years with a bar that are multiples of 20”). Hover/focus shows year · count. User has not asked to commit.
- 2026-09-06 — `/manifesto` cover wall (Cursor Grok). Assets `?v=2026090618`. Completes the singular URL scheme; **not Batch 6**. Four-slot header unchanged. Footer + home Ways in + 404 list Manifestos. `/manifestos` 301. User has not asked to commit.
- 2026-09-06 — Nav split: hub link vs chevron submenu (Cursor Grok). Assets `?v=2026090617`. User has not asked to commit.
- 2026-09-06 — Mobile drawer accordion + footer IA (Cursor Grok). Assets `?v=2026090616`. Drawer no longer dumps both megas; footer is Home / Elections / Parties / Nations / About. User has not asked to commit.
- 2026-09-06 — Homepage hero: dropped subtitle + trust paragraph (Cursor Grok). Assets `?v=2026090614`. Stat row stays. User has not asked to commit.
- 2026-09-06 — `/search` duplicate Catalogue/Full text toggles (Cursor Grok). Assets `?v=2026090613`. Page form owns the only on-page pair; results no longer inject a second. Overlay ⌘K still has its own. User has not asked to commit.
- 2026-09-06 — Batch 5 titles + TOC (Cursor Grok). Assets `?v=2026090613`. Wikipedia slogans for Lab/Con/LD; 1979 Conservative cover line; generic H1 fallback (Natural Law 1997). SEO `{Party} manifesto {Year} — {slogan}`. Mobile TOC list scrolls inside a 60vh cap. User has not asked to commit.
- 2026-09-06 — Batch 5 (Cursor Grok). Assets `?v=2026090610`. Titles from `scripts/build-manifesto-titles.py`. Reader H1 + cite + provenance. Home hero 659/71 + trust line. `/search?q=` SPA + SearchAction. Sticky rails. Regenerated seo/sitemap/latest-additions. Do not start Batch 6 until this is on `main`. User has not asked to commit.
- 2026-09-06 — Batch 4 (Cursor Grok). Assets `?v=2026090608`. Singular hubs + 301s; four-slot header; Europe → `/party/european-groups`; NI without 🇮🇪; related parties; guessable 404s. Sitemap/seo/catalog regenerated. Verified 301s locally; browser pass `/`, `/election`, `/party/labour`, `/nation`, `/nation/northern-ireland`, `/election/1997`, `/manifesto/1997/labour`, 375 drawer, light theme. Do not start Batch 5 until this is on `main`. User has not asked to commit.
- 2026-09-06 — Batch 3 (Cursor Grok). Assets `?v=2026090607`. Tokens in `styles.css` / [tokens](../../knowledge/design/tokens.md). **1.2–1.6** type/space/radius/shadow; **1.3** 11px floor + UI for tracked caps; **1.4** UI/display/body + `→`; **1.7** mega inset; **1.8** nations 2×2/4-col; **1.10** latest covers first; **1.11** four ways as links; **1.12** nbsp before “manifestos”; **1.13** 2×2 stats at 375; **1.14** light gold `#7a5f24`. Skipped **1.9**. Verified `/`, `/nations`, `/election/1997`, `/party/labour`, `/manifesto/1997/labour`. Do not start Batch 4 until this is on `main`. User has not asked to commit.
- 2026-09-06 — Batch 2 (Cursor Grok). Assets `?v=2026090606`. **3.3** letter `h2` + `<ul>` on `/parties/all`; **3.4** ink/border tags + winner badge; **3.5** `.results-scroll` (Votes + Vote % at 375px); **3.6** 44px chrome / 24px legend; **3.7** trap holds (`inert` on nav/app/footer/skip-link, Tab cycle, Escape); **3.9** `forced-colors`; **3.10** SVG `<desc>` + legend list; **3.11** `manifestoCardShell`. Verified `/`, `/election/1997`, `/parties/all`, both themes. Do not start Batch 3 until this is on `main`. User has not asked to commit.
- 2026-09-06 — Batch 1 (Cursor Grok). Assets `?v=2026090605`. 1222 WebP thumbs; self-hosted Latin fonts; `marked.min.js`; `fetchTyped` memo + `?v=`; homepage accordion indexes only ≤1024px; chamber JS on devolved/party routes; search extras via `fetchTyped` on overlay open. Limits script: 8736 files. Do not start Batch 2 until this is on `main`. User has not asked to commit.
- 2026-09-06 — Header collision fix (Cursor Grok): two-line nowrap wordmark; hamburger from 1100px. Assets `?v=2026090604`.
- 2026-09-06 — Header wordmark wraps below 1400px (Cursor Grok). Assets `?v=2026090603`. Batch 0 still the current batch; next remains Batch 1.
- 2026-09-06 — Batch 0 verified (Cursor Grok). Assets `?v=2026090602`. Parties `/parties/all` now sets `aria-current` on the Parties button. Local preview does not apply `_headers` (Cloudflare will). Next: Batch 1.
- 2026-09-06 — I04/I08 reopened: four-slot header is in scope for Batch 4. WebP thumbs beside PNGs confirmed. No code yet. Start at Batch 0.
- 2026-09-06 — Plan recorded (Cursor Grok). No code yet. Start at Batch 0.
