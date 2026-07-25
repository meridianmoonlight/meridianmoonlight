#!/usr/bin/env python3
"""
MERIDIAN MOONLIGHT — compute model.

This file is the single source of numeric truth for the project. Every figure in
the whitepaper, every number on the website, and every claim in the README is
produced by running this script. Nothing is hand-typed downstream.

Run:
    python analysis/compute_model.py

Outputs:
    analysis/numbers.json   machine-readable, consumed by docs tooling
    analysis/NUMBERS.md     human-readable table of every derived figure
    docs/figures/*.png      all figures

DESIGN PRINCIPLE
----------------
Two claims about this network need completely different physics, and conflating
them is the most common error in decentralized-compute proposals:

  1. INFERENCE (serving AI to people) is *memory-bandwidth bound*. Generating one
     token requires streaming every model weight from RAM into the accelerator.
     Peak NPU TOPS are almost irrelevant; GB/s is the ceiling. Batch size on a
     phone is 1, so there is no way to amortize that read across many users.

  2. SCIENTIFIC BATCH WORK (docking, molecular dynamics, ensembles) is
     *compute bound* and floating-point. It does not run on an INT8 NPU at all —
     it runs on the CPU/GPU in FP32. Arithmetic intensity is high, so the chip
     can actually approach its FP ceiling.

Mixing these units — quoting INT8 NPU TOPS and then comparing to Folding@home's
FP throughput — inflates the numbers by one to two orders of magnitude. This
model keeps them strictly separate.

Every assumption below is a named constant with a stated basis and an honest
uncertainty. Where a figure is uncertain we prefer the conservative end. The
sensitivity analysis at the bottom shows what happens if we are wrong.

Milestone 0 of the roadmap exists specifically to replace the modelled
per-device throughput numbers with measured ones.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parent.parent
FIGDIR = ROOT / "docs" / "figures"
FIGDIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# PALETTE
# ---------------------------------------------------------------------------
# Protanopia-safe. Red is never used as a signal colour anywhere in this
# project: roughly 8% of men (including this project's author) cannot reliably
# distinguish it from green. Categorical hues are separated by luminance as well
# as by hue, so the figures survive greyscale printing too.

INK = "#131A33"
BG = "#F6F7FB"
GRID = "#DCE1F0"
BLUE = "#3B5BDB"
TEAL = "#0E9DA8"
AMBER = "#E8912B"
MAGENTA = "#B3399E"
SLATE = "#7A88A8"
DEEP = "#1E2A5A"

plt.rcParams.update(
    {
        "figure.facecolor": BG,
        "axes.facecolor": BG,
        "savefig.facecolor": BG,
        "axes.edgecolor": "#B9C1DA",
        "axes.labelcolor": INK,
        "axes.titlecolor": INK,
        "text.color": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "grid.color": GRID,
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "axes.grid": True,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.constrained_layout.use": True,
    }
)


# ===========================================================================
# 1. THE DEVICE FLEET
# ===========================================================================
# How many phones could actually be a node? The binding constraint is RAM: the
# model weights plus KV cache plus the OS must coexist without the app being
# killed. Android will evict a background process long before the device swaps.
#
# BASIS: global active smartphone install base is on the order of 4.5-4.7B
# handsets. The share carrying >=8GB RAM is a minority: 8GB+ only became common
# in the mid-tier around 2022-2023, and install base lags shipments by roughly
# a 3-4 year replacement cycle.
#
# HONESTY NOTE: the original project draft assumed 2.2B devices with 8GB+ RAM
# today. That number is a plausible *2030* figure, not a present-day one. We use
# the present-day figure for all "today" claims and state the projection
# separately.

SMARTPHONE_INSTALL_BASE = 4.60e9  # active handsets worldwide, 2026 estimate
SHARE_RAM_8GB_PLUS = 0.26  # >=8GB: can host a 3-4B parameter model at Q4
SHARE_RAM_6GB = 0.22  # 6GB: can host a 1.5-2B parameter model at Q4

# Projection, for the long-horizon claims only.
INSTALL_BASE_2030 = 5.00e9
SHARE_RAM_8GB_PLUS_2030 = 0.48

CAPABLE_FLEET_TODAY = SMARTPHONE_INSTALL_BASE * SHARE_RAM_8GB_PLUS
CAPABLE_FLEET_2030 = INSTALL_BASE_2030 * SHARE_RAM_8GB_PLUS_2030


# ===========================================================================
# 2. PER-DEVICE INFERENCE THROUGHPUT  (memory-bandwidth bound)
# ===========================================================================
# Decode throughput ceiling for a batch-size-1 autoregressive model:
#
#     tokens/sec  =  usable_memory_bandwidth (GB/s)  /  weight_footprint (GB)
#
# because every weight must be read once per generated token. This is why a
# phone advertising 45 INT8 TOPS delivers ~20 tokens/sec on a 3B model: it is
# starved, not slow.
#
# `usable_fraction` accounts for the gap between the datasheet peak and what a
# real kernel achieves — DRAM refresh, page misses, contention with the OS and
# display pipeline, and imperfect prefetch. llama.cpp on mobile SoCs typically
# lands at 55-65% of theoretical peak.
#
# `thermal_derate` accounts for sustained operation. Burst benchmarks are run
# for seconds on a cool device. We are proposing eight-hour runs on a phone that
# is simultaneously charging, which is itself a heat source. Sustained clocks on
# mobile silicon settle well below burst.


@dataclass
class DeviceClass:
    name: str
    share: float  # share of the >=8GB capable fleet
    peak_bandwidth_gbs: float  # datasheet peak memory bandwidth
    usable_fraction: float  # achievable fraction of peak, real kernels
    model_params_b: float  # model size this class hosts, billions
    weight_gb: float  # Q4_K_M weight footprint on disk/RAM
    fp32_peak_tflops: float  # GPU FP32 peak, for scientific workloads
    fp32_sustained_fraction: float  # sustained share of FP peak over hours


# Q4_K_M averages ~4.8 bits per weight including scales and the higher-precision
# tensors that quantisation schemes keep in 6-8 bit. 3B params -> ~1.80 GB.
DEVICE_CLASSES = [
    DeviceClass(
        name="Flagship (LPDDR5X)",
        share=0.30,
        peak_bandwidth_gbs=68.0,
        usable_fraction=0.62,
        model_params_b=3.0,
        weight_gb=1.80,
        fp32_peak_tflops=1.50,
        fp32_sustained_fraction=0.30,
    ),
    DeviceClass(
        name="Upper-mid (LPDDR5)",
        share=0.45,
        peak_bandwidth_gbs=44.0,
        usable_fraction=0.58,
        model_params_b=3.0,
        weight_gb=1.80,
        fp32_peak_tflops=0.85,
        fp32_sustained_fraction=0.33,
    ),
    DeviceClass(
        name="Mid (LPDDR4X)",
        share=0.25,
        peak_bandwidth_gbs=29.0,
        usable_fraction=0.55,
        model_params_b=1.5,
        weight_gb=0.95,
        fp32_peak_tflops=0.50,
        fp32_sustained_fraction=0.30,
    ),
]

THERMAL_DERATE = 0.70  # sustained vs burst, 8-hour run while charging

# For the "why not just use the NPU TOPS number" comparison figure. This is the
# marketing peak for a current flagship mobile NPU at INT8.
FLAGSHIP_NPU_PEAK_TOPS = 45.0


# ===========================================================================
# 2b. THE DESKTOP TIER
# ===========================================================================
# Desktops are better nodes than phones in almost every dimension: more RAM, real
# GPUs, active cooling, mains power, no app-store review, and no background
# execution limits. They are also where scientific batch work belongs, because
# FP32 throughput on a discrete GPU is roughly two orders of magnitude above a
# phone's.
#
# Two corrections applied to the earlier desktop estimates:
#
#   1. The same bandwidth wall applies. A "80 TOPS" gaming GPU decoding an 8B Q4
#      model at batch 1 is bound by its ~350 GB/s of VRAM bandwidth, not by its
#      tensor cores. Peak TOPS overstates decode throughput here just as badly as
#      it does on mobile.
#
#   2. Availability is LOWER than mobile, not higher. Phones get plugged in
#      nightly as a matter of habit; desktops get switched off. This is the one
#      place the desktop tier loses, and it partly cancels correction (1) when
#      computing crossover points.
#
# Machine counts are estimates of the installed base able to host a node at all.

DESKTOP_DGPU_COUNT = 250e6         # gaming and workstation discrete GPUs
DESKTOP_APPLE_COUNT = 70e6         # Apple Silicon Macs (unified memory)
DESKTOP_CPU_ONLY_COUNT = 600e6     # 16GB+ RAM, integrated graphics only


@dataclass
class DesktopClass:
    name: str
    count: float
    peak_bandwidth_gbs: float       # VRAM or unified/system memory bandwidth
    usable_fraction: float
    model_params_b: float           # desktops can host larger models than phones
    weight_gb: float
    fp32_peak_tflops: float         # this is what the science case rests on
    fp32_sustained_fraction: float  # active cooling + mains power -> high


DESKTOP_CLASSES = [
    DesktopClass(
        name="Discrete GPU",
        count=DESKTOP_DGPU_COUNT,
        peak_bandwidth_gbs=350.0,      # fleet average across 1650/3050/3060/4060/4070+
        usable_fraction=0.75,          # GPU memory subsystems are efficient
        model_params_b=8.0,
        weight_gb=4.70,                # 8B at Q4_K_M
        fp32_peak_tflops=12.0,         # fleet average, not a flagship
        fp32_sustained_fraction=0.80,
    ),
    DesktopClass(
        name="Apple Silicon",
        count=DESKTOP_APPLE_COUNT,
        peak_bandwidth_gbs=120.0,      # M1 68 -> M2/M3 100 -> Pro/Max far higher
        usable_fraction=0.70,
        model_params_b=8.0,
        weight_gb=4.70,
        fp32_peak_tflops=4.0,
        fp32_sustained_fraction=0.80,
    ),
    DesktopClass(
        name="CPU only (16GB+)",
        count=DESKTOP_CPU_ONLY_COUNT,
        peak_bandwidth_gbs=50.0,       # dual-channel DDR4/DDR5
        usable_fraction=0.60,
        model_params_b=3.0,
        weight_gb=1.80,
        fp32_peak_tflops=0.25,         # AVX2/AVX-512 across ~8 cores
        fp32_sustained_fraction=0.80,
    ),
]

DESKTOP_FLEET = sum(d.count for d in DESKTOP_CLASSES)

# Desktop thermal derate is much gentler than mobile: a tower with fans on mains
# power holds its clocks nearly indefinitely.
DESKTOP_THERMAL_DERATE = 0.88

# Desktop contribution gate. Same shape as mobile, different probabilities.
# The dominant term is simply whether the machine is left powered on.
P_DESKTOP_LEFT_ON = 0.35        # most people shut down; enthusiasts do not
P_DESKTOP_NETWORK = 0.97        # wired or permanent Wi-Fi
P_DESKTOP_IDLE = 0.95
DESKTOP_DAYTIME_AVAILABILITY = 0.12   # idle at a desk during the working day

DESKTOP_NIGHT_PEAK = P_DESKTOP_LEFT_ON * P_DESKTOP_NETWORK * P_DESKTOP_IDLE


def per_desktop_inference():
    """Per-class and fleet-weighted desktop throughput. Same physics as mobile."""
    rows = []
    for d in DESKTOP_CLASSES:
        usable_bw = d.peak_bandwidth_gbs * d.usable_fraction
        toks_burst = usable_bw / d.weight_gb
        toks_sustained = toks_burst * DESKTOP_THERMAL_DERATE
        ops_per_token = 2.0 * d.model_params_b * 1e9
        share = d.count / DESKTOP_FLEET
        rows.append(
            {
                "name": d.name,
                "count": d.count,
                "share": share,
                "usable_bandwidth_gbs": usable_bw,
                "tokens_per_sec_burst": toks_burst,
                "tokens_per_sec_sustained": toks_sustained,
                "sustained_tops": toks_sustained * ops_per_token / 1e12,
                "fp32_sustained_tflops": d.fp32_peak_tflops * d.fp32_sustained_fraction,
            }
        )
    w_tok = sum(r["share"] * r["tokens_per_sec_sustained"] for r in rows)
    w_tops = sum(r["share"] * r["sustained_tops"] for r in rows)
    w_flops = sum(r["share"] * r["fp32_sustained_tflops"] for r in rows)
    return rows, w_tok, w_tops, w_flops


def desktop_availability(local_h):
    """Desktop equivalent of device_availability(). Lower ceiling than mobile."""
    return DESKTOP_DAYTIME_AVAILABILITY + (
        DESKTOP_NIGHT_PEAK - DESKTOP_DAYTIME_AVAILABILITY
    ) * _night_weight(local_h)


def desktop_availability_profile(n: int = 24 * 12):
    hours = np.linspace(0, 24, n, endpoint=False)
    vals = np.array(
        [
            float(np.sum(DEVICE_DENSITY * desktop_availability(local_hour(_LON_GRID, h))))
            for h in hours
        ]
    )
    return hours, vals


def per_device_inference():
    """Returns per-class and fleet-weighted inference throughput."""
    rows = []
    for d in DEVICE_CLASSES:
        usable_bw = d.peak_bandwidth_gbs * d.usable_fraction
        toks_burst = usable_bw / d.weight_gb
        toks_sustained = toks_burst * THERMAL_DERATE
        # 2 operations (one multiply, one add) per parameter per token.
        ops_per_token = 2.0 * d.model_params_b * 1e9
        sustained_ops = toks_sustained * ops_per_token
        rows.append(
            {
                "name": d.name,
                "share": d.share,
                "usable_bandwidth_gbs": usable_bw,
                "tokens_per_sec_burst": toks_burst,
                "tokens_per_sec_sustained": toks_sustained,
                "sustained_tops": sustained_ops / 1e12,
                "fp32_sustained_tflops": d.fp32_peak_tflops * d.fp32_sustained_fraction,
            }
        )
    w_tok = sum(r["share"] * r["tokens_per_sec_sustained"] for r in rows)
    w_tops = sum(r["share"] * r["sustained_tops"] for r in rows)
    w_flops = sum(r["share"] * r["fp32_sustained_tflops"] for r in rows)
    return rows, w_tok, w_tops, w_flops


# ===========================================================================
# 3. AVAILABILITY  ("follow the moon")
# ===========================================================================
# A device contributes only while charging AND on Wi-Fi AND screen-off/idle.
# The overnight ceiling is therefore not 100% or even 95% — it is the joint
# probability of three ordinary human behaviours.
#
# HONESTY NOTE: the original draft assumed 95% overnight availability. That
# implicitly assumes every enrolled user charges every night on Wi-Fi, which is
# not how people behave. We model the conjunction explicitly.

P_CHARGES_OVERNIGHT = 0.72  # plugs in on a given night
P_ON_WIFI = 0.86  # home Wi-Fi rather than cellular-only
P_IDLE_UNDISTURBED = 0.97  # not picked up mid-window
DAYTIME_AVAILABILITY = 0.05  # desk/car charging that also meets the gate

NIGHT_PEAK_AVAILABILITY = P_CHARGES_OVERNIGHT * P_ON_WIFI * P_IDLE_UNDISTURBED

# Device density by longitude. We deliberately do NOT model this as a handful of
# point clusters: doing so creates an artificial global trough where every
# cluster happens to be in daylight at once, which is a modelling artefact
# rather than a real property of the planet. Handsets are spread more or less
# continuously across inhabited longitudes, so we place weighted clusters and
# smear each one with a Gaussian before summing onto a fine longitude grid.
#
# Weights approximate where capable (>=6-8GB) handsets actually live, which is
# not the same as raw population — it skews toward higher-income markets.

DEVICE_CLUSTERS = [
    # (name, centre longitude, weight, spread in degrees)
    ("US West & Mexico", -105.0, 0.045, 9.0),
    ("Canada", -95.0, 0.010, 12.0),
    ("US East", -77.0, 0.055, 8.0),
    ("Andes & Colombia", -72.0, 0.025, 7.0),
    ("Brazil & Southern Cone", -47.0, 0.045, 9.0),
    ("UK & Ireland", -3.0, 0.020, 3.0),
    ("West Africa", 3.0, 0.030, 8.0),
    ("Western Europe", 7.0, 0.055, 6.0),
    ("Southern Africa", 28.0, 0.015, 7.0),
    ("Eastern Europe & Turkey", 32.0, 0.040, 8.0),
    ("East Africa", 37.0, 0.025, 6.0),
    ("Middle East", 48.0, 0.030, 7.0),
    ("Central Asia & Urals", 60.0, 0.020, 10.0),
    ("Pakistan & Western India", 70.0, 0.090, 6.0),
    ("Eastern India & Bangladesh", 85.0, 0.130, 6.0),
    ("Siberia", 90.0, 0.010, 20.0),
    ("Mainland Southeast Asia", 105.0, 0.080, 7.0),
    ("Eastern China", 115.0, 0.155, 7.0),
    ("Maritime Southeast Asia", 122.0, 0.050, 8.0),
    ("Japan & Korea", 133.0, 0.060, 5.0),
    ("Australia & New Zealand", 148.0, 0.020, 10.0),
]

_LON_GRID = np.arange(-180.0, 180.0, 2.0)


def _device_density() -> np.ndarray:
    """Normalised share of the enrolled fleet per longitude bin."""
    d = np.zeros_like(_LON_GRID)
    for _name, centre, weight, spread in DEVICE_CLUSTERS:
        # Wrap the angular distance so clusters near the dateline behave.
        delta = (_LON_GRID - centre + 180.0) % 360.0 - 180.0
        d += weight * np.exp(-0.5 * (delta / spread) ** 2)
    return d / d.sum()


DEVICE_DENSITY = _device_density()


def local_hour(lon, utc_hour):
    return (utc_hour + np.asarray(lon) / 15.0) % 24.0


# The "night window" is not a step function — people go to bed and get up at
# different times, and a phone put on the charger at 21:00 is contributing long
# before midnight. We model the overnight window as a smooth bell over the local
# clock, centred on 02:00, reaching half-height around 21:30 and 06:30 and
# decaying to the daytime baseline through the working day.
NIGHT_CENTRE_HOUR = 2.0
NIGHT_HALF_WIDTH_HOURS = 4.5
NIGHT_EDGE_SOFTNESS = 1.0


def _night_weight(local_h):
    """Smooth 0..1 overnight window over the local clock."""
    local_h = np.asarray(local_h, dtype=float)
    # Circular distance from the centre of the night, in hours (0..12).
    dist = np.abs((local_h - NIGHT_CENTRE_HOUR + 12.0) % 24.0 - 12.0)
    return 1.0 / (1.0 + np.exp((dist - NIGHT_HALF_WIDTH_HOURS) / NIGHT_EDGE_SOFTNESS))


def device_availability(local_h):
    """Probability a single enrolled device is contributing at this local hour."""
    return DAYTIME_AVAILABILITY + (NIGHT_PEAK_AVAILABILITY - DAYTIME_AVAILABILITY) * _night_weight(
        local_h
    )


def global_availability(utc_hour: float) -> float:
    """Share of the *enrolled* fleet contributing at a given UTC hour."""
    return float(np.sum(DEVICE_DENSITY * device_availability(local_hour(_LON_GRID, utc_hour))))


def availability_profile(n: int = 24 * 12):
    hours = np.linspace(0, 24, n, endpoint=False)
    vals = np.array([global_availability(h) for h in hours])
    return hours, vals


# Coarse regions, used only for the stacked area chart. The underlying model
# uses the continuous density above.
REGIONS = [
    {"name": "Americas", "lo": -180.0, "hi": -30.0},
    {"name": "Europe & Africa", "lo": -30.0, "hi": 45.0},
    {"name": "South & Central Asia", "lo": 45.0, "hi": 95.0},
    {"name": "East Asia & Oceania", "lo": 95.0, "hi": 180.0},
]


def region_availability(region, utc_hour: float) -> float:
    """That region's contribution to global availability, in fleet-share units."""
    mask = (_LON_GRID >= region["lo"]) & (_LON_GRID < region["hi"])
    return float(
        np.sum(DEVICE_DENSITY[mask] * device_availability(local_hour(_LON_GRID[mask], utc_hour)))
    )


