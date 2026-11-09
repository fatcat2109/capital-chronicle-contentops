# CC-322: public results for ended conditional plans

The existing `plan_status_posts.py --publish` consumer now reads CC-325's
explicit `plans[].outcome` and `scored_call_count`, through Main's own validated
CC-307 reader. It sends hit, stopped or expired results to Telegram, Discord and
Threads through the existing coordinator. No per-post model call is made.

Initial result identity is fixed per plan, independent of export refresh time,
outcome arrival time and later count changes. A Main correction with
`corrects_outcome_id` creates a new correction post. Existing calls and result
payloads are never edited. Main's score identity, result, plan and asset must
agree. Pending and unavailable outcomes never become inferred price results.
An explicit untriggered expiry replaces its ordinary expiry status post, stays
unscored and posts only for an announced plan. Historical scored outcomes remain
owed and retain their actual end time in ET; they do not become fresh calls.

Only fixed result wording, plan levels, the source count and times reach the
reader. Source commentary, score basis, execution details and performance claims
do not. Decision 40's notices and decision 83's no-link rule remain. Results use
CC-314's existing fact-card fallback: taking a new chart for a past outcome
would introduce later bars, contrary to decision 19b. The gold card was visually
inspected at its actual 1600 x 900 resolution. No snapshot service is replaced.

`current-source-consumer.json` records the current source hash and exact result
copy. The validated live export contains two scored calls: EUR/USD expired and
gold stopped. `live-dry-run.json` proves both enter the existing live consumer
without modifying its store. Preview PNGs remain binary local artifacts.

The branch continues `52fc1aaaf004afc6a96277a67b9c6ff15c0f5634`, merging the current
Publisher operating base `52adbf3442645a1ffc2fd098eaf85b942baaa6cc`. The remote
default predates these operating consumers. Unrelated telemetry and duplicate
ledger edits remain outside this item.

The unchanged minute task loads `scripts/plan_status_posts.py` from
`A:\Capital Chronicle\ContentOps` on each invocation. Integration requires no
restart or schedule change. No chat message or desktop automation is used.

Launch PID 6792 configured `--model gpt-6.1-sol` and
`model_reasoning_effort="high"`: CONFIGURED_NOT_OBSERVED. No supported runtime
model/effort telemetry was available. Editorial model roles are unused for this
deterministic result route.

Final focused verification: 33 tests passed in 161.78 seconds, serially, covering
the new result route and existing recovery (`pytest.xml`). The earlier composer
and publication selection passed 44 tests with one fixture-title mismatch;
that fixture was corrected and passes in the final run. The integration test
sends an old explicit outcome through the real coordinator with fixture
transports, confirms all three destinations once, then proves a repeat writes
nothing. It also refuses a chart capture containing later observations.
