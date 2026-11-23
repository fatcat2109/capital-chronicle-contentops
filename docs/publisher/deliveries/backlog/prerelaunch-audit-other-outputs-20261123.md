# Delivery: pre-relaunch audit of the public outputs other than plan posts

- Branch: `backlog/prerelaunch-audit-other-outputs-20261123`
- Base: `b4508d05d948035b3d29d2f990353a1889a0d626` (live head on 23 Nov 2026)
- Code commit: `082394d09e0f6d4c42e921ae5b1b54ecbaebd9e6` (this note is the next commit on the branch)
- Builder: Claude Builder for Ops Product (decision 64), 23 Nov 2026. No reviews (decision 161); this note is the
  self-check.
- Nothing was posted, published or sent. The production store was opened read-only only to copy it (sqlite backup
  from a `mode=ro` connection) to `C:\CapitalChronicleScratch\builder-c-audit-data\store_copy.sqlite3`. Nothing under
  `A:\Capital Chronicle\Runtime` was written; Main's run folders were only read.

## Files changed

Code (all in this Builder's file list):
`live_contentops/plan_analysis_pages_v1.py`, `plan_reader_editorial_v1.py`, `market_wrap_editorial_v1.py`,
`market_wrap_sources_v1.py`, `daily_trend_board_v1.py`, `substack_daily_note_v1.py`, `manual_desk_v1.py`,
`x_reply_fact_sources_v1.py`, `x_reply_pack_v1.py`, `correction_reply_v1.py`, `pinned_result_scorecard_v1.py`.

Tests: new `tests/test_prerelaunch_audit_other_outputs_20261123.py` (26 tests); updated expectations in
`tests/test_public_market_quote_cc509.py` (no "Main quote", five places for EUR/USD) and
`tests/test_x_reply_fact_cc495.py` (fixture fact "7000.0 USD" now prints "7000.00 USD").

Not touched: plan_call_cards_v1, plan_state_alerts_v1, plan_status_posts_v1, plan_reader_copy_v1, scenario_voice_v1,
neo_destination_handoff_v1, native_neo_executor_v1, publication_coordinator_v1, public_decision_checks_v1,
day_readback_v1, publication_image_contract_v1. No task, runner or live root was touched; no tag; no merge.

## Stored copy keeps its bytes

Every copy change is gated so a stored item re-validates to its exact bytes:

| Output | Gate |
| --- | --- |
| Substack plan pages | manuscript `reader_revision` 8 (`PAGE_COPY_REVISION` 7 -> 8); stored revision-6/7 pages re-assemble identically (checked on all five pages of 19-23 Nov: `stored re-assembles identical: True`) |
| Old-format page target line | freeze at or after 22 Nov 21:09:03Z (decision 157) |
| Weekend/daily wrap | only new staging (`article_for`); stored wraps are hash-checked files; `derivative_payload` unchanged |
| Trend board | boards captured from 24 Nov ET carry `public_voice`; earlier projections unchanged (as ROUNDED_FROM_ET) |
| X reply facts | `display: MARKET_PLACES_V1` marker in the new source's artifact binding; held sources resolve to their old excerpt and id |
| X reply relative day | drafts checked from 24 Nov 00:00Z |
| Substack daily Note | Notes for 24 Nov ET on (`STRICT_FROM_DAY`) |
| Correction reply | checks run only when a new correction is registered |
| Desk packs | composed fresh each tick; the stored platform copy is not rewritten |

## Defects found and what was done

Evidence: store copy and renders in `C:\CapitalChronicleScratch\builder-c-audit-data\` (`public\*.txt` = public text
of every stored payload of 19-23 Nov; `render_pages_base.txt` / `render_pages_new.txt` = the five stored plan pages
re-rendered by the base code and by this branch; `render_wrap_new.txt`; `desk_render.txt` / `desk_render_new.txt`).

Substack plan pages (decision 113 full analysis):
1. Internal ids and desk wording in public text: "(cc415 ...)", "KB:markets/btcusd.md@...", "CC-460", "priced_in is
   MISSING", "cot_crowding", "STARTER sell stop rather than an OPEN", "The book already holds the same direction in
   the MID lane", "frozen files", "frozen geometry", "this WATCH registers", "row not read in this pass", "broker
   stop", "Sized STARTER" (21-23 Nov pages). FIXED: `plan_analysis_pages_v1.public_span_problem`, used by
   `plan_reader_editorial_v1._plan_page_sources` (revision 8). Test: `test_an_analyst_sentence_that_cannot_stand_alone...`.
2. Fragments printed as analysis: "Capitulation.", "Before entry.", "Stop tightening fact.", "Trend and flow.",
   "Claim 4 and its evidence." FIXED (same function; case support lines via `_public_cases`). Tests:
   `test_revision_8_cases_drop_fragment_drivers_and_group_numbers`.
3. Numbers not grouped and mixed with grouped ones ("60977.64", "3584.47", "68450.00" beside "61,940.88").
   FIXED: `group_thousands` (years 1900-2100, dates, clocks and names untouched); held page choices still match
   (`repair_cached_page_quotes`). Test: `test_group_thousands_...`.
4. Sentences cut after "8:30 a.m." into "... a.m." / "ET and the jobs report ..." paragraphs (22 Nov BTC page).
   FIXED: `join_abbreviation_spans` and option merge in `_plan_page_sources`. Test: `test_a_sentence_cut_after...`.
5. The same scenario line printed twice (case driver plus the raw excerpt, once with "shorts" reworded).
   FIXED: `_drop_case_repeats`. Test: `test_revision_8_prints_a_case_line_once...`.
6. UTC clocks ("2026-12-09T18:00Z", "17:00Z") in the 21 Nov pages: already converted by the live head's
   revision 6/7; revision 8 also refuses any left. Relative "today/tomorrow" spans refused too.
7. Old-format pages (no reader contract) print "Capital Chronicle model objective: <target>". No such page is unsent;
   FIXED for any page frozen after decision 157 (`_public_geometry`). Test: `test_an_old_format_page_frozen_after...`.
   Re-rendered result: `render_pages_new.txt` (all five pages render, numbers bound, no internal wording left).

Weekend wrap (22 Nov, published):
8. "Main's market review", "Main's plan", "Main's export", "Main recorded ..." in public text (decision 109).
   FIXED: `market_wrap_editorial_v1.article_for`, `market_wrap_sources_v1.prior_stops`. Test: `test_wrap_stops_line_never_names_main`.
9. "keep the incremental USDJPY view flat and do not add to the existing short" (the desk's own position, decision 40).
   FIXED: `public_line` drops lines about the desk's book or with internal wording.
10. "M15", "H1" timeframes and "58630.87". FIXED: timeframes in words, grouped numbers (`public_line`, `_case_line`).
11. "Capital Chronicle model estimate(s)" and legacy "Main (54%)/Alternative" labels. FIXED: "Capital Chronicle
    estimate(s)", "Base case"/"Alternative case" (new packs already use CC-755 cases).
12. Notice printed twice (weekly call record carries its own). FIXED: the record's notice is dropped inside the wrap.
    Test: `test_wrap_lines_use_timeframe_words...`.

Daily trend board:
13. "158.60999999999999" on 20 Nov: already fixed on the live head for boards from 23 Nov; the stored 20 Nov board
    cannot post (BOARD_PUBLIC_DAY_EXPIRED).
14. Ten "long/short" words per board ("Short with trend ... (short)") against decision 158, and "Historical model
    estimates". FIXED for boards from 24 Nov ET: "Follow a downtrend, 20 sessions (bearish)", "Historical estimates".
    Test: `test_board_from_24_nov_names_rules_in_scenario_words...`.

X reply drafts:
15. Prices printed as raw floats: "82.86000061035156 USD", "82.19999694824219 USD", "103.73400115966797 points"
    (20 Nov packs). FIXED: `x_reply_fact_sources_v1.display_value` (market precision), for held bars, native bars,
    saved Main quotes and on-demand quotes. Test: `test_reply_fact_prints_its_market_precision...`.
16. Attribution "Capital Chronicle Main" / "EURUSD Main quote". FIXED: "Capital Chronicle", "EUR/USD price".
17. "If Bitcoin closes down today" (20 Nov draft). FIXED: writer told to name the day; drafts checked from 24 Nov
    refuse a relative day (`x_reply_pack_v1._check_dated`). Test: `test_reply_drafts_from_the_relaunch_week...`.

Posting-desk packs:
18. "Macro: The US front end through today's retail sales" re-used in the 22 Nov USD/JPY result pack (its "today"
    was 17 Nov). FIXED: a relative-day analysis line is left out of a fresh pack; the call line is kept
    (`manual_desk_v1._split_lines(dated=True)`). Not re-dated, because result posts re-quote setup text.
    Test: `test_desk_leaves_out_a_relative_day_line_and_keeps_the_call`. Render: 10 packs, 0 withheld.

Corrections:
19. A correction body was sent verbatim with no public-copy check. FIXED: `correction_reply_v1.check_body` (no
    target, account, AI label, relative day; ET time; notice check) at registration. The prepared 23 Nov USD/JPY
    correction passes it. Test: `test_a_new_correction_body_passes...`.

Substack daily Note (none stored 19-23 Nov; last state NOTE_WAITING_SOURCE on 17 Nov):
20. No target or relative-day check. FIXED from 24 Nov ET (`validate_copy(strict=...)`). Test: `test_a_note_from_24_nov...`.

Scorecard:
21. Empty scorecard text named "Main". FIXED. Checked: no "model calls"; levels on the plan tick; plans that end
    during the pause appear newest first (test `test_plans_that_ended_while_posting_was_paused...`).

Measured-odds piece (21 Nov): no target, model name or relative day; ET dates. Its "Table fingerprint" hash is
required by `validate_piece` as the public proof of the table, so it was kept (a commitment, not a private id).

## Found, not fixed here (outside these files or needs another owner)

- A. `plan_reader_copy_v1` (plan-post Builder's file) rewrites "shorts" as "traders positioned for losses" and "net
  long positions" as "net positions set for gains", which inverts the meaning on the pages ("The desk's own recent
  traders positioned for losses ... have paid"). Revision 8 drops the duplicated cases, but the scenario driver from
  `scenario_case_copy` keeps the wording. Fix belongs in `plan_reader_copy_v1` ("short sellers", "buyers").
- B. `scenario_case_copy` takes only the first sentence of a driver, so a case can read "BTC carries that through a
  1.31 beta" (dangling "that") or a one-word driver (dropped here). Same owner.
- C. The plan-post social variants (`plan_reader_editorial_v1.prepare_variants` prompt, validated by
  `plan_reader_copy_v1.validate_fields`) still require "Main (odds%):" and "Alternative (odds%):" lines. Changing
  the prompt alone would fail the validator in the other Builder's file; both must change together (plan posts).
- D. Decision 82: the 22 Nov BTC page (`plan_add6d622...`) published with no image: the TradingView capture timed
  out and `publication_image_contract_v1.bounded_text_fallback` allows a text-only page; decision 82 asks for the
  CC-290 fact card then. Needs the image-contract owner (fact cards are delivery-only today).
- E. The prepared correction `correction-reply-usdjpy-230-20261123` says the 20 Nov USD/JPY result "will follow in
  its own post"; that plan's exit (23 Nov 06:00Z) falls inside the pause, so under eb5d506e it is shown only in the
  scorecard. Ops Product should edit or drop that correction before the relaunch.
- F. The scorecard shows plan `plan_caf370e4...` as "EXPIRED (untriggered)" while its page says "cancelled": Main's
  export result, not ContentOps copy.
- G. Pages still name weekdays ("Friday's low", "early Monday") without a date; the page states its fixed date, so
  these were left.

## Tests (one pytest process at a time)

Command: `python -B -m pytest -q -p no:cacheprovider --basetemp=C:\CapitalChronicleScratch\builder-c-tmp <files>`

Files: test_call_followups_cc603, test_correction_reply_v1, test_daily_trend_board_cc537,
test_jim_pause_results_20261123, test_manual_desk_cc748, test_manual_desk_tick_cc748, test_market_wrap_cc689,
test_measured_odds_series_cc536, test_pinned_result_scorecard_cc394, test_plan_analysis_copy_cc688,
test_plan_analysis_discord_cc432, test_plan_analysis_distribution_cc435, test_plan_analysis_layers_cc730,
test_plan_analysis_link_copy_cc432, test_plan_analysis_pages_cc432, test_plan_copy_cc682,
test_plan_link_recovery_cc584, test_plan_page_current_cc584, test_plan_reader_editorial_cc466,
test_public_output_golden_cc691, test_public_rules_cc583, test_substack_daily_note_cc468,
test_substack_growth_review_cc468, test_weekly_scored_calls_cc379, test_x_mention_responder_cc456,
test_x_reply_base_rates_cc510, test_x_reply_bot_cc464, test_x_reply_bot_entry_cc464, test_x_reply_fact_cc495,
test_x_reply_funnel_cc511, test_x_reply_pack_cc455, test_x_reply_tabs_cc458, test_x_reply_topics_cc511,
test_public_market_quote_cc509, test_heavy_news_quotes_cc467, plus the new test file.

| Run | Result |
| --- | --- |
| Live head b4508d05, before any edit (33 files) | 746 passed, 1 failed: `test_public_rules_cc583.py::test_f5_weekly_unscored_expiry_uses_the_same_rule` |
| This branch, 36 files | 798 passed, 7 failed: the same `test_f5` id, plus 6 in `test_x_reply_fact_cc495.py` whose fixture quoted "7000.0 USD" |
| After updating that fixture: `test_x_reply_fact_cc495.py` + new file | 56 passed |
| Final desk/correction/Note code: `test_manual_desk_cc748`, `test_manual_desk_tick_cc748`, `test_correction_reply_v1`, `test_substack_daily_note_cc468` | 46 passed |

Failing id on this branch equal to the live head's: `tests/test_public_rules_cc583.py::test_f5_weekly_unscored_expiry_uses_the_same_rule`
(listed as a known live-head failure). Logs: `builder-c-audit-data\baseline_tests.txt`, `run1_tests.txt`.

## Live step

Merge `backlog/prerelaunch-audit-other-outputs-20261123` onto the live head (only this Builder's files; the two
existing tests changed are this lane's). Unsent pages of revision 6 (USD/JPY 4bcfb118, gold 7c24bb53, BTC 1d9bc560)
are re-composed at revision 8 by `refresh_page_reader_terms` before any send; their plans ended in the pause, so
eb5d506e keeps them to the scorecard.

## Left undone

Items A-G above. No full suite was run (by the brief).
