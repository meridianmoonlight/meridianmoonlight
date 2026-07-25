#!/usr/bin/env python3
"""
Build site/whitepaper.html from WHITEPAPER.md.

The markdown file is the single source of truth. This script renders it into the
site's visual language rather than duplicating the content, so the published page
can never drift from the repository document.

Also copies docs/figures/ into site/figures/ so the static site is
self-contained and can be uploaded anywhere without a build step on the host.

Run:
    pip install markdown
    python site/build.py
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import markdown
from markdown.extensions.toc import TocExtension

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
SRC = ROOT / "WHITEPAPER.md"
OUT = SITE / "whitepaper.html"

REPO = "https://github.com/OWNER/meridian-moonlight"


def github_slugify(value: str, separator: str = "-") -> str:
    """Match GitHub's heading anchor generation.

    python-markdown's default differs slightly, which would silently break the
    cross-references inside the whitepaper.
    """
    value = value.strip().lower()
    value = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE)
    value = re.sub(r"[\s]+", separator, value)
    return value


CSS = """
:root{
  --abyss:#0A0E20; --night:#111735; --raised:#1A2149;
  --line:rgba(178,190,235,.14); --moon:#EAEDFA; --dim:#8D97C2;
  --amber:#FFB454; --amber-soft:rgba(255,180,84,.10); --dawn:#6FC3E8;
  --display:'Archivo',system-ui,sans-serif;
  --body:'Public Sans',system-ui,sans-serif;
  --mono:'JetBrains Mono',ui-monospace,monospace;
  --wrap:820px; --pad:clamp(20px,5vw,44px);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--abyss);color:var(--moon);
  font-family:var(--body);font-weight:300;font-size:17.5px;line-height:1.72;
  -webkit-font-smoothing:antialiased;
  background-image:radial-gradient(ellipse 120% 60% at 50% -8%,rgba(60,80,180,.18),transparent 60%);
  background-repeat:no-repeat}

/* nav */
.nav{position:sticky;top:0;z-index:50;backdrop-filter:blur(14px);
  background:rgba(10,14,32,.80);border-bottom:1px solid var(--line)}
.nav .inner{max-width:var(--wrap);margin:0 auto;padding:14px var(--pad);
  display:flex;align-items:center;justify-content:space-between;gap:18px}
.brand{font-family:var(--display);font-weight:800;font-variation-settings:'wdth' 116;
  font-size:.9rem;letter-spacing:.11em;text-decoration:none;white-space:nowrap;color:var(--moon)}
.brand span{color:var(--amber)}
.nav .links{display:flex;gap:20px;font-size:.85rem;color:var(--dim)}
.nav .links a{color:var(--dim);text-decoration:none;transition:color .2s}
.nav .links a:hover{color:var(--moon)}
@media(max-width:640px){.nav .links a.hide-sm{display:none}}

/* page */
main{max-width:var(--wrap);margin:0 auto;padding:clamp(40px,7vw,72px) var(--pad) 120px}

h1,h2,h3,h4{font-family:var(--display);font-weight:700;
  font-variation-settings:'wdth' 110;line-height:1.12;letter-spacing:-.02em;
  scroll-margin-top:80px}
h1{font-size:clamp(2.3rem,5.6vw,3.5rem);font-variation-settings:'wdth' 118;
  margin:0 0 .3em;letter-spacing:-.03em}
h2{font-size:clamp(1.5rem,3.2vw,2.05rem);margin:2.9em 0 .7em;
  padding-top:1.1em;border-top:1px solid var(--line)}
h3{font-size:1.22rem;margin:2.1em 0 .5em;font-variation-settings:'wdth' 106}
h4{font-size:1.02rem;margin:1.8em 0 .4em;color:var(--dawn)}
h1+h2{border-top:0;padding-top:0;margin-top:1.6em}

p{margin:0 0 1.25em}
strong{color:var(--moon);font-weight:500}
em{font-style:italic}
a{color:var(--dawn);text-decoration:none;border-bottom:1px solid rgba(111,195,232,.32);
  transition:border-color .2s,color .2s}
a:hover{color:var(--amber);border-bottom-color:var(--amber)}
h2 a,h3 a{border:0}

/* lead paragraph after h1 */
h1+p{font-size:1.2rem;color:var(--dim)}

ul,ol{margin:0 0 1.5em;padding-left:1.5em;color:var(--dim)}
li{margin-bottom:.6em}
li>strong{color:var(--moon)}
li::marker{color:var(--amber)}

hr{border:0;border-top:1px solid var(--line);margin:3em 0}

blockquote{margin:1.6em 0;padding:.2em 0 .2em 1.3em;
  border-left:2px solid var(--dawn);color:var(--dim)}
blockquote p:last-child{margin-bottom:0}

code{font-family:var(--mono);font-size:.86em;background:var(--night);
  border:1px solid var(--line);padding:.12em .42em;border-radius:2px;color:var(--amber)}
pre{background:var(--night);border:1px solid var(--line);border-left:2px solid var(--amber);
  padding:18px 20px;overflow-x:auto;margin:1.6em 0;font-size:.86rem;line-height:1.6}
