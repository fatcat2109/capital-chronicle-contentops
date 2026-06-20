import pytest

from live_contentops import platform_preflight_dry_run_request_budget_contract as contract
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit

def test_packet_builds_deterministically():
    packet1 = contract.build_preflight_dry_run_request_budget_packet()
    packet2 = contract.build_preflight_dry_run_request_budget_packet()
    assert packet1.packet_id == packet2.packet_id
    assert packet1.packet_hash == packet2.packet_hash
    assert len(packet1.proposed_actions) == 10
    assert len(packet1.decisions) == 10
    
    platforms = {a.platform_id for a in packet1.proposed_actions}
    assert len(platforms) == 10


def test_safety_violations_block_preflight():
    actions = contract.build_default_proposed_actions()
    
    # Test each safety violation flag
    violations = [
        {"live_read_requested": True},
        {"live_write_requested": True},
        {"env_read_requested": True},
        {"credential_hydration_requested": True},
        {"platform_api_call_requested": True},
        {"public_post_requested": True},
        {"scheduler_requested": True},
        {"browser_automation_requested": True},
    ]
    
    for v in violations:
        bad_action = contract.replace(actions[0], action_id="bad_action", **v)
        decision = contract.build_preflight_dry_run_decision(bad_action)
        assert decision.decision_status == "blocked_preflight"
        assert decision.decision_strength == "deterministic_block"
        flag_name = list(v.keys())[0]
        assert flag_name in decision.blocked_reasons


def test_kill_switch_open_or_missing_blocks_api_platforms():
    actions = contract.build_default_proposed_actions()
    
    for action in actions:
        if action.platform_id == "substack_newsletter":
            continue
            
        # Open kill switch
        open_action = contract.replace(action, action_id="open_ks", kill_switch_state="open")
        dec_open = contract.build_preflight_dry_run_decision(open_action)
        assert dec_open.decision_status == "blocked_preflight"
        assert dec_open.decision_strength == "deterministic_block"
        assert dec_open.kill_switch_status == "kill_switch_open_blocks"
        assert "kill_switch_open_blocks" in dec_open.blocked_reasons
        
        # Missing kill switch
        missing_action = contract.replace(action, action_id="missing_ks", kill_switch_state="missing")
        dec_missing = contract.build_preflight_dry_run_decision(missing_action)
        assert dec_missing.decision_status == "blocked_preflight"
        assert dec_missing.decision_strength == "deterministic_block"
        assert dec_missing.kill_switch_status == "kill_switch_missing_blocks"
        assert "kill_switch_missing_blocks" in dec_missing.blocked_reasons


def test_request_budget_exceeds_max_blocks():
    actions = contract.build_default_proposed_actions()
    
    # Find youtube action (max allowed is 1)
    youtube_action = next(a for a in actions if a.platform_id == "youtube")
    over_budget_action = contract.replace(youtube_action, action_id="over_budget", requested_request_budget=5)
    
    dec = contract.build_preflight_dry_run_decision(over_budget_action)
    assert dec.decision_status == "blocked_preflight"
    assert dec.decision_strength == "deterministic_block"
    assert dec.request_budget_status == "request_budget_exceeds_limit"
    assert "request_budget_exceeds_limit" in dec.blocked_reasons


def test_retry_or_auto_retry_blocks_action():
    actions = contract.build_default_proposed_actions()
    
    # Retry count > 0 blocks
    retry_action = contract.replace(actions[0], action_id="retry_action", requested_retry_count=2)
    dec = contract.build_preflight_dry_run_decision(retry_action)
    assert dec.decision_status == "blocked_preflight"
    assert dec.decision_strength == "deterministic_block"
    assert dec.retry_status == "retry_forbidden"
    assert "retry_forbidden" in dec.blocked_reasons


def test_substack_newsletter_is_manual_export_only():
    packet = contract.build_preflight_dry_run_request_budget_packet()
    sub_action = next(a for a in packet.proposed_actions if a.platform_id == "substack_newsletter")
    sub_decision = next(d for d in packet.decisions if d.platform_id == "substack_newsletter")
    
    assert sub_action.action_kind == "newsletter_manual_export"
    assert sub_action.requested_request_budget == 0
    assert sub_decision.decision_status == "manual_export_only"
    assert sub_decision.decision_strength == "weak_manual_policy"
    assert sub_decision.request_budget_status == "request_budget_not_applicable_manual_export"
    assert sub_decision.kill_switch_status == "manual_stop_policy"


