# CC-268: remaining old failures, each with a named owner

From the run of the 52 triage files on backlog/cc-268-suite-hygiene (5 Nov 23:30Z), after the removals.
Every failure here also failed on the clean 5 Nov baseline (live head 95c9e3c3); none comes from CC-267, CC-248 or CC-283.

## Hash seal on frozen files or receipts (C3: no seals)

Owner: **Ops Product (decision)**. Recommend removal as seals (a frozen hash fails on every legitimate change); else re-pin by the module owner.

| Test file | Failing | First error |
|---|---|---|
| `tests/test_capability_policy_genericity_and_readiness_receipt_repair_v1.py` | 2 | AssertionError: assert {'git_blob_sh...stry_v2.json'} == {'git_blob_sh...stry_v2.json'} |
| `tests/test_decision_time_freshness_and_current_operator_readiness_v1.py` | 1 | AssertionError: assert '994ebd0063cc...3d5726d2c1bda' == 'df400013ccf7...259c2f522c814' |
| `tests/test_generic_foundation_freeze_and_production_adapter_conformance_v1.py` | 1 | AssertionError: assert not ('frozen_semantic_file_mutated:live_contentops/content_intelligence_contracts_v2.py |
| `tests/test_production_adapter_batch_treasury_cftc_h41_v1.py` | 1 | AssertionError: assert not ('frozen_semantic_file_mutated:live_contentops/content_intelligence_contracts_v2.py |
| `tests/test_production_adapter_wave2_official_committed_artifacts_v1.py` | 1 | AssertionError: assert not ('frozen_semantic_file_mutated:live_contentops/content_intelligence_contracts_v2.py |
| `tests/test_production_adapter_wave3_official_artifacts_and_contract_coverage_v1.py` | 1 | AssertionError: assert not ('frozen_semantic_file_mutated:live_contentops/content_intelligence_contracts_v2.py |
| `tests/test_temporal_authority_and_point_in_time_replay_integrity_v1.py` | 1 | AssertionError: assert '4ddef654ac8d...8e85e4d6e320b' == '5e6b783bcfdb...723150283cdf1' |
| `tests/test_verified_evidence_window_incremental_editorial_shadow_v1.py` | 10 | live_contentops.universal_evidence_receipt_verifier_v1.EvidenceReceiptVerificationError: implementation_runtim |
| `tests/test_wave01_master_authority_and_metadata_consistency_v1.py` | 3 | AssertionError: assert 'c4ad5299022a...33e98a67a23e8' == '5c90e6d243b7...3565f4899197b' |
| `tests/test_wave02_durable_store_authority_and_metadata_consistency_v1.py` | 3 | AssertionError: assert 'CONTINUE_FDA..._SOURCE_EPOCH' == 'REFRESH_GOVE...NONICAL_CYCLE' |

## Retired transport or route (Edge CDP to Neo, Gemini to native Codex)

Owner: **ContentOps V1 lane**. Update to the current registry and routing (Neo since 20 and 28 Oct; native Codex writer); remove what only tests the retired path.

| Test file | Failing | First error |
|---|---|---|
| `tests/test_destination_identity_pinning_v1.py` | 8 | AssertionError: assert ('BROWSEROS_NEO_MCP', None) == ('EDGE_CDP', 9223) |
| `tests/test_llm_cost_governor_v1.py` | 2 | assert 6 == 12 |
| `tests/test_operator_browser_lab_policy.py` | 2 | assert 9223 == 9222 |
| `tests/test_three_trigger_editorial_flow_v1.py` | 1 | AssertionError: assert 'NATIVE_CODEX_DESKTOP' == 'SIMPLE_GEMINI_RUNTIME' |

## Historical status or authority documents

Owner: **Ops Product (decision)**. Recommend removal: they pin the text of retired V6 status docs, not behaviour.

| Test file | Failing | First error |
|---|---|---|
| `tests/test_current_project_status_guardrail_v6.py` | 1 | AssertionError: assert '`ui/institutional_operator_cockpit_v4/`' in '# current project status\n\n`ui/contentop |
| `tests/test_final_environment_format_inventory.py` | 1 | AssertionError: assert ['TELEGRAM_BO...DING_ID', ...] == [] |
| `tests/test_final_product_readiness_metadata_consistency.py` | 1 | AssertionError: assert 'V1_PRESELECT...G_SOAK_ACTIVE' == 'PASS_VERIFIE...CHATGPT_AUDIT' |
| `tests/test_status_progress_docs_v6.py` | 2 | AssertionError: assert 'Product North Star' in '# Capital Chronicle ContentOps — Historical V6/Post-v1 Routing |
| `tests/test_v6_north_star_authority_consistency.py` | 4 | AssertionError: assert 'TASK_CONTENTOPS_V1_0_FINAL_AUCTION_LOGIC_REPAIR_ACCEPTANCE_AND_TAG_V1' in '# Capital C |

## Text-first and editorial-mode changes since 2 Nov

Owner: **Codex Publisher**. Native editorial owner: align fixtures with text-first (a7bba1fd) and current story kinds, or name a defect.

| Test file | Failing | First error |
|---|---|---|
| `tests/test_generic_evidence_freshness_visual_editorial_fabric_v2.py` | 8 | AssertionError: assert 'straight_news' == 'analysis' |
| `tests/test_growth_first_editorial_wake_canonical_first_v1.py` | 4 | AssertionError: assert 'BREAKING_BRIEF' == 'EVERGREEN_EXPLAINER' |
| `tests/test_native_manual_candidate_v1.py` | 34 | AssertionError: assert 'write' == 'media-plan' |
| `tests/test_native_photoless_briefs_v1.py` | 1 | Failed: DID NOT RAISE <class 'ValueError'> |
| `tests/test_native_pre_writer_outcomes_v1.py` | 1 | ValueError: ANALYSIS_OFFICIAL_HISTORY_CHARTS_REQUIRED |
| `tests/test_nonnumeric_story_authority_consumer_v1.py` | 1 | ValueError: canonical_editorial_capability_unresolved:unsupported_story_type |

## Publication lifecycle and recovery behaviour

Owner: **Codex Publisher**. Publication owner: each is a changed expectation or a defect; decide per test (CC-179 and CC-247 changed readback and recovery).

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
| `tests/test_native_newsroom_publication_recovery_v1.py` | 5 | AssertionError: assert 'DISTRIBUTION_INCOMPLETE' == 'RECONCILED' |
| `tests/test_public_object_identity_persistence_v1.py` | 7 | assert False is True |
| `tests/test_story_scoped_permission_and_operator_ready_package_v1.py` | 1 | assert False is True |
| `tests/test_v1_throughput_architecture_v1.py` | 1 | KeyError: 'company_investor_relations_release_feed_v1' |

## Environment-dependent (node, git, job object, live browser)

Owner: **ContentOps V1 lane**. Make hermetic (fake the subprocess or browser, or skip with a named reason when the tool is absent).

| Test file | Failing | First error |
|---|---|---|
| `tests/test_cockpit_ui_shell_contract.py` | 6 | FileNotFoundError: [Errno 2] No such file or directory: 'A:\\Capital Chronicle\\Worktrees\\contentops-cc268-su |
| `tests/test_contentops_daily_app_launcher_v1.py` | 1 | PermissionError: [WinError 5] Access is denied |
| `tests/test_contentops_ingestion_bootstrap_v1.py` | 1 | AssertionError: assert 'UNAVAILABLE' == 'READY' |
| `tests/test_native_desktop_workspace_v1.py` | 3 | subprocess.CalledProcessError: Command '['node', 'A:\\Capital Chronicle\\Worktrees\\contentops-cc268-suite-hyg |
| `tests/test_reader_first_data_journalism_v1.py` | 1 | AssertionError: node:internal/modules/cjs/loader:1451 |
| `tests/test_trusted_evidence_verifier_registry_and_real_multi_topic_canary_v1.py` | 3 | subprocess.CalledProcessError: Command '['git', '-C', 'A:\\Capital Chronicle\\Worktrees\\contentops-cc268-suit |
| `tests/test_v2_freeform_chapter_pipeline_v1.py` | 1 | video.freeform_chapter_pipeline_v1.pipeline.PipelineError: Required dependency is missing: A:\Capital Chronicl |

## Removed function

Owner: **ContentOps V1 lane**. live_contentops.server no longer has _run_id_from_stdout: remove those tests.

| Test file | Failing | First error |
|---|---|---|
| `tests/test_server.py` | 5 | AttributeError: module 'live_contentops.server' has no attribute '_run_id_from_stdout' |

