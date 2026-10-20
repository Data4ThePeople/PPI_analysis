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
no index under either code. Eleven more codes with no series of their own (nine
items and two parent groups) match exactly one series at the same code length
with the same name (BLS recoded the item and carried its history), for example
small arms 151301 to 151401. These are found automatically in `indexes.py` and
printed when it runs.

Separately, the page shows an item as one row when its code left the weight
tree in one December and a code with the same name entered it the next (21
pairs across the window, including the four leather items and the alias pairs
above). None of the old codes has an index of its own, so no price history is
mixed. The row's base weight is the old code's, because the base month is in
the old tree; the weight can differ a lot from the new code's (for example
159A09 rolled to January 2025 is 0.067; its successor 159A11 is 0.009 in
December 2025, after BLS's weight update). Some new codes have an index that
starts too late for the first term (027B01, 094A01, 101712, 131108, 336101,
371205), so they are estimated for part of the year; the page says so.

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
December falls short by more than 0.03, those items get their weight from the
December a year earlier (as used for that year, the second column of the
following file), rolled forward a year with BLS's formula and are filled like any item without
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
before T's year and DN the December of the year before T's year (so for
T = December 2025, DN is December 2024, not December 2025):

    c = w_B x (I_DN/I_B - 1) + (FD_DN/FD_B) x RI_DN x (I_T/I_DN - 1)

w_B = RI_DP x (I_B/I_DP) / (FD_B/FD_DP), BLS's roll-forward. When T is a
December, B is DN and the first term is zero. An item that is only in the DN
tree (new in January) has only the second term; its base weight on the page
and in the filled share is K x RI_DN, its second-term weight. An item only in
the DP tree has only the first term. The terms add to the published 12-month
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
the change of final demand goods, services or construction, chosen by the
first two digits of the code (80 is construction; 01-15 goods; the rest
services). Using final demand's own
residual would force every month to tie out and hide the error.

**The price change shown (the color).** For an item with an index at both B
and T, it is that index's own 12-month change. This includes seasonal items
such as melons, which BLS publishes in June but not December: the contribution
must borrow (the chain needs December), but the color is the item's own change.
For an item without its own index for those months, it is the changes the item
was given in each term, linked: (1 + term-1 change) x (1 + term-2 change) - 1.
That is the parent's 12-month change when one parent is used throughout. The
page marks these with a dashed ring and calls them estimated. It is never
contribution divided by weight: the weight resets at DN, so that ratio is not a
price change (it gave +252% for other metal ores in March 2026, whose parent
rose 79.9%). An item that entered or left final demand at DN shows its change
since or through December, and the tooltip says so.

**The filled share.** The sum of base weights (as above) of every item that is
estimated in either term, including items estimated for only part of the
year, as a percent of final demand. Rule 3 of the tie-out and the large-miss
note use it.

**What the gap is.** Items with no published index (1-2% of weight) are
estimated, and the published indexes are rounded. Their combined error is the
gap between what the items add up to and the published change. We do not
force it away. The page shows it as a gray piece, so the pieces add up to the
published change, and states its size every month. In 2026 the gap runs
positive every month (+0.012 to +0.040); we have not identified a cause.

## Tie-out (`scripts/monthly.py`, `scripts/tieout.py`, `TIEOUT.md`)

Every month from October 2016 to September 2026 (120 months) is shown. The
tool is educational, so months that miss our tie-out stay in and are flagged
on the page with the reason (Eric, October 17, 2026).

The strict tie-out, fixed before looking at results. A month passes when:
1. both index values in its 12-month change were published to three decimals
   (base month July 2021 or later);
2. the items add up to the published change within 0.05 points, half of the
   0.1 precision BLS publishes 12-month changes at;
3. filled items carry 10% of weight or less (the filled share, defined under
   Method).

