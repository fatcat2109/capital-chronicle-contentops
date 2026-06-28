"""Test canonical article draft gate logic."""
from __future__ import annotations

from live_contentops import canonical_article_draft_gate_v6 as gate


def test_gate_blocked_default():
    pack = {
        "verified_source_pack_status": "MISSING_REQUIRED_SOURCE_VERIFICATION",
        "source_pack_complete": False,
        "source_entries": [
            {"source_requirement_id": "req_1", "verification_status": "missing"}
        ]
    }
    reqs = [{"research_requirement_id": "req_1"}]
    claims = [{"claim_id": "c1", "source_requirement_refs": ["req_1"]}]

    report, blockers = gate.evaluate_draft_gate(pack, reqs, claims)

    assert report["gate_status"] == "BLOCKED_MISSING_VERIFIED_SOURCE_PACK"
    assert "verified_source_pack_missing" in blockers
    assert "source_verification_required" in blockers


def test_gate_passed_with_complete_pack():
    pack = {
        "verified_source_pack_status": "COMPLETE",
        "source_pack_complete": True,
        "source_entries": [
            {"source_requirement_id": "req_1", "verification_status": "verified"}
        ]
    }
    reqs = [{"research_requirement_id": "req_1"}]
    claims = [{"claim_id": "c1", "source_requirement_refs": ["req_1"]}]

    report, blockers = gate.evaluate_draft_gate(pack, reqs, claims)

    assert report["gate_status"] == "PASSED"
    assert "verified_source_pack_missing" not in blockers
    assert "source_verification_required" not in blockers
