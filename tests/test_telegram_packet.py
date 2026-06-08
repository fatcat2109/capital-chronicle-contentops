import json
import os
import pytest
from pathlib import Path

def test_telegram_packet_validity():
    packet_path = Path(os.path.dirname(__file__)) / ".." / "docs" / "TELEGRAM_PRIVATE_STAGING_DRY_RUN_OPERATOR_PACKET_V1.json"
    assert packet_path.exists(), "Telegram packet JSON must exist"
    
    with open(packet_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert "packet_id" in data
    assert "task_label" in data
    assert "decision_status" in data
    
    # strictly enforce live capability flags
    assert data["live_credentials_allowed_now"] is False
    assert data["network_allowed_now"] is False
    assert data["telegram_api_allowed_now"] is False
    assert data["publish_allowed_now"] is False
    assert data["autonomous_replies_allowed_now"] is False
    
    assert data["recommended_platform"] == "telegram_private_staging"
    assert len(data["blocker_list"]) > 0
    assert "future_go_requirements" in data
    assert "exact_next_task" in data
    assert "TASK_CONTENTOPS_0048_TELEGRAM_STAGING_DRY_RUN_ARTIFACT_FLOW_AND_AUDIT_TRAIL" in data["exact_next_task"]

def test_telegram_packet_cli(capsys):
    from live_contentops import cli
    cli.telegram_private_staging_packet_status()
    captured = capsys.readouterr()
    
    assert "Live credentials allowed now: False" in captured.out
    assert "Network allowed now: False" in captured.out
    assert "Telegram API allowed now: False" in captured.out
    assert "Publish allowed now: False" in captured.out
    assert "Top Blockers:" in captured.out
    assert "Exact next task: TASK_CONTENTOPS_0048_TELEGRAM_STAGING_DRY_RUN_ARTIFACT_FLOW_AND_AUDIT_TRAIL" in captured.out
