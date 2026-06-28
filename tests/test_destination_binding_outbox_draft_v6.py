import json
from pathlib import Path
from live_contentops import destination_binding_outbox_draft_v6 as dest_lane


def write_preview_inputs(tmp_path: Path) -> None:
    preview_dir = tmp_path / "V6_PAYLOAD_PREVIEW_HASH"
    preview_dir.mkdir(parents=True, exist_ok=True)
    (preview_dir / "payload_hash_record.json").write_text(json.dumps({
        "payload_hash": "a" * 64
    }, indent=2), encoding="utf-8")
    (preview_dir / "payload_preview_exact_review.json").write_text(json.dumps({
        "payload_preview_id": "mock_preview_v6_id",
        "payload_body_redacted": True
    }, indent=2), encoding="utf-8")


def test_default_state_blocks_awaiting_operator_signature(tmp_path):
    write_preview_inputs(tmp_path)

    rc = dest_lane.main(["--output-dir", str(tmp_path)])
    assert rc == 0

    out_dir = tmp_path / "V6_DESTINATION_BINDING_OUTBOX_DRAFT"
    packet = json.loads((out_dir / "destination_binding_outbox_draft_packet.json").read_text(encoding="utf-8"))
    validation = json.loads((out_dir / "outbox_draft_validation_report.json").read_text(encoding="utf-8"))

    assert packet["destination_outbox_status"] == "BLOCKED_AWAITING_OPERATOR_SIGNATURE"
    assert packet["operator_signature_valid"] is False
    assert packet["destination_binding_complete"] is False
    assert packet["outbox_draft_created"] is False
    assert packet["outbox_entry_created"] is False
    assert packet["outbox_dispatchable"] is False
    assert packet["approval_valid_for_dispatch"] is False
    assert packet["dispatch_allowed_now"] is False
    assert packet["live_write_allowed_now"] is False
    assert packet["credentials_hydrated"] is False
    assert packet["browser_session_started"] is False
    assert packet["public_postable"] is False
    assert packet["kill_switch_active"] is True
    assert packet["next_recommended_task"] == "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_CAPTURE_LOCAL_RUN_STEP"

    assert validation["operator_signature_valid"] is False
    assert "operator_signature_missing" in validation["validation_blockers"]


def test_synthetic_valid_signature_creates_draft_and_binds(tmp_path):
    write_preview_inputs(tmp_path)

    # Write a valid local signature into temporary capture location
    capture_dir = tmp_path / "V6_OPERATOR_APPROVAL_CAPTURE"
    capture_dir.mkdir(parents=True, exist_ok=True)
    (capture_dir / "operator_approval_signature.local.json").write_text(json.dumps({
        "operator_id": "JIM_OPERATOR",
        "approval_decision": "APPROVED",
        "payload_hash": "a" * 64,
        "signed_at": "2026-06-28T12:00:00Z",
        "valid_for_dispatch": False,
        "revoked": False
    }, indent=2), encoding="utf-8")

    rc = dest_lane.main(["--output-dir", str(tmp_path)])
    assert rc == 0

    out_dir = tmp_path / "V6_DESTINATION_BINDING_OUTBOX_DRAFT"
    packet = json.loads((out_dir / "destination_binding_outbox_draft_packet.json").read_text(encoding="utf-8"))
    draft = json.loads((out_dir / "outbox_draft_preview_packet.json").read_text(encoding="utf-8"))

    assert packet["destination_outbox_status"] == "OUTBOX_DRAFT_READY_FOR_REVIEW"
    assert packet["operator_signature_valid"] is True
    assert packet["destination_binding_complete"] is True
    assert packet["outbox_draft_created"] is True
    assert packet["outbox_dispatchable"] is False
    assert packet["next_recommended_task"] == "TASK_CONTENTOPS_V6_SUPERVISED_DISPATCH_READINESS_REVALIDATION_LANE_HEAVY_BATCH_V0"

    assert draft["outbox_draft_created"] is True
    assert draft["dispatchable"] is False
    assert draft["draft_details"]["body_preview"] == "mock_preview_v6_id"


def test_mismatched_signature_blocks_draft(tmp_path):
    write_preview_inputs(tmp_path)

    capture_dir = tmp_path / "V6_OPERATOR_APPROVAL_CAPTURE"
    capture_dir.mkdir(parents=True, exist_ok=True)
    (capture_dir / "operator_approval_signature.local.json").write_text(json.dumps({
        "operator_id": "JIM_OPERATOR",
        "approval_decision": "APPROVED",
        "payload_hash": "WRONG_HASH",
        "signed_at": "2026-06-28T12:00:00Z",
        "valid_for_dispatch": False,
        "revoked": False
    }, indent=2), encoding="utf-8")

    dest_lane.main(["--output-dir", str(tmp_path)])

    out_dir = tmp_path / "V6_DESTINATION_BINDING_OUTBOX_DRAFT"
    packet = json.loads((out_dir / "destination_binding_outbox_draft_packet.json").read_text(encoding="utf-8"))
    assert packet["destination_outbox_status"] == "SIGNATURE_INVALID_OUTBOX_BLOCKED"
    assert "payload_hash_mismatch" in packet["blockers"]


def test_destinations_contain_no_live_identifiers(tmp_path):
    write_preview_inputs(tmp_path)
    dest_lane.main(["--output-dir", str(tmp_path)])

    out_dir = tmp_path / "V6_DESTINATION_BINDING_OUTBOX_DRAFT"
    matrix = json.loads((out_dir / "destination_binding_review_matrix.json").read_text(encoding="utf-8"))

    for row in matrix:
        assert row["live_destination_bound"] is False
        assert row["destination_identifier_redacted_or_absent"] is True
        assert row["credential_hydrated"] is False
        assert row["dispatch_adapter_class"] == "not_enabled"
        assert "discord.com/api/webhooks" not in json.dumps(row)
        assert "token_value" not in json.dumps(row)


def test_module_contains_no_forbidden_behavior():
    attrs = dir(dest_lane)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs
