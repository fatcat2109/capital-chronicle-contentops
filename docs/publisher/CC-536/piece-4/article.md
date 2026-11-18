# What a tight stop cost in our historical test

A fixed charge weighed most on narrow stops, and daily prices left the order of some exits uncertain.

We found that the tightest stop lost the most in our six-market test. The fixed trading charge took a larger share of the initial stop distance, and more daily bars reached both exit levels.

The sample spans November 2016 to November 2026. Each width used 1893 trade observations, both sides together. Trades can overlap, so the observations are dependent.

## What we held fixed

The test took a trade with our trend rule every fifth session, counting both sides together. The target was 2R, and the hold lasted up to 5 sessions.

A normal day is the average true range over 14 daily bars. The study charged 0.05 of a normal day per round trip. R is the initial stop distance, and the averages include costs.

## What changed as stops moved out

At 0.3 normal days, both sides together averaged -0.213R per trade. The assumed round-trip cost at that width was 0.17R. This was also the width most often affected by a daily bar spanning both exits.

At 0.5 normal days, both sides together averaged -0.029R per trade. At 1.0 normal day, both sides together averaged 0.02R per trade. The next wider setting had the same rounded mean, and the widest settings stayed close to flat.

The cost assumption stays fixed in normal days. Its cost in R changes because a wider stop increases the price distance that R represents.

## What the daily bar leaves open

When a bar reached both exit levels, we counted the stop first. A daily bar shows the range, so the actual order remains unknown. The tightest stop was most sensitive to that choice.

Gold, shares and Bitcoin rose over the decade, which can help trades that follow upward trends. The wider study examined 54 market-and-rule combinations, increasing the chances of a result that appears to pay by luck. Futures roll gaps and the next-open proxy for the euro and yen close also affect the historical sample.

So what: We treat the narrowest result as evidence to question how cost and price noise are modeled. The pooled figures give a historical comparison across widths, with market-specific stop choices still open.

These are hypothetical historical tests. Read [how we measure historical odds](https://capitalchronicle.substack.com/p/how-we-measure-a-trading-rule-before) for the test design and its limits. The figures come from our audited historical table. Table fingerprint `4462cfd99426679c0b31a2c1a01291fd39a28d3af5da4810677a7523208ade41`.

Capital Chronicle offers analysis only, not financial advice or recommendations.

Capital Chronicle may hold positions in the markets it covers.