pre code{background:0;border:0;padding:0;color:var(--moon);font-size:1em}

/* tables — the whitepaper leans on these heavily */
.tablewrap{overflow-x:auto;margin:1.8em 0;
  border:1px solid var(--line);background:var(--night)}
table{width:100%;border-collapse:collapse;font-size:.93rem;min-width:min(100%,520px)}
th{text-align:left;font-family:var(--mono);font-size:.64rem;letter-spacing:.14em;
  text-transform:uppercase;color:var(--dim);font-weight:400;
  padding:14px 16px;border-bottom:1px solid var(--line);white-space:nowrap;
  background:rgba(10,14,32,.45)}
td{padding:13px 16px;border-bottom:1px solid var(--line);color:var(--dim);
  vertical-align:top}
tr:last-child td{border-bottom:0}
td strong{color:var(--amber);font-weight:500}

img{max-width:100%;height:auto;display:block;margin:2.2em 0;
  border:1px solid var(--line);background:#F6F7FB}

/* the status banner up top */
.status{background:var(--night);border:1px solid var(--line);
  border-left:2px solid var(--dawn);padding:18px 22px;margin:0 0 2.4em;
  font-family:var(--mono);font-size:.78rem;letter-spacing:.04em;color:var(--dim);line-height:1.7}
.status b{color:var(--dawn);font-weight:500}

/* table of contents */
.toc{background:var(--night);border:1px solid var(--line);padding:24px 28px;margin:2.6em 0}
.toc>ul{margin:0;padding-left:1.1em;columns:2;column-gap:34px}
@media(max-width:640px){.toc>ul{columns:1}}
.toc li{margin-bottom:.42em;font-size:.92rem}
.toc a{color:var(--dim);border:0}
.toc a:hover{color:var(--amber)}
.toc-title{font-family:var(--mono);font-size:.66rem;letter-spacing:.2em;
  text-transform:uppercase;color:var(--amber);margin:0 0 14px}

/* heading anchors */
.headerlink{opacity:0;margin-left:.4em;font-weight:400;color:var(--dim);
  border:0;font-size:.8em;transition:opacity .15s}
h2:hover .headerlink,h3:hover .headerlink,h4:hover .headerlink{opacity:.55}

footer{border-top:1px solid var(--line);margin-top:60px;padding:36px var(--pad) 70px;
  color:var(--dim);font-size:.85rem;max-width:var(--wrap);margin-left:auto;margin-right:auto}
footer a{color:var(--dim)}
footer .fine{font-size:.76rem;opacity:.7;margin-top:14px}

:focus-visible{outline:2px solid var(--amber);outline-offset:3px}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}

/* Print / PDF. The screen theme is light-on-dark, so every colour that relies
   on a dark background has to be re-specified here — otherwise near-white
   `strong` text renders invisible on paper. */
