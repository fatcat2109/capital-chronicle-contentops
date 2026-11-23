# Delivery: TradingView idea pack, scenario labels, "expired, no entry" pages, page capture budget

- Branch: `backlog/prerelaunch-desk-and-labels-20261123`
- Base: `965094c8` (live head when started, 23 Nov 2026 11:13Z); live head `6e52dca4` (Builder B's plan posts and
  the decision checks) merged in at `23b033fb` before pieces 2 and 3 were committed.
- Code commits: `7c0b818e` (CC-469 idea pack), `19969af6` (expired, no entry), `dee92423` (variant labels),
  `36365a32` (page capture budget; variant fix). This note is the next commit.
- Builder F for Ops Product (decision 64), no reviews (decision 161). Nothing was posted, published or sent; no
  browser; no task, runner or file under `A:\Capital Chronicle\Runtime` touched. The store was read only through
  Builder C's payload dumps in `C:\CapitalChronicleScratch\builder-c-audit-data`; Main's export was only read.

## Files

Code: `live_contentops/tradingview_idea_v1.py` (new), `manual_desk_v1.py`, `plan_reader_editorial_v1.py`,
`plan_analysis_pages_v1.py` (functions `ended_plan_status`, new `_ended_without_entry`, `_assemble`, `_card`, new
`PAGE_CAPTURE_ALLOWED`), `scripts/plan_status_posts.py` (passes its start time to the page slice, 2 lines).

Tests (new): `tests/test_tradingview_idea_cc469.py` (25), `tests/test_plan_page_expired_no_entry_20261123.py` (9),
`tests/test_variant_scenario_labels_20261123.py` (5), `tests/test_page_capture_budget_20261123.py` (5); fixture
`tests/fixtures/tradingview_idea_cc469_plans.json` (two stored plan posts: 20 Nov USD/JPY setup, 22 Nov Bitcoin
update, only the fields the pack reads).

Not touched: Builder A's and Builder E's files, plan_call_cards_v1, plan_state_alerts_v1, plan_reader_copy_v1,
public_decision_checks_v1, day_readback_v1. Builder E's branch `backlog/prerelaunch-chart-fallback-20261123`
(51fda991) merges with this branch without a conflict (checked with `git merge-tree`).

## 1. CC-469: TradingView idea pack on the posting desk

- `tradingview_idea_v1.build_idea` makes one pack per new plan (a `setup`, or the `update` that replaced an unsent
  setup) in the six markets, from the stored plan post's own fields: a normal-case title ("USD/JPY: bearish at
  158.8–158.88, wrong above 159.6 (20 Nov 2026)"); a description with the Base case (side and odds), the Bull or Bear
  case (odds), each with its cause, what is priced in, positioning, what confirms the base case, the entry zone, the
  invalidation, and the plan's ET dates and horizon (decision 90); chart instructions (the snapshot code's reviewed
  symbol, e.g. `FX_IDC:USDJPY`, a timeframe from the horizon via `interval_for`, the zone and the invalidation line,
  nothing else); a one-line how-to for Jim. Plan text with desk codes (snake_case fields, hashes, `cc4xx` blocks,
  "broker", "MISSING", ...) or a relative day is left out clause by clause, never rewritten; long numbers are grouped
  and rounded.
- `check_idea` refuses a URL, a domain, an email or @handle, a contact or social reference, "Capital Chronicle",
  a target or take-profit (an "inflation target" is allowed), an AI word or model name, a relative day, non-English
  text, a title in capitals, a missing Base or Bull/Bear case, and runs the existing `public_filter`.
- Desk: the pack is in `packs.json`, on the page (copy buttons for title and description) and in the pack's first
  phone send only (how-to, title, description). It has no Posted mark, so pack states are unchanged; a reply to an
  idea message is not a Posted mark.
- Evidence: all 18 stored setups and updates of 19-23 Nov in the six markets build a pack that passes the check
  (scratch run over Builder C's payload dump).
- Tests: `test_stored_plans_of_20_to_22_nov_make_packs_that_pass_the_check`, the 14 refusal cases (link, brand,
  contact, target, AI, relative day, capitals, non-English, empty), the desk page and phone-send tests.

## 2. Scenario labels in the social-variant prompt (decision 158)

Done after Builder B was live (`29a9cd82`). `prepare_variants` asks for `Base case (odds%):` and, for the alternative,
the plan's own side from `scenario_voice_v1.case_records` (`Bull case` against a bearish base, `Bear case` against a
bullish one), each saying what drives it; the schema example follows. B's `validate_fields` accepts both label sets,
so stored Main/Alternative variants keep their bytes.
Test: `test_variant_prompt_asks_for_base_and_bull_cases_and_the_labelled_variant_validates` (a "Base case (55%)"
variant is PREPARED), plus the label cases.

