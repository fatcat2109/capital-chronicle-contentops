"""Unit tests for Performance Summary Stub to Content Feedback Precheck contract (0175BA)."""
from __future__ import annotations

import json
from pathlib import Path
import pytest
import subprocess

from live_contentops.performance_summary_stub_to_content_feedback_precheck_contract import (
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


def test_2_consumes_0175az_precedent():
    """2. Verify that the contract successfully consumes 0175AZ precedent."""
    p = build_contract_packet()
    assert "precheck_records" in p
    assert len(p["precheck_records"]) == 10


def test_3_all_supported_platform_content_feedback_prechecks_exist():
    """3. Verify all supported platform content feedback prechecks exist."""
    p = build_contract_packet()
    records = p["precheck_records"]
    assert len(records) == 10
    target_ids = {r["platform_target_id"] for r in records}
    expected_ids = {
        "x", "telegram_channel_destination", "telegram_remote_operator",
        "substack", "linkedin", "threads", "instagram",
        "facebook_page", "tiktok", "youtube"
    }
    assert target_ids == expected_ids


def test_4_every_content_feedback_precheck_status_is_content_feedback_precheck_blocked():
    """4. Verify every content feedback precheck status is content_feedback_precheck_blocked."""
    p = build_contract_packet()
    for r in p["precheck_records"]:
        assert r["content_feedback_precheck_status"] == "content_feedback_precheck_blocked"


def test_5_to_16_feedback_reference_assertions():
    """Verify feedback references configurations and assertions."""
    p = build_contract_packet()

    expected_fields_by_target = {
        "x": ["hook_feedback_stub", "clarity_feedback_stub", "citation_feedback_stub", "limitation_feedback_stub"],
        "telegram_channel_destination": ["message_feedback_stub", "operator_context_feedback_stub", "citation_feedback_stub", "limitation_feedback_stub"],
        "telegram_remote_operator": ["operator_log_feedback_stub", "audit_feedback_stub", "manual_action_feedback_stub"],
        "substack": ["title_feedback_stub", "thesis_feedback_stub", "structure_feedback_stub", "citation_feedback_stub", "limitation_feedback_stub"],
        "linkedin": ["professional_framing_feedback_stub", "body_feedback_stub", "citation_feedback_stub", "limitation_feedback_stub"],
        "threads": ["short_text_feedback_stub", "clarity_feedback_stub", "citation_feedback_stub", "limitation_feedback_stub"],
        "instagram": ["caption_feedback_stub", "media_context_feedback_stub", "alt_text_feedback_stub", "citation_feedback_stub", "limitation_feedback_stub"],
        "facebook_page": ["post_text_feedback_stub", "attachment_context_feedback_stub", "citation_feedback_stub", "limitation_feedback_stub"],
        "tiktok": ["caption_feedback_stub", "video_context_feedback_stub", "disclosure_feedback_stub", "citation_feedback_stub"],
        "youtube": ["title_feedback_stub", "description_feedback_stub", "video_context_feedback_stub", "citation_feedback_stub", "limitation_feedback_stub"]
    }

    for r in p["precheck_records"]:
        tid = r["platform_target_id"]
        refs = r["feedback_references"]

        # 5. every required feedback reference exists by target
        ref_names = [f["reference_name"] for f in refs]
        assert ref_names == expected_fields_by_target[tid]

        for f in refs:
            # 6. every feedback reference placeholder_only true
            assert f["placeholder_only"] is True
            # 7. every feedback reference feedback_generated false
            assert f["feedback_generated"] is False
            # 8. every feedback reference rewrite_suggestion_generated false
            assert f["rewrite_suggestion_generated"] is False
            # 9. every feedback reference recommendation_generated false
            assert f["recommendation_generated"] is False
            # 10. every feedback reference optimization_suggestion_generated false
            assert f["optimization_suggestion_generated"] is False
            # 11. every feedback reference platform_strategy_generated false
            assert f["platform_strategy_generated"] is False
            # 12. every feedback reference content_score_computed false
            assert f["content_score_computed"] is False
            # 13. every feedback reference ranking_generated false
            assert f["ranking_generated"] is False
            # 14. every feedback reference best_or_worst_claim_generated false
            assert f["best_or_worst_claim_generated"] is False
            # 15. every feedback reference performance_claim_generated false
            assert f["performance_claim_generated"] is False
            # 16. every feedback reference requires_human_editorial_review true
            assert f["requires_human_editorial_review"] is True


def test_17_every_invariant_exists():
    """17. Verify every invariant exists."""
    p = build_contract_packet()
    expected_invariants = {
        "no_content_feedback_generated",
        "no_rewrite_suggestion_generated",
        "no_recommendation_generated",
        "no_optimization_suggestion_generated",
        "no_platform_strategy_generated",
        "no_content_score_computed",
        "no_ranking_generated",
        "no_best_or_worst_claim_generated",
        "no_performance_claim_generated",
        "no_real_metrics_recorded",
        "no_metric_values_recorded",
        "no_metric_score_computed",
        "no_kpi_comparison_computed",
        "no_platform_analytics_pull",
        "no_scraping",
        "no_provider_api_call",
        "no_platform_api_call",
        "no_credential_or_env_read",
        "no_account_binding_active",
        "no_scheduler",
        "no_autonomous_posting",
        "no_autonomous_reply_or_dm",
        "no_publishable_payload_created",
        "no_platform_payload_created",
        "no_publishable_copy_created",
        "no_public_postable",
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
        "require_content_feedback_gate"
    }
    for r in p["precheck_records"]:
        inv_ids = {inv["invariant_id"] for inv in r["invariants"]}
        assert inv_ids == expected_invariants


def test_18_every_invariant_passed_true_for_blocked_state_preservation():
    """18. Verify every invariant passed true for blocked-state preservation."""
    p = build_contract_packet()
    for r in p["precheck_records"]:
        for inv in r["invariants"]:
            assert inv["passed"] is True


def test_19_to_27_feedback_and_scoring_flags_false():
    """Verify all feedback, rewrite, recommendation, strategy, score, and ranking flags remain false."""
    p = build_contract_packet()
    # 19-27: verified on safety_flags for packet-level (when present) or precheck records (all cases)
    assert p["safety_flags"]["recommendation_generated"] is False
    assert p["safety_flags"]["optimization_suggestion_generated"] is False
    assert p["safety_flags"]["platform_strategy_generated"] is False
    assert p["safety_flags"]["content_score_computed"] is False
    assert p["safety_flags"]["ranking_generated"] is False
    assert p["safety_flags"]["best_or_worst_claim_generated"] is False
    assert p["safety_flags"]["performance_claim_generated"] is False

    for r in p["precheck_records"]:
        assert r["feedback_generated"] is False
        assert r["rewrite_suggestion_generated"] is False
        assert r["recommendation_generated"] is False
        assert r["optimization_suggestion_generated"] is False
        assert r["platform_strategy_generated"] is False
        assert r["content_score_computed"] is False
        assert r["ranking_generated"] is False
        assert r["best_or_worst_claim_generated"] is False
        assert r["performance_claim_generated"] is False


def test_28_to_33_metrics_and_analytics_flags_false():
    """Verify metrics and analytics flags remain false."""
    p = build_contract_packet()
    # 28. real_metrics_recorded false
    assert p["safety_flags"]["real_metrics_recorded"] is False
    # 29. metric_values_recorded false
    assert p["safety_flags"]["metric_values_recorded"] is False
    # 30. metric_score_computed false
    assert p["safety_flags"]["metric_score_computed"] is False
    # 31. kpi_comparison_computed false
    assert p["safety_flags"]["kpi_comparison_computed"] is False
    # 32. platform_analytics_pull_performed false
    assert p["safety_flags"]["platform_analytics_pull_performed"] is False
    # 33. public_metrics_recorded false
    assert p["safety_flags"]["public_metrics_recorded"] is False

    for r in p["precheck_records"]:
        assert r["real_metrics_recorded"] is False
        assert r["metric_values_recorded"] is False
        assert r["metric_score_computed"] is False
        assert r["kpi_comparison_computed"] is False
        assert r["platform_analytics_pull_performed"] is False
        assert r["public_metrics_recorded"] is False


def test_34_publishable_payload_created_false():
    """34. Verify publishable_payload_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["publishable_payload_created"] is False
    for r in p["precheck_records"]:
        assert r["publishable_payload_created"] is False


def test_35_platform_payload_created_false():
    """35. Verify platform_payload_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["platform_payload_created"] is False
    for r in p["precheck_records"]:
        assert r["platform_payload_created"] is False


def test_36_publishable_copy_created_false():
    """36. Verify publishable_copy_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["publishable_copy_created"] is False
    for r in p["precheck_records"]:
        assert r["publishable_copy_created"] is False


def test_37_public_postable_false():
    """37. Verify public_postable false."""
    p = build_contract_packet()
    assert p["safety_flags"]["public_postable"] is False
    for r in p["precheck_records"]:
        assert r["public_postable"] is False


def test_38_publishable_text_false():
    """38. Verify publishable_text false."""
    p = build_contract_packet()
    for r in p["precheck_records"]:
        assert r["publishable_text"] is False


def test_39_platform_ready_false():
    """39. Verify platform_ready false."""
    p = build_contract_packet()
    for r in p["precheck_records"]:
        assert r["platform_ready"] is False


def test_40_dispatch_ready_false():
    """40. Verify dispatch_ready false."""
    p = build_contract_packet()
    assert p["safety_flags"]["dispatch_ready"] is False
    for r in p["precheck_records"]:
        assert r["dispatch_ready"] is False


def test_41_approval_granted_false():
    """41. Verify approval_granted false."""
    p = build_contract_packet()
    assert p["safety_flags"]["approval_granted"] is False
    for r in p["precheck_records"]:
        assert r["approval_granted"] is False


def test_42_operator_identity_not_bound():
    """42. Verify operator identity not bound."""
    p = build_contract_packet()
    assert p["safety_flags"]["operator_identity_bound"] is False
    for r in p["precheck_records"]:
        assert r["operator_identity_bound"] is False
        assert r["operator_identity_status"] == "identity_required_but_unbound"


def test_43_operator_signature_absent():
    """43. Verify operator signature absent."""
    p = build_contract_packet()
    assert p["safety_flags"]["operator_signature_present"] is False
    for r in p["precheck_records"]:
        assert r["operator_signature_present"] is False
        assert r["operator_signature_status"] == "signature_required_but_missing"


def test_44_payload_hash_not_locked():
    """44. Verify payload hash not locked."""
    p = build_contract_packet()
    assert p["safety_flags"]["payload_hash_locked"] is False
    for r in p["precheck_records"]:
        assert r["payload_hash_locked"] is False
        assert r["payload_hash_lock_status"] == "hash_lock_required_but_pending"


def test_45_account_binding_and_credential_gates_required_but_inactive():
    """45. Verify account binding and credential gates required but inactive."""
    p = build_contract_packet()
    assert p["safety_flags"]["account_binding_active"] is False
    assert p["safety_flags"]["credential_values_loaded"] is False
    for r in p["precheck_records"]:
        assert r["account_binding_active"] is False
        assert r["credential_values_loaded"] is False
        assert r["account_binding_status"] == "binding_required_but_inactive"
        assert r["credential_gate_status"] == "credential_required_but_locked"


def test_46_citation_and_limitation_statuses_preserved():
    """46. Verify citation and limitation statuses preserved."""
    p = build_contract_packet()
    for r in p["precheck_records"]:
        assert r["citation_status"] == "citation_rendering_required_but_pending"
        assert r["limitation_status"] == "limitation_rendering_required_but_pending"


def test_47_dqr_readiness_current_truth_not_cleared():
    """47. Verify DQR/readiness/current truth not cleared."""
    p = build_contract_packet()
    assert p["safety_flags"]["dqr_cleared_by_contentops"] is False
    assert p["safety_flags"]["readiness_cleared_by_contentops"] is False
    assert p["safety_flags"]["current_truth_promoted"] is False


def test_48_no_financial_advice_signal_execution_language():
    """48. Verify no financial advice/signal/execution language."""
    p = build_contract_packet()
    assert p["safety_flags"]["financial_advice"] is False
    assert p["safety_flags"]["signal_language"] is False
    assert p["safety_flags"]["broker_order_execution"] is False


def test_49_no_fake_market_numbers():
    """49. Verify no fake market numbers."""
    p = build_contract_packet()
    assert p["safety_flags"]["financial_advice"] is False
    assert p["safety_flags"]["broker_order_execution"] is False

    out_dir = Path("docs/automation/0175BA")
    runbook_path = out_dir / "performance_summary_stub_to_content_feedback_precheck_contract.md"
    assert runbook_path.exists()
    content = runbook_path.read_text(encoding="utf-8")
    assert "fake" not in content.lower()


def test_50_no_env_network_credential_platform_provider_api_imports_or_calls():
    """50. Scan code to ensure no environment, network, or credential API modules are imported."""
    with open("live_contentops/performance_summary_stub_to_content_feedback_precheck_contract.py", encoding="utf-8") as f:
        content = f.read()
    forbidden = ["import os", "from os", "import requests", "urllib", "dotenv", "socket"]
    for pattern in forbidden:
        assert pattern not in content, f"Forbidden import or keyword '{pattern}' found."


def test_51_no_ingestion_repo_mutation_or_path_access():
    """51. Verify no ingestion repo mutation or path access is allowed."""
    p = build_contract_packet()
    assert p["safety_flags"]["ingestion_repo_mutated"] is False


def test_52_no_scraping_screenshots_or_platform_analytics_pull():
    """52. Verify no scraping, screenshots, or platform analytics pull."""
    p = build_contract_packet()
    assert p["safety_flags"]["scraping"] is False
    assert "scraping" in p["blocked_capabilities"]
    assert "live_metrics_retrieval" in p["blocked_capabilities"]


def test_53_no_score_kpi_recommendation_ranking_best_worst_performance_claim_content_feedback():
    """53. Verify no score/KPI/recommendation/ranking/best-worst/performance claim/content feedback generated."""
    p = build_contract_packet()
    assert p["safety_flags"]["metric_score_computed"] is False
    assert p["safety_flags"]["kpi_comparison_computed"] is False
    assert p["safety_flags"]["performance_claim_generated"] is False
    assert p["safety_flags"]["recommendation_generated"] is False
    assert p["safety_flags"]["ranking_generated"] is False
    assert p["safety_flags"]["best_or_worst_claim_generated"] is False
    for r in p["precheck_records"]:
        assert r["feedback_generated"] is False
    assert "performance_scoring" in p["blocked_capabilities"]


def test_54_ledger_family_registered():
    """54. Verify ledger family performance_summary_stub_to_content_feedback_precheck_future is registered."""
    assert LEDGER_FAMILY in ENTRY_FAMILIES


def test_55_artifacts_written_only_under_docs_automation_0175ba():
    """55. Verify that write_artifacts fails with ValueError outside docs/automation/0175BA."""
    with pytest.raises(ValueError, match="artifact_writer_refuses_paths_outside_docs_automation_0175BA"):
        write_artifacts(repo_root=".", output_dir="docs/automation/other")


def test_56_progress_ledger_resolves_0175az_and_appends_0175ba():
    """56. Verify progress ledger resolves 0175AZ final HEAD and appends 0175BA."""
    path = Path("docs/CONTENTOPS_PROGRESS_LEDGER_AND_FINAL_PRODUCT_CHECKLIST.md")
    assert path.exists()
    content = path.read_text(encoding="utf-8")

    # One-task-lag checks
    assert "| `TASK_CONTENTOPS_0175AZ_PERFORMANCE_AUDIT_PRECHECK_TO_SUMMARY_STUB_V0` | `048b27c6dce2aef5fb38e0552b8208d4fd408d9f` | `888d6c34b31daa107056bb5a56ab0d5e7430e49b` |" in content
    assert "| `TASK_CONTENTOPS_0175BA_PERFORMANCE_SUMMARY_STUB_TO_CONTENT_FEEDBACK_PRECHECK_V0` | `888d6c34b31daa107056bb5a56ab0d5e7430e49b` | `RECORDED_IN_NEXT_TASK_READBACK` |" in content


def test_57_no_pycache_or_pyc_staged():
    """57. Ensure no pycache or .pyc files are staged/tracked in git."""
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
