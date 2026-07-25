#!/usr/bin/env python3
"""
Consistency check across the whole project.

Everything published should trace back to the model. This verifies that, plus
the boring things that rot silently: dead links, missing images, stale framing,
and drift between the repo and the upload package.

Run:
    python analysis/consistency_check.py

Exits non-zero if anything fails, so it can gate a commit.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FAILURES: list[str] = []
WARNINGS: list[str] = []
CHECKS = 0


def ok(label: str) -> None:
    global CHECKS
    CHECKS += 1
    print(f"  [ok]   {label}")


def fail(label: str, detail: str = "") -> None:
    global CHECKS
    CHECKS += 1
    FAILURES.append(f"{label}{(' — ' + detail) if detail else ''}")
    print(f"  [FAIL] {label}{(' — ' + detail) if detail else ''}")


def warn(label: str, detail: str = "") -> None:
    WARNINGS.append(f"{label}{(' — ' + detail) if detail else ''}")
    print(f"  [warn] {label}{(' — ' + detail) if detail else ''}")


def read(rel: str) -> str:
    p = ROOT / rel
    return p.read_text(encoding="utf-8") if p.exists() else ""


# Documents that make public claims. PROJECT_LOG is history and exempt.
PUBLIC_DOCS = [
    "README.md", "WHITEPAPER.md", "VISION.md", "ARCHITECTURE.md",
    "docs/faq.md", "docs/threat-model.md", "docs/desktop-security.md",
    "docs/economy.md", "docs/task-types.md", "docs/governance.md",
    "docs/protocol-spec.md", "docs/MILESTONES.md",
    "analysis/NUMBERS.md", "analysis/LADDER.md", "analysis/ECONOMICS.md",
    "site/index.html",
]

print("=" * 74)
print("MERIDIAN MOONLIGHT — CONSISTENCY CHECK")
print("=" * 74)

# ===========================================================================
print("\n1. The model still runs and its outputs exist")
# ===========================================================================
for f in ("analysis/numbers.json", "analysis/ladder.json",
          "analysis/economics.json", "analysis/NUMBERS.md"):
    if (ROOT / f).exists():
        ok(f"{f} present")
    else:
        fail(f"{f} missing", "run the analysis scripts")

N = json.loads(read("analysis/numbers.json") or "{}")
L = json.loads(read("analysis/ladder.json") or "{}")
E = json.loads(read("analysis/economics.json") or "{}")

# ===========================================================================
print("\n2. Published figures match the model")
# ===========================================================================
if N and L:
    d = N["desktop"]
    lad = {x["name"]: x for x in L["ladder"]}
    reach = {x["name"]: x for x in L["reach"]}

    # (label, expected value, the strings that must appear somewhere public)
    claims = [
        ("phone fleet 1.2B", 1.2, ["1.2 billion", "1.2B"]),
        ("desktop fleet 920M", 920, ["920 million", "920M"]),
        ("phone tok/s 12.3", 12.3, ["12.3"]),
        ("phone FP32 0.299", 0.299, ["0.30", "299"]),
        ("desktop FP32 2.983", 2.983, ["2,983", "2.98"]),
        ("mobile availability 25.7", 25.7, ["25.7%"]),
        ("desktop availability 19.6", 19.6, ["19.6%"]),
        ("floor 14.1", 14.1, ["14.1%"]),
        ("night peak 60.1", 60.1, ["60.1%"]),
        ("NPU gap 457", 457, ["457"]),
        ("F@h parity phones 31M", 31, ["31 million", "31M"]),
        ("F@h parity mixed desktops 4.1M", 4.1, ["4.1 million", "4.1M"]),
        ("F@h parity dGPU 1.3M", 1.3, ["1.3 million", "1.3M"]),
        ("desktop full 538", 538, ["538"]),
        ("combined 630", 630, ["630"]),
        ("combined multiple 262", 262, ["262"]),
        ("desktop science share 85", 85, ["85%"]),
        ("dGPU vs phone 32x", 32, ["32 phones"]),
        ("flagship 331K", 331, ["331,000", "331K"]),
        ("participant tokens 274K", 274, ["274,000", "274K"]),
        ("headroom 9.1", 9.1, ["9.1", "nine times", "9&times;"]),
    ]

    # verify the expected values really are what the model says
    model_values = {
        "phone fleet 1.2B": round(N["fleet"]["capable_fleet_today"] / 1e9, 1),
        "desktop fleet 920M": round(d["fleet"] / 1e6),
        "phone tok/s 12.3": round(N["per_device"]["weighted_tokens_per_sec"], 1),
        "phone FP32 0.299": round(N["per_device"]["weighted_sustained_tflops_fp32"], 3),
        "desktop FP32 2.983": round(d["weighted_sustained_tflops_fp32"], 3),
        "mobile availability 25.7": round(N["availability"]["mean_over_24h"] * 100, 1),
        "desktop availability 19.6": round(d["availability"]["mean_over_24h"] * 100, 1),
        "floor 14.1": round(N["availability"]["global_min"] * 100, 1),
        "night peak 60.1": round(N["availability"]["night_peak"] * 100, 1),
        "NPU gap 457": round(N["per_device"]["npu_peak_to_real_ratio"]),
        "F@h parity phones 31M": round(N["crossovers"]["enrolled_to_match_folding_at_home_peak"] / 1e6),
        "F@h parity mixed desktops 4.1M": round(d["folding_parity_mixed_fleet"] / 1e6, 1),
        "F@h parity dGPU 1.3M": round(d["folding_parity_dgpu_only"] / 1e6, 1),
        "desktop full 538": round(d["full_fleet_exaflops"]),
        "combined 630": round(N["combined"]["science_exaflops_full_both"]),
        "combined multiple 262": round(N["combined"]["science_folding_multiple_both"]),
        "desktop science share 85": round(N["combined"]["desktop_share_of_science"] * 100),
        "dGPU vs phone 32x": round(d["dgpu_science_advantage_vs_mobile"]),
        "flagship 331K": round(reach["32B"]["machines_needed"]["100000"] / 1e3),
        "participant tokens 274K": round(N["self_sufficiency"]["tokens_per_participant_per_day"] / 1e3),
        "headroom 9.1": round(N["self_sufficiency"]["ratio"], 1),
    }

    corpus = "\n".join(read(f) for f in PUBLIC_DOCS)
    for label, expected, needles in claims:
        actual = model_values.get(label)
        if actual is None:
            continue
        # does the model still produce the value we are asserting?
        if abs(float(actual) - float(expected)) > max(0.06 * abs(expected), 0.05):
            fail(f"model drifted: {label}", f"model now says {actual}, docs assert {expected}")
            continue
        if any(nd in corpus for nd in needles):
            ok(f"{label} = {actual}, cited in the docs")
        else:
            warn(f"{label} = {actual} not found in any public doc", "may be fine if unused")

# ===========================================================================
print("\n3. Retracted claims appear only as retractions")
# ===========================================================================
RETRACTED = ["1.4%", "5,800", "14,520", "2.2 billion", "6.6 TOPS", "2,400 Folding",
             "73×", "880M", "1.39%"]
CONTEXT = ["retract", "previous", "earlier draft", "corrected", "was wrong",
           "we've been wrong", "wrong by", "strike", "historical", "superseded"]
for token in RETRACTED:
    hits = []
    for f in PUBLIC_DOCS:
        text = read(f)
        for m in re.finditer(re.escape(token), text):
            window = text[max(0, m.start() - 700): m.end() + 700].lower()
            if not any(c in window for c in CONTEXT):
                hits.append(f)
                break
    if hits:
        fail(f"'{token}' stated as live claim", ", ".join(sorted(set(hits))))
    else:
        ok(f"'{token}' only appears in retraction context")

# ===========================================================================
print("\n4. Nothing phone-first or pledge-era survives")
# ===========================================================================
STALE = {
    "Your phone works for the world": "old phone-first headline",
    "subscribe.php": "removed backend",
    "Pledge a phone": "removed pledge CTA",
    "OWNER/meridian": "unresolved repo placeholder",
    "moonlight-config": "removed credentials file",
}
# A mention is only stale if it reads as current. Explaining that something was
# removed is exactly the kind of note this project should keep.
REMOVAL_CONTEXT = ["deleted", "removed", "no longer", "was replaced", "used to",
                   "gone", "rather than leaving", "dead weight"]
for token, why in STALE.items():
    hits = []
    for f in PUBLIC_DOCS + ["ASKS.md", "site/README.md", "DEPLOY.md"]:
        text = read(f)
        for m in re.finditer(re.escape(token), text):
            window = text[max(0, m.start() - 400): m.end() + 400].lower()
            if not any(c in window for c in REMOVAL_CONTEXT):
                hits.append(f)
                break
    if hits:
        fail(f"stale: {token} ({why})", ", ".join(sorted(set(hits))))
    else:
        ok(f"no stale '{token}'")

# ===========================================================================
print("\n5. Every internal link and image resolves")
# ===========================================================================
broken = 0
for f in PUBLIC_DOCS + ["ASKS.md", "site/README.md", "CONTRIBUTING.md", "SECURITY.md",
                        "CODE_OF_CONDUCT.md", "measurements/README.md"]:
    p = ROOT / f
    if not p.exists():
        continue
    text = p.read_text(encoding="utf-8")
    for m in re.finditer(r"\]\((?!https?:|mailto:|#)([^)#]+)(?:#[^)]*)?\)", text):
        target = m.group(1).strip()
        if target.startswith("../../"):     # GitHub repo-relative, valid on github.com
            continue
        resolved = (p.parent / target).resolve()
        if not resolved.exists():
            fail(f"dead link in {f}", target)
            broken += 1
    for m in re.finditer(r'src="([^"]+)"', text):
        src = m.group(1)
        if src.startswith(("http", "data:")):
            continue
        resolved = (p.parent / src).resolve()
        if not resolved.exists():
            fail(f"missing image in {f}", src)
            broken += 1
if broken == 0:
    ok("all internal links and images resolve")

# ===========================================================================
print("\n6. The upload package matches the site")
# ===========================================================================
site, deploy = ROOT / "site", ROOT / "deploy" / "public_html"
if not deploy.exists():
    fail("deploy/public_html missing")
else:
    required = ["index.html", "whitepaper.html", ".htaccess", "og.png",
                "robots.txt", "sitemap.xml", "meridian-moonlight-whitepaper.pdf"]
    for r in required:
        if (deploy / r).exists():
            ok(f"deploy has {r}")
        else:
            fail(f"deploy missing {r}")

    for sub in ("figures", "diagrams"):
        s_files = {f.name for f in (site / sub).glob("*")} if (site / sub).exists() else set()
        d_files = {f.name for f in (deploy / sub).glob("*")} if (deploy / sub).exists() else set()
        if s_files == d_files and s_files:
            ok(f"deploy/{sub} matches site/{sub} ({len(s_files)} files)")
        else:
            fail(f"deploy/{sub} out of sync", f"only in site: {s_files - d_files}; only in deploy: {d_files - s_files}")

    for f in ("index.html", "whitepaper.html"):
        if (site / f).exists() and (deploy / f).exists():
            if (site / f).read_bytes() == (deploy / f).read_bytes():
                ok(f"deploy/{f} is byte-identical to site/{f}")
            else:
                fail(f"deploy/{f} differs from site/{f}", "re-copy after rebuilding")

    # every asset the page references must be in the package
    idx = (deploy / "index.html").read_text(encoding="utf-8") if (deploy / "index.html").exists() else ""
    for m in re.finditer(r'src="((?:figures|diagrams)/[^"]+)"', idx):
        if not (deploy / m.group(1)).exists():
            fail("index.html references a file missing from the package", m.group(1))

    if not any(deploy.rglob("*.php")):
        ok("no PHP in the upload package (fully static)")
    else:
        fail("PHP found in upload package", "the backend was supposed to be removed")

# ===========================================================================
print("\n7. Generated artefacts are current")
# ===========================================================================
model_src = (ROOT / "analysis" / "compute_model.py").stat().st_mtime
for gen in ("analysis/NUMBERS.md", "analysis/numbers.json",
            "docs/figures/fig1_bandwidth_wall.png", "docs/figures/fig7_tiers.png"):
    g = ROOT / gen
    if g.exists() and g.stat().st_mtime >= model_src - 2:
        ok(f"{gen} newer than the model")
    elif g.exists():
        warn(f"{gen} older than compute_model.py", "re-run the model")

wp = (ROOT / "WHITEPAPER.md").stat().st_mtime
for gen in ("site/whitepaper.html", "site/meridian-moonlight-whitepaper.pdf"):
    g = ROOT / gen
    if g.exists() and g.stat().st_mtime >= wp - 2:
        ok(f"{gen} newer than WHITEPAPER.md")
    elif g.exists():
        warn(f"{gen} older than WHITEPAPER.md", "re-run site/build.py and reprint the PDF")

# ===========================================================================
print("\n" + "=" * 74)
print(f"{CHECKS} checks · {len(FAILURES)} failures · {len(WARNINGS)} warnings")
print("=" * 74)
if FAILURES:
    print("\nFAILURES:")
    for f in FAILURES:
        print("  -", f)
if WARNINGS:
    print("\nWarnings (not blocking):")
    for w in WARNINGS:
        print("  -", w)
sys.exit(1 if FAILURES else 0)