def test_telegram_remote_operator_and_channel_are_distinct():
    packet = contract.build_preflight_dry_run_request_budget_packet()
    op_dec = next(d for d in packet.decisions if d.platform_id == "telegram_remote_operator")
    ch_dec = next(d for d in packet.decisions if d.platform_id == "telegram_channel_destination")
    
    assert op_dec.decision_id != ch_dec.decision_id
    assert op_dec.action_kind != ch_dec.action_kind
    
    # Operator inbox requirements & no arbitrary DM
    assert "no_arbitrary_dm_allowed" in op_dec.blocked_reasons
    assert "operator_inbox_chat_proof_required" in op_dec.missing_proofs
    
    # Channel bot administrator checker
    assert "permission_gate_status_official_doc_supported" in ch_dec.blocked_reasons
    assert "channel_permission_proof_required" in ch_dec.missing_proofs


def test_x_decision_includes_expected_blockers():
    packet = contract.build_preflight_dry_run_request_budget_packet()
    x_dec = next(d for d in packet.decisions if d.platform_id == "x")
    
    assert "rate_limit_and_spend_gate_unresolved" in x_dec.blocked_reasons
    assert "permission_gate_status_needs_human_review" in x_dec.blocked_reasons


def test_linkedin_decision_includes_org_page_blockers():
    packet = contract.build_preflight_dry_run_request_budget_packet()
    li_dec = next(d for d in packet.decisions if d.platform_id == "linkedin")
    
    assert "linkedin_organization_page_binding_missing" in li_dec.missing_proofs


def test_meta_platforms_preserve_blockers():
    packet = contract.build_preflight_dry_run_request_budget_packet()
    for pid in ("threads", "instagram", "facebook_page"):
        dec = next(d for d in packet.decisions if d.platform_id == pid)
        assert dec.decision_status == "needs_human_review"
        assert len(dec.missing_proofs) > 0


def test_tiktok_decision_preserves_audit_blocker():
    packet = contract.build_preflight_dry_run_request_budget_packet()
    tiktok_dec = next(d for d in packet.decisions if d.platform_id == "tiktok")
    
    assert "tiktok_audit_closed" in tiktok_dec.missing_proofs


def test_youtube_decision_has_budget_1_no_stale_1600():
    packet = contract.build_preflight_dry_run_request_budget_packet()
    yt_action = next(a for a in packet.proposed_actions if a.platform_id == "youtube")
    yt_dec = next(d for d in packet.decisions if d.platform_id == "youtube")
    
    assert yt_action.requested_request_budget == 1
    assert yt_dec.readiness_cleared is False
    assert yt_dec.public_post_allowed is False
    
    # Quota upload limits (100 calls/day, 1 unit) exist without stale 1600
    assert "quota_upload_gate_closed" in yt_dec.missing_proofs
    assert "1600" not in contract.render_runbook(packet)


def test_counters_and_safety_invariants_are_zero():
    packet = contract.build_preflight_dry_run_request_budget_packet()
    
    assert packet.live_read_allowed_count == 0
    assert packet.live_write_allowed_count == 0
    assert packet.env_read_allowed_count == 0
    assert packet.credential_hydrated_count == 0
    assert packet.platform_api_called_count == 0
    assert packet.public_post_allowed_count == 0
    assert packet.readiness_cleared_count == 0
    assert packet.scheduler_enabled_count == 0
    assert packet.browser_session_used_count == 0
    
    for dec in packet.decisions:
        assert dec.live_read_allowed is False
        assert dec.live_write_allowed is False
        assert dec.env_read_allowed is False
        assert dec.credential_hydrated is False
        assert dec.platform_api_called is False
        assert dec.public_post_allowed is False
        assert dec.readiness_cleared is False
        assert dec.scheduler_enabled is False
        assert dec.browser_session_used is False


def test_u9_audit_entries_validate_cleanly():
    packet = contract.build_preflight_dry_run_request_budget_packet()
    assert len(packet.u9_audit_entry_ids) == 10
    assert all(f == "preflight_dry_run_request_budget_future" for f in packet.u9_audit_entry_families)
    
    entries = contract.build_u9_audit_entries(packet)
    chain = audit.build_ledger_chain(entries)
    validation = audit.validate_ledger_chain(chain)
    
    assert validation.validation_status == "pass"
    assert len(validation.blocked_reasons) == 0


def test_artifact_writer_enforces_directory_restriction(tmp_path):
    with pytest.raises(ValueError):
        contract.write_artifacts(repo_root=tmp_path, output_dir=tmp_path / "unauthorized_dir")


def test_unofficial_platform_action_fails_closed():
    with pytest.raises(ValueError):
        contract.ProposedPlatformAction(
            action_id="act_invalid",
            platform_id="invalid_platform",  # Not in universe
            action_kind="draft_preview",
            intended_destination_ref="ref",
            account_binding_ref="ref",
            credential_handle_ref="ref",
            payload_ref="ref",
            requested_request_budget=0,
            requested_retry_count=0,
            requested_timeout_seconds=0,
            operator_approval_ref="ref",
            kill_switch_state="closed",
            evidence_refs=(),
            action_hash="",
            action_hash_algorithm="sha256",
        )
