"""Test V6 Platform Variant Input Contract Queue Coordinator."""
from __future__ import annotations

from pathlib import Path
from live_contentops import platform_variant_input_contract_queue_v6 as coordinator


def test_coordinator_execution(tmp_path):
    out_dir = tmp_path / "V6_PLATFORM_VARIANT_INPUT_CONTRACT_QUEUE"
    coordinator.main(["--output-dir", str(out_dir)])

    expected = [
        "platform_variant_queue_packet.json",
        "platform_variant_input_contract.json",
        "platform_variant_blocked_output.json",
        "platform_variant_readiness_matrix.json",
        "platform_variant_checklist.json",
        "platform_variant_queue_validation_report.json",
        "platform_variant_blocker_report.md",
        "platform_variant_runbook.md",
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
