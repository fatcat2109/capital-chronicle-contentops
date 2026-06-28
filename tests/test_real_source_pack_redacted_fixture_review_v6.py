"""Test V6 Real Source Pack Redacted Fixture Review Coordinator."""
from __future__ import annotations

import json
from pathlib import Path
from live_contentops import real_source_pack_redacted_fixture_review_v6 as review_mod


def test_coordinator_execution(tmp_path):
    out_dir = tmp_path / "V6_REAL_SOURCE_PACK_REDACTED_FIXTURE_REVIEW"
    review_mod.main(["--output-dir", str(out_dir)])

    expected = [
        "real_source_pack_redacted_fixture_packet.json",
        "operator_filled_redacted_fixture_example.json",
        "redacted_hash_presence_review.json",
        "redacted_claim_binding_review.json",
        "redacted_fixture_validation_report.json",
        "redacted_fixture_blocker_report.md",
        "redacted_fixture_review_runbook.md",
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
