"""Hero for ppi-september-2026: the long-distance trucking chart as a mountain highway.

The ridge line is the real 12-month change in long-distance motor carrying
(WPU301202), every month from June 2010 to the release month, read from the BLS
flat files, on a labeled axis. The mountain fill, road, signs and truck are
decoration; every number on a sign is a real value from the series.
Writes posts/ppi-september-2026/images/ppi-september-2026-hero-1680x1080.png
and the same image as -hero-source.png.
"""
from __future__ import annotations

import math
import shutil

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Circle, FancyBboxPatch, Polygon, Rectangle  # noqa: E402
from matplotlib.transforms import Affine2D, IdentityTransform  # noqa: E402

from common import ROOT, TARGET
from takeaways import month_label, raw_levels, shift_month, xpos

SLUG = "ppi-september-2026"
MONTH = f"{TARGET[0]}-{TARGET[1]:02d}"
OUT = ROOT / "posts" / SLUG / "images"
W, H, DPI = 1680, 1080, 100
YLO, YHI = -20, 32
INK = "#E8E6E1"

plt.rcParams.update({"font.family": ["Arial", "DejaVu Sans"], "text.parse_math": False})


START = "2019-01"   # the full history back to 2010 makes the 2026 climb nearly vertical at hero width


def series():
    lv = raw_levels("WPU301202")
    allm = [m for m in sorted(lv) if shift_month(m, 12) in lv and m <= MONTH]
    yy = {m: (lv[m] / lv[shift_month(m, 12)] - 1) * 100 for m in allm}
    avg = sum(yy[m] for m in allm if m < MONTH) / len([m for m in allm if m < MONTH])
    months = [m for m in allm if m >= START]
    return months, [yy[m] for m in months], avg, allm[0]


def gradient(ax, extent, top, bottom, clip=None, z=0):
    g = np.linspace(0, 1, 256)[:, None]
    c0, c1 = np.array(matplotlib.colors.to_rgb(top)), np.array(matplotlib.colors.to_rgb(bottom))
    img = (c0 + (c1 - c0) * g[..., None]) * np.ones((1, 2, 1))
    im = ax.imshow(img, extent=extent, aspect="auto", origin="upper", zorder=z, interpolation="bicubic")
    if clip is not None:
        im.set_clip_path(clip)
    return im


def truck(ax, fig, x0, y0, x1, y1):
    """A long-nose semi with its rear wheels at data (x0, y0) and front wheels at (x1, y1)."""
    to_px = ax.transData.transform
    (px0, py0), (px1, py1) = to_px((x0, y0)), to_px((x1, y1))
    ang = math.atan2(py1 - py0, px1 - px0)
    L = math.hypot(px1 - px0, py1 - py0) / (0.90 - 0.06)
    ox, oy = px0 - 0.06 * L * math.cos(ang), py0 - 0.06 * L * math.sin(ang)
    length = L
    tr = Affine2D().translate(0, -0.055).scale(L).rotate(ang).translate(ox, oy) + IdentityTransform()
    road = 0.035                                   # wheels sit on top of the road stripe
    parts = [
        Rectangle((-0.02, road + 0.09), 0.62, 0.30, fc="#F4F1EA", ec="#9a9a9a", lw=1),      # trailer
        Rectangle((-0.02, road + 0.075), 0.62, 0.02, fc="#7d7d7d", ec="none"),              # trailer frame
        Rectangle((0.62, road + 0.07), 0.36, 0.035, fc="#3a3a3a", ec="none"),               # chassis
        Polygon([(0.63, road + 0.10), (0.63, road + 0.36), (0.68, road + 0.40), (0.78, road + 0.40),
                 (0.79, road + 0.25), (0.79, road + 0.10)], closed=True, fc="#C8322B", ec="#7a1d18", lw=1),  # cab
        Polygon([(0.79, road + 0.10), (0.79, road + 0.25), (0.95, road + 0.23), (0.99, road + 0.19),
                 (0.99, road + 0.10)], closed=True, fc="#C8322B", ec="#7a1d18", lw=1),       # long nose
        Polygon([(0.70, road + 0.27), (0.70, road + 0.36), (0.775, road + 0.36), (0.78, road + 0.27)],
                closed=True, fc="#9fd3ec", ec="#2b2b2b", lw=0.8),                            # window
        Rectangle((0.975, road + 0.11), 0.02, 0.09, fc="#d9d9d9", ec="none"),               # grille
        Rectangle((0.655, road + 0.36), 0.012, 0.16, fc="#c9c9c9", ec="none"),              # stack
        Rectangle((0.985, road + 0.165), 0.012, 0.02, fc="#ffe9a6", ec="none"),             # headlight
    ]
    for p in parts:
        p.set_transform(tr)
        p.set_zorder(9)
        ax.add_artist(p)
    for wx in (0.06, 0.16, 0.50, 0.70, 0.90):
        for r, fc in ((0.055, "#1b1b1b"), (0.025, "#9a9a9a")):
            c = Circle((wx, road + 0.055), r, fc=fc, ec="none", transform=tr, zorder=10)
            ax.add_artist(c)
    lab = ax.text(0.29, road + 0.24, "LONG-HAUL TRUCKING", transform=tr, ha="center", va="center",
                  fontsize=length / 27, fontweight="bold", color="#2b2b2b", zorder=11,
                  rotation=math.degrees(ang), rotation_mode="anchor")
    return lab


def sign(ax, x, y_ground, y_top, lines, fc="#1F6B3A", fs=13):
    ax.plot([x, x], [y_ground, y_top], color="#8a8a8a", lw=2.2, zorder=6, solid_capstyle="butt")
    ax.text(x, y_top, "\n".join(lines), ha="center", va="bottom", fontsize=fs, fontweight="bold", color="white",
            zorder=7, linespacing=1.25,
            bbox=dict(boxstyle="round,pad=0.45,rounding_size=0.25", fc=fc, ec="white", lw=2))