# ===========================================================================
# 4. REFERENCE POINTS FOR COMPARISON
# ===========================================================================
# We compare against two anchors. Both are stated as assumptions with ranges,
# because neither is a published, audited figure.

# Folding@home at its COVID-era peak — the largest volunteer computing effort in
# history, widely reported at roughly 2.4 exaFLOPS across ~1M machines. This is
# a mixed-precision figure dominated by consumer GPU FP32.
FOLDING_AT_HOME_PEAK_EXAFLOPS = 2.4

# A very large AI training cluster, ~100k H100-class accelerators. At ~1,979
# dense INT8 TOPS each this is ~200 exaOPS of *peak* throughput. We include it
# only to demonstrate why peak-OPS is the wrong axis: neither this cluster nor
# MERIDIAN can sustain its peak on real inference work.
LARGE_DC_PEAK_EXAOPS_INT8 = 200.0

# Realistic aggregate serving throughput for that cluster on a small model with
# continuous batching. Batching is the data centre's structural advantage: one
# weight read serves hundreds of concurrent sequences. Wide range, stated as
# such.
DC_TOKENS_PER_SEC_PER_GPU = 3000.0
DC_GPU_COUNT = 100_000

# What one person plausibly consumes. Heavy daily use of a chat assistant is a
# few hundred thousand output tokens per month, not per day.
HEAVY_USER_TOKENS_PER_DAY = 30_000
SECONDS_PER_DAY = 86_400
SECONDS_PER_YEAR = 3.156e7


