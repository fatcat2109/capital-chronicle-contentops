"""Claim-scoped evidence sufficiency for the canonical rolling-X newsroom.

This module does not acquire evidence and grants no publication authority.  It converts the
accepted source documents plus discovery-only story summaries into an explicit record of claims
that are supported, omitted, or blocked.  X/social text remains candidate material only.
"""
from __future__ import annotations

from hashlib import sha256
from html import unescape
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
_SENSITIVE_CLAIM_RE = re.compile(
    r"\b(?:alleg(?:e|ed|es|edly|ation|ations)|accus(?:e|ed|es|ation|ations)|"
    r"disput(?:e|ed|es)|unconfirm(?:ed|able)|uncertain(?:ty)?|deny|denied|denies|"
    r"conflict|attack(?:ed|s)?|strike|struck|fires?|fired|kill(?:ed|s|ing)?|"
    r"casualt(?:y|ies)|war|blockade|fraud|misconduct|probe|investigat(?:e|ed|ion)|"
    r"lawsuit|sanction(?:ed|s)?|breach(?:ed)?|secretly|conceal(?:ed|s)?)\b",
    re.IGNORECASE,
)
_CAUSAL_MARKET_FUTURE_RE = re.compile(
    r"\b(?:caus(?:e|ed|es|al)|led\s+to|driv(?:e|en|es|ing)|because\s+of|"
    r"market\s+reaction|shares?\s+(?:rose|fell|jumped|slid)|price\s+(?:rose|fell)|"
    r"will\s+(?:cause|drive|lead|raise|lower)|future\s+outcome)\b",
    re.IGNORECASE,
)
_RESERVED_PROPRIETARY_RE = re.compile(
    r"\b(?:probabilit(?:y|ies)|forecast|scenario|regime|valuation|price\s+target|"
    r"expected\s+return|base\s+case|bull\s+case|bear\s+case|decision\s+signal)\b",
    re.IGNORECASE,
)
_ATTRIBUTED_SELF_STATEMENT_RE = re.compile(
    r"\b(?:said|says|stated|announced|published|filed|denied|claims?|according\s+to|"
    r"in\s+(?:its|the)\s+(?:statement|filing|release|notice))\b",
    re.IGNORECASE,
)
_INTERESTED_PARTY_ROLES = frozenset(
    {"INTERESTED_PARTY", "ISSUER", "SUBJECT", "ADVOCATE", "MANAGEMENT", "PARTY_TO_DISPUTE"}
)
_EXPLICIT_SENSITIVITY_KEYS = (
    "sensitive_claim",
    "claim_sensitive",
    "unusually_consequential",
    "disputed",
    "uncertain",
    "conflict_related",
    "allegation",
)


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
            # Compact newsroom labels such as ``US CPI July 2026 Report`` are legitimate event
            # identities even when they fall just below a prose-sentence threshold. Twelve
            # characters still excludes empty/vague fragments while letting evidence ranking bind
            # the label to a fuller accepted source title. Reader-value remains a later hard gate.
            if len(sentence) >= 12 and sentence not in candidates:
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


def _document_support_segments(document: Mapping[str, Any]) -> list[str]:
    """Return reader-level evidence segments instead of one document-wide token bag.

    A long official page can mention the subject in one section and unrelated market terms in
    another.  Treating the whole page as one bag of words allowed those scattered tokens to
    appear to support a composite headline claim.  Claim support must be local to a title,
    excerpt, sentence, or HTML block; topic overlap elsewhere in the document is insufficient.
    """
    segments: list[str] = []
    block_tag = re.compile(
        r"</?(?:article|aside|blockquote|br|div|footer|h[1-6]|header|li|ol|p|"
        r"section|table|tbody|td|th|thead|tr|ul)[^>]*>",
        flags=re.IGNORECASE,
    )
    for value in (
        document.get("title"),
        document.get("source_excerpt"),
        document.get("canonical_content_text"),
    ):
        text = unescape(str(value or ""))
        text = block_tag.sub("\n", text)
        text = re.sub(r"<[^>]+>", " ", text)
        for raw_segment in re.split(r"\n+|(?<=[.!?])\s+", text):
            segment = " ".join(raw_segment.split())
            if segment and segment not in segments:
                segments.append(segment)
    return segments


