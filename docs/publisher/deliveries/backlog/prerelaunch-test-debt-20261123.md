# Delivery: backlog/prerelaunch-test-debt-20261123 (Builder G, 23 Nov 2026)

Goal: the 26 failing ids on the ContentOps live head 568a0825, in 10 test files, pass.
Base 568a0825; the live heads e542abc7 (Builder E) and 67ceb43e were merged in before the final run.
Nothing was posted, sent or opened; nothing under Runtime was touched.

Result: 25 ids were stale tests, 1 was a real code defect (id 7). All 10 files pass on the branch
(final run in the last section).

## Per id

| # | Test id(s) | Verdict | Commit that changed the behaviour | What changed here |
|---|---|---|---|---|
| 1a | `test_discord_queue_cc437.py::test_channel_route_refuses_a_substituted_thread_or_reply` | stale | 6ca6f4d8 (CC-584, 14 Nov): `validate_parent_intent` runs the shared freshness rule, which reads the held outbox row | The test passes a store with no held row, plus the row's key, format 4 and clock. The route assertion is unchanged. |
| 1b | `...::test_frozen_copy_survives_a_formatter_change_but_changed_intents_and_private_copy_do_not` | stale | 6ca6f4d8 (same freshness rule); bed0c9c1 (CC-584): an image is required on every format-4 post (decision 82) | Same store, key and clock; the run context carries one TradingView chart asset. All three assertions are unchanged. |
| 1c | `...::test_ended_unstarted_fill_update_retires_before_preparation_without_changing_bytes` | stale | bb09c3ed (CC-584) and 3df2d098 (CC-672): each refused row records its readbacks | The expected result adds `"readbacks": []`. |
| 2 | `test_light_model_caller_cc512.py::test_next_image_preparation_continues_legacy_failure_once_and_keeps_original_bytes` | stale | e4bd997a (CC-465, 21 Nov): removed the template acceptance artifact and `ACCEPTANCE_CONTROL` | Removed the monkeypatch of the deleted constant. |
| 3 | `test_public_rules_cc583.py::test_f5_weekly_unscored_expiry_uses_the_same_rule` | stale | 0a1c8c6e (17 Nov, "describe expired plans without inferring a missed zone"): the weekly record uses `no_entry_words` | Expected text: "the entry window ended with no entry; not scored." |
| 4 | `test_image_templates_cc465.py::test_instagram_publishes_and_reads_back_the_native_chart_and_table` | stale | cc585388 (CC-681, 22 Nov): every readback also observes the posted images (`observe_images=True`) | The fake `read()` accepts `observe_images` and asserts it is True. |
| 5a | `test_dated_distribution_recovery_v1.py::test_dated_amendment_retains_original_bytes_and_one_exact_send[facebook_page, instagram_business, youtube]` | stale | e0048b30 (CC-463, 11 Nov): one image contract before every fresh write, which reads the run's media through `_durable_intent_inputs` | The fixture's fake `_durable_intent_inputs` also returns `media_assets`, as the real reader does. Without it the contract refused with `KeyError 'media_assets'` (PUBLICATION_IMAGE_CONTRACT_INVALID). |
| 5b | `...::test_wrong_model_cannot_accept_dated_recovery` and `...::test_current_social_reviewer_still_requires_max` | stale | 49dd59f4 (CC-403, 10 Nov): `validate_native_configuration` records the actual values and never vetoes (decision 60) | Renamed to `test_other_model_review_is_recorded_as_observed_without_a_send` and `test_current_social_reviewer_effort_is_recorded_as_observed`. They check that the actual model or effort is kept verbatim (C5) and that accepting a review sends nothing. |
| 6 | `test_plan_status_recovery_cc340.py::test_late_recovery_requires_validity_and_is_bounded_to_24_hours[None-...]` | stale | bddc6ffb (CC-515, 12 Nov): an invalid row is isolated at the consumer, not a rejected export; the same commit updated the CC-400 tests but not this one | It checks that the contract still refuses `status.plans[0].expires_at_utc` and that nothing is queued. The stub Main root has no schemas for the row projection, so the run status there is EXPORT_UNREADABLE. |
| 7 | `test_public_time_cc326.py::test_et_retrospective_notice_survives_all_eight_native_packages` | **real defect** | edac397c (CC-395, 10 Nov; found by bisect over first-parent commits) changed the analysis-notice constant | See the defect section below. The test is unchanged. |
| 8 | `test_publication_coordinator_v1.py::test_case_g_expired_destination_isolated`, `::test_complete_v1_transaction_attempts_all_eight_ready_derivatives_once`, `::test_one_derivative_failure_does_not_block_remaining_ready_derivatives` | stale | f4367ae1 (CC-684, 21 Nov): a new LinkedIn copy also goes to the company page through Neo, and a restriction stops only the affected account | The expected destinations, publish calls and derivative counts include `linkedin_company`. Case G: the member's REAUTH_REQUIRED holds only the member copy. |
| 9 | `test_reopened_article_routes_cc454.py::test_linkedin_readback_binds_exact_activity_id_to_its_author` (8 params) | stale | cc585388 (CC-681): the LinkedIn readback drops avatar and actor images with `img.closest(...)` | The fake DOM image has `closest()`, as every real element does. |
| 10 | `test_restore_x_cc431.py::test_missing_x_identity_holds_every_derivative` and `::test_pending_x_identity_reaches_the_coordinator_caller` | stale | 52d7906f (CC-124, 21 Nov): the X identity proof moved from the whole-article preflight to the X dispatch; that commit added its own covering test | Renamed to `test_missing_x_identity_holds_only_x` and `test_pending_x_identity_returns_its_request_on_the_x_result`. A missing identity holds X alone (SESSION_UNAVAILABLE), the other outlets still send, and a pending identity returns NATIVE_NEO_TOOL_PENDING with its request on the X result. |

