"""Unit tests for Platform Preview Dry Render Packet contract (0175AO)."""
from __future__ import annotations

import json
from pathlib import Path
import pytest
import subprocess

from live_contentops.platform_preview_dry_render_packet_contract import (
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


def test_2_consumes_0175an_shape_registry_precedent():
    """2. Verify that the contract successfully consumes 0175AN shape registry precedent."""
    p = build_contract_packet()
    assert "platform_shapes" in p
    assert len(p["platform_shapes"]) == 10


def test_3_all_supported_platform_target_dry_renders_exist():
    """3. Verify all supported platform target dry renders exist."""
    p = build_contract_packet()
    records = p["render_records"]
    assert len(records) == 10
    target_ids = {r["platform_target_id"] for r in records}
    expected_ids = {
        "x", "telegram_channel_destination", "telegram_remote_operator",
        "substack", "linkedin", "threads", "instagram",
        "facebook_page", "tiktok", "youtube"
    }
    assert target_ids == expected_ids


def test_4_every_render_status_is_dry_render_blocked():
    """4. Verify every render status is dry_render_blocked."""
    p = build_contract_packet()
    for r in p["render_records"]:
        assert r["render_status"] == "dry_render_blocked"


def test_5_every_field_placeholder_only_true():
    """5. Verify every field placeholder_only true."""
    p = build_contract_packet()
    for r in p["render_records"]:
        for f in r["field_renders"]:
            assert f["placeholder_only"] is True


def test_6_every_field_publishable_text_false():
    """6. Verify every field publishable_text false."""
    p = build_contract_packet()
    for r in p["render_records"]:
        for f in r["field_renders"]:
            assert f["publishable_text"] is False


def test_7_every_field_platform_ready_false():
    """7. Verify every field platform_ready false."""
    p = build_contract_packet()
    for r in p["render_records"]:
        for f in r["field_renders"]:
            assert f["platform_ready"] is False


def test_8_dispatch_ready_false_across_all_renders():
    """8. Verify dispatch_ready false across all renders."""
    p = build_contract_packet()
    for r in p["render_records"]:
        for f in r["field_renders"]:
            assert f["dispatch_ready"] is False
    for r in p["render_records"]:
        assert r["dispatch_ready"] is False
    assert p["safety_flags"]["dispatch_ready"] is False


def test_9_platform_payload_created_false():
    """9. Verify platform_payload_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["platform_payload_created"] is False
    for r in p["render_records"]:
        assert r["platform_payload_created"] is False


def test_10_publishable_payload_created_false():
    """10. Verify publishable_payload_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["publishable_payload_created"] is False
    for r in p["render_records"]:
        assert r["publishable_payload_created"] is False


def test_11_export_ready_false():
    """11. Verify export_ready false."""
    p = build_contract_packet()
    assert p["safety_flags"]["export_ready"] is False
    for r in p["render_records"]:
        assert r["export_ready"] is False


def test_12_account_binding_and_credential_gates_required_but_inactive():
    """12. Verify account binding and credential gates required but inactive."""
    p = build_contract_packet()
    assert p["safety_flags"]["account_binding_active"] is False
    assert p["safety_flags"]["credential_values_loaded"] is False
    for r in p["render_records"]:
        assert r["account_binding_active"] is False
        assert r["credential_values_loaded"] is False
        assert r["account_binding_status"] == "binding_required_but_inactive"
        assert r["credential_gate_status"] == "credential_required_but_locked"


def test_13_payload_hash_lock_required():
    """13. Verify payload hash lock required."""
    p = build_contract_packet()
    for r in p["render_records"]:
        assert r["payload_hash_lock_status"] == "hash_lock_required_but_pending"


def test_14_operator_review_required():
    """14. Verify operator review required."""
    p = build_contract_packet()
    for r in p["render_records"]:
        assert r["operator_review_required"] is True
        assert r["operator_review_status"] == "review_required_but_pending"


def test_15_citation_and_limitation_slots_preserved():
    """15. Verify citation and limitation slots preserved."""
    p = build_contract_packet()
    for r in p["render_records"]:
        assert r["citation_slot_status"] == "citation_rendering_required_but_pending"
        assert r["limitation_slot_status"] == "limitation_rendering_required_but_pending"


def test_16_dqr_readiness_current_truth_not_cleared():
    """16. Verify DQR, readiness, and current truth not cleared."""
    p = build_contract_packet()
    assert p["safety_flags"]["dqr_cleared_by_contentops"] is False
    assert p["safety_flags"]["readiness_cleared_by_contentops"] is False
    assert p["safety_flags"]["current_truth_promoted"] is False


def test_17_no_financial_advice_signal_execution_language():
    """17. Verify no financial advice, signal language, or broker order execution flags/fields exist."""
    p = build_contract_packet()
    assert p["safety_flags"]["financial_advice"] is False
    assert p["safety_flags"]["signal_language"] is False
    assert p["safety_flags"]["broker_order_execution"] is False
    assert p["safety_flags"]["raw_vendor_redistribution"] is False
    for r in p["render_records"]:
        for f in r["field_renders"]:
            assert f["contains_financial_advice"] is False
            assert f["contains_signal_language"] is False


def test_18_no_fake_market_numbers():
    """18. Verify that field renders do not contain fake market numbers."""
    p = build_contract_packet()
    for r in p["render_records"]:
        for f in r["field_renders"]:
            assert f["contains_market_number"] is False
            assert not any(char.isdigit() for char in f["placeholder_value"] if char not in (".", "_", ":", "/"))


def test_19_no_env_network_credential_platform_provider_api_imports_or_calls():
    """19. Scan code to ensure no environment, network, or credential API modules are imported."""
    with open("live_contentops/platform_preview_dry_render_packet_contract.py", encoding="utf-8") as f:
        content = f.read()
    forbidden = ["import os", "from os", "import requests", "urllib", "dotenv", "socket"]
    for pattern in forbidden:
        assert pattern not in content, f"Forbidden import or keyword '{pattern}' found."


def test_20_no_ingestion_repo_mutation_or_path_access():
    """20. Verify no ingestion repo mutation or path access is allowed."""
    p = build_contract_packet()
    assert p["safety_flags"]["ingestion_repo_mutated"] is False


def test_21_ledger_family_registered():
    """21. Verify ledger family is registered."""
    assert LEDGER_FAMILY in ENTRY_FAMILIES


def test_22_artifacts_written_only_under_docs_automation_0175ao():
    """22. Verify that write_artifacts fails with ValueError outside docs/automation/0175AO."""
    with pytest.raises(ValueError, match="artifact_writer_refuses_paths_outside_docs_automation_0175AO"):
        write_artifacts(repo_root=".", output_dir="docs/automation/other")


def test_23_progress_ledger_resolves_0175an_and_appends_0175ao():
    """23. Verify progress ledger is updated with 0175AN final HEAD and 0175AO row."""
    path = Path("docs/CONTENTOPS_PROGRESS_LEDGER_AND_FINAL_PRODUCT_CHECKLIST.md")
    assert path.exists()
    content = path.read_text(encoding="utf-8")

    # One-task-lag check
    assert "| `TASK_CONTENTOPS_0175AN_PLATFORM_PREVIEW_DRY_PAYLOAD_SHAPE_REGISTRY_V0` | `4d10a497d0104f5d3acae54097708e9e8b97e5d7` | `f57a23fb61a550d9528c1984d8e758e7f00ab265` |" in content
    assert "| `TASK_CONTENTOPS_0175AO_PLATFORM_PREVIEW_DRY_RENDER_PACKET_V0` | `f57a23fb61a550d9528c1984d8e758e7f00ab265` | `RECORDED_IN_NEXT_TASK_READBACK` |" in content


def test_24_no_pycache_or_pyc_staged():
    """24. Ensure no pycache or .pyc files are staged/tracked in git."""
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
