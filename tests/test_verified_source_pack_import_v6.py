"""Test verified source pack import module."""
from __future__ import annotations

from live_contentops import verified_source_pack_import_v6 as importer


def test_import_template_and_blank_validations():
    tpl = importer.make_operator_source_pack_import_template()
    assert tpl["source_pack_import_status"] == "OPERATOR_SOURCE_PACK_REQUIRED"
    assert tpl["import_mode"] == "manual_local_file_deferred"
    assert len(tpl["source_entries"]) == 0

    report, blockers = importer.validate_imported_source_pack(tpl)
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "operator_source_pack_missing" in blockers
    assert "verified_source_pack_missing" in blockers
    assert "draft_generation_blocked" in blockers
    assert report["safety_checks"]["verified_fields_complete"] is False
