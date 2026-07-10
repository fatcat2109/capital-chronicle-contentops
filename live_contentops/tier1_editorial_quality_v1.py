"""Tier-1 reader-facing editorial and SEO audit with a local comparison fixture."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


SCHEMA_VERSION = "contentops.tier1_editorial_quality.v1"
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
    quote_count = len(re.findall(r"[\"“][^\"”]{18,}[\"”]", rendered))
    source_urls = sorted(set(URL_RE.findall(rendered)))
    media_ids = [str(item.get("asset_id") or item.get("media_asset_id") or "") for item in media_assets]

    editorial_checks = {
        "lede_what_changed": bool(re.search(r"\b3\.62%\b", opening) and re.search(r"2026-07-08", opening)),
        "lede_why_now": bool(re.search(r"\b(latest|on 2026-07-08|now|new reading)\b", opening, re.IGNORECASE)),
        "lede_market_consequence": bool(re.search(r"\b(markets?|cash|funding|yield|curve|treasur|policy transmission)\b", opening, re.IGNORECASE)),
        "concise_nut_graf": bool(re.search(r"\b(the distinction|the issue|what matters|the signal)\b", opening, re.IGNORECASE)),
        "mode_declared": str(article.get("editorial_mode") or "") in {"straight_news", "analysis", "explainer"},
        "mechanism_present": bool(re.search(r"\b(volume-weighted|overnight unsecured|policy corridor|transmission)\b", rendered, re.IGNORECASE)),
        "context_present": bool(re.search(r"\b(liquidity|issuance|treasury|term premium|cross-asset|foreign exchange|credit)\b", rendered, re.IGNORECASE)),
        "confirmation_condition": bool(re.search(r"\b(would confirm|confirmation would|confirm the)\b", closing, re.IGNORECASE)),
        "falsification_condition": bool(re.search(r"\b(would challenge|would weaken|would falsify|challenge the)\b", closing, re.IGNORECASE)),
        "named_next_catalysts": bool(re.search(r"\b(FOMC|CPI|payrolls|Treasury auction|SOFR|reserve balances|facility usage)\b", closing, re.IGNORECASE)),
        "no_process_language": not process_hits,
        "no_fabricated_quotes": quote_count == 0 or bool(article.get("quote_source_records")),
        "no_financial_advice": not advice_hits,
        "single_caveat": caveat_count <= 1,
        "high_information_density": not filler_hits and duplicate_sentences == 0 and 550 <= _word_count(body) <= 1400,
    }
    editorial_score = round(100 * sum(editorial_checks.values()) / len(editorial_checks))

    title = _normalise(str(article.get("title") or ""))
    seo_title = _normalise(str(article.get("seo_title") or ""))
    meta = _normalise(str(article.get("meta_description") or ""))
    slug = str(article.get("slug") or article.get("slug_candidate") or "")
    subtitle = _normalise(str(article.get("subtitle") or article.get("dek") or ""))
    visual_ids = VISUAL_RE.findall(body)
    seo_checks = {
        "reader_headline": 35 <= len(title) <= 90 and "3.62%" in title,
        "seo_title": 35 <= len(seo_title) <= 70 and "fed funds" in seo_title.casefold(),
        "slug": bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug)) and "fed" in slug,
        "meta_description": 110 <= len(meta) <= 165 and "3.62%" in meta,
        "canonical_url_metadata": str(article.get("canonical_url") or "").startswith("https://"),
        "primary_topic_in_opening": "effective federal funds" in opening.casefold(),
        "semantic_keyword_coverage": all(term in rendered.casefold() for term in ("policy corridor", "treasury", "sofr")),
        "heading_hierarchy": len(re.findall(r"^##\s+", body, flags=re.MULTILINE)) >= 4 and not re.search(r"^#\s+", body, flags=re.MULTILINE),
        "source_reference_links": len(source_urls) >= 3,
        "chart_metadata": len(media_assets) >= 3 and all(item.get("caption") and item.get("alt_text") for item in media_assets),
        "social_og_lead_media": bool(article.get("social_og_media_asset_id") in media_ids),
        "title_dek_not_duplicated": bool(subtitle and title.casefold() != subtitle.casefold()),
        "clean_rendered_body": "[[VISUAL:" not in rendered and not process_hits,
        "visual_markers_complete": visual_ids == ["primary", "policy_corridor", "sofr_context"],
    }
    seo_score = round(100 * sum(seo_checks.values()) / len(seo_checks))
    blockers = [name for name, passed in editorial_checks.items() if not passed]
    seo_blockers = [name for name, passed in seo_checks.items() if not passed]
    return {
        "schema_version": SCHEMA_VERSION,
        "classification": "PASS" if editorial_score >= 85 and seo_score >= 85 and not process_hits else "NEEDS_REVISION",
        "editorial_score": editorial_score,
        "seo_score": seo_score,
        "word_count": _word_count(body),
        "process_language_hits": process_hits,
        "filler_hits": filler_hits,
        "caveat_count": caveat_count,
        "duplicated_sentence_count": duplicate_sentences,
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
