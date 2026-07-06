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
import uuid
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

load_dotenv()

from live_contentops.ai_research_canonical_article_engine_v6 import (
    EngineInput,
    run_article_engine,
    validate_article_quality,
)
from live_contentops.platform_native_variant_generator_live_v6 import (
    generate_live_platform_variants,
    validate_platform_variants,
)

ARTICLE_OUTPUT_PATH = Path("docs/automation/V6_CANONICAL_SUBSTACK_ARTICLE/canonical_article_packet.json")
VARIANT_OUTPUT_DIR = Path("docs/automation/V6_PLATFORM_NATIVE_VARIANTS")
DISPATCH_AUDIT_PATH = VARIANT_OUTPUT_DIR / "latest_dispatch_audit.json"


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _write_dispatch_audit(payload: dict[str, Any]) -> None:
    DISPATCH_AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    DISPATCH_AUDIT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _result_url(result: dict[str, Any]) -> str | None:
    response = result.get("response") if isinstance(result.get("response"), dict) else {}
    return result.get("url") or response.get("url") or response.get("final_url")


def _normalize_dispatch_result(platform: str, result: dict[str, Any] | None = None, error: Exception | str | None = None) -> dict[str, Any]:
    result = result or {}
    status = str(result.get("status") or ("FAILED" if error else "UNKNOWN")).upper()
    err = str(error or result.get("error") or "").strip()
    ok = status in {"SUCCESS", "OK", "POSTED", "SENT"} and not err
    return {
        "platform": platform,
        "status": status,
        "ok": ok,
        "error_class": None if ok else (result.get("error_class") or type(error).__name__ if error else "dispatch_failed"),
        "error": err or None,
        "url": _result_url(result),
        "raw": result,
    }


def _blocked_result(platform: str, reason: str) -> dict[str, Any]:
    return {
        "platform": platform,
        "status": "BLOCKED",
        "ok": False,
        "error_class": "missing_payload",
        "error": reason,
        "url": None,
        "raw": {"missing": [reason]},
    }


def _dispatch_summary(results: dict[str, Any]) -> dict[str, Any]:
    flat: list[dict[str, Any]] = []
    for key, value in results.items():
        if isinstance(value, list):
            flat.extend(item for item in value if isinstance(item, dict) and "ok" in item)
        elif isinstance(value, dict) and "ok" in value:
            flat.append(value)
    attempted = [item["platform"] for item in flat]
    return {
        "attempted_platforms": attempted,
        "successful_platforms": [item["platform"] for item in flat if item.get("ok")],
        "failed_platforms": [item["platform"] for item in flat if not item.get("ok") and item.get("status") != "BLOCKED"],
        "blocked_platforms": [item["platform"] for item in flat if item.get("status") == "BLOCKED"],
    }


def _require_payload(value: Any, name: str) -> str | None:
    return None if str(value or "").strip() else f"{name}_missing"



