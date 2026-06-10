import os
import json
from live_contentops.mock_publish_flow import validate_mock_publish_result, validate_manual_metrics_readiness

FIX_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures", "mock_publish_flow")

def _load(name):
    with open(os.path.join(FIX_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)

def test_valid_mock_publish_ready():
    rec = _load("valid_mock_publish_ready.json")
    appr = {"approval_state": "operator_approved_for_mock_publish"}
    ks = {"mock_publish_allowed_when_enabled": True}
    res = validate_mock_publish_result(rec, approval_rec=appr, ks=ks)
    assert res["valid"] is True

def test_valid_manual_metrics_readiness():
    rec = _load("valid_manual_metrics_readiness.json")
    res = validate_manual_metrics_readiness(rec)
    assert res["valid"] is True

def test_invalid_missing_mock_approval():
    rec = _load("valid_mock_publish_ready.json")
    rec["packet_status"] = "blocked"
    appr = {"approval_state": "operator_review_required"}
    ks = {"mock_publish_allowed_when_enabled": True}
    res = validate_mock_publish_result(rec, approval_rec=appr, ks=ks)
    assert res["valid"] is False
    assert any("invalid_approval_state" in e for e in res["errors"])

def test_invalid_kill_switch_blocks_mock_publish():
    rec = _load("valid_mock_publish_ready.json")
    rec["packet_status"] = "blocked"
    appr = {"approval_state": "operator_approved_for_mock_publish"}
    ks = _load("invalid_kill_switch_blocks_mock_publish.json")
    res = validate_mock_publish_result(rec, approval_rec=appr, ks=ks)
    assert res["valid"] is False
    assert "kill_switch_blocks_mock_publish" in res["errors"]

def test_invalid_live_execution_true():
    rec = _load("invalid_live_execution_true.json")
    res = validate_mock_publish_result(rec)
    assert res["valid"] is False
    assert "live_execution_must_be_false" in res["errors"]

def test_invalid_network_accessed_true():
    rec = _load("invalid_network_accessed_true.json")
    res = validate_mock_publish_result(rec)
    assert res["valid"] is False
    assert "network_accessed_must_be_false" in res["errors"]

def test_invalid_credential_accessed_true():
    rec = _load("invalid_credential_accessed_true.json")
    res = validate_mock_publish_result(rec)
    assert res["valid"] is False
    assert "credential_accessed_must_be_false" in res["errors"]

def test_invalid_scheduler_accessed_true():
    rec = _load("invalid_scheduler_accessed_true.json")
    res = validate_mock_publish_result(rec)
    assert res["valid"] is False
    assert "scheduler_accessed_must_be_false" in res["errors"]

def test_invalid_platform_api_payload_generated_true():
    rec = _load("invalid_platform_api_payload_generated_true.json")
    res = validate_mock_publish_result(rec)
    assert res["valid"] is False
    assert "platform_api_payload_generated_must_be_false" in res["errors"]

def test_invalid_automatic_metrics_ingestion_true():
    rec = _load("invalid_automatic_metrics_ingestion_true.json")
    res = validate_manual_metrics_readiness(rec)
    assert res["valid"] is False
    assert "automatic_metrics_ingestion_must_be_false" in res["errors"]

def test_missing_metrics_policy():
    rec = _load("valid_manual_metrics_readiness.json")
    rec["metric_null_policy"] = "coerce_to_zero"
    res = validate_manual_metrics_readiness(rec)
    assert res["valid"] is False
    assert "metric_null_policy_coerces_to_zero" in res["errors"]
