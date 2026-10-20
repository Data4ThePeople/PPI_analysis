"""Static charts for the September 2026 takeaways post, in the dark house palette.

Every number drawn is read from data/processed/monthly_items.csv and
monthly_summary.csv, the same numbers the scuba diver shows. The numbers behind
each chart are also written to charts/<month>/numbers/*.csv for the tie-out.
"""
from __future__ import annotations

import csv
from datetime import date

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

import json

from common import PROCESSED, RAW, ROOT, TARGET, WP

MONTH = f"{TARGET[0]}-{TARGET[1]:02d}"
CHARTS = ROOT / "charts" / MONTH
NUM = CHARTS / "numbers"

BG, INK, MUTED, GRID = "#181A1B", "#BBBDC0", "#8C9094", "#2A2E31"
UP, DOWN = "#f37952", "#5598e7"            # coral = adds to the 12-month change, blue = subtracts
GOODS, SERVICES, CONSTRUCTION = "#f37952", "#e8b04b", "#8C9094"
FUEL = "#f2b84b"
LINE_A, LINE_B = "#f37952", "#5598e7"
SOURCE = ("Data 4 The People  ·  Source: BLS Producer Price Index for final demand (not seasonally adjusted) "
          "and relative importance tables; contributions computed by Data 4 The People")

JET, AIR, TRUCK = "057203", "302201", "301202"
PORTFOLIO, BROKERAGE = "402101", "401101"

SHORT = {
    "Unleaded regular gasoline": "Regular gasoline",
    "Unleaded premium gasoline": "Premium gasoline",
    "Long-distance motor carrying": "Long-distance trucking",
    "Other commodities wholesaling": "Other goods wholesaling",
    "Airline passenger services": "Airline passenger services",
    "Hospital inpatient care": "Hospital inpatient care",
    "Securities brokerage, dealing, and investment advice": "Securities brokerage and advice",
    "Automotive fuels and lubricants retailing": "Fuel retailing (gas stations)",
    "Automobile retailing (Partial)": "Car dealers",
    "Eggs for fresh use": "Eggs",
    "Pork products, fresh, frozen, or processed, except sausage": "Pork",
    "Cellular phone and other wireless telecommunication services": "Cell phone service",
    "Parts and supplies for machinery and equipment wholesaling": "Machinery parts wholesaling",
    "Metals, minerals, and ores wholesaling": "Metals and ores wholesaling",
    "Other merchandise retailing (partial)": "Other merchandise retailing",
    "Automotive parts, including tires, retailing": "Auto parts and tires retailing",
    "Apparel, footwear, and accessories retailing": "Apparel and footwear retailing",
    "Professional and commercial equipment wholesaling": "Office and business equipment wholesaling",
    "Chemicals and allied products wholesaling": "Chemicals wholesaling",
}

plt.rcParams.update({"text.parse_math": False, "font.family": ["Arial", "DejaVu Sans"],
                     "axes.facecolor": BG, "figure.facecolor": BG, "text.color": INK,
                     "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
                     "axes.edgecolor": GRID})


def short(name):
    return SHORT.get(name, name)


def pts(v):
    """Percentage points: two decimals, three when the value rounds below 0.01."""
    return f"{v:+.2f}" if abs(v) >= 0.01 else f"{v:+.3f}"


def month_label(ym):
    y, m = map(int, ym.split("-"))
    return date(y, m, 1).strftime("%B %Y")


def xpos(ym):
    return int(ym[:4]) + (int(ym[5:]) - 1) / 12


def fig(title, sub, h=7.5, legend=None):
    f = plt.figure(figsize=(12, h), dpi=150)
    px = 1 / (h * 150)
    f.text(0.04, 1 - 22 * px, title, fontsize=20, fontweight="bold", va="top")
    y = 1 - 75 * px
    for line in sub.split("\n"):
        f.text(0.04, y, line, fontsize=12.5, color=MUTED, va="top")
        y -= 30 * px
    if legend:
        y -= 8 * px
        x = 0.04
        r = f.canvas.get_renderer()
        for word, color in legend:
            t = f.text(x, y, word, fontsize=12, fontweight="bold", color=color, va="top")
            x += t.get_window_extent(renderer=r).width / f.bbox.width + 0.025
        y -= 30 * px
    return f, y - 22 * px


def finish(f, ax, name, rows, header, source=SOURCE):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(length=0)
    f.text(0.04, 0.02, source, fontsize=8.5, color=MUTED)
    CHARTS.mkdir(parents=True, exist_ok=True)
    f.savefig(CHARTS / name, facecolor=BG)
    plt.close(f)
    NUM.mkdir(parents=True, exist_ok=True)
    with open(NUM / name.replace(".png", ".csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    print("wrote", name)


def year_axis(ax, months):
    y0, y1 = int(months[0][:4]), int(months[-1][:4])
    ax.set_xlim(xpos(months[0]) - 0.15, xpos(months[-1]) + 0.9)
    ax.set_xticks(range(y0 + 1, y1 + 1))
    ax.set_xticklabels([str(y) for y in range(y0 + 1, y1 + 1)])


def headline(items, summary, name):
    """Published 12-month change (line) and goods / services / construction contributions (bars)."""
    g = items.groupby(["month", "group"]).contrib.sum().unstack().fillna(0)
    s = summary.set_index("month")
    months = list(s.index)
    pub = s.published
    last = pub[MONTH]
    prev_higher = [m for m in months if m < MONTH and pub[m] >= last][-1]
    f, top = fig(f"Wholesale prices rose {last:.1f}% over the 12 months to {month_label(MONTH)}",
                 f"12-month change in PPI final demand, {month_label(months[0])} to {month_label(MONTH)}. "
                 f"The line is the rate BLS publishes, the\nhighest since {month_label(prev_higher)}. "
                 "The bars split our item contributions into goods, services and construction.\n"
                 "June to September 2026 are preliminary and BLS will revise them.",
                 h=7.8, legend=[("Published by BLS", INK), ("Goods", GOODS), ("Services", SERVICES),
                                ("Construction", CONSTRUCTION)])
    ax = f.add_axes([0.07, 0.10, 0.84, top - 0.12])
    xs = [xpos(m) for m in months]
    w = 1 / 12 * 0.8
    pos_base = [0.0] * len(months)
    neg_base = [0.0] * len(months)
    for grp, color in (("Goods", GOODS), ("Services", SERVICES), ("Construction", CONSTRUCTION)):
        vals = [g.loc[m, grp] for m in months]
        bottoms = [pb if v >= 0 else nb for v, pb, nb in zip(vals, pos_base, neg_base)]
        ax.bar(xs, vals, width=w, bottom=bottoms, color=color, alpha=0.85, linewidth=0)
        pos_base = [pb + max(v, 0) for v, pb in zip(vals, pos_base)]
        neg_base = [nb + min(v, 0) for v, nb in zip(vals, neg_base)]
    ax.plot(xs, list(pub), color=INK, lw=2, zorder=3)
    ax.scatter([xpos(MONTH)], [last], s=40, color=INK, zorder=4)
    ax.text(xpos(MONTH) + 0.12, last, f"{last:.1f}%", fontsize=12, fontweight="bold", va="center")
    peak_m = pub.idxmax()
    ax.text(xpos(peak_m), pub[peak_m] + 0.35, f"{pub[peak_m]:.1f}%\n{month_label(peak_m)}", fontsize=10.5,
            ha="center", va="bottom", color=INK)
    ax.axhline(0, color=MUTED, lw=0.8)
    lo, hi = min(neg_base) - 0.5, pub.max() + 1.4
    ax.set_ylim(lo, hi)
    ticks = [t for t in range(-4, 14, 2) if lo <= t <= hi]
    ax.set_yticks(ticks)
    ax.set_yticklabels([f"{t}%" for t in ticks])
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    year_axis(ax, months)
    rows = [(m, round(pub[m], 4), round(g.loc[m, "Goods"], 6), round(g.loc[m, "Services"], 6),
             round(g.loc[m, "Construction"], 6)) for m in months]
    finish(f, ax, name, rows, ["month", "published_pct", "goods_pts", "services_pts", "construction_pts"])


WATERFALL_UP, WATERFALL_DOWN = 8, 4


def waterfall(items, summary, name):
    m = items[items.month == MONTH].sort_values("contrib", ascending=False)
    up = m.head(WATERFALL_UP)
    down = m.sort_values("contrib").head(WATERFALL_DOWN)
    rest = m.drop(up.index).drop(down.index)
    total = m.contrib.sum()
    pub = summary.set_index("month").published[MONTH]
    fuel = lambda code: code.startswith("05")     # group 05: fuels and related products and power
    steps = ([(short(r["name"]), r.contrib, FUEL if fuel(r.code) else UP) for _, r in up.iterrows()]
             + [(f"The other {len(rest)} items, net", rest.contrib.sum(), MUTED)]
             + [(short(r["name"]), r.contrib, DOWN) for _, r in down.iterrows()])
    f, top = fig(f"What added up to wholesale inflation, {month_label(MONTH)}",
                 "Each bar is one item's share of the 12-month change in PPI final demand, in percentage points.\n"
                 "Bars build from left to right; the bottom bar is the total. In parentheses, the item's 12-month price change.\n"
                 f"Our items add up to {total:.2f} points; BLS publishes {pub:.2f}%.",
                 h=8.6, legend=[("Fuels, pushed up", FUEL), ("Other items, pushed up", UP), ("Pulled down", DOWN),
                                ("Everything else", MUTED)])
    ax = f.add_axes([0.33, 0.08, 0.61, top - 0.10])
    yoy = dict(zip(m.name.map(short), m.yoy))
    run, rows = 0.0, []
    n = len(steps)
    for k, (lab, v, color) in enumerate(steps):
        y = n - k
        left = run if v >= 0 else run + v
        ax.barh(y, abs(v), left=left, height=0.62, color=color)
        if k < n - 1:
            ax.plot([run + v, run + v], [y - 0.31, y - 1 + 0.31], color=MUTED, lw=0.7, ls=(0, (2, 2)))
        full = lab if color == MUTED else f"{lab}  ({yoy[lab]:+.1f}%)"
        ax.text(-0.08, y, full, ha="right", va="center", fontsize=11.5, color=INK)
        tx = (left + abs(v) + 0.05) if v >= 0 else (left - 0.05)
        ax.text(tx, y, pts(v), ha="left" if v >= 0 else "right", va="center", fontsize=11, color=INK)
        run += v
        rows.append((lab, round(v, 6), round(run, 6)))
    ax.barh(0, total, height=0.62, color=INK)
    ax.text(-0.08, 0, "All items", ha="right", va="center", fontsize=11.5, color=INK, fontweight="bold")
    ax.text(total + 0.05, 0, f"{total:+.2f}", ha="left", va="center", fontsize=11, color=INK, fontweight="bold")
    rows.append(("All items", round(total, 6), round(total, 6)))
    peak = max(r[2] for r in rows)
    ax.set_xlim(0, peak * 1.1)
    ax.set_ylim(-0.6, n + 0.6)
    ax.set_yticks([]); ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    ax.axvline(0, color=MUTED, lw=0.8)
    finish(f, ax, name, rows, ["step", "contrib_pts", "running_total_pts"])


def two_lines(items, codes, title, sub, name, labels):
    months = sorted(items.month.unique())
    f, top = fig(title, sub, h=7.5, legend=[(labels[0], LINE_A), (labels[1], LINE_B)])
    ax = f.add_axes([0.07, 0.10, 0.80, top - 0.12])
    rows, lo, hi = [], 0, 0
    for code, color, lab in zip(codes, (LINE_A, LINE_B), labels):
        x = items[items.code == code].set_index("month").reindex(months)
        ys = list(x.yoy)
        ax.plot([xpos(m) for m in months], ys, color=color, lw=2)
        ax.scatter([xpos(MONTH)], [ys[-1]], s=36, color=color, zorder=4)
        ax.text(xpos(MONTH) + 0.12, ys[-1], f"{ys[-1]:+.1f}%", color=INK, fontsize=12, fontweight="bold",
                va="center")
        lo, hi = min(lo, min(ys)), max(hi, max(ys))
        rows += [(code, lab, m, round(v, 4)) for m, v in zip(months, ys)]
    ax.axhline(0, color=MUTED, lw=0.8)
    span = hi - lo
    step = 50 if span > 150 else 20 if span > 60 else 10
    lo_t, hi_t = (int(lo // step) * step), (int(hi // step) + 1) * step
    ax.set_ylim(lo_t - step * 0.2, hi_t + step * 0.2)
    ticks = list(range(lo_t, hi_t + 1, step))
    ax.set_yticks(ticks)
    ax.set_yticklabels([f"{t:+d}%" if t else "0%" for t in ticks])
    ax.grid(axis="y", color=GRID, lw=0.6)
    year_axis(ax, months)
    finish(f, ax, name, rows, ["code", "item", "month", "yoy_pct"],
           source="Data 4 The People  ·  Source: BLS Producer Price Index commodity indexes "
                  f"(WPU{codes[0]}, WPU{codes[1]}), not seasonally adjusted")


def trade(items, name, n_up=6, n_down=4):
    """The trade margin items (codes 57x, 58x) that moved the total most, both ways."""
    m = items[(items.month == MONTH) & items.code.str.match(r"^5[78]")]
    up = m.sort_values("contrib", ascending=False).head(n_up)
    down = m.sort_values("contrib").head(n_down)
    sel = pd.concat([up, down.iloc[::-1]]).iloc[::-1]
    total = m.contrib.sum()
    f, top = fig(f"Store and wholesaler margins, {month_label(MONTH)}",
                 "PPI trade prices are margins: what a store or wholesaler sells a good for, minus what it costs them to buy it now.\n"
                 "Each bar is the item's share of the 12-month change in PPI final demand, in percentage points.\n"
                 f"In parentheses, the margin's 12-month change. All {len(m)} trade items together: {pts(total)} points.",
                 h=7.8, legend=[("Margins that rose", UP), ("Margins that fell", DOWN)])
    ax = f.add_axes([0.42, 0.08, 0.50, top - 0.10])
    ys = list(range(len(sel)))
    vals = list(sel.contrib)
    ax.barh(ys, vals, height=0.62, color=[UP if v >= 0 else DOWN for v in vals])
    lim_hi, lim_lo = max(vals) * 1.18, min(vals) * 1.18
    ax.set_xlim(min(lim_lo, -0.05) - 0.04, lim_hi)
    for y, (_, r) in zip(ys, sel.iterrows()):
        ax.text(-0.02, y, f"{short(r['name'])}  ({r.yoy:+.1f}%)", ha="right", va="center",
                fontsize=11.5, color=INK, transform=ax.get_yaxis_transform())
        v = r.contrib
        ax.text(v + (0.008 if v >= 0 else -0.008), y, pts(v), ha="left" if v >= 0 else "right", va="center",
                fontsize=11, color=INK)
    ax.set_yticks([]); ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    ax.axvline(0, color=MUTED, lw=0.8)
    finish(f, ax, name, [(r.code, r["name"], round(r.yoy, 4), round(r.contrib, 6)) for _, r in sel.iloc[::-1].iterrows()]
           + [("all", f"all {len(m)} trade items", "", round(total, 6))],
           ["code", "item", "yoy_pct", "contrib_pts"])


def raw_levels(sid):
    """Monthly index levels for one series, straight from the BLS flat files (full history)."""
    out = {}
    for p in sorted(WP.glob("wp.data.*")):
        for line in open(p):
            if line.split("\t", 1)[0].strip() == sid:
                f = line.rstrip("\n").split("\t")
                if f[2].startswith("M") and f[2] != "M13":
                    out[f"{f[1]}-{f[2][1:]}"] = float(f[3])
    return out


def trucking(name, upto=None):
    """Long-distance trucking's 12-month change over its whole published history, against its average."""
    lv = raw_levels(f"WPU{TRUCK}")
    months = [m for m in sorted(lv) if f"{int(m[:4]) - 1}{m[4:]}" in lv and m <= MONTH]
    ys = [(lv[m] / lv[f"{int(m[:4]) - 1}{m[4:]}"] - 1) * 100 for m in months]
    last = ys[-1]
    avg = sum(ys[:-1]) / len(ys[:-1])
    rank = sorted(ys, reverse=True).index(last) + 1
    higher = [m for m, v in zip(months, ys) if v > last]
    f, top = fig("Long-distance trucking, 12-month price change",
                 f"{month_label(months[0])} to {month_label(MONTH)}, every month BLS has published. The dashed line is the average of\n"
                 f"all months before {month_label(MONTH)}. {month_label(MONTH)} ranks {rank} of {len(ys)} months; the {len(higher)} higher months "
                 f"are all in {sorted({m[:4] for m in higher})[0]}.\nJune to September 2026 are preliminary.",
                 h=7.5, legend=[("Long-distance trucking", LINE_A), ("Average", MUTED)])
    ax = f.add_axes([0.07, 0.10, 0.80, top - 0.12])
    xs = [xpos(m) for m in months]
    k = upto or len(months)                       # animation frames draw the first k months
    ax.plot(xs[:k], ys[:k], color=LINE_A, lw=2)
    ax.scatter([xs[k - 1]], [ys[k - 1]], s=36, color=LINE_A, zorder=4)
    ax.text(xs[k - 1] + 0.15, ys[k - 1], f"{ys[k - 1]:+.1f}%", color=INK, fontsize=12, fontweight="bold", va="center")
    if k < len(months):                           # month tag while drawing; the last frame matches the chart
        ax.text(xs[k - 1], ys[k - 1] + (3.2 if ys[k - 1] >= avg else -3.2), month_label(months[k - 1]),
                color=MUTED, fontsize=10.5, ha="center", va="center")
    ax.plot([xs[0], xs[-1]], [avg, avg], color=MUTED, lw=1.2, ls=(0, (4, 3)))
    ax.text(xs[-1] + 0.15, avg, f"average {avg:+.1f}%", color=INK, fontsize=10.5, va="center")
    ax.axhline(0, color=MUTED, lw=0.8)
    lo, hi = min(ys), max(ys)
    lo_t, hi_t = int(lo // 10) * 10, (int(hi // 10) + 1) * 10
    ax.set_ylim(lo_t - 2, hi_t + 2)
    ticks = list(range(lo_t, hi_t + 1, 10))
    ax.set_yticks(ticks)
    ax.set_yticklabels([f"{t:+d}%" if t else "0%" for t in ticks])
    ax.grid(axis="y", color=GRID, lw=0.6)
    y0, y1 = int(months[0][:4]), int(MONTH[:4])
    ax.set_xlim(xs[0] - 0.15, xs[-1] + 1.3)
    ax.set_xticks(range(y0 + 1, y1 + 1, 2))
    ax.set_xticklabels([str(y) for y in range(y0 + 1, y1 + 1, 2)])
    if upto is not None:
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.tick_params(length=0)
        f.text(0.04, 0.02, "Data 4 The People  ·  Source: BLS Producer Price Index, long-distance motor carrying "
               f"(WPU{TRUCK}), not seasonally adjusted", fontsize=8.5, color=MUTED)
        return f, len(months)
    finish(f, ax, name, [(TRUCK, m, round(v, 4)) for m, v in zip(months, ys)]
           + [(TRUCK, "average_before_" + MONTH, round(avg, 4))], ["code", "month", "yoy_pct"],
           source="Data 4 The People  ·  Source: BLS Producer Price Index, long-distance motor carrying "
                  f"(WPU{TRUCK}), not seasonally adjusted")


def jet_cpi(items, name):
    """Jet fuel (PPI) against airline fares in the CPI, 12-month change."""
    months = sorted(items.month.unique())
    jet = items[items.code == JET].set_index("month").reindex(months).yoy
    cpi = json.loads((RAW / "cpi_airline_fares.json").read_text())
    fares = [(cpi[m] / cpi[f"{int(m[:4]) - 1}{m[4:]}"] - 1) * 100
             if m in cpi and f"{int(m[:4]) - 1}{m[4:]}" in cpi else float("nan") for m in months]
    f, top = fig("Jet fuel and airline fares, 12-month price change",
                 f"{month_label(months[0])} to {month_label(MONTH)}. Jet fuel is the producer price in PPI final demand. Airline\n"
                 "fares are what travelers pay, from the Consumer Price Index. The gap is October 2025: BLS did not\n"
                 "collect CPI data during the lapse in appropriations. June to September 2026 PPI figures are preliminary.",
                 h=7.5, legend=[("Jet fuel (PPI)", LINE_A), ("Airline fares (CPI)", LINE_B)])
    ax = f.add_axes([0.07, 0.10, 0.80, top - 0.12])
    xs = [xpos(m) for m in months]
    rows = []
    for ys, color, code, lab in ((list(jet), LINE_A, "WPU" + JET, "Jet fuel (PPI)"),
                                 (fares, LINE_B, "CUUR0000SETG01", "Airline fares (CPI)")):
        ax.plot(xs, ys, color=color, lw=2)
        ax.scatter([xs[-1]], [ys[-1]], s=36, color=color, zorder=4)
        ax.text(xs[-1] + 0.12, ys[-1], f"{ys[-1]:+.1f}%", color=INK, fontsize=12, fontweight="bold", va="center")
        rows += [(code, lab, m, round(v, 4)) for m, v in zip(months, ys) if v == v]
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.set_ylim(-110, 210)
    ticks = list(range(-100, 201, 50))
    ax.set_yticks(ticks)
    ax.set_yticklabels([f"{t:+d}%" if t else "0%" for t in ticks])
    ax.grid(axis="y", color=GRID, lw=0.6)
    year_axis(ax, months)
    finish(f, ax, name, rows, ["series", "item", "month", "yoy_pct"],
           source="Data 4 The People  ·  Source: BLS Producer Price Index (jet fuel) and Consumer Price Index "
                  "(airline fares, CPI-U, U.S. city average), both not seasonally adjusted")


SP_LAG = 1   # months: BLS holds a portfolio's assets fixed from the start of the period


def shift_month(ym, k):
    y, m = map(int, ym.split("-"))
    n = y * 12 + m - 1 - k
    return f"{n // 12}-{n % 12 + 1:02d}"


def portfolio_sp(items, name):
    """Portfolio management (PPI) against the S&P 500's 12-month change, lagged SP_LAG months."""
    months = sorted(items.month.unique())
    pm = list(items[items.code == PORTFOLIO].set_index("month").reindex(months).yoy)
    sp = json.loads((RAW / "sp500_month_end.json").read_text())
    spy = []
    for m in months:
        a = shift_month(m, SP_LAG)
        spy.append((sp[a] / sp[shift_month(a, 12)] - 1) * 100)
    n = len(months)
    mp, ms = sum(pm) / n, sum(spy) / n
    corr = (sum((a - mp) * (b - ms) for a, b in zip(pm, spy))
            / (sum((a - mp) ** 2 for a in pm) * sum((b - ms) ** 2 for b in spy)) ** 0.5)
    f, top = fig("Portfolio management fees and the stock market, 12-month change",
                 f"{month_label(months[0])} to {month_label(MONTH)}. The blue line is the S&P 500's 12-month change to the end of the\n"
                 "month before. BLS holds the assets fixed from the start of the period and updates them by the rate of\n"
                 "return; a one-month shift matches best. "
                 "June to September 2026 PPI figures are preliminary.",
                 h=7.5, legend=[("Portfolio management (PPI)", LINE_A), ("S&P 500, one month earlier", LINE_B)])
    ax = f.add_axes([0.07, 0.10, 0.80, top - 0.12])
    xs = [xpos(m) for m in months]
    for ys, color in ((pm, LINE_A), (spy, LINE_B)):
        ax.plot(xs, ys, color=color, lw=2)
        ax.scatter([xs[-1]], [ys[-1]], s=36, color=color, zorder=4)
    off = 1.2 if pm[-1] > spy[-1] else -1.2
    ax.text(xs[-1] + 0.12, pm[-1] + off, f"{pm[-1]:+.1f}%", color=INK, fontsize=12, fontweight="bold", va="center")
    ax.text(xs[-1] + 0.12, spy[-1] - off, f"{spy[-1]:+.1f}%", color=INK, fontsize=12, fontweight="bold", va="center")
    ax.axhline(0, color=MUTED, lw=0.8)
    lo, hi = min(pm + spy), max(pm + spy)
    lo_t, hi_t = int(lo // 10) * 10, (int(hi // 10) + 1) * 10
    ax.set_ylim(lo_t - 2, hi_t + 2)
    ticks = list(range(lo_t, hi_t + 1, 10))
    ax.set_yticks(ticks)
    ax.set_yticklabels([f"{t:+d}%" if t else "0%" for t in ticks])
    ax.grid(axis="y", color=GRID, lw=0.6)
    year_axis(ax, months)
    rows = [(m, round(a, 4), shift_month(m, SP_LAG), round(b, 4)) for m, a, b in zip(months, pm, spy)]
    rows.append(("correlation", round(corr, 4), "", ""))
    finish(f, ax, name, rows, ["month", "portfolio_mgmt_yoy_pct", "sp500_month", "sp500_yoy_pct"],
           source="Data 4 The People  ·  Source: BLS Producer Price Index (portfolio management, not seasonally adjusted); "
                  "S&P 500 month-end closes, S&P Dow Jones Indices via FRED and Yahoo Finance")


def main():
    items = pd.read_csv(PROCESSED / "monthly_items.csv", dtype={"code": str, "old_code": str})
    summary = pd.read_csv(PROCESSED / "monthly_summary.csv")
    headline(items, summary, "01-headline.png")
    waterfall(items, summary, "02-waterfall.png")
    first = month_label(sorted(items.month.unique())[0])
    trade(items, "04-trade-margins.png")
    portfolio_sp(items, "05-portfolio.png")
    trucking("06-trucking.png")
    jet_cpi(items, "03-jet-fuel.png")


if __name__ == "__main__":
    main()
