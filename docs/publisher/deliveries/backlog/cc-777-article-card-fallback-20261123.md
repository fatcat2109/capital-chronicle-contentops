# Delivery: CC-777, an article whose TradingView capture fails carries its own data card (Builder H)

- Branch: `backlog/cc-777-article-card-fallback-20261123`
- Base: `e542abc7` (live head when the work started, 23 Nov 2026). The live head was merged in twice:
  `67ceb43e` (Builder F, desk and labels, before piece 2) and `77e60f92` (Builder G, test debt, before this note).
- Code commits: `b5a56804` (piece 1), `cb23bd69` (piece 2), `075fe3e1` (the CC-459 test expects piece 2). Merges:
  `d68ab274`, `aa25a584`. This note is the next commit.
- Builder: Claude Builder H for Ops Product (decision 64), 23 Nov 2026. No reviews (decision 161).
- Nothing was posted, published or sent. No browser was opened and no TradingView capture was made. No task, runner or
  file under `A:\Capital Chronicle\Runtime` was touched, and the store was not read.

## Files

- `live_contentops/tradingview_snapshot_v1.py`: `article_card_refusal` and `article_card_fallback`. Piece 1 calls the
  fallback from `prepare_contract_article`'s failed-capture branch. Piece 2 changes `plan_snapshot`: a deferral no
  longer starts the capture window.
- `live_contentops/publication_image_contract_v1.py`:
  - `exhausted_capture_state`, split out of `bounded_text_fallback`, which behaves as before;
  - `_validate_article_card`;
  - `validate_write` accepts a lead card only when its binding checks out;
  - a new image type, `ARTICLE_FACT_CARD_FALLBACK`.
- `live_contentops/article_publication_quality_v1.py`: `_bound_card_lead`. A card lead with no TradingView image owes
  no "Chart: TradingView" credit.
- `live_contentops/market_wrap_job_v1.py`: when a wrap's capture fails, `prepare_media` leads with the wrap's own
  market-moves card.
- `live_contentops/public_decision_checks_v1.py`: the decision 82 check reads the article's bound card, including from
  the run's own `run_context_v1.json`.
- `scripts/audit_publication_images_cc463.py`: the daily image audit allows a card post, like a text fallback, and
  never counts it as a chart.
- Tests: the new file `tests/test_cc777_article_card_fallback_20261123.py` (16 tests), and one expectation changed in
  `tests/test_tradingview_plan_charts_cc459.py` (piece 2).
- Not touched: `publication_coordinator_v1`, `native_neo_executor_v1`, `neo_endpoint_executor_v1`.

## Piece 1: decision 82 on ordinary articles

How it works:
- **Fallback.** When an article's own bounded capture ends `TEXT_ONLY`, `prepare_contract_article` no longer drops
  the article's cards. It keeps the article's own fact card (`source_bound_data_card`) as the lead.
- **Which card.** The card must carry facts. A title-only card does not count, nor a template, a headline card
  (`post_card_binding`) or a derivative. Second choice is an owned data chart (`source_backed_chart`). For the wrap,
  it is the wrap's market-moves card.
- **Binding.** The card is bound as `article_chart_fallback` {key, market, ratio, cause} to that capture state.
- **Instagram.** Every destination, Instagram included (the cards are 1080x1350), gets the card.
- **Records.** The article records `tradingview_card_fallback` {asset_id, cause, key, market}. The outcome log gets an
  `ARTICLE_FACT_CARD` row.
- **No card.** If the article has no usable card, it stays text only as before. It records why in
  `tradingview_card_fallback_refused` (`..._NO_CARD`, `..._TITLE_ONLY` or `..._TARGET_REFUSED`).
- **Never a target.** A card whose title, caption or facts mention a target or take-profit is refused (decisions 40
  and 157). "Inflation target" is allowed.

Each fix and its test (all in `tests/test_cc777_article_card_fallback_20261123.py`):

| Fix | Test |
| --- | --- |
| Failed capture: the real cc333 article run leads with its own card, bound to the capture cause. `validate_write` accepts it and reports the cause. Substack and Telegram pass `before_article_write` without a TradingView credit. The register records `ARTICLE_FACT_CARD_FALLBACK`. | `test_article_whose_capture_fails_leads_with_its_own_card_and_passes_the_write_checks` |
| A TradingView chart lead still owes its credit. | `test_a_tradingview_lead_still_owes_its_chart_credit` |
| The write boundary refuses a changed cause, a changed record, a capture window not yet spent, or changed bytes. | `test_the_card_is_refused_when_its_binding_or_bytes_change` (4 cases) |
| No card, a title-only card, or a card with a target: still text only, with the reason recorded. | `test_without_an_own_fact_card_the_article_stays_text_only_and_records_why` (3 cases) |
| A stored text-only article keeps its bytes, its capture state and its bounded text fallback. | `test_a_stored_text_only_article_keeps_its_bytes_and_its_text_fallback` |
| The wrap leads with its own market-moves card when its capture fails. | `test_the_wrap_leads_with_its_own_market_moves_card_when_its_capture_fails` |
| Decision 82 check: an article led by its bound card is `FACT_CARD_FALLBACK` with `chart_causes`. Text only still fails (`MARKET_TRADINGVIEW_CHART_MISSING`). | `test_decision_82_check_counts_an_article_card_with_its_cause_and_still_fails_text_only` (2 cases) |
| The daily image audit: a card post is no violation and never counts as a chart. | `test_the_daily_image_audit_allows_a_card_post_but_never_counts_it_as_a_chart` |

## Piece 2: a deferred page capture no longer uses up the capture window

- **The defect.** `plan_snapshot` saved `started_at_utc` when Builder F's run-time deferral fired. Several short runs in
  a row could then spend the five-minute window with no capture tried.
- **The fix.** A state still at zero attempts after a deferral restamps `started_at_utc` at its first real attempt. It
  keeps the original time as `first_deferred_at_utc`. A capture that already made an attempt keeps its clock.
- **Tests:**
  - `test_a_deferred_page_capture_starts_no_clock_and_its_window_counts_from_the_first_attempt`: two deferrals ten
    minutes apart, then both real attempts still run.
  - `test_a_capture_that_already_attempted_keeps_its_clock`.
  - `test_tradingview_plan_charts_cc459.py::test_budget_deferral_resumes_same_request_without_drawing_or_losing_attempts`:
    this test asserted the old clock. It now asserts `first_deferred_at_utc` and a start at the first attempt; the
    attempts are still kept.

## Tests

- **Branch at `075fe3e1`** (after merging `67ceb43e`): every test file that imports a changed module, the audit script
  or the decision-check helpers, 52 files.
  - Result: 1450 passed, 3 skipped, 6 failed.
  - One failure was the CC-459 expectation above. It was updated and its file passes (8 passed).
  - The other 5 also fail on a detached worktree of live head `67ceb43e`, so they are older than this work:
    - `test_image_templates_cc465.py::test_instagram_publishes_and_reads_back_the_native_chart_and_table`
    - `test_public_rules_cc583.py::test_f5_weekly_unscored_expiry_uses_the_same_rule`
    - `test_publication_coordinator_v1.py::test_complete_v1_transaction_attempts_all_eight_ready_derivatives_once`
    - `test_publication_coordinator_v1.py::test_one_derivative_failure_does_not_block_remaining_ready_derivatives`
    - `test_publication_coordinator_v1.py::test_case_g_expired_destination_isolated`
- **After merging Builder G (`77e60f92`):** the files G changed in that set (cc465, cc583, publication_coordinator_v1),
  plus the new file, cc459, cc463 and cc333: 380 passed, 0 failed. G's changes cleared the 5 older failures.

## What is left

- **Macro and event-pack articles.**
  - The fallback covers market articles only, the scope of decision 82.
  - A macro article whose capture fails stays text only, as before.
  - The event pack still passes no card to `prepare_contract_article` (`macro_chart_assets`), so it has none to use.
- **Article runs in flight.** Runs prepared before this goes live keep their frozen text-only package.
- **Live check.** The first real failed capture after the relaunch is the live check. No capture was run here.
