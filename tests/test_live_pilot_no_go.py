import pytest
import json
import os

def test_live_pilot_no_go_matrix():
    matrix_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'TELEGRAM_STAGING_LIVE_BLOCKER_MATRIX_V1.json')
    assert os.path.exists(matrix_path), "Blocker matrix JSON must exist"
    
    with open(matrix_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    assert data["decision_status"] == "NO_GO_FOR_LIVE_CREDENTIALS_NOW"
    assert len(data["top_blockers"]) > 0
    assert data["exact_next_task"] == "TASK_CONTENTOPS_0051_LIVE_CONTROL_PLANE_LOCAL_RELEASE_RECAP_AND_OPERATOR_HANDOFF_BUNDLE"
    
    for comp_name, comp_data in data["components"].items():
        assert comp_data["can_use_live_keys_now"] is False
        assert comp_data["can_call_network_now"] is False
        assert comp_data["can_send_telegram_now"] is False
        assert comp_data["can_schedule_now"] is False
        assert comp_data["can_publish_now"] is False

def test_live_pilot_no_go_doc_statements():
    doc_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'TELEGRAM_STAGING_LIVE_PILOT_NO_GO_REINFORCEMENT.md')
    assert os.path.exists(doc_path), "NO-GO reinforcement doc must exist"
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    assert "0048" in content
    assert "0049" in content
    assert "Bot Tokens" in content or "bot token" in content.lower()
    assert "Chat IDs" in content or "chat ID" in content.lower()
    assert "Network Operations" in content or "network" in content.lower()
    assert "Telegram APIs" in content or "telegram api" in content.lower()
    assert "Live Sending" in content or "live sending" in content.lower()