# ===========================================================================
# 5. DERIVED RESULTS
# ===========================================================================


def compute_all() -> dict:
    rows, w_tok, w_tops, w_flops = per_device_inference()
    hours, avail = availability_profile()
    mean_avail = float(avail.mean())
    min_avail = float(avail.min())
    max_avail = float(avail.max())

    def inference_tokens_per_sec(enrolled: float) -> float:
        return enrolled * mean_avail * w_tok

    def science_exaflops(enrolled: float) -> float:
        return enrolled * mean_avail * w_flops * 1e12 / 1e18

    def sustained_exaops_int8(enrolled: float) -> float:
        return enrolled * mean_avail * w_tops * 1e12 / 1e18

    # --- self-sufficiency: can the network feed its own members? --------
    # Capacity per participant is scale-invariant, because both the numerator
    # and the denominator are proportional to enrolment. This is the single most
    # important structural property of the design: it means the network is
    # viable at a thousand devices and at a billion, and never needs to reach a
    # threshold before it is useful.
    #
    # We report two bounds. The mean case averages over the 24-hour cycle. The
    # worst case uses the global availability trough, which is the honest number
    # because demand peaks during waking hours while supply peaks overnight.
    tokens_per_participant_per_day = mean_avail * w_tok * SECONDS_PER_DAY
    self_sufficiency_ratio = tokens_per_participant_per_day / HEAVY_USER_TOKENS_PER_DAY
    worst_hour_tokens_per_participant_per_day = min_avail * w_tok * SECONDS_PER_DAY
    worst_hour_ratio = worst_hour_tokens_per_participant_per_day / HEAVY_USER_TOKENS_PER_DAY

    # --- science crossover ---------------------------------------------
    fah_flops = FOLDING_AT_HOME_PEAK_EXAFLOPS * 1e18
    enrolled_to_match_fah = fah_flops / (mean_avail * w_flops * 1e12)

    # --- the OPS crossover the original draft claimed -------------------
    enrolled_to_match_dc_peak_ops = (LARGE_DC_PEAK_EXAOPS_INT8 * 1e18) / (
        mean_avail * w_tops * 1e12
    )

    # --- data centre serving throughput, for the tok/s comparison -------
    dc_tokens_per_sec = DC_TOKENS_PER_SEC_PER_GPU * DC_GPU_COUNT
    enrolled_to_match_dc_tokens = dc_tokens_per_sec / (mean_avail * w_tok)

    # --- Folding@home-equivalents ---------------------------------------
    full_fleet = CAPABLE_FLEET_TODAY
    full_fleet_exaflops = science_exaflops(full_fleet)
    fah_years_per_year = full_fleet_exaflops / FOLDING_AT_HOME_PEAK_EXAFLOPS
    days_to_deliver_one_fah_year = 365.0 / fah_years_per_year

    scales = [1e3, 1e4, 1e5, 1e6, 1e7, 3e7, 1e8, 3e8, CAPABLE_FLEET_TODAY]

    # =================================================================
    # DESKTOP TIER
    # =================================================================
    d_rows, d_tok, d_tops, d_flops = per_desktop_inference()
    _, d_avail = desktop_availability_profile()
    d_mean = float(d_avail.mean())
    d_min = float(d_avail.min())
    d_max = float(d_avail.max())

    def desktop_science_exaflops(enrolled: float) -> float:
        return enrolled * d_mean * d_flops * 1e12 / 1e18

    # Folding@home parity, per desktop class and for the mixed fleet. This is the
    # headline the desktop tier exists to produce: it is roughly an order of
    # magnitude fewer machines than the mobile equivalent.
    dgpu = d_rows[0]
    desktop_parity_mixed = fah_flops / (d_mean * d_flops * 1e12)
    desktop_parity_dgpu_only = fah_flops / (d_mean * dgpu["fp32_sustained_tflops"] * 1e12)

    desktop_full_exaflops = desktop_science_exaflops(DESKTOP_FLEET)

    desktop = {
        "fleet": DESKTOP_FLEET,
        "classes": d_rows,
        "weighted_tokens_per_sec": d_tok,
        "weighted_sustained_tops_int8": d_tops,
        "weighted_sustained_tflops_fp32": d_flops,
        "thermal_derate": DESKTOP_THERMAL_DERATE,
        "availability": {
            "night_peak": DESKTOP_NIGHT_PEAK,
            "mean_over_24h": d_mean,
            "global_min": d_min,
            "global_max": d_max,
            "components": {
                "p_left_on_overnight": P_DESKTOP_LEFT_ON,
                "p_network": P_DESKTOP_NETWORK,
                "p_idle": P_DESKTOP_IDLE,
                "daytime": DESKTOP_DAYTIME_AVAILABILITY,
            },
        },
        "folding_parity_mixed_fleet": desktop_parity_mixed,
        "folding_parity_dgpu_only": desktop_parity_dgpu_only,
        "full_fleet_exaflops": desktop_full_exaflops,
        "full_fleet_folding_multiple": desktop_full_exaflops / FOLDING_AT_HOME_PEAK_EXAFLOPS,
        # How much more scientific throughput one desktop delivers than one phone.
        "science_advantage_vs_mobile": d_flops / w_flops,
        "dgpu_science_advantage_vs_mobile": dgpu["fp32_sustained_tflops"] / w_flops,
        # And how many fewer machines that translates into.
        "parity_machines_saved_vs_mobile": enrolled_to_match_fah / desktop_parity_mixed,
        "by_scale": [
            {
                "enrolled": s,
                "exaflops_fp32": desktop_science_exaflops(s),
                "folding_at_home_multiple": desktop_science_exaflops(s)
                / FOLDING_AT_HOME_PEAK_EXAFLOPS,
                "tokens_per_sec": s * d_mean * d_tok,
            }
            for s in [1e5, 5e5, 1e6, 2.5e6, 1e7, 1e8, DESKTOP_FLEET]
        ],
    }

    results = {
        "fleet": {
            "smartphone_install_base": SMARTPHONE_INSTALL_BASE,
            "share_ram_8gb_plus": SHARE_RAM_8GB_PLUS,
            "capable_fleet_today": CAPABLE_FLEET_TODAY,
            "capable_fleet_2030_projection": CAPABLE_FLEET_2030,
        },
        "per_device": {
            "classes": rows,
            "weighted_tokens_per_sec": w_tok,
            "weighted_sustained_tops_int8": w_tops,
            "weighted_sustained_tflops_fp32": w_flops,
            "thermal_derate": THERMAL_DERATE,
            "flagship_npu_peak_tops": FLAGSHIP_NPU_PEAK_TOPS,
            # Flagship peak vs that same flagship's own sustained decode figure.
            # Comparing the flagship's peak against the fleet-weighted average
            # would conflate two separate effects and overstate the gap.
            "npu_peak_to_real_ratio": FLAGSHIP_NPU_PEAK_TOPS / rows[0]["sustained_tops"],
            "flagship_sustained_tops": rows[0]["sustained_tops"],
        },
        "availability": {
            "night_peak": NIGHT_PEAK_AVAILABILITY,
            "mean_over_24h": mean_avail,
            "global_min": min_avail,
            "global_max": max_avail,
            "components": {
                "p_charges_overnight": P_CHARGES_OVERNIGHT,
                "p_on_wifi": P_ON_WIFI,
                "p_idle_undisturbed": P_IDLE_UNDISTURBED,
                "daytime": DAYTIME_AVAILABILITY,
            },
        },
        "self_sufficiency": {
            "tokens_per_participant_per_day": tokens_per_participant_per_day,
            "heavy_user_tokens_per_day": HEAVY_USER_TOKENS_PER_DAY,
            "ratio": self_sufficiency_ratio,
            "worst_hour_tokens_per_participant_per_day": worst_hour_tokens_per_participant_per_day,
            "worst_hour_ratio": worst_hour_ratio,
        },
        "crossovers": {
            "enrolled_to_match_folding_at_home_peak": enrolled_to_match_fah,
            "enrolled_to_match_dc_peak_int8_ops": enrolled_to_match_dc_peak_ops,
            "enrolled_to_match_dc_serving_tokens": enrolled_to_match_dc_tokens,
            "dc_tokens_per_sec_assumed": dc_tokens_per_sec,
        },
        "full_fleet": {
            "enrolled": full_fleet,
            "exaflops_fp32_sustained": full_fleet_exaflops,
            "folding_at_home_years_per_year": fah_years_per_year,
            "days_to_deliver_one_folding_at_home_year": days_to_deliver_one_fah_year,
            "tokens_per_sec": inference_tokens_per_sec(full_fleet),
            "sustained_exaops_int8": sustained_exaops_int8(full_fleet),
        },
        "by_scale": [
            {
                "enrolled": s,
                "available_mean": s * mean_avail,
                "tokens_per_sec": inference_tokens_per_sec(s),
                "exaflops_fp32": science_exaflops(s),
                "exaops_int8": sustained_exaops_int8(s),
                "folding_at_home_multiple": science_exaflops(s) / FOLDING_AT_HOME_PEAK_EXAFLOPS,
            }
            for s in scales
        ],
    }

    results["desktop"] = desktop
    # Combined fleets, which is what the network actually looks like.
    results["combined"] = {
        "science_exaflops_full_both": full_fleet_exaflops + desktop_full_exaflops,
        "science_folding_multiple_both": (full_fleet_exaflops + desktop_full_exaflops)
        / FOLDING_AT_HOME_PEAK_EXAFLOPS,
        "desktop_share_of_science": desktop_full_exaflops
        / (full_fleet_exaflops + desktop_full_exaflops),
    }
    results["sensitivity"] = sensitivity(mean_avail)
    return results


