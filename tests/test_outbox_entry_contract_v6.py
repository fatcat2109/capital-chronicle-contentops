"""Unit tests for outbox entry contract coordinator."""
from __future__ import annotations

from pathlib import Path
from live_contentops import outbox_entry_contract_v6 as coordinator


def test_coordinator_execution(tmp_path):
    out_dir = tmp_path / "V6_OUTBOX_ENTRY_CONTRACT"
    coordinator.main(["--output-dir", str(out_dir)])

    expected = [
        "outbox_entry_packet.json",
        "outbox_entry_input_contract.json",
        "outbox_entry_blocked_template.json",
        "outbox_entry_blocked_output.json",
        "outbox_entry_gate_matrix.json",
        "outbox_entry_checklist.json",
        "outbox_entry_validation_report.json",
        "outbox_entry_blocker_report.md",
        "outbox_entry_runbook.md",
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
