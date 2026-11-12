CC-509 adds a shared on-demand public quote to the existing private reply bot
and TradingView price check. Main's timed minute export is read first, then an
exact native M1 row, then a usable held same-session fact, then HTTPS. Source
failures leave other facts available. The seven CC-495 rules, ranking floor,
15-minute send limit, private destination binding and Jim's own X send remain.

The Yahoo endpoint and six-market FX/futures symbols follow Data's installed
`tools/data_foundation/market_history_intake_v1.py` and its `TICKERS` map in
`Runtime/OfficialRates/cc-481-20261112/code`. Publisher uses a bounded individual
quote read, rather than calling Data's bulk history importer, which writes its
own archives and database. S&P 500 uses the cash index matching the chart; NDX
and Brent extend that source map. CNBC's public quick-quote endpoint supplies
spot gold, the dollar index, and US 2-year and 10-year Treasury yields with
complete observation timestamps. Measured Yahoo gold and dollar-index quotes
were ten minutes delayed; CNBC's spot quotes were current enough for the chart
check's unchanged two-minute window. A closed cash index or failed direct
source can use a live yield driver; rule 5 still requires its link in the reply.
Yahoo's checked 2-year yield future was stale and is not a Treasury spot yield.

Each actual quote retains source, URL, source symbol, instrument name/type,
observation and receipt clocks, units, prior close, day's change and fetch
seconds. Yields retain percent and percentage-point changes. Futures keep their
own names; there is no future-to-CFD level conversion. The cache is under
`Runtime/ContentOps/references/public-quotes-v1`, shared by both consumers.
Immutable observation bytes and hashes bind each issued fact; a new latest
quote cannot rewrite an issued draft. A nonblocking OS lock and a saved fetch
claim limit successes, failures and interrupted fetches to one per symbol per
60 seconds across processes. Each HTTPS read has a five-second timeout and
512 KiB limit. No terminal, broker API, application or schedule is used.

The chart capture acquires before taking its image. The price check only reads
the saved observation at capture; it cannot certify an old chart with a later
fetch. Its existing 120-second comparison window, last-close behavior and
0.15%/0.40% mismatch limits remain. A measured mismatch still refuses the image.
A genuinely unavailable quote retains its exact source attempts and the chart's
existing `NOT_COMPARED` behavior. No later source erases a measured mismatch.

Only one attributed fact may enter a reply (host rule 7). Raw source series
stay in Runtime; test fixtures use isolated stores and controlled responses.
The phone message shows the fact's ET observation clock and its elapsed age.
The existing minute result records source attempts and fetch seconds per symbol.

Build checks: `quote-tests.xml` and `consumer-regressions.xml`. The latter covers
the existing CC-495 fact policy, CC-464 private bot and CC-489 chart reader.
Launch readback found `gpt-6.1-sol` with effort `max`, labelled
`CONFIGURED_NOT_OBSERVED`; this describes the configured launch, not runtime
model telemetry. Integration and live observations are recorded below when
performed. Tests alone do not claim a phone delivery or a live compared chart.

The code was fast-forwarded into `A:/Capital Chronicle/ContentOps` at
18:33 GMT+7 on 12 November, followed by the fact-clock correction at
18:39 GMT+7 and the source-order change at 18:48 GMT+7. The live and rollback tags, exact commits and preserved-file
checks are in [integration.json](integration.json). No schedule or application
was changed. The minute consumer ran the installed code; its readback is
[installed-consumer-readback.json](installed-consumer-readback.json).

The real [Brent replay](brent-live-fetch-replay.json) retained the original
09:41:49Z post clock and exact target text. A live quote supplied a same-session
fact to the actual Antigravity ranking call. It returned in 79.35 seconds with
`NO_ADDED_FACT_ABOVE_QUALITY_FLOOR`. No draft or message was sent. This proves
the acquisition-to-ranking path; it does not turn an expired post into a fresh
phone opportunity. The call's configured model/effort and unavailable runtime
telemetry are retained in that evidence and the existing Runtime role artifact.

The installed [EUR/USD chart capture](installed-chart-capture.json) used the
actual TradingView download and the shared Yahoo observation captured before
the image. It was bound `AT_CAPTURE`, with a 70.50-second quote age and
0.02254% difference against the unchanged 0.15% limit. The binary image and
complete snapshot metadata stay at the recorded Runtime paths. This was a
separate capture proof, not a dispatched public plan card. The
[spot-source readback](spot-source-readback.json) also observed current CNBC
gold and dollar-index quotes inside the chart's two-minute window.

The implementation is live. Completion still requires the next natural
on-topic target's private delivery within 15 minutes, and the next naturally
dispatched plan chart's compared binding. The early minute runs had no
eligible target with an identified market. Two fresh Oman tanker headlines
were refused as `FACT_MARKET_UNIDENTIFIED` under the unchanged CC-495 rule;
their exact causes remain in the installed result. The existing consumer
continues; no target clock,
ranking score, expired plan, public object or issued request was changed to
manufacture either proof. Those pending live observations keep CC-509 open
as a named blocked result, with no person action or Ops review step.

Installed checks passed 100 regressions after the fact-clock correction.
The final source-order change then passed 72 installed checks, covering the
public quote, actual capture, private delivery and chart reader paths. See
[installed-tests.xml](installed-tests.xml) and
[installed-final-source-order-tests.xml](installed-final-source-order-tests.xml).
The remaining source limitation is explicit: the free WTI futures quote was
about ten minutes delayed. It can support the reply rule when current enough,
but fails the chart's two-minute comparison unless Main or native M1 supplies
the fresher reference. Its exact source clock stays recorded; the limit was
not widened. Closed cash indices can use a fresh yield driver in replies.

The 18:56 GMT+7 natural minute run then acquired fresh Bitcoin and spot gold
quotes in 0.212 and 0.408 seconds respectively. Those facts reached the actual
ranker for three current targets. It returned in 32.04 seconds with scores
46, 42 and 34, below the unchanged 80 floor, so no writer or send ran.
[natural-consumer-readback.json](natural-consumer-readback.json) records the
exact targets, source clocks, source attempts, elapsed seconds and outcomes.
An earlier natural call returned `AGY_RANK_TIMEOUT_90S`, already addressed by
the separately assigned CC-512; it is retained as a failure. CC-509's quote
acquisition itself is operating. The remaining first cause for the phone
proof is `NO_ADDED_FACT_ABOVE_QUALITY_FLOOR`, followed by the next dispatched
plan-chart observation; no person action is pending.