def _support_score(claim: str, document: Mapping[str, Any]) -> float:
    claim_tokens = _tokens(claim)
    if not claim_tokens:
        return 0.0
    return max(
        (
            len(claim_tokens.intersection(_tokens(segment))) / len(claim_tokens)
            for segment in _document_support_segments(document)
        ),
        default=0.0,
    )


def _numbers_supported(claim: str, document: Mapping[str, Any]) -> bool:
    numbers = [re.sub(r"[^0-9.]", "", value) for value in _NUMBER_RE.findall(claim)]
    if not numbers:
        return True
    if str(document.get("source_authority_class") or "") not in (
        PRIMARY_AUTHORITY_CLASSES | SECONDARY_AUTHORITY_CLASSES
    ):
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
    # Remove ordinal suffixes together with the numeric token.  Leaving ``st`` behind from
    # ``1st`` produced malformed live prose (for example, "becomes st European ...").
    narrowed = re.sub(
        r"(?<![A-Za-z])[-+]?(?:\$|€|£)?\d[\d,]*(?:\.\d+)?(?:st|nd|rd|th)(?![A-Za-z])",
        "",
        claim,
        flags=re.IGNORECASE,
    )
    narrowed = _NUMBER_RE.sub("", narrowed)
    narrowed = re.sub(
        r"\b(?:basis points?|bps|billion|million|trillion|percent|percentage|per cent|shares?|dollars?|euros?|pounds?)\b",
        "",
        narrowed,
        flags=re.IGNORECASE,
    )
    # Approximation and comparison words qualify the removed number. Retaining them creates
    # malformed residual prose ("nearly in potential sales") and can make a broader claim look
    # supported merely because its numeric fragment disappeared.
    narrowed = re.sub(
        r"\b(?:approximately|approx\.?|nearly|roughly|about|around|up to|at least|"
        r"at most|more than|less than|over|under)\b",
        "",
        narrowed,
        flags=re.IGNORECASE,
    )
    narrowed = re.sub(r"\s+([,.;:])", r"\1", narrowed)
    return " ".join(narrowed.split()).strip(" ,;:-")


def _numeric_scope_narrowing_supported(
    claim: str, document: Mapping[str, Any]
) -> bool:
    """Require the non-numeric proposition to be locally supported as a whole.

    Numeric omission may remove only the number and its qualifier. It must not silently narrow
    countries, actors, timing, coordination, causality, or another material proposition. The old
    0.34 topic-overlap threshold admitted an Italy-only source for a simultaneous, coordinated
    Norway/Italy/South-Korea claim. A single reader-level evidence segment must now retain strong
    coverage of the complete residual proposition.
    """
    claim_tokens = _tokens(claim)
    if not claim_tokens:
        return False
    return any(
        len(claim_tokens.intersection(_tokens(segment))) / len(claim_tokens) >= 0.80
        for segment in _document_support_segments(document)
    )


def _claim_requires_corroboration(request: Mapping[str, Any], claim: str) -> bool:
    """Classify sensitivity at claim scope, keeping geopolitical reporting conservative."""
    context = request.get("story_context")
    context = context if isinstance(context, Mapping) else {}
    if str(request.get("story_type") or "") == "geopolitical_event":
        return True
    for source in (request, context):
        if any(source.get(key) is True for key in _EXPLICIT_SENSITIVITY_KEYS):
            return True
        risk = " ".join(
            str(value)
            for key in ("risk_flags", "claim_risk", "sensitivity", "dispute_status")
            for value in (
                source.get(key)
                if isinstance(source.get(key), (list, tuple, set))
                else [source.get(key)]
            )
            if value is not None
        )
        if _SENSITIVE_CLAIM_RE.search(risk):
            return True
    return bool(
        _SENSITIVE_CLAIM_RE.search(str(claim or ""))
        or _CAUSAL_MARKET_FUTURE_RE.search(str(claim or ""))
        or _RESERVED_PROPRIETARY_RE.search(str(claim or ""))
    )


def _document_is_interested_party(document: Mapping[str, Any]) -> bool:
    authority = str(document.get("source_authority_class") or "")
    role = str(
        document.get("source_interest_role")
        or document.get("source_relationship_to_claim")
        or ""
    ).upper()
    return authority == "first_party_public_source" or role in _INTERESTED_PARTY_ROLES


