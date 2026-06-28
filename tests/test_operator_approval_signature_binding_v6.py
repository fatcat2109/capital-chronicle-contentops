import json
from pathlib import Path

from live_contentops import operator_approval_signature_binding_v6 as binding


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
    (payload_dir / "payload_hash_inputs_redacted.json").write_text(json.dumps({
        "hash_blocked": False,
    }, indent=2), encoding="utf-8")

    approval_dir = tmp_path / "V6_OPERATOR_APPROVAL_GATE"
    approval_dir.mkdir(parents=True, exist_ok=True)
    (approval_dir / "operator_approval_gate_packet.json").write_text(json.dumps({
        "approval_gate_status": "AWAITING_OPERATOR_SIGNATURE",
    }, indent=2), encoding="utf-8")
    (approval_dir / "operator_approval_review_packet.json").write_text(json.dumps({
        "review_required": True,
    }, indent=2), encoding="utf-8")
    (approval_dir / "operator_approval_signature_template.json").write_text(json.dumps({
        "valid_for_dispatch": False,
    }, indent=2), encoding="utf-8")


def test_signature_binding_outputs_inert_defaults(tmp_path):
    write_hash_inputs(tmp_path)

    rc = binding.main(["--output-dir", str(tmp_path)])
    assert rc == 0

    out_dir = tmp_path / "V6_OPERATOR_APPROVAL_SIGNATURE_BINDING"
    packet = json.loads((out_dir / "operator_signature_binding_packet.json").read_text(encoding="utf-8"))
    review = json.loads((out_dir / "operator_signature_binding_review_packet.json").read_text(encoding="utf-8"))
    template = json.loads((out_dir / "operator_signature_template.json").read_text(encoding="utf-8"))
    validation = json.loads((out_dir / "operator_signature_validation_report.json").read_text(encoding="utf-8"))

    assert packet["signature_binding_status"] == "AWAITING_OPERATOR_SIGNATURE"
    assert packet["payload_hash_bound"] is True
    assert packet["exact_payload_preview_bound"] is True
    assert packet["operator_signature_present"] is False
    assert packet["operator_signature_valid"] is False
    assert packet["approval_valid_for_dispatch"] is False
    assert packet["dispatch_allowed_now"] is False
    assert packet["public_postable"] is False
    assert packet["kill_switch_active"] is True
    assert packet["next_recommended_task"] == "TASK_CONTENTOPS_V6_OPERATOR_SIGN_PAYLOAD_HASH_MANUAL_STEP"

    assert review["dispatch_not_authorized"] is True
    assert review["live_write_not_authorized"] is True

    assert template["approval_decision"] == "PENDING"
    assert template["payload_hash"] == "a" * 64
    assert template["valid_for_dispatch"] is False
    assert template["revoked"] is False

    assert validation["operator_signature_present"] is False
    assert validation["operator_signature_valid"] is False
    assert "operator_approval_incomplete" in validation["validation_blockers"]


def test_signature_binding_accepts_valid_manual_signature(tmp_path):
    write_hash_inputs(tmp_path)
    sig_dir = tmp_path / "V6_OPERATOR_APPROVAL_SIGNATURE_BINDING"
    sig_dir.mkdir(parents=True, exist_ok=True)
    (sig_dir / "operator_signature.json").write_text(json.dumps({
        "operator_id": "JIM_OPERATOR",
        "approval_decision": "APPROVED",
        "payload_hash": "a" * 64,
        "signed_at": "2026-06-28T03:00:00Z",
        "valid_for_dispatch": False,
        "revoked": False,
    }, indent=2), encoding="utf-8")

    binding.main(["--output-dir", str(tmp_path)])
    packet = json.loads((sig_dir / "operator_signature_binding_packet.json").read_text(encoding="utf-8"))
    validation = json.loads((sig_dir / "operator_signature_validation_report.json").read_text(encoding="utf-8"))

    assert packet["signature_binding_status"] == "SIGNATURE_BOUND_REVIEW_ONLY"
    assert packet["operator_signature_present"] is True
    assert packet["operator_signature_valid"] is True
    assert validation["validation_blockers"] == []
    assert validation["approval_valid_for_dispatch"] is False


def test_signature_binding_rejects_early_dispatch_claim(tmp_path):
    write_hash_inputs(tmp_path)
    sig_dir = tmp_path / "V6_OPERATOR_APPROVAL_SIGNATURE_BINDING"
    sig_dir.mkdir(parents=True, exist_ok=True)
    (sig_dir / "operator_signature.json").write_text(json.dumps({
        "operator_id": "JIM_OPERATOR",
        "approval_decision": "APPROVED",
        "payload_hash": "a" * 64,
        "signed_at": "2026-06-28T03:00:00Z",
        "valid_for_dispatch": True,
        "revoked": False,
    }, indent=2), encoding="utf-8")

    binding.main(["--output-dir", str(tmp_path)])
    packet = json.loads((sig_dir / "operator_signature_binding_packet.json").read_text(encoding="utf-8"))
    validation = json.loads((sig_dir / "operator_signature_validation_report.json").read_text(encoding="utf-8"))

    assert packet["signature_binding_status"] == "AWAITING_OPERATOR_SIGNATURE"
    assert packet["operator_signature_valid"] is False
    assert "dispatch_validity_claimed_too_early" in validation["validation_blockers"]


def test_module_contains_no_forbidden_behavior():
    attrs = dir(binding)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs
