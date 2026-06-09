"""Tests for the local platform official-docs verification pack (0081).

Advisory only; never grants runtime authority or live publishing.
"""

import json
import os

import live_contentops.platform_official_docs_verification as v

ROOT = os.path.join(os.path.dirname(__file__), "..")
FIX = os.path.join(ROOT, "fixtures", "platform_official_docs")


def _load(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_fix(name):
    return _load(os.path.join(FIX, name))


# --- schemas load -----------------------------------------------------------

def test_schemas_load():
    assert v.load_record_schema()["title"] == "PlatformOfficialDocsVerificationRecord"
    assert v.load_pack_schema()["title"] == "PlatformOfficialDocsVerificationPack"


# --- positive flows ---------------------------------------------------------

def test_valid_not_verified_pack():
    res = v.validate_pack_file(
        os.path.join(FIX, "valid_not_verified_pack.json")
    )
    assert res["valid"] is True
    assert set(res["platform_ids"]) == set(v.PLATFORMS)


def test_valid_partially_verified_pack():
    res = v.validate_pack_file(
        os.path.join(FIX, "valid_partially_verified_pack_with_operator_supplied_sources.json")
    )
    assert res["valid"] is True
    assert "telegram" in res["platform_ids"]


# --- negative flows (fail closed) -------------------------------------------

def test_invalid_live_enabled():
    rec = _load_fix("invalid_live_enabled.json")
    res = v.validate_record(rec)
    assert res["valid"] is False
    assert "live_posting_enabled_must_be_false" in res["errors"]


def test_invalid_network_accessed():
    rec = _load_fix("invalid_network_accessed.json")
    res = v.validate_record(rec)
    assert res["valid"] is False
    assert "network_accessed_by_repo_must_be_false" in res["errors"]


def test_invalid_docs_runtime_authority():
    rec = _load_fix("invalid_docs_runtime_authority_true.json")
    res = v.validate_record(rec)
    assert res["valid"] is False
    assert "docs_runtime_authority_must_be_false" in res["errors"]


def test_invalid_verified_without_sources():
    rec = _load_fix("invalid_verified_without_sources.json")
    res = v.validate_record(rec)
    assert res["valid"] is False
    assert "source_documents_required_when_verified" in res["errors"]


def test_missing_unknowns_when_not_verified():
    # If status is not_verified but unknowns list is empty, validation must fail.
    rec = {
        "platform_id": "telegram",
        "verification_status": "not_verified",
        "source_collection_method": "not_supplied",
        "source_documents": [],
        "unknowns": [],  # missing
        "live_gate_blockers": ["missing"],
        "docs_runtime_authority": False,
        "network_accessed_by_repo": False,
        "credential_accessed_by_repo": False,
        "live_posting_enabled": False
    }
    res = v.validate_record(rec)
    assert res["valid"] is False
    assert "unknowns_required_when_not_fully_verified" in res["errors"]