# ===========================================================================
# 6. SENSITIVITY
# ===========================================================================
# The point of publishing this is that a reader who disagrees with an assumption
# can see immediately how much it matters. We vary each input across a plausible
# range and report the effect on the Folding@home-parity enrolment, which is the
# project's load-bearing scientific claim.


def sensitivity(mean_avail: float) -> list[dict]:
    global THERMAL_DERATE, P_CHARGES_OVERNIGHT, NIGHT_PEAK_AVAILABILITY

    baseline_rows, _, _, base_flops = per_device_inference()
    fah_flops = FOLDING_AT_HOME_PEAK_EXAFLOPS * 1e18
    baseline = fah_flops / (mean_avail * base_flops * 1e12)

    out = []

    def record(label: str, low_val: float, high_val: float, low_n: float, high_n: float):
        out.append(
            {
                "parameter": label,
                "low_input": low_val,
                "high_input": high_val,
                "enrolled_low": low_n,
                "enrolled_high": high_n,
                "baseline": baseline,
            }
        )

    # FP32 sustained fraction — the least certain input in the model.
    originals = [d.fp32_sustained_fraction for d in DEVICE_CLASSES]
    ns = []
    for mult in (0.5, 2.0):
        for d, o in zip(DEVICE_CLASSES, originals):
            d.fp32_sustained_fraction = min(o * mult, 0.85)
        _, _, _, f = per_device_inference()
        ns.append(fah_flops / (mean_avail * f * 1e12))
    for d, o in zip(DEVICE_CLASSES, originals):
        d.fp32_sustained_fraction = o
    record("Sustained FP32 fraction (0.5x / 2x)", 0.5, 2.0, ns[0], ns[1])

    # Overnight charging behaviour.
    orig_charge = P_CHARGES_OVERNIGHT
    ns = []
    for v in (0.50, 0.90):
        P_CHARGES_OVERNIGHT = v
        NIGHT_PEAK_AVAILABILITY = v * P_ON_WIFI * P_IDLE_UNDISTURBED
        _, a = availability_profile()
        ns.append(fah_flops / (float(a.mean()) * base_flops * 1e12))
    P_CHARGES_OVERNIGHT = orig_charge
    NIGHT_PEAK_AVAILABILITY = P_CHARGES_OVERNIGHT * P_ON_WIFI * P_IDLE_UNDISTURBED
    record("Share who charge overnight (0.50 / 0.90)", 0.50, 0.90, ns[0], ns[1])

    # Folding@home reference figure itself.
    record(
        "Folding@home peak, exaFLOPS (1.2 / 4.8)",
        1.2,
        4.8,
        (1.2e18) / (mean_avail * base_flops * 1e12),
        (4.8e18) / (mean_avail * base_flops * 1e12),
    )

    # Device mix skewed toward or away from flagships.
    orig_shares = [d.share for d in DEVICE_CLASSES]
    ns = []
    for shares in ([0.10, 0.35, 0.55], [0.55, 0.35, 0.10]):
        for d, s in zip(DEVICE_CLASSES, shares):
            d.share = s
        _, _, _, f = per_device_inference()
        ns.append(fah_flops / (mean_avail * f * 1e12))
    for d, s in zip(DEVICE_CLASSES, orig_shares):
        d.share = s
    record("Device mix (low-end skew / flagship skew)", 0.0, 1.0, ns[0], ns[1])

    return out


