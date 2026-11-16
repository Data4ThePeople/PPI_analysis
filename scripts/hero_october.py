"""Hero for ppi-october-2026: printed circuit assemblies, drawn as a rocket launch.

The trail is the real 12-month change in printed circuit assemblies, loaded
boards, modules and consumer external modems (WPU117861), every month from the
first 12-month change (June 1983) to the release month, from the BLS flat
files (the same series as charts/<month>/07-circuit-history.png). Hero style:
no axis and no small text. The rocket, stars and flame are decoration; the only
numbers drawn are real values from the series. Writes
posts/ppi-october-2026/images/ppi-october-2026-hero-1680x1080.png and the same
image as -hero-source.png.
"""
from __future__ import annotations

import math
import shutil

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Circle, Polygon  # noqa: E402
from matplotlib.transforms import Affine2D, IdentityTransform  # noqa: E402

from common import ROOT, TARGET_LABEL
from hero_trucking import gradient
from takeaways import MONTH, month_label, raw_levels, shift_month, xpos

SLUG = "ppi-october-2026"
OUT = ROOT / "posts" / SLUG / "images"
W, H, DPI = 1680, 1080, 100
CODE = "117861"
YLO, YHI = -25, 215
TRAIL = "#4fd1c5"

plt.rcParams.update({"font.family": ["Arial", "DejaVu Sans"], "text.parse_math": False})


def series():
    lv = raw_levels(f"WPU{CODE}")
    months = [m for m in sorted(lv) if shift_month(m, 12) in lv and m <= MONTH]
    return months, [(lv[m] / lv[shift_month(m, 12)] - 1) * 100 for m in months]


def rocket(ax, x, y, height_px, angle_deg=90):
    """A rocket whose tail sits at data (x, y), pointing angle_deg (90 = straight up)."""
    px, py = ax.transData.transform((x, y))
    tr = (Affine2D().rotate_deg(angle_deg - 90).scale(height_px).translate(px, py + 0.04 * height_px)
          + IdentityTransform())
    body = [(-0.11, 0.10), (-0.11, 0.70), (-0.06, 0.86), (0.0, 0.94), (0.06, 0.86), (0.11, 0.70), (0.11, 0.10)]
    parts = [
        Polygon([(-0.07, 0.10), (0.0, -0.32), (0.07, 0.10)], fc="#f7b733", ec="none"),        # flame
        Polygon([(-0.04, 0.10), (0.0, -0.16), (0.04, 0.10)], fc="#fff3c4", ec="none"),        # flame core
        Polygon([(-0.11, 0.30), (-0.24, 0.04), (-0.24, 0.0), (-0.11, 0.10)], fc="#e4572e", ec="none"),  # fin
        Polygon([(0.11, 0.30), (0.24, 0.04), (0.24, 0.0), (0.11, 0.10)], fc="#e4572e", ec="none"),      # fin
        Polygon(body, fc="#f4f1ea", ec="#b9b4aa", lw=1.5),                                    # body
        Polygon([(-0.06, 0.86), (0.0, 0.94), (0.06, 0.86), (0.075, 0.82), (-0.075, 0.82)],
                fc="#e4572e", ec="none"),                                                     # nose
        Polygon([(-0.025, 0.10), (-0.025, 0.40), (0.025, 0.40), (0.025, 0.10)], fc="#e4572e", ec="none"),
    ]
    for p in parts:
        p.set_transform(tr); p.set_zorder(9); p.set_clip_on(False); ax.add_artist(p)
    for r, fc in ((0.055, "#2b2b2b"), (0.04, "#7fd3ff")):
        c = Circle((0.0, 0.60), r, fc=fc, ec="none", transform=tr, zorder=10, clip_on=False)
        ax.add_artist(c)


def main():
    months, ys = series()
    xs, ys = np.array([xpos(m) for m in months]), np.array(ys)
    before = ys[np.array([m < "2024-01" for m in months])]

    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI)
    bg = fig.add_axes([0, 0, 1, 1])
    bg.set_axis_off()
    gradient(bg, (0, 1, 0, 1), "#070b1a", "#2a1f4a", z=0)
    bg.set_xlim(0, 1); bg.set_ylim(0, 1)
    rng = np.random.default_rng(7)                    # fixed stars, decoration only
    sx, sy = rng.random(140), rng.random(140)
    bg.scatter(sx, sy, s=rng.random(140) * 5 + 0.5, color="white", alpha=0.55, lw=0, zorder=1)

    ax = fig.add_axes([0.085, 0.11, 0.79, 0.56])
    ax.set_facecolor("none")
    x0, x1 = xs[0] - 0.3, xs[-1] + 1.2
    ax.set_xlim(x0, x1); ax.set_ylim(YLO, YHI)
    ax.set_axis_off()

    # Launch pad: the 0% line, then the real trail with a soft glow.
    ax.plot([x0, x1], [0, 0], color="white", alpha=0.18, lw=1.5, zorder=2)
    for lw, a in ((18, 0.06), (10, 0.12), (5, 0.35)):
        ax.plot(xs, ys, color=TRAIL, lw=lw, alpha=a, zorder=3, solid_joinstyle="round", solid_capstyle="round")
    ax.plot(xs, ys, color="#c9fff8", lw=2.2, zorder=4, solid_joinstyle="round")

    rocket(ax, xs[-1], ys[-1], height_px=225)

    ax.text(xs[-1] - 2.2, ys[-1] - 6, f"{ys[-1]:+.1f}%", ha="right", va="center", fontsize=64,
            fontweight="bold", color="white", zorder=12)
    ax.text(xs[-1] - 2.2, ys[-1] - 32, month_label(MONTH), ha="right", va="center", fontsize=30,
            color="#cfd6ff", zorder=12)
    ax.text(xs[0], 16, f"{months[0][:4]} to 2023: between −{abs(before.min()):.0f}% and {before.max():+.0f}%",
            ha="left", va="bottom", fontsize=30, color="#cfd6ff", zorder=12)

    fig.text(0.085, 0.905, "Printed circuit assembly prices", fontsize=62, color="white", fontweight="bold", va="top")
    fig.text(0.085, 0.815, f"rose {ys[-1]:.1f}% in a year", fontsize=62, color=TRAIL, fontweight="bold", va="top")
    fig.text(0.085, 0.73, f"Six takeaways from the {TARGET_LABEL} PPI", fontsize=34, color="#cfd6ff", va="top")

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{SLUG}-hero-1680x1080.png"
    fig.savefig(out, dpi=DPI, facecolor="#070b1a")
    plt.close(fig)
    shutil.copyfile(out, OUT / f"{SLUG}-hero-source.png")
    print("wrote", out.relative_to(ROOT), round(ys[-1], 1), "before 2024", round(before.min(), 1),
          round(before.max(), 1))


if __name__ == "__main__":
    main()
