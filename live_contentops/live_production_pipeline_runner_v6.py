"""V6 Live Production Pipeline Runner.

Runs the end-to-end live generation process under Fast Ship Mode:
1. Performs grounded search on news/geopolitical topics.
2. Generates canonical Substack article using Gemini 3.5 Flash via 9router.
3. Generates platform-native variants with threading models (X, Threads) and summaries.
4. Automatically retrieves and downloads matching Google Images.
5. Saves packets cleanly to canonical output locations.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any

from live_contentops.ai_research_canonical_article_engine_v6 import (
    EngineInput,
    run_article_engine,
)
from live_contentops.platform_native_variant_generator_live_v6 import (
    generate_live_platform_variants,
)

ARTICLE_OUTPUT_PATH = Path("docs/automation/V6_CANONICAL_SUBSTACK_ARTICLE/canonical_article_packet.json")
VARIANT_OUTPUT_DIR = Path("docs/automation/V6_PLATFORM_NATIVE_VARIANTS")


def run_live_production_pipeline(
    topic: str,
    editorial_angle: str,
    target_audience: str = "general_financial_education",
    live_run: bool = False,
    timeout_seconds: int = 30
) -> dict[str, Any]:
    print(f"[Info] Starting V6 production run for topic: '{topic}' (live={live_run})")
    
    # 1. Run canonical article production engine (which calls Grounded Search automatically when live)
    inputs = EngineInput(
        operator_idea=topic,
        target_audience=target_audience,
        editorial_angle=editorial_angle,
        source_context=[],
        risk_disclaimer_policy="V6_EDUCATIONAL_DISCLAIMER",
        output_style="educational_process_heavy",
        source_notes=f"Live production run on: {topic}"
    )
    
    provider_mode = "live_provider_call" if live_run else "dry_run_fixture"
    
    article_packet = run_article_engine(
        inputs,
        provider_mode=provider_mode,
        live_provider="9router",
        provider_request_budget=2
    )
    
    # Write canonical article packet
    ARTICLE_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ARTICLE_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(article_packet, f, indent=2, sort_keys=True)
    print(f"[Info] Saved canonical article packet to: {ARTICLE_OUTPUT_PATH}")
    
    # 2. Run platform native variant generator (which downloads Google Images and creates thread layouts)
    variant_packet = generate_live_platform_variants(
        article_packet_path=ARTICLE_OUTPUT_PATH,
        output_dir=VARIANT_OUTPUT_DIR,
        live_run=live_run,
        timeout_seconds=timeout_seconds
    )
    print(f"[Info] Saved platform variant packet to: {VARIANT_OUTPUT_DIR / 'platform_variant_packet.json'}")
    
    return {
        "article_packet_id": article_packet.get("packet_id"),
        "platform_variant_packet_id": variant_packet.get("platform_variant_packet_id"),
        "image_path": variant_packet.get("image_path"),
        "variant_status": variant_packet.get("variant_status"),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Live Production Pipeline Runner")
    parser.add_argument("--topic", default="US recession risks rise as oil volatility spikes", help="Topic idea")
    parser.add_argument("--angle", default="Focus on data transparency, geopolitics, and yield curves.", help="Editorial angle")
    parser.add_argument("--live-run", action="store_true", help="Enable 9router LLM and live searches")
    args = parser.parse_args(argv)
    
    result = run_live_production_pipeline(
        topic=args.topic,
        editorial_angle=args.angle,
        live_run=args.live_run
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
