# The British Manifesto Archive

A static web archive of UK general election manifestos, results, and maps (1945–2024).

## Local preview

```bash
python3 -m http.server 8888 --bind 127.0.0.1
```

Open [http://127.0.0.1:8888/](http://127.0.0.1:8888/).

## Deploy to Cloudflare Pages

1. Push this repository to GitHub (or GitLab).
2. In [Cloudflare Pages](https://pages.cloudflare.com/), choose **Create a project → Connect to Git**.
3. Select the repository and use these build settings:

   | Setting | Value |
   |---------|-------|
   | **Framework preset** | None |
   | **Build command** | *(leave empty)* |
   | **Build output directory** | `.` |

4. Deploy. The site will be served from `https://<project>.pages.dev`.

`wrangler.toml` and `_headers` in the repo root configure the static output directory and caching headers.

### Before deploying

```bash
python3 scripts/check-cloudflare-limits.py
```

This checks Cloudflare’s **25 MiB per-file** and **20,000 files per site** (free plan) limits.

### Custom domain

In the Pages project: **Custom domains → Set up a custom domain**, then follow Cloudflare’s DNS steps.
