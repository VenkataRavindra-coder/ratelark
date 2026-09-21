# RateLark: multi-page site

63 static pages (9 languages x 7 tools), each with its own URL, title, description,
canonical link, hreflang tags and structured data, plus sitemap.xml and robots.txt.

    site/                 <- upload this folder to your host
    hourkit.html         <- the source app (single file, all tools and translations)
    build.py              <- turns hourkit.html into site/

## 0. Already done for you

The site is built for `https://ratelark.com`. The `site/` folder is ready to upload. It includes
favicon and app icons, a social share image (`og.png`), a privacy page, `sitemap.xml`, `robots.txt`,
a `_headers` file (security headers and caching, read by Cloudflare Pages and Netlify), and
versioned asset URLs. Icons and the share image live in `static/` and are copied in by `build.py`.

If GitHub Pages is your host, note that it ignores `_headers`. Cloudflare Pages or Netlify is
recommended so the security headers apply.

## 1. Put your domain in (only if it changes)

Every canonical link, hreflang tag and the sitemap contain a placeholder domain.
Rebuild with yours:

    pip install beautifulsoup4
    python3 build.py https://ratelark.com

No Python? Search and replace `https://YOUR-DOMAIN.com` with your domain in every
file under `site/` (a text editor's "replace in folder" works), then deploy.

## 2. Deploy (any static host works)

- Cloudflare Pages or Netlify: create a project, upload the `site` folder, attach your domain.
- GitHub Pages: push the contents of `site/` to a repo and enable Pages. (`.nojekyll` is included.)

The URLs are `/en/hourly-rate/`, `/es/tax/`, and so on. The root `/` sends visitors to
their language.

## 3. Tell Google and Bing

1. Add the site in Google Search Console and Bing Webmaster Tools.
2. Submit `https://yourdomain.com/sitemap.xml`.
3. In Search Console, watch Performance by country and by page. That shows which markets and
   tools are working, and where to put your effort.

## Changing things

Edit `hourkit.html` (tools, text, translations), then run `build.py` again.
The single file also works on its own if you open it in a browser.

## Known limits

- Translations were machine-written and have not been reviewed by native speakers.
- Tax rates are for 2026 (US, UK 2026/27, Canada, Australia 2026-27) and need updating each year.
- Fonts load from Google Fonts (the privacy page says so; the security policy allows it).
- No analytics are included. Add your preferred script to the `<head>` in `build.py`.
