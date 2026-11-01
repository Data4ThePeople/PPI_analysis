"""How unusual was each month's item-level inflation?

For every final demand leaf with its own index, compares each month's price
change with that item's own history: above average + 1 SD, above average + 2 SD,
and in the top 10% of its months. Results are shares of items and shares of
weight, January 2014 to the latest month. Method in DATASETS.md, "Item breadth".
Writes charts/<month>-breadth/numbers/.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from chain import Inputs
from common import PROCESSED, ROOT, TARGET, month_add

LAST = f"{TARGET[0]}-{TARGET[1]:02d}"
FIRST = "2014-01"         # first month whose weights (December 2013) we hold
MIN_OBS = 60              # months of history an item needs to be judged
OUT = ROOT / "charts" / f"{LAST}-breadth" / "numbers"


def months(a=FIRST, b=LAST):
    out = [a]
    while out[-1] != b:
        out.append(month_add(out[-1], 1))
    return out


def wide(inp):
    """Index levels for every leaf ever in a tree, one column per weight-file code."""
    codes = {c for y in range(2013, 2026) for c in inp.tree(y)["ri"]}
    data = {c: inp.series(c) for c in codes if inp.series(c)}
    all_m = months("2012-01")
    return pd.DataFrame(data).reindex(all_m).astype(float)


def weights(inp, lv, t, lag):
    """Leaf weights rolled from the December before t to month `lag`, BLS's formula."""
    yn = int(t[:4]) - 1
    dn = f"{yn}-12"
    fd = inp.series("FD4")
    rel = fd[lag] / fd[dn]
    out = {}
    for c, r in inp.tree(yn)["ri"].items():
        roll = None
        if c in lv and pd.notna(lv.at[dn, c]) and pd.notna(lv.at[lag, c]):
            roll = lv.at[lag, c] / lv.at[dn, c]
        out[c] = r * (roll if roll is not None else 1.0) / rel
    return out


def flags(ch, base_mask, deseason=False):
    """Long table inputs: z-score and top-10% share for every item-month."""
    use = ch[base_mask]
    if deseason:
        cal = ch.index.str[5:]
        ch = ch - use.groupby(use.index.str[5:]).mean().reindex(cal).set_axis(ch.index)
        use = ch[base_mask]
    mean, sd, n = use.mean(), use.std(ddof=1), use.notna().sum()
    z = (ch - mean) / sd
    z = z.loc[:, (n >= MIN_OBS) & (sd > 0)]
    # Share of the item's baseline months at or above this month's change. Ties
    # count against the month, so a run of zero changes never reaches the top 10%.
    u = use[z.columns].values
    arr = ch[z.columns].values
    share = np.full(arr.shape, np.nan)
    for j in range(arr.shape[1]):
        col = u[:, j]; col = np.sort(col[~np.isnan(col)])
        ok = ~np.isnan(arr[:, j])
        share[ok, j] = (len(col) - np.searchsorted(col, arr[ok, j], side="left")) / len(col)
    return z, pd.DataFrame(share, index=ch.index, columns=z.columns)


def summarize(inp, lv, z, top):
    rows, det = [], []
    for t in months():
        lag = month_add(t, -1)            # the weight going into a monthly change
        w = weights(inp, lv, t, lag)
        tot = sum(w.values())
        rec = {"month": t, "items": 0, "w_judged": 0.0, "w_all": tot}
        for k in ("sd1", "sd2", "top10", "dn1", "dn2"):
            rec[k + "_n"] = 0; rec[k + "_w"] = 0.0
        for c, wt in w.items():
            if c not in z.columns or pd.isna(z.at[t, c]):
                continue
            zz, tt = z.at[t, c], top.at[t, c]
            rec["items"] += 1; rec["w_judged"] += wt
            for k, hit in (("sd1", zz > 1), ("sd2", zz > 2), ("top10", tt <= .10),
                           ("dn1", zz < -1), ("dn2", zz < -2)):
                rec[k + "_n"] += hit; rec[k + "_w"] += wt * hit
            det.append((t, c, wt, zz, tt))
        for k in ("sd1", "sd2", "top10", "dn1", "dn2"):
            rec[k + "_pct_n"] = 100 * rec[k + "_n"] / rec["items"]
            rec[k + "_pct_w"] = 100 * rec[k + "_w"] / rec["w_judged"]
        rec["coverage"] = 100 * rec["w_judged"] / tot
        rows.append(rec)
    return pd.DataFrame(rows).set_index("month"), pd.DataFrame(det, columns=["month", "code", "w", "z", "top"])


def main():
    inp = Inputs()
    lv = wide(inp)
    OUT.mkdir(parents=True, exist_ok=True)
    mom = (lv / lv.shift(1) - 1) * 100
    yoy = (lv / lv.shift(12) - 1) * 100
    mom = mom.iloc[1:]; yoy = yoy.iloc[12:]
    runs = {
        "monthly": (mom, mom.index >= "2012-02", False),
        "monthly_seasonal": (mom, mom.index >= "2012-02", True),
        "monthly_pre2020": (mom, mom.index <= "2019-12", False),
        "monthly_from2021": (mom, mom.index >= "2021-07", False),
        "yoy": (yoy, yoy.index >= "2013-01", False),
        "yoy_pre2020": (yoy, yoy.index <= "2019-12", False),
    }
    res = {}
    for name, (ch, mask, ds) in runs.items():
        z, top = flags(ch, mask, ds)
        s, det = summarize(inp, lv, z, top)
        s.round(4).to_csv(OUT / f"{name}.csv")
        res[name] = (s, det)
        if name in ("monthly", "yoy"):
            d = det[det.month == LAST].copy()
            d["name"] = [ (inp.tree(int(LAST[:4])-1)["nodes"][c].name) for c in d.code]
            d["change"] = [ch.at[LAST, c] for c in d.code]
            d["avg"] = [ch.loc[mask, c].mean() for c in d.code]
            d["sd"] = [ch.loc[mask, c].std(ddof=1) for c in d.code]
            d.sort_values("z", ascending=False).round(4).to_csv(OUT / f"{name}_{LAST}_items.csv", index=False)
    return res, lv, mom, yoy


if __name__ == "__main__":
    res, lv, mom, yoy = main()
    pd.set_option("display.width", 220); pd.set_option("display.max_rows", 200); pd.set_option("display.max_columns", 30)
    cols = ["items", "coverage", "sd1_n", "sd1_pct_n", "sd1_pct_w", "sd2_n", "sd2_pct_n", "sd2_pct_w", "top10_n", "top10_pct_n", "top10_pct_w"]
    for name, (s, det) in res.items():
        print("\n==", name, "avg", s[["sd1_pct_n", "sd1_pct_w", "sd2_pct_n", "sd2_pct_w", "top10_pct_n", "top10_pct_w"]].mean().round(1).to_dict())
        print(s.loc[LAST, cols].round(1).to_dict())
        for k in ["sd1_pct_n", "sd1_pct_w", "sd2_pct_n", "sd2_pct_w", "top10_pct_n", "top10_pct_w"]:
            r = s[k].rank(ascending=False, method="min")
            top = s[k].sort_values(ascending=False).head(4)
            print(f"  {k}: Sep rank {int(r[LAST])}/{len(s)}; top: " + ", ".join(f"{m} {v:.1f}" for m, v in top.items()))
    print(res["monthly"][0].loc["2021-01":"2022-12", cols].round(1))
    print(res["monthly"][0].loc["2025-10":, cols].round(1))
