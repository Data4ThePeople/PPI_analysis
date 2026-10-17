"""Read the BLS final demand relative importance files into December weight trees.

Each yearly file lists every commodity in final demand with its December
weight for two years. The tree is defined by the commodity codes: a code's
parent is the longest other code in the same December that is a prefix of it,
and the two-digit groups hang from FD4. A dash means the item was not in
final demand that December.
"""
from __future__ import annotations

import re
import zipfile
import xml.etree.ElementTree as ET

from common import WEIGHTS

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
ROOT_CODE = "FD4"
TOLERANCE = 0.0035     # parent vs sum of children, in percentage points (rounding)


class Node:
    __slots__ = ("code", "name", "weight", "parent", "kids", "level", "order")

    def __init__(self, code, name, weight, order):
        self.code, self.name, self.weight, self.order = code, name, weight, order
        self.parent, self.kids, self.level = None, [], 0

    def __repr__(self):
        return f"<{self.code} {self.name!r} {self.weight}>"


def _rows(path):
    with zipfile.ZipFile(path) as z:
        strings = ["".join(t.text or "" for t in si.iter(NS + "t"))
                   for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(NS + "si")]
        sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    out = []
    for row in sheet.iter(NS + "row"):
        rec = {}
        for cell in row.iter(NS + "c"):
            col = re.match(r"[A-Z]+", cell.get("r")).group()
            v = cell.find(NS + "v")
            if v is None or v.text is None:
                continue
            rec[col] = strings[int(v.text)] if cell.get("t") == "s" else v.text
        out.append(rec)
    return out


def read_file(year):
    """{'decs': (Dy-2, Dy-1), 'items': [(code, name, w_first, w_second)]} for file `year`.

    Weights are floats, or None where BLS prints a dash.
    """
    rows = _rows(WEIGHTS / f"fd-commodities-{year}.xlsx")
    head = next(r for r in rows if (r.get("B") or "").strip() == "Code")
    decs = tuple(int(re.search(r"December (\d{4})", head[c]).group(1)) for c in ("D", "E"))
    if decs != (year - 2, year - 1):
        raise RuntimeError(f"file {year}: columns are Decembers {decs}")
    items, seen = [], set()
    for r in rows:
        code, name = (r.get("B") or "").strip(), (r.get("C") or "").strip()
        if not code or not name or code == "Code" or not re.fullmatch(r"FD4|[0-9A-Z]{2,8}", code):
            continue
        if code in seen:
            raise RuntimeError(f"file {year}: duplicate code {code}")
        seen.add(code)

        def num(x):
            x = (x or "").strip()
            if x in ("-", "–", ""):
                return None
            return float(x)
        items.append((code, " ".join(name.split()), num(r.get("D")), num(r.get("E"))))
    if items[0][0] != ROOT_CODE:
        raise RuntimeError(f"file {year}: first row is {items[0]}")
    return {"decs": decs, "items": items}


def build_tree(items, which):
    """Nodes for one December column (`which` = 2 for the first, 3 for the second).

    Returns {code: Node} with parent/kids set, after checking each parent
    against the sum of its children.
    """
    nodes = {}
    for i, it in enumerate(items):
        w = it[which]
        if w is None:
            continue
        nodes[it[0]] = Node(it[0], it[1], w, i)
    codes = sorted((c for c in nodes if c != ROOT_CODE), key=len)
    for c in codes:
        par = ROOT_CODE
        for k in range(len(c) - 1, 1, -1):
            if c[:k] in nodes:
                par = c[:k]
                break
        nodes[c].parent = par
        nodes[par].kids.append(c)
    for n in nodes.values():
        n.kids.sort(key=lambda k: nodes[k].order)
        lv, p = 0, n.parent
        while p is not None:
            lv, p = lv + 1, nodes[p].parent
        n.level = lv
    return nodes


def check_sums(nodes, label):
    """Every parent equals the sum of its children within rounding."""
    bad = []
    for n in nodes.values():
        if n.kids:
            s = sum(nodes[k].weight for k in n.kids)
            tol = max(TOLERANCE, 0.0006 * len(n.kids))
            if abs(s - n.weight) > tol:
                bad.append((n.code, n.name, n.weight, round(s, 4)))
    return bad


_cache = {}


def december(year):
    """The weight tree for December `year`, the set used for January-December year+1.

    It comes from the second column of file year+1, which BLS says reflects the
    sample revisions effective that January.
    """
    if year not in _cache:
        f = read_file(year + 1)
        _cache[year] = build_tree(f["items"], 3)
    return _cache[year]


def leaves(nodes):
    return {c: n for c, n in nodes.items() if not n.kids}


if __name__ == "__main__":
    for y in range(2013, 2026):
        t = december(y)
        lf = leaves(t)
        bad = check_sums(t, y)
        print(f"Dec {y}: {len(t)} nodes, {len(lf)} leaves, leaf sum {sum(n.weight for n in lf.values()):.3f}, "
              f"{len(bad)} parents off: {bad[:4]}")
