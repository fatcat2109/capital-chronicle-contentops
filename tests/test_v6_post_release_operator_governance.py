"""Tests for V6 Post-Release Operator Governance & Maintenance Module."""
from __future__ import annotations

import json
from pathlib import Path
from live_contentops.v6_post_release_operator_governance import (
    audit_telemetry_registry,
    rotate_telemetry_log,
    inspect_platform_capabilities,
    audit_and_archive_stale_artifacts,
    audit_status_ledger_alignment,
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
    assert result["corrupt_entries_count"] == 0
    assert result["telemetry_archive"]["exists"] is False
    assert result["telemetry_archive"]["total_entries"] == 0
    assert result["telemetry_archive"]["size_bytes"] == 0

def test_audit_telemetry_registry_with_mock_log(tmp_path):
    mock_log = tmp_path / "telemetry.jsonl"
    archive_log = tmp_path / "telemetry_archive.jsonl"
    
    entries = [
        {"platform_id": "discord", "success": True},
        {"platform_id": "telegram", "success": True},
        {"platform_id": "meta_facebook", "success": False},
    ]
    with open(mock_log, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
        f.write("corrupt json line\n")

    # Create mock archive entries
    archive_entries = [
        {"platform_id": "discord", "success": True},
        {"platform_id": "threads", "success": True},
    ]
    with open(archive_log, "w", encoding="utf-8") as f:
        for e in archive_entries:
            f.write(json.dumps(e) + "\n")

    result = audit_telemetry_registry(mock_log)
    assert result["exists"] is True
    assert result["total_entries"] == 3
    assert result["success_count"] == 2
    assert result["error_count"] == 1
    assert result["corrupt_entries_count"] == 1
    assert result["platform_breakdown"]["discord"] == 1
    assert result["platform_breakdown"]["telegram"] == 1
    assert result["platform_breakdown"]["meta_facebook"] == 1
    
    assert result["telemetry_archive"]["exists"] is True
    assert result["telemetry_archive"]["total_entries"] == 2
    assert result["telemetry_archive"]["size_bytes"] > 0

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

def test_audit_status_ledger_alignment(tmp_path):
    status_json = tmp_path / "current_project_status.json"
    observed_sha = "a" * 40
    status_json.write_text(
        json.dumps(
            {
                "last_verified_remote_sha": observed_sha,
                "accepted_product_baseline_sha": "b" * 40,
                "last_status_commit_sha": "c" * 40,
                "latest_accepted_task": "TASK_TEST",
            }
        ),
        encoding="utf-8",
    )

    aligned = audit_status_ledger_alignment(status_json, observed_sha)
    assert aligned["status"] == "PASS_STATUS_LEDGER_ALIGNED"
    assert aligned["ledger_matches_observed_remote"] is True
    assert aligned["issues"] == []

    mismatch = audit_status_ledger_alignment(status_json, "d" * 40)
    assert mismatch["status"] == "REQUIRES_STATUS_LEDGER_RECONCILIATION"
    assert mismatch["ledger_matches_observed_remote"] is False
    assert mismatch["issues"] == ["last_verified_remote_sha_mismatch"]


def test_audit_status_ledger_alignment_with_missing_file(tmp_path):
    missing = audit_status_ledger_alignment(tmp_path / "missing.json", "a" * 40)
    assert missing["status"] == "MISSING_STATUS_LEDGER"
    assert missing["ledger_matches_observed_remote"] is False
    assert missing["issues"] == ["status_json_missing"]


def test_generate_operator_governance_summary():
    summary = generate_operator_governance_summary()
    assert summary["schema_version"] == "6.0.0"
    assert summary["governance_status"] in {
        "PASS_OPERATOR_GOVERNANCE_HEALTHY",
        "REQUIRES_STATUS_LEDGER_RECONCILIATION",
    }
    assert "packet_hash" in summary
    assert len(summary["platform_capabilities"]) == 10
    assert summary["system_invariants"]["financial_advice_forbidden"] is True
    assert "corrupt_entries_count" in summary["telemetry_audit"]
    assert "telemetry_rotation" in summary
    assert "status_ledger_audit" in summary
    assert summary["status_ledger_audit"]["status_json_exists"] is True


def test_rotate_telemetry_log(tmp_path):
    mock_log = tmp_path / "telemetry_rot.jsonl"
    archive_log = tmp_path / "telemetry_rot_archive.jsonl"

    # 1. Non-existent file
    res = rotate_telemetry_log(mock_log, max_lines=2)
    assert res["rotated"] is False
    assert res["archived_lines"] == 0

    # 2. Under max_lines limit
    with open(mock_log, "w", encoding="utf-8") as f:
        f.write('{"id": 1}\n')
    res = rotate_telemetry_log(mock_log, max_lines=2)
    assert res["rotated"] is False
    assert res["archived_lines"] == 0

    # 3. Exceeds limit -> should rotate
    with open(mock_log, "a", encoding="utf-8") as f:
        f.write('{"id": 2}\n')
        f.write('{"id": 3}\n')
        f.write('{"id": 4}\n')

    # active has 4 lines now, limit is 2. Rotation keeps limit // 2 = 1 line. Rotates 3.
    res = rotate_telemetry_log(mock_log, max_lines=2)
    assert res["rotated"] is True
    assert res["archived_lines"] == 3

    # check remaining lines in mock_log
    with open(mock_log, "r", encoding="utf-8") as f:
        active_lines = f.readlines()
    assert len(active_lines) == 1
    assert json.loads(active_lines[0])["id"] == 4

    # check archived lines
    assert archive_log.exists()
    with open(archive_log, "r", encoding="utf-8") as f:
        archived_lines = f.readlines()
    assert len(archived_lines) == 3
    assert json.loads(archived_lines[0])["id"] == 1
    assert json.loads(archived_lines[1])["id"] == 2
    assert json.loads(archived_lines[2])["id"] == 3

