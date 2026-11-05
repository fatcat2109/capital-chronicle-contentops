# CC-268: remaining old failures, each with a named owner

- Final full run on a clean checkout (backlog/cc-268-suite-hygiene at b16979c8, rebased on live bd73f4ae; 4 Nov 23:38Z to 5 Nov 00:51Z; pytest basetemp and scratch on C:): 10,198 tests, 131 failed, 9 errors. `git status` was empty afterwards.
- Clean baseline for comparison (live head 95c9e3c3, 4 Nov 21:04Z): 10,807 tests, 515 failed, 170 errors.
- Every failing id of the final run was re-run at ca39e453 (rebased on live bda0d915, with the commits after b16979c8): 37 no longer exist (removed and listed in removed-tests.md), 5 pass, 4 skip with a named reason, and 94 still fail. All 94 are listed below with an owner.
- None of the 94 is new: each failed on the clean baseline too, so none comes from CC-267, CC-248, CC-283 or CC-268.
- A file-write probe ran through both runs: no test wrote outside its temp folder after the Run Now fix (before it, six operator-trigger tests wrote nine raw X captures into the live headline root).

## Text-first and editorial-mode changes since 2 Nov (BACKLOG CC-288)

Owner: **Codex Publisher**. Align fixtures with text-first (a7bba1fd) and the current story kinds, or name a defect.

| Test file | Failing | First error |
|---|---|---|
| `tests/test_generic_evidence_freshness_visual_editorial_fabric_v2.py` | 8 | AssertionError: assert 'story_type_a..._mode_profile' == 'caller' |
| `tests/test_growth_first_editorial_wake_canonical_first_v1.py` | 4 | assert 0 == 1 |
| `tests/test_native_manual_candidate_v1.py` | 34 | AssertionError: assert 'write' == 'media-plan' |
| `tests/test_native_photoless_briefs_v1.py` | 1 | Failed: DID NOT RAISE <class 'ValueError'> |
| `tests/test_native_pre_writer_outcomes_v1.py` | 1 | ValueError: ANALYSIS_OFFICIAL_HISTORY_CHARTS_REQUIRED |
| `tests/test_nonnumeric_story_authority_consumer_v1.py` | 1 | ValueError: canonical_editorial_capability_unresolved:unsupported_story_type |

## Publication lifecycle and recovery behaviour (BACKLOG CC-288)

Owner: **Codex Publisher**. Each is a changed expectation or a defect; decide per test (CC-179 and CC-247 changed readback and recovery).

| Test file | Failing | First error |
|---|---|---|
| `tests/test_core_v0_acceptance_harness_v1.py` | 1 | assert 9 == 4 |
| `tests/test_core_v0_repeated_shadow_soak_and_recovery_v1.py` | 1 | assert 9 == 4 |
| `tests/test_daily_app_publication_lifecycle_v1.py` | 19 | assert False is True |
| `tests/test_dated_distribution_recovery_v1.py` | 2 | AssertionError: assert 'DERIVATIVE_E...TALE_NO_WRITE' == 'CORRECTION_B...IVATIVE_STALE' |
| `tests/test_evidence_gate_calibration_v1.py` | 3 | AssertionError: assert 'NO_PUBLICATION' == 'SUCCESS' |
| `tests/test_executable_snapshot_requirement_separation_v1.py` | 1 | assert False is True |
| `tests/test_native_configured_provenance_v1.py` | 1 | Failed: DID NOT RAISE <class 'ValueError'> |
| `tests/test_native_live_source_recovery_v1.py` | 1 | KeyError: 'stage' |
| `tests/test_native_newsroom_publication_recovery_v1.py` | 5 | ValueError: EXACT_FAILED_SOURCE_ATTEMPTS_REQUIRED |
| `tests/test_public_object_identity_persistence_v1.py` | 7 | assert False is True |
| `tests/test_story_scoped_permission_and_operator_ready_package_v1.py` | 1 | assert False is True |
| `tests/test_v1_throughput_architecture_v1.py` | 1 | KeyError: 'company_investor_relations_release_feed_v1' |

## Native desk manual resume (new; not yet in CC-288)

Owner: **Codex Publisher**. `scripts/run_native_desktop_editorial.py:470` reads `frozen_input["rolling_input"]`; the test's frozen input predates that key. Update the fixture, or use `.get` if a frozen input may lack it.

| Test file | Failing | First error |
|---|---|---|
| `tests/test_native_desktop_workspace_v1.py` | 2 | KeyError: 'rolling_input' |

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

