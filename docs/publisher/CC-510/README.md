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

Publisher-B delivered `72cb1b12372586c2772d4c3b836475a4f0698e28` without a live
consumer tick, Telegram send, schedule change, Main edit or application restart.

The first Publisher stream integrated it with CC-509 at
`d346c0d688cdc41f5238d5384a0c7a3f111f0595`, from the current operating HEAD
`0f96aee9a23eb888eba98f4eb7dd65347f124b96`. Both quote supplementation and
base-rate collection remain in the mobile fact collector. The phone formatter
preserves the elapsed age for quotes and adds the base-rate cutoff label.
[integration.json](integration.json) records the launch configuration, source
hashes, preserved uncommitted files, live tag and rollback tag. Runtime model and
effort telemetry remain unavailable; launch arguments were `gpt-6.1-sol / max`,
labelled `CONFIGURED_NOT_OBSERVED`.

[installed-tests.xml](installed-tests.xml) records 140 passing targeted checks
from `A:/Capital Chronicle/ContentOps` in 55.87 seconds, using one pytest process.
The added combined-source test proves that a current quote and both historical
horizons enter the same candidate and ranking input, with the larger base-rate
sample first. Unit tests inject their statistics producer rather than reading
the live Data store. No schedule or application was changed.

[installed-producer-readback.json](installed-producer-readback.json) contains 12
real producer answers for the six explicit fixture conditions and both horizons,
with no gaps. One Bitcoin query took 2.33 seconds; all others took less than two.
These fixture queries read held history; they are not a natural phone delivery.

[installed-consumer-readback.json](installed-consumer-readback.json) records the
existing minute consumer after installation. The 19:33 GMT+7 run supplied one
eligible target to the actual ranker. That target had no supported move condition,
so no base rate was requested. The ranker rejected its session fact as
`NO_ADDED_FACT_ABOVE_QUALITY_FLOOR`; no writer or send ran. No manual tick or
replacement scheduler was added, and no score, target clock or source was changed.

The code is live. The remaining acceptance evidence is
`BASE_RATE_PHONE_PROOF_PENDING`: the next natural private draft using a base rate
must show its count, period and `Fact: base rate through <date>`. The observed
cause is `NO_MATCHING_MOVE_HEADLINE_IN_OBSERVED_TARGETS`. The existing minute
consumer continues this path; no person action or Ops review is pending.

The [14 November readback](resume-20261114/readback.json) supersedes that initial
absence-of-headlines diagnosis. It found three confirmed phone
deliveries since installation, all using session facts and none using a base
rate. There are no uncertain delivery rows in that interval. The read occurred
on 14 November at 01:38 GMT+7; the latest stored consumer run ended at 01:36.

The [saved ranking scan](resume-20261114/ranking-scan.json) examined 505 actual
ranking prompts. CC-481's counts reached eight distinct targets across 41
appearances; three attempts passed the existing quality floor. The Bitcoin
writer omitted a target because daily-loss counts did not answer its annual
return claim. A gold target's run failed with `CODEX_EXIT_1`. The third target
received a session-fact draft, confirmed as phone message 5. Other statistics
targets remained below the quality floor. These are observed editorial results,
not a source-collection failure or a reason to retry an expired target.

The live adapter, collector, ranker and fact-policy files match this worktree.
No production code changed in this continuation. The earlier six-market tests,
12 producer answers and 3/109 replay remain the implementation evidence; no
pytest or editorial call was repeated. The readback used SQLite `mode=ro` and
saved runtime artifacts. It made no model, transport or manual consumer calls,
changed no schedule and restarted no application. It exports no retained X
text, chat identity, credentials or raw model response.

`BASE_RATE_PHONE_PROOF_PENDING` remains the sole unfinished acceptance step:
read the next natural delivery using a base rate, then verify its count,
historical period and `Fact: base rate through <date>`. The existing minute
consumer supplies that opportunity; no person action or Ops review is needed.
The unchanged source remains live while that observation is pending. Reproduce
the bounded saved-evidence read with
`python docs/publisher/CC-510/resume-20261114/readback.py`.

The [follow-up readback at 01:53 GMT+7](resume-20261114/followup-20261113T185340Z/readback.json)
on 14 November found the same three confirmed session-fact deliveries and zero
base-rate deliveries. Its latest stored consumer result ended at 01:50 GMT+7
with `NO_NEW_ELIGIBLE_TARGETS`. The bounded saved-prompt scan still has eight
statistics targets, 41 appearances and three quality-floor passes, with zero
scan errors. All four installed source files still match the lane. CC-510 stays
OPEN for the natural phone observation. No production code, editorial call,
transport call or manual consumer tick was needed, so the accepted targeted
tests were retained. This continuation's observed launch arguments were
`gpt-6.1-sol / max`, labelled `CONFIGURED_NOT_OBSERVED` in the readback.
