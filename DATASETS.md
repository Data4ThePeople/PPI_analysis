# Datasets

One section per dataset, updated whenever we learn something new.

## PPI commodity and final demand indexes (BLS flat files)

**What it is.** Monthly Producer Price Index levels, not seasonally adjusted.
`WPUFD4` is final demand, the headline. `WPU<code>` is each commodity in the
final demand weight file. `WPUFD41`, `WPUFD42` and `WPUFD43` (final demand
goods, services, construction) are used only for orphan items (see Filling).

**Where it comes from.** `https://download.bls.gov/pub/time.series/wp/`, every
`wp.data.*` file plus `wp.series` and `wp.item`, tab-separated. It needs a
browser-like User-Agent with a contact address. No key or request limit.
`scripts/fetch.py` downloads; `scripts/indexes.py` reads every file into
`data/processed/indexes.json`. The same series appears in more than one file;
a repeated month must carry the same value or the build stops.

**Version and vintage.** Pulled October 17, 2026, after the September 2026
release. BLS revises PPI indexes for four months after first release; June to
September 2026 carry the "P" (preliminary) footnote and will change. We pin
the October 17 pull. A refresh is `fetch.py --force`.

**Coverage and precision.** Index levels were published to one decimal
before July 2021 and to three decimals from July 2021 on (BLS notice, "Producer
Price Index to Publish Interim Index Values to 3 Decimal Places", December
2021). BLS did not revise the earlier history. With an index near 110, one
decimal moves a 12-month change by up to about 0.09 points from rounding
alone. This is what sets where the page starts (see Tie-out).

**Items without a published index.** BLS weights some commodities in final
demand but does not publish their index, usually because too few companies
report to publish without revealing one of them. Others stopped being
published partway through (military aircraft after May 2024, processed eggs
after January 2022). In September 2026, items with no index for the months a
term needs carried 1.55% of final demand weight; in the months shown it ranges
from 1.04% to 2.20%. Before 2021 it was 6% to 9%, mostly machinery and
equipment wholesaling (about 4% of weight, no published index 2014-2018).

**Recoded items.** BLS moved group 04 (hides, skins, leather) to 159F in the
index database while the weight files kept the 04 codes through December 2024.
Hides and the three footwear items are matched to their 159F series by name
(`chain.SERIES_ALIAS`). Finished leather, luggage and other leather goods have
no index under either code. Eleven more codes with no series of their own match
exactly one series at the same code length with the same name (BLS recoded the
item and carried its history), for example small arms 151301 to 151401. These
are found automatically in `indexes.py` and printed when it runs.

**Missing data.** None for FD4 in the window. October 2025 was published
(unlike the CPI).

**License.** U.S. government work, public domain.

## Relative importance of commodities in final demand (BLS)

**What it is.** Each commodity's share of PPI final demand, in percent, as of
December. Commodity codes nest: a code's parent is the longest other code in
the same December that starts it (011101 Citrus fruits under 0111 under 011
under 01 Farm products under FD4). The six-digit codes are the leaves BLS
assigns weights to; higher levels are sums.

**Where it comes from.**
`https://www.bls.gov/ppi/tables/final-demand-relative-importance-of-commodities-{year}.xlsx`,
2014 to 2026, saved as `data/raw/weights/fd-commodities-{year}.xlsx`. The 2026
file is the same as `https://www.bls.gov/web/ppi/ppi-fdallrel.xlsx`. The
yearly files go back to 2014 (December 2012 and 2013); 2010-2013 URLs redirect.

**Version and vintage.** File Y holds December Y-2 and December Y-1, posted
each June. The December Y-1 column "reflects all sample revisions effective
January Y", so it is the weight set used for January to December of year Y.
We use that column (file Y+1, second column, for December Y). The same December
reprinted as the first column of the next file matches except for a few items:
see Known quirks.

**Weight updates inside the window.** January 2018 (2012 census shipments),
January 2021 (allocation to final demand from the 2012 BEA input-output
tables), January 2023 (2017 census shipments), January 2026 (allocation from
the 2017 input-output tables). Each is a January reset, which the chained
method handles.

