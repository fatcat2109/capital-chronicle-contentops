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
    assert pos["test_only"] is True
    assert pos["runtime_truth"] is False
    assert pos["synthetic_fixture_loaded"] is True
    assert pos["committed_runtime_verified_source_pack_created"] is False
    assert pos["real_source_fetch_performed"] is False
    assert pos["operator_verification_performed"] is False
    assert pos["source_urls_persisted_in_runtime_artifact"] is False
    assert pos["evidence_hashes_persisted_in_runtime_artifact"] is False
    assert pos["positive_path_unit_test_only"] is True
    assert pos["publication_allowed"] is False
    assert pos["dispatch_allowed_now"] is False
    assert pos["public_postable"] is False

    # Check task labels in markdown files
    blocker_md = (out_dir / "verified_source_pack_import_blocker_report.md").read_text(encoding="utf-8")
    assert "TASK_CONTENTOPS_V6_VERIFIED_SOURCE_PACK_IMPORT_AND_REVALIDATION_DRY_RUN_HEAVY_BATCH_V0" in blocker_md
    assert "V6_SOURCE_PACK_VERIFICATION_UI" not in blocker_md

    impl_md = (out_dir / "implementation_report.md").read_text(encoding="utf-8")
    assert "TASK_CONTENTOPS_V6_VERIFIED_SOURCE_PACK_IMPORT_AND_REVALIDATION_DRY_RUN_HEAVY_BATCH_V0" in impl_md
    assert "V6_SOURCE_PACK_VERIFICATION_UI" not in impl_md

    # Check for no leak of operator_jim_sig or real URLs/hashes in all output files
    for name in expected_files:
        content = (out_dir / name).read_text(encoding="utf-8")
        assert "operator_jim_sig" not in content
        assert "federalreserve.gov" not in content
        assert "V6_SOURCE_PACK_VERIFICATION_UI" not in content

    # Check runtime default import artifacts remain blocked and do not set generation/dispatch flags
    import_report = json.loads((out_dir / "verified_source_pack_import_validation_report.json").read_text(encoding="utf-8"))
    assert import_report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "draft_generation_blocked" in import_report["blockers"]

    import_packet = json.loads((out_dir / "verified_source_pack_import_packet.json").read_text(encoding="utf-8"))
    assert import_packet["allowed_for_publication"] is False
    assert import_packet["public_postable"] is False
    assert import_packet["dispatch_allowed_now"] is False

