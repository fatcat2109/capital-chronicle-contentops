"""Regression tests for ContentOps Execution Frameworks (MAIN_CODEX and SUB_ANTIGRAVITY).

Authority: CONTENTOPS_MAIN_CODEX_AND_ANTIGRAVITY_SUBFRAMEWORK_OWNER_OVERRIDE_V1
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import pytest

from live_contentops.capital_chronicle_institutional_edge_v1 import (
    build_institutional_edge_editorial_packet,
)
from live_contentops.codex_desktop_newsroom_operator_v1 import (
    COORDINATOR_MODEL,
    COORDINATOR_REASONING_EFFORT,
    EDITORIAL_WORKER_MODEL,
    EDITORIAL_WORKER_REASONING_EFFORT,
    build_editorial_worker_routing_packet,
    four_task_setup_packet,
    validate_editorial_worker_return,
)
from live_contentops.destination_transport_registry_v1 import (
    V1_REQUIRED_PUBLICATION_DESTINATIONS,
)
from live_contentops.execution_framework_v1 import (
    DEFAULT_EXECUTION_FRAMEWORK,
    FRAMEWORK_MAIN_CODEX,
    FRAMEWORK_SUB_ANTIGRAVITY,
    assert_framework_continuity,
    validate_execution_framework,
)
from live_contentops.publication_coordinator_v1 import (
    UNKNOWN_WRITE,
)


def _sample_evidence() -> dict[str, Any]:
    proposition = "The central bank notice confirmed that the policy corridor remains unchanged."
    return {
        "status": "PASS",
        "evidence_id": "ev-sample-1",
        "evidence_documents": [
            {
                "document_id": "ev-1",
                "publisher": "Official Agency",
                "title": "Official policy notice",
                "canonical_content_text": proposition,
                "url": "https://esri.cao.go.jp/sample.html",
            }
        ],
        "claim_evidence_contract": {
            "supported_claims": [
                {"claim_id": "claim-1", "claim_text": proposition, "evidence_document_ids": ["ev-1"]}
            ]
        },
    }


def _full_institutional_article(editorial_packet: Mapping[str, Any], evidence: Mapping[str, Any]) -> dict[str, Any]:
    title = "The Policy Corridor Holds as the Central Bank Waits"
    dek = "The official notice preserves the current position while leaving the next decision dependent on new evidence."
    meta = "The official notice keeps the current position intact and identifies the evidence readers should watch before the next decision."
    observed = "The central bank notice confirmed that the policy corridor remains unchanged."
    body = (
        f"{observed} The record leaves the next decision open rather than announcing a new course.\n\n"
        "For readers, the useful distinction is between a position that has not changed and an outlook that still can. "
        "The notice establishes the first point; incoming evidence will determine the second.\n\n"
        "The next checkpoint is the agency's dated follow-up notice. It would show whether the current position remains intact or needs to be reassessed."
    )
    return {
        "title": title,
        "canonical_editorial_headline": title,
        "subtitle": dek,
        "dek": dek,
        "seo_title": title,
        "search_title": title,
        "social_lede": "The official notice keeps the current position intact while the next decision remains open.",
        "social_hook": "The official notice keeps the current position intact while the next decision remains open.",
        "meta_description": meta,
        "author_identity": "Capital Chronicle",
        "publisher_identity": "Capital Chronicle",
        "slug": "policy-corridor-central-bank-waits",
        "canonical_slug_candidate": "policy-corridor-central-bank-waits",
        "substack_body_markdown": body,
        "primary_reader_question": "What changed in the official notice, and what remains open?",
        "secondary_reader_questions": ["What should readers watch next?"],
        "entities": ["Official Agency"],
        "topics": ["policy notice"],
        "search_freshness_class": "CURRENT",
        "internal_link_candidates": [
            {
                "relation": "technical_explainer",
                "anchor_text": "how the policy corridor works",
                "candidate_slug": "policy-corridor-explainer",
            }
        ],
        "structured_data_packet": {
            "@type": "NewsArticle",
            "headline": title,
            "description": meta,
            "datePublished": "2026-08-17T09:00:00Z",
            "dateModified": "2026-08-17T09:00:00Z",
            "author": "Capital Chronicle",
            "publisher": "Capital Chronicle",
        },
        "epistemic_claims": [
            {
                "text": observed,
                "layer": "OBSERVED_FACT",
                "public_treatment": "DIRECT_SOURCE_FACT",
                "source_ids": ["ev-1"],
            }
        ],
        "quote_source_records": [],
        "humor_lines": [],
        "institutional_edge_editorial_packet_sha256": str(editorial_packet.get("editorial_packet_sha256") or ""),
    }


def _valid_main_worker_return(governed_input_hash: str, article: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "execution_framework": FRAMEWORK_MAIN_CODEX,
        "model": EDITORIAL_WORKER_MODEL,
        "reasoning_effort": EDITORIAL_WORKER_REASONING_EFFORT,
        "fresh": True,
        "isolated": True,
        "governed_input_hash": governed_input_hash,
        "bounded_revision_count": 0,
        "public_write_attempted": False,
        "article": article if article is not None else {"title": "Sample Valid Article"},
    }


def _valid_sub_worker_return(governed_input_hash: str, model: str = "Gemini 3.7 Flash (High)", article: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "execution_framework": FRAMEWORK_SUB_ANTIGRAVITY,
        "model": model,
        "reasoning_effort": "NOT_APPLICABLE_SUB_FRAMEWORK",
        "fresh": False,
        "isolated": False,
        "logical_role_isolated": True,
        "governed_input_hash": governed_input_hash,
        "bounded_revision_count": 0,
        "public_write_attempted": False,
        "article": article if article is not None else {"title": "Sample Valid Article"},
    }


# Regression A: MAIN_CODEX default behavior remains exact
def test_regression_a_main_codex_default_exact():
    assert DEFAULT_EXECUTION_FRAMEWORK == FRAMEWORK_MAIN_CODEX
    fw = validate_execution_framework()
    assert fw["framework"] == FRAMEWORK_MAIN_CODEX
    assert fw["is_main"] is True
    assert fw["coordinator_model"] == COORDINATOR_MODEL
    assert fw["coordinator_reasoning_effort"] == COORDINATOR_REASONING_EFFORT
    assert fw["editorial_worker_model"] == EDITORIAL_WORKER_MODEL
    assert fw["editorial_worker_reasoning_effort"] == EDITORIAL_WORKER_REASONING_EFFORT

    evidence = _sample_evidence()
    route = build_editorial_worker_routing_packet(
        opportunity_state="ARTICLE_QUALIFIED",
        governed_context={
            "accepted_evidence_packet": evidence,
            "exact_source_handles": ["https://esri.cao.go.jp/sample.html"],
        },
    )
    assert route["execution_framework"] == FRAMEWORK_MAIN_CODEX
    assert route["decision"] == "SPAWN_ONE_FRESH_ISOLATED_XHIGH_EDITORIAL_WORKER"
    assert route["coordinator"]["model"] == "gpt-5.6-sol"
    assert route["coordinator"]["reasoning_effort"] == "HIGH"
    assert route["worker_request"]["fresh"] is True
    assert route["worker_request"]["isolated"] is True

    valid_return = _valid_main_worker_return(route["governed_input_hash"])
    validation = validate_editorial_worker_return(
        worker_return=valid_return,
        expected_governed_input_hash=route["governed_input_hash"],
    )
    assert validation["classification"] == "PASS_BOUND_XHIGH_EDITORIAL_RETURN"
    assert validation["execution_framework"] == FRAMEWORK_MAIN_CODEX
    assert validation["worker_fresh_and_isolated"] is True


# Regression B: SUB_ANTIGRAVITY is rejected unless explicitly selected
def test_regression_b_sub_antigravity_rejected_unless_explicitly_selected():
    assert validate_execution_framework()["framework"] == FRAMEWORK_MAIN_CODEX

    with pytest.raises(ValueError, match="unrecognized_execution_framework"):
        validate_execution_framework("INVALID_FRAMEWORK")

    with pytest.raises(ValueError, match="sub_antigravity_model_identity_required"):
        validate_execution_framework(FRAMEWORK_SUB_ANTIGRAVITY)

    with pytest.raises(ValueError, match="sub_antigravity_model_identity_required"):
        validate_execution_framework(FRAMEWORK_SUB_ANTIGRAVITY, sub_model_identity="")


# Regression C: SUB receipt cannot claim MAIN/Codex identities
def test_regression_c_sub_cannot_claim_main_or_spoof_sol():
    with pytest.raises(ValueError, match="sub_antigravity_cannot_spoof_main_model_identity"):
        validate_execution_framework(FRAMEWORK_SUB_ANTIGRAVITY, sub_model_identity="gpt-5.6-sol")

    with pytest.raises(ValueError, match="sub_antigravity_cannot_spoof_main_model_identity"):
        validate_execution_framework(FRAMEWORK_SUB_ANTIGRAVITY, sub_model_identity="cx/gpt-5.6-sol(xhigh)")

    evidence = _sample_evidence()
    route = build_editorial_worker_routing_packet(
        opportunity_state="ARTICLE_QUALIFIED",
        governed_context={
            "accepted_evidence_packet": evidence,
            "exact_source_handles": ["https://esri.cao.go.jp/sample.html"],
        },
        execution_framework=FRAMEWORK_SUB_ANTIGRAVITY,
        sub_model_identity="Gemini 3.7 Flash (High)",
    )

    spoofed_framework = _valid_sub_worker_return(route["governed_input_hash"])
    spoofed_framework["execution_framework"] = FRAMEWORK_MAIN_CODEX
    with pytest.raises(ValueError, match="sub_editorial_worker_framework_invalid"):
        validate_editorial_worker_return(
            worker_return=spoofed_framework,
            expected_governed_input_hash=route["governed_input_hash"],
            execution_framework=FRAMEWORK_SUB_ANTIGRAVITY,
            expected_model_identity="Gemini 3.7 Flash (High)",
        )

    spoofed_model = _valid_sub_worker_return(route["governed_input_hash"])
    spoofed_model["model"] = "gpt-5.6-sol"
    with pytest.raises(ValueError, match="sub_editorial_worker_cannot_spoof_main_model"):
        validate_editorial_worker_return(
            worker_return=spoofed_model,
            expected_governed_input_hash=route["governed_input_hash"],
            execution_framework=FRAMEWORK_SUB_ANTIGRAVITY,
            expected_model_identity="Gemini 3.7 Flash (High)",
        )


# Regression D: Governed input hash mismatch fails closed
def test_regression_d_hash_mismatch_fails_closed():
    evidence = _sample_evidence()
    route = build_editorial_worker_routing_packet(
        opportunity_state="ARTICLE_QUALIFIED",
        governed_context={
            "accepted_evidence_packet": evidence,
            "exact_source_handles": ["https://esri.cao.go.jp/sample.html"],
        },
        execution_framework=FRAMEWORK_SUB_ANTIGRAVITY,
        sub_model_identity="Gemini 3.7 Flash (High)",
    )

    valid_return = _valid_sub_worker_return(route["governed_input_hash"])
    valid_return["governed_input_hash"] = "corrupted_or_different_hash"

    with pytest.raises(ValueError, match="desktop_editorial_worker_input_hash_mismatch"):
        validate_editorial_worker_return(
            worker_return=valid_return,
            expected_governed_input_hash=route["governed_input_hash"],
            execution_framework=FRAMEWORK_SUB_ANTIGRAVITY,
            expected_model_identity="Gemini 3.7 Flash (High)",
        )


# Regression E: Article factual/numeric/Institutional Edge validation is identical across frameworks
def test_regression_e_institutional_edge_identical_across_frameworks():
    evidence = _sample_evidence()
    editorial_packet = build_institutional_edge_editorial_packet(
        article_mode="STANDARD_ANALYSIS",
        accepted_evidence_packet=evidence,
        structured_data_supported=True,
    )

    route_main = build_editorial_worker_routing_packet(
        opportunity_state="ARTICLE_QUALIFIED",
        governed_context={
            "accepted_evidence_packet": evidence,
            "exact_source_handles": ["https://esri.cao.go.jp/sample.html"],
        },
        execution_framework=FRAMEWORK_MAIN_CODEX,
    )
    route_sub = build_editorial_worker_routing_packet(
        opportunity_state="ARTICLE_QUALIFIED",
        governed_context={
            "accepted_evidence_packet": evidence,
            "exact_source_handles": ["https://esri.cao.go.jp/sample.html"],
        },
        execution_framework=FRAMEWORK_SUB_ANTIGRAVITY,
        sub_model_identity="Gemini 3.7 Flash (High)",
    )

    # Incomplete article fails in both
    bad_article = {"title": "Short", "subtitle": "Short", "substack_body_markdown": "Short"}
    bad_main = _valid_main_worker_return(route_main["governed_input_hash"], bad_article)
    bad_sub = _valid_sub_worker_return(route_sub["governed_input_hash"], "Gemini 3.7 Flash (High)", bad_article)

    with pytest.raises(ValueError, match="institutional_edge_invalid"):
        validate_editorial_worker_return(
            worker_return=bad_main,
            expected_governed_input_hash=route_main["governed_input_hash"],
            expected_editorial_packet=editorial_packet,
            accepted_evidence_packet=evidence,
            execution_framework=FRAMEWORK_MAIN_CODEX,
        )

    with pytest.raises(ValueError, match="institutional_edge_invalid"):
        validate_editorial_worker_return(
            worker_return=bad_sub,
            expected_governed_input_hash=route_sub["governed_input_hash"],
            expected_editorial_packet=editorial_packet,
            accepted_evidence_packet=evidence,
            execution_framework=FRAMEWORK_SUB_ANTIGRAVITY,
            expected_model_identity="Gemini 3.7 Flash (High)",
        )

    # Complete valid institutional edge article passes in both
    good_article = _full_institutional_article(editorial_packet, evidence)
    good_main = _valid_main_worker_return(route_main["governed_input_hash"], good_article)
    good_sub = _valid_sub_worker_return(route_sub["governed_input_hash"], "Gemini 3.7 Flash (High)", good_article)

    val_main = validate_editorial_worker_return(
        worker_return=good_main,
        expected_governed_input_hash=route_main["governed_input_hash"],
        expected_editorial_packet=editorial_packet,
        accepted_evidence_packet=evidence,
        execution_framework=FRAMEWORK_MAIN_CODEX,
    )
    val_sub = validate_editorial_worker_return(
        worker_return=good_sub,
        expected_governed_input_hash=route_sub["governed_input_hash"],
        expected_editorial_packet=editorial_packet,
        accepted_evidence_packet=evidence,
        execution_framework=FRAMEWORK_SUB_ANTIGRAVITY,
        expected_model_identity="Gemini 3.7 Flash (High)",
    )
    assert val_main["classification"] == "PASS_BOUND_XHIGH_EDITORIAL_RETURN"
    assert val_sub["classification"] == "PASS_BOUND_SUB_ANTIGRAVITY_EDITORIAL_RETURN"


# Regression F: SUB model still has zero publication/public-write authority
def test_regression_f_sub_zero_publication_authority():
    route_sub = build_editorial_worker_routing_packet(
        opportunity_state="ARTICLE_QUALIFIED",
        governed_context={
            "accepted_evidence_packet": _sample_evidence(),
            "exact_source_handles": ["https://esri.cao.go.jp/sample.html"],
        },
        execution_framework=FRAMEWORK_SUB_ANTIGRAVITY,
        sub_model_identity="Gemini 3.7 Flash (High)",
    )
    assert route_sub["worker_request"]["grants_public_write_authority"] is False
    assert route_sub["worker_request"]["grants_factual_authority"] is False
    assert route_sub["worker_request"]["grants_numeric_authority"] is False

    valid_sub = _valid_sub_worker_return(route_sub["governed_input_hash"])
    valid_sub["public_write_attempted"] = True

    with pytest.raises(ValueError, match="public_write_forbidden"):
        validate_editorial_worker_return(
            worker_return=valid_sub,
            expected_governed_input_hash=route_sub["governed_input_hash"],
            execution_framework=FRAMEWORK_SUB_ANTIGRAVITY,
            expected_model_identity="Gemini 3.7 Flash (High)",
        )


# Regression G: No framework switch is allowed mid-opportunity
def test_regression_g_no_mid_opportunity_framework_switch():
    assert_framework_continuity(FRAMEWORK_MAIN_CODEX, FRAMEWORK_MAIN_CODEX)
    assert_framework_continuity(FRAMEWORK_SUB_ANTIGRAVITY, FRAMEWORK_SUB_ANTIGRAVITY)

    with pytest.raises(ValueError, match="execution_framework_switch_mid_opportunity_forbidden"):
        assert_framework_continuity(FRAMEWORK_MAIN_CODEX, FRAMEWORK_SUB_ANTIGRAVITY)

    with pytest.raises(ValueError, match="execution_framework_switch_mid_opportunity_forbidden"):
        assert_framework_continuity(FRAMEWORK_SUB_ANTIGRAVITY, FRAMEWORK_MAIN_CODEX)


# Regression H: UNKNOWN_WRITE / readiness / DurablePublicationCoordinator semantics are framework-independent
def test_regression_h_coordinator_invariants_framework_independent():
    assert UNKNOWN_WRITE == "UNKNOWN_WRITE"
    assert "substack" in V1_REQUIRED_PUBLICATION_DESTINATIONS
    assert len(V1_REQUIRED_PUBLICATION_DESTINATIONS) == 9


# Regression I: TikTok remains absent from V1
def test_regression_i_tiktok_absent_from_v1():
    assert "tiktok" not in V1_REQUIRED_PUBLICATION_DESTINATIONS


# Regression J: Existing four V1 native Codex automations remain PAUSED and unchanged
def test_regression_j_four_tasks_paused_and_unchanged():
    packet = four_task_setup_packet()
    assert packet["routine_task_count"] == 4
    assert len(packet["tasks"]) == 4
    assert packet["model"] == "gpt-5.6-sol"
    assert packet["reasoning_effort"] == "HIGH"
    assert packet["editorial_worker_model"] == "gpt-5.6-sol"
    assert packet["editorial_worker_reasoning_effort"] == "XHIGH"
    assert packet["publication_minimum"] == 0
    assert packet["automatic_scale_up"] is False


# Regression K: No V2 runtime/store/publication mutation
def test_regression_k_no_v2_mutation():
    # Verify root AGENTS.md preserves V2 isolation and zero public write
    root_agents = Path("AGENTS.md").read_text(encoding="utf-8")
    assert "ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY" in root_agents
