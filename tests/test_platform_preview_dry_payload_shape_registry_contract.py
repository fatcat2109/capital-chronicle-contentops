"""Unit tests for Platform Preview Dry Payload Shape Registry contract (0175AN)."""
from __future__ import annotations

import json
from pathlib import Path
import pytest
import subprocess

from live_contentops.platform_preview_dry_payload_shape_registry_contract import (
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


def test_2_consumes_0175am_precheck_precedent():
    """2. Verify that the contract successfully consumes/aligns with precheck targets."""
    p = build_contract_packet()
    assert "platform_shapes" in p
    assert len(p["platform_shapes"]) > 0


def test_3_all_supported_platform_targets_exist():
    """3. Verify all supported platform targets exist."""
    p = build_contract_packet()
    shapes = p["platform_shapes"]
    assert len(shapes) == 10
    target_ids = {s["platform_target_id"] for s in shapes}
    expected_ids = {
        "x", "telegram_channel_destination", "telegram_remote_operator",
        "substack", "linkedin", "threads", "instagram",
        "facebook_page", "tiktok", "youtube"
    }
    assert target_ids == expected_ids


def test_4_each_platform_shape_has_required_fields():
    """4. Verify each platform shape has required fields."""
    p = build_contract_packet()
    shapes = p["platform_shapes"]
    for s in shapes:
        assert len(s["required_fields"]) > 0
        field_names = {f["field_name"] for f in s["fields"]}
        assert set(s["required_fields"]).issubset(field_names)


def test_5_every_field_placeholder_only_true():
    """5. Verify every field placeholder_only true."""
    p = build_contract_packet()
    for s in p["platform_shapes"]:
        for f in s["fields"]:
            assert f["placeholder_only"] is True


def test_6_every_field_publishable_text_false():
    """6. Verify every field publishable_text false."""
    p = build_contract_packet()
    for s in p["platform_shapes"]:
        for f in s["fields"]:
            assert f["publishable_text"] is False


def test_7_dispatch_ready_false_across_all_shapes():
    """7. Verify dispatch_ready false across all shapes."""
    p = build_contract_packet()
    for s in p["platform_shapes"]:
        for f in s["fields"]:
            assert f["dispatch_ready"] is False


def test_8_platform_payload_created_false():
    """8. Verify platform_payload_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["platform_payload_created"] is False


def test_9_publishable_payload_created_false():
    """9. Verify publishable_payload_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["publishable_payload_created"] is False


def test_10_account_binding_and_credential_gates_required_but_inactive():
    """10. Verify account binding and credential gates required but inactive."""
    p = build_contract_packet()
    assert p["safety_flags"]["account_binding_active"] is False
    assert p["safety_flags"]["credential_values_loaded"] is False
    for s in p["platform_shapes"]:
        assert "requires future account binding verification" in s["account_binding_requirement"]
        assert "requires future credential gate authentication" in s["credential_gate_requirement"]


def test_11_payload_hash_lock_required():
    """11. Verify payload hash lock required."""
    p = build_contract_packet()
    for s in p["platform_shapes"]:
        assert "requires cryptographically verified payload hash lock" in s["payload_hash_lock_requirement"]


def test_12_operator_review_required():
    """12. Verify operator review required."""
    p = build_contract_packet()
    for s in p["platform_shapes"]:
        assert "requires manual operator confirmation" in s["operator_review_requirement"]


def test_13_citation_and_limitation_rendering_required():
    """13. Verify citation and limitation rendering required."""
    p = build_contract_packet()
    for s in p["platform_shapes"]:
        assert "must append citation footnotes stub format" in s["citation_rendering_requirement"]
        assert "must append limitations warn label format" in s["limitations_rendering_requirement"]


def test_14_dqr_readiness_current_truth_not_cleared():
    """14. Verify DQR/readiness/current truth not cleared."""
    p = build_contract_packet()
    assert p["safety_flags"]["dqr_cleared_by_contentops"] is False
    assert p["safety_flags"]["readiness_cleared_by_contentops"] is False
    assert p["safety_flags"]["current_truth_promoted"] is False


def test_15_no_financial_advice_signal_execution_language():
    """15. Verify no financial advice/signal/execution language."""
    p = build_contract_packet()
    assert p["safety_flags"]["financial_advice"] is False
    assert p["safety_flags"]["signal_language"] is False
    assert p["safety_flags"]["broker_order_execution"] is False
    assert p["safety_flags"]["raw_vendor_redistribution"] is False


def test_16_no_env_network_credential_platform_provider_api_imports_or_calls():
    """16. Scan code to ensure no environment, network, or credential API modules are imported."""
    with open("live_contentops/platform_preview_dry_payload_shape_registry_contract.py", encoding="utf-8") as f:
        content = f.read()
    forbidden = ["import os", "from os", "import requests", "urllib", "dotenv", "socket"]
    for pattern in forbidden:
        assert pattern not in content, f"Forbidden import or keyword '{pattern}' found."


def test_17_no_ingestion_repo_mutation_or_path_access():
    """17. Verify no ingestion repo mutation or path access is allowed."""
    p = build_contract_packet()
    assert p["safety_flags"]["ingestion_repo_mutated"] is False


def test_18_ledger_family_registered():
    """18. Verify ledger family is registered."""
    assert LEDGER_FAMILY in ENTRY_FAMILIES


def test_19_artifacts_written_only_under_docs_automation_0175an():
    """19. Verify that write_artifacts fails with ValueError outside docs/automation/0175AN."""
    with pytest.raises(ValueError, match="artifact_writer_refuses_paths_outside_docs_automation_0175AN"):
        write_artifacts(repo_root=".", output_dir="docs/automation/other")


def test_20_progress_ledger_resolves_0175am_and_appends_0175an():
    """20. Verify progress ledger is updated with 0175AM final HEAD and 0175AN row."""
    path = Path("docs/CONTENTOPS_PROGRESS_LEDGER_AND_FINAL_PRODUCT_CHECKLIST.md")
    assert path.exists()
    content = path.read_text(encoding="utf-8")

    # One-task-lag check
    assert "| `TASK_CONTENTOPS_0175AM_LANE_C_APPROVAL_PACKET_TO_PLATFORM_PREVIEW_PRECHECK_V0` | `ba81ce1851c8365cbd00f332daba2e087ea309df` | `4d10a497d0104f5d3acae54097708e9e8b97e5d7` |" in content
    assert "| `TASK_CONTENTOPS_0175AN_PLATFORM_PREVIEW_DRY_PAYLOAD_SHAPE_REGISTRY_V0` | `4d10a497d0104f5d3acae54097708e9e8b97e5d7` | `RECORDED_IN_NEXT_TASK_READBACK` |" in content


def test_21_no_pycache_or_pyc_staged():
    """21. Ensure no pycache or .pyc files are staged/tracked in git."""
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
