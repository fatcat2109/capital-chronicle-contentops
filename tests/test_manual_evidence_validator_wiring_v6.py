import json
from pathlib import Path
from live_contentops import manual_evidence_fixture_validator_v6 as validator


def test_missing_console_fixture_defaults_to_empty(tmp_path):
    # If no CLI and no console file exists, validation status defaults to EMPTY_FIXTURE_AWAITING_OPERATOR_INPUT
    # We mock main with tmp_path as output dir
    output_dir = tmp_path / "validator_output"
    
    # We run main, ensuring we don't have console file at docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/operator_evidence_fixture.json
    # or docs/automation/V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR/operator_fillable_fixture.json
    # by making sure CLI is run or console/fallbacks are missing
    
    # We can pass an empty CLI path or none. If console_path is missing, resolution fallback or missing will trigger.
    # To isolate, let's call validate_fixture directly and main with an empty/non-existent temp CLI file.
    
    non_existent = tmp_path / "does_not_exist.json"
    status, errors, rejected, unsafe, complete = validator.validate_fixture({})
    assert status == "EMPTY_FIXTURE_AWAITING_OPERATOR_INPUT"
    assert complete is False


def test_empty_or_placeholder_console_fixture_not_complete():
    # If a console fixture has only placeholders, it must remain EMPTY_FIXTURE_AWAITING_OPERATOR_INPUT
    placeholders = {slot: "PLACEHOLDER_REPLACE_BEFORE_REVIEW" for slot in validator.REQUIRED_SLOTS}
    status, errors, rejected, unsafe, complete = validator.validate_fixture(placeholders)
    assert status == "EMPTY_FIXTURE_AWAITING_OPERATOR_INPUT"
    assert complete is False


def test_unsafe_console_fixture_is_rejected():
    unsafe_fixture = {
        "operator_idea_source_ref": "https://discord.com/api/webhooks/123",
        "topic_statement": "Valid topic",
        "factual_claims": ["claim"],
        "source_notes": "verified",
        "citation_candidates": ["citation"],
        "supporting_artifacts": ["doc"],
        "limitation_notes": "none",
        "no_signal_disclosure": "yes",
        "intended_content_lane": "substack",
        "intended_canonical_article_angle": "angle"
    }
    status, errors, rejected, unsafe, complete = validator.validate_fixture(unsafe_fixture)
    assert status == "FIXTURE_REJECTED_UNSAFE_VALUES"
    assert unsafe is True
    assert complete is False


def test_valid_synthetic_safe_test_fixture(tmp_path):
    safe_fixture = {
        "operator_idea_source_ref": "docs/evidence/jim_notes.pdf",
        "topic_statement": "Valid topic",
        "factual_claims": ["claim"],
        "source_notes": "verified",
        "citation_candidates": ["citation"],
        "supporting_artifacts": ["doc"],
        "limitation_notes": "none",
        "no_signal_disclosure": "yes",
        "intended_content_lane": "substack",
        "intended_canonical_article_angle": "angle"
    }
    
    status, errors, rejected, unsafe, complete = validator.validate_fixture(safe_fixture)
    assert status == "VALIDATION_SUCCESS_READY_FOR_HUMAN_REVIEW"
    assert complete is True


def test_cli_override_console(tmp_path):
    # If a CLI path is passed, it takes precedence
    cli_file = tmp_path / "cli_fixture.json"
    cli_fixture = {
        "operator_idea_source_ref": "docs/evidence/cli_notes.pdf",
        "topic_statement": "CLI topic",
        "factual_claims": ["cli claim"],
        "source_notes": "verified via cli",
        "citation_candidates": ["cli citation"],
        "supporting_artifacts": ["cli doc"],
        "limitation_notes": "none",
        "no_signal_disclosure": "yes",
        "intended_content_lane": "substack",
        "intended_canonical_article_angle": "cli angle"
    }
    cli_file.write_text(json.dumps(cli_fixture), encoding="utf-8")
    
    # We call main specifying CLI argument and isolated test directories
    output_dir = tmp_path / "validator_output"
    wiring_dir = tmp_path / "wiring_output"
    validator.main([
        "--fixture-file", str(cli_file),
        "--output-dir", str(output_dir),
        "--wiring-output-dir", str(wiring_dir)
    ])
    
    # Verify resolution snapshot in isolated temp directory
    snap_file = wiring_dir / "operator_fixture_resolution_snapshot.json"
    assert snap_file.exists()
    
    snap = json.loads(snap_file.read_text(encoding="utf-8"))
    assert snap["selected_fixture_file"] == str(cli_file)
    assert "CLI --fixture-file" in snap["resolution_reason"]
    assert snap["evidence_complete"] is True
    assert snap["status_at_resolution"] == "VALIDATION_SUCCESS_READY_FOR_HUMAN_REVIEW"


def test_committed_artifacts_honesty():
    # Verify the committed repo artifacts reflect honest, unpolluted awaiting state
    wiring_file = Path("docs/automation/V6_MANUAL_EVIDENCE_VALIDATOR_WIRING/validator_wiring_packet.json")
    snap_file = Path("docs/automation/V6_MANUAL_EVIDENCE_VALIDATOR_WIRING/operator_fixture_resolution_snapshot.json")
    pointer_file = Path("docs/automation/V6_MANUAL_EVIDENCE_VALIDATOR_WIRING/next_task_pointer.md")

    assert wiring_file.exists()
    assert snap_file.exists()
    assert pointer_file.exists()

    wiring = json.loads(wiring_file.read_text(encoding="utf-8"))
    snap = json.loads(snap_file.read_text(encoding="utf-8"))
    pointer = pointer_file.read_text(encoding="utf-8")

    # Contaminated paths checks
    for path_str in [str(wiring.get("resolved_fixture_file")), str(snap.get("selected_fixture_file"))]:
        if path_str and path_str != "None":
            assert "pytest" not in path_str
            assert "AppData" not in path_str
            assert "Temp" not in path_str
            assert Path(path_str).is_absolute() is False

    # Honest awaiting checks
    assert wiring["dispatch_allowed_now"] is False
    assert wiring["live_write_allowed_now"] is False
    assert wiring["approval_valid_for_dispatch"] is False
    assert wiring["credentials_hydrated"] is False
    assert wiring["browser_session_started"] is False
    assert wiring["kill_switch_active"] is True

    assert snap["evidence_complete"] is False
    assert snap["status_at_resolution"] == "EMPTY_FIXTURE_AWAITING_OPERATOR_INPUT"

    # Pointer checks
    assert "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_GATE_LANE_V0" not in pointer
    assert "TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0" in pointer


def test_wiring_packet_safety(tmp_path):
    # Test generated wiring file safety
    output_dir = tmp_path / "validator_output"
    wiring_dir = tmp_path / "wiring_output"
    validator.main([
        "--output-dir", str(output_dir),
        "--wiring-output-dir", str(wiring_dir)
    ])

    wiring_file = wiring_dir / "validator_wiring_packet.json"
    assert wiring_file.exists()
    
    data = json.loads(wiring_file.read_text(encoding="utf-8"))
    assert data["dispatch_allowed_now"] is False
    assert data["live_write_allowed_now"] is False
    assert data["approval_valid_for_dispatch"] is False
    assert data["public_postable"] is False
    assert data["credentials_hydrated"] is False
    assert data["browser_session_started"] is False
    assert data["kill_switch_active"] is True
    
    # No raw secret keywords
    assert data.get("raw_secret_output", False) is False
    assert data.get("webhook_url_printed", False) is False


def test_no_forbidden_behavior_in_module():
    attrs = dir(validator)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs
