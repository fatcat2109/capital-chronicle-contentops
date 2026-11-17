CC-489 supplies the existing TradingView price-scale check with held minute
prices. The reader prefers a timed price in Main's minute plan-status export,
then an exact-instrument M1 close in CC-481's existing SQLite store, then CC-509's
public quote, then Main's saved tick. `DurablePublicationCoordinator` remains the publication
owner. No terminal, broker API, application or schedule is started or changed.

Every new reference records its source, source hash, observation time, known-at
time, age at comparison and age at image capture. A bar also retains its exact
row hash and start/end. The mutable database is opened read-only and closed after
each bounded read. Its raw broker prices remain in runtime image metadata; the
source-readback artifact here omits the price value and all account fields.

The export reader accepts an explicitly timed `last_price` or an exact-instrument
`quote`/`last_quote`. A plan level, entry, export generation time or check time
cannot stand in for a quote's observation time. At the initial installation the
export had none of these price fields; the 14 November readback below supersedes
that source state. The bar reader uses native M1 rows, excluding a forming bar,
an invalid bar, a proxy contract and a source learned after the image was taken.

CC-463's 120-second comparison window and closed-market rule remain: the S&P 500
cash index outside 09:30–16:00 ET uses the last close; the other non-Bitcoin
markets use the common weekend close. Both capture age and comparison age are
recorded, so a Friday close is not described as a fresh weekend quote. The
existing regular-session rule does not infer holidays or early closes.

A missing, stale or unreadable source becomes a named source attempt and the
chart remains `NOT_COMPARED`. WTI keeps the plain chart when its basis cannot be
measured. An actual excessive difference still refuses the image, before any
WTI level translation. A measured mismatch cannot be erased by choosing a second,
more convenient source. Existing issued checks, requests, public objects and
recovery paths retain their exact bindings.

The chart service adds its compared checks and measured refusals to the existing
`tradingview_snapshot_outcomes_v1.jsonl`. Publication still records the accepted
check in the existing `published_images_v1.jsonl`. No new ledger or observer job
is added. The read-only [audit](../../../scripts/audit_chart_prices_cc489.py)
deduplicates destination copies and readbacks, excludes reservations, and requires
a completed newsroom day before reporting the 95% result. Every remaining chart
names its cause. A missing-quote refusal fails the daily result.

The same audit reports each market's observed differences over a specified
72-hour window, including measured refusals. A completed window and three distinct
ET dates are required to describe a three-day sample. With no such sample, the
actual limits remain the approved starting values:

| Market | Current absolute difference limit |
| --- | ---: |
| Gold | 0.15% |
| S&P 500 | 0.15% |
| EUR/USD | 0.15% |
| USD/JPY | 0.15% |
| WTI | 0.40% |
| Bitcoin | 0.40% |

These are **not three-day-calibrated limits**. Inventing observations or widening
them from unmatched clocks would defeat the check. The audit reports the sample
count, dates, maximum, 95th percentile, closed-market counts and excesses for each
market, beside its current limit.

Build verification: [59 initial checks](price-reference-tests.xml) passed. The
[58 reader, capture and audit checks](reference-audit-capture-tests.xml) include
the real coordinator and image register, all six markets, malformed/stale/missing
sources, closed-market comparisons, known-at boundaries, observed-day coverage,
three-day sample accounting and unchanged publication with no quote. Tests use
temporary stores and controlled transports only. The launch arguments were
`gpt-6.1-sol/max`, recorded as `CONFIGURED_NOT_OBSERVED` in [build.json](build.json).

[Source readback](source-readback-before-integration.json) found no usable
reference for any of the six markets: Main's minute export omits the price; the
native M1 rows end on 10 November; no matching saved tick is available. The
smallest upstream change is a timed exact-instrument last quote in the existing
minute export, or refreshed native M1 rows from its Data owner. Publisher's
reader and publication consumer are ready to use either without another change.

The operating root fast-forwarded to code commit
`465178811b01979a2732364d8891025960ad5610` on **12 November 05:07:32 GMT+7**.
Both `contentops-live-20261112-cc489` and
`contentops-rollback-20261112-cc489` are pushed. All seven delivered Python files
match their committed Git blobs. The two worktree telemetry files and six
unrelated dirty operating-root files retain their initial hashes.
[Integration evidence](integration.json) records these checks and the original
operating HEAD. [All 69 installed tests](installed-tests.xml) pass from that root.

The existing [minute task](installed-task.json) still uses `pythonw.exe` and
`-B scripts\plan_status_posts.py --publish` in the same operating root. The
[last logged consumer result](installed-consumer-readback.json) is OK with zero
queued rows, but its 05:04:48 GMT+7 run clock precedes installation. The task was
observed Running; its raw last-result code is retained. No completed run using
the new code, or new live compared chart, is claimed by this readback.

The [installed day audit](installed-day-audit.json) reports
`OBSERVATION_PENDING`: zero observed plan charts in the current production day,
zero missing-quote refusals, no three-day comparison sample, and all six current
references `NOT_COMPARED` with their precise causes. Zero charts cannot prove
95% coverage. The starting limits in the table remain explicitly uncalibrated.

The initial result was **BLOCKED: PLAN_STATUS_LAST_PRICE_NOT_EXPORTED / CHART_REFERENCE_STALE**.
Main can supply the timed exact-instrument price in its existing minute export;
alternatively Data can refresh the existing native M1 store. Once either source
is current, the installed reader consumes it automatically. A completed live
day and the actual three-day differences must then be read through the existing
register and outcomes with the audit command. No watcher, schedule change,
duplicate publication or request to Jim is needed.

## 14 November 2026 continuation

The two repairs are installed at code commit
`c0dc8be499fd0f6f632c52770eea774fc46ac26d`, applied at **01:17:58 GMT+7**.
Both `contentops-live-20261114-cc489` and
`contentops-rollback-20261114-cc489` are pushed. The existing minute task's
01:18:30 GMT+7 result is `OK`, with zero new rows queued. It still runs the same
`pythonw.exe -B scripts\plan_status_posts.py --publish` action in the operating
root. No task or application changed. See [integration](resume-20261114/integration.json)
and the [consumer run](resume-20261114/installed-consumer-run.json).

The coverage audit now deduplicates by original chart hash and capture clock.
One gold capture had eight publication records under six different work IDs;
the previous audit counted it six times. It now reports **one distinct chart,
compared once (100%)**, for the completed 12 November production day, with zero
missing-quote refusals. The records include Telegram, Discord, Threads and
Substack Notes. This establishes that day's coverage; it does not establish
six-market coverage. The 11 November day retains its failure and 13 November
has no observed plan chart. The [installed audit](resume-20261114/installed-live-audit.json)
retains the exact capture identity and input hashes.

The live source check also exposed a USD/JPY failure: Yahoo's `JPY=X` request
returns the canonical `USDJPY=X` symbol. The reader now requests `USDJPY=X`
and keeps exact symbol, instrument type, unit and clock checks. There is no
pair inversion or price conversion. A regression takes the canonical response
through the actual chart consumer and still rejects `JPYUSD=X`.

At **01:18:38 GMT+7**, the installed capture preparation and reader found usable
public references for gold, S&P 500, EUR/USD, USD/JPY and Bitcoin. Their ages
were 55.35, 2.50, 5.50, 2.50 and 3.50 seconds respectively. Main now exports
timed prices, but those held observations and the native M1 rows were stale.
WTI's Yahoo quote was 605.50 seconds old. A separate CNBC read of the correctly
identified NYMEX WTI contract was also about ten minutes delayed. Neither can
replace a two-minute reference. The named failures retain `NOT_COMPARED`;
missing data still never refuses a chart. Public objects and issued bindings
were not changed, and no new publication was made to manufacture evidence.

The three-day requirement remains incomplete. The held register, outcomes and
[42 retained metadata files](resume-20261114/retained-snapshot-search.json) contain
measurements on only 12 November ET. The available differences are:

| Market | Distinct measured captures | Maximum and p95 difference | Current limit |
| --- | ---: | ---: | ---: |
| Gold | 4 | 0.049055% | 0.15% |
| S&P 500 | 0 | Not observed | 0.15% |
| EUR/USD | 1 | 0.022541% | 0.15% |
| USD/JPY | 0 | Not observed | 0.15% |
| WTI | 0 | Not observed | 0.40% |
| Bitcoin | 0 | Not observed | 0.40% |

These remain starting limits, not limits calibrated over three days. The audit
names every market still lacking that sample. The original observation window
ends **15 November 05:07:32 GMT+7**; passing that clock alone cannot supply the
absent observations. Continue using natural chart checks and the existing
records; select a later actual observation window if this one lacks records.
A current native WTI observation from CC-479/CC-471 would remove its
remaining source gap without another Publisher change.

Verification: [47 initial checks](resume-20261114/targeted-tests.xml),
[81 source/audit checks](resume-20261114/source-audit-tests.xml), and the same
[81 installed checks](resume-20261114/installed-tests.xml) passed, one pytest
process at a time. They include the real chart/publication consumers, distinct
capture counting, absent quotes, the wrong pair and the unchanged source limits.
The configured launch is `gpt-6.1-sol/max`, `CONFIGURED_NOT_OBSERVED`.

CC-489 remains **BLOCKED: THREE_DAY_COMPARISON_SAMPLE_ABSENT**. The implementation
and repairs are live; the missing historical sample cannot be fabricated.
Next: read the existing audit after natural comparisons span three days for
each market, retaining the closed-market rule and WTI's exact source cause.
