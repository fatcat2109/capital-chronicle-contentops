import json
from pathlib import Path
from live_contentops import operator_approval_capture_v6 as capture


def write_hash_inputs(tmp_path: Path) -> None:
    payload_dir = tmp_path / "V6_PAYLOAD_PREVIEW_HASH"
    payload_dir.mkdir(parents=True, exist_ok=True)
    (payload_dir / "payload_preview_hash_packet.json").write_text(json.dumps({
        "payload_hash_created": True,
        "exact_payload_preview_created": True,
        "payload_preview_status": "READY_FOR_OPERATOR_REVIEW",
        "payload_hash": "a" * 64,
    }, indent=2), encoding="utf-8")
    (payload_dir / "payload_preview_exact_review.json").write_text(json.dumps({
        "payload_preview_id": "preview_real",
        "payload_body_redacted": True,
    }, indent=2), encoding="utf-8")
    (payload_dir / "payload_hash_record.json").write_text(json.dumps({
        "payload_hash": "a" * 64,
    }, indent=2), encoding="utf-8")


def test_capture_outputs_inert_defaults(tmp_path):
    write_hash_inputs(tmp_path)

    rc = capture.main(["--output-dir", str(tmp_path), "--binding-dir", str(tmp_path / "BINDING")])
    assert rc == 0

    out_dir = tmp_path / "V6_OPERATOR_APPROVAL_CAPTURE"
    packet = json.loads((out_dir / "operator_approval_capture_packet.json").read_text(encoding="utf-8"))
    validation = json.loads((out_dir / "operator_approval_capture_validation_report.json").read_text(encoding="utf-8"))

    assert packet["approval_capture_status"] == "AWAITING_OPERATOR_ACTION"
    assert packet["operator_approval_captured"] is False
    assert packet["operator_signature_created"] is False
    assert packet["operator_signature_valid"] is False
    assert packet["payload_hash_displayed"] is True
    assert packet["exact_payload_preview_displayed"] is True
    assert packet["approval_valid_for_dispatch"] is False
    assert packet["dispatch_allowed_now"] is False
    assert packet["live_write_allowed_now"] is False
    assert packet["outbox_entry_created"] is False
    assert packet["destination_binding_complete"] is False
    assert packet["credentials_hydrated"] is False
    assert packet["browser_session_started"] is False
    assert packet["public_postable"] is False
    assert packet["kill_switch_active"] is True
    assert packet["next_recommended_task"] == "TASK_CONTENTOPS_V6_OPERATOR_SIGN_PAYLOAD_HASH_MANUAL_STEP"

    assert validation["operator_signature_present"] is False
    assert validation["operator_signature_valid"] is False
    assert "operator_approval_incomplete" in validation["validation_blockers"]


def test_capture_accepts_valid_signature(tmp_path):
    write_hash_inputs(tmp_path)
    capture_dir = tmp_path / "V6_OPERATOR_APPROVAL_CAPTURE"
    binding_dir = tmp_path / "V6_OPERATOR_APPROVAL_SIGNATURE_BINDING"
    capture_dir.mkdir(parents=True, exist_ok=True)
    binding_dir.mkdir(parents=True, exist_ok=True)

    # Write a valid mock signature to capture local path
    (capture_dir / "operator_approval_signature.local.json").write_text(json.dumps({
        "operator_id": "JIM_OPERATOR",
        "approval_decision": "APPROVED",
        "payload_hash": "a" * 64,
        "signed_at": "2026-06-28T09:30:00Z",
        "valid_for_dispatch": False,
        "revoked": False,
        "is_local_only": True
    }, indent=2), encoding="utf-8")

    rc = capture.main(["--output-dir", str(tmp_path), "--binding-dir", str(binding_dir)])
    assert rc == 0

    packet = json.loads((capture_dir / "operator_approval_capture_packet.json").read_text(encoding="utf-8"))
    assert packet["approval_capture_status"] == "SIGNATURE_VALIDATED_REVIEW_ONLY"
    assert packet["operator_approval_captured"] is True
    assert packet["operator_signature_valid"] is True
    assert packet["approval_valid_for_dispatch"] is False
    assert packet["dispatch_allowed_now"] is False


