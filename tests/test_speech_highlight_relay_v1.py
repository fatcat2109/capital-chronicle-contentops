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
    binding = relay.source_binding(packet)
    packet["rights"]["source_binding_sha256"] = binding
    packet["selection"]["source_binding_sha256"] = binding
    packet["selection"]["third_party_review"]["source_binding_sha256"] = binding

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


def _review_package_fixture(tmp_path: Path) -> Path:
    packet = _fixture_packet(tmp_path)
    package = tmp_path / "package"
    package.mkdir()
    verification = relay.validate_packet(packet, tmp_path, inspect_media=False)
    (package / "source_packet.json").write_text(json.dumps(packet, indent=2), encoding="utf-8")
    (package / "source_verification.json").write_text(json.dumps(verification, indent=2), encoding="utf-8")
    (package / "rights_triage_manifest.json").write_text(json.dumps(packet["rights"], indent=2), encoding="utf-8")
    cues = verification["relative_cues"]
    transcript = {
        **packet["transcript"],
        "cues": cues,
        "exact_quote": packet["selection"]["exact_quote"],
        "text_match_is_audio_verification": False,
    }
    (package / "transcript_alignment_manifest.json").write_text(json.dumps(transcript, indent=2), encoding="utf-8")
    (package / "highlight_selection_manifest.json").write_text(
        json.dumps(packet["selection"], indent=2), encoding="utf-8"
    )
    for filename in relay.ARTIFACT_FILES.values():
        (package / filename).write_bytes(filename.encode("utf-8"))
    (package / "extracted_clip.mp4").write_bytes(b"clip")
    receipt = {
        "created_at": "2026-10-17T00:00:00+00:00",
        "media_probes": {"clean_master": {"fixture": "clean"}, "captioned_derivative": {"fixture": "captioned"}},
        "extracted_clip": relay.artifact_identity(package / "extracted_clip.mp4"),
        "audio_listening_status": "NOT_VERIFIED",
        "production_eligible": False,
        "publication_control": relay.PUBLICATION_CONTROL,
    }
    (package / "render_receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    relay.compose_private_review_packet(package, tmp_path)
    manifest = {
        "schema": relay.PACKAGE_SCHEMA,
        "source_binding_sha256": verification["source_binding_sha256"],
        "package_id": f"{packet['source_id']}:{packet['selection']['candidate_id']}",
        "publication_control": relay.PUBLICATION_CONTROL,
        "production_eligible": False,
        "artifacts": {key: relay.artifact_identity(package / filename) for key, filename in relay.ARTIFACT_FILES.items()},
        "manifest_hashes": {
            name: relay.sha256_file(package / name)
            for name in sorted(relay.MANIFEST_FILES | {relay.PRIVATE_REVIEW_PACKET_FILE})
        },
    }
    (package / "package_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return package


def test_source_binding_covers_provenance_clock_and_policy_reference(tmp_path):
    packet = _fixture_packet(tmp_path)
    original = relay.source_binding(packet)
    packet["provenance"]["full_event_mapping"] = "different retained clock"
    assert relay.source_binding(packet) != original
    packet = _fixture_packet(tmp_path)
    original = relay.source_binding(packet)
    packet["rights"]["policy_url"] = "https://example.test/changed-policy"
    assert relay.source_binding(packet) != original


def test_private_review_packet_rejects_provenance_or_policy_drift(tmp_path):
    package = _review_package_fixture(tmp_path)
    source_path = package / "source_packet.json"
    source = json.loads(source_path.read_text(encoding="utf-8"))
    source["provenance"]["full_event_mapping"] = "tampered retained clock"
    source_path.write_text(json.dumps(source, indent=2), encoding="utf-8")

    with pytest.raises(relay.SpeechRelayError, match="Rights review scope|Source verification"):
        relay.verify_private_review_packet(package, tmp_path)


def test_private_review_packet_rejects_render_output_hash_drift(tmp_path):
    package = _review_package_fixture(tmp_path)
    (package / relay.ARTIFACT_FILES["captioned_derivative"]).write_bytes(b"tampered output")

    with pytest.raises(relay.SpeechRelayError, match="body does not match bound package bytes"):
        relay.verify_private_review_packet(package, tmp_path)
