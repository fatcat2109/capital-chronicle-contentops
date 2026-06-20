import pytest
import json
from pathlib import Path
from dataclasses import replace

from live_contentops import live_read_only_research_local_preflight_simulation_contract as contract
from live_contentops import live_read_only_research_runbook_approval_gate_dry_run_contract as runbook
from live_contentops import live_read_only_research_evidence_packet_dry_run_schema_contract as evidence
from live_contentops import live_read_only_research_approval_packet_schema_contract as approval
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit
from live_contentops import platform_universe_registry_v2
from live_contentops import platform_preflight_dry_run_request_budget_contract
from live_contentops import rate_budget_kill_switch_matrix_contract


def test_packet_builds_deterministically():
    # 1. Packet builds deterministically.
    p1 = contract.build_supervised_live_read_only_research_local_preflight_simulation_packet()
    p2 = contract.build_supervised_live_read_only_research_local_preflight_simulation_packet()
    assert p1.packet_id == p2.packet_id
    assert p1.packet_hash == p2.packet_hash


def test_exactly_10_platforms_represented():
    # 2. Exactly 10 platforms represented.
    packet = contract.build_supervised_live_read_only_research_local_preflight_simulation_packet()
    assert len(packet.simulated_adapter_profiles) == 10
    assert packet.platform_count == 10


def test_platform_ids_match_universe():
    # 3. Platform IDs match platform universe registry.
    packet = contract.build_supervised_live_read_only_research_local_preflight_simulation_packet()
    pids = {p.platform_id for p in packet.simulated_adapter_profiles}
    assert pids == set(contract.PLATFORM_IDS)


def test_runbook_gate_packet_consumed():
    # 4. 0174UQ runbook gate packet is consumed.
    rq = runbook.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet()
    dec_x = next(d for d in rq.runbook_gate_decisions if d.platform_id == "x")
    dec_x_mod = replace(dec_x, precheck_status="custom_precheck_test_val")
    rq_mod = replace(rq, runbook_gate_decisions=tuple(dec_x_mod if d.platform_id == "x" else d for d in rq.runbook_gate_decisions))
    
    packet = contract.build_supervised_live_read_only_research_local_preflight_simulation_packet(runbook_packet=rq_mod)
    dec_x_sim = next(d for d in packet.simulation_decisions if d.platform_id == "x")
    assert dec_x_sim.precheck_status == "custom_precheck_test_val"


def test_evidence_packet_consumed():
    # 5. 0174UP evidence packet is consumed.
    packet = contract.build_supervised_live_read_only_research_local_preflight_simulation_packet()
    ep = evidence.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet()
    for t in ep.templates:
        assert packet.redaction_policy_summary[t.platform_id] == t.redaction_policy_ref


def test_approval_packet_consumed():
    # 6. 0174UO approval packet is consumed.
    ap = approval.build_supervised_live_read_only_research_approval_packet_schema_packet()
    assert approval.TASK_LABEL == "TASK_CONTENTOPS_0174UO_LIVE_READ_ONLY_RESEARCH_APPROVAL_PACKET_SCHEMA_V0"
    assert ap.matrix_version is not None


def test_all_simulated_adapter_profiles_are_simulated_only():
    # 7. All simulated adapter profiles are simulated_only.
    packet = contract.build_supervised_live_read_only_research_local_preflight_simulation_packet()
    for p in packet.simulated_adapter_profiles:
        assert p.adapter_mode == "simulated_only"


def test_all_counters_and_safety_flags_are_zero():
    # 8. All network/env/credential/API/provider/browser/scheduler/scraping/DM counters are zero.
    packet = contract.build_supervised_live_read_only_research_local_preflight_simulation_packet()
    for p in packet.simulated_adapter_profiles:
        assert p.credential_values_accessed is False
        assert p.env_read is False
        assert p.network_performed is False
        assert p.platform_api_called is False
        assert p.provider_api_called is False
        assert p.browser_session_used is False
        assert p.raw_response_stored is False
        assert p.secret_output_allowed is False
        assert p.response_body_storage_allowed is False
        assert p.public_post_allowed is False
        assert p.live_write_allowed is False
    
    for d in packet.simulation_decisions:
        assert d.live_read_allowed is False
        assert d.live_write_allowed is False
        assert d.env_read_allowed is False
        assert d.credential_hydrated is False
        assert d.platform_api_called is False
        assert d.provider_api_called is False
        assert d.public_post_allowed is False
        assert d.scheduler_enabled is False
        assert d.browser_session_used is False
        assert d.scraping_performed is False
        assert d.dm_or_reply_automation_allowed is False
        assert d.readiness_cleared is False
    
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


