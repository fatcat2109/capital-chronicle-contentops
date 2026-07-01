from live_contentops.manual_distribution_evidence_registry_v6 import build_manual_distribution_evidence_registry


def test_registry_contains_current_manual_platforms_and_hashes():
    registry = build_manual_distribution_evidence_registry()
    assert {p["platform"] for p in registry["platforms"]} == {"substack", "linkedin", "x"}
    assert registry["registry_hash"] == build_manual_distribution_evidence_registry()["registry_hash"]
    assert registry["registry_packet_id"].endswith(registry["registry_hash"][:16])
    for platform in registry["platforms"]:
        assert platform["lane_status"] == "fixture_manual_operator_supplied"
        assert platform["manual_operator_supplied"] is True
        for role in ("export", "approval", "handoff", "url", "metrics"):
            assert platform["source_packets"][role]["packet_id"]
            assert platform["source_packets"][role]["hash"]


def test_registry_safety_flags_and_controls_are_blocked():
    registry = build_manual_distribution_evidence_registry()
    required_controls = {"approve", "send", "publish", "dispatch", "schedule"}
    for platform in registry["platforms"]:
        flags = platform["safety_flags"]
        assert flags == {
            "api_used": False,
            "network_call_made": False,
            "url_network_verified": False,
            "metrics_network_verified": False,
            "env_value_read_made": False,
            "credential_read_made": False,
            "browser_session_used": False,
            "live_publish_performed_by_contentops": False,
            "enabled_publish_send_dispatch_approve_controls": False,
        }
        assert required_controls.issubset(set(platform["blocked_controls"]))
        assert "not_network_verified" in platform["metric_provenance"]
        assert "not_network_verified" in platform["url_provenance"]


def test_registry_contains_no_forbidden_claim_language():
    registry_text = str(build_manual_distribution_evidence_registry()).lower()
    forbidden = [
        "financial advice",
        "signal service",
        "trade execution",
        "url_network_verified': true",
        "metrics_network_verified': true",
        "api_used': true",
    ]
    for phrase in forbidden:
        assert phrase not in registry_text
