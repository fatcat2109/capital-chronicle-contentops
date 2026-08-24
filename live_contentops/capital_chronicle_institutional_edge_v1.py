"""Compact, hash-bound Capital Chronicle Institutional Edge editorial contract.

The committed owner documents remain the human authority.  This module projects only the
minimum machine-consumable contract needed at the existing fresh XHIGH writer boundary and
performs deterministic proposition/packaging checks after the writer returns.  It is not a
writer, router, factual authority, or publication gate.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "contentops.capital_chronicle_institutional_edge_editorial_packet.v1"
VALIDATION_SCHEMA_VERSION = "contentops.institutional_edge_editorial_validation.v1"
SEO_PACKAGE_SCHEMA_VERSION = "contentops.institutional_edge_seo_package.v1"

# Findings in this set never change the factual meaning of public copy.  They remain observable,
# but they are repair/warning concerns rather than article-terminal truth gates.  Any unknown code
# stays hard by default.
SOFT_REPRESENTATION_AND_METADATA_FINDINGS = frozenset(
    {
        "canonical_editorial_headline_title_mismatch",
        "dek_subtitle_mismatch",
        "search_title_seo_title_mismatch",
        "social_hook_social_lede_mismatch",
        "canonical_slug_alias_mismatch",
        "author_identity_representation_mismatch",
        "publisher_identity_representation_mismatch",
        "epistemic_claim_not_present_in_public_copy",
        "scenario_not_conditional",
        "structured_data_packet_missing",
        "structured_data_type_invalid",
        "structured_data_headline_mismatch",
        "structured_data_description_mismatch",
        "structured_data_dates_missing_or_unbound",
        "structured_data_author_identity_mismatch",
        "structured_data_publisher_identity_mismatch",
        "search_freshness_class_invalid",
        "primary_reader_question_invalid",
        "boilerplate_search_title",
        "internal_link_candidate_invalid",
        "internal_link_relation_invalid",
        "internal_link_anchor_not_descriptive",
    }
)


def classify_institutional_edge_findings(
    findings: Sequence[Any],
) -> dict[str, list[str]]:
    """Split truth/authority blockers from representation and metadata warnings."""
    hard: list[str] = []
    soft: list[str] = []
    for raw in findings:
        finding = str(raw or "").strip()
        if not finding:
            continue
        if finding in SOFT_REPRESENTATION_AND_METADATA_FINDINGS:
            soft.append(finding)
        else:
            hard.append(finding)
    return {
        "hard_blockers": list(dict.fromkeys(hard)),
        "soft_warnings": list(dict.fromkeys(soft)),
    }

_REPO_ROOT = Path(__file__).resolve().parents[1]
_AUTHORITY_PATHS = (
    "docs/editorial/CAPITAL_CHRONICLE_INSTITUTIONAL_EDGE_V1.md",
    "docs/editorial/CAPITAL_CHRONICLE_HUMOR_AND_INFORMALITY_POLICY_V1.md",
    "docs/editorial/CAPITAL_CHRONICLE_EDITORIAL_SEO_CONTRACT_V1.json",
)
_LAYERS = (
    "OBSERVED_FACT",
    "ATTRIBUTED_INTERPRETATION",
    "CAPITAL_CHRONICLE_ANALYSIS",
    "SCENARIO_OR_UNCERTAINTY",
)
_MODE_ALIASES = {
    "BREAKING": "BREAKING_BRIEF",
    "BREAKING_BRIEF": "BREAKING_BRIEF",
    "FOLLOW_UP_UPDATE": "FOLLOW_UP_UPDATE",
    "STANDARD_NEWS_ANALYSIS": "STANDARD_ANALYSIS",
    "CAPITAL_CHRONICLE_VIEW": "HOUSE_VIEW",
    "WHAT_THE_MARKET_IS_MISSING": "HOUSE_VIEW",
    "EVERGREEN_EXPLAINER": "EXPLAINER",
    "DATA_OR_DOCUMENT_LENS": "DOCUMENT_LENS",
    "WEEK_AHEAD_OR_WATCH": "WEEK_AHEAD_WATCH",
    "DATA": "DATA_RELEASE",
    "DATA_RELEASE": "DATA_RELEASE",
    "POLICY": "POLICY_DECISION",
    "POLICY_DECISION": "POLICY_DECISION",
    "STRAIGHT_NEWS": "STANDARD_ANALYSIS",
    "ANALYSIS": "STANDARD_ANALYSIS",
    "STANDARD": "STANDARD_ANALYSIS",
    "STANDARD_ANALYSIS": "STANDARD_ANALYSIS",
    "MARKET": "MARKET_MOVE",
    "MARKET_MOVE": "MARKET_MOVE",
    "EXPLAINER": "EXPLAINER",
    "DEEP": "DEEP_ANALYSIS",
    "DEEP_ANALYSIS": "DEEP_ANALYSIS",
    "STRUCTURAL_ANALYSIS": "DEEP_ANALYSIS",
}
_MODE_EXPECTATIONS = {
    "BREAKING_BRIEF": ("fact_first", "narrow_interpretation", "explicit_uncertainty"),
    "FOLLOW_UP_UPDATE": (
        "material_delta_first",
        "prior_and_current_state_source_bound",
        "bounded_breaking_update_scope",
        "no_recycled_or_invented_update",
    ),
    "DATA_RELEASE": ("result_and_supported_comparison", "preserve_measurement_distinctions", "no_one_print_regime_claim"),
    "POLICY_DECISION": ("decision_first", "official_language_or_vote", "transmission_and_uncertainty"),
    "STANDARD_ANALYSIS": ("early_thesis", "mechanism", "counter_case_and_watch_condition"),
    "HOUSE_VIEW": (
        "strong_thesis_early",
        "factual_premises_source_bound",
        "exact_supplied_source_markers_for_factual_copy",
        "explicit_branded_qualitative_inference_using_capital_chronicle_view_interpretation_or_inference",
        "no_unbound_or_fabricated_quotes",
        "no_unsupported_causal_claim",
        "material_counter_case_or_uncertainty_when_appropriate",
        "no_proprietary_probability_forecast_scenario_regime_valuation_base_case_or_decision_truth_without_exact_publication_authorized_cc_authority",
    ),
    "MARKET_MOVE": ("move_is_observation", "causality_requires_support", "separate_flow_from_fundamentals"),
    "EXPLAINER": ("plain_english_first", "institutional_depth_second", "define_specialist_terms_once"),
    "DOCUMENT_LENS": (
        "preserve_source_and_document_distinction",
        "separate_document_fact_from_supported_implication",
        "no_unsupported_implication",
    ),
    "WEEK_AHEAD_WATCH": (
        "distinguish_scheduled_facts_from_future_outcomes",
        "no_invented_pre_release_conclusions",
        "explicit_uncertainty_and_watch_conditions",
    ),
    "DEEP_ANALYSIS": ("institutional_mechanics", "countervailing_forces", "scenario_boundaries_and_exact_cc_authority"),
}
_HUMOR_CEILING = {
    "BREAKING_BRIEF": 0,
    "FOLLOW_UP_UPDATE": 0,
    "DATA_RELEASE": 1,
    "POLICY_DECISION": 0,
    "STANDARD_ANALYSIS": 1,
    "HOUSE_VIEW": 2,
    "MARKET_MOVE": 2,
    "EXPLAINER": 1,
    "DOCUMENT_LENS": 1,
    "WEEK_AHEAD_WATCH": 1,
    "DEEP_ANALYSIS": 2,
}
_INTERNAL_LANGUAGE = re.compile(
    r"\b(?:evidence packet|candidate pipeline|governed input|publication authority|hash binding|"
    r"semantic review|writer routing|xhigh worker|contentops runtime)\b",
    re.I,
)
_CAUSAL = re.compile(r"\b(?:caused|drove|triggered|led directly to|proves?|guarantees?)\b", re.I)
_SCENARIO_CONDITIONAL_OR_UNCERTAIN = re.compile(
    r"\b(?:if|unless|until|would|could|may|might|possible|potential|uncertain|unclear|unknown|"
    r"depends?\s+on|dependent\s+on|subject\s+to|contingent\s+on|but\s+not|"
    r"(?:does|do|did)\s+not\s+(?:specify|disclose|establish|show)|"
    r"remain(?:s|ed)?\s+(?:open|unknown|unclear|uncertain))\b",
    re.I,
)
_SOURCE_OMISSION_ASSERTION = re.compile(
    r"\b(?:report|source|filing|document|notice|announcement|evidence|record)\b"
    r"[^.!?]{0,120}\b(?:does|do|did|has|have|had)\s+not\s+"
    r"(?:specify|disclose|provide|state|identify|include|reveal)\b|"
    r"\b(?:amount|sum|valuation|value|investors?|geograph(?:y|ic)|locations?|scope|"
    r"timing|timeline|dates?|details?)\b[^.!?]{0,120}\b"
    r"(?:remain(?:s|ed)?\s+)?(?:undisclosed|unspecified|unknown|not\s+"
    r"(?:specified|disclosed|provided|stated|identified))\b|"
    r"\bno\s+(?:amount|sum|valuation|value|investors?|geograph(?:y|ic)|locations?|"
    r"scope|timing|timeline|dates?|details?)\b[^.!?]{0,80}\b"
    r"(?:provided|disclosed|specified|stated|identified)\b|"
    r"\bbut\s+not\s+(?:(?:the|their|its)\s+)?"
    r"(?:amount|scale|scope|footprint|timing|timeline|details?)\b",
    re.I,
)
_SENSATIONAL = re.compile(
    r"\b(?:shocking|apocalypse|apocalyptic|catastrophic collapse|you won.t believe|secret that|"
    r"guaranteed|destroys?|obliterates?)\b",
    re.I,
)
_PROHIBITED_INFORMALITY = re.compile(
    r"\b(?:lol|lmao|no cap|stonks|diamond hands|to the moon|ngl|rekt|cope harder)\b|[🚀💎🔥]{2,}",
    re.I,
)
_BOILERPLATE_SEARCH = re.compile(
    r"^(?:latest update|everything you need to know|what you need to know|breaking news|market update)(?:\b|:)",
    re.I,
)
_QUOTE = re.compile(r"[\"“]([^\"”]{8,})[\"”]")
_NUMBER = re.compile(
    r"(?<![A-Za-z])(?:[$€£]\s*\d[\d,]*(?:\.\d+)?|"
    r"\d[\d,]*(?:\.\d+)?%|\d[\d,]*(?:\.\d+)?\s*(?:bp|bps|billion|million|trillion))(?!\w)",
    re.I,
)
_STOPWORDS = frozenset(
    "a an and are as at be by for from has have how in into is it its of on or that the their this to was were what when where which who why will with".split()
)
_SENSITIVE = re.compile(
    r"\b(?:death|dead|killed|casualt(?:y|ies)|victim|war|famine|disaster|earthquake|flood|"
    r"allegation|accused|lawsuit|indictment|legal jeopardy|severe hardship)\b",
    re.I,
)
_ELIGIBLE_LINK_RELATIONS = frozenset(
    {
        "same_event_chain",
        "technical_explainer",
        "prior_data_release",
        "prior_capital_chronicle_analysis",
        "material_update_predecessor",
    }
)


def _logical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str).encode("utf-8")
    ).hexdigest()


def _authority_bindings() -> dict[str, str]:
    bindings: dict[str, str] = {}
    for relative in _AUTHORITY_PATHS:
        path = _REPO_ROOT / relative
        bindings[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return bindings


def _normalise_mode(value: Any) -> str:
    key = re.sub(r"[^A-Z0-9]+", "_", str(value or "").strip().upper()).strip("_")
    return _MODE_ALIASES.get(key, "STANDARD_ANALYSIS")


def _evidence_text(packet: Mapping[str, Any] | None) -> str:
    if not isinstance(packet, Mapping):
        return ""
    parts: list[str] = []
    for row in packet.get("evidence_documents") or []:
        if isinstance(row, Mapping):
            parts.extend(str(row.get(key) or "") for key in (
                "title", "publisher", "canonical_content_text", "source_identity"
            ))
    claim_contract = packet.get("claim_evidence_contract")
    if isinstance(claim_contract, Mapping):
        parts.extend(
            str(row.get("claim_text") or "")
            for row in claim_contract.get("supported_claims") or []
            if isinstance(row, Mapping)
        )
    minimum = packet.get("minimum_trustworthy_evidence_packet")
    if isinstance(minimum, Mapping):
        parts.append(str(minimum.get("core_factual_proposition") or ""))
    research = packet.get("grounded_research_packet")
    if isinstance(research, Mapping):
        parts.append(str(research.get("core_factual_proposition") or ""))
        for row in research.get("confirmed_facts") or []:
            if isinstance(row, Mapping):
                parts.append(str(row.get("factual_statement") or row.get("claim_text") or ""))
    return "\n".join(parts)


def build_institutional_edge_editorial_packet(
    *,
    article_mode: Any,
    accepted_evidence_packet: Mapping[str, Any] | None = None,
    structured_data_supported: bool = True,
) -> dict[str, Any]:
    """Project the committed authority into a compact deterministic writer packet."""
    mode = _normalise_mode(article_mode)
    evidence = _evidence_text(accepted_evidence_packet)
    sensitive = bool(_SENSITIVE.search(evidence))
    humor_ceiling = 0 if sensitive else _HUMOR_CEILING[mode]
    core = {
        "schema_version": SCHEMA_VERSION,
        "authority_date": "2026-08-17",
        "voice_id": "CAPITAL_CHRONICLE_INSTITUTIONAL_EDGE_V1",
        "authority_sha256": _authority_bindings(),
        "article_mode": mode,
        "mode_expectations": list(_MODE_EXPECTATIONS[mode]),
        "epistemic_layers": list(_LAYERS),
        "first_screen": {
            "approximate_word_window_not_quota": 120,
            "establish_when_supported": [
                "what_changed", "magnitude_or_comparison", "why_it_matters",
                "leading_mechanism", "principal_uncertainty",
            ],
        },
        "reader_value": [
            "strongest_evidence", "change_from_prior_state", "mechanism", "consequence",
            "uncertainty", "confirm_or_challenge", "watch_next",
        ],
        "headline_contract": {
            "canonical": "institutional_proposition_led",
            "search": "descriptive_query_aligned_same_proposition",
            "social": "compressed_same_or_narrower_proposition",
        },
        "humor": {
            "optional_never_quota": True,
            "sensitive_story_zero_humor": sensitive,
            "maximum_declared_dry_lines": humor_ceiling,
            "allowed_targets": ["market_contradiction", "model_assumption", "institutional_incentive", "balance_sheet_constraint"],
            "prohibited": ["victims_or_hardship", "forced_slang_or_meme", "ideological_dunk", "trading_call", "unsupported_premise"],
        },
        "seo": {
            "schema_version": "capital_chronicle_editorial_seo_contract_v1",
            "required_surfaces": [
                "canonical_editorial_headline", "dek", "article_body", "search_title", "social_hook",
                "meta_description", "canonical_slug_candidate", "primary_reader_question",
                "secondary_reader_questions", "entities", "topics", "search_freshness_class",
                "internal_link_candidates", "structured_data_packet_when_supported",
            ],
            "structured_data_supported": bool(structured_data_supported),
            "structured_data_types": ["Article", "NewsArticle"],
            "search_learning_status": "HOLD_WITHOUT_SEARCH_SPECIFIC_EVIDENCE",
        },
        "fixed_word_paragraph_heading_keyword_or_joke_quota": False,
        "additional_general_seo_writer": False,
        "additional_mandatory_semantic_review": False,
        "grants_factual_authority": False,
        "grants_numeric_authority": False,
        "grants_capital_chronicle_authority": False,
        "grants_permission_authority": False,
        "grants_publication_authority": False,
        "grants_public_write_authority": False,
        "packet_hash_semantics": "sha256(canonical_json(packet_without_editorial_packet_sha256))",
    }
    return {**core, "editorial_packet_sha256": _logical_hash(core)}


def validate_institutional_edge_packet(packet: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    if str(packet.get("schema_version") or "") != SCHEMA_VERSION:
        blockers.append("institutional_edge_packet_schema_invalid")
    core = dict(packet)
    supplied_hash = str(core.pop("editorial_packet_sha256", ""))
    if not supplied_hash or supplied_hash != _logical_hash(core):
        blockers.append("institutional_edge_packet_hash_invalid")
    if dict(packet.get("authority_sha256") or {}) != _authority_bindings():
        blockers.append("institutional_edge_packet_authority_binding_invalid")
    for key in (
        "grants_factual_authority", "grants_numeric_authority", "grants_capital_chronicle_authority",
        "grants_permission_authority", "grants_publication_authority", "grants_public_write_authority",
    ):
        if packet.get(key) is not False:
            blockers.append(f"institutional_edge_packet_must_deny:{key}")
    return blockers


def _normalise(value: Any) -> str:
    return " ".join(str(value or "").split())


def _tokens(value: Any) -> set[str]:
    return {
        token for token in re.findall(r"[a-z0-9][a-z0-9'-]+", _normalise(value).casefold())
        if len(token) > 2 and token not in _STOPWORDS
    }


def _paragraphs(body: str) -> list[str]:
    return [
        _normalise(re.sub(r"^#{1,6}\s+", "", block))
        for block in re.split(r"\n\s*\n", body)
        if _normalise(block) and not block.lstrip().startswith("[[VISUAL:")
    ]


def _evidence_ids(packet: Mapping[str, Any] | None) -> set[str]:
    if not isinstance(packet, Mapping):
        return set()
    return {
        str(row.get("document_id") or row.get("evidence_id") or row.get("source_id") or "")
        for row in packet.get("evidence_documents") or []
        if isinstance(row, Mapping)
    } - {""}


def _source_omission_assertions(public_copy: str) -> list[str]:
    return list(
        dict.fromkeys(
            assertion
            for assertion in (
                _normalise(value)
                for value in re.split(r"(?<=[.!?])\s+|\n+", str(public_copy or ""))
            )
            if assertion and _SOURCE_OMISSION_ASSERTION.search(assertion)
        )
    )


def _supported_source_omission_claims(
    packet: Mapping[str, Any] | None,
) -> list[str]:
    if not isinstance(packet, Mapping):
        return []
    contract = packet.get("claim_evidence_contract")
    if not isinstance(contract, Mapping):
        return []
    evidence_ids = _evidence_ids(packet)
    supported: list[str] = []
    for row in contract.get("supported_claims") or []:
        if not isinstance(row, Mapping):
            continue
        status = str(row.get("support_status") or "SUPPORTED").upper()
        if any(marker in status for marker in ("UNSUPPORTED", "OMITTED", "REJECTED", "BLOCKED")):
            continue
        source_ids = {
            str(value)
            for value in (
                row.get("evidence_document_ids") or row.get("source_ids") or []
            )
            if str(value)
        }
        claim = _normalise(
            row.get("claim_text") or row.get("text") or row.get("factual_statement")
        )
        if claim and source_ids and source_ids.issubset(evidence_ids):
            supported.append(claim)
    return list(dict.fromkeys(supported))


def build_editorial_seo_package(article: Mapping[str, Any]) -> dict[str, Any]:
    """Return the bounded editorial/SEO package embedded in all release preparation."""
    structured = article.get("structured_data_packet")
    core = {
        "schema_version": SEO_PACKAGE_SCHEMA_VERSION,
        "canonical_editorial_headline": _normalise(article.get("canonical_editorial_headline") or article.get("title")),
        "dek": _normalise(article.get("dek") or article.get("subtitle")),
        "search_title": _normalise(article.get("search_title") or article.get("seo_title")),
        "social_hook": _normalise(article.get("social_hook") or article.get("social_lede")),
        "meta_description": _normalise(article.get("meta_description")),
        "author_identity": _normalise(article.get("author_identity") or "Capital Chronicle"),
        "publisher_identity": _normalise(article.get("publisher_identity") or "Capital Chronicle"),
        "canonical_slug_candidate": _normalise(article.get("canonical_slug_candidate") or article.get("slug")),
        "primary_reader_question": _normalise(article.get("primary_reader_question")),
        "secondary_reader_questions": list(article.get("secondary_reader_questions") or []),
        "entities": list(article.get("entities") or []),
        "topics": list(article.get("topics") or []),
        "search_freshness_class": _normalise(article.get("search_freshness_class")),
        "internal_link_candidates": list(article.get("internal_link_candidates") or []),
        "structured_data_packet": dict(structured) if isinstance(structured, Mapping) else None,
        "institutional_edge_editorial_packet_sha256": _normalise(article.get("institutional_edge_editorial_packet_sha256")),
        "search_learning_status": "HOLD_WITHOUT_SEARCH_SPECIFIC_EVIDENCE",
        "publication_authority": False,
        "public_write_authority": False,
    }
    return {**core, "editorial_seo_package_sha256": _logical_hash(core)}


def validate_institutional_edge_article(
    article: Mapping[str, Any],
    *,
    editorial_packet: Mapping[str, Any],
    accepted_evidence_packet: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Apply explicit deterministic integrity checks; no subjective style score is produced."""
    blockers = validate_institutional_edge_packet(editorial_packet)
    expected_hash = str(editorial_packet.get("editorial_packet_sha256") or "")
    if str(article.get("institutional_edge_editorial_packet_sha256") or "") != expected_hash:
        blockers.append("institutional_edge_article_packet_binding_mismatch")

    package = build_editorial_seo_package(article)
    required_text = (
        "canonical_editorial_headline", "dek", "search_title", "social_hook", "meta_description",
        "canonical_slug_candidate", "primary_reader_question", "search_freshness_class",
        "author_identity", "publisher_identity",
    )
    for key in required_text:
        if not _normalise(package.get(key)):
            blockers.append(f"institutional_edge_required_surface_missing:{key}")
    body = str(article.get("substack_body_markdown") or article.get("article_body") or "")
    if not body.strip():
        blockers.append("institutional_edge_required_surface_missing:article_body")
    for key in ("secondary_reader_questions", "entities", "topics", "internal_link_candidates"):
        if not isinstance(article.get(key), Sequence) or isinstance(article.get(key), (str, bytes)):
            blockers.append(f"institutional_edge_surface_type_invalid:{key}")
    for key in ("entities", "topics"):
        if not any(_normalise(value) for value in article.get(key) or []):
            blockers.append(f"institutional_edge_required_surface_missing:{key}")
    if package["search_freshness_class"] not in {
        "BREAKING", "CURRENT", "UPDATE", "EVERGREEN"
    }:
        blockers.append("search_freshness_class_invalid")
    if not package["primary_reader_question"].endswith("?"):
        blockers.append("primary_reader_question_invalid")

    title = package["canonical_editorial_headline"]
    dek = package["dek"]
    search_title = package["search_title"]
    social_hook = package["social_hook"]
    meta = package["meta_description"]
    all_public = "\n".join((title, dek, search_title, social_hook, meta, body))
    evidence_text = _evidence_text(accepted_evidence_packet)
    evidence_folded = evidence_text.casefold()

    accepted_packet = (
        accepted_evidence_packet
        if isinstance(accepted_evidence_packet, Mapping)
        else {}
    )
    latest_state = accepted_packet.get("latest_event_state_closure")
    if not isinstance(latest_state, Mapping):
        research_packet = accepted_packet.get("grounded_research_packet")
        latest_state = (
            research_packet.get("latest_event_state_closure")
            if isinstance(research_packet, Mapping)
            else {}
        )
    latest_state = latest_state if isinstance(latest_state, Mapping) else {}
    if str(latest_state.get("latest_supported_state") or "") in {
        "OCCURRED_OR_OUTCOME_REPORTED",
        "CHANGED_OR_CANCELLED",
    }:
        from live_contentops.grounded_news_research_v1 import (
            _FORWARD_EVENT_STATE_RE,
        )

        target_terms = {
            str(value).casefold()
            for value in latest_state.get("target_terms") or []
            if str(value)
        }
        structured = package.get("structured_data_packet")
        stale_state_surfaces = [
            title,
            dek,
            search_title,
            social_hook,
            meta,
            body,
            *[str(value) for value in article.get("secondary_reader_questions") or []],
            *(
                [
                    str(structured.get("headline") or ""),
                    str(structured.get("description") or ""),
                ]
                if isinstance(structured, Mapping)
                else []
            ),
        ]
        required_overlap = 1 if len(target_terms) == 1 else 2
        if any(
            _FORWARD_EVENT_STATE_RE.search(surface)
            and len(_tokens(surface).intersection(target_terms)) >= required_overlap
            for surface in stale_state_surfaces
        ):
            blockers.append("superseded_forward_event_state_in_public_copy")

    if _normalise(article.get("title")) != title:
        blockers.append("canonical_editorial_headline_title_mismatch")
    if _normalise(article.get("subtitle")) != dek:
        blockers.append("dek_subtitle_mismatch")
    if _normalise(article.get("seo_title")) != search_title:
        blockers.append("search_title_seo_title_mismatch")
    if _normalise(article.get("social_lede")) != social_hook:
        blockers.append("social_hook_social_lede_mismatch")
    if _normalise(article.get("slug")) != package["canonical_slug_candidate"]:
        blockers.append("canonical_slug_alias_mismatch")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", package["canonical_slug_candidate"]):
        blockers.append("canonical_slug_candidate_invalid")
    if _INTERNAL_LANGUAGE.search(all_public):
        blockers.append("internal_system_language_leakage")
    if _PROHIBITED_INFORMALITY.search(all_public):
        blockers.append("prohibited_informality")
    if _BOILERPLATE_SEARCH.search(search_title):
        blockers.append("boilerplate_search_title")

    body_tokens = _tokens(body + " " + dek)
    title_tokens = _tokens(title)
    if title_tokens and len(title_tokens & body_tokens) / len(title_tokens) < 0.45:
        blockers.append("headline_body_proposition_mismatch")
    proposition_tokens = _tokens(title + " " + dek + " " + body)
    social_tokens = _tokens(social_hook)
    if social_tokens and len(social_tokens & proposition_tokens) / len(social_tokens) < 0.65:
        blockers.append("social_hook_introduces_new_claim")

    for surface_name, surface in (("headline", title), ("search_title", search_title), ("social_hook", social_hook), ("meta_description", meta)):
        if _SENSATIONAL.search(surface) and _normalise(surface).casefold() not in evidence_folded:
            blockers.append(f"unsupported_sensational_{surface_name}")
    for surface_name, surface in (("search_title", search_title), ("social_hook", social_hook), ("meta_description", meta)):
        surface_markers = {
            match.group(0).casefold()
            for pattern in (_CAUSAL, _SENSATIONAL)
            for match in pattern.finditer(surface)
        }
        body_markers = {
            match.group(0).casefold()
            for pattern in (_CAUSAL, _SENSATIONAL)
            for match in pattern.finditer(body)
        }
        if surface_markers.difference(body_markers):
            blockers.append(f"seo_or_social_claim_strengthening:{surface_name}")

    annotations = article.get("epistemic_claims")
    annotations = list(annotations) if isinstance(annotations, Sequence) and not isinstance(annotations, (str, bytes)) else []
    valid_analysis: list[str] = []
    evidence_ids = _evidence_ids(accepted_evidence_packet)
    for row in annotations:
        if not isinstance(row, Mapping):
            blockers.append("epistemic_claim_annotation_invalid")
            continue
        claim = _normalise(row.get("text"))
        layer = str(row.get("layer") or "")
        treatment = str(row.get("public_treatment") or "")
        source_ids = {str(value) for value in row.get("source_ids") or [] if str(value)}
        if not claim or claim.casefold() not in _normalise(all_public).casefold():
            blockers.append("epistemic_claim_not_present_in_public_copy")
        if layer not in _LAYERS:
            blockers.append("epistemic_claim_layer_invalid")
        if layer in {"OBSERVED_FACT", "ATTRIBUTED_INTERPRETATION"} and (
            not source_ids or not source_ids.issubset(evidence_ids)
        ):
            blockers.append("epistemic_source_binding_invalid")
        if layer == "ATTRIBUTED_INTERPRETATION" and treatment != "ADJACENT_ATTRIBUTION":
            blockers.append("attributed_interpretation_treatment_invalid")
        if layer == "CAPITAL_CHRONICLE_ANALYSIS":
            valid_analysis.append(claim.casefold())
            if treatment not in {"EXPLICIT_ANALYSIS", "SUPPORTED_SYNTHESIS"}:
                blockers.append("capital_chronicle_analysis_presented_as_source_fact")
        if layer == "SCENARIO_OR_UNCERTAINTY" and treatment != "CONDITIONAL":
            blockers.append("scenario_not_conditional")
        if (
            layer == "SCENARIO_OR_UNCERTAINTY"
            and claim
            and not _SCENARIO_CONDITIONAL_OR_UNCERTAIN.search(claim)
        ):
            blockers.append("scenario_public_copy_not_conditional")
    omission_support = [
        value.casefold()
        for value in _supported_source_omission_claims(accepted_evidence_packet)
    ]
    for assertion in _source_omission_assertions(all_public):
        folded = assertion.casefold()
        if not any(claim in folded or folded in claim for claim in omission_support):
            blockers.append("unproven_source_omission_claim")
            break
    for sentence in re.split(r"(?<=[.!?])\s+", _normalise(body)):
        sentence_tokens = _tokens(sentence)
        source_overlap = bool(sentence_tokens) and (
            len(sentence_tokens & _tokens(evidence_text)) / len(sentence_tokens) >= 0.65
        )
        if _CAUSAL.search(sentence) and not source_overlap and not any(
            claim and claim in sentence.casefold() for claim in valid_analysis
        ):
            blockers.append("unsupported_causality")

    evidence_numbers = set(_NUMBER.findall(evidence_text))
    for number in _NUMBER.findall(all_public):
        if number not in evidence_numbers:
            blockers.append("numeric_source_binding_violation")
            break

    quotes = [_normalise(value) for value in _QUOTE.findall(all_public)]
    quote_records = [row for row in article.get("quote_source_records") or [] if isinstance(row, Mapping)]
    for quote in quotes:
        if not any(
            _normalise(row.get("quote_text")) == quote
            and set(str(value) for value in row.get("source_ids") or []).issubset(evidence_ids)
            and bool(row.get("source_ids"))
            for row in quote_records
        ):
            blockers.append("fake_or_unbound_quote_presentation")
            break

    paragraphs = _paragraphs(body)
    if len(paragraphs) >= 3:
        closing_tokens = _tokens(paragraphs[-1])
        for prior in paragraphs[:-1]:
            prior_tokens = _tokens(prior)
            union = closing_tokens | prior_tokens
            if union and len(closing_tokens & prior_tokens) / len(union) >= 0.78:
                blockers.append("duplicated_conclusion")
                break

    keyword = _normalise(article.get("seo_primary_keyword"))
    if keyword:
        occurrences = len(re.findall(rf"(?<!\w){re.escape(keyword)}(?!\w)", all_public, re.I))
        word_count = max(1, len(re.findall(r"\b\w+\b", all_public)))
        keyword_words = max(1, len(keyword.split()))
        if occurrences >= 5 and (occurrences * keyword_words) / word_count > 0.06:
            blockers.append("keyword_stuffing")

    for row in article.get("internal_link_candidates") or []:
        if not isinstance(row, Mapping):
            blockers.append("internal_link_candidate_invalid")
            continue
        if str(row.get("relation") or "") not in _ELIGIBLE_LINK_RELATIONS:
            blockers.append("internal_link_relation_invalid")
        anchor = _normalise(row.get("anchor_text"))
        if len(_tokens(anchor)) < 2 or anchor.casefold() in {"click here", "read more", "here"}:
            blockers.append("internal_link_anchor_not_descriptive")

    structured_supported = bool((editorial_packet.get("seo") or {}).get("structured_data_supported"))
    structured = package.get("structured_data_packet")
    if structured_supported:
        if not isinstance(structured, Mapping):
            blockers.append("structured_data_packet_missing")
        else:
            if str(structured.get("@type") or "") not in {"Article", "NewsArticle"}:
                blockers.append("structured_data_type_invalid")
            if _normalise(structured.get("headline")) != title:
                blockers.append("structured_data_headline_mismatch")
            if _normalise(structured.get("description")) != meta:
                blockers.append("structured_data_description_mismatch")
            published = _normalise(structured.get("datePublished"))
            modified = _normalise(structured.get("dateModified"))
            pending_binding = str(structured.get("publication_time_binding") or "") == (
                "COORDINATOR_MUST_BIND_EXACT_TIMESTAMP_BEFORE_EMISSION"
            ) and structured.get("eligible_for_emission") is False
            if bool(published) != bool(modified) or (not published and not pending_binding):
                blockers.append("structured_data_dates_missing_or_unbound")
            if _normalise(structured.get("author")) != package["author_identity"]:
                blockers.append("structured_data_author_identity_mismatch")
            if _normalise(structured.get("publisher")) != package["publisher_identity"]:
                blockers.append("structured_data_publisher_identity_mismatch")

    humor_lines = article.get("humor_lines")
    humor_lines = list(humor_lines) if isinstance(humor_lines, Sequence) and not isinstance(humor_lines, (str, bytes)) else []
    ceiling = int((editorial_packet.get("humor") or {}).get("maximum_declared_dry_lines") or 0)
    if len(humor_lines) > ceiling:
        blockers.append("prohibited_humor_class_or_ceiling")
    for line in humor_lines:
        if _normalise(line).casefold() not in _normalise(all_public).casefold():
            blockers.append("declared_humor_line_not_present")

    all_findings = list(dict.fromkeys(blockers))
    checks = {
        "packet_hash_bound": not any("packet" in blocker and ("hash" in blocker or "binding" in blocker) for blocker in all_findings),
        "required_surfaces_present": not any("required_surface" in blocker or "surface_type" in blocker for blocker in all_findings),
        "proposition_bound": not any(blocker in {"headline_body_proposition_mismatch", "social_hook_introduces_new_claim", "unsupported_causality"} for blocker in all_findings),
        "seo_truth_preserved": not any(blocker.startswith(("unsupported_sensational_", "seo_or_social_claim_strengthening", "keyword_stuffing")) for blocker in all_findings),
        "epistemic_and_source_binding": not any(blocker in {"epistemic_source_binding_invalid", "capital_chronicle_analysis_presented_as_source_fact", "numeric_source_binding_violation", "fake_or_unbound_quote_presentation"} for blocker in all_findings),
        "tone_policy_preserved": not any(blocker in {"prohibited_informality", "prohibited_humor_class_or_ceiling"} for blocker in all_findings),
        "structured_data_matches_visible_copy": not any(blocker.startswith("structured_data_") for blocker in all_findings),
    }
    severity = classify_institutional_edge_findings(all_findings)
    return {
        "schema_version": VALIDATION_SCHEMA_VERSION,
        "classification": "PASS" if not severity["hard_blockers"] else "BLOCKED",
        "blockers": severity["hard_blockers"],
        "hard_blockers": severity["hard_blockers"],
        "soft_warnings": severity["soft_warnings"],
        "all_findings": all_findings,
        "checks": checks,
        "editorial_packet_sha256": expected_hash,
        "editorial_seo_package": package,
        "ordinary_semantic_review_calls": 0,
        "factual_authority": False,
        "numeric_authority": False,
        "publication_authority": False,
        "public_write_authority": False,
    }