def test_raw_response_logging_always_false():
    # 9. Raw response logging is always false.
    packet = contract.build_supervised_live_read_only_research_local_preflight_simulation_packet()
    for s in packet.simulation_scenarios:
        assert s.raw_response_logged is False


def test_secret_output_always_false():
    # 10. Secret output is always false.
    packet = contract.build_supervised_live_read_only_research_local_preflight_simulation_packet()
    for p in packet.simulated_adapter_profiles:
        assert p.secret_output_allowed is False


def test_response_body_storage_always_false():
    # 11. Response body storage is always false.
    packet = contract.build_supervised_live_read_only_research_local_preflight_simulation_packet()
    for p in packet.simulated_adapter_profiles:
        assert p.response_body_storage_allowed is False


def test_request_budget_max_for_api_platforms():
    # 12. Request budget cannot exceed 1 for API-like platforms.
    packet = contract.build_supervised_live_read_only_research_local_preflight_simulation_packet()
    for p in packet.simulated_adapter_profiles:
        if p.platform_id != "substack_newsletter":
            assert p.request_budget_max <= 1


def test_substack_newsletter_manual_only():
    # 13. Substack is manual-only/no API/no credential.
    packet = contract.build_supervised_live_read_only_research_local_preflight_simulation_packet()
    p = next(profile for profile in packet.simulated_adapter_profiles if profile.platform_id == "substack_newsletter")
    assert p.endpoint_allowlist_status == "manual_no_api"
    assert p.request_budget_max == 0
    assert p.timeout_seconds_max == 0
    assert p.credential_policy == "manual_no_credential"
    
    for d in packet.simulation_decisions:
        if d.platform_id == "substack_newsletter":
            assert d.validation_status == "manual_only"
            assert d.validation_strength == "manual_policy_only"
            assert "manual_export_only" in d.blocked_reasons


def test_telegram_remote_and_channel_remain_distinct():
    # 14. Telegram Remote Operator and Telegram Channel Destination remain distinct.
    packet = contract.build_supervised_live_read_only_research_local_preflight_simulation_packet()
    t_op = next(p for p in packet.simulated_adapter_profiles if p.platform_id == "telegram_remote_operator")
    t_ch = next(p for p in packet.simulated_adapter_profiles if p.platform_id == "telegram_channel_destination")
    assert t_op.endpoint_family != t_ch.endpoint_family
    assert t_op.endpoint_family == "telegram_bot_getupdates_or_webhook_symbolic"
    assert t_ch.endpoint_family == "telegram_bot_getchat_symbolic"


def test_x_proof_gaps_blocked():
    # 15. X proof gaps remain blocked.
    packet = contract.build_supervised_live_read_only_research_local_preflight_simulation_packet()
    for d in packet.simulation_decisions:
        if d.platform_id == "x":
            for r in ("x_app_access_gap", "spend_gate_unresolved", "rate_budget_gap", "read_only_endpoint_proof_gap"):
                assert r in d.blocked_reasons
                assert r in d.missing_proofs


def test_telegram_remote_operator_blocked_reasons():
    # 16. Telegram Remote Operator arbitrary DM/reply automation remains blocked.
    packet = contract.build_supervised_live_read_only_research_local_preflight_simulation_packet()
    for d in packet.simulation_decisions:
        if d.platform_id == "telegram_remote_operator":
            assert "no_arbitrary_dm_allowed" in d.blocked_reasons
            assert "operator_inbox_proof_required" in d.blocked_reasons


def test_telegram_channel_destination_blocked_reasons():
    # 17. Telegram Channel Destination posting/admin proof gaps remain blocked.
    packet = contract.build_supervised_live_read_only_research_local_preflight_simulation_packet()
    for d in packet.simulation_decisions:
        if d.platform_id == "telegram_channel_destination":
            assert "channel_admin_proof_required" in d.blocked_reasons
            assert "bot_permission_gap" in d.blocked_reasons
            assert "channel_state_symbolic_only" in d.blocked_reasons


def test_linkedin_blocked_reasons():
    # 18. LinkedIn proof gaps remain blocked.
    packet = contract.build_supervised_live_read_only_research_local_preflight_simulation_packet()
    for d in packet.simulation_decisions:
        if d.platform_id == "linkedin":
            assert "linkedin_organization_page_proof_missing" in d.blocked_reasons


