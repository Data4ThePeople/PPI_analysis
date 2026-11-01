"""Charts for the item breadth analysis, in the dark house palette. Reads only
the CSVs item_breadth.py writes; every label is computed from them."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from common import ROOT, TARGET  # noqa: E402

LAST = f"{TARGET[0]}-{TARGET[1]:02d}"
DIR = ROOT / "charts" / f"{LAST}-breadth"
BG, INK, MUTED, GRID = "#181A1B", "#BBBDC0", "#8C9094", "#2A2E31"
LINE, SHADE, NOW = "#5598e7", "#3A2A24", "#f37952"
SOURCE = ("Data 4 The People  ·  Source: BLS Producer Price Index for final demand, not seasonally adjusted, and "
          "relative importance tables. June to September 2026 are preliminary.")
ROWS = [("sd1", "More than 1 SD above the item's average"),
        ("sd2", "More than 2 SD above the item's average"),
        ("top10", "In the item's top 10% of months")]
FIGS = [("monthly", "01-monthly-as-asked",
         "How many items had an unusually large one-month price increase?",
         "Each item's monthly change compared with its own average since 2012"),
        ("monthly_seasonal", "02-monthly-time-of-year",
         "The same test, adjusted for the time of year",
         "Each item's monthly change compared with its own average for that calendar month"),
        ("yoy", "03-twelve-month",
         "What share of items had a 12-month increase well above their own average?",
         "Each item's 12-month change compared with its own average since 2013")]


def fig(name, out, title, sub):
    d = pd.read_csv(DIR / "numbers" / f"{name}.csv", index_col=0)
    x = pd.to_datetime(d.index)
    f, axs = plt.subplots(3, 2, figsize=(14, 10.5), sharex=True, facecolor=BG)
    for r, (key, label) in enumerate(ROWS):
        top = max(d[f"{key}_pct_n"].max(), d[f"{key}_pct_w"].max()) * 1.2
        for c, (kind, word) in enumerate((("n", "Share of items"), ("w", "Share of weight"))):
            ax, y = axs[r][c], d[f"{key}_pct_{kind}"]
            ax.set_facecolor(BG)
            ax.axvspan(pd.Timestamp("2021-01-01"), pd.Timestamp("2022-12-31"), color=SHADE, lw=0)
            ax.hlines(y.mean(), x[0], x[-1], color=MUTED, lw=1, ls=(0, (4, 3)))
            ax.plot(x, y, color=LINE, lw=1.6)
            ax.set_ylim(0, top)
            ax.grid(axis="y", color=GRID, lw=.8)
            ax.set_axisbelow(True)
            ax.tick_params(colors=MUTED, labelsize=11, length=0)
            for s in ax.spines.values():
                s.set_visible(False)
            ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
            ax.set_title(f"{word}: {label.lower().replace(' sd ', ' SD ')}", color=INK, fontsize=12.5, loc="left", pad=8)
            pk = y.idxmax()
            ax.annotate(f"{pd.Timestamp(pk):%b %Y}: {y[pk]:.1f}%", (pd.Timestamp(pk), y[pk]),
                        xytext=(-8, 0), textcoords="offset points", ha="right", va="center", color=INK, fontsize=11)
            ax.scatter([x[-1]], [y.iloc[-1]], color=NOW, s=46, zorder=5)
            ax.annotate(f"Sep 2026\n{y.iloc[-1]:.1f}%", (x[-1], y.iloc[-1]), xytext=(6, 0), textcoords="offset points",
                        ha="left", va="center", color=INK, fontsize=11, annotation_clip=False)
            ax.annotate(f"Average {y.mean():.1f}%", (x[0], y.mean()), xytext=(2, 5), textcoords="offset points",
                        color=MUTED, fontsize=10.5)
            if r == 0:
                ax.annotate("2021-2022", (pd.Timestamp("2022-01-01"), top), xytext=(0, -14), textcoords="offset points",
                            ha="center", color=MUTED, fontsize=10.5)
    f.suptitle(title, color="#E6E7E8", fontsize=20, x=.04, y=.975, ha="left", fontweight="bold")
    f.text(.04, .925, sub + ", January 2014 to September 2026", color=INK, fontsize=13.5)
    f.text(.04, .018, SOURCE, color=MUTED, fontsize=9.5)
    f.subplots_adjust(left=.05, right=.93, top=.865, bottom=.075, hspace=.3, wspace=.2)
    f.savefig(DIR / f"{out}.png", dpi=120, facecolor=BG)
    plt.close(f)


if __name__ == "__main__":
    for a in FIGS:
        fig(*a)
