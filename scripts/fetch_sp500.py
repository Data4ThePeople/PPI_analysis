"""S&P 500 month-end closes, January 2015 on, for the portfolio management chart.

FRED's SP500 series (S&P Dow Jones Indices) only reaches back ten years, to
October 2016, so the daily closes come from Yahoo Finance (^GSPC) and every
month-end close in FRED's window is checked against FRED. Writes
data/raw/sp500_month_end.json as {"YYYY-MM": close}.
"""
from __future__ import annotations

import csv
import io
import json
import urllib.request
from datetime import datetime, timedelta, timezone

from common import RAW, USER_AGENT

YAHOO = ("https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?interval=1d"
         "&period1=1420070400&period2={end}")
FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=SP500&cosd=2015-01-01"
OUT = RAW / "sp500_month_end.json"


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": USER_AGENT}), timeout=60).read()


def month_end(daily: dict[str, float]) -> dict[str, float]:
    out = {}
    for day in sorted(daily):
        out[day[:7]] = daily[day]                  # the last trading day's close wins
    return out


def main():
    r = json.loads(get(YAHOO.format(end=int(datetime.now(timezone.utc).timestamp()))))["chart"]["result"][0]
    tz = timedelta(seconds=r["meta"]["gmtoffset"])
    daily = {(datetime.fromtimestamp(t, timezone.utc) + tz).strftime("%Y-%m-%d"): c
             for t, c in zip(r["timestamp"], r["indicators"]["quote"][0]["close"]) if c is not None}
    fred = {row["observation_date"]: float(row["SP500"])
            for row in csv.DictReader(io.StringIO(get(FRED).decode())) if row["SP500"] not in ("", ".")}
    ym, fm = month_end(daily), month_end(fred)
    first_full = min(fm)                          # FRED's first month is partial; compare from the next
    checked = [m for m in fm if m > first_full and m in ym]
    worst = max(abs(ym[m] - fm[m]) for m in checked)
    if worst > 0.01:
        raise SystemExit(f"Yahoo and FRED month-end closes differ by up to {worst:.4f}")
    OUT.write_text(json.dumps({m: round(v, 2) for m, v in sorted(ym.items())}, indent=0))
    print(f"wrote {OUT.name}: {len(ym)} months, {min(ym)} to {max(ym)}; "
          f"{len(checked)} month-ends match FRED within {worst:.4f}")


if __name__ == "__main__":
    main()
