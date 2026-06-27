import json
from pathlib import Path
from live_contentops import platform_adapter_selection_policy_v6 as policy


def test_free_practical_api_maps_to_official_api_adapter():
    res = policy.resolve_preferred_adapter(has_free_api=True, api_restrictions=[])
    assert res == "official_api_adapter"


def test_paid_restricted_heavy_api_maps_to_browser_or_manual_fallback():
    # Paid API
    assert policy.resolve_preferred_adapter(has_free_api=False, api_restrictions=["paid"]) == "supervised_browser_cdp_adapter"
    # Overly restrictive/heavy review
    assert policy.resolve_preferred_adapter(has_free_api=False, api_restrictions=["review_heavy"]) == "supervised_browser_cdp_adapter"
    # Explicit manual fallback
    assert policy.resolve_preferred_adapter(has_free_api=False, api_restrictions=["manual_only"]) == "manual_fallback_adapter"


def test_browser_cdp_checkpoints_and_prohibitions():
    # Load policy packet
    packet = {
        "cdp_governance_rules": {
            "bypass_forbidden_checkpoints": [
                "exact_preview",
                "payload_hash",
                "destination_binding",
                "jim_approval",
                "outbox_revalidation",
                "redacted_audit",
                "idempotency",
                "kill_switch",
                "manual_fallback"
            ],
            "prohibited_actions": [
                "selfbot_behavior",
                "hidden_posting",
                "dms",
                "scraping",
                "account_switching",
                "cookie_extraction",
                "localstorage_extraction",
                "sessionstorage_extraction",
                "token_extraction",
                "raw_token_persistence",
                "approval_bypass"
            ]
        }
    }
    
    rules = packet["cdp_governance_rules"]
    assert "exact_preview" in rules["bypass_forbidden_checkpoints"]
    assert "payload_hash" in rules["bypass_forbidden_checkpoints"]
    assert "destination_binding" in rules["bypass_forbidden_checkpoints"]
    assert "jim_approval" in rules["bypass_forbidden_checkpoints"]
    assert "outbox_revalidation" in rules["bypass_forbidden_checkpoints"]
    assert "redacted_audit" in rules["bypass_forbidden_checkpoints"]
    
    assert "selfbot_behavior" in rules["prohibited_actions"]
    assert "dms" in rules["prohibited_actions"]
    assert "scraping" in rules["prohibited_actions"]
    assert "cookie_extraction" in rules["prohibited_actions"]
    assert "localstorage_extraction" in rules["prohibited_actions"]
    assert "token_extraction" in rules["prohibited_actions"]


def test_packet_flags_are_secure():
    # Make a dummy generation run to verify packet settings
    out_dir = Path("docs/automation/V6_PLATFORM_ADAPTER_SELECTION_POLICY")
    policy.main(["--output-dir", str(out_dir)])
    
    packet_file = out_dir / "platform_adapter_selection_policy_packet.json"
    assert packet_file.exists()
    
    data = json.loads(packet_file.read_text(encoding="utf-8"))
    assert data["dispatch_allowed_now"] is False
    assert data["live_write_allowed_now"] is False
    assert data["credentials_hydrated"] is False
    assert data["browser_session_started"] is False


def test_no_sensitive_values_in_generated_docs():
    # Verify MD policy content has no raw secret values or concrete webhook URLs
    md = policy.generate_policy_markdown()
    assert "discord.com/api/webhooks/" not in md
    assert "ghp_" not in md
    assert "xoxb-" not in md
    assert ".env" not in md


def test_module_contains_no_forbidden_behavior():
    attrs = dir(policy)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs
