"""What moved the 12-month PPI final demand rate from the month before to TARGET.

For each item, the change in its contribution to the 12-month change (points),
TARGET minus the month before, both from data/processed/monthly_items.csv (the
month before as revised in the same pull). Draws the 10 items that pushed the
rate up most and the 10 that pulled it down most; the rest are netted in one
bar. Also writes the unweighted 12-month movers (items with their own published
index) to numbers/ for the post text.
"""
from __future__ import annotations

import csv

import pandas as pd

from common import PRELIM, PROCESSED, month_add
from takeaways import (BG, CHARTS, DOWN, INK, MONTH, MUTED, NUM, UP, fig, finish,
                       month_label, short)

N = 10
EXTRA_SHORT = {
    "Health and beauty care retailing, including optical goods": "Health and beauty retailing",
    "Computer hardware, software, and supplies retailing": "Computer retailing",
    "Machinery and vehicle wholesaling": "Machinery and vehicle wholesaling",
    "Beef and veal products, fresh or frozen": "Beef and veal",
}


def label(name):
    return EXTRA_SHORT.get(name, short(name))


def main():
    items = pd.read_csv(PROCESSED / "monthly_items.csv", dtype={"code": str, "old_code": str},
                        low_memory=False)
    summary = pd.read_csv(PROCESSED / "monthly_summary.csv").set_index("month")
    prev = month_add(MONTH, -1)
    a = items[items.month == MONTH].set_index("code")
    b = items[items.month == prev].set_index("code")
    if set(a.index) != set(b.index):
        raise RuntimeError("item lists differ between the two months")
    a = a.assign(prev_yoy=b.yoy, prev_contrib=b.contrib, change=a.contrib - b.contrib)
    up = a.sort_values("change", ascending=False).head(N)
    down = a.sort_values("change").head(N)
    rest = a.drop(up.index).drop(down.index)
    pub_a, pub_b = summary.published[MONTH], summary.published[prev]
    tot = a.change.sum()

    bars = ([(label(r["name"]), r.prev_yoy, r.yoy, r.change, UP) for _, r in up.iterrows()]
            + [(f"The other {len(rest)} items, net", None, None, rest.change.sum(), MUTED)]
            + [(label(r["name"]), r.prev_yoy, r.yoy, r.change, DOWN) for _, r in down.iloc[::-1].iterrows()])
    f, top = fig(f"What moved wholesale inflation from {pub_b:.1f}% to {pub_a:.1f}%",
                 f"Change in each item's share of the 12-month change in PPI final demand, {month_label(prev)} to "
                 f"{month_label(MONTH)}, in percentage\npoints. In parentheses, the item's 12-month price change in "
                 f"each month. Our items add up to {tot:+.3f} points; BLS's published\nrate moves "
                 f"{pub_a - pub_b:+.3f} ({pub_b:.2f}% to {pub_a:.2f}%). "
                 "Items ending in \"retailing\" or \"wholesaling\" measure the margin sellers keep.",
                 h=9.2, legend=[("Pushed the rate up", UP), ("Pulled it down", DOWN), ("Everything else", MUTED)])
    ax = f.add_axes([0.40, 0.07, 0.55, top - 0.09])
    rows = []
    n = len(bars)
    for k, (lab, py, y, v, color) in enumerate(bars):
        yy = n - 1 - k
        ax.barh(yy, v, height=0.62, color=color)
        full = lab if py is None else f"{lab}  ({py:+.1f}% to {y:+.1f}%)"
        ax.text(-0.215, yy, full, ha="right", va="center", fontsize=11.5, color=INK)
        ax.text(v + (0.004 if v >= 0 else -0.004), yy, f"{v:+.3f}",
                ha="left" if v >= 0 else "right", va="center", fontsize=11, color=INK)
        rows.append((lab, "" if py is None else round(py, 4), "" if y is None else round(y, 4), round(v, 6)))
    rows.append(("All items", "", "", round(tot, 6)))
    rows.append(("Published", round(pub_b, 4), round(pub_a, 4), round(pub_a - pub_b, 6)))
    ax.axvline(0, color=MUTED, lw=0.8)
    ax.set_xlim(-0.21, 0.14)
    ax.set_ylim(-0.6, n - 0.4)
    ax.set_yticks([]); ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    finish(f, ax, "02-drivers.png", rows, ["item", f"yoy_{prev}", f"yoy_{MONTH}", "contrib_change_pts"],
           source="Data 4 The People  ·  Source: BLS Producer Price Index for final demand, not seasonally "
                  f"adjusted, and relative importance tables. {PRELIM} are preliminary.")

    own = a[a.own_index & a.filled_from.isna()]
    with open(NUM / "02-movers-unweighted.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["list", "code", "item", "weight", f"yoy_{prev}", f"yoy_{MONTH}"])
        for lst, df in (("rising", own.sort_values("yoy", ascending=False).head(15)),
                        ("falling", own.sort_values("yoy").head(15))):
            for code, r in df.iterrows():
                w.writerow([lst, code, r["name"], round(r.weight_base, 4), round(r.prev_yoy, 4), round(r.yoy, 4)])
    print("wrote 02-movers-unweighted.csv")


if __name__ == "__main__":
    main()
