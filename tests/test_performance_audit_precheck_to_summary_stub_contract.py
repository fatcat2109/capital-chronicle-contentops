"""Unit tests for Performance Audit Precheck to Summary Stub contract (0175AZ)."""
from __future__ import annotations

import json
from pathlib import Path
import pytest
import subprocess

from live_contentops.performance_audit_precheck_to_summary_stub_contract import (
    build_contract_packet,
    write_artifacts,
    TASK_LABEL,
    MATRIX_VERSION,
    SOURCE_BASELINE_COMMIT,
    LEDGER_FAMILY
)
from live_contentops.redacted_immutable_audit_ledger_v2_contract import ENTRY_FAMILIES


def test_1_deterministic_packet_hash():
    """1. Verify that build_contract_packet creates deterministic hashes."""
    p1 = build_contract_packet()
    p2 = build_contract_packet()
    assert p1["packet_hash"] == p2["packet_hash"]
    assert p1["task_label"] == TASK_LABEL
    assert p1["matrix_version"] == MATRIX_VERSION
    assert p1["source_baseline_commit"] == SOURCE_BASELINE_COMMIT


def test_2_consumes_0175ay_precedent():
    """2. Verify that the contract successfully consumes 0175AY precedent."""
    p = build_contract_packet()
    assert "summary_records" in p
    assert len(p["summary_records"]) == 10


def test_3_all_supported_platform_performance_summary_stubs_exist():
    """3. Verify all supported platform performance summary stubs exist."""
    p = build_contract_packet()
    records = p["summary_records"]
    assert len(records) == 10
    target_ids = {r["platform_target_id"] for r in records}
    expected_ids = {
        "x", "telegram_channel_destination", "telegram_remote_operator",
        "substack", "linkedin", "threads", "instagram",
        "facebook_page", "tiktok", "youtube"
    }
    assert target_ids == expected_ids


def test_4_every_performance_summary_stub_status_is_performance_summary_stub_blocked():
    """4. Verify every performance summary stub status is performance_summary_stub_blocked."""
    p = build_contract_packet()
    for r in p["summary_records"]:
        assert r["performance_summary_stub_status"] == "performance_summary_stub_blocked"


def test_5_to_15_metric_reference_assertions():
    """Verify metric references configurations and assertions."""
    p = build_contract_packet()

    expected_fields_by_target = {
        "x": ["impressions_stub", "likes_stub", "replies_stub", "reposts_stub", "clicks_stub"],
        "telegram_channel_destination": ["views_stub", "reactions_stub", "forwards_stub", "replies_stub"],
        "telegram_remote_operator": ["operator_review_count_stub", "manual_action_count_stub", "audit_event_count_stub"],
        "substack": ["opens_stub", "clicks_stub", "likes_stub", "comments_stub", "subscriber_delta_stub"],
        "linkedin": ["impressions_stub", "reactions_stub", "comments_stub", "reposts_stub", "clicks_stub"],
        "threads": ["views_stub", "likes_stub", "replies_stub", "reposts_stub"],
        "instagram": ["views_stub", "likes_stub", "comments_stub", "shares_stub", "saves_stub"],
        "facebook_page": ["reach_stub", "reactions_stub", "comments_stub", "shares_stub", "clicks_stub"],
        "tiktok": ["views_stub", "likes_stub", "comments_stub", "shares_stub", "saves_stub"],
        "youtube": ["views_stub", "likes_stub", "comments_stub", "watch_time_stub", "subscriber_delta_stub"]
    }

    for r in p["summary_records"]:
        tid = r["platform_target_id"]
        refs = r["metric_references"]

        # 5. every required metric reference exists by target
        ref_names = [f["metric_name"] for f in refs]
        assert ref_names == expected_fields_by_target[tid]

        for f in refs:
            # 6. every metric reference placeholder_only true
            assert f["placeholder_only"] is True
            # 7. every metric reference real_metric_recorded false
            assert f["real_metric_recorded"] is False
            # 8. every metric reference metric_value_recorded false
            assert f["metric_value_recorded"] is False
            # 9. every metric reference metric_score_computed false
            assert f["metric_score_computed"] is False
            # 10. every metric reference kpi_comparison_computed false
            assert f["kpi_comparison_computed"] is False
            # 11. every metric reference performance_claim_generated false
            assert f["performance_claim_generated"] is False
            # 12. every metric reference recommendation_generated false
            assert f["recommendation_generated"] is False
            # 13. every metric reference rank_generated false
            assert f["rank_generated"] is False
            # 14. every metric reference best_or_worst_claim_generated false
            assert f["best_or_worst_claim_generated"] is False
            # 15. every metric reference requires_human_performance_review true
            assert f["requires_human_performance_review"] is True


def test_16_every_invariant_exists():
    """16. Verify every invariant exists."""
    p = build_contract_packet()
    expected_invariants = {
        "no_real_metrics_recorded",
        "no_metric_values_recorded",
        "no_platform_metric_id_recorded",
        "no_external_metric_timestamp_recorded",
        "no_public_metrics_recorded",
        "no_metric_score_computed",
        "no_kpi_comparison_computed",
        "no_performance_claim_generated",
        "no_recommendation_generated",
        "no_rank_generated",
        "no_best_or_worst_claim_generated",
        "no_platform_analytics_pull",
        "no_scraping",
        "no_manual_publish_record_created",
        "no_platform_publication_url_recorded",
        "no_platform_post_id_recorded",
        "no_export_file_created",
        "no_clipboard_payload_created",
        "no_download_artifact_created",
        "no_publishable_payload_created",
        "no_platform_payload_created",
        "no_platform_api_call",
        "no_provider_api_call",
        "no_credential_or_env_read",
        "no_account_binding_active",
        "no_scheduler",
        "no_autonomous_posting",
        "no_autonomous_reply_or_dm",
        "no_financial_advice",
        "no_signal_language",
        "no_market_number_fabrication",
        "preserve_citation_requirements",
        "preserve_limitations",
        "preserve_dqr_readiness_blocks",
        "require_operator_signature",
        "require_payload_hash_lock",
        "require_metrics_gate",
        "require_performance_audit_gate",
        "require_future_content_feedback_precheck"
    }
    for r in p["summary_records"]:
        inv_ids = {inv["invariant_id"] for inv in r["invariants"]}
        assert inv_ids == expected_invariants


def test_17_every_invariant_passed_true_for_blocked_state_preservation():
    """17. Verify every invariant passed true for blocked-state preservation."""
    p = build_contract_packet()
    for r in p["summary_records"]:
        for inv in r["invariants"]:
            assert inv["passed"] is True


def test_18_to_29_metrics_and_scoring_flags_false():
    """Verify all metrics, scores, and analytics properties remain false."""
    p = build_contract_packet()
    # 18. real_metrics_recorded false
    assert p["safety_flags"]["real_metrics_recorded"] is False
    # 19. metric_values_recorded false
    assert p["safety_flags"]["metric_values_recorded"] is False
    # 20. platform_metric_id_recorded false
    assert p["safety_flags"]["platform_metric_id_recorded"] is False
    # 21. external_metric_timestamp_recorded false
    assert p["safety_flags"]["external_metric_timestamp_recorded"] is False
    # 22. public_metrics_recorded false
    assert p["safety_flags"]["public_metrics_recorded"] is False
    # 23. metric_score_computed false
    assert p["safety_flags"]["metric_score_computed"] is False
    # 24. kpi_comparison_computed false
    assert p["safety_flags"]["kpi_comparison_computed"] is False
    # 25. performance_claim_generated false
    assert p["safety_flags"]["performance_claim_generated"] is False
    # 26. recommendation_generated false
    assert p["safety_flags"]["recommendation_generated"] is False
    # 27. rank_generated false
    assert p["safety_flags"]["rank_generated"] is False
    # 28. best_or_worst_claim_generated false
    assert p["safety_flags"]["best_or_worst_claim_generated"] is False
    # 29. platform_analytics_pull_performed false
    assert p["safety_flags"]["platform_analytics_pull_performed"] is False

    for r in p["summary_records"]:
        assert r["real_metrics_recorded"] is False
        assert r["metric_values_recorded"] is False
        assert r["platform_metric_id_recorded"] is False
        assert r["external_metric_timestamp_recorded"] is False
        assert r["public_metrics_recorded"] is False
        assert r["metric_score_computed"] is False
        assert r["kpi_comparison_computed"] is False
        assert r["performance_claim_generated"] is False
        assert r["recommendation_generated"] is False
        assert r["rank_generated"] is False
        assert r["best_or_worst_claim_generated"] is False
        assert r["platform_analytics_pull_performed"] is False


def test_30_manual_publish_record_created_false():
    """30. Verify manual_publish_record_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["manual_publish_record_created"] is False
    for r in p["summary_records"]:
        assert r["manual_publish_record_created"] is False


def test_31_platform_publication_url_recorded_false():
    """31. Verify platform_publication_url_recorded false."""
    p = build_contract_packet()
    assert p["safety_flags"]["platform_publication_url_recorded"] is False
    for r in p["summary_records"]:
        assert r["platform_publication_url_recorded"] is False


def test_32_platform_post_id_recorded_false():
    """32. Verify platform_post_id_recorded false."""
    p = build_contract_packet()
    assert p["safety_flags"]["platform_post_id_recorded"] is False
    for r in p["summary_records"]:
        assert r["platform_post_id_recorded"] is False


def test_33_external_publish_timestamp_recorded_false():
    """33. Verify external_publish_timestamp_recorded false."""
    p = build_contract_packet()
    assert p["safety_flags"]["external_publish_timestamp_recorded"] is False
    for r in p["summary_records"]:
        assert r["external_publish_timestamp_recorded"] is False


def test_34_export_ready_false():
    """34. Verify export_ready false."""
    p = build_contract_packet()
    assert p["safety_flags"]["export_ready"] is False
    for r in p["summary_records"]:
        assert r["export_ready"] is False


def test_35_manual_export_allowed_false():
    """35. Verify manual_export_allowed false."""
    p = build_contract_packet()
    assert p["safety_flags"]["manual_export_allowed"] is False
    for r in p["summary_records"]:
        assert r["manual_export_allowed"] is False


def test_36_export_file_created_false():
    """36. Verify export_file_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["export_file_created"] is False
    for r in p["summary_records"]:
        assert r["export_file_created"] is False


def test_37_clipboard_payload_created_false():
    """37. Verify clipboard_payload_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["clipboard_payload_created"] is False
    for r in p["summary_records"]:
        assert r["clipboard_payload_created"] is False


def test_38_download_artifact_created_false():
    """38. Verify download_artifact_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["download_artifact_created"] is False
    for r in p["summary_records"]:
        assert r["download_artifact_created"] is False


def test_39_publishable_payload_created_false():
    """39. Verify publishable_payload_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["publishable_payload_created"] is False
    for r in p["summary_records"]:
        assert r["publishable_payload_created"] is False


def test_40_platform_payload_created_false():
    """40. Verify platform_payload_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["platform_payload_created"] is False
    for r in p["summary_records"]:
        assert r["platform_payload_created"] is False


def test_41_public_postable_false():
    """41. Verify public_postable false."""
    p = build_contract_packet()
    assert p["safety_flags"]["public_postable"] is False
    for r in p["summary_records"]:
        assert r["public_postable"] is False


def test_42_publishable_text_false():
    """42. Verify publishable_text false."""
    p = build_contract_packet()
    for r in p["summary_records"]:
        assert r["publishable_text"] is False


def test_43_platform_ready_false():
    """43. Verify platform_ready false."""
    p = build_contract_packet()
    for r in p["summary_records"]:
        assert r["platform_ready"] is False


def test_44_dispatch_ready_false():
    """44. Verify dispatch_ready false."""
    p = build_contract_packet()
    assert p["safety_flags"]["dispatch_ready"] is False
    for r in p["summary_records"]:
        assert r["dispatch_ready"] is False


def test_45_approval_granted_false():
    """45. Verify approval_granted false."""
    p = build_contract_packet()
    assert p["safety_flags"]["approval_granted"] is False
    for r in p["summary_records"]:
        assert r["approval_granted"] is False


def test_46_operator_identity_not_bound():
    """46. Verify operator identity not bound."""
    p = build_contract_packet()
    for r in p["summary_records"]:
        assert r["operator_identity_bound"] is False
        assert r["operator_identity_status"] == "identity_required_but_unbound"


def test_47_operator_signature_absent():
    """47. Verify operator signature absent."""
    p = build_contract_packet()
    for r in p["summary_records"]:
        assert r["operator_signature_present"] is False
        assert r["operator_signature_status"] == "signature_required_but_missing"


def test_48_payload_hash_not_locked():
    """48. Verify payload hash not locked."""
    p = build_contract_packet()
    for r in p["summary_records"]:
        assert r["payload_hash_locked"] is False


def test_49_account_binding_and_credential_gates_required_but_inactive():
    """49. Verify account binding and credential gates required but inactive."""
    p = build_contract_packet()
    assert p["safety_flags"]["account_binding_active"] is False
    assert p["safety_flags"]["credential_values_loaded"] is False
    for r in p["summary_records"]:
        assert r["account_binding_active"] is False
        assert r["credential_values_loaded"] is False
        assert r["account_binding_status"] == "binding_required_but_inactive"
        assert r["credential_gate_status"] == "credential_required_but_locked"


def test_50_citation_and_limitation_statuses_preserved():
    """50. Verify citation and limitation statuses preserved."""
    p = build_contract_packet()
    for r in p["summary_records"]:
        assert r["citation_status"] == "citation_rendering_required_but_pending"
        assert r["limitation_status"] == "limitation_rendering_required_but_pending"


def test_51_dqr_readiness_current_truth_not_cleared():
    """51. Verify DQR/readiness/current truth not cleared."""
    p = build_contract_packet()
    assert p["safety_flags"]["dqr_cleared_by_contentops"] is False
    assert p["safety_flags"]["readiness_cleared_by_contentops"] is False
    assert p["safety_flags"]["current_truth_promoted"] is False


def test_52_no_financial_advice_signal_execution_language():
    """52. Verify no financial advice/signal/execution language."""
    p = build_contract_packet()
    assert p["safety_flags"]["financial_advice"] is False
    assert p["safety_flags"]["signal_language"] is False
    assert p["safety_flags"]["broker_order_execution"] is False


def test_53_no_fake_market_numbers():
    """53. Verify no fake market numbers."""
    p = build_contract_packet()
    assert p["safety_flags"]["financial_advice"] is False
    assert p["safety_flags"]["broker_order_execution"] is False

    out_dir = Path("docs/automation/0175AZ")
    runbook_path = out_dir / "performance_audit_precheck_to_summary_stub_contract.md"
    assert runbook_path.exists()
    content = runbook_path.read_text(encoding="utf-8")
    assert "fake" not in content.lower()


def test_54_no_env_network_credential_platform_provider_api_imports_or_calls():
    """54. Scan code to ensure no environment, network, or credential API modules are imported."""
    with open("live_contentops/performance_audit_precheck_to_summary_stub_contract.py", encoding="utf-8") as f:
        content = f.read()
    forbidden = ["import os", "from os", "import requests", "urllib", "dotenv", "socket"]
    for pattern in forbidden:
        assert pattern not in content, f"Forbidden import or keyword '{pattern}' found."


def test_55_no_ingestion_repo_mutation_or_path_access():
    """55. Verify no ingestion repo mutation or path access is allowed."""
    p = build_contract_packet()
    assert p["safety_flags"]["ingestion_repo_mutated"] is False


def test_56_no_scraping_screenshots_or_platform_analytics_pull():
    """56. Verify no scraping, screenshots, or platform analytics pull."""
    p = build_contract_packet()
    assert p["safety_flags"]["scraping"] is False
    assert "scraping" in p["blocked_capabilities"]
    assert "live_metrics_retrieval" in p["blocked_capabilities"]


def test_57_no_score_kpi_recommendation_ranking_best_worst_performance_claim_content_feedback():
    """57. Verify no score/KPI/recommendation/ranking/best-worst/performance claim/content feedback generated."""
    p = build_contract_packet()
    assert p["safety_flags"]["metric_score_computed"] is False
    assert p["safety_flags"]["kpi_comparison_computed"] is False
    assert p["safety_flags"]["performance_claim_generated"] is False
    assert p["safety_flags"]["recommendation_generated"] is False
    assert p["safety_flags"]["rank_generated"] is False
    assert p["safety_flags"]["best_or_worst_claim_generated"] is False
    assert "performance_scoring" in p["blocked_capabilities"]
    assert "performance_claims_reporting" in p["blocked_capabilities"]


def test_58_ledger_family_registered():
    """58. Verify ledger family performance_audit_precheck_to_summary_stub_future is registered."""
    assert LEDGER_FAMILY in ENTRY_FAMILIES


def test_59_artifacts_written_only_under_docs_automation_0175az():
    """59. Verify that write_artifacts fails with ValueError outside docs/automation/0175AZ."""
    with pytest.raises(ValueError, match="artifact_writer_refuses_paths_outside_docs_automation_0175AZ"):
        write_artifacts(repo_root=".", output_dir="docs/automation/other")


def test_60_progress_ledger_resolves_0175ay_and_appends_0175az():
    """60. Verify progress ledger resolves 0175AY final HEAD and appends 0175AZ."""
    path = Path("docs/CONTENTOPS_PROGRESS_LEDGER_AND_FINAL_PRODUCT_CHECKLIST.md")
    assert path.exists()
    content = path.read_text(encoding="utf-8")

    # One-task-lag checks
    assert "| `TASK_CONTENTOPS_0175AY_METRICS_RECORD_STUB_TO_PERFORMANCE_AUDIT_PRECHECK_V0` | `f3e0cb0e2774b8a9566e652ee61be947bf686a5e` | `048b27c6dce2aef5fb38e0552b8208d4fd408d9f` |" in content
    assert "| `TASK_CONTENTOPS_0175AZ_PERFORMANCE_AUDIT_PRECHECK_TO_SUMMARY_STUB_V0` | `048b27c6dce2aef5fb38e0552b8208d4fd408d9f` | `888d6c34b31daa107056bb5a56ab0d5e7430e49b` |" in content


def test_61_no_pycache_or_pyc_staged():
    """61. Ensure no pycache or .pyc files are staged/tracked in git."""
    res = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True
    )
    for line in res.stdout.splitlines():
        status_code = line[:2]
        path_str = line[3:]
        if "__pycache__" in path_str or path_str.endswith(".pyc"):
            if status_code[0] != " ":
                raise AssertionError(f"Staged pycache or .pyc file found: {line}")
