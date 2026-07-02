"""Tests for V6 Discord operator source + GO phrase intake."""
from __future__ import annotations

import json
from pathlib import Path

from live_contentops.discord_operator_source_go_phrase_intake_v5_adapter_codegen_v6 import (
    generate_operator_source_go_phrase_intake_adapter,
)
from live_contentops.discord_operator_source_go_phrase_intake_v6 import (
    DECISION_PHRASES,
    DECISION_SCOPE,
    GO_PHRASE,
    build_operator_source_go_phrase_intake,
)

ROOT = Path(__file__).resolve().parents[1]
PACKET_DIR = ROOT / "docs" / "automation" / "V6_DISCORD_OPERATOR_SOURCE_AND_GO_PHRASE_INTAKE"
INBOX = PACKET_DIR / "inbox"
PACKET = PACKET_DIR / "operator_source_go_phrase_intake_packet.json"
NORMALIZED = PACKET_DIR / "normalized_candidate" / "normalized_operator_source_go_phrase_candidate.json"
ENVELOPE = PACKET_DIR / "review_only_dry_run_envelope" / "discord_review_only_dry_run_envelope_normalization.json"
ADAPTER = ROOT / "ui" / "contentops_v5" / "src" / "data" / "discordOperatorSourceGoPhraseIntakeAdapter.ts"
DESTINATION = PACKET_DIR / "destination_binding_proof.json"
KILL_SWITCH = PACKET_DIR / "kill_switch_evidence" / "discord_kill_switch_evidence.json"
CREDENTIAL_PRESENCE = PACKET_DIR / "credential_presence_evidence" / "discord_credential_presence_evidence.json"
FIXTURE_REVIEW = PACKET_DIR / "fixture_review" / "discord_operator_source_artifact_fixture_review.json"
PRE_DISPATCH = PACKET_DIR / "pre_dispatch_readiness" / "discord_pre_dispatch_readiness.json"
LIVE_PREFLIGHT = PACKET_DIR / "live_preflight" / "discord_blocked_live_preflight.json"
OPERATOR_INPUT_CONTRACT = PACKET_DIR / "operator_input_contract" / "discord_operator_supplied_live_preflight_input_contract.json"
REDACTED_REVIEW = PACKET_DIR / "redacted_operator_review" / "discord_redacted_operator_review_packet.json"
OPERATOR_REVIEW_DECISION = PACKET_DIR / "operator_review_decision" / "discord_operator_review_decision_packet.json"
DISPATCH_DECISION_READINESS = PACKET_DIR / "dispatch_decision_readiness" / "discord_dispatch_decision_readiness.json"
DISPATCH_ROUTE_PREVIEW = PACKET_DIR / "dispatch_route_preview" / "discord_dispatch_route_preview.json"
OPERATOR_SUPERVISION_CONTRACT = PACKET_DIR / "operator_supervision_contract" / "discord_operator_supervision_contract.json"
OPERATOR_REVIEW_DECISION_INBOX = PACKET_DIR / "operator_review_decision" / "inbox"
FIXTURE_EXAMPLE = PACKET_DIR / "fixtures" / "non_real_operator_source_fixture.example.json"
SURFACES = [
    ROOT / "ui" / "contentops_v5" / "src" / "views" / "ApprovalQueue.tsx",
    ROOT / "ui" / "contentops_v5" / "src" / "views" / "PlatformPreview.tsx",
    ROOT / "ui" / "contentops_v5" / "src" / "views" / "PreflightBundle.tsx",
    ROOT / "ui" / "contentops_v5" / "src" / "views" / "EvidenceVault.tsx",
    ROOT / "ui" / "contentops_v5" / "src" / "views" / "ManualExportPilotVerification.tsx",
]


def _clean_inbox() -> None:
    INBOX.mkdir(parents=True, exist_ok=True)
    for path in INBOX.iterdir():
        if path.name != ".gitkeep":
            path.unlink()
    OPERATOR_REVIEW_DECISION_INBOX.mkdir(parents=True, exist_ok=True)
    for path in OPERATOR_REVIEW_DECISION_INBOX.iterdir():
        if path.name != ".gitkeep":
            path.unlink()


def _present_keys(monkeypatch) -> None:
    for key in [
        "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK",
        "DISCORD_LIVE_ANNOUNCEMENTS_CHANNEL_LABEL",
        "CONTENTOPS_LIVE_KILL_SWITCH",
    ]:
        monkeypatch.setenv(key, "present-marker-not-read")


def test_empty_inbox_candidate_blocks_precisely(monkeypatch) -> None:
    _clean_inbox()
    for key in [
        "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK",
        "DISCORD_LIVE_ANNOUNCEMENTS_CHANNEL_LABEL",
        "CONTENTOPS_LIVE_KILL_SWITCH",
    ]:
        monkeypatch.delenv(key, raising=False)

    packet = build_operator_source_go_phrase_intake()
    stored = json.loads(PACKET.read_text(encoding="utf-8"))
    normalized = json.loads(NORMALIZED.read_text(encoding="utf-8"))

    assert stored == packet
    assert packet["intake_status"] == "blocked"
    assert packet["operator_source_artifact_path"] == ""
    assert packet["operator_source_artifact_kind"] == "missing"
    assert packet["operator_source_artifact_real_claimed"] is False
    assert packet["fixture_only"] is False
    assert packet["not_public_postable"] is True
    assert packet["operator_go_phrase_recorded"] is False
    assert packet["operator_go_phrase_valid"] is False
    assert packet["destination_binding_confirmed"] is False
    assert packet["ready_for_dispatch"] is False
    assert packet["live_action_allowed"] is False
    assert packet["dry_run_envelope_normalization_performed"] is True
    assert packet["dry_run_request_envelope_preview_created"] is True
    assert packet["dry_run_envelope_value_stored"] is False
    assert packet["dry_run_request_envelope_id"].startswith("discord_review_envelope_")
    assert normalized["candidate_status"] == "blocked"
    destination = json.loads(DESTINATION.read_text(encoding="utf-8"))
    kill_switch = json.loads(KILL_SWITCH.read_text(encoding="utf-8"))
    credential_presence = json.loads(CREDENTIAL_PRESENCE.read_text(encoding="utf-8"))
    fixture_review = json.loads(FIXTURE_REVIEW.read_text(encoding="utf-8"))
    pre_dispatch = json.loads(PRE_DISPATCH.read_text(encoding="utf-8"))
    live_preflight = json.loads(LIVE_PREFLIGHT.read_text(encoding="utf-8"))
    input_contract = json.loads(OPERATOR_INPUT_CONTRACT.read_text(encoding="utf-8"))
    redacted_review = json.loads(REDACTED_REVIEW.read_text(encoding="utf-8"))
    dispatch_decision = json.loads(DISPATCH_DECISION_READINESS.read_text(encoding="utf-8"))
    route_preview = json.loads(DISPATCH_ROUTE_PREVIEW.read_text(encoding="utf-8"))
    supervision_contract = json.loads(OPERATOR_SUPERVISION_CONTRACT.read_text(encoding="utf-8"))
    assert packet["operator_input_contract_status"] == "blocked"
    assert packet["redacted_operator_review_status"] == "blocked"
    assert packet["operator_review_decision_status"] == "blocked"
    assert dispatch_decision["dispatch_decision_readiness_status"] == "blocked"
    assert "blocked_operator_review_decision_artifact_missing" in dispatch_decision["blocked_reasons"]
    assert redacted_review["redacted_operator_review_status"] == "blocked"
    assert redacted_review["redaction_performed"] is True
    assert redacted_review["body_value_stored"] is False
    assert redacted_review["go_phrase_value_stored"] is False
    assert redacted_review["webhook_url_value_stored"] is False
    assert redacted_review["credential_value_stored"] is False
    review_decision = json.loads(OPERATOR_REVIEW_DECISION.read_text(encoding="utf-8"))
    assert review_decision["operator_review_decision_status"] == "blocked"
    assert "blocked_operator_review_decision_artifact_missing" in review_decision["blocked_reasons"]
    assert review_decision["notes_value_stored"] is False
    assert review_decision["dispatchable"] is False
    assert dispatch_decision["dispatch_decision_readiness_status"] == "blocked"
    assert "blocked_operator_review_decision_artifact_missing" in dispatch_decision["blocked_reasons"]
    assert dispatch_decision["dispatchable"] is False
    assert dispatch_decision["ready_for_dispatch"] is False
    assert dispatch_decision["live_action_allowed"] is False
    assert route_preview["dispatch_route_preview_status"] == "blocked"
    assert route_preview["route_class"] == "deferred_blocked"
    assert route_preview["route_preview_ready_not_dispatch"] is False
    assert route_preview["ready_for_dispatch"] is False
    assert route_preview["live_action_allowed"] is False
    assert packet["operator_supervision_contract_status"] == "blocked"
    assert supervision_contract["operator_supervision_contract_status"] == "blocked"
    assert supervision_contract["supervision_state"] == "deferred_blocked"
    assert supervision_contract["route_class"] == "deferred_blocked"
    assert supervision_contract["operator_supervision_contract_ready_not_dispatch"] is False
    assert supervision_contract["future_exact_live_scope_artifact_required"] is True
    assert supervision_contract["future_exact_live_scope_artifact_present"] is False
    assert supervision_contract["request_envelope_executable"] is False
    assert supervision_contract["dispatchable"] is False
    assert supervision_contract["ready_for_dispatch"] is False
    assert supervision_contract["live_action_allowed"] is False
    assert supervision_contract["webhook_validation_performed"] is False
    assert "blocked_dispatch_route_deferred" in supervision_contract["blocked_reasons"]
    assert input_contract["operator_input_contract_status"] == "blocked"
    assert input_contract["fixture_can_satisfy_contract"] is False
    assert input_contract["required_inbox_path"] == "docs/automation/V6_DISCORD_OPERATOR_SOURCE_AND_GO_PHRASE_INTAKE/inbox/"
    assert "blocked_operator_supplied_input_contract_unsatisfied" in input_contract["blocked_reasons"]
    assert input_contract["body_value_stored"] is False
    assert input_contract["go_phrase_value_stored"] is False
    assert input_contract["credential_value_read_made"] is False
    assert input_contract["env_value_read_made"] is False
    assert input_contract["webhook_validation_performed"] is False
    assert packet["real_operator_artifact_present"] is False
    assert packet["real_operator_artifact_intake_ready"] is False
    assert packet["fixture_vs_real_separation_enforced"] is True
    assert live_preflight["live_preflight_status"] == "blocked"
    assert live_preflight["real_operator_artifact_present"] is False
    assert "blocked_real_operator_artifact_required" in live_preflight["blocked_reasons"]
    assert "blocked_real_operator_artifact_intake_not_ready" in live_preflight["blocked_reasons"]
    assert destination["destination_proof_status"] == "blocked"
    assert destination["destination_binding_confirmed"] is False
    assert destination["webhook_validation_performed"] is False
    assert kill_switch["kill_switch_status"] == "blocked"
    assert kill_switch["kill_switch_key_presence"] == "missing"
    assert kill_switch["kill_switch_value_read_made"] is False
    assert credential_presence["credential_presence_status"] == "blocked"
    assert credential_presence["credential_values_read_made"] is False
    assert fixture_review["fixture_review_status"] == "blocked"
    assert fixture_review["real_operator_artifact_claimed"] is False
    assert fixture_review["ready_for_dispatch"] is False
    assert pre_dispatch["pre_dispatch_readiness_status"] == "blocked"
    assert pre_dispatch["operator_review_ready"] is False
    assert pre_dispatch["ready_for_dispatch"] is False
    for reason in [
        "blocked_missing_operator_source_artifact",
        "blocked_operator_go_phrase_not_recorded",
        "blocked_operator_go_phrase_not_valid",
        "blocked_destination_label_missing",
        "blocked_destination_binding_not_confirmed",
        "blocked_kill_switch_not_active",
        "blocked_discord_live_announcements_webhook_key_missing",
        "blocked_discord_live_announcements_channel_label_key_missing",
        "blocked_contentops_live_kill_switch_key_missing",
    ]:
        assert reason in packet["blocked_reasons"]


def test_valid_non_real_fixture_ready_for_fixture_review_never_dispatches(monkeypatch) -> None:
    _clean_inbox()
    _present_keys(monkeypatch)
    (INBOX / "operator_source_fixture.json").write_text(
        json.dumps(
            {
                "fixture_kind": "discord_operator_source_artifact_non_real_fixture_v0",
                "non_real_fixture": True,
                "fixture_only": True,
                "not_public_postable": True,
                "real_operator_artifact_claimed": False,
                "body": "Capital Chronicle supervised Discord pilot fixture update. Local review only; not public postable.",
                "go_phrase": GO_PHRASE,
                "destination_label": "discord-live-announcements",
                "destination_binding_confirmed": True,
                "kill_switch_active": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    packet = build_operator_source_go_phrase_intake()
    normalized = json.loads(NORMALIZED.read_text(encoding="utf-8"))
    envelope = json.loads(ENVELOPE.read_text(encoding="utf-8"))
    fixture_review = json.loads(FIXTURE_REVIEW.read_text(encoding="utf-8"))
    pre_dispatch = json.loads(PRE_DISPATCH.read_text(encoding="utf-8"))
    live_preflight = json.loads(LIVE_PREFLIGHT.read_text(encoding="utf-8"))
    input_contract = json.loads(OPERATOR_INPUT_CONTRACT.read_text(encoding="utf-8"))
    redacted_review = json.loads(REDACTED_REVIEW.read_text(encoding="utf-8"))
    dispatch_decision = json.loads(DISPATCH_DECISION_READINESS.read_text(encoding="utf-8"))
    route_preview = json.loads(DISPATCH_ROUTE_PREVIEW.read_text(encoding="utf-8"))
    supervision_contract = json.loads(OPERATOR_SUPERVISION_CONTRACT.read_text(encoding="utf-8"))

    assert packet["intake_status"] == "ready_for_operator_review_not_dispatch"
    assert packet["operator_source_artifact_kind"] == "non_real_fixture"
    assert packet["operator_source_artifact_real_claimed"] is False
    assert packet["non_real_fixture"] is True
    assert packet["fixture_only"] is True
    assert packet["not_public_postable"] is True
    assert packet["real_operator_artifact_present"] is False
    assert packet["real_operator_artifact_intake_ready"] is False
    assert packet["fixture_vs_real_separation_enforced"] is True
    assert input_contract["operator_input_contract_status"] == "blocked"
    assert input_contract["fixture_can_satisfy_contract"] is False
    assert "blocked_operator_supplied_input_contract_fixture_not_allowed" in input_contract["blocked_reasons"]
    assert live_preflight["live_preflight_status"] == "blocked"
    assert "blocked_non_real_fixture_cannot_satisfy_real_operator_artifact" in live_preflight["blocked_reasons"]
    assert packet["operator_go_phrase_valid"] is True
    assert packet["operator_go_phrase_value_stored"] is False
    assert packet["dry_run_envelope_normalization_performed"] is True
    assert packet["dry_run_request_envelope_preview_created"] is True
    assert packet["dry_run_envelope_value_stored"] is False
    assert packet["fixture_review_status"] == "ready_for_fixture_review_not_dispatch"
    assert packet["redacted_operator_review_status"] == "blocked"
    assert packet["operator_review_decision_status"] == "blocked"
    assert redacted_review["redacted_operator_review_status"] == "blocked"
    assert "blocked_fixture_cannot_enter_redacted_operator_review" in redacted_review["blocked_reasons"]
    assert redacted_review["dispatchable"] is False
    assert dispatch_decision["dispatch_decision_readiness_status"] == "blocked"
    assert "blocked_fixture_cannot_enter_dispatch_decision_readiness" in dispatch_decision["blocked_reasons"]
    assert route_preview["dispatch_route_preview_status"] == "blocked"
    assert route_preview["route_class"] == "deferred_blocked"
    assert supervision_contract["operator_supervision_contract_status"] == "blocked"
    assert supervision_contract["dispatchable"] is False
    assert supervision_contract["ready_for_dispatch"] is False
    assert "blocked_dispatch_route_deferred" in supervision_contract["blocked_reasons"]
    assert packet["fixture_review_ready"] is True
    assert fixture_review["fixture_review_status"] == "ready_for_fixture_review_not_dispatch"
    assert fixture_review["real_operator_artifact_claimed"] is False
    assert fixture_review["real_operator_artifact_required_for_dispatch"] is True
    assert fixture_review["request_envelope_executable"] is False
    assert fixture_review["ready_for_dispatch"] is False
    assert fixture_review["live_action_allowed"] is False
    assert envelope["envelope_status"] == "ready_for_operator_review_not_dispatch"
    assert envelope["normalized_allowed_mentions_parse"] == []
    assert envelope["request_envelope_executable"] is False
    assert envelope["dispatchable"] is False
    assert pre_dispatch["pre_dispatch_readiness_status"] == "ready_for_operator_review_not_dispatch"
    assert pre_dispatch["fixture_review_ready"] is True
    assert pre_dispatch["ready_for_dispatch"] is False
    assert GO_PHRASE not in PACKET.read_text(encoding="utf-8")
    assert GO_PHRASE not in NORMALIZED.read_text(encoding="utf-8")
    assert GO_PHRASE not in ENVELOPE.read_text(encoding="utf-8")
    assert "present-marker-not-read" not in PACKET.read_text(encoding="utf-8")
    assert "present-marker-not-read" not in CREDENTIAL_PRESENCE.read_text(encoding="utf-8")
    assert "Capital Chronicle supervised Discord pilot fixture update" not in ENVELOPE.read_text(encoding="utf-8")
    assert "Capital Chronicle supervised Discord pilot fixture update" not in LIVE_PREFLIGHT.read_text(encoding="utf-8")
    assert normalized["dispatchable"] is False
    for key in [
        "webhook_validation_performed",
        "request_envelope_executable",
        "approval_ledger_entry_created",
        "executable_outbox_entry_created",
        "real_outbox_entry_created",
        "dispatch_outbox_ready",
        "dispatch_attempted",
        "ready_for_dispatch",
        "live_action_allowed",
        "credential_value_read_made",
        "env_value_read_made",
        "provider_call_made",
        "platform_api_used",
        "public_url_fetch_made",
        "browser_session_used",
        "live_publish_performed_by_contentops",
        "enabled_publish_send_dispatch_approve_controls",
    ]:
        assert packet[key] is False
    assert packet["dispatch_request_count"] == 0
    assert packet["webhook_request_count"] == 0
    assert packet["platform_api_request_count"] == 0
    _clean_inbox()
    build_operator_source_go_phrase_intake()


def test_valid_real_operator_artifact_ready_for_preflight_review_never_dispatches(monkeypatch) -> None:
    _clean_inbox()
    _present_keys(monkeypatch)
    (INBOX / "operator_source_real.json").write_text(
        json.dumps(
            {
                "artifact_kind": "discord_operator_source_artifact_v0",
                "real_operator_artifact_claimed": True,
                "non_real_fixture": False,
                "fixture_only": False,
                "not_public_postable": False,
                "body": "Capital Chronicle supervised Discord pilot real operator artifact. Local review hash only.",
                "go_phrase": GO_PHRASE,
                "destination_label": "discord-live-announcements",
                "destination_binding_confirmed": True,
                "kill_switch_active": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    packet = build_operator_source_go_phrase_intake()
    live_preflight = json.loads(LIVE_PREFLIGHT.read_text(encoding="utf-8"))
    fixture_review = json.loads(FIXTURE_REVIEW.read_text(encoding="utf-8"))
    input_contract = json.loads(OPERATOR_INPUT_CONTRACT.read_text(encoding="utf-8"))
    redacted_review = json.loads(REDACTED_REVIEW.read_text(encoding="utf-8"))
    dispatch_decision = json.loads(DISPATCH_DECISION_READINESS.read_text(encoding="utf-8"))
    supervision_contract = json.loads(OPERATOR_SUPERVISION_CONTRACT.read_text(encoding="utf-8"))

    assert packet["operator_input_contract_status"] == "satisfied_for_real_artifact_review"
    assert input_contract["operator_input_contract_status"] == "satisfied_for_real_artifact_review"
    assert input_contract["blocked_reasons"] == []
    assert input_contract["dispatchable"] is False
    assert input_contract["ready_for_dispatch"] is False
    assert input_contract["live_action_allowed"] is False
    assert packet["operator_source_artifact_kind"] == "real_operator_artifact"
    assert packet["operator_source_artifact_real_claimed"] is True
    assert packet["real_operator_artifact_present"] is True
    assert packet["real_operator_artifact_intake_ready"] is True
    assert packet["fixture_vs_real_separation_enforced"] is True
    assert packet["non_real_fixture"] is False
    assert packet["fixture_only"] is False
    assert live_preflight["live_preflight_status"] == "ready_for_real_operator_artifact_review_not_dispatch"
    assert packet["redacted_operator_review_status"] == "ready_for_redacted_operator_review_not_dispatch"
    assert packet["operator_review_decision_status"] == "blocked"
    assert redacted_review["redacted_operator_review_status"] == "ready_for_redacted_operator_review_not_dispatch"
    assert redacted_review["redacted_review_packet_ready"] is True
    assert redacted_review["body_value_stored"] is False
    assert redacted_review["go_phrase_value_stored"] is False
    assert redacted_review["dispatchable"] is False
    assert live_preflight["blocked_reasons"] == []
    assert fixture_review["fixture_review_status"] == "blocked"
    assert fixture_review["real_operator_artifact_claimed"] is True
    assert packet["live_action_allowed"] is False
    assert packet["request_envelope_executable"] is False
    assert supervision_contract["operator_supervision_contract_status"] == "blocked"
    assert supervision_contract["dispatchable"] is False
    assert "blocked_operator_review_decision_artifact_missing" in supervision_contract["blocked_reasons"]
    assert GO_PHRASE not in PACKET.read_text(encoding="utf-8")
    assert "present-marker-not-read" not in PACKET.read_text(encoding="utf-8")
    assert "Capital Chronicle supervised Discord pilot real operator artifact" not in LIVE_PREFLIGHT.read_text(encoding="utf-8")
    assert "Capital Chronicle supervised Discord pilot real operator artifact" not in REDACTED_REVIEW.read_text(encoding="utf-8")
    _clean_inbox()
    build_operator_source_go_phrase_intake()


def test_conflicting_fixture_and_real_markers_block(monkeypatch) -> None:
    _clean_inbox()
    _present_keys(monkeypatch)
    (INBOX / "operator_source_conflict.json").write_text(
        json.dumps(
            {
                "real_operator_artifact_claimed": True,
                "non_real_fixture": True,
                "fixture_only": True,
                "not_public_postable": True,
                "body": "Capital Chronicle supervised Discord pilot conflict artifact.",
                "go_phrase": GO_PHRASE,
                "destination_label": "discord-live-announcements",
                "destination_binding_confirmed": True,
                "kill_switch_active": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    packet = build_operator_source_go_phrase_intake()
    live_preflight = json.loads(LIVE_PREFLIGHT.read_text(encoding="utf-8"))

    assert packet["operator_source_artifact_kind"] == "ambiguous_or_conflicting_artifact"
    assert packet["fixture_vs_real_separation_enforced"] is False
    assert "blocked_conflicting_fixture_and_real_artifact_markers" in packet["blocked_reasons"]
    assert "blocked_fixture_vs_real_separation_failed" in live_preflight["blocked_reasons"]
    assert packet["ready_for_dispatch"] is False
    _clean_inbox()
    build_operator_source_go_phrase_intake()


def test_fixture_example_is_safe_and_non_real() -> None:
    _clean_inbox()
    build_operator_source_go_phrase_intake()
    fixture = json.loads(FIXTURE_EXAMPLE.read_text(encoding="utf-8"))
    assert fixture["non_real_fixture"] is True
    assert fixture["fixture_only"] is True
    assert fixture["not_public_postable"] is True
    assert fixture["real_operator_artifact_claimed"] is False
    assert "Non-real fixture" in fixture["fixture_caveat"]


def test_adapter_sync_and_ui_surfaces() -> None:
    build_operator_source_go_phrase_intake()
    generate_operator_source_go_phrase_intake_adapter()
    assert generate_operator_source_go_phrase_intake_adapter(verify_only=True) == {
        "adapter_in_sync": True,
        "packet_hash_matches": True,
    }
    assert "discordOperatorSourceArtifactFixtureReview" in ADAPTER.read_text(encoding="utf-8")
    assert "discordLivePreflightEvidence" in ADAPTER.read_text(encoding="utf-8")
    assert "discordOperatorInputContract" in ADAPTER.read_text(encoding="utf-8")
    assert "discordRedactedOperatorReviewPacket" in ADAPTER.read_text(encoding="utf-8")
    assert "discordOperatorReviewDecisionPacket" in ADAPTER.read_text(encoding="utf-8")
    assert "discordDispatchDecisionReadiness" in ADAPTER.read_text(encoding="utf-8")
    assert "discordDispatchRoutePreview" in ADAPTER.read_text(encoding="utf-8")
    assert "discordOperatorSupervisionContract" in ADAPTER.read_text(encoding="utf-8")
    combined = "\n".join(path.read_text(encoding="utf-8") for path in SURFACES)
    assert combined.count("DiscordOperatorSourceGoPhraseIntakePanel") >= len(SURFACES)
    panel = (ROOT / "ui" / "contentops_v5" / "src" / "views" / "DiscordOperatorSourceGoPhraseIntakePanel.tsx").read_text(encoding="utf-8")
    for term in [
        "operator_source_go_phrase_intake_status=blocked",
        "operator_source_artifact_kind=",
        "operator_source_artifact_real_claimed=",
        "non_real_fixture=",
        "fixture_only=",
        "not_public_postable=",
        "operator_go_phrase_value_stored=false",
        "dry_run_envelope_normalization_performed=true",
        "dry_run_request_envelope_preview_created=true",
        "dry_run_envelope_value_stored=false",
        "request_envelope_executable=false",
        "dispatch_attempted=false",
        "webhook_request_count=0",
        "ready_for_dispatch=false",
        "live_action_allowed=false",
        "credential_value_read_made=false",
        "env_value_read_made=false",
        "webhook_validation_performed=false",
        "destination_proof_id=",
        "kill_switch_evidence_id=",
        "credential_presence_evidence_id=",
        "fixture_review_id=",
        "fixture_review_hash=",
        "fixture_review_status=",
        "fixture_review_ready=",
        "redacted_operator_review_id=",
        "redacted_operator_review_hash=",
        "redacted_operator_review_status=",
        "redacted_review_packet_ready=",
        "redaction_performed=",
        "redaction_fields=",
        "redacted_body_value_stored=",
        "redacted_go_phrase_value_stored=",
        "redacted_webhook_url_value_stored=",
        "redacted_credential_value_stored=",
        "redacted_review_blocked_reasons=",
        "operator_review_decision_id=",
        "operator_review_decision_hash=",
        "operator_review_decision_status=",
        "operator_review_decision_available=",
        "operator_review_decision_approved=",
        "operator_review_decision_rejected=",
        "operator_review_decision_held=",
        "operator_review_decision_value=",
        "operator_review_decision_scope=",
        "operator_review_decision_phrase_valid=",
        "operator_review_decision_notes_value_stored=",
        "operator_review_decision_blocked_reasons=",
        "dispatch_decision_readiness_id=",
        "dispatch_decision_readiness_hash=",
        "dispatch_decision_readiness_status=",
        "dispatch_decision_approval_route_candidate_ready_not_dispatch=",
        "dispatch_decision_rejection_route_recorded_not_dispatch=",
        "dispatch_decision_hold_route_recorded_not_dispatch=",
        "dispatch_decision_tier_model=",
        "automation_first_alignment=",
        "jim_final_authority_required=",
        "supervised_live_edge_required=",
        "dispatch_decision_request_envelope_executable=",
        "dispatch_decision_dispatchable=",
        "dispatch_decision_ready_for_dispatch=",
        "dispatch_decision_live_action_allowed=",
        "dispatch_decision_blocked_reasons=",
        "dispatch_route_preview_id=",
        "dispatch_route_preview_hash=",
        "dispatch_route_preview_status=",
        "dispatch_route_class=",
        "dispatch_route_selection_reason=",
        "route_preview_ready_not_dispatch=",
        "dispatch_route_request_envelope_executable=",
        "dispatch_route_dispatchable=",
        "dispatch_route_ready_for_dispatch=",
        "dispatch_route_live_action_allowed=",
        "dispatch_route_blocked_reasons=",
        "operator_supervision_contract_id=",
        "operator_supervision_contract_hash=",
        "operator_supervision_contract_status=",
        "operator_supervision_state=",
        "operator_supervision_contract_ready_not_dispatch=",
        "operator_supervision_jim_final_authority_required=",
        "operator_supervision_jim_must_supervise_live_edge=",
        "operator_supervision_route_class=",
        "operator_supervision_required_actions=",
        "operator_supervision_required_artifacts=",
        "operator_supervision_future_exact_live_scope_artifact_required=",
        "operator_supervision_future_exact_live_scope_artifact_present=",
        "operator_supervision_request_envelope_executable=",
        "operator_supervision_dispatchable=",
        "operator_supervision_ready_for_dispatch=",
        "operator_supervision_live_action_allowed=",
        "operator_supervision_webhook_validation_performed=",
        "operator_supervision_blocked_reasons=",
        "pre_dispatch_readiness_id=",
        "normalized_pre_dispatch_readiness_evaluated=true",
        "real_operator_artifact_present=",
        "real_operator_artifact_intake_ready=",
        "fixture_vs_real_separation_enforced=",
        "operator_input_contract_id=",
        "operator_input_contract_hash=",
        "operator_input_contract_status=",
        "operator_input_contract_required_inbox_path=",
        "operator_input_contract_required_json_fields=",
        "operator_input_contract_forbidden_fixture_markers=",
        "fixture_can_satisfy_contract=",
        "operator_input_contract_blocked_reasons=",
        "live_preflight_id=",
        "live_preflight_hash=",
        "live_preflight_status=",
        "live_preflight_blocked_reasons=",
        "operator_review_ready=",
    ]:
        assert term in panel


def _write_real_source() -> None:
    (INBOX / "operator_source_real.json").write_text(
        json.dumps(
            {
                "artifact_kind": "discord_operator_source_artifact_v0",
                "real_operator_artifact_claimed": True,
                "non_real_fixture": False,
                "fixture_only": False,
                "not_public_postable": False,
                "body": "Capital Chronicle supervised Discord pilot real operator artifact for review decision.",
                "go_phrase": GO_PHRASE,
                "destination_label": "discord-live-announcements",
                "destination_binding_confirmed": True,
                "kill_switch_active": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def test_valid_operator_review_decisions_parse_without_dispatch(monkeypatch) -> None:
    for decision in ["approve", "reject", "hold"]:
        _clean_inbox()
        _present_keys(monkeypatch)
        _write_real_source()
        first = build_operator_source_go_phrase_intake()
        (OPERATOR_REVIEW_DECISION_INBOX / "decision.json").write_text(
            json.dumps(
                {
                    "redacted_operator_review_id": first["redacted_operator_review_id"],
                    "redacted_operator_review_hash": first["redacted_operator_review_hash"],
                    "decision": decision,
                    "decision_scope": DECISION_SCOPE,
                    "decision_phrase": DECISION_PHRASES[decision],
                    "operator_id": "operator-jim",
                    "created_at_manual": "2026-07-03T00:00:00+07:00",
                    "notes": "Reviewed redacted packet only.",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        packet = build_operator_source_go_phrase_intake()
        review_decision = json.loads(OPERATOR_REVIEW_DECISION.read_text(encoding="utf-8"))
        dispatch_decision = json.loads(DISPATCH_DECISION_READINESS.read_text(encoding="utf-8"))
        route_preview = json.loads(DISPATCH_ROUTE_PREVIEW.read_text(encoding="utf-8"))
        supervision_contract = json.loads(OPERATOR_SUPERVISION_CONTRACT.read_text(encoding="utf-8"))
        assert packet["operator_review_decision_status"] == "decision_recorded_not_dispatch"
        assert review_decision["operator_review_decision_available"] is True
        assert review_decision["operator_review_decision_approved"] is (decision == "approve")
        assert review_decision["operator_review_decision_rejected"] is (decision == "reject")
        assert review_decision["operator_review_decision_held"] is (decision == "hold")
        assert review_decision["dispatchable"] is False
        assert review_decision["ready_for_dispatch"] is False
        assert review_decision["live_action_allowed"] is False
        assert review_decision["notes_value_stored"] is False
        expected_status = {"approve": "ready_for_approval_route_review_not_dispatch", "reject": "rejected_not_dispatch", "hold": "held_not_dispatch"}[decision]
        assert dispatch_decision["dispatch_decision_readiness_status"] == expected_status
        assert dispatch_decision["approval_route_candidate_ready_not_dispatch"] is (decision == "approve")
        assert dispatch_decision["rejection_route_recorded_not_dispatch"] is (decision == "reject")
        assert dispatch_decision["hold_route_recorded_not_dispatch"] is (decision == "hold")
        assert dispatch_decision["automation_first_alignment"] is True
        assert dispatch_decision["jim_final_authority_required"] is True
        assert dispatch_decision["supervised_live_edge_required"] is True
        assert dispatch_decision["request_envelope_executable"] is False
        assert dispatch_decision["dispatchable"] is False
        assert dispatch_decision["ready_for_dispatch"] is False
        assert dispatch_decision["live_action_allowed"] is False
        assert route_preview["route_class"] == ("supervised_webhook" if decision == "approve" else "deferred_blocked")
        assert route_preview["route_preview_ready_not_dispatch"] is (decision == "approve")
        assert route_preview["dispatchable"] is False
        assert route_preview["ready_for_dispatch"] is False
        assert route_preview["live_action_allowed"] is False
        assert route_preview["webhook_validation_performed"] is False
        assert supervision_contract["operator_supervision_contract_status"] == ("ready_for_operator_supervision_not_dispatch" if decision == "approve" else "blocked")
        assert supervision_contract["operator_supervision_contract_ready_not_dispatch"] is (decision == "approve")
        assert supervision_contract["route_class"] == ("supervised_webhook" if decision == "approve" else "deferred_blocked")
        assert supervision_contract["future_exact_live_scope_artifact_required"] is True
        assert supervision_contract["future_exact_live_scope_artifact_present"] is False
        assert supervision_contract["dispatchable"] is False
        assert supervision_contract["ready_for_dispatch"] is False
        assert supervision_contract["live_action_allowed"] is False
        assert supervision_contract["webhook_validation_performed"] is False
        assert "Reviewed redacted packet only." not in OPERATOR_REVIEW_DECISION.read_text(encoding="utf-8")
    _clean_inbox()
    build_operator_source_go_phrase_intake()


def test_operator_review_decision_wrong_link_or_phrase_blocks(monkeypatch) -> None:
    _clean_inbox()
    _present_keys(monkeypatch)
    _write_real_source()
    first = build_operator_source_go_phrase_intake()
    (OPERATOR_REVIEW_DECISION_INBOX / "decision.json").write_text(
        json.dumps(
            {
                "redacted_operator_review_id": first["redacted_operator_review_id"],
                "redacted_operator_review_hash": "wrong",
                "decision": "approve",
                "decision_scope": DECISION_SCOPE,
                "decision_phrase": "wrong",
                "operator_id": "operator-jim",
                "created_at_manual": "2026-07-03T00:00:00+07:00",
                "notes": "Reviewed redacted packet only.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    build_operator_source_go_phrase_intake()
    review_decision = json.loads(OPERATOR_REVIEW_DECISION.read_text(encoding="utf-8"))
    dispatch_decision = json.loads(DISPATCH_DECISION_READINESS.read_text(encoding="utf-8"))
    assert review_decision["operator_review_decision_status"] == "blocked"
    assert "blocked_operator_review_decision_redacted_review_hash_mismatch" in review_decision["blocked_reasons"]
    assert "blocked_operator_review_decision_phrase_invalid" in review_decision["blocked_reasons"]
    assert review_decision["dispatchable"] is False
    _clean_inbox()
    build_operator_source_go_phrase_intake()


def test_operator_supervision_contract_evidence_surfaces_stay_in_sync(monkeypatch) -> None:
    _clean_inbox()
    _present_keys(monkeypatch)
    packet = build_operator_source_go_phrase_intake()
    generate_operator_source_go_phrase_intake_adapter()

    contract = json.loads(OPERATOR_SUPERVISION_CONTRACT.read_text(encoding="utf-8"))
    safety = json.loads((PACKET_DIR / "operator_source_go_phrase_safety_signature.json").read_text(encoding="utf-8"))
    adapter = ADAPTER.read_text(encoding="utf-8")
    status_md = (ROOT / "docs" / "status" / "CURRENT_PROJECT_STATUS.md").read_text(encoding="utf-8")
    status_json = json.loads((ROOT / "docs" / "status" / "current_project_status.json").read_text(encoding="utf-8"))

    contract_id = contract["operator_supervision_contract_id"]
    contract_hash = contract["operator_supervision_contract_hash"]
    assert packet["operator_supervision_contract_id"] == contract_id
    assert packet["operator_supervision_contract_hash"] == contract_hash
    assert safety["operator_supervision_contract_id"] == contract_id
    assert safety["operator_supervision_contract_hash"] == contract_hash
    assert adapter.count(contract_id) == 3
    assert adapter.count(contract_hash) == 3
    assert contract_id in status_md
    assert contract_hash in status_md
    assert contract_id in status_json["latest_evidence_summary"]
    assert contract_hash in status_json["latest_evidence_summary"]
    assert generate_operator_source_go_phrase_intake_adapter(verify_only=True)["adapter_in_sync"] is True
