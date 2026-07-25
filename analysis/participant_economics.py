#!/usr/bin/env python3
"""
What would a participant actually earn if we sold compute and split the money?

This module exists because "sell access to corporations and divide the payments
across the network" is the most common suggestion this project receives, and the
answer depends entirely on the magnitude. Arguing about it is pointless; the
arithmetic settles it.

Imports the verified per-device throughput and availability figures from
compute_model.py so the two cannot drift apart.

Run:
    python analysis/participant_economics.py

Outputs:
    analysis/ECONOMICS.md
    analysis/economics.json
    docs/figures/fig8_participant_earnings.png

THE SHORT ANSWER
----------------
Under central assumptions a participant nets well under a dollar a year, and in
high-electricity markets the figure is negative — they would be paying for the
privilege of contributing. Even the deliberately optimistic case lands around
twenty dollars a year.

That is the worst possible magnitude: too small to motivate anyone, but large
enough to convert a volunteer into a paid contractor and trigger every tax,
platform-policy, and fraud problem that comes with it. See ECONOMICS.md for the
non-financial consequences, which matter more than the numbers.
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
    availability_profile,
    per_device_inference,
    SECONDS_PER_YEAR,
    INK, BG, GRID, BLUE, TEAL, AMBER, MAGENTA, SLATE, DEEP,
)

ROOT = Path(__file__).resolve().parent.parent
FIGDIR = ROOT / "docs" / "figures"
FIGDIR.mkdir(parents=True, exist_ok=True)

HOURS_PER_YEAR = SECONDS_PER_YEAR / 3600.0


# ===========================================================================
# ASSUMPTIONS
# ===========================================================================
# Every one of these is arguable. The conclusion is not sensitive to any single
# one of them, which is the point of the range analysis at the bottom.

# --- what the compute is worth ---------------------------------------------
# Interruptible, unverified, high-latency compute on consumer hardware does not
# sell at cloud list price. It does not even sell at cloud *spot* price, because
# spot instances at least have a known machine behind them and no checkpointing
# requirement. We express the price as $ per TFLOP-hour of FP32 work.
#
# Reference points: a cloud T4-class GPU delivers roughly 8 TFLOPS FP32 at a
# spot price in the region of $0.10-0.35/hour, implying roughly $0.013-0.045 per
# TFLOP-hour. We take the middle of that and then apply a discount, because
# nobody pays cloud rates for compute that vanishes when someone picks up their
# phone.
CLOUD_PRICE_PER_TFLOP_HOUR = 0.022
VOLUNTEER_DISCOUNT = 0.55  # what unreliable, interruptible capacity fetches

# --- how much of the capacity actually sells -------------------------------
# Capacity is not revenue. Someone has to want it, at that price, at that hour.
UTILISATION = 0.30

# --- overheads that come off the top ---------------------------------------
VERIFICATION_OVERHEAD = 1.30  # redundant execution burns compute we cannot sell
PLATFORM_CUT = 0.30           # hosting, bandwidth, development, payment rails

# --- what it costs the participant ----------------------------------------
# Sustained system power for a phone under moderate compute load with the screen
# off. Not peak, not idle.
DEVICE_POWER_W = 3.5
CHARGING_EFFICIENCY = 0.85  # wall draw is higher than what reaches the SoC

ELECTRICITY_PRICES = {          # $/kWh, residential
    "India": 0.08,
    "United States": 0.17,
    "United Kingdom": 0.29,
    "Germany": 0.40,
}
BASELINE_MARKET = "United States"

# --- payment rails ---------------------------------------------------------
# The unavoidable cost of moving a small amount of money to a person.
PAYOUT_FIXED_FEE = 0.28      # typical per-transaction minimum
PAYOUT_PERCENT_FEE = 0.029


def compute() -> dict:
    _, _, _, fp32_tflops_per_device = per_device_inference()
    _, avail = availability_profile()
    mean_avail = float(avail.mean())

    # Hours per year a given enrolled device is actually contributing.
    contributing_hours = mean_avail * HOURS_PER_YEAR

    # Work delivered, in TFLOP-hours.
    tflop_hours = fp32_tflops_per_device * contributing_hours

    # --- revenue side ------------------------------------------------------
    price = CLOUD_PRICE_PER_TFLOP_HOUR * VOLUNTEER_DISCOUNT
    gross_market_value = tflop_hours * price
    sold = gross_market_value * UTILISATION
    sellable = sold / VERIFICATION_OVERHEAD
    to_participant_pool = sellable * (1.0 - PLATFORM_CUT)

    # --- cost side ---------------------------------------------------------
    kwh = (DEVICE_POWER_W / 1000.0) * contributing_hours / CHARGING_EFFICIENCY

    per_market = {}
    for market, rate in ELECTRICITY_PRICES.items():
        electricity = kwh * rate
        per_market[market] = {
            "electricity_price_per_kwh": rate,
            "electricity_cost_year": electricity,
            "net_year": to_participant_pool - electricity,
        }

    baseline_net = per_market[BASELINE_MARKET]["net_year"]

    # --- payment rails -----------------------------------------------------
    # What fraction of a payout is eaten by moving the money.
    def payout_fee_fraction(amount: float) -> float:
        if amount <= 0:
            return float("nan")
        fee = PAYOUT_FIXED_FEE + amount * PAYOUT_PERCENT_FEE
        return min(fee / amount, 1.0)

    rails = {
        "annual_payout": {
            "amount": to_participant_pool,
            "fee_fraction": payout_fee_fraction(to_participant_pool),
        },
        "monthly_payout": {
            "amount": to_participant_pool / 12.0,
            "fee_fraction": payout_fee_fraction(to_participant_pool / 12.0),
        },
    }

    # --- optimistic and pessimistic bounds ---------------------------------
    def scenario(price_mult, util, plat_cut, verif, power_w):
        p = CLOUD_PRICE_PER_TFLOP_HOUR * price_mult
        rev = tflop_hours * p * util / verif * (1.0 - plat_cut)
        k = (power_w / 1000.0) * contributing_hours / CHARGING_EFFICIENCY
        return rev, rev - k * ELECTRICITY_PRICES[BASELINE_MARKET]

    optimistic_rev, optimistic_net = scenario(1.00, 0.80, 0.10, 1.15, 3.0)
    central_rev, central_net = scenario(
        VOLUNTEER_DISCOUNT, UTILISATION, PLATFORM_CUT, VERIFICATION_OVERHEAD, DEVICE_POWER_W
    )
    pessimistic_rev, pessimistic_net = scenario(0.30, 0.10, 0.45, 1.50, 4.5)

    # For scale: what an hour of minimum-wage work is worth, as a yardstick for
    # whether any of this could plausibly motivate a person.
    MIN_WAGE_HOUR = 7.25

    return {
        "inputs": {
            "fp32_tflops_per_available_device": fp32_tflops_per_device,
            "mean_availability": mean_avail,
            "contributing_hours_per_year": contributing_hours,
            "tflop_hours_per_year": tflop_hours,
            "price_per_tflop_hour_cloud": CLOUD_PRICE_PER_TFLOP_HOUR,
            "volunteer_discount": VOLUNTEER_DISCOUNT,
            "utilisation": UTILISATION,
            "verification_overhead": VERIFICATION_OVERHEAD,
            "platform_cut": PLATFORM_CUT,
            "device_power_w": DEVICE_POWER_W,
            "kwh_per_year": kwh,
        },
        "revenue_chain": {
            "gross_market_value_year": gross_market_value,
            "after_utilisation": sold,
            "after_verification_overhead": sellable,
            "to_participant_year": to_participant_pool,
            "to_participant_per_night": to_participant_pool / 365.0,
        },
        "by_market": per_market,
        "baseline_market": BASELINE_MARKET,
        "baseline_net_year": baseline_net,
        "payment_rails": rails,
        "scenarios": {
            "optimistic": {"revenue": optimistic_rev, "net": optimistic_net},
            "central": {"revenue": central_rev, "net": central_net},
            "pessimistic": {"revenue": pessimistic_rev, "net": pessimistic_net},
        },
        "yardsticks": {
            "minimum_wage_hour": MIN_WAGE_HOUR,
            "hours_of_minimum_wage_equivalent": to_participant_pool / MIN_WAGE_HOUR,
        },
    }


# ===========================================================================
# FIGURE
# ===========================================================================

def fig_earnings(R: dict) -> None:
    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(12.4, 5.4), gridspec_kw={"width_ratios": [1.15, 1]}
    )

    # ---- left: the revenue chain, dollars per participant per year --------
    rc = R["revenue_chain"]
    labels = [
        "Market value of\nthe compute",
        "After utilisation\n(30% sells)",
        "After verification\noverhead",
        "To participant\nafter platform cut",
    ]
    vals = [
        rc["gross_market_value_year"],
        rc["after_utilisation"],
        rc["after_verification_overhead"],
        rc["to_participant_year"],
    ]
    colors = [SLATE, TEAL, BLUE, AMBER]
    bars = ax1.bar(labels, vals, color=colors, width=0.62, zorder=3)
    for b, v in zip(bars, vals):
        ax1.annotate(f"${v:,.2f}", (b.get_x() + b.get_width() / 2, v),
                     textcoords="offset points", xytext=(0, 6),
                     ha="center", fontweight="bold", fontsize=10.5)
    ax1.set_ylabel("US$ per participant per year")
    ax1.set_title("What a year of one phone's spare compute is worth")
    ax1.set_ylim(0, max(vals) * 1.28)
    ax1.grid(axis="x", visible=False)
    ax1.tick_params(axis="x", labelsize=9.5)

    # ---- right: net after electricity, by market -------------------------
    markets = list(R["by_market"].keys())
    nets = [R["by_market"][m]["net_year"] for m in markets]
    cols = [TEAL if n > 0 else MAGENTA for n in nets]
    ypos = np.arange(len(markets))
    ax2.barh(ypos, nets, color=cols, height=0.58, zorder=3)
    ax2.axvline(0, color=INK, lw=1.4, zorder=4)
    for y, n in zip(ypos, nets):
        ax2.annotate(
            f"${n:+,.2f}", (n, y),
            textcoords="offset points",
            xytext=(7 if n >= 0 else -7, 0),
            ha="left" if n >= 0 else "right", va="center",
            fontweight="bold", fontsize=10.5,
        )
    ax2.set_yticks(ypos)
    ax2.set_yticklabels(
        [f"{m}\n(${R['by_market'][m]['electricity_price_per_kwh']:.2f}/kWh)" for m in markets],
        fontsize=9.5,
    )
    ax2.set_xlabel("US$ per year, after the participant's own electricity")
    ax2.set_title("What they keep")
    pad = max(abs(min(nets)), abs(max(nets))) * 0.55
    ax2.set_xlim(min(nets) - pad, max(nets) + pad)
    ax2.grid(axis="y", visible=False)

    # Placed in the empty positive-x region; the negative bars occupy the left.
    ax2.annotate(
        "In high-electricity markets\nthe participant pays\nto contribute.",
        xy=(0.60, 0.66), xycoords="axes fraction", fontsize=10, color=DEEP,
        bbox=dict(boxstyle="round,pad=0.45", fc="white", ec=MAGENTA, lw=1.3),
    )

    fig.suptitle(
        "Paying participants: the magnitude is the argument",
        fontsize=15, fontweight="bold", color=INK,
    )
    fig.savefig(FIGDIR / "fig8_participant_earnings.png", dpi=155)
    plt.close(fig)


# ===========================================================================
# REPORT
# ===========================================================================

def write_md(R: dict, path: Path) -> None:
    i, rc, sc, rails = R["inputs"], R["revenue_chain"], R["scenarios"], R["payment_rails"]
    L: list[str] = []

    L.append("# Should we sell compute and pay participants?\n")
    L.append(
        "Generated by `analysis/participant_economics.py`. This is the most frequently "
        "suggested change to the project's funding model, so it gets a costed answer "
        "rather than an opinion.\n"
    )
    L.append("## The short version\n")
    L.append(
        f"A participant would net **${R['baseline_net_year']:.2f} per year** in "
        f"{R['baseline_market']} under central assumptions, after their own electricity. "
        f"That is **{R['yardsticks']['hours_of_minimum_wage_equivalent']:.2f} hours** of "
        "minimum-wage work, per year, for running a service on their phone every night.\n"
    )
    L.append(
        "In high-electricity markets the number is **negative** — the participant pays for "
        "the privilege of contributing.\n"
    )
    L.append(
        "This is the worst possible magnitude. Too small to motivate anyone, and large "
        "enough to convert a volunteer into a paid contractor — which triggers every tax, "
        "platform-policy, and fraud problem in the second half of this document.\n"
    )

    L.append("![What a participant would earn](../docs/figures/fig8_participant_earnings.png)\n")
    L.append("## Where the money goes\n")
    L.append("| Stage | US$/participant/year |")
    L.append("|---|---|")
    L.append(f"| Market value of the compute delivered | ${rc['gross_market_value_year']:.2f} |")
    L.append(f"| × utilisation ({i['utilisation']:.0%} of capacity actually sells) | ${rc['after_utilisation']:.2f} |")
    L.append(f"| ÷ verification overhead ({i['verification_overhead']:.2f}×) | ${rc['after_verification_overhead']:.2f} |")
    L.append(f"| − platform cut ({i['platform_cut']:.0%}: hosting, bandwidth, dev, payment rails) | **${rc['to_participant_year']:.2f}** |")
    L.append(f"| Per night | ${rc['to_participant_per_night']:.4f} |")

    L.append("\n## Minus the participant's own electricity\n")
    L.append(
        f"A phone drawing {i['device_power_w']:.1f}W for "
        f"{i['contributing_hours_per_year']:,.0f} contributing hours consumes about "
        f"**{i['kwh_per_year']:.1f} kWh/year** at the wall.\n"
    )
    L.append("| Market | Electricity | Earnings | **Net** |")
    L.append("|---|---|---|---|")
    for m, d in R["by_market"].items():
        L.append(
            f"| {m} (${d['electricity_price_per_kwh']:.2f}/kWh) | "
            f"−${d['electricity_cost_year']:.2f} | ${rc['to_participant_year']:.2f} | "
            f"**${d['net_year']:+.2f}** |"
        )

    L.append("\n## Even the optimistic case does not rescue it\n")
    L.append("| Scenario | Gross to participant | Net after electricity |")
    L.append("|---|---|---|")
    for name in ("optimistic", "central", "pessimistic"):
        s = sc[name]
        L.append(f"| {name.title()} | ${s['revenue']:.2f}/yr | **${s['net']:+.2f}/yr** |")
    L.append(
        f"\nThe optimistic case assumes full cloud pricing with no volunteer discount, "
        f"{80}% utilisation, a 10% platform cut, and an efficient phone. It reaches "
        f"**${sc['optimistic']['net']:.0f}/year**. Nobody changes their behaviour for "
        "that, and it still incurs every downside below.\n"
    )

    L.append("## Payment rails make small payouts absurd\n")
    L.append("| Payout cadence | Amount | Eaten by fees |")
    L.append("|---|---|---|")
    for k, v in rails.items():
        L.append(
            f"| {k.replace('_', ' ').title()} | ${v['amount']:.2f} | "
            f"**{v['fee_fraction']:.0%}** |"
        )
    L.append(
        "\nA fixed per-transaction fee of $"
        f"{PAYOUT_FIXED_FEE:.2f} against a ${rails['monthly_payout']['amount']:.2f} monthly "
        "payout means most of the money never reaches the person. The only rail that makes "
        "micropayments cheap is a token — which is the one thing this project has "
        "committed never to do, and the thing that caps every competitor in the crypto "
        "niche.\n"
    )

    L.append("## The non-financial costs, which are the real argument\n")

    L.append("### 1. It turns an unsolved security problem into the business model\n")
    L.append(
        "[Sybil resistance is explicitly bounded, not solved](../docs/threat-model.md#sybil-attacks) — "
        "no cheap solution exists without a trusted registry or a costly stake. Today a fake "
        "node earns nothing but reputation. **Under payment, every fake node is direct "
        "revenue.** We would be attaching a cash bounty to the one attack we have already "
        "admitted we cannot prevent. Emulator farms are cheap and this is a solved craft on "
        "the attacker's side.\n"
    )

    L.append("### 2. It makes app-store approval harder, not easier\n")
    L.append(
        "[Store policy is already a live risk](../docs/threat-model.md#app-store-removal). "
        "Paying users for background resource use moves the app from *volunteer computing* "
        "into the category stores scrutinise most heavily. It also gives a reviewer a simple, "
        "accurate description that sounds bad: an app that pays people to run compute jobs "
        "on their phones.\n"
    )

    L.append("### 3. It changes the participant's legal status\n")
    L.append(
        "A volunteer becomes a paid contractor. That brings income reporting obligations, "
        "worker-classification questions in some jurisdictions, consumer-protection rules "
        "about advertised earnings, and cross-border payment and tax compliance. A project "
        "with no funding and one maintainer would be taking on a compliance surface larger "
        "than its engineering surface. **This needs actual legal advice, not a founder's "
        "judgement** — which is itself a cost.\n"
    )

    L.append("### 4. It destroys the one unclaimed position\n")
    L.append(
        "[§12 of the whitepaper](../WHITEPAPER.md#12-prior-art-and-positioning) argues that "
        "Acurast, Pocket Network, Destra and the rest all solved participation with payment, "
        "and none escaped the crypto niche. Adding payment makes this the fifteenth entrant "
        "in a crowded category, with less funding than the incumbents and no "
        "differentiation. The unclaimed position — the SETI@home position — is the entire "
        "strategic thesis.\n"
    )

    L.append("### 5. It creates a constituency that wants the safety gate weakened\n")
    L.append(
        "The [contribution gate](../ARCHITECTURE.md#33-the-contribution-gate) is conservative "
        "because nobody is being paid. Introduce earnings and some participants will want "
        "hotter phones, longer windows, and a lower battery threshold, because those "
        "increase their income. It also directly contradicts "
        "[constitution item 7](../docs/governance.md#a-published-constitution): participant "
        "experience outranks paying workloads.\n"
    )

    L.append("### 6. It changes what the surplus is for\n")
    L.append(
        "The project's justification for existing is that the surplus becomes a research "
        "instrument for people who cannot afford one. If corporate buyers pay more than "
        "research bodies — they will — then science is outbid on its own network, by "
        "construction.\n"
    )

    L.append("## What the instinct behind the question gets right\n")
    L.append(
        "Two things, and both are real:\n\n"
        "1. **The funding model is unvalidated.** No institution has agreed to pay for "
        "anything, and the whitepaper "
        "[says so plainly](../WHITEPAPER.md#103-the-honest-gap). Wanting a firmer revenue "
        "line is correct.\n"
        "2. **There is a genuine fairness argument.** If a corporation profits from work "
        "done on someone's hardware, that person's interest in the proceeds is not "
        "frivolous.\n\n"
        "The problem is not the motive. It is that at this magnitude, cash cannot deliver "
        "on either.\n"
    )

    L.append("## Recommended alternatives\n")
    L.append(
        "**Sell to corporations. Do not divide the cash.** Corporate batch-compute revenue "
        "funds hosting, development, a published research grant pool, and a reserve — with "
        "**open books**. Every dollar in and out published quarterly. This captures the "
        "revenue, keeps the volunteer framing, and avoids all six costs above.\n"
    )
    L.append(
        "**Reciprocate in capability, not currency.** Contributors get priority routing, "
        "access to larger models, and higher quotas. This is real value with no payment "
        "rails, no tax status change, and no Sybil bounty — a fake node would earn only the "
        "right to use a network it is defrauding.\n"
    )
    L.append(
        "**Let participants direct their share.** If the fairness argument should be "
        "honoured in money, let each participant assign their notional share to a research "
        "project or charity from a published list. This preserves the gift framing, is "
        "far simpler to administer, and turns the accounting into a feature: *your phone "
        "funded this study.*\n"
    )
    L.append(
        "**Make transparency the trust mechanism instead of payouts.** \"Owned by no one, "
        "with open books\" is a stronger and more credible claim than \"earn $0.60 a "
        "year.\"\n"
    )
    L.append(
        "**If cash to individuals is still wanted:** do it as a distribution from a "
        "participant-owned cooperative or foundation rather than as per-task payment. "
        "Different legal character, different incentive structure, and it does not price "
        "each night's work — which is the thing that invites the comparison to minimum "
        "wage that this document opens with.\n"
    )

    L.append("---\n")
    L.append(
        "**Every assumption here is arguable and all of them are named constants at the top "
        "of `participant_economics.py`.** If you think the price of interruptible consumer "
        "compute is five times what we assumed, change one number and re-run — the "
        "optimistic column already tests roughly that, and the conclusion holds. "
        "[File an issue](../../issues/new) if it does not.\n"
    )

    path.write_text("\n".join(L), encoding="utf-8")


def main() -> None:
    R = compute()
    (ROOT / "analysis" / "economics.json").write_text(
        json.dumps(R, indent=2), encoding="utf-8"
    )
    write_md(R, ROOT / "analysis" / "ECONOMICS.md")
    fig_earnings(R)

    rc, sc = R["revenue_chain"], R["scenarios"]
    print("=" * 72)
    print("PAYING PARTICIPANTS — what one phone earns per year")
    print("=" * 72)
    print(f"  TFLOP-hours contributed / year ......... {R['inputs']['tflop_hours_per_year']:,.0f}")
    print(f"  Market value of that compute ........... ${rc['gross_market_value_year']:.2f}")
    print(f"  Reaching the participant ............... ${rc['to_participant_year']:.2f}")
    print(f"  Their electricity ({R['baseline_market']}) ......... "
          f"-${R['by_market'][R['baseline_market']]['electricity_cost_year']:.2f}")
    print(f"  NET .................................... ${R['baseline_net_year']:+.2f} / year")
    print()
    for m, d in R["by_market"].items():
        print(f"    {m:<16} (${d['electricity_price_per_kwh']:.2f}/kWh) "
              f"net ${d['net_year']:+.2f}/yr")
    print()
    print(f"  Optimistic case ........................ ${sc['optimistic']['net']:+.2f} / year")
    print(f"  Pessimistic case ....................... ${sc['pessimistic']['net']:+.2f} / year")
    print(f"  = hours of minimum wage ................ "
          f"{R['yardsticks']['hours_of_minimum_wage_equivalent']:.2f} h / year")
    print(f"  Monthly payout eaten by fees ........... "
          f"{R['payment_rails']['monthly_payout']['fee_fraction']:.0%}")
    print("=" * 72)
    print("Wrote analysis/ECONOMICS.md, analysis/economics.json,")
    print("      docs/figures/fig8_participant_earnings.png")


if __name__ == "__main__":
    main()
