"""Report-truth versus event-truth adapter for the current Simple V1 newsroom.

This module acquires nothing and grants no authority. It projects already-governed candidate
provenance and accepted evidence bytes into a small machine-readable epistemic state, reusing the
existing attribution taxonomy and claim-risk contract.
"""
from __future__ import annotations

import re
from hashlib import sha256
from typing import Any, Mapping, Sequence
from urllib.parse import urlsplit

from live_contentops.claim_evidence_contract_v1 import (
    build_claim_evidence_contract,
    requires_enhanced_evidence_review,
)
from live_contentops.preselection_intelligence_v1 import (
    ATTRIBUTED_REPUTABLE_PUBLISHERS,
    attributed_reputable_source_hints,
)
SCHEMA_VERSION = "contentops.v1_simple_epistemic_state.v1"
EVIDENCE_BASES = frozenset(
    {
        "PRIMARY_EVENT_EVIDENCE",
        "DIRECT_REPUTABLE_REPORT",
        "DIRECT_NEWSROOM_SOCIAL_REPORT",
        "TRUSTED_RELAY_ATTRIBUTED_REPORT",
        "TRUSTED_MARKET_RUMOR",
    }
)
EVENT_CONFIRMATION_STATES = frozenset(
    {
        "CONFIRMED",
        "UNCONFIRMED",
        "PARTIALLY_CONFIRMED",
        "DISPUTED_OR_DENIED",
        "SUPERSEDED",
    }
)
ORIGIN_CHARACTERS = frozenset(
    {
        "ON_RECORD",
        "ANONYMOUS_OR_INTERNAL_SOURCES",
        "LEAK",
        "RUMOR",
        "UNSPECIFIED",
    }
)
SOURCE_MULTIPLICITIES = frozenset({"SINGLE_SOURCE", "MULTI_SOURCE"})
PRIMARY_AUTHORITY_CLASSES = frozenset(
    {
        "official_public_primary_source",
        "first_party_public_source",
        "governed_capital_chronicle",
    }
)
SECONDARY_AUTHORITY_CLASSES = frozenset({"reputable_secondary_source"})
TRUSTED_RELAY_AUTHORITY_CLASS = "trusted_professional_feed_relay"
# Relay authority is record-scoped, not handle-scoped. The owner-curated canonical list marker is
# derived only by the canonical sidecar loader; historical professional-feed handles remain
# freshness-only and arbitrary social rows never enter this set.

_URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
_ORIGIN_INTERNAL_RE = re.compile(
    r"\b(?:anonymous|people\s+familiar|person\s+familiar|internal\s+sources?|"
    r"sources?\s+familiar|sources?\s+inside|officials?\s+who\s+asked\s+not\s+to\s+be\s+named)\b",
    re.IGNORECASE,
)
_ORIGIN_LEAK_RE = re.compile(r"\b(?:leak|leaked|leaking)\b", re.IGNORECASE)
_ORIGIN_RUMOR_RE = re.compile(r"\b(?:rumou?r|market\s+chatter)\b", re.IGNORECASE)
_DENIAL_RE = re.compile(r"\b(?:denied|denies|disputed|rejects?\s+the\s+report)\b", re.IGNORECASE)


def _normal(value: Any) -> str:
    return " ".join(str(value or "").split()).casefold()


def _source_account(candidate: Mapping[str, Any]) -> str:
    return str(candidate.get("source_account") or "").strip().lstrip("@").casefold()


def _canonical_x_provenance(candidate: Mapping[str, Any]) -> dict[str, Any]:
    value = candidate.get("canonical_x_list_provenance")
    value = dict(value) if isinstance(value, Mapping) else {}
    try:
        from live_contentops.newsroom_assignment_scheduler_v1 import (
            CANONICAL_X_LIST_PROVENANCE_SCHEMA_VERSION,
            CANONICAL_X_LIST_SOURCE_PLATFORM,
        )
        from live_contentops.x_list_ingest_capture_v1 import TARGET_LIST_ID
    except ImportError:
        return {}
    if (
        value.get("schema_version") != CANONICAL_X_LIST_PROVENANCE_SCHEMA_VERSION
        or value.get("owner_curated_canonical_x_list") is not True
        or str(value.get("target_list_id") or "") != TARGET_LIST_ID
        or str(value.get("source_platform") or "")
        != CANONICAL_X_LIST_SOURCE_PLATFORM
        or value.get("exact_sidecar_record") is not True
        or value.get("report_truth_scope_only") is not True
        or value.get("underlying_event_truth_granted") is not False
        or value.get("capital_chronicle_numeric_authority_granted") is not False
        or value.get("public_write_authority_granted") is not False
    ):
        return {}
    return value


