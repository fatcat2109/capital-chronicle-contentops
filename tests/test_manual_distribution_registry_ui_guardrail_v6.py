from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "ui/contentops_v5/src/views/ManualDistributionRegistryPanel.tsx"
VIEWS = [
    ROOT / "ui/contentops_v5/src/views/ManualExportPilotVerification.tsx",
    ROOT / "ui/contentops_v5/src/views/ApprovalQueue.tsx",
    ROOT / "ui/contentops_v5/src/views/EvidenceVault.tsx",
]


def test_reusable_registry_panel_exists_and_is_used_by_canonical_views():
    assert COMPONENT.exists()
    for view in VIEWS:
        text = view.read_text(encoding="utf-8")
        assert "ManualDistributionRegistryPanel" in text
        assert "manualDistributionRegistryPlatforms.map" not in text


def test_registry_panel_has_safety_labels_without_external_urls_or_enabled_controls():
    text = COMPONENT.read_text(encoding="utf-8")
    for label in ["api_used", "url_network_verified", "metrics_network_verified", "controls_enabled"]:
        assert label in text
    forbidden = ["https://substack", "https://www.linkedin", "https://x.com", "twitter.com"]
    for phrase in forbidden:
        assert phrase not in text.lower()
    assert "disabled={false}" not in text
    assert "enabled={true}" not in text.lower()
    assert "disabled={false}" not in text.lower()
    for control in ["approve", "send", "publish", "dispatch", "schedule"]:
        assert control in text.lower()


def test_registry_panel_packet_drilldown_roles_and_safe_hash_separator():
    text = COMPONENT.read_text(encoding="utf-8")
    assert "Packet drilldown audit" in text
    assert "?" not in text
    for role in ["export", "approval", "handoff", "url", "metrics"]:
        assert role in text
    assert "packet_id=" in text
    assert "..." in text



def test_registry_panel_audit_index_readiness_summary():
    text = COMPONENT.read_text(encoding="utf-8")
    assert "Audit Index / Operator Review Readiness" in text
    assert "ready_for_manual_operator_review_only" in text
    assert "manual operator review only" in text
    assert "not live readiness" in text
    for phrase in ["ready for live", "api ready", "dispatch ready", "public url verified", "platform auth ready"]:
        assert phrase not in text.lower()
    for field in [
        "live_readiness_claimed", "api_readiness_claimed", "public_url_verification_claimed",
        "platform_auth_readiness_claimed", "dispatch_readiness_claimed", "network_call_made",
        "provider_call_made", "env_value_read_made", "credential_read_made", "browser_session_used",
        "public_url_fetch_made", "live_publish_performed_by_contentops",
        "enabled_publish_send_dispatch_approve_controls",
    ]:
        assert field in text
    assert "manualDistributionRegistryAuditIndex.blockers" in text
    assert "manualDistributionRegistryAuditIndex.caveats" in text
