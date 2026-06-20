import pytest
import json
from pathlib import Path

from live_contentops import local_preflight_bundle_v5_read_model_precheck_contract as contract
from live_contentops import platform_universe_registry_v2 as universe
from live_contentops import read_only_credential_slot_inspection_mock_audit_contract as mock_audit
from live_contentops import read_only_credential_slot_check_validation_contract as slot_check
from live_contentops import live_read_only_research_local_preflight_simulation_contract as simulation
from live_contentops import live_read_only_research_runbook_approval_gate_dry_run_contract as runbook
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit


def test_packet_builds_deterministically():
    # 1. Packet builds deterministically.
    p1 = contract.build_local_preflight_bundle_v5_read_model_precheck_packet()
    p2 = contract.build_local_preflight_bundle_v5_read_model_precheck_packet()
    assert p1.packet_id == p2.packet_id
    assert p1.packet_hash == p2.packet_hash


def test_exactly_10_platforms_represented():
    # 2. Exactly 10 platforms represented.
    packet = contract.build_local_preflight_bundle_v5_read_model_precheck_packet()
    assert packet.platform_count == 10
    platforms = {ps.platform_id for ps in packet.platform_states}
    assert platforms == set(contract.PLATFORM_IDS)


def test_platform_ids_match_registry():
    # 3. Platform IDs match platform universe registry.
    packet = contract.build_local_preflight_bundle_v5_read_model_precheck_packet()
    for ps in packet.platform_states:
        assert ps.platform_id in contract.PLATFORM_IDS


def test_all_required_precedent_contracts_consumed():
    # 4. All required precedent contracts are consumed.
    packet = contract.build_local_preflight_bundle_v5_read_model_precheck_packet()
    ref_ids = {ref.source_ref_id for ref in packet.source_refs}
    required = {
        "platform_universe_registry_v2",
        "platform_account_binding_registry_v2_contract",
        "credential_handle_dotenv_secret_boundary_v2_contract",
        "live_read_only_research_approval_packet_schema_contract",
        "live_read_only_research_evidence_packet_dry_run_schema_contract",
        "live_read_only_research_runbook_approval_gate_dry_run_contract",
        "live_read_only_research_local_preflight_simulation_contract",
        "read_only_credential_slot_check_validation_contract",
        "read_only_credential_slot_inspection_mock_audit_contract",
        "supervised_live_read_only_research_gate_precheck_contract",
        "platform_preflight_dry_run_request_budget_contract",
        "rate_budget_kill_switch_matrix_contract",
        "redacted_immutable_audit_ledger_v2_contract",
        "local_content_governance_summary_mart_contract",
        "manual_publish_record_metrics_ledger_contract",
        "content_performance_review_editorial_feedback_contract",
        "internal_alpha_artifact_intake_content_eligibility_contract",
    }
    assert required.issubset(ref_ids)


def test_mock_audit_packet_consumed():
    # 5. 0174UT mock audit packet is consumed.
    packet = contract.build_local_preflight_bundle_v5_read_model_precheck_packet()
    ref = next(r for r in packet.source_refs if r.source_ref_id == "read_only_credential_slot_inspection_mock_audit_contract")
    assert ref.consumed is True


def test_slot_check_packet_consumed():
    # 6. 0174US slot check packet is consumed.
    packet = contract.build_local_preflight_bundle_v5_read_model_precheck_packet()
    ref = next(r for r in packet.source_refs if r.source_ref_id == "read_only_credential_slot_check_validation_contract")
    assert ref.consumed is True


def test_simulation_packet_consumed():
    # 7. 0174UR simulation packet is consumed.
    packet = contract.build_local_preflight_bundle_v5_read_model_precheck_packet()
    ref = next(r for r in packet.source_refs if r.source_ref_id == "live_read_only_research_local_preflight_simulation_contract")
    assert ref.consumed is True


def test_runbook_packet_consumed():
    # 8. 0174UQ runbook packet is consumed.
    packet = contract.build_local_preflight_bundle_v5_read_model_precheck_packet()
    ref = next(r for r in packet.source_refs if r.source_ref_id == "live_read_only_research_runbook_approval_gate_dry_run_contract")
    assert ref.consumed is True


