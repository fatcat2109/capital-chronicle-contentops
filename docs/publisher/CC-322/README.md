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

Integrated implementation: `9940fec91be67705ca9602bda8cf2a887e2ca610` in the
Publisher operating root. Both remote tags are pushed:
`contentops-live-20261109-cc322` and `contentops-rollback-20261109-cc322` (the latter
at `52adbf3442645a1ffc2fd098eaf85b942baaa6cc`). The installed route sent both held
scored results at about 23:17 GMT+7 on 9 November. All six copies are now
DISPATCH_CONFIRMED and both result rows are PUBLISHED. Gold's initial Threads
UNKNOWN_WRITE is retained in `installed-publication-run.json`; its existing
dispatch is now reconciled to the confirmed object, not a replacement post.

| Result | Telegram | Discord | Threads |
|---|---|---|---|
| EUR/USD expired | [112](https://t.me/CapitalChronicle/112) | [message](https://discord.com/channels/1519310996030750782/1519311669216673802/1569385473137189106) | [post](https://www.threads.com/@official.capitalchronicle/post/DfhvefCo9WR) |
| Gold stopped | [113](https://t.me/CapitalChronicle/113) | [message](https://discord.com/channels/1519310996030750782/1519311669216673802/1569385514925301791) | [post](https://www.threads.com/@official.capitalchronicle/post/DfhvfreI9zt) |

`integration.json` records the existing coordinator's readbacks and a repeat
live-consumer dry run with zero rows to queue. Neo independently read both
Telegram posts on the public channel page and both exact Threads objects;
`browser-readbacks.json` retains the relevant text checks. No Gmail or signed-in
Telegram page was read.

The acceptance clause requiring the first plan ending **after** integration
remains pending: the two scored outcomes above ended earlier. The route is live
and consumes held data now; this observation does not gate publication. No
post-integration terminal Main outcome was present during this run. The existing
minute route will consume the next one; Publisher then reads back its three
copies. No new schedule, watcher or polling loop was added.


## Continuation readback, 10 November 2026

`readback-20261110.json` records one current read through Main's validated
export reader and a read-only query of the production coordinator store.
The fresh export contains 63 plans and four scored calls. New post-integration
stops exist for gold and EUR/USD; the previous statement that no new terminal
outcome exists describes the earlier run only.

Neither new stop satisfies this item's 9 November acceptance amendment:
decision 106 allows one loss post in seven days, and the confirmed gold loss
was queued on 9 November at 16:17 UTC. Its next loss slot is 16 November at
23:17 GMT+7. A new hit or explicit correction can qualify earlier. There is
no new hit or correction in this source snapshot. Each new stop is counted
with `LOSS_POST_LIMIT_DECISION_106` in the audit. This is the item's eligibility
assessment, not a claim that today's separate card consumer refused it.

CC-399 now owns the live queue via `plan_call_cards_v1.queue_posts`, effective
10 November at 09:11 GMT+7. Its newer backlog direction gives every announced
card an ending. The readback preserves this installed route: gold's new result
already has a READY_FOR_PUBLISHER card row, and EUR/USD's latest result has no
outbox row at this observation. Neither has a confirmed result dispatch.
No pending card was removed, rewritten or sent by this run. The minute route's
latest recorded run and its source clocks are retained in the audit.

The existing six confirmed historical result copies remain in the coordinator
store with readbacks. They do not satisfy the amended prospective acceptance.
CC-322 therefore remains `FIRST_ELIGIBLE_POST_INTEGRATION_RESULT_PENDING`;
Publisher's next action is one readback when the existing consumer processes
an eligible result, without a new watcher or schedule.

This continuation changes evidence only. No tests were rerun: source is
unchanged and Jim bars test starts until 22:30 GMT+7 on 10 November. The prior
33-test result remains historical evidence. Launch PID 15344 explicitly
configured gpt-6.1-sol/high, recorded as CONFIGURED_NOT_OBSERVED. No editorial
model was called, no public write was made, and no runtime state was changed.
