# The British Manifesto Archive

A static web archive of UK general election manifestos, results, and maps (1945–2024).

## Local preview

```bash
python3 -m http.server 8888 --bind 127.0.0.1
```

Open [http://127.0.0.1:8888/](http://127.0.0.1:8888/).

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

Push to `main` (or **Deployments → Retry deployment**). The site will be served from your `*.workers.dev` or `*.pages.dev` URL.

### Before deploying

```bash
python3 scripts/check-cloudflare-limits.py
```

This checks Cloudflare’s **25 MiB per-file** and **20,000 files per site** (free plan) limits.

### Custom domain

In the Pages project: **Custom domains → Set up a custom domain**, then follow Cloudflare’s DNS steps.
