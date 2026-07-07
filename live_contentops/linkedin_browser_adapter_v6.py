"""LinkedIn Playwright Browser Adapter for ContentOps V6 (Fast Ship Mode).

Executes post publishing, commenting, and editing on LinkedIn via Playwright
using a temporary clone of the operator's browser profile.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import time
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_FAST_SHIP_LIVE_DISPATCH_LINKEDIN_V0"
DEFAULT_PROFILE_SRC = Path(r"A:\Capital Chronicle\operator-browser-profiles\contentops-social-main")
TEMP_PROFILE_DIR = Path(r"A:\Capital Chronicle\tools\cc-live-contentops\scratch\temp_profile_linkedin")


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


def _safe_click(locator: Any, *, timeout_ms: int = 2500) -> bool:
    try:
        if not locator.is_visible():
            return False
        try:
            if not locator.is_enabled():
                return False
        except Exception:
            pass
        try:
            locator.click(timeout=timeout_ms)
            return True
        except Exception:
            try:
                locator.click(timeout=timeout_ms, force=True)
                return True
            except Exception:
                locator.evaluate("el => el.click()")
                return True
    except Exception:
        return False


def _click_first_visible(page: Any, selectors: tuple[str, ...], *, timeout_ms: int = 2500) -> str | None:
    for selector in selectors:
        try:
            loc = page.locator(selector).first
            if _safe_click(loc, timeout_ms=timeout_ms):
                return selector
        except Exception:
            continue
    return None


def _clear_linkedin_overlays(page: Any) -> None:
    overlay_selectors = (
        "dialog button[aria-label='Dismiss']",
        "dialog button[aria-label='Close']",
        "dialog button:has-text('Dismiss')",
        "dialog button:has-text('Close')",
        "dialog button:has-text('Maybe later')",
        "dialog button:has-text('Not now')",
        "dialog button:has-text('Skip')",
        "dialog button:has-text('Accept')",
        "button[aria-label='Dismiss']",
        "button[aria-label='Close']",
        "button:has-text('Maybe later')",
        "button:has-text('Not now')",
    )
    for _ in range(3):
        clicked_selector = _click_first_visible(page, overlay_selectors, timeout_ms=2000)
        if clicked_selector:
            time.sleep(1)
            continue
        try:
            page.keyboard.press("Escape")
            time.sleep(1)
        except Exception:
            break


def _accept_linkedin_alerts(page: Any) -> None:
    _clear_linkedin_overlays(page)
    _click_first_visible(
        page,
        (
            "dialog button:has-text('Accept')",
            "button[data-testid^='global-alerts-actions']:has-text('Accept')",
            "button:has-text('Accept')",
        ),
        timeout_ms=3000,
    )
    time.sleep(1)
    _clear_linkedin_overlays(page)


def execute_linkedin_post(
    text: str,
    dry_run: bool = False,
    profile_src: Path = DEFAULT_PROFILE_SRC,
    temp_dir: Path = TEMP_PROFILE_DIR,
    image_path: str | None = None,
) -> dict[str, Any]:
    """Publishes a new update/post to LinkedIn using the operator's profile."""
    payload_hash = hashlib.md5(text.encode("utf-8")).hexdigest()[:12]

    if dry_run:
        return {
            "status": "DRY_RUN_PASS",
            "platform": "linkedin",
            "action": "post",
            "payload_redacted": {
                "text": text,
            },
            "response": {
                "id": f"linkedin_mock_post_{payload_hash}",
                "url": f"https://www.linkedin.com/feed/update/urn:li:activity:mock_{payload_hash}",
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
            page.goto("https://www.linkedin.com/feed/", timeout=30000)
            time.sleep(6)

            _accept_linkedin_alerts(page)

            posted = False
            if not _click_first_visible(
                page,
                (
                    "button:has-text('Start a post')",
                    "text=Start a post",
                    "button[aria-label*='Start a post']",
                ),
                timeout_ms=5000,
            ):
                page.click("text=Start a post", timeout=10000)
            time.sleep(4)

            editor = page.locator("div.ql-editor, [role='textbox']").first
            if editor.is_visible():
                editor.focus()
                page.keyboard.type(text)
                time.sleep(2)

                # Best-effort image attach; never fail the text post if the control is absent.
                if image_path and os.path.exists(image_path):
                    try:
                        file_input = page.query_selector("input[type='file']")
                        if file_input:
                            file_input.set_input_files(image_path)
                            time.sleep(5)
                            # Click any "Next"/"Done" to return to the share composer if a media dialog opened.
                            for sel in ("button:has-text('Next')", "button:has-text('Done')"):
                                loc = page.locator(sel).first
                                if loc.is_visible():
                                    loc.click()
                                    time.sleep(3)
                                    break
                    except Exception as img_exc:
                        print(f"[Warning] LinkedIn image upload skipped: {img_exc}")

                post_btn = page.locator("button.share-actions__primary-action, button.share-actions__post-button").first
                if post_btn.is_visible() and post_btn.is_enabled():
                    post_btn.click()
                    posted = True
                    time.sleep(8)

            final_url = page.url
            browser.close()

            if posted:
                result = {
                    "status": "SUCCESS",
                    "platform": "linkedin",
                    "action": "post",
                    "id": f"activity_{payload_hash}",
                    "response": {"final_url": final_url},
                }
            else:
                result = {
                    "status": "FAILED",
                    "platform": "linkedin",
                    "action": "post",
                    "error": "Could not submit post in modal",
                }
    except Exception as e:
        result = {
            "status": "FAILED",
            "platform": "linkedin",
            "action": "post",
            "error": str(e),
        }

    latency_ms = (time.perf_counter() - t0) * 1000.0
    classify_and_record_dispatch(
        platform_id="linkedin",
        action="post",
        adapter_result=result,
        latency_ms=latency_ms,
        payload_size_bytes=len(text),
    )
    return result


def execute_linkedin_comment(
    post_url_or_id: str,
    message: str,
    dry_run: bool = False,
    profile_src: Path = DEFAULT_PROFILE_SRC,
    temp_dir: Path = TEMP_PROFILE_DIR,
) -> dict[str, Any]:
    """Replies/comments on a specific LinkedIn update/post."""
    payload_hash = hashlib.md5(f"{post_url_or_id}:{message}".encode("utf-8")).hexdigest()[:12]

    if dry_run:
        return {
            "status": "DRY_RUN_PASS",
            "platform": "linkedin",
            "action": "comment",
            "payload_redacted": {
                "post_url_or_id": post_url_or_id,
                "message": message,
            },
            "response": {
                "id": f"linkedin_mock_comment_{payload_hash}",
            },
        }

    from playwright.sync_api import sync_playwright
    from .live_telemetry_v6 import classify_and_record_dispatch

    t0 = time.perf_counter()
    copy_essential_profile(profile_src, temp_dir)

    try:
        # Determine target URL or fallback to profile recent activity feed
        target_url = None
        if post_url_or_id.startswith("http://") or post_url_or_id.startswith("https://"):
            target_url = post_url_or_id
        elif "urn:li:" in post_url_or_id or (post_url_or_id.isdigit() and len(post_url_or_id) > 5):
            urn = post_url_or_id if "urn:li:" in post_url_or_id else f"urn:li:activity:{post_url_or_id}"
            target_url = f"https://www.linkedin.com/feed/update/{urn}/"

        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=str(temp_dir),
                channel="msedge",
                headless=True,
            )
            page = browser.pages[0]
            
            if target_url:
                page.goto(target_url, timeout=30000)
            else:
                profile_handle = post_url_or_id if post_url_or_id and not post_url_or_id.startswith("activity_") else "jimcc"
                page.goto(f"https://www.linkedin.com/in/{profile_handle}/recent-activity/all/", timeout=30000)
            time.sleep(8)

            _accept_linkedin_alerts(page)

            post_card = None
            if target_url:
                post_card = page.locator(".feed-shared-update-v2, [data-urn], main").first
            else:
                # Filter by Posts tab to guarantee top item is a commentable post
                posts_tab = page.locator("button:has-text('Posts')").first
                if posts_tab.is_visible():
                    posts_tab.click()
                    time.sleep(4)

                # Locate the card containing "Capital Chronicle" (polling feed to index new post)
                for attempt in range(5):
                    cards = page.locator(".feed-shared-update-v2, [data-urn]").all()
                    for card in cards:
                        try:
                            txt = card.inner_text()
                            if "Capital Chronicle" in txt:
                                post_card = card
                                break
                        except Exception:
                            pass
                    if post_card:
                        break
                    print("Target post card not found in feed yet, reloading page...")
                    page.reload()
                    time.sleep(5)

                # Fallback to top card if specific card not found
                if not post_card:
                    post_card = page.locator(".feed-shared-update-v2, [data-urn]").first

            commented = False

            # 1. Try to find the editor directly first (common for single/direct post update pages)
            editor = None
            if post_card:
                editor = post_card.locator("form.comments-comment-box__form div.ql-editor, div.ql-editor, [role='textbox']").first
            if not editor or not editor.is_visible():
                editor = page.locator("form.comments-comment-box__form div.ql-editor, div.ql-editor, [role='textbox']").first

            # 2. If editor is not visible, look for comment button and click it to reveal the editor
            if not editor or not editor.is_visible():
                comment_btn = None
                if post_card:
                    comment_btn = post_card.locator("button.comment-button, button:has-text('Comment'), button[aria-label*='Comment']").first
                if not comment_btn or not comment_btn.is_visible():
                    comment_btn = page.locator("button.comment-button, button:has-text('Comment'), button[aria-label*='Comment']").first

                if comment_btn and comment_btn.is_visible():
                    comment_btn.click()
                    time.sleep(4)

                    # Re-locate the editor after clicking
                    if post_card:
                        editor = post_card.locator("form.comments-comment-box__form div.ql-editor, div.ql-editor, [role='textbox']").first
                    if not editor or not editor.is_visible():
                        editor = page.locator("form.comments-comment-box__form div.ql-editor, div.ql-editor, [role='textbox']").first

            # 3. If editor is visible (either initially or after click), proceed with comment entry and submission
            if editor and editor.is_visible():
                editor.focus()
                page.keyboard.type(message)
                time.sleep(2)

                submit_btn = None
                if post_card:
                    submit_btn = post_card.locator(
                        "form.comments-comment-box__form button[type='submit'], "
                        "form.comments-comment-box__form button:has-text('Post'), "
                        "form.comments-comment-box__form button:has-text('Comment'), "
                        ".comments-comment-box button:has-text('Post'), "
                        ".comments-comment-box button:has-text('Comment')"
                    ).first
                if not submit_btn or not submit_btn.is_visible():
                    submit_btn = page.locator(
                        "form.comments-comment-box__form button[type='submit'], "
                        "form.comments-comment-box__form button:has-text('Post'), "
                        "form.comments-comment-box__form button:has-text('Comment'), "
                        ".comments-comment-box button:has-text('Post'), "
                        ".comments-comment-box button:has-text('Comment')"
                    ).first

                if submit_btn and submit_btn.is_visible() and submit_btn.is_enabled():
                    submit_btn.click()
                    commented = True
                    time.sleep(5)

            final_url = page.url
            browser.close()

            if commented:
                result = {
                    "status": "SUCCESS",
                    "platform": "linkedin",
                    "action": "comment",
                    "response": {"target_url": final_url},
                }
            else:
                result = {
                    "status": "FAILED",
                    "platform": "linkedin",
                    "action": "comment",
                    "error": "Could not submit comment",
                }
    except Exception as e:
        result = {
            "status": "FAILED",
            "platform": "linkedin",
            "action": "comment",
            "error": str(e),
        }

    latency_ms = (time.perf_counter() - t0) * 1000.0
    classify_and_record_dispatch(
        platform_id="linkedin",
        action="comment",
        adapter_result=result,
        latency_ms=latency_ms,
        payload_size_bytes=len(message),
    )
    return result


def execute_linkedin_edit(
    post_url_or_id: str,
    new_text: str,
    dry_run: bool = False,
    profile_src: Path = DEFAULT_PROFILE_SRC,
    temp_dir: Path = TEMP_PROFILE_DIR,
) -> dict[str, Any]:
    """Edits an existing LinkedIn update/post."""
    if dry_run:
        return {
            "status": "DRY_RUN_PASS",
            "platform": "linkedin",
            "action": "edit",
            "payload_redacted": {
                "post_url_or_id": post_url_or_id,
                "new_text": new_text,
            },
            "response": {
                "target_url": f"https://www.linkedin.com/feed/update/{post_url_or_id}",
            },
        }

    from playwright.sync_api import sync_playwright
    from .live_telemetry_v6 import classify_and_record_dispatch

    t0 = time.perf_counter()
    copy_essential_profile(profile_src, temp_dir)

    try:
        # Determine target URL or fallback to profile recent activity feed
        target_url = None
        if post_url_or_id.startswith("http://") or post_url_or_id.startswith("https://"):
            target_url = post_url_or_id
        elif "urn:li:" in post_url_or_id or (post_url_or_id.isdigit() and len(post_url_or_id) > 5):
            urn = post_url_or_id if "urn:li:" in post_url_or_id else f"urn:li:activity:{post_url_or_id}"
            target_url = f"https://www.linkedin.com/feed/update/{urn}/"

        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=str(temp_dir),
                channel="msedge",
                headless=True,
            )
            page = browser.pages[0]
            
            if target_url:
                page.goto(target_url, timeout=30000)
            else:
                profile_handle = post_url_or_id if post_url_or_id and not post_url_or_id.startswith("activity_") else "jimcc"
                page.goto(f"https://www.linkedin.com/in/{profile_handle}/recent-activity/all/", timeout=30000)
            time.sleep(8)

            _accept_linkedin_alerts(page)

            post_card = None
            if target_url:
                post_card = page.locator(".feed-shared-update-v2, [data-urn], main").first
            else:
                posts_tab = page.locator("button:has-text('Posts')").first
                if posts_tab.is_visible():
                    posts_tab.click()
                    time.sleep(4)

                # Locate the card containing "Capital Chronicle" (polling feed to index new post)
                for attempt in range(5):
                    cards = page.locator(".feed-shared-update-v2, [data-urn]").all()
                    for card in cards:
                        try:
                            txt = card.inner_text()
                            if "Capital Chronicle" in txt:
                                post_card = card
                                break
                        except Exception:
                            pass
                    if post_card:
                        break
                    print("Target post card not found in feed yet, reloading page...")
                    page.reload()
                    time.sleep(5)

                # Fallback to top card if specific card not found
                if not post_card:
                    post_card = page.locator(".feed-shared-update-v2, [data-urn]").first

            edited = False
            three_dots = None
            if post_card:
                three_dots = post_card.locator("button.feed-shared-control-menu__trigger, button[aria-label*='options'], button[aria-label*='Control menu'], button:has-text('...')").first
            if not three_dots or not three_dots.is_visible():
                three_dots = page.locator("button.feed-shared-control-menu__trigger, button[aria-label*='options'], button[aria-label*='Control menu'], button:has-text('...')").first

            if three_dots.is_visible():
                three_dots.click()
                time.sleep(3)

                edit_option = page.locator(".option-edit, div.option-edit, [role='button']:has-text('Edit post')").first
                if not edit_option.is_visible():
                    edit_option = page.locator("span:has-text('Edit post'), button:has-text('Edit post'), li:has-text('Edit post')").first

                if edit_option.is_visible():
                    edit_option.click()
                    time.sleep(4)

                    editor = page.locator("div[role='dialog'] div.ql-editor, div[role='dialog'] [role='textbox'], .share-box div.ql-editor, div.ql-editor, [role='textbox']").first
                    if editor.is_visible():
                        editor.focus()
                        page.keyboard.type(f" {new_text}")
                        time.sleep(2)

                        save_btn = page.locator("div[role='dialog'] button:has-text('Save'), div[role='dialog'] button.share-actions__primary-action, .share-box button:has-text('Save'), button:has-text('Save')").first
                        if save_btn.is_visible() and save_btn.is_enabled():
                            save_btn.click()
                            edited = True
                            time.sleep(6)

            final_url = page.url
            browser.close()

            if edited:
                result = {
                    "status": "SUCCESS",
                    "platform": "linkedin",
                    "action": "edit",
                    "response": {"target_url": final_url},
                }
            else:
                result = {
                    "status": "FAILED",
                    "platform": "linkedin",
                    "action": "edit",
                    "error": "Could not save edit on LinkedIn post",
                }
    except Exception as e:
        result = {
            "status": "FAILED",
            "platform": "linkedin",
            "action": "edit",
            "error": str(e),
        }

    latency_ms = (time.perf_counter() - t0) * 1000.0
    classify_and_record_dispatch(
        platform_id="linkedin",
        action="edit",
        adapter_result=result,
        latency_ms=latency_ms,
        payload_size_bytes=len(new_text),
    )
    return result
