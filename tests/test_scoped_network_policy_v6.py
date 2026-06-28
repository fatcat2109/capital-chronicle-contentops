import json
from pathlib import Path
from live_contentops import scoped_network_policy_v6 as policy


def test_scoped_network_policy_action_classes():
    out_dir = Path("docs/automation/V6_NETWORK_SCOPE_POLICY")
    policy.main(["--output-dir", str(out_dir)])
    
    packet_file = out_dir / "network_scope_policy_packet.json"
    assert packet_file.exists()
    
    data = json.loads(packet_file.read_text(encoding="utf-8"))
    assert set(data["action_classes"]) == set(policy.ACTION_CLASSES)
    assert data["dispatch_allowed_now"] is False
    assert data["live_write_allowed_now"] is False
    assert data["kill_switch_active"] is True
    assert data["policy_compliance_status"] == "POLICY_COMPLIANCE_SUCCESS"


def test_allowlist_structure():
    assert len(policy.ALLOWLIST) == 1
    fonts = policy.ALLOWLIST[0]
    assert fonts["resource_family"] == "google_fonts"
    assert "fonts.googleapis.com" in fonts["domains"]
    assert "fonts.gstatic.com" in fonts["domains"]
    assert fonts["action_class"] == "passive_static_resource"
    assert fonts["cookies_or_storage_access"] is False
    assert fonts["credentials_required"] is False


def test_scan_ui_files_detects_violations(tmp_path):
    # Create a synthetic violation in temp UI dir
    bad_ui_dir = tmp_path / "ui_test"
    bad_ui_dir.mkdir()
    
    # 1. Good file with allowed domains
    good_file = bad_ui_dir / "index.html"
    good_file.write_text('<link href="https://fonts.googleapis.com/css">', encoding="utf-8")
    
    # 2. Bad file with unauthorized domain
    bad_file = bad_ui_dir / "app.js"
    bad_file.write_text('fetch("https://unauthorized-api.com/v1/data")', encoding="utf-8")
    
    violations = policy.scan_ui_files(bad_ui_dir)
    assert len(violations) == 1
    assert "unauthorized-api.com" in violations[0]


def test_no_sensitive_values_in_governance_docs():
    out_dir = Path("docs/automation/V6_NETWORK_SCOPE_POLICY")
    policy.main(["--output-dir", str(out_dir)])
    
    md_file = out_dir / "scoped_network_policy_v6.md"
    assert md_file.exists()
    content = md_file.read_text(encoding="utf-8")
    assert "discord.com/api/webhooks" not in content
    assert "ghp_" not in content
    assert "token_value" not in content.lower()


def test_module_contains_no_forbidden_behavior():
    attrs = dir(policy)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs
