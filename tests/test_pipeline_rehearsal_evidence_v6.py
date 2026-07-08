import json

from live_contentops.pipeline_rehearsal_evidence_v6 import (
    build_rehearsal_evidence_packet,
    readback_checks,
    write_rehearsal_evidence,
)


def test_rehearsal_evidence_packet_binds_result_to_dispatch_audit(tmp_path):
    audit = {
        "run_id": "run_123",
        "pipeline_status": "DISPATCH_PARTIAL_FAILURE",
        "dispatch_live": True,
        "dispatch_summary": {
            "attempted_platforms": ["linkedin"],
            "successful_platforms": [],
            "failed_platforms": ["linkedin"],
            "blocked_platforms": [],
        },
        "dispatch_results": {
            "linkedin": {
                "status": "FAILED",
                "error": "token expired",
                "raw": {"access_token": "never persist raw audit results in evidence"},
            }
        },
    }
    result = {
        "run_id": "run_123",
        "pipeline_status": "DISPATCH_PARTIAL_FAILURE",
        "article_packet_id": "article_1",
        "platform_variant_packet_id": "variant_1",
        "variant_status": "VARIANT_READY",
        "dispatch_audit_path": str(tmp_path / "audit.json"),
        "dispatch_live": True,
        "dispatch_summary": audit["dispatch_summary"],
    }
    packet = build_rehearsal_evidence_packet(
        result,
        command=["python", "-m", "live_contentops.live_production_pipeline_runner_v6"],
        repo_state={"branch": "master", "head_sha": "abc"},
        audit_packet=audit,
    )

    assert packet["readback_checks"] == {
        "audit_file_present": True,
        "run_id_matches": True,
        "pipeline_status_matches": True,
        "dispatch_summary_matches": True,
        "readback_ready": True,
    }
    assert packet["dispatch_audit_excerpt"]["dispatch_summary"] == audit["dispatch_summary"]
    serialized = json.dumps(packet).lower()
    assert "access_token" not in serialized
    assert "never persist raw audit" not in serialized


def test_write_rehearsal_evidence_writes_json_and_summary(tmp_path):
    blocked_audit = {
        "run_id": "run_456",
        "pipeline_status": "DISPATCH_BLOCKED",
        "dispatch_live": False,
        "dispatch_blocked": True,
        "dispatch_blockers": ["public_dispatch_freeze_guard:operator_approval_marker_missing"],
        "dispatch_summary": {
            "attempted_platforms": [],
            "successful_platforms": [],
            "failed_platforms": [],
            "blocked_platforms": ["pipeline"],
        },
        "dispatch_results": {
            "telegram": {
                "status": "PUBLIC_DISPATCH_FROZEN",
                "raw": {"bot_token": "never persist raw audit results in evidence"},
            }
        },
    }
    packet = build_rehearsal_evidence_packet(
        {
            "run_id": "run_456",
            "pipeline_status": "DISPATCH_BLOCKED",
            "dispatch_live": False,
            "dispatch_blocked": True,
            "dispatch_blockers": blocked_audit["dispatch_blockers"],
            "dispatch_summary": blocked_audit["dispatch_summary"],
        },
        repo_state={"branch": "master", "head_sha": "abc"},
        audit_packet=blocked_audit,
    )

    path = write_rehearsal_evidence(packet, tmp_path / "rehearsal_evidence_packet.json")

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["evidence_packet_id"].startswith("v6_pipeline_rehearsal_")
    assert saved["sensitive_marker_detected"] is False
    assert saved["dispatch_audit_excerpt"]["dispatch_blocked"] is True
    assert saved["dispatch_audit_excerpt"]["dispatch_blockers"] == blocked_audit["dispatch_blockers"]
    assert saved["readback_checks"]["readback_ready"] is True
    summary = (tmp_path / "rehearsal_readback_summary.md").read_text(encoding="utf-8")
    assert "V6 Pipeline Rehearsal Readback Summary" in summary
    assert "DISPATCH_BLOCKED" in summary
    assert "pipeline" in summary
    serialized = json.dumps(saved).lower()
    assert "bot_token" not in serialized
    assert "never persist raw audit" not in serialized
    assert "bot_token" not in summary.lower()


def test_readback_checks_detect_mismatched_audit():
    checks = readback_checks(
        {"run_id": "run_a", "pipeline_status": "DISPATCH_COMPLETE", "dispatch_live": True, "dispatch_summary": {"successful_platforms": ["x"]}},
        {"run_id": "run_b", "pipeline_status": "DISPATCH_COMPLETE", "dispatch_summary": {"successful_platforms": ["x"]}},
    )

    assert checks["audit_file_present"] is True
    assert checks["run_id_matches"] is False
    assert checks["pipeline_status_matches"] is True
    assert checks["dispatch_summary_matches"] is True
    assert checks["readback_ready"] is False


def test_generation_only_rehearsal_ignores_stale_dispatch_audit(tmp_path):
    stale_audit = tmp_path / "latest_dispatch_audit.json"
    stale_audit.write_text(
        json.dumps({
            "run_id": "old_dispatch",
            "pipeline_status": "DISPATCH_COMPLETE",
            "dispatch_summary": {"successful_platforms": ["linkedin"]},
        }),
        encoding="utf-8",
    )

    packet = build_rehearsal_evidence_packet(
        {
            "run_id": "generated_only",
            "pipeline_status": "GENERATED",
            "dispatch_audit_path": str(stale_audit),
            "dispatch_live": False,
            "dispatch_summary": {},
        },
        repo_state={"branch": "master", "head_sha": "abc"},
    )

    assert packet["dispatch_audit_excerpt"] == {}
    assert packet["readback_checks"] == {
        "audit_file_present": False,
        "run_id_matches": False,
        "pipeline_status_matches": False,
        "dispatch_summary_matches": False,
        "readback_ready": True,
    }
