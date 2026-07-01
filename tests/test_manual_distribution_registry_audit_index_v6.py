from live_contentops.manual_distribution_registry_audit_index_v6 import build_manual_distribution_registry_audit_index


def test_audit_index_binds_registry_and_source_path_audit_packets():
    index = build_manual_distribution_registry_audit_index()
    assert index["registry_packet_id"] == "manual_distribution_evidence_registry_7f75feba8ed20f2d"
    assert index["registry_hash"] == "7f75feba8ed20f2d98b4ee15aff0f41a4271a76e3634fbec2563d17bc8f66fac"
    assert index["source_path_audit_packet_id"].startswith("manual_distribution_registry_source_path_audit_")
    assert len(index["source_path_audit_hash"]) == 64


def test_audit_index_platforms_and_readiness_are_review_only():
    index = build_manual_distribution_registry_audit_index()
    assert set(index["platforms_included"]) == {"Substack", "LinkedIn", "X"}
    assert index["source_path_audit_status"] == "passed"
    assert index["registry_readiness_status"] == "ready_for_manual_operator_review_only"
    forbidden = str(index).lower()
    for phrase in ["ready_for_live", "api_ready", "dispatch_ready", "platform_auth_ready", "public_url_verified"]:
        assert phrase not in forbidden
    assert all(value is False for value in index["non_readiness_claims"].values())


def test_audit_index_safety_flags_blockers_caveats_and_hash():
    index = build_manual_distribution_registry_audit_index()
    for flag in [
        "network_call_made", "provider_call_made", "env_value_read_made", "credential_read_made",
        "browser_session_used", "public_url_fetch_made", "live_publish_performed_by_contentops",
        "enabled_publish_send_dispatch_approve_controls",
    ]:
        assert index[flag] is False
    assert any("live/provider/platform execution disabled" in blocker for blocker in index["blockers"])
    assert any("fixture/operator-supplied/manual only" in caveat for caveat in index["caveats"])
    assert index["exact_payload_hash"] == build_manual_distribution_registry_audit_index()["exact_payload_hash"]
    assert index["audit_index_packet_id"].endswith(index["exact_payload_hash"][:16])