def main():
    months, ys, avg, first = series()
    xs = np.array([xpos(m) for m in months])
    ys = np.array(ys)

    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI)
    bg = fig.add_axes([0, 0, 1, 1])
    bg.set_axis_off()
    gradient(bg, (0, 1, 0, 1), "#0d1626", "#e08a4f", z=0)          # dusk sky
    bg.set_xlim(0, 1); bg.set_ylim(0, 1)

    ax = fig.add_axes([0.075, 0.095, 0.875, 0.58])
    ax.set_facecolor("none")
    x0, x1 = xs[0] - 0.2, xs[-1] + 0.55
    ax.set_xlim(x0, x1)
    ax.set_ylim(YLO, YHI)


    # The mountain: everything under the real line, with a rock gradient.
    poly = Polygon(np.column_stack([np.r_[xs[0], xs, xs[-1]], np.r_[YLO, ys, YLO]]), closed=True,
                   transform=ax.transData, fc="none", ec="none")
    ax.add_patch(poly)
    gradient(ax, (x0, x1, YLO, YHI), "#8a7563", "#2a2421", clip=poly, z=2)

    # The road along the ridge: asphalt, then a dashed center line.
    ax.plot(xs, ys, color="#2a2a2a", lw=9, zorder=4, solid_joinstyle="round", solid_capstyle="round")
    ax.plot(xs, ys, color="#f2c94c", lw=1.4, zorder=5, ls=(0, (4, 4)))

    # Axis, kept readable.
    for t in range(-20, 31, 10):
        ax.axhline(t, color="white", alpha=0.10, lw=1, zorder=1.5)
        ax.text(x0 - 0.12, t, f"{t:+d}%" if t else "0%", ha="right", va="center", fontsize=15, color=INK)
    ax.plot([xs[0], xs[-1]], [avg, avg], color="white", alpha=0.55, lw=1.6, ls=(0, (6, 4)), zorder=5.5)
    for y in range(int(months[0][:4]), int(MONTH[:4]) + 1):
        ax.text(y, YLO - 1.6, str(y), ha="center", va="top", fontsize=15, color=INK)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks([]); ax.set_yticks([])

    # Signs, each carrying a real value from the series.
    i_pk = int(ys.argmax())
    sign(ax, xs[i_pk] - 0.45, ys[i_pk - 4], 29.5,
         ["PEAK", f"{month_label(months[i_pk]).upper()}", f"{ys[i_pk]:+.1f}%"])
    i_lo = int(np.argmin(np.where(np.array([m.startswith("2023") for m in months]), ys, 99)))
    sign(ax, xs[i_lo] + 0.55, ys[i_lo + 7], ys[i_lo + 7] + 9,
         ["VALLEY", f"{month_label(months[i_lo]).upper()}", f"{ys[i_lo]:+.1f}%"], fs=12)
    sign(ax, 2019.55, avg, avg + 9, ["AVERAGE SINCE", f"{first[:4]}: {avg:+.1f}%"], fs=12)
    sign(ax, xs[-1] + 0.02, ys[-1] + 3.5, 29.5, [month_label(MONTH).upper(), f"{ys[-1]:+.1f}%"], fc="#1F6B3A")
    # Yellow grade sign on the latest climb.
    feb = months.index("2026-02")
    ax.plot([xs[feb] - 0.3] * 2, [ys[feb] + 1, ys[feb] + 8.5], color="#8a8a8a", lw=2.2, zorder=6)
    ax.text(xs[feb] - 0.3, ys[feb] + 8.5, "STEEP\nGRADE", ha="center", va="center", fontsize=10.5,
            fontweight="bold", color="#1b1b1b", zorder=7, linespacing=1.1,
            bbox=dict(boxstyle="round,pad=0.55", fc="#F2C94C", ec="#1b1b1b", lw=2))

    # Yellow engine-brake sign on the steep descent out of 2022.
    d = months.index("2022-12")
    ax.plot([xs[d]] * 2, [ys[d], ys[d] + 9.5], color="#8a8a8a", lw=2.2, zorder=3.9)
    ax.text(xs[d] + 0.22, ys[d] + 9.5, "TRUCKS\nUSE ENGINE\nBRAKE", ha="center", va="center", fontsize=10.5,
            fontweight="bold", color="#1b1b1b", zorder=7, linespacing=1.1,
            bbox=dict(boxstyle="round,pad=0.55", fc="#F2C94C", ec="#1b1b1b", lw=2))

    # The truck on the latest hill, rear wheels in April 2026, pointed at September.
    a = months.index("2026-04")
    truck(ax, fig, xs[a], ys[a], xs[-1], ys[-1])

    # Title block.
    fig.text(0.045, 0.94, "Five takeaways from the", fontsize=40, color="white", fontweight="bold", va="top")
    fig.text(0.045, 0.875, "September 2026 PPI data release", fontsize=40, color="white", fontweight="bold",
             va="top")
    fig.text(0.045, 0.80, f"Long-haul trucking prices, 12-month change, {month_label(months[0])} to "
             f"{month_label(MONTH)}", fontsize=19, color="#f3dcc6", va="top")
    fig.text(0.955, 0.012, "Data 4 The People  ·  Source: BLS Producer Price Index, long-distance motor carrying",
             fontsize=12.5, color="#d9d4cc", ha="right", va="bottom")

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{SLUG}-hero-1680x1080.png"
    fig.savefig(out, dpi=DPI, facecolor="#0d1626")
    plt.close(fig)
    shutil.copyfile(out, OUT / f"{SLUG}-hero-source.png")
    print("wrote", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