def _event_proposition(text: str, hint: Mapping[str, Any] | None) -> str:
    cleaned = " ".join(_URL_RE.sub("", str(text or "")).split()).strip(" -:;,.\n")
    if not hint:
        return cleaned
    alias = re.escape(str(hint.get("matched_alias") or ""))
    if not alias:
        return cleaned
    leading = re.compile(
        rf"^(?:the\s+)?{alias}\s+(?:reports?|reported|says|said)\s+(?:that\s+)?",
        re.IGNORECASE,
    )
    cleaned = leading.sub("", cleaned)
    trailing = re.compile(
        rf"\s*,?\s*(?:per|via|according\s+to|reported\s+by)\s+(?:the\s+)?{alias}\b.*$",
        re.IGNORECASE,
    )
    cleaned = trailing.sub("", cleaned)
    trailing_reported = re.compile(
        rf"\s*,?\s*(?:the\s+)?{alias}\s+(?:reports?|reported|says|said)"
        r"(?:\s+(?:today|friday|monday|tuesday|wednesday|thursday|saturday|sunday))?\.?$",
        re.IGNORECASE,
    )
    cleaned = trailing_reported.sub("", cleaned)
    return cleaned.strip(" -:;,.\n")


def _report_clause(event: str) -> str:
    if len(event) >= 2 and event[:2].isupper():
        return event
    return event[:1].lower() + event[1:]


