"""Build dist/index.html (the PPI scuba diver) from src/template.html and monthly.json.

Injects the payload at the single /*DATA*/{} placeholder, parse-checks the
script, then runs the page in headless Chrome, full and embedded, failing on
any JavaScript error. Nothing is hardcoded in the page: the depth scale, the
size scale and the color bins are fixed here from the data, once, for all
months.
"""
from __future__ import annotations

import json
import math
import os
import re
import subprocess
import tempfile
from datetime import date

from common import DIST, PROCESSED, ROOT

SRC = ROOT / "src"
STEPS = [1, 2, 5, 10, 25]          # color bins on |own 12-month change|, percent

SHORT = {
    "Unleaded regular gasoline": "Gasoline, regular",
    "Unleaded premium gasoline": "Gasoline, premium",
    "Machinery and vehicle wholesaling": "Machinery and vehicle wholesaling",
    "Automobile retailing (Partial)": "Car dealers' margins",
    "Long-distance motor carrying": "Long-distance trucking",
    "Securities brokerage and dealing related services (partial)": "Securities brokerage",
    "Securities brokerage, dealing, and investment advice": "Brokerage and investment advice",
    "Automotive fuels and lubricants retailing": "Fuel retailing margins",
    "Fresh vegetables, except potatoes": "Fresh vegetables",
    "Residential real estate loans (partial)": "Home loans",
    "Beef and veal products, fresh or frozen": "Beef and veal",
    "Health and beauty care retailing, including optical goods": "Health and beauty retailing",
    "Computer hardware, software, and supplies retailing": "Computer retailing",
    "Bundled wired telecommunications access services": "Bundled telecom service",
    "Hardware and building materials and supplies retailing": "Building materials retailing",
    "Other merchandise retailing (partial)": "Other merchandise retailing",
    "Parts and supplies for machinery and equipment wholesaling": "Machinery parts wholesaling",
}


def label(ym):
    y, m = map(int, ym.split("-"))
    return date(y, m, 1).strftime("%B %Y")


def rounding_bound(t, M):
    """Largest change in the 12-month rate that rounding of the two published
    index values can cause: half of the last published digit on each (one
    decimal before July 2021, three from then on)."""
    b = f"{int(t[:4]) - 1}{t[4:]}"
    hT = 0.05 if t < "2021-07" else 0.0005
    hB = 0.05 if b < "2021-07" else 0.0005
    T, B = M["fd"]["T"], M["fd"]["B"]
    return 100 * (hT / B + T * hB / B ** 2)


def encode(m):
    order = m["order"]
    codes, meta = [], {}
    for t in order:
        for i in m["months"][t]["items"]:
            if i["code"] not in meta:
                codes.append(i["code"])
            meta[i["code"]] = i                      # latest name wins
    parents, months = [], {}
    for t in order:
        M = m["months"][t]
        by = {i["code"]: i for i in M["items"]}
        rows, s = [], 0.0
        for c in codes:
            i = by.get(c)
            if i is None:
                rows.append(None)
                continue
            frm = -1
            if not i["own_index"]:
                if i["filled_from"] not in parents:
                    parents.append(i["filled_from"])
                frm = parents.index(i["filled_from"])
            # flags: 1 = own index for only part of the year (rest borrowed);
            # 2 = in final demand only since December; 4 = only through December
            # 8 = the change shown is borrowed (estimated), not the item's own
            flags = ((1 if i["partly_own"] else 0) | (2 if i["span"] == "since December" else 0)
                     | (4 if i["span"] == "through December" else 0)
                     | (8 if i["yoy_source"] in ("borrowed", "partly borrowed") else 0))
            rows.append([None if i["yoy"] is None else round(i["yoy"], 3), round(i["contrib"], 5),
                         round(i["w_base"], 4), frm, flags])
            s += round(i["contrib"], 5)
        gap = round(M["published"] - s, 5)          # the gray piece: what the items do not explain
        months[t] = {"label": label(t), "short": date(int(t[:4]), int(t[5:]), 1).strftime("%b %Y"),
                     "base": label(M["base"]), "pub": round(M["published"], 4), "sum": round(s, 4),
                     "gap": gap, "prelim": M["preliminary"], "pass": M["pass"], "why": M["why_out"],
                     "precise": M["precise"], "fdT": M["fd"]["T"], "fdB": M["fd"]["B"],
                     "pub1": round(M["published"], 1), "filled": round(M["filled_share"], 2),
                     "round_max": round(rounding_bound(t, M), 4), "r": rows}
    pubs = [months[t]["pub"] for t in order]
    lo = min(0, math.floor(min(pubs)))
    hi = 2 * math.ceil(max(pubs) / 2)
    up = max(sum(r[1] for r in months[t]["r"] if r and r[1] > 0) + max(months[t]["gap"], 0) for t in order)
    dn = max(-sum(r[1] for r in months[t]["r"] if r and r[1] < 0) - min(months[t]["gap"], 0) for t in order)
    items = [[SHORT.get(meta[c]["name"], meta[c]["name"]), meta[c]["name"], meta[c]["group"],
              meta[c]["major"], c] for c in codes]
    return {
        "title": "The PPI Scuba Diver",
        "dek": ("Each month, the diver sits as deep as wholesale inflation: the 12-month change in the "
                "Producer Price Index for final demand. Items that pushed it up hang below as anchors. "
                "Items that pulled it down float above. Every month shows our work, including the months "
                "where the items miss BLS's headline."),
        "source": ("Source: BLS Producer Price Index for final demand (WPUFD4) and its commodity indexes, "
                   "not seasonally adjusted, and BLS relative importance tables. Contributions computed by "
                   "Data 4 The People. Items with no published index use their parent category's change. "
                   "Before July 2021 BLS published its "
                   "indexes to one decimal, so the items cannot match the headline as closely; those months "
                   "are flagged."),
        "axis": {"lo": lo, "hi": hi, "step": 2}, "size": {"up": round(up, 4), "dn": round(dn, 4)},
        "color": {"steps": STEPS}, "items": items, "parents": parents,
        "order": order, "months": months, "checks": m["checks"],
    }


