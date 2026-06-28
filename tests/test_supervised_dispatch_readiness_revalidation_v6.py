import json
from pathlib import Path
from live_contentops import supervised_dispatch_readiness_revalidation_v6 as reval_lane


def write_test_inputs(tmp_path: Path, **kwargs) -> dict[str, Path]:
    paths = {}
    
    # 1. Capture packet
    cap_data = {
        "approval_capture_status": kwargs.get("approval_capture_status", "AWAITING_OPERATOR_ACTION"),
        "operator_signature_valid": kwargs.get("operator_signature_valid", False)
    }
    cap_path = tmp_path / "operator_approval_capture_packet.json"
    cap_path.write_text(json.dumps(cap_data, indent=2), encoding="utf-8")
    paths["capture_packet"] = cap_path
    
    # 2. Capture report
    paths["capture_report"] = tmp_path / "operator_approval_capture_validation_report.json"
    paths["capture_report"].write_text(json.dumps({"valid": False}, indent=2), encoding="utf-8")
    
    # 3. Sign packet
    sign_data = {
        "operator_signature_valid": kwargs.get("operator_signature_valid", False)
    }
    sign_path = tmp_path / "operator_signature_binding_packet.json"
    sign_path.write_text(json.dumps(sign_data, indent=2), encoding="utf-8")
    paths["sign_packet"] = sign_path
    
    # 4. Sign report
    paths["sign_report"] = tmp_path / "operator_signature_validation_report.json"
    paths["sign_report"].write_text(json.dumps({"valid": False}, indent=2), encoding="utf-8")
    
    # 5. Dest packet
    dest_data = {
        "destination_binding_complete": kwargs.get("destination_binding_complete", False),
        "outbox_draft_created": kwargs.get("outbox_draft_created", False)
    }
    dest_path = tmp_path / "destination_binding_outbox_draft_packet.json"
    dest_path.write_text(json.dumps(dest_data, indent=2), encoding="utf-8")
    paths["dest_packet"] = dest_path
    
    # 6. Dest matrix
    paths["dest_matrix"] = tmp_path / "destination_binding_review_matrix.json"
    paths["dest_matrix"].write_text(json.dumps([], indent=2), encoding="utf-8")
    
    # 7. Outbox preview
    paths["outbox_preview"] = tmp_path / "outbox_draft_preview_packet.json"
    paths["outbox_preview"].write_text(json.dumps({"created": False}, indent=2), encoding="utf-8")
    
    # 8. Outbox report
    paths["outbox_report"] = tmp_path / "outbox_draft_validation_report.json"
    paths["outbox_report"].write_text(json.dumps({"valid": False}, indent=2), encoding="utf-8")
    
    # 9. Payload hash
    paths["payload_hash"] = tmp_path / "payload_preview_hash_packet.json"
    paths["payload_hash"].write_text(json.dumps({"hash": "foo"}, indent=2), encoding="utf-8")
    
    # 10. Payload record
    paths["payload_record"] = tmp_path / "payload_hash_record.json"
    paths["payload_record"].write_text(json.dumps({"record": "bar"}, indent=2), encoding="utf-8")
    
    # 11. Upload bundle
    paths["upload_bundle"] = tmp_path / "project_sources_upload_bundle_packet.json"
    paths["upload_bundle"].write_text(json.dumps({"status": "READY"}, indent=2), encoding="utf-8")
    
    return paths


def test_default_committed_state_is_blocked(tmp_path):
    paths = write_test_inputs(tmp_path)
    
    rc = reval_lane.main([
        "--capture-packet", str(paths["capture_packet"]),
        "--capture-report", str(paths["capture_report"]),
        "--sign-packet", str(paths["sign_packet"]),
        "--sign-report", str(paths["sign_report"]),
        "--dest-packet", str(paths["dest_packet"]),
        "--dest-matrix", str(paths["dest_matrix"]),
        "--outbox-preview", str(paths["outbox_preview"]),
        "--outbox-report", str(paths["outbox_report"]),
        "--payload-hash", str(paths["payload_hash"]),
        "--payload-record", str(paths["payload_record"]),
        "--upload-bundle", str(paths["upload_bundle"]),
        "--output-dir", str(tmp_path)
    ])
    
    assert rc == 0
    
    packet = json.loads((tmp_path / "supervised_dispatch_readiness_packet.json").read_text(encoding="utf-8"))
    blockers = json.loads((tmp_path / "dispatch_readiness_blocker_matrix.json").read_text(encoding="utf-8"))
    report = json.loads((tmp_path / "dispatch_readiness_validation_report.json").read_text(encoding="utf-8"))
    
    assert packet["supervised_dispatch_readiness_status"] == "BLOCKED"
    assert packet["dispatch_allowed_now"] is False
    assert packet["approval_valid_for_dispatch"] is False
    assert packet["kill_switch_active"] is True
    assert packet["public_postable"] is False
    assert packet["next_recommended_task"] == "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_CAPTURE_LOCAL_RUN_STEP"
    
    # Confirm all required blockers exist in default blocked state
    blocker_ids = [b["blocker_id"] for b in blockers]
    assert "operator_signature_missing" in blocker_ids
    assert "destination_binding_incomplete" in blocker_ids
    assert "outbox_creation_blocked" in blocker_ids
    assert "live_write_authorization_missing" in blocker_ids
    assert "safety_review_incomplete" in blocker_ids
    assert "kill_switch_active" in blocker_ids
    assert "public_postable_false" in blocker_ids
    
    # Confirm blocker fields match requirement contract
    for b in blockers:
        assert "severity" in b
        assert "source_ref" in b
        assert "required_next_action" in b
        assert b["dispatch_blocking"] is True


def test_unsafe_material_scanning_detects_webhook_and_token(tmp_path):
    paths = write_test_inputs(tmp_path)
    # Inject webhook and token into one of the files
    paths["capture_packet"].write_text(json.dumps({
        "webhook_url": "https://discord.com/api/webhooks/12345",
        "bot_token": "xoxb-some-token-value"
    }), encoding="utf-8")
    
    packet, blockers, report = reval_lane.run_revalidation(
        paths["capture_packet"], paths["capture_report"],
        paths["sign_packet"], paths["sign_report"],
        paths["dest_packet"], paths["dest_matrix"],
        paths["outbox_preview"], paths["outbox_report"],
        paths["payload_hash"], paths["payload_record"],
        paths["upload_bundle"]
    )
    
    assert report["unsafe_material_detected"] is True
    assert "webhook_url_present" in report["unsafe_material_findings"]
    assert "slack_token_present" in report["unsafe_material_findings"]
    
    blocker_ids = [b["blocker_id"] for b in blockers]
    assert "unsafe_artifact_material" in blocker_ids


def test_unsafe_material_scanning_detects_fake_metrics_and_financial_signals(tmp_path):
    paths = write_test_inputs(tmp_path)
    paths["capture_packet"].write_text(json.dumps({
        "fake_metric": "cpc_value",
        "financial": "guaranteed_returns"
    }), encoding="utf-8")
    
    packet, blockers, report = reval_lane.run_revalidation(
        paths["capture_packet"], paths["capture_report"],
        paths["sign_packet"], paths["sign_report"],
        paths["dest_packet"], paths["dest_matrix"],
        paths["outbox_preview"], paths["outbox_report"],
        paths["payload_hash"], paths["payload_record"],
        paths["upload_bundle"]
    )
    
    assert report["unsafe_material_detected"] is True
    assert "fake_metrics_present" in report["unsafe_material_findings"]
    assert "financial_signal_present" in report["unsafe_material_findings"]


def test_unexpected_safety_claims_trigger_blocker(tmp_path):
    paths = write_test_inputs(tmp_path)
    # Inject unexpected claim
    paths["capture_packet"].write_text(json.dumps({
        "dispatch_allowed_now": True
    }), encoding="utf-8")
    
    packet, blockers, report = reval_lane.run_revalidation(
        paths["capture_packet"], paths["capture_report"],
        paths["sign_packet"], paths["sign_report"],
        paths["dest_packet"], paths["dest_matrix"],
        paths["outbox_preview"], paths["outbox_report"],
        paths["payload_hash"], paths["payload_record"],
        paths["upload_bundle"]
    )
    
    assert report["unexpected_dispatch_claims_detected"] is True
    assert "capture_packet:dispatch_allowed_now" in report["unexpected_dispatch_claims_findings"]
    
    blocker_ids = [b["blocker_id"] for b in blockers]
    assert "unexpected_dispatch_readiness_claim" in blocker_ids


def test_synthetic_valid_signature_remains_blocked(tmp_path):
    paths = write_test_inputs(
        tmp_path,
        operator_signature_valid=True,
        destination_binding_complete=True,
        outbox_draft_created=True
    )
    
    packet, blockers, report = reval_lane.run_revalidation(
        paths["capture_packet"], paths["capture_report"],
        paths["sign_packet"], paths["sign_report"],
        paths["dest_packet"], paths["dest_matrix"],
        paths["outbox_preview"], paths["outbox_report"],
        paths["payload_hash"], paths["payload_record"],
        paths["upload_bundle"]
    )
    
    # Must still remain blocked since kill-switch and live writes are disabled
    assert packet["supervised_dispatch_readiness_status"] == "BLOCKED"
    assert packet["dispatch_allowed_now"] is False
    assert "kill_switch_active" in packet["blockers"]
    
    # Routes to ledger recording when signature is valid
    assert packet["next_recommended_task"] == "TASK_CONTENTOPS_V6_APPROVAL_LEDGER_AND_OUTBOX_RECORDING_LANE_HEAVY_BATCH_V0"


def test_zero_network_or_env_dependencies():
    attrs = dir(reval_lane)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs
