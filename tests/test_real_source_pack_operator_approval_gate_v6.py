"""Test V6 Real Source Pack Operator Approval Gate Coordinator."""
from __future__ import annotations

import json
from pathlib import Path
from live_contentops import real_source_pack_operator_approval_gate_v6 as gate_mod


def test_coordinator_execution(tmp_path):
    out_dir = tmp_path / "V6_REAL_SOURCE_PACK_OPERATOR_APPROVAL_GATE"
    gate_mod.main(["--output-dir", str(out_dir)])

    expected = [
        "source_pack_operator_approval_gate_packet.json",
        "source_pack_operator_approval_template.json",
        "source_pack_approval_readiness_matrix.json",
        "source_pack_operator_approval_validation_report.json",
        "source_pack_approval_blocker_report.md",
        "source_pack_approval_runbook.md",
        "implementation_report.md",
        "next_task_pointer.md"
    ]

    for name in expected:
        assert (out_dir / name).exists()

    # Verify no raw/fake credentials or signature values leaked
    for name in expected:
        content = (out_dir / name).read_text(encoding="utf-8")
        assert "operator_jim_sig" not in content
        assert "federalreserve.gov" not in content
        assert "test.treasury.gov" not in content
        assert "e3b0c442" not in content
