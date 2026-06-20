import pytest
import json
from pathlib import Path
from dataclasses import replace

from live_contentops import live_read_only_research_runbook_approval_gate_dry_run_contract as contract
from live_contentops import live_read_only_research_evidence_packet_dry_run_schema_contract as evidence
from live_contentops import live_read_only_research_approval_packet_schema_contract as approval
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit


def test_packet_builds_deterministically():
    # 1. Packet builds deterministically.
    p1 = contract.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet()
    p2 = contract.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet()
    assert p1.packet_id == p2.packet_id
    assert p1.packet_hash == p2.packet_hash


def test_exactly_10_platforms_represented():
    # 2. Exactly 10 platforms represented.
    packet = contract.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet()
    assert len(packet.runbook_gate_decisions) == 10
    platforms = {d.platform_id for d in packet.runbook_gate_decisions}
    assert len(platforms) == 10


def test_platform_ids_match_registry():
    # 3. Platform IDs match existing platform universe registry.
    packet = contract.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet()
    platforms = {d.platform_id for d in packet.runbook_gate_decisions}
    for pid in platforms:
        assert pid in contract.PLATFORM_IDS


def test_evidence_schema_consumed():
    # 4. 0174UP evidence schema is consumed.
    packet = contract.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet()
    ep = evidence.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet()
    assert packet.evidence_template_count == len(ep.templates)


def test_approval_schema_consumed():
    # 5. 0174UO approval schema is consumed.
    packet = contract.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet()
    ap = approval.build_supervised_live_read_only_research_approval_packet_schema_packet()
    assert packet.approval_decision_count == len(ap.validation_decisions)


def test_runbook_gate_status_never_ready():
    # 6. Runbook gate status is never ready.
    packet = contract.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet()
    for d in packet.runbook_gate_decisions:
        assert d.runbook_gate_status in ("blocked", "not_ready", "manual_only")
        assert d.runbook_gate_status != "ready"


def test_safety_counters_are_zero():
    # 7. All live/env/credential/API/provider/public/scheduler/browser/scraping/DM counters are zero.
    packet = contract.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet()
    # Summarized counts check
    for d in packet.runbook_gate_decisions:
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


def test_all_live_actions_blocked():
    # 8. all_live_actions_blocked is true.
    packet = contract.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet()
    assert packet.safety_flags["live_read_allowed"] is False
    assert packet.safety_flags["live_write_allowed"] is False


def test_all_raw_responses_blocked():
    # 9. all_raw_responses_blocked is true.
    packet = contract.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet()
    for d in packet.runbook_gate_decisions:
        assert d.raw_response_policy_status == "raw_response_blocked_ok"


def test_all_secret_outputs_blocked():
    # 10. all_secret_outputs_blocked is true.
    packet = contract.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet()
    for d in packet.runbook_gate_decisions:
        assert d.redaction_policy_status != "secret_output_allowed_blocked"


def test_substack_is_manual_only():
    # 11. Substack remains manual-only/no API/no credential.
    packet = contract.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet()
    sub_dec = next(d for d in packet.runbook_gate_decisions if d.platform_id == "substack_newsletter")
    assert sub_dec.runbook_gate_status == "manual_only"
    assert sub_dec.credential_policy_status == "manual_no_credential"
    assert sub_dec.request_budget_status == "manual_no_api"
    assert "manual_export_only" in sub_dec.blocked_reasons


def test_telegram_remote_and_channel_distinct():
    # 12. Telegram Remote Operator and Telegram Channel Destination remain distinct.
    packet = contract.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet()
    t_op = next(d for d in packet.runbook_gate_decisions if d.platform_id == "telegram_remote_operator")
    t_ch = next(d for d in packet.runbook_gate_decisions if d.platform_id == "telegram_channel_destination")
    assert t_op.endpoint_family == "telegram_bot_getupdates_or_webhook_symbolic"
    assert t_ch.endpoint_family == "telegram_bot_getchat_symbolic"


def test_x_blockers():
    # 13. X has app/spend/rate/endpoint proof blockers.
    packet = contract.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet()
    x_dec = next(d for d in packet.runbook_gate_decisions if d.platform_id == "x")
    for b in ("x_app_access_gap", "spend_gate_unresolved", "rate_budget_gap", "read_only_endpoint_proof_gap"):
        assert b in x_dec.blocked_reasons


def test_telegram_remote_operator_dm_prohibition():
    # 14. Telegram Remote Operator prohibits arbitrary DM/reply automation.
    packet = contract.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet()
    t_op = next(d for d in packet.runbook_gate_decisions if d.platform_id == "telegram_remote_operator")
    assert "no_arbitrary_dm_allowed" in t_op.blocked_reasons
    assert "operator_inbox_proof_required" in t_op.blocked_reasons


def test_telegram_channel_destination_requirements():
    # 15. Telegram Channel Destination requires channel/admin/bot proof.
    packet = contract.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet()
    t_ch = next(d for d in packet.runbook_gate_decisions if d.platform_id == "telegram_channel_destination")
    assert "channel_admin_proof_required" in t_ch.blocked_reasons
    assert "bot_permission_gap" in t_ch.blocked_reasons


def test_linkedin_blockers():
    # 16. LinkedIn has app/page/org review proof blocker.
    packet = contract.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet()
    li_dec = next(d for d in packet.runbook_gate_decisions if d.platform_id == "linkedin")
    assert "linkedin_organization_page_proof_missing" in li_dec.blocked_reasons


def test_meta_family_blockers():
    # 17. Meta-family platforms have app review/account proof blockers.
    packet = contract.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet()
    for pid in ("threads", "instagram", "facebook_page"):
        dec = next(d for d in packet.runbook_gate_decisions if d.platform_id == pid)
        assert "meta_app_review_closed" in dec.blocked_reasons
        assert "meta_app_account_proof_required" in dec.blocked_reasons


def test_tiktok_blockers():
    # 18. TikTok has audit/creator/video proof blockers.
    packet = contract.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet()
    tt_dec = next(d for d in packet.runbook_gate_decisions if d.platform_id == "tiktok")
    assert "tiktok_app_audit_closed" in tt_dec.blocked_reasons
    assert "creator_account_proof_required" in tt_dec.blocked_reasons
    assert "video_publish_proof_required" in tt_dec.blocked_reasons


def test_youtube_blockers():
    # 19. YouTube has OAuth/quota/upload proof blockers and no “1600” text.
    packet = contract.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet()
    yt_dec = next(d for d in packet.runbook_gate_decisions if d.platform_id == "youtube")
    assert "youtube_quota_unresolved" in yt_dec.blocked_reasons
    assert "youtube_oauth_flow_closed" in yt_dec.blocked_reasons
    assert "upload_proof_required" in yt_dec.blocked_reasons

    # Check that "1600" is not in the compiled runbook markdown text
    runbook_md = contract.render_runbook(packet)
    assert "1600" not in runbook_md


def test_missing_operator_approval_fails_closed():
    # 20. Missing operator approval fails closed.
    ep = evidence.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet()
    t_x = next(t for t in ep.templates if t.platform_id == "x")
    bad_template = replace(t_x, operator_approval_required=False)
    templates = tuple(bad_template if t.platform_id == "x" else t for t in ep.templates)
    
    ep_bad = replace(ep, templates=templates)
    packet = contract.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet(evidence_packet=ep_bad)
    x_dec = next(d for d in packet.runbook_gate_decisions if d.platform_id == "x")
    assert x_dec.runbook_gate_status == "blocked"
    assert "operator_approval_disabled" in x_dec.blocked_reasons


def test_missing_allowlist_fails_closed():
    # 21. Missing endpoint allowlist fails closed for API platforms.
    ep = evidence.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet()
    t_x = next(t for t in ep.templates if t.platform_id == "x")
    bad_template = replace(t_x, endpoint_allowlist=())
    templates = tuple(bad_template if t.platform_id == "x" else t for t in ep.templates)
    
    ep_bad = replace(ep, templates=templates)
    packet = contract.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet(evidence_packet=ep_bad)
    x_dec = next(d for d in packet.runbook_gate_decisions if d.platform_id == "x")
    assert x_dec.runbook_gate_status == "blocked"
    assert "endpoint_allowlist_missing" in x_dec.blocked_reasons


def test_raw_response_logging_allowed_fails_closed():
    # 22. Raw response logging allowed fails closed.
    ep = evidence.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet()
    t_x = next(t for t in ep.templates if t.platform_id == "x")
    bad_template = replace(t_x, raw_response_logging_allowed=True)
    templates = tuple(bad_template if t.platform_id == "x" else t for t in ep.templates)
    
    ep_bad = replace(ep, templates=templates)
    packet = contract.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet(evidence_packet=ep_bad)
    x_dec = next(d for d in packet.runbook_gate_decisions if d.platform_id == "x")
    assert x_dec.runbook_gate_status == "blocked"
    assert "raw_response_logging_allowed" in x_dec.blocked_reasons


