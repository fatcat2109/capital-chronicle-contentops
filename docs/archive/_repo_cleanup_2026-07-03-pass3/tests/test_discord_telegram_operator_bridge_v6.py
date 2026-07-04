from live_contentops import discord_telegram_operator_bridge_v6 as bridge

import json
from pathlib import Path
from live_contentops import discord_telegram_operator_bridge_v6 as bridge

def test_bridge_status_and_defaults(tmp_path):
    # Setup inputs
    contract = {
        "variant_pack": {
            "substack_canonical": {},
            "discord_drop": {}
        },
        "draft_inspector": {
            "draft_inspector_status": "BLOCKED_REVIEW_ONLY_ISSUES_FOUND",
            "blockers": ["source_verification_required"]
        }
    }
    hash_data = {
        "unified_payload_bundle_hash": "a" * 64
    }
    
    contract_file = tmp_path / "contract.json"
    hash_file = tmp_path / "hash.json"
    contract_file.write_text(json.dumps(contract), encoding="utf-8")
    hash_file.write_text(json.dumps(hash_data), encoding="utf-8")
    
    # Run main orchestration
    out_dir = tmp_path / "out"
    bridge.main([
        "--output-dir", str(out_dir),
        "--contract-packet", str(contract_file),
        "--hash-manifest", str(hash_file)
    ])
    
    # Read generated packets
    bp = json.loads((out_dir / "operator_bridge_packet.json").read_text(encoding="utf-8"))
    assert bp["operator_bridge_status"] == "READY_FOR_REVIEW_ONLY_REDACTED_STATUS"
    assert bp["live_discord_webhook_call_performed"] is False
    assert bp["live_telegram_api_call_performed"] is False
    assert bp["dispatch_allowed_now"] is False
    assert bp["kill_switch_active"] is True
    
    # Check blockers are preserved
    preserved = bp["blockers"]
    assert "source_verification_required" in preserved
    assert "operator_signature_missing" in preserved
    assert "destination_binding_incomplete" in preserved
    assert "outbox_creation_blocked" in preserved
    assert "live_write_authorization_missing" in preserved
    assert "kill_switch_active" in preserved

def test_no_forbidden_network_or_env_access():
    # Verify that the new bridge/status modules do not import or call any of the forbidden packages/functions.
    forbidden_imports = [
        "import requests", "from requests",
        "import httpx", "from httpx",
        "import urllib.request",
        "import openai", "from openai",
        "import anthropic", "from anthropic",
        "import discord", "from discord",
        "import telegram", "from telegram",
        "import tweepy", "from tweepy",
        "import selenium", "from selenium",
        "import playwright", "from playwright",
        "getenv", "environ["
    ]
    bridge_files = [
        "live_contentops/discord_telegram_operator_bridge_v6.py",
        "live_contentops/redacted_operator_status_v6.py",
        "live_contentops/operator_bridge_message_preview_v6.py",
        "live_contentops/operator_bridge_capability_matrix_v6.py"
    ]
    for path_str in bridge_files:
        path = Path(path_str)
        content = path.read_text(encoding="utf-8")
        for fw in forbidden_imports:
            assert fw not in content, f"Forbidden import/call pattern '{fw}' found in {path}"

