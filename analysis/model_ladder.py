#!/usr/bin/env python3
"""
What changes if desktops run BIGGER models, not just science?

The desktop tier was introduced as the research instrument. This module asks a
different question: what if those machines host 14B, 32B, or 70B models to make
the network's *AI* better, rather than to do floating-point science?

Two constraints govern the answer, and they pull in opposite directions:

  1. VRAM decides what can be hosted at all. A model that doesn't fit doesn't
     run at any speed. This is a hard cliff, not a gradient.

  2. The bandwidth wall gets WORSE with size. tokens/sec = usable bandwidth /
     weight footprint, so a 32B model produces roughly a quarter the tokens of
     an 8B model on the same card. Capability per token goes up; tokens per
     second goes down, close to proportionally.

The interesting result is in the interaction. Big-VRAM cards are rare, but they
are also *fast* — bandwidth scales with VRAM across the product stack — so the
throughput penalty is smaller than the naive 1/params estimate suggests. And
because a flagship model only needs a small number of large machines, the
network's best capability turns out to have the LOWEST adoption bar of anything
in this project.

Run:
    python analysis/model_ladder.py

Outputs:
    analysis/LADDER.md
    analysis/ladder.json
    docs/figures/fig9_model_ladder.png
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from compute_model import (
    DESKTOP_DGPU_COUNT,
    DESKTOP_APPLE_COUNT,
    DESKTOP_CPU_ONLY_COUNT,
    DESKTOP_THERMAL_DERATE,
    desktop_availability_profile,
    CAPABLE_FLEET_TODAY,
    INK, BG, GRID, BLUE, TEAL, AMBER, MAGENTA, SLATE, DEEP,
)

ROOT = Path(__file__).resolve().parent.parent
FIGDIR = ROOT / "docs" / "figures"
FIGDIR.mkdir(parents=True, exist_ok=True)

VIOLET = "#B388F0"


# ===========================================================================
# THE MODEL LADDER
# ===========================================================================
# Weight footprints are Q4_K_M unless noted, including scales and the
# higher-precision tensors quantisation schemes retain. KV cache and runtime
# overhead add roughly 1-2 GB at useful context lengths, so "fits" means
# weights + headroom, not weights alone.

MODELS = [
    {"name": "3B",  "params_b": 3.0,  "weight_gb": 1.80, "needs_gb": 3.5,  "tier": "phone"},
    {"name": "8B",  "params_b": 8.0,  "weight_gb": 4.70, "needs_gb": 6.5,  "tier": "baseline"},
    {"name": "14B", "params_b": 14.0, "weight_gb": 8.50, "needs_gb": 10.5, "tier": "strong"},
    {"name": "32B", "params_b": 32.0, "weight_gb": 19.0, "needs_gb": 22.0, "tier": "flagship"},
    {"name": "70B", "params_b": 70.0, "weight_gb": 40.0, "needs_gb": 44.0, "tier": "frontier-ish"},
]


# ===========================================================================
# HARDWARE POPULATION, TIERED BY MEMORY
# ===========================================================================
# CONFIDENCE: LOW. These distributions are our own construction from the shape
# of the consumer GPU market, not a dataset. They are the least defensible
# numbers in this file and the most consequential, so they are stated as named
# constants and tested in the sensitivity block at the bottom.
#
# The key correlation, which matters more than the exact shares: on consumer
# hardware, MORE VRAM ALSO MEANS MORE BANDWIDTH. A 24GB card is not merely
# roomier than an 8GB card, it is roughly three times faster at streaming
# weights. That partly rescues large models from the bandwidth wall.

DGPU_TIERS = [
    # (label, share of dGPU fleet, usable VRAM GB, peak bandwidth GB/s)
    ("4-6GB",   0.22,  5.0,  240.0),
    ("8GB",     0.36,  8.0,  330.0),
    ("10-12GB", 0.24, 12.0,  460.0),
    ("16GB",    0.12, 16.0,  620.0),
    ("24GB",    0.05, 24.0,  950.0),
    ("32GB+",   0.01, 32.0, 1500.0),
]

# Apple Silicon: unified memory, so the whole machine's RAM is available to the
# GPU. Bandwidth is lower than a discrete card at equivalent capacity, but the
# capacity ceiling is far higher — which makes Macs the best consumer substrate
# for very large models by a wide margin.
APPLE_TIERS = [
    ("8GB",     0.45,  6.0,   90.0),
    ("16GB",    0.33, 12.0,  140.0),
    ("24-36GB", 0.16, 26.0,  270.0),
    ("48GB+",   0.06, 56.0,  450.0),
]

# CPU-only machines can host large models in system RAM but stream weights at
# DDR speeds. Too slow for conversation; usable for overnight batch work.
CPU_TIERS = [
    ("16GB RAM", 0.62, 12.0, 50.0),
    ("32GB RAM", 0.28, 26.0, 55.0),
    ("64GB+ RAM", 0.10, 56.0, 60.0),
]

USABLE_FRACTION_GPU = 0.75
USABLE_FRACTION_APPLE = 0.70
USABLE_FRACTION_CPU = 0.60

# What one active conversation consumes, in tokens/sec. Roughly human reading
# speed — below this a chat feels slow.
TOK_PER_SESSION = 15.0

# Below this, a model is too slow for interactive use and is batch-only.
INTERACTIVE_FLOOR_TOKS = 6.0


def _population():
    rows = []
    for label, share, vram, bw in DGPU_TIERS:
        rows.append({"family": "Discrete GPU", "label": label,
                     "count": DESKTOP_DGPU_COUNT * share, "vram_gb": vram,
                     "bandwidth": bw, "usable": USABLE_FRACTION_GPU})
    for label, share, vram, bw in APPLE_TIERS:
        rows.append({"family": "Apple Silicon", "label": label,
                     "count": DESKTOP_APPLE_COUNT * share, "vram_gb": vram,
                     "bandwidth": bw, "usable": USABLE_FRACTION_APPLE})
    for label, share, vram, bw in CPU_TIERS:
        rows.append({"family": "CPU only", "label": label,
                     "count": DESKTOP_CPU_ONLY_COUNT * share, "vram_gb": vram,
                     "bandwidth": bw, "usable": USABLE_FRACTION_CPU})
    return rows


def compute() -> dict:
    pop = _population()
    _, d_avail = desktop_availability_profile()
    mean_avail = float(d_avail.mean())

    # A machine that can HOLD a model is not the same as a machine that can
    # hold a *conversation* with it. A 64GB CPU-only desktop fits a 32B model
    # and streams it at under 2 tok/s — real capacity for overnight batch work,
    # useless for chat. Averaging the two together produces a number that
    # describes neither, so we keep them apart throughout.
    ladder = []
    for m in MODELS:
        hosts = inter_hosts = batch_hosts = 0.0
        wt_all = wt_inter = 0.0
        by_family, inter_by_family = {}, {}
        for h in pop:
            if h["vram_gb"] < m["needs_gb"]:
                continue
            toks = (h["bandwidth"] * h["usable"] / m["weight_gb"]) * DESKTOP_THERMAL_DERATE
            hosts += h["count"]
            wt_all += h["count"] * toks
            by_family[h["family"]] = by_family.get(h["family"], 0.0) + h["count"]
            if toks >= INTERACTIVE_FLOOR_TOKS:
                inter_hosts += h["count"]
                wt_inter += h["count"] * toks
                inter_by_family[h["family"]] = inter_by_family.get(h["family"], 0.0) + h["count"]
            else:
                batch_hosts += h["count"]

        mean_all = (wt_all / hosts) if hosts else 0.0
        mean_inter = (wt_inter / inter_hosts) if inter_hosts else 0.0
        ladder.append({
            **m,
            "hosts": hosts,
            "hosts_share_of_desktop_fleet": hosts / (
                DESKTOP_DGPU_COUNT + DESKTOP_APPLE_COUNT + DESKTOP_CPU_ONLY_COUNT),
            "interactive_hosts": inter_hosts,
            "batch_only_hosts": batch_hosts,
            "mean_tokens_per_sec": mean_all,
            "mean_tokens_per_sec_interactive": mean_inter,
            "by_family": by_family,
            "interactive_by_family": inter_by_family,
            "full_tokens_per_sec": inter_hosts * mean_avail * mean_inter,
            "full_concurrent_sessions": inter_hosts * mean_avail * mean_inter / TOK_PER_SESSION,
        })

    # ------------------------------------------------------------------
    # The headline: how many machines does a given capability actually need?
    # ------------------------------------------------------------------
    # Answering "what enrolment delivers N concurrent conversations at this
    # model size" is more useful than a total, because the flagship tier is
    # small and the number turns out to be surprisingly reachable.
    TARGETS = [1_000, 10_000, 100_000, 1_000_000]
    reach = []
    for L in ladder:
        # Interactive service only — batch-only machines cannot hold a conversation.
        if L["interactive_hosts"] == 0 or L["mean_tokens_per_sec_interactive"] <= 0:
            continue
        per_enrolled = mean_avail * L["mean_tokens_per_sec_interactive"] / TOK_PER_SESSION
        reach.append({
            "name": L["name"],
            "sessions_per_enrolled_machine": per_enrolled,
            "mean_tokens_per_sec_interactive": L["mean_tokens_per_sec_interactive"],
            "machines_needed": {str(t): t / per_enrolled for t in TARGETS},
            "capable_pool": L["interactive_hosts"],
            "pool_share_needed": {
                str(t): (t / per_enrolled) / L["interactive_hosts"] for t in TARGETS
            },
        })

    # ------------------------------------------------------------------
    # Contention: the same big cards are the best science machines.
    # ------------------------------------------------------------------
    # A 24GB card can host the flagship model OR run FP32 science. Not both in
    # the same device-hour. This is a real internal competition and the
    # whitepaper should not pretend otherwise.
    big = [h for h in pop if h["vram_gb"] >= 22.0 and h["family"] == "Discrete GPU"]
    big_count = sum(h["count"] for h in big)
    flagship = next(L for L in ladder if L["name"] == "32B")

    contention = {
        "big_vram_dgpu_count": big_count,
        "share_of_dgpu_fleet": big_count / DESKTOP_DGPU_COUNT,
        "flagship_sessions_if_all_inference": big_count * mean_avail
        * flagship["mean_tokens_per_sec_interactive"] / TOK_PER_SESSION,
        # Those same machines are the top of the science fleet too.
        "note": "The machines that can host the flagship model are the same ones "
                "that carry the science tier. Every device-hour spent on 32B "
                "inference is a device-hour not spent on FP32 batch work.",
    }

    # ------------------------------------------------------------------
    # Throughput cost of capability, on identical hardware.
    # ------------------------------------------------------------------
    ref_bw = 950.0 * USABLE_FRACTION_GPU   # a 24GB consumer card
    cost_of_capability = [
        {
            "name": m["name"],
            "tokens_per_sec_on_24gb": (ref_bw / m["weight_gb"]) * DESKTOP_THERMAL_DERATE
            if m["needs_gb"] <= 24 else None,
            "fits_in_24gb": m["needs_gb"] <= 24,
        }
        for m in MODELS
    ]

    # ------------------------------------------------------------------
    # Sensitivity on the least defensible input: the VRAM distribution.
    # ------------------------------------------------------------------
    sens = []
    for label, mult in (("half as many big cards", 0.5), ("twice as many big cards", 2.0)):
        scaled = []
        for h in pop:
            c = h["count"] * (mult if h["vram_gb"] >= 22.0 else 1.0)
            scaled.append({**h, "count": c})
        elig = [
            h for h in scaled
            if h["vram_gb"] >= flagship["needs_gb"]
            and (h["bandwidth"] * h["usable"] / flagship["weight_gb"]) * DESKTOP_THERMAL_DERATE
            >= INTERACTIVE_FLOOR_TOKS
        ]
        hosts = sum(h["count"] for h in elig)
        wt = sum(
            h["count"] * (h["bandwidth"] * h["usable"] / flagship["weight_gb"]) * DESKTOP_THERMAL_DERATE
            for h in elig
        )
        mt = wt / hosts if hosts else 0
        sens.append({
            "scenario": label,
            "flagship_capable_machines": hosts,
            "machines_for_100k_sessions": 100_000 / (mean_avail * mt / TOK_PER_SESSION) if mt else None,
        })

    return {
        "desktop_mean_availability": mean_avail,
        "tokens_per_session": TOK_PER_SESSION,
        "interactive_floor_toks": INTERACTIVE_FLOOR_TOKS,
        "ladder": ladder,
        "reach": reach,
        "contention": contention,
        "cost_of_capability": cost_of_capability,
        "sensitivity": sens,
        "population": pop,
    }


# ===========================================================================
# FIGURE
# ===========================================================================

def _si(v, _pos=None):
    v = float(v)
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(v) >= div:
            s = v / div
            return f"{s:.0f}{suf}" if s >= 10 else f"{s:.1f}{suf}"
    return f"{v:.0f}"


def fig_ladder(R: dict) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.8, 5.6))
    names = [L["name"] for L in R["ladder"]]

    # ---- left: what can host it, and how fast --------------------------
    hosts = [L["interactive_hosts"] for L in R["ladder"]]
    toks = [L["mean_tokens_per_sec_interactive"] for L in R["ladder"]]
    x = np.arange(len(names))

    bars = ax1.bar(x, hosts, color=[SLATE, BLUE, TEAL, AMBER, MAGENTA], width=0.6, zorder=3)
    ax1.set_yscale("log")
    ax1.set_xticks(x); ax1.set_xticklabels(names)
    ax1.set_ylabel("Desktops fast enough to hold a conversation")
    ax1.set_xlabel("Model size (Q4)")
    ax1.set_title("VRAM is a cliff, not a gradient")
    ax1.yaxis.set_major_formatter(FuncFormatter(_si))
    for b, h, t in zip(bars, hosts, toks):
        ax1.annotate(f"{_si(h)}\n{t:.0f} tok/s",
                     (b.get_x() + b.get_width()/2, h),
                     textcoords="offset points", xytext=(0, 6),
                     ha="center", fontsize=9.5, fontweight="bold")
    ax1.set_ylim(min(h for h in hosts if h > 0) * 0.25, max(hosts) * 6)
    ax1.grid(axis="x", visible=False)

    # ---- right: machines needed for 100k concurrent conversations ------
    tgt = "100000"
    lab, need, pool = [], [], []
    for r in R["reach"]:
        lab.append(r["name"])
        need.append(r["machines_needed"][tgt])
        pool.append(r["pool_share_needed"][tgt])
    y = np.arange(len(lab))
    cols = [SLATE, BLUE, TEAL, AMBER, MAGENTA][:len(lab)]
    ax2.barh(y, need, color=cols, height=0.55, zorder=3)
    for yy, n, p in zip(y, need, pool):
        ax2.annotate(f"  {_si(n)} machines  ({p*100:.1f}% of the capable pool)",
                     (n, yy), textcoords="offset points", xytext=(6, 0),
                     va="center", fontsize=10, fontweight="bold")
    ax2.set_yticks(y); ax2.set_yticklabels(lab)
    ax2.set_xscale("log")
    ax2.set_xlim(min(need)/3, max(need)*160)
    ax2.set_xlabel("Machines needed to serve 100,000 concurrent conversations")
    ax2.tick_params(axis="y", labelsize=11)
    ax2.set_title("The best capability has the lowest adoption bar")
    ax2.grid(axis="y", visible=False)
    ax2.invert_yaxis()

    fig.suptitle("Running bigger models on desktops", fontsize=15,
                 fontweight="bold", color=INK)
    fig.savefig(FIGDIR / "fig9_model_ladder.png", dpi=155)
    plt.close(fig)


# ===========================================================================
# REPORT
# ===========================================================================

def write_md(R: dict, path: Path) -> None:
    L: list[str] = []
    ladder = {x["name"]: x for x in R["ladder"]}
    reach = {x["name"]: x for x in R["reach"]}

    L.append("# The model ladder\n")
    L.append(
        "*What changes if desktops run bigger models — not to do science, but to make the "
        "network's AI itself more capable.*\n"
    )
    L.append(
        "Generated by `analysis/model_ladder.py`. The desktop tier was introduced as the "
        "[research instrument](../WHITEPAPER.md#41-the-desktop-tier); this asks what those "
        "machines are worth as *better AI* instead.\n"
    )

    L.append("## The short answer\n")
    f32 = ladder["32B"]
    r32 = reach["32B"]
    L.append(
        f"**It is the largest single upgrade available to the mission, and it has the lowest "
        f"adoption bar in the project.** Serving 100,000 concurrent conversations against a "
        f"32B-class model needs about **{_si(r32['machines_needed']['100000'])} machines** — "
        f"{r32['pool_share_needed']['100000']*100:.1f}% of the desktops that can host it, and a "
        f"rounding error next to the 31 million phones the science case needs.\n"
    )
    L.append(
        "It also costs something real, in three places: throughput, verification, and "
        "concentration. All three are below.\n"
    )

    L.append("![The model ladder](../docs/figures/fig9_model_ladder.png)\n")

    L.append("## VRAM is a cliff, not a gradient\n")
    L.append(
        "A model that does not fit does not run at any speed. This makes the ladder a series "
        "of steps rather than a curve, and each step discards most of the fleet.\n"
    )
    L.append("| Model | Weights (Q4) | Needs | Can hold it | **Fast enough to chat** | Speed when it can |")
    L.append("|---|---|---|---|---|---|")
    for m in R["ladder"]:
        L.append(
            f"| **{m['name']}** | {m['weight_gb']:.1f} GB | {m['needs_gb']:.0f} GB | "
            f"{_si(m['hosts'])} | **{_si(m['interactive_hosts'])}** | "
            f"{m['mean_tokens_per_sec_interactive']:.0f} tok/s |"
        )
    L.append(
        "\n**\"Can hold it\" and \"fast enough to chat\" are very different numbers**, and "
        "conflating them is the easiest way to overstate this tier. A 64GB CPU-only desktop "
        "fits a 32B model and streams it at under 2 tok/s — real capacity for overnight batch "
        "work, useless for conversation. Every figure below uses the interactive column."
    )
    L.append(
        "\nNote where the cliff falls. Going from 8B to 32B discards roughly "
        f"{(1 - ladder['32B']['interactive_hosts']/ladder['8B']['interactive_hosts'])*100:.0f}% "
        "of the machines that could otherwise serve a conversation.\n"
    )

    L.append("### Apple Silicon is the best large-model substrate in consumer hands\n")
    fam70 = ladder["70B"]["interactive_by_family"]
    L.append(
        "Unified memory means the whole machine's RAM is addressable by the GPU, so capacity "
        "ceilings are far higher than on discrete cards. For the 70B tier:\n"
    )
    L.append("| Family | Machines fast enough to chat at 70B |")
    L.append("|---|---|")
    for fam, cnt in sorted(fam70.items(), key=lambda kv: -kv[1]):
        L.append(f"| {fam} | {_si(cnt)} |")
    L.append(
        "\nCPU-only machines with 64GB of RAM can *hold* a 70B model but stream weights at DDR "
        f"speeds. They fall below the {R['interactive_floor_toks']:.0f} tok/s interactive floor "
        "and are batch-only — useful for overnight work, useless for conversation.\n"
    )

    L.append("## The bandwidth wall gets worse with size\n")
    L.append(
        "`tokens/sec = usable bandwidth ÷ weight footprint`, so throughput falls roughly in "
        "proportion to parameter count. On one 24GB consumer card:\n"
    )
    L.append("| Model | Tokens/sec | Relative to 8B |")
    L.append("|---|---|---|")
    base = next(c["tokens_per_sec_on_24gb"] for c in R["cost_of_capability"] if c["name"] == "8B")
    for c in R["cost_of_capability"]:
        if c["tokens_per_sec_on_24gb"] is None:
            L.append(f"| {c['name']} | — | *does not fit in 24GB* |")
        else:
            L.append(
                f"| {c['name']} | {c['tokens_per_sec_on_24gb']:.0f} | "
                f"{c['tokens_per_sec_on_24gb']/base:.2f}× |"
            )
    L.append(
        "\n**But the fleet-wide penalty is smaller than that**, because on consumer hardware "
        "more VRAM also means more bandwidth. A 24GB card is not merely roomier than an 8GB "
        "card — it streams weights roughly three times faster. The machines that can host big "
        "models are the machines best equipped to run them quickly, which partially rescues "
        "the ladder from its own arithmetic.\n"
    )

    L.append("## What it would take\n")
    L.append("Machines needed to sustain a given number of concurrent conversations:\n")
    L.append("| Model | 1,000 sessions | 10,000 | 100,000 | 1,000,000 |")
    L.append("|---|---|---|---|---|")
    for r in R["reach"]:
        row = [f"| **{r['name']}** "]
        for t in ("1000", "10000", "100000", "1000000"):
            n = r["machines_needed"][t]
            share = r["pool_share_needed"][t]
            cell = f"| {_si(n)}"
            if share > 1.0:
                cell += " — **exceeds the pool**"
            elif share > 0.10:
                cell += f" ({share*100:.0f}% of pool)"
            row.append(cell + " ")
        L.append("".join(row) + "|")

    L.append(
        f"\nThe 32B row is the one that matters. **{_si(r32['machines_needed']['100000'])} "
        "enthusiast desktops** — the kind of person who already runs local models and reads "
        "r/LocalLLaMA — would put a genuinely capable free assistant in front of a hundred "
        "thousand people at once.\n"
    )
    L.append(
        "That is the strategic point. Everywhere else in this project, capability requires "
        "scale. Here it requires *a small number of the right machines*, and their owners are "
        "the community most likely to join first.\n"
    )

    L.append("## What it costs\n")

    L.append("### 1. Verification gets harder, exactly where it matters most\n")
    L.append(
        "Bigger models mean fewer capable hosts, which means smaller comparison pools. That "
        "hurts twice: [redundant execution](../docs/threat-model.md#2-verification-how-we-know-the-work-is-real) "
        "costs 3× of an already-expensive operation, and "
        "[diversity constraints](../docs/desktop-security.md#diversity-constraints-on-node-selection) "
        "are harder to satisfy when there are fewer candidate nodes to draw from.\n"
    )
    L.append(
        "**The flagship tier is therefore the most vulnerable to an eclipse attack** — the "
        "smallest node pool, carrying the most valuable answers. Mitigations exist (weight "
        "canaries heavily toward the big-model tier, and lean on coordinator re-derivation "
        "against a trusted reference node) but this is a genuine security regression and "
        "should be recorded as one.\n"
    )

    L.append("### 2. It competes with the science tier for the same machines\n")
    ct = R["contention"]
    L.append(
        f"About **{_si(ct['big_vram_dgpu_count'])} discrete GPUs** have 24GB or more — "
        f"{ct['share_of_dgpu_fleet']*100:.1f}% of the dGPU fleet. Those are the only cards that "
        "can host the flagship model. They are also the top of the "
        "[science tier](../WHITEPAPER.md#41-the-desktop-tier).\n"
    )
    L.append(
        "**Every device-hour spent on 32B inference is a device-hour not spent on FP32 batch "
        "work.** The project cannot promise both the best free AI and maximum research "
        "throughput from the same silicon; it has to schedule between them and say so. The "
        "[availability curve](../WHITEPAPER.md#6-follow-the-moon) helps — interactive demand "
        "peaks in daylight and science can fill the night — but it does not eliminate the "
        "contention.\n"
    )

    L.append("### 3. It concentrates the network's most valuable capability\n")
    L.append(
        f"If the flagship capability lives on {ct['share_of_dgpu_fleet']*100:.1f}% of nodes, then "
        "the network's headline service depends on a small, wealthy, and relatively "
        "identifiable subset of contributors. That is a centralisation of a different kind "
        "from the coordinator problem, and it sits awkwardly beside *owned by no one*.\n"
    )
    L.append(
        "It also interacts with the [credit design](../docs/economy.md#earning). Credits accrue "
        "for **hours, not horsepower**, deliberately — so the person contributing a 24GB card "
        "earns exactly what a four-year-old phone earns. That is the right call for the mission "
        "and it may be the wrong call for recruiting the machines the flagship tier needs. "
        "**We do not have a good answer to this tension yet.**\n"
    )

    L.append("### 4. Model licensing tightens as size increases\n")
    L.append(
        "The larger the open model, the likelier its licence carries a monthly-active-user "
        "threshold, a field-of-use restriction, or an acceptable-use policy binding downstream "
        "distributors. A network intending to reach millions cannot adopt weights whose licence "
        "quietly caps it. Each rung of this ladder needs its own licence review "
        "*before* adoption, published, per "
        "[WHITEPAPER §3.6](../WHITEPAPER.md#36-model-selection-and-licensing).\n"
    )

    L.append("## Sensitivity\n")
    L.append(
        "The VRAM distribution is the least defensible input here — it is our construction from "
        "the shape of the consumer GPU market, not a dataset. Varying the number of big cards:\n"
    )
    L.append("| Scenario | 32B-capable machines | Needed for 100k sessions |")
    L.append("|---|---|---|")
    for s in R["sensitivity"]:
        L.append(
            f"| {s['scenario']} | {_si(s['flagship_capable_machines'])} | "
            f"{_si(s['machines_for_100k_sessions'])} |"
        )
    L.append(
        "\nThe conclusion is robust to this: even with half as many big cards, the machines "
        "needed to serve 100,000 concurrent flagship conversations remain a small number of "
        "enthusiast desktops.\n"
    )

    L.append("## Recommendation\n")
    L.append(
        "**Build the ladder, tier it explicitly, and be honest that the top rung is scarce.**\n"
    )
    L.append(
        "- Ship 8B as the desktop baseline — it fits on most cards and is a clear step up from "
        "the 3B phone tier.\n"
        "- Treat 32B as the **flagship tier**, served by a deliberately recruited pool of "
        "big-VRAM machines, with heavier canary rates and reference-node adjudication to offset "
        "the smaller comparison pool.\n"
        "- Treat 70B as **batch-only** for now: Apple Silicon and 64GB workstations can host it, "
        "but there are too few for interactive service and verification would be very thin.\n"
        "- Keep the [free floor](../docs/economy.md#the-free-floor-comes-first) on the baseline "
        "tier. Access to the flagship is exactly the sort of *headroom* credits are supposed to "
        "buy — which the economy already anticipates.\n"
    )
    L.append(
        "**And it fixes a strategic weakness this project has not otherwise addressed.** A "
        "3B-class assistant competes with the free tiers of frontier labs and loses on quality. "
        "A 32B-class assistant with no account, no rate limit, no retention, and no price is a "
        "genuinely differentiated product. This is the difference between *free AI that is "
        "adequate* and *free AI that is good* — and it is reachable without waiting for "
        "planetary adoption.\n"
    )

    L.append("---\n")
    L.append(
        "**Every assumption is a named constant at the top of `model_ladder.py`.** The VRAM "
        "distribution is the one most worth arguing about. If you have real data on the "
        "consumer GPU memory distribution, that would be a genuinely valuable correction — "
        "[open an issue](../../issues/new).\n"
    )

    path.write_text("\n".join(L), encoding="utf-8")


def main() -> None:
    R = compute()
    (ROOT / "analysis" / "ladder.json").write_text(json.dumps(R, indent=2), encoding="utf-8")
    write_md(R, ROOT / "analysis" / "LADDER.md")
    fig_ladder(R)

    print("=" * 74)
    print("THE MODEL LADDER — bigger models on desktops")
    print("=" * 74)
    print(f"  Desktop mean availability ............... {R['desktop_mean_availability']:.1%}")
    print()
    print("  MODEL   CAN HOLD   CAN CHAT    SPEED    100k SESSIONS NEEDS")
    byname = {r["name"]: r for r in R["reach"]}
    for m in R["ladder"]:
        r = byname.get(m["name"])
        if not r:
            print(f"  {m['name']:>5}  {_si(m['hosts']):>9}  {'none':>9}   batch-only")
            continue
        print(f"  {m['name']:>5}  {_si(m['hosts']):>9}  {_si(m['interactive_hosts']):>9}  "
              f"{m['mean_tokens_per_sec_interactive']:5.0f} t/s  "
              f"{_si(r['machines_needed']['100000']):>8} machines"
              f"  ({r['pool_share_needed']['100000']*100:.1f}% of pool)")
    ct = R["contention"]
    print()
    print(f"  24GB+ discrete GPUs ..................... {_si(ct['big_vram_dgpu_count'])}"
          f"  ({ct['share_of_dgpu_fleet']*100:.1f}% of dGPU fleet)")
    print(f"  ... and they are ALSO the science tier — every 32B hour costs an FP32 hour")
    print("=" * 74)
    print("Wrote analysis/LADDER.md, analysis/ladder.json,")
    print("      docs/figures/fig9_model_ladder.png")


if __name__ == "__main__":
    main()