def test_source_refs_no_live_capability():
    # 9. Source refs never claim live capability.
    packet = contract.build_local_preflight_bundle_v5_read_model_precheck_packet()
    for ref in packet.source_refs:
        assert ref.live_capability_added is False
        assert ref.credential_values_accessed is False
        assert ref.env_read is False
        assert ref.platform_api_called is False
        assert ref.ui_mutated is False
        assert ref.ingestion_mutated is False


def test_platform_states_never_allow_live_actions():
    # 10. Platform states never allow live read/write/public post/dispatch/readiness.
    packet = contract.build_local_preflight_bundle_v5_read_model_precheck_packet()
    for ps in packet.platform_states:
        assert ps.live_read_allowed is False
        assert ps.live_write_allowed is False
        assert ps.public_post_allowed is False
        assert ps.dispatch_ready is False
        assert ps.readiness_cleared is False


def test_v5_room_prechecks_include_required_rooms():
    # 11. V5 room prechecks include all required rooms.
    packet = contract.build_local_preflight_bundle_v5_read_model_precheck_packet()
    assert packet.room_count == 13
    rooms = {pr.room_id for pr in packet.room_binding_prechecks}
    required = {
        "command_center",
        "evidence_vault",
        "approval_queue",
        "platform_payload_preview",
        "substack_manual_export",
        "credential_boundary",
        "account_binding",
        "live_readiness_gate",
        "manual_publish_metrics",
        "content_performance_review",
        "internal_alpha_artifact_intake",
        "writer_studio",
        "grounded_news_workbench",
    }
    assert rooms == required


def test_no_ui_imports_or_mutations():
    # 12. No UI files are imported or mutated by the module.
    module_path = Path("live_contentops/local_preflight_bundle_v5_read_model_precheck_contract.py")
    content = module_path.read_text(encoding="utf-8")
    assert "import ui" not in content
    assert "from ui" not in content


def test_safe_display_fields_have_no_secrets():
    # 13. Safe display fields never include secret values, token slices, hashes, raw responses, env values, or credential values.
    packet = contract.build_local_preflight_bundle_v5_read_model_precheck_packet()
    for ps in packet.platform_states:
        for f in ps.safe_display_fields:
            assert f not in ("raw_secrets", "credential_values", "token_slices", "hashes", "raw_api_responses", "env_values")


def test_hidden_redacted_fields_contain_credentials_and_raw_responses():
    # 14. Hidden/redacted fields include credential and raw response families.
    packet = contract.build_local_preflight_bundle_v5_read_model_precheck_packet()
    for ps in packet.platform_states:
        assert "raw_secrets" in ps.hidden_or_absent_fields
        assert "credential_values" in ps.hidden_or_absent_fields
        assert "raw_api_responses" in ps.redaction_required_fields or "raw_api_responses" in ps.hidden_or_absent_fields


def test_future_action_affordances_disabled():
    # 15. All future action affordances are disabled or read-only.
    packet = contract.build_local_preflight_bundle_v5_read_model_precheck_packet()
    for field in packet.v5_candidate_fields:
        if field.user_action_affordance == "disabled_future_gate":
            assert field.forbidden_affordance_reason == "live_action_blocked_local_only"
        else:
            assert field.user_action_affordance in ("read_only", "manual_review_only")


def test_substack_manual_only():
    # 16. Substack remains manual-only/no API/no credential/manual export.
    packet = contract.build_local_preflight_bundle_v5_read_model_precheck_packet()
    ps = next(s for s in packet.platform_states if s.platform_id == "substack_newsletter")
    assert "manual_export_only" in ps.blocked_reasons
    assert ps.endpoint_family == "manual"
    assert ps.credential_slot_status == "manual_no_credential"


def test_telegram_remote_and_channel_distinct():
    # 17. Telegram Remote Operator and Telegram Channel Destination remain distinct.
    packet = contract.build_local_preflight_bundle_v5_read_model_precheck_packet()
    t_op = next(s for s in packet.platform_states if s.platform_id == "telegram_remote_operator")
    t_ch = next(s for s in packet.platform_states if s.platform_id == "telegram_channel_destination")
    assert t_op.platform_role != t_ch.platform_role
    assert "no_arbitrary_dm_allowed" in t_op.blocked_reasons
    assert "channel_admin_proof_required" in t_ch.blocked_reasons


def test_x_proof_gaps_blocked():
    # 18. X proof gaps remain blocked.
    packet = contract.build_local_preflight_bundle_v5_read_model_precheck_packet()
    ps = next(s for s in packet.platform_states if s.platform_id == "x")
    assert "x_app_access_gap" in ps.blocked_reasons
    assert "spend_gate_unresolved" in ps.blocked_reasons


def test_linkedin_proof_gaps_blocked():
    # 19. LinkedIn proof gaps remain blocked.
    packet = contract.build_local_preflight_bundle_v5_read_model_precheck_packet()
    ps = next(s for s in packet.platform_states if s.platform_id == "linkedin")
    assert "linkedin_organization_page_proof_missing" in ps.blocked_reasons


def test_meta_family_proof_gaps_blocked():
    # 20. Meta-family proof gaps remain blocked.
    packet = contract.build_local_preflight_bundle_v5_read_model_precheck_packet()
    for pid in ("threads", "instagram", "facebook_page"):
        ps = next(s for s in packet.platform_states if s.platform_id == pid)
        assert "meta_app_review_closed" in ps.blocked_reasons


def test_tiktok_proof_gaps_blocked():
    # 21. TikTok proof gaps remain blocked.
    packet = contract.build_local_preflight_bundle_v5_read_model_precheck_packet()
    ps = next(s for s in packet.platform_states if s.platform_id == "tiktok")
    assert "tiktok_app_audit_closed" in ps.blocked_reasons


def test_youtube_proof_gaps_blocked_no_1600():
    # 22. YouTube proof gaps remain blocked and no “1600” appears.
    packet = contract.build_local_preflight_bundle_v5_read_model_precheck_packet()
    ps = next(s for s in packet.platform_states if s.platform_id == "youtube")
    assert "youtube_quota_unresolved" in ps.blocked_reasons
    
    md_text = contract.render_runbook(packet)
    assert "1600" not in md_text


def test_global_safety_flags_are_false():
    # 23. Global safety flags are all false/review_only mode.
    packet = contract.build_local_preflight_bundle_v5_read_model_precheck_packet()
    sf = packet.safety_flags
    assert sf["local_only"] is True
    assert sf["read_model_precheck_only"] is True
    assert sf["ui_mutated"] is False
    assert sf["live_read_allowed"] is False
    assert sf["live_write_allowed"] is False
    assert sf["public_post_allowed"] is False
    assert sf["dispatch_ready"] is False
    assert sf["autonomous_posting_allowed"] is False
    assert sf["env_read"] is False
    assert sf["credential_values_accessed"] is False
    assert sf["credential_hydrated"] is False
    assert sf["secret_output_allowed"] is False
    assert sf["platform_api_called"] is False
    assert sf["provider_api_called"] is False
    assert sf["network_performed"] is False
    assert sf["browser_session_used"] is False
    assert sf["scheduler_enabled"] is False
    assert sf["scraping_performed"] is False
    assert sf["dm_or_reply_automation_allowed"] is False
    assert sf["current_truth_promoted"] is False
    assert sf["dqr_cleared"] is False
    assert sf["readiness_cleared"] is False
    assert sf["ingestion_repo_mutated"] is False


def test_u9_audit_entries_validate():
    # 24. U9 audit entries validate.
    packet = contract.build_local_preflight_bundle_v5_read_model_precheck_packet()
    entries = contract.build_u9_audit_entries(packet.packet_id, packet.platform_states)

    chain = audit.build_ledger_chain(entries)
    validation = audit.validate_ledger_chain(chain)
    assert validation.validation_status == "pass"
    assert len(validation.blocked_reasons) == 0


def test_u9_family_matches():
    # 25. U9 family equals local_preflight_bundle_v5_read_model_precheck_future.
    packet = contract.build_local_preflight_bundle_v5_read_model_precheck_packet()
    assert len(packet.u9_audit_entry_families) > 0
    for fam in packet.u9_audit_entry_families:
        assert fam == "local_preflight_bundle_v5_read_model_precheck_future"


def test_artifact_writer_refuses_outside_paths(tmp_path):
    # 26. Artifact writer refuses paths outside docs/automation/0174UU.
    with pytest.raises(ValueError) as excinfo:
        contract.write_artifacts(repo_root=tmp_path, output_dir=tmp_path / "invalid_dir")
    assert "artifact_writer_refuses_paths_outside_docs_automation_0174UU" in str(excinfo.value)


def test_operator_planning_docs_untouched():
    # 27. Known untracked operator/stale-context paths remain untouched.
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
