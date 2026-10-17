"""Item contributions for every month from October 2016 to the release month.

Every month is computed, checked, and goes to the page. Months that miss the
strict tie-out rules stay in and are flagged, with the reason, so the page
shows its work (Eric, October 17, 2026: the tool is educational).
Writes:
- data/processed/monthly.json: the passing months' items, for the animated page;
- data/processed/monthly_summary.csv: one row per month with the published
  12-month change, what the items add up to, the gap, the filled weight, and
  whether the month passes;
- data/processed/monthly_items.csv: one row per month and item, for checking.

A month passes the strict tie-out when (rules fixed before looking at the results):
1. both index values in its 12-month change (FD4 at T and at B) were published
   to three decimals. BLS published one decimal before July 2021 and did not
   revise that history, so rounding alone can move a 12-month change by up to
   about 0.09 points;
2. the items add up to the published change within 0.05 points, half of the
   0.1 precision BLS publishes 12-month changes at;
3. items without their own index carry 10% of weight or less.
"""
from __future__ import annotations

import csv
import json

from chain import FILL, Inputs, compute_month
from common import PROCESSED, START, TARGET, month_add

THREE_DECIMALS_FROM = "2021-07"
CHECKS = {"max_gap_pts": 0.05, "max_filled_share": 10.0,
          "three_decimals_from": THREE_DECIMALS_FROM, "fill": FILL}


def month_list():
    t, end = f"{START[0]}-{START[1]:02d}", f"{TARGET[0]}-{TARGET[1]:02d}"
    out = []
    while t <= end:
        out.append(t)
        t = month_add(t, 1)
    return out


def main():
    inp = Inputs()
    summary, item_rows, months = [], [], {}
    for t in month_list():
        r = compute_month(inp, t)
        items = r["items"]
        gap = r["sum"] - r["published"]
        filled = sum(i["w_base"] for i in items if not i["own_index"])
        precise = r["base"] >= THREE_DECIMALS_FROM
        reasons = []
        if not precise:
            reasons.append("one-decimal index at base month")
        if abs(gap) > CHECKS["max_gap_pts"]:
            reasons.append("gap over 0.05")
        if filled > CHECKS["max_filled_share"]:
            reasons.append("filled weight over 10%")
        ok = not reasons
        summary.append({
            "month": t, "status": "pass" if ok else "flagged",
            "published": round(r["published"], 4), "items": round(r["sum"], 4),
            "gap": round(gap, 4), "published_1dp": round(r["published"], 1),
            "fd_T": r["fd"]["T"], "fd_B": r["fd"]["B"], "preliminary": r["fd_note"] == "P",
            "items_n": len(items), "filled_items": sum(1 for i in items if not i["own_index"]),
            "filled_share": round(filled, 3),
            "weights": f"Dec {r['dec_prior'][:4]} rolled to {r['base']}, then Dec {r['dec_new'][:4]}",
            "why_out": "; ".join(reasons),
        })
        months[t] = {"base": r["base"], "published": r["published"], "sum": r["sum"],
                     "preliminary": r["fd_note"] == "P", "pass": ok, "why_out": "; ".join(reasons),
                     "precise": precise, "fd": r["fd"],
                     "items": [{k: i[k] for k in ("code", "name", "group", "major", "own_index",
                                                  "filled_from", "yoy", "contrib", "w_base")}
                               for i in items]}
        for i in items:
            item_rows.append({"month": t, "code": i["code"], "old_code": i["old_code"] or "",
                              "name": i["name"], "group": i["group"], "own_index": i["own_index"],
                              "filled_from": i["filled_from"] or "",
                              "weight_base": round(i["w_base"], 5),
                              "yoy": None if i["yoy"] is None else round(i["yoy"], 4),
                              "contrib_first": round(i["c1"], 6), "contrib_second": round(i["c2"], 6),
                              "contrib": round(i["contrib"], 6)})

    order = [s["month"] for s in summary]
    passing = [s["month"] for s in summary if s["status"] == "pass"]

    PROCESSED.mkdir(parents=True, exist_ok=True)
    (PROCESSED / "monthly.json").write_text(json.dumps(
        {"checks": CHECKS, "order": order, "months": months}))
    with open(PROCESSED / "monthly_summary.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(summary[0]))
        w.writeheader()
        w.writerows(summary)
    with open(PROCESSED / "monthly_items.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(item_rows[0]))
        w.writeheader()
        w.writerows(item_rows)
    print(f"{len(summary)} months computed and shown; {len(passing)} pass the strict tie-out "
          f"({passing[0]} to {passing[-1]})")


if __name__ == "__main__":
    main()
