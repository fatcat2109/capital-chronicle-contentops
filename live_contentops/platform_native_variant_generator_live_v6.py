"""V6 Live Platform Native Variant Generator with Threading & Image Search.

Reads the canonical article packet and generates tailored versions for LinkedIn,
Discord, Telegram, X (Twitter), and Threads. Supports threading for short-form
platforms and automatically downloads news hero images from Google.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

load_dotenv()

from live_contentops.ai_research_canonical_article_engine_v6 import (
    call_live_provider,
    parse_llm_json,
)
from live_contentops.google_image_search_v6 import (
    execute_google_image_search_and_download,
)

TASK_LABEL = "TASK_CONTENTOPS_V6_PLATFORM_NATIVE_VARIANT_GENERATOR_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_ARTICLE_PACKET = Path("docs/automation/V6_CANONICAL_SUBSTACK_ARTICLE/canonical_article_packet.json")
DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_PLATFORM_NATIVE_VARIANTS")
DEFAULT_PACKET_OUTPUT = DEFAULT_OUTPUT_DIR / "platform_variant_packet.json"


def compute_packet_hash(data: dict[str, Any]) -> str:
    clone = dict(data)
    clone.pop("platform_variant_packet_id", None)
    clone.pop("exact_payload_hash", None)
    serialized = json.dumps(clone, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def _contains_placeholder(text: str) -> bool:
    return any(marker in text.lower() for marker in ("stub", "scaffold", "placeholder", "lorem ipsum"))


def _contains_advice_phrase(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in (
        "you should buy",
        "you should sell",
        "buy now",
        "sell now",
        "guaranteed return",
        "risk-free return",
        "not financial advice but",
    ))


def _has_no_advice_context(text: str) -> bool:
    lowered = text.lower()
    return "not investment advice" in lowered or "without giving investment advice" in lowered or "educational" in lowered


def _generic_variant(text: str) -> bool:
    lowered = text.lower()
    return lowered.count("capital chronicle") == 0 and not any(term in lowered for term in ("macro", "policy", "shipping", "liquidity", "geopolitic", "yield", "data"))


def validate_platform_variants(variants: dict[str, str], variant_threads: dict[str, list[str]], live_run: bool = True) -> list[str]:
    required = {
        "substack": 1200,
        "linkedin": 120,
        "facebook": 120,
        "discord": 80,
        "telegram": 60,
        "threads": 80,
        "instagram_caption": 80,
    }
    failures: list[str] = []
    for platform, min_len in required.items():
        text = str(variants.get(platform, "")).strip()
        if len(text) < min_len:
            failures.append(f"{platform}_too_short:{len(text)}<{min_len}")
        if _contains_placeholder(text):
            failures.append(f"{platform}_placeholder_detected")
        if _contains_advice_phrase(text):
            failures.append(f"{platform}_financial_advice_phrase_detected")
        if platform in {"substack", "linkedin", "facebook", "instagram_caption"} and not _has_no_advice_context(text):
            failures.append(f"{platform}_no_advice_context_missing")
        if platform != "substack" and _generic_variant(text):
            failures.append(f"{platform}_generic_language_detected")
    limits = {"x": 280, "threads": 500}
    for platform in ("x", "threads"):
        thread = [str(item).strip() for item in variant_threads.get(platform, []) if str(item).strip()]
        if not thread:
            failures.append(f"{platform}_thread_missing")
        if any(_contains_placeholder(item) for item in thread):
            failures.append(f"{platform}_thread_placeholder_detected")
        if any(_contains_advice_phrase(item) for item in thread):
            failures.append(f"{platform}_thread_financial_advice_phrase_detected")
        for idx, item in enumerate(thread, start=1):
            if len(item) > limits[platform]:
                failures.append(f"{platform}_thread_item_too_long:{idx}:{len(item)}>{limits[platform]}")
    return failures


def summarize_validation(failures: list[str]) -> dict[str, Any]:
    blocked_platforms = sorted({failure.split("_", 1)[0] for failure in failures})
    return {
        "failure_count": len(failures),
        "blocked_platforms": blocked_platforms,
        "ready": not failures,
    }


def _fallback_variants(title: str, subtitle: str, body_text: str) -> tuple[dict[str, str], dict[str, list[str]]]:
    short = re.sub(r"\s+", " ", body_text).strip()
    summary = short[:900].rsplit(" ", 1)[0] if len(short) > 900 else short
    linkedin = f"{title}\n\n{subtitle}\n\n{summary}\n\nCapital Chronicle frames this as educational macro context, not investment advice."
    discord = f"**{title}**\n\n{summary[:1200]}\n\nDiscuss the data, assumptions, and transmission channels."
    telegram = f"Capital Chronicle: {title}\n\n{summary[:850]}"
    facebook = f"{title}\n\n{subtitle}\n\n{summary[:1600]}\n\nEducational macro analysis from Capital Chronicle."
    instagram_caption = f"{title}\n\n{summary[:1800]}\n\n#CapitalChronicle #Macro #Geopolitics"
    x_thread = []
    chunks = [summary[i:i + 230].strip() for i in range(0, min(len(summary), 1600), 230)]
    for idx, chunk in enumerate(chunks[:8], start=1):
        x_thread.append(f"{idx}/ {chunk}" if idx == 1 else f"{idx}/ {chunk}")
    threads_thread = [chunk for chunk in [summary[i:i + 450].strip() for i in range(0, min(len(summary), 2200), 450)] if chunk]
    return {
        "substack": body_text,
        "linkedin": linkedin,
        "facebook": facebook,
        "discord": discord,
        "telegram": telegram,
        "x": "\n\n---\n\n".join(x_thread),
        "threads": "\n\n---\n\n".join(threads_thread),
        "instagram_caption": instagram_caption,
    }, {"x": x_thread, "threads": threads_thread}


def generate_live_platform_variants(
    article_packet_path: str | Path = DEFAULT_ARTICLE_PACKET,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    live_run: bool = False,
    timeout_seconds: int = 20
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        with open(article_packet_path, "r", encoding="utf-8") as f:
            article_data = json.load(f)
    except Exception as exc:
        print(f"[Warning] Failed to load canonical article: {exc}")
        article_data = {}

    article_draft = article_data.get("canonical_article_draft", {})
    title = article_draft.get("title", "Capital Chronicle Macro Volatility Briefing")
    subtitle = article_draft.get("subtitle", "Process-led macro analysis")
    intro = article_draft.get("intro", "")
    conclusion = article_draft.get("conclusion", "")
    sections = article_draft.get("sections", [])
    body_text = f"{intro}\n\n"
    for section in sections:
        body_text += f"### {section.get('title')}\n{section.get('body')}\n\n"
    body_text += conclusion

    variants, variant_threads = _fallback_variants(title, subtitle, body_text)
    image_path = None
    public_image_url = None
    provider_call_made = False
    provider_recovery_used = False
    provider_attempts: list[dict[str, Any]] = []
    validation_failures: list[str] = []

    try:
        image_path, public_image_url = execute_google_image_search_and_download(title)
    except Exception as e:
        print(f"[Warning] Google Image search failed: {e}")

    if live_run:
        api_key = os.environ.get("NINE_ROUTER_API_KEY")
        if not api_key:
            validation_failures.append("NINE_ROUTER_API_KEY_missing")
        else:
            prompt = (
                f"You are a platform content editor for Capital Chronicle. Convert this canonical article into platform-native posts.\n"
                f"Title: {title}\nSubtitle: {subtitle}\nArticle:\n{body_text}\n\n"
                f"Return ONLY raw JSON: {{\"linkedin\": str, \"facebook\": str, \"discord\": str, \"telegram\": str, "
                f"\"instagram_caption\": str, \"x_thread\": [str], \"threads_thread\": [str]}}.\n"
                f"Rules: no stubs/placeholders, no financial advice, concrete article-specific language, X posts <= 280 chars, Threads posts <= 500 chars."
            )
            try:
                llm_text = call_live_provider(prompt, "9router", timeout_seconds)
                provider_call_made = True
                llm_data = parse_llm_json(llm_text) or {}
                if not llm_data:
                    provider_attempts.append({"provider": "9router", "status": "failed", "failure": "variant_provider_json_parse_empty", "timeout_seconds": timeout_seconds})
                    validation_failures.append("variant_provider_json_parse_empty")
                else:
                    provider_attempts.append({"provider": "9router", "status": "accepted", "failure": None, "timeout_seconds": timeout_seconds})
                for key in ("linkedin", "facebook", "discord", "telegram", "instagram_caption"):
                    if llm_data.get(key):
                        variants[key] = str(llm_data[key])
                if llm_data.get("x_thread"):
                    variant_threads["x"] = [str(x) for x in llm_data["x_thread"]]
                    variants["x"] = "\n\n---\n\n".join(variant_threads["x"])
                if llm_data.get("threads_thread"):
                    variant_threads["threads"] = [str(x) for x in llm_data["threads_thread"]]
                    variants["threads"] = "\n\n---\n\n".join(variant_threads["threads"])
            except Exception as exc:
                provider_call_made = True
                provider_recovery_used = True
                provider_attempts.append({"provider": "9router", "status": "failed", "failure": f"variant_provider_failed:{type(exc).__name__}:{exc}", "timeout_seconds": timeout_seconds})
                validation_failures.append(f"variant_provider_failed:{type(exc).__name__}:{exc}")

    validation_failures.extend(validate_platform_variants(variants, variant_threads, live_run=live_run))
    validation_summary = summarize_validation(validation_failures)
    variant_status = "VARIANT_READY" if not validation_failures else "VARIANT_VALIDATION_FAILED"

    for plat, text in variants.items():
        suffix = "telegram_operator_preview.md" if plat == "telegram" else f"{plat}_variant.md"
        out_file = output_dir / suffix
        out_file.write_text("\n".join([
            f"# {plat.upper()} NATIVE VARIANT",
            f"- **Status**: {variant_status}",
            f"- **Associated Image**: {image_path or 'None'}",
            f"- **Timestamp**: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            text,
        ]) + "\n", encoding="utf-8")

    packet = {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "source_article_id": article_data.get("packet_id"),
        "source_intent_id": article_data.get("operator_idea_id"),
        "variant_status": variant_status,
        "variant_stage": "platform_native_validated" if not validation_failures else "platform_native_validation_failed",
        "target_platforms": ["substack", "discord", "linkedin", "facebook", "x", "threads", "telegram", "instagram"],
        "variants": variants,
        "variant_threads": variant_threads,
        "image_path": str(image_path) if image_path else None,
        "public_image_url": public_image_url,
        "provider_call_made": provider_call_made,
        "provider_recovery_used": provider_recovery_used,
        "provider_attempts": provider_attempts,
        "validation_failures": validation_failures,
        "validation_summary": validation_summary,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())
    }
    packet["platform_variant_packet_id"] = f"variant_packet_{compute_packet_hash(packet)[:12]}"
    packet["exact_payload_hash"] = compute_packet_hash(packet)
    write_json(output_dir / "platform_variant_packet.json", packet)
    try:
        write_json(Path("ui/contentops_v5/src/data/platform_variant_packet.json"), packet)
        print("[Info] Copied variant packet to UI src/data folder")
    except Exception as e:
        print(f"[Warning] Failed to copy variant packet to UI src/data: {e}")
    return packet


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Live Platform Variant Generator")
    parser.add_argument("--article-packet", default=str(DEFAULT_ARTICLE_PACKET))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--live-run", action="store_true", help="Run 9router live generation")
    args = parser.parse_args(argv)
    
    packet = generate_live_platform_variants(
        article_packet_path=args.article_packet,
        output_dir=args.output_dir,
        live_run=args.live_run
    )
    
    print(json.dumps({
        "platform_variant_packet_id": packet["platform_variant_packet_id"],
        "variant_status": packet["variant_status"],
        "image_path": packet["image_path"],
        "provider_call_made": packet["provider_call_made"]
    }, indent=2))
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
