import json
import os
import pytest
from pathlib import Path

def test_operator_prerequisites_validity():
    prereq_path = Path(os.path.dirname(__file__)) / ".." / "docs" / "archive" / "_repo_cleanup_2026-07-03-pass2" / "docs" / "LIVE_PILOT_OPERATOR_PREREQUISITES_V1.json"
    assert prereq_path.exists(), "Prerequisites JSON must exist"
    
    with open(prereq_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert "prerequisites" in data
    entries = data["prerequisites"]
    
    # ensure it parses and contains required fields
    for entry in entries:
        assert "id" in entry
        assert "title" in entry
        assert "status" in entry
        assert "required_before" in entry
        assert "evidence_required" in entry
        assert "owner" in entry
        assert "can_store_secret_value_here" in entry
        assert "can_commit_to_git" in entry
        assert "blocker_if_missing" in entry
        
        # explicitly forbid secret storage
        assert entry["can_store_secret_value_here"] is False, f"NO-GO: {entry['id']} cannot store secret values"
        
        # explicitly ensure missing fields
        assert entry["status"] in ["MISSING_OPERATOR_INPUT", "FUTURE_VERIFICATION_REQUIRED", "DESIGN_DEFINED_NOT_EXECUTED", "NOT_REQUIRED_FOR_DRY_RUN"], f"Invalid status: {entry['status']}"
        
    # ensure at least one blocker remains explicit
    blockers = [e for e in entries if e["blocker_if_missing"] is True and e["status"] in ["MISSING_OPERATOR_INPUT", "FUTURE_VERIFICATION_REQUIRED"]]
    assert len(blockers) > 0, "At least one live blocker must remain explicitly missing or unverified"

def test_prerequisite_cli(capsys):
    from live_contentops import cli
    cli.pilot_prerequisites_status()
    captured = capsys.readouterr()
    
    assert "Live pilot credential GO allowed now: False" in captured.out
    assert "Network allowed now: False" in captured.out
    assert "Publish allowed now: False" in captured.out
    assert "Top Blockers:" in captured.out
    assert "Recommended next task: TASK_CONTENTOPS_0047_TELEGRAM_PRIVATE_STAGING_DRY_RUN_OPERATOR_PACKET" in captured.out
