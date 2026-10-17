"""Monthly not seasonally adjusted index levels for every code in the weight trees.

Reads every wp.data.* flat file. The same series often appears in more than
one file (wp.data.0.Current repeats the group files); a repeated month must
carry the same value, or the build stops. Annual averages (M13) are dropped.
Writes data/processed/indexes.json: {series_id: {"YYYY-MM": value}} plus the
footnote codes ("P" preliminary) for FD4.
"""
from __future__ import annotations

import csv
import json

from common import HEADLINE, PROCESSED, WP

FIRST_YEAR = 2012


def tree_codes():
    from weights import december
    codes = {}
    for y in range(2013, 2026):
        for c, n in december(y).items():
            codes.setdefault(c, n.name)
    codes.pop("FD4")
    return codes


def name_aliases(codes):
    """Codes in the weight files with no series of their own, matched to the one
    series at the same code length with the same name (BLS recoded the item and
    carried its history). Whether the series covers a month is checked later."""
    from chain import SERIES_ALIAS, norm
    have = set()
    with open(WP / "wp.series") as fh:
        next(fh)
        have = {line.split("\t")[0].strip() for line in fh}
    byname = {}
    with open(WP / "wp.item") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            c = r["group_code"] + r["item_code"]
            if f"WPU{c}" in have:
                byname.setdefault(norm(r["item_name"]), []).append(c)
    out = {}
    for c, name in codes.items():
        if f"WPU{c}" in have or c in SERIES_ALIAS:
            continue
        alts = [a for a in byname.get(norm(name), []) if len(a) == len(c) and a != c]
        if len(alts) == 1:
            out[c] = alts[0]
        elif len(alts) > 1:
            raise SystemExit(f"{c} {name}: several same-name series {alts}")
    return out


def wanted_ids(codes, alias):
    from chain import SERIES_ALIAS
    keep = set(codes) | set(SERIES_ALIAS.values()) | set(alias.values())
    return {HEADLINE, "WPUFD41", "WPUFD42", "WPUFD43"} | {f"WPU{c}" for c in keep}


def load(ids):
    out, notes = {}, {}
    files = sorted(p for p in WP.glob("wp.data.*"))
    if not files:
        raise SystemExit("no wp.data files; run fetch.py")
    for p in files:
        with open(p) as fh:
            next(fh)
            for line in fh:
                parts = line.rstrip("\n").split("\t")
                sid = parts[0].strip()
                if sid not in ids:
                    continue
                year, period = int(parts[1]), parts[2].strip()
                if year < FIRST_YEAR or not period.startswith("M") or period == "M13":
                    continue
                val = parts[3].strip()
                if val in ("", "-"):
                    continue
                key = f"{year}-{period[1:]}"
                v = float(val)
                prev = out.setdefault(sid, {}).get(key)
                if prev is not None and prev != v:
                    raise SystemExit(f"{sid} {key}: {prev} in one file, {v} in {p.name}")
                out[sid][key] = v
                if sid == HEADLINE:
                    notes[key] = parts[4].strip() if len(parts) > 4 else ""
    return {s: dict(sorted(v.items())) for s, v in out.items()}, notes


def main():
    codes = tree_codes()
    alias = name_aliases(codes)
    ids = wanted_ids(codes, alias)
    data, notes = load(ids)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    (PROCESSED / "indexes.json").write_text(json.dumps(
        {"series": data, "fd4_footnotes": notes, "name_alias": alias}))
    print("name aliases:", alias)
    print(f"{len(ids)} series wanted, {len(data)} found; FD4 runs {min(data[HEADLINE])} to {max(data[HEADLINE])}")


if __name__ == "__main__":
    main()