def _primary_support_kind(
    request: Mapping[str, Any], claim: str, document: Mapping[str, Any]
) -> str | None:
    """Classify how one primary may support this exact claim.

    Interested parties prove their own public act/statement and inspectable contents, not the
    independent truth of disputed third-party allegations, misconduct, causality, or future
    outcomes.  Reserved Core Analyzer-style conclusions require governed CC authority.
    """
    authority = str(document.get("source_authority_class") or "")
    if authority not in PRIMARY_AUTHORITY_CLASSES:
        return None
    if _RESERVED_PROPRIETARY_RE.search(claim):
        return "INDEPENDENT" if authority == "governed_capital_chronicle" else None
    interested = _document_is_interested_party(document)
    sensitive = bool(_SENSITIVE_CLAIM_RE.search(claim))
    causal = bool(_CAUSAL_MARKET_FUTURE_RE.search(claim))
    if interested and (sensitive or causal):
        return "ATTRIBUTED_INTERESTED_PARTY" if _ATTRIBUTED_SELF_STATEMENT_RE.search(claim) else None
    if causal and authority != "governed_capital_chronicle":
        capabilities = {
            str(value) for value in (document.get("claim_capabilities") or [])
        }
        if not ({"observed_market_reaction", "independent_causality_evidence"} & capabilities):
            return None
    return "ATTRIBUTED_INTERESTED_PARTY" if interested else "INDEPENDENT"


def requires_enhanced_evidence_review(request: Mapping[str, Any]) -> bool:
    """Return whether the story must retain claim-scoped enhanced evidence review.

    Ordinary newsroom reporting does not need a claim-by-claim dossier. Allegations,
    disputes, conflict reporting, unusually consequential claims, and exact quotations keep
    the stronger contract because a false or misattributed publication would be materially
    harmful.
    """
    candidates = _claim_candidates(request)
    return any(
        _claim_requires_corroboration(request, claim) or bool(_QUOTE_RE.search(claim))
        for claim in candidates or [""]
    )


