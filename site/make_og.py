#!/usr/bin/env python3
"""
Generate site/og.png — the 1200x630 social preview card.

Reuses the terminator-band motif from the site's hero and the same availability
curve as analysis/compute_model.py, so the dots are in physically correct
positions rather than decorative.

Run:
    python site/make_og.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))

from compute_model import (  # noqa: E402
    DEVICE_DENSITY,
    _LON_GRID,
    NIGHT_PEAK_AVAILABILITY,
    DAYTIME_AVAILABILITY,
    device_availability,
    local_hour,
)

ABYSS = "#0A0E20"
NIGHT = "#1A2149"
MOON = "#EAEDFA"
DIM = "#8D97C2"
AMBER = "#FFB454"
DAWN = "#6FC3E8"

W, H = 1200, 630
DPI = 100
UTC_HOUR = 20.0  # Asian night — the fullest-looking moment of the cycle

rng = np.random.default_rng(11)


def main() -> None:
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI, facecolor=ABYSS)
    # compute_model sets constrained_layout globally; this figure is hand-placed.
    fig.set_layout_engine("none")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_facecolor(ABYSS)

    # Soft glow at the top, matching the site's radial gradient. Spans the full
    # canvas with a smooth vertical falloff — a partial-height overlay leaves a
    # visible horizontal seam where its extent ends.
    ny, nx = 300, 400
    gy, gx = np.mgrid[0:ny, 0:nx]
    glow = np.exp(-(((gx - nx / 2) / (nx * 0.50)) ** 2) - (((ny - 1 - gy) / (ny * 0.57)) ** 2))
    ax.imshow(
        glow, extent=(0, 1, 0, 1), aspect="auto", origin="lower",
        cmap=matplotlib.colors.LinearSegmentedColormap.from_list(
            "glow", [ABYSS, "#2A3A80"]
        ),
        alpha=0.60, zorder=0,
    )

    # --- the terminator band -------------------------------------------
    band_y0, band_y1 = 0.10, 0.40
    ax.add_patch(plt.Rectangle((0, band_y0), 1, band_y1 - band_y0,
                               facecolor=ABYSS, edgecolor="none", zorder=1))

    # Night shading sampled across longitude.
    n = 300
    for i in range(n):
        x = i / n
        lon = x * 360 - 180
        a = device_availability(local_hour(lon, UTC_HOUR)) / NIGHT_PEAK_AVAILABILITY
        ax.add_patch(
            plt.Rectangle(
                (x, band_y0), 1 / n + 0.002, band_y1 - band_y0,
                facecolor=NIGHT, alpha=0.18 + 0.62 * float(a),
                edgecolor="none", zorder=2,
            )
        )

    # Hairlines top and bottom of the band.
    for y in (band_y0, band_y1):
        ax.plot([0, 1], [y, y], color="#B2BEEB", alpha=0.16, lw=1, zorder=4)

    # Devices, placed by the real density function.
    cum = np.cumsum(DEVICE_DENSITY)
    for _ in range(220):
        k = int(np.searchsorted(cum, rng.random()))
        lon = float(_LON_GRID[min(k, len(_LON_GRID) - 1)]) + rng.uniform(-1, 1)
        av = device_availability(local_hour(lon, UTC_HOUR))
        lit = (av - DAYTIME_AVAILABILITY) / (NIGHT_PEAK_AVAILABILITY - DAYTIME_AVAILABILITY)
        x = (lon + 180) / 360
        y = band_y0 + 0.03 + rng.random() * (band_y1 - band_y0 - 0.06)
        r = 0.0022 + rng.random() * 0.0030
        if lit > 0.10:
            ax.add_patch(Circle((x, y), r * 3.0, facecolor=AMBER,
                                alpha=0.13 * float(lit), edgecolor="none", zorder=5))
            ax.add_patch(Circle((x, y), r, facecolor=AMBER,
                                alpha=0.55 + 0.40 * float(lit), edgecolor="none", zorder=6))
        else:
            ax.add_patch(Circle((x, y), r * 0.8, facecolor=DAWN,
                                alpha=0.22, edgecolor="none", zorder=5))

    # --- type ----------------------------------------------------------
    ax.text(0.055, 0.895, "DECENTRALIZED AI  ·  NO DATA CENTER  ·  NO TOKEN",
            color=AMBER, fontsize=11.5, fontweight="medium",
            family="DejaVu Sans", zorder=10,
            transform=ax.transAxes, va="top")

    ax.text(0.055, 0.815, "Your phone works for the world",
            color=MOON, fontsize=44, fontweight="bold",
            family="DejaVu Sans", zorder=10, transform=ax.transAxes, va="top")
    ax.text(0.055, 0.700, "while you sleep.",
            color=AMBER, fontsize=44, fontweight="bold",
            family="DejaVu Sans", zorder=10, transform=ax.transAxes, va="top")

    ax.text(0.055, 0.575,
            "A free AI network built from idle phones — charging, on Wi-Fi, asleep.\n"
            "Every number published and auditable. Including the one we retracted.",
            color=DIM, fontsize=15.5, family="DejaVu Sans",
            zorder=10, transform=ax.transAxes, va="top", linespacing=1.55)

    ax.text(0.055, 0.045, "MERIDIAN MOONLIGHT",
            color=MOON, fontsize=13, fontweight="bold", family="DejaVu Sans",
            zorder=10, transform=ax.transAxes, va="bottom")
    ax.text(0.945, 0.045, "meridianmoonlight.com",
            color=DIM, fontsize=12.5, family="DejaVu Sans",
            zorder=10, transform=ax.transAxes, va="bottom", ha="right")

    out = ROOT / "site" / "og.png"
    fig.savefig(out, dpi=DPI, facecolor=ABYSS)
    plt.close(fig)
    print(f"Wrote {out.relative_to(ROOT)}  ({out.stat().st_size/1024:.0f} KB, {W}x{H})")


if __name__ == "__main__":
    main()
