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
