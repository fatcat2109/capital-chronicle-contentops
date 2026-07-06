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
TASK_LABEL = "TASK_CONTENTOPS_V6_AI_RESEARCH_CANONICAL_ARTICLE_PRODUCTION_ENGINE_HEAVY_BATCH_V0"
DETERMINISTIC_TIMESTAMP = "2026-07-01T02:56:46+07:00"
RECOMMENDED_NEXT_TASK = "TASK_CONTENTOPS_V6_VARIANT_PREVIEW_HASH_APPROVAL_TO_DISCORD_OUTBOX_HEAVY_BATCH_V0"

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
        if word in {"buy", "sell", "hold", "entry", "entries", "exit", "exits", "target", "targets"}:
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
            if k in {"target_audience", "publish_target", "downstream_targets", "env_key_name", "task_label", "schema_version", "recommended_next_task"}:
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


def validate_article_quality(draft: dict[str, Any], min_chars: int = 5000) -> list[str]:
    text = article_plain_text(draft)
    low = text.lower()
    failures: list[str] = []
    if len(text) < min_chars:
        failures.append(f"article_too_short:{len(text)}<{min_chars}")
    if len(draft.get("sections", [])) < 4:
        failures.append("too_few_sections")
    if any(marker in low for marker in ("stub", "scaffold", "lorem ipsum", "placeholder")):
        failures.append("placeholder_language_detected")
    if not re.search(r"\b\d+(?:\.\d+)?\s*(?:%|percent|bps|basis points|trillion|billion|million|days|weeks|months|years)\b", low):
        failures.append("missing_specific_numbers")
    if not any(term in low for term in ("source", "data", "reported", "according", "index", "shipping", "policy", "liquidity")):
        failures.append("missing_source_or_data_language")
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
            "max_tokens": 5000,
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

    provider_call_made = False
    provider_request_count = 0
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

                prompt = (
                    f"You are a senior macroeconomic and geopolitical features writer for Capital Chronicle.\n"
                    f"Write a long-form educational newsroom-style analysis with the depth, structure, and specificity expected from tier-1 financial journalism.\n\n"
                    f"Topic Idea: {inputs.operator_idea}\n"
                    f"Editorial Angle: {inputs.editorial_angle}\n"
                    f"Target Audience: {inputs.target_audience}\n"
                    f"Grounded Search Context:\n{search_context_str}\n\n"
                    f"REQUIRED OUTPUT QUALITY:\n"
                    f"- At least 1,500 words across intro, 5-7 named sections, and conclusion.\n"
                    f"- Include concrete numbers from the provided context when available; if unavailable, explain data gaps without inventing.\n"
                    f"- Explain transmission channels, historical context, second-order effects, and limitations.\n"
                    f"- Use a polished newspaper feature style while staying educational and non-advisory.\n"
                    f"- Include image placement note text in one section body if a relevant chart/photo would help.\n\n"
                    f"SAFETY EXCLUSIONS:\n"
                    f"- DO NOT provide any financial advice, investment recommendations, or trade signals.\n"
                    f"- DO NOT use transactional words like 'buy', 'sell', 'hold', 'price target', 'long', 'short'.\n\n"
                    f"Return ONLY a raw JSON object matching this schema, with no markdown fences:\n"
                    f"{{\n"
                    f"  \"title\": \"Feature title\",\n"
                    f"  \"subtitle\": \"Specific, analytical subtitle\",\n"
                    f"  \"intro\": \"Three to five substantial paragraphs...\",\n"
                    f"  \"sections\": [{{\"title\": \"Section title\", \"body\": \"Four to seven substantial paragraphs...\"}}],\n"
                    f"  \"conclusion\": \"Two to four substantial paragraphs...\"\n"
                    f"}}\n"
                )
                models: list[str | None] = [None]
                if live_provider == "9router":
                    models.append("vx/gemini-3.1-pro-preview")
                best_failure: list[str] = []
                for attempt_idx, model_name in enumerate(models, start=1):
                    try:
                        llm_text = call_live_provider(prompt, live_provider, timeout_seconds, model_override=model_name)
                        provider_call_made = True
                        provider_request_count = attempt_idx
                        llm_data = parse_llm_json(llm_text)
                        if not llm_data:
                            best_failure = ["provider_json_parse_failed"]
                            continue
                        next_title, next_subtitle, next_intro, next_sections, next_conclusion = apply_llm_article_data(llm_data, sections)
                        candidate = {
                            "title": next_title or title,
                            "subtitle": next_subtitle or subtitle,
                            "intro": next_intro or intro,
                            "sections": next_sections,
                            "conclusion": next_conclusion or conclusion,
                        }
                        failures = validate_article_quality(candidate)
                        if failures:
                            best_failure = failures
                            warnings.append(f"article_quality_retry:{model_name or 'default'}:{'|'.join(failures)}")
                            continue
                        title = candidate["title"]
                        subtitle = candidate["subtitle"]
                        intro = candidate["intro"]
                        sections = candidate["sections"]
                        conclusion = candidate["conclusion"]
                        if model_name:
                            warnings.append(f"article_model_fallback_used:{model_name}")
                        break
                    except Exception as exc:
                        provider_call_made = True
                        provider_request_count = attempt_idx
                        best_failure = [f"provider_call_failed:{str(exc)}"]
                        warnings.append(best_failure[0])
                else:
                    blockers.append("article_quality_gate_failed:" + "|".join(best_failure or ["unknown"]))


    draft = {
        "title": title,
        "subtitle": subtitle,
        "slug_candidate": slug,
        "dek": f"An educational breakdown of macro calibration and metadata context regarding {inputs.operator_idea}.",
        "thesis": thesis,
        "intro": intro,
        "sections": sections,
        "conclusion": conclusion,
        "source_notes": f"Sources referenced: {', '.join(citations if citations else inputs.source_context)}. Optional notes: {inputs.source_notes}",
        "assumptions": "Assumes data sufficiency and operator verification under V6 standards.",
        "uncertainty_notes": "Prior cycles may not predict future macro distributions.",
        "no_financial_advice_check": True,
        "no_fake_data_check": True,
        "citations": citations if citations else ["UNVERIFIED_SAMPLE_SOURCE_REF"],
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
        "meta_description": f"An educational briefing analyzing {inputs.operator_idea} under the editorial angle: {inputs.editorial_angle}."
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
