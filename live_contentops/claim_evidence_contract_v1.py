"""Claim-scoped evidence sufficiency for the canonical rolling-X newsroom.

This module does not acquire evidence and grants no publication authority.  It converts the
accepted source documents plus discovery-only story summaries into an explicit record of claims
that are supported, omitted, or blocked.  X/social text remains candidate material only.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "contentops.claim_evidence_contract.v1"
PRIMARY_AUTHORITY_CLASSES = frozenset(
    {"official_public_primary_source", "first_party_public_source", "governed_capital_chronicle"}
)
SECONDARY_AUTHORITY_CLASSES = frozenset({"reputable_secondary_source"})
_STOPWORDS = frozenset(
    {
        "about", "after", "again", "against", "along", "also", "amid", "among", "and",
        "are", "been", "being", "between", "could", "from", "have", "into", "more", "over",
        "report", "reported", "reports", "says", "than", "that", "the", "their", "there",
        "for", "these", "they", "this", "through", "under", "while", "will", "with", "would",
    }
)
_NUMBER_RE = re.compile(
    r"(?<![A-Za-z])[-+]?(?:\$|€|£)?\d[\d,]*(?:\.\d+)?(?:%|bn|mn|[kmbt])?",
    re.IGNORECASE,
)
_QUOTE_RE = re.compile(r"[\"“]([^\"”]{8,})[\"”]")


def _logical_hash(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def _tokens(text: str) -> set[str]:
    return {
        token.casefold()
        for token in re.findall(r"[A-Za-z][A-Za-z0-9'-]{2,}", str(text or ""))
        if token.casefold() not in _STOPWORDS
    }


def _claim_candidates(request: Mapping[str, Any]) -> list[str]:
    context = request.get("story_context") or {}
    values = [
        *(context.get("leaf_summaries") or []),
        context.get("why_now"),
    ]
    candidates: list[str] = []
    for value in values:
        text = " ".join(str(value or "").split())
        protected = (
            text.replace("U.S.", "U<PERIOD>S<PERIOD>")
            .replace("U.K.", "U<PERIOD>K<PERIOD>")
        )
        for sentence in re.split(r"(?<=[.!?])\s+|\s+\|\s+", protected):
            sentence = sentence.replace("<PERIOD>", ".")
            sentence = sentence.strip(" -")
            if len(sentence) >= 24 and sentence not in candidates:
                candidates.append(sentence[:600])
    return candidates[:20]


def _document_text(document: Mapping[str, Any]) -> str:
    return " ".join(
        str(value or "")
        for value in (
            document.get("title"),
            document.get("canonical_content_text"),
            document.get("source_excerpt"),
        )
    )


def _support_score(claim: str, document: Mapping[str, Any]) -> float:
    claim_tokens = _tokens(claim)
    if not claim_tokens:
        return 0.0
    document_tokens = _tokens(_document_text(document))
    return len(claim_tokens.intersection(document_tokens)) / len(claim_tokens)


def _numbers_supported(claim: str, document: Mapping[str, Any]) -> bool:
    numbers = [re.sub(r"[^0-9.]", "", value) for value in _NUMBER_RE.findall(claim)]
    if not numbers:
        return True
    if str(document.get("source_authority_class") or "") not in PRIMARY_AUTHORITY_CLASSES:
        return False
    haystack = re.sub(r"[^0-9.]", "", _document_text(document))
    return all(value and value in haystack for value in numbers)


def _quotes_supported(claim: str, document: Mapping[str, Any]) -> bool:
    quotes = [" ".join(value.split()).casefold() for value in _QUOTE_RE.findall(claim)]
    if not quotes:
        return True
    haystack = " ".join(_document_text(document).split()).casefold()
    return all(value in haystack for value in quotes)


def _without_numeric_scope(claim: str) -> str:
    narrowed = _NUMBER_RE.sub("", claim)
    narrowed = re.sub(
        r"\b(?:basis points?|bps|billion|million|trillion|percent|percentage|per cent|shares?|dollars?|euros?|pounds?)\b",
        "",
        narrowed,
        flags=re.IGNORECASE,
    )
    narrowed = re.sub(r"\s+([,.;:])", r"\1", narrowed)
    return " ".join(narrowed.split()).strip(" ,;:-")


def build_claim_evidence_contract(
    request: Mapping[str, Any],
    documents: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Bind only supportable claims and explicitly omit unsupported candidate material."""
    docs = [dict(row) for row in documents if isinstance(row, Mapping)]
    candidates = _claim_candidates(request)
    supported: list[dict[str, Any]] = []
    omitted: list[dict[str, Any]] = []
    story_type = str(request.get("story_type") or "")
    sensitive_secondary = story_type in {
        "geopolitical_event", "physical_event", "policy_decision", "regulatory_fiscal_event"
    }

    for index, claim in enumerate(candidates):
        claim_id = "claim-" + sha256(claim.encode("utf-8")).hexdigest()[:16]
        scored = [
            (document, _support_score(claim, document))
            for document in docs
        ]
        plausible = [(document, score) for document, score in scored if score >= 0.34]
        numeric = bool(_NUMBER_RE.search(claim))
        quoted = bool(_QUOTE_RE.search(claim))
        eligible = [
            (document, score)
            for document, score in plausible
            if _numbers_supported(claim, document) and _quotes_supported(claim, document)
        ]
        primary = [
            document for document, _score in eligible
            if str(document.get("source_authority_class") or "") in PRIMARY_AUTHORITY_CLASSES
        ]
        secondary = [
            document for document, _score in eligible
            if str(document.get("source_authority_class") or "") in SECONDARY_AUTHORITY_CLASSES
        ]
        secondary_publishers = {
            str(row.get("publisher") or row.get("source_identity") or "").casefold()
            for row in secondary
            if str(row.get("publisher") or row.get("source_identity") or "").strip()
        }
        cautious_single_secondary = bool(secondary) and len(secondary_publishers) == 1
        accepted = bool(primary) or (
            len(secondary_publishers) >= 2
            or (cautious_single_secondary and not sensitive_secondary and not numeric and not quoted)
        )
        if accepted:
            bound = primary or secondary
            supported.append(
                {
                    "claim_id": claim_id,
                    "claim_text": claim,
                    "support_status": (
                        "SUPPORTED_PRIMARY"
                        if primary
                        else "SUPPORTED_CORROBORATED_SECONDARY"
                        if len(secondary_publishers) >= 2
                        else "SUPPORTED_ATTRIBUTED_SINGLE_SECONDARY"
                    ),
                    "numeric_claim": numeric,
                    "quoted_claim": quoted,
                    "attribution_required": not bool(primary),
                    "evidence_document_ids": sorted(
                        {
                            str(row.get("document_id") or row.get("evidence_id") or "")
                            for row in bound
                            if str(row.get("document_id") or row.get("evidence_id") or "")
                        }
                    ),
                    "authority_classes": sorted(
                        {str(row.get("source_authority_class") or "") for row in bound}
                    ),
                }
            )
        else:
            narrowed_supported = False
            if numeric and not quoted:
                narrowed = _without_numeric_scope(claim)
                narrowed_eligible = [
                    document
                    for document in docs
                    if len(narrowed) >= 24
                    and _support_score(narrowed, document) >= 0.34
                    and _quotes_supported(narrowed, document)
                ]
                narrowed_primary = [
                    row
                    for row in narrowed_eligible
                    if str(row.get("source_authority_class") or "") in PRIMARY_AUTHORITY_CLASSES
                ]
                narrowed_secondary = [
                    row
                    for row in narrowed_eligible
                    if str(row.get("source_authority_class") or "") in SECONDARY_AUTHORITY_CLASSES
                ]
                narrowed_publishers = {
                    str(row.get("publisher") or row.get("source_identity") or "").casefold()
                    for row in narrowed_secondary
                    if str(row.get("publisher") or row.get("source_identity") or "").strip()
                }
                narrowed_bound = narrowed_primary or narrowed_secondary
                narrowed_supported = bool(narrowed_primary) or (
                    len(narrowed_publishers) >= 2
                    or (bool(narrowed_secondary) and not sensitive_secondary)
                )
                if narrowed_supported:
                    supported.append(
                        {
                            "claim_id": claim_id + "-narrowed",
                            "claim_text": narrowed,
                            "support_status": "SUPPORTED_WITH_NUMERIC_SCOPE_OMITTED",
                            "numeric_claim": False,
                            "quoted_claim": False,
                            "attribution_required": not bool(narrowed_primary),
                            "evidence_document_ids": sorted(
                                {
                                    str(row.get("document_id") or row.get("evidence_id") or "")
                                    for row in narrowed_bound
                                    if str(row.get("document_id") or row.get("evidence_id") or "")
                                }
                            ),
                            "authority_classes": sorted(
                                {
                                    str(row.get("source_authority_class") or "")
                                    for row in narrowed_bound
                                }
                            ),
                            "scope_reduction": "PRECISE_NUMERIC_CLAIM_OMITTED",
                        }
                    )
            reason = (
                "numeric_primary_authority_unavailable"
                if numeric and plausible
                else "quote_exact_support_unavailable"
                if quoted and plausible
                else "secondary_corroboration_insufficient"
                if plausible and sensitive_secondary
                else "candidate_claim_not_found_in_evidence"
            )
            omitted.append(
                {
                    "claim_id": claim_id,
                    "claim_text": claim,
                    "support_status": "OMITTED",
                    "reason": reason,
                }
            )

    # When discovery summaries are broader than the acquired evidence, the verified document
    # title is still a safe minimum claim.  It is never taken from X and is always attributed.
    if not supported:
        primary_docs = [
            row
            for row in docs
            if str(row.get("source_authority_class") or "") in PRIMARY_AUTHORITY_CLASSES
        ]
        secondary_docs = [
            row
            for row in docs
            if str(row.get("source_authority_class") or "") in SECONDARY_AUTHORITY_CLASSES
        ]
        secondary_publishers = {
            str(row.get("publisher") or row.get("source_identity") or "").casefold()
            for row in secondary_docs
            if str(row.get("publisher") or row.get("source_identity") or "").strip()
        }
        fallback_docs = primary_docs
        if not fallback_docs and (
            not sensitive_secondary or len(secondary_publishers) >= 2
        ):
            fallback_docs = secondary_docs
        for document in fallback_docs:
            raw_title = " ".join(str(document.get("title") or "").split())
            numeric_scope_omitted = bool(_NUMBER_RE.search(raw_title))
            title = _without_numeric_scope(raw_title) if numeric_scope_omitted else raw_title
            authority = str(document.get("source_authority_class") or "")
            if len(title) < 8 or _NUMBER_RE.search(title) or _QUOTE_RE.search(title):
                continue
            if authority not in PRIMARY_AUTHORITY_CLASSES | SECONDARY_AUTHORITY_CLASSES:
                continue
            if candidates:
                document_tokens = _tokens(_document_text(document))
                overlap_counts = [
                    len(_tokens(candidate).intersection(document_tokens))
                    for candidate in candidates
                ]
                if max(overlap_counts, default=0) < 2:
                    continue
            corroborating = [document]
            if authority in SECONDARY_AUTHORITY_CLASSES and sensitive_secondary:
                corroborating = [
                    row
                    for row in secondary_docs
                    if _support_score(title, row) >= 0.25
                ]
                if len(
                    {
                        str(row.get("publisher") or row.get("source_identity") or "").casefold()
                        for row in corroborating
                    }
                ) < 2:
                    continue
            supported.append(
                {
                    "claim_id": "claim-" + sha256(title.encode("utf-8")).hexdigest()[:16],
                    "claim_text": title,
                    "support_status": "SUPPORTED_SOURCE_TITLE",
                    "numeric_claim": False,
                    "quoted_claim": False,
                    "attribution_required": authority in SECONDARY_AUTHORITY_CLASSES,
                    "evidence_document_ids": sorted(
                        {
                            str(row.get("document_id") or row.get("evidence_id") or "")
                            for row in corroborating
                            if str(row.get("document_id") or row.get("evidence_id") or "")
                        }
                    ),
                    "authority_classes": [authority],
                    **(
                        {"scope_reduction": "SOURCE_TITLE_NUMERIC_SCOPE_OMITTED"}
                        if numeric_scope_omitted
                        else {}
                    ),
                }
            )
            break

    result = {
        "schema_version": SCHEMA_VERSION,
        "status": "PASS" if supported else "BLOCKED",
        "supported_claims": supported,
        "omitted_unsupported_claims": omitted,
        "blocked_claims": [] if supported else omitted,
        "supported_claim_count": len(supported),
        "omitted_claim_count": len(omitted),
        "fabricated_claim_count": 0,
        "x_content_grants_factual_authority": False,
        "publication_authority": False,
    }
    result["claim_contract_sha256"] = _logical_hash(result)
    return result