**Result.** 51 months pass, July 2022 to September 2026: mean absolute gap
0.013 points, largest 0.040 (May 2026), 42 within 0.02. 69 months are flagged,
October 2016 to June 2022, all for rule 1 (a one-decimal base month); 33 of
them also miss by more than 0.05, up to 0.26 points (October 2019). In 50 of
the 120 months the items round to a different one-decimal figure than BLS
publishes; the page shows both.

**Why the strict tie-out starts at July 2022.** Earlier months compare against
a one-decimal index, which BLS never revised to three decimals. Rounding alone
can move a 12-month change by up to about 0.09 points. The months from July
2021 to June 2022 land within 0.05, but their base month is one-decimal, so a
close match there can be luck. The weight files would allow going back to
October 2016, the ten-year limit.

**What the page shows for each month.** BLS's index values (one or three
decimals, as published), the 12-month change they give, what the items add
up to, the gray piece needed to reach BLS's figure, both rounded to one
decimal, and whether the month passes.

**Large misses.** For each month the build computes the largest change in the
12-month rate that rounding of BLS's two headline index values can cause:
half of the last published digit on each (0.05 before July 2021, 0.0005
after), carried through T/B. When a flagged month's gap is bigger than that,
the flag says so and gives the share of weight estimated from parent
categories. This happens in 21 months (November 2016 to January 2021, largest
October 2019: 0.257 against a bound of 0.086, with 6.1% of weight
estimated). The bound covers only the headline index; the item indexes were
also rounded to one decimal in those years, which adds to the gap on the
items side, so we attribute the excess to estimated items and item rounding
together, not to either alone. The date axis shades the one-decimal
months and marks every flagged month with an amber dot.

## What some PPI items measure (for the September 2026 takeaways)

**Trade services are margins.** The wholesale and retail items (codes 57x and
58x, 33 items in September 2026) do not price the goods sold. BLS treats
stores and wholesalers as sellers of a service and prices the margin: selling
price minus the acquisition price of the same good. A margin can fall when the
price of the good rises, if the store's cost rises faster. Sources: BLS,
"Wholesale and retail Producer Price Indexes: margin prices," Beyond the
Numbers, vol. 1 (https://www.bls.gov/opub/btn/volume-1/wholesale-and-retail-producer-price-indexes-margin-prices.htm);
BLS 2026 notice on final demand commodity weight allocations, which describes
trade services as "measured as the difference between selling and acquisition
price." BLS leaves zero or negative margins out of the calculation (BLS working
paper EC200070, 2020).

**Portfolio management follows asset values.** BLS prices it mostly from
management fees charged as a share of assets under management (fee = basis
points times fund value). The assets are held fixed at the start of the
period, with no inflows or outflows, and updated by the portfolio's rate of
return. So the index moves with market returns as well as fee rates. Source:
BLS factsheet, "Producer Price Index for Portfolio Management and Investment
Advice - NAICS 523940" (https://www.bls.gov/ppi/factsheets/producer-price-index-for-portfolio-management-and-investment-advice-naics-523940.htm).

**Airline passenger services** is what airlines receive for passenger
flights, a producer price, not the consumer fare in the CPI.

**Preliminary months.** June to September 2026 carry BLS's "P" footnote and
will be revised; every September 2026 number in the takeaways is preliminary.

**Charts and tie-out.** `scripts/takeaways.py` draws the five charts into
`charts/2026-09/` (the numbers behind each in `charts/2026-09/numbers/`);
`scripts/takeaways_tieout.py` recomputes every 12-month change from the raw
flat files and every contribution and total, and writes `TAKEAWAYS_TIEOUT.md`.

**Long-distance trucking (WPU301202)** starts June 2009 in the flat files, so
its 12-month change starts June 2010. The takeaways chart uses that full
history, not only the diver's window. Trucking prices often carry fuel
surcharges; BLS, "The Impact of Fuel Surcharges on the PPI" (Current Price
Topics, second quarter 2011), describes transportation PPIs falling as
surcharges fell in 2009. BLS does not split surcharges from base rates in
this index.
