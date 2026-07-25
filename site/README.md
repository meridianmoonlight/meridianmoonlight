# site/ — meridianmoonlight.com

Static. No framework, no bundler, no build step on the host. Upload the folder.

## Before the first deploy: one substitution

Every repository link contains the placeholder `OWNER`. Replace it with the actual
GitHub account or organisation name:

```bash
# from the repo root
grep -rl 'OWNER/meridian-moonlight' . --exclude-dir=.git
sed -i 's|OWNER/meridian-moonlight|YOURNAME/meridian-moonlight|g' \
  site/index.html site/build.py WHITEPAPER.md
python site/build.py   # regenerate whitepaper.html with the corrected links
```

Verify none are left:

```bash
grep -rn 'OWNER' site/ *.md docs/ | grep -v 'copyright owner'
```

## Files

| File | Notes |
|---|---|
| `index.html` | Hand-written. Self-contained apart from Google Fonts. |
| `whitepaper.html` | **Generated** from `../WHITEPAPER.md` by `build.py`. Do not edit. |
| `figures/` | **Generated** — copied from `../docs/figures/` by `build.py`. |
| `og.png` | **Generated** by `make_og.py`. Social preview card, 1200×630. |
| `CNAME` | GitHub Pages custom domain. |
| `robots.txt`, `sitemap.xml` | Static. Update the sitemap if pages are added. |

## Rebuilding

```bash
pip install markdown numpy matplotlib

python analysis/compute_model.py   # figures + numbers (run first if the model changed)
python site/build.py               # whitepaper.html + copies figures into site/
python site/make_og.py             # og.png
```

`build.py` renders the markdown rather than duplicating it, so the published page
can't drift from the repository document. If you find yourself editing
`whitepaper.html` by hand, edit `WHITEPAPER.md` and rebuild instead.

## The availability model is duplicated on purpose

`index.html` contains a JavaScript port of the availability curve from
`analysis/compute_model.py` — the same cluster weights, the same smooth night
window, the same normalisation. That's what makes the live readout on the home
page agree with the published figures instead of being decorative.

**If you change one, change both.** They are verified to agree:

| | night peak | mean | min | max |
|---|---|---|---|---|
| Python | 60.1% | 25.7% | 14.1% | 40.8% |
| JavaScript | 60.1% | 25.7% | 14.1% | 40.8% |

## Deploying

**GitHub Pages** — set Pages to serve from the `main` branch, `/site` folder.
`CNAME` is already in place; point the apex domain's DNS at GitHub's A records
and add a `www` CNAME to `<owner>.github.io`.

**Anything else** (Netlify, Cloudflare Pages, plain hosting) — publish directory
is `site/`, build command is `python site/build.py`, or just upload the folder
after building locally.

## Accessibility notes

- No red as a signal colour anywhere, on the site or in the figures.
- The hero animation respects `prefers-reduced-motion` — it holds at the current
  UTC hour instead of animating.
- Tables scroll inside their own containers; the page body never scrolls
  horizontally, verified down to 375px.
- The canvas has an `aria-label` describing what it depicts.
