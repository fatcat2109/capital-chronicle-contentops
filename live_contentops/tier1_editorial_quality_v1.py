"""Tier-1 reader-facing editorial and SEO audit with a local comparison fixture."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


SCHEMA_VERSION = "contentops.tier1_editorial_quality.v2"
SUPPORTED_ARTICLE_MODES = {"straight_news", "data_release", "policy_decision", "market_move", "explainer", "deep_analysis", "scenario_outlook", "analysis"}
ANALYSIS_MODES = {"deep_analysis", "scenario_outlook"}
HEADLINE_MAX_LENGTHS = {"reader": 95, "seo": 70, "social": 120, "push": 70, "youtube_community": 100}
PROCESS_LANGUAGE_PATTERNS = (
    r"\bthe editorial task\b",
    r"\bthe reporting discipline\b",
    r"\bin a serious financial-news report\b",
    r"\bthe editorial value\b",
    r"\bthe schedule and sidecars\b",
    r"\bthe chart manifest\b",
    r"\beditors should look\b",
    r"\bthe newsroom standard\b",
    r"\bcontentops\b",
    r"\bprompt\b",
    r"\bpipeline\b",
)
FILLER_PATTERNS = (
    r"\bthe point is not to predict the next tick\b",
    r"\bthe productive question is\b",
    r"\bthe editorial task is\b",
    r"\bthe reporting discipline is\b",
)
ADVICE_PATTERNS = (
    r"\byou should (?:buy|sell|short|hold)\b",
    r"\bguaranteed return\b",
    r"\bmust buy\b",
)
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
URL_RE = re.compile(r"https?://[^\s)]+")
VISUAL_RE = re.compile(r"\[\[VISUAL:([^\]]+)\]\]")
LLM_REVIEW_CHECKS = (
    "clear_news_peg",
    "why_now",
    "material_market_consequence",
    "concise_nut_graf",
    "mode_consistent",
    "source_backed_mechanism",
    "relevant_context",
    "specific_confirmation_condition",
    "specific_falsification_condition",
    "reader_facing_prose",
    "no_unsupported_certainty",
    "no_fabricated_quotes",
    "no_financial_advice",
    "high_information_density",
)


def _normalise(value: str) -> str:
    return " ".join(str(value or "").split())


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def rendered_body(markdown: str) -> str:
    body = VISUAL_RE.sub("", str(markdown or ""))
    body = re.sub(r"^#{1,6}\s+", "", body, flags=re.MULTILINE)
    body = re.sub(r"[*_`]", "", body)
    return re.sub(r"\n{3,}", "\n\n", body).strip()


def _sentences(markdown: str) -> list[str]:
    plain = _normalise(rendered_body(markdown))
    return [item.strip() for item in SENTENCE_RE.split(plain) if item.strip()]


def _pattern_hits(text: str, patterns: Sequence[str]) -> list[str]:
    return [pattern for pattern in patterns if re.search(pattern, text, flags=re.IGNORECASE)]


def _duplicate_sentence_count(markdown: str) -> int:
    seen: set[str] = set()
    duplicates = 0
    for sentence in _sentences(markdown):
        key = re.sub(r"[^a-z0-9]+", " ", sentence.casefold()).strip()
        if len(key) < 45:
            continue
        if key in seen:
            duplicates += 1
        seen.add(key)
    return duplicates


def _word_count(markdown: str) -> int:
    return len(re.findall(r"\b[A-Za-z0-9][A-Za-z0-9'-]*\b", rendered_body(markdown)))


def _paragraph_redundancy(markdown: str) -> list[dict[str, Any]]:
    paragraphs = [re.sub(r"^#{1,6}\s+", "", value).strip() for value in str(markdown or "").split("\n\n")]
    paragraphs = [value for value in paragraphs if value and not VISUAL_RE.fullmatch(value)]
    findings: list[dict[str, Any]] = []
    for index, left in enumerate(paragraphs):
        left_terms = set(re.findall(r"[a-z0-9]{4,}", left.casefold()))
        if len(left_terms) < 6:
            continue
        for right_index in range(index + 1, len(paragraphs)):
            right_terms = set(re.findall(r"[a-z0-9]{4,}", paragraphs[right_index].casefold()))
            overlap = len(left_terms & right_terms) / max(1, len(left_terms | right_terms))
            if overlap >= 0.72:
                findings.append({"paragraph_a": index + 1, "paragraph_b": right_index + 1, "token_overlap": round(overlap, 3)})
    return findings


def evaluate_headline_desk(article: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate supplied packaging variants; no variant conveys publication permission."""
    variants = {
        "reader": article.get("title"), "seo": article.get("seo_title"), "social": article.get("social_headline"),
        "push": article.get("push_headline"), "youtube_community": article.get("youtube_community_headline"),
    }
    keyword = str(article.get("seo_primary_keyword") or "").casefold()
    results = []
    for channel, raw in variants.items():
        text = _normalise(str(raw or ""))
        checks = {
            "present": bool(text), "length": bool(text) and len(text) <= HEADLINE_MAX_LENGTHS[channel],
            "specificity": bool(re.search(r"\d|%|\b[A-Z]{2,}\b", text)) or len(text.split()) >= 5,
            "search_intent": channel != "seo" or bool(keyword and keyword in text.casefold()),
            "no_clickbait": not bool(re.search(r"\b(shocking|you won.t believe|guaranteed|secret)\b", text, re.I)),
            "no_mismatch": not bool(re.search(r"\b(always|never|proves)\b", text, re.I)),
        }
        rejected = [name for name, passed in checks.items() if not passed]
        results.append({"channel": channel, "text": text, "score": round(100 * sum(checks.values()) / len(checks)), "checks": checks, "rejection_reasons": rejected})
    return {"schema_version": SCHEMA_VERSION, "publication_authority": False, "variants": results, "rejected_variant_count": sum(bool(row["rejection_reasons"]) for row in results)}


