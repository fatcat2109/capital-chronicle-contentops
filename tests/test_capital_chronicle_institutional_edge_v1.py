from __future__ import annotations

from copy import deepcopy

import pytest

from live_contentops.capital_chronicle_institutional_edge_v1 import (
    SCHEMA_VERSION,
    build_editorial_seo_package,
    build_institutional_edge_editorial_packet,
    validate_institutional_edge_article,
    validate_institutional_edge_packet,
)


def _evidence(*, sensitive: bool = False):
    proposition = (
        "The emergency agency notice confirmed disaster relief funding remains available."
        if sensitive
        else "The central bank notice confirmed that the policy corridor remains unchanged."
    )
    return {
        "status": "PASS",
        "evidence_documents": [
            {
                "document_id": "ev-1",
                "publisher": "Official Agency",
                "title": "Official policy notice",
                "canonical_content_text": proposition,
            }
        ],
        "claim_evidence_contract": {
            "supported_claims": [
                {"claim_id": "claim-1", "claim_text": proposition, "evidence_document_ids": ["ev-1"]}
            ]
        },
    }


def _article(packet, *, sensitive: bool = False):
    observed = (
        "The emergency agency notice confirmed disaster relief funding remains available."
        if sensitive
        else "The central bank notice confirmed that the policy corridor remains unchanged."
    )
    title = "Relief Funding Remains Available After the Emergency Notice" if sensitive else "The Policy Corridor Holds as the Central Bank Waits"
    dek = "The official notice preserves the current position while leaving the next decision dependent on new evidence."
    meta = "The official notice keeps the current position intact and identifies the evidence readers should watch before the next decision."
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
        "slug": "relief-funding-emergency-notice" if sensitive else "policy-corridor-central-bank-waits",
        "canonical_slug_candidate": "relief-funding-emergency-notice" if sensitive else "policy-corridor-central-bank-waits",
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
        "seo_primary_keyword": "policy corridor" if not sensitive else "relief funding",
        "institutional_edge_editorial_packet_sha256": packet["editorial_packet_sha256"],
    }


@pytest.mark.parametrize(
    ("mode", "sensitive"),
    [
        ("BREAKING_BRIEF", True),
        ("DATA_RELEASE", False),
        ("POLICY_DECISION", False),
        ("STANDARD_ANALYSIS", False),
        ("MARKET_MOVE", False),
        ("EXPLAINER", False),
        ("DEEP_ANALYSIS", False),
    ],
)
def test_six_story_classes_and_deep_mode_pass_the_same_hash_bound_contract(mode, sensitive):
    evidence = _evidence(sensitive=sensitive)
    packet = build_institutional_edge_editorial_packet(
        article_mode=mode,
        accepted_evidence_packet=evidence,
    )
    result = validate_institutional_edge_article(
        _article(packet, sensitive=sensitive),
        editorial_packet=packet,
        accepted_evidence_packet=evidence,
    )

    assert packet["schema_version"] == SCHEMA_VERSION
    assert validate_institutional_edge_packet(packet) == []
    assert result["classification"] == "PASS", result["blockers"]
    assert result["ordinary_semantic_review_calls"] == 0
    assert result["factual_authority"] is False
    assert result["numeric_authority"] is False
    if sensitive:
        assert packet["humor"]["maximum_declared_dry_lines"] == 0


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (lambda row: row.update(substack_body_markdown=row["substack_body_markdown"] + "\n\nThe evidence packet passed semantic review."), "internal_system_language_leakage"),
        (lambda row: row.update(search_title="Latest Update: Everything You Need to Know"), "boilerplate_search_title"),
        (lambda row: row.update(social_hook="A secret currency rupture guarantees an immediate crisis."), "social_hook_introduces_new_claim"),
        (lambda row: row["structured_data_packet"].update(headline="A different article"), "structured_data_headline_mismatch"),
        (lambda row: row.update(humor_lines=["Markets chose chaos, lol."], substack_body_markdown=row["substack_body_markdown"] + "\n\nMarkets chose chaos, lol."), "prohibited_informality"),
        (lambda row: row.update(substack_body_markdown=row["substack_body_markdown"] + "\n\nThe notice caused a global selloff."), "unsupported_causality"),
        (lambda row: row.update(meta_description="The notice guarantees a policy reversal."), "seo_or_social_claim_strengthening:meta_description"),
        (lambda row: row.update(substack_body_markdown=row["substack_body_markdown"] + '\n\nAn official said “rates will fall tomorrow.”'), "fake_or_unbound_quote_presentation"),
        (lambda row: row.update(substack_body_markdown=row["substack_body_markdown"] + "\n\nThe program added $5 billion."), "numeric_source_binding_violation"),
        (lambda row: row.update(canonical_editorial_headline="Currency Markets Abandon the Old Regime", title="Currency Markets Abandon the Old Regime"), "headline_body_proposition_mismatch"),
        (lambda row: row.update(canonical_editorial_headline="A Shocking Policy Apocalypse", title="A Shocking Policy Apocalypse"), "unsupported_sensational_headline"),
        (lambda row: row["epistemic_claims"].append({"text": "The next decision is predetermined.", "layer": "CAPITAL_CHRONICLE_ANALYSIS", "public_treatment": "DIRECT_SOURCE_FACT", "source_ids": ["ev-1"]}) or row.update(substack_body_markdown=row["substack_body_markdown"] + "\n\nThe next decision is predetermined."), "capital_chronicle_analysis_presented_as_source_fact"),
        (lambda row: row.update(seo_primary_keyword="policy corridor", substack_body_markdown=row["substack_body_markdown"] + "\n\n" + "policy corridor " * 18), "keyword_stuffing"),
        (lambda row: row.update(substack_body_markdown=row["substack_body_markdown"] + "\n\n" + row["substack_body_markdown"].split("\n\n")[0]), "duplicated_conclusion"),
    ],
)
def test_deterministic_protections_reject_explicit_integrity_failures(mutation, expected):
    evidence = _evidence()
    packet = build_institutional_edge_editorial_packet(
        article_mode="STANDARD_ANALYSIS",
        accepted_evidence_packet=evidence,
    )
    article = deepcopy(_article(packet))
    mutation(article)

    result = validate_institutional_edge_article(
        article,
        editorial_packet=packet,
        accepted_evidence_packet=evidence,
    )

    assert result["classification"] == "BLOCKED"
    assert expected in result["blockers"]


def test_editorial_seo_package_is_deterministic_and_zero_authority():
    evidence = _evidence()
    packet = build_institutional_edge_editorial_packet(
        article_mode="POLICY_DECISION", accepted_evidence_packet=evidence
    )
    article = _article(packet)

    first = build_editorial_seo_package(article)
    second = build_editorial_seo_package(deepcopy(article))

    assert first == second
    assert first["editorial_seo_package_sha256"]
    assert first["publication_authority"] is False
    assert first["public_write_authority"] is False
    assert first["search_learning_status"] == "HOLD_WITHOUT_SEARCH_SPECIFIC_EVIDENCE"


def test_superseded_kushner_future_state_cannot_pass_any_reader_facing_surface():
    evidence = _evidence()
    evidence["latest_event_state_closure"] = {
        "status": "PASS",
        "latest_supported_state": "OCCURRED_OR_OUTCOME_REPORTED",
        "target_terms": ["netanyahu", "gaza"],
        "supporting_document_ids": ["ev-1"],
        "model_assertion_grants_event_state_authority": False,
    }
    packet = build_institutional_edge_editorial_packet(
        article_mode="BREAKING_BRIEF", accepted_evidence_packet=evidence
    )
    article = _article(packet)
    stale = "Kushner was scheduled to meet Netanyahu afterward regarding Gaza."
    article["substack_body_markdown"] += "\n\n" + stale
    article["secondary_reader_questions"] = [
        "What should readers watch after the planned Netanyahu talks on Gaza?"
    ]
    article["structured_data_packet"]["description"] = (
        "Kushner met Hamas ahead of scheduled Netanyahu talks on Gaza."
    )
    article["meta_description"] = article["structured_data_packet"]["description"]

    result = validate_institutional_edge_article(
        article,
        editorial_packet=packet,
        accepted_evidence_packet=evidence,
    )

    assert result["classification"] == "BLOCKED"
    assert "superseded_forward_event_state_in_public_copy" in result["blockers"]
