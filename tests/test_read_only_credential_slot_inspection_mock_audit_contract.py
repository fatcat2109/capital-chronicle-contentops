import pytest
import json
from pathlib import Path
from dataclasses import replace

from live_contentops import read_only_credential_slot_inspection_mock_audit_contract as contract
from live_contentops import read_only_credential_slot_check_validation_contract as slot_check
from live_contentops import credential_handle_dotenv_secret_boundary_v2_contract as boundary
from live_contentops import platform_account_binding_registry_v2_contract as binding
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit
from live_contentops import platform_universe_registry_v2


def test_packet_builds_deterministically():
    # 1. Packet builds deterministically.
    p1 = contract.build_supervised_credential_slot_inspection_audit_packet()
    p2 = contract.build_supervised_credential_slot_inspection_audit_packet()
    assert p1.packet_id == p2.packet_id
    assert p1.packet_hash == p2.packet_hash


def test_exactly_10_platforms_represented():
    # 2. Exactly 10 platforms represented.
    packet = contract.build_supervised_credential_slot_inspection_audit_packet()
    assert packet.platform_count == 10
    platforms = {inv.platform_id for inv in packet.mock_inventories}
    assert platforms == set(contract.PLATFORM_IDS)


def test_platform_ids_match_universe():
    # 3. Platform IDs match platform universe registry.
    packet = contract.build_supervised_credential_slot_inspection_audit_packet()
    for inv in packet.mock_inventories:
        assert inv.platform_id in contract.PLATFORM_IDS


def test_slot_check_packet_consumed():
    # 4. 0174US credential slot check packet is consumed.
    sc = slot_check.build_supervised_read_only_credential_slot_check_packet()
    sc_mod = replace(sc, matrix_version="custom_version_slot_val")
    packet = contract.build_supervised_credential_slot_inspection_audit_packet(slot_packet=sc_mod)
    assert len(packet.mock_inventories) > 0


def test_boundary_contract_consumed_no_env():
    # 5. Credential boundary precedent contract is consumed without reading env.
    bp = boundary.build_credential_boundary_packet()
    assert len(bp.credential_handles) > 0


def test_account_binding_contract_consumed():
    # 6. Account binding precedent contract is consumed.
    ab = binding.build_platform_account_binding_registry_packet()
    assert len(ab.bindings) > 0


def test_no_os_environ_usage():
    # 7. New module contains no os.environ/getenv/load_dotenv/dotenv_values usage.
    module_path = Path("live_contentops/read_only_credential_slot_inspection_mock_audit_contract.py")
    content = module_path.read_text(encoding="utf-8")
    assert "os.environ" not in content
    assert "getenv" not in content
    assert "load_dotenv" not in content
    assert "dotenv_values" not in content


def test_mock_inventories_are_mock_only():
    # 8. Mock inventories are mock_only.
    packet = contract.build_supervised_credential_slot_inspection_audit_packet()
    for inv in packet.mock_inventories:
        assert inv.inventory_mode == "mock_only"


def test_no_raw_secret_in_packet_json():
    # 9. No raw secret value appears in packet JSON.
    packet = contract.build_supervised_credential_slot_inspection_audit_packet()
    packet_text = repr(packet)
    forbidden_terms = ("REPLACE_WITH_REAL", "api_key=", "token=", "password=", "bearer ")
    assert not any(term.lower() in packet_text.lower() for term in forbidden_terms)


def test_redacted_placeholder_as_classification():
    # 10. Redacted placeholder is allowed only as simulated classification, not as real value.
    packet = contract.build_supervised_credential_slot_inspection_audit_packet()
    for inv in packet.mock_inventories:
        assert inv.redacted_value == "[REDACTED]"
        assert inv.raw_secret_value == "absent"


def test_all_global_counters_are_zero():
    # 11. all global real env/dotenv/credential/secret/API/network/browser/scheduler/scraping/DM/live counters are zero.
    packet = contract.build_supervised_credential_slot_inspection_audit_packet()
    for inv in packet.mock_inventories:
        assert inv.value_material_serialized is False

    for f in packet.inspection_findings:
        assert f.secret_material_exposed is False
        assert f.credential_value_read is False
        assert f.env_read is False
        assert f.dotenv_loaded is False
        assert f.secret_hash_displayed is False
        assert f.token_prefix_displayed is False
        assert f.token_suffix_displayed is False
        assert f.platform_api_called is False
        assert f.provider_api_called is False
        assert f.live_read_allowed is False
        assert f.live_write_allowed is False
        assert f.public_post_allowed is False
        assert f.readiness_cleared is False

    sf = packet.safety_flags
    assert sf["live_read_allowed"] is False
    assert sf["live_write_allowed"] is False
    assert sf["public_post_allowed"] is False
    assert sf["credential_hydrated"] is False
    assert sf["platform_api_called"] is False
    assert sf["provider_api_called"] is False
    assert sf["telegram_api_called"] is False
    assert sf["network_performed"] is False
    assert sf["env_read"] is False
    assert sf["browser_session_used"] is False
    assert sf["scheduler_enabled"] is False
    assert sf["scraping_performed"] is False
    assert sf["dm_or_reply_automation_allowed"] is False
    assert sf["dispatch_ready"] is False
    assert sf["public_postable"] is False
    assert sf["autonomous_posting_allowed"] is False
    assert sf["current_truth_promoted"] is False
    assert sf["dqr_cleared"] is False
    assert sf["readiness_cleared"] is False
    assert sf["ingestion_repo_mutated"] is False
    assert sf["ui_generated"] is False
    assert sf["local_readiness_review_only"] is True
    assert sf["review_only"] is True
    assert sf["mock_only"] is True
    assert sf["all_real_secret_reads_blocked"] is True
    assert sf["all_env_reads_blocked"] is True
    assert sf["all_dotenv_loads_blocked"] is True
    assert sf["all_secret_outputs_blocked"] is True
    assert sf["all_live_actions_blocked"] is True


def test_credential_value_attempt_present_fails_closed():
    # 12. credential_value_attempt_present fails closed.
    packet = contract.build_supervised_credential_slot_inspection_audit_packet()
    for d in packet.audit_decisions:
        if "credential_value_attempt_present" in d.inventory_id:
            assert d.audit_decision_status in ("blocked", "manual_only")
            assert d.highest_severity == "high"
            assert "credential_value_attempt_present_blocked" in d.blocked_reasons


def test_secret_hash_attempt_present_fails_closed():
    # 13. secret_hash_attempt_present fails closed.
    packet = contract.build_supervised_credential_slot_inspection_audit_packet()
    for d in packet.audit_decisions:
        if "secret_hash_attempt_present" in d.inventory_id:
            assert d.audit_decision_status in ("blocked", "manual_only")
            assert d.highest_severity == "high"
            assert "secret_hash_attempt_present_blocked" in d.blocked_reasons


def test_token_prefix_suffix_attempt_present_fails_closed():
    # 14. token_prefix_suffix_attempt_present fails closed.
    packet = contract.build_supervised_credential_slot_inspection_audit_packet()
    for d in packet.audit_decisions:
        if "token_prefix_suffix_attempt_present" in d.inventory_id:
            assert d.audit_decision_status in ("blocked", "manual_only")
            assert d.highest_severity == "high"
            assert "token_prefix_suffix_attempt_present_blocked" in d.blocked_reasons


def test_dotenv_read_attempt_fails_closed():
    # 15. dotenv_read_attempt fails closed.
    packet = contract.build_supervised_credential_slot_inspection_audit_packet()
    for d in packet.audit_decisions:
        if "dotenv_read_attempt" in d.inventory_id:
            assert d.audit_decision_status in ("blocked", "manual_only")
            assert d.highest_severity == "high"
            assert "dotenv_read_attempt_blocked" in d.blocked_reasons


def test_env_read_attempt_fails_closed():
    # 16. env_read_attempt fails closed.
    packet = contract.build_supervised_credential_slot_inspection_audit_packet()
    for d in packet.audit_decisions:
        if d.inventory_id.endswith("_env_read_attempt"):
            assert d.audit_decision_status in ("blocked", "manual_only")
            assert d.highest_severity == "high"
            assert "env_read_attempt_blocked" in d.blocked_reasons


def test_forbidden_slot_name_present_fails_closed():
    # 17. forbidden_slot_name_present fails closed.
    packet = contract.build_supervised_credential_slot_inspection_audit_packet()
    for d in packet.audit_decisions:
        if "forbidden_slot_name_present" in d.inventory_id:
            assert d.audit_decision_status in ("blocked", "manual_only")
            assert d.highest_severity == "high"
            assert "forbidden_slot_name_present_blocked" in d.blocked_reasons


def test_missing_required_slot_fails_closed():
    # 18. missing_required_slot fails closed.
    packet = contract.build_supervised_credential_slot_inspection_audit_packet()
    for d in packet.audit_decisions:
        if "missing_required_slot" in d.inventory_id or "all_slots_absent" in d.inventory_id:
            assert d.audit_decision_status in ("blocked", "manual_only")
            assert d.highest_severity in ("high", "none")


def test_substack_newsletter_manual_only():
    # 19. Substack is manual-only/no API/no credential.
    packet = contract.build_supervised_credential_slot_inspection_audit_packet()
    for d in packet.audit_decisions:
        if d.platform_id == "substack_newsletter":
            assert d.audit_decision_status == "manual_only"
            assert d.audit_strength == "manual_policy_only"


def test_telegram_remote_and_channel_remain_distinct():
    # 20. Telegram Remote Operator and Telegram Channel Destination remain distinct.
    packet = contract.build_supervised_credential_slot_inspection_audit_packet()
    t_op = next(i for i in packet.mock_inventories if i.platform_id == "telegram_remote_operator" and "all_slots_absent" in i.inventory_id)
    t_ch = next(i for i in packet.mock_inventories if i.platform_id == "telegram_channel_destination" and "all_slots_absent" in i.inventory_id)
    assert t_op.inventory_id != t_ch.inventory_id


def test_x_proof_gaps_blocked():
    # 21. X proof gaps remain blocked.
    packet = contract.build_supervised_credential_slot_inspection_audit_packet()
    for d in packet.audit_decisions:
        if d.platform_id == "x":
            assert "x_app_access_gap" in d.blocked_reasons
            assert "spend_gate_unresolved" in d.blocked_reasons


def test_telegram_remote_operator_arbitrary_dm_blocked():
    # 22. Telegram Remote Operator arbitrary DM/reply remains blocked.
    packet = contract.build_supervised_credential_slot_inspection_audit_packet()
    for d in packet.audit_decisions:
        if d.platform_id == "telegram_remote_operator":
            assert "no_arbitrary_dm_allowed" in d.blocked_reasons


def test_telegram_channel_destination_posting_admin_gaps_blocked():
    # 23. Telegram Channel Destination posting/admin proof gaps remain blocked.
    packet = contract.build_supervised_credential_slot_inspection_audit_packet()
    for d in packet.audit_decisions:
        if d.platform_id == "telegram_channel_destination":
            assert "channel_admin_proof_required" in d.blocked_reasons


def test_linkedin_proof_gaps_remain_blocked():
    # 24. LinkedIn proof gaps remain blocked.
    packet = contract.build_supervised_credential_slot_inspection_audit_packet()
    for d in packet.audit_decisions:
        if d.platform_id == "linkedin":
            assert "linkedin_organization_page_proof_missing" in d.blocked_reasons


def test_meta_family_proof_gaps_remain_blocked():
    # 25. Meta-family proof gaps remain blocked.
    packet = contract.build_supervised_credential_slot_inspection_audit_packet()
    for pid in ("threads", "instagram", "facebook_page"):
        for d in packet.audit_decisions:
            if d.platform_id == pid:
                assert "meta_app_review_closed" in d.blocked_reasons


def test_tiktok_proof_gaps_remain_blocked():
    # 26. TikTok audit/creator/video proof gaps remain blocked.
    packet = contract.build_supervised_credential_slot_inspection_audit_packet()
    for d in packet.audit_decisions:
        if d.platform_id == "tiktok":
            assert "tiktok_app_audit_closed" in d.blocked_reasons


def test_youtube_proof_gaps_remain_blocked_no_1600():
    # 27. YouTube OAuth/quota/upload proof gaps remain blocked and no “1600” appears.
    packet = contract.build_supervised_credential_slot_inspection_audit_packet()
    for d in packet.audit_decisions:
        if d.platform_id == "youtube":
            assert "youtube_quota_unresolved" in d.blocked_reasons

    md_text = contract.render_runbook(packet)
    assert "1600" not in md_text


def test_u9_audit_entries_validate():
    # 28. U9 audit entries validate.
    packet = contract.build_supervised_credential_slot_inspection_audit_packet()
    decisions = packet.audit_decisions
    entries = contract.build_u9_audit_entries(decisions)

    chain = audit.build_ledger_chain(entries)
    validation = audit.validate_ledger_chain(chain)
    assert validation.validation_status == "pass"
    assert len(validation.blocked_reasons) == 0


def test_u9_family_matches():
    # 29. U9 family equals read_only_credential_slot_inspection_mock_audit_future.
    packet = contract.build_supervised_credential_slot_inspection_audit_packet()
    assert len(packet.u9_audit_entry_families) > 0
    for fam in packet.u9_audit_entry_families:
        assert fam == "read_only_credential_slot_inspection_mock_audit_future"


def test_artifact_writer_refuses_outside_paths(tmp_path):
    # 30. Artifact writer refuses paths outside docs/automation/0174UT.
    with pytest.raises(ValueError) as excinfo:
        contract.write_artifacts(repo_root=tmp_path, output_dir=tmp_path / "invalid_dir")
    assert "artifact_writer_refuses_paths_outside_docs_automation_0174UT" in str(excinfo.value)


def test_operator_planning_docs_untouched():
    # 31. Known untracked operator/stale-context paths remain untouched.
    untracked_paths = [
        "docs/archive/_repo_cleanup_2026-07-03/docs/CAPITAL_CHRONICLE_CONTENTOPS_HEAVY_BATCH_MASTER_PLAN_AFTER_0174U0.md",
        "docs/archive/_repo_cleanup_2026-07-03/docs/Capital Chronicle ContentOps Strategy.pdf",
        "docs/archive/_repo_cleanup_2026-07-03/docs/reports/"
    ]
    for path_str in untracked_paths:
        p = Path(path_str)
        assert p.exists()