def write_page(payload, filename, description):
    data = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
    (PROCESSED / "page_data.json").write_text(data)
    t = (SRC / "template.html").read_text()
    assert t.count("/*DATA*/{}") == 1
    t = t.replace("/*DATA*/{}", data)

    jsc = "/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc"
    if os.path.exists(jsc):
        i = t.index("<script>") + 8
        js = t[i:t.index("</script>", i)]
        with tempfile.TemporaryDirectory() as tmp:
            open(f"{tmp}/page.js", "w").write(js)
            open(f"{tmp}/chk.js", "w").write(
                'try{ new Function(read("%s/page.js")); print("ok") }catch(e){ print("PARSE ERROR: "+e) }' % tmp)
            out = subprocess.run([jsc, f"{tmp}/chk.js"], capture_output=True, text=True).stdout.strip()
        assert out == "ok", out

    head_end = t.index("</style>") + len("</style>")
    full = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f'<meta name="description" content="{description}">\n'
            + t[:head_end].replace('<meta charset="utf-8">\n', "") + "\n</head>\n<body>\n"
            + t[head_end:] + "\n</body>\n</html>\n")
    DIST.mkdir(exist_ok=True)
    (DIST / filename).write_text(full)

    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if os.path.exists(chrome):
        with tempfile.TemporaryDirectory() as tmp:
            probe = full.replace("<script>", '<script>window.onerror=(m,u,l,c)=>{document.body.setAttribute("data-err",m+" @"+l+":"+c)};', 1)
            open(f"{tmp}/probe.html", "w").write(probe)
            for mode in ("", "#embed=1", "#month=2022-07"):
                dom = subprocess.run([chrome, "--headless=new", "--disable-gpu", "--window-size=1100,800",
                                      "--virtual-time-budget=4000", "--dump-dom", f"file://{tmp}/probe.html{mode}"],
                                     capture_output=True, text=True, timeout=120).stdout
                err = re.search(r'data-err="([^"]*)"', dom)
                assert dom and not err, f"page JavaScript error {mode}: {err.group(1) if err else 'no output'}"
                assert 'data-ready="1"' in dom, f"page script did not finish {mode}"
            # Real time, not virtual: the script must finish quickly or the page sits blank.
            dom = subprocess.run([chrome, "--headless=new", "--disable-gpu", "--window-size=1100,800",
                                  "--dump-dom", f"file://{tmp}/probe.html"],
                                 capture_output=True, text=True, timeout=120).stdout
            ms = int(re.search(r'data-ms="(\d+)"', dom).group(1))
            assert ms < 1000, f"page script took {ms} ms before first draw"
            # Playback must not resize the scene: a resize repacks every month and flashes.
            # Every month's clusters must fit between the surface and the date axis.
            step = ('<script>{const hs=new Set();let over="";for(let k=0;k<N;k++){pos=target=k;lastReadout=-1;updateReadout();'
                    'hs.add(Math.round(document.getElementById("stage").getBoundingClientRect().height));'
                    'const L=lay(k),y=depthY(M[k].pub);if(y+GAP+L.up.bot-L.up.top>H-G.axisH-4||y-GAP-(L.dn.bot-L.dn.top)<G.sky*0.4-2)over+=ORDER[k]+" "}'
                    'document.body.setAttribute("data-heights",[...hs].join(","));document.body.setAttribute("data-over",over)}</script>')
            for width in (1100, 700, 500):
                open(f"{tmp}/steps.html", "w").write(probe.replace("</body>", step + "</body>"))
                dom = subprocess.run([chrome, "--headless=new", "--disable-gpu", f"--window-size={width},800",
                                      "--virtual-time-budget=3000", "--dump-dom", f"file://{tmp}/steps.html"],
                                     capture_output=True, text=True, timeout=120).stdout
                hs = re.search(r'data-heights="([^"]*)"', dom).group(1)
                assert "," not in hs, f"scene height changes during playback at width {width}: {hs}"
                over = re.search(r'data-over="([^"]*)"', dom).group(1).strip()
                assert not over, f"clusters overflow the scene at width {width}: {over}"
        print(f"dist/{filename}: runs in Chrome (full, embedded, July 2022) without errors; script ready in {ms} ms; scene height steady and every month fits")
    return full


def main():
    m = json.loads((PROCESSED / "monthly.json").read_text())
    payload = encode(m)
    a, b = label(m["order"][0]), label(m["order"][-1])
    write_page(payload, "index.html",
               f"Which items pushed U.S. wholesale prices (PPI final demand) up and down in every month from "
               f"{a} to {b}, drawn as a scuba diver weighed down by anchors and lifted by floats. "
               "Built by Data 4 The People.")


if __name__ == "__main__":
    main()
