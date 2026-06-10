import json
from pathlib import Path
from live_contentops.pre_alpha_content_lane_policy import validate_policy_packet

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "pre_alpha_content_lane_policy"

def load_fixture(filename):
    with open(FIXTURES_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)

def test_valid_pre_alpha_general_process_policy():
    payload = load_fixture("valid_pre_alpha_general_process_policy.json")
    result = validate_policy_packet(payload)
    assert result["packet_status"] == "pass"

def test_invalid_artifact_backed_without_artifacts():
    payload = load_fixture("invalid_artifact_backed_without_artifacts.json")
    result = validate_policy_packet(payload)
    assert result["packet_status"] == "blocked"
    assert any("Cannot claim artifact-backed status without explicit real artifact references" in r for r in result["reasons"])

def test_invalid_grounded_news_signal_language():
    payload = load_fixture("invalid_grounded_news_signal_language.json")
    result = validate_policy_packet(payload)
    assert result["packet_status"] == "blocked"
    assert any("Forbidden financial/signal language detected" in r for r in result["reasons"])

def test_invalid_public_postable_true():
    payload = load_fixture("invalid_public_postable_true.json")
    result = validate_policy_packet(payload)
    assert result["packet_status"] == "blocked"
    assert any("public_postable must be false" in r for r in result["reasons"])

def test_forbidden_pre_alpha_claims():
    payload = load_fixture("valid_pre_alpha_general_process_policy.json")
    payload["text_content"] = "Our DQR is high and forecast readiness is complete."
    result = validate_policy_packet(payload)
    assert result["packet_status"] == "blocked"
    assert any("Forbidden DQR/forecast readiness/lineage claim in pre-alpha lane" in r for r in result["reasons"])

def test_invented_source_artifact_ids():
    payload = load_fixture("valid_pre_alpha_general_process_policy.json")
    payload["lane"] = "future_artifact_backed_cc"
    payload["claims_artifact_backed"] = True
    payload["source_artifact_ids"] = ["fake_id_123"]
    result = validate_policy_packet(payload)
    assert result["packet_status"] == "blocked"
    assert any("Invented source artifact ID detected: fake_id_123" in r for r in result["reasons"])
