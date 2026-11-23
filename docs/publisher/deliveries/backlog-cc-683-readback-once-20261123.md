# CC-683 delivery: a read-back that cannot run ends once with its cause

- Branch: `backlog/cc-683-readback-once-20261123`
- Code commit: `abf1ed09ace3cf0a386e3d85b51aeac30c18b843` (this note is the next commit)
- Base: `b4508d05d948035b3d29d2f990353a1889a0d626`. The live head has since moved to 6e52dca4; this branch does not merge it.
- Builder: Claude Builder A (Opus 5.5), 23 Nov 2026, started by Ops Product.

## What was wrong

From 02:08Z to 04:13Z on 20 Nov, the minute job wrote a LinkedIn READBACK request for the gold result post (`plan-result-post-580a244ff31eb610ac567a5f53621814`) on every run: 52 requests, and none ran. On the live code of that day, LinkedIn (member) was not an automatic endpoint route. Each run built a new `EndpointNeoExecutor` with a new `neo-endpoint:<uuid>` invocation id, so each run made a new request hash and a new row, and nothing ran any of them.

Across the whole store (copy of 23 Nov), 97 post-destination-days held more than two read-back requests, 8,148 rows in all. Most of them carry one repeated cause, for example `READBACK_UNAVAILABLE / NEO_EXACT_PUBLIC_OBJECT_NOT_FOUND` 1,228 times for one Note on 18 Nov, and 610 times for one X copy on 20 Nov.

## What changed

- `live_contentops/native_neo_executor_v1.py`
  - `readback_binding(request)`: the identity of the read itself (object, copy, account, dispatch clock), without per-run fields (request hash, invocation id, 10-minute epoch, reader revision, the delivery-receipt hash, the digest hour).
  - `unrunnable_readback_cause(result)`: returns the cause of a read that observed nothing (`READBACK_UNAVAILABLE`, `SKIPPED`, `BLOCKED`, `FAILED_BEFORE_WRITE`, with no object, no text and no absence proof). Otherwise it returns None.
  - `NativeNeoExecutor._readback_ends` and `_end_readback`: one `NATIVE_NEO_READBACK_ENDED` row per issued read that could not run, in the existing outbox (`internal:native-neo-tool`, same work item). Its payload carries `result.request_sha256`, `status READBACK_ENDED`, `reason_code`, `readback_try` and `next_try`. The evening check (`day_readback_v1._native_returns`) reads it like any return, so the cause appears there once without changes to that file.
- `live_contentops/neo_endpoint_executor_v1.py`, in `EndpointNeoExecutor` (the minute job's executor):
  - Before writing a new READBACK request, the executor reuses today's end of the same read under the same route and reader revision (`_ended_readback`). It runs the read again only when the cause has changed:
    - a route appears for the destination;
    - the reader code (`executor_revision`) changes;
    - the endpoint answers again after `NEO_ENDPOINT_UNAVAILABLE`;
    - a new object, copy or dispatch clock changes the binding;
    - one later try no sooner than 30 minutes after the first end.
  - This allows at most two tries per read per UTC day.
  - A read with no route, or with the endpoint down, re-raises its first issued request, so that request stays the one pending request and no new row is written.
  - Ends are recorded at each place a read stops (`_finish_readback`): no route, endpoint down, a refusal before claim, an incomplete observation, or a returned unavailable read.
  - Unchanged: reads under a native parent (`automatic_destinations` given), every PUBLISH and EDIT request, and reads that observed something.
- `compare_public_images` (Ops Product's added request, from Builder D's finding): when the platform served a resized copy, both images are now compared at half the served size after a 1.5 blur (`RGB_RESIZED_HALF_BLUR15_TILE32_LUMA60_V1`), with the same thresholds. Same-size copies keep the old rule (`RGB_BLUR075_TILE32_LUMA60_V1`).
  - Telegram 229 (our 1600x900 chart served as an 800x450 JPEG):
    - live head: no match (rms 7.80, worst tile 19.94, luma 172);
    - this branch: match (rms 2.99, worst tile 5.78, luma 17).
  - Three other charts against the same Telegram image stay far outside the limits (worst tile 54 to 117 in every setting tried).
  - Limit: a one-digit change in a small (22-pixel) price label on a half-size re-encoded copy is below what this rule can resolve. Telegram's own re-encoding of 229 differs from our chart by more than that change does. A moved level line and its label, an added level, or a different chart all fail, as they should.

## Tests added

- `tests/test_readback_once_cc683.py` (14 tests, all pass):
  - the 20 Nov case, with no route over 52 minute runs: 1 request and 1 end row, and the request stays pending;
  - a route that appears reads at once;
  - an unreadable object read every third minute through a day: exactly 2 runs and 2 end rows, the second at least 30 minutes after the first, and one more try the next UTC day;
  - a repaired reader reads again;
  - an endpoint outage: one request, which reads when the endpoint returns;
  - native-parent reads keep the old protocol;
  - the binding ignores per-run fields;
  - only a read that observed nothing ends;
  - PUBLISH is untouched.
- `tests/test_public_image_resize_cc683.py` (3 tests, all pass): the same chart at half size as JPEG matches. A different chart fails, and a moved level fails.

## Targeted tests run on this branch (per file, in the worktree, before commit)

These are the test files that name `native_neo_executor_v1` or `neo_endpoint_executor_v1`. Ops Product stopped the sweep before the last 9 files.

Passed (exit 0): article_publication_quality_cc333 55, call_followup_readback_cc603 18, call_followup_reply_gap_cc603 15, call_followups_cc603 26, completed_finalized_intent_cc247 3, cpi_derivative_media_revision_v1 27, day_readback_cc639 55, heavy_news_quote_transport_cc467 27, linkedin_neo_recovery_v1 55, manual_desk_cc748 13, market_wrap_cc689 23, measured_odds_series_cc536 38, media_repair_cc247 11, minute_consumer_cc515 27, native_desktop_publication_v1 37, native_neo_claude_surface_cc283 8, native_neo_composed_run_cc283 12, native_neo_executor_v1 130, native_neo_verify_before_click_cc283 11, native_publication_latency_v1 28 (+3 skipped), neo_endpoint_executor_cc436 105, pinned_result_scorecard_cc394 30, plan_analysis_copy_cc688 18, plan_analysis_distribution_cc435 38, plan_link_recovery_cc584 7, plan_page_current_cc584 37, plan_publication_freshness_cc584 20, plan_state_alerts_cc543 22, plan_status_publication_cc306 15, plan_status_rationale_cc353 21, plan_substack_transport_cc466 38, plan_thread_consistency_cc549 29, platform_rules_cc393 12, posted_chart_readback_cc681 21, published_content_v1 71, readback_once_cc683 14, reader_article_contract_cc403 56, reader_presentation_revision_v1 8, public_image_resize_cc683 3.

The first three files listed below each fail some ids; every one of those ids fails on the live head b4508d05 too (rerun by id in `C:\CapitalChronicleScratch\builder-a-cc683-livehead`):

| File | Failing ids on this branch | Same ids on live head |
|---|---|---|
| dated_distribution_recovery_v1 | `test_dated_amendment_retains_original_bytes_and_one_exact_send[facebook_page]`, `[instagram_business]`, `[youtube]`, `test_wrong_model_cannot_accept_dated_recovery`, `test_current_social_reviewer_still_requires_max` | fail (same 5) |
| plan_status_recovery_cc340 | `test_late_recovery_requires_validity_and_is_bounded_to_24_hours[None-2026-11-06T13:33:46.424024Z]` | known live failure |
| public_time_cc326 | `test_et_retrospective_notice_survives_all_eight_native_packages` (`native_preview_quality_contract_failed`) | fails |
| publication_coordinator_v1 | `test_complete_v1_transaction_attempts_all_eight_ready_derivatives_once`, `test_one_derivative_failure_does_not_block_remaining_ready_derivatives`, `test_case_g_expired_destination_isolated` | fail (same 3) |
| reopened_article_routes_cc454 | 8 x `test_linkedin_readback_binds_exact_activity_id_to_its_author[...]` (the node subprocess on `neo_endpoint_steps_v1.js`, a file this branch does not touch) | fail (same 8) |

Not run on this branch, because Ops Product stopped the sweep: restore_x_cc431 (known live failure), seven_destinations_cc395, site_first_publication_v1, substack_daily_digest_v1, substack_daily_note_cc468, substack_draft_inventory_v1, telegram_public_readback_cc306, v1_simple_publication_handoff_recovery_v1, weekly_scored_calls_cc379. Ops Product's `integrate_if_green.py` runs them at integration.

## Replay on a copy of the store

The store was copied read-only from `A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3` (sqlite backup API) to `C:\CapitalChronicleScratch\builder-a-cc683-data\store_copy_20261123.sqlite3`; integrity_check returned ok. Each replay works on its own byte copy of that file.

The harness is `C:\CapitalChronicleScratch\builder-a-cc683-tools\replay_cc683.py`. It replays every original READBACK request at its original minute through the minute job's read path: a fresh standalone `EndpointNeoExecutor` per run, then `NeoDestinationHandoff.readback`. The browser is replaced by the return that run actually got. A read that had no return is replayed with no route. Nothing touches a network or a browser.

- Eight worst groups, 25 runs each (200 runs). The gold LinkedIn post of 20 Nov is among them.
  - Live head: 200 requests written, 25 per post-destination-day, 8 groups over two (`replay_live.json`).
  - This branch: 13 requests written, at most 2 per post-destination-day, 0 groups over two (`replay_branch.json`).
  - The gold post: 25 requests on the live head against 1 request plus 1 end row on this branch.
- All 97 groups, up to 60 runs each (2,350 runs; 8,148 requests in those groups originally), on this branch (`replay_sweep_branch.json`):
  - 286 requests written and 137 end rows;
  - 60 groups at two or fewer;
  - 37 groups over two, max 32.
- What the remaining repeats are:
  - Reads that observed something and so are not "cannot run": `SUCCESS` with observed text (60), `READBACK_COMPLETE` (54), `SUCCESS / NEO_THREAD_READBACK_INCOMPLETE` (31; one X thread on 21 Nov accounts for 30). This branch leaves them as they are. An end row there would hand `_reconcile` a non-observation and downgrade a CONTENT_INCOMPLETE reconciliation back to pending. They need their own item: stop re-reading an identical incomplete observation.
  - Groups with 3 end rows: these are the read's cause changing within the day (the replay's no-route turned into a routed read), which the rule allows.
  - Heavy-quote X reads (11 a day): observed reads, same class as the first bullet.
  - 37 runs could not rebuild their old intent on today's code (`MEDIA_REPAIR_EXACT_CC247_SCOPE_REQUIRED`, `READER_REVISION...`, `DATED_DISTRIBUTION...`) and were skipped.
- The live-head sweep was not run for all 97 groups. The originals (8,148) and the 8-group live sample (one request per run) show the live behaviour.

## Evidence paths (C:\CapitalChronicleScratch)

- `builder-a-cc683-data\replay_live.json`, `replay_branch.json`, `replay_sweep_branch.json` (and `.log`)
- `builder-a-cc683-data\pf-branch\*.log|*.xml|summary.txt` (per-file test results), `livehead_failing_ids.log`
- `builder-a-cc683-data\img\` (Telegram 229 public JPEG and its source chart), `builder-a-cc683-tools\tg229.py`
- `builder-a-cc683-tools\replay_cc683.py`, `selection.json`, `sweep.json`

## Left undone

- The BACKLOG acceptance line asks for proof in the live store. This branch shows it on a copy. The live check needs this branch live and a day of runs; the paused relaunch blocks both until next week.
- Reads that ran and observed an identical incomplete result still repeat (see the replay). That needs a follow-up item.
- Reads under a native Desktop parent (`plan-status-posts-cc399` style, 768 rows in the store) are unchanged, to keep the Desktop pending protocol intact.