def _all_terms_present(text: str, terms: Sequence[str]) -> bool:
    lowered = text.casefold()
    return bool(terms) and all(str(term).casefold() in lowered for term in terms)


def audit_tier1_article(
    article: Mapping[str, Any],
    *,
    media_assets: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    body = str(article.get("substack_body_markdown") or article.get("body_markdown") or "")
    rendered = str(article.get("rendered_body") or rendered_body(body))
    opening = _normalise(rendered)[:900]
    closing = _normalise(rendered)[-1600:]
    process_hits = _pattern_hits(rendered, PROCESS_LANGUAGE_PATTERNS)
    filler_hits = _pattern_hits(rendered, FILLER_PATTERNS)
    advice_hits = _pattern_hits(rendered, ADVICE_PATTERNS)
    caveat_count = len(re.findall(r"not financial advice", rendered, flags=re.IGNORECASE))
    duplicate_sentences = _duplicate_sentence_count(body)
    paragraph_redundancy = _paragraph_redundancy(body)
    mode = str(article.get("editorial_mode") or article.get("article_mode") or "")
    original_value = dict(article.get("original_value") or {})
    quote_count = len(re.findall(r"[\"“][^\"”]{18,}[\"”]", rendered))
    source_urls = sorted(set(URL_RE.findall(rendered)))
    media_ids = [str(item.get("asset_id") or item.get("media_asset_id") or "") for item in media_assets]
    news_peg_terms = list(article.get("news_peg_terms") or ["3.62%", "2026-07-08"])
    market_consequence_terms = list(
        article.get("market_consequence_terms")
        or ["market", "cash", "funding", "yield", "curve", "treasury", "policy transmission"]
    )
    primary_topic = str(article.get("primary_topic") or "effective federal funds")
    seo_primary_keyword = str(article.get("seo_primary_keyword") or "fed funds")
    semantic_terms = list(article.get("seo_semantic_terms") or ["policy corridor", "treasury", "sofr"])
    expected_visual_ids = list(article.get("visual_asset_ids_expected") or ["primary", "policy_corridor", "sofr_context"])
    mechanism_terms = list(article.get("mechanism_terms") or ["volume-weighted", "overnight unsecured", "policy corridor", "transmission"])
    catalyst_terms = list(article.get("named_catalyst_terms") or ["FOMC", "CPI", "payrolls", "Treasury auction", "SOFR", "reserve balances", "facility usage"])

    editorial_checks = {
        "lede_what_changed": _all_terms_present(opening, news_peg_terms),
        "lede_why_now": bool(re.search(r"\b(latest|raised|released|on (?:january|february|march|april|may|june|july|august|september|october|november|december|20\d\d)|now|new reading|new forecast)\b", opening, re.IGNORECASE)),
        "lede_market_consequence": any(term.casefold() in opening.casefold() for term in market_consequence_terms),
        "concise_nut_graf": bool(re.search(r"\b(the distinction|the issue|what matters|the signal)\b", opening, re.IGNORECASE)),
        "mode_declared": mode in SUPPORTED_ARTICLE_MODES,
        "mode_rubric": (mode not in {"market_move", "data_release", "policy_decision"} or bool(article.get("as_of_utc"))) and (mode not in ANALYSIS_MODES or all(original_value.get(key) for key in ("original_value_type", "original_value_description", "methodology", "limitations"))),
        "original_value_claim_support": mode not in ANALYSIS_MODES or bool(original_value.get("supporting_claim_ids")),
        "mechanism_present": any(term.casefold() in rendered.casefold() for term in mechanism_terms),
        "context_present": bool(re.search(r"\b(liquidity|issuance|treasury|term premium|cross-asset|foreign exchange|credit)\b", rendered, re.IGNORECASE)),
        "confirmation_condition": bool(re.search(r"\b(would confirm|confirmation would|confirm the)\b", closing, re.IGNORECASE)),
        "falsification_condition": bool(re.search(r"\b(would (?:be )?challeng|would weaken|would falsify|challenge the)\b", closing, re.IGNORECASE)),
        "named_next_catalysts": sum(term.casefold() in closing.casefold() for term in catalyst_terms) >= min(2, len(catalyst_terms)),
        "no_process_language": not process_hits,
        "no_fabricated_quotes": quote_count == 0 or bool(article.get("quote_source_records")),
        "no_financial_advice": not advice_hits,
        "single_caveat": caveat_count <= 1,
        "high_information_density": not filler_hits and duplicate_sentences == 0 and not paragraph_redundancy and _word_count(body) >= 300,
    }
    editorial_score = round(100 * sum(editorial_checks.values()) / len(editorial_checks))

    title = _normalise(str(article.get("title") or ""))
    seo_title = _normalise(str(article.get("seo_title") or ""))
    meta = _normalise(str(article.get("meta_description") or ""))
    slug = str(article.get("slug") or article.get("slug_candidate") or "")
    subtitle = _normalise(str(article.get("subtitle") or article.get("dek") or ""))
    visual_ids = VISUAL_RE.findall(body)
    seo_checks = {
        "reader_headline": 35 <= len(title) <= 95 and seo_primary_keyword.casefold() in title.casefold(),
        "seo_title": 35 <= len(seo_title) <= 70 and seo_primary_keyword.casefold() in seo_title.casefold(),
        "slug": bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug)) and any(token in slug for token in re.findall(r"[a-z0-9]+", seo_primary_keyword.casefold())),
        "meta_description": 110 <= len(meta) <= 165,
        "canonical_url_metadata": str(article.get("canonical_url") or "").startswith("https://"),
        "primary_topic_in_opening": primary_topic.casefold() in opening.casefold(),
        "semantic_keyword_coverage": _all_terms_present(rendered, semantic_terms),
        "heading_hierarchy": len(re.findall(r"^##\s+", body, flags=re.MULTILINE)) >= 4 and not re.search(r"^#\s+", body, flags=re.MULTILINE),
        "source_reference_links": len(source_urls) >= 3,
        "chart_metadata": len(media_assets) >= 3 and all(item.get("caption") and item.get("alt_text") for item in media_assets),
        "social_og_lead_media": bool(article.get("social_og_media_asset_id") in media_ids),
        "title_dek_not_duplicated": bool(subtitle and title.casefold() != subtitle.casefold()),
        "clean_rendered_body": "[[VISUAL:" not in rendered and not process_hits,
        "visual_markers_complete": visual_ids == expected_visual_ids,
    }
    seo_score = round(100 * sum(seo_checks.values()) / len(seo_checks))
    headline_desk = evaluate_headline_desk(article)
    blockers = [name for name, passed in editorial_checks.items() if not passed]
    seo_blockers = [name for name, passed in seo_checks.items() if not passed]
    return {
        "schema_version": SCHEMA_VERSION,
        "classification": "PASS" if editorial_score >= 85 and seo_score >= 85 and not process_hits else "NEEDS_REVISION",
        "editorial_score": editorial_score,
        "seo_score": seo_score,
        "seo_hygiene_score": seo_score,
        "seo_hygiene_is_observed_search_performance": False,
        "word_count": _word_count(body),
        "process_language_hits": process_hits,
        "filler_hits": filler_hits,
        "caveat_count": caveat_count,
        "duplicated_sentence_count": duplicate_sentences,
        "paragraph_redundancy_findings": paragraph_redundancy,
        "headline_desk": headline_desk,
        "editorial_checks": editorial_checks,
        "seo_checks": seo_checks,
        "editorial_blockers": blockers,
        "seo_blockers": seo_blockers,
        "source_urls": source_urls,
        "visual_asset_ids": visual_ids,
        "rendered_body_sha256": _sha256(rendered),
    }


def build_llm_editorial_review_prompt(article: Mapping[str, Any]) -> str:
    """Build a bounded semantic review prompt with no publication authority."""
    review_input = {
        "title": str(article.get("title") or ""),
        "subtitle": str(article.get("subtitle") or article.get("dek") or ""),
        "seo_title": str(article.get("seo_title") or ""),
        "slug": str(article.get("slug") or article.get("slug_candidate") or ""),
        "meta_description": str(article.get("meta_description") or ""),
        "editorial_mode": str(article.get("editorial_mode") or ""),
        "rendered_body": str(article.get("rendered_body") or rendered_body(str(article.get("substack_body_markdown") or article.get("body_markdown") or ""))),
    }
    checks = ",".join(f'"{name}":true' for name in LLM_REVIEW_CHECKS)
    return "\n".join(
        [
            "You are a Capital Chronicle standards editor reviewing reader-facing financial journalism.",
            "Review only the supplied article. Do not add facts, infer market reactions, rewrite the story, or authorize publication.",
            "Mark a check false when support is ambiguous. Internal editorial/process/prompt/pipeline language is reader-facing failure.",
            "Generic watch lists do not satisfy confirmation or falsification checks; named observable catalysts or market conditions are required.",
            "Return JSON only, with exactly this top-level shape:",
            '{"decision":"PASS|NEEDS_REVISION","mode":"straight_news|analysis|explainer","checks":{'
            + checks
            + '},"issues":[{"code":"short_machine_code","evidence":"brief article evidence"}],"summary":"brief standards rationale"}',
            "Every listed check must appear as a JSON boolean. PASS requires every check to be true.",
            "ARTICLE:",
            json.dumps(review_input, ensure_ascii=True, sort_keys=True),
        ]
    )


