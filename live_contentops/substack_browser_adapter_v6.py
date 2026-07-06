"""Substack Playwright Browser Adapter for ContentOps V6 (Fast Ship Mode).

Executes post publishing, commenting, and editing on Substack via Playwright 
using a temporary clone of the operator's browser profile.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import time
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_FAST_SHIP_LIVE_DISPATCH_SUBSTACK_AND_X_V0"
DEFAULT_PROFILE_SRC = Path(r"A:\Capital Chronicle\operator-browser-profiles\contentops-social-main")
TEMP_PROFILE_DIR = Path(r"A:\Capital Chronicle\tools\cc-live-contentops\scratch\temp_profile_substack")


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


def execute_substack_post(
    title: str,
    subtitle: str = "",
    body_markdown: str = "",
    dry_run: bool = False,
    profile_src: Path = DEFAULT_PROFILE_SRC,
    temp_dir: Path = TEMP_PROFILE_DIR,
) -> dict[str, Any]:
    """Publishes a new long-form article to Substack."""
    payload_hash = hashlib.md5(f"{title}:{subtitle}:{body_markdown}".encode("utf-8")).hexdigest()[:12]

    if dry_run:
        return {
            "status": "DRY_RUN_PASS",
            "platform": "substack",
            "action": "post",
            "payload_redacted": {
                "title": title,
                "subtitle": subtitle,
                "body_len": len(body_markdown),
            },
            "response": {
                "id": f"substack_mock_post_{payload_hash}",
                "url": f"https://capitalchronicle.substack.com/p/mock-post-{payload_hash}",
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
            page.goto("https://capitalchronicle.substack.com/publish/post", timeout=30000)
            time.sleep(6)

            # Fill title
            title_el = page.wait_for_selector("#post-title", timeout=15000)
            if title_el:
                title_el.fill(title)

            # Fill subtitle
            if subtitle:
                subtitle_el = page.query_selector("textarea[placeholder*='subtitle']")
                if subtitle_el:
                    subtitle_el.fill(subtitle)

            # Fill body
            if body_markdown:
                editor_el = page.query_selector("div.ProseMirror")
                if editor_el:
                    editor_el.focus()
                    page.keyboard.type(body_markdown)

            time.sleep(2)
            # Click Continue / Publish button in top header
            continue_btn = None
            for selector in [
                "button:has-text('Publish')",
                "button:has-text('Publish...')",
                "button:has-text('Continue')",
                "button:has-text('Settings')",
                "a:has-text('Publish')",
            ]:
                loc = page.locator(selector).first
                if loc.is_visible():
                    continue_btn = loc
                    break

            if continue_btn:
                continue_btn.click()
                time.sleep(5)

            # Final publish button in the settings panel
            publish_btn = None
            for selector in [
                "button:has-text('Send to everyone now')",
                "button:has-text('Publish now')",
                "button:has-text('Send now')",
                "button:has-text('Publish post now')",
                "button:has-text('Confirm')",
            ]:
                loc = page.locator(selector).first
                if loc.is_visible():
                    publish_btn = loc
                    break

            if publish_btn:
                publish_btn.click()
                time.sleep(4)

                # Check for "Publish without buttons" confirm modal
                confirm_btn = None
                for selector in [
                    "button:has-text('Publish without buttons')",
                    "button:has-text('Publish now')",
                    "button:has-text('Confirm')",
                ]:
                    loc = page.locator(selector).first
                    if loc.is_visible():
                        confirm_btn = loc
                        break

                if confirm_btn:
                    confirm_btn.click()
                    time.sleep(6)

            final_url = page.url
            browser.close()

            result = {
                "status": "SUCCESS",
                "platform": "substack",
                "action": "post",
                "url": final_url,
                "id": final_url.split("/")[-1] if "/" in final_url else f"post_{payload_hash}",
                "response": {"final_url": final_url},
            }
    except Exception as e:
        result = {
            "status": "FAILED",
            "platform": "substack",
            "action": "post",
            "error": str(e),
        }

    latency_ms = (time.perf_counter() - t0) * 1000.0
    classify_and_record_dispatch(
        platform_id="substack",
        action="post",
        adapter_result=result,
        latency_ms=latency_ms,
        payload_size_bytes=len(title) + len(body_markdown),
    )
    return result


def execute_substack_comment(
    post_url_or_slug: str,
    message: str,
    dry_run: bool = False,
    profile_src: Path = DEFAULT_PROFILE_SRC,
    temp_dir: Path = TEMP_PROFILE_DIR,
) -> dict[str, Any]:
    """Posts a comment to a published Substack article."""
    if dry_run:
        return {
            "status": "DRY_RUN_PASS",
            "platform": "substack",
            "action": "comment",
            "payload_redacted": {
                "target": post_url_or_slug,
                "message": message,
            },
            "response": {
                "id": f"substack_mock_comment_{hashlib.md5(message.encode('utf-8')).hexdigest()[:8]}",
            },
        }

    from playwright.sync_api import sync_playwright
    from .live_telemetry_v6 import classify_and_record_dispatch

    t0 = time.perf_counter()
    copy_essential_profile(profile_src, temp_dir)

    target_url = post_url_or_slug
    if not target_url.startswith("http"):
        target_url = f"https://capitalchronicle.substack.com/p/{post_url_or_slug}"

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

            comment_input = page.wait_for_selector("textarea[placeholder*='comment']", timeout=15000)
            if comment_input:
                comment_input.fill(message)
                time.sleep(1)

                submit_btn = page.locator("button:has-text('Post')").first
                if not submit_btn.is_visible():
                    submit_btn = page.locator("button:has-text('Comment')").first

                if submit_btn.is_visible():
                    submit_btn.click()
                    time.sleep(4)

            final_url = page.url
            browser.close()

            result = {
                "status": "SUCCESS",
                "platform": "substack",
                "action": "comment",
                "url": final_url,
                "response": {"target_url": final_url},
            }
    except Exception as e:
        result = {
            "status": "FAILED",
            "platform": "substack",
            "action": "comment",
            "error": str(e),
        }

    latency_ms = (time.perf_counter() - t0) * 1000.0
    classify_and_record_dispatch(
        platform_id="substack",
        action="comment",
        adapter_result=result,
        latency_ms=latency_ms,
        payload_size_bytes=len(message),
    )
    return result


def execute_substack_edit(
    post_id_or_url: str,
    title: str = "",
    subtitle: str = "",
    body_markdown: str = "",
    dry_run: bool = False,
    profile_src: Path = DEFAULT_PROFILE_SRC,
    temp_dir: Path = TEMP_PROFILE_DIR,
) -> dict[str, Any]:
    """Edits an existing Substack post or draft."""
    if dry_run:
        return {
            "status": "DRY_RUN_PASS",
            "platform": "substack",
            "action": "edit",
            "payload_redacted": {
                "post_id": post_id_or_url,
                "title": title,
                "subtitle": subtitle,
            },
            "response": {
                "id": f"substack_mock_edit_{post_id_or_url}",
            },
        }

    from playwright.sync_api import sync_playwright
    from .live_telemetry_v6 import classify_and_record_dispatch

    t0 = time.perf_counter()
    copy_essential_profile(profile_src, temp_dir)

    if post_id_or_url.startswith("http"):
        edit_url = post_id_or_url
    else:
        edit_url = f"https://capitalchronicle.substack.com/publish/post/{post_id_or_url}"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=str(temp_dir),
                channel="msedge",
                headless=True,
            )
            page = browser.pages[0]
            page.goto(edit_url, timeout=30000)
            time.sleep(6)

            if title:
                title_el = page.query_selector("#post-title")
                if title_el:
                    title_el.fill(title)

            if subtitle:
                subtitle_el = page.query_selector("textarea[placeholder*='subtitle']")
                if subtitle_el:
                    subtitle_el.fill(subtitle)

            if body_markdown:
                editor_el = page.query_selector("div.ProseMirror")
                if editor_el:
                    editor_el.focus()
                    page.keyboard.type(body_markdown)

            time.sleep(2)
            continue_btn = page.locator("button:has-text('Continue')").first
            if continue_btn.is_visible():
                continue_btn.click()
                time.sleep(4)

            save_btn = page.locator("button:has-text('Send to everyone now')").first
            if not save_btn.is_visible():
                save_btn = page.locator("button:has-text('Save')").first

            if save_btn.is_visible():
                save_btn.click()
                time.sleep(4)

            final_url = page.url
            browser.close()

            result = {
                "status": "SUCCESS",
                "platform": "substack",
                "action": "edit",
                "url": final_url,
                "response": {"final_url": final_url},
            }
    except Exception as e:
        result = {
            "status": "FAILED",
            "platform": "substack",
            "action": "edit",
            "error": str(e),
        }

    latency_ms = (time.perf_counter() - t0) * 1000.0
    classify_and_record_dispatch(
        platform_id="substack",
        action="edit",
        adapter_result=result,
        latency_ms=latency_ms,
        payload_size_bytes=len(title) + len(body_markdown),
    )
    return result
