"""Substack Playwright Browser Adapter for ContentOps V6 (Fast Ship Mode).

Executes post publishing, commenting, and editing on Substack via Playwright 
using a temporary clone of the operator's browser profile.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import time
import urllib.parse
from pathlib import Path
from typing import Any, Mapping, Sequence

TASK_LABEL = "TASK_CONTENTOPS_V6_FAST_SHIP_LIVE_DISPATCH_SUBSTACK_AND_X_V0"
DEFAULT_PROFILE_SRC = Path(r"A:\Capital Chronicle\operator-browser-profiles\contentops-social-main")
TEMP_PROFILE_DIR = Path(r"A:\Capital Chronicle\tools\cc-live-contentops\scratch\temp_profile_substack")
VISUAL_MARKER_RE = re.compile(r"\[\[VISUAL:([a-zA-Z0-9_-]+)\]\]")
SUPERVISED_BROWSER_REQUEST_SCHEMA = "contentops.substack_supervised_browser_request.v1"
SUPERVISED_BROWSER_READBACK_SCHEMA = "contentops.substack_supervised_browser_readback.v1"
_SENSITIVE_READBACK_KEY_RE = re.compile(
    r"(cookie|token|secret|password|authorization|session|localstorage|sessionstorage|webhook)",
    re.IGNORECASE,
)


def _is_public_substack_url(url: str | None) -> bool:
    return bool(url and "/p/" in url and "/publish/" not in url)


def _is_externally_usable_substack_url(url: str | None) -> bool:
    """Reject private editor routes; preview URLs may carry a draft query string."""
    if not url:
        return False
    parsed = urllib.parse.urlparse(url)
    return bool(
        parsed.scheme == "https"
        and "substack.com" in parsed.netloc
        and "/publish/" not in parsed.path
    )


def _absolute_substack_url(url: str | None) -> str | None:
    if not url:
        return None
    if url.startswith("/"):
        return f"https://capitalchronicle.substack.com{url}"
    return url


def _slugify_title(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:90].strip("-")


def _extract_page_attr(page: Any, selector: str, attr: str) -> str | None:
    try:
        loc = page.locator(selector).first
        if loc.count():
            value = loc.get_attribute(attr)
            return value or None
    except Exception:
        return None
    return None


def _extract_public_url_from_page(page: Any, title: str) -> str | None:
    candidates: list[str] = []
    for selector, attr in (
        ("link[rel='canonical']", "href"),
        ("meta[property='og:url']", "content"),
        ("meta[name='twitter:url']", "content"),
    ):
        value = _absolute_substack_url(_extract_page_attr(page, selector, attr))
        if value:
            candidates.append(value)
    try:
        links = page.locator("a[href*='/p/']").all()
        for link in links:
            href = _absolute_substack_url(link.get_attribute("href"))
            if href:
                candidates.append(href)
    except Exception:
        pass
    for candidate in candidates:
        if _is_public_substack_url(candidate):
            return candidate.split("?", 1)[0]
    slug = _slugify_title(title)
    return f"https://capitalchronicle.substack.com/p/{slug}" if slug else None


def _extract_public_image_url_from_page(page: Any) -> str | None:
    candidates: list[str] = []
    for selector, attr in (
        ("meta[property='og:image']", "content"),
        ("meta[name='twitter:image']", "content"),
        ("link[rel='image_src']", "href"),
    ):
        value = _extract_page_attr(page, selector, attr)
        if value:
            candidates.append(value)
    try:
        images = page.locator("img[src]").all()
        for image in images:
            src = image.get_attribute("src")
            if src:
                candidates.append(src)
    except Exception:
        pass
    for candidate in candidates:
        lowered = candidate.lower()
        if candidate.startswith("http") and "substack-post-office" not in lowered and "default-logo" not in lowered:
            if any(marker in lowered for marker in ("substackcdn", "substack-post-media", "bucketeer", "amazonaws")):
                return candidate
    return None


def _set_first_file_input(page: Any, image_path: str) -> str | None:
    abs_path = str(Path(image_path).resolve())
    try:
        inputs = page.locator("input[type='file']").all()
        for file_input in inputs:
            try:
                attrs = file_input.evaluate(
                    "e => ({id:e.id || '', accept:e.getAttribute('accept') || '', className:e.className || '', parentText:e.parentElement ? e.parentElement.innerText || '' : ''})"
                )
                descriptor = " ".join(str(attrs.get(k, "")) for k in ("id", "accept", "className", "parentText")).lower()
                if "file-sidebar" in descriptor or "thumbnail" in descriptor or "audio/" in descriptor:
                    continue
                file_input.set_input_files(abs_path)
                return "uploaded"
            except Exception:
                continue
    except Exception:
        pass
    return None


def _editor_image_count(page: Any) -> int:
    try:
        return page.locator("div.ProseMirror img, .ProseMirror img").count()
    except Exception:
        return 0


def _focus_substack_editor_at_end(page: Any) -> bool:
    try:
        editor = page.locator("div.ProseMirror, .ProseMirror").first
        if not editor.is_visible():
            return False
        editor.click(timeout=2500)
        editor.evaluate(
            """
            (editor) => {
              editor.focus();
              const range = document.createRange();
              range.selectNodeContents(editor);
              range.collapse(false);
              const selection = window.getSelection();
              selection.removeAllRanges();
              selection.addRange(range);
            }
            """
        )
        return True
    except Exception:
        try:
            page.keyboard.press("Control+End")
            return True
        except Exception:
            return False


def _focus_after_last_editor_image(page: Any) -> bool:
    try:
        count = _editor_image_count(page)
        if count <= 0:
            return _focus_substack_editor_at_end(page)
        image = page.locator("div.ProseMirror img, .ProseMirror img").nth(count - 1)
        image.scroll_into_view_if_needed(timeout=3000)
        box = image.bounding_box(timeout=3000)
        if not box:
            return _focus_substack_editor_at_end(page)
        x = box["x"] + min(max(box["width"] / 2, 20), max(box["width"] - 4, 4))
        y = box["y"] + box["height"] + 12
        page.mouse.click(x, y)
        time.sleep(0.5)
        return True
    except Exception:
        return _focus_substack_editor_at_end(page)


def _insert_editor_text(page: Any, text: str) -> None:
    if not text:
        return
    _focus_substack_editor_at_end(page)
    # Substack's ProseMirror editor applies Markdown shortcuts during real
    # key events; insert_text is faster but can bypass heading conversion.
    page.keyboard.type(text)


def _upload_substack_body_image_via_toolbar(page: Any, image_path: str) -> str | None:
    abs_path = str(Path(image_path).resolve())
    for button_selector in (
        "button[aria-label='Image']",
        "button[title='Insert image']",
        "button[aria-label*='Image']",
    ):
        try:
            button = page.locator(button_selector).first
            if not button.is_visible():
                continue
            _focus_substack_editor_at_end(page)
            before_count = _editor_image_count(page)
            button.click()
            time.sleep(1)
            menu_item = page.locator("[role='menuitem']").filter(has_text=re.compile(r"^Image$")).first
            with page.expect_file_chooser(timeout=5000) as chooser_info:
                if menu_item.is_visible():
                    menu_item.click()
                else:
                    page.keyboard.press("Enter")
            chooser_info.value.set_files(abs_path)
            for _ in range(12):
                time.sleep(1)
                after_count = _editor_image_count(page)
                if after_count > before_count:
                    _focus_after_last_editor_image(page)
                    return "uploaded"
            return "uploaded_unverified"
        except Exception:
            continue
    return None


def _upload_substack_image(page: Any, image_path: str | None) -> str:
    if not image_path:
        return "not_requested"
    if not os.path.exists(image_path):
        return "local_file_missing"
    status = _upload_substack_body_image_via_toolbar(page, image_path)
    if status:
        return status
    status = _set_first_file_input(page, image_path)
    if status:
        time.sleep(5)
        return "uploaded_unverified"
    for selector in (
        "button[aria-label*='Image']",
        "button[aria-label*='image']",
        "button[aria-label*='Photo']",
        "button[aria-label*='photo']",
        "button:has-text('Image')",
        "button:has-text('Photo')",
        "button:has-text('Upload')",
        "[role='button']:has-text('Image')",
    ):
        try:
            loc = page.locator(selector).first
            if loc.is_visible():
                loc.click()
                time.sleep(2)
                status = _set_first_file_input(page, image_path)
                if status:
                    time.sleep(5)
                    return status
        except Exception:
            continue
    return "skipped_no_file_input"


def _normalise_image_assets(image_path: str | None = None, image_assets: list[dict[str, Any]] | None = None) -> dict[str, str]:
    assets: dict[str, str] = {}
    if image_path:
        assets["primary"] = image_path
    for idx, asset in enumerate(image_assets or [], start=1):
        if not isinstance(asset, dict):
            continue
        local_path = str(asset.get("local_path") or asset.get("image_path") or "").strip()
        if not local_path:
            continue
        asset_id = str(asset.get("asset_id") or ("primary" if idx == 1 else f"visual_{idx}")).strip()
        assets[asset_id] = local_path
        if idx == 1:
            assets.setdefault("primary", local_path)
    return assets


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_readback_mapping(value: Any) -> bool:
    """Reject session-bearing browser material before it can enter evidence."""
    if isinstance(value, Mapping):
        for key, item in value.items():
            safe_negative_attestation = str(key) in {"browser_session_material_recorded"} and item is False
            if _SENSITIVE_READBACK_KEY_RE.search(str(key)) and not safe_negative_attestation:
                return False
            if not _safe_readback_mapping(item):
                return False
    elif isinstance(value, (list, tuple)):
        return all(_safe_readback_mapping(item) for item in value)
    return True


def prepare_supervised_substack_browser_request(
    *,
    run_id: str,
    publication_mode: str,
    title: str,
    subtitle: str,
    body_markdown: str,
    article_markdown_path: str | Path,
    image_assets: Sequence[Mapping[str, Any]],
    output_path: str | Path,
) -> dict[str, Any]:
    """Create the exact, safe local packet used by a supervised Substack editor.

    This is intentionally separate from the legacy cloned-profile executor. It
    binds one editor action to one article body and any truthfully available ContentOps-owned
    media paths, without reading or persisting any browser-session material.
    """
    mode = str(publication_mode or "").lower()
    if mode not in {"draft", "publish"}:
        raise ValueError("publication_mode_must_be_draft_or_publish")
    article_path = Path(article_markdown_path)
    if not article_path.exists():
        raise ValueError(f"article_markdown_missing:{article_path}")
    marker_ids = VISUAL_MARKER_RE.findall(body_markdown or "")
    if len(marker_ids) != len(set(marker_ids)):
        raise ValueError("substack_body_visual_markers_must_be_unique")

    asset_rows: list[dict[str, Any]] = []
    asset_ids: list[str] = []
    for source in image_assets:
        asset_id = str(source.get("asset_id") or "").strip()
        local_path = Path(str(source.get("path") or source.get("local_path") or ""))
        if not asset_id or not local_path.exists():
            raise ValueError(f"substack_image_asset_invalid:{asset_id or 'missing'}")
        for required in ("caption", "alt_text", "source_label", "source_page_url", "provenance_status"):
            if not str(source.get(required) or "").strip():
                raise ValueError(f"substack_image_asset_missing_{required}:{asset_id}")
        asset_rows.append(
            {
                "asset_id": asset_id,
                "local_path": str(local_path),
                "sha256": _sha256_file(local_path),
                "caption": str(source["caption"]),
                "alt_text": str(source["alt_text"]),
                "source_label": str(source["source_label"]),
                "source_page_url": str(source["source_page_url"]),
                "provenance_status": str(source["provenance_status"]),
                "media_class": str(source.get("media_class") or ""),
            }
        )
        asset_ids.append(asset_id)
    if marker_ids != asset_ids:
        raise ValueError("substack_visual_marker_order_must_match_asset_order")

    request = {
        "schema_version": SUPERVISED_BROWSER_REQUEST_SCHEMA,
        "status": "READY_FOR_SUPERVISED_BROWSER_ASSIST",
        "run_id": run_id,
        "publication_mode": mode,
        "publication_url": "https://capitalchronicle.substack.com/publish/post",
        "title": title,
        "subtitle": subtitle,
        "article_markdown_path": str(article_path),
        "article_markdown_sha256": _sha256_file(article_path),
        "body_markdown": body_markdown,
        "body_markdown_sha256": _sha256_text(body_markdown),
        "visual_marker_order": marker_ids,
        "image_assets": asset_rows,
        "required_readback": {
            "publication_state": mode,
            "matching_title": title,
            "matching_body_markdown_sha256": _sha256_text(body_markdown),
            "minimum_editor_body_image_count": len(asset_rows),
            "in_body_visual_asset_ids": marker_ids,
            "url_kind": "public_url" if mode == "publish" else "externally_usable_preview_or_draft_url",
        },
        "safety": {
            "browser_profile_values_recorded": False,
            "cookies_recorded": False,
            "session_storage_recorded": False,
            "raw_credentials_recorded": False,
        },
    }
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(request, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return request


def build_supervised_substack_browser_readback(
    *,
    request: Mapping[str, Any],
    publication_state: str,
    article_url: str,
    editor_body_image_count: int,
    in_body_visual_asset_ids: Sequence[str],
    output_path: str | Path,
) -> dict[str, Any]:
    """Persist only the post-action facts required to complete the run."""
    state = str(publication_state or "").lower()
    if state not in {"draft", "published"}:
        raise ValueError("publication_state_must_be_draft_or_published")
    url = str(article_url or "").strip()
    if not _is_externally_usable_substack_url(url):
        raise ValueError("substack_readback_requires_externally_usable_preview_or_public_url")
    expected_state = str(request.get("publication_mode") or "").lower()
    if expected_state and state != ("published" if expected_state == "publish" else "draft"):
        raise ValueError("substack_readback_publication_state_mismatch")
    readback = {
        "schema_version": SUPERVISED_BROWSER_READBACK_SCHEMA,
        "status": "SUCCESS",
        "run_id": str(request.get("run_id") or ""),
        "publication_state": state,
        "public_url": url if state == "published" else None,
        "draft_url": url if state == "draft" else None,
        "title": str(request.get("title") or ""),
        "body_markdown_sha256": str(request.get("body_markdown_sha256") or ""),
        "editor_body_image_count": int(editor_body_image_count),
        "in_body_visual_asset_ids": [str(item) for item in in_body_visual_asset_ids],
        "browser_session_material_recorded": False,
    }
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(readback, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return readback


def build_supervised_substack_browser_blocked_readback(
    *,
    request: Mapping[str, Any],
    draft_id: str,
    saved_state: str,
    editor_body_text_length: int,
    editor_body_image_count: int,
    attempted_asset_id: str,
    blocker: str,
    next_unblock: str,
    output_path: str | Path,
) -> dict[str, Any]:
    """Persist a safe, resumable blocked state without leaking the editor URL."""
    if not str(draft_id or "").strip():
        raise ValueError("substack_blocked_readback_requires_draft_id")
    if not str(blocker or "").strip() or not str(next_unblock or "").strip():
        raise ValueError("substack_blocked_readback_requires_blocker_and_next_unblock")
    readback = {
        "schema_version": SUPERVISED_BROWSER_READBACK_SCHEMA,
        "status": "BLOCKED_SUPERVISED_SUBSTACK_BROWSER_ASSIST",
        "run_id": str(request.get("run_id") or ""),
        "draft_id": str(draft_id),
        "external_preview_or_public_url": None,
        "title": str(request.get("title") or ""),
        "body_markdown_sha256": str(request.get("body_markdown_sha256") or ""),
        "saved_state": str(saved_state or ""),
        "editor_body_text_length": int(editor_body_text_length),
        "editor_body_image_count": int(editor_body_image_count),
        "expected_visual_asset_ids": [str(item) for item in request.get("visual_marker_order") or []],
        "attempted_asset_id": str(attempted_asset_id or ""),
        "blocker": str(blocker),
        "next_unblock": str(next_unblock),
        "telegram_action": "NOT_ATTEMPTED_NO_EXTERNALLY_USABLE_SUBSTACK_URL",
        "browser_session_material_recorded": False,
    }
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(readback, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return readback


def validate_supervised_substack_browser_readback(
    request: Mapping[str, Any], readback: Mapping[str, Any]
) -> dict[str, Any]:
    """Fail closed unless the browser readback proves canonical in-body media."""
    blockers: list[str] = []
    if not _safe_readback_mapping(readback):
        blockers.append("substack_readback_contains_sensitive_browser_material")
    if readback.get("schema_version") != SUPERVISED_BROWSER_READBACK_SCHEMA:
        blockers.append("substack_readback_schema_mismatch")
    if readback.get("status") != "SUCCESS":
        blockers.append("substack_readback_not_success")
    if str(readback.get("run_id") or "") != str(request.get("run_id") or ""):
        blockers.append("substack_readback_run_id_mismatch")
    if str(readback.get("title") or "") != str(request.get("title") or ""):
        blockers.append("substack_readback_title_mismatch")
    if str(readback.get("body_markdown_sha256") or "") != str(request.get("body_markdown_sha256") or ""):
        blockers.append("substack_readback_body_hash_mismatch")
    expected_ids = list(request.get("visual_marker_order") or [])
    actual_ids = [str(item) for item in readback.get("in_body_visual_asset_ids") or []]
    if actual_ids != expected_ids:
        blockers.append("substack_readback_visual_order_mismatch")
    minimum_image_count = int(
        (request.get("required_readback") or {}).get("minimum_editor_body_image_count")
        or 0
    )
    if int(readback.get("editor_body_image_count") or 0) < minimum_image_count:
        blockers.append("substack_readback_body_image_count_below_required")

    state = str(readback.get("publication_state") or "").lower()
    expected_mode = str(request.get("publication_mode") or "").lower()
    expected_state = "published" if expected_mode == "publish" else "draft"
    if state != expected_state:
        blockers.append("substack_readback_publication_state_mismatch")
    public_url = str(readback.get("public_url") or "").strip()
    draft_url = str(readback.get("draft_url") or "").strip()
    canonical_url = public_url or draft_url
    parsed = urllib.parse.urlparse(canonical_url)
    if not canonical_url or parsed.scheme != "https" or "substack.com" not in parsed.netloc:
        blockers.append("substack_readback_canonical_url_missing_or_invalid")
    elif not _is_externally_usable_substack_url(canonical_url):
        blockers.append("substack_readback_canonical_url_is_private_editor_url")

    return {
        "status": "SUCCESS" if not blockers else "BLOCKED_SUBSTACK_READBACK_INVALID",
        "blockers": blockers,
        "publication_state": state or None,
        "canonical_url": canonical_url or None,
        "public_url": public_url or None,
        "draft_url": draft_url or None,
        "editor_body_image_count": int(readback.get("editor_body_image_count") or 0),
        "in_body_visual_asset_ids": actual_ids,
        "title": str(readback.get("title") or ""),
        "body_markdown_sha256": str(readback.get("body_markdown_sha256") or ""),
    }


def _split_body_visual_markers(body_markdown: str) -> list[tuple[str, str]]:
    segments: list[tuple[str, str]] = []
    last = 0
    for match in VISUAL_MARKER_RE.finditer(body_markdown or ""):
        if match.start() > last:
            segments.append(("text", body_markdown[last:match.start()]))
        segments.append(("visual", match.group(1)))
        last = match.end()
    if last < len(body_markdown or ""):
        segments.append(("text", body_markdown[last:]))
    return segments or [("text", body_markdown or "")]


def _type_body_with_visual_markers(
    page: Any,
    body_markdown: str,
    image_path: str | None = None,
    image_assets: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    segments = _split_body_visual_markers(body_markdown)
    asset_lookup = _normalise_image_assets(image_path, image_assets)
    has_markers = any(kind == "visual" for kind, _value in segments)
    results: list[dict[str, Any]] = []

    if not has_markers:
        if body_markdown:
            _insert_editor_text(page, body_markdown)
        status = _upload_substack_image(page, image_path)
        if image_path:
            results.append({"asset_id": "primary", "local_path": image_path, "status": status})
        return results

    for kind, value in segments:
        if kind == "text":
            if value:
                _insert_editor_text(page, value)
            continue
        active_path = asset_lookup.get(value)
        if not active_path:
            results.append({"asset_id": value, "local_path": "", "status": "missing_asset"})
            continue
        _focus_substack_editor_at_end(page)
        before_count = _editor_image_count(page)
        status = _upload_substack_image(page, active_path)
        after_count = _editor_image_count(page)
        if status == "uploaded" and after_count <= before_count:
            status = "uploaded_unverified"
        results.append({
            "asset_id": value,
            "local_path": active_path,
            "status": status,
            "editor_image_count_before": before_count,
            "editor_image_count_after": after_count,
        })
        try:
            _focus_after_last_editor_image(page)
            page.keyboard.press("Enter")
            page.keyboard.press("Enter")
            _focus_substack_editor_at_end(page)
        except Exception:
            pass
    return results


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
    image_path: str | None = None,
    image_assets: list[dict[str, Any]] | None = None,
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
                "visual_marker_count": len(VISUAL_MARKER_RE.findall(body_markdown or "")),
                "image_asset_count": len(image_assets or ([] if not image_path else [{"local_path": image_path}])),
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
            media_upload_results: list[dict[str, str]] = []
            if body_markdown:
                editor_el = page.query_selector("div.ProseMirror")
                if editor_el:
                    editor_el.focus()
                    media_upload_results = _type_body_with_visual_markers(
                        page,
                        body_markdown,
                        image_path=image_path,
                        image_assets=image_assets,
                    )
            elif image_path:
                media_upload_results = [{"asset_id": "primary", "local_path": image_path, "status": _upload_substack_image(page, image_path)}]

            requested_upload = bool(image_path or image_assets)
            uploaded_count = sum(1 for item in media_upload_results if item.get("status") == "uploaded")
            failed_uploads = [
                item for item in media_upload_results
                if item.get("status") not in {"uploaded", "not_requested"}
            ]
            media_upload_status = "uploaded" if requested_upload and uploaded_count and not failed_uploads else ("not_requested" if not requested_upload else "failed")
            if requested_upload and media_upload_status != "uploaded":
                print(f"[Warning] Substack image upload status: {media_upload_status}")
                browser.close()
                raise RuntimeError(f"substack_image_upload_failed:{media_upload_status}:{media_upload_results}")

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
            public_url = _extract_public_url_from_page(page, title)
            public_image_url = _extract_public_image_url_from_page(page)
            browser.close()

            result = {
                "status": "SUCCESS",
                "platform": "substack",
                "action": "post",
                "url": public_url or final_url,
                "id": (public_url or final_url).split("/")[-1] if "/" in (public_url or final_url) else f"post_{payload_hash}",
                "media_upload_status": media_upload_status,
                "media_upload_results": media_upload_results,
                "public_url": public_url,
                "public_image_url": public_image_url,
                "response": {
                    "final_url": final_url,
                    "public_url": public_url,
                    "public_image_url": public_image_url,
                    "media_upload_status": media_upload_status,
                    "media_upload_results": media_upload_results,
                },
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
