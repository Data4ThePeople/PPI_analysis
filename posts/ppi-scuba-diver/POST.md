---
title: "The PPI Scuba Diver: What Is Driving Wholesale Prices, Every Month Since 2016"
subtitle: A free, animated chart of every item in the Producer Price Index for final demand, sized by how much it added to or took away from the 12-month change, every month from October 2016 to September 2026.
slug: ppi-scuba-diver
date: 2026-10-19
time: 07:00:00-04:00
section: Visualization
hero: images/ppi-scuba-diver-hero-1680x1080.png
hero_alt:
meta_title:
description:
keywords:
schema_type: dataset
drop_cap: false
heading_spacer: 20px
caption_spacer: 20px
dividers: false
---

# The PPI Scuba Diver: What Is Driving Wholesale Prices, Every Month Since 2016

<iframe src="https://data4thepeople.github.io/PPI_analysis/dist/index.html#embed=1" width="100%" height="780" loading="lazy" style="border:0" title="The PPI Scuba Diver: every item in PPI final demand, October 2016 to September 2026"></iframe>

::: spacer 40px

::: blurb
**[Open the full visualization](https://data4thepeople.github.io/PPI_analysis/dist/index.html)** **for a larger view and dark mode.**
:::

::: spacer

## Purpose

::: spacer

This chart breaks the Producer Price Index for final demand into every item the Bureau of Labor Statistics (BLS) weights in it, about 820 in a typical month, and shows how much each one added to or took away from the 12-month change. It covers every month from October 2016 to September 2026. It is free to use and needs no sign-in. It is the companion to our [CPI Hot Air Balloon](https://www.data4thepeople.com/p/what-is-driving-cpi), which does the same for consumer prices.

The Producer Price Index (PPI) measures the prices U.S. businesses receive for what they sell. "Final demand" is the part sold to final buyers: households, businesses buying equipment, governments and buyers overseas. It covers goods, services and construction. It is not what consumers pay at the register, and it includes the margins that wholesalers and retailers earn, which is why items such as "car dealers' margins" appear in the chart.

::: blurb Read this first
Our items add up closely to BLS's published figure from July 2022 on. Before that, they miss by more, because BLS published its indexes rounded to one decimal place until July 2021. We show every month anyway. The note under the chart says whether each month passes our own tie-out test, and if not, why. About 1% to 2% of final demand has no published price index in recent years, and 6% to 9% did before 2021. We estimate those items from their parent category, and the chart marks them.
:::

## Using the visualization

::: spacer

**1. Press Play.** The diver moves through every month from October 2016 to September 2026. The 1x, 2x and 4x buttons set the speed. The space bar starts and stops it.

**2. Pick a month.** Drag the slider, use the ‹ and › buttons, or press the left and right arrow keys to move one month at a time.

**3. Point at a piece.** On a computer, move your mouse over it. On a phone or tablet, tap it. A box shows the item's name, how many points it added to or took away from the 12-month change, its price change and its weight. If the item has no published index for those months, the box says so and names the category it was estimated from.

**4. Read the numbers in the top left.** They show BLS's index for the month and a year earlier, the 12-month change those give, what our items add up to, and both figures rounded to one decimal place.

**5. Read the note under the chart.** It says whether the month passes our tie-out test, and if it does not, why.

**6. Switch to the table.** The Table button lists every item for the month. Click a column heading to sort by it.

### How to read it

- **Depth.** The diver sits as deep as the 12-month change in PPI final demand, on the scale at the right. Deeper means more inflation. The scale runs from −2% to 12% and is the same in every month. The water gets darker as the diver goes deeper, and a shark swims by when the rate is above about 5%.
- **Anchors.** Items that added to the 12-month change hang below the diver, pulling it deeper.
- **Floats.** Items that took away from it float above the diver, lifting it up.
- **Size.** The area of each piece is how many percentage points the item added or took away. One size scale is used for every month, so pieces can be compared across months.
- **Color.** The item's own price change over the 12 months, from blue (its price fell) to red (its price rose).
- **Dashed ring.** BLS publishes no index for the item in those months, so we used its parent category's price change. Its color shows that estimated change.
- **Gray circle.** The part of BLS's published change that our items do not add up to. Point at it to see its size.
- **Labels.** The five largest anchors and floats are labeled on wider screens.
- **Date axis.** The shaded months are the ones where BLS published its index to one decimal place. An amber dot marks every month that misses our tie-out test.
- **Preliminary months.** BLS revises the PPI for four months after it first comes out. June to September 2026 are preliminary and will change.

### What it shows right now

In September 2026, PPI final demand was 6.3% higher than a year earlier. BLS's index was 159.613, against 150.100 in September 2025. Our 823 items add up to 6.350%, which is 0.012 points more than BLS's figure, so the month passes our tie-out test. Of those items, 117 had no published index for the months needed, and they carried 1.6% of final demand.

Gasoline added the most, 0.76 points, with a price 66.1% higher than a year earlier. Fuel retailing margins took away the most, 0.12 points.

Over the 10 years, the 12-month change peaked at 11.7% in March 2022. It was lowest in April 2020, at −1.5%, one of five months in 2020 when it was below zero.

Tomorrow we will walk through five takeaways from the September numbers.

## What this page is

::: spacer

Every chart we publish should be something you can check, question and rebuild yourself. This page documents how we built this one: where the data comes from, every step we took, and the judgment calls we made. The code, the data and the built files are in a public repository, linked at the end.

## The data sources

::: spacer

**Producer Price Index, U.S. Bureau of Labor Statistics.** Monthly index values, not seasonally adjusted, for final demand (series WPUFD4) and for every commodity in it. We also use the indexes for final demand goods, services and construction for a few items with no category above them (Step 3). We download BLS's full PPI data files.

**Relative importance of commodities in final demand, U.S. Bureau of Labor Statistics.** Each commodity's share of final demand as of each December, in a spreadsheet BLS posts each year. We use the files for 2014 to 2026.

## How we built it

::: spacer

### Step 0: What BLS does before we get the data

We start from published figures, so their limits are our limits.

BLS builds the PPI from prices that businesses report to it each month. It weights each commodity by how much of it is sold to final buyers, using census data on what businesses ship and government tables of who buys what. BLS updated those weights four times in these 10 years, each in January: 2018, 2021, 2023 and 2026.

BLS revises each month's PPI for four months after it first comes out. It published index values to one decimal place until July 2021, and to three decimal places from then on. It did not go back and add decimals to the older figures.

BLS does not publish an index for every commodity it weights. Some are withheld because too few companies report to publish one without revealing a company's prices. Others stopped being published partway through, such as processed eggs after January 2022 and military aircraft after May 2024.

### Step 1: Use the same method as the CPI Hot Air Balloon

An item's contribution is its weight times its price change. BLS sets new weights each December, so we split each 12-month period at December. For the months before December, we use the previous December's weights, moved forward the way BLS does it as prices change. For the months after, we use the new December's weights. Added together, the two parts give each item's contribution to the 12-month change. If every item had a published index, the contributions would add up exactly to BLS's published change.

### Step 2: Build the list of items each December

The commodity codes nest inside each other. The most detailed codes, the ones BLS assigns weights to, are the items in the chart. The list changes from year to year: 848 items in December 2013 and 783 in December 2025. Each part of the 12-month period uses its own December's list, so a month shows between 808 and 860 items.

When BLS gives an item a new code but keeps its name, the chart shows it as one item. We found 21 of these over the 10 years, including four leather items that BLS moved to a new group in its index files.

### Step 3: Estimate the items with no published index

For an item with no index for the months it needs, we use the price change of the nearest category above it that has one. For example, other metal ores uses the change for nonferrous metal ores.

This differs from the CPI Hot Air Balloon. There, a missing item gets the part of its category's change that the category's other items do not explain. That works in the CPI because a category's index is built from its items with the same weights the headline uses. In the PPI it is not. A PPI category's index is weighted by everything businesses sell, while final demand counts only the part sold to final buyers, and that part differs from item to item. When we tried the CPI approach, it gave results such as a 195% drop in processed egg prices in December 2025. So we chose the category's own change. We made that choice on method, not because it made the totals match better.

A few items have no published category above them at all, such as finished leather and luggage. They use the change for final demand goods, services or construction. Using what final demand itself leaves unexplained would force every month to match and hide the error.

Some seasonal items, such as melons, have a published index in some months but not in December, which the method needs. Their contribution is estimated the same way, but their color shows their own published 12-month change.

### Step 4: Fill weights BLS printed as zero

In December 2019, December 2021 and December 2024, BLS printed 0.000 for a few items that had weight the year before, and the weights no longer added to 100%. They added to 99.78%, 99.80% and 99.96%. The missing items include farm tractors, locomotives and ships. For those items we carried the previous December's weight forward, moved by price change the way BLS does it. We checked these against what BLS printed for the same December a year later, where it did: farm tractors 0.120% (BLS later printed 0.116%), locomotives 0.073% (0.073%) and ships 0.022% (0.023%).

### Step 5: Pick the months

The chart shows 10 years, October 2016 to September 2026. Before we looked at any results, we set three rules a month must meet to pass our tie-out test:

1. Both of BLS's index values in the 12-month change were published to three decimal places.
2. Our items add up to BLS's published change within 0.05 points, half of the 0.1 point BLS rounds its 12-month changes to.
3. Items with no published index carry 10% of the weight or less.

We show every month, including the ones that fail, and flag those that do.

### Step 6: Check the numbers

The 51 months from July 2022 to September 2026 pass. In those months, our items are off from BLS's figure by 0.013 points on average, and by 0.040 points at most (May 2026). In 42 of them, they are within 0.02 points.

The 69 months from October 2016 to June 2022 are flagged, all because the index a year earlier was published to one decimal place. Rounding to one decimal can move a 12-month change by up to about 0.09 points by itself. Thirty-three of those months also miss by more than 0.05 points, by as much as 0.26 points in October 2019. The months from July 2021 to June 2022 land within 0.05 points, but because the earlier index was rounded, a close match there may be luck.

In 21 months, from November 2016 to January 2021, the miss is larger than rounding of BLS's headline index can explain by itself. The note under the chart says so in those months. The rest very likely comes from the estimated items, which carried 6% to 9% of the weight before 2021, together with rounding in the item indexes, which were also published to one decimal place then.

In 50 of the 120 months, our items round to a different one-decimal figure than BLS's. The chart shows both.

A script recomputes BLS's published 12-month change from the raw data files and checks that the pieces drawn in the chart, including the gray circle, add up to it in every month. A second check, written separately from the raw files without using our scripts, reached the same totals within 0.0003 points, the same item contributions, and the same pass or fail result in all 120 months. It also found that estimated items were colored by a figure that was not a price change. We fixed that before publishing.

### Step 7: Draw the chart

The depth scale and the size scale are fixed once, from all 120 months, so every month is drawn on the same scales. The chart is one self-contained web page with no outside code.

## Updating

::: spacer

BLS releases the PPI each month and revises the last four months each time. We plan to add each new month when it comes out. Every number in the chart is computed by the build scripts.

## Honest notes and limitations

::: spacer

**A contribution is not a cause.** It shows how much an item moved the published number. It does not explain why the item's price changed.

**This is not consumer inflation.** The PPI measures prices businesses receive, including wholesale and retail margins, and it includes exports. It does not include imports. For prices consumers pay, see the [CPI Hot Air Balloon](https://www.data4thepeople.com/p/what-is-driving-cpi).

**The months before July 2022 do not tie out as closely.** BLS published one-decimal indexes then, and the estimated items carried more weight. We show those months and flag them rather than leave them out.

**Estimated items are less reliable.** About 1% to 2% of final demand had no published index in recent months, and 6% to 9% before 2021. Each of those items moves with its category, which may not match its own price.

**The 2026 gap runs one way.** In every month of 2026 so far, our items add up to a little more than BLS's figure, by 0.012 to 0.040 points. We have not found the cause.

**Some weights are our estimates.** The weights we filled in for December 2019, 2021 and 2024 are close to what BLS later printed but not the same.

**Recent months will change.** June to September 2026 are preliminary.

**The data is not seasonally adjusted.** Seasonal items, such as fresh fruit and vegetables, can swing widely from one month to the next.

**No error bars.** We have not used any measure of sampling error, so small differences between items should not be read as real.

## Reproduce it yourself

::: spacer

The code, the build steps and the published files are at [github.com/Data4ThePeople/PPI_analysis](https://github.com/Data4ThePeople/PPI_analysis). You need BLS's PPI data files, the final demand relative importance files for 2014 to 2026, and Python. The [README](https://github.com/Data4ThePeople/PPI_analysis#readme) lists the steps in order, [DATASETS.md](https://github.com/Data4ThePeople/PPI_analysis/blob/main/DATASETS.md) explains every source and its limits, and [TIEOUT.md](https://github.com/Data4ThePeople/PPI_analysis/blob/main/TIEOUT.md) lists the tie-out for every month. One row per month is free to download as [monthly_summary.csv](https://raw.githubusercontent.com/Data4ThePeople/PPI_analysis/main/data/processed/monthly_summary.csv). If you get a different number from us, tell us, and we will look.

::: divider

## Common questions

::: spacer

### What is the PPI Scuba Diver?

An animated chart of every item in the Producer Price Index for final demand. The diver sits as deep as the 12-month change. Items that added to it hang below as anchors, and items that took away from it float above. It covers every month from October 2016 to September 2026.

### What is PPI final demand?

The Producer Price Index for final demand measures the prices U.S. businesses receive for goods, services and construction sold to final buyers: households, businesses buying equipment, governments and buyers overseas. BLS publishes it each month as series WPUFD4.

### How is the PPI different from the CPI?

The CPI measures prices consumers pay. The PPI measures prices businesses receive, including wholesalers' and retailers' margins and sales to businesses, governments and buyers overseas. Our [CPI Hot Air Balloon](https://www.data4thepeople.com/p/what-is-driving-cpi) shows the CPI the same way.

### What is driving PPI right now?

In September 2026, PPI final demand was 6.3% higher than a year earlier. Gasoline added the most, 0.76 points, with a price 66.1% higher than a year earlier. Fuel retailing margins took away the most, 0.12 points.

### Why do some months miss your tie-out test?

Before July 2021, BLS published its indexes rounded to one decimal place, which can move a 12-month change by up to about 0.09 points. More items also had no published index then. Every month from July 2022 on passes. We show the earlier months and flag them.

### What does the gray circle mean?

It is the part of BLS's published change that our items do not add up to. With it, the pieces add up to BLS's figure exactly. It is small from July 2022 on.

### What does a dashed ring mean?

BLS does not publish an index for that item in those months. We used the price change of the category above it, so its color is an estimate.

### Why does the chart show "margins"?

Final demand includes the services that wholesalers and retailers provide, measured by their margins: what they sell an item for, less what they paid for it. When margins shrink, they pull the PPI down even if the goods themselves cost more.

### Is the data seasonally adjusted?

No. We use the data that is not seasonally adjusted, the same data BLS uses to move its weights forward from one December to the next.

### How often is the chart updated?

Each month, after BLS releases the PPI.

### Can I embed the chart?

Yes. It is free to use and embed. Add #embed=1 to the end of the full visualization's address for the 780-pixel version shown on this page.

### Where does the data come from?

The U.S. Bureau of Labor Statistics: monthly PPI index values for final demand and every commodity in it, and the relative importance tables that give each commodity's share of final demand.
