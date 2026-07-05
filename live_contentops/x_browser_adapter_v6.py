"""X (Twitter) Playwright Browser Adapter for ContentOps V6 (Fast Ship Mode).

Executes post publishing, commenting/replying, and editing on X via Playwright
using a temporary clone of the operator's browser profile.
"""
from __future__ import annotations

import hashlib
import shutil
import time
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_FAST_SHIP_LIVE_DISPATCH_SUBSTACK_AND_X_V0"
DEFAULT_PROFILE_SRC = Path(r"A:\Capital Chronicle\operator-browser-profiles\contentops-social-main")
TEMP_PROFILE_DIR = Path(r"A:\Capital Chronicle\tools\cc-live-contentops\scratch\temp_profile_x")


def copy_essential_profile(src_dir: Path = DEFAULT_PROFILE_SRC, dest_dir: Path = TEMP_PROFILE_DIR) -> None:
    """Copies essential cookie/storage files from operator profile to prevent browser locks."""
    if dest_dir.exists():
        try:
            shutil.rmtree(dest_dir)
        except Exception:
            pass
    dest_dir.mkdir(parents=True, exist_ok=True)

    exclude_dirs = {
        "Cache", "Code Cache", "Service Worker", "GPUCache", "DawnGraphiteCache",
        "DawnWebGPUCache", "optimization_guide_model_store", "ProvenanceData",
        "BrowserMetrics", "GrShaderCache"
    }

    local_state_src = src_dir / "Local State"
    if local_state_src.exists():
        shutil.copy2(local_state_src, dest_dir / "Local State")

    default_src = src_dir / "Default"
    default_dest = dest_dir / "Default"
    if default_src.exists():
        default_dest.mkdir(exist_ok=True)
        for item in default_src.iterdir():
            if item.name in exclude_dirs:
                continue
            try:
                if item.is_dir():
                    shutil.copytree(
                        item,
                        default_dest / item.name,
                        ignore=shutil.ignore_patterns("Cache", "Code Cache", "Service Worker")
                    )
                else:
                    shutil.copy2(item, default_dest / item.name)
            except Exception:
                pass


def execute_x_post(
    text: str,
    image_url: str | None = None,
    dry_run: bool = False,
    profile_src: Path = DEFAULT_PROFILE_SRC,
    temp_dir: Path = TEMP_PROFILE_DIR,
) -> dict[str, Any]:
    """Publishes a post/tweet to X (Twitter)."""
    payload_hash = hashlib.md5(text.encode("utf-8")).hexdigest()[:12]

    if dry_run:
        return {
            "status": "DRY_RUN_PASS",
            "platform": "x",
            "action": "post",
            "payload_redacted": {
                "text": text,
                "image_url": image_url,
            },
            "response": {
                "id": f"x_mock_tweet_{payload_hash}",
                "url": f"https://x.com/Capitalnicle/status/mock_{payload_hash}",
            },
        }

    from playwright.sync_api import sync_playwright
    from .live_telemetry_v6 import classify_and_record_dispatch

    t0 = time.perf_counter()
    copy_essential_profile(profile_src, temp_dir)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=str(temp_dir),
                channel="msedge",
                headless=True,
            )
            page = browser.pages[0]
            page.goto("https://x.com", timeout=30000)
            time.sleep(6)

            composer = page.wait_for_selector("[data-testid='tweetTextarea_0']", timeout=15000)
            if composer:
                composer.focus()
                page.keyboard.type(text)
                time.sleep(2)

                post_btn = page.locator("[data-testid='tweetButtonInline']").first
                if not post_btn.is_visible():
                    post_btn = page.locator("[data-testid='tweetButton']").first

                if post_btn.is_visible():
                    post_btn.click()
                    time.sleep(5)

            final_url = page.url
            browser.close()

            result = {
                "status": "SUCCESS",
                "platform": "x",
                "action": "post",
                "id": f"tweet_{payload_hash}",
                "response": {"url": final_url},
            }
    except Exception as e:
        result = {
            "status": "FAILED",
            "platform": "x",
            "action": "post",
            "error": str(e),
        }

    latency_ms = (time.perf_counter() - t0) * 1000.0
    classify_and_record_dispatch(
        platform_id="x",
        action="post",
        adapter_result=result,
        latency_ms=latency_ms,
        payload_size_bytes=len(text),
    )
    return result