# ===========================================================================
# 7. FIGURES
# ===========================================================================

def _si(v, _pos=None):
    v = float(v)
    for div, suf in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(v) >= div:
            s = v / div
            return (f"{s:.0f}{suf}" if s >= 10 or s == int(s) else f"{s:.1f}{suf}")
    return f"{v:.0f}"


def fig_bandwidth_wall(R):
    """The honesty figure: why peak NPU TOPS is the wrong number."""
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    p = R["per_device"]
    flagship = p["classes"][0]
    burst_tops = flagship["tokens_per_sec_burst"] * 2 * 3e9 / 1e12
    labels = [
        "Marketing figure\nflagship NPU peak\n(INT8)",
        "Bandwidth ceiling\nbatch-1 decode,\nburst",
        "Same flagship,\nsustained over 8h",
        "Fleet-weighted\nacross all\ndevice classes",
    ]
    vals = [
        FLAGSHIP_NPU_PEAK_TOPS,
        burst_tops,
        p["flagship_sustained_tops"],
        p["weighted_sustained_tops_int8"],
    ]
    colors = [SLATE, TEAL, BLUE, AMBER]
    bars = ax.bar(labels, vals, color=colors, width=0.60, zorder=3)
    ax.set_yscale("log")
    ax.set_ylabel("INT8 throughput per device (TOPS)")
    ax.set_title("The bandwidth wall: advertised AI horsepower is not available for LLM decode")
    for b, v in zip(bars, vals):
        ax.annotate(
            f"{v:,.3f}" if v < 1 else (f"{v:,.2f}" if v < 10 else f"{v:,.0f}"),
            (b.get_x() + b.get_width() / 2, v),
            textcoords="offset points", xytext=(0, 7), ha="center", fontweight="bold",
        )
    ax.annotate(
        f"{p['npu_peak_to_real_ratio']:,.0f}x gap between the number\n"
        "on the box and the number that\nactually serves a user",
        xy=(0.53, 0.55), xycoords="axes fraction", ha="center", fontsize=11.5, color=DEEP,
        bbox=dict(boxstyle="round,pad=0.55", fc="white", ec=AMBER, lw=1.4),
    )
    ax.annotate(
        "", xy=(0.06, 0.93), xytext=(0.06, 0.20), xycoords="axes fraction",
        arrowprops=dict(arrowstyle="<|-|>", color=DEEP, lw=1.6),
    )
    ax.set_ylim(vals[-1] * 0.32, FLAGSHIP_NPU_PEAK_TOPS * 5)
    ax.grid(axis="x", visible=False)
    fig.savefig(FIGDIR / "fig1_bandwidth_wall.png", dpi=155)
    plt.close(fig)


def fig_self_sufficiency(R):
    """Supply and member demand grow together, so the surplus is structural."""
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    mean_avail = R["availability"]["mean_over_24h"]
    min_avail = R["availability"]["global_min"]
    w_tok = R["per_device"]["weighted_tokens_per_sec"]

    n = np.logspace(3, np.log10(CAPABLE_FLEET_TODAY), 300)
    capacity_mean = n * mean_avail * w_tok
    capacity_trough = n * min_avail * w_tok
    # Conservative: assume every single member is a heavy daily user.
    demand = n * HEAVY_USER_TOKENS_PER_DAY / SECONDS_PER_DAY

    ax.fill_between(n, demand, capacity_trough, color=TEAL, alpha=0.18, zorder=2,
                    label="Guaranteed surplus for open science")
    ax.plot(n, capacity_mean, color=BLUE, lw=3.2, zorder=4,
            label="Network capacity (24h mean)")
    ax.plot(n, capacity_trough, color=DEEP, lw=2.0, ls=(0, (5, 3)), zorder=4,
            label="Network capacity at the daily trough")
    ax.plot(n, demand, color=AMBER, lw=2.6, zorder=4,
            label=f"Member demand if everyone is a heavy user ({_si(HEAVY_USER_TOKENS_PER_DAY)} tok/day)")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Participating devices")
    ax.set_ylabel("Output tokens per second")
    ax.set_title("Supply and demand grow together, so the surplus is structural — not a scale target")
    ax.xaxis.set_major_formatter(FuncFormatter(_si))
    ax.yaxis.set_major_formatter(FuncFormatter(_si))

    s = R["self_sufficiency"]
    ax.annotate(
        f"The three lines are parallel. Capacity exceeds even worst-case\n"
        f"member demand by {s['ratio']:.1f}x on average and {s['worst_hour_ratio']:.1f}x at the daily\n"
        f"trough — at one thousand devices and at one billion alike.\n"
        f"There is no threshold to reach before the network is useful.",
        xy=(0.035, 0.70), xycoords="axes fraction", fontsize=10.5, color=DEEP,
        bbox=dict(boxstyle="round,pad=0.55", fc="white", ec=TEAL, lw=1.4),
    )
    ax.legend(loc="lower right", frameon=False, fontsize=9.5)
    fig.savefig(FIGDIR / "fig2_self_sufficiency.png", dpi=155)
    plt.close(fig)


def fig_follow_the_moon(R):
    fig, ax = plt.subplots(figsize=(11, 5.6))
    hours, total = availability_profile()
    colors = [BLUE, AMBER, TEAL, MAGENTA]
    stack = [[region_availability(r, h) * 100 for h in hours] for r in REGIONS]
    ax.stackplot(hours, *stack, labels=[r["name"] for r in REGIONS],
                 colors=colors, alpha=0.80, edgecolor="none")
    ax.plot(hours, total * 100, color=INK, lw=2.6, zorder=5, label="Total available")
    floor = R["availability"]["global_min"] * 100
    ax.axhline(floor, color=DEEP, lw=1.5, ls=":", zorder=6)
    ax.annotate(
        f"Floor: never below {floor:.0f}% of the enrolled fleet",
        xy=(0.4, floor + 1.2), fontsize=10.5, color=DEEP, fontweight="bold",
    )
    ax.set_xlim(0, 24)
    ax.set_ylim(0, max(total) * 100 * 1.42)
    ax.set_xticks(range(0, 25, 3))
    ax.set_xlabel("Hour (UTC)")
    ax.set_ylabel("% of enrolled fleet contributing")
    ax.set_title("Follow the moon: night rotates, so supply never falls to zero")
    ax.legend(loc="upper center", ncol=5, frameon=False, fontsize=9.5)
    fig.savefig(FIGDIR / "fig3_follow_the_moon.png", dpi=155)
    plt.close(fig)


def fig_science_capacity(R):
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    n = np.logspace(4, np.log10(CAPABLE_FLEET_TODAY), 200)
    mean_avail = R["availability"]["mean_over_24h"]
    wf = R["per_device"]["weighted_sustained_tflops_fp32"]
    ef = n * mean_avail * wf * 1e12 / 1e18
    ax.plot(n, ef, color=TEAL, lw=3.2, zorder=4, label="MERIDIAN sustained FP32")
    ax.axhline(FOLDING_AT_HOME_PEAK_EXAFLOPS, color=AMBER, lw=2.4, ls="--", zorder=3,
               label=f"Folding@home at its peak (~{FOLDING_AT_HOME_PEAK_EXAFLOPS} exaFLOPS)")
    x0 = R["crossovers"]["enrolled_to_match_folding_at_home_peak"]
    ax.plot([x0], [FOLDING_AT_HOME_PEAK_EXAFLOPS], "o", ms=11, color=DEEP, zorder=6)
    ax.annotate(
        f"Parity with the largest volunteer\ncomputing effort in history:\n{_si(x0)} enrolled devices",
        xy=(x0, FOLDING_AT_HOME_PEAK_EXAFLOPS), xytext=(0.20, 0.56),
        textcoords="axes fraction", ha="center", fontsize=11, color=DEEP,
        arrowprops=dict(arrowstyle="-|>", color=DEEP, lw=1.3,
                        connectionstyle="arc3,rad=-0.15"),
        bbox=dict(boxstyle="round,pad=0.5", fc="white", ec=DEEP, lw=1.2),
    )
    full = R["full_fleet"]
    ax.plot([full["enrolled"]], [full["exaflops_fp32_sustained"]], "o", ms=11, color=MAGENTA, zorder=6)
    ax.annotate(
        f"Every capable phone today ({_si(full['enrolled'])}):\n"
        f"{full['exaflops_fp32_sustained']:,.0f} exaFLOPS sustained\n"
        f"~{full['folding_at_home_years_per_year']:,.0f}x Folding@home, continuously",
        xy=(full["enrolled"], full["exaflops_fp32_sustained"]), xytext=(0.66, 0.28),
        textcoords="axes fraction", ha="center", fontsize=11, color=DEEP,
        arrowprops=dict(arrowstyle="-|>", color=MAGENTA, lw=1.3,
                        connectionstyle="arc3,rad=0.2"),
        bbox=dict(boxstyle="round,pad=0.5", fc="white", ec=MAGENTA, lw=1.2),
    )
    ax.set_ylim(3e-4, 4e2)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Participating devices")
    ax.set_ylabel("Sustained FP32 throughput (exaFLOPS)")
    ax.set_title("Scientific batch capacity, in the units science actually uses")
    ax.xaxis.set_major_formatter(FuncFormatter(_si))
    ax.legend(loc="upper left", frameon=False)
    fig.savefig(FIGDIR / "fig4_science_capacity.png", dpi=155)
    plt.close(fig)


def fig_roadmap(R):
    fig, ax = plt.subplots(figsize=(11.5, 5.4))
    phases = [
        ("M0  One node lives", 0, 1, "1 device", BLUE),
        ("M1  The network answers", 1, 3, "~100 devices", TEAL),
        ("M2  Follow the moon", 3, 9, "~10K devices", AMBER),
        ("M3  Open protocol", 9, 18, "~100K devices", MAGENTA),
        ("M4  Public utility", 18, 36, "1M+ devices", DEEP),
    ]
    for i, (label, start, end, scale, color) in enumerate(phases):
        y = len(phases) - i - 1
        ax.barh(y, end - start, left=start, height=0.52, color=color, zorder=3)
        ax.text(start + 0.25, y + 0.42, label, fontsize=12, fontweight="bold", va="bottom")
        ax.text(end + 0.4, y, scale, fontsize=10.5, va="center", color=DEEP)
    ax.set_yticks([])
    ax.set_xlim(0, 42)
    ax.set_xticks([0, 1, 3, 9, 18, 36])
    ax.set_xlabel("Months from start")
    ax.set_title("Every milestone ships something that runs")
    ax.grid(axis="y", visible=False)
    ax.spines["left"].set_visible(False)
    fig.savefig(FIGDIR / "fig5_roadmap.png", dpi=155)
    plt.close(fig)


