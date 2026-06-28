import json
from pathlib import Path
from live_contentops import manual_evidence_refresh_orchestrator_v6 as orchestrator


def test_committed_orchestrator_packet_is_blocked():
    out_dir = Path("docs/automation/V6_MANUAL_EVIDENCE_REFRESH_ORCHESTRATOR")
    orchestrator.main(["--output-dir", str(out_dir)])
    
    packet_file = out_dir / "manual_evidence_refresh_orchestrator_packet.json"
    assert packet_file.exists()
    
    data = json.loads(packet_file.read_text(encoding="utf-8"))
    assert data["orchestrator_status"] == "BLOCKED_AWAITING_OPERATOR_EVIDENCE"
    assert data["evidence_complete"] is False
    assert data["operator_fixture_exists"] is False
    assert data["dispatch_allowed_now"] is False
    assert data["live_write_allowed_now"] is False
    assert data["approval_valid_for_dispatch"] is False
    assert data["kill_switch_active"] is True
    assert data["next_recommended_task"] == "TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0"


def test_execution_order_includes_all_required_lanes():
    out_dir = Path("docs/automation/V6_MANUAL_EVIDENCE_REFRESH_ORCHESTRATOR")
    orchestrator.main(["--output-dir", str(out_dir)])
    
    order_file = out_dir / "manual_evidence_refresh_execution_order.json"
    assert order_file.exists()
    order_data = json.loads(order_file.read_text(encoding="utf-8"))
    assert order_data["execution_order"] == orchestrator.EXECUTION_ORDER


def test_dry_run_with_missing_fixture_stays_blocked(tmp_path):
    out_dir = tmp_path / "orchestrator_output"
    orchestrator.main(["--fixture-file", "non_existent.json", "--output-dir", str(out_dir)])
    
    packet_file = out_dir / "V6_MANUAL_EVIDENCE_REFRESH_ORCHESTRATOR/manual_evidence_refresh_orchestrator_packet.json"
    assert packet_file.exists()
    data = json.loads(packet_file.read_text(encoding="utf-8"))
    assert data["orchestrator_status"] == "BLOCKED_AWAITING_OPERATOR_EVIDENCE"
    assert data["evidence_complete"] is False


def test_dry_run_with_placeholder_fixture_stays_incomplete(tmp_path):
    slots = [
        "operator_idea_source_ref", "topic_statement", "factual_claims", "source_notes",
        "citation_candidates", "supporting_artifacts", "limitation_notes",
        "no_signal_disclosure", "intended_content_lane", "intended_canonical_article_angle"
    ]
    fixture_data = {slot: "PLACEHOLDER_REPLACE_BEFORE_REVIEW" if slot not in ["factual_claims", "citation_candidates", "supporting_artifacts"] else ["PLACEHOLDER_REPLACE_BEFORE_REVIEW"] for slot in slots}
    fixture_file = tmp_path / "placeholder_fixture.json"
    fixture_file.write_text(json.dumps(fixture_data), encoding="utf-8")
    
    out_dir = tmp_path / "orchestrator_output"
    orchestrator.main(["--fixture-file", str(fixture_file), "--output-dir", str(out_dir)])
    
    packet_file = out_dir / "V6_MANUAL_EVIDENCE_REFRESH_ORCHESTRATOR/manual_evidence_refresh_orchestrator_packet.json"
    assert packet_file.exists()
    data = json.loads(packet_file.read_text(encoding="utf-8"))
    assert data["orchestrator_status"] == "BLOCKED_AWAITING_OPERATOR_EVIDENCE"
    assert data["evidence_complete"] is False


def test_dry_run_with_unsafe_fixture_is_rejected(tmp_path):
    slots = [
        "operator_idea_source_ref", "topic_statement", "factual_claims", "source_notes",
        "citation_candidates", "supporting_artifacts", "limitation_notes",
        "no_signal_disclosure", "intended_content_lane", "intended_canonical_article_angle"
    ]
    fixture_data = {slot: "VALID" if slot not in ["factual_claims", "citation_candidates", "supporting_artifacts"] else ["VALID"] for slot in slots}
    # Inject restricted token/webhook keyword
    fixture_data["source_notes"] = "This contains a secret token value."
    
    fixture_file = tmp_path / "unsafe_fixture.json"
    fixture_file.write_text(json.dumps(fixture_data), encoding="utf-8")
    
    out_dir = tmp_path / "orchestrator_output"
    orchestrator.main(["--fixture-file", str(fixture_file), "--output-dir", str(out_dir)])
    
    packet_file = out_dir / "V6_MANUAL_EVIDENCE_REFRESH_ORCHESTRATOR/manual_evidence_refresh_orchestrator_packet.json"
    assert packet_file.exists()
    data = json.loads(packet_file.read_text(encoding="utf-8"))
    assert data["orchestrator_status"] == "FIXTURE_REJECTED_UNSAFE_VALUES"
    assert data["evidence_complete"] is False


def test_dry_run_with_valid_synthetic_fixture_shows_success(tmp_path):
    slots = [
        "operator_idea_source_ref", "topic_statement", "factual_claims", "source_notes",
        "citation_candidates", "supporting_artifacts", "limitation_notes",
        "no_signal_disclosure", "intended_content_lane", "intended_canonical_article_angle"
    ]
    fixture_data = {slot: "VALID_FACTS" if slot not in ["factual_claims", "citation_candidates", "supporting_artifacts"] else ["VALID_FACTS"] for slot in slots}
    fixture_data["no_signal_disclosure"] = "Verified: No signals are contained in this content."
    
    fixture_file = tmp_path / "valid_fixture.json"
    fixture_file.write_text(json.dumps(fixture_data), encoding="utf-8")
    
    out_dir = tmp_path / "orchestrator_output"
    orchestrator.main(["--fixture-file", str(fixture_file), "--output-dir", str(out_dir)])
    
    packet_file = out_dir / "V6_MANUAL_EVIDENCE_REFRESH_ORCHESTRATOR/manual_evidence_refresh_orchestrator_packet.json"
    assert packet_file.exists()
    data = json.loads(packet_file.read_text(encoding="utf-8"))
    assert data["orchestrator_status"] == "PREFLIGHT_CANDIDATE_READY_FOR_APPROVAL"
    assert data["evidence_complete"] is True
    # Verify locks remain strictly locked
    assert data["dispatch_allowed_now"] is False
    assert data["live_write_allowed_now"] is False
    assert data["approval_valid_for_dispatch"] is False
    assert data["kill_switch_active"] is True


def test_no_sensitive_values_in_artifacts():
    out_dir = Path("docs/automation/V6_MANUAL_EVIDENCE_REFRESH_ORCHESTRATOR")
    orchestrator.main(["--output-dir", str(out_dir)])
    
    files = [
        out_dir / "manual_evidence_refresh_orchestrator_packet.json",
        out_dir / "manual_evidence_refresh_execution_order.json",
        out_dir / "manual_evidence_refresh_rollup.json",
        out_dir / "manual_evidence_refresh_blocker_report.md",
        out_dir / "manual_evidence_refresh_operator_runbook.md",
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
    attrs = dir(orchestrator)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs
