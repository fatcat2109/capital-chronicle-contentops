# Five sessions did not settle the trend question

The long side looked stronger, but the benchmark and later-half results still matter.

We find a stronger historical record for buying rising markets than for shorting falling ones, even over a short holding period.
That does not make five sessions a general recipe: the always-long comparison and later-half results still matter.

The euro and yen are now included after a repair to the currency feed's daily closes.
Their close uses the next session's open, a proxy rather than an independently observed closing quote.
The [method page](https://capitalchronicle.substack.com/p/how-we-measure-a-trading-rule-before) explains the original test and its limits.
These are hypothetical historical tests, rather than our trade results.

## Same horizon, different rules

For both rules, the maximum holding period is 5 sessions.
The with-trend stop is 1.5 normal days; the against-trend stop is 1 normal day.
Both target 2R and enter at the next open after the signal.
Different stop widths mean this comparison changes more than direction.

The rising yardstick requires price above its levels 20 and 60 sessions earlier.
It also requires price above its 20-session and 50-session simple averages; falling signals reverse those conditions.
Mixed signals produce no entry.
A normal day uses the average true daily range over 14 sessions.
The assumed round-trip cost is 0.05 normal day.
R means each trade's initial stop distance; means include the assumed cost.

## Following the trend, with the benchmark beside it

Each cell gives that rule's trade count, then its mean net R per trade.
Always long enters whenever free, with the trend rule's stop, target and holding period.
Its entry dates and denominator differ from the conditional rules.

| Market | Trend long (trades; mean R) | Trend short (trades; mean R) | Always long (trades; mean R) |
|---|---:|---:|---:|
| Gold futures | 230; 0.109 | 119; -0.055 | 476; 0.087 |
| Oil futures | 180; 0.115 | 153; -0.092 | 476; 0.001 |
| S&P 500 futures | 301; 0.032 | 77; -0.155 | 476; 0.093 |
| Bitcoin | 281; 0.197 | 218; -0.048 | 704; 0.086 |
| Euro / US dollar | 162; -0.026 | 185; -0.079 | 480; -0.035 |
| US dollar / yen | 214; 0.032 | 119; -0.099 | 461; 0.03 |

Bitcoin's trend-long mean was 0.32R in the first half and 0.05R in the later half.
Its trend-short mean changed from 0.01R to -0.09R.
The halves split at the fixed calendar midpoint, 2021-11-10.
Gold and oil trend-long means were also positive in both halves.
The S&P trend-long mean fell to -0.06R in the later half.

Gold's always-long result was positive too, and the S&P always-long mean exceeded the trend-long mean.
Being long at all paid in those rising markets; a trend filter gets no automatic credit for that drift.

## Going against the yardstick

These are separate side records, with the tighter stop described above.
Each cell again gives trades, then mean net R per trade.

| Market | Against-trend long (trades; mean R) | Against-trend short (trades; mean R) |
|---|---:|---:|
| Gold futures | 119; -0.013 | 230; -0.154 |
| Oil futures | 153; 0.013 | 180; -0.265 |
| S&P 500 futures | 77; 0.015 | 301; -0.143 |
| Bitcoin | 218; 0.04 | 281; -0.169 |
| Euro / US dollar | 185; 0.017 | 162; -0.094 |
| US dollar / yen | 119; 0.068 | 214; -0.112 |

The short side lost on average in every market under both rules.
The positive full-period against-trend long means were negative in the earlier half, except for the S&P, which lost later.
None supplies a clean argument that fading the trend worked everywhere.

## The denominator and the limits

Gold, oil, S&P and euro samples span 2016-11-14 through 2026-11-10.
The yen sample spans 2016-11-11 through 2026-11-09.
Bitcoin spans 2016-11-12 through 2026-11-10, including weekends.
Each table cell belongs to its own count and that market's period.

The audited table examined 54 market-and-behaviour rows.
Looking across many rows makes attractive results possible by chance.
The decade favoured rising gold, shares and Bitcoin, while repeated market conditions make trades dependent.
Daily bars leave intraday order uncertain; continuous futures also carry contract-roll risk.
The uniform cost assumption is not a record of actual fills.

So what: five sessions did not turn the trend into a universal edge.
Keep each side's count, its benchmark and its weaker half beside the attractive average.
These results are historical comparisons, not a probability for the next trade or a current entry signal.

Table fingerprint: `4462cfd99426679c0b31a2c1a01291fd39a28d3af5da4810677a7523208ade41`.

Capital Chronicle offers analysis only, not financial advice or recommendations.

Capital Chronicle may hold positions in the markets it covers.
