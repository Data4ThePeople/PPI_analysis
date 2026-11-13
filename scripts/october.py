"""Charts for the October 2026 takeaways post, written to charts/<TARGET>/.

01 headline and 03 trucking reuse takeaways.py; 02 drivers is drivers.py;
04 software and 05 fuels are drawn here. Every number drawn is also written to
charts/<month>/numbers/*.csv for takeaways_tieout.py.
"""
from __future__ import annotations

import pandas as pd

import drivers
from common import PRELIM, PROCESSED
from takeaways import (DOWN, FUEL, GRID, INK, LINE_B, MONTH, MUTED, fig, finish, headline,
                       month_label, raw_levels, trucking, xpos, year_axis)

SOFTWARE = "341101"
BLS = "Data 4 The People  ·  Source: BLS Producer Price Index"


def software(items, name):
    """System software publishing: 12-month change over the index's whole history."""
    lv = raw_levels(f"WPU{SOFTWARE}")
    base = lambda m: f"{int(m[:4]) - 1}{m[4:]}"
    months = [m for m in sorted(lv) if base(m) in lv and m <= MONTH]
    ys = [(lv[m] / lv[base(m)] - 1) * 100 for m in months]
    first_index = min(lv)
    prev = months[-2]
    mom = (lv[MONTH] / lv[prev] - 1) * 100
    row = items[(items.month == MONTH) & (items.code == SOFTWARE)].iloc[0]
    low = min(ys) == ys[-1]
    f, top = fig("System software publishing, 12-month price change",
                 f"{month_label(months[0])} to {month_label(MONTH)}. BLS began this index in {month_label(first_index)}, so 12-month "
                 f"changes start a year later.\n{month_label(MONTH)} is "
                 + (f"the lowest of all {len(ys)} months" if low else f"{ys[-1]:+.1f}%")
                 + f"; the index fell {abs(mom):.1f}% from {month_label(prev)}. The item carries "
                 f"about {row.weight_base:.1f}% of final demand\nand took {abs(row.contrib):.2f} points off the 12-month change. "
                 f"{PRELIM} are preliminary.",
                 h=7.5, legend=[("System software publishing", DOWN)])
    ax = f.add_axes([0.07, 0.10, 0.80, top - 0.12])
    xs = [xpos(m) for m in months]
    ax.plot(xs, ys, color=DOWN, lw=2)
    ax.scatter([xs[-1]], [ys[-1]], s=36, color=DOWN, zorder=4)
    ax.text(xs[-1] + 0.06, ys[-1], f"{ys[-1]:+.1f}%", color=INK, fontsize=12, fontweight="bold", va="center")
    hi_m = months[ys.index(max(ys))]
    ax.text(xpos(hi_m), max(ys) + 1.5, f"{max(ys):+.1f}%\n{month_label(hi_m)}", color=INK, fontsize=10.5,
            ha="center", va="bottom")
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.set_ylim(-25, 22)
    ticks = list(range(-20, 21, 10))
    ax.set_yticks(ticks)
    ax.set_yticklabels([f"{t:+d}%" if t else "0%" for t in ticks])
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_xlim(xs[0] - 0.1, xs[-1] + 0.45)
    ax.set_xticks(range(2024, int(MONTH[:4]) + 1))
    rows = [(SOFTWARE, m, round(v, 4)) for m, v in zip(months, ys)]
    rows += [(SOFTWARE, f"mom_{MONTH}", round(mom, 4)), (SOFTWARE, f"weight_{MONTH}", round(row.weight_base, 5)),
             (SOFTWARE, f"contrib_{MONTH}", round(row.contrib, 6))]
    finish(f, ax, name, rows, ["code", "month", "yoy_pct"],
           source=f"{BLS}, system software publishing (WPU{SOFTWARE}), not seasonally adjusted")


