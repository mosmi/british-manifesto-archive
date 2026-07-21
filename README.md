# The British Manifesto Archive

A static web archive of UK general election manifestos, results, and maps (1945–2024).

## Local preview

Use the SPA-aware preview so deep links (`/elections`, `/party/…`, etc.) work on
hard refresh — same idea as Cloudflare `_redirects`:

```bash
python3 scripts/serve-preview.py
```

Open [http://127.0.0.1:8888/](http://127.0.0.1:8888/). See
[`knowledge/architecture/local-preview.md`](knowledge/architecture/local-preview.md).

## Deploy to Cloudflare

### Option A — Workers (current setup)

If your Cloudflare project says **“Connect your Worker to a Git repository”** and shows **Deploy command: `npx wrangler deploy`**, you created a **Workers** project. That is fine for this static site.

Keep these dashboard settings:

| Setting | Value |
|---------|-------|
| **Build command** | *(empty)* |
| **Deploy command** | `npx wrangler deploy` |
| **Root directory** | `/` |

`wrangler.toml` tells Wrangler to upload the repo root as static assets (`[assets] directory = "./"`). `.assetsignore` excludes `.git/`, `scripts/`, and other non-public files from the upload.

### Option B — Pages (alternative)

For the classic Pages UI (Framework preset, Build output directory):

1. **Workers & Pages** → **Create** → choose the **Pages** tab (not Workers)
2. **Import an existing Git repository** → select this repo
3. Framework preset: **None**, Build command: *(empty)*, Build output directory: **`.`**

### After connecting Git

Push to `main` (or **Deployments → Retry deployment**). The site will be served from your `*.pages.dev` URL.

**Pages build settings must be:**

| Setting | Value |
|---|---|
| Framework preset | **None** |
| Build command | *(empty)* |
| Build output directory | **`.`** |
| Deploy command | *(empty — do not use `npx wrangler deploy`)* |

If the deploy command is still `npx wrangler deploy` from an old Workers setup, Git pushes will land on GitHub but **will not update the live site**. Check **Deployments** for failed builds after each push.

### Before deploying

```bash
python3 scripts/check-cloudflare-limits.py
```

This checks Cloudflare’s **25 MiB per-file** and **20,000 files per site** (free plan) limits.

### Custom domain

Attach **www.manifestos.org.uk** to the **same** Cloudflare project that receives your Git deploys (Workers *or* Pages — not both).

If you have both a **Workers** project (`npx wrangler deploy`) and a **Pages** project (`*.pages.dev`) connected to the same repo, only one will receive each push. Symptoms of a mismatch:

- `british-manifesto-archive.pages.dev` shows new features but `www.manifestos.org.uk` does not
- Direct URLs like `/election/2024` render a blank page (stale or mismatched JS)

**Fix:** In Cloudflare → **Workers & Pages**, open each project → **Custom domains**. Remove the domain from the stale project and attach it to the one that deploys successfully from Git. Then **Caching → Configuration → Purge Everything**.

### After deploying

Hard-refresh the site (Shift+Reload) or purge Cloudflare cache so updated assets are served. `index.html` uses a `?v=` query string on `styles.css` and `js/*.js` — bump that date when you need to force browsers to reload CSS/JS.

**Verify a deploy succeeded:** open `https://www.manifestos.org.uk/js/app.js?v=…` and search for `renderNationsHub`. If it is missing, the live site is still on an older build even though `main` on GitHub is up to date.
