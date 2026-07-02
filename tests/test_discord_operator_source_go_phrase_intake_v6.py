"""Tests for V6 Discord operator source + GO phrase intake."""
from __future__ import annotations

import json
from pathlib import Path

from live_contentops.discord_operator_source_go_phrase_intake_v5_adapter_codegen_v6 import (
    generate_operator_source_go_phrase_intake_adapter,
)
from live_contentops.discord_operator_source_go_phrase_intake_v6 import (
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

    assert packet["intake_status"] == "ready_for_operator_review_not_dispatch"
    assert packet["operator_source_artifact_kind"] == "non_real_fixture"
    assert packet["operator_source_artifact_real_claimed"] is False
    assert packet["non_real_fixture"] is True
    assert packet["fixture_only"] is True
    assert packet["not_public_postable"] is True
    assert packet["operator_go_phrase_valid"] is True
    assert packet["operator_go_phrase_value_stored"] is False
    assert packet["dry_run_envelope_normalization_performed"] is True
    assert packet["dry_run_request_envelope_preview_created"] is True
    assert packet["dry_run_envelope_value_stored"] is False
    assert packet["fixture_review_status"] == "ready_for_fixture_review_not_dispatch"
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
        "pre_dispatch_readiness_id=",
        "normalized_pre_dispatch_readiness_evaluated=true",
        "operator_review_ready=",
    ]:
        assert term in panel
