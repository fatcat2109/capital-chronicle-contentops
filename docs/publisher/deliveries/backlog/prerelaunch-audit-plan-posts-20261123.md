# Delivery: pre-relaunch audit of the plan posts and the relaunch path (Builder B, 23 Nov 2026)

- Branch: `backlog/prerelaunch-audit-plan-posts-20261123`
- Commits: `79867560923561544e85333fcea5f2d6801cd7a6` (audit fixes), then one commit with Builder C's three
  findings, the promised result and this note (its sha is the branch head; see the report).
- Base: `b4508d05d948035b3d29d2f990353a1889a0d626` (the live head at the start)
- Ordered by Jim, 23 Nov 2026 (decision 161): audit before the relaunch; no reviews.

## Files changed

- `live_contentops/plan_call_cards_v1.py`: `inside_jim_pause`, `OPEN_PAUSE_END`, `PROMISED_RESULT_PLANS`, `queue_posts` (result rows record
  `result_queued_at_utc`; pause test through `inside_jim_pause`), `settle_pending` (a result's 24-hour attempt
  limit counts from `result_queued_at_utc`), `destination_payloads` (passes the scenario-voice layout flags).
- `live_contentops/plan_state_alerts_v1.py`: `compose` (scenario-voice waiting lead), `scenario_case_count`,
  `nine_layer_parts` (`cases`, `whole_lines`).
- `live_contentops/plan_reader_copy_v1.py`: `_scenario_voice_quote`, called by `_public_plan_quote` for
  scenario-voice quotes only; `whole_scenario_quote`, used by `scenario_case_copy`; `validate_fields` accepts the
  scenario-voice case labels.
- New: `tests/test_prerelaunch_audit_plan_posts_20261123.py`,
  `docs/publisher/prerelaunch-audit-20261123/fixtures/btcusd-plan-20261123.json` (the 23 Nov Bitcoin plan's row of
  Main's public export, as stored in its plan-post row).
- Not changed: `plan_status_posts_v1.py`, `scenario_voice_v1.py` (audited, no defect needing a change there).

Stored bytes: every changed copy path is gated by `scenario_voice` (no stored row in the production store
carries `CC755_V1`: searched on the copy, 0 rows) or by the new `result_queued_at_utc` field. All 25 stored
format-4 plan-post rows of 18-23 Nov recompose to their exact stored text and pass `validate` on the branch.

## Evidence (all on copies, under `C:\CapitalChronicleScratch\builder-b-audit-data\`)

- `store_copy.sqlite3`: sqlite backup of the production store from a `mode=ro` connection, 23 Nov 09:35Z.
- `export-now\`: copy of Main's `plan-status.public.json` and `plan-transitions.public.json`, generated 09:38:22Z.
- `scripts\audit_rows.py`: recomposes the stored rows, renders every destination, checks the public-copy rules.
  Results: `recompose\` (stored rows on the base), `recompose-voice\` (the same plans as new scenario-voice rows on
  the base), `recompose-voice-fixed\` and `recompose-fixed\` (after the fixes). `findings.json` in each.
- `scripts\relaunch_sim.py`: two minute ticks at a relaunch of 30 Nov 18:00Z on a writable copy of the store, with
  Main's export re-dated and the scenario's changes; prepare_post and the send are recorders, secrets are never
  read. Results: `relaunch\result-*.json` (base) and `relaunch-fixed\result-before.json` (branch).

## Defects found

| # | Rule | Row kind / destination | Evidence | Status |
|---|------|------------------------|----------|--------|
| 1 | Relaunch: no partial or misleading late posts | result, all destinations except Telegram/Discord | `relaunch\result-before.json`: the 22 Nov USD/JPY result queued at the relaunch went to Telegram and Discord in the immediate pass, then threads, facebook_page, instagram_business, x, substack_notes were closed in the same minute (`PUBLISHING_OLDER_THAN_24_HOURS`), because the age counted from the plan's ending. Same for every correction (its clock is the original ending). | Fixed: `settle_pending` + `result_queued_at_utc`; `relaunch-fixed\result-before.json` reaches every destination; test `test_a_dated_result_queued_at_the_relaunch_is_not_closed_by_its_old_ending`, `test_new_result_rows_record_when_they_were_queued` |
| 2 | Relaunch: results after the pause must post | result | `jim_pause_window` returns an end of `datetime.max` when `restored.json` is absent: if the tasks are enabled while the record is missing (the restore raises after enabling them, e.g. a stop-file unlink error, or tasks enabled by hand), every later result is skipped as `JIM_PAUSE_RESULT_SHOWN_IN_SCORECARD` for good. | Fixed: `inside_jim_pause` (after the earliest resume, 25 Nov 16:00Z, a running job posts a result that ended within its 60-minute window); tests `test_pause_window_and_a_missing_restore_record`, `test_the_live_window_reads_the_restore_record_and_falls_back` |
| 3 | No internal terms (decision 107: market names, not the book's symbols) | setup/update/result, every destination | `recompose-voice\`: "Base case (54%): BTCUSD is below 60977.64 ...", "60-day US500 beta", raw "68450.00" | Fixed for scenario-voice rows: `_scenario_voice_quote`; test `test_scenario_voice_quotes_read_for_people` |
| 4 | No internal terms | setup (23 Nov Bitcoin), every destination | "Priced in: ... not officially confirmed in the frozen files"; "What would undo the base case: 68450.00 is above ... the lane's measured minimum 6,862.67" (stop-placement note); "What would undo the base case: Stop tightening fact." (a list label) | Fixed for scenario-voice rows: phrase removed, desk notes refused, and a case line takes a whole field only from its first sentence on (`whole_scenario_quote`), so no clause that leans on a dropped one; tests `test_scenario_voice_drops_desk_notes_and_fragments`, `test_case_lines_never_open_on_a_clause_whose_subject_was_dropped` |
| 5 | Scenario voice must not mislead | setup, every destination | CC-755 rewrote "trapped shorts fuel a squeeze" as "trapped traders positioned for losses fuel a squeeze" and "net long positions" as "net positions set for gains" | Fixed: "bets on a fall/rise", true whether the source means traders or the desk's own trades (Builder C's page case: "The desk's own recent traders positioned for losses ... have paid"); "bullish/bearish" would trip decision 40's unconditional-call guard |
| 6 | Plain copy | setup (WAITING), every destination | "Bitcoin: armed, waiting for price breaks through 60,250 (breakout)." (jargon, broken verb) | Fixed for scenario-voice rows: "Bitcoin: waiting for price to break through 60,250 (breakout)."; non-voice rows keep their bytes; test `test_a_waiting_plan_reads_plainly_in_the_scenario_voice` |
| 7 | Buy zone and invalidation given (decision 158) | setup, x and threads | X carried the call, zone and cancel line in post 8 of 10, Threads in its last part | Fixed: `nine_layer_parts(cases=...)` puts them right after the case headings; test `test_short_routes_give_the_call_right_after_the_cases` |
| 8 | No sentence cut mid-way | setup/update, linkedin and linkedin_company | overflow path excerpts every layer to an equal share with "…" | Fixed for scenario-voice rows: whole lines kept in order, the rest on the linked page; test `test_linkedin_overflow_keeps_whole_sentences`. No audited row reached the overflow path. |
| 9 | Cancel as a condition (CC-682) | rows of cards announced before CC682 | "Bitcoin plan cancelled on high at or above 68,450 before entry" in the 22 Nov MID card and its fill | Not changed: a later post keeps its card's level contract so the thread stays consistent; every new card uses "Cancel if ...". |
| 11 | Scenario voice (decision 158), reported by Builder C | reader fields (CC-466 social copy) | `validate_fields` accepted only "Main (odds%):" and "Alternative (odds%):" | Fixed in the validator only: it accepts "Base case", "Bull case", "Bear case" beside the old labels, with decimal odds; the prompt half sits in `plan_reader_editorial_v1` (Builder C's file), not changed here; test `test_reader_fields_accept_the_scenario_voice_labels` |
| 12 | No sentence cut mid-way, reported by Builder C | pages, wraps, plan posts (scenario voice) | `scenario_case_copy` took the first passing sentence of a driver, e.g. "BTC carries that through a 1.31 beta" | Fixed with #4 (`whole_scenario_quote`) |
| 10 | Targets off (decisions 40, 157) | update (22 Nov 19:27Z Bitcoin fill, PUBLISHING) | queued before 22 Nov 22:30Z, carries "Target level: 53,000" | No change needed: at the relaunch it is older than 24 hours and settles, or is superseded if the position closed (simulated both); no destination sends it. Every row queued after the policy prints no target (checked on all destinations). |

Checked and holding on the base for current rows: notices once per destination (CC-729), result leads with the
result and names its dates, "Correction to the ..." (CC-768), chart credit on the first part with the chart on
the root, no model names, every part within its platform limit.

## Promised result (Ops Product, 23 Nov)

The correction on Telegram 232 and its Discord thread (23 Nov 04:23Z) promises the result of the 20 Nov USD/JPY
plan `plan_4bcfb1182f0fff4f8254172c` "in its own post". `PROMISED_RESULT_PLANS` names it; it is exempt from the
pause skip, and the relaunch rules above (dated result reaches every destination) already let it post. It posts
once, when Main scores it (today its outcome is unscored: `OUTCOME_LIFECYCLE_JOIN_INVALID`, Ops Live's item).
Its frame will read "USD/JPY, plan of 20–22 Nov: ..." (not "of 20 Nov"): the close at 23 Nov 03:00:13Z is
22 Nov 22:00 ET, and CC-768's frame uses the public ET calendar. Tests: three cases of
`test_a_result_promised_by_a_published_correction_posts_a_week_later` (scored 03:00:13Z; scored inside the pause;
a control plan inside the pause stays off).

## Relaunch simulation (30 Nov 18:00Z, Main's export of 23 Nov 09:38Z re-dated)

- Setups still active: none posts. A setup older than 24 hours is refused at the queue
  (`PLAN_SETUP_OUTSIDE_QUEUE_WINDOW`); one between 60 minutes and 24 hours is queued and retired as stale.
- Fills during the pause: older than 24 hours settle (`LATE_STATE_LIMIT_24_HOURS`); a fill inside the last 24
  hours posts, dated "Updated ...". The pending 22 Nov Bitcoin fill (PUBLISHING) settles, or is superseded once
  the position closed.
- Results that ended inside the pause: skipped (`JIM_PAUSE_RESULT_SHOWN_IN_SCORECARD`): the 20 Nov USD/JPY time
  exit (simulated at 06:00Z 23 Nov), the Bitcoin MID short (simulated stop 27 Nov), and three untriggered plans
  that ended on 23 Nov.
- A result that ended just before the pause (simulated 04:40Z 23 Nov): one post, "USD/JPY, plan of 20–22 Nov:
  ...", on every destination after the fix (Telegram and Discord only before it).
- A correction of a published result: "Correction to the 19 Nov Gold result: ...".
- The open Bitcoin MID short closing after the restore (simulated 30 s before the relaunch tick): one post,
  "Bitcoin, plan of 22–30 Nov: stopped at its invalidation level.", on every destination
  (`relaunch-fixed
esult-btc_closed_after.json`); its old fill row is superseded, not re-sent.
- Duplicated transitions: no duplicate row. A second minute queues nothing new. 31 never-announced plans stay
  `PLAN_NEVER_ANNOUNCED`; 12 old fills `POSITION_CLOSED_BEFORE_FILL_ANNOUNCEMENT`.

## Tests

Command: `python -B -m pytest -q -p no:cacheprovider --basetemp=C:\CapitalChronicleScratchuilder-b-tmp <files>`,
one process at a time, on the branch worktree. Outputs: `tests-branch-core.txt`, `tests-branch-second.txt`,
`tests-branch-third.txt` in the evidence folder.

- Core (17 files: the new audit file, test_plan_copy_cc682, test_plan_state_alerts_cc543, test_plan_call_cards_cc399,
  test_result_frame_20261123, test_jim_pause_results_20261123, test_scenario_voice_cc755,
  test_targets_off_decision40_20261123, test_minute_consumer_cc515, test_plan_analysis_layers_cc730,
  test_plan_analysis_copy_cc688, test_plan_thread_consistency_cc549, test_plan_scenario_lines_ops_20261120,
  test_plan_queue_clock_cc732, test_plan_result_posts_cc322, test_plan_page_current_cc584,
  test_plan_publication_freshness_cc584): 312 passed, 1 failed. The failure,
  `tests/test_scenario_voice_cc755.py::test_minute_queue_and_three_platforms_use_the_new_voice`, was this branch's
  own (a four-word minimum dropped "Physical demand slowed."); the rule was removed and the test passes below.
- Second (13 files, after Builder C's fixes: the audit file, test_scenario_voice_cc755,
  test_targets_off_decision40_20261123, test_result_frame_20261123, test_plan_analysis_layers_cc730,
  test_plan_reader_copy_cc466, test_plan_reader_editorial_cc466, test_plan_analysis_pages_cc432,
  test_market_wrap_cc689, test_x_reply_pack_cc455, test_manual_desk_cc748, test_public_output_golden_cc691,
  test_public_decision_checks_cc690): 213 passed.
- Third (after the promised result: the audit file, test_jim_pause_results_20261123, test_plan_call_cards_cc399,
  test_minute_consumer_cc515, test_result_frame_20261123): 147 passed.
- Failing ids on the branch now: none, so no live-head comparison was needed (a live-head worktree was prepared
  at `C:\CapitalChronicleScratchuilder-b-livehead`, detached at the base).
- Stored rows: all 25 format-4 plan-post rows of 18-23 Nov recompose byte-identical and validate on the final
  branch (`recompose-fixedindings.json`: no RECOMPOSE_DIFFERS, VALIDATE_FAILED or payload failure).

## Left undone, outside these files

- Nine CC-603 call follow-ups (`CC603_PREPARED`, 15 Nov) and two prepared corrections are owed without an age
  limit (`freshness_limit_minutes`, call_followups_v1): whether they go out at the relaunch is the correction
  module owner's call.
- "Registered 22 Nov 22:51 ET" uses a different clock format from "Sun 22 Nov, 11:00 PM ET"; left as is.