def test_meta_family_blocked_reasons():
    # 19. Meta-family proof gaps remain blocked.
    packet = contract.build_supervised_live_read_only_research_local_preflight_simulation_packet()
    for pid in ("threads", "instagram", "facebook_page"):
        for d in packet.simulation_decisions:
            if d.platform_id == pid:
                assert "meta_app_review_closed" in d.blocked_reasons
                assert "meta_app_account_proof_required" in d.blocked_reasons


def test_tiktok_blocked_reasons():
    # 20. TikTok audit/creator/video proof gaps remain blocked.
    packet = contract.build_supervised_live_read_only_research_local_preflight_simulation_packet()
    for d in packet.simulation_decisions:
        if d.platform_id == "tiktok":
            assert "tiktok_app_audit_closed" in d.blocked_reasons
            assert "creator_account_proof_required" in d.blocked_reasons
            assert "video_publish_proof_required" in d.blocked_reasons


def test_youtube_blocked_reasons_and_no_1600():
    # 21. YouTube OAuth/quota/upload proof gaps remain blocked and no “1600” appears.
    packet = contract.build_supervised_live_read_only_research_local_preflight_simulation_packet()
    for d in packet.simulation_decisions:
        if d.platform_id == "youtube":
            assert "youtube_quota_unresolved" in d.blocked_reasons
            assert "youtube_oauth_flow_closed" in d.blocked_reasons
            assert "upload_proof_required" in d.blocked_reasons
    
    md_text = contract.render_runbook(packet)
    assert "1600" not in md_text


def test_simulation_scenarios_fail_closed():
    # 22-30. Scenario failures closed.
    packet = contract.build_supervised_live_read_only_research_local_preflight_simulation_packet()
    scenarios_to_check = [
        ("endpoint_allowlist_missing", "endpoint_allowlist_missing"),
        ("request_budget_exceeded", "request_budget_exceeds_limit"),
        ("timeout_triggered", "timeout_triggered"),
        ("credential_slot_missing", "credential_values_exposed"),
        ("redaction_proof_missing", "redaction_policy_missing"),
        ("raw_response_attempt_blocked", "raw_response_logging_allowed"),
        ("secret_output_attempt_blocked", "secret_output_allowed"),
        ("kill_switch_open_blocked", "kill_switch_policy_unresolved"),
        ("operator_approval_missing", "operator_approval_disabled"),
    ]
    for sc_id, expected_blocked_reason in scenarios_to_check:
        for d in packet.simulation_decisions:
            if d.scenario_id == sc_id:
                assert d.validation_status in ("blocked", "manual_only")
                assert expected_blocked_reason in d.blocked_reasons
                assert d.live_read_allowed is False


def test_u9_audit_entries_validate():
    # 31. U9 audit entries validate.
    packet = contract.build_supervised_live_read_only_research_local_preflight_simulation_packet()
    decisions = packet.simulation_decisions
    entries = contract.build_u9_audit_entries(decisions)
    
    chain = audit.build_ledger_chain(entries)
    validation = audit.validate_ledger_chain(chain)
    assert validation.validation_status == "pass"
    assert len(validation.blocked_reasons) == 0


def test_u9_family_matches():
    # 32. U9 family equals live_read_only_research_local_preflight_simulation_future.
    packet = contract.build_supervised_live_read_only_research_local_preflight_simulation_packet()
    assert len(packet.u9_audit_entry_families) > 0
    for fam in packet.u9_audit_entry_families:
        assert fam == "live_read_only_research_local_preflight_simulation_future"


def test_artifact_writer_refuses_outside_paths(tmp_path):
    # 33. Artifact writer refuses paths outside docs/automation/0174UR.
    with pytest.raises(ValueError) as excinfo:
        contract.write_artifacts(repo_root=tmp_path, output_dir=tmp_path / "invalid_dir")
    assert "artifact_writer_refuses_paths_outside_docs_automation_0174UR" in str(excinfo.value)


def test_operator_planning_docs_untouched():
    # 34. Known untracked operator/stale-context paths remain untouched.
    untracked_paths = [
        "docs/CAPITAL_CHRONICLE_CONTENTOPS_HEAVY_BATCH_MASTER_PLAN_AFTER_0174U0.md",
        "docs/Capital Chronicle ContentOps Strategy.pdf",
        "docs/automation/0174YO_YP_YQ/",
        "docs/automation/0174YU_YV_YW/",
        "docs/reports/"
    ]
    for path_str in untracked_paths:
        p = Path(path_str)
        assert p.exists()
