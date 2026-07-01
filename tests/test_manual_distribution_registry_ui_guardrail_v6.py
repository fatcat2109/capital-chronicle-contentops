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
