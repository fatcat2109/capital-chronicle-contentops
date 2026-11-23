# Delivery: backlog/cc-774-readback-incomplete-and-tests-20261123 (Claude Builder I, 23 Nov 2026)

- Branch: `backlog/cc-774-readback-incomplete-and-tests-20261123`
- Base: 67ceb43e. The live head 2b775517 (Builder G's test debt and Builder H's cc-777 integrated) was merged in (3663b251) before the final test runs.
- Commits: f13d43cf (CC-774 code and tests), 18684f70 (five test ids), 3663b251 (merge of the live head), 9c3d33d1 (test id 4, after H went live). This note is the next commit.
- Nothing was posted, sent or opened. Nothing under Runtime was touched. The store was read only through Builder A's copy `C:\CapitalChronicleScratch\builder-a-cc683-data\store_copy_20261123.sqlite3`; each replay ran on its own byte copy.

## Piece 1: CC-774

### What was wrong

On 21 Nov the minute job read the X thread of `plan-result-post-e0f557aab6350bf4877ef518d5784123` 98 times between 00:42Z and 11:21Z. Every read found the post and returned `SUCCESS / NEO_THREAD_READBACK_INCOMPLETE` with `content_verified: false`. Only the view count, the timestamps and the invocation id changed between reads. Each run builds a new `EndpointNeoExecutor` with a new invocation id, so each run made a new request. The 10-minute reuse in `fresh_readback_request` reuses only verified reads.

The replay also found a defect in CC-683 on the live head. When a later read on the same day could not run (`NEO_REGISTERED_PROFILE_UNAVAILABLE` at 01:41Z), CC-683's end row was handed back on every later run. That end carries no observation, so `_reconcile` moved the X reconciliation from `RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE` to `RECONCILIATION_PENDING`. In the coordinator replay on the live head this happened in 69 of 98 runs.

### What changed

- `live_contentops/native_neo_executor_v1.py`: `observed_incomplete_readback(request, result)` is true for a read that ran and found the public object but could not verify its whole content. That means `content_verified is False`, an object id or URL, a native return hash, and no absence proof. It is false for a deferred image comparison, which still asks for the full read at once (5 Nov EIA).
- `live_contentops/neo_endpoint_executor_v1.py`: `EndpointNeoExecutor._repeated_incomplete_readback`, called at the end of `fresh_readback_request`. It applies only to the standalone minute-job executor and only to a routed read. It looks at today's (UTC) observed reads of the same read: the same `readback_binding`, the same `readback_transport_revision` (reader code) and the same observing tool and surface (endpoint). If the latest of them is an incomplete observation, it hands back that issued request, and its saved return answers the read. Nothing new is written.
  - The post is read again once, no sooner than 30 minutes after the later of the last read and the last CC-683 end.
  - A changed post, copy or dispatch clock, a changed reader or a changed endpoint is a different read and reads at once.
  - At most two tries per read and UTC day. CC-683 end rows count as tries.
  - The observation outranks an end, so a try that could not run no longer pushes CONTENT_INCOMPLETE back to pending.
  - Unchanged: verified reads (the existing 10-minute reuse), reads under a native parent, every PUBLISH and EDIT, and reads that observed nothing (CC-683).
- `live_contentops/posted_chart_readback_v1.py`: chart evidence on a browser read now carries that read's own observation time instead of the current time. Before, each run added a new readback evidence row for the same observation, because only `posted_chart_readback.observed_at_utc` differed. Fresh pixel comparisons, the API image routes and Telegram still stamp the current time.
- `tests/test_readback_incomplete_cc774.py` (8 tests):
  - the 21 Nov case: 98 runs give 2 reads, every run keeps the observation and `write_exists`, and no end row is written;
  - the 30-minute later try, and a new UTC day reads again;
  - a changed post or reader reads at once;
  - the observation outranks a later try that could not run;
  - a verified read is not held;
  - a native parent is unchanged;
  - the classifier;
  - chart evidence keeps its observation time.

### Replay on a copy of the store

