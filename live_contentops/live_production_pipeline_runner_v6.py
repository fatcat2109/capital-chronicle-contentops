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
from dotenv import load_dotenv

load_dotenv()

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
    dispatch_live: bool = False,
    timeout_seconds: int = 30
) -> dict[str, Any]:
    print(f"[Info] Starting V6 production run for topic: '{topic}' (live={live_run}, dispatch={dispatch_live})")
    
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
    
    variants = variant_packet.get("variants", {})
    variant_threads = variant_packet.get("variant_threads", {})
    public_image_url = variant_packet.get("public_image_url")
    
    ret = {
        "article_packet_id": article_packet.get("packet_id"),
        "platform_variant_packet_id": variant_packet.get("platform_variant_packet_id"),
        "image_path": variant_packet.get("image_path"),
        "public_image_url": public_image_url,
        "variant_status": variant_packet.get("variant_status"),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    # 3. Perform automated live dispatches if requested
    if dispatch_live:
        print("[Info] Starting automated live dispatches for Substack, LinkedIn, X, and Instagram...")
        dispatch_results = {}
        
        # A. Substack Newsletter
        try:
            from live_contentops.substack_browser_adapter_v6 import execute_substack_post
            print("[Info] Dispatching to Substack...")
            sub_res = execute_substack_post(
                title=article_packet.get("canonical_article_draft", {}).get("title", topic),
                subtitle=article_packet.get("canonical_article_draft", {}).get("subtitle", ""),
                body_markdown=variants.get("substack", ""),
                dry_run=False
            )
            dispatch_results["substack"] = sub_res
            print(f"[Info] Substack dispatch outcome: {sub_res.get('status')} (URL: {sub_res.get('url') or sub_res.get('response', {}).get('final_url')})")
        except Exception as exc:
            print(f"[Warning] Substack dispatch failed: {exc}")
            dispatch_results["substack"] = {"status": "FAILED", "error": str(exc)}
            
        time.sleep(5)
        
        # B. LinkedIn
        try:
            from live_contentops.linkedin_browser_adapter_v6 import execute_linkedin_post
            print("[Info] Dispatching to LinkedIn...")
            li_res = execute_linkedin_post(
                text=variants.get("linkedin", ""),
                dry_run=False
            )
            dispatch_results["linkedin"] = li_res
            print(f"[Info] LinkedIn dispatch outcome: {li_res.get('status')} (URL: {li_res.get('response', {}).get('url')})")
        except Exception as exc:
            print(f"[Warning] LinkedIn dispatch failed: {exc}")
            dispatch_results["linkedin"] = {"status": "FAILED", "error": str(exc)}
            
        time.sleep(5)
        
        # C. X (Twitter) thread
        try:
            from live_contentops.x_browser_adapter_v6 import execute_x_post, execute_x_comment
            x_thread = variant_threads.get("x", [])
            if x_thread:
                print(f"[Info] Dispatching thread of {len(x_thread)} tweets to X...")
                first_tweet = x_thread[0]
                x_res = execute_x_post(
                    text=first_tweet,
                    dry_run=False
                )
                dispatch_results["x_post"] = x_res
                print(f"[Info] X initial post outcome: {x_res.get('status')}")
                
                if x_res.get("status") == "SUCCESS":
                    post_url = x_res.get("response", {}).get("url", "")
                    tweet_id = post_url.split("/status/")[-1] if "/status/" in post_url else ""
                    target_ref = post_url if post_url else tweet_id
                    
                    comment_results = []
                    for idx, comment_text in enumerate(x_thread[1:]):
                        time.sleep(6)
                        print(f"[Info] Dispatching thread reply {idx + 1}/{len(x_thread) - 1}...")
                        rep_res = execute_x_comment(
                            tweet_url_or_id=target_ref,
                            text=comment_text,
                            dry_run=False
                        )
                        comment_results.append(rep_res)
                    dispatch_results["x_replies"] = comment_results
            else:
                print("[Warning] No tweets found in X thread sequence.")
        except Exception as exc:
            print(f"[Warning] X thread dispatch failed: {exc}")
            dispatch_results["x"] = {"status": "FAILED", "error": str(exc)}
            
        time.sleep(5)
        
        # D. Instagram
        try:
            from live_contentops.instagram_adapter_v6 import execute_instagram_post
            print("[Info] Dispatching to Instagram...")
            fallback_img = "https://cdn.corporatefinanceinstitute.com/assets/geopolitics.jpeg"
            active_img = public_image_url if public_image_url else fallback_img
            ig_res = execute_instagram_post(
                image_url=active_img,
                caption=variants.get("telegram", "Capital Chronicle Macro Update"),
                dry_run=False
            )
            dispatch_results["instagram"] = ig_res
            print(f"[Info] Instagram dispatch outcome: {ig_res.get('status')}")
        except Exception as exc:
            print(f"[Warning] Instagram dispatch failed: {exc}")
            dispatch_results["instagram"] = {"status": "FAILED", "error": str(exc)}
            
        time.sleep(5)
        
        # E. Facebook Page Feed
        try:
            from live_contentops.facebook_page_adapter_v6 import execute_facebook_post
            print("[Info] Dispatching to Facebook Page...")
            fb_res = execute_facebook_post(
                message=variants.get("linkedin", ""),
                dry_run=False
            )
            dispatch_results["facebook"] = fb_res
            print(f"[Info] Facebook dispatch outcome: {fb_res.get('status')}")
        except Exception as exc:
            print(f"[Warning] Facebook dispatch failed: {exc}")
            dispatch_results["facebook"] = {"status": "FAILED", "error": str(exc)}
            
        time.sleep(5)
        
        # F. Telegram Channel
        try:
            from live_contentops.telegram_live_adapter_v6 import execute_telegram_post
            print("[Info] Dispatching to Telegram Channel...")
            tg_res = execute_telegram_post(
                message=variants.get("telegram", ""),
                dry_run=False
            )
            dispatch_results["telegram"] = tg_res
            print(f"[Info] Telegram dispatch outcome: {tg_res.get('status')}")
        except Exception as exc:
            print(f"[Warning] Telegram dispatch failed: {exc}")
            dispatch_results["telegram"] = {"status": "FAILED", "error": str(exc)}
            
        time.sleep(5)
        
        # G. Threads Post
        try:
            from live_contentops.threads_adapter_v6 import execute_threads_post
            print("[Info] Dispatching to Threads...")
            threads_res = execute_threads_post(
                text=variants.get("threads", ""),
                dry_run=False
            )
            dispatch_results["threads"] = threads_res
            print(f"[Info] Threads dispatch outcome: {threads_res.get('status')}")
        except Exception as exc:
            print(f"[Warning] Threads dispatch failed: {exc}")
            dispatch_results["threads"] = {"status": "FAILED", "error": str(exc)}
            
        time.sleep(5)
        
        # H. Discord Announcement
        try:
            from live_contentops.discord_live_adapter_v6 import execute_discord_post
            print("[Info] Dispatching to Discord Channel...")
            discord_res = execute_discord_post(
                message=variants.get("discord", ""),
                dry_run=False
            )
            dispatch_results["discord"] = discord_res
            print(f"[Info] Discord dispatch outcome: {discord_res.get('status')}")
        except Exception as exc:
            print(f"[Warning] Discord dispatch failed: {exc}")
            dispatch_results["discord"] = {"status": "FAILED", "error": str(exc)}
            
        time.sleep(5)
            
        print("[Info] Automated dispatches complete.")
        ret["dispatch_live"] = True
        ret["dispatch_results"] = dispatch_results
        
    return ret


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Live Production Pipeline Runner")
    parser.add_argument("--topic", default="US recession risks rise as oil volatility spikes", help="Topic idea")
    parser.add_argument("--angle", default="Focus on data transparency, geopolitics, and yield curves.", help="Editorial angle")
    parser.add_argument("--live-run", action="store_true", help="Enable 9router LLM and live searches")
    parser.add_argument("--dispatch-live", action="store_true", help="Enable live posting/publishing to all platforms")
    args = parser.parse_args(argv)
    
    result = run_live_production_pipeline(
        topic=args.topic,
        editorial_angle=args.angle,
        live_run=args.live_run,
        dispatch_live=args.dispatch_live
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
