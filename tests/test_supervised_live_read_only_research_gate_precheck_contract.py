import pytest
import json
from pathlib import Path
from dataclasses import replace

from live_contentops import supervised_live_read_only_research_gate_precheck_contract as contract
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit
from live_contentops import supervised_live_readiness_review_index_contract as readiness


def test_packet_builds_deterministically():
    # 1. packet builds deterministically
    packet1 = contract.build_supervised_live_read_only_research_gate_precheck_packet()
    packet2 = contract.build_supervised_live_read_only_research_gate_precheck_packet()
    assert packet1.packet_id == packet2.packet_id
    assert packet1.packet_hash == packet2.packet_hash


def test_gate_and_decision_counts():
    packet = contract.build_supervised_live_read_only_research_gate_precheck_packet()
    # 2. exactly 10 proposed gates exist.
    assert len(packet.proposed_gates) == 10
    # 3. exactly 10 decisions exist.
    assert len(packet.decisions) == 10


def test_required_platforms_represented():
    packet = contract.build_supervised_live_read_only_research_gate_precheck_packet()
    # 4. all 10 required platforms are represented.
    platforms = {d.platform_id for d in packet.decisions}
    expected = {
        "x", "telegram_remote_operator", "telegram_channel_destination",
        "substack_newsletter", "linkedin", "threads", "instagram",
        "facebook_page", "tiktok", "youtube"
    }
    assert platforms == expected


def test_global_precheck_safety_invariants():
    packet = contract.build_supervised_live_read_only_research_gate_precheck_packet()
    # 5. global_live_read_only_precheck_status is blocked or not_ready, never ready.
    assert packet.global_live_read_only_precheck_status in ("blocked", "not_ready")
    assert packet.global_live_read_only_precheck_status != "ready"

    # 6. all_live_actions_blocked is true.
    assert packet.all_live_actions_blocked is True

    # 7. all live/API/env/credential/public-post/readiness/scheduler/browser counts are zero.
    assert packet.live_read_allowed_count == 0
    assert packet.live_write_allowed_count == 0
    assert packet.env_read_allowed_count == 0
    assert packet.credential_hydrated_count == 0
    assert packet.platform_api_called_count == 0
    assert packet.public_post_allowed_count == 0
    assert packet.readiness_cleared_count == 0
    assert packet.scheduler_enabled_count == 0
    assert packet.browser_session_used_count == 0

    for d in packet.decisions:
        assert d.live_read_allowed is False
        assert d.live_write_allowed is False
        assert d.env_read_allowed is False
        assert d.credential_hydrated is False
        assert d.platform_api_called is False
        assert d.public_post_allowed is False
        assert d.readiness_cleared is False
        assert d.scheduler_enabled is False
        assert d.browser_session_used is False


def test_requested_live_flags_block():
    # 8. any requested live/API/env/credential/public-post/scheduler/browser flag blocks.
    gates = contract.build_default_proposed_gates()
    # Modify X gate to request live_read
    g_x = next(g for g in gates if g.platform_id == "x")
    bad_gate = replace(g_x, live_read_requested=True)
    gates_modified = tuple(bad_gate if g.platform_id == "x" else g for g in gates)
    packet = contract.build_supervised_live_read_only_research_gate_precheck_packet(gates_modified)

    x_dec = next(d for d in packet.decisions if d.platform_id == "x")
    assert x_dec.decision_status == "blocked_precheck"
    assert "live_actions_forbidden_in_current_task" in x_dec.blocked_reasons


def test_kill_switch_open_or_missing_blocks():
    # 9. kill switch open or missing blocks API-capable platforms.
    gates = contract.build_default_proposed_gates()
    g_x = next(g for g in gates if g.platform_id == "x")
    bad_gate = replace(g_x, kill_switch_state="open")
    gates_modified = tuple(bad_gate if g.platform_id == "x" else g for g in gates)
    packet = contract.build_supervised_live_read_only_research_gate_precheck_packet(gates_modified)

    x_dec = next(d for d in packet.decisions if d.platform_id == "x")
    assert x_dec.decision_status == "blocked_precheck"
    assert x_dec.kill_switch_status == "kill_switch_open_blocks"
    assert "kill_switch_gate_open_or_missing" in x_dec.blocked_reasons


def test_endpoint_allowlist_missing_blocks():
    # 10. endpoint allowlist missing blocks.
    gates = contract.build_default_proposed_gates()
    g_x = next(g for g in gates if g.platform_id == "x")
    bad_gate = replace(g_x, endpoint_allowlist=())
    gates_modified = tuple(bad_gate if g.platform_id == "x" else g for g in gates)
    packet = contract.build_supervised_live_read_only_research_gate_precheck_packet(gates_modified)

    x_dec = next(d for d in packet.decisions if d.platform_id == "x")
    assert x_dec.decision_status == "blocked_precheck"
    assert x_dec.endpoint_allowlist_status == "allowlist_missing"
    assert "endpoint_allowlist_missing" in x_dec.blocked_reasons


def test_credential_policy_unverified():
    # 11. credential policy missing/future-required blocks or not_ready.
    packet = contract.build_supervised_live_read_only_research_gate_precheck_packet()
    x_dec = next(d for d in packet.decisions if d.platform_id == "x")
    assert x_dec.decision_status in ("blocked_precheck", "not_ready")
    assert x_dec.credential_policy_status in ("credential_handle_symbolic_only", "credential_required_future")
    assert "credential_boundary_unverified" in x_dec.blocked_reasons


def test_redaction_proof_missing():
    # 12. redaction proof missing blocks or not_ready.
    gates = contract.build_default_proposed_gates()
    g_x = next(g for g in gates if g.platform_id == "x")
    bad_gate = replace(g_x, evidence_refs=())  # missing evidence/proof
    gates_modified = tuple(bad_gate if g.platform_id == "x" else g for g in gates)
    packet = contract.build_supervised_live_read_only_research_gate_precheck_packet(gates_modified)

    x_dec = next(d for d in packet.decisions if d.platform_id == "x")
    assert x_dec.decision_status in ("blocked_precheck", "not_ready")
    assert x_dec.redaction_status == "redaction_required_missing_proof"
    assert "redaction_proof_missing" in x_dec.missing_proofs


def test_request_budget_exceeds_blocks():
    # 13. request budget exceed blocks.
    gates = contract.build_default_proposed_gates()
    g_x = next(g for g in gates if g.platform_id == "x")
    bad_gate = replace(g_x, requested_request_budget=5)  # exceeds symbolic budget of 1
    gates_modified = tuple(bad_gate if g.platform_id == "x" else g for g in gates)
    packet = contract.build_supervised_live_read_only_research_gate_precheck_packet(gates_modified)

    x_dec = next(d for d in packet.decisions if d.platform_id == "x")
    assert x_dec.decision_status == "blocked_precheck"
    assert x_dec.request_budget_status == "request_budget_exceeds_limit"
    assert "request_budget_limit_exceeded" in x_dec.blocked_reasons


def test_um_blocked_row_forces_blocked():
    # 14. 0174UM blocked row forces blocked_precheck.
    # In 0174UM, X is blocked.
    packet = contract.build_supervised_live_read_only_research_gate_precheck_packet()
    x_dec = next(d for d in packet.decisions if d.platform_id == "x")
    assert x_dec.decision_status == "blocked_precheck"
    assert "platform_readiness_blocked_in_um" in x_dec.blocked_reasons


def test_um_needs_review_forces_not_ready():
    # 15. 0174UM needs_human_review row forces not_ready.
    # In 0174UM, telegram_remote_operator status is needs_human_review.
    packet = contract.build_supervised_live_read_only_research_gate_precheck_packet()
    op_dec = next(d for d in packet.decisions if d.platform_id == "telegram_remote_operator")
    assert op_dec.decision_status == "not_ready"
    assert "platform_readiness_requires_human_review_in_um" in op_dec.blocked_reasons


def test_substack_newsletter_manual_only():
    # 16. Substack is manual_only/manual_export_no_api.
    packet = contract.build_supervised_live_read_only_research_gate_precheck_packet()
    sub_dec = next(d for d in packet.decisions if d.platform_id == "substack_newsletter")
    assert sub_dec.decision_status == "manual_only"
    assert sub_dec.endpoint_allowlist_status == "manual_no_api"
    assert sub_dec.credential_policy_status == "manual_no_credential"
    assert sub_dec.request_budget_status == "manual_no_api"
    assert sub_dec.redaction_status == "manual_no_secret"
    assert sub_dec.kill_switch_status == "manual_stop_policy"
    assert "manual_export_only" in sub_dec.blocked_reasons


def test_telegram_remote_and_channel_distinct():
    # 17. Telegram remote/channel gates are distinct.
    packet = contract.build_supervised_live_read_only_research_gate_precheck_packet()
    op_dec = next(d for d in packet.decisions if d.platform_id == "telegram_remote_operator")
    ch_dec = next(d for d in packet.decisions if d.platform_id == "telegram_channel_destination")
    assert op_dec.decision_id != ch_dec.decision_id
    assert op_dec.research_kind == "inbox_state_read"
    assert ch_dec.research_kind == "channel_state_read"


def test_telegram_operator_blockers():
    # 18. Telegram remote operator includes no arbitrary DM / operator inbox blocker.
    packet = contract.build_supervised_live_read_only_research_gate_precheck_packet()
    op_dec = next(d for d in packet.decisions if d.platform_id == "telegram_remote_operator")
    assert "no_arbitrary_dm_allowed" in op_dec.blocked_reasons
    assert "operator_inbox_proof_required" in op_dec.blocked_reasons


def test_telegram_channel_blockers():
    # 19. Telegram channel destination includes channel/admin/bot proof blocker.
    packet = contract.build_supervised_live_read_only_research_gate_precheck_packet()
    ch_dec = next(d for d in packet.decisions if d.platform_id == "telegram_channel_destination")
    assert "channel_admin_proof_required" in ch_dec.blocked_reasons
    assert "bot_permission_gap" in ch_dec.blocked_reasons
    assert "channel_state_symbolic_only" in ch_dec.blocked_reasons


def test_x_blockers():
    # 20. X includes app access/spend/rate budget blockers.
    packet = contract.build_supervised_live_read_only_research_gate_precheck_packet()
    x_dec = next(d for d in packet.decisions if d.platform_id == "x")
    assert "x_app_access_gap" in x_dec.blocked_reasons
    assert "spend_gate_unresolved" in x_dec.blocked_reasons
    assert "rate_budget_gap" in x_dec.blocked_reasons
    assert "read_only_endpoint_proof_gap" in x_dec.blocked_reasons


def test_linkedin_blockers():
    # 21. LinkedIn includes org/page proof blocker.
    packet = contract.build_supervised_live_read_only_research_gate_precheck_packet()
    li_dec = next(d for d in packet.decisions if d.platform_id == "linkedin")
    assert "linkedin_organization_page_proof_missing" in li_dec.blocked_reasons


def test_meta_blockers():
    # 22. Meta platforms preserve app review/account proof blockers.
    packet = contract.build_supervised_live_read_only_research_gate_precheck_packet()
    for pid in ("threads", "instagram", "facebook_page"):
        m_dec = next(d for d in packet.decisions if d.platform_id == pid)
        assert "meta_app_review_closed" in m_dec.blocked_reasons
        assert "meta_app_account_proof_required" in m_dec.blocked_reasons


def test_tiktok_blockers():
    # 23. TikTok preserves audit/account/video proof blocker.
    packet = contract.build_supervised_live_read_only_research_gate_precheck_packet()
    tt_dec = next(d for d in packet.decisions if d.platform_id == "tiktok")
    assert "tiktok_app_audit_closed" in tt_dec.blocked_reasons
    assert "creator_account_proof_required" in tt_dec.blocked_reasons
    assert "video_publish_proof_required" in tt_dec.blocked_reasons


def test_youtube_blockers():
    # 24. YouTube preserves OAuth/quota/upload blocker and no stale 1600.
    packet = contract.build_supervised_live_read_only_research_gate_precheck_packet()
    yt_dec = next(d for d in packet.decisions if d.platform_id == "youtube")
    assert "youtube_quota_unresolved" in yt_dec.blocked_reasons
    assert "youtube_oauth_flow_closed" in yt_dec.blocked_reasons
    assert "upload_proof_required" in yt_dec.blocked_reasons

    # Verify no mention of "1600" in the runbook content
    runbook_content = contract.render_runbook(packet)
    assert "1600" not in runbook_content


def test_future_approval_fields_present():
    # 25. future approval packet required fields are present for every non-manual platform.
    packet = contract.build_supervised_live_read_only_research_gate_precheck_packet()
    expected_fields = {
        "explicit_task_label", "platform_id", "endpoint_family", "endpoint_allowlist",
        "credential_policy", "credential_handle_key_names_only", "request_budget",
        "timeout_seconds", "redaction_policy", "secret_output_prohibition",
        "no_raw_response_logging", "kill_switch_state", "stop_conditions",
        "rollback_or_abort_policy", "evidence_packet_schema", "operator_approval_ref"
    }
    for d in packet.decisions:
        if d.platform_id != "substack_newsletter":
            assert set(d.required_future_approval_packet_fields) == expected_fields
        else:
            assert len(d.required_future_approval_packet_fields) == 0


def test_u9_ledger_integration():
    # 26. U9 family is supervised_live_read_only_research_gate_precheck_future.
    packet = contract.build_supervised_live_read_only_research_gate_precheck_packet()
    assert all(fam == "supervised_live_read_only_research_gate_precheck_future" for fam in packet.u9_audit_entry_families)
    assert len(packet.u9_audit_entry_ids) == 10

    # 27. U9 ledger chain validates and contains no secrets.
    from live_contentops import supervised_live_read_only_research_gate_precheck_contract as impl
    gates = impl.build_default_proposed_gates()
    decisions = tuple(impl.compile_decision(g) for g in gates)
    entries = impl.build_u9_audit_entries(decisions)

    chain = audit.build_ledger_chain(entries)
    validation = audit.validate_ledger_chain(chain)
    assert validation.validation_status == "pass"
    assert len(validation.blocked_reasons) == 0

    # Check for sensitive key words in JSON payload (ignoring known safe status strings)
    sensitive_keys = {"secret", "token", "password", "apikey", "credential"}
    for entry in entries:
        payload_str = json.dumps(entry.redacted_summary).lower()
        cleaned_str = payload_str.replace("credential_boundary_unverified", "").replace("credential_hydrated", "")
        for key in sensitive_keys:
            assert key not in cleaned_str or "[redacted]" in cleaned_str


def test_artifact_writer_restrictions(tmp_path):
    # 28. artifact writer touches only docs/automation/0174UN.
    # Verify that writing outside the expected relative docs folder triggers a ValueError
    with pytest.raises(ValueError) as excinfo:
        contract.write_artifacts(repo_root=tmp_path, output_dir=tmp_path / "invalid_dir")
    assert "artifact_writer_refuses_paths_outside_docs_automation_0174UN" in str(excinfo.value)
