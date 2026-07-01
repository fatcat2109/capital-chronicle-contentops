import json
import re

from live_contentops.manual_distribution_registry_v5_adapter_codegen_v6 import (
    build_manual_distribution_registry_v5_adapter_text,
    check_manual_distribution_registry_v5_adapter_in_sync,
)


def _extract_const_json(adapter_text: str, export_name: str) -> dict:
    match = re.search(rf"export const {export_name} = (.*?) as const;", adapter_text, re.S)
    assert match, export_name
    return json.loads(match.group(1))


def test_generated_adapter_matches_committed_adapter():
    status = check_manual_distribution_registry_v5_adapter_in_sync()
    assert status["adapter_in_sync"] is True


def test_generated_adapter_hashes_match_committed_packets():
    text = build_manual_distribution_registry_v5_adapter_text()
    registry = _extract_const_json(text, "manualDistributionEvidenceRegistry")
    audit_index = _extract_const_json(text, "manualDistributionRegistryAuditIndex")
    assert registry["registry_hash"] == "7f75feba8ed20f2d98b4ee15aff0f41a4271a76e3634fbec2563d17bc8f66fac"
    assert audit_index["registry_hash"] == registry["registry_hash"]
    assert audit_index["exact_payload_hash"] == "b968984b920bbf93edef7941ab3c93f229db393f6be7bcf0025a713b82cc5477"
    assert audit_index["audit_index_packet_id"] == "manual_distribution_registry_audit_index_b968984b920bbf93"


def test_generated_adapter_readiness_is_review_only_and_non_readiness_false():
    text = build_manual_distribution_registry_v5_adapter_text()
    audit_index = _extract_const_json(text, "manualDistributionRegistryAuditIndex")
    assert audit_index["registry_readiness_status"] == "ready_for_manual_operator_review_only"
    assert all(value is False for value in audit_index["non_readiness_claims"].values())
    lowered = text.lower()
    for phrase in ["ready for live", "api ready", "dispatch ready", "public url verified", "platform auth ready"]:
        assert phrase not in lowered


def test_generated_adapter_has_no_external_platform_urls_or_enabled_live_controls():
    text = build_manual_distribution_registry_v5_adapter_text().lower()
    for phrase in ["https://substack", "https://www.linkedin", "https://x.com", "twitter.com"]:
        assert phrase not in text
    assert '"enabled_publish_send_dispatch_approve_controls": true' not in text
    assert '"network_call_made": true' not in text
    assert '"provider_call_made": true' not in text
    assert '"env_value_read_made": true' not in text
    assert '"credential_read_made": true' not in text
    assert '"browser_session_used": true' not in text
    assert '"public_url_fetch_made": true' not in text
    assert '"live_publish_performed_by_contentops": true' not in text


def test_generated_adapter_output_is_deterministic():
    assert build_manual_distribution_registry_v5_adapter_text() == build_manual_distribution_registry_v5_adapter_text()
    assert check_manual_distribution_registry_v5_adapter_in_sync() == check_manual_distribution_registry_v5_adapter_in_sync()
