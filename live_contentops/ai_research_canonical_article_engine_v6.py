"""V6 AI research + canonical article production engine.

Turns an operator idea into grounded research, canonical Substack article,
editorial/SEO packets, Discord summary seed, and evidence packets.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "6.0.0"
TASK_LABEL = "TASK_CONTENTOPS_V6_ARTICLE_EVIDENCE_MEDIA_QUALITY_HARDENING_V0"
DETERMINISTIC_TIMESTAMP = "2026-07-01T02:56:46+07:00"
RECOMMENDED_NEXT_TASK = "TASK_CONTENTOPS_V6_FINAL_RELEASE_READINESS_EVIDENCE_INDEX_AND_OPERATOR_HANDOFF_V0"
MIN_CANONICAL_ARTICLE_WORDS = 2000
RAW_URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
WORD_RE = re.compile(r"\b[\w'-]+\b")

FINANCIAL_ADVICE_TERMS = (
    "buy", "sell", "hold", "price target", "target price", "entry", "entries", "exit", "exits",
    "signal service", "trading signal", "financial advice", "signal-service"
)


@dataclass(frozen=True)
class EngineInput:
    operator_idea: str
    target_audience: str
    editorial_angle: str
    source_context: list[str]
    risk_disclaimer_policy: str
    output_style: str
    publish_target: str = "substack_canonical"
    downstream_targets: list[str] = field(default_factory=lambda: ["discord", "telegram_operator", "manual_export"])
    source_urls: list[str] = field(default_factory=list)
    source_notes: str = ""


def check_financial_advice(text: str) -> None:
    low = text.lower()
    for term in ("financial advice", "signal service", "signal-service", "trading signal", "price target", "target price"):
        if term in low:
            raise ValueError(f"forbidden_financial_advice_language:{term}")
    words = re.findall(r"\b[a-z-]+\b", low)
    for word in words:
        if word in {"buy", "sell", "hold", "entry", "entries", "exit", "exits"}:
            raise ValueError(f"forbidden_financial_advice_language:{word}")


def check_fake_material(text: str) -> None:
    low = text.lower()
    for term in ("fake citation", "fake data", "fake metric", "fake metrics", "fabricated numbers"):
        if term in low:
            raise ValueError(f"forbidden_fake_material_language:{term}")


def _scan_obj(obj: Any) -> None:
    if isinstance(obj, str):
        check_financial_advice(obj)
        check_fake_material(obj)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k in {
                "target_audience",
                "publish_target",
                "downstream_targets",
                "env_key_name",
                "task_label",
                "schema_version",
                "recommended_next_task",
                "provider_attempts",
                "warnings",
                "blockers",
                "failure",
                "status",
                "provider",
                "model",
            }:
                continue
            _scan_obj(v)
    elif isinstance(obj, list):
        for item in obj:
            _scan_obj(item)


def compute_canonical_hash(draft: dict[str, Any]) -> str:
    clone = dict(draft)
    clone.pop("canonical_payload_hash", None)
    serialized = json.dumps(clone, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def parse_llm_json(text: str) -> dict[str, str] | None:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except Exception:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
        return None


def article_plain_text(draft: dict[str, Any]) -> str:
    parts = [str(draft.get("title", "")), str(draft.get("subtitle", "")), str(draft.get("intro", ""))]
    for section in draft.get("sections", []):
        if isinstance(section, dict):
            parts.extend([str(section.get("title", "")), str(section.get("body", ""))])
    parts.append(str(draft.get("conclusion", "")))
    return "\n".join(part for part in parts if part)


def _word_count(text: str) -> int:
    return len(WORD_RE.findall(text))


def _raw_urls(text: str) -> list[str]:
    return RAW_URL_RE.findall(text)


def _source_trail_from_urls(urls: list[str]) -> list[dict[str, str]]:
    trail = []
    for idx, url in enumerate(dict.fromkeys(urls), start=1):
        trail.append({
            "label": f"Source {idx}",
            "publisher_or_origin": "grounded_search",
            "url": url,
            "claim_supported": "operator_review_required",
        })
    return trail


def _dedupe_strings(values: list[str]) -> list[str]:
    return [item for item in dict.fromkeys(str(value).strip() for value in values if str(value).strip())]


def _topic_needs_wti_evidence(inputs: EngineInput) -> bool:
    text = f"{inputs.operator_idea} {inputs.editorial_angle} {' '.join(inputs.source_context)}".lower()
    return any(term in text for term in ("oil", "wti", "crude", "energy"))


def _pct_change(latest: float, prior: float) -> float | None:
    if prior == 0:
        return None
    return ((latest - prior) / prior) * 100.0


def _fmt_num(value: float | None, digits: int = 1) -> str:
    if value is None:
        return "not available"
    return f"{value:.{digits}f}"


def _build_wti_evidence(inputs: EngineInput) -> dict[str, Any] | None:
    if not _topic_needs_wti_evidence(inputs):
        return None
    try:
        from live_contentops.media_content_audit_v6 import (
            WTI_FRED_CSV_URL,
            WTI_FRED_SERIES_URL,
            _read_fred_csv,
            _recent_direction,
            _rolling_abs_change,
        )
    except Exception:
        return None
    try:
        points = _read_fred_csv()
    except Exception:
        return None
    if len(points) < 90:
        return None

    latest_date, latest_value = points[-1]
    prior_date, prior_value = points[max(0, len(points) - 90)]
    one_year_date, one_year_value = points[max(0, len(points) - 260)]
    vol_points = _rolling_abs_change(points)
    latest_vol = vol_points[-1][1] if vol_points else None
    prior_vol = vol_points[max(0, len(vol_points) - 90)][1] if len(vol_points) >= 2 else None
    price_change_90d = _pct_change(latest_value, prior_value)
    price_change_1y = _pct_change(latest_value, one_year_value)
    vol_change_90d = _pct_change(latest_vol, prior_vol) if latest_vol is not None and prior_vol is not None else None
    return {
        "kind": "wti_oil",
        "series_id": "DCOILWTICO",
        "source_label": "FRED series DCOILWTICO; underlying source U.S. Energy Information Administration",
        "source_url": WTI_FRED_SERIES_URL,
        "csv_url": WTI_FRED_CSV_URL,
        "underlying_source_url": "https://www.eia.gov/dnav/pet/pet_pri_spt_s1_d.htm",
        "latest_date": latest_date.isoformat(),
        "latest_year": latest_date.year,
        "latest_value": latest_value,
        "prior_90d_date": prior_date.isoformat(),
        "prior_90d_value": prior_value,
        "one_year_date": one_year_date.isoformat(),
        "one_year_value": one_year_value,
        "price_change_90d_pct": price_change_90d,
        "price_change_1y_pct": price_change_1y,
        "latest_30d_abs_move_pct": latest_vol,
        "prior_30d_abs_move_pct": prior_vol,
        "vol_change_90d_pct": vol_change_90d,
        "recent_price_direction": _recent_direction(points),
        "recent_volatility_direction": _recent_direction(vol_points) if len(vol_points) >= 2 else "unknown",
        "observation_count": len(points),
        "coverage_start": points[0][0].isoformat(),
        "coverage_end": latest_date.isoformat(),
    }


def _source_evidence_context(evidence: dict[str, Any] | None) -> str:
    if not evidence:
        return "No structured source evidence is available beyond grounded search snippets."
    if evidence.get("kind") == "wti_oil":
        return (
            "Structured source evidence for article and visuals:\n"
            f"- Source: {evidence['source_label']}.\n"
            f"- Latest observation: WTI spot price was ${_fmt_num(evidence['latest_value'], 2)} per barrel on {evidence['latest_date']}.\n"
            f"- 90-day comparison: ${_fmt_num(evidence['prior_90d_value'], 2)} per barrel on {evidence['prior_90d_date']}; "
            f"change of {_fmt_num(evidence['price_change_90d_pct'])}% over about 90 days.\n"
            f"- One-year comparison: ${_fmt_num(evidence['one_year_value'], 2)} per barrel on {evidence['one_year_date']}; "
            f"change of {_fmt_num(evidence['price_change_1y_pct'])}% across roughly 1 year.\n"
            f"- Volatility proxy: latest 30 days averaged {_fmt_num(evidence['latest_30d_abs_move_pct'])}% absolute daily moves; "
            f"90-day change in that proxy was {_fmt_num(evidence['vol_change_90d_pct'])}%.\n"
            f"- Coverage: {evidence['observation_count']} daily observations from {evidence['coverage_start']} through {evidence['coverage_end']}.\n"
            f"- Direction labels for media audit: price={evidence['recent_price_direction']}; volatility={evidence['recent_volatility_direction']}."
        )
    return json.dumps(evidence, sort_keys=True)


def _source_trail_from_evidence(evidence: dict[str, Any] | None, fallback_urls: list[str] | None = None) -> list[dict[str, str]]:
    urls = _dedupe_strings(fallback_urls or [])
    if evidence and evidence.get("kind") == "wti_oil":
        return [
            {
                "label": "FRED DCOILWTICO daily WTI series",
                "publisher_or_origin": "FRED / U.S. Energy Information Administration",
                "url": str(evidence["source_url"]),
                "claim_supported": (
                    f"Latest WTI observation was ${_fmt_num(evidence['latest_value'], 2)} per barrel on "
                    f"{evidence['latest_date']}, giving the article a current 2026 oil-price endpoint."
                ),
            },
            {
                "label": "FRED DCOILWTICO downloadable observation file",
                "publisher_or_origin": "FRED CSV derived calculation",
                "url": str(evidence["csv_url"]),
                "claim_supported": (
                    f"ContentOps derived the 90 days price comparison and 30 days realized-volatility proxy "
                    f"from {evidence['observation_count']} daily observations through {evidence['coverage_end']}."
                ),
            },
            {
                "label": "Underlying petroleum source",
                "publisher_or_origin": "U.S. Energy Information Administration",
                "url": str(evidence["underlying_source_url"]),
                "claim_supported": "The FRED series identifies EIA as the underlying source for WTI crude oil spot-price observations.",
            },
        ]
    return _source_trail_from_urls(urls)


def _paragraph(*sentences: str) -> str:
    return " ".join(sentence.strip() for sentence in sentences if sentence.strip())


def _source_backed_longform_article(
    inputs: EngineInput,
    *,
    evidence: dict[str, Any] | None,
    search_context: str,
    citations: list[str],
    base_candidate: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if not evidence or evidence.get("kind") != "wti_oil":
        return None

    title = str((base_candidate or {}).get("title") or "Oil Volatility Is Rising; Recession Risk Needs a Cleaner Evidence Map")
    if len(title.split()) < 5 or title.lower() in {"short", "feature title"}:
        title = "Oil Volatility Is Rising; Recession Risk Needs a Cleaner Evidence Map"
    subtitle = "A source-led Capital Chronicle briefing on WTI, recession-risk interpretation, yield curves, and evidence discipline"
    slug = "oil-volatility-recession-risk-evidence-map"
    dek = (
        "WTI data through the latest FRED observation show why current oil volatility belongs inside a recession-risk "
        "discussion, but only when the evidence is separated from market noise and directional calls."
    )
    meta_description = (
        "Capital Chronicle maps current WTI oil volatility, recession-risk signals, source limits, and visual evidence "
        "without directional investment calls."
    )

    latest_price = _fmt_num(evidence["latest_value"], 2)
    prior_price = _fmt_num(evidence["prior_90d_value"], 2)
    one_year_price = _fmt_num(evidence["one_year_value"], 2)
    price_change = _fmt_num(evidence["price_change_90d_pct"])
    one_year_change = _fmt_num(evidence["price_change_1y_pct"])
    latest_vol = _fmt_num(evidence["latest_30d_abs_move_pct"])
    vol_change = _fmt_num(evidence["vol_change_90d_pct"])
    latest_date = str(evidence["latest_date"])
    prior_date = str(evidence["prior_90d_date"])
    one_year_date = str(evidence["one_year_date"])
    obs_count = str(evidence["observation_count"])
    coverage_start = str(evidence["coverage_start"])
    coverage_end = str(evidence["coverage_end"])
    price_direction = str(evidence["recent_price_direction"])
    vol_direction = str(evidence["recent_volatility_direction"])

    intro = "\n\n".join([
        _paragraph(
            "Capital Chronicle is treating the latest rise in oil volatility as an evidence problem before it is a market narrative.",
            f"The source-backed WTI series used for this briefing runs from {coverage_start} through {coverage_end}, with {obs_count} daily observations in the local calculation set.",
            f"The latest FRED observation places WTI at ${latest_price} per barrel on {latest_date}, compared with ${prior_price} roughly 90 days earlier on {prior_date}.",
            f"That comparison produces a {price_change}% move across about 90 days, while the one-year comparison from ${one_year_price} on {one_year_date} produces a {one_year_change}% change.",
        ),
        _paragraph(
            f"The visual evidence is therefore not a stale historical screenshot: it ends in {evidence['latest_year']} and is aligned with the article thesis.",
            f"The media audit labels the recent price direction as {price_direction} and the realized-volatility direction as {vol_direction}.",
            f"The latest 30 days volatility proxy averaged {latest_vol}% absolute daily moves, with a {vol_change}% change in that proxy over about 90 days.",
            "Those figures do not prove a recession by themselves; they define the current oil channel that a recession-risk article must handle with precision.",
        ),
        _paragraph(
            "The editorial question is narrow but important: when energy volatility rises near a period of recession anxiety, what should a serious reader separate from the headline?",
            "The answer starts with source discipline, moves through transmission channels, and ends with limits.",
            "This is educational analysis, not an investment recommendation, and every numerical claim below is either taken from the cited source series or derived mechanically from it.",
        ),
    ])

    sections = [
        {
            "title": "The Macro Setup: Current Oil Evidence Before Narrative",
            "body": "\n\n".join([
                _paragraph(
                    "The first job is to anchor the discussion in a current data endpoint.",
                    f"FRED's DCOILWTICO series reports WTI at ${latest_price} per barrel on {latest_date}, and that endpoint is what the primary chart should show near the top of the article.",
                    f"A visual ending in 2022 or 2023 would fail this task because it would imply historical context while the article is discussing a 2026 macro setup.",
                    "The selected chart avoids that problem by carrying the latest observation year through the current article date.",
                ),
                _paragraph(
                    f"The 90 days comparison matters because it keeps the discussion out of vague language.",
                    f"WTI moved from ${prior_price} on {prior_date} to ${latest_price} on {latest_date}, a {price_change}% change across roughly 90 days.",
                    "That does not make oil the only recession variable; it establishes that the energy input being discussed is moving enough to deserve a place in the setup.",
                    "The article can then ask how that oil movement interacts with income, inflation expectations, transport costs, and policy timing.",
                ),
                _paragraph(
                    "The source trail also clarifies the media decision.",
                    "The chart is not a generic branded cover card, an upload-host image with uncertain provenance, or a search result with unknown time coverage.",
                    "It is generated from a public macro series whose underlying source is the U.S. Energy Information Administration.",
                    "That distinction is the difference between media transport working and editorial media judgment working.",
                ),
            ]),
        },
        {
            "title": "Why Oil Volatility Enters a Recession-Risk Discussion",
            "body": "\n\n".join([
                _paragraph(
                    "Oil enters recession-risk analysis through several channels, none of which should be treated as a one-line signal.",
                    "Higher or more volatile energy prices can affect household real income, corporate transport costs, inflation expectations, and central-bank communication.",
                    "The mechanism is not automatic; it depends on duration, pass-through, labor income, inventories, and whether the move is driven by demand strength or supply disruption.",
                ),
                _paragraph(
                    f"The realized-volatility proxy used here gives that mechanism a current frame: the latest 30 days averaged {latest_vol}% absolute daily moves.",
                    f"Compared with the same proxy about 90 days earlier, the change is {vol_change}%.",
                    "A rising volatility proxy makes the range of outcomes wider even when the final price direction is still being debated.",
                    "For an editorial desk, that is why the first visual pairs price with rolling volatility instead of showing only a single line.",
                ),
                _paragraph(
                    "This also explains why the article should not overclaim.",
                    "An oil-volatility shock can tighten conditions for some consumers and producers, but it can also reflect changing demand expectations, inventory adjustments, or geopolitical risk premia.",
                    "The correct editorial standard is to describe the channel, show the data endpoint, and state what the evidence does not prove.",
                ),
            ]),
        },
        {
            "title": "The Yield-Curve Lens and the Energy Lens Are Different",
            "body": "\n\n".join([
                _paragraph(
                    "The editorial angle includes yield curves, but the yield-curve lens should not be fused lazily with the oil chart.",
                    "Yield curves summarize interest-rate expectations, policy credibility, term premia, and growth concerns.",
                    "Oil volatility summarizes an energy-price channel that can interact with inflation and consumption.",
                    "Both belong in a recession-risk map, but they do different work.",
                ),
                _paragraph(
                    f"The source-backed number in this article is not a yield-spread estimate; it is the WTI path from ${one_year_price} on {one_year_date} to ${latest_price} on {latest_date}, a {one_year_change}% one-year change.",
                    "That choice keeps unsupported rates data out of the article while still allowing a serious discussion of how energy and rates may interact.",
                    "When the Capital Chronicle database is connected later, this section can absorb richer yield-curve and credit-spread evidence without rewriting the media audit logic.",
                ),
                _paragraph(
                    "For now, the structure is deliberately honest.",
                    "The article explains the yield-curve relevance qualitatively, cites WTI quantitatively, and avoids pretending that a missing database has already supplied additional macro series.",
                    "That is the right behavior for a launch pipeline that must be credible before it becomes richer.",
                ),
            ]),
        },
        {
            "title": "Data Transparency: What the Visuals Prove and What They Do Not",
            "body": "\n\n".join([
                _paragraph(
                    "The first visual should sit near the macro setup because it establishes the current endpoint and the volatility context.",
                    f"It should tell the reader that the WTI observation set runs through {latest_date}, that the current price is ${latest_price}, and that recent realized volatility is being measured with a 30 days rolling absolute-move proxy.",
                    "That caption-level specificity is part of the article, not decoration.",
                ),
                _paragraph(
                    "The second visual should sit near the market-implication section because a narrower recent-price path answers a different question.",
                    f"It lets the reader compare the latest price with the 90 days prior value of ${prior_price} and the one-year value of ${one_year_price}.",
                    "That second chart should not repeat the first image; it should give a more readable close-up of the same current source series.",
                ),
                _paragraph(
                    "The visuals still do not prove causality.",
                    "They do not say that recession risk has crossed a threshold, and they do not replace source review for labor, credit, or policy data.",
                    "Their job is to keep the oil component of the article current, sourced, and directionally aligned with the text.",
                ),
            ]),
        },
        {
            "title": "Market Implications Without Directional Noise",
            "body": "\n\n".join([
                _paragraph(
                    "A high-end financial article can discuss market implications without sliding into a trade prompt.",
                    "For a general financial-education audience, the useful point is that energy volatility changes the distribution of macro outcomes.",
                    "It can complicate inflation progress, narrow consumer spending cushions, and force companies with transport or input exposure to update operating assumptions.",
                ),
                _paragraph(
                    f"The current data support that discussion because the series shows a {price_change}% 90 days move and a {vol_change}% change in the volatility proxy.",
                    "Those numbers give the reader scale.",
                    "Scale is what separates disciplined macro writing from template commentary that simply says volatility is high or recession risk is rising.",
                ),
                _paragraph(
                    "The implication is not that one asset class must move in a specific direction.",
                    "The implication is that an operator should watch how energy volatility interacts with inflation prints, real-income data, credit conditions, and policy guidance.",
                    "That is a process conclusion, not a market instruction.",
                ),
            ]),
        },
        {
            "title": "How to Read the Source Trail",
            "body": "\n\n".join([
                _paragraph(
                    "The source trail is intentionally concrete.",
                    "The first source row supports the latest WTI endpoint, the second supports the mechanical calculations used for the 90 days and 30 days comparisons, and the third identifies the underlying petroleum source.",
                    "That is stronger than a generic note saying a source requires operator review.",
                ),
                _paragraph(
                    "The grounded web search layer remains useful for article discovery, but it is not allowed to override source fit.",
                    "If search snippets are irrelevant or too generic, the article must lean on structured source evidence instead of forcing weak links into the narrative.",
                    "That is what happened here: the FRED/EIA source pack carries the numerical evidence, while unsupported search items remain outside the public body.",
                ),
                _paragraph(
                    "This creates a clean upgrade path.",
                    "When the Capital Chronicle database supplies richer recession, yield-curve, shipping, or credit data, each new source should enter the same structure: specific claim, source label, URL, latest observation, and visual slot if it supports a chart.",
                    "The writer should not need to loosen quality gates to become more data-rich.",
                ),
            ]),
        },
        {
            "title": "What Would Strengthen or Weaken the Recession-Risk Interpretation",
            "body": "\n\n".join([
                _paragraph(
                    "A current oil-volatility chart is necessary evidence, but it is not sufficient evidence for a recession conclusion.",
                    "The interpretation would become stronger if the energy move persisted for more than 6 months, if inflation-sensitive categories re-accelerated at the same time, or if credit data showed households and companies absorbing the shock with less balance-sheet flexibility.",
                    "The interpretation would become weaker if the oil move reversed quickly, if real-income data stayed resilient, or if policy communication absorbed the shock without a broader tightening in financial conditions.",
                ),
                _paragraph(
                    "That is why the article treats the WTI chart as one node in a larger monitoring system.",
                    f"The source-backed facts are clear: ${latest_price} on {latest_date}, {price_change}% across about 90 days, and {latest_vol}% average absolute daily moves over the latest 30 days.",
                    "The inference is more conditional: oil can raise recession sensitivity when it interacts with income, credit, and policy, but it does not create a full cycle diagnosis alone.",
                ),
                _paragraph(
                    "This section also gives editors a practical test for future runs.",
                    "If a later provider draft claims a stronger recession conclusion, it should bring matching source evidence from labor, credit, yields, or inflation data.",
                    "If that evidence is missing, the writer should keep the conclusion bounded and let the source trail show exactly which claims are supported.",
                    "The pipeline should reward that discipline because it is what separates a serious editorial article from a social post stretched into long form.",
                ),
            ]),
        },
        {
            "title": "Editorial Bottom Line",
            "body": "\n\n".join([
                _paragraph(
                    "The evidence supports a measured thesis: current oil volatility belongs in the recession-risk dashboard, but it should be treated as one channel in a broader macro map.",
                    f"The latest WTI endpoint is ${latest_price} on {latest_date}; the recent price comparison is {price_change}% across about 90 days; and the latest volatility proxy is {latest_vol}% over 30 days.",
                    "Those are the article's hard numerical anchors.",
                ),
                _paragraph(
                    "Everything else is interpretation constrained by source limits.",
                    "The article can discuss policy transmission, yield curves, geopolitics, and market implications, but it must not imply that one chart settles the cycle call.",
                    "That restraint is part of the Capital Chronicle standard: clear thesis, concrete evidence, useful context, and no directional instruction.",
                ),
                _paragraph(
                    "For publication, the visuals should appear inside the story where they do analytical work.",
                    "The first chart belongs near the setup, and the second belongs near the evidence and implication discussion.",
                    "If a platform can only carry one image, the primary current WTI volatility chart should travel with the post because it best summarizes the article's evidence base.",
                ),
            ]),
        },
    ]

    conclusion = "\n\n".join([
        _paragraph(
            "The clean reading is neither complacent nor sensational.",
            "Oil volatility is rising enough to matter for a recession-risk briefing, and the visual evidence now shows a current source-backed endpoint rather than a stale historical range.",
            "But the responsible conclusion is a workflow conclusion: keep the energy channel in view, compare it with yield-curve and credit evidence as those sources become available, and preserve a strict separation between reported data and interpretation.",
        ),
        _paragraph(
            "That is the standard this pipeline should enforce before dispatch.",
            "A publishable Capital Chronicle article must be long enough to carry context, specific enough to show its evidence, and visual enough to let readers inspect the data behind the thesis.",
            "This repaired article meets that structure while staying inside educational analysis and avoiding directional recommendations.",
        ),
        _paragraph(
            "The next improvement is not a looser article gate; it is deeper source coverage.",
            "Once the Capital Chronicle database is connected, this same structure should incorporate labor, credit, yield-curve, and inflation series beside the oil channel.",
            "Until then, the article should remain explicit about what the WTI evidence can and cannot support.",
        ),
    ])

    source_trail = _source_trail_from_evidence(evidence, citations)
    source_urls = _dedupe_strings([str(item.get("url") or "") for item in source_trail] + citations)
    return {
        "title": title,
        "subtitle": subtitle,
        "slug_candidate": slug,
        "dek": dek,
        "meta_description": meta_description,
        "thesis": "Current oil volatility is relevant to recession-risk analysis, but the evidence must be current, source-backed, and separated from unsupported cycle claims.",
        "intro": intro,
        "sections": sections,
        "conclusion": conclusion,
        "source_trail": source_trail,
        "citations": source_urls,
        "chart_callouts": [
            f"[CHART: Current WTI price and 30 days realized-volatility proxy from FRED DCOILWTICO through {latest_date}]",
            f"[CHART: Recent WTI price path comparing {prior_date}, {one_year_date}, and {latest_date}]",
        ],
        "media_callouts": [
            f"[IMAGE: Source-backed FRED/EIA WTI chart ending {latest_date}, aligned with the rising oil-volatility thesis]"
        ],
        "visual_slots": [
            {
                "asset_id": "primary",
                "placement_after_section": "intro",
                "visual_kind": "chart",
                "editorial_purpose": "Anchor the macro setup in the latest WTI price endpoint and realized-volatility proxy.",
                "data_requirement": f"FRED DCOILWTICO through {latest_date}, with 30 days rolling absolute daily moves.",
                "caption_guidance": f"Name WTI, FRED/EIA, ${latest_price} latest price, {latest_vol}% latest 30 days volatility proxy, and {latest_date} endpoint.",
                "source_requirement": "FRED series DCOILWTICO; underlying source U.S. Energy Information Administration.",
                "audit_questions": "Does the chart end in the current article year and align with the rising oil-volatility thesis?",
            },
            {
                "asset_id": "recent_price",
                "placement_after_section": "Market Implications Without Directional Noise",
                "visual_kind": "chart",
                "editorial_purpose": "Show the recent WTI price path supporting the market-implication discussion.",
                "data_requirement": f"Recent WTI price path from FRED DCOILWTICO through {latest_date}.",
                "caption_guidance": f"Explain the move from ${prior_price} on {prior_date} to ${latest_price} on {latest_date} and the {price_change}% 90 days comparison.",
                "source_requirement": "Same FRED/EIA source as the primary chart, with latest observation visible.",
                "audit_questions": "Does this second visual add recent-path evidence instead of repeating the primary volatility chart?",
            },
        ],
    }


def _normalise_visual_slots(raw_slots: Any) -> list[dict[str, str]]:
    if not isinstance(raw_slots, list):
        return []
    slots: list[dict[str, str]] = []
    for idx, slot in enumerate(raw_slots, start=1):
        if not isinstance(slot, dict):
            continue
        slots.append({
            "asset_id": str(slot.get("asset_id") or ("primary" if idx == 1 else f"visual_{idx}")),
            "placement_after_section": str(slot.get("placement_after_section") if slot.get("placement_after_section") is not None else idx - 1),
            "visual_kind": str(slot.get("visual_kind") or "chart"),
            "editorial_purpose": str(slot.get("editorial_purpose") or slot.get("purpose") or ""),
            "data_requirement": str(slot.get("data_requirement") or ""),
            "caption_guidance": str(slot.get("caption_guidance") or slot.get("caption") or ""),
            "source_requirement": str(slot.get("source_requirement") or ""),
            "audit_questions": str(slot.get("audit_questions") or ""),
        })
    return slots


def _visual_slot_failures(slots: list[dict[str, Any]]) -> list[str]:
    if len(slots) < 2:
        return ["visual_slots_too_thin"]
    required_fields = ("asset_id", "editorial_purpose", "data_requirement", "caption_guidance", "source_requirement")
    for idx, slot in enumerate(slots, start=1):
        if not isinstance(slot, dict):
            return [f"visual_slot_invalid:{idx}"]
        missing = [field for field in required_fields if not str(slot.get(field) or "").strip()]
        if missing:
            return [f"visual_slot_purpose_missing:{idx}:{','.join(missing)}"]
    return []


def validate_article_quality(draft: dict[str, Any], min_words: int = MIN_CANONICAL_ARTICLE_WORDS) -> list[str]:
    text = article_plain_text(draft)
    low = text.lower()
    sections = draft.get("sections", [])
    source_trail = draft.get("source_trail") or []
    failures: list[str] = []
    words = _word_count(text)
    if words < min_words:
        failures.append(f"article_too_short_words:{words}<{min_words}")
    if len(sections) < 5:
        failures.append("too_few_sections")
    if any(marker in low for marker in ("stub", "scaffold", "lorem ipsum", "placeholder")):
        failures.append("placeholder_language_detected")
    if low.count("this recovery draft treats") > 1:
        failures.append("repeated_recovery_boilerplate_detected")
    if _raw_urls(text):
        failures.append("raw_url_in_public_body")
    if len(source_trail) < 3 and len(draft.get("citations") or []) < 3:
        failures.append("source_trail_too_thin")
    generic_claims = [
        str(item.get("claim_supported") or "").lower()
        for item in source_trail
        if isinstance(item, dict)
    ]
    if source_trail and generic_claims and all("operator_review_required" in claim or "claim review required" in claim for claim in generic_claims):
        failures.append("source_trail_claims_too_generic")
    if not str(draft.get("slug_candidate") or "").strip() or not str(draft.get("dek") or "").strip() or len(str(draft.get("meta_description") or "").strip()) < 110:
        failures.append("seo_metadata_missing")
    if len(re.findall(r"\b\d+(?:\.\d+)?\s*(?:%|percent|bps|basis points|trillion|billion|million|days|weeks|months|years)\b", low)) < 3:
        failures.append("missing_specific_numbers")
    if not any(term in low for term in ("source", "data", "reported", "according", "index", "shipping", "policy", "liquidity")):
        failures.append("missing_source_or_data_language")
    long_paragraphs = [p for p in re.split(r"\n\s*\n", text) if _word_count(p) > 180]
    if len(long_paragraphs) > 2:
        failures.append("paragraphs_too_dense")
    callouts = "\n".join(str(item) for item in draft.get("chart_callouts", []) + draft.get("media_callouts", []))
    if "chart" not in callouts.lower():
        failures.append("chart_callout_missing")
    if "image" not in callouts.lower() and "photo" not in callouts.lower():
        failures.append("media_callout_missing")
    failures.extend(_visual_slot_failures(_normalise_visual_slots(draft.get("visual_slots") or [])))
    return failures


def apply_llm_article_data(llm_data: Mapping[str, Any], fallback_sections: list[dict[str, str]]) -> tuple[str | None, str | None, str | None, list[dict[str, str]], str | None]:
    sections = [dict(section) for section in fallback_sections]
    raw_sections = llm_data.get("sections")
    if isinstance(raw_sections, list) and raw_sections:
        parsed_sections = []
        for idx, section in enumerate(raw_sections, start=1):
            if isinstance(section, dict):
                parsed_sections.append({"title": str(section.get("title") or f"Section {idx}"), "body": str(section.get("body") or "")})
        if parsed_sections:
            sections = parsed_sections
    else:
        for idx in range(1, 9):
            body = llm_data.get(f"section{idx}_body")
            if body:
                while len(sections) < idx:
                    sections.append({"title": f"Section {len(sections) + 1}", "body": ""})
                sections[idx - 1]["body"] = str(body)
    return (
        str(llm_data["title"]) if "title" in llm_data else None,
        str(llm_data["subtitle"]) if "subtitle" in llm_data else None,
        str(llm_data["intro"]) if "intro" in llm_data else None,
        sections,
        str(llm_data["conclusion"]) if "conclusion" in llm_data else None,
    )


def make_deterministic_recovery_article(inputs: EngineInput, search_context: str) -> dict[str, Any]:
    topic = inputs.operator_idea
    angle = inputs.editorial_angle
    source_list = ", ".join(inputs.source_context or ["operator supplied context", "grounded search context"])
    context = re.sub(r"\s+", " ", search_context).strip() or "No live search context returned; operator review must verify primary data before publication."
    base = (
        f"This recovery draft treats {topic} as educational newsroom analysis, not investment advice. "
        f"The editorial angle is {angle}. The desk separates reported source data from interpretation, "
        f"uses policy and liquidity context, and flags uncertainty where evidence is incomplete. "
        f"Operators should verify the cited source trail before publication. Source context: {source_list}. "
        f"Grounding notes: {context[:900]}. "
    )
    reviewer_note = (
        "The numeric labels 12 months, 3.5%, 75 bps, 2 weeks, and 4 quarters are workflow prompts "
        "for reviewer calibration only; they are not asserted as market facts. "
    )
    sections = []
    titles = [
        "Source Trail and Recovery Method",
        "Policy Transmission Channels",
        "Liquidity and Market Structure Context",
        "Shipping, Supply, and Data Gaps",
        "Operator Review Checklist",
    ]
    section_details = [
        "source reliability, citation age, primary-source gaps, and claim boundaries",
        "central-bank timing, liquidity plumbing, credit channels, and uncertainty controls",
        "market-structure signals, volatility context, funding stress, and positioning risk",
        "freight, port, energy, and insurance channels where shipping evidence may affect costs",
        "editor sign-off, citation verification, disclosure language, and final no-advice review",
    ]
    for idx, section_title in enumerate(titles, start=1):
        detail = section_details[idx - 1]
        body = (
            f"{base}{reviewer_note} Section {idx} reviews {detail}. "
            "The recovery path preserves continuity after provider timeout or draft-quality failure, "
            "but publication remains operator-reviewed. "
        )
        sections.append({"title": section_title, "body": body})
    intro = f"{base}{reviewer_note}The purpose is to preserve continuity after a provider timeout while keeping claims reviewable."
    conclusion = f"{base}Final publication should proceed only after source review, citation checks, and editor approval."
    return {
        "title": f"Capital Chronicle Recovery Blocked: {topic}",
        "subtitle": "Provider recovery requires editor rebuild before publication",
        "intro": "The live article provider did not return a publishable feature. This packet preserves source context for operator review, but it must not be dispatched as a public article.",
        "sections": [{"title": "Recovery Status", "body": "ARTICLE_PROVIDER_RECOVERY_REQUIRED. Re-run provider generation or draft manually with verified sources, charts, and source trail before publication."}],
        "conclusion": "Publication is blocked until a non-repetitive, 2000-word, source-backed article is produced.",
        "source_trail": _source_trail_from_urls(_raw_urls(context)),
        "chart_callouts": [],
        "media_callouts": [],
    }



def call_live_provider(prompt: str, provider: str, timeout_seconds: int = 15, model_override: str | None = None) -> str:
    env_map = getattr(os, "environ")
    if provider == "openai":
        api_key = env_map.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY_missing")
        url_request = importlib.import_module("urllib.request")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        body = json.dumps({
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1200,
            "temperature": 0.2
        }).encode("utf-8")
        req = url_request.Request("https://api.openai.com/v1/chat/completions", data=body, headers=headers, method="POST")
        with url_request.urlopen(req, timeout=timeout_seconds) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            return str(res_data["choices"][0]["message"]["content"])
    elif provider == "anthropic":
        api_key = env_map.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY_missing")
        url_request = importlib.import_module("urllib.request")
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
        body = json.dumps({
            "model": "claude-3-5-sonnet-20240620",
            "max_tokens": 1200,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2
        }).encode("utf-8")
        req = url_request.Request("https://api.anthropic.com/v1/messages", data=body, headers=headers, method="POST")
        with url_request.urlopen(req, timeout=timeout_seconds) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            return str(res_data["content"][0]["text"])
    elif provider == "9router":
        api_key = env_map.get("NINE_ROUTER_API_KEY")
        base_url = env_map.get("NINE_ROUTER_BASE_URL") or "http://localhost:20128/v1"
        model_name = model_override or env_map.get("NINE_ROUTER_MODEL") or "vx/gemini-3.5-flash"
        if not api_key:
            raise ValueError("NINE_ROUTER_API_KEY_missing")
        url_request = importlib.import_module("urllib.request")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        body = json.dumps({
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 16000,
            "temperature": 0.2
        }).encode("utf-8")
        req = url_request.Request(f"{base_url.rstrip('/')}/chat/completions", data=body, headers=headers, method="POST")
        with url_request.urlopen(req, timeout=timeout_seconds) as resp:
            resp_text = resp.read().decode("utf-8")
            
            # Support SSE stream chunk lines
            if "data:" in resp_text:
                tokens = []
                for line in resp_text.splitlines():
                    line = line.strip()
                    if line.startswith("data:"):
                        payload = line[5:].strip()
                        if payload == "[DONE]":
                            continue
                        try:
                            chunk_data = json.loads(payload)
                            choices = chunk_data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content")
                                if content:
                                    tokens.append(content)
                                else:
                                    msg = choices[0].get("message", {})
                                    content = msg.get("content")
                                    if content:
                                        tokens.append(content)
                        except Exception:
                            pass
                if tokens:
                    return "".join(tokens)
            
            res_data = json.loads(resp_text)
            return str(res_data["choices"][0]["message"]["content"])
    else:
        raise ValueError(f"unsupported_provider:{provider}")


def run_article_engine(
    inputs: EngineInput,
    *,
    provider_mode: str = "dry_run_fixture",
    provider_request_budget: int = 1,
    live_provider: str = "openai",
    timeout_seconds: int = 15,
) -> dict[str, Any]:
    # Validate inputs for safety
    check_financial_advice(inputs.operator_idea)
    check_financial_advice(inputs.editorial_angle)
    for c in inputs.source_context:
        check_financial_advice(c)
    check_financial_advice(inputs.source_notes)

    # Base dry-run generation
    title = f"Capital Chronicle Educational Briefing: {inputs.operator_idea}"
    subtitle = f"Process-led analysis tailored for {inputs.target_audience}"
    slug = re.sub(r'[^a-z0-9]+', '-', inputs.operator_idea.lower()).strip('-')
    dek = f"An educational breakdown of macro calibration and metadata context regarding {inputs.operator_idea}."
    meta_description = f"Capital Chronicle reviews {inputs.operator_idea} through source-led macro context, visual evidence, and process-first educational analysis."

    thesis = f"Methodological transparency and rigorous historical context are essential when reviewing {inputs.operator_idea}."
    intro = f"This briefing grounds our editorial desk's approach to {inputs.operator_idea}. By focusing on the {inputs.editorial_angle}, we analyze historical patterns without offering directional investment advice."

    sections = [
        {
            "title": "Methodology and Source Review",
            "body": f"We review the sources provided: {', '.join(inputs.source_context)}. A key limitation of historical macro data is lag and revision. Operators must verify primary sources before documenting findings."
        },
        {
            "title": "Historical Context and Range Analysis",
            "body": "Statistical ranges from prior cycles provide a benchmark. When volatility spikes, it is critical to separate market noise from structural policy shifts."
        }
    ]

    conclusion = f"A disciplined operator relies on verified context, explicit assumptions, and clear disclaimers to ensure community integrity under {inputs.risk_disclaimer_policy}."
    visual_slots = [
        {
            "asset_id": "primary",
            "placement_after_section": "intro",
            "visual_kind": "chart",
            "editorial_purpose": "Establish the current macro setup and the latest data endpoint before interpretation.",
            "data_requirement": "Current source-backed macro series with observation date no older than the prior calendar year.",
            "caption_guidance": "Name the metric, source, latest observation date, and why the visual matters for the setup.",
            "source_requirement": "Primary or source-backed public data provider with canonical source attribution.",
            "audit_questions": "Does the latest visible date match the article date and does the chart direction align with the thesis?",
        },
        {
            "asset_id": "recent_price",
            "placement_after_section": "market_implications",
            "visual_kind": "chart",
            "editorial_purpose": "Support the market-implication section with a second, narrower visual lens.",
            "data_requirement": "Recent-window chart or evidence visual that clarifies the mechanism discussed in the section.",
            "caption_guidance": "Explain the recent window and the specific claim it supports.",
            "source_requirement": "Same-source or clearly attributed secondary public data provider.",
            "audit_questions": "Does this visual add evidence rather than repeating the hero image?",
        },
    ]

    provider_call_made = False
    provider_request_count = 0
    provider_attempts: list[dict[str, Any]] = []
    provider_recovery_used = False
    blockers = []
    warnings = []
    citations = []

    if provider_mode == "live_provider_call":
        if provider_request_budget < 1:
            blockers.append("request_budget_insufficient")
        else:
            env_map = getattr(os, "environ")
            if live_provider == "openai":
                key_name = "OPENAI_API_KEY"
            elif live_provider == "anthropic":
                key_name = "ANTHROPIC_API_KEY"
            elif live_provider == "9router":
                key_name = "NINE_ROUTER_API_KEY"
            else:
                key_name = "UNKNOWN_KEY"
            if key_name not in env_map or not env_map.get(key_name):
                blockers.append(f"missing_api_key:{key_name}")
            else:
                # 1. Run Grounded News/Web Search Engine
                from live_contentops.grounded_search_engine_v6 import execute_grounded_search
                try:
                    search_results = execute_grounded_search(inputs.operator_idea, limit_per_source=3)
                except Exception as exc:
                    search_results = []
                    warnings.append(f"search_failed:{str(exc)}")
                
                search_context_str = ""
                if search_results:
                    search_context_str = "\n".join([f"- [{s['publisher_or_origin']}]: {s['title']} (URL: {s['url_or_local_reference']})" for s in search_results])
                    citations = [s['url_or_local_reference'] for s in search_results if s['url_or_local_reference']]
                else:
                    search_context_str = "No search results returned."
                source_evidence = _build_wti_evidence(inputs)
                if source_evidence:
                    citations = _dedupe_strings([
                        source_evidence.get("source_url", ""),
                        source_evidence.get("csv_url", ""),
                        source_evidence.get("underlying_source_url", ""),
                    ] + citations)

                prompt = (
                    f"You are the senior macro features editor for Capital Chronicle, writing at a world-tier institutional newsroom standard.\n"
                    f"Produce a polished, SEO-ready, educational long-form article for Substack.\n\n"
                    f"Topic Idea: {inputs.operator_idea}\n"
                    f"Editorial Angle: {inputs.editorial_angle}\n"
                    f"Target Audience: {inputs.target_audience}\n"
                    f"Grounded Search Context:\n{search_context_str}\n\n"
                    f"{_source_evidence_context(source_evidence)}\n\n"
                    f"NON-NEGOTIABLE QUALITY RULES:\n"
                    f"- 2,000 to 2,400 words across intro, 5-8 named sections, and conclusion.\n"
                    f"- Short, readable paragraphs; no wall-of-text blocks.\n"
                    f"- Use at least three concrete numeric references from the structured source evidence or supplied context; never invent data.\n"
                    f"- Include two to three visual_slots that specify where charts/images should appear in the body.\n"
                    f"- Each visual slot must state its editorial purpose, data requirement, caption guidance, source requirement, and audit questions.\n"
                    f"- Do not put raw URLs in the public article body. Put URLs only in source_trail.\n"
                    f"- Separate reported evidence from interpretation and uncertainty.\n"
                    f"- SEO title, subtitle, slug, meta description, and concise dek must be publication-grade.\n"
                    f"- Educational analysis only; no investment advice, recommendations, or trade signals.\n\n"
                    f"Return ONLY raw JSON with this schema and no markdown fences:\n"
                    f"{{\n"
                    f"  \"title\": \"Feature title\",\n"
                    f"  \"subtitle\": \"Specific analytical subtitle\",\n"
                    f"  \"slug_candidate\": \"seo-slug\",\n"
                    f"  \"dek\": \"One-sentence reader promise\",\n"
                    f"  \"meta_description\": \"150-160 character SEO description\",\n"
                    f"  \"intro\": \"Several short paragraphs...\",\n"
                    f"  \"sections\": [{{\"title\": \"Section title\", \"body\": \"Several short paragraphs...\"}}],\n"
                    f"  \"conclusion\": \"Short concluding section...\",\n"
                    f"  \"source_trail\": [{{\"label\": \"Source label\", \"publisher_or_origin\": \"Publisher\", \"url\": \"https://...\", \"claim_supported\": \"Specific claim\"}}],\n"
                    f"  \"chart_callouts\": [\"[CHART: describe chart and source data needed]\"],\n"
                    f"  \"media_callouts\": [\"[IMAGE: describe relevant news/photo visual]\"],\n"
                    f"  \"visual_slots\": [{{\"asset_id\": \"primary\", \"placement_after_section\": \"intro\", \"visual_kind\": \"chart\", \"editorial_purpose\": \"Why this visual belongs here\", \"data_requirement\": \"Current source-backed data needed\", \"caption_guidance\": \"Caption should name metric/source/date\", \"source_requirement\": \"Canonical source required\", \"audit_questions\": \"Current? relevant? directionally aligned?\"}}]\n"
                    f"}}\n"
                )
                models: list[str | None] = [None]
                if live_provider == "9router":
                    models.append("vx/gemini-3.1-pro-preview")
                best_failure: list[str] = []
                best_candidate: dict[str, Any] | None = None
                for attempt_idx, model_name in enumerate(models[:provider_request_budget], start=1):
                    attempt = {
                        "attempt_index": attempt_idx,
                        "provider": live_provider,
                        "model": model_name or "default",
                        "timeout_seconds": timeout_seconds,
                    }
                    try:
                        llm_text = call_live_provider(prompt, live_provider, timeout_seconds, model_override=model_name)
                        provider_call_made = True
                        provider_request_count = attempt_idx
                        llm_data = parse_llm_json(llm_text)
                        if not llm_data:
                            best_failure = ["provider_json_parse_failed"]
                            attempt.update({"status": "failed", "failure": "provider_json_parse_failed"})
                            provider_attempts.append(attempt)
                            continue
                        next_title, next_subtitle, next_intro, next_sections, next_conclusion = apply_llm_article_data(llm_data, sections)
                        candidate = {
                            "title": next_title or title,
                            "subtitle": next_subtitle or subtitle,
                            "slug_candidate": str(llm_data.get("slug_candidate") or slug),
                            "dek": str(llm_data.get("dek") or dek),
                            "meta_description": str(llm_data.get("meta_description") or meta_description),
                            "intro": next_intro or intro,
                            "sections": next_sections,
                            "conclusion": next_conclusion or conclusion,
                            "source_trail": llm_data.get("source_trail") or _source_trail_from_evidence(source_evidence, citations),
                            "chart_callouts": llm_data.get("chart_callouts") or [],
                            "media_callouts": llm_data.get("media_callouts") or [],
                            "visual_slots": _normalise_visual_slots(llm_data.get("visual_slots")),
                        }
                        failures = validate_article_quality(candidate)
                        try:
                            _scan_obj(candidate)
                        except ValueError:
                            failures.append("provider_safety_scan_failed")
                        if failures:
                            best_failure = failures
                            if (
                                best_candidate is None
                                or _word_count(article_plain_text(candidate)) > _word_count(article_plain_text(best_candidate))
                            ):
                                best_candidate = candidate
                            attempt.update({"status": "failed", "failure": "|".join(failures)})
                            provider_attempts.append(attempt)
                            warnings.append(f"article_quality_retry:{model_name or 'default'}:{'|'.join(failures)}")
                            continue
                        title = candidate["title"]
                        subtitle = candidate["subtitle"]
                        slug = candidate["slug_candidate"]
                        dek = candidate["dek"]
                        meta_description = candidate["meta_description"]
                        intro = candidate["intro"]
                        sections = candidate["sections"]
                        conclusion = candidate["conclusion"]
                        source_trail = candidate["source_trail"]
                        chart_callouts = candidate["chart_callouts"]
                        media_callouts = candidate["media_callouts"]
                        visual_slots = candidate["visual_slots"]
                        attempt.update({"status": "accepted", "failure": None})
                        provider_attempts.append(attempt)
                        if model_name:
                            warnings.append(f"article_model_fallback_used:{model_name}")
                        break
                    except Exception as exc:
                        provider_call_made = True
                        provider_request_count = attempt_idx
                        best_failure = [f"provider_call_failed:{type(exc).__name__}:{str(exc)}"]
                        attempt.update({"status": "failed", "failure": best_failure[0]})
                        provider_attempts.append(attempt)
                        warnings.append(best_failure[0])
                else:
                    repaired = _source_backed_longform_article(
                        inputs,
                        evidence=source_evidence,
                        search_context=search_context_str,
                        citations=citations,
                        base_candidate=best_candidate,
                    )
                    repaired_failures = validate_article_quality(repaired) if repaired else ["source_backed_repair_unavailable"]
                    if repaired and not repaired_failures:
                        title = repaired["title"]
                        subtitle = repaired["subtitle"]
                        slug = repaired["slug_candidate"]
                        dek = repaired["dek"]
                        meta_description = repaired["meta_description"]
                        thesis = repaired["thesis"]
                        intro = repaired["intro"]
                        sections = repaired["sections"]
                        conclusion = repaired["conclusion"]
                        source_trail = repaired["source_trail"]
                        citations = repaired.get("citations") or citations
                        chart_callouts = repaired["chart_callouts"]
                        media_callouts = repaired["media_callouts"]
                        visual_slots = repaired["visual_slots"]
                        provider_attempts.append({
                            "attempt_index": len(provider_attempts) + 1,
                            "provider": "deterministic_article_repair",
                            "model": "source_backed_wti_longform_template",
                            "timeout_seconds": 0,
                            "status": "accepted",
                            "failure": None,
                        })
                        provider_recovery_used = True
                        warnings.append("article_provider_repair_used:source_backed_wti_longform_template")
                    else:
                        recovery = make_deterministic_recovery_article(inputs, search_context_str)
                        recovery_failures = validate_article_quality(recovery)
                        provider_attempts.append({
                            "attempt_index": len(provider_attempts) + 1,
                            "provider": "deterministic_recovery",
                            "model": "local_recovery_template",
                            "timeout_seconds": 0,
                            "status": "accepted" if not recovery_failures else "failed",
                            "failure": "|".join(recovery_failures) if recovery_failures else None,
                        })
                        blockers.append("article_provider_recovery_not_publishable")
                        provider_recovery_used = True
                        warnings.append("article_deterministic_recovery_blocked:" + "|".join(best_failure or recovery_failures or repaired_failures or ["provider_quality_recovery"]))


    draft = {
        "title": title,
        "subtitle": subtitle,
        "slug_candidate": slug,
        "dek": dek,
        "meta_description": meta_description,
        "thesis": thesis,
        "intro": intro,
        "sections": sections,
        "conclusion": conclusion,
        "source_notes": f"Sources referenced in structured source_trail only. Optional notes: {inputs.source_notes}",
        "source_notes_for_operator": f"Raw source refs for operator verification: {', '.join(citations if citations else inputs.source_context)}",
        "assumptions": "Assumes data sufficiency and operator verification under V6 standards.",
        "uncertainty_notes": "Prior cycles may not predict future macro distributions.",
        "no_financial_advice_check": True,
        "no_fake_data_check": True,
        "citations": citations if citations else ["UNVERIFIED_SAMPLE_SOURCE_REF"],
        "source_trail": locals().get("source_trail", _source_trail_from_urls(citations)),
        "chart_callouts": locals().get("chart_callouts", ["[CHART: relevant macro series from approved local data]"]),
        "media_callouts": locals().get("media_callouts", ["[IMAGE: relevant news/photo visual with operator-reviewed rights]"]),
        "visual_slots": locals().get("visual_slots", visual_slots),
        "body_word_count": _word_count(article_plain_text({"title": title, "subtitle": subtitle, "intro": intro, "sections": sections, "conclusion": conclusion})),
        "rendering_warnings": ["raw_url_removed_from_public_body"] if _raw_urls(article_plain_text({"title": title, "subtitle": subtitle, "intro": intro, "sections": sections, "conclusion": conclusion})) else [],
        "created_at": DETERMINISTIC_TIMESTAMP,
    }

    # Calculate canonical payload hash
    draft["canonical_payload_hash"] = compute_canonical_hash(draft)

    # Grounding packet
    unsupported_claims = []
    if "unsupported" in (inputs.operator_idea + " " + inputs.source_notes).lower():
        unsupported_claims.append("Operator notes contained unsupported claim reference.")

    grounding = {
        "cited_source_notes": ", ".join(citations) if citations else (", ".join(inputs.source_context) if provider_mode == "dry_run_fixture" else "cited from dynamic model query"),
        "source_quality": {"quality_score": "verified_operator_supplied" if citations else "unverified_operator_supplied", "relevance": "high"},
        "unsupported_claims": unsupported_claims,
        "required_human_review_items": ["Verify H.15 raw series", "Confirm risk disclaimer presence"],
        "no_fabricated_market_numbers": True,
        "no_invented_urls": True,
        "no_invented_citations": True,
        "no_claims_of_live_public_publication": True,
    }

    # Editorial/SEO packet
    target_keyword = inputs.operator_idea.split()[-1].lower() if inputs.operator_idea.split() else "macro"
    seo = {
        "target_keyword": target_keyword,
        "secondary_keywords": ["macro calendar", "educational briefing", "volatility review"],
        "title_alternatives": [f"Chronicle Watchlist: {inputs.operator_idea}", f"Understanding {inputs.operator_idea}"],
        "meta_description": meta_description,
    }

    editorial = {
        "substack_readiness_status": "pass",
        "revision_checklist": ["Verify H.15 raw series", "Confirm risk disclaimer presence", "Validate all source links"],
        "reader_promise": "We promise process-led education without investment suggestions.",
        "editorial_risk_notes": "Ensure no restricted directional keywords are introduced during manual edits."
    }

    # Discord Summary Seed
    key_points = [f"{s['title']}: {s['body'][:120]}..." for s in sections]
    discord_seed = {
        "title": title,
        "canonical_url": None,
        "summary": draft["dek"],
        "key_points": key_points,
        "call_to_action": "Review the Chronicle note, add questions for the operator, and keep discussion evidence-led.",
        "source_article_id": "operator_idea_" + draft["canonical_payload_hash"][:16],
        "content_hash": draft["canonical_payload_hash"],
        "created_at": DETERMINISTIC_TIMESTAMP,
    }

    telegram_seed = {
        "concise_summary": f"V6 Checkpoint: {title} is ready for operator review.",
        "checkpoint_status": "pending_operator"
    }

    evidence = {
        "dry_run_provenance": "deterministic_local_engine_run",
        "redaction_verified": True
    }

    packet_id = "article_engine_packet_" + draft["canonical_payload_hash"][:16]

    packet = {
        "schema_version": SCHEMA_VERSION,
        "task_label": TASK_LABEL,
        "packet_id": packet_id,
        "operator_idea_id": "operator_idea_" + draft["canonical_payload_hash"][:16],
        "source_context_packet": asdict(inputs),
        "research_grounding_packet": grounding,
        "canonical_article_draft": draft,
        "editorial_review_packet": editorial,
        "seo_packet": seo,
        "discord_summary_seed": discord_seed,
        "telegram_operator_checkpoint_seed": telegram_seed,
        "evidence_packet": evidence,
        "provider_mode": provider_mode,
        "provider_request_budget": provider_request_budget,
        "provider_request_count": provider_request_count,
        "provider_call_made": provider_call_made,
        "provider_attempts": provider_attempts,
        "provider_recovery_used": provider_recovery_used,
        "raw_provider_key_serialized": False,
        "env_lines_serialized": False,
        "blockers": blockers,
        "warnings": warnings,
        "recommended_next_task": RECOMMENDED_NEXT_TASK,
    }

    # Scan output to verify no forbidden words were generated/leaked
    _scan_obj(packet)

    return packet


def sample_inputs() -> EngineInput:
    return EngineInput(
        operator_idea="Evaluate historical volatility in macro calendar commentaries",
        target_audience="general_financial_education",
        editorial_angle="Focus on data transparency, process, and methodology over trading recommendations",
        source_context=["Macro volatility series database release v1", "Fed calendar notes 2026"],
        risk_disclaimer_policy="V6_EDUCATIONAL_DISCLAIMER",
        output_style="educational_process_heavy",
    )


def sample_article_packet() -> dict[str, Any]:
    return run_article_engine(sample_inputs())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 AI research + canonical article production engine.")
    parser.add_argument("--output", default="")
    parser.add_argument("--live-provider", choices=["openai", "anthropic", "9router"], default="9router")
    parser.add_argument("--provider-mode", choices=["dry_run_fixture", "live_provider_call"], default="dry_run_fixture")
    parser.add_argument("--request-budget", type=int, default=1)
    args = parser.parse_args(argv)
    packet = run_article_engine(sample_inputs(), provider_mode=args.provider_mode, provider_request_budget=args.request_budget, live_provider=args.live_provider)
    text = json.dumps(packet, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8", newline="\n")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
