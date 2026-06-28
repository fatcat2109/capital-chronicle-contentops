"""Test verified source pack revalidation coordinator."""
from __future__ import annotations

import json
from pathlib import Path
from live_contentops import verified_source_pack_revalidation_v6 as coordinator


def test_main_execution(tmp_path):
    out_dir = tmp_path / "V6_VERIFIED_SOURCE_PACK_IMPORT_REVALIDATION"
    coordinator.main(["--output-dir", str(out_dir)])

    expected_files = [
        "verified_source_pack_import_packet.json",
        "operator_source_pack_import_template.json",
        "verified_source_pack_import_validation_report.json",
        "source_pack_claim_binding_revalidation_report.json",
        "canonical_draft_gate_revalidation_report.json",
        "test_only_positive_fixture_report.json",
        "verified_source_pack_import_blocker_report.md",
        "verified_source_pack_import_runbook.md",
        "implementation_report.md",
        "next_task_pointer.md"
    ]

    for name in expected_files:
        assert (out_dir / name).exists()

    # Load and check default revalidation report (BLOCKED)
    gate = json.loads((out_dir / "canonical_draft_gate_revalidation_report.json").read_text(encoding="utf-8"))
    assert gate["gate_status"] == "BLOCKED_MISSING_VERIFIED_SOURCE_PACK"
    assert gate["draft_copy_generation_allowed"] is False
    assert gate["publication_allowed"] is False
    assert gate["human_research_required"] is True

    # Load and check positive fixture summary (UNBLOCKED FOR TEST)
    pos = json.loads((out_dir / "test_only_positive_fixture_report.json").read_text(encoding="utf-8"))
    assert pos["synthetic_fixture_loaded"] is True
    assert pos["pos_blockers_count"] == 1
    assert pos["pos_gate_status"] == "PASSED_VERIFIED_SOURCE_PACK_VALID"
    assert pos["draft_generation_possible_on_this_fixture"] is True