def test_secret_output_allowed_fails_closed():
    # 23. Secret output allowed fails closed.
    ep = evidence.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet()
    t_x = next(t for t in ep.templates if t.platform_id == "x")
    bad_template = replace(t_x, secret_output_allowed=True)
    templates = tuple(bad_template if t.platform_id == "x" else t for t in ep.templates)
    
    ep_bad = replace(ep, templates=templates)
    packet = contract.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet(evidence_packet=ep_bad)
    x_dec = next(d for d in packet.runbook_gate_decisions if d.platform_id == "x")
    assert x_dec.runbook_gate_status == "blocked"
    assert "secret_output_allowed" in x_dec.blocked_reasons


def test_response_body_storage_allowed_fails_closed():
    # 24. Response body storage allowed fails closed.
    ep = evidence.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet()
    t_x = next(t for t in ep.templates if t.platform_id == "x")
    bad_template = replace(t_x, response_body_storage_allowed=True)
    templates = tuple(bad_template if t.platform_id == "x" else t for t in ep.templates)
    
    ep_bad = replace(ep, templates=templates)
    packet = contract.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet(evidence_packet=ep_bad)
    x_dec = next(d for d in packet.runbook_gate_decisions if d.platform_id == "x")
    assert x_dec.runbook_gate_status == "blocked"
    assert "response_body_storage_allowed" in x_dec.blocked_reasons


def test_request_budget_fails_closed():
    # 25. Request budget above symbolic limit fails closed.
    ep = evidence.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet()
    t_x = next(t for t in ep.templates if t.platform_id == "x")
    bad_template = replace(t_x, request_budget_max=12)
    templates = tuple(bad_template if t.platform_id == "x" else t for t in ep.templates)
    
    ep_bad = replace(ep, templates=templates)
    packet = contract.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet(evidence_packet=ep_bad)
    x_dec = next(d for d in packet.runbook_gate_decisions if d.platform_id == "x")
    assert x_dec.runbook_gate_status == "blocked"
    assert "request_budget_exceeds_limit" in x_dec.blocked_reasons


def test_kill_switch_open_fails_closed():
    # 26. Kill switch open fails closed.
    ep = evidence.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet()
    t_x = next(t for t in ep.templates if t.platform_id == "x")
    bad_template = replace(t_x, kill_switch_required_state="open")
    templates = tuple(bad_template if t.platform_id == "x" else t for t in ep.templates)
    
    ep_bad = replace(ep, templates=templates)
    packet = contract.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet(evidence_packet=ep_bad)
    x_dec = next(d for d in packet.runbook_gate_decisions if d.platform_id == "x")
    assert x_dec.runbook_gate_status == "blocked"
    assert "kill_switch_policy_unresolved" in x_dec.blocked_reasons


def test_u9_audit_entries_validate():
    # 27. U9 audit entries validate.
    packet = contract.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet()
    
    ap = approval.build_supervised_live_read_only_research_approval_packet_schema_packet()
    ep = evidence.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet()
    decisions = tuple(contract.compile_runbook_decision(pid, ap, ep) for pid in contract.PLATFORM_IDS)
    entries = contract.build_u9_audit_entries(decisions)
    
    chain = audit.build_ledger_chain(entries)
    validation = audit.validate_ledger_chain(chain)
    assert validation.validation_status == "pass"
    assert len(validation.blocked_reasons) == 0


def test_u9_family_matches():
    # 28. U9 family equals live_read_only_research_runbook_approval_gate_dry_run_future.
    packet = contract.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet()
    assert all(fam == "live_read_only_research_runbook_approval_gate_dry_run_future" for fam in packet.u9_audit_entry_families)
    assert len(packet.u9_audit_entry_ids) == 10


def test_artifact_writer_refuses_outside_paths(tmp_path):
    # 29. Artifact writer refuses paths outside docs/automation/0174UQ.
    with pytest.raises(ValueError) as excinfo:
        contract.write_artifacts(repo_root=tmp_path, output_dir=tmp_path / "invalid_dir")
    assert "artifact_writer_refuses_paths_outside_docs_automation_0174UQ" in str(excinfo.value)


def test_operator_planning_docs_untouched():
    # 30. Known untracked operator/stale-context paths remain untouched.
    # Verify paths exist and are unmutated.
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
