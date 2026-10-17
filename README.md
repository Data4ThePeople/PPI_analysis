# The PPI Scuba Diver

Data 4 The People. Each commodity in the Producer Price Index for final demand
(not seasonally adjusted), sized by how much it added to or took away from the
12-month change, month by month from October 2016 to September 2026. Months that miss our
strict tie-out (all before July 2022, when BLS published one-decimal indexes)
are shown and flagged. The diver
sits as deep as the headline rate; anchors pushed it up, floats pulled it down.

- Page: `dist/index.html` (one self-contained file)
- Method, sources and limits: `DATASETS.md`
- Every month's tie-out: `TIEOUT.md`; one row per month in `data/processed/monthly_summary.csv`

## Rebuild

Python 3, standard library only (Chrome is used, if present, to test the page).

```
cd scripts
python fetch.py      # weight files and BLS flat files (--force to refresh)
python indexes.py    # index cache
python monthly.py    # every month, October 2016 to September 2026, with checks
python build.py      # dist/index.html
python tieout.py     # prints the tie-out table, writes TIEOUT.md
```

Source: U.S. Bureau of Labor Statistics. Public domain.
