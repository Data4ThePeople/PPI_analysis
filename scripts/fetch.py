"""Download every raw input: the yearly weight files and the PPI commodity flat files.

The flat files at download.bls.gov/pub/time.series/wp/ carry every published
commodity index, current and discontinued, with no request limits. Each data
file is fetched once; pass --force to refresh (PPI revises the last four
months, so a refresh changes those months).
"""
from __future__ import annotations

import re
import sys
import urllib.request

from common import (WEIGHT_URL, WEIGHT_YEARS, WEIGHTS, WP, WP_DIR_URL, USER_AGENT,
                    download)


def main():
    force = "--force" in sys.argv
    for y in WEIGHT_YEARS:
        download(WEIGHT_URL.format(year=y), WEIGHTS / f"fd-commodities-{y}.xlsx", force)
    req = urllib.request.Request(WP_DIR_URL, headers={"User-Agent": USER_AGENT})
    listing = urllib.request.urlopen(req, timeout=120).read().decode()
    files = sorted(set(re.findall(r"/wp/(wp\.[A-Za-z0-9._-]+)\"", listing)))
    if not any(f.startswith("wp.data.") for f in files):
        raise RuntimeError("wp directory listing changed; no data files found")
    for f in files:
        download(WP_DIR_URL + f, WP / f, force)
    print(f"{len(WEIGHT_YEARS)} weight files, {len(files)} flat files in {WP}")


if __name__ == "__main__":
    main()