**Changes over time.** Items enter and leave final demand from one December
to the next (848 leaves in December 2013, 783 in December 2025). Each term of
the chained formula is computed on its own December's tree. An item that left
and one that entered with the same name (the leather recode) are shown as one.

**Suppressed values.** BLS prints 0.000 for some items that had weight the
year before, and the table then falls short of 100: December 2019 (99.78),
December 2021 (99.80), December 2024 (99.96). The missing weight is farm
tractors, locomotives, nonpropelled ships and a few small items. When a
December falls short by more than 0.03, those items get their prior December
weight rolled forward with BLS's formula and are filled like any item without
an index. Checked against what BLS printed for the same December a year
later: tractors 0.1195 (BLS later 0.116), locomotives 0.0730 (0.073), ships
0.0216 (0.023). December 2021 was never reprinted with values. `TIEOUT.md`
lists every restored item.

**Units and rounding.** Percent, three decimals; 0.000 means under 0.0005.
Leaves sum to 100 within about 0.02 apart from the short Decembers above.

**Known quirks.** Nonferrous metal ores (1021) prints 0.033 in December 2024
while its children sum to 0.043. Leaf weights are used, so this does not
matter.

**License.** U.S. government work, public domain.

## Method

**Chained contribution** (`scripts/chain.py`), the same structure as the CPI
balloon. For target month T, base B a year earlier, DP the December two years
before T's year and DN the December just before T:

    c = w_B x (I_DN/I_B - 1) + (FD_DN/FD_B) x RI_DN x (I_T/I_DN - 1)

w_B = RI_DP x (I_B/I_DP) / (FD_B/FD_DP), BLS's roll-forward. When T is a
December, the first term is zero. The terms add to the published 12-month
change exactly if the items and weights are complete.

**Filling items without an index: borrowed change, not residual.** A leaf
with no index for the months a term needs takes its nearest published
parent's own price change, at its own weight. This departs from the CPI
method, where a filled item takes the parent's residual (parent total minus
its published children). The residual works in the CPI because a CPI parent
index is built from its children with the same weights the headline uses. A
PPI parent index is not: it is weighted by all shipments of those products,
while final demand includes only the share sold to final buyers, and that
share differs item by item. So the residual of a PPI parent is not the
missing items' share of final demand. It produced changes such as -195% for
processed eggs in December 2025. We chose the borrowed change for that reason,
not for the size of the gap. (Its gaps are also smaller: in the months shown,
mean 0.013 points against 0.029 with the residual.) `FILL = "residual"` in
`chain.py` switches back.

Leaves with no published index anywhere above them (finished leather,
luggage, other leather goods; computer training schools through 2019) take
the change of final demand goods or services. Using final demand's own
residual would force every month to tie out and hide the error.

**What the gap is.** Items with no published index (1-2% of weight) are
estimated, and the published indexes are rounded. Their combined error is the
gap between what the items add up to and the published change. We do not
force it away. The page shows it as a gray piece, so the pieces add up to the
published change, and states its size every month. In 2026 the gap runs
positive every month (+0.012 to +0.040); we have not identified a cause.

## Tie-out (`scripts/monthly.py`, `scripts/tieout.py`, `TIEOUT.md`)

Rules fixed before looking at results. A month is shown when:
1. both index values in its 12-month change were published to three decimals
   (base month July 2021 or later);
2. the items add up to the published change within 0.05 points, half of the
   0.1 precision BLS publishes 12-month changes at;
3. filled items carry 10% of weight or less.

**Result.** July 2022 to September 2026, 51 months, all pass. Mean absolute
gap 0.013 points, largest 0.040 (May 2026); 42 of 51 within 0.02.

**Why the range stops at July 2022.** Earlier months compare against a
one-decimal index. The weight history would allow October 2016, the ten-year
limit. Of the 69 months from October 2016 to June 2022, 33 miss by more than
0.05 (up to 0.26 in October 2019), and the ones that pass do so partly by
rounding luck. July 2021 to June 2022 all land within 0.05, but their base
month is one-decimal, so they are not shown.
