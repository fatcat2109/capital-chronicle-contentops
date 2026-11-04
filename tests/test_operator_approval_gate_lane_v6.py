import json
from pathlib import Path
from live_contentops import operator_approval_gate_v6 as approval
from live_contentops import project_sources_upload_bundle_v6 as upload


def test_committed_approval_packet_properties():
    out_dir = Path("docs/automation/V6_OPERATOR_APPROVAL_GATE")
    approval.main(["--output-dir", str(out_dir)])
    
    packet_file = out_dir / "operator_approval_gate_packet.json"
    assert packet_file.exists()
    
    data = json.loads(packet_file.read_text(encoding="utf-8"))
    assert data["approval_gate_status"] == "AWAITING_OPERATOR_SIGNATURE"
    assert data["evidence_complete"] is True
    assert data["source_preflight_ready"] is True
    assert data["source_ref_resolved"] is True
    assert data["operator_idea_source_ref_resolved"] is True
    
    # Critical security locks
    assert data["approval_valid_for_dispatch"] is False
    assert data["dispatch_allowed_now"] is False
    assert data["live_write_allowed_now"] is False
    assert data["outbox_entry_created"] is False
    assert data["payload_hash_created"] is True
    assert data["credentials_hydrated"] is False
    assert data["browser_session_started"] is False
    assert data["public_postable"] is False
    assert data["kill_switch_active"] is True


def test_signature_template_is_inert():
    out_dir = Path("docs/automation/V6_OPERATOR_APPROVAL_GATE")
    approval.main(["--output-dir", str(out_dir)])
    
    sig_file = out_dir / "operator_approval_signature_template.json"
    assert sig_file.exists()
    
    data = json.loads(sig_file.read_text(encoding="utf-8"))
    assert data["operator_id"] == "PLACEHOLDER_OPERATOR_ID"
    assert data["approval_decision"] == "PENDING"
    assert data["payload_hash"] is None
    assert data["valid_for_dispatch"] is False
    assert data["expires_at"] is None
    assert data["revoked"] is False


def test_no_raw_fixture_body_in_approval_reports():
    out_dir = Path("docs/automation/V6_OPERATOR_APPROVAL_GATE")
    approval.main(["--output-dir", str(out_dir)])
    
    files = [
        out_dir / "operator_approval_gate_packet.json",
        out_dir / "operator_approval_review_packet.json",
        out_dir / "operator_approval_signature_template.json",
        out_dir / "operator_approval_blocker_report.md",
        out_dir / "operator_approval_runbook.md",
        out_dir / "implementation_report.md",
        out_dir / "next_task_pointer.md"
    ]
    
    for f in files:
        assert f.exists()
        content = f.read_text(encoding="utf-8")
        assert "Capital Chronicle ContentOps V6 now has a guarded manual" not in content
        assert "The scoped network policy restricts external domain" not in content
        assert "Reviewing V6 contentops security" not in content
        assert "discord.com/api/webhooks" not in content
        assert "token_value" not in content.lower()
        assert "cookie_value" not in content.lower()


def test_stale_rollup_repair_in_upload_bundle(tmp_path):
    # Simulate bundle candidate list generation
    tmp_rb = tmp_path / "readiness_evidence_bundle_packet.json"
    tmp_dr = tmp_path / "supervised_dispatch_readiness_packet.json"
    
    rb_data = {
        "readiness_evidence_bundle_packet_id": "bundle_fbe34af9e66e",
        "source_supervised_dispatch_readiness_packet_id": "readiness_34edf10af116",
        "unresolved_blockers": [
            "destination_binding_incomplete",
            "evidence_incomplete",
            "kill_switch_active",
            "live_write_authorization_missing",
            "operator_approval_incomplete",
            "operator_idea_source_ref_missing",
            "outbox_creation_blocked",
            "payload_hash_incomplete",
            "safety_review_incomplete"
        ]
    }
    dr_data = {
        "supervised_dispatch_readiness_packet_id": "readiness_34edf10af116"
    }
    
    tmp_rb.write_text(json.dumps(rb_data), encoding="utf-8")
    tmp_dr.write_text(json.dumps(dr_data), encoding="utf-8")
    
    # Write a simulated delegated evidence refresh result to tmp_path to trigger filtering
    (tmp_path / "delegated_evidence_refresh_result.json").write_text(json.dumps({
        "evidence_complete": True
    }), encoding="utf-8")
    
    packet, files = upload.materialize_project_sources_upload_bundle_packets(tmp_rb, tmp_dr)
    
    # Since delegated evidence exists or console fixture is complete
    assert "evidence_incomplete" not in packet["unresolved_blockers"]
    assert "operator_idea_source_ref_missing" not in packet["unresolved_blockers"]
    
    # Must preserve locks
    assert "operator_approval_incomplete" in packet["unresolved_blockers"]
    assert "payload_hash_incomplete" in packet["unresolved_blockers"]
    assert "kill_switch_active" in packet["unresolved_blockers"]
    assert "safety_review_incomplete" in packet["unresolved_blockers"]


def test_module_contains_no_forbidden_behavior():
    attrs = dir(approval)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs


def test_operator_approval_runbook_dispatch_validity_boundary():
    out_dir = Path("docs/automation/V6_OPERATOR_APPROVAL_GATE")
    approval.main(["--output-dir", str(out_dir)])
    
    runbook_file = out_dir / "operator_approval_runbook.md"
    assert runbook_file.exists()
    content = runbook_file.read_text(encoding="utf-8")
    
    # Assert runbook does not instruct setting dispatch validity to true / near true
    assert "valid_for_dispatch=true" not in content.replace(" ", "").lower()
    assert "valid_for_dispatch to true" not in content.lower()
    assert "keep `valid_for_dispatch=false`" in content.lower()
    
    # Assert runbook points to signature-binding as next control stage after payload hash exists
    assert "task_contentops_v6_operator_approval_signature_binding_lane_heavy_batch_v0" in content.lower()


def test_operator_approval_review_packet_keeps_safety_boundaries():
    out_dir = Path("docs/automation/V6_OPERATOR_APPROVAL_GATE")
    approval.main(["--output-dir", str(out_dir)])
    
    review_file = out_dir / "operator_approval_review_packet.json"
    assert review_file.exists()
    
    data = json.loads(review_file.read_text(encoding="utf-8"))
    assert data["exact_approved_content_unavailable"] is True
    assert data["dispatch_not_authorized"] is True
    assert data["live_write_not_authorized"] is True
