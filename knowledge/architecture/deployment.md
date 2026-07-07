---
type: runbook
title: Cloudflare deployment
description: How www.manifestos.org.uk is built and served, and the Workers/Pages pitfall that silently breaks deploys.
resource: https://dash.cloudflare.com
tags: [deploy, cloudflare, ops]
timestamp: 2026-07-05T00:00:00Z
---

# Deployment

Static site, **no build step**, deployed to Cloudflare on push to `main`.
Git remote: `github.com/mosmi/british-manifesto-archive`.

## The one critical gotcha
The custom domain **www.manifestos.org.uk** must be attached to the *same*
Cloudflare project that receives git deploys — **Workers or Pages, never both.**

If both a Workers project (`npx wrangler deploy`) and a Pages project (`*.pages.dev`)
are connected to the repo, only one receives each push. Symptoms of a mismatch:
- `british-manifesto-archive.pages.dev` shows new features but the live domain doesn't
- Direct URLs like `/election/2024` render a blank page (stale/mismatched JS)

**Fix:** Cloudflare → Workers & Pages → open each project → Custom domains. Remove the
domain from the stale project, attach it to the one that deploys from Git, then
Caching → Configuration → Purge Everything.

## Two valid setups
- **Workers (current):** Build command *(empty)*, Deploy command `npx wrangler deploy`,
  Root `/`. `wrangler.toml` uploads the repo root as static assets
  (`[assets] directory = "./"`); `.assetsignore` excludes `.git/`, `scripts/`, etc.
- **Pages (alternative):** Framework preset **None**, Build command *(empty)*, Build
  output dir **`.`**, Deploy command *(empty — do NOT use `npx wrangler deploy`)*.

## Before deploying
```bash
python3 scripts/check-cloudflare-limits.py   # 25 MiB/file, 20,000 files/site (free plan)
```

## Verify a deploy actually shipped
Open `https://www.manifestos.org.uk/js/app.js?v=…` and search for the newest function
name (e.g. `renderNationsHub`). If it's missing, the live site is still on an older
build even though `main` is up to date.

## After deploying
Hard-refresh (Shift+Reload) or purge Cloudflare cache. See
[cache-busting](./cache-busting.md) for the `?v=` rule.

## robots.txt
The committed `robots.txt` includes `Sitemap:` and `Llms-Txt:` pointers. If
Cloudflare **managed robots.txt** is enabled in the dashboard, it may override
the committed file — disable it so the repo version is served. See
[structured-data](./structured-data.md).
