import json
from pathlib import Path
from live_contentops import platform_adapter_policy_matrix_reconciliation_v6 as recon


def test_telegram_prefers_official_api_adapter():
    row = {"platform": "Telegram channel", "platform_family": "remote_operator", "adapter_class": "official_api_adapter"}
    res = recon.reconcile_platform_row(row)
    assert res["preferred_adapter"] == "official_api_adapter"
    assert res["free_practical_api_available"] is True
    assert res["official_api_practical_for_required_actions"] is True
    assert res["cdp_allowed_supervised_only"] is False


def test_substack_prefers_supervised_browser_cdp_adapter():
    row = {"platform": "Substack publication", "platform_family": "owned_long_form", "adapter_class": "browser_cdp_adapter"}
    res = recon.reconcile_platform_row(row)
    assert res["preferred_adapter"] == "supervised_browser_cdp_adapter"
    assert res["free_practical_api_available"] is False
    assert res["official_api_practical_for_required_actions"] is False
    assert res["cdp_allowed_supervised_only"] is True
    assert "cdp_governance_rules" in res


def test_twitter_prefers_manual_fallback_adapter():
    row = {"platform": "X manual", "platform_family": "social_distribution", "adapter_class": "manual_fallback_adapter"}
    res = recon.reconcile_platform_row(row)
    assert res["preferred_adapter"] == "manual_fallback_adapter"
    assert res["free_practical_api_available"] is False
    assert res["official_api_practical_for_required_actions"] is False
    assert res["cdp_allowed_supervised_only"] is True


def test_meta_prefers_supervised_browser_cdp_adapter():
    row = {"platform": "Facebook Page", "platform_family": "social_distribution", "adapter_class": "official_api_adapter"}
    res = recon.reconcile_platform_row(row)
    assert res["preferred_adapter"] == "supervised_browser_cdp_adapter"
    assert res["free_practical_api_available"] is False
    assert res["official_api_practical_for_required_actions"] is False
    assert res["cdp_allowed_supervised_only"] is True


def test_reconciled_packet_contains_no_sensitive_values():
    out_dir = Path("docs/automation/V6_PLATFORM_ADAPTER_POLICY_MATRIX_RECONCILIATION")
    recon.main(["--output-dir", str(out_dir)])
    
    packet_file = out_dir / "adapter_policy_matrix_reconciliation_packet.json"
    assert packet_file.exists()
    
    data = json.loads(packet_file.read_text(encoding="utf-8"))
    assert data["dispatch_allowed_now"] is False
    assert data["live_write_allowed_now"] is False
    assert data["credentials_hydrated"] is False
    assert data["browser_session_started"] is False
    
    # check that we do not write webhook templates or token lengths
    assert data.get("raw_secret_output", False) is False
    assert data.get("webhook_url_printed", False) is False


def test_module_contains_no_forbidden_behavior():
    attrs = dir(recon)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs
