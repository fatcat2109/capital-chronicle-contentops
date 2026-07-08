"""Deterministic V6 editorial acceptance audit.

This module is intentionally separate from transport/dispatch validation. A
packet can be mechanically dispatchable while still failing tier-1 editorial
acceptance because sources, SEO, structure, or public-body tone need review.
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.parse
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "editorial_quality_audit_v6.1"
EDITORIAL_APPROVED = "EDITORIAL_APPROVED"
EDITORIAL_NEEDS_REVIEW = "EDITORIAL_NEEDS_REVIEW"
EDITORIAL_BLOCKED = "EDITORIAL_BLOCKED"

URL_RE = re.compile(r"https?://[^\s<>()\[\]\"']+", re.IGNORECASE)
WORD_RE = re.compile(r"\b[a-z][a-z0-9'-]{2,}\b", re.IGNORECASE)

STOPWORDS = {
    "about", "after", "against", "along", "also", "analysis", "article", "before",
    "briefing", "capital", "chronicle", "current", "daily", "data", "does", "from",
    "have", "into", "latest", "more", "near", "news", "only", "other", "over",
    "reader", "risk", "risks", "source", "sources", "that", "the", "their", "this",
    "through", "when", "where", "while", "with", "without", "would",
}

WEAK_SEO_KEYWORDS = {
    "spike", "spikes", "rise", "rises", "update", "market", "macro", "briefing",
    "analysis", "news", "watch", "risk", "risks",
}

PIPELINE_INTERNAL_PATTERNS = {
    "capital_chronicle_database": r"\bcapital chronicle database\b",
    "contentops": r"\bcontentops\b",
    "deterministic": r"\bdeterministic\b",
    "dispatch": r"\bdispatch(?:ed|es|ing)?\b",
    "media_audit": r"\bmedia audit\b",
    "operator": r"\boperator(?:s)?\b",
    "pipeline": r"\bpipeline\b",
    "provider": r"\bprovider\b",
    "visual_slot": r"\bvisual slots?\b",
}

SOURCE_FAMILY_RULES = [
    ("fred", re.compile(r"(^|\.)fred\.stlouisfed\.org$", re.IGNORECASE)),
    ("eia", re.compile(r"(^|\.)eia\.gov$", re.IGNORECASE)),
    ("federal_reserve", re.compile(r"(^|\.)federalreserve\.gov$", re.IGNORECASE)),
    ("treasury", re.compile(r"(^|\.)treasury\.gov$", re.IGNORECASE)),
    ("bls", re.compile(r"(^|\.)bls\.gov$", re.IGNORECASE)),
    ("bea", re.compile(r"(^|\.)bea\.gov$", re.IGNORECASE)),
    ("imf", re.compile(r"(^|\.)imf\.org$", re.IGNORECASE)),
    ("world_bank", re.compile(r"(^|\.)worldbank\.org$", re.IGNORECASE)),
    ("iea", re.compile(r"(^|\.)iea\.org$", re.IGNORECASE)),
    ("opec", re.compile(r"(^|\.)opec\.org$", re.IGNORECASE)),
]

PRIMARY_SOURCE_CONCEPTS = {
    "fred": {"macro", "oil", "wti", "crude", "energy", "recession", "yield", "rates", "inflation", "volatility"},
    "eia": {"oil", "wti", "crude", "energy", "gasoline", "inventory", "volatility"},
    "federal_reserve": {"rates", "yield", "policy", "inflation", "recession", "macro"},
    "treasury": {"rates", "yield", "fiscal", "debt", "macro"},
    "bls": {"labor", "inflation", "wages", "macro", "recession"},
    "bea": {"gdp", "growth", "income", "macro", "recession"},
    "imf": {"macro", "geopolitics", "growth", "inflation", "recession"},
    "world_bank": {"macro", "geopolitics", "growth", "energy"},
    "iea": {"oil", "crude", "energy", "geopolitics"},
    "opec": {"oil", "crude", "energy", "geopolitics"},
}

CONCEPT_ALIASES = {
    "oil": {"oil", "wti", "crude", "brent", "energy", "petroleum", "eia"},
    "volatility": {"volatility", "volatile", "realized", "vol"},
    "recession": {"recession", "slowdown", "cycle", "growth"},
    "yield": {"yield", "curve", "rates", "treasury", "fed", "policy"},
    "geopolitics": {"geopolitics", "geopolitical", "war", "opec", "sanction", "tariff"},
    "inflation": {"inflation", "prices", "cpi", "pce"},
    "labor": {"labor", "jobs", "payroll", "wages", "unemployment"},
}


def _normalise_words(text: str) -> set[str]:
    words = {match.group(0).lower().strip("'") for match in WORD_RE.finditer(str(text or ""))}
    return {word for word in words if word not in STOPWORDS}


def _draft_from_packet(packet_or_draft: dict[str, Any]) -> dict[str, Any]:
    if isinstance(packet_or_draft.get("canonical_article_draft"), dict):
        return packet_or_draft["canonical_article_draft"]
    return packet_or_draft


def _article_text(draft: dict[str, Any]) -> str:
    parts = [
        str(draft.get("title") or ""),
        str(draft.get("subtitle") or ""),
        str(draft.get("dek") or ""),
        str(draft.get("meta_description") or ""),
        str(draft.get("thesis") or ""),
        str(draft.get("intro") or ""),
    ]
    for section in draft.get("sections") or []:
        if isinstance(section, dict):
            parts.append(str(section.get("title") or ""))
            parts.append(str(section.get("body") or ""))
    parts.append(str(draft.get("conclusion") or ""))
    return "\n".join(part for part in parts if part)


def _section_titles(draft: dict[str, Any]) -> list[str]:
    return [
        str(section.get("title") or "")
        for section in draft.get("sections") or []
        if isinstance(section, dict) and str(section.get("title") or "").strip()
    ]


def _urls_from_value(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [match.group(0).rstrip(".,;:)") for match in URL_RE.finditer(value)]
    if isinstance(value, dict):
        urls: list[str] = []
        for item in value.values():
            urls.extend(_urls_from_value(item))
        return urls
    if isinstance(value, list):
        urls = []
        for item in value:
            urls.extend(_urls_from_value(item))
        return urls
    return []


def _host(url: str) -> str:
    try:
        return urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def _url_text(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    raw = f"{parsed.netloc} {parsed.path} {parsed.query}"
    return urllib.parse.unquote(raw).replace("_", " ").replace("-", " ").lower()


def _source_family(url: str) -> str:
    host = _host(url)
    for family, pattern in SOURCE_FAMILY_RULES:
        if pattern.search(host):
            return family
    if host.endswith("yahoo.com") or host.endswith("finance.yahoo.com"):
        return "yahoo_finance"
    parts = host.split(".")
    return parts[-2] if len(parts) >= 2 else host or "unknown"


def _concepts_from_text(text: str) -> set[str]:
    low = str(text or "").lower()
    concepts: set[str] = set()
    for concept, aliases in CONCEPT_ALIASES.items():
        if any(re.search(rf"\b{re.escape(alias)}\b", low) for alias in aliases):
            concepts.add(concept)
    return concepts


def _expected_concepts(packet_or_draft: dict[str, Any], topic: str | None) -> set[str]:
    draft = _draft_from_packet(packet_or_draft)
    source_context = ""
    if isinstance(packet_or_draft.get("source_context_packet"), dict):
        source_context = json.dumps(packet_or_draft["source_context_packet"], sort_keys=True)
    base = " ".join([
        str(topic or ""),
        str(draft.get("title") or ""),
        str(draft.get("subtitle") or ""),
        str(draft.get("dek") or ""),
        str(draft.get("meta_description") or ""),
        str(draft.get("thesis") or ""),
        source_context,
    ])
    concepts = _concepts_from_text(base)
    return concepts or _concepts_from_text(_article_text(draft))


def _collect_source_urls(packet_or_draft: dict[str, Any]) -> dict[str, set[str]]:
    draft = _draft_from_packet(packet_or_draft)
    fields: dict[str, set[str]] = {}

    def add(field: str, url: str) -> None:
        clean = str(url or "").strip().rstrip(".,;:)")
        if clean:
            fields.setdefault(clean, set()).add(field)

    for url in _urls_from_value(draft.get("citations")):
        add("canonical_article_draft.citations", url)
    for url in _urls_from_value(draft.get("source_notes_for_operator")):
        add("canonical_article_draft.source_notes_for_operator", url)
    for item in draft.get("source_trail") or []:
        if isinstance(item, dict):
            for url in _urls_from_value(item.get("url")):
                add("canonical_article_draft.source_trail", url)
    if isinstance(packet_or_draft.get("research_grounding_packet"), dict):
        for url in _urls_from_value(packet_or_draft["research_grounding_packet"].get("cited_source_notes")):
            add("research_grounding_packet.cited_source_notes", url)
    return fields


def _url_relevance(url: str, expected_concepts: set[str], topic_terms: set[str]) -> tuple[str, list[str], str]:
    family = _source_family(url)
    family_concepts = PRIMARY_SOURCE_CONCEPTS.get(family, set())
    if family_concepts & expected_concepts:
        return "SUPPORTS_TOPIC", sorted(family_concepts & expected_concepts), family

    text_words = _normalise_words(_url_text(url))
    matched_words = sorted((text_words & topic_terms) | (text_words & set().union(*CONCEPT_ALIASES.values())))
    matched_concepts = sorted(_concepts_from_text(_url_text(url)) & expected_concepts)
    if matched_concepts or len(text_words & topic_terms) >= 2:
        return "SUPPORTS_TOPIC", sorted(set(matched_words) | set(matched_concepts)), family
    return "UNRELATED_TO_THESIS", [], family


def _audit_sources(packet_or_draft: dict[str, Any], topic: str | None) -> dict[str, Any]:
    draft = _draft_from_packet(packet_or_draft)
    text_for_terms = " ".join([
        str(topic or ""),
        str(draft.get("title") or ""),
        str(draft.get("subtitle") or ""),
        str(draft.get("thesis") or ""),
        str(draft.get("dek") or ""),
    ])
    topic_terms = _normalise_words(text_for_terms)
    expected_concepts = _expected_concepts(packet_or_draft, topic)
    url_fields = _collect_source_urls(packet_or_draft)

    audited_urls: list[dict[str, Any]] = []
    irrelevant: list[dict[str, Any]] = []
    relevant_families: set[str] = set()
    for url, fields in sorted(url_fields.items()):
        status, matched_terms, family = _url_relevance(url, expected_concepts, topic_terms)
        item = {
            "url": url,
            "fields": sorted(fields),
            "domain": _host(url),
            "source_family": family,
            "relevance_status": status,
            "matched_terms": matched_terms,
        }
        audited_urls.append(item)
        if status == "SUPPORTS_TOPIC":
            relevant_families.add(family)
        else:
            irrelevant.append(item)

    source_trail = draft.get("source_trail") or []
    generic_source_claims = [
        str(item.get("claim_supported") or "").lower()
        for item in source_trail
        if isinstance(item, dict)
    ]
    claims_too_generic = bool(
        generic_source_claims
        and all("operator_review_required" in claim or "claim review required" in claim for claim in generic_source_claims)
    )
    return {
        "expected_concepts": sorted(expected_concepts),
        "audited_urls": audited_urls,
        "irrelevant_urls": irrelevant,
        "relevant_source_families": sorted(relevant_families),
        "relevant_source_family_count": len(relevant_families),
        "source_trail_count": len(source_trail),
        "source_trail_claims_too_generic": claims_too_generic,
    }


def _audit_seo(packet_or_draft: dict[str, Any], topic: str | None) -> dict[str, Any]:
    draft = _draft_from_packet(packet_or_draft)
    seo_packet = packet_or_draft.get("seo_packet") if isinstance(packet_or_draft.get("seo_packet"), dict) else {}
    title = str(draft.get("title") or "")
    slug = str(draft.get("slug_candidate") or "")
    dek = str(draft.get("dek") or "")
    meta = str(draft.get("meta_description") or seo_packet.get("meta_description") or "")
    target_keyword = str(seo_packet.get("target_keyword") or "").strip().lower()
    keyword_text = " ".join([target_keyword, title, slug, dek, meta])
    expected_concepts = _expected_concepts(packet_or_draft, topic)
    keyword_concepts = _concepts_from_text(keyword_text)
    missing_fields = [
        name for name, value in {
            "title": title,
            "slug_candidate": slug,
            "dek": dek,
            "meta_description": meta,
        }.items()
        if not value.strip()
    ]
    target_keyword_weak = bool(
        not target_keyword
        or target_keyword in WEAK_SEO_KEYWORDS
        or (len(target_keyword.split()) == 1 and not keyword_concepts)
    )
    aligned = bool((keyword_concepts & expected_concepts) or not expected_concepts)
    return {
        "missing_fields": missing_fields,
        "target_keyword": target_keyword,
        "target_keyword_weak": target_keyword_weak,
        "keyword_concepts": sorted(keyword_concepts),
        "expected_concepts": sorted(expected_concepts),
        "keyword_aligned": aligned and not target_keyword_weak,
        "meta_description_length": len(meta),
    }


def _audit_structure(draft: dict[str, Any]) -> dict[str, Any]:
    text = _article_text(draft).lower()
    headings = " ".join(_section_titles(draft)).lower()
    checks = {
        "clear_news_hook": bool(re.search(r"\b(latest|current|recent|now|today|2026|fresh)\b", text[:2500])),
        "why_now": bool(re.search(r"\b(why|now|current|latest|recent|through 2026|as of|on 2026)\b", text[:3500])),
        "evidence": bool(re.search(r"\b(source|reported|fred|eia|data|observation|according)\b", text) and re.search(r"\d", text)),
        "counterargument_or_limits": bool(re.search(r"\b(does not prove|not sufficient|limits?|uncertainty|however|but|weaker|stronger)\b", text)),
        "what_to_watch_next": bool(re.search(r"\b(watch|monitor|what to watch|next|would strengthen|would weaken|if a later)\b", text + " " + headings)),
    }
    return {
        "checks": checks,
        "missing": [name for name, passed in checks.items() if not passed],
        "section_count": len(_section_titles(draft)),
    }


def _audit_tone(draft: dict[str, Any]) -> dict[str, Any]:
    public_text = _article_text(draft).lower()
    hits = []
    for label, pattern in PIPELINE_INTERNAL_PATTERNS.items():
        matches = re.findall(pattern, public_text, flags=re.IGNORECASE)
        if matches:
            hits.append({"term": label, "count": len(matches)})
    return {
        "pipeline_internal_language_hits": hits,
        "pipeline_internal_language_count": sum(item["count"] for item in hits),
    }


def _needs_source_diversity(packet_or_draft: dict[str, Any], topic: str | None) -> bool:
    concepts = _expected_concepts(packet_or_draft, topic)
    return bool({"recession", "yield", "geopolitics", "inflation", "labor"} & concepts)


def audit_editorial_quality_packet(packet_or_draft: dict[str, Any], *, topic: str | None = None) -> dict[str, Any]:
    """Return editorial acceptance status without changing dispatch status."""
    draft = _draft_from_packet(packet_or_draft)
    source_audit = _audit_sources(packet_or_draft, topic)
    seo_audit = _audit_seo(packet_or_draft, topic)
    structure_audit = _audit_structure(draft)
    tone_audit = _audit_tone(draft)

    blockers: list[str] = []
    review_items: list[str] = []

    citation_irrelevant = [
        item for item in source_audit["irrelevant_urls"]
        if "canonical_article_draft.citations" in item["fields"]
    ]
    source_note_irrelevant = [
        item for item in source_audit["irrelevant_urls"]
        if (
            "canonical_article_draft.source_notes_for_operator" in item["fields"]
            or "research_grounding_packet.cited_source_notes" in item["fields"]
        )
    ]
    if citation_irrelevant:
        blockers.append(
            "irrelevant_citation_urls:"
            + ",".join(item["url"] for item in citation_irrelevant[:5])
        )
    if source_note_irrelevant:
        blockers.append(
            "irrelevant_source_note_urls:"
            + ",".join(item["url"] for item in source_note_irrelevant[:5])
        )
    if source_audit["source_trail_claims_too_generic"]:
        blockers.append("source_trail_claims_too_generic")
    if source_audit["source_trail_count"] < 3:
        blockers.append(f"source_trail_too_thin:{source_audit['source_trail_count']}<3")

    if seo_audit["missing_fields"]:
        blockers.append("seo_fields_missing:" + ",".join(seo_audit["missing_fields"]))
    if seo_audit["meta_description_length"] < 110:
        blockers.append(f"seo_meta_description_too_short:{seo_audit['meta_description_length']}<110")
    if not seo_audit["keyword_aligned"]:
        review_items.append("seo_target_keyword_not_topic_aligned")

    if structure_audit["missing"]:
        review_items.append("tier1_structure_missing:" + ",".join(structure_audit["missing"]))

    if _needs_source_diversity(packet_or_draft, topic) and source_audit["relevant_source_family_count"] < 3:
        review_items.append(
            f"source_diversity_too_narrow:{source_audit['relevant_source_family_count']}<3"
        )

    if tone_audit["pipeline_internal_language_count"] >= 3:
        review_items.append(
            f"public_body_pipeline_internal_language:{tone_audit['pipeline_internal_language_count']}"
        )

    if blockers:
        classification = EDITORIAL_BLOCKED
    elif review_items:
        classification = EDITORIAL_NEEDS_REVIEW
    else:
        classification = EDITORIAL_APPROVED

    return {
        "schema_version": SCHEMA_VERSION,
        "classification": classification,
        "tier1_editorial_approved": classification == EDITORIAL_APPROVED,
        "dispatch_status_independent": True,
        "blockers": blockers,
        "review_items": review_items,
        "source_relevance_audit": source_audit,
        "seo_audit": seo_audit,
        "tier1_structure_audit": structure_audit,
        "public_body_tone_audit": tone_audit,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit V6 article editorial acceptance.")
    parser.add_argument("packet", help="Path to canonical article packet JSON")
    parser.add_argument("--topic", default=None)
    args = parser.parse_args(argv)
    data = json.loads(Path(args.packet).read_text(encoding="utf-8"))
    print(json.dumps(audit_editorial_quality_packet(data, topic=args.topic), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
