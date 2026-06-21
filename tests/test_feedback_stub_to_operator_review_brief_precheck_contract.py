"""Unit tests for Feedback Stub to Operator Review Brief Precheck contract (0175BC)."""
from __future__ import annotations

import json
from pathlib import Path
import pytest
import subprocess

from live_contentops.feedback_stub_to_operator_review_brief_precheck_contract import (
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


def test_2_consumes_0175bb_precedent():
    """2. Verify that the contract successfully consumes 0175BB precedent."""
    p = build_contract_packet()
    assert "precheck_records" in p
    assert len(p["precheck_records"]) == 10


def test_3_all_supported_platform_operator_review_brief_prechecks_exist():
    """3. Verify all supported platform operator review brief prechecks exist."""
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


def test_4_every_operator_review_brief_precheck_status_is_operator_review_brief_precheck_blocked():
    """4. Verify every status is operator_review_brief_precheck_blocked."""
    p = build_contract_packet()
    for r in p["precheck_records"]:
        assert r["operator_review_brief_precheck_status"] == "operator_review_brief_precheck_blocked"


def test_5_to_20_brief_reference_assertions():
    """Verify brief references configurations and assertions."""
    p = build_contract_packet()

    expected_fields_by_target = {
        "x": ["hook_review_stub", "clarity_review_stub", "citation_review_stub", "limitation_review_stub", "operator_decision_stub"],
        "telegram_channel_destination": ["message_review_stub", "operator_context_review_stub", "citation_review_stub", "limitation_review_stub", "operator_decision_stub"],
        "telegram_remote_operator": ["operator_log_review_stub", "audit_review_stub", "manual_action_review_stub", "operator_decision_stub"],
        "substack": ["title_review_stub", "thesis_review_stub", "structure_review_stub", "citation_review_stub", "limitation_review_stub", "operator_decision_stub"],
        "linkedin": ["professional_framing_review_stub", "body_review_stub", "citation_review_stub", "limitation_review_stub", "operator_decision_stub"],
        "threads": ["short_text_review_stub", "clarity_review_stub", "citation_review_stub", "limitation_review_stub", "operator_decision_stub"],
        "instagram": ["caption_review_stub", "media_context_review_stub", "alt_text_review_stub", "citation_review_stub", "limitation_review_stub", "operator_decision_stub"],
        "facebook_page": ["post_text_review_stub", "attachment_context_review_stub", "citation_review_stub", "limitation_review_stub", "operator_decision_stub"],
        "tiktok": ["caption_review_stub", "video_context_review_stub", "disclosure_review_stub", "citation_review_stub", "operator_decision_stub"],
        "youtube": ["title_review_stub", "description_review_stub", "video_context_review_stub", "citation_review_stub", "limitation_review_stub", "operator_decision_stub"]
    }

    for r in p["precheck_records"]:
        tid = r["platform_target_id"]
        refs = r["brief_references"]

        # 5. every required brief reference exists by target
        ref_names = [f["reference_name"] for f in refs]
        assert ref_names == expected_fields_by_target[tid]

        for f in refs:
            # 6. every brief reference placeholder_only true
            assert f["placeholder_only"] is True
            # 7. every brief reference operator_review_brief_generated false
            assert f["operator_review_brief_generated"] is False
            # 8. every brief reference operator_decision_generated false
            assert f["operator_decision_generated"] is False
            # 9. every brief reference feedback_generated false
            assert f["feedback_generated"] is False
            # 10. every brief reference editorial_advice_generated false
            assert f["editorial_advice_generated"] is False
            # 11. every brief reference rewrite_suggestion_generated false
            assert f["rewrite_suggestion_generated"] is False
            # 12. every brief reference recommendation_generated false
            assert f["recommendation_generated"] is False
            # 13. every brief reference optimization_suggestion_generated false
            assert f["optimization_suggestion_generated"] is False
            # 14. every brief reference platform_strategy_generated false
            assert f["platform_strategy_generated"] is False
            # 15. every brief reference content_score_computed false
            assert f["content_score_computed"] is False
            # 16. every brief reference ranking_generated false
            assert f["ranking_generated"] is False
            # 17. every brief reference best_or_worst_claim_generated false
            assert f["best_or_worst_claim_generated"] is False
            # 18. every brief reference performance_claim_generated false
            assert f["performance_claim_generated"] is False
            # 19. every brief reference publishable_copy_created false
            assert f["publishable_copy_created"] is False
            # 20. every brief reference requires_human_operator_review true
            assert f["requires_human_operator_review"] is True


def test_21_every_invariant_exists():
    """21. Verify every invariant exists."""
    p = build_contract_packet()
    expected_invariants = {
        "no_operator_review_brief_generated",
        "no_operator_decision_generated",
        "no_content_feedback_generated",
        "no_editorial_advice_generated",
        "no_rewrite_suggestion_generated",
        "no_recommendation_generated",
        "no_optimization_suggestion_generated",
        "no_platform_strategy_generated",
        "no_content_score_computed",
        "no_ranking_generated",
        "no_best_or_worst_claim_generated",
        "no_performance_claim_generated",
        "no_publishable_copy_created",
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
        "no_public_postable",
        "no_financial_advice",
        "no_signal_language",
        "no_market_number_fabrication",
        "preserve_citation_requirements",
        "preserve_limitations",
        "preserve_dqr_readiness_blocks",
        "require_operator_signature",
        "require_payload_hash_lock",
        "require_content_feedback_gate",
        "require_operator_review_brief_gate"
    }
    for r in p["precheck_records"]:
        inv_ids = {inv["invariant_id"] for inv in r["invariants"]}
        assert inv_ids == expected_invariants


def test_22_every_invariant_passed_true_for_blocked_state_preservation():
    """22. Verify every invariant passed true for blocked-state preservation."""
    p = build_contract_packet()
    for r in p["precheck_records"]:
        for inv in r["invariants"]:
            assert inv["passed"] is True


def test_23_to_35_brief_feedback_and_scoring_flags_false():
    """Verify all generator and scoring flags remain false."""
    p = build_contract_packet()
    # 23-35: verified on safety_flags for packet-level (when present) or precheck records (all cases)
    assert p["safety_flags"]["operator_review_brief_generated"] is False
    assert p["safety_flags"]["operator_decision_generated"] is False
    assert p["safety_flags"]["feedback_generated"] is False
    assert p["safety_flags"]["rewrite_suggestion_generated"] is False
    assert p["safety_flags"]["editorial_advice_generated"] is False
    assert p["safety_flags"]["recommendation_generated"] is False
    assert p["safety_flags"]["optimization_suggestion_generated"] is False
    assert p["safety_flags"]["platform_strategy_generated"] is False
    assert p["safety_flags"]["content_score_computed"] is False
    assert p["safety_flags"]["ranking_generated"] is False
    assert p["safety_flags"]["best_or_worst_claim_generated"] is False
    assert p["safety_flags"]["performance_claim_generated"] is False
    assert p["safety_flags"]["publishable_copy_created"] is False

    for r in p["precheck_records"]:
        assert r["operator_review_brief_generated"] is False
        assert r["operator_decision_generated"] is False
        assert r["feedback_generated"] is False
        assert r["rewrite_suggestion_generated"] is False
        assert r["editorial_advice_generated"] is False
        assert r["recommendation_generated"] is False
        assert r["optimization_suggestion_generated"] is False
        assert r["platform_strategy_generated"] is False
        assert r["content_score_computed"] is False
        assert r["ranking_generated"] is False
        assert r["best_or_worst_claim_generated"] is False
        assert r["performance_claim_generated"] is False
        assert r["publishable_copy_created"] is False


def test_36_to_41_metrics_and_analytics_flags_false():
    """Verify metrics and analytics flags remain false."""
    p = build_contract_packet()
    # 36. real_metrics_recorded false
    assert p["safety_flags"]["real_metrics_recorded"] is False
    # 37. metric_values_recorded false
    assert p["safety_flags"]["metric_values_recorded"] is False
    # 38. metric_score_computed false
    assert p["safety_flags"]["metric_score_computed"] is False
    # 39. kpi_comparison_computed false
    assert p["safety_flags"]["kpi_comparison_computed"] is False
    # 40. platform_analytics_pull_performed false
    assert p["safety_flags"]["platform_analytics_pull_performed"] is False
    # 41. public_metrics_recorded false
    assert p["safety_flags"]["public_metrics_recorded"] is False

    for r in p["precheck_records"]:
        assert r["real_metrics_recorded"] is False
        assert r["metric_values_recorded"] is False
        assert r["metric_score_computed"] is False
        assert r["kpi_comparison_computed"] is False
        assert r["platform_analytics_pull_performed"] is False
        assert r["public_metrics_recorded"] is False


def test_42_publishable_payload_created_false():
    """42. Verify publishable_payload_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["publishable_payload_created"] is False
    for r in p["precheck_records"]:
        assert r["publishable_payload_created"] is False


def test_43_platform_payload_created_false():
    """43. Verify platform_payload_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["platform_payload_created"] is False
    for r in p["precheck_records"]:
        assert r["platform_payload_created"] is False


def test_44_public_postable_false():
    """44. Verify public_postable false."""
    p = build_contract_packet()
    assert p["safety_flags"]["public_postable"] is False
    for r in p["precheck_records"]:
        assert r["public_postable"] is False


def test_45_publishable_text_false():
    """45. Verify publishable_text false."""
    p = build_contract_packet()
    for r in p["precheck_records"]:
        assert r["publishable_text"] is False


def test_46_platform_ready_false():
    """46. Verify platform_ready false."""
    p = build_contract_packet()
    for r in p["precheck_records"]:
        assert r["platform_ready"] is False


def test_47_dispatch_ready_false():
    """47. Verify dispatch_ready false."""
    p = build_contract_packet()
    assert p["safety_flags"]["dispatch_ready"] is False
    for r in p["precheck_records"]:
        assert r["dispatch_ready"] is False


def test_48_approval_granted_false():
    """48. Verify approval_granted false."""
    p = build_contract_packet()
    assert p["safety_flags"]["approval_granted"] is False
    for r in p["precheck_records"]:
        assert r["approval_granted"] is False


def test_49_operator_identity_not_bound():
    """49. Verify operator identity not bound."""
    p = build_contract_packet()
    assert p["safety_flags"]["operator_identity_bound"] is False
    for r in p["precheck_records"]:
        assert r["operator_identity_bound"] is False
        assert r["operator_identity_status"] == "identity_required_but_unbound"


def test_50_operator_signature_absent():
    """50. Verify operator signature absent."""
    p = build_contract_packet()
    assert p["safety_flags"]["operator_signature_present"] is False
    for r in p["precheck_records"]:
        assert r["operator_signature_present"] is False
        assert r["operator_signature_status"] == "signature_required_but_missing"


def test_51_payload_hash_not_locked():
    """51. Verify payload hash not locked."""
    p = build_contract_packet()
    assert p["safety_flags"]["payload_hash_locked"] is False
    for r in p["precheck_records"]:
        assert r["payload_hash_locked"] is False
        assert r["payload_hash_lock_status"] == "hash_lock_required_but_pending"


def test_52_account_binding_and_credential_gates_required_but_inactive():
    """52. Verify account binding and credential gates required but inactive."""
    p = build_contract_packet()
    assert p["safety_flags"]["account_binding_active"] is False
    assert p["safety_flags"]["credential_values_loaded"] is False
    for r in p["precheck_records"]:
        assert r["account_binding_active"] is False
        assert r["credential_values_loaded"] is False
        assert r["account_binding_status"] == "binding_required_but_inactive"
        assert r["credential_gate_status"] == "credential_required_but_locked"


def test_53_citation_and_limitation_statuses_preserved():
    """53. Verify citation and limitation statuses preserved."""
    p = build_contract_packet()
    for r in p["precheck_records"]:
        assert r["citation_status"] == "citation_rendering_required_but_pending"
        assert r["limitation_status"] == "limitation_rendering_required_but_pending"


def test_54_dqr_readiness_current_truth_not_cleared():
    """54. Verify DQR/readiness/current truth not cleared."""
    p = build_contract_packet()
    assert p["safety_flags"]["dqr_cleared_by_contentops"] is False
    assert p["safety_flags"]["readiness_cleared_by_contentops"] is False
    assert p["safety_flags"]["current_truth_promoted"] is False


def test_55_no_financial_advice_signal_execution_language():
    """55. Verify no financial advice/signal/execution language."""
    p = build_contract_packet()
    assert p["safety_flags"]["financial_advice"] is False
    assert p["safety_flags"]["signal_language"] is False
    assert p["safety_flags"]["broker_order_execution"] is False


def test_56_no_fake_market_numbers():
    """56. Verify no fake market numbers."""
    p = build_contract_packet()
    assert p["safety_flags"]["financial_advice"] is False
    assert p["safety_flags"]["broker_order_execution"] is False

    out_dir = Path("docs/automation/0175BC")
    runbook_path = out_dir / "feedback_stub_to_operator_review_brief_precheck_contract.md"
    assert runbook_path.exists()
    content = runbook_path.read_text(encoding="utf-8")
    assert "fake" not in content.lower()


def test_57_no_env_network_credential_platform_provider_api_imports_or_calls():
    """57. Scan code to ensure no environment, network, or credential API modules are imported."""
    with open("live_contentops/feedback_stub_to_operator_review_brief_precheck_contract.py", encoding="utf-8") as f:
        content = f.read()
    forbidden = ["import os", "from os", "import requests", "urllib", "dotenv", "socket"]
    for pattern in forbidden:
        assert pattern not in content, f"Forbidden import or keyword '{pattern}' found."


def test_58_no_ingestion_repo_mutation_or_path_access():
    """58. Verify no ingestion repo mutation or path access is allowed."""
    p = build_contract_packet()
    assert p["safety_flags"]["ingestion_repo_mutated"] is False


def test_59_no_scraping_screenshots_or_platform_analytics_pull():
    """59. Verify no scraping, screenshots, or platform analytics pull."""
    p = build_contract_packet()
    assert p["safety_flags"]["scraping"] is False
    assert "scraping" in p["blocked_capabilities"]
    assert "live_metrics_retrieval" in p["blocked_capabilities"]


def test_60_no_operator_review_brief_operator_decision_score_kpi_recommendation_ranking_best_worst_performance_claim_content_feedback_editorial_advice_rewrite_suggestion_platform_strategy():
    """60. Verify no operator brief/decision/score/KPI/recommendation/ranking/best-worst/performance claim/content feedback/editorial advice/rewrite suggestion/platform strategy."""
    p = build_contract_packet()
    assert p["safety_flags"]["operator_review_brief_generated"] is False
    assert p["safety_flags"]["operator_decision_generated"] is False
    assert p["safety_flags"]["metric_score_computed"] is False
    assert p["safety_flags"]["kpi_comparison_computed"] is False
    assert p["safety_flags"]["performance_claim_generated"] is False
    assert p["safety_flags"]["recommendation_generated"] is False
    assert p["safety_flags"]["ranking_generated"] is False
    assert p["safety_flags"]["best_or_worst_claim_generated"] is False
    assert p["safety_flags"]["feedback_generated"] is False
    assert p["safety_flags"]["editorial_advice_generated"] is False
    assert p["safety_flags"]["rewrite_suggestion_generated"] is False
    assert p["safety_flags"]["platform_strategy_generated"] is False
    assert "performance_scoring" in p["blocked_capabilities"]


def test_61_ledger_family_registered():
    """61. Verify ledger family feedback_stub_to_operator_review_brief_precheck_future is registered."""
    assert LEDGER_FAMILY in ENTRY_FAMILIES


def test_62_artifacts_written_only_under_docs_automation_0175bc():
    """62. Verify that write_artifacts fails with ValueError outside docs/automation/0175BC."""
    with pytest.raises(ValueError, match="artifact_writer_refuses_paths_outside_docs_automation_0175BC"):
        write_artifacts(repo_root=".", output_dir="docs/automation/other")


def test_63_progress_ledger_resolves_0175bb_and_appends_0175bc():
    """63. Verify progress ledger resolves 0175BB final HEAD and appends 0175BC."""
    path = Path("docs/CONTENTOPS_PROGRESS_LEDGER_AND_FINAL_PRODUCT_CHECKLIST.md")
    assert path.exists()
    content = path.read_text(encoding="utf-8")

    # One-task-lag checks
    assert "| `TASK_CONTENTOPS_0175BB_CONTENT_FEEDBACK_PRECHECK_TO_FEEDBACK_STUB_V0` | `1e278a83bb2cf95464edc80dbfe819adf6ba6107` | `a3bc9ed1d6636796e3a8d1866c37492ef0207141` |" in content
    assert "| `TASK_CONTENTOPS_0175BC_FEEDBACK_STUB_TO_OPERATOR_REVIEW_BRIEF_PRECHECK_V0` | `a3bc9ed1d6636796e3a8d1866c37492ef0207141` | `RECORDED_IN_NEXT_TASK_READBACK` |" in content


def test_64_no_pycache_or_pyc_staged():
    """64. Ensure no pycache or .pyc files are staged/tracked in git."""
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