@media print{
  body{background:#fff;color:#141414;background-image:none;font-size:11.5pt;line-height:1.6}
  .nav,footer .fine,.headerlink{display:none}
  main{max-width:none;padding:0}

  h1,h2,h3,h4{color:#000}
  h2{border-top:1px solid #bbb;page-break-after:avoid}
  h3,h4{page-break-after:avoid}
  h1+p{color:#333}

  p,li,td,th,blockquote{color:#222}
  strong,li>strong,td strong{color:#000;font-weight:600}
  em{color:#222}
  li::marker{color:#777}

  a{color:#0b3d63;border:0;text-decoration:underline}

  code{background:#f0f1f5;border:1px solid #ccc;color:#8a4500}
  pre{background:#f6f7fb;border:1px solid #ccc;border-left:2px solid #8a4500;
      page-break-inside:avoid}
  pre code{color:#141414}

  .status{background:#f6f7fb;border:1px solid #ccc;border-left:2px solid #666;color:#333}
  .status b{color:#000}

  .toc{background:#f6f7fb;border:1px solid #ccc;page-break-inside:avoid}
  .toc-title{color:#555}
  .toc a{color:#222;text-decoration:none}

  .tablewrap{background:#fff;border:1px solid #bbb;overflow:visible;
             page-break-inside:avoid}
  table{min-width:0}
  th{background:#f0f1f5;color:#444}
  td,th{border-bottom:1px solid #ddd}

  blockquote{border-left:2px solid #666}
  img{border:1px solid #ccc;page-break-inside:avoid;max-height:78vh;
      margin:1.4em auto}
  hr{border-top:1px solid #ddd}
  footer{border-top:1px solid #ccc;color:#444}
  footer a{color:#0b3d63}
}
"""

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Whitepaper — Meridian Moonlight</title>
<meta name="description" content="Meridian Moonlight whitepaper: a free AI network built from the world's sleeping phones. Includes the retraction of our own headline claim, full derivations, and a sensitivity analysis.">
<link rel="canonical" href="https://meridianmoonlight.com/whitepaper.html">
<meta property="og:title" content="Meridian Moonlight — Whitepaper">
<meta property="og:description" content="A free AI network built from the world's sleeping phones. Every number auditable, and one of them is a retraction of our own headline claim.">
<meta property="og:type" content="article">
<meta property="og:url" content="https://meridianmoonlight.com/whitepaper.html">
<meta property="og:image" content="https://meridianmoonlight.com/og.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@100..125,400..800&family=Public+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{css}</style>
</head>
<body>

<nav class="nav">
  <div class="inner">
    <a class="brand" href="index.html">MERIDIAN <span>MOONLIGHT</span></a>
    <div class="links">
      <a href="index.html">Home</a>
      <a href="{repo}/blob/main/analysis/compute_model.py" class="hide-sm" target="_blank" rel="noopener">The model</a>
      <a href="meridian-moonlight-whitepaper.pdf" class="hide-sm">PDF</a>
      <a href="{repo}" target="_blank" rel="noopener">GitHub</a>
    </div>
  </div>
</nav>

<main>
<div class="status">
  <b>STATUS: PROPOSAL.</b> Nothing in this document has been built yet. It is published at this
  stage on purpose &mdash; the numbers most likely to be wrong are cheaper to correct now than
  after a year of building on them.
</div>

{body}
</main>

<footer>
  <p>
    <a href="index.html">meridianmoonlight.com</a> &middot;
    <a href="{repo}" target="_blank" rel="noopener">GitHub</a> &middot;
    <a href="{repo}/issues/new" target="_blank" rel="noopener">Found an error? File it</a> &middot;
    <a href="mailto:hello@meridianmoonlight.com">hello@meridianmoonlight.com</a>
  </p>
  <p class="fine">
    This document is released under
    <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noopener">CC BY 4.0</a>.
    Code in the repository is Apache-2.0. Generated from
    <code>WHITEPAPER.md</code> by <code>site/build.py</code> &mdash; edit the markdown, not this page.
    No figure uses red as a signal colour.
  </p>
</footer>

</body>
</html>
"""


def rewrite_links(html: str) -> str:
    """Point repository-relative links at GitHub, and figures at the local copy."""
    # Figures are copied into site/figures/, so make those paths local.
    html = html.replace('src="docs/figures/', 'src="figures/')

    # Everything else that points into the repo goes to GitHub.
    repo_targets = [
        "analysis/compute_model.py",
        "analysis/NUMBERS.md",
        "analysis/numbers.json",
        "docs/threat-model.md",
        "docs/protocol-spec.md",
        "docs/governance.md",
        "docs/faq.md",
        "docs/MILESTONES.md",
        "ARCHITECTURE.md",
        "VISION.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "LICENSE",
    ]
    for t in repo_targets:
        html = html.replace(f'href="{t}"', f'href="{REPO}/blob/main/{t}" target="_blank" rel="noopener"')

    # Same-document anchors that were written as WHITEPAPER.md#anchor.
    html = re.sub(r'href="WHITEPAPER\.md#', 'href="#', html)
    html = html.replace('href="WHITEPAPER.md"', 'href="whitepaper.html"')

    # The OWNER placeholder in the source document.
    html = html.replace("https://github.com/OWNER/meridian-moonlight", REPO)
    return html


def wrap_tables(html: str) -> str:
    """Tables must scroll inside their own container, never the page body."""
    return html.replace("<table>", '<div class="tablewrap"><table>').replace(
        "</table>", "</table></div>"
    )


def main() -> None:
    text = SRC.read_text(encoding="utf-8")

    # The markdown has a hand-written Contents list. The toc extension builds a
    # better one, so drop the manual block to avoid two tables of contents.
    text = re.sub(
        r"^## Contents\n.*?(?=^---$)", "", text, count=1, flags=re.S | re.M
    )

    md = markdown.Markdown(
        extensions=[
            "tables",
            "fenced_code",
            "attr_list",
            "md_in_html",
            "sane_lists",
            TocExtension(slugify=github_slugify, permalink="#", toc_depth="2-3"),
        ]
    )
    body = md.convert(text)
    body = wrap_tables(body)
    body = rewrite_links(body)

    toc = md.toc  # type: ignore[attr-defined]
    toc_block = (
        f'<nav class="toc"><p class="toc-title">Contents</p>{toc}</nav>'
        if toc.strip()
        else ""
    )

    # Insert the generated TOC directly after the abstract's closing rule.
    marker = "<hr />"
    if marker in body:
        first = body.index(marker) + len(marker)
        body = body[:first] + "\n" + toc_block + body[first:]
    else:
        body = toc_block + body

    OUT.write_text(
        HTML.format(css=CSS, body=body, repo=REPO), encoding="utf-8", newline="\n"
    )

    # Copy figures so the site is self-contained.
    figs_src = ROOT / "docs" / "figures"
    figs_dst = SITE / "figures"
    figs_dst.mkdir(parents=True, exist_ok=True)
    copied = 0
    for png in sorted(figs_src.glob("*.png")):
        shutil.copy2(png, figs_dst / png.name)
        copied += 1

    kb = OUT.stat().st_size / 1024
    print(f"Wrote {OUT.relative_to(ROOT)}  ({kb:.0f} KB)")
    print(f"Copied {copied} figures to {figs_dst.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
