"""Chained item contributions to the 12-month change in PPI final demand, any month.

For a target month T, base B one year earlier, DP the December two years
before T's year ends (December of T's year minus 2) and DN the December just
before T:

    c = w_B x (I_DN/I_B - 1) + (FD_DN/FD_B) x RI_DN x (I_T/I_DN - 1)

w_B is the DP relative importance rolled forward to B the way BLS rolls it:
RI_DP x (I_B/I_DP) / (FD_B/FD_DP). RI_DN is BLS's December table for DN.
When T is a December, B is DN and the first term is zero.

Unlike the CPI, PPI items come and go between Decembers, so the two terms are
computed on their own trees: the first on the DP tree, the second on the DN
tree. Each item's contribution is the sum of the terms it appears in.

Leaves without a published index for the months a term needs are filled from
their nearest published parent, one term at a time. With FILL = "borrow" (the
default) a filled leaf takes the parent's own price change. With "residual"
(the CPI method), deepest parent first, the parent's own index and weight (the
sum of its leaves' weights) give its contribution, and what its other leaves do
not explain goes to the filled leaves, shared by their December weights.

Two exceptions, both small (see DATASETS.md):
- A leaf with no published index anywhere above it (only final demand) would
  take final demand's residual, which would force every month to tie out. It
  takes the change of final demand goods, services or construction instead.
- When BLS prints 0.000 for leaves that had weight the December before and the
  table then falls short of 100 (December 2019, 2021 and 2024), those leaves get
  their prior December weight rolled forward, and are filled from their parent.
"""
from __future__ import annotations

import json
import re

from common import HEADLINE, PROCESSED, month_add
from weights import december

RESTORE_MIN = 0.03       # percent of final demand; smaller shortfalls are rounding
# How a leaf without its own index is filled from its nearest published parent:
# "borrow" gives it the parent's own price change; "residual" gives it what the
# parent's other leaves do not explain (the CPI method). PPI parent indexes are
# weighted by all shipments, not by final demand, so the residual can be far off
# (processed eggs: -195% in December 2025). See DATASETS.md, "Filling".
FILL = "borrow"

# BLS moved group 04 (hides, skins, leather) to 159F in the index database; the
# weight files used the 04 codes through December 2024. Matched by name.
SERIES_ALIAS = {"041": "159F11", "0419": "159F11", "041901": "159F1101",
                "043": "159F2", "0431": "159F21", "043105": "159F2101",
                "0432": "159F22", "043205": "159F2201",
                "0439": "159F23", "043901": "159F2301"}
# Orphans (no published ancestor) borrow the change of their final demand type.
TYPE_SERIES = {"Goods": "FD41", "Services": "FD42", "Construction": "FD43"}


def months_for(t: str):
    y = int(t[:4])
    return t, month_add(t, -12), f"{y-2}-12", f"{y-1}-12"


def group_of(code):
    two = int(code[:2])
    return "Goods" if two <= 15 else ("Construction" if two == 80 else "Services")


def norm(name):
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


class Inputs:
    def __init__(self):
        d = json.loads((PROCESSED / "indexes.json").read_text())
        self.idx = d["series"]
        self.fd4_notes = d["fd4_footnotes"]
        self.alias = dict(SERIES_ALIAS, **d["name_alias"])
        self._trees = {}

    def series(self, code):
        if code == "FD4":
            return self.idx.get(HEADLINE, {})
        if code.startswith("FD"):
            return self.idx.get(f"WPU{code}", {})
        return self.idx.get(f"WPU{self.alias.get(code, code)}", {})

    def tree(self, year):
        if year not in self._trees:
            nodes = december(year)
            ri = {c: n.weight for c, n in nodes.items() if not n.kids}
            short = 100.0 - sum(ri.values())
            restored = {}
            if short > RESTORE_MIN:
                prev = december(year - 1)
                d0, d1 = f"{year-1}-12", f"{year}-12"
                FD = self.series("FD4")
                for c, w in ri.items():
                    if w == 0.0 and c in prev and not prev[c].kids and prev[c].weight > 0:
                        p = c
                        while not all(m in self.series(p) for m in (d0, d1)):
                            p = nodes[p].parent
                        s = self.series(p)
                        restored[c] = (prev[c].weight * (s[d1] / s[d0]) / (FD[d1] / FD[d0]))
                if not restored:
                    raise RuntimeError(f"December {year} is {short:.3f} short of 100 with no zeroed items")
                ri.update(restored)
            self._trees[year] = {"nodes": nodes, "ri": ri, "short": short, "restored": restored}
        return self._trees[year]


def run_term(inp, year, months, wfac, change):
    """Contributions for one term on December `year`'s tree.

    months: the months a series must have for this term.
    wfac(s, ri): the term weight of a node with series s and December weight ri.
    change(s): the node's price change over the term, as a fraction.
    Returns ({code: {"w", "c", "g", "own", "from"}} for every leaf, [fills]);
    g is the price change the leaf was given (its own, or the one it borrowed).
    """
    tr = inp.tree(year)
    nodes, ri = tr["nodes"], tr["ri"]

    def has(code):
        s = inp.series(code)
        return all(m in s for m in months)

    out, fill_parent = {}, {}
    for code, r in ri.items():
        if has(code):
            s = inp.series(code)
            w = wfac(s, r)
            out[code] = {"w": w, "c": w * change(s), "g": change(s), "own": True, "from": code}
            continue
        p = nodes[code].parent
        while p != "FD4" and not has(p):
            p = nodes[p].parent
        if p == "FD4":                      # orphan: borrow the type's change
            t = TYPE_SERIES[group_of(code)]
            s = inp.series(t)
            if not has(t):
                raise RuntimeError(f"{year}: {t} missing {months}")
            w = wfac(s, r)
            out[code] = {"w": w, "c": w * change(s), "g": change(s), "own": False, "from": t}
        else:
            fill_parent[code] = p

    def leaves_under(p):
        return [c for c in ri if c.startswith(p) and c != p] or [p]

    fills = []
    if FILL == "borrow":
        for p in sorted(set(fill_parent.values())):
            s = inp.series(p)
            fill = [c for c, q in fill_parent.items() if q == p]
            for c in fill:
                w = wfac(s, ri[c])
                out[c] = {"w": w, "c": w * change(s), "g": change(s), "own": False, "from": p}
            fills.append({"parent": p, "items": fill, "weight": sum(out[c]["w"] for c in fill),
                          "contrib": sum(out[c]["c"] for c in fill)})
        return out, fills
    for p in sorted(set(fill_parent.values()), key=lambda c: (-nodes[c].level, nodes[c].order)):
        under = leaves_under(p)
        fill = [c for c in under if fill_parent.get(c) == p]
        rest = [c for c in under if c not in fill]
        if any(c not in out for c in rest):
            raise RuntimeError(f"{year} {p}: a deeper fill was not done first")
        s = inp.series(p)
        WP = wfac(s, sum(ri[c] for c in under))
        cP = WP * change(s)
        Wf = WP - sum(out[c]["w"] for c in rest)
        cres = cP - sum(out[c]["c"] for c in rest)
        tot = sum(ri[c] for c in fill)
        for c in fill:
            a = ri[c] / tot if tot else 1 / len(fill)
            out[c] = {"w": Wf * a, "c": cres * a, "g": cres / Wf if Wf else 0.0, "own": False, "from": p}
        fills.append({"parent": p, "items": fill, "weight": Wf, "contrib": cres})
    return out, fills


def compute_month(inp: Inputs, t: str):
    T, B, DP, DN = months_for(t)
    FD = inp.series("FD4")
    for m in (T, B, DP, DN):
        if m not in FD:
            raise KeyError(f"{t}: final demand index missing for {m}")
    rel_b = FD[B] / FD[DP]
    K = FD[DN] / FD[B]
    yp, yn = int(DP[:4]), int(DN[:4])

    t1, f1 = run_term(inp, yp, (DP, B, DN),
                      lambda s, r: r * (s[B] / s[DP]) / rel_b,
                      lambda s: s[DN] / s[B] - 1)
    t2, f2 = run_term(inp, yn, (DN, T),
                      lambda s, r: K * r,
                      lambda s: s[T] / s[DN] - 1)

    nodes_p, nodes_n = inp.tree(yp)["nodes"], inp.tree(yn)["nodes"]
    names = {c: n.name for c, n in nodes_p.items()}
    names.update({c: n.name for c, n in nodes_n.items()})
    for k in TYPE_SERIES.values():
        names[k] = {"FD41": "Final demand goods", "FD42": "Final demand services",
                    "FD43": "Final demand construction"}[k]

    # An item that left the tree at DN and one that entered it with the same
    # name (a recode, such as the leather items in January 2026) are one item.
    # Its base weight is the old code's (the base month is in the old tree).
    merge = {}
    only1 = {norm(names[c]): c for c in t1 if c not in t2}
    for c in t2:
        if c not in t1 and norm(names[c]) in only1:
            merge[only1[norm(names[c])]] = c

    def major(code):
        top = code[:2]
        return (nodes_n.get(top) or nodes_p.get(top)).name

    items = []
    for code in sorted((set(t1) | set(t2)) - set(merge)):
        old = next((o for o, n in merge.items() if n == code), None)
        a, b = t1.get(old or code), t2.get(code)
        s_new, s_old = inp.series(code), inp.series(old or code)
        own = all(x["own"] for x in (a, b) if x)
        partly = not own and any(x["own"] for x in (a, b) if x)
        w = a["w"] if a else b["w"]                 # weight at the base month
        contrib = (a["c"] if a else 0.0) + (b["c"] if b else 0.0)
        # The price change shown (and colored) is the item's own index change
        # where it has one, else the changes it was given, linked across the
        # two terms. Never contribution / weight: the weight changes at DN.
        # A seasonal item (melons) can have both months but no December, so its
        # contribution is borrowed while its own 12-month change is published.
        if B in s_old and T in s_new:
            yoy, src = (s_new[T] / s_old[B] - 1) * 100, "published"
        else:
            yoy = ((1 + (a["g"] if a else 0.0)) * (1 + (b["g"] if b else 0.0)) - 1) * 100
            src = "linked" if own else ("partly borrowed" if partly else "borrowed")
        # Over part of the year only: the item entered at DN, or left at DN.
        span = "full" if (a and b) or B == DN else ("since December" if b else "through December")
        froms = [x["from"] for x in (a, b) if x and not x["own"]]
        items.append({
            "code": code, "old_code": old, "name": names[code], "group": group_of(code),
            "major": major(code), "own_index": own,
            "partly_own": partly, "span": span,
            "in_first": a is not None, "in_second": b is not None,
            "w_base": w, "ri_dn": b["w"] / K if b else 0.0,
            "c1": a["c"] if a else 0.0, "c2": b["c"] if b else 0.0,
            "contrib": contrib, "yoy": yoy, "yoy_source": src,
            "filled_from": names.get(froms[-1], froms[-1]) if froms else None,
            "restored": code in inp.tree(yp)["restored"] or code in inp.tree(yn)["restored"],
        })
    published = (FD[T] / FD[B] - 1) * 100
    return {"month": T, "base": B, "dec_prior": DP, "dec_new": DN,
            "published": published, "sum": sum(i["contrib"] for i in items),
            "fd": {"T": FD[T], "B": FD[B]}, "fd_note": inp.fd4_notes.get(T, ""),
            "restored": {"first": inp.tree(yp)["restored"], "second": inp.tree(yn)["restored"]},
            "fills": {"first": f1, "second": f2}, "items": items}


if __name__ == "__main__":
    import sys
    inp = Inputs()
    t = sys.argv[1] if len(sys.argv) > 1 else "2026-09"
    r = compute_month(inp, t)
    print(t, "published %.4f items %.4f gap %.5f" % (r["published"], r["sum"], r["sum"] - r["published"]))
