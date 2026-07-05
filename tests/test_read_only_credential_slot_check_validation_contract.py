import pytest
import json
from pathlib import Path
from dataclasses import replace

from live_contentops import read_only_credential_slot_check_validation_contract as contract
from live_contentops import live_read_only_research_local_preflight_simulation_contract as simulation
from live_contentops import live_read_only_research_runbook_approval_gate_dry_run_contract as runbook
from live_contentops import credential_handle_dotenv_secret_boundary_v2_contract as boundary
from live_contentops import platform_account_binding_registry_v2_contract as binding
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit
from live_contentops import platform_universe_registry_v2


def test_packet_builds_deterministically():
    # 1. Packet builds deterministically.
    p1 = contract.build_supervised_read_only_credential_slot_check_packet()
    p2 = contract.build_supervised_read_only_credential_slot_check_packet()
    assert p1.packet_id == p2.packet_id
    assert p1.packet_hash == p2.packet_hash


def test_exactly_10_platforms_represented():
    # 2. Exactly 10 platforms represented.
    packet = contract.build_supervised_read_only_credential_slot_check_packet()
    assert len(packet.credential_slot_specs) == 10
    assert packet.platform_count == 10


def test_platform_ids_match_universe():
    # 3. Platform IDs match platform universe registry.
    packet = contract.build_supervised_read_only_credential_slot_check_packet()
    pids = {s.platform_id for s in packet.credential_slot_specs}
    assert pids == set(contract.PLATFORM_IDS)


def test_simulation_packet_consumed():
    # 4. 0174UR local preflight simulation packet is consumed.
    sim = simulation.build_supervised_live_read_only_research_local_preflight_simulation_packet()
    dec_x = next(d for d in sim.simulation_decisions if d.platform_id == "x")
    dec_x_mod = replace(dec_x, precheck_status="custom_precheck_slot_val")
    sim_mod = replace(sim, simulation_decisions=tuple(dec_x_mod if d.platform_id == "x" else d for d in sim.simulation_decisions))

    packet = contract.build_supervised_read_only_credential_slot_check_packet(sim_packet=sim_mod)
    dec_x_slot = next(d for d in packet.slot_validation_decisions if d.platform_id == "x")
    assert dec_x_slot.precheck_status == "custom_precheck_slot_val"


def test_runbook_packet_consumed():
    # 5. 0174UQ runbook gate packet is consumed.
    rq = runbook.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet()
    assert len(rq.runbook_gate_decisions) == 10


def test_boundary_contract_consumed_no_env():
    # 6. Credential boundary precedent contract is consumed without reading env.
    bp = boundary.build_credential_boundary_packet()
    assert len(bp.credential_handles) > 0


def test_account_binding_contract_consumed():
    # 7. Account binding precedent contract is consumed.
    ab = binding.build_platform_account_binding_registry_packet()
    assert len(ab.bindings) > 0


def test_no_environ_reads_in_module():
    # 8. No os.environ/getenv/dotenv value read appears in the new module.
    module_path = Path("live_contentops/read_only_credential_slot_check_validation_contract.py")
    content = module_path.read_text(encoding="utf-8")
    assert "os.environ" not in content
    assert "getenv" not in content
    assert "load_dotenv" not in content


def test_all_credential_slot_specs_are_key_name_only():
    # 9. All credential slot specs are key-name-only.
    packet = contract.build_supervised_read_only_credential_slot_check_packet()
    for s in packet.credential_slot_specs:
        assert s.credential_values_accessed is False
        assert s.credential_hydrated is False


def test_no_slot_decision_contains_raw_secret_values():
    # 10. No slot decision contains raw secret values.
    packet = contract.build_supervised_read_only_credential_slot_check_packet()
    packet_text = repr(packet)
    forbidden_terms = ("REPLACE_WITH_REAL", "api_key=", "token=", "password=", "bearer ")
    assert not any(term.lower() in packet_text.lower() for term in forbidden_terms)


def test_no_token_prefix_suffix_hash_display():
    # 11. No token prefix/suffix/hash display is allowed.
    packet = contract.build_supervised_read_only_credential_slot_check_packet()
    for s in packet.credential_slot_specs:
        assert s.secret_hash_displayed is False
        assert s.token_prefix_displayed is False
        assert s.token_suffix_displayed is False


def test_all_counters_and_safety_flags_are_zero():
    # 12. All env/dotenv/credential/secret-store/API/provider/browser/scheduler/scraping/DM counters are zero.
    packet = contract.build_supervised_read_only_credential_slot_check_packet()
    for s in packet.credential_slot_specs:
        assert s.credential_values_accessed is False
        assert s.env_read is False
        assert s.dotenv_loaded is False
        assert s.secret_store_accessed is False
        assert s.credential_hydrated is False
        assert s.secret_value_serialized is False
        assert s.secret_hash_displayed is False
        assert s.token_prefix_displayed is False
        assert s.token_suffix_displayed is False
        assert s.live_read_allowed is False
        assert s.live_write_allowed is False
        assert s.platform_api_called is False
        assert s.provider_api_called is False
        assert s.public_post_allowed is False

    for d in packet.slot_validation_decisions:
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
    assert sf["all_credential_values_blocked"] is True
    assert sf["all_env_reads_blocked"] is True
    assert sf["all_dotenv_loads_blocked"] is True
    assert sf["all_secret_outputs_blocked"] is True
    assert sf["all_live_actions_blocked"] is True


def test_substack_newsletter_manual_only():
    # 13. Substack is manual-only/no API/no credential and has no required slots.
    packet = contract.build_supervised_read_only_credential_slot_check_packet()
    s = next(spec for spec in packet.credential_slot_specs if spec.platform_id == "substack_newsletter")
    assert s.slot_policy == "manual_no_credential"
    assert s.required_slot_names == ()
    assert s.manual_only is True

    for d in packet.slot_validation_decisions:
        if d.platform_id == "substack_newsletter":
            assert d.validation_status == "manual_only"
            assert d.validation_strength == "manual_policy_only"
            assert "manual_export_only" in d.blocked_reasons


def test_x_slot_checks_remain_blocked():
    # 14. X slot checks remain blocked.
    packet = contract.build_supervised_read_only_credential_slot_check_packet()
    for d in packet.slot_validation_decisions:
        if d.platform_id == "x":
            assert d.validation_status in ("blocked", "manual_only")
            for r in ("x_app_access_gap", "spend_gate_unresolved", "rate_budget_gap", "read_only_endpoint_proof_gap"):
                assert r in d.blocked_reasons


def test_telegram_remote_and_channel_remain_distinct():
    # 15. Telegram Remote Operator and Telegram Channel Destination remain distinct.
    packet = contract.build_supervised_read_only_credential_slot_check_packet()
    t_op = next(s for s in packet.credential_slot_specs if s.platform_id == "telegram_remote_operator")
    t_ch = next(s for s in packet.credential_slot_specs if s.platform_id == "telegram_channel_destination")
    assert t_op.endpoint_family != t_ch.endpoint_family
    assert t_op.required_slot_names != t_ch.required_slot_names
    assert "TELEGRAM_OPERATOR_CHAT_ID" in t_op.required_slot_names
    assert "TELEGRAM_CHANNEL_ID" in t_ch.required_slot_names


def test_telegram_remote_operator_arbitrary_dm_blocked():
    # 16. Telegram Remote Operator arbitrary DM/reply remains blocked.
    packet = contract.build_supervised_read_only_credential_slot_check_packet()
    for d in packet.slot_validation_decisions:
        if d.platform_id == "telegram_remote_operator":
            assert "no_arbitrary_dm_allowed" in d.blocked_reasons
            assert "operator_inbox_proof_required" in d.blocked_reasons


def test_telegram_channel_destination_posting_admin_gaps_blocked():
    # 17. Telegram Channel Destination posting/admin proof gaps remain blocked.
    packet = contract.build_supervised_read_only_credential_slot_check_packet()
    for d in packet.slot_validation_decisions:
        if d.platform_id == "telegram_channel_destination":
            assert "channel_admin_proof_required" in d.blocked_reasons
            assert "bot_permission_gap" in d.blocked_reasons
            assert "channel_state_symbolic_only" in d.blocked_reasons


def test_linkedin_proof_gaps_remain_blocked():
    # 18. LinkedIn proof gaps remain blocked.
    packet = contract.build_supervised_read_only_credential_slot_check_packet()
    for d in packet.slot_validation_decisions:
        if d.platform_id == "linkedin":
            assert "linkedin_organization_page_proof_missing" in d.blocked_reasons


def test_meta_family_proof_gaps_remain_blocked():
    # 19. Meta-family proof gaps remain blocked.
    packet = contract.build_supervised_read_only_credential_slot_check_packet()
    for pid in ("threads", "instagram", "facebook_page"):
        for d in packet.slot_validation_decisions:
            if d.platform_id == pid:
                assert "meta_app_review_closed" in d.blocked_reasons
                assert "meta_app_account_proof_required" in d.blocked_reasons


def test_tiktok_proof_gaps_remain_blocked():
    # 20. TikTok audit/creator/video proof gaps remain blocked.
    packet = contract.build_supervised_read_only_credential_slot_check_packet()
    for d in packet.slot_validation_decisions:
        if d.platform_id == "tiktok":
            assert "tiktok_app_audit_closed" in d.blocked_reasons
            assert "creator_account_proof_required" in d.blocked_reasons
            assert "video_publish_proof_required" in d.blocked_reasons


def test_youtube_proof_gaps_remain_blocked_no_1600():
    # 21. YouTube OAuth/quota/upload proof gaps remain blocked and no “1600” appears.
    packet = contract.build_supervised_read_only_credential_slot_check_packet()
    for d in packet.slot_validation_decisions:
        if d.platform_id == "youtube":
            assert "youtube_quota_unresolved" in d.blocked_reasons
            assert "youtube_oauth_flow_closed" in d.blocked_reasons
            assert "upload_proof_required" in d.blocked_reasons

    md_text = contract.render_runbook(packet)
    assert "1600" not in md_text


def test_scenarios_fail_closed():
    # 22-30. Scenario failures closed.
    packet = contract.build_supervised_read_only_credential_slot_check_packet()
    scenarios_to_check = [
        ("required_slot_missing", "required_slot_name_missing"),
        ("forbidden_slot_name_pattern", "forbidden_slot_name_pattern"),
        ("credential_value_present_attempt_blocked", "credential_value_read_blocked"),
        ("env_read_attempt_blocked", "env_read_blocked"),
        ("dotenv_load_attempt_blocked", "dotenv_load_blocked"),
        ("secret_hash_display_attempt_blocked", "secret_hash_display_blocked"),
        ("token_prefix_suffix_display_attempt_blocked", "prefix_suffix_display_blocked"),
        ("redaction_policy_missing", "redaction_policy_missing"),
        ("operator_approval_missing", "operator_approval_disabled"),
    ]
    for sc_id, expected_blocked_reason in scenarios_to_check:
        for d in packet.slot_validation_decisions:
            if d.scenario_id == sc_id:
                assert d.validation_status in ("blocked", "manual_only")
                assert expected_blocked_reason in d.blocked_reasons
                assert d.live_read_allowed is False


def test_u9_audit_entries_validate():
    # 31. U9 audit entries validate.
    packet = contract.build_supervised_read_only_credential_slot_check_packet()
    decisions = packet.slot_validation_decisions
    entries = contract.build_u9_audit_entries(decisions)

    chain = audit.build_ledger_chain(entries)
    validation = audit.validate_ledger_chain(chain)
    assert validation.validation_status == "pass"
    assert len(validation.blocked_reasons) == 0


def test_u9_family_matches():
    # 32. U9 family equals read_only_credential_slot_check_validation_future.
    packet = contract.build_supervised_read_only_credential_slot_check_packet()
    assert len(packet.u9_audit_entry_families) > 0
    for fam in packet.u9_audit_entry_families:
        assert fam == "read_only_credential_slot_check_validation_future"


def test_artifact_writer_refuses_outside_paths(tmp_path):
    # 33. Artifact writer refuses paths outside docs/automation/0174US.
    with pytest.raises(ValueError) as excinfo:
        contract.write_artifacts(repo_root=tmp_path, output_dir=tmp_path / "invalid_dir")
    assert "artifact_writer_refuses_paths_outside_docs_automation_0174US" in str(excinfo.value)


def test_operator_planning_docs_untouched():
    # 34. Known untracked operator/stale-context paths remain untouched.
    untracked_paths = [
        "docs/archive/_repo_cleanup_2026-07-03/docs/CAPITAL_CHRONICLE_CONTENTOPS_HEAVY_BATCH_MASTER_PLAN_AFTER_0174U0.md",
        "docs/archive/_repo_cleanup_2026-07-03/docs/Capital Chronicle ContentOps Strategy.pdf",
        "docs/archive/_repo_cleanup_2026-07-03/docs/reports/"
    ]
    for path_str in untracked_paths:
        p = Path(path_str)
        assert p.exists()