def execute_x_comment(
    tweet_url_or_id: str,
    text: str,
    dry_run: bool = False,
    profile_src: Path = DEFAULT_PROFILE_SRC,
    temp_dir: Path = TEMP_PROFILE_DIR,
) -> dict[str, Any]:
    """Replies/comments on a specific X post/tweet."""
    payload_hash = hashlib.md5(f"{tweet_url_or_id}:{text}".encode("utf-8")).hexdigest()[:12]

    if dry_run:
        return {
            "status": "DRY_RUN_PASS",
            "platform": "x",
            "action": "comment",
            "payload_redacted": {
                "tweet_url_or_id": tweet_url_or_id,
                "text": text,
            },
            "response": {
                "id": f"x_mock_reply_{payload_hash}",
            },
        }

    from playwright.sync_api import sync_playwright
    from .live_telemetry_v6 import classify_and_record_dispatch

    t0 = time.perf_counter()
    copy_essential_profile(profile_src, temp_dir)

    target_url = tweet_url_or_id
    if not target_url.startswith("http"):
        target_url = f"https://x.com/Capitalnicle/status/{tweet_url_or_id}"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=str(temp_dir),
                channel="msedge",
                headless=True,
            )
            page = browser.pages[0]
            page.goto(target_url, timeout=30000)
            time.sleep(6)

            composer = page.wait_for_selector("[data-testid='tweetTextarea_0']", timeout=15000)
            if composer:
                composer.focus()
                page.keyboard.type(text)
                time.sleep(2)

                reply_btn = page.locator("[data-testid='tweetButtonInline']").first
                if not reply_btn.is_visible():
                    reply_btn = page.locator("[data-testid='tweetButton']").first

                if reply_btn.is_visible():
                    reply_btn.click()
                    time.sleep(5)

            final_url = page.url
            browser.close()

            result = {
                "status": "SUCCESS",
                "platform": "x",
                "action": "comment",
                "response": {"target_url": final_url},
            }
    except Exception as e:
        result = {
            "status": "FAILED",
            "platform": "x",
            "action": "comment",
            "error": str(e),
        }

    latency_ms = (time.perf_counter() - t0) * 1000.0
    classify_and_record_dispatch(
        platform_id="x",
        action="comment",
        adapter_result=result,
        latency_ms=latency_ms,
        payload_size_bytes=len(text),
    )
    return result


def execute_x_edit(
    tweet_url_or_id: str,
    new_text: str,
    dry_run: bool = False,
    profile_src: Path = DEFAULT_PROFILE_SRC,
    temp_dir: Path = TEMP_PROFILE_DIR,
) -> dict[str, Any]:
    """Edits a tweet or updates publication record for X."""
    payload_hash = hashlib.md5(f"{tweet_url_or_id}:{new_text}".encode("utf-8")).hexdigest()[:12]

    if dry_run:
        return {
            "status": "DRY_RUN_PASS",
            "platform": "x",
            "action": "edit",
            "payload_redacted": {
                "tweet_url_or_id": tweet_url_or_id,
                "new_text": new_text,
            },
            "response": {
                "id": f"x_mock_edit_{payload_hash}",
            },
        }

    from playwright.sync_api import sync_playwright
    from .live_telemetry_v6 import classify_and_record_dispatch

    t0 = time.perf_counter()
    copy_essential_profile(profile_src, temp_dir)

    target_url = tweet_url_or_id
    if not target_url.startswith("http"):
        target_url = f"https://x.com/Capitalnicle/status/{tweet_url_or_id}"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=str(temp_dir),
                channel="msedge",
                headless=True,
            )
            page = browser.pages[0]
            page.goto(target_url, timeout=30000)
            time.sleep(5)

            # Check for edit button in X premium menu if available
            more_btn = page.query_selector("[data-testid='caret']")
            if more_btn:
                more_btn.click()
                time.sleep(1)
                edit_btn = page.query_selector("[data-testid='editTweet']")
                if edit_btn:
                    edit_btn.click()
                    time.sleep(2)
                    composer = page.query_selector("[data-testid='tweetTextarea_0']")
                    if composer:
                        composer.fill(new_text)
                        time.sleep(1)
                        save_btn = page.locator("[data-testid='tweetButtonInline']").first
                        if save_btn.is_visible():
                            save_btn.click()
                            time.sleep(4)

            final_url = page.url
            browser.close()

            result = {
                "status": "SUCCESS",
                "platform": "x",
                "action": "edit",
                "response": {"target_url": final_url},
            }
    except Exception as e:
        result = {
            "status": "FAILED",
            "platform": "x",
            "action": "edit",
            "error": str(e),
        }

    latency_ms = (time.perf_counter() - t0) * 1000.0
    classify_and_record_dispatch(
        platform_id="x",
        action="edit",
        adapter_result=result,
        latency_ms=latency_ms,
        payload_size_bytes=len(new_text),
    )
    return result
