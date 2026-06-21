from __future__ import annotations

from pathlib import Path

from live_contentops.v5_manual_export_pilot_verification_contract import (
    REQUIRED_PLATFORM_TARGETS,
    SOURCE_READ_MODEL_PACKET_HASH,
    build_v5_manual_export_pilot_verification_packet,
)


FORBIDDEN_SOURCE_TOKENS = (
    "import os",
    "os.environ",
    ".getenv(",
    "import dotenv",
    "from dotenv",
    "import requests",
    "import httpx",
    "urllib.request",
    "socket.socket",
    "subprocess.",
)


def test_v5_manual_export_packet_is_deterministic() -> None:
    first = build_v5_manual_export_pilot_verification_packet()
    second = build_v5_manual_export_pilot_verification_packet()

    assert first.packet_hash == second.packet_hash
    assert first.export_package_id == second.export_package_id
    assert first.source_read_model_packet_hash == SOURCE_READ_MODEL_PACKET_HASH
    assert first.generated_at_epoch == 0


def test_required_targets_are_manual_only_and_not_dispatchable() -> None:
    packet = build_v5_manual_export_pilot_verification_packet()
    targets = {target.target_id: target for target in packet.platform_targets}

    for target_id in REQUIRED_PLATFORM_TARGETS:
        target = targets[target_id]
        assert target.manual_only is True
        assert target.not_live is True
        assert target.no_api is True
        assert target.no_credentials is True
        assert target.no_scheduler is True
        assert target.public_postable is False
        assert target.dispatch_ready is False
        assert target.not_public_postable_until_operator_action_outside_system is True


def test_copy_blocks_are_redacted_draft_only_exports() -> None:
    packet = build_v5_manual_export_pilot_verification_packet()

    assert len(packet.manual_copy_blocks) == 4
    for block in packet.manual_copy_blocks:
        assert block.draft_only is True
        assert block.manual_export_only is True
        assert block.no_fake_live_market_data is True
        assert block.no_secrets is True
        assert block.no_raw_response_bodies is True
        assert "api call" not in block.copy_text.lower()
        assert "credential value" not in block.copy_text.lower()


def test_placeholders_are_empty_and_local_only() -> None:
    packet = build_v5_manual_export_pilot_verification_packet()

    assert packet.manual_publish_url_placeholder.value == ""
    assert packet.manual_metrics_placeholder.value == ""
    assert packet.review_signature_placeholder.signature_value == ""
    assert packet.review_signature_placeholder.cryptographic_signature is False
    assert packet.review_signature_placeholder.uses_secret_material is False
    assert packet.pilot_verification_status == "blocked_pending_operator_manual_review"


def test_disabled_live_dispatch_state_blocks_every_live_action() -> None:
    packet = build_v5_manual_export_pilot_verification_packet()
    state = packet.disabled_live_dispatch_state

    assert state.live_dispatch_enabled is False
    assert state.publish_enabled is False
    assert state.send_enabled is False
    assert state.schedule_enabled is False
    assert state.connect_account_enabled is False
    assert state.verify_credentials_enabled is False
    assert state.sync_platform_enabled is False
    assert packet.safety_flags["env_read"] is False
    assert packet.safety_flags["credential_values_accessed"] is False
    assert packet.safety_flags["platform_api_called"] is False
    assert packet.safety_flags["posting_performed"] is False


def test_contract_source_does_not_import_live_or_secret_access_paths() -> None:
    source = Path("live_contentops/v5_manual_export_pilot_verification_contract.py").read_text(encoding="utf-8")

    for token in FORBIDDEN_SOURCE_TOKENS:
        assert token not in source
