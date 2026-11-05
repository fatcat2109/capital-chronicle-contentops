from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

import pytest

from live_contentops import multi_story_platform_native_operator_packages_v1 as packages
from live_contentops.payload_preview_hash_v6 import compute_payload_hash


EVIDENCE_DIR = Path(
    "docs/automation/"
    "CONTENTOPS_FAST_SHIP_BIND_THREE_V3_PACKETS_TO_CANONICAL_EDITORIAL_AND_OPERATOR_PACKAGES_V1"
)
UPSTREAM_AUTHORITY = Path(
    "A:/Capital Chronicle/Headline Raw data local json/"
    "capital-chronicle-ingestion-multi-story-authority-v1/"
    "docs/research/publication_evidence/current/"
    "CapitalChronicleMultiStoryScopedReportingAuthorityBatchV1.json"
)


def _load(name: str):
    return json.loads((EVIDENCE_DIR / name).read_text(encoding="utf-8"))


def _authority():
    return json.loads(UPSTREAM_AUTHORITY.read_text(encoding="utf-8"))


def test_canonical_editorial_outcomes_bind_articles_claims_roles_and_holds():
    packet = _load("canonical_editorial_outcomes.json")
    assert packet["outcome_count"] == 3
    assert packet["story_ids"] == list(packages.EXPECTED_STORY_IDS)
    for outcome in packet["outcomes"]:
        assert outcome["canonical_article_id"].startswith("cc-canonical-draft-")
        assert outcome["canonical_article_hash"] == packages._logical_hash(
            outcome["canonical_article"]
        )
        assert outcome["article_used_approved_claim_ids"] == list(
            packages.AUTHORIZED_CLAIMS[outcome["story_id"]]
        )
        assert outcome["canonical_article"]["claim_ids_used"] == outcome[
            "article_used_approved_claim_ids"
        ]
        assert len(outcome["role_outcomes"]) == 8
        assert [row["role"] for row in outcome["role_outcomes"]] == [
            "assignment_editor",
            "evidence_planner",
            "reporter_writer",
            "quantitative_editor",
            "visual_editor",
            "copy_editor",
            "platform_editor",
            "adversarial_final_reviewer",
        ]
        assert outcome["editorial_review_hash"] == packages._logical_hash(
            outcome["editorial_review"]
        )
        assert outcome["editorial_state"] == (
            "PASS" if not outcome["unresolved_blockers"] else "HOLD"
        )
        unhashed = dict(outcome)
        observed = unhashed.pop("outcome_hash")
        assert packages._logical_hash(unhashed) == observed


def test_superseding_operator_packages_are_unsigned_pending_and_fully_bound():
    packet = _load("superseding_unsigned_operator_packages.json")
    outcomes = {
        row["story_id"]: row
        for row in _load("canonical_editorial_outcomes.json")["outcomes"]
    }
    assert packet["package_count"] == 3
    assert packet["state"] == "PENDING_OPERATOR_DECISION"
    for package in packet["packages"]:
        outcome = outcomes[package["story_id"]]
        assert package["state"] == "PENDING_OPERATOR_DECISION"
        assert package["signature"] is None
        assert package["operator_identity"] is None
        assert package["selected_decision"] is None
        assert package["operator_approval_captured"] is False
        assert package["publication_authority"] is False
        assert package["dispatch_authority"] is False
        assert package["public_write_authority"] is False
        assert package["authority_binding"]["exact_git_receipt"] == packages._expected_authority_receipt()
        binding = package["editorial_binding"]
        assert binding["v3_packet_id"] == outcome["v3_packet_id"]
        assert binding["v3_packet_logical_hash"] == outcome["v3_packet_logical_hash"]
        assert binding["canonical_article_id"] == outcome["canonical_article_id"]
        assert binding["canonical_article_hash"] == outcome["canonical_article_hash"]
        assert binding["article_used_approved_claim_ids"] == outcome["article_used_approved_claim_ids"]
        assert binding["editorial_review_hash"] == outcome["editorial_review_hash"]
        assert binding["freshness_disposition"] == outcome["freshness_disposition"]
        assert binding["visual_disposition"] == outcome["visual_disposition"]
        assert binding["final_adversarial_review_disposition"] == outcome["final_adversarial_review_disposition"]
        assert binding["unresolved_blockers"] == outcome["unresolved_blockers"]
        assert len(package["variant_payload_hashes"]) == 6
        unhashed = dict(package)
        observed = unhashed.pop("package_hash")
        assert packages._logical_hash(unhashed) == observed


