import pytest
import json
from pathlib import Path
from dataclasses import replace

from live_contentops import live_read_only_research_approval_packet_schema_contract as contract
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit


def test_packet_builds_deterministically():
    # 1. packet builds deterministically.
    p1 = contract.build_supervised_live_read_only_research_approval_packet_schema_packet()
    p2 = contract.build_supervised_live_read_only_research_approval_packet_schema_packet()
    assert p1.packet_id == p2.packet_id
    assert p1.packet_hash == p2.packet_hash


def test_required_schema_fields_exist():
    # 2. all required schema fields exist.
    packet = contract.build_supervised_live_read_only_research_approval_packet_schema_packet()
    field_names = {f.field_name for f in packet.schema_fields}
    for field in contract.REQUIRED_16_FIELDS:
        assert field in field_names


def test_non_manual_templates_contain_16_fields():
    # 3. every non-manual platform template contains the 16 required future approval fields.
    packet = contract.build_supervised_live_read_only_research_approval_packet_schema_packet()
    for t in packet.templates:
        if t.platform_id != "substack_newsletter":
            for field in contract.REQUIRED_16_FIELDS:
                assert field in t.required_fields


def test_additional_boundary_fields_exist():
    # 4. additional boundary fields exist.
    packet = contract.build_supervised_live_read_only_research_approval_packet_schema_packet()
    field_names = {f.field_name for f in packet.schema_fields}
    for field in contract.BOUNDARY_4_FIELDS:
        assert field in field_names


def test_template_and_decision_counts_and_platforms():
    packet = contract.build_supervised_live_read_only_research_approval_packet_schema_packet()
    # 5. exactly 10 templates exist.
    assert len(packet.templates) == 10
    # 6. exactly 10 validation decisions exist.
    assert len(packet.validation_decisions) == 10
    # 7. all 10 required platforms are represented.
    platforms = {d.platform_id for d in packet.validation_decisions}
    expected = {
        "x", "telegram_remote_operator", "telegram_channel_destination",
        "substack_newsletter", "linkedin", "threads", "instagram",
        "facebook_page", "tiktok", "youtube"
    }
    assert platforms == expected


def test_global_schema_safety_invariants():
    packet = contract.build_supervised_live_read_only_research_approval_packet_schema_packet()
    # 8. global_schema_status is blocked/not_ready/schema_only, never ready.
    assert packet.global_schema_status in ("blocked", "not_ready", "schema_only")
    assert packet.global_schema_status != "ready"

    # 9. all_live_actions_blocked is true.
    assert packet.all_live_actions_blocked is True

    # 10. all live/API/env/credential/public-post/readiness/scheduler/browser counts are zero.
    assert packet.live_read_allowed_count == 0
    assert packet.live_write_allowed_count == 0
    assert packet.env_read_allowed_count == 0
    assert packet.credential_hydrated_count == 0
    assert packet.platform_api_called_count == 0
    assert packet.public_post_allowed_count == 0
    assert packet.readiness_cleared_count == 0
    assert packet.scheduler_enabled_count == 0
    assert packet.browser_session_used_count == 0

    for d in packet.validation_decisions:
        assert d.live_read_allowed is False
        assert d.live_write_allowed is False
        assert d.env_read_allowed is False
        assert d.credential_hydrated is False
        assert d.platform_api_called is False
        assert d.public_post_allowed is False
        assert d.readiness_cleared is False
        assert d.scheduler_enabled is False
        assert d.browser_session_used is False


def test_forbidden_live_capabilities_fail_validation():
    # 11. any template with forbidden live/write/env/credential/API/public-post/scheduler/browser/readiness true fails validation.
    templates = contract.build_default_templates()
    t_x = next(t for t in templates if t.platform_id == "x")
    bad_template = replace(t_x, live_write_allowed_by_schema=True)
    templates_modified = tuple(bad_template if t.platform_id == "x" else t for t in templates)
    packet = contract.build_supervised_live_read_only_research_approval_packet_schema_packet(templates_modified)

    x_dec = next(d for d in packet.validation_decisions if d.platform_id == "x")
    assert x_dec.validation_status == "schema_blocked"
    assert x_dec.validation_strength == "forbidden_live_capability"
    assert "forbidden_live_capability_requested" in x_dec.blocked_reasons


def test_missing_required_field_fails_validation():
    # 12. missing required field fails validation.
    templates = contract.build_default_templates()
    t_x = next(t for t in templates if t.platform_id == "x")
    bad_template = replace(t_x, required_fields=tuple(f for f in t_x.required_fields if f != "explicit_task_label"))
    templates_modified = tuple(bad_template if t.platform_id == "x" else t for t in templates)
    packet = contract.build_supervised_live_read_only_research_approval_packet_schema_packet(templates_modified)

    x_dec = next(d for d in packet.validation_decisions if d.platform_id == "x")
    assert x_dec.validation_status == "schema_blocked"
    assert x_dec.validation_strength == "missing_required_field"
    assert "missing_required_field_explicit_task_label" in x_dec.blocked_reasons


def test_endpoint_allowlist_missing_fails_validation():
    # 13. endpoint allowlist missing fails validation.
    templates = contract.build_default_templates()
    t_x = next(t for t in templates if t.platform_id == "x")
    bad_template = replace(t_x, endpoint_allowlist=())
    templates_modified = tuple(bad_template if t.platform_id == "x" else t for t in templates)
    packet = contract.build_supervised_live_read_only_research_approval_packet_schema_packet(templates_modified)

    x_dec = next(d for d in packet.validation_decisions if d.platform_id == "x")
    assert x_dec.validation_status == "schema_blocked"
    assert x_dec.endpoint_allowlist_status == "allowlist_missing"
    assert "endpoint_allowlist_missing" in x_dec.blocked_reasons


def test_credential_key_names_must_be_names_only():
    # 14. credential key names must be names only, not values.
    templates = contract.build_default_templates()
    t_x = next(t for t in templates if t.platform_id == "x")
    bad_template = replace(t_x, credential_handle_key_names_only=False)
    templates_modified = tuple(bad_template if t.platform_id == "x" else t for t in templates)
    packet = contract.build_supervised_live_read_only_research_approval_packet_schema_packet(templates_modified)

    x_dec = next(d for d in packet.validation_decisions if d.platform_id == "x")
    assert x_dec.validation_status == "schema_blocked"
    assert x_dec.credential_policy_status == "credential_values_exposed"
    assert "credential_values_exposed" in x_dec.blocked_reasons


def test_redaction_policy_missing_fails_validation():
    # 15. redaction policy missing fails validation.
    templates = contract.build_default_templates()
    t_x = next(t for t in templates if t.platform_id == "x")
    bad_template = replace(t_x, redaction_policy_ref="")
    templates_modified = tuple(bad_template if t.platform_id == "x" else t for t in templates)
    packet = contract.build_supervised_live_read_only_research_approval_packet_schema_packet(templates_modified)

    x_dec = next(d for d in packet.validation_decisions if d.platform_id == "x")
    assert x_dec.validation_status == "schema_blocked"
    assert x_dec.redaction_policy_status == "redaction_policy_missing"
    assert "redaction_policy_missing" in x_dec.blocked_reasons


def test_raw_response_logging_prohibited():
    # 16. no_raw_response_logging must be true.
    templates = contract.build_default_templates()
    t_x = next(t for t in templates if t.platform_id == "x")
    bad_template = replace(t_x, no_raw_response_logging=False)
    templates_modified = tuple(bad_template if t.platform_id == "x" else t for t in templates)
    packet = contract.build_supervised_live_read_only_research_approval_packet_schema_packet(templates_modified)

    x_dec = next(d for d in packet.validation_decisions if d.platform_id == "x")
    assert x_dec.validation_status == "schema_blocked"
    assert "no_raw_response_logging_disabled" in x_dec.blocked_reasons


def test_secret_output_prohibited():
    # 17. secret_output_prohibition must be true.
    templates = contract.build_default_templates()
    t_x = next(t for t in templates if t.platform_id == "x")
    bad_template = replace(t_x, secret_output_prohibition=False)
    templates_modified = tuple(bad_template if t.platform_id == "x" else t for t in templates)
    packet = contract.build_supervised_live_read_only_research_approval_packet_schema_packet(templates_modified)

    x_dec = next(d for d in packet.validation_decisions if d.platform_id == "x")
    assert x_dec.validation_status == "schema_blocked"
    assert "secret_output_prohibition_disabled" in x_dec.blocked_reasons


def test_kill_switch_state_must_be_closed():
    # 18. kill_switch_required_state must be closed.
    templates = contract.build_default_templates()
    t_x = next(t for t in templates if t.platform_id == "x")
    bad_template = replace(t_x, kill_switch_required_state="open")
    templates_modified = tuple(bad_template if t.platform_id == "x" else t for t in templates)
    packet = contract.build_supervised_live_read_only_research_approval_packet_schema_packet(templates_modified)

    x_dec = next(d for d in packet.validation_decisions if d.platform_id == "x")
    assert x_dec.validation_status == "schema_blocked"
    assert x_dec.kill_switch_policy_status == "kill_switch_policy_unresolved"
    assert "kill_switch_policy_unresolved" in x_dec.blocked_reasons


def test_request_budget_exceeds_fails_validation():
    # 19. request budget above symbolic max fails validation.
    templates = contract.build_default_templates()
    t_x = next(t for t in templates if t.platform_id == "x")
    bad_template = replace(t_x, request_budget_max=10)
    templates_modified = tuple(bad_template if t.platform_id == "x" else t for t in templates)
    packet = contract.build_supervised_live_read_only_research_approval_packet_schema_packet(templates_modified)

    x_dec = next(d for d in packet.validation_decisions if d.platform_id == "x")
    assert x_dec.validation_status == "schema_blocked"
    assert x_dec.request_budget_status == "request_budget_exceeds_limit"
    assert "request_budget_exceeds_limit" in x_dec.blocked_reasons


def test_x_blockers_and_proofs():
    # 20. X template contains app access/spend/rate budget proof requirements.
    packet = contract.build_supervised_live_read_only_research_approval_packet_schema_packet()
    x_dec = next(d for d in packet.validation_decisions if d.platform_id == "x")
    assert "x_app_access_gap" in x_dec.blocked_reasons
    assert "spend_gate_unresolved" in x_dec.blocked_reasons
    assert "rate_budget_gap" in x_dec.blocked_reasons
    assert "read_only_endpoint_proof_gap" in x_dec.blocked_reasons


def test_telegram_remote_and_channel_templates_distinct():
    # 21. Telegram remote/channel templates are distinct.
    packet = contract.build_supervised_live_read_only_research_approval_packet_schema_packet()
    t_op = next(t for t in packet.templates if t.platform_id == "telegram_remote_operator")
    t_ch = next(t for t in packet.templates if t.platform_id == "telegram_channel_destination")
    assert t_op.template_id != t_ch.template_id
    assert t_op.endpoint_family == "telegram_bot_getupdates_or_webhook_symbolic"
    assert t_ch.endpoint_family == "telegram_bot_getchat_symbolic"


def test_telegram_operator_blockers():
    # 22. Telegram remote operator prohibits arbitrary DM/reply automation.
    packet = contract.build_supervised_live_read_only_research_approval_packet_schema_packet()
    op_dec = next(d for d in packet.validation_decisions if d.platform_id == "telegram_remote_operator")
    assert "no_arbitrary_dm_allowed" in op_dec.blocked_reasons
    assert "operator_inbox_proof_required" in op_dec.blocked_reasons


def test_telegram_channel_blockers():
    # 23. Telegram channel destination requires channel/admin/bot proof.
    packet = contract.build_supervised_live_read_only_research_approval_packet_schema_packet()
    ch_dec = next(d for d in packet.validation_decisions if d.platform_id == "telegram_channel_destination")
    assert "channel_admin_proof_required" in ch_dec.blocked_reasons
    assert "bot_permission_gap" in ch_dec.blocked_reasons
    assert "channel_state_symbolic_only" in ch_dec.blocked_reasons


def test_substack_is_manual_only():
    # 24. Substack is manual_only and has no API request budget or credential hydration.
    packet = contract.build_supervised_live_read_only_research_approval_packet_schema_packet()
    sub_dec = next(d for d in packet.validation_decisions if d.platform_id == "substack_newsletter")
    assert sub_dec.validation_status == "manual_only"
    assert sub_dec.endpoint_allowlist_status == "manual_no_api"
    assert sub_dec.credential_policy_status == "manual_no_credential"
    assert sub_dec.request_budget_status == "manual_no_api"
    assert sub_dec.redaction_policy_status == "manual_no_secret"
    assert sub_dec.kill_switch_policy_status == "manual_stop_policy"
    assert "manual_export_only" in sub_dec.blocked_reasons


def test_linkedin_blockers():
    # 25. LinkedIn contains org/page proof requirements.
    packet = contract.build_supervised_live_read_only_research_approval_packet_schema_packet()
    li_dec = next(d for d in packet.validation_decisions if d.platform_id == "linkedin")
    assert "linkedin_organization_page_proof_missing" in li_dec.blocked_reasons


def test_meta_blockers():
    # 26. Meta templates contain app review/account proof requirements.
    packet = contract.build_supervised_live_read_only_research_approval_packet_schema_packet()
    for pid in ("threads", "instagram", "facebook_page"):
        m_dec = next(d for d in packet.validation_decisions if d.platform_id == pid)
        assert "meta_app_review_closed" in m_dec.blocked_reasons
        assert "meta_app_account_proof_required" in m_dec.blocked_reasons


def test_tiktok_blockers():
    # 27. TikTok contains app audit/creator/video proof requirements.
    packet = contract.build_supervised_live_read_only_research_approval_packet_schema_packet()
    tt_dec = next(d for d in packet.validation_decisions if d.platform_id == "tiktok")
    assert "tiktok_app_audit_closed" in tt_dec.blocked_reasons
    assert "creator_account_proof_required" in tt_dec.blocked_reasons
    assert "video_publish_proof_required" in tt_dec.blocked_reasons


def test_youtube_blockers():
    # 28. YouTube contains OAuth/quota/channel proof requirements and no stale 1600.
    packet = contract.build_supervised_live_read_only_research_approval_packet_schema_packet()
    yt_dec = next(d for d in packet.validation_decisions if d.platform_id == "youtube")
    assert "youtube_quota_unresolved" in yt_dec.blocked_reasons
    assert "youtube_oauth_flow_closed" in yt_dec.blocked_reasons
    assert "upload_proof_required" in yt_dec.blocked_reasons

    # Verify no mention of "1600" in the runbook content
    runbook_content = contract.render_runbook(packet)
    assert "1600" not in runbook_content


def test_u9_ledger_integration():
    # 29. U9 family is live_read_only_research_approval_packet_schema_future.
    packet = contract.build_supervised_live_read_only_research_approval_packet_schema_packet()
    assert all(fam == "live_read_only_research_approval_packet_schema_future" for fam in packet.u9_audit_entry_families)
    assert len(packet.u9_audit_entry_ids) == 10

    # 30. U9 ledger chain validates and contains no secrets.
    from live_contentops import live_read_only_research_approval_packet_schema_contract as impl
    templates = impl.build_default_templates()
    decisions = tuple(impl.compile_decision(t) for t in templates)
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
    # 31. artifact writer touches only docs/automation/0174UO.
    with pytest.raises(ValueError) as excinfo:
        contract.write_artifacts(repo_root=tmp_path, output_dir=tmp_path / "invalid_dir")
    assert "artifact_writer_refuses_paths_outside_docs_automation_0174UO" in str(excinfo.value)
