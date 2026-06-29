"""Unit tests for approval queue exact payload review contract coordinator."""
from __future__ import annotations

from pathlib import Path
from live_contentops import approval_queue_exact_payload_review_contract_v6 as coordinator


def test_coordinator_execution(tmp_path):
    out_dir = tmp_path / "V6_APPROVAL_QUEUE_EXACT_PAYLOAD_REVIEW_CONTRACT"
    coordinator.main(["--output-dir", str(out_dir)])

    expected = [
        "approval_queue_exact_payload_review_packet.json",
        "approval_queue_exact_payload_review_input_contract.json",
        "approval_queue_blocked_review_template.json",
        "approval_queue_blocked_review_output.json",
        "approval_queue_review_gate_matrix.json",
        "approval_queue_review_checklist.json",
        "approval_queue_review_validation_report.json",
        "approval_queue_review_blocker_report.md",
        "approval_queue_review_runbook.md",
        "implementation_report.md",
        "next_task_pointer.md"
    ]

    for name in expected:
        assert (out_dir / name).exists()

    # Verify no leaks in generated files
    for name in expected:
        content = (out_dir / name).read_text(encoding="utf-8")
        assert "operator_jim_sig" not in content
        assert "federalreserve.gov" not in content
        assert "test.treasury.gov" not in content
