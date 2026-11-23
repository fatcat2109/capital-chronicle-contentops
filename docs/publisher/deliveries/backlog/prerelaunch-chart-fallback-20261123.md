# Delivery: decision 82 chart fallback before the relaunch (Builder E)

- Branch: `backlog/prerelaunch-chart-fallback-20261123`
- Base: `b4508d05d948035b3d29d2f990353a1889a0d626` (live head when the work started, 23 Nov 2026). The live
  head was merged in twice as the other Builders' work went live: `965094c87d74d8440f2baa6cc0a5374b82478ae4`
  (Builder C's pages) and `6e52dca4708f84bffeb3a3f9ea8aac584403d2a4` (Builder D's checks and Builder B's plan
  posts). The branch head before this note is `e1ff1a6c0b33de1e7e106abe561ad2bd63cfb93e`.
- Code commits: `4acbd94b` (capture and write boundary), `1847a48e` (page fact card and tests), `3f6ace5b`
  (decision 82 check), `e1ff1a6c` (the CC-734 test expects the new check status). This note is the next commit.
- Builder: Claude Builder E for Ops Product (decision 64), 23 Nov 2026. No reviews (decision 161).
- Nothing was posted, published or sent. No browser was opened, no TradingView capture was made, and no task,
  runner or file under `A:\Capital Chronicle\Runtime` was touched. The production store was read only through a
  `mode=ro` connection, skipping chat, token, secret, webhook, phone, user and binding keys.

## Files

- `live_contentops/tradingview_snapshot_v1.py`: capture timing, per-attempt causes, interrupted attempts, and the
  worker's single deadline. It also gains `page_card_facts` and `page_fact_card`.
- `live_contentops/publication_image_contract_v1.py`: `_validate_page_card` at the write boundary.
- `live_contentops/plan_analysis_pages_v1.py` (Builder C's work was live before this edit): `render` falls back
  to the fact card, and `validate_plan` accepts the bound card.
- `live_contentops/public_decision_checks_v1.py` (Builder D's work was live before this edit): the new
  `FACT_CARD_FALLBACK` status.
- Tests:
  - new: `tests/test_prerelaunch_chart_fallback_20261123.py` (16 tests);
  - two expectations changed in `tests/test_plan_state_alerts_cc543.py`: the CC-734 first attempt is now 90 s,
    not 60 s, and the check reports that card post as `FACT_CARD_FALLBACK`.
- Not touched: `plan_call_cards_v1`, `plan_state_alerts_v1`, `plan_status_posts_v1`, `plan_reader_copy_v1`,
  `scenario_voice_v1`, `native_neo_executor_v1`, `neo_endpoint_executor_v1`.

## What the two BTC pieces actually carried (store, read-only)

- **23 Nov setup post** `plan-status-post-23c6a79a77a6a90ed1932e0ce0943196` (plan `plan_1d9bc560342b94e3d5a0cdb1`):
  - It carried CC-290's plan fact card, not a chart.
  - Telegram 231, Discord, Facebook and Threads sent `plan-fact-card-a43067804f6221acb5a9-16x9`; Instagram sent
    the `-4x5` card. Each destination row's `native_payload.media_asset_ids` names that card, and the dispatch is
    `DISPATCH_CONFIRMED`.
  - X and Substack Notes were `DEFINITE_NO_WRITE`.
  - Both capture states are `PLAN_CARD` with cause `TRADINGVIEW_SNAPSHOT_TIMEOUT`.
  - So decision 82 was met. The audit's FAIL was the check's own gap (fix C below).
- **22 Nov analysis page** `plan-analysis-plan_add6d62299828744939aafc1`:
  - It went out text-only: `run_context_v1.json` has `media.assets: []`.
  - Its capture state is `TEXT_ONLY`, attempts 1, cause `TRADINGVIEW_CAPTURE_WAIT_EXPIRED`.

## Why the BTC captures failed (read only: capture states, the outcome log, the minute job's run log)

**It is not specific to BTC.** BTC captures since 15 Nov take a median of 19 s, against 17-30 s for the other
markets. The same TIMEOUT also hit USDJPY on 20 Nov and XAUUSD on 21 Nov. Two days running on BTC is a
coincidence of which plans were posting during slow moments. The defects in our code:

1. **The page capture was cut by the minute job's five-minute limit, then never retried.** The limit is the one
   `scripts/manual_desk_tick.py` documents.
   - The 19:35Z tick reached the page phase at 19:39:02Z, and capture attempt 1 started.
   - The job stopped before the attempt saved a cause: the state has attempts 1 and no `first_cause`.
   - The orphaned worker still finished at 19:41:33Z, 148.4 s in. It left a valid `BTCUSD_2026-11-22_19-41-32.png`
     and its `.snapshot-n3pxytax/result.json` in `media_assets`.
   - At 19:47:46Z the next run found the five-minute window over, wrote `TEXT_ONLY` "WAIT_EXPIRED" without a
     second attempt, and the page went out text-only.
2. **The worker's waits added up to more than the parent's kill timeout.**
   - The waits were goto 1/2 of the budget, canvas 1/3, title 1/4, plus 2.5 s of paint and 20 s for the
     download: about 77 s against a 52 s budget. The parent killed the worker at 60 s.
   - So a slow page always ended as the bare `TRADINGVIEW_SNAPSHOT_TIMEOUT`, with no step named.
   - On 23 Nov 04:01Z the BTC portrait downloaded about 61 s into its 60 s first attempt (the PNG is in
     `media_assets/4x5/attempt-1`) and was killed while being resized to 4:5.
3. **The retry's own cause was lost.**
   - The final state keeps only the first cause.
   - The late-chart retry at 04:06Z failed as `TRADINGVIEW_SNAPSHOT_WORKER_FAILED:      - waiting 500ms`.
     That is the last line of Playwright's call log, not the error.
   - That retry runs the optional price-axis double-click (`reset_price_scale`). A click that could not land
     failed the whole attempt.
4. **Folder sharing.** 16:9 template captures (`_cc465`) wrote into `media_assets/4x5/attempt-N`, the same
   folders as the portrait attempts.

Not verified: why the host or TradingView was slow at 19:39Z on 22 Nov and 03:55-04:02Z on 23 Nov. The 148 s
worker run points to a loaded host, but there is no CPU record to show it.

## Fixes, each with its test (`tests/test_prerelaunch_chart_fallback_20261123.py` unless named)

| Fix | Test |
| --- | --- |
| A. A plan page whose capture ends `TEXT_ONLY` carries CC-290's fact card: zone, invalidation, status (in page wording) and ET time, built from Main's registration through the plan posts' own `plan_facts`. It never shows a target. The card sits in the page body after the introduction, bound as `plan_chart_fallback` {key, market, ratio, cause}. | `test_page_whose_capture_fails_carries_the_plan_fact_card_and_passes_the_write_boundary` (the plan carries a target of 1.15, which is never shown) |
| A. `validate_plan` accepts only the card built from the registration's own facts. `validate_write` binds it to the page's own exhausted capture state, its cause, path, hash and PNG. | `test_page_fact_card_is_refused_when_its_facts_or_binding_change` (three cases) |
| A. No card while the capture is still running; the status comes from the page's active or final status. | `test_page_fact_card_waits_for_the_bounded_capture_to_end` |
| B1. An attempt with no saved cause is named `TRADINGVIEW_CAPTURE_INTERRUPTED` and does not count. One extra bounded window (90 s + 30 s) allows the real attempts, once. | `test_an_interrupted_attempt_is_named_and_retried_once_after_the_window`, `test_a_second_interruption_gets_no_further_attempt` |
| B2. Plan charts (posts and pages) get 90 s on every attempt; generic article captures keep 60 s. | `test_plan_charts_get_ninety_seconds_on_every_attempt`; `test_plan_state_alerts_cc543.py::test_cc734_failed_chart_retries_then_delivers_card_to_every_route` |
| B2. The worker runs on one deadline. Each wait gets at most what is left; a spent budget or failed step names it (`TRADINGVIEW_WORKER_BUDGET_SPENT:<step>`, `TRADINGVIEW_WORKER_STEP_TIMEOUT:<step>`), and the worker reports it as JSON. | `test_worker_waits_share_one_deadline_and_name_the_step_that_ran_out` |
| B3. `attempt_causes` keeps every attempt's cause; the final `cause` is still the first one, which CC-734 binds. Worker failures name the exception line, not the call log. The price-scale reset is best-effort (`price_scale_reset_cause` in the result); the parent still checks the price scale of every download. | `test_each_attempt_keeps_its_own_cause_and_the_final_cause_stays_the_first`, `test_worker_failure_names_the_error_not_the_playwright_call_log` |
| B4. Only a portrait capture goes under `4x5`. | `test_a_wide_template_capture_no_longer_shares_the_portrait_attempt_folders` |
| C. In the decision 82 check, a copy whose only image is a recorded `plan_fact_card` fallback, with the image seen, gets the new status `FACT_CARD_FALLBACK` (`MARKET_TRADINGVIEW_FACT_CARD_FALLBACK`, with `chart_causes`). It is counted per decision as `fact_card_fallback`, not as failed. A text-only copy, or a card the public copy does not show, still fails. | `test_decision_82_check_counts_a_recorded_fact_card_fallback_with_its_cause` (three cases) |

Fact cards for different plans differ by 10-20 bits in the image register's perceptual hash, against a limit
of 6. A page card is therefore not refused as `IMAGE_REUSED` against other plans' cards (measured on four
rendered cards).

The worker's Playwright steps were not run against TradingView (no browser while posting is paused). Only their
deadline and cause logic is tested. The first real capture after the relaunch is the live check.

## Tests

- Branch: every test file that imports the three capture or page modules (55 files). Run on the branch before
  the second live-head merge: 1449 passed, 3 skipped, 10 failed.
  - The 2 CC-734 failures were this change's intended 60 s to 90 s difference; their expectation was updated and
    they pass.
  - The other 8 also fail on a detached worktree of live head `965094c8`, so they are older than this change:
    - `test_discord_queue_cc437.py::test_channel_route_refuses_a_substituted_thread_or_reply`
    - `test_discord_queue_cc437.py::test_frozen_copy_survives_a_formatter_change_but_changed_intents_and_private_copy_do_not`
    - `test_discord_queue_cc437.py::test_ended_unstarted_fill_update_retires_before_preparation_without_changing_bytes`
    - `test_image_templates_cc465.py::test_instagram_publishes_and_reads_back_the_native_chart_and_table`
    - `test_public_rules_cc583.py::test_f5_weekly_unscored_expiry_uses_the_same_rule`
    - `test_publication_coordinator_v1.py::test_complete_v1_transaction_attempts_all_eight_ready_derivatives_once`
    - `test_publication_coordinator_v1.py::test_one_derivative_failure_does_not_block_remaining_ready_derivatives`
    - `test_publication_coordinator_v1.py::test_case_g_expired_destination_isolated`
- After merging `6e52dca4`:
  - the decision-check, day-readback and golden-output tests (`test_prerelaunch_decision_checks_20261123`,
    `test_public_decision_checks_cc690`, `test_day_readback_cc639`, `test_public_output_golden_cc691`) and the new
    file: 140 passed;
  - the capture and page set: 299 passed, 2 failed. The 2 were the CC-734 test still expecting
    `MARKET_TRADINGVIEW_CHART_MISSING` for the card post, which fix C changes on purpose; its expectation was
    updated (`e1ff1a6c`) and it passes.

## Left with its owner

- **Generic articles (Ops Product and Codex Publisher).**
  - `prepare_contract_article` drops the route's own cards on a failed capture (`return article, []`), and its
    callers then go out text-only under `bounded_text_fallback`.
  - The outcome log has no text-only generic article to date: the only `TEXT_ONLY` rows are plan pages, plan
    posts and one trend board.
  - Carrying the route's card there needs three changes together:
    1. keep a `source_bound_data_card` as the lead with a `plan_chart_fallback`-style binding;
    2. `validate_write` accepts it; the generic bound-card acceptance can reuse `_validate_page_card`'s shape;
    3. `article_publication_quality_v1`'s `TRADINGVIEW_ATTRIBUTION_REQUIRED` and the newsroom compiler's
       "Chart: TradingView" credit must skip a card lead.
  - Making only the first change would turn text-only posts into refused posts, so it was not done here.
  - The market wrap and the event pack pass no card to `prepare_contract_article` (`[]` and `macro_chart_assets`),
    so they have no card to use. The event pack builds its own `data_card` and then replaces it.
- **Page capture budget (owner of `plan_reader_editorial_v1.run_due`).**
  - The page capture runs late in the minute job with no `snapshot_allowed`, so it can still be cut by the
    five-minute limit.
  - B1 now recovers from that, and the page carries the fact card if the retry also fails.
  - Passing a run-time budget into `run_due`, as plan posts do with `SNAPSHOT_RUN_BUDGET_SECONDS`, would avoid
    starting a capture that cannot finish.
- **The 22 Nov page.** It is already published text-only and is not changed. Adding the card to the live page
  would be a media edit through the existing reader-revision route, which is Ops Product's call.
