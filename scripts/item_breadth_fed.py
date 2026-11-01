"""12-month item breadth above, the Fed's target rate below, on one time axis.
Two panels rather than two y-scales on one panel. Labels are computed from the data."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from common import RAW  # noqa: E402
from item_breadth_charts import BG, DIR, GRID, INK, LINE, MUTED, NOW, SOURCE  # noqa: E402

WEIGHT, RATE, SHADE = "#e8b04b", "#BBBDC0", "#2B3036"

d = pd.read_csv(DIR / "numbers" / "yoy.csv", index_col=0)
x = pd.to_datetime(d.index)
r = pd.read_csv(RAW / "fed_target_upper.csv")
r.columns = ["date", "rate"]
r["date"] = pd.to_datetime(r.date)
r["rate"] = pd.to_numeric(r.rate, errors="coerce")
r = r.dropna().set_index("date").rate
r = r[(r.index >= "2014-01-01")]
ch = r.diff().dropna()
ch = ch[ch != 0]
first = ch[(ch > 0) & (ch.index >= "2022-01-01")].index[0]
big = ch[(ch >= .75) & (ch.index >= "2022-01-01")].index[0]
peak = r[r.index <= "2024-01-01"].idxmax()
cut_to = x[-1] + pd.offsets.MonthEnd(0)
r = r[r.index <= cut_to]

f, (a, b) = plt.subplots(2, 1, figsize=(14, 9.5), sharex=True, facecolor=BG,
                         gridspec_kw={"height_ratios": [2.3, 1], "hspace": .16})
for ax in (a, b):
    ax.set_facecolor(BG)
    ax.axvspan(first, peak, color=SHADE, lw=0)
    ax.axvline(big, color=MUTED, lw=1, ls=(0, (3, 3)))
    ax.grid(axis="y", color=GRID, lw=.8)
    ax.set_axisbelow(True)
    ax.tick_params(colors=MUTED, labelsize=12, length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")

for col, c, word in (("sd1_pct_n", LINE, "items"), ("sd1_pct_w", WEIGHT, "weight")):
    y = d[col]
    a.plot(x, y, color=c, lw=2)
    pk = y.idxmax()
    a.annotate(f"Share of {word}\npeak {pd.Timestamp(pk):%b %Y}: {y[pk]:.1f}%", (pd.Timestamp(pk), y[pk]),
               xytext=(-14, 2) if word == "items" else (34, 34), textcoords="offset points",
               ha="right" if word == "items" else "left", va="center", color=c, fontsize=12.5)
    a.scatter([x[-1]], [y.iloc[-1]], color=c, s=46, zorder=5)
    a.annotate(f"{y.iloc[-1]:.1f}%", (x[-1], y.iloc[-1]), xytext=(8, 0), textcoords="offset points",
               va="center", color=INK, fontsize=12.5, annotation_clip=False)
a.set_ylim(0, 82)
a.set_title("PPI final demand items with a 12-month change more than 1 SD above their own average",
            color=INK, fontsize=13.5, loc="left", pad=8)

b.step(r.index, r.values, where="post", color=RATE, lw=2)
b.set_ylim(0, 6.5)
b.set_title("Federal funds target rate, upper limit", color=INK, fontsize=13.5, loc="left", pad=8)
b.annotate(f"First increase\n{first:%b %Y}", (first, r[first]), xytext=(-10, 24), textcoords="offset points",
           ha="right", color=INK, fontsize=12)
b.annotate(f"First 0.75-point\nincrease {big:%b %Y}", (big, 6.3), xytext=(-6, 0), textcoords="offset points",
           ha="right", va="top", color=INK, fontsize=12)
b.annotate(f"Peak {r[peak]:.2f}%\n{peak:%b %Y}", (peak, r[peak]), xytext=(8, -2), textcoords="offset points",
           ha="left", va="top", color=INK, fontsize=12)
b.annotate(f"{r.iloc[-1]:.2f}%", (r.index[-1], r.iloc[-1]), xytext=(8, 0), textcoords="offset points",
           va="center", color=INK, fontsize=12.5, annotation_clip=False)
f.suptitle("Item-level price increases and the Fed's rate increases", color="#E6E7E8", fontsize=20,
           x=.05, y=.965, ha="left", fontweight="bold")
f.text(.05, .915, "January 2014 to September 2026. Shaded: first rate increase to the peak.", color=INK, fontsize=13.5)
f.text(.05, .02, SOURCE + " Fed rate: FRED, DFEDTARU.", color=MUTED, fontsize=9)
f.subplots_adjust(left=.05, right=.94, top=.855, bottom=.08)
f.savefig(DIR / "04-twelve-month-fed.png", dpi=120, facecolor=BG)
print(first.date(), big.date(), peak.date(), r[peak], r.index[-1].date(), r.iloc[-1], ch[ch.index>=first].round(2).to_dict())
