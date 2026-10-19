"""Tie-out for the September 2026 takeaways charts; writes TAKEAWAYS_TIEOUT.md.

Checks, each recomputed here rather than read from the chart code:
1. Every 12-month price change drawn or labeled (headline and items), recomputed
   from the raw BLS flat-file lines in data/raw/wp, not the cached indexes.json.
2. Every contribution drawn, against monthly_items.csv, and every total
   (waterfall, goods/services/construction, trade items) re-summed.
3. The numbers the text will lean on: the headline and its rank, the fuels
   share, the jet fuel and portfolio management comparisons.
"""
from __future__ import annotations

import csv

import pandas as pd

from common import PROCESSED, ROOT, TARGET, WP

MONTH = f"{TARGET[0]}-{TARGET[1]:02d}"
NUM = ROOT / "charts" / MONTH / "numbers"
TOL_YOY, TOL_PTS = 0.0001, 0.000001


def raw(series: set[str]) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {s: {} for s in series}
    for p in sorted(WP.glob("wp.data.*")):
        for line in open(p):
            sid = line.split("\t", 1)[0].strip()
            if sid in out:
                f = line.rstrip("\n").split("\t")
                if f[2].startswith("M") and f[2] != "M13":
                    m, v = f"{f[1]}-{f[2][1:]}", float(f[3])
                    if m in out[sid] and out[sid][m] != v:
                        raise SystemExit(f"{sid} {m}: two values in the flat files")
                    out[sid][m] = v
    return out


def yoy(levels: dict[str, float], m: str) -> float:
    y, mo = int(m[:4]), m[5:]
    return (levels[m] / levels[f"{y - 1}-{mo}"] - 1) * 100


def main():
    items = pd.read_csv(PROCESSED / "monthly_items.csv", dtype={"code": str, "old_code": str})
    summary = pd.read_csv(PROCESSED / "monthly_summary.csv").set_index("month")
    cur = items[items.month == MONTH].set_index("code")
    lines, fails = [], []

    def check(label, ours, theirs, tol):
        ok = abs(ours - theirs) <= tol
        if not ok:
            fails.append(label)
        lines.append(f"| {label} | {theirs:.4f} | {ours:.4f} | {'ok' if ok else 'DIFF'} |")

    wf = list(csv.DictReader(open(NUM / "02-waterfall.csv")))
    tr = list(csv.DictReader(open(NUM / "04-trade-margins.csv")))
    lines_codes = {r["code"] for f in ("03-jet-fuel.csv", "05-portfolio.csv") for r in csv.DictReader(open(NUM / f))}
    name_to_code = {}
    from takeaways import short
    for code, r in cur.iterrows():
        name_to_code[short(r["name"])] = code
    wf_codes = [name_to_code[r["step"]] for r in wf if r["step"] in name_to_code]
    tr_codes = [r["code"] for r in tr if r["code"] != "all"]
    codes = sorted(set(wf_codes) | set(tr_codes) | lines_codes)
    lv = raw({"WPUFD4"} | {f"WPU{c}" for c in codes})

    lines += ["## 1. 12-month changes from the raw flat files", "",
              "| Series | Chart / CSV | Raw recompute | |", "|---|---:|---:|---|"]
    h = list(csv.DictReader(open(NUM / "01-headline.csv")))
    for r in h:
        check(f"WPUFD4 {r['month']}", yoy(lv["WPUFD4"], r["month"]), float(r["published_pct"]), 0.0001)
    for c in codes:
        check(f"{c} {cur.loc[c, 'name'][:45]} {MONTH}", yoy(lv[f"WPU{c}"], MONTH), cur.loc[c, "yoy"], TOL_YOY)
    for f in ("03-jet-fuel.csv", "05-portfolio.csv"):
        for r in csv.DictReader(open(NUM / f)):
            check(f"{r['code']} {r['month']}", yoy(lv[f"WPU{r['code']}"], r["month"]), float(r["yoy_pct"]), TOL_YOY)
    n_hist = len(lines)

    lines += ["", "## 2. Contributions and totals", "", "| Check | Chart / CSV | Recompute | |", "|---|---:|---:|---|"]
    for r in wf:
        if r["step"] in name_to_code:
            check(f"waterfall {r['step']}", cur.loc[name_to_code[r["step"]], "contrib"], float(r["contrib_pts"]), TOL_PTS)
    up = cur.sort_values("contrib", ascending=False).head(8).index
    dn = cur.sort_values("contrib").head(4).index
    rest = cur.drop(up).drop(dn)
    other = next(r for r in wf if r["step"].startswith("The other"))
    check(f"waterfall {other['step']}", rest.contrib.sum(), float(other["contrib_pts"]), TOL_PTS)
    check("waterfall all items", cur.contrib.sum(), float(wf[-1]["contrib_pts"]), TOL_PTS)
    g = cur.groupby("group").contrib.sum()
    last = next(r for r in h if r["month"] == MONTH)
    for grp in ("Goods", "Services", "Construction"):
        check(f"{grp} {MONTH}", g[grp], float(last[f"{grp.lower()}_pts"]), TOL_PTS)
    for r in tr:
        if r["code"] == "all":
            t = cur[cur.index.str.match(r"^5[78]")]
            check(f"all {len(t)} trade items", t.contrib.sum(), float(r["contrib_pts"]), TOL_PTS)
        else:
            check(f"trade {r['item'][:45]}", cur.loc[r["code"], "contrib"], float(r["contrib_pts"]), TOL_PTS)

    pub = {m: yoy(lv["WPUFD4"], m) for m in summary.index}
    fuels = cur[cur.index.str.startswith("05")].contrib.sum()
    total = cur.contrib.sum()
    before = [m for m in summary.index if m < MONTH and pub[m] >= pub[MONTH]][-1]
    jet = {m: yoy(lv["WPU057203"], m) for m in summary.index}
    jet_before = [m for m in summary.index if m < MONTH and jet[m] >= jet[MONTH]][-1]
    pm = {m: yoy(lv["WPU402101"], m) for m in summary.index}
    rank = list(cur.sort_values("contrib", ascending=False).index)
    facts = [
        ("PPI final demand, 12-month change, " + MONTH, f"{pub[MONTH]:.2f}%"),
        ("Last month at or above it", before + f" ({pub[before]:.2f}%)"),
        ("February 2026", f"{pub['2026-02']:.2f}%"),
        ("Peak in the window", f"{max(pub, key=pub.get)} ({max(pub.values()):.2f}%)"),
        ("Sum of item contributions", f"{total:.3f} points"),
        ("Fuels and power (codes 05), contribution", f"{fuels:.3f} points, {fuels / total * 100:.1f}% of the item sum"),
        ("Jet fuel 12-month change / contribution", f"{jet[MONTH]:.1f}% / {cur.loc['057203', 'contrib']:.3f} points"),
        ("Jet fuel, last month at or above it", f"{jet_before} ({jet[jet_before]:.1f}%)"),
        ("Airline passenger services", f"{cur.loc['302201', 'yoy']:.1f}% / {cur.loc['302201', 'contrib']:.3f} points"),
        ("Portfolio management", f"{pm[MONTH]:.1f}% / {cur.loc['402101', 'contrib']:.3f} points, rank {rank.index('402101') + 1} of {len(rank)}"),
        ("Portfolio management, highest in the window", f"{max(pm, key=pm.get)} ({max(pm.values()):.1f}%)"),
        ("Preliminary months", ", ".join(m for m in summary.index if summary.loc[m, "preliminary"])),
    ]
    lines += ["", "## 3. Numbers for the text (recomputed from the raw index levels and monthly_items.csv)", "",
              "| Fact | Value |", "|---|---|"] + [f"| {a} | {b} |" for a, b in facts]

    head = [f"# Takeaways tie-out, {MONTH}", "",
            f"Generated by `scripts/takeaways_tieout.py`. {len(fails)} differences.", ""]
    (ROOT / "TAKEAWAYS_TIEOUT.md").write_text("\n".join(head + lines) + "\n")
    print(f"{n_hist} history rows; {len(fails)} differences")
    for a, b in facts:
        print(f"  {a}: {b}")
    for f in fails:
        print("  DIFF", f)


if __name__ == "__main__":
    main()
