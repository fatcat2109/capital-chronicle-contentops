import json
from pathlib import Path
from live_contentops import operator_pipeline_status_consolidation_v6 as cons


def test_committed_consolidation_packet_is_blocked():
    packet_file = Path("docs/automation/V6_OPERATOR_PIPELINE_STATUS_CONSOLIDATION/operator_pipeline_status_packet.json")
    snap_file = Path("docs/automation/V6_OPERATOR_PIPELINE_STATUS_CONSOLIDATION/operator_pipeline_stage_matrix.json")
    pointer_file = Path("docs/automation/V6_OPERATOR_PIPELINE_STATUS_CONSOLIDATION/next_task_pointer.md")

    assert packet_file.exists()
    assert snap_file.exists()
    assert pointer_file.exists()

    data = json.loads(packet_file.read_text(encoding="utf-8"))
    assert data["overall_status"] == "PREFLIGHT_CANDIDATE_READY_FOR_APPROVAL"
    assert data["evidence_complete"] is True
    assert data["source_preflight_ready"] is True
    
    # Check flags are locked
    assert data["dispatch_allowed_now"] is False
    assert data["live_write_allowed_now"] is False
    assert data["approval_valid_for_dispatch"] is False
    assert data["outbox_entry_created"] is False
    assert data["payload_hash_created"] is False
    assert data["credentials_hydrated"] is False
    assert data["browser_session_started"] is False
    assert data["public_postable"] is False
    assert data["kill_switch_active"] is True

    # Check pointer recommended next task
    pointer = pointer_file.read_text(encoding="utf-8")
    assert "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_GATE_LANE_V0" not in pointer
    assert "TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0" in pointer


def test_stage_matrix_contains_all_required_stages():
    snap_file = Path("docs/automation/V6_OPERATOR_PIPELINE_STATUS_CONSOLIDATION/operator_pipeline_stage_matrix.json")
    matrix = json.loads(snap_file.read_text(encoding="utf-8"))
    
    stages = [m["stage_name"] for m in matrix]
    assert len(stages) == 9
    assert set(stages) == set(cons.STAGES_LIST)
    
    for stage in matrix:
        assert stage["dispatch_allowed_now"] is False
        assert stage["live_write_allowed_now"] is False
        assert stage["approval_valid_for_dispatch"] is False
        assert stage["outbox_entry_created"] is False
        assert stage["payload_hash_created"] is False
        assert stage["credentials_hydrated"] is False
        assert stage["browser_session_started"] is False
        assert stage["public_postable"] is False
        assert stage["kill_switch_active"] is True


def test_no_sensitive_data_in_committed_consolidation_docs():
    for f in [
        "operator_pipeline_status_packet.json",
        "operator_pipeline_stage_matrix.json",
        "operator_next_action_runbook.md",
        "blocked_state_summary.md",
        "operator_fixture_submission_checklist.md",
        "pipeline_truth_table.json"
    ]:
        path = Path("docs/automation/V6_OPERATOR_PIPELINE_STATUS_CONSOLIDATION") / f
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "discord.com/api/webhooks" not in text
        assert "ghp_" not in text
        assert "pytest" not in text
        assert "AppData" not in text
        assert "Temp" not in text

        if f == "operator_next_action_runbook.md":
            assert "Step 1: Copy Operator Evidence Fixture" in text
            assert "Step 2: Fill All 10 Evidence Slots" in text
            assert "Step 3: Run Validator Lane" in text
            assert "Step 4: Staging Gates Preflight" in text
            assert "Step 5: Operator Approval Signatures" in text

        if f == "operator_fixture_submission_checklist.md":
            for slot in [
                "operator_idea_source_ref", "topic_statement", "factual_claims",
                "source_notes", "citation_candidates", "supporting_artifacts",
                "limitation_notes", "no_signal_disclosure", "intended_content_lane",
                "intended_canonical_article_angle"
            ]:
                assert slot in text
            assert "no fake" in text.lower()
            assert "no secret" in text.lower() or "zero secret" in text.lower()
            assert "no financial advice" in text.lower()


def test_synthetic_ready_run(tmp_path):
    # If any packet reports evidence_complete = true, overall status consolidated resolves to ready-for-approval
    console_file = tmp_path / "console_packet.json"
    console_data = {"evidence_complete": True}
    console_file.write_text(json.dumps(console_data), encoding="utf-8")

    output_dir = tmp_path / "consolidation"
    cons.main([
        "--console-packet", str(console_file),
        "--output-dir", str(output_dir)
    ])

    res_file = output_dir / "operator_pipeline_status_packet.json"
    assert res_file.exists()
    
    res = json.loads(res_file.read_text(encoding="utf-8"))
    assert res["overall_status"] == "PREFLIGHT_CANDIDATE_READY_FOR_APPROVAL"
    assert res["evidence_complete"] is True
    assert res["dispatch_allowed_now"] is False
    assert res["live_write_allowed_now"] is False
    assert res["approval_valid_for_dispatch"] is False
    assert res["kill_switch_active"] is True


def test_no_forbidden_behavior_in_module():
    attrs = dir(cons)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs
