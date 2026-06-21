"""Unit tests for Platform Preview Dry Render to Review Bundle contract (0175AP)."""
from __future__ import annotations

import json
from pathlib import Path
import pytest
import subprocess

from live_contentops.platform_preview_dry_render_to_review_bundle_contract import (
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


def test_2_consumes_0175ao_dry_render_packet_precedent():
    """2. Verify that the contract successfully consumes 0175AO dry render packet precedent."""
    p = build_contract_packet()
    assert "bundle_items" in p
    # Should import/use values from 0175AO dry renders
    assert len(p["bundle_items"]) == 10


def test_3_all_supported_platform_target_bundle_items_exist():
    """3. Verify all supported platform target bundle items exist."""
    p = build_contract_packet()
    items = p["bundle_items"]
    assert len(items) == 10
    target_ids = {item["platform_target_id"] for item in items}
    expected_ids = {
        "x", "telegram_channel_destination", "telegram_remote_operator",
        "substack", "linkedin", "threads", "instagram",
        "facebook_page", "tiktok", "youtube"
    }
    assert target_ids == expected_ids


def test_4_every_bundle_status_is_review_bundle_blocked():
    """4. Verify every bundle status is review_bundle_blocked."""
    p = build_contract_packet()
    for item in p["bundle_items"]:
        assert item["bundle_status"] == "review_bundle_blocked"


def test_5_operator_review_and_manual_decision_required():
    """5. Verify operator review and manual decision are required (both True) for all platform items."""
    p = build_contract_packet()
    for item in p["bundle_items"]:
        assert item["operator_review_required"] is True
        assert item["manual_decision_required"] is True


def test_6_publishability_status_is_non_publishable_review_bundle():
    """6. Verify publishability status is non_publishable_review_bundle for all platform items."""
    p = build_contract_packet()
    for item in p["bundle_items"]:
        assert item["publishability_status"] == "non_publishable_review_bundle"


def test_7_citation_and_limitation_slots_preserved():
    """7. Verify citation and limitation slot status are preserved from the dry render records."""
    p = build_contract_packet()
    for item in p["bundle_items"]:
        assert item["citation_slot_status"] == "citation_rendering_required_but_pending"
        assert item["limitation_slot_status"] == "limitation_rendering_required_but_pending"


def test_8_dqr_readiness_current_truth_unresolved():
    """8. Verify DQR status, readiness status, and current truth status are unresolved/unpromoted."""
    p = build_contract_packet()
    for item in p["bundle_items"]:
        assert item["dqr_status"] == "dqr_unresolved"
        assert item["readiness_status"] == "readiness_unresolved"
        assert item["current_truth_status"] == "current_truth_unpromoted"


def test_9_account_binding_credential_hash_lock_and_dispatch_gates():
    """9. Verify account binding, credential, payload hash lock, and dispatch gate status are preserved."""
    p = build_contract_packet()
    for item in p["bundle_items"]:
        assert item["account_binding_status"] == "binding_required_but_inactive"
        assert item["credential_gate_status"] == "credential_required_but_locked"
        assert item["payload_hash_lock_status"] == "hash_lock_required_but_pending"
        assert item["dispatch_gate_status"] == "dispatch_gate_required_but_locked"


def test_10_decision_stub_disabled_pending_future_operator_gate():
    """10. Verify decision stub exists with decision_status set to disabled_pending_future_operator_gate."""
    p = build_contract_packet()
    for item in p["bundle_items"]:
        assert "decision_stub" in item
        assert item["decision_stub"]["decision_status"] == "disabled_pending_future_operator_gate"


def test_11_all_buttons_in_decision_stub_disabled():
    """11. Verify all buttons in the decision stub are False."""
    p = build_contract_packet()
    for item in p["bundle_items"]:
        stub = item["decision_stub"]
        assert stub["approve_button_enabled"] is False
        assert stub["reject_button_enabled"] is False
        assert stub["request_revision_enabled"] is False
        assert stub["publish_button_enabled"] is False
        assert stub["dispatch_button_enabled"] is False


def test_12_operator_identity_and_approval_signature_absent():
    """12. Verify operator identity bound and approval signature present are False in decision stubs."""
    p = build_contract_packet()
    for item in p["bundle_items"]:
        stub = item["decision_stub"]
        assert stub["operator_identity_bound"] is False
        assert stub["approval_signature_present"] is False


def test_13_payload_hash_locked_false_in_decision_stubs():
    """13. Verify payload hash locked is False in decision stubs."""
    p = build_contract_packet()
    for item in p["bundle_items"]:
        stub = item["decision_stub"]
        assert stub["payload_hash_locked"] is False


def test_14_global_blockers_list_contains_active_blockers():
    """14. Verify global blockers list contains exactly 10 active blockers."""
    p = build_contract_packet()
    assert len(p["global_blockers"]) == 10
    for blocker in p["global_blockers"]:
        assert blocker["active"] is True


def test_15_verification_checklist_items_pending():
    """15. Verify verification checklist contains exactly 3 pending items."""
    p = build_contract_packet()
    assert len(p["bundle_checklist"]) == 3
    for checklist_item in p["bundle_checklist"]:
        assert checklist_item["passed"] is False


def test_16_invariant_validation_safety_flags_correct():
    """16. Verify all invariant validation safety flags are set correctly."""
    p = build_contract_packet()
    safety = p["safety_flags"]
    assert safety["local_only"] is True
    assert safety["fixture_only"] is True
    assert safety["schema_only"] is True
    assert safety["dry_render_only"] is True
    assert safety["review_bundle_only"] is True
    assert safety["network_performed"] is False
    assert safety["env_read"] is False
    assert safety["credential_values_loaded"] is False
    assert safety["platform_api_called"] is False
    assert safety["provider_api_called"] is False
    assert safety["account_binding_active"] is False
    assert safety["scheduler_enabled"] is False
    assert safety["autonomous_posting"] is False
    assert safety["autonomous_reply_or_dm"] is False
    assert safety["scraping"] is False
    assert safety["ingestion_repo_mutated"] is False
    assert safety["dqr_cleared_by_contentops"] is False
    assert safety["readiness_cleared_by_contentops"] is False
    assert safety["current_truth_promoted"] is False
    assert safety["public_postable"] is False
    assert safety["dispatch_ready"] is False
    assert safety["platform_payload_created"] is False
    assert safety["publishable_payload_created"] is False
    assert safety["export_ready"] is False
    assert safety["approved_for_publication"] is False
    assert safety["operator_approval_granted"] is False
    assert safety["financial_advice"] is False
    assert safety["signal_language"] is False
    assert safety["broker_order_execution"] is False
    assert safety["raw_vendor_redistribution"] is False
    assert safety["approved_internal_alpha_artifacts_available"] is False


def test_17_summary_counts_dictionary_correct():
    """17. Verify summary counts dictionary is correct."""
    p = build_contract_packet()
    counts = p["summary_counts"]
    assert counts["registered_renders_count"] == 10
    assert counts["bundle_items_count"] == 10
    assert counts["global_blockers_count"] == 10
    assert counts["checklist_items_count"] == 3


def test_18_blocked_capabilities_list_correct():
    """18. Verify blocked capabilities list is correct."""
    p = build_contract_packet()
    assert p["blocked_capabilities"] == [
        "live_publishing_dispatch",
        "autonomous_reply_automation",
        "live_credential_hydration",
        "active_scheduler_triggers",
        "manual_review_export"
    ]


def test_19_missing_future_gates_list_correct():
    """19. Verify missing future gates list is correct."""
    p = build_contract_packet()
    assert p["missing_future_gates"] == [
        "lane_c_platform_review_bundle_operator_decision_gate",
        "production_key_vault_decrypter",
        "live_operator_signature_vault"
    ]


def test_20_next_required_gate_correct():
    """20. Verify next required gate is lane_c_platform_review_bundle_operator_decision_gate."""
    p = build_contract_packet()
    assert p["next_required_gate"] == "lane_c_platform_review_bundle_operator_decision_gate"


def test_21_ledger_family_registered():
    """21. Verify ledger family platform_preview_dry_render_to_review_bundle_future is registered."""
    assert LEDGER_FAMILY in ENTRY_FAMILIES


def test_22_artifacts_written_only_under_docs_automation_0175ap():
    """22. Verify that write_artifacts fails with ValueError outside docs/automation/0175AP."""
    with pytest.raises(ValueError, match="artifact_writer_refuses_paths_outside_docs_automation_0175AP"):
        write_artifacts(repo_root=".", output_dir="docs/automation/other")


def test_23_progress_ledger_resolves_0175ao_and_appends_0175ap():
    """23. Verify progress ledger resolves 0175AO to 1a2d9bd78a254bee8790c3a8288168166a3f2fa8 and appends 0175AP."""
    path = Path("docs/CONTENTOPS_PROGRESS_LEDGER_AND_FINAL_PRODUCT_CHECKLIST.md")
    assert path.exists()
    content = path.read_text(encoding="utf-8")

    # One-task-lag checks
    assert "| `TASK_CONTENTOPS_0175AO_PLATFORM_PREVIEW_DRY_RENDER_PACKET_V0` | `f57a23fb61a550d9528c1984d8e758e7f00ab265` | `1a2d9bd78a254bee8790c3a8288168166a3f2fa8` |" in content
    assert "| `TASK_CONTENTOPS_0175AP_PLATFORM_PREVIEW_DRY_RENDER_TO_REVIEW_BUNDLE_V0` | `1a2d9bd78a254bee8790c3a8288168166a3f2fa8` | `ab4a851ff60121cc3c3bdd85e25ed58c07aa9766` |" in content


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


def test_25_no_env_network_credential_platform_provider_api_imports_or_calls():
    """25. Scan code to ensure no environment, network, or credential API modules are imported."""
    with open("live_contentops/platform_preview_dry_render_to_review_bundle_contract.py", encoding="utf-8") as f:
        content = f.read()
    forbidden = ["import os", "from os", "import requests", "urllib", "dotenv", "socket"]
    for pattern in forbidden:
        assert pattern not in content, f"Forbidden import or keyword '{pattern}' found."


def test_26_no_ingestion_repo_mutation_or_path_access():
    """26. Verify no ingestion repo mutation or path access is allowed."""
    p = build_contract_packet()
    assert p["safety_flags"]["ingestion_repo_mutated"] is False


def test_27_review_notes_placeholder_format():
    """27. Verify review notes placeholder format is correct."""
    p = build_contract_packet()
    for item in p["bundle_items"]:
        tid = item["platform_target_id"]
        assert item["review_notes_placeholder"] == f"[REVIEW_NOTE_PLACEHOLDER: operator comments for {tid}]"


def test_28_target_files_generated_exist_and_are_valid():
    """28. Verify target files generated in docs/automation/0175AP exist and are valid."""
    out_dir = Path("docs/automation/0175AP")
    packet_path = out_dir / "platform_preview_dry_render_to_review_bundle_contract_packet.json"
    runbook_path = out_dir / "platform_preview_dry_render_to_review_bundle_contract.md"
    assert packet_path.exists()
    assert runbook_path.exists()

    # Load and validate json
    data = json.loads(packet_path.read_text(encoding="utf-8"))
    assert data["packet_hash"] is not None
    assert len(data["bundle_items"]) == 10

    # Read markdown
    md_content = runbook_path.read_text(encoding="utf-8")
    assert "# Platform Preview Dry Render to Review Bundle Contract" in md_content