Tools are in `C:\CapitalChronicleScratch\builder-i-tools\`; results are in `C:\CapitalChronicleScratch\builder-i-data\`.

- **21 Nov X-thread group, through the coordinator** (`replay_reconcile.py`). For each of the 98 original runs at its minute, a fresh minute-job composition (`bind_native_neo_coordinator`, `automatic=True`) calls `readback_existing_dispatch` on `dispatch_6b9523b884609108f45751e858725f60`. The browser returns what that run actually got.
  - Branch: 2 reads (00:42:20Z and 01:15:25Z) and 0 end rows. The reconciliation stays `RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE` after all 98 runs. 2 readback evidence rows were added. (`reconcile_x21_branch.json`)
  - Live head 67ceb43e: 31 reads and 2 end rows. The reconciliation stayed CONTENT_INCOMPLETE after 29 runs and went to RECONCILIATION_PENDING after 69. 32 evidence rows were added. (`reconcile_x21_live.json`)
- **Same group through Builder A's handoff harness** (`replay_cc683.py`, all 100 originals): branch 3 requests, live head 32.
  - The third request on the branch is a different read: the discovery read at 00:34Z, with no object id, which could not run (profile unavailable) and ended once under CC-683.
  - The post itself is read twice. (`replay_x21_branch.json`, `replay_x21_live.json`)
- **All 97 groups, up to 60 runs each** (2,350 runs): branch 255 requests, live head 285. The maximum per post-destination-day is 11 on the branch and 32 on the live head. On both, 37 groups have more than two. (`sweep_branch_final.json`, `sweep_live.json`)
  - One of the 37 branch groups is the 21 Nov thread itself, at 3: its 2 reads plus the discovery request explained above.
  - The other 36 are not CC-774's class:
    - X heavy-quote reads (up to 11 a day) return complete reads (`READBACK_COMPLETE`);
    - groups whose CC-683 cause changed within the day (allowed by CC-683);
    - old 4-5 Nov LinkedIn rows rebuilt on today's code.
  - Each of those 36 has the same count on the live head, except one Notes group (5 on live, 4 on the branch).

## Piece 2: the six failing ids

| # | Test id | Verdict | Commit that changed the behaviour | Change |
|---|---|---|---|---|
| 1 | `test_capital_chronicle_desk_record_source_v1.py::test_mandatory_source_credit_is_preserved[disclaimer]` | stale, but the old notice was not the cause | d43abc7e (CC-338, 10 Nov): a BLS source the article names in full needs no export disclaimer footer | The disclaimer case checks that a BLS article passes without the footer, and that the same source under another official class (BEA) still needs its disclaimer. The fixture now writes the current notice; `validate_article_citations` still accepts the old one on stored items. |
| 2 | `test_native_editorial_continuation_v1.py::test_writer_notice_survives_all_eight_derivatives_and_thread_limits` | stale | edac397c (CC-395, 10 Nov): every package carries the current notice | The test now takes two bodies, one with the current notice and one with the old one (a stored item). Both give the current notice in all 8 packages within thread limits. |
| 3 | `test_retrospective_piece_v1.py::test_real_retrospective_notice_and_bound_fed_attribution_survive_all_previews` | stale for the notice; the preview failure was Builder G's real defect, fixed in 876fb985 (now live) | edac397c (CC-395) | It expects the current notice in each package. The stored 1 Nov body keeps its old line. It passes only with G's 876fb985, which is now merged. |
| 4 | `test_post_visuals_v1.py::test_shared_transport_preserves_installed_image_failure_fallback[linkedin]` | stale | f4367ae1 (CC-684, 21 Nov): a new LinkedIn member copy goes through Neo; one without that route is refused before transport as API-retired | Test only, changed after H went live (2b775517): the LinkedIn intent carries `transport_type: BROWSEROS_NEO_MCP`. `post_visuals_v1` is untouched. |
| 5 | `test_capital_chronicle_desk_record_source_v1.py::test_dated_new_desk_writer_resumes_exact_prompt_but_refuses_changed_prompt` | stale | 121e15fb (CC-338, 10 Nov): a writer whose governed input is unchanged replays its issued prompt after a template change; only changed input conflicts | Renamed to `test_dated_new_desk_writer_resumes_exact_prompt_and_refuses_changed_input`. A changed prompt gives the same pending request, and a changed governed input raises CONFLICT. |
| 6 | `test_cpi_reaction_verification_cc425.py::test_current_visual_reviewer_keeps_exact_binding_and_unresolved_issue_guard` | **real defect** | e010a55a (CC-659, 18 Nov) began copying `binding["reviewer_assignment"]` in `validate_final_visual_return` | See below. The test is unchanged, and a new test covers the refusal. |

**Real defect (id 6).** `native_desktop_editorial_v1.validate_final_visual_return` read `binding["reviewer_assignment"]` without checking that the key exists. An issued binding without it stopped with `KeyError` instead of a named refusal. The store copy holds six such bindings: decision-53 bindings of 4, 10 and 17 Nov (`cc124-next-article-20261104-a`, `cc124-next-article-20261103-b`, `cc124-prepare-20261103-a`, and three of `cc338-cpi-preview-20261110-v1`).

The fix copies the assignment only when the issued binding has one. A binding without it is compared as it is and gets `FINAL_VISUAL_REVIEW_REVISION_CHANGED`, as before e010a55a. The new test `test_issued_binding_without_reviewer_assignment_gets_the_named_refusal` fails on the live head (KeyError) and passes here.

## Tests

- Before the merge, on the branch: the 108 test files that name `native_neo_executor_v1`, `neo_endpoint_executor_v1`, `posted_chart_readback_v1` or `native_desktop_editorial_v1`, plus the six ids' files. Result: 33 failed, 2898 passed, 12 skipped (`branch_targeted.log`). Builder G's integrated branch fixed most of the 33.
- After merging the live head 2b775517, the 21 files that held a failure, plus `test_readback_incomplete_cc774.py`, `test_readback_once_cc683.py` and the six ids' files, were run on the branch and on a detached live-head worktree:
  - branch: **10 failed, 695 passed** (`files_branch.log`);
  - live head 2b775517: **16 failed, 679 passed** (`files_live.log`).
  - The 6 ids that fail only on the live head are this item's six; all pass here. The other 10 fail on both, so this branch adds no new failure.
- The 10 still failing on the live head (not in this item; not traced here):
  - `test_capital_chronicle_report_editorial_workspace_v1::test_correction_after_existing_article_and_withdrawal_link_obsolete_previews`
  - `test_native_configured_provenance_v1::test_final_review_accepts_labelled_max_only_with_same_actual_writer`
  - `test_native_desktop_editorial_v1::test_presence_is_not_validity_instagram_fallback_and_linkedin_expiry`
  - `test_native_editorial_claude_cc300`: two parameters of `test_a_claude_return_without_true_labels_or_invocation_evidence_is_refused`, and `test_the_next_role_call_has_the_same_claude_session_run_the_stage`
  - `test_native_headline_filter_v1::test_role_model_effort_fail_closed`
  - `test_native_manual_candidate_v1::test_active_candidate_preserves_media_writer_role_and_same_writer_guards`
  - `test_native_newsroom_publication_recovery_v1`: `test_scheduled_source_recovery_rejects_wrong_identity_budget_or_freeze[max_frozen]` and `test_planned_source_request_survives_initial_empty_resolver_packet`

  Most of them check model or effort labels; they look like the decision-60 change Builder G found in id 5b.

## Left undone

- The live-store check (two reads a day, CONTENT_INCOMPLETE kept) needs this branch live and a day of runs. Posting is paused until the relaunch.
- Complete reads that repeat, such as the X heavy-quote reads (up to 11 a day, `READBACK_COMPLETE`), are outside CC-774 and unchanged.
- The second read of the day writes its own evidence row even when it saw the same thing (the 21 Nov replay shows 2 rows). That is the one later try the outcome allows.
- The 10 live failing ids listed above.
