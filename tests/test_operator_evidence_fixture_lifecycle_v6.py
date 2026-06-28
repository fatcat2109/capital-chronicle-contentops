import json
from pathlib import Path
from live_contentops import operator_evidence_fixture_lifecycle_v6 as lifecycle


def test_committed_lifecycle_packet_is_blocked():
    out_dir = Path("docs/automation/V6_OPERATOR_EVIDENCE_FIXTURE_LIFECYCLE")
    lifecycle.main(["--output-dir", str(out_dir)])
    
    packet_file = out_dir / "fixture_lifecycle_packet.json"
    assert packet_file.exists()
    
    data = json.loads(packet_file.read_text(encoding="utf-8"))
    assert data["lifecycle_status"] == "EMPTY_FIXTURE_AWAITING_OPERATOR_INPUT"
    assert data["operator_fixture_exists"] is False
    assert data["evidence_complete"] is False
    assert data["dispatch_allowed_now"] is False
    assert data["live_write_allowed_now"] is False
    assert data["approval_valid_for_dispatch"] is False
    assert data["kill_switch_active"] is True
    assert data["next_recommended_task"] == "TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0"


def test_all_lifecycle_stages_exist():
    out_dir = Path("docs/automation/V6_OPERATOR_EVIDENCE_FIXTURE_LIFECYCLE")
    lifecycle.main(["--output-dir", str(out_dir)])
    
    matrix_file = out_dir / "fixture_lifecycle_stage_matrix.json"
    assert matrix_file.exists()
    matrix = json.loads(matrix_file.read_text(encoding="utf-8"))
    assert set(matrix["stages"].keys()) == set(lifecycle.LIFECYCLE_STAGES)


def test_dry_run_with_missing_fixture_stays_blocked(tmp_path):
    out_dir = tmp_path / "lifecycle_output"
    # Provide a non-existent fixture path
    lifecycle.main(["--fixture-file", "non_existent.json", "--output-dir", str(out_dir)])
    
    packet_file = out_dir / "fixture_lifecycle_packet.json"
    assert packet_file.exists()
    data = json.loads(packet_file.read_text(encoding="utf-8"))
    assert data["lifecycle_status"] == "EMPTY_FIXTURE_AWAITING_OPERATOR_INPUT"
    assert data["evidence_complete"] is False


def test_dry_run_with_placeholder_fixture_stays_incomplete(tmp_path):
    fixture_data = {slot: "PLACEHOLDER_REPLACE_BEFORE_REVIEW" if slot not in ["factual_claims", "citation_candidates", "supporting_artifacts"] else ["PLACEHOLDER_REPLACE_BEFORE_REVIEW"] for slot in lifecycle.REQUIRED_SLOTS}
    fixture_file = tmp_path / "placeholder_fixture.json"
    fixture_file.write_text(json.dumps(fixture_data), encoding="utf-8")
    
    out_dir = tmp_path / "lifecycle_output"
    lifecycle.main(["--fixture-file", str(fixture_file), "--output-dir", str(out_dir)])
    
    packet_file = out_dir / "fixture_lifecycle_packet.json"
    assert packet_file.exists()
    data = json.loads(packet_file.read_text(encoding="utf-8"))
    assert data["lifecycle_status"] == "EMPTY_FIXTURE_AWAITING_OPERATOR_INPUT"
    assert data["evidence_complete"] is False


def test_dry_run_with_unsafe_fixture_is_rejected(tmp_path):
    fixture_data = {slot: "VALID" if slot not in ["factual_claims", "citation_candidates", "supporting_artifacts"] else ["VALID"] for slot in lifecycle.REQUIRED_SLOTS}
    # Inject restricted token/webhook keyword
    fixture_data["source_notes"] = "This contains a secret token value."
    
    fixture_file = tmp_path / "unsafe_fixture.json"
    fixture_file.write_text(json.dumps(fixture_data), encoding="utf-8")
    
    out_dir = tmp_path / "lifecycle_output"
    lifecycle.main(["--fixture-file", str(fixture_file), "--output-dir", str(out_dir)])
    
    packet_file = out_dir / "fixture_lifecycle_packet.json"
    assert packet_file.exists()
    data = json.loads(packet_file.read_text(encoding="utf-8"))
    assert data["lifecycle_status"] == "FIXTURE_REJECTED_UNSAFE_VALUES"
    assert data["evidence_complete"] is False


def test_dry_run_with_valid_synthetic_fixture_shows_success(tmp_path):
    fixture_data = {slot: "VALID_FACTS" if slot not in ["factual_claims", "citation_candidates", "supporting_artifacts"] else ["VALID_FACTS"] for slot in lifecycle.REQUIRED_SLOTS}
    # Affirm disclaimer manually
    fixture_data["no_signal_disclosure"] = "Verified: No signals are contained in this content."
    
    fixture_file = tmp_path / "valid_fixture.json"
    fixture_file.write_text(json.dumps(fixture_data), encoding="utf-8")
    
    out_dir = tmp_path / "lifecycle_output"
    lifecycle.main(["--fixture-file", str(fixture_file), "--output-dir", str(out_dir)])
    
    packet_file = out_dir / "fixture_lifecycle_packet.json"
    assert packet_file.exists()
    data = json.loads(packet_file.read_text(encoding="utf-8"))
    assert data["lifecycle_status"] == "VALIDATION_SUCCESS_READY_FOR_HUMAN_REVIEW"
    assert data["evidence_complete"] is True
    # Verify locks remain strictly locked
    assert data["dispatch_allowed_now"] is False
    assert data["live_write_allowed_now"] is False
    assert data["approval_valid_for_dispatch"] is False
    assert data["kill_switch_active"] is True


def test_no_sensitive_values_in_artifacts():
    out_dir = Path("docs/automation/V6_OPERATOR_EVIDENCE_FIXTURE_LIFECYCLE")
    lifecycle.main(["--output-dir", str(out_dir)])
    
    files = [
        out_dir / "fixture_lifecycle_packet.json",
        out_dir / "fixture_lifecycle_stage_matrix.json",
        out_dir / "fixture_dry_run_validation_report.json",
        out_dir / "fixture_audit_trail_template.json",
        out_dir / "fixture_submission_recovery_runbook.md",
        out_dir / "fixture_do_not_commit_real_evidence_note.md",
        out_dir / "implementation_report.md",
        out_dir / "next_task_pointer.md"
    ]
    
    for f in files:
        assert f.exists()
        content = f.read_text(encoding="utf-8")
        assert "discord.com/api/webhooks" not in content
        assert "token_value" not in content.lower()
        assert "cookie_value" not in content.lower()
        assert "secret_key" not in content.lower()
        assert "env_value" not in content.lower()


def test_module_contains_no_forbidden_behavior():
    attrs = dir(lifecycle)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs
