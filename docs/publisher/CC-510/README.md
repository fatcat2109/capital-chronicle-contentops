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

The [02:02 GMT+7 readback](resume-20261114/followup-20261113T190229Z/readback.json)
on 14 November again found three confirmed session-fact phone deliveries and
zero base-rate deliveries. The latest stored consumer run ended at 02:01 GMT+7
with `NO_NEW_ELIGIBLE_TARGETS`. Eight statistics targets, 41 appearances and
three quality-floor passes remain recorded, with no scan errors. All four
installed source files match the lane; the existing 140 passing installed
tests remain applicable. This continuation made no production-code, model,
transport, manual-tick or schedule change. Its verified launch arguments were
`gpt-6.1-sol / max`, recorded as `CONFIGURED_NOT_OBSERVED`. CC-510 remains OPEN
for the next natural base-rate phone delivery with its count, period and cutoff.

## Completion readback — 17 November 2026

The [saved delivery readback](resume-20261117/readback.json) closes the remaining
acceptance step. Of the three deliveries Ops named on 16 November, the third
used a base rate: private message **9**, delivered at `2026-11-15T19:40:46Z`
(16 November, **02:40:46 GMT+7**). Eight deliveries are confirmed since the
original installation; one uses a base rate and none is uncertain.

The exact saved Bitcoin draft says **949 of 1,750** higher next-session closes
after daily losses, over **2016-11-10 to 2026-11-14**. Its saved `stats_after`
answer supplies both counts. Rebuilding the source from that answer reproduces
the bound source identity and hash. The send-time market, condition, horizon,
completed-day and draft checks all pass, with delivery 6.19 minutes after the
target post. No history was recounted and no producer query was repeated.

The unchanged production formatter supplies these fact lines:

```text
Fact: base rate through 2026-11-14
949 of 1750 higher next-session closes after daily losses (desk count, 2016-11-10 to 2026-11-14)
```

This is a Bot API-confirmed delivery joined to its exact saved pack and
send-time fact binding. The fact lines replay the formatter, whose function
matches the original installation. It does not observe Jim opening his phone
or independently read the Telegram message body. The private draft has not
been claimed as a public reply.

[targeted-tests.xml](resume-20261117/targeted-tests.xml) records **40 passing
tests**, run from the operating root in one pytest process, in 15.84 seconds.
They include six-market collection, wrong-market and wrong-condition refusals,
and the collector-to-ranker-to-pack-to-message path. The accepted 12 November
replay remains **3 of 109** previously refused targets supplied to ranking with
a base rate; this evidence closeout changes no production source or replay
assumption. All four installed source files match the lane.

The run used the current operating HEAD as its base and preserved all eight
pre-existing tracked work-in-progress files across the lane and operating root.
It made no model, producer, transport or manual consumer calls, changed no
schedule and restarted no application. The launch explicitly configured
`gpt-6.1-sol / max`, recorded as `CONFIGURED_NOT_OBSERVED` in
[run-context.json](resume-20261117/run-context.json). The operating-root merge
and live/rollback tags are recorded in
[integration.json](resume-20261117/integration.json).

Reproduce only the saved-evidence checks with
`python -X utf8 docs/publisher/CC-510/resume-20261117/readback.py`.
