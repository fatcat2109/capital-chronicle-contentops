# What happened when the stop followed daily closes

The trailing exit earned more per trade and won less often in our six-market historical test.

We found that a stop following daily closes earned the most on average in our historical exit test. It also won less often than every version with a fixed target. The test held the entry rule constant, so we can compare the exits directly.

## What we held constant

The sample spans November 2016 to November 2026. We took signals with the trend every fifth session, both sides together. Simulated trades could overlap.

The stop distance was 1.5 normal days, and each version could run up to 10 sessions, both sides together. A normal day is the average daily range over 14 sessions, including gaps. The test charged 0.05 of a normal day for each round trip.

The fixed versions closed at the target, the stop or the end of the holding window. The trailing version moved its stop after a favourable close and kept it there through any reversal.

## What each exit earned

Each comparison used 1888 simulated trades, both sides together. R is the initial stop distance. The averages below are after the test's estimated cost.

The widest fixed exit averaged 0.068R per trade, both sides together. The trailing stop averaged 0.117R per trade, both sides together. A trailing stop can leave a move running and still give back part of its gains before it closes the trade.

## Where the comparison is fragile

Gold, shares and Bitcoin rose over the decade. The pooled result can reflect that rise and the mix of markets and directions. The wider study examined 54 market-and-rule combinations, giving luck more chances to make a result look strong.

Daily bars leave the order of intraday touches uncertain. The test used one round-trip cost across markets, even though gaps and trading costs vary. A later sample would show whether the difference persists.

## So what

Compare exits by average return after costs as well as win rate. Our sample gives those two measures different rankings.

These are hypothetical historical tests. Read [how we measure historical odds](https://capitalchronicle.substack.com/p/how-we-measure-a-trading-rule-before) for the full design and its limits. Table fingerprint `4462cfd99426679c0b31a2c1a01291fd39a28d3af5da4810677a7523208ade41`.

Capital Chronicle offers analysis only, not financial advice or recommendations.

Capital Chronicle may hold positions in the markets it covers.