def candidate_report_provenance(candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Project explicit candidate provenance without promoting arbitrary social content."""
    headline = str(candidate.get("headline_text") or "")
    hints = attributed_reputable_source_hints(headline)
    hint = hints[0] if len(hints) == 1 else None
    account = _source_account(candidate)
    canonical_x = _canonical_x_provenance(candidate)
    event = _event_proposition(headline, hint)
    publisher = str((hint or {}).get("publisher") or "")
    report = (
        f"{publisher} reports that {_report_clause(event)}"
        if publisher and event
        else ""
    )
    trusted_relay = bool(canonical_x and hint is not None)
    explicit_rumor = bool(canonical_x and _ORIGIN_RUMOR_RE.search(headline))
    return {
        "schema_version": "contentops.v1_simple_candidate_report_provenance.v1",
        "explicit_reputable_attribution": hint is not None,
        "attributed_reputable_sources": hints,
        "primary_reporting_publisher": publisher or None,
        "primary_reporting_source_identity": str(
            (hint or {}).get("normalized_host") or ""
        )
        or None,
        "event_proposition": event,
        "report_proposition": report or None,
        "source_account": account or None,
        "source_url": str(candidate.get("source_url") or "") or None,
        "trusted_relay_identity_approved": trusted_relay,
        "owner_curated_canonical_x_record": bool(canonical_x),
        "canonical_x_list_provenance": canonical_x,
        "explicit_market_rumor": explicit_rumor,
        "preferred_route": (
            "TRUSTED_RELAY_ATTRIBUTED_REPORT"
            if trusted_relay
            else "TRUSTED_MARKET_RUMOR"
            if explicit_rumor
            else "ATTRIBUTED_REPUTABLE_REPORT_FIRST"
            if hint is not None
            else "DEFAULT_SHORTEST_GOVERNED_ROUTE"
        ),
        "arbitrary_x_list_membership_grants_authority": False,
        "report_or_event_authority_granted": False,
    }


def trusted_relay_document(
    request: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Return exact canonical-list report truth, never underlying event truth."""
    context = request.get("story_context")
    context = context if isinstance(context, Mapping) else {}
    profile = context.get("report_provenance")
    profile = profile if isinstance(profile, Mapping) else {}
    relay = bool(
        profile.get("trusted_relay_identity_approved") is True
        and profile.get("explicit_reputable_attribution") is True
    )
    rumor = bool(
        profile.get("owner_curated_canonical_x_record") is True
        and profile.get("explicit_market_rumor") is True
        and profile.get("explicit_reputable_attribution") is not True
    )
    if not relay and not rumor:
        return None
    text = str((context.get("leaf_summaries") or [""])[0] or "").strip()
    url = str(profile.get("source_url") or "")
    account = str(profile.get("source_account") or "")
    published = str(context.get("candidate_source_timestamp_utc") or "")
    if not text or not url.startswith("https://x.com/") or not account or not published:
        return None
    digest = sha256(text.encode("utf-8")).hexdigest()
    authority = (
        "trusted_professional_feed_relay"
        if relay
        else "trusted_market_rumor_source"
    )
    return {
        "document_id": ("trusted-relay-" if relay else "trusted-rumor-") + digest[:20],
        "title": text,
        "publisher": account,
        "source_identity": account,
        "source_authority_class": authority,
        "source_url": url,
        "reader_source_url": url,
        "published_at_utc": published,
        "published_at_source": "EXACT_GOVERNED_SIDECAR_SOURCE_TIMESTAMP",
        "canonical_content_sha256": digest,
        "canonical_content_text": text,
        "public_claim_allowed": True,
        "report_truth_only": True,
        "underlying_event_truth_granted": False,
        "original_publisher_report_separately_resolved": False,
        "retrieval_method": (
            "EXACT_GOVERNED_CANONICAL_X_RELAY_SIDECAR"
            if relay
            else "EXACT_GOVERNED_CANONICAL_X_RUMOR_SIDECAR"
        ),
    }


def canonical_x_report_document(
    request: Mapping[str, Any],
) -> tuple[dict[str, Any] | None, list[str]]:
    """Admit only an exact owner-curated canonical-list relay/rumor proposition.

    The document proves the relay's own captured words. It never proves the cited publisher's
    original report or the underlying event, and high-harm records retain enhanced evidence.
    """
    context = request.get("story_context")
    context = context if isinstance(context, Mapping) else {}
    profile = context.get("report_provenance")
    profile = profile if isinstance(profile, Mapping) else {}
    if profile.get("owner_curated_canonical_x_record") is not True:
        return None, ["canonical_x_owner_curated_provenance_required"]
    if requires_enhanced_evidence_review(request):
        return None, ["canonical_x_high_harm_enhanced_evidence_required"]
    document = trusted_relay_document(request)
    if document is None:
        return None, [
            "canonical_x_explicit_attribution_or_rumor_required"
        ]
    return document, []


def _origin_character(
    evidence_basis: str, source_text: str
) -> str:
    if evidence_basis == "PRIMARY_EVENT_EVIDENCE":
        return "ON_RECORD"
    if _ORIGIN_RUMOR_RE.search(source_text):
        return "RUMOR"
    if _ORIGIN_LEAK_RE.search(source_text):
        return "LEAK"
    if _ORIGIN_INTERNAL_RE.search(source_text):
        return "ANONYMOUS_OR_INTERNAL_SOURCES"
    return "UNSPECIFIED"


def _reader_label(
    *,
    evidence_basis: str,
    event_state: str,
    publisher: str,
    relay: str | None,
    multiplicity: str,
) -> str:
    if event_state == "CONFIRMED":
        return "CONFIRMED"
    if event_state == "DISPUTED_OR_DENIED":
        return "DISPUTED / DENIED"
    if evidence_basis == "TRUSTED_RELAY_ATTRIBUTED_REPORT":
        return f"RELAYED / UNCONFIRMED - @{relay}, citing {publisher}"
    if evidence_basis == "TRUSTED_MARKET_RUMOR":
        return "MARKET RUMOR — UNCONFIRMED"
    prefix = "SINGLE-SOURCE REPORT" if multiplicity == "SINGLE_SOURCE" else "UNCONFIRMED REPORT"
    return f"{prefix} - {publisher.upper()}"


def validate_epistemic_state(state: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    if state.get("schema_version") != SCHEMA_VERSION:
        blockers.append("epistemic_state_schema_invalid")
    if str(state.get("evidence_basis") or "") not in EVIDENCE_BASES:
        blockers.append("epistemic_evidence_basis_invalid")
    if str(state.get("event_confirmation_state") or "") not in EVENT_CONFIRMATION_STATES:
        blockers.append("epistemic_event_confirmation_state_invalid")
    if str(state.get("origin_character") or "") not in ORIGIN_CHARACTERS:
        blockers.append("epistemic_origin_character_invalid")
    if str(state.get("source_multiplicity") or "") not in SOURCE_MULTIPLICITIES:
        blockers.append("epistemic_source_multiplicity_invalid")
    for field in (
        "report_proposition",
        "event_proposition",
        "primary_reporting_publisher",
        "primary_reporting_source_identity",
        "reader_visible_epistemic_label",
    ):
        if len(str(state.get(field) or "").strip()) < 3:
            blockers.append(f"epistemic_{field}_missing")
    if state.get("report_truth_supported") is not True:
        blockers.append("epistemic_report_truth_not_supported")
    if (
        state.get("event_confirmation_state") == "CONFIRMED"
        and state.get("event_truth_supported") is not True
    ):
        blockers.append("epistemic_confirmed_event_truth_not_supported")
    if (
        state.get("evidence_basis") != "PRIMARY_EVENT_EVIDENCE"
        and state.get("event_truth_supported") is not False
    ):
        blockers.append("epistemic_report_basis_event_truth_inflation")
    if state.get("authority_granted_by_adapter") is not False:
        blockers.append("epistemic_adapter_authority_invalid")
    return sorted(set(blockers))


def build_epistemic_state(
    *,
    request: Mapping[str, Any],
    documents: Sequence[Mapping[str, Any]],
    selected_route: str,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Classify accepted bytes against the narrowest proposition they actually prove."""
    context = request.get("story_context")
    context = context if isinstance(context, Mapping) else {}
    profile = context.get("report_provenance")
    profile = profile if isinstance(profile, Mapping) else {}
    docs = [
        dict(row)
        for row in documents
        if isinstance(row, Mapping) and row.get("public_claim_allowed") is True
    ]
    if not docs:
        return None, ["epistemic_accepted_document_missing"]
    event = str(profile.get("event_proposition") or "").strip()
    if len(event) < 8:
        return None, ["epistemic_event_proposition_missing"]
    if requires_enhanced_evidence_review(request) and len(
        {
            str(row.get("publisher") or row.get("source_identity") or "").casefold()
            for row in docs
        }
    ) < 2 and not any(
        str(row.get("source_authority_class") or "") in PRIMARY_AUTHORITY_CLASSES
        for row in docs
    ):
        return None, ["epistemic_high_harm_single_source_insufficient"]

    authorities = {
        str(row.get("source_authority_class") or "") for row in docs
    }
    attributed_host = str(profile.get("primary_reporting_source_identity") or "")
    attributed_publisher = str(profile.get("primary_reporting_publisher") or "")
    matching_docs = docs
    if attributed_host:
        matching_docs = [
            row
            for row in docs
            if str(row.get("source_identity") or "").casefold().removeprefix("www.")
            == attributed_host.removeprefix("www.")
        ]
    relay = TRUSTED_RELAY_AUTHORITY_CLASS in authorities
    rumor = "trusted_market_rumor_source" in authorities
    primary = bool(authorities.intersection(PRIMARY_AUTHORITY_CLASSES))
    secondary = bool(authorities.intersection(SECONDARY_AUTHORITY_CLASSES))
    if relay:
        matching_docs = docs
        evidence_basis = "TRUSTED_RELAY_ATTRIBUTED_REPORT"
    elif rumor:
        matching_docs = docs
        evidence_basis = "TRUSTED_MARKET_RUMOR"
    elif primary:
        evidence_basis = "PRIMARY_EVENT_EVIDENCE"
    elif secondary and matching_docs:
        evidence_basis = "DIRECT_REPUTABLE_REPORT"
    else:
        return None, ["epistemic_report_provenance_not_governed"]

    contract_request = {
        **dict(request),
        "story_context": {**dict(context), "leaf_summaries": [event]},
    }
    if relay or rumor:
        relay_text = _normal(matching_docs[0].get("canonical_content_text"))
        event_terms = {
            value
            for value in re.findall(r"[a-z][a-z0-9'-]{2,}", _normal(event))
            if value not in {"that", "this", "with", "from", "report", "reports"}
        }
        if len([term for term in event_terms if term in relay_text]) < 3:
            return None, ["epistemic_relay_event_proposition_not_exactly_captured"]
        contract = {
            "status": "PASS",
            "supported_claims": [
                {
                    "support_status": (
                        "SUPPORTED_EXACT_TRUSTED_RELAY_ATTRIBUTION"
                        if relay
                        else "SUPPORTED_EXACT_CANONICAL_X_MARKET_RUMOR"
                    )
                }
            ],
        }
    else:
        contract = build_claim_evidence_contract(contract_request, matching_docs)
        if contract.get("status") != "PASS":
            return None, [
                "epistemic_selected_event_not_supported_by_route",
                *[
                    str(row.get("reason") or "epistemic_claim_blocked")
                    for row in contract.get("omitted_unsupported_claims") or []
                    if isinstance(row, Mapping)
                ],
            ]

    publisher = attributed_publisher or str(
        matching_docs[0].get("publisher") or matching_docs[0].get("source_identity") or ""
    )
    identity = attributed_host or str(matching_docs[0].get("source_identity") or "")
    report = str(profile.get("report_proposition") or "").strip()
    if relay:
        report = (
            f"@{profile.get('source_account')}, citing {publisher}, reports "
            f"{_report_clause(event)}"
        )
    if rumor and not report:
        report = f"@{profile.get('source_account')} relays market chatter that {_report_clause(event)}"
    if not report:
        report = f"{publisher} reports that {_report_clause(event)}"
    event_state = "CONFIRMED" if primary else "UNCONFIRMED"
    source_text = "\n".join(
        str(row.get("canonical_content_text") or "") for row in matching_docs
    )
    if _DENIAL_RE.search(source_text) and not primary:
        event_state = "DISPUTED_OR_DENIED"
    publishers = {
        str(row.get("publisher") or row.get("source_identity") or "").casefold()
        for row in matching_docs
        if str(row.get("publisher") or row.get("source_identity") or "")
    }
    multiplicity = "MULTI_SOURCE" if len(publishers) >= 2 else "SINGLE_SOURCE"
    relay_identity = str(profile.get("source_account") or "") or None
    state = {
        "schema_version": SCHEMA_VERSION,
        "evidence_basis": evidence_basis,
        "event_confirmation_state": event_state,
        "origin_character": _origin_character(evidence_basis, source_text),
        "source_multiplicity": multiplicity,
        "primary_reporting_publisher": publisher,
        "primary_reporting_source_identity": identity,
        "relay_source_identity": relay_identity if relay or rumor else None,
        "report_proposition": report,
        "event_proposition": event,
        "report_truth_supported": True,
        "event_truth_supported": primary,
        "report_truth_support_status": str(
            (contract.get("supported_claims") or [{}])[0].get("support_status") or "SUPPORTED"
        ),
        "event_truth_support_status": "SUPPORTED_PRIMARY" if primary else "UNCONFIRMED",
        "supporting_document_ids": sorted(
            str(row.get("document_id") or "") for row in matching_docs if row.get("document_id")
        ),
        "reader_visible_epistemic_label": _reader_label(
            evidence_basis=evidence_basis,
            event_state=event_state,
            publisher=publisher,
            relay=relay_identity,
            multiplicity=multiplicity,
        ),
        "analysis_must_be_conditional": event_state != "CONFIRMED",
        "underlying_event_may_be_stated_as_confirmed": primary,
        "adapter_changes_proposition_not_evidence_authority": True,
        "authority_granted_by_adapter": False,
        "public_write_authority": False,
        "selected_route": selected_route,
    }
    blockers = validate_epistemic_state(state)
    return (None, blockers) if blockers else (state, [])


def document_host(document: Mapping[str, Any]) -> str:
    return str(
        document.get("source_identity")
        or urlsplit(str(document.get("source_url") or "")).hostname
        or ""
    ).casefold().removeprefix("www.")


def publisher_for_host(host: str) -> str:
    profile = ATTRIBUTED_REPUTABLE_PUBLISHERS.get(str(host).removeprefix("www."))
    return str((profile or {}).get("publisher") or host)
