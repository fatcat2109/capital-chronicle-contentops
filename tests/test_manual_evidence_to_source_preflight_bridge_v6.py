import json
from pathlib import Path
from live_contentops import manual_evidence_to_source_preflight_bridge_v6 as bridge


def test_committed_bridge_packet_is_honest_awaiting():
    # Verify the committed repo bridge packet is blocked and locked
    packet_file = Path("docs/automation/V6_MANUAL_EVIDENCE_TO_SOURCE_PREFLIGHT_BRIDGE/bridge_packet.json")
    snap_file = Path("docs/automation/V6_MANUAL_EVIDENCE_TO_SOURCE_PREFLIGHT_BRIDGE/evidence_to_preflight_status_snapshot.json")
    pointer_file = Path("docs/automation/V6_MANUAL_EVIDENCE_TO_SOURCE_PREFLIGHT_BRIDGE/next_task_pointer.md")

    assert packet_file.exists()
    assert snap_file.exists()
    assert pointer_file.exists()

    data = json.loads(packet_file.read_text(encoding="utf-8"))
    assert data["bridge_status"] == "BLOCKED_AWAITING_OPERATOR_EVIDENCE"
    assert data["evidence_complete"] is False
    assert data["source_preflight_ready"] is False
    
    # Flags lock checking
    assert data["dispatch_allowed_now"] is False
    assert data["live_write_allowed_now"] is False
    assert data["approval_valid_for_dispatch"] is False
    assert data["outbox_entry_created"] is False
    assert data["payload_hash_created"] is False
    assert data["credentials_hydrated"] is False
    assert data["browser_session_started"] is False
    assert data["public_postable"] is False
    assert data["kill_switch_active"] is True

    snap = json.loads(snap_file.read_text(encoding="utf-8"))
    assert snap["evidence_complete"] is False
    assert snap["source_preflight_ready"] is False
    assert snap["preflight_bridge_status"] == "BLOCKED_AWAITING_OPERATOR_EVIDENCE"
    assert snap["dispatch_blocked"] is True

    pointer = pointer_file.read_text(encoding="utf-8")
    assert "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_GATE_LANE_V0" not in pointer
    assert "TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0" in pointer


def test_synthetic_valid_evidence_preflight_projection(tmp_path):
    # Setup test input mock files in temp path
    wiring_file = tmp_path / "validator_wiring_packet.json"
    snap_file = tmp_path / "operator_fixture_resolution_snapshot.json"
    summary_file = tmp_path / "manual_evidence_fixture_validation_summary.json"
    fixture_file = tmp_path / "operator_evidence_fixture.json"

    # Synthetic complete fixture data
    fixture_data = {
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
    fixture_file.write_text(json.dumps(fixture_data), encoding="utf-8")

    wiring_data = {
        "wiring_status": "WIRING_SUCCESS",
        "resolved_fixture_file": str(fixture_file),
        "resolution_reason": "CLI override test mock"
    }
    wiring_file.write_text(json.dumps(wiring_data), encoding="utf-8")

    snap_data = {
        "evidence_complete": True,
        "status_at_resolution": "VALIDATION_SUCCESS_READY_FOR_HUMAN_REVIEW",
        "selected_fixture_file": str(fixture_file)
    }
    snap_file.write_text(json.dumps(snap_data), encoding="utf-8")

    summary_data = {
        "validation_status": "VALIDATION_SUCCESS_READY_FOR_HUMAN_REVIEW",
        "evidence_complete": True
    }
    summary_file.write_text(json.dumps(summary_data), encoding="utf-8")

    # Run bridge script outputting to tmp_path / "bridge"
    output_dir = tmp_path / "bridge"
    bridge.main([
        "--wiring-packet", str(wiring_file),
        "--resolution-snapshot", str(snap_file),
        "--validation-summary", str(summary_file),
        "--output-dir", str(output_dir)
    ])

    # Check generated files in the test-isolated directory
    res_packet_file = output_dir / "bridge_packet.json"
    assert res_packet_file.exists()
    res_data = json.loads(res_packet_file.read_text(encoding="utf-8"))
    
    # Should project ready state, but keeping dispatch locked!
    assert res_data["bridge_status"] == "PREFLIGHT_CANDIDATE_READY_FOR_REVIEW"
    assert res_data["source_preflight_ready"] is True
    assert res_data["evidence_complete"] is True
    assert res_data["dispatch_allowed_now"] is False
    assert res_data["live_write_allowed_now"] is False
    assert res_data["approval_valid_for_dispatch"] is False
    assert res_data["public_postable"] is False
    assert res_data["kill_switch_active"] is True

    projection_file = output_dir / "source_preflight_input_projection.json"
    assert projection_file.exists()
    proj = json.loads(projection_file.read_text(encoding="utf-8"))
    for slot in [
        "operator_idea_source_ref_status", "topic_statement_status", "factual_claims_status",
        "citation_candidates_status", "supporting_artifacts_status", "limitation_notes_status",
        "no_signal_disclosure_status", "intended_content_lane_status", "intended_canonical_article_angle_status"
    ]:
        assert proj[slot] == "PROVIDED_VAL_READY"


def test_bridge_packet_contains_no_sensitive_values():
    packet_file = Path("docs/automation/V6_MANUAL_EVIDENCE_TO_SOURCE_PREFLIGHT_BRIDGE/bridge_packet.json")
    data = json.loads(packet_file.read_text(encoding="utf-8"))
    
    # Check no Windows temp absolute paths or pytest paths
    for val in data.values():
        if isinstance(val, str):
            assert "pytest" not in val
            assert "AppData" not in val
            assert "Temp" not in val
            assert "discord.com/api/webhooks" not in val


def test_no_forbidden_behavior_in_module():
    attrs = dir(bridge)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs
