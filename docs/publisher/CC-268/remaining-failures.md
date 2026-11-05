# CC-268: remaining old failures, each with a named owner

- Final full run on a clean checkout (backlog/cc-268-suite-hygiene at b16979c8, rebased on live bd73f4ae; 4 Nov 23:38Z to 5 Nov 00:51Z; pytest basetemp and scratch on C:): 10,198 tests, 131 failed, 9 errors. `git status` was empty afterwards.
- Clean baseline for comparison (live head 95c9e3c3, 4 Nov 21:04Z): 10,807 tests, 515 failed, 170 errors.
- Every failing id of the final run was re-run at ca39e453 (rebased on live bda0d915, with the commits after b16979c8): 37 no longer exist (removed and listed in removed-tests.md), 5 pass, 4 skip with a named reason, and 94 still fail. All 94 had an owner here; CC-288 closed them (section below).
- None of the 94 is new: each failed on the clean baseline too, so none comes from CC-267, CC-248, CC-283 or CC-268.
- A file-write probe ran through both runs: no test wrote outside its temp folder after the Run Now fix (before it, six operator-trigger tests wrote nine raw X captures into the live headline root).

## What is left (5 Nov, after CC-288)

| Test | Cause | Owner |
|---|---|---|
| `tests/test_tiktok_local_desktop_oauth_pkce_v1.py::test_local_fake_e2e_and_refresh_leak_nothing_or_persist_anything` | OAUTH_CALLBACK_TIMEOUT. Another process (PID 29928, seen with netstat at about 06:40Z) listens on 127.0.0.1:8765, the module's fixed callback port, so the fake callback never reaches the test's listener. Fails the same way at 70c2a2a4, so not CC-297's. Not a code defect on a free port. | **Ops Product**: identify the 8765 listener; the test passes on a host where the port is free |
| `tests/test_contentops_editorial_desk_v1.py::test_review_api_origin_exact_revision_and_daily_app_readback` | ConnectionAbortedError (WinError 10053) on its 127.0.0.1 test server during the 86-minute full run; passes alone on this branch and on 70c2a2a4. | **Codex Publisher**: flaky under load; give the local server call a retry or a longer timeout |
| `tests/test_daily_app_operator_trigger_v1.py::test_historical_run_pipeline_remains_quarantined` | Same WinError 10053 on its 127.0.0.1 server in one focused run; passed in the full run and the rerun. | **Codex Publisher**: same flake |

Fixed on this branch after the full run (test-only unless noted):
- `tests/test_discord_live_adapter_v6.py` (3 cases, also failing at 70c2a2a4): decision 61 (49b238d0) sends every Discord post with its selected, hash-verified image; the photo-optional case became a DEFINITE_NO_WRITE case.
- `tests/test_substack_draft_inventory_v1.py` (2 cases, also failing at 70c2a2a4): the fixture intent now carries `plan_hash`, which the absence clock reads since 525156ac.
- `tests/test_daily_app_operator_trigger_v1.py::test_autonomous_default_operator_cycle_keeps_canonical_gate_flag_only`: passed at 70c2a2a4 and failed here because of this branch's routing fix. The supervisor's prepared-candidate refresh reads the live headline sidecars; at 70c2a2a4 it raised KeyError on a routed data-release headline and wrote no checkpoint, so the cycle got no `prepared_candidate_state`. Now it does, and the test allows that kwarg.

CC-297 follow-up (Ops Product, 5 Nov): every file in `C:\CapitalChronicleScratch\pytest-cc297\order_all.txt` ran inside the full run above at 7856953b. The only failures among them were the Discord, Substack draft inventory and TikTok files; all three fail the same way at 70c2a2a4 (run one file at a time, 4 GB free), so none comes from CC-297's secret reader.

## CC-288 result (Claude Builder, 5 Nov)

All 94 ids this file listed at 8074a821 now pass, or were removed with the reason written beside them in the test file. Branch `backlog/cc-288-outdated-tests`, live tag `contentops-live-20261105-cc288-outdated-tests`.

- Before (focused runs on a C: worktree at live 44af672b, 5 Nov 04:09-04:33Z): 94 failing (49 text-first and editorial-mode, 43 lifecycle and recovery, 2 native desk). The two Instagram pipeline cases already passed there: Codex Publisher's 44af672b gave their fixtures the selected, hash-verified image that `require_publication_image` checks (decision 61).
- After (focused runs, one file at a time, 04:09-04:48Z): 0 of them fail.
- Full run on the rebased branch: 10,267 tests at c95c838f (this branch rebased on live 7856953b), 5 Nov 04:49-06:15Z, one process, basetemp on C:: 10,191 passed, 8 failed, 68 skipped. None of the 8 is a CC-288 id. Six were then fixed on this branch; the other two, and one flake seen in a later focused run, are under "What is left".

