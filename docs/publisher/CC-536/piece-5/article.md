# What waiting to enter cost in our historical test

In our historical test, the next open earned the most per signal. A nearby stop entry earned the most per fill.

We found that entering at the next open earned the most per signal in our six-market historical test. The nearer stop entry did best among trades that filled. Waiting changed which signals turned into trades.

## What counted as an entry

The sample spans November 2016 to November 2026. We took signals with the trend every fifth session, both sides together. Simulated trades could overlap.

Market entry used the next open. A limit waited for a better price. A stop entry waited for price to move farther in the signal’s direction. Pending orders waited up to 3 sessions, both sides together.

A normal day measures the average range over 14 daily bars, including gaps. We fixed that measure at the signal close. We used a trailing stop of 1.5 normal days and held up to 10 sessions, both sides together. The test charged 0.05 of a normal day per round trip.

## What the orders earned

R is the initial stop distance. Per-fill averages use the trades that filled. Per-signal averages include unfilled orders at zero.

The next open filled all 1888 signals, both sides together. It averaged 0.117R per signal and 0.117R per fill.

The limit at 0.5 normal day better had 1154 fills, both sides together. It averaged 0.058R per signal and 0.096R per fill. At 1 normal day better, the limit had 658 fills, both sides together. It averaged 0.019R per signal and 0.055R per fill.

The stop entry at 0.5 normal day farther had 1190 fills, both sides together. It averaged 0.109R per signal and 0.173R per fill. At 1 normal day farther, the stop entry had 708 fills, both sides together. It averaged 0.049R per signal and 0.13R per fill.

## What daily prices leave open

A fill counted from the day it occurred. The test allowed an exit on that same bar. Daily prices leave the order of those intraday moves uncertain. The model used a single cost assumption across all six markets.

Gold, shares and Bitcoin rose over the decade. The wider study examined 54 market-and-rule combinations, giving luck more chances to make a result look strong. Futures roll gaps and the euro and yen close proxies also affect the sample.

So what: Judge a waiting order over all the signals it receives. A stronger average among completed trades can hide the opportunities it skipped.

These are hypothetical historical tests. Read [how we measure historical odds](https://capitalchronicle.substack.com/p/how-we-measure-a-trading-rule-before) for the design and its limits. Table fingerprint `4462cfd99426679c0b31a2c1a01291fd39a28d3af5da4810677a7523208ade41`.

Capital Chronicle offers analysis only, not financial advice or recommendations.

Capital Chronicle may hold positions in the markets it covers.