Each changed test carries a comment that cites its commit.

## The real defect (id 7)

`v1_simple_gemini_newsroom_v1._reader_safe_native_article` carries the "Retrospective analysis, written on
D Month YYYY (ET)" line into `editorial_scope_notice`. That line has no full stop. Before edac397c, the old
analysis notice ("Analysis, not financial advice. Readers decide whether to trade.") was appended after it
whenever the body held it, so the paragraph ended with a full stop. edac397c changed that constant to the
current notice. An article whose body lacks the current notice (every article before 10 Nov, or any body
without that exact sentence) now leaves the bare date line as its own thread paragraph. The X and Threads
sentence-boundary check then refuses it, and `_native_preview_bundle` fails the whole package with
`native_preview_quality_contract_failed:threads:orphan_fragment_count;...;x:...`.

Fix (commit 876fb985): the carried line gets a full stop inside the scope notice. The Substack body and the
regex that finds the line are unchanged. Issued intents keep their frozen bytes.

Check: 36 test files that touch the scope notice, the newsroom previews or retrospective pieces were run on
the branch: 6 failed, 1073 passed. The same 6 ids also fail without the fix, so the fix adds no new failure.
They are listed below.

## Failing ids found outside the 10 files (not fixed here; same on the live head)

- `test_capital_chronicle_desk_record_source_v1.py::test_mandatory_source_credit_is_preserved[disclaimer]`
  and `test_native_editorial_continuation_v1.py::test_writer_notice_survives_all_eight_derivatives_and_thread_limits`
  and `test_retrospective_piece_v1.py::test_real_retrospective_notice_and_bound_fed_attribution_survive_all_previews`:
  they still expect the pre-edac397c notice "Analysis, not financial advice." Likely stale; the reader-facing
  wording owner (Ops Product) should confirm and update them.
- `test_capital_chronicle_desk_record_source_v1.py::test_dated_new_desk_writer_resumes_exact_prompt_but_refuses_changed_prompt`:
  DID NOT RAISE ValueError (probably the same decision-60 label change as id 5b; not traced).
- `test_cpi_reaction_verification_cc425.py::test_current_visual_reviewer_keeps_exact_binding_and_unresolved_issue_guard`:
  `KeyError: 'reviewer_assignment'` (not traced).
- `test_post_visuals_v1.py::test_shared_transport_preserves_installed_image_failure_fallback[linkedin]`:
  CC684_LINKEDIN_MEMBER_API_RETIRED (stale against f4367ae1, CC-684). `post_visuals_v1` is Builder E's file,
  so it was left alone.

## Final run (branch head before this note, live head 67ceb43e merged)

`python -B -m pytest -q -p no:cacheprovider --basetemp=C:\CapitalChronicleScratch\builder-g-tmp` on the 10 files:
**471 passed in 548 s, 0 failed** (head e1bce311). Before the fixes the same 10 files gave 26 failed, 445 passed on 568a0825.
