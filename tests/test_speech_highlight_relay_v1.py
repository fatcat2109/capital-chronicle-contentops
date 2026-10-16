import hashlib
import json
from pathlib import Path

import pytest

from live_contentops import speech_highlight_relay_v1 as relay


ROOT = Path(__file__).resolve().parents[1]
PACKET_PATH = ROOT / "video" / "speech_highlight_relay_v1" / "retained_replay_fed_20260729.json"


def _fixture_packet(tmp_path: Path) -> dict:
    packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
    media = tmp_path / "retained.mp4"
    transcript = tmp_path / "transcript.txt"
    rights_note = tmp_path / "rights-note.md"
    media.write_bytes(b"local fixture media bytes")
    transcript.write_text(packet["selection"]["exact_quote"], encoding="utf-8")
    rights_note.write_text("historical note only", encoding="utf-8")
    packet["media"]["file"] = media.name
    packet["media"]["sha256"] = hashlib.sha256(media.read_bytes()).hexdigest()
    packet["transcript"]["document"] = {
        "file": transcript.name,
        "sha256": hashlib.sha256(transcript.read_bytes()).hexdigest(),
        "format": "UTF8_TEXT",
    }
    packet["rights"]["historical_note"] = {
        "file": rights_note.name,
        "sha256": hashlib.sha256(rights_note.read_bytes()).hexdigest(),
    }
    binding = relay.source_binding(packet)
    packet["rights"]["source_binding_sha256"] = binding
    packet["selection"]["source_binding_sha256"] = binding
    packet["selection"]["third_party_review"]["source_binding_sha256"] = binding
    return packet


def test_retained_packet_validates_without_media_probe(tmp_path):
    packet = _fixture_packet(tmp_path)
    result = relay.validate_packet(packet, tmp_path, inspect_media=False)

    assert result["status"] == "INTEGRITY_AND_TEXT_CHECKED_PRIVATE_REVIEW_ONLY"
    assert result["discovery_status"] == "RETAINED_REPLAY_ONLY"
    assert result["production_eligible"] is False
    assert result["legal_clearance_status"] == "NOT_VERIFIED"
    assert result["audio_listening_status"] == "NOT_VERIFIED"


def test_unknown_publisher_cannot_inherit_retained_rights(tmp_path):
    packet = _fixture_packet(tmp_path)
    packet["publisher"] = "Unknown publisher"

    with pytest.raises(relay.SpeechRelayError, match="Rights review scope"):
        relay.validate_packet(packet, tmp_path, inspect_media=False)


def test_affirmative_rights_and_production_are_rejected(tmp_path):
    packet = _fixture_packet(tmp_path)
    packet["rights"]["triage_state"] = "REUSE_CLEAR"
    packet["rights"]["production_eligible"] = True

    with pytest.raises(relay.SpeechRelayError, match="Private review only"):
        relay.validate_packet(packet, tmp_path, inspect_media=False)


def test_quote_without_protected_qualifier_is_rejected(tmp_path):
    packet = _fixture_packet(tmp_path)
    packet["selection"]["exact_quote"] = packet["selection"]["exact_quote"].replace("generally ", "")

    with pytest.raises(relay.SpeechRelayError, match="Protected qualifiers"):
        relay.validate_packet(packet, tmp_path, inspect_media=False)


def test_cli_has_no_discovery_default():
    with pytest.raises(SystemExit) as exc:
        relay.speech_highlight_relay_command(["--discover"])

    assert exc.value.code == 2


def test_package_controls_are_immutable(tmp_path):
    packet = _fixture_packet(tmp_path)
    packet["publication_control"]["unknown_writes"] = 1

    with pytest.raises(relay.PublicWriteProhibitedError, match="PUBLICATION_HOLD"):
        relay.validate_packet(packet, tmp_path, inspect_media=False)
