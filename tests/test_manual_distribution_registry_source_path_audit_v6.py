from pathlib import Path

from live_contentops.manual_distribution_evidence_registry_v6 import build_manual_distribution_evidence_registry
from live_contentops.manual_distribution_evidence_registry_source_path_audit_v6 import (
    PACKET_ROLES,
    build_manual_distribution_registry_source_path_audit,
)

ROOT = Path(__file__).resolve().parents[1]


def test_source_path_audit_covers_expected_platforms_and_roles():
    audit = build_manual_distribution_registry_source_path_audit(build_manual_distribution_evidence_registry())
    assert {platform["platform"] for platform in audit["platforms"]} == {"substack", "linkedin", "x"}
    for platform in audit["platforms"]:
        assert set(platform["roles"]) == set(PACKET_ROLES)


def test_source_paths_are_local_existing_docs_automation_paths():
    audit = build_manual_distribution_registry_source_path_audit()
    assert audit["all_paths_exist"] is True
    assert audit["all_paths_within_docs_automation"] is True
    assert audit["no_url_like_source_paths"] is True
    for platform in audit["platforms"]:
        for check in platform["roles"].values():
            source_path = check["source_path"]
            assert source_path.startswith("docs/automation/")
            assert "://" not in source_path.lower()
            assert not source_path.lower().startswith(("http:", "https:", "www."))
            assert (ROOT / source_path).is_file()
            assert check["path_exists"] is True
            assert check["path_within_docs_automation"] is True
            assert check["path_url_like"] is False


def test_packet_ids_and_hashes_match_source_packet_fields():
    audit = build_manual_distribution_registry_source_path_audit()
    assert audit["all_packet_ids_match"] is True
    assert audit["all_hashes_match"] is True
    for platform in audit["platforms"]:
        for check in platform["roles"].values():
            assert check["packet_id_field"]
            assert check["hash_field"]
            assert check["registry_packet_id"] == check["observed_packet_id"]
            assert check["registry_hash"] == check["observed_hash"]
            assert check["packet_id_matches"] is True
            assert check["hash_matches"] is True


def test_source_path_audit_safety_flags_and_deterministic_hash():
    audit = build_manual_distribution_registry_source_path_audit()
    assert audit["source_path_audit_status"] == "passed"
    assert audit["audit_packet_id"].endswith(audit["exact_payload_hash"][:16])
    assert audit["exact_payload_hash"] == build_manual_distribution_registry_source_path_audit()["exact_payload_hash"]
    for flag in [
        "network_call_made",
        "provider_call_made",
        "env_value_read_made",
        "credential_read_made",
        "browser_session_used",
        "public_url_fetch_made",
        "live_publish_performed_by_contentops",
    ]:
        assert audit[flag] is False


def test_source_path_audit_contains_no_forbidden_claim_language():
    text = str(build_manual_distribution_registry_source_path_audit()).lower()
    for phrase in [
        "financial advice",
        "signal service",
        "trade execution",
        "network_call_made': true",
        "provider_call_made': true",
        "public_url_fetch_made': true",
    ]:
        assert phrase not in text
