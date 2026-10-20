"""CPI airline fares (CUUR0000SETG01, U.S. city average, not seasonally adjusted) from the BLS API.

Used only for the jet fuel chart in the September 2026 takeaways. Writes
data/raw/cpi_airline_fares.json as {"YYYY-MM": index}. BLS published no CPI
for October 2025.
"""
from __future__ import annotations

import json
import os
import urllib.request

from common import RAW, USER_AGENT

SERIES = "CUUR0000SETG01"
OUT = RAW / "cpi_airline_fares.json"


def main():
    body = json.dumps({"seriesid": [SERIES], "startyear": "2015", "endyear": "2026",
                       "registrationkey": os.environ["BLS_API_KEY"]}).encode()
    req = urllib.request.Request("https://api.bls.gov/publicAPI/v2/timeseries/data/", data=body,
                                 headers={"Content-Type": "application/json", "User-Agent": USER_AGENT})
    d = json.load(urllib.request.urlopen(req, timeout=60))
    if d["status"] != "REQUEST_SUCCEEDED":
        raise SystemExit(d.get("message"))
    out = {}
    for r in d["Results"]["series"][0]["data"]:
        if r["period"].startswith("M") and r["period"] != "M13" and r["value"] not in ("-", ""):
            out[f"{r['year']}-{r['period'][1:]}"] = float(r["value"])
    OUT.write_text(json.dumps(dict(sorted(out.items())), indent=0))
    print("wrote", OUT.name, len(out), "months,", min(out), "to", max(out))


if __name__ == "__main__":
    main()
