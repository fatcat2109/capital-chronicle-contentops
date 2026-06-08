import json
import pytest
from pathlib import Path
from live_contentops.adapters import telegram

def load_fixture(name):
    p = Path(__file__).parent / "fixtures" / "telegram_adapter" / name
    return json.loads(p.read_text(encoding="utf-8"))

def test_dry_run_success():
    req = load_fixture("valid_telegram_dry_run_request.json")
    res = telegram.run_telegram_dry_run(req)
    assert "[SIMULATED MESSAGE PREVIEW]" in res["simulated_message_preview"]
    assert "safe_for_publish" in res and res["safe_for_publish"] is False
    assert res["telegram_api_used"] is False

def test_dry_run_blocked():
    req = load_fixture("blocked_source_required_request.json")
    res = telegram.run_telegram_dry_run(req)
    assert "[BLOCKED]" in res["simulated_message_preview"]

def test_invalid_api_used():
    req = load_fixture("invalid_telegram_api_used_true.json")
    with pytest.raises(ValueError, match="telegram_api_used cannot be true"):
        telegram.run_telegram_dry_run(req)

def test_invalid_platform_used():
    req = load_fixture("invalid_platform_api_used_true.json")
    with pytest.raises(ValueError, match="platform_api_used cannot be true"):
        telegram.run_telegram_dry_run(req)

def test_invalid_safe_for_publish():
    req = load_fixture("invalid_safe_for_publish_true.json")
    with pytest.raises(ValueError, match="safe_for_publish cannot be true"):
        telegram.run_telegram_dry_run(req)

def test_invalid_bot_token():
    req = load_fixture("invalid_bot_token_field.json")
    with pytest.raises(ValueError, match="Bot-token-like field detected"):
        telegram.run_telegram_dry_run(req)

def test_invalid_real_chat_id():
    req = load_fixture("invalid_real_chat_id_field.json")
    with pytest.raises(ValueError, match="Real-looking chat_id detected"):
        telegram.run_telegram_dry_run(req)

def test_invalid_live_send():
    req = load_fixture("invalid_live_send_request.json")
    with pytest.raises(ValueError, match="dry_run_only must be true"):
        telegram.run_telegram_dry_run(req)

def test_staging_contract_builds():
    contract = telegram.build_telegram_staging_contract()
    assert contract["platform"] == "telegram"
    assert contract["is_ready_for_credentials"] is False
    assert len(contract["prerequisites_required"]) > 10
