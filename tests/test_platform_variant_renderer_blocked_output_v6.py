"""Test V6 Platform Variant Renderer Blocked Output Coordinator."""
from __future__ import annotations

from pathlib import Path
from live_contentops import platform_variant_renderer_blocked_output_v6 as coordinator


def test_coordinator_execution(tmp_path):
    out_dir = tmp_path / "V6_PLATFORM_VARIANT_RENDERER_BLOCKED_OUTPUT"
    coordinator.main(["--output-dir", str(out_dir)])

    expected = [
        "platform_variant_renderer_packet.json",
        "platform_variant_renderer_input_contract.json",
        "platform_variant_renderer_blocked_output.json",
        "platform_variant_renderer_matrix.json",
        "platform_variant_renderer_checklist.json",
        "platform_variant_renderer_validation_report.json",
        "platform_variant_renderer_blocker_report.md",
        "platform_variant_renderer_runbook.md",
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
