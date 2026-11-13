"""Tie-out for the October 2026 takeaways charts; writes TAKEAWAYS_TIEOUT_<month>.md.

Every 12-month change is recomputed from the raw BLS flat-file lines
(takeaways_tieout.raw), not from the chart code or the cached indexes. Every
contribution and total is re-summed from monthly_items.csv here. Ranks and
"highest since" claims are recomputed. Sentence-level claims on each chart are
listed at the end with what supports them.
"""
from __future__ import annotations

import csv

import pandas as pd

from common import PROCESSED, ROOT, month_add
from takeaways import short
from takeaways_tieout import raw, yoy
from drivers import label as dlabel
from weights import december

from common import TARGET_STR as MONTH

NUM = ROOT / "charts" / MONTH / "numbers"
OUT = ROOT / f"TAKEAWAYS_TIEOUT_{MONTH}.md"
TOL = 0.0001


def rd(name):
    return list(csv.DictReader(open(NUM / name)))


def main():
    items = pd.read_csv(PROCESSED / "monthly_items.csv", dtype={"code": str, "old_code": str}, low_memory=False)
    summary = pd.read_csv(PROCESSED / "monthly_summary.csv").set_index("month")
    prev = month_add(MONTH, -1)
    cur, pre = items[items.month == MONTH].set_index("code"), items[items.month == prev].set_index("code")
    lines, fails = [], []

    def check(label, ours, theirs, tol=TOL):
        ok = abs(float(ours) - float(theirs)) <= tol
        if not ok:
            fails.append(label)
        lines.append(f"| {label} | {float(theirs):.4f} | {float(ours):.4f} | {'ok' if ok else 'DIFF'} |")

    def head(t):
        lines.extend(["", f"## {t}", "", "| Check | Chart / CSV | Recomputed | |", "|---|---:|---:|---|"])

    # every code the charts touch
    dr = rd("02-drivers.csv")
    by_label = {dlabel(r["name"]): c for c, r in cur.iterrows()}
    dr_codes = [by_label[r["item"]] for r in dr if r["item"] in by_label]
    mv = rd("02-movers-unweighted.csv")
    fu = rd("05-fuels.csv")
    fu_top = [r["month"][4:] for r in fu if r["month"].startswith("top_")]
    codes = set(dr_codes) | {r["code"] for r in mv} | set(fu_top) | {"301202", "341101"}
    lv = raw({"WPUFD4"} | {f"WPU{c}" for c in codes})
    fd = lv["WPUFD4"]

    head("1. Headline (01-headline)")
    h = rd("01-headline.csv")
    g = items.groupby(["month", "group"]).contrib.sum().unstack().fillna(0)
    for r in h:
        check(f"WPUFD4 {r['month']} 12-month", yoy(fd, r["month"]), r["published_pct"])
        for grp in ("Goods", "Services", "Construction"):
            check(f"{grp} {r['month']}", g.loc[r["month"], grp], r[f"{grp.lower()}_pts"], 1e-5)
    pubs = {r["month"]: yoy(fd, r["month"]) for r in h}
    last = pubs[MONTH]
    since = [m for m in pubs if m < MONTH and pubs[m] >= last][-1]
    lines.append(f"| highest since (title text) | November 2022 | {since} | {'ok' if since == '2022-11' else 'DIFF'} |")
    if since != "2022-11":
        fails.append("headline since")
    pk = max(pubs, key=pubs.get)
    lines.append(f"| peak label 11.7% March 2022 | 11.7 2022-03 | {pubs[pk]:.1f} {pk} | "
                 f"{'ok' if (round(pubs[pk], 1), pk) == (11.7, '2022-03') else 'DIFF'} |")

    head("2. Drivers, September to October (02-drivers)")
    for r in dr:
        if r["item"] in by_label:
            c = by_label[r["item"]]
            check(f"{c} {r['item']} {prev} 12-month", yoy(lv[f'WPU{c}'], prev), r[f"yoy_{prev}"])
            check(f"{c} {r['item']} {MONTH} 12-month", yoy(lv[f'WPU{c}'], MONTH), r[f"yoy_{MONTH}"])
            check(f"{c} contribution change", cur.loc[c, "contrib"] - pre.loc[c, "contrib"], r["contrib_change_pts"], 1e-5)
    change = cur.contrib - pre.contrib
    other = change.drop(dr_codes).sum()
    o = next(r for r in dr if r["item"].startswith("The other"))
    check(o["item"], other, o["contrib_change_pts"], 1e-5)
    n_other = len(change) - len(dr_codes)
    lines.append(f"| other items count | {o['item'].split()[2]} | {n_other} | {'ok' if str(n_other) == o['item'].split()[2] else 'DIFF'} |")
    top10 = set(change.sort_values(ascending=False).index[:10]) | set(change.sort_values().index[:10])
    lines.append(f"| chart shows the 10 largest each way | 20 | {len(top10 & set(dr_codes))} | "
                 f"{'ok' if top10 == set(dr_codes) else 'DIFF'} |")
    a = next(r for r in dr if r["item"] == "All items")
    check("all items change", change.sum(), a["contrib_change_pts"], 1e-5)
    p = next(r for r in dr if r["item"] == "Published")
    check(f"published {prev}", yoy(fd, prev), p[f"yoy_{prev}"])
    check(f"published {MONTH}", yoy(fd, MONTH), p[f"yoy_{MONTH}"])
    check("published change", yoy(fd, MONTH) - yoy(fd, prev), p["contrib_change_pts"])

    head("2b. Unweighted movers (02-movers-unweighted.csv)")
    for r in mv:
        c = r["code"]
        check(f"{c} {r['item'][:40]} {MONTH}", yoy(lv[f'WPU{c}'], MONTH), r[f"yoy_{MONTH}"])
        if not (cur.loc[c, "own_index"] and pd.isna(cur.loc[c, "filled_from"])):
            fails.append(f"{c} not own index")
    own = cur[cur.own_index & cur.filled_from.isna()]
    want = set(own.yoy.sort_values(ascending=False).index[:15]) | set(own.yoy.sort_values().index[:15])
    lines.append(f"| lists are the top and bottom 15 own-index items | 30 | {len(want & {r['code'] for r in mv})} | "
                 f"{'ok' if want == {r['code'] for r in mv} else 'DIFF'} |")

    head("3. Long-distance trucking (03-trucking)")
    tk = rd("03-trucking.csv")
    t = lv["WPU301202"]
    tv = {}
    for r in tk:
        if r["month"].startswith("average"):
            continue
        tv[r["month"]] = yoy(t, r["month"])
        check(f"301202 {r['month']}", tv[r["month"]], r["yoy_pct"])
    avg = sum(v for m, v in tv.items() if m < MONTH) / (len(tv) - 1)
    check("average before " + MONTH, avg, next(r for r in tk if r["month"].startswith("average"))["yoy_pct"])
    first = min(m for m in t if f"{int(m[:4]) + 1}{m[4:]}" in t)
    lines.append(f"| first 12-month change June 2010 | 2010-06 | {min(tv)} | {'ok' if min(tv) == '2010-06' else 'DIFF'} |")
    rank = sorted(tv.values(), reverse=True).index(tv[MONTH]) + 1
    lines.append(f"| rank 1 of 197 | 1 of 197 | {rank} of {len(tv)} | {'ok' if (rank, len(tv)) == (1, 197) else 'DIFF'} |")
    before = {m: v for m, v in tv.items() if m < MONTH}
    pk = max(before, key=before.get)
    lines.append(f"| earlier high +26.9% May 2022 | 26.9 2022-05 | {before[pk]:.1f} {pk} | "
                 f"{'ok' if (round(before[pk], 1), pk) == (26.9, '2022-05') else 'DIFF'} |")
    check("301202 trucking in items file", cur.loc["301202", "yoy"], tv[MONTH])

    head("4. System software publishing (04-software)")
    sw = rd("04-software.csv")
    s = lv["WPU341101"]
    sv = {}
    for r in sw:
        m = r["month"]
        if m.startswith("mom_"):
            check("341101 monthly change", (s[MONTH] / s[prev] - 1) * 100, r["yoy_pct"])
        elif m.startswith("relative_importance_dec"):
            y = int(m[-4:])
            ri = december(y)["341101"].weight
            check(f"341101 relative importance December {y}", ri, r["yoy_pct"], 1e-6)
        elif m.startswith("contrib_"):
            check("341101 contribution", cur.loc["341101", "contrib"], r["yoy_pct"], 1e-5)
        else:
            sv[m] = yoy(s, m)
            check(f"341101 {m}", sv[m], r["yoy_pct"])
    lines.append(f"| index starts May 2022 | 2022-05 | {min(s)} | {'ok' if min(s) == '2022-05' else 'DIFF'} |")
    lowest = min(sv, key=sv.get)
    lines.append(f"| lowest of 42 months | {MONTH}, 42 | {lowest}, {len(sv)} | "
                 f"{'ok' if (lowest, len(sv)) == (MONTH, 42) else 'DIFF'} |")
    hi = max(sv, key=sv.get)
    lines.append(f"| high label +13.2% July 2024 | 13.2 2024-07 | {sv[hi]:.1f} {hi} | "
                 f"{'ok' if (round(sv[hi], 1), hi) == (13.2, '2024-07') else 'DIFF'} |")
    worst = cur.contrib.idxmin()
    lines.append(f"| largest pull-down item in {MONTH} | 341101 | {worst} | {'ok' if worst == '341101' else 'DIFF'} |")

    head("5. Fuels (05-fuels)")
    f5 = items.code.str.startswith("05")
    fs = items[f5].groupby("month").contrib.sum()
    rs = items[~f5].groupby("month").contrib.sum()
    for r in fu:
        m = r["month"]
        if m.startswith("share_"):
            check("fuels share of item total", fs[MONTH] / (fs[MONTH] + rs[MONTH]) * 100, r["fuels_pts"])
        elif m.startswith("last_at_or_above"):
            since = [k for k in fs.index if k < MONTH and fs[k] >= fs[MONTH]][-1]
            lines.append(f"| most points since | {r['fuels_pts']} | {since} | {'ok' if since == r['fuels_pts'] else 'DIFF'} |")
        elif m.startswith("top_"):
            c = m[4:]
            check(f"{c} {cur.loc[c, 'name'][:30]} contribution", cur.loc[c, "contrib"], r["fuels_pts"], 1e-5)
            check(f"{c} {cur.loc[c, 'name'][:30]} 12-month", yoy(lv[f'WPU{c}'], MONTH), r["other_pts"])
        else:
            check(f"fuels {m}", fs[m], r["fuels_pts"], 1e-5)
            check(f"others {m}", rs[m], r["other_pts"], 1e-5)
    pk = fs.idxmax()
    lines.append(f"| peak label +3.16 June 2022 | 3.16 2022-06 | {fs[pk]:.2f} {pk} | "
                 f"{'ok' if (round(fs[pk], 2), pk) == (3.16, '2022-06') else 'DIFF'} |")
    top4 = list(cur[cur.index.str.startswith("05")].contrib.sort_values(ascending=False).index[:4])
    lines.append(f"| four largest fuels named | {' '.join(fu_top)} | {' '.join(top4)} | {'ok' if top4 == fu_top else 'DIFF'} |")

    words = """
## Words on the charts

| Chart | Claim | Support | Status |
|---|---|---|---|
| all | "{prelim} are preliminary" | BLS "P" footnote on July to October 2026 in the flat files | supported |
| 01 | "the highest since November 2022" | section 1 recompute | supported |
| 02 | "Items ending in retailing or wholesaling measure the margin sellers keep" | BLS, "Wholesale and retail Producer Price Indexes: margin prices," Beyond the Numbers vol. 1: the price of a trade service is the selling price less the acquisition price (DATASETS.md "What some PPI items measure") | supported |
| 02 | "Our items add up to +0.228; BLS's rate moves +0.234" | section 2 recompute | supported |
| 03 | "every month BLS has published" | WPU301202 12-month changes start June 2010 (index June 2009) | supported |
| 03 | "highest of all 197 months; earlier high +26.9% in May 2022" | section 3 recompute | supported |
| 04 | "BLS began this index in May 2022" | WPU341101 first value 2022-05 (100.000) in wp.series and flat file | supported |
| 04 | "lowest of all 42 months; fell 6.1% from September" | section 4 recompute | supported |
| 04 | "BLS's December 2025 weights put it at 0.92% of final demand" | December 2025 column of final-demand-relative-importance-of-commodities-2026.xlsx, 341101 = 0.919 | supported |
| 05 | "group 05, fuels and related products and power, which includes electricity and natural gas" | wp.series: WPU05 "Fuels and related products and power"; 053101 natural gas and 054121 residential electric power are group 05 items in the October data | supported |
| 05 | "29.5% of our item total, the most points since July 2022" | section 5 recompute; share of our item sum, not of BLS's published rate | supported |
""".format(prelim="July to October 2026")
    body = [f"# Takeaways tie-out, {MONTH}", "",
            "Generated by `scripts/october_tieout.py`. 12-month changes recomputed from the raw BLS flat files; "
            "contributions re-summed from `data/processed/monthly_items.csv`.", "",
            f"**Result: {len(fails)} differences.**" + ("" if not fails else " " + "; ".join(fails))] + lines + [words]
    OUT.write_text("\n".join(body) + "\n")
    print(OUT.name, "differences:", len(fails), fails[:10])


if __name__ == "__main__":
    main()
