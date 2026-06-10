import os
import json
from live_contentops.platform_official_docs_verification import validate_platform_official_docs_verification_packet

FIX_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures", "platform_official_docs")

def _load(name):
    with open(os.path.join(FIX_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)

def test_valid_operator_supplied_official_docs_packet():
    res = validate_platform_official_docs_verification_packet(_load("valid_operator_supplied_official_docs_packet.json"))
    assert res["valid"] is True

def test_valid_unknowns_marked_packet():
    res = validate_platform_official_docs_verification_packet(_load("valid_unknowns_marked_packet.json"))
    assert res["valid"] is True

def test_invalid_unofficial_source_marked_verified():
    res = validate_platform_official_docs_verification_packet(_load("invalid_unofficial_source_marked_verified.json"))
    assert res["valid"] is False
    assert any("verified_with_unofficial_source" in e for e in res["errors"])

def test_invalid_missing_accessed_date():
    res = validate_platform_official_docs_verification_packet(_load("invalid_missing_accessed_date.json"))
    assert res["valid"] is False
    assert any("source_missing_accessed_date" in e for e in res["errors"])

def test_invalid_live_api_enabled_from_docs():
    res = validate_platform_official_docs_verification_packet(_load("invalid_live_api_enabled_from_docs.json"))
    assert res["valid"] is False
    assert "live_api_status_must_be_disabled" in res["errors"]

def test_invalid_credentials_required_but_unredacted():
    res = validate_platform_official_docs_verification_packet(_load("invalid_credentials_required_but_unredacted.json"))
    assert res["valid"] is False
    assert any("unsafe_secret_detected" in e for e in res["errors"])

def test_invalid_official_docs_verified_without_source():
    res = validate_platform_official_docs_verification_packet(_load("invalid_official_docs_verified_without_source.json"))
    assert res["valid"] is False
    assert any("verified_without_source" in e for e in res["errors"])

def test_packet_status_pass_but_errors_exist():
    p = _load("valid_operator_supplied_official_docs_packet.json")
    p["platform_records"][0]["runtime_authority"] = True
    res = validate_platform_official_docs_verification_packet(p)
    assert res["valid"] is False
    assert "packet_status_pass_but_errors_exist" in res["errors"]
    assert "runtime_authority_must_be_false" in res["errors"]
