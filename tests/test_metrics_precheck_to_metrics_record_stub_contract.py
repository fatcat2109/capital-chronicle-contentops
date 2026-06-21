"""Unit tests for Metrics Precheck to Metrics Record Stub contract (0175AX)."""
from __future__ import annotations

import json
from pathlib import Path
import pytest
import subprocess

from live_contentops.metrics_precheck_to_metrics_record_stub_contract import (
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


def test_2_consumes_0175aw_precedent():
    """2. Verify that the contract successfully consumes 0175AW metrics precheck precedent."""
    p = build_contract_packet()
    assert "record_stubs" in p
    assert len(p["record_stubs"]) == 10


def test_3_all_supported_platform_metrics_record_stubs_exist():
    """3. Verify all supported platform metrics record stubs exist."""
    p = build_contract_packet()
    records = p["record_stubs"]
    assert len(records) == 10
    target_ids = {r["platform_target_id"] for r in records}
    expected_ids = {
        "x", "telegram_channel_destination", "telegram_remote_operator",
        "substack", "linkedin", "threads", "instagram",
        "facebook_page", "tiktok", "youtube"
    }
    assert target_ids == expected_ids


def test_4_every_metrics_record_stub_status_is_metrics_record_stub_blocked():
    """4. Verify every metrics record stub status is metrics_record_stub_blocked."""
    p = build_contract_packet()
    for r in p["record_stubs"]:
        assert r["metrics_record_stub_status"] == "metrics_record_stub_blocked"


def test_5_to_12_metric_field_assertions():
    """Verify metric fields configurations and assertions."""
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

    for r in p["record_stubs"]:
        tid = r["platform_target_id"]
        fields = r["metric_fields"]

        # 5. every required metric field exists by target
        field_names = [f["field_name"] for f in fields]
        assert field_names == expected_fields_by_target[tid]

        for f in fields:
            # 6. every metric field placeholder_only true
            assert f["placeholder_only"] is True
            # 7. every metric field recorded_value false
            assert f["recorded_value"] is False
            # 8. every metric field real_metric_recorded false
            assert f["real_metric_recorded"] is False
            # 9. every metric field metric_value_recorded false
            assert f["metric_value_recorded"] is False
            # 10. every metric field platform_metric_id_recorded false
            assert f["platform_metric_id_recorded"] is False
            # 11. every metric field external_metric_timestamp_recorded false
            assert f["external_metric_timestamp_recorded"] is False
            # 12. every metric field requires_human_metrics_logging true
            assert f["requires_human_metrics_logging"] is True

            # Obviously non-public placeholder test
            expected_val = f"[METRICS_RECORD_STUB_ONLY: {tid}.{f['field_name']}]"
            assert f["placeholder_value"] == expected_val


def test_13_every_invariant_exists():
    """13. Verify every invariant exists."""
    p = build_contract_packet()
    expected_invariants = {
        "no_real_metrics_recorded",
        "no_metric_values_recorded",
        "no_platform_metric_id_recorded",
        "no_external_metric_timestamp_recorded",
        "no_public_metrics_recorded",
        "no_manual_publish_record_created",
        "no_platform_publication_url_recorded",
        "no_platform_post_id_recorded",
        "no_export_file_created",
        "no_clipboard_payload_created",
        "no_download_artifact_created",
        "no_publishable_payload_created",
        "no_platform_payload_created",
        "no_platform_api_call",
        "no_credential_or_env_read",
        "no_account_binding_active",
        "no_scheduler",
        "no_autonomous_posting",
        "no_autonomous_reply_or_dm",
        "no_scraping",
        "no_financial_advice",
        "no_signal_language",
        "no_market_number_fabrication",
        "preserve_citation_requirements",
        "preserve_limitations",
        "preserve_dqr_readiness_blocks",
        "require_operator_signature",
        "require_payload_hash_lock",
        "require_manual_publish_record_gate",
        "require_metrics_gate",
        "require_future_performance_audit_precheck"
    }
    for r in p["record_stubs"]:
        inv_ids = {inv["invariant_id"] for inv in r["invariants"]}
        assert inv_ids == expected_invariants


def test_14_every_invariant_passed_true_for_blocked_state_preservation():
    """14. Verify every invariant passed true for blocked-state preservation."""
    p = build_contract_packet()
    for r in p["record_stubs"]:
        for inv in r["invariants"]:
            assert inv["passed"] is True


def test_15_to_19_metrics_flags_false():
    """Verify all metrics properties remain false."""
    p = build_contract_packet()
    # 15. real_metrics_recorded false
    assert p["safety_flags"]["real_metrics_recorded"] is False
    # 16. metric_values_recorded false
    assert p["safety_flags"]["metric_values_recorded"] is False
    # 17. platform_metric_id_recorded false
    assert p["safety_flags"]["platform_metric_id_recorded"] is False
    # 18. external_metric_timestamp_recorded false
    assert p["safety_flags"]["external_metric_timestamp_recorded"] is False
    # 19. public_metrics_recorded false
    assert p["safety_flags"]["public_metrics_recorded"] is False

    for r in p["record_stubs"]:
        assert r["real_metrics_recorded"] is False
        assert r["metric_values_recorded"] is False
        assert r["platform_metric_id_recorded"] is False
        assert r["external_metric_timestamp_recorded"] is False
        assert r["public_metrics_recorded"] is False


def test_20_manual_publish_record_created_false():
    """20. Verify manual_publish_record_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["manual_publish_record_created"] is False
    for r in p["record_stubs"]:
        assert r["manual_publish_record_created"] is False


def test_21_platform_publication_url_recorded_false():
    """21. Verify platform_publication_url_recorded false."""
    p = build_contract_packet()
    assert p["safety_flags"]["platform_publication_url_recorded"] is False
    for r in p["record_stubs"]:
        assert r["platform_publication_url_recorded"] is False


def test_22_platform_post_id_recorded_false():
    """22. Verify platform_post_id_recorded false."""
    p = build_contract_packet()
    assert p["safety_flags"]["platform_post_id_recorded"] is False
    for r in p["record_stubs"]:
        assert r["platform_post_id_recorded"] is False


def test_23_external_publish_timestamp_recorded_false():
    """23. Verify external_publish_timestamp_recorded false."""
    p = build_contract_packet()
    assert p["safety_flags"]["external_publish_timestamp_recorded"] is False
    for r in p["record_stubs"]:
        assert r["external_publish_timestamp_recorded"] is False


def test_24_export_ready_false():
    """24. Verify export_ready false."""
    p = build_contract_packet()
    assert p["safety_flags"]["export_ready"] is False
    for r in p["record_stubs"]:
        assert r["export_ready"] is False


def test_25_manual_export_allowed_false():
    """25. Verify manual_export_allowed false."""
    p = build_contract_packet()
    assert p["safety_flags"]["manual_export_allowed"] is False
    for r in p["record_stubs"]:
        assert r["manual_export_allowed"] is False


def test_26_export_file_created_false():
    """26. Verify export_file_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["export_file_created"] is False
    for r in p["record_stubs"]:
        assert r["export_file_created"] is False


def test_27_clipboard_payload_created_false():
    """27. Verify clipboard_payload_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["clipboard_payload_created"] is False
    for r in p["record_stubs"]:
        assert r["clipboard_payload_created"] is False


def test_28_download_artifact_created_false():
    """28. Verify download_artifact_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["download_artifact_created"] is False
    for r in p["record_stubs"]:
        assert r["download_artifact_created"] is False


def test_29_publishable_payload_created_false():
    """29. Verify publishable_payload_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["publishable_payload_created"] is False
    for r in p["record_stubs"]:
        assert r["publishable_payload_created"] is False


def test_30_platform_payload_created_false():
    """30. Verify platform_payload_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["platform_payload_created"] is False
    for r in p["record_stubs"]:
        assert r["platform_payload_created"] is False


def test_31_public_postable_false():
    """31. Verify public_postable false."""
    p = build_contract_packet()
    assert p["safety_flags"]["public_postable"] is False
    for r in p["record_stubs"]:
        assert r["public_postable"] is False


def test_32_publishable_text_false():
    """32. Verify publishable_text false."""
    p = build_contract_packet()
    for r in p["record_stubs"]:
        assert r["publishable_text"] is False


def test_33_platform_ready_false():
    """33. Verify platform_ready false."""
    p = build_contract_packet()
    for r in p["record_stubs"]:
        assert r["platform_ready"] is False


def test_34_dispatch_ready_false():
    """34. Verify dispatch_ready false."""
    p = build_contract_packet()
    assert p["safety_flags"]["dispatch_ready"] is False
    for r in p["record_stubs"]:
        assert r["dispatch_ready"] is False


def test_35_approval_granted_false():
    """35. Verify approval_granted false."""
    p = build_contract_packet()
    assert p["safety_flags"]["approval_granted"] is False
    for r in p["record_stubs"]:
        assert r["approval_granted"] is False


def test_36_operator_identity_not_bound():
    """36. Verify operator identity not bound."""
    p = build_contract_packet()
    for r in p["record_stubs"]:
        assert r["operator_identity_bound"] is False
        assert r["operator_identity_status"] == "identity_required_but_unbound"


def test_37_operator_signature_absent():
    """37. Verify operator signature absent."""
    p = build_contract_packet()
    for r in p["record_stubs"]:
        assert r["operator_signature_present"] is False
        assert r["operator_signature_status"] == "signature_required_but_missing"


def test_38_payload_hash_not_locked():
    """38. Verify payload hash not locked."""
    p = build_contract_packet()
    for r in p["record_stubs"]:
        assert r["payload_hash_locked"] is False


def test_39_account_binding_and_credential_gates_required_but_inactive():
    """39. Verify account binding and credential gates required but inactive."""
    p = build_contract_packet()
    assert p["safety_flags"]["account_binding_active"] is False
    assert p["safety_flags"]["credential_values_loaded"] is False
    for r in p["record_stubs"]:
        assert r["account_binding_active"] is False
        assert r["credential_values_loaded"] is False
        assert r["account_binding_status"] == "binding_required_but_inactive"
        assert r["credential_gate_status"] == "credential_required_but_locked"


def test_40_citation_and_limitation_statuses_preserved():
    """40. Verify citation and limitation statuses preserved."""
    p = build_contract_packet()
    for r in p["record_stubs"]:
        assert r["citation_status"] == "citation_rendering_required_but_pending"
        assert r["limitation_status"] == "limitation_rendering_required_but_pending"


def test_41_dqr_readiness_current_truth_not_cleared():
    """41. Verify DQR/readiness/current truth not cleared."""
    p = build_contract_packet()
    assert p["safety_flags"]["dqr_cleared_by_contentops"] is False
    assert p["safety_flags"]["readiness_cleared_by_contentops"] is False
    assert p["safety_flags"]["current_truth_promoted"] is False


def test_42_no_financial_advice_signal_execution_language():
    """42. Verify no financial advice/signal/execution language."""
    p = build_contract_packet()
    assert p["safety_flags"]["financial_advice"] is False
    assert p["safety_flags"]["signal_language"] is False
    assert p["safety_flags"]["broker_order_execution"] is False


def test_43_no_fake_market_numbers():
    """43. Verify no fake market numbers."""
    p = build_contract_packet()
    assert p["safety_flags"]["financial_advice"] is False
    assert p["safety_flags"]["broker_order_execution"] is False

    out_dir = Path("docs/automation/0175AX")
    runbook_path = out_dir / "metrics_precheck_to_metrics_record_stub_contract.md"
    assert runbook_path.exists()
    content = runbook_path.read_text(encoding="utf-8")
    assert "fake" not in content.lower()


def test_44_no_env_network_credential_platform_provider_api_imports_or_calls():
    """44. Scan code to ensure no environment, network, or credential API modules are imported."""
    with open("live_contentops/metrics_precheck_to_metrics_record_stub_contract.py", encoding="utf-8") as f:
        content = f.read()
    forbidden = ["import os", "from os", "import requests", "urllib", "dotenv", "socket"]
    for pattern in forbidden:
        assert pattern not in content, f"Forbidden import or keyword '{pattern}' found."


def test_45_no_ingestion_repo_mutation_or_path_access():
    """45. Verify no ingestion repo mutation or path access is allowed."""
    p = build_contract_packet()
    assert p["safety_flags"]["ingestion_repo_mutated"] is False


def test_46_no_scraping_or_platform_analytics_pull():
    """46. Verify no scraping or platform analytics pull."""
    p = build_contract_packet()
    assert p["safety_flags"]["scraping"] is False
    assert "scraping" in p["blocked_capabilities"]
    assert "live_metrics_retrieval" in p["blocked_capabilities"]


def test_47_ledger_family_registered():
    """47. Verify ledger family metrics_precheck_to_metrics_record_stub_future is registered."""
    assert LEDGER_FAMILY in ENTRY_FAMILIES


def test_48_artifacts_written_only_under_docs_automation_0175ax():
    """48. Verify that write_artifacts fails with ValueError outside docs/automation/0175AX."""
    with pytest.raises(ValueError, match="artifact_writer_refuses_paths_outside_docs_automation_0175AX"):
        write_artifacts(repo_root=".", output_dir="docs/automation/other")


def test_49_progress_ledger_resolves_0175aw_and_appends_0175ax():
    """49. Verify progress ledger resolves 0175AW final HEAD and appends 0175AX."""
    path = Path("docs/CONTENTOPS_PROGRESS_LEDGER_AND_FINAL_PRODUCT_CHECKLIST.md")
    assert path.exists()
    content = path.read_text(encoding="utf-8")

    # One-task-lag checks
    assert "| `TASK_CONTENTOPS_0175AW_MANUAL_PUBLISH_RECORD_STUB_TO_METRICS_PRECHECK_V0` | `1c8d66919f6e577b247f32b096b12f7eccd09bd6` | `c0d3e9944767f82b470b7e3f1bff0ba718c6e01d` |" in content
    assert "| `TASK_CONTENTOPS_0175AX_METRICS_PRECHECK_TO_METRICS_RECORD_STUB_V0` | `c0d3e9944767f82b470b7e3f1bff0ba718c6e01d` | `RECORDED_IN_NEXT_TASK_READBACK` |" in content


def test_50_no_pycache_or_pyc_staged():
    """50. Ensure no pycache or .pyc files are staged/tracked in git."""
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