def fuels(items, summary, name):
    """Group 05 (fuels and related products and power) against every other item, in points."""
    months = sorted(items.month.unique())
    is_fuel = items.code.str.startswith("05")
    fu = items[is_fuel].groupby("month").contrib.sum().reindex(months)
    rest = items[~is_fuel].groupby("month").contrib.sum().reindex(months)
    last, tot = fu[MONTH], fu[MONTH] + rest[MONTH]
    above = [m for m in months if m < MONTH and fu[m] >= last]
    top_items = (items[(items.month == MONTH) & is_fuel].sort_values("contrib", ascending=False).head(4))
    named = ", ".join(f"{r['name'].replace('Unleaded regular gasoline', 'regular gasoline').replace('No. 2 diesel fuel', 'diesel').replace('Unleaded premium gasoline', 'premium gasoline').replace('Jet fuel', 'jet fuel')} ({r.yoy:+.0f}%)"
                      for _, r in top_items.iterrows())
    f, top = fig(f"Fuels added {last:.1f} points to wholesale inflation in {month_label(MONTH)}",
                 f"Contribution to the 12-month change in PPI final demand, in percentage points, {month_label(months[0])} to "
                 f"{month_label(MONTH)}. Fuels are BLS\ngroup 05, fuels and related products and power, which includes "
                 f"electricity and natural gas. In {month_label(MONTH)} fuels were {last / tot * 100:.1f}% of\nour item total, the "
                 f"most points since {month_label(above[-1])}. Largest: {named}.\n{PRELIM} are preliminary.",
                 h=7.8, legend=[("Fuels", FUEL), ("All other items", LINE_B)])
    ax = f.add_axes([0.07, 0.10, 0.80, top - 0.12])
    xs = [xpos(m) for m in months]
    for s, color in ((fu, FUEL), (rest, LINE_B)):
        ax.plot(xs, list(s), color=color, lw=2)
        ax.scatter([xs[-1]], [s[MONTH]], s=36, color=color, zorder=4)
        ax.text(xs[-1] + 0.12, s[MONTH], f"{s[MONTH]:+.2f}", color=INK, fontsize=12, fontweight="bold", va="center")
    pk = fu.idxmax()
    ax.text(xpos(pk), fu[pk] + 0.3, f"{fu[pk]:+.2f}\n{month_label(pk)}", color=INK, fontsize=10.5, ha="center",
            va="bottom")
    ax.axhline(0, color=MUTED, lw=0.8)
    lo, hi = min(fu.min(), rest.min()), max(fu.max(), rest.max())
    import math
    lo_t = 2 * math.floor(lo / 2)
    ax.set_ylim(lo_t - 0.4, math.ceil(hi) + 1)
    ticks = list(range(lo_t, math.ceil(hi) + 1, 2))
    ax.set_yticks(ticks)
    ax.set_yticklabels([f"{t:+d}" if t else "0" for t in ticks])
    ax.grid(axis="y", color=GRID, lw=0.6)
    year_axis(ax, months)
    rows = [(m, round(fu[m], 6), round(rest[m], 6)) for m in months]
    rows += [(f"share_{MONTH}", round(last / tot * 100, 4), ""), (f"last_at_or_above_{MONTH}", above[-1], "")]
    rows += [(f"top_{r.code}", round(r.contrib, 6), round(r.yoy, 4)) for _, r in top_items.iterrows()]
    finish(f, ax, name, rows, ["month", "fuels_pts", "other_pts"],
           source=f"{BLS} for final demand, not seasonally adjusted, and relative importance tables")


def main():
    items = pd.read_csv(PROCESSED / "monthly_items.csv", dtype={"code": str, "old_code": str}, low_memory=False)
    summary = pd.read_csv(PROCESSED / "monthly_summary.csv")
    headline(items, summary, "01-headline.png")
    drivers.main()
    trucking("03-trucking.png")
    software(items, "04-software.png")
    fuels(items, summary, "05-fuels.png")


if __name__ == "__main__":
    main()