def fig_tiers(R):
    """Why the desktop tier carries the science, and the mobile tier the mission."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.6, 5.6),
                                   gridspec_kw={"width_ratios": [1, 1.1]})
    d = R["desktop"]

    # ---- left: sustained FP32 per machine, log scale --------------------
    names = [c["name"] for c in d["classes"]] + ["Phone\n(fleet average)"]
    vals = [c["fp32_sustained_tflops"] for c in d["classes"]] + [
        R["per_device"]["weighted_sustained_tflops_fp32"]
    ]
    colors = [BLUE, TEAL, SLATE, AMBER]
    bars = ax1.bar(names, vals, color=colors, width=0.62, zorder=3)
    ax1.set_yscale("log")
    ax1.set_ylabel("Sustained FP32 per machine (TFLOPS)")
    ax1.set_title("Scientific throughput is a desktop story")
    for b, v in zip(bars, vals):
        ax1.annotate(f"{v:,.2f}" if v < 1 else f"{v:,.1f}",
                     (b.get_x() + b.get_width() / 2, v),
                     textcoords="offset points", xytext=(0, 6),
                     ha="center", fontweight="bold")
    ax1.annotate(
        f"One discrete GPU does the scientific\nwork of about "
        f"{d['dgpu_science_advantage_vs_mobile']:,.0f} phones.\n"
        "A CPU-only desktop does less than one.",
        xy=(0.97, 0.34), xycoords="axes fraction", ha="right",
        fontsize=10, color=DEEP,
        bbox=dict(boxstyle="round,pad=0.5", fc="white", ec=BLUE, lw=1.3),
    )
    ax1.grid(axis="x", visible=False)
    ax1.tick_params(axis="x", labelsize=9.5)

    # ---- right: machines needed for Folding@home parity ----------------
    labels = ["Phones", "Desktops\n(mixed fleet)", "Desktops\n(discrete GPU only)"]
    counts = [
        R["crossovers"]["enrolled_to_match_folding_at_home_peak"],
        d["folding_parity_mixed_fleet"],
        d["folding_parity_dgpu_only"],
    ]
    cols = [AMBER, TEAL, BLUE]
    ypos = np.arange(len(labels))
    ax2.barh(ypos, counts, color=cols, height=0.55, zorder=3)
    for y, v in zip(ypos, counts):
        ax2.annotate(f"  {_si(v)} machines", (v, y), textcoords="offset points",
                     xytext=(6, 0), va="center", fontweight="bold", fontsize=10.5)
    ax2.set_yticks(ypos)
    ax2.set_yticklabels(labels, fontsize=10.5)
    ax2.set_xscale("log")
    ax2.set_xlim(counts[2] / 4, counts[0] * 6)
    ax2.set_xlabel("Machines needed to match Folding@home's peak, sustained")
    ax2.set_title("Which is why desktop-first is the faster proof")
    ax2.xaxis.set_major_formatter(FuncFormatter(_si))
    ax2.grid(axis="y", visible=False)
    ax2.invert_yaxis()

    ax2.annotate(
        f"Desktops reach parity with about\n"
        f"{d['parity_machines_saved_vs_mobile']:,.0f}x fewer machines — despite\n"
        f"being switched off more often "
        f"({d['availability']['mean_over_24h']:.0%} vs {R['availability']['mean_over_24h']:.0%}\n"
        f"mean availability).",
        xy=(0.40, 0.20), xycoords="axes fraction", fontsize=10, color=DEEP,
        bbox=dict(boxstyle="round,pad=0.5", fc="white", ec=TEAL, lw=1.3),
    )

    fig.suptitle("Two tiers, two jobs", fontsize=15, fontweight="bold", color=INK)
    fig.savefig(FIGDIR / "fig7_tiers.png", dpi=155)
    plt.close(fig)


def fig_sensitivity(R):
    fig, ax = plt.subplots(figsize=(11, 4.8))
    rows = R["sensitivity"]
    base = rows[0]["baseline"]
    # Classic tornado ordering: widest uncertainty band at the top.
    rows = sorted(
        rows,
        key=lambda r: max(r["enrolled_low"], r["enrolled_high"])
        / max(min(r["enrolled_low"], r["enrolled_high"]), 1e-9),
    )
    ys = np.arange(len(rows))
    for y, r in zip(ys, rows):
        lo, hi = sorted([r["enrolled_low"], r["enrolled_high"]])
        ax.plot([lo, hi], [y, y], lw=13, color=TEAL, alpha=0.5, solid_capstyle="butt", zorder=3)
        ax.plot([lo], [y], "|", ms=20, color=DEEP, mew=2.4, zorder=4)
        ax.plot([hi], [y], "|", ms=20, color=DEEP, mew=2.4, zorder=4)
        ax.annotate(_si(lo), (lo, y), xytext=(-8, 0), textcoords="offset points",
                    ha="right", va="center", fontsize=9.5)
        ax.annotate(_si(hi), (hi, y), xytext=(8, 0), textcoords="offset points",
                    ha="left", va="center", fontsize=9.5)
    ax.axvline(base, color=AMBER, lw=2.4, zorder=5)
    ax.annotate(
        f"Baseline: {_si(base)} devices",
        xy=(base, 1.02), xycoords=("data", "axes fraction"),
        ha="center", va="bottom", color=DEEP, fontsize=10.5, fontweight="bold",
    )
    ax.set_yticks(ys)
    ax.set_yticklabels([r["parameter"] for r in rows], fontsize=10.5)
    ax.set_xscale("log")
    ax.set_xlim(base / 4.5, base * 4.5)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.set_xlabel("Enrolled devices needed to match Folding@home's peak, sustained")
    ax.set_title("How much each assumption matters", pad=26)
    ax.xaxis.set_major_formatter(FuncFormatter(_si))
    ax.grid(axis="y", visible=False)
    fig.savefig(FIGDIR / "fig6_sensitivity.png", dpi=155)
    plt.close(fig)


# ===========================================================================
# 8. REPORT
# ===========================================================================

def write_numbers_md(R: dict, path: Path):
    a = R["availability"]
    p = R["per_device"]
    c = R["crossovers"]
    f = R["full_fleet"]
    s = R["self_sufficiency"]

    L: list[str] = []
    L.append("# Derived numbers\n")
    L.append(
        "Generated by `analysis/compute_model.py`. Do not edit by hand — change the "
        "model and re-run. Every figure quoted in the whitepaper, the README, and on "
        "the website appears in this table.\n"
    )
    L.append("## Fleet\n")
    L.append("| Quantity | Value |")
    L.append("|---|---|")
    L.append(f"| Active smartphones worldwide | {_si(SMARTPHONE_INSTALL_BASE)} |")
    L.append(f"| Share with >=8GB RAM | {SHARE_RAM_8GB_PLUS:.0%} |")
    L.append(f"| **Capable fleet today** | **{_si(CAPABLE_FLEET_TODAY)} devices** |")
    L.append(f"| Capable fleet, 2030 projection | {_si(CAPABLE_FLEET_2030)} devices |")

    L.append("\n## Per-device throughput\n")
    L.append("| Device class | Share | Usable BW | Burst tok/s | Sustained tok/s | Sustained INT8 | Sustained FP32 |")
    L.append("|---|---|---|---|---|---|---|")
    for r in p["classes"]:
        L.append(
            f"| {r['name']} | {r['share']:.0%} | {r['usable_bandwidth_gbs']:.1f} GB/s | "
            f"{r['tokens_per_sec_burst']:.1f} | {r['tokens_per_sec_sustained']:.1f} | "
            f"{r['sustained_tops']*1000:.0f} GOPS | {r['fp32_sustained_tflops']*1000:.0f} GFLOPS |"
        )
    L.append(
        f"| **Fleet-weighted** | 100% | — | — | **{p['weighted_tokens_per_sec']:.1f}** | "
        f"**{p['weighted_sustained_tops_int8']*1000:.0f} GOPS** | "
        f"**{p['weighted_sustained_tflops_fp32']*1000:.0f} GFLOPS** |"
    )
    L.append(
        f"\nA flagship NPU is marketed at {FLAGSHIP_NPU_PEAK_TOPS:.0f} INT8 TOPS. That same "
        f"flagship, decoding a 3B model at batch size 1 for eight hours, sustains "
        f"{p['flagship_sustained_tops']*1000:.0f} GOPS — a "
        f"**{p['npu_peak_to_real_ratio']:,.0f}x gap**. That gap is the bandwidth wall. Any "
        "proposal that quotes peak TOPS for inference throughput has already made a "
        "two-order-of-magnitude error, and every downstream conclusion inherits it.\n"
    )

    L.append("## Availability\n")
    L.append("| Quantity | Value |")
    L.append("|---|---|")
    L.append(f"| Charges overnight | {a['components']['p_charges_overnight']:.0%} |")
    L.append(f"| On Wi-Fi | {a['components']['p_on_wifi']:.0%} |")
    L.append(f"| Undisturbed while idle | {a['components']['p_idle_undisturbed']:.0%} |")
    L.append(f"| **Overnight peak (joint)** | **{a['night_peak']:.1%}** |")
    L.append(f"| Daytime baseline | {a['components']['daytime']:.0%} |")
    L.append(f"| **Global mean over 24h** | **{a['mean_over_24h']:.1%}** |")
    L.append(f"| Global minimum (the floor) | {a['global_min']:.1%} |")
    L.append(f"| Global maximum | {a['global_max']:.1%} |")

    L.append("\n## Self-sufficiency\n")
    L.append(
        f"Each participant's share of network capacity is "
        f"**{_si(s['tokens_per_participant_per_day'])} output tokens per day** on average, "
        f"against **{_si(s['heavy_user_tokens_per_day'])}** for heavy personal use — "
        f"**{s['ratio']:.1f}x headroom**. At the global availability trough, when supply is "
        f"lowest, the figure is {_si(s['worst_hour_tokens_per_participant_per_day'])} tokens/day "
        f"({s['worst_hour_ratio']:.1f}x).\n"
    )
    L.append(
        "This ratio does not depend on scale: capacity and membership grow together, so it "
        "is the same at one thousand devices as at one billion. The network never has to "
        "reach a threshold before it is useful to the people in it, and the surplus above "
        "personal use is what funds open science.\n"
    )

    L.append("## Crossovers\n")
    L.append("| Comparison | Enrolled devices needed |")
    L.append("|---|---|")
    L.append(f"| Match Folding@home's peak, sustained | **{_si(c['enrolled_to_match_folding_at_home_peak'])}** |")
    L.append(f"| Match a 100k-GPU cluster's *serving* throughput | {_si(c['enrolled_to_match_dc_serving_tokens'])} |")
    L.append(f"| Match a 100k-GPU cluster's *peak INT8 OPS* | {_si(c['enrolled_to_match_dc_peak_int8_ops'])} — **not reachable** |")
    L.append(
        "\nThe last row is the important one, and it is a retraction. An earlier draft of "
        "this project claimed that ~30M devices (1.4% adoption) would pass the largest AI "
        "data centre on Earth. That claim was built on peak NPU TOPS and does not survive "
        f"bandwidth-bound analysis: the real figure is {_si(c['enrolled_to_match_dc_peak_int8_ops'])} "
        "devices, which exceeds every smartphone in existence. **The network does not and "
        "will not out-compute a hyperscale data centre in raw operations.** It wins on cost, "
        "reach, privacy, and resilience instead.\n"
    )

    L.append("## At full capable-fleet enrolment\n")
    L.append("| Quantity | Value |")
    L.append("|---|---|")
    L.append(f"| Enrolled | {_si(f['enrolled'])} devices |")
    L.append(f"| Sustained FP32 | {f['exaflops_fp32_sustained']:,.0f} exaFLOPS |")
    L.append(f"| Folding@home-equivalents per year | {f['folding_at_home_years_per_year']:,.0f} |")
    L.append(f"| Days to deliver one Folding@home-year | {f['days_to_deliver_one_folding_at_home_year']:.1f} |")
    L.append(f"| Inference throughput | {_si(f['tokens_per_sec'])} output tokens/sec |")

    L.append("\n## Capacity by scale\n")
    L.append("| Enrolled | Available (mean) | Inference (tok/s) | Science (exaFLOPS) | vs Folding@home |")
    L.append("|---|---|---|---|---|")
    for row in R["by_scale"]:
        L.append(
            f"| {_si(row['enrolled'])} | {_si(row['available_mean'])} | "
            f"{_si(row['tokens_per_sec'])} | {row['exaflops_fp32']:,.2f} | "
            f"{row['folding_at_home_multiple']:.3f}x |"
        )

    d = R["desktop"]
    L.append("\n## The desktop tier\n")
    L.append(
        "Desktops are better nodes than phones in almost every dimension: more RAM, real "
        "GPUs, active cooling, mains power, no app-store review, and no background-execution "
        "limits. They lose on exactly one axis, and it matters — **people switch desktops off, "
        "and plug phones in.**\n"
    )
    L.append("| Class | Machines | Sustained tok/s | Sustained FP32 |")
    L.append("|---|---|---|---|")
    for dc in d["classes"]:
        L.append(
            f"| {dc['name']} | {_si(dc['count'])} | {dc['tokens_per_sec_sustained']:.0f} | "
            f"**{dc['fp32_sustained_tflops']*1000:,.0f} GFLOPS** |"
        )
    L.append(
        f"| **Fleet-weighted** | {_si(d['fleet'])} | {d['weighted_tokens_per_sec']:.0f} | "
        f"**{d['weighted_sustained_tflops_fp32']*1000:,.0f} GFLOPS** |"
    )

    da = d["availability"]
    L.append("\n### Desktop availability is lower than mobile\n")
    L.append("| Quantity | Desktop | Mobile |")
    L.append("|---|---|---|")
    L.append(
        f"| Left on / plugged in overnight | {da['components']['p_left_on_overnight']:.0%} | "
        f"{a['components']['p_charges_overnight']:.0%} |"
    )
    L.append(f"| Overnight peak (joint) | {da['night_peak']:.1%} | {a['night_peak']:.1%} |")
    L.append(f"| **Mean over 24h** | **{da['mean_over_24h']:.1%}** | **{a['mean_over_24h']:.1%}** |")
    L.append(f"| Daily floor | {da['global_min']:.1%} | {a['global_min']:.1%} |")

    L.append("\n### And yet it wins the science case decisively\n")
    L.append("| Comparison | Value |")
    L.append("|---|---|")
    L.append(
        f"| One desktop vs one phone, scientific FP32 | "
        f"**{d['science_advantage_vs_mobile']:,.0f}x** |"
    )
    L.append(
        f"| One discrete GPU vs one phone | "
        f"**{d['dgpu_science_advantage_vs_mobile']:,.0f}x** |"
    )
    L.append(
        f"| Folding@home parity, phones | "
        f"{_si(c['enrolled_to_match_folding_at_home_peak'])} devices |"
    )
    L.append(
        f"| Folding@home parity, mixed desktops | "
        f"**{_si(d['folding_parity_mixed_fleet'])} machines** |"
    )
    L.append(
        f"| Folding@home parity, discrete GPUs only | "
        f"**{_si(d['folding_parity_dgpu_only'])} machines** |"
    )
    L.append(
        f"| Fewer machines needed than mobile | "
        f"{d['parity_machines_saved_vs_mobile']:,.0f}x |"
    )
    L.append(
        f"| Full desktop fleet ({_si(d['fleet'])}) | "
        f"{d['full_fleet_exaflops']:,.0f} exaFLOPS, "
        f"{d['full_fleet_folding_multiple']:,.0f}x Folding@home |"
    )
    comb = R["combined"]
    L.append(
        f"| Both fleets at full enrolment | "
        f"{comb['science_exaflops_full_both']:,.0f} exaFLOPS "
        f"({comb['desktop_share_of_science']:.0%} of it from desktops) |"
    )
    L.append(
        f"\n**This is the argument for building the desktop client first.** Reaching parity with "
        f"the largest volunteer computing effort in history needs roughly "
        f"{_si(d['folding_parity_dgpu_only'])} gaming PCs, against "
        f"{_si(c['enrolled_to_match_folding_at_home_peak'])} phones. The mobile fleet remains the "
        "mission and the scale story; the desktop fleet is the research instrument.\n"
    )
    L.append(
        "The same bandwidth wall applies to desktop inference, incidentally: a discrete GPU "
        f"decoding an 8B model at batch 1 sustains about {d['classes'][0]['tokens_per_sec_sustained']:.0f} "
        "tokens/sec, bound by VRAM bandwidth rather than by its tensor cores. Peak TOPS "
        "overstates desktop decode throughput exactly as badly as it does mobile.\n"
    )

    L.append("\n## Sensitivity\n")
    L.append("Effect on the Folding@home-parity enrolment figure.\n")
    L.append("| Assumption varied | Low | High |")
    L.append("|---|---|---|")
    for r in R["sensitivity"]:
        lo, hi = sorted([r["enrolled_low"], r["enrolled_high"]])
        L.append(f"| {r['parameter']} | {_si(lo)} | {_si(hi)} |")
    L.append(f"\nBaseline: {_si(base_of(R))} devices.\n")

    path.write_text("\n".join(L), encoding="utf-8")


def base_of(R):
    return R["sensitivity"][0]["baseline"]


def main():
    R = compute_all()

    (ROOT / "analysis" / "numbers.json").write_text(
        json.dumps(R, indent=2), encoding="utf-8"
    )
    write_numbers_md(R, ROOT / "analysis" / "NUMBERS.md")

    fig_bandwidth_wall(R)
    fig_self_sufficiency(R)
    fig_follow_the_moon(R)
    fig_science_capacity(R)
    fig_roadmap(R)
    fig_tiers(R)
    fig_sensitivity(R)

    a, p, c, f, s = (
        R["availability"], R["per_device"], R["crossovers"], R["full_fleet"], R["self_sufficiency"],
    )
    print("=" * 72)
    print("MERIDIAN MOONLIGHT — headline figures")
    print("=" * 72)
    print(f"  Capable fleet today ..................... {_si(CAPABLE_FLEET_TODAY)} devices")
    print(f"  Sustained tok/s per available device .... {p['weighted_tokens_per_sec']:.1f}")
    print(f"  Sustained INT8 per available device ..... {p['weighted_sustained_tops_int8']*1000:.0f} GOPS")
    print(f"  Sustained FP32 per available device ..... {p['weighted_sustained_tflops_fp32']*1000:.0f} GFLOPS")
    print(f"  NPU-peak-to-real gap .................... {p['npu_peak_to_real_ratio']:,.0f}x")
    print(f"  Overnight peak availability ............. {a['night_peak']:.1%}")
    print(f"  Mean availability / floor ............... {a['mean_over_24h']:.1%} / {a['global_min']:.1%}")
    print(f"  Tokens per participant per day .......... {_si(s['tokens_per_participant_per_day'])}"
          f"  ({s['ratio']:.1f}x heavy use; {s['worst_hour_ratio']:.1f}x at the trough)")
    print(f"  Folding@home parity at ................. {_si(c['enrolled_to_match_folding_at_home_peak'])} devices")
    print(f"  DC serving-throughput parity at ......... {_si(c['enrolled_to_match_dc_serving_tokens'])} devices")
    print(f"  DC peak-OPS parity at ................... {_si(c['enrolled_to_match_dc_peak_int8_ops'])} devices"
          "  <-- NOT REACHABLE")
    print(f"  Full fleet .............................. {f['exaflops_fp32_sustained']:,.0f} exaFLOPS,"
          f" {f['folding_at_home_years_per_year']:,.0f}x F@h")
    print(f"  Days for one Folding@home-year .......... {f['days_to_deliver_one_folding_at_home_year']:.1f}")
    d = R["desktop"]
    print("-" * 72)
    print("  DESKTOP TIER")
    print(f"    Machines in scope ..................... {_si(d['fleet'])}")
    print(f"    Mean availability (vs mobile) ......... {d['availability']['mean_over_24h']:.1%}"
          f"  (mobile {a['mean_over_24h']:.1%})")
    print(f"    Sustained FP32 per machine ............ {d['weighted_sustained_tflops_fp32']*1000:,.0f} GFLOPS")
    print(f"    Science advantage vs one phone ........ {d['science_advantage_vs_mobile']:,.0f}x"
          f"  (dGPU alone {d['dgpu_science_advantage_vs_mobile']:,.0f}x)")
    print(f"    Folding@home parity, mixed ............ {_si(d['folding_parity_mixed_fleet'])} machines")
    print(f"    Folding@home parity, dGPU only ........ {_si(d['folding_parity_dgpu_only'])} machines")
    print(f"    ... vs phones ......................... {_si(c['enrolled_to_match_folding_at_home_peak'])} devices"
          f"  ({d['parity_machines_saved_vs_mobile']:,.0f}x fewer)")
    print(f"    Full desktop fleet .................... {d['full_fleet_exaflops']:,.0f} exaFLOPS,"
          f" {d['full_fleet_folding_multiple']:,.0f}x F@h")
    print(f"    Both fleets combined .................. "
          f"{R['combined']['science_exaflops_full_both']:,.0f} exaFLOPS"
          f"  ({R['combined']['desktop_share_of_science']:.0%} from desktops)")
    print("=" * 72)
    n_figs = len(list(FIGDIR.glob("fig*.png")))
    print(f"Wrote analysis/numbers.json, analysis/NUMBERS.md, and {n_figs} figures to docs/figures/")


if __name__ == "__main__":
    main()
