# CC-510 — measured base rates in reply facts

The reply pack calls `x_reply_base_rates_v1.collect` once during mobile fact
collection. It asks the installed CC-481 `stats_after` owner for the target
market's stated daily-move analogue, over one and five completed sessions.
Publisher preserves the returned hits, denominator, source instrument, historical
period, outcome horizon and interval. It converts a headline's percent threshold
to the producer's logarithmic-return units; it computes no outcome or base rate.
A record headline uses an explicitly labelled prior-252-session daily-breakout
analogue, never a lifetime-record claim.

The CC-506 census contributes the target market's active measured rows and their
conditions to the writer's bound context, ordered by sample size. Its market rows
contain n and average R, not a win numerator. No numerator is inferred from those
averages or the pooled construction percentages. The desk's own trade record is
never read. Only the statistics producer's hits and n enter these reply facts.

The existing fact policy refuses another market, a mismatching condition, a
future or incomplete sample, and a draft that changes the count, condition or
forward horizon or outcome direction. Sources are resolved again with the original as-known query
before delivery. Statistics failures remain source-local; other held facts
continue. The private message adds `Fact: base rate through <date>`, with the
count and period below it. The existing approved editorial callers still write
the reply; this adapter supplies structured facts.

`final-tests.xml` records 122 passing targeted consumer, policy, pack and bot
checks in one pytest process, in 51.98 seconds. The later census-failure isolation
extension passed all 39 module checks (`source-local-tests.xml`). Earlier test
artifacts retain their checkpoint counts. Coverage includes collection through
ranking, pack build, exact source recheck and private-message formatting; all six
markets; both horizons; thin samples; market, condition and outcome mismatches;
foreign dollars; distinct indices/oils; unrelated subjects and release percentages.
The two older fixture edits isolate the new reader from production paths.

`producer-readback.json` records 12 real, read-only producer answers for six
explicit fixture conditions, across both horizons. There were no gaps; the
slowest statistics query took 0.445 seconds. Four markets also supplied active
census rows; WTI and USD/JPY had no active measured behaviour at that cutoff.
The census rows enter the same writer evidence context as the statistics facts.

`replay.json` covers 12 November 00:00 through 18:21:37 GMT+7: 503 saved minute
run results and 109 distinct targets. It recovers all 66 quality-floor targets
from their saved requests and all 43 no-fact targets from intake captured before
their original run. No retained X text is exported in this evidence.

| First cause | Distinct targets | Now supplied to ranking with a base rate |
|---|---:|---:|
| `NO_ADDED_FACT_ABOVE_QUALITY_FLOOR` | 66 | 3 |
| `NO_USABLE_FACT` | 43 | 0 |

The replay uses each original check clock and the producer's as-known history.
It captures the real ranking-input builder without invoking an editorial model,
writer or Telegram transport. These counts prove additional ranking evidence,
not a new quality score or a sent draft. The early targets predate the census's
knowledge clock, so their historical replay correctly uses only statistics.
Nasdaq and Brent are queried as their own markets. The bound statistics store
reported no D1 series for them; the Brent target retains
`NO_HELD_SERIES_IN_STORE:BRENT:D1`. Other facts continue.

Reproduce the bounded reads from this worktree:

```powershell
python docs/publisher/CC-510/replay.py
python docs/publisher/CC-510/replay.py --producer-check --output docs/publisher/CC-510/producer-readback.json
```

Publisher-B performed no live consumer tick, Telegram send, schedule change,
Main edit, deployment or application restart. Under CC-510's integration line,
the first Publisher stream merges onto its current operating HEAD, runs the
targeted checks and reads back the next real private draft. The backlog returns
to `OPEN (integrate ...)` with Owner `Codex Publisher`; there is no Ops review
step. The next phone draft using a base rate must show its count, period and
`Fact: base rate through <date>` before the item is DONE.
