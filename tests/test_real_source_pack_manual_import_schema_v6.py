"""Test V6 Real Source Pack Manual Import Schema Definition."""
from __future__ import annotations

import json
from pathlib import Path
from live_contentops import real_source_pack_manual_import_schema_v6 as schema_mod


def test_schema_fields_definition():
    fields = schema_mod.get_source_entry_schema_fields()
    
    assert fields["source_requirement_id"] == "string"
    assert fields["required_source_type"] == "string"
    assert fields["source_name_redacted"] == "string"
    assert fields["source_url_redacted"] == "string"
    assert fields["source_publisher_redacted"] == "string"
    assert fields["verification_status"] == "string"
    assert fields["allowed_for_article_use"] == "boolean"
    assert fields["human_review_required"] == "boolean"
    assert fields["runtime_truth"] == "boolean"


def test_blank_import_fixture():
    fixture = schema_mod.make_blank_import_fixture()
    
    assert fixture["import_fixture_status"] == "OPERATOR_MANUAL_SOURCE_PACK_REQUIRED"
    assert fixture["runtime_truth"] is False
    assert fixture["real_source_pack_imported"] is False
    assert fixture["source_entries"] == []
    assert fixture["allowed_for_publication"] is False
    assert fixture["public_postable"] is False
    assert fixture["dispatch_allowed_now"] is False


def test_coordinator_execution(tmp_path):
    out_dir = tmp_path / "V6_REAL_SOURCE_PACK_MANUAL_IMPORT_SCHEMA"
    schema_mod.main(["--output-dir", str(out_dir)])

    expected = [
        "real_source_pack_manual_import_schema.json",
        "real_source_pack_manual_import_blank_fixture.json",
        "real_source_pack_hash_review_packet.json",
        "real_source_pack_redaction_policy.json",
        "real_source_pack_manual_import_validation_report.json",
        "real_source_pack_manual_import_blocker_report.md",
        "real_source_pack_manual_import_runbook.md",
        "implementation_report.md",
        "next_task_pointer.md"
    ]

    for name in expected:
        assert (out_dir / name).exists()

    # Confirm zero leak of jim's signature or urls in reports
    for name in expected:
        content = (out_dir / name).read_text(encoding="utf-8")
        assert "operator_jim_sig" not in content
        assert "federalreserve.gov" not in content
        assert "test.treasury.gov" not in content
        assert "e3b0c442" not in content
