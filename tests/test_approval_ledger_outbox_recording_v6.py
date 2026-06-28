import json
from pathlib import Path
from live_contentops import approval_ledger_outbox_recording_v6 as recording_lane


def write_test_inputs(tmp_path: Path, **kwargs) -> dict[str, Path]:
    paths = {}
    
    # 1. Sign packet
    sign_data = {
        "operator_signature_valid": kwargs.get("operator_signature_valid", False)
    }
    sign_path = tmp_path / "operator_signature_binding_packet.json"
    sign_path.write_text(json.dumps(sign_data, indent=2), encoding="utf-8")
    paths["sign_packet"] = sign_path
    
    # 2. Readiness packet
    readiness_data = {
        "supervised_dispatch_readiness_status": kwargs.get("supervised_dispatch_readiness_status", "BLOCKED"),
        "blockers": kwargs.get("readiness_blockers", ["operator_signature_missing"])
    }
    readiness_path = tmp_path / "supervised_dispatch_readiness_packet.json"
    readiness_path.write_text(json.dumps(readiness_data, indent=2), encoding="utf-8")
    paths["readiness_packet"] = readiness_path
    
    # 3. Hash record
    hash_data = {
        "payload_hash": "a" * 64
    }
    hash_path = tmp_path / "payload_hash_record.json"
    hash_path.write_text(json.dumps(hash_data, indent=2), encoding="utf-8")
    paths["hash_record"] = hash_path
    
    # 4. Preview exact
    preview_data = {
        "body": "mock_preview"
    }
    preview_path = tmp_path / "payload_preview_exact_review.json"
    preview_path.write_text(json.dumps(preview_data, indent=2), encoding="utf-8")
    paths["preview_exact"] = preview_path
    
    return paths


def test_default_committed_state_is_blocked(tmp_path):
    paths = write_test_inputs(tmp_path)
    
    rc = recording_lane.main([
        "--sign-packet", str(paths["sign_packet"]),
        "--readiness-packet", str(paths["readiness_packet"]),
        "--hash-record", str(paths["hash_record"]),
        "--preview-exact", str(paths["preview_exact"]),
        "--output-dir", str(tmp_path)
    ])
    
    assert rc == 0
    
    packet = json.loads((tmp_path / "approval_ledger_outbox_packet.json").read_text(encoding="utf-8"))
    ledger_preview = json.loads((tmp_path / "approval_ledger_entry_preview.json").read_text(encoding="utf-8"))
    outbox_preview = json.loads((tmp_path / "outbox_record_preview.json").read_text(encoding="utf-8"))
    
    assert packet["approval_ledger_outbox_status"] == "BLOCKED_AWAITING_OPERATOR_SIGNATURE"
    assert packet["approval_ledger_entry_created"] is False
    assert packet["outbox_record_created"] is False
    assert packet["outbox_entry_created"] is False
    assert packet["outbox_dispatchable"] is False
    assert packet["operator_signature_valid"] is False
    assert packet["supervised_dispatch_readiness_status"] == "BLOCKED"
    assert packet["approval_valid_for_dispatch"] is False
    assert packet["dispatch_allowed_now"] is False
    assert packet["live_write_allowed_now"] is False
    assert packet["live_write_authorization_present"] is False
    assert packet["credentials_hydrated"] is False
    assert packet["browser_session_started"] is False
    assert packet["public_postable"] is False
    assert packet["kill_switch_active"] is True
    
    # Previews must exist but not be committed/dispatchable
    assert ledger_preview["ledger_entry_preview_created"] is True
    assert ledger_preview["ledger_entry_committed"] is False
    assert ledger_preview["operator_signature_required"] is True
    assert ledger_preview["operator_signature_valid"] is False
    assert ledger_preview["valid_for_dispatch"] is False
    assert ledger_preview["ledger_mutation_allowed"] is False
    
    assert outbox_preview["outbox_record_preview_created"] is True
    assert outbox_preview["outbox_record_created"] is False
    assert outbox_preview["dispatchable"] is False
    assert outbox_preview["platform_family"] == "telegram"
    assert outbox_preview["destination_class"] == "operator_review_only"
    assert outbox_preview["live_destination_bound"] is False
    assert outbox_preview["destination_identifier_redacted_or_absent"] is True
    assert outbox_preview["credential_hydrated"] is False
    assert outbox_preview["dispatch_adapter_enabled"] is False


def test_unsafe_material_scanning_detects_webhook_and_token(tmp_path):
    paths = write_test_inputs(tmp_path)
    # Inject webhook and token into hash record
    paths["hash_record"].write_text(json.dumps({
        "webhook_url": "https://discord.com/api/webhooks/12345",
        "bot_token": "xoxb-some-token-value"
    }), encoding="utf-8")
    
    packet, ledger_p, outbox_p, ledger_r, outbox_r, blockers = recording_lane.run_recording(
        paths["sign_packet"], paths["readiness_packet"],
        paths["hash_record"], paths["preview_exact"]
    )
    
    assert ledger_r["unsafe_material_detected"] is True
    assert "webhook_url_present" in ledger_r["unsafe_material_findings"]
    assert "slack_token_present" in ledger_r["unsafe_material_findings"]
    assert "unsafe_artifact_material" in blockers


def test_unexpected_safety_claims_trigger_blocker(tmp_path):
    paths = write_test_inputs(tmp_path)
    # Inject unexpected claim into readiness packet
    paths["readiness_packet"].write_text(json.dumps({
        "supervised_dispatch_readiness_status": "BLOCKED",
        "dispatch_allowed_now": True
    }), encoding="utf-8")
    
    packet, ledger_p, outbox_p, ledger_r, outbox_r, blockers = recording_lane.run_recording(
        paths["sign_packet"], paths["readiness_packet"],
        paths["hash_record"], paths["preview_exact"]
    )
    
    assert ledger_r["unexpected_claims_detected"] is True
    assert "readiness_packet:dispatch_allowed_now" in ledger_r["unexpected_claims_findings"]
    assert "unexpected_dispatch_readiness_claim" in blockers


def test_synthetic_valid_signature_creates_review_only_previews(tmp_path):
    paths = write_test_inputs(
        tmp_path,
        operator_signature_valid=True,
        supervised_dispatch_readiness_status="READY",
        readiness_blockers=[]
    )
    
    packet, ledger_p, outbox_p, ledger_r, outbox_r, blockers = recording_lane.run_recording(
        paths["sign_packet"], paths["readiness_packet"],
        paths["hash_record"], paths["preview_exact"]
    )
    
    # Must still remain blocked since live writes/dispatch are globally disabled
    assert packet["approval_ledger_outbox_status"] == "DRAFT_READY_FOR_REVIEW"
    assert packet["approval_ledger_entry_created"] is False
    assert packet["outbox_record_created"] is False
    assert packet["outbox_dispatchable"] is False
    assert packet["dispatch_allowed_now"] is False
    assert packet["live_write_allowed_now"] is False
    
    assert ledger_p["operator_signature_valid"] is True
    assert ledger_p["ledger_entry_committed"] is False
    
    assert outbox_p["outbox_record_created"] is False
    assert outbox_p["dispatchable"] is False


def test_zero_network_or_env_dependencies():
    attrs = dir(recording_lane)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs
