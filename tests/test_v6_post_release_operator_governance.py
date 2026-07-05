"""Tests for V6 Post-Release Operator Governance & Maintenance Module."""
from __future__ import annotations

import json
from pathlib import Path
from live_contentops.v6_post_release_operator_governance import (
    audit_telemetry_registry,
    inspect_platform_capabilities,
    audit_and_archive_stale_artifacts,
    generate_operator_governance_summary,
    ALL_PLATFORMS,
)

def test_inspect_platform_capabilities_covers_all_ten_platforms():
    caps = inspect_platform_capabilities()
    assert len(caps) == 10
    platform_ids = {c["platform_id"] for c in caps}
    for p in ALL_PLATFORMS:
        assert p in platform_ids

def test_audit_telemetry_registry_with_missing_file(tmp_path):
    fake_path = tmp_path / "non_existent.jsonl"
    result = audit_telemetry_registry(fake_path)
    assert result["exists"] is False
    assert result["total_entries"] == 0

def test_audit_telemetry_registry_with_mock_log(tmp_path):
    mock_log = tmp_path / "telemetry.jsonl"
    entries = [
        {"platform_id": "discord", "success": True},
        {"platform_id": "telegram", "success": True},
        {"platform_id": "meta_facebook", "success": False},
    ]
    with open(mock_log, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")

    result = audit_telemetry_registry(mock_log)
    assert result["exists"] is True
    assert result["total_entries"] == 3
    assert result["success_count"] == 2
    assert result["error_count"] == 1
    assert result["platform_breakdown"]["discord"] == 1
    assert result["platform_breakdown"]["telegram"] == 1
    assert result["platform_breakdown"]["meta_facebook"] == 1

def test_audit_and_archive_stale_artifacts(tmp_path):
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    (scratch / "temp_test.tmp").write_text("data")
    (scratch / "normal.txt").write_text("keep")
    
    stale_dir = scratch / "temp_profile_test"
    stale_dir.mkdir()
    (stale_dir / "nested.txt").write_text("nested data")

    normal_dir = scratch / "keep_profile_test"
    normal_dir.mkdir()

    result = audit_and_archive_stale_artifacts(scratch)
    assert result["status"] == "CLEAN"
    assert "temp_test.tmp" in result["stale_files_found"]
    assert len(result["stale_files_found"]) == 1
    assert "temp_profile_test" in result["stale_directories_found"]
    assert len(result["stale_directories_found"]) == 1
    assert result["archived_count"] == 2

    assert not (scratch / "temp_test.tmp").exists()
    assert not stale_dir.exists()
    assert (scratch / "normal.txt").exists()
    assert normal_dir.exists()

def test_generate_operator_governance_summary():
    summary = generate_operator_governance_summary()
    assert summary["schema_version"] == "6.0.0"
    assert summary["governance_status"] == "PASS_OPERATOR_GOVERNANCE_HEALTHY"
    assert "packet_hash" in summary
    assert len(summary["platform_capabilities"]) == 10
    assert summary["system_invariants"]["financial_advice_forbidden"] is True