## 3. "Cancelled" on the expired Bitcoin page

Finding (corrects the brief): the word came from Main's export at the time, not from ContentOps copy alone. The
stored result post of 21 Nov 00:01Z holds Main's record for `plan_caf370e4bd6053e0a4cdfef8`: status CANCELLED at
00:00:44Z, outcome NOT_SCORED_UNTRIGGERED, no cancel_kind, price 58,834 (far below its 61,940.88 cancel level). The
page (written 13:28Z, published 14:00Z) printed that status. Main now exports EXPIRED at 23 Nov 00:00Z with no
CANCELLED transition, so Main rewrote that plan's public history; the published page cannot change without a new
publish.
Fix in `plan_analysis_pages_v1.ended_plan_status`: an untriggered plan that Main ended CANCELLED without a
cancel_kind, or EXPIRED, becomes `{"status": "EXPIRED", "no_entry": true}` (Main's word kept as `export_status`);
`_assemble` writes "Status: expired, no entry" and "(plan expired, no entry)". INVALIDATED (the plan's own cancel
level), a runaway CANCELLED, a triggered plan and a record without an outcome keep their word; a stored page without
the mark keeps its bytes; the CC-584 daily check still finds "status: expired".
Tests: `test_the_bitcoin_record_of_21_nov_reads_expired_no_entry`, `test_the_page_says_expired_no_entry_where_it_said_cancelled`,
`test_a_page_stored_before_the_change_keeps_its_bytes`, `test_other_ends_keep_mains_word`.

## 4. Page capture budget (Ops Product's added item; Builder E's cause)

22 Nov 19:39Z the minute job hit its five-minute limit mid-capture and the next run published text only. Now
`scripts/plan_status_posts.py` passes `job_deadline=started + 300` to `plan_reader_editorial_v1.run_due`, which sets
`plan_analysis_pages_v1.PAGE_CAPTURE_ALLOWED` for its slice; `_card` passes it to the existing `snapshot_allowed`
hook of `tradingview_snapshot_v1.plan_snapshot` (as the plan posts do with their run budget). A new attempt starts only
if 90 s (Builder E's attempt time; the live 90 s retry time before E) plus a 20 s margin ends before the limit;
otherwise it is DEFERRED with no attempt used, the page render raises, run_due records SOURCE_PAGE_PENDING, and the next
run captures. Outside run_due (tests, CLI resume) nothing changes.
Tests: `test_page_capture_budget_20261123.py` (the start rule, a deferral with no attempt, the capture with time left,
run_due setting and clearing the budget, the job passing its limit).
Open: a deferral still starts the capture's 5-minute wait window (`started_at_utc`, Builder E's file). If the job runs
out of time on several runs in a row, the window can expire and E's fact card is used. Changing that is E's call.

## Tests: branch versus live head

The same 34 covering files (desk, pages, editorial, posts, alerts, decision checks, B's and C's audits) were run once on
the branch (at `dee92423`) and once on a detached live head (`6e52dca4`):
- branch: 842 passed, 6 failed; live head: 804 passed, 5 failed.
- The 5 shared failures are older than this branch: `test_discord_queue_cc437` (3: substituted thread, frozen copy,
  ended unstarted fill), `test_light_model_caller_cc512::test_next_image_preparation_continues_legacy_failure_once_and_keeps_original_bytes`,
  `test_public_rules_cc583::test_f5_weekly_unscored_expiry_uses_the_same_rule`.
- The sixth (`test_light_model_caller_cc512::test_variant_consumer_still_checks_the_fallback_source_and_copy`, a packet
  without `source_plan`) was fixed in `36365a32`; that file, the editorial, page and posts files pass again apart from
  the shared failure.
- On a scratch merge of this branch (36365a32) with Builder E's 51fda991: E's chart-fallback tests, this branch's four
  new test files, cc584, cc543 alerts, cc432 pages and cc512: 171 passed, 1 failed (the shared cc512 legacy-image id).

## Left

- The 21 Nov Bitcoin page stays as published ("cancelled") until a republish; Main's rewritten transition is Main's
  defect to raise (its public transitions should only append).
- The idea pack has no Posted mark or tracking of Jim's TradingView posts.
