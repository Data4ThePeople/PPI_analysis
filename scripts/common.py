"""Paths, BLS download convention and the flat-file reader shared by every script."""
from __future__ import annotations

import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, os.path.expanduser("~/.claude/d4tp-process"))
from d4tp_env import load_env  # noqa: E402

load_env()

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
WP = RAW / "wp"
WEIGHTS = RAW / "weights"
PROCESSED = ROOT / "data" / "processed"
DIST = ROOT / "dist"

# download.bls.gov rejects bare agents; BLS asks callers to identify themselves.
CONTACT = os.environ.get("D4TP_CONTACT_EMAIL", "")
USER_AGENT = f"Mozilla/5.0 PPI_analysis/1.0 ({CONTACT})"

# One file per year, each holding two Decembers: file Y has December Y-2 and
# December Y-1. December Y-1 is the weight set used for January-December Y.
WEIGHT_URL = ("https://www.bls.gov/ppi/tables/"
              "final-demand-relative-importance-of-commodities-{year}.xlsx")
WEIGHT_YEARS = range(2014, 2027)
WP_DIR_URL = "https://download.bls.gov/pub/time.series/wp/"

HEADLINE = "WPUFD4"          # PPI final demand, not seasonally adjusted
# The release month this analysis runs through, and the earliest month shown.
TARGET = (2026, 9)
START = (2016, 10)           # ten years of 12-month changes, through TARGET


def download(url: str, dest: Path, force: bool = False) -> Path:
    if dest.exists() and not force:
        return dest
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    body = urllib.request.urlopen(req, timeout=300).read()
    if dest.suffix == ".xlsx" and not body.startswith(b"PK"):
        raise RuntimeError(f"{url} did not return an xlsx (got an HTML page?)")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(body)
    return dest


def month_add(t: str, k: int) -> str:
    y, m = int(t[:4]), int(t[5:])
    n = y * 12 + (m - 1) + k
    return f"{n // 12}-{n % 12 + 1:02d}"
