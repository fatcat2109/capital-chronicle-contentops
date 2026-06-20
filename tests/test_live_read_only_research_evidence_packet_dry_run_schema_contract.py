import pytest
import json
from pathlib import Path
from dataclasses import replace

from live_contentops import live_read_only_research_evidence_packet_dry_run_schema_contract as contract
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit


def test_packet_builds_deterministically():
    # 1. packet builds deterministically.
    p1 = contract.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet()
    p2 = contract.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet()
    assert p1.packet_id == p2.packet_id
    assert p1.packet_hash == p2.packet_hash


def test_required_schema_fields_exist():
    # 2. all required schema fields exist.
    packet = contract.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet()
    field_names = {f.field_name for f in packet.schema_fields}
    for field in contract.ALL_FIELD_KINDS:
        assert field in field_names


def test_counts_and_platforms():
    packet = contract.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet()
    # 3. exactly 10 templates exist.
    assert len(packet.templates) == 10
    # 4. exactly 10 validation decisions exist.
    assert len(packet.validation_decisions) == 10
    # 5. all 10 required platforms are represented.
    platforms = {d.platform_id for d in packet.validation_decisions}
    expected = {
        "x", "telegram_remote_operator", "telegram_channel_destination",
        "substack_newsletter", "linkedin", "threads", "instagram",
        "facebook_page", "tiktok", "youtube"
    }
    assert platforms == expected


def test_global_schema_safety_invariants():
    packet = contract.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet()
    # 6. global_evidence_schema_status is blocked/not_ready/schema_only, never ready.
    assert packet.global_evidence_schema_status in ("blocked", "not_ready", "schema_only")
    assert packet.global_evidence_schema_status != "ready"

    # 7. all_live_actions_blocked is true.
    assert packet.all_live_actions_blocked is True

    # 8. all_raw_responses_blocked is true.
    assert packet.all_raw_responses_blocked is True

    # 9. all_secret_outputs_blocked is true.
    assert packet.all_secret_outputs_blocked is True

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

    # 11. raw_response_logging_allowed_count is zero.
    assert packet.raw_response_logging_allowed_count == 0
    # 12. secret_output_allowed_count is zero.
    assert packet.secret_output_allowed_count == 0
    # 13. response_body_storage_allowed_count is zero.
    assert packet.response_body_storage_allowed_count == 0

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


def test_missing_field_fails_validation():
    # 14. missing required evidence field fails validation.
    templates = contract.build_default_templates()
    t_x = next(t for t in templates if t.platform_id == "x")
    bad_template = replace(t_x, required_fields=tuple(f for f in t_x.required_fields if f != "task_identity"))
    templates_modified = tuple(bad_template if t.platform_id == "x" else t for t in templates)
    packet = contract.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet(templates_modified)

    x_dec = next(d for d in packet.validation_decisions if d.platform_id == "x")
    assert x_dec.validation_status == "dry_run_schema_blocked"
    assert x_dec.validation_strength == "missing_required_field"
    assert "missing_required_field_task_identity" in x_dec.blocked_reasons


def test_raw_response_logging_allowed_fails_validation():
    # 15. allowing raw response logging fails validation.
    templates = contract.build_default_templates()
    t_x = next(t for t in templates if t.platform_id == "x")
    bad_template = replace(t_x, raw_response_logging_allowed=True)
    templates_modified = tuple(bad_template if t.platform_id == "x" else t for t in templates)
    packet = contract.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet(templates_modified)

    x_dec = next(d for d in packet.validation_decisions if d.platform_id == "x")
    assert x_dec.validation_status == "dry_run_schema_blocked"
    assert x_dec.validation_strength == "forbidden_raw_response"
    assert "raw_response_logging_allowed" in x_dec.blocked_reasons


def test_secret_output_allowed_fails_validation():
    # 16. allowing secret output fails validation.
    templates = contract.build_default_templates()
    t_x = next(t for t in templates if t.platform_id == "x")
    bad_template = replace(t_x, secret_output_allowed=True)
    templates_modified = tuple(bad_template if t.platform_id == "x" else t for t in templates)
    packet = contract.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet(templates_modified)

    x_dec = next(d for d in packet.validation_decisions if d.platform_id == "x")
    assert x_dec.validation_status == "dry_run_schema_blocked"
    assert x_dec.validation_strength == "forbidden_secret_output"
    assert "secret_output_allowed" in x_dec.blocked_reasons


def test_response_body_storage_allowed_fails_validation():
    # 17. allowing response body storage fails validation.
    templates = contract.build_default_templates()
    t_x = next(t for t in templates if t.platform_id == "x")
    bad_template = replace(t_x, response_body_storage_allowed=True)
    templates_modified = tuple(bad_template if t.platform_id == "x" else t for t in templates)
    packet = contract.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet(templates_modified)

    x_dec = next(d for d in packet.validation_decisions if d.platform_id == "x")
    assert x_dec.validation_status == "dry_run_schema_blocked"
    assert x_dec.validation_strength == "forbidden_raw_response"
    assert "response_body_storage_allowed" in x_dec.blocked_reasons


def test_live_capabilities_allowed_fails_validation():
    # 18. allowing live/API/env/credential/public-post/scheduler/browser/readiness flags fails validation.
    templates = contract.build_default_templates()
    t_x = next(t for t in templates if t.platform_id == "x")
    bad_template = replace(t_x, live_write_allowed_by_schema=True)
    templates_modified = tuple(bad_template if t.platform_id == "x" else t for t in templates)
    packet = contract.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet(templates_modified)

    x_dec = next(d for d in packet.validation_decisions if d.platform_id == "x")
    assert x_dec.validation_status == "dry_run_schema_blocked"
    assert x_dec.validation_strength == "forbidden_live_capability"
    assert "forbidden_live_capability_requested" in x_dec.blocked_reasons


def test_credential_policy_key_names_only():
    # 19. credential policy must be key names only, not values.
    templates = contract.build_default_templates()
    t_x = next(t for t in templates if t.platform_id == "x")
    bad_template = replace(t_x, credential_key_names_only_required=False)
    templates_modified = tuple(bad_template if t.platform_id == "x" else t for t in templates)
    packet = contract.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet(templates_modified)

    x_dec = next(d for d in packet.validation_decisions if d.platform_id == "x")
    assert x_dec.validation_status == "dry_run_schema_blocked"
    assert x_dec.credential_policy_status == "credential_values_exposed"
    assert "credential_values_exposed" in x_dec.blocked_reasons


def test_evidence_artifact_hash_required():
    # 20. evidence artifact hash required.
    templates = contract.build_default_templates()
    t_x = next(t for t in templates if t.platform_id == "x")
    bad_template = replace(t_x, evidence_artifact_hash_required=False)
    templates_modified = tuple(bad_template if t.platform_id == "x" else t for t in templates)
    packet = contract.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet(templates_modified)

    x_dec = next(d for d in packet.validation_decisions if d.platform_id == "x")
    assert x_dec.validation_status == "dry_run_schema_blocked"
    assert x_dec.artifact_hash_policy_status == "artifact_hash_missing_blocked"
    assert "artifact_hash_missing" in x_dec.blocked_reasons


def test_source_payload_hash_required():
    # 21. source payload hash required.
    templates = contract.build_default_templates()
    t_x = next(t for t in templates if t.platform_id == "x")
    bad_template = replace(t_x, source_payload_hash_required=False)
    templates_modified = tuple(bad_template if t.platform_id == "x" else t for t in templates)
    packet = contract.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet(templates_modified)

    x_dec = next(d for d in packet.validation_decisions if d.platform_id == "x")
    assert x_dec.validation_status == "dry_run_schema_blocked"
    assert x_dec.artifact_hash_policy_status == "artifact_hash_missing_blocked"
    assert "artifact_hash_missing" in x_dec.blocked_reasons


def test_response_status_classification():
    # 22. response status stored only as classification.
    templates = contract.build_default_templates()
    t_x = next(t for t in templates if t.platform_id == "x")
    bad_template = replace(t_x, status_code_storage_policy="raw_status_code")
    templates_modified = tuple(bad_template if t.platform_id == "x" else t for t in templates)
    packet = contract.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet(templates_modified)

    x_dec = next(d for d in packet.validation_decisions if d.platform_id == "x")
    assert x_dec.validation_status == "dry_run_schema_blocked"
    assert x_dec.response_storage_policy_status == "response_body_storage_allowed_blocked"


def test_response_shape_classification():
    # 23. response shape stored only as classification/hash.
    templates = contract.build_default_templates()
    t_x = next(t for t in templates if t.platform_id == "x")
    bad_template = replace(t_x, response_shape_storage_policy="raw_response_body")
    templates_modified = tuple(bad_template if t.platform_id == "x" else t for t in templates)
    packet = contract.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet(templates_modified)

    x_dec = next(d for d in packet.validation_decisions if d.platform_id == "x")
    assert x_dec.validation_status == "dry_run_schema_blocked"
    assert x_dec.response_storage_policy_status == "response_body_storage_allowed_blocked"


def test_request_budget_exceed_fails():
    # 24. request budget exceed fails validation.
    templates = contract.build_default_templates()
    t_x = next(t for t in templates if t.platform_id == "x")
    bad_template = replace(t_x, request_budget_max=15)
    templates_modified = tuple(bad_template if t.platform_id == "x" else t for t in templates)
    packet = contract.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet(templates_modified)

    x_dec = next(d for d in packet.validation_decisions if d.platform_id == "x")
    assert x_dec.validation_status == "dry_run_schema_blocked"
    assert x_dec.request_budget_status == "request_budget_exceeds_limit"


def test_kill_switch_state_closed():
    # 25. kill switch required state must be closed.
    templates = contract.build_default_templates()
    t_x = next(t for t in templates if t.platform_id == "x")
    bad_template = replace(t_x, kill_switch_required_state="open")
    templates_modified = tuple(bad_template if t.platform_id == "x" else t for t in templates)
    packet = contract.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet(templates_modified)

    x_dec = next(d for d in packet.validation_decisions if d.platform_id == "x")
    assert x_dec.validation_status == "dry_run_schema_blocked"
    assert x_dec.kill_switch_policy_status == "kill_switch_policy_unresolved"


def test_operator_approval_required():
    # 26. operator approval required.
    templates = contract.build_default_templates()
    t_x = next(t for t in templates if t.platform_id == "x")
    bad_template = replace(t_x, operator_approval_required=False)
    templates_modified = tuple(bad_template if t.platform_id == "x" else t for t in templates)
    packet = contract.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet(templates_modified)

    x_dec = next(d for d in packet.validation_decisions if d.platform_id == "x")
    assert x_dec.validation_status == "dry_run_schema_blocked"
    assert x_dec.operator_approval_status == "operator_approval_disabled"


def test_x_blockers():
    # 27. X template contains app access/spend/rate budget proof requirements.
    packet = contract.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet()
    x_dec = next(d for d in packet.validation_decisions if d.platform_id == "x")
    assert "x_app_access_gap" in x_dec.blocked_reasons
    assert "spend_gate_unresolved" in x_dec.blocked_reasons
    assert "rate_budget_gap" in x_dec.blocked_reasons
    assert "read_only_endpoint_proof_gap" in x_dec.blocked_reasons


def test_telegram_remote_operator_and_channel_templates_distinct():
    # 28. Telegram remote/channel templates are distinct.
    packet = contract.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet()
    t_op = next(t for t in packet.templates if t.platform_id == "telegram_remote_operator")
    t_ch = next(t for t in packet.templates if t.platform_id == "telegram_channel_destination")
    assert t_op.template_id != t_ch.template_id
    assert t_op.endpoint_family == "telegram_bot_getupdates_or_webhook_symbolic"
    assert t_ch.endpoint_family == "telegram_bot_getchat_symbolic"


def test_telegram_operator_blockers():
    # 29. Telegram remote operator prohibits arbitrary DM/reply automation.
    packet = contract.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet()
    op_dec = next(d for d in packet.validation_decisions if d.platform_id == "telegram_remote_operator")
    assert "no_arbitrary_dm_allowed" in op_dec.blocked_reasons
    assert "operator_inbox_proof_required" in op_dec.blocked_reasons


def test_telegram_channel_blockers():
    # 30. Telegram channel destination requires channel/admin/bot proof.
    packet = contract.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet()
    ch_dec = next(d for d in packet.validation_decisions if d.platform_id == "telegram_channel_destination")
    assert "channel_admin_proof_required" in ch_dec.blocked_reasons
    assert "bot_permission_gap" in ch_dec.blocked_reasons
    assert "channel_state_symbolic_only" in ch_dec.blocked_reasons


def test_substack_is_manual_only():
    # 31. Substack is manual_only and has no API request budget or credential hydration.
    packet = contract.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet()
    sub_dec = next(d for d in packet.validation_decisions if d.platform_id == "substack_newsletter")
    assert sub_dec.validation_status == "manual_only"
    assert sub_dec.endpoint_allowlist_status == "manual_no_api"
    assert sub_dec.credential_policy_status == "manual_no_credential"
    assert sub_dec.request_budget_status == "manual_no_api"
    assert sub_dec.redaction_policy_status == "manual_no_secret"
    assert sub_dec.kill_switch_policy_status == "manual_stop_policy"
    assert "manual_export_only" in sub_dec.blocked_reasons


def test_linkedin_blockers():
    # 32. LinkedIn contains org/page proof requirements.
    packet = contract.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet()
    li_dec = next(d for d in packet.validation_decisions if d.platform_id == "linkedin")
    assert "linkedin_organization_page_proof_missing" in li_dec.blocked_reasons


def test_meta_blockers():
    # 33. Meta templates contain app review/account proof requirements.
    packet = contract.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet()
    for pid in ("threads", "instagram", "facebook_page"):
        m_dec = next(d for d in packet.validation_decisions if d.platform_id == pid)
        assert "meta_app_review_closed" in m_dec.blocked_reasons
        assert "meta_app_account_proof_required" in m_dec.blocked_reasons


def test_tiktok_blockers():
    # 34. TikTok contains app audit/creator/video proof requirements.
    packet = contract.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet()
    tt_dec = next(d for d in packet.validation_decisions if d.platform_id == "tiktok")
    assert "tiktok_app_audit_closed" in tt_dec.blocked_reasons
    assert "creator_account_proof_required" in tt_dec.blocked_reasons
    assert "video_publish_proof_required" in tt_dec.blocked_reasons


def test_youtube_blockers():
    # 35. YouTube contains OAuth/quota/channel/upload proof requirements and no stale 1600.
    packet = contract.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet()
    yt_dec = next(d for d in packet.validation_decisions if d.platform_id == "youtube")
    assert "youtube_quota_unresolved" in yt_dec.blocked_reasons
    assert "youtube_oauth_flow_closed" in yt_dec.blocked_reasons
    assert "upload_proof_required" in yt_dec.blocked_reasons

    # Verify no mention of "1600" in the runbook content
    runbook_content = contract.render_runbook(packet)
    assert "1600" not in runbook_content


def test_u9_ledger_integration():
    # 36. U9 family is live_read_only_research_evidence_packet_dry_run_schema_future.
    packet = contract.build_supervised_live_read_only_research_evidence_packet_dry_run_schema_packet()
    assert all(fam == "live_read_only_research_evidence_packet_dry_run_schema_future" for fam in packet.u9_audit_entry_families)
    assert len(packet.u9_audit_entry_ids) == 10

    # 37. U9 ledger chain validates and contains no secrets.
    from live_contentops import live_read_only_research_evidence_packet_dry_run_schema_contract as impl
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
    # 38. artifact writer touches only docs/automation/0174UP.
    with pytest.raises(ValueError) as excinfo:
        contract.write_artifacts(repo_root=tmp_path, output_dir=tmp_path / "invalid_dir")
    assert "artifact_writer_refuses_paths_outside_docs_automation_0174UP" in str(excinfo.value)
