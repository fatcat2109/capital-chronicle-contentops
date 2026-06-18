import importlib
import pathlib

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_import_has_no_side_effects():
    module = importlib.import_module("live_contentops.supervised_dispatch_readiness_summary")
    assert module.NEXT_BATCH_PROMPT.endswith("MANUAL_EXPORT_REVIEW_SURFACE_CONTRACT_V0")


def _result():
    from live_contentops import supervised_dispatch_readiness_summary as s

    return s.write_artifacts(REPO_ROOT)


def test_readiness_summary_not_ready_and_blocked_statuses():
    summary = _result()["summary"]
    assert summary["readiness_class"] == "NOT_READY_FOR_LIVE_DISPATCH"
    assert summary["local_governance_status"] == "PASS_DRY_RUN_CHAIN"
    assert summary["live_dispatch_status"] == "BLOCKED"


def test_summary_forbids_ready_claims():
    from live_contentops import supervised_dispatch_readiness_policy as p

    summary = _result()["summary"]
    p.validate_no_forbidden_readiness_claims(summary)
    text = " ".join(_scalar_strings(summary))
    for claim in ["production-ready", "live-ready", "dispatch-ready", "public-postable", "ready to send"]:
        assert claim not in text


def test_platform_readiness_statuses():
    readiness = _result()["summary"]["platform_readiness"]
    assert readiness["telegram"] == "DISPATCH_PROVEN_FROZEN_NO_SEND"
    assert readiness["x"] == "DRY_RUN_ONLY_NO_API"
    assert readiness["substack"] == "MANUAL_EXPORT_ONLY_NO_API"


def test_required_future_gates_and_live_blockers():
    summary = _result()["summary"]
    assert summary["required_future_gates"] == ["kill_switch_activation", "redacted_audit_packet", "manual_fallback_proof", "operator_supervision_window", "live_dispatch_separate_approval"]
    for item in ["kill switch activation missing", "redacted audit packet for real platform response missing", "manual fallback proof missing", "operator supervision window missing", "live dispatch separate approval missing", "credential hydration forbidden in current chain", "platform API calls forbidden in current chain", "provider response not called", "request budget used is 0", "final URL not verified"]:
        assert item in summary["live_blockers"]


def test_no_live_behavior_proof_aggregates_correctly():
    proof = _result()["summary"]["no_live_behavior_proof"]
    assert proof["all_false"] is True
    for key in ["network_performed", "telegram_api_called", "x_api_called", "substack_api_called", "platform_api_called", "provider_api_called", "llm_provider_api_called", "env_read", "dotenv_read", "credential_read", "credential_hydration_performed", "scheduler_enabled", "live_post_performed", "autonomous_replies_or_dms", "scraping_performed", "public_ready_content_generated", "platform_dispatch_performed", "live_ready_state_created", "raw_request_persisted", "raw_response_persisted", "token_logged"]:
        assert proof[key] is True
    assert proof["provider_response_class_values"] == ["not_called"]
    assert proof["request_budget_used_values"] == [0]
    assert proof["all_final_url_verified_null"] is True


def test_chain_checksum_references_present():
    summary = _result()["summary"]
    for key in ["platform_universe_registry_checksum", "telegram_dispatch_registry_checksum", "remote_inbox_checksum", "intent_ingress_checksum", "editorial_brief_checksum", "platform_variant_checksum", "approval_challenge_checksum", "approval_ledger_checksum", "dispatch_outbox_candidate_checksum", "dispatch_gate_matrix_checksum", "dispatch_audit_dry_run_checksum"]:
        assert summary[key]
        assert len(summary[key]) >= 32


def test_full_dry_run_chain_reconciliation_in_order():
    reconciliation = _result()["reconciliation"]
    expected = ["remote_operator_intent_ingress", "llm_intent_editorial_brief", "primary_platform_variant_dry_run", "approval_challenge_candidate", "approval_ledger", "dispatch_outbox_candidate", "dispatch_gate_matrix", "dispatch_audit_dry_run", "supervised_dispatch_readiness_summary"]
    assert reconciliation["stage_order"] == expected
    assert [stage["stage"] for stage in reconciliation["stages"]] == expected
    assert reconciliation["stage_count"] == len(expected)
    assert reconciliation["readiness_class"] == "NOT_READY_FOR_LIVE_DISPATCH"


def test_next_task_manual_export_or_review_surface_not_live_dispatch():
    next_packet = _result()["next_packet"]
    assert "MANUAL_EXPORT_REVIEW_SURFACE" in next_packet["next_batch_prompt"]
    assert next_packet["allowed_direction"] == "manual_export_review_surface_or_cockpit_read_model"
    assert next_packet["forbidden_direction"] == "live_dispatch"
    assert "live_dispatch" in next_packet["forbidden_outputs"]


def test_no_live_network_env_provider_platform_behavior_flags():
    summary = _result()["summary"]
    assert summary["is_local_only"] is True
    for key in ["network_performed", "telegram_api_called", "x_api_called", "substack_api_called", "platform_api_called", "provider_api_called", "llm_provider_api_called", "env_read", "dotenv_read", "credential_read", "credential_hydration_performed", "scheduler_enabled", "live_post_performed", "autonomous_replies_or_dms", "scraping_performed", "public_ready_content_generated", "platform_dispatch_performed", "live_ready_state_created", "raw_request_persisted", "raw_response_persisted", "token_logged"]:
        assert summary[key] is False


def test_supported_platforms_and_dry_run_capabilities():
    summary = _result()["summary"]
    assert summary["supported_primary_platforms"] == ["x", "telegram", "substack"]
    for item in ["remote operator intent ingress fixture accepted", "review-only platform payload previews hashed", "dispatch gate matrix evaluated", "redacted dispatch audit dry-run events recorded"]:
        assert item in summary["dry_run_capabilities_proven"]


def test_summary_evidence_and_hashes_present():
    summary = _result()["summary"]
    assert summary["evidence_refs"]
    assert summary["audit_hash"]
    assert summary["supervised_dispatch_readiness_summary_checksum"]


def _scalar_strings(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _scalar_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _scalar_strings(item)
    elif isinstance(value, str):
        yield value.lower()


def test_no_forbidden_autonomous_behavior_values():
    summary = _result()["summary"]
    for item in ["autonomous posting", "scheduling", "autonomous replies", "direct messages", "scraping", "trading or signal behavior"]:
        assert item in summary["forbidden_capabilities"]


def test_deterministic_generation_and_unsafe_path_refused(tmp_path):
    from live_contentops import supervised_dispatch_readiness_summary as s

    first = s.write_artifacts(REPO_ROOT)
    second = s.write_artifacts(REPO_ROOT)
    assert first == second
    with pytest.raises(ValueError, match="unsafe_output_path_refused"):
        s.write_artifacts(REPO_ROOT, tmp_path)