def summarize_evidence_substance(
    request: Mapping[str, Any],
    documents: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Measure usable writing depth without turning depth into factual eligibility.

    A source-title/RSS record can prove an ordinary core proposition while still being too thin
    for a useful article. This signal requests bounded enrichment; it never makes a second source
    mandatory and never changes the minimum-evidence decision.
    """
    effective_mode = str(
        request.get("effective_article_mode")
        or request.get("resolved_article_mode")
        or request.get("article_mode")
        or ""
    )
    concise = effective_mode in {"BREAKING_BRIEF", "FOLLOW_UP_UPDATE"}
    target_words = 90 if concise else 180
    rows: list[dict[str, Any]] = []
    total_words = 0
    for document in documents:
        if not isinstance(document, Mapping):
            continue
        authority = str(document.get("source_authority_class") or "")
        if authority not in PRIMARY_AUTHORITY_CLASSES | SECONDARY_AUTHORITY_CLASSES:
            continue
        title = " ".join(str(document.get("title") or "").split())
        content = unescape(str(document.get("canonical_content_text") or ""))
        content = re.sub(r"<[^>]+>", " ", content)
        content = " ".join(content.split())
        words = re.findall(r"\b[A-Za-z0-9][A-Za-z0-9'’-]*\b", content)
        # A listing whose content is only its title is factual evidence but contributes no
        # article-depth beyond the proposition already counted by minimum eligibility.
        title_only = bool(title) and content.casefold().strip(" .") == title.casefold().strip(" .")
        usable_words = 0 if title_only else len(words)
        total_words += usable_words
        rows.append(
            {
                "document_id": str(
                    document.get("document_id")
                    or document.get("evidence_id")
                    or document.get("source_id")
                    or ""
                ),
                "usable_content_words": usable_words,
                "title_only": title_only,
                "source_authority_class": authority,
            }
        )
    enough = total_words >= target_words
    return {
        "schema_version": "contentops.evidence_substance_summary.v1",
        "article_mode": effective_mode,
        "target_usable_content_words": target_words,
        "usable_content_words": total_words,
        "usable_document_count": len(rows),
        "substantive_document_count": sum(
            1 for row in rows if int(row["usable_content_words"]) >= 60
        ),
        "enough_for_useful_article": enough,
        "enrichment_recommended": not enough,
        "additional_source_is_eligibility_requirement": False,
        "documents": rows,
        "publication_authority": False,
    }


def build_minimum_trustworthy_evidence_packet(
    request: Mapping[str, Any],
    documents: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build the compact ordinary-story packet authorized by the newsroom owner.

    The packet binds one directly attributed core proposition to one accessible reputable
    source. It intentionally has no claim-by-claim support matrix. Enhanced-risk stories are
    routed to :func:`build_claim_evidence_contract` instead.
    """
    if requires_enhanced_evidence_review(request):
        return {
            "schema_version": "contentops.minimum_trustworthy_evidence_packet.v1",
            "status": "ENHANCED_EVIDENCE_REQUIRED",
            "risk_tier": "ENHANCED",
            "publication_authority": False,
        }
    eligible = [
        dict(row)
        for row in documents
        if isinstance(row, Mapping)
        and str(row.get("source_authority_class") or "")
        in PRIMARY_AUTHORITY_CLASSES | SECONDARY_AUTHORITY_CLASSES
        and str(row.get("source_url") or "").startswith("https://")
    ]
    candidates = _claim_candidates(request)
    ranked: list[tuple[int, int, dict[str, Any]]] = []
    for index, document in enumerate(eligible):
        document_tokens = _tokens(_document_text(document))
        overlap = max(
            (len(_tokens(candidate).intersection(document_tokens)) for candidate in candidates),
            default=0,
        )
        ranked.append((overlap, -index, document))
    ranked.sort(key=lambda row: (row[0], row[1]), reverse=True)
    selected = ranked[0][2] if ranked and (ranked[0][0] >= 2 or not candidates) else None
    raw_title = " ".join(str((selected or {}).get("title") or "").split())
    proposition = re.sub(
        r"^(?:exclusive|breaking|update|analysis)\s*(?:[:|\-]\s*)",
        "",
        raw_title,
        flags=re.IGNORECASE,
    ).strip()
    title_is_transport_filename = bool(
        re.fullmatch(r"[^/\\]+\.(?:csv|json|pdf|txt|xml)", raw_title, re.IGNORECASE)
    )
    if selected is not None and (len(proposition) < 8 or title_is_transport_filename):
        bound_candidates = sorted(
            (
                (_support_score(candidate, selected), -index, candidate)
                for index, candidate in enumerate(candidates)
                if _support_score(candidate, selected) >= 0.34
                and _numbers_supported(candidate, selected)
                and _quotes_supported(candidate, selected)
            ),
            reverse=True,
        )
        if bound_candidates:
            proposition = bound_candidates[0][2]
    if selected is None or len(proposition) < 8:
        result = {
            "schema_version": "contentops.minimum_trustworthy_evidence_packet.v1",
            "status": "BLOCKED",
            "risk_tier": "ORDINARY",
            "blockers": ["ordinary_core_factual_proposition_not_directly_bound"],
            "publication_authority": False,
        }
        result["evidence_packet_sha256"] = _logical_hash(result)
        return result
    document_id = str(selected.get("document_id") or selected.get("evidence_id") or "")
    authority = str(selected.get("source_authority_class") or "")
    interested_party = _document_is_interested_party(selected)
    result = {
        "schema_version": "contentops.minimum_trustworthy_evidence_packet.v1",
        "status": "PASS",
        "risk_tier": "ORDINARY",
        "core_factual_proposition": proposition,
        "source_title": raw_title,
        "publisher": str(selected.get("publisher") or selected.get("source_identity") or ""),
        "source_url": str(selected.get("source_url") or ""),
        "reader_source_url": str(selected.get("reader_source_url") or "") or None,
        "reader_attribution_mode": (
            "BOUND_LINK" if selected.get("reader_source_url") else "ATTRIBUTION_ONLY"
            if selected.get("secondary_listing_only") is True
            else "BOUND_SOURCE_URL"
        ),
        "published_at_utc": str(
            selected.get("published_at_utc") or selected.get("event_time_utc") or ""
        ),
        "evidence_document_id": document_id,
        "source_authority_class": authority,
        "attribution_required": authority in SECONDARY_AUTHORITY_CLASSES or interested_party,
        "source_interest_role": (
            str(selected.get("source_interest_role") or "INTERESTED_PARTY")
            if interested_party else "INDEPENDENT_OR_OFFICIAL_RECORD"
        ),
        "independent_authority_for_disputed_third_party_allegations": False
        if interested_party else None,
        "directly_attributed_numbers_permitted": True,
        "unsupported_optional_claims_must_be_omitted": True,
        "x_content_grants_factual_authority": False,
        "publication_authority": False,
    }
    result["evidence_packet_sha256"] = _logical_hash(result)
    return result


def build_claim_evidence_contract(
    request: Mapping[str, Any],
    documents: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Bind only supportable claims and explicitly omit unsupported candidate material."""
    docs = [dict(row) for row in documents if isinstance(row, Mapping)]
    candidates = _claim_candidates(request)
    supported: list[dict[str, Any]] = []
    omitted: list[dict[str, Any]] = []
    for index, claim in enumerate(candidates):
        sensitive_secondary = _claim_requires_corroboration(request, claim)
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
        primary_support = [
            (document, _primary_support_kind(request, claim, document))
            for document, _score in eligible
            if str(document.get("source_authority_class") or "") in PRIMARY_AUTHORITY_CLASSES
        ]
        independent_primary = [
            document for document, kind in primary_support if kind == "INDEPENDENT"
        ]
        attributed_interested = [
            document
            for document, kind in primary_support
            if kind == "ATTRIBUTED_INTERESTED_PARTY"
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
        accepted = bool(independent_primary or attributed_interested) or (
            len(secondary_publishers) >= 2
            or (cautious_single_secondary and not sensitive_secondary and not quoted)
        )
        if accepted:
            bound = independent_primary or attributed_interested or secondary
            supported.append(
                {
                    "claim_id": claim_id,
                    "claim_text": claim,
                    "support_status": (
                        "SUPPORTED_PRIMARY"
                        if independent_primary
                        else "SUPPORTED_ATTRIBUTED_INTERESTED_PARTY"
                        if attributed_interested
                        else "SUPPORTED_CORROBORATED_SECONDARY"
                        if len(secondary_publishers) >= 2
                        else "SUPPORTED_ATTRIBUTED_SINGLE_SECONDARY"
                    ),
                    "numeric_claim": numeric,
                    "quoted_claim": quoted,
                    "attribution_required": not bool(independent_primary),
                    **(
                        {
                            "interested_party_source": True,
                            "independent_authority_for_disputed_third_party_allegations": False,
                        }
                        if attributed_interested else {}
                    ),
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
                    and _numeric_scope_narrowing_supported(narrowed, document)
                    and _quotes_supported(narrowed, document)
                ]
                narrowed_primary = [
                    row for row in narrowed_eligible
                    if _primary_support_kind(request, narrowed, row) == "INDEPENDENT"
                ]
                narrowed_attributed_interested = [
                    row for row in narrowed_eligible
                    if _primary_support_kind(request, narrowed, row)
                    == "ATTRIBUTED_INTERESTED_PARTY"
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
                narrowed_bound = (
                    narrowed_primary or narrowed_attributed_interested or narrowed_secondary
                )
                narrowed_supported = bool(
                    narrowed_primary or narrowed_attributed_interested
                ) or (
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
                            **(
                                {
                                    "interested_party_source": True,
                                    "independent_authority_for_disputed_third_party_allegations": False,
                                }
                                if narrowed_attributed_interested else {}
                            ),
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
        if not fallback_docs:
            fallback_docs = secondary_docs
        for document in fallback_docs:
            raw_title = " ".join(str(document.get("title") or "").split())
            authority = str(document.get("source_authority_class") or "")
            # An exact number in the accepted source title is directly stated evidence. It may
            # be retained from a primary source or an attributed reputable professional source;
            # discovery/X text itself never supplies the number.
            numeric_scope_omitted = False
            title = raw_title
            primary_kind = _primary_support_kind(request, title, document)
            title_sensitive = _claim_requires_corroboration(request, title)
            if (
                len(title) < 8
                or _QUOTE_RE.search(title)
            ):
                continue
            if authority not in PRIMARY_AUTHORITY_CLASSES | SECONDARY_AUTHORITY_CLASSES:
                continue
            if authority in PRIMARY_AUTHORITY_CLASSES and primary_kind is None:
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
            if authority in SECONDARY_AUTHORITY_CLASSES and title_sensitive:
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
                    "support_status": (
                        "SUPPORTED_ATTRIBUTED_INTERESTED_PARTY_SOURCE_TITLE"
                        if primary_kind == "ATTRIBUTED_INTERESTED_PARTY"
                        else "SUPPORTED_SOURCE_TITLE"
                    ),
                    "numeric_claim": bool(_NUMBER_RE.search(title)),
                    "quoted_claim": False,
                    "attribution_required": (
                        authority in SECONDARY_AUTHORITY_CLASSES
                        or primary_kind == "ATTRIBUTED_INTERESTED_PARTY"
                    ),
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