def run_live_production_pipeline(
    topic: str,
    editorial_angle: str,
    target_audience: str = "general_financial_education",
    live_run: bool = False,
    dispatch_live: bool = False,
    timeout_seconds: int = 30
) -> dict[str, Any]:
    run_id = f"v6_pipeline_{uuid.uuid4().hex[:12]}"
    print(f"[Info] Starting V6 production run {run_id} for topic: '{topic}' (live={live_run}, dispatch={dispatch_live})")

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

    ARTICLE_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ARTICLE_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(article_packet, f, indent=2, sort_keys=True)
    print(f"[Info] Saved canonical article packet to: {ARTICLE_OUTPUT_PATH}")

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
        "run_id": run_id,
        "pipeline_status": "GENERATED",
        "article_packet_id": article_packet.get("packet_id"),
        "platform_variant_packet_id": variant_packet.get("platform_variant_packet_id"),
        "image_path": variant_packet.get("image_path"),
        "public_image_url": public_image_url,
        "variant_status": variant_packet.get("variant_status"),
        "timestamp": _utc_now(),
        "timestamp_gmt7": time.strftime("%Y-%m-%dT%H:%M:%S+07:00", time.gmtime(time.time() + 7 * 3600)),
        "dispatch_audit_path": str(DISPATCH_AUDIT_PATH),
    }

    article_failures = validate_article_quality(article_packet.get("canonical_article_draft", {}), min_chars=5000) if live_run else []
    variant_failures = validate_platform_variants(variants, variant_threads, live_run=live_run) if live_run else []
    variant_failures.extend(variant_packet.get("validation_failures") or [])
    blockers = list(article_packet.get("blockers") or []) + article_failures + variant_failures
    if dispatch_live and blockers:
        ret.update({
            "pipeline_status": "DISPATCH_BLOCKED",
            "dispatch_live": False,
            "dispatch_blocked": True,
            "dispatch_blockers": blockers,
            "dispatch_summary": {
                "attempted_platforms": [],
                "successful_platforms": [],
                "failed_platforms": [],
                "blocked_platforms": ["pipeline"],
            },
        })
        _write_dispatch_audit(ret)
        return ret

    if dispatch_live:
        print("[Info] Starting automated live dispatches for Substack, LinkedIn, X, and Instagram...")
        dispatch_results: dict[str, Any] = {}

        try:
            from live_contentops.substack_browser_adapter_v6 import execute_substack_post
            body = variants.get("substack", "")
            missing = _require_payload(body, "substack_body")
            if missing:
                dispatch_results["substack"] = _blocked_result("substack", missing)
            else:
                print("[Info] Dispatching to Substack...")
                sub_res = execute_substack_post(
                    title=article_packet.get("canonical_article_draft", {}).get("title", topic),
                    subtitle=article_packet.get("canonical_article_draft", {}).get("subtitle", ""),
                    body_markdown=body,
                    dry_run=False
                )
                dispatch_results["substack"] = _normalize_dispatch_result("substack", sub_res)
                print(f"[Info] Substack dispatch outcome: {dispatch_results['substack']['status']} (URL: {dispatch_results['substack'].get('url')})")
        except Exception as exc:
            print(f"[Warning] Substack dispatch failed: {exc}")
            dispatch_results["substack"] = _normalize_dispatch_result("substack", error=exc)

        time.sleep(5)

        try:
            from live_contentops.linkedin_browser_adapter_v6 import execute_linkedin_post
            text = variants.get("linkedin", "")
            missing = _require_payload(text, "linkedin_text")
            if missing:
                dispatch_results["linkedin"] = _blocked_result("linkedin", missing)
            else:
                print("[Info] Dispatching to LinkedIn...")
                li_res = execute_linkedin_post(text=text, dry_run=False)
                dispatch_results["linkedin"] = _normalize_dispatch_result("linkedin", li_res)
                print(f"[Info] LinkedIn dispatch outcome: {dispatch_results['linkedin']['status']} (URL: {dispatch_results['linkedin'].get('url')})")
        except Exception as exc:
            print(f"[Warning] LinkedIn dispatch failed: {exc}")
            dispatch_results["linkedin"] = _normalize_dispatch_result("linkedin", error=exc)

        time.sleep(5)

        try:
            from live_contentops.x_browser_adapter_v6 import execute_x_post, execute_x_comment
            x_thread = [str(item).strip() for item in variant_threads.get("x", []) if str(item).strip()]
            if not x_thread:
                dispatch_results["x_post"] = _blocked_result("x_post", "x_thread_missing")
                dispatch_results["x_replies"] = []
            else:
                print(f"[Info] Dispatching thread of {len(x_thread)} tweets to X...")
                x_res = execute_x_post(text=x_thread[0], dry_run=False)
                dispatch_results["x_post"] = _normalize_dispatch_result("x_post", x_res)
                print(f"[Info] X initial post outcome: {dispatch_results['x_post']['status']}")

                comment_results = []
                if dispatch_results["x_post"].get("ok"):
                    post_url = dispatch_results["x_post"].get("url") or ""
                    tweet_id = post_url.split("/status/")[-1] if "/status/" in post_url else ""
                    target_ref = post_url if post_url else tweet_id
                    for idx, comment_text in enumerate(x_thread[1:], start=1):
                        time.sleep(6)
                        print(f"[Info] Dispatching thread reply {idx}/{len(x_thread) - 1}...")
                        try:
                            rep_res = execute_x_comment(tweet_url_or_id=target_ref, text=comment_text, dry_run=False)
                            comment_results.append(_normalize_dispatch_result(f"x_reply_{idx}", rep_res))
                        except Exception as exc:
                            comment_results.append(_normalize_dispatch_result(f"x_reply_{idx}", error=exc))
                dispatch_results["x_replies"] = comment_results
        except Exception as exc:
            print(f"[Warning] X thread dispatch failed: {exc}")
            dispatch_results["x"] = _normalize_dispatch_result("x", error=exc)

        time.sleep(5)

        try:
            from live_contentops.instagram_adapter_v6 import execute_instagram_post
            caption = variants.get("instagram_caption", variants.get("telegram", ""))
            fallback_img = "https://cdn.corporatefinanceinstitute.com/assets/geopolitics.jpeg"
            active_img = public_image_url if public_image_url else fallback_img
            missing = _require_payload(caption, "instagram_caption") or _require_payload(active_img, "instagram_image_url")
            if missing:
                dispatch_results["instagram"] = _blocked_result("instagram", missing)
            else:
                print("[Info] Dispatching to Instagram...")
                ig_res = execute_instagram_post(image_url=active_img, caption=caption, dry_run=False)
                dispatch_results["instagram"] = _normalize_dispatch_result("instagram", ig_res)
                print(f"[Info] Instagram dispatch outcome: {dispatch_results['instagram']['status']}")
        except Exception as exc:
            print(f"[Warning] Instagram dispatch failed: {exc}")
            dispatch_results["instagram"] = _normalize_dispatch_result("instagram", error=exc)

        time.sleep(5)

        try:
            from live_contentops.facebook_page_adapter_v6 import execute_facebook_post
            message = variants.get("facebook", variants.get("linkedin", ""))
            missing = _require_payload(message, "facebook_message")
            if missing:
                dispatch_results["facebook"] = _blocked_result("facebook", missing)
            else:
                print("[Info] Dispatching to Facebook Page...")
                fb_res = execute_facebook_post(message=message, dry_run=False)
                dispatch_results["facebook"] = _normalize_dispatch_result("facebook", fb_res)
                print(f"[Info] Facebook dispatch outcome: {dispatch_results['facebook']['status']}")
        except Exception as exc:
            print(f"[Warning] Facebook dispatch failed: {exc}")
            dispatch_results["facebook"] = _normalize_dispatch_result("facebook", error=exc)

        time.sleep(5)

        try:
            from live_contentops.telegram_live_adapter_v6 import execute_telegram_post
            message = variants.get("telegram", "")
            missing = _require_payload(message, "telegram_message")
            if missing:
                dispatch_results["telegram"] = _blocked_result("telegram", missing)
            else:
                print("[Info] Dispatching to Telegram Channel...")
                tg_res = execute_telegram_post(message=message, dry_run=False)
                dispatch_results["telegram"] = _normalize_dispatch_result("telegram", tg_res)
                print(f"[Info] Telegram dispatch outcome: {dispatch_results['telegram']['status']}")
        except Exception as exc:
            print(f"[Warning] Telegram dispatch failed: {exc}")
            dispatch_results["telegram"] = _normalize_dispatch_result("telegram", error=exc)

        time.sleep(5)

        try:
            from live_contentops.threads_adapter_v6 import execute_threads_post
            threads_sequence = [str(item).strip() for item in variant_threads.get("threads", []) if str(item).strip()]
            if not threads_sequence:
                dispatch_results["threads"] = _blocked_result("threads", "threads_thread_missing")
                dispatch_results["threads_replies"] = []
            else:
                print("[Info] Dispatching to Threads...")
                threads_res = execute_threads_post(text=threads_sequence[0], dry_run=False)
                dispatch_results["threads"] = _normalize_dispatch_result("threads", threads_res)
                thread_reply_results = []
                parent_id = threads_res.get("id") or threads_res.get("container_id")
                if dispatch_results["threads"].get("ok") and parent_id:
                    for idx, reply_text in enumerate(threads_sequence[1:], start=1):
                        time.sleep(6)
                        print(f"[Info] Dispatching Threads reply {idx}/{len(threads_sequence) - 1}...")
                        try:
                            thread_reply_results.append(_normalize_dispatch_result(
                                f"threads_reply_{idx}",
                                execute_threads_post(text=reply_text, reply_to_id=parent_id, dry_run=False)
                            ))
                        except Exception as exc:
                            thread_reply_results.append(_normalize_dispatch_result(f"threads_reply_{idx}", error=exc))
                dispatch_results["threads_replies"] = thread_reply_results
            print(f"[Info] Threads dispatch outcome: {dispatch_results['threads'].get('status')}")
        except Exception as exc:
            print(f"[Warning] Threads dispatch failed: {exc}")
            dispatch_results["threads"] = _normalize_dispatch_result("threads", error=exc)

        time.sleep(5)

        try:
            from live_contentops.discord_live_adapter_v6 import execute_discord_post
            message = variants.get("discord", "")
            missing = _require_payload(message, "discord_message")
            if missing:
                dispatch_results["discord"] = _blocked_result("discord", missing)
            else:
                print("[Info] Dispatching to Discord Channel...")
                discord_res = execute_discord_post(message=message, dry_run=False)
                dispatch_results["discord"] = _normalize_dispatch_result("discord", discord_res)
                print(f"[Info] Discord dispatch outcome: {dispatch_results['discord']['status']}")
        except Exception as exc:
            print(f"[Warning] Discord dispatch failed: {exc}")
            dispatch_results["discord"] = _normalize_dispatch_result("discord", error=exc)

        time.sleep(5)

        summary = _dispatch_summary(dispatch_results)
        print("[Info] Automated dispatches complete.")
        ret["dispatch_live"] = True
        ret["dispatch_results"] = dispatch_results
        ret["dispatch_summary"] = summary
        ret["pipeline_status"] = "DISPATCH_COMPLETE" if not summary["failed_platforms"] and not summary["blocked_platforms"] else "DISPATCH_PARTIAL_FAILURE"
        _write_dispatch_audit(ret)

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
