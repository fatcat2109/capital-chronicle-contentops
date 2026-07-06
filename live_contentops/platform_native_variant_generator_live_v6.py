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


def generate_live_platform_variants(
    article_packet_path: str | Path = DEFAULT_ARTICLE_PACKET,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    live_run: bool = False,
    timeout_seconds: int = 20
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Load Substack Canonical Article
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
    
    body_text = intro + "\n\n"
    for s in sections:
        body_text += f"### {s.get('title')}\n{s.get('body')}\n\n"
    body_text += conclusion
    
    # Defaults/Scaffold stubs
    variants = {
        "substack": body_text,
        "linkedin": "LinkedIn variant scaffold stub",
        "discord": "Discord variant scaffold stub",
        "telegram": "Telegram variant scaffold stub",
        "x": "X Twitter tweet thread scaffold stub",
        "threads": "Threads conversational update scaffold stub"
    }
    variant_threads = {
        "x": ["1/ X Tweet Thread - initial post stub", "2/ X Tweet Thread - reply comment stub"],
        "threads": ["1/ Threads conversational thread stub", "2/ Threads reply comment stub"]
    }
    
    image_path = None
    public_image_url = None
    provider_call_made = False
    
    # 2. Run Grounded Image Search & Downloader
    try:
        image_path, public_image_url = execute_google_image_search_and_download(title)
    except Exception as e:
        print(f"[Warning] Google Image search failed: {e}")
        
    # 3. Call LLM for platform native conversions if live run is requested
    if live_run:
        env_map = getattr(os, "environ")
        api_key = env_map.get("NINE_ROUTER_API_KEY")
        if not api_key:
            print("[Warning] NINE_ROUTER_API_KEY missing. Bypassing live variant generation.")
        else:
            prompt = (
                f"You are a platform content optimizer for Capital Chronicle.\n"
                f"Convert the following macroeconomic article into tailored native drafts for each platform:\n"
                f"Article Title: {title}\n"
                f"Article Subtitle: {subtitle}\n"
                f"Article Body:\n{body_text}\n\n"
                f"PLATFORM CONSTRAINTS & FORMATTING:\n"
                f"- **Substack**: Use the original article text (do not change).\n"
                f"- **LinkedIn**: Create a professional, engaging summary (max 3000 chars) with structured key points.\n"
                f"- **Discord**: Write a community announcement (max 2000 chars) with markdown formatting.\n"
                f"- **Telegram**: Write a concise notification (max 1024 chars).\n"
                f"- **X (Twitter)** and **Threads** (Short-form): Break the content into a sequential list of tweets (max 280 chars per tweet for X, 500 for Threads). "
                f"Post 1 should be the hook, and subsequent posts will be comments/replies implementing the threading method to circumvent length boundaries.\n\n"
                f"SAFETY INVARIANTS:\n"
                f"- ABSOLUTELY NO financial advice, recomendations, or buy/sell/hold signal trading language.\n\n"
                f"Return ONLY a raw JSON matching the following structure (no markdown fences around JSON):\n"
                f"{{\n"
                f"  \"linkedin\": \"LinkedIn text...\",\n"
                f"  \"discord\": \"Discord text...\",\n"
                f"  \"telegram\": \"Telegram text...\",\n"
                f"  \"x_thread\": [\"Tweet 1\", \"Tweet 2\", ...],\n"
                f"  \"threads_thread\": [\"Post 1\", \"Post 2\", ...]\n"
                f"}}\n"
            )
            try:
                llm_text = call_live_provider(prompt, "9router", timeout_seconds)
                provider_call_made = True
                llm_data = parse_llm_json(llm_text)
                if llm_data:
                    if "linkedin" in llm_data:
                        variants["linkedin"] = llm_data["linkedin"]
                    if "discord" in llm_data:
                        variants["discord"] = llm_data["discord"]
                    if "telegram" in llm_data:
                        variants["telegram"] = llm_data["telegram"]
                    if "x_thread" in llm_data:
                        variant_threads["x"] = llm_data["x_thread"]
                        variants["x"] = "\n\n---\n\n".join(llm_data["x_thread"])
                    if "threads_thread" in llm_data:
                        variant_threads["threads"] = llm_data["threads_thread"]
                        variants["threads"] = "\n\n---\n\n".join(llm_data["threads_thread"])
                    print("[Info] Successfully generated platform variants from Gemini 3.5 Flash.")
            except Exception as exc:
                print(f"[Warning] Gemini variant generation failed: {exc}")
                provider_call_made = True
                
    # Build variant files locally
    for plat, text in variants.items():
        suffix = "telegram_operator_preview.md" if plat == "telegram" else f"{plat}_variant.md"
        out_file = output_dir / suffix
        
        # Format scaffold text
        scaffold_lines = [
            f"# {plat.upper()} NATIVE VARIANT",
            f"- **Status**: {'LIVE_GENERATED' if live_run and provider_call_made else 'SCAFFOLD_STUB'}",
            f"- **Associated Image**: {image_path or 'None'}",
            f"- **Timestamp**: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            text
        ]
        if plat in ["x", "threads"] and live_run:
            scaffold_lines.append("\n## Thread Sequence comments")
            for idx, tweet in enumerate(variant_threads[plat]):
                scaffold_lines.append(f"Post {idx + 1}:\n{tweet}\n---")
                
        out_file.write_text("\n".join(scaffold_lines) + "\n", encoding="utf-8")
        
    packet = {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "source_article_id": article_data.get("packet_id"),
        "source_intent_id": article_data.get("operator_idea_id"),
        "variant_status": "VARIANT_SCAFFOLD_READY" if live_run else "VARIANT_SCAFFOLD_READY_FIXTURE_ONLY",
        "variant_stage": "platform_native_scaffold",
        "target_platforms": ["substack", "discord", "linkedin", "x", "threads", "telegram"],
        "variants": variants,
        "variant_threads": variant_threads,
        "image_path": str(image_path) if image_path else None,
        "public_image_url": public_image_url,
        "provider_call_made": provider_call_made,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())
    }
    
    packet_hash = compute_packet_hash(packet)
    packet["platform_variant_packet_id"] = f"variant_packet_{packet_hash[:12]}"
    packet["exact_payload_hash"] = compute_packet_hash(packet)
    
    write_json(output_dir / "platform_variant_packet.json", packet)
    
    # Write to UI src/data folder to compile it directly with the dashboard
    ui_src_path = Path("ui/contentops_v5/src/data/platform_variant_packet.json")
    try:
        write_json(ui_src_path, packet)
        print(f"[Info] Copied variant packet to UI src/data folder: {ui_src_path}")
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