def _parse_llm_review_json(raw: str | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(raw, Mapping):
        return dict(raw)
    value = str(raw or "").strip()
    if value.startswith("```"):
        value = re.sub(r"^```(?:json)?\s*", "", value, flags=re.IGNORECASE)
        value = re.sub(r"\s*```$", "", value)
    start, end = value.find("{"), value.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("llm_editorial_review_not_json_object")
    parsed = json.loads(value[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("llm_editorial_review_not_json_object")
    return parsed


def validate_llm_editorial_review(review: Mapping[str, Any]) -> dict[str, Any]:
    decision = str(review.get("decision") or "").upper()
    mode = str(review.get("mode") or "")
    source_checks = review.get("checks") if isinstance(review.get("checks"), Mapping) else {}
    checks = {name: source_checks.get(name) if isinstance(source_checks.get(name), bool) else None for name in LLM_REVIEW_CHECKS}
    missing_or_invalid = [name for name, value in checks.items() if value is None]
    failed = [name for name, value in checks.items() if value is False]
    issues = review.get("issues") if isinstance(review.get("issues"), list) else []
    valid = (
        decision in {"PASS", "NEEDS_REVISION"}
        and mode in {"straight_news", "analysis", "explainer"}
        and not missing_or_invalid
        and isinstance(review.get("summary"), str)
        and bool(str(review.get("summary") or "").strip())
    )
    effective_decision = "PASS" if valid and decision == "PASS" and not failed else "NEEDS_REVISION"
    normalized = {
        "status": "SUCCESS" if valid else "INVALID_LLM_REVIEW",
        "decision": effective_decision,
        "mode": mode,
        "checks": checks,
        "failed_checks": failed,
        "missing_or_invalid_checks": missing_or_invalid,
        "issues": issues,
        "summary": str(review.get("summary") or "").strip(),
    }
    normalized["review_sha256"] = _sha256(json.dumps(normalized, sort_keys=True))
    return normalized


def _load_dotenv_safely() -> None:
    path = Path(".env")
    if not path.exists():
        return
    try:
        from dotenv import load_dotenv
    except Exception:
        return
    load_dotenv(dotenv_path=path, override=False)


def _choose_llm_provider(requested: str) -> str:
    if requested and requested != "auto":
        return requested
    from .ai_provider_gate_v6 import inspect_provider_credentials

    present = inspect_provider_credentials()
    for env_name, provider in (
        ("NINE_ROUTER_API_KEY", "9router"),
        ("ANTHROPIC_API_KEY", "anthropic"),
        ("OPENAI_API_KEY", "openai"),
    ):
        if present.get(env_name):
            return provider
    raise RuntimeError("no_live_llm_editorial_reviewer_credentials_present")


def _default_llm_editorial_reviewer(prompt: str, provider: str) -> str:
    from .ai_research_canonical_article_engine_v6 import call_live_provider

    return call_live_provider(prompt, provider=provider, timeout_seconds=60)


def review_tier1_article_with_llm(
    article: Mapping[str, Any],
    *,
    llm_provider: str = "auto",
    llm_reviewer: Callable[[str, str], str | Mapping[str, Any]] = _default_llm_editorial_reviewer,
) -> dict[str, Any]:
    """Run one bounded semantic review; unavailable or malformed output fails closed."""
    prompt = build_llm_editorial_review_prompt(article)
    try:
        _load_dotenv_safely()
        provider = _choose_llm_provider(llm_provider)
        parsed = _parse_llm_review_json(llm_reviewer(prompt, provider))
        validated = validate_llm_editorial_review(parsed)
        return {
            **validated,
            "provider": provider,
            "prompt_sha256": _sha256(prompt),
            "publication_authority": False,
        }
    except Exception as exc:
        return {
            "status": "BLOCKED_LLM_EDITORIAL_REVIEW",
            "decision": "NEEDS_REVISION",
            "provider": str(llm_provider or "auto"),
            "prompt_sha256": _sha256(prompt),
            "error_class": type(exc).__name__,
            "publication_authority": False,
        }


def combine_editorial_gates(deterministic: Mapping[str, Any], llm_review: Mapping[str, Any]) -> dict[str, Any]:
    deterministic_pass = deterministic.get("classification") == "PASS"
    llm_pass = llm_review.get("status") == "SUCCESS" and llm_review.get("decision") == "PASS"
    blockers = []
    if not deterministic_pass:
        blockers.append("deterministic_tier1_or_seo_gate_failed")
    if not llm_pass:
        blockers.append("llm_semantic_editorial_gate_failed_or_unavailable")
    return {
        "classification": "PASS" if deterministic_pass and llm_pass else "NEEDS_REVISION",
        "deterministic_pass": deterministic_pass,
        "llm_semantic_pass": llm_pass,
        "llm_cannot_override_deterministic_blockers": True,
        "publication_authority": False,
        "blockers": blockers,
    }


def build_revised_fed_funds_candidate(
    original: Mapping[str, Any],
    *,
    media_assets: Sequence[Mapping[str, Any]],
    canonical_url: str,
) -> dict[str, Any]:
    body = """## The Overnight Rate Is Stable. The Curve Is Not

The effective federal funds rate was 3.62% on July 8, unchanged in practical terms from 3.63% a day earlier and comfortably inside the Federal Reserve's 3.50% to 3.75% target range. For markets, the new reading confirms that overnight policy implementation remains orderly even as longer Treasury yields continue to price a more complicated mix of inflation, fiscal supply and growth risk.

What matters is the separation between the policy anchor and the broader cost of capital. A well-contained overnight rate says the Fed's operating framework is transmitting its current setting. It does not say that financial conditions are unchanged across the yield curve, credit markets or foreign exchange.

[[VISUAL:primary]]

*The effective federal funds rate remained inside the Federal Reserve's target range through July 8. Source: [FRED DFF](https://fred.stlouisfed.org/series/DFF), [DFEDTARL](https://fred.stlouisfed.org/series/DFEDTARL), [DFEDTARU](https://fred.stlouisfed.org/series/DFEDTARU) and IORB.*

## Policy Transmission Is Working At The Short End

The effective federal funds rate is the volume-weighted median of overnight unsecured transactions between depository institutions. Its position within the target corridor is therefore a direct test of whether reserves and administered rates are keeping unsecured funding close to the Fed's intended policy setting.

The July 8 reading passes that test. At 3.62%, the effective rate stood 12 basis points above the lower bound and three basis points below the 3.65% interest rate on reserve balances. That relationship is consistent with an orderly implementation regime rather than a scramble for overnight liquidity.

The comparison matters because pressure in the overnight market would appear first through a persistent drift toward a corridor boundary, a widening gap against administered rates or a divergence from secured funding benchmarks. None of those signals can be inferred from the policy rate alone, but the current configuration gives investors a clean baseline for judging them.

[[VISUAL:policy_corridor]]

*The July 8 policy corridor: lower bound 3.50%, effective fed funds 3.62%, IORB 3.65% and upper bound 3.75%. Source: [Federal Reserve open-market operations](https://www.federalreserve.gov/monetarypolicy/openmarket.htm) and FRED.*

## Longer Yields Carry A Different Message

Stability in overnight funding has not prevented the Treasury curve from remaining elevated. On July 8, the two-year yield was 4.21%, the 10-year 4.56% and the 30-year 5.06%, while the Secured Overnight Financing Rate was 3.58%. The gap between those instruments and the effective fed funds rate reflects expectations extending well beyond the current operating setting.

Those longer yields absorb anticipated inflation, future policy, Treasury issuance and term premium. They can rise even when the overnight rate is steady, tightening mortgage, corporate and government borrowing conditions without any malfunction in the Fed's day-to-day implementation framework.

That distinction also clarifies the cross-asset signal. Credit spreads respond to refinancing and default risk; equities respond to discount rates and earnings expectations; foreign exchange responds to relative policy paths. A stable overnight benchmark is the anchor for those comparisons, not a verdict on their direction.

[[VISUAL:sofr_context]]

*DFF and SOFR compared with two-, 10- and 30-year Treasury yields on July 8. Source: [New York Fed SOFR](https://www.newyorkfed.org/markets/reference-rates/sofr) and FRED Treasury series.*

## What Would Confirm Or Challenge The Signal

Confirmation would be a continued DFF-IORB relationship near current levels, SOFR moving in step with unsecured funding and no abrupt increase in Federal Reserve facility usage. That would leave inflation data, Treasury auctions and the next FOMC communication as the more likely drivers of any curve repricing.

The signal would be challenged by a persistent move toward either target boundary, a material secured-unsecured funding gap or evidence that reserve balances are becoming unevenly distributed. A weak Treasury auction, a CPI surprise or a payrolls shock could still move longer yields, but that would be a macro or supply story rather than proof that overnight implementation had failed.

This article is for informational purposes only and is not financial advice.
"""
    return {
        **dict(original),
        "title": "Fed Funds Stay Anchored at 3.62% While Treasury Yields Signal Wider Pressure",
        "subtitle": "The overnight policy rate remains orderly inside the Fed's corridor, but the Treasury curve is carrying a separate inflation, supply and term-premium message.",
        "seo_title": "Fed Funds Rate at 3.62% as Treasury Yields Stay Elevated",
        "slug": "fed-funds-rate-3-62-treasury-yield-curve",
        "meta_description": "The effective fed funds rate held at 3.62% inside the Fed's target corridor, while Treasury yields reflected inflation, supply and term-premium risks.",
        "canonical_url": canonical_url,
        "editorial_mode": "analysis",
        "primary_topic": "effective federal funds rate",
        "social_og_media_asset_id": "primary",
        "substack_body_markdown": body,
        "rendered_body": rendered_body(body),
        "word_count": _word_count(body),
        "public_write_authorized": False,
    }


def build_grounded_oil_release_candidate(
    selection: Mapping[str, Any],
    *,
    source_packet: Mapping[str, Any],
    media_assets: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    if source_packet.get("status") != "PASS_OFFICIAL_EIA_RELEASE_GROUNDED":
        raise ValueError("official_eia_source_packet_required")
    if len(media_assets) < 3:
        raise ValueError("oil_article_requires_three_media_assets")
    facts = dict(source_packet.get("facts") or {})
    visual_ids = [str(item.get("asset_id") or "") for item in media_assets[:3]]
    if not all(visual_ids):
        raise ValueError("oil_article_media_asset_ids_required")
    primary = dict(media_assets[0])
    wti_value = float(primary.get("latest_observation_value"))
    wti_date = str(primary.get("latest_observation_date") or "")
    release_date = "July 7, 2026"
    eia_url = str(source_packet["source_url"])
    supporting = list(source_packet.get("supporting_source_urls") or [])
    steo_url = supporting[0]
    fred_url = supporting[1]
    fed_url = supporting[2]
    wpsr_url = supporting[3] if len(supporting) > 3 else "https://www.eia.gov/petroleum/supply/weekly/"
    brent_june = float(facts["brent_june_average_usd_per_barrel"])
    brent_q3 = float(facts["brent_q3_2026_forecast_usd_per_barrel"])
    brent_2027 = float(facts["brent_2027_forecast_usd_per_barrel"])
    gasoline_q3 = float(facts["gasoline_q3_2026_forecast_usd_per_gallon"])
    gasoline_q4 = float(facts["gasoline_q4_2026_forecast_usd_per_gallon"])
    wpsr_date = str(facts.get("next_weekly_petroleum_status_report_date") or "")
    steo_date = str(facts.get("next_steo_release_date") or "")
    wpsr_label = datetime.fromisoformat(wpsr_date).strftime("%B %d").replace(" 0", " ") if wpsr_date else "the next"
    steo_label = datetime.fromisoformat(steo_date).strftime("%B %d").replace(" 0", " ") if steo_date else "the next"
    title = "EIA Sees Oil Supply Nearing Pre-War Levels as Hormuz Flows Resume"
    subtitle = "The agency expects crude output and trade to recover near pre-conflict levels by year-end, shifting the market test from disruption to inventories and demand."
    seo_title = "EIA Oil Forecast: Hormuz Reopening Reshapes Supply"
    slug = re.sub(r"[^a-z0-9]+", "-", title.casefold()).strip("-")[:90].strip("-")
    canonical_url = f"https://capitalchronicle.substack.com/p/{slug}"
    meta = "EIA expects oil output and trade to approach pre-conflict levels by year-end as Hormuz flows resume, reshaping Brent, gasoline and inflation risks."
    captions = [
        f"{item.get('caption')} [Source]({item.get('source_page_url')})"
        for item in media_assets[:3]
    ]
    body = f"""## Oil Supply Is Returning Faster Than Feared

The U.S. Energy Information Administration raised its global oil production forecast on {release_date} after tanker traffic through the Strait of Hormuz increased following the June 18 U.S.-Iran memorandum. The agency now expects global crude output and trade flows to return near pre-conflict levels by year-end, with most shut-in production restored by the first quarter of 2027. For oil markets, the new forecast shifts the immediate question from physical disruption to whether supply recovery will outrun demand and rebuild inventories.

What matters is the speed of that transition. The EIA said Brent averaged ${brent_june:.0f} a barrel in June and forecast a ${brent_q3:.0f} third-quarter average, before easing toward ${brent_2027:.0f} in 2027. Those figures are forecasts rather than certainties, but they provide a measurable baseline for crude prices, inflation expectations and energy-sensitive assets. The complete official release is available from the [EIA]({eia_url}).

[[VISUAL:{visual_ids[0]}]]

*{captions[0]}*

## Reopened Flows Change The Price Mechanism

The Strait of Hormuz is a transit constraint as much as a production story. Reopening the route allows previously displaced barrels to reach refiners, reduces freight and insurance pressure, and makes the restoration of shut-in fields commercially useful. Supply can therefore recover before every damaged or idled facility is fully normalized.

The latest manifest-bound WTI observation was ${wti_value:.2f} a barrel on {wti_date}. That market price does not prove the EIA forecast, but it shows the level from which traders are testing the agency's supply assumptions. Confirmation would require rising tanker traffic, restored output and slower inventory withdrawals to persist together; a price decline without those physical signals would be less durable.

[[VISUAL:{visual_ids[1]}]]

*{captions[1]}*

## Cheaper Crude Helps Inflation, But Does Not Set Fed Policy

The EIA expects lower crude costs to pull U.S. gasoline prices down, forecasting about ${gasoline_q3:.2f} a gallon in the third quarter and ${gasoline_q4:.2f} in the fourth. That would ease a visible part of household inflation and reduce some transport and input costs for businesses.

The policy effect is narrower than the headline. The Federal Reserve's June statement said inflation remained elevated partly because of energy-related supply shocks, but officials still assess broader price persistence, labor conditions and expectations. Cheaper fuel can improve headline inflation without guaranteeing an equivalent move in core services or the policy rate. The relevant policy context is in the [June FOMC statement]({fed_url}), while the forecast tables remain in the [July Short-Term Energy Outlook]({steo_url}).

## The Cross-Asset Test Runs Through Inventories And The Curve

For bonds, a sustained energy retreat would reduce one source of near-term inflation compensation, although fiscal supply and underlying services inflation can keep longer yields elevated. For currencies, the effect depends on relative import exposure: large oil importers gain purchasing-power relief, while exporters face softer revenue. Energy equities split between producers exposed to lower realizations and refiners or transport-intensive companies that may benefit from cheaper feedstock and fuel.

The multi-year range matters because a forecast decline can still leave oil above prior-cycle averages. Investors should distinguish a normalization of the war premium from a collapse in underlying demand. That distinction determines whether lower prices signal successful supply repair or a broader growth slowdown.

[[VISUAL:{visual_ids[2]}]]

*{captions[2]}*

## What Would Confirm Or Challenge The Rebalance

Confirmation would come from continued Hormuz traffic normalization, restoration of shut-in production, inventory builds and Brent trading broadly in line with the EIA's declining forecast path. The next named catalysts are the [{wpsr_label} Weekly Petroleum Status Report]({wpsr_url}) and the [{steo_label} Short-Term Energy Outlook]({steo_url}), which can test both current balances and the agency's assumptions.

The thesis would be challenged by renewed disruption in the strait, slower field restarts, persistent inventory draws or prices holding materially above the forecast despite recovering volumes. Those outcomes would imply that logistics, demand or geopolitical risk remained tighter than the headline supply recovery suggests.

The WTI observations in this article come from [FRED series DCOILWTICO]({fred_url}), whose underlying source is the EIA. This article is for informational purposes only and is not financial advice.
"""
    return {
        "schema_version": SCHEMA_VERSION,
        "article_family": "oil",
        "title": title,
        "subtitle": subtitle,
        "seo_title": seo_title,
        "slug": slug,
        "meta_description": meta,
        "canonical_url": canonical_url,
        "editorial_mode": "analysis",
        "primary_topic": "Energy Information Administration raised its global oil production forecast",
        "seo_primary_keyword": "EIA",
        "seo_semantic_terms": ["Strait of Hormuz", "Brent", "oil production"],
        "news_peg_terms": ["EIA", "global oil production", "July 7, 2026"],
        "market_consequence_terms": ["oil markets", "Brent", "inflation", "bonds"],
        "mechanism_terms": ["transit constraint", "restoration of shut-in fields", "inventory"],
        "named_catalyst_terms": [f"{wpsr_label} Weekly Petroleum Status Report", f"{steo_label} Short-Term Energy Outlook"],
        "visual_asset_ids_expected": visual_ids,
        "social_og_media_asset_id": visual_ids[0],
        "source_trail": [eia_url, *supporting],
        "numeric_source_packet_sha256": source_packet.get("source_text_sha256"),
        "selection_rationale": selection.get("why_ranked"),
        "market_mechanism": "Reopened Hormuz transit, restored shut-in production and rebuilding inventories determine whether the supply recovery translates into a durable decline in crude prices.",
        "policy_context": "Lower gasoline prices can ease headline inflation, but Federal Reserve policy still depends on broader price persistence, labor conditions and inflation expectations.",
        "cross_asset_implications": "A sustained oil retreat can reduce near-term inflation compensation, support large energy importers and pressure producer revenues without guaranteeing lower long-term yields.",
        "social_lede": "EIA expects crude flows to approach pre-conflict levels by year-end.",
        "social_mechanism_summary": "Reopened Hormuz transit and restored output will test whether inventories rebuild and crude prices keep falling.",
        "social_policy_summary": "Cheaper gasoline can ease headline inflation without settling Federal Reserve policy.",
        "social_cross_asset_summary": "Lower oil can help energy importers while pressuring producer revenues.",
        "substack_body_markdown": body,
        "rendered_body": rendered_body(body),
        "word_count": _word_count(body),
        "public_write_authorized": False,
    }


def build_comparison_packet(
    context: Mapping[str, Any],
    *,
    canonical_url: str,
    llm_provider: str | None = None,
    llm_reviewer: Callable[[str, str], str | Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    original = dict(context["article"])
    original["canonical_url"] = canonical_url
    original["editorial_mode"] = "analysis"
    original["social_og_media_asset_id"] = "primary"
    media_assets = list((context.get("media") or {}).get("assets") or [])
    revised = build_revised_fed_funds_candidate(original, media_assets=media_assets, canonical_url=canonical_url)
    before = audit_tier1_article(original, media_assets=media_assets)
    after = audit_tier1_article(revised, media_assets=media_assets)
    llm_review = (
        review_tier1_article_with_llm(
            revised,
            llm_provider=llm_provider or "auto",
            llm_reviewer=llm_reviewer or _default_llm_editorial_reviewer,
        )
        if llm_provider is not None or llm_reviewer is not None
        else {
            "status": "NOT_RUN",
            "decision": "NEEDS_REVISION",
            "publication_authority": False,
        }
    )
    combined_gate = combine_editorial_gates(after, llm_review)
    removed = []
    original_body = str(original.get("substack_body_markdown") or "")
    revised_body = str(revised.get("substack_body_markdown") or "")
    for pattern in PROCESS_LANGUAGE_PATTERNS:
        match = re.search(pattern, original_body, flags=re.IGNORECASE)
        if match and not re.search(pattern, revised_body, flags=re.IGNORECASE):
            removed.append(match.group(0))
    return {
        "schema_version": SCHEMA_VERSION,
        "classification": "PASS_LOCAL_REVISED_CANDIDATE" if combined_gate["classification"] == "PASS" else "BLOCKED_REVISED_CANDIDATE_GATE",
        "public_write_performed": False,
        "canonical_article_modified": False,
        "original_audit": before,
        "revised_audit": after,
        "llm_semantic_review": llm_review,
        "combined_editorial_gate": combined_gate,
        "process_language_removed": removed,
        "word_count_reduction": before["word_count"] - after["word_count"],
        "retained_factual_claims": ["DFF 3.62% on 2026-07-08", "target range 3.50%-3.75%", "IORB 3.65%", "SOFR and Treasury curve observations"],
        "source_continuity": {
            "media_asset_ids": [item.get("asset_id") for item in media_assets],
            "media_sha256": {str(item.get("asset_id")): item.get("sha256") for item in media_assets},
            "all_three_visuals_retained": after["visual_asset_ids"] == ["primary", "policy_corridor", "sofr_context"],
        },
        "revised_candidate": revised,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local tier-1 editorial comparison packet.")
    parser.add_argument("context", type=Path)
    parser.add_argument("--canonical-url", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--llm-provider", default="auto")
    args = parser.parse_args(argv)
    context = json.loads(args.context.read_text(encoding="utf-8"))
    packet = build_comparison_packet(context, canonical_url=args.canonical_url, llm_provider=args.llm_provider)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(str(packet["revised_candidate"]["substack_body_markdown"]), encoding="utf-8")
    print(json.dumps({"classification": packet["classification"], "editorial_before": packet["original_audit"]["editorial_score"], "editorial_after": packet["revised_audit"]["editorial_score"], "seo_before": packet["original_audit"]["seo_score"], "seo_after": packet["revised_audit"]["seo_score"]}, sort_keys=True))
    return 0 if packet["classification"] == "PASS_LOCAL_REVISED_CANDIDATE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
