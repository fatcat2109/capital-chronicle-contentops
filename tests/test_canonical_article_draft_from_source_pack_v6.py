"""Test canonical article draft coordinator execution, including default missing and positive-path fixtures."""
from __future__ import annotations

import json
from pathlib import Path
from live_contentops import canonical_article_draft_from_source_pack_v6 as coordinator


def test_main_execution_default_blocked(tmp_path):
    out_dir = tmp_path / "V6_CANONICAL_ARTICLE_DRAFT_FROM_VERIFIED_SOURCE_PACK"
    coordinator.main(["--output-dir", str(out_dir)])

    expected_files = [
        "verified_source_pack_schema.json",
        "verified_source_pack_missing_default.json",
        "source_pack_gate_report.json",
        "source_claim_binding_report.json",
        "canonical_article_draft_packet.json",
        "canonical_article_draft_preview.md",
        "canonical_article_draft_validation_report.json",
        "canonical_article_draft_blocker_report.md",
        "canonical_article_draft_runbook.md",
        "implementation_report.md",
        "next_task_pointer.md"
    ]

    for name in expected_files:
        assert (out_dir / name).exists()

    # Load draft packet and verify blocked flags
    packet = json.loads((out_dir / "canonical_article_draft_packet.json").read_text(encoding="utf-8"))
    assert packet["canonical_article_draft_status"] == "BLOCKED_MISSING_VERIFIED_SOURCE_PACK"
    assert packet["article_copy_generated"] is False
    assert packet["draft_copy_generation_allowed"] is False
    assert packet["allowed_for_publication"] is False
    assert packet["public_postable"] is False
    assert packet["dispatch_allowed_now"] is False
    assert packet["live_write_allowed_now"] is False
    assert packet["provider_call_performed"] is False
    assert packet["llm_provider_call_performed"] is False
    assert packet["browser_session_started"] is False
    assert packet["credentials_hydrated"] is False
    assert packet["human_review_required"] is True
    assert packet["kill_switch_active"] is True

    # Check preview markdown contains blocked warning and outline scaffold
    preview = (out_dir / "canonical_article_draft_preview.md").read_text(encoding="utf-8")
    assert "DRAFT COPY GENERATION BLOCKED" in preview
    assert "Required Research Sources" in preview
    assert "buy" not in preview.lower()
    assert "sell" not in preview.lower()


def test_positive_path_with_complete_verified_source_pack(tmp_path):
    out_dir = tmp_path / "V6_CANONICAL_ARTICLE_DRAFT_FROM_VERIFIED_SOURCE_PACK"
    
    # Generate complete verified source pack fixture using clean examples
    # (using mock yield database names, no real/fake secrets or buy/sell triggers)
    reqs_path = Path("docs/automation/V6_NEXT_CANONICAL_ARTICLE_FROM_BACKLOG/article_research_requirements.json")
    if reqs_path.exists():
        reqs = json.loads(reqs_path.read_text(encoding="utf-8"))
    else:
        reqs = [{"research_requirement_id": "req_stub", "required_source_type": "treasury_yield_series", "source_name_placeholder": "Stub Yield"}]

    source_entries = []
    for r in reqs:
        source_entries.append({
            "source_requirement_id": r["research_requirement_id"],
            "required_source_type": r["required_source_type"],
            "source_name": "Official Treasury yield database series index",
            "source_url": "https://example-official-sources.gov/yields",
            "source_publisher": "Federal Statistics Bureau",
            "retrieval_method": "manual_ingestion",
            "retrieved_at": "2026-06-28T12:00:00Z",
            "evidence_hash": "sha256_8f93aa900ef2a1",
            "source_excerpt_ref": "Verified interest rate spread values",
            "verification_status": "verified",
            "operator_verified_by": "operator_jim_sig",
            "source_supports_claim_ids": ["claim_stub"],
            "limitations": "Subject to historical reporting updates.",
            "caveats": "Consult policy guidelines.",
            "allowed_for_article_use": True,
            "human_review_required": True
        })

    verified_pack = {
        "verified_source_pack_status": "COMPLETE",
        "source_pack_complete": True,
        "human_research_required": True,
        "source_verification_required": True,
        "source_entries": source_entries
    }

    pack_file = tmp_path / "verified_source_pack_fixture.json"
    pack_file.write_text(json.dumps(verified_pack, indent=2), encoding="utf-8")

    coordinator.main([
        "--output-dir", str(out_dir),
        "--custom-source-pack", str(pack_file)
    ])

    # Check generated preview and reports
    preview = (out_dir / "canonical_article_draft_preview.md").read_text(encoding="utf-8")
    assert "DRAFT COPY GENERATION BLOCKED" not in preview
    assert "Official Treasury yield database series index" in preview

    # Verify flags are still locked to review-only
    packet = json.loads((out_dir / "canonical_article_draft_packet.json").read_text(encoding="utf-8"))
    assert packet["canonical_article_draft_status"] == "READY_FOR_OPERATOR_REVIEW"
    assert packet["article_copy_generated"] is True
    assert packet["draft_copy_generation_allowed"] is True
    assert packet["allowed_for_publication"] is False
    assert packet["public_postable"] is False
    assert packet["dispatch_allowed_now"] is False
    assert packet["live_write_allowed_now"] is False