Live code changed only for two defects the tests exposed, each with its own test (`tests/test_evidence_gate_calibration_v1.py`):
- `classify_rolling_x_story_types_deterministically` raised KeyError for three routable locator surfaces that had no story profile (`bea_current_releases_v1`, `imf_press_release_feed_v1`, `company_investor_relations_release_feed_v1`). A GDP/PCE, IMF or Nvidia-results headline in the 24 h window failed the supervisor's whole prepared-candidate refresh. Shown by `test_v1_throughput_architecture_v1::test_zero_write_prepared_candidate_to_canonical_plan_smoke`.
- `_rebind_story_scoped_receipt` kept a deep dive's `capital_chronicle_authority_not_verified` on lower modes that need no authority, so a deep dive could never downgrade (since 3c5aea4c, 21 Aug). Shown by `test_evidence_gate_calibration_v1::test_e_deep_dive_downgrades_to_standard_when_cc_authority_is_unavailable`.

| Test file | Ids | What was done |
|---|---|---|
| `tests/test_generic_evidence_freshness_visual_editorial_fabric_v2.py` | 8 | Updated to the Aug registry: default straight_news, mode profiles, adapter families; straight news needs no market snapshot. The no-mode and mismatch rules are still tested on a registry copy and an unsupported mode. |
| `tests/test_growth_first_editorial_wake_canonical_first_v1.py` | 4 | Quiet-day explainer now falls back to BREAKING_BRIEF with the fallback recorded (330f1978). Material wake: the supervisor stages it idempotently and runs no cycle itself (the routine owner is the native desk). 2 removed: FDA-G scheduled-window dispatch, unreachable under the live owner NATIVE_CODEX_DESKTOP. |
| `tests/test_native_manual_candidate_v1.py` | 34 | Fixture uses a long-form mode, which still takes media-plan then visual-edit (a brief is text-first, time-sensitive modes skip the visual edit); the source cap is read from the bound volume policy (20). |
| `tests/test_native_photoless_briefs_v1.py` | 1 | Decision 39 removed the photo minimum; analysis keeps its official-history charts (decision 41). |
| `tests/test_native_pre_writer_outcomes_v1.py` | 1 | Error code is now ANALYSIS_OFFICIAL_HISTORY_CHARTS_REQUIRED. |
| `tests/test_nonnumeric_story_authority_consumer_v1.py` | 1 | Removed: the canonical-shadow route for this family has had no registry story type since fa829e72 (1 Aug) and no live caller. |
| `tests/test_core_v0_acceptance_harness_v1.py`, `tests/test_core_v0_repeated_shadow_soak_and_recovery_v1.py` | 2 | Schema version asserted as the store's SCHEMA_VERSION (9). |
| `tests/test_daily_app_publication_lifecycle_v1.py` | 19 | Removed: they drove the supervisor's own window publication, which the live runtime never reaches (owner NATIVE_CODEX_DESKTOP, publication through DurablePublicationCoordinator). The same rules are tested in `tests/test_publication_coordinator_v1.py`. |
| `tests/test_public_object_identity_persistence_v1.py` | 7 | Removed for the same reason; the store-level identity tests stay. |
| `tests/test_dated_distribution_recovery_v1.py` | 2 | An expired stale derivative keeps DERIVATIVE_EXPIRED_STALE_NO_WRITE under an ordinary correction, with no write. |
| `tests/test_evidence_gate_calibration_v1.py` | 3 | Deep-dive downgrade passes after the defect fix; diagnostics carry the status code; a second pass skips recently failed routes; an X-only story stops before any claim contract. |
| `tests/test_executable_snapshot_requirement_separation_v1.py` | 1 | Asserts the live registry; parity with the frozen 1 Aug V5 receipt removed (historical record, no live consumer). |
| `tests/test_native_configured_provenance_v1.py` | 1 | CC-186 (4883791e) dropped the fixed authority label; positive test added. |
| `tests/test_native_live_source_recovery_v1.py` | 1 | Fixture uses a long-form mode, which keeps the visual-edit path. |
| `tests/test_native_newsroom_publication_recovery_v1.py` | 5 | 4 pass through the shared fixture; the 2 Nov replay uses the Substack-first fixture (as `test_native_text_first_v1`) and the decision 61 destination set. |
| `tests/test_story_scoped_permission_and_operator_ready_package_v1.py` | 1 | Rebuilt outcomes: straight news needs no market snapshot. |
| `tests/test_v1_throughput_architecture_v1.py` | 1 | Passes after the defect fix. |
| `tests/test_native_desktop_workspace_v1.py` | 2 | Frozen input carries `rolling_input`; the pending request is a real file, as `operation()` re-reads it. |

Open question for Ops Product (not changed here): since 330f1978, preselection can never resolve EVERGREEN_EXPLAINER or WEEK_AHEAD_OR_WATCH for a general public event, because that story type offers only straight_news and analysis; it falls back to BREAKING_BRIEF. If quiet-day explainers should exist, the registry needs those profiles.

## Skipped in a clean checkout, with the reason

Each skips only while its dependency is absent. The live root has ui/contentops_v5/node_modules, so the two renderer tests run there. The Chapter05 stock clip (Pexels 4121754) sits under the gitignored video/projects/*/public/ and is absent in the live root too. The detached-spawn test runs wherever the host job permits breakaway (the scheduled task's does).

| Test | Reason |
|---|---|
| `tests/test_contentops_daily_app_launcher_v1.py::test_detached_spawn_survives_launcher_exit` | this shell's job object forbids breakaway (WinError 5); the scheduled task's permits it |
| `tests/test_native_desktop_workspace_v1.py::test_desk_export_is_offline_read_only_and_preserves_the_existing_store` | ui/contentops_v5/node_modules is not installed in this checkout (npm ci there) |
| `tests/test_reader_first_data_journalism_v1.py::test_channel_photo_preview_keeps_archive_context_without_dropping_unknown_rights` | ui/contentops_v5/node_modules is not installed in this checkout (npm ci there) |
| `tests/test_v2_freeform_chapter_pipeline_v1.py::test_video_only_chapter_render_never_regenerates_audio` | the project's gitignored public/ media is absent in this checkout: Required dependency is missing: A:\Capital Chronicle\Worktrees\contentops-v1-lane-20261104\video\projects\frozen_without_breaking_v1\public\assets\documentary\grocery_cashier_pexels_4121754.mp4 |

## Failed in the final run, pass now

- `tests/test_contentops_ingestion_bootstrap_v1.py::test_browser_roles_remain_separated_in_launcher_summary`
- `tests/test_destination_identity_pinning_v1.py::test_global_probe_all_is_passive_and_never_calls_browser_or_provider`
- `tests/test_llm_cost_governor_v1.py::test_accepted_fallback_caches_model_scoped_unavailability_for_same_cycle`
- `tests/test_llm_cost_governor_v1.py::test_provider_attempt_budget_spans_retries_model_changes_and_next_call`
- `tests/test_substack_browser_adapter_v6.py::test_substack_segment_composer_preserves_visual_upload_order`

## Live writes the probe caught in the final run (fixed)

Run Now's forced intake sync ignored `CONTENTOPS_DAILY_APP_DISABLE_INTAKE_LANE`, so six tests in `tests/test_daily_app_operator_trigger_v1.py` drove the real X capture (CDP 9222) and wrote these raw captures into `A:\Capital Chronicle\Runtime\ContentOps\headline_ingestion\data\raw_archive\headline_cdp\`. No sidecar row was appended (every headline was already captured). They are genuine captures of the list, so they stay where they are. The switch now covers the sync, and `tests/test_run_now_intake_isolation_cc268.py` fails if any Run Now path reaches the capture.

- `step1_x_cdp_raw_20261104T234826Z_eca5433b16b85fc4.json`
- `step1_x_cdp_raw_20261104T234831Z_a60451ec1e61005c.json`
- `step1_x_cdp_raw_20261104T234844Z_5befc11a07ddcea8.json`
- `step1_x_cdp_raw_20261104T234900Z_c4a8c3a241b64dc1.json`
- `step1_x_cdp_raw_20261104T234920Z_a51c44c58522cdaf.json`
- `step1_x_cdp_raw_20261104T234934Z_2edb14e1486da727.json`
- `step1_x_cdp_raw_20261104T234938Z_cd5372b7b058d46d.json`
- `step1_x_cdp_raw_20261104T234951Z_3512a3ad850f2606.json`
- `step1_x_cdp_raw_20261104T234955Z_b47ce2f1edb1a8a7.json`