def test_capture_rejects_hash_mismatch(tmp_path):
    write_hash_inputs(tmp_path)
    capture_dir = tmp_path / "V6_OPERATOR_APPROVAL_CAPTURE"
    capture_dir.mkdir(parents=True, exist_ok=True)

    (capture_dir / "operator_approval_signature.local.json").write_text(json.dumps({
        "operator_id": "JIM_OPERATOR",
        "approval_decision": "APPROVED",
        "payload_hash": "WRONG_HASH",
        "signed_at": "2026-06-28T09:30:00Z",
        "valid_for_dispatch": False,
        "revoked": False
    }, indent=2), encoding="utf-8")

    capture.main(["--output-dir", str(tmp_path), "--binding-dir", str(tmp_path / "BINDING")])
    packet = json.loads((capture_dir / "operator_approval_capture_packet.json").read_text(encoding="utf-8"))
    assert packet["approval_capture_status"] == "SIGNATURE_INVALID"
    assert packet["operator_approval_captured"] is False
    assert "payload_hash_mismatch" in packet["capture_blockers"]


def test_capture_rejects_non_approved_decision(tmp_path):
    write_hash_inputs(tmp_path)
    capture_dir = tmp_path / "V6_OPERATOR_APPROVAL_CAPTURE"
    capture_dir.mkdir(parents=True, exist_ok=True)

    (capture_dir / "operator_approval_signature.local.json").write_text(json.dumps({
        "operator_id": "JIM_OPERATOR",
        "approval_decision": "PENDING",
        "payload_hash": "a" * 64,
        "signed_at": "2026-06-28T09:30:00Z",
        "valid_for_dispatch": False,
        "revoked": False
    }, indent=2), encoding="utf-8")

    capture.main(["--output-dir", str(tmp_path), "--binding-dir", str(tmp_path / "BINDING")])
    packet = json.loads((capture_dir / "operator_approval_capture_packet.json").read_text(encoding="utf-8"))
    assert "operator_approval_not_approved" in packet["capture_blockers"]


def test_capture_rejects_premature_dispatch_validity(tmp_path):
    write_hash_inputs(tmp_path)
    capture_dir = tmp_path / "V6_OPERATOR_APPROVAL_CAPTURE"
    capture_dir.mkdir(parents=True, exist_ok=True)

    (capture_dir / "operator_approval_signature.local.json").write_text(json.dumps({
        "operator_id": "JIM_OPERATOR",
        "approval_decision": "APPROVED",
        "payload_hash": "a" * 64,
        "signed_at": "2026-06-28T09:30:00Z",
        "valid_for_dispatch": True,
        "revoked": False
    }, indent=2), encoding="utf-8")

    capture.main(["--output-dir", str(tmp_path), "--binding-dir", str(tmp_path / "BINDING")])
    packet = json.loads((capture_dir / "operator_approval_capture_packet.json").read_text(encoding="utf-8"))
    assert "dispatch_validity_claimed_too_early" in packet["capture_blockers"]


def test_capture_rejects_malformed_signed_at(tmp_path):
    write_hash_inputs(tmp_path)
    capture_dir = tmp_path / "V6_OPERATOR_APPROVAL_CAPTURE"
    capture_dir.mkdir(parents=True, exist_ok=True)

    (capture_dir / "operator_approval_signature.local.json").write_text(json.dumps({
        "operator_id": "JIM_OPERATOR",
        "approval_decision": "APPROVED",
        "payload_hash": "a" * 64,
        "signed_at": "bad-timestamp",
        "valid_for_dispatch": False,
        "revoked": False
    }, indent=2), encoding="utf-8")

    capture.main(["--output-dir", str(tmp_path), "--binding-dir", str(tmp_path / "BINDING")])
    packet = json.loads((capture_dir / "operator_approval_capture_packet.json").read_text(encoding="utf-8"))
    assert "operator_signature_timestamp_missing_or_invalid" in packet["capture_blockers"]


def test_capture_rejects_unsafe_material(tmp_path):
    write_hash_inputs(tmp_path)
    capture_dir = tmp_path / "V6_OPERATOR_APPROVAL_CAPTURE"
    capture_dir.mkdir(parents=True, exist_ok=True)

    (capture_dir / "operator_approval_signature.local.json").write_text(json.dumps({
        "operator_id": "JIM_OPERATOR",
        "approval_decision": "APPROVED",
        "payload_hash": "a" * 64,
        "signed_at": "2026-06-28T09:30:00Z",
        "valid_for_dispatch": False,
        "revoked": False,
        "secret_keys": "discord.com/api/webhooks/12345"
    }, indent=2), encoding="utf-8")

    capture.main(["--output-dir", str(tmp_path), "--binding-dir", str(tmp_path / "BINDING")])
    packet = json.loads((capture_dir / "operator_approval_capture_packet.json").read_text(encoding="utf-8"))
    assert "unsafe_signature_material" in packet["capture_blockers"]


def test_module_contains_no_forbidden_behavior():
    attrs = dir(capture)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs
