CC-489 supplies the existing TradingView price-scale check with held minute
prices. The reader prefers a timed price in Main's minute plan-status export,
then an exact-instrument M1 close in CC-481's existing SQLite store, then Main's
existing saved tick. `DurablePublicationCoordinator` remains the publication
owner. No terminal, broker API, application or schedule is started or changed.

Every new reference records its source, source hash, observation time, known-at
time, age at comparison and age at image capture. A bar also retains its exact
row hash and start/end. The mutable database is opened read-only and closed after
each bounded read. Its raw broker prices remain in runtime image metadata; the
source-readback artifact here omits the price value and all account fields.

The export reader accepts an explicitly timed `last_price` or an exact-instrument
`quote`/`last_quote`. A plan level, entry, export generation time or check time
cannot stand in for a quote's observation time. The current export has none of
these price fields. The bar reader uses native M1 rows, excluding a forming bar,
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

Integration and observed-day evidence are recorded below after installation.
