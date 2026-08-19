"""Direct-CDP publishing adapters bound to the canonical ContentOps Edge profile.

The adapters connect to an already-running Microsoft Edge profile after the
profile doctor validates ownership. They never clone or read profile files and
only persist public publication facts and redacted UI outcomes.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import time
import urllib.parse
import urllib.request
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping, Sequence

from live_contentops.article_rich_text_v1 import (
    markdown_to_rich_text,
    rich_text_to_html,
    rich_text_to_plain_text,
)

from live_contentops.publishing_profile_registry_v1 import (
    CANONICAL_PROFILE_ID,
    PublishingProfileError,
    assert_canonical_edge_cdp,
)
from live_contentops.browser_interaction_budget_v1 import record_browser_interaction_event
from live_contentops.media_manifest_authority_v1 import (
    original_substack_media_url,
    read_public_image_bytes,
    sha256_bytes,
    sha256_file,
)


_VISUAL_MARKER_RE = re.compile(r"\[\[VISUAL:([A-Za-z0-9_-]+)\]\]")
_PRIVATE_SUBSTACK_PATH_MARKER = "/publish/"
_MEANINGFUL_IMAGE_MIN_WIDTH = 200
_MEANINGFUL_IMAGE_MIN_HEIGHT = 100
_LINKEDIN_CHART_SIMILARITY_MINIMUM = 0.78
_YOUTUBE_COMMUNITY_HANDLE = "@CapitalChronicleYouTube"
_X_PUBLIC_HANDLE = "@Capitalnicle"
_TECHNICAL_PUBLIC_TEXT_RE = re.compile(
    r"(?:eight[_ -]?platform[_ -]?live|run[_ -]?id|recovery\d+|docs[\\/]automation|[A-Za-z]:\\)",
    re.IGNORECASE,
)
_EDITORIAL_PROCESS_TEXT_RE = re.compile(
    r"(?:the editorial task|the reporting discipline|the newsroom standard|"
    r"the schedule and sidecars|the chart manifest|editors should look|pipeline narration|prompt narration|"
    r"manifest-bound|packet timestamp|evidence packet|public claim permission)",
    re.IGNORECASE,
)


def _is_public_substack_url(value: str | None) -> bool:
    if not value:
        return False
    try:
        parsed = urllib.parse.urlparse(value)
        explicit_port = parsed.port
    except ValueError:
        return False
    return bool(
        parsed.scheme.casefold() == "https"
        and (parsed.hostname or "").casefold() == "capitalchronicle.substack.com"
        and explicit_port is None
        and parsed.username is None
        and parsed.password is None
        and parsed.path.startswith("/p/")
        and len(parsed.path.removeprefix("/p/").strip("/")) > 0
        and _PRIVATE_SUBSTACK_PATH_MARKER not in parsed.path
    )


def _absolute_substack_url(value: str | None) -> str | None:
    if not value:
        return None
    if value.startswith("/"):
        return f"https://capitalchronicle.substack.com{value}"
    return value


def _public_x_url(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urllib.parse.urlparse(value)
    match = re.fullmatch(r"/([^/]+)/status/(\d+)(?:/.*)?", parsed.path)
    if parsed.scheme == "https" and parsed.netloc in {"x.com", "www.x.com"} and match:
        return f"https://x.com/{match.group(1)}/status/{match.group(2)}"
    return None


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json_sha256(value: Any) -> str:
    return _sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    )


def _expected_article_media_identity_rows(
    expected_image_assets: Sequence[Mapping[str, Any]] | None,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Return exact canonical article-media identities; delivery media is invalid here."""
    rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    for index, raw in enumerate(expected_image_assets or []):
        asset = dict(raw)
        asset_id = str(asset.get("asset_id") or f"article_media_{index}")
        media_role = str(asset.get("media_role") or "")
        if (
            media_role == "delivery_only"
            or asset.get("delivery_only") is True
            or asset.get("article_inclusion") is False
            or asset.get("canonical_article_media") is False
        ):
            blockers.append(f"delivery_only_media_forbidden_in_article_manifest:{asset_id}")
        declared_sha = str(asset.get("sha256") or "").casefold()
        local_path = Path(
            str(
                asset.get("absolute_local_source_path")
                or asset.get("local_path")
                or asset.get("path")
                or ""
            )
        )
        local_sha = sha256_file(local_path) if local_path.is_file() else ""
        if declared_sha and local_sha and declared_sha != local_sha:
            blockers.append(f"canonical_article_media_local_hash_mismatch:{asset_id}")
        identity_sha = declared_sha or local_sha
        if not re.fullmatch(r"[0-9a-f]{64}", identity_sha):
            blockers.append(f"canonical_article_media_sha256_unavailable:{asset_id}")
        rows.append(
            {
                "asset_id": asset_id,
                "sha256": identity_sha or None,
                "media_role": media_role or None,
            }
        )
    return rows, list(dict.fromkeys(blockers))


def _remote_substack_image_identity(src: str | None) -> dict[str, Any]:
    supplied_url = str(src or "")
    original_url = original_substack_media_url(supplied_url)
    identity: dict[str, Any] = {
        "src": supplied_url or None,
        "original_url": original_url or None,
        "sha256": None,
        "identity_read_error_class": None,
    }
    if not original_url.startswith("https://"):
        identity["identity_read_error_class"] = "public_media_url_unavailable"
        return identity
    try:
        identity["sha256"] = sha256_bytes(read_public_image_bytes(original_url))
    except Exception as exc:
        identity["identity_read_error_class"] = type(exc).__name__
    return identity


def _exact_substack_article_media_contract(
    *,
    expected_image_assets: Sequence[Mapping[str, Any]] | None,
    observed_image_rows: Sequence[Mapping[str, Any]],
    expected_manifest_supplied: bool = True,
) -> dict[str, Any]:
    """Compare exact canonical article-media multisets and counts, failing on ambiguity."""
    expected_rows, expected_blockers = _expected_article_media_identity_rows(
        expected_image_assets
    )
    observed_rows = [
        {
            "src": str(row.get("src") or "") or None,
            "original_url": str(row.get("original_url") or "") or None,
            "sha256": str(row.get("sha256") or "").casefold() or None,
            "identity_read_error_class": row.get("identity_read_error_class"),
        }
        for row in observed_image_rows
    ]
    expected_hashes = [str(row.get("sha256") or "") for row in expected_rows]
    observed_hashes = [str(row.get("sha256") or "") for row in observed_rows]
    expected_counter = Counter(value for value in expected_hashes if value)
    observed_counter = Counter(value for value in observed_hashes if value)
    missing_hashes = list((expected_counter - observed_counter).elements())
    unexpected_hashes = list((observed_counter - expected_counter).elements())
    unresolved_rows = [row for row in observed_rows if not row.get("sha256")]
    count_exact = len(expected_rows) == len(observed_rows)
    blockers = list(expected_blockers)
    if not expected_manifest_supplied:
        blockers.append("canonical_article_media_manifest_not_supplied")
    if not count_exact:
        blockers.append("canonical_article_media_count_mismatch")
    if missing_hashes:
        blockers.append("canonical_article_media_missing")
    if unexpected_hashes:
        blockers.append("unexpected_public_body_media")
    if unresolved_rows:
        blockers.append("public_body_media_identity_unresolved")
    exact = bool(
        expected_manifest_supplied
        and not blockers
        and expected_counter == observed_counter
    )
    unexpected_rows: list[dict[str, Any]] = []
    remaining = Counter(expected_counter)
    for row in observed_rows:
        digest = str(row.get("sha256") or "")
        if digest and remaining[digest] > 0:
            remaining[digest] -= 1
            continue
        unexpected_rows.append(dict(row))
    expected_manifest = [
        {"asset_id": row["asset_id"], "sha256": row["sha256"]}
        for row in expected_rows
    ]
    unexpected_manifest = [
        {
            "src": row.get("src"),
            "original_url": row.get("original_url"),
            "sha256": row.get("sha256"),
        }
        for row in unexpected_rows
    ]
    return {
        "expected_article_media_count": len(expected_rows),
        "actual_article_media_count": len(observed_rows),
        "article_media_count_exact": count_exact,
        "expected_article_media_sha256": expected_hashes,
        "actual_article_media_sha256": [value or None for value in observed_hashes],
        "missing_article_media_sha256": missing_hashes,
        "unexpected_article_media_sha256": unexpected_hashes,
        "unexpected_article_media_identities": unexpected_manifest,
        "unresolved_article_media_identity_count": len(unresolved_rows),
        "expected_article_media_manifest_sha256": _canonical_json_sha256(
            expected_manifest
        ),
        "unexpected_article_media_manifest_sha256": _canonical_json_sha256(
            unexpected_manifest
        ),
        "article_media_manifest_exact_match": exact,
        "article_media_contract_blockers": list(dict.fromkeys(blockers)),
    }


def _substack_resume_media_contract(
    *,
    expected_image_assets: Sequence[Mapping[str, Any]],
    observed_image_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Accept only an exact sequential canonical prefix for an existing draft."""
    expected_rows, expected_blockers = _expected_article_media_identity_rows(
        expected_image_assets
    )
    observed_rows = [dict(row) for row in observed_image_rows]
    observed_hashes = [str(row.get("sha256") or "").casefold() for row in observed_rows]
    expected_hashes = [str(row.get("sha256") or "").casefold() for row in expected_rows]
    blockers = list(expected_blockers)
    if len(observed_rows) > len(expected_rows):
        blockers.append("existing_draft_contains_unexpected_extra_media")
    if any(not value for value in observed_hashes):
        blockers.append("existing_draft_media_identity_unresolved")
    prefix_expected = expected_hashes[: len(observed_hashes)]
    if observed_hashes != prefix_expected:
        blockers.append("existing_draft_media_not_exact_canonical_prefix")
    return {
        "resume_media_safe": not blockers,
        "resume_media_exact": bool(
            not blockers and len(observed_hashes) == len(expected_hashes)
        ),
        "observed_editor_image_count": len(observed_rows),
        "expected_image_count": len(expected_rows),
        "observed_editor_media_sha256": [value or None for value in observed_hashes],
        "expected_editor_media_sha256": expected_hashes,
        "resume_media_blockers": list(dict.fromkeys(blockers)),
    }


def _first_visible(page: Any, selectors: Sequence[str]) -> tuple[Any | None, str | None]:
    for selector in selectors:
        try:
            candidates = page.locator(selector)
            for index in range(min(candidates.count(), 8)):
                locator = candidates.nth(index)
                if locator.is_visible(timeout=1200):
                    return locator, selector
        except Exception:
            continue
    return None, None


def _click_first_visible(page: Any, selectors: Sequence[str]) -> str | None:
    for start_index, start_selector in enumerate(selectors):
        locator, selector = _first_visible(page, selectors[start_index:])
        if not locator:
            return None
        try:
            locator.click(timeout=6000)
            return selector
        except Exception:
            continue
    return None


def _set_first_file_input(page: Any, file_path: str | Path) -> str | None:
    resolved = str(Path(file_path).resolve())
    for selector in ("input[type='file']", "[data-testid='fileInput']"):
        try:
            for input_locator in page.locator(selector).all():
                try:
                    input_locator.set_input_files(resolved, timeout=10000)
                    return selector
                except Exception:
                    continue
        except Exception:
            continue
    return None


def _file_input_snapshot(page: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        inputs = page.locator("input[type='file']").all()
    except Exception:
        return rows
    for index, locator in enumerate(inputs):
        try:
            rows.append(
                {
                    "index": index,
                    "accept": str(locator.get_attribute("accept") or "").lower(),
                    "disabled": bool(locator.is_disabled(timeout=500)),
                    "connected": bool(locator.evaluate("node => node.isConnected")),
                }
            )
        except Exception:
            rows.append({"index": index, "accept": "", "disabled": True, "connected": False})
    return rows


def _accepts_media_kind(accept: str, media_kind: str, *, exclusive: bool = False) -> bool:
    normalized = str(accept or "").lower()
    markers = {
        "image": ("image/", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".heic", ".heif"),
        "video": ("video/", ".mp4", ".mov", ".webm", ".m4v"),
    }
    if media_kind not in markers or not any(marker in normalized for marker in markers[media_kind]):
        return False
    if exclusive:
        other_kind = "video" if media_kind == "image" else "image"
        if any(marker in normalized for marker in markers[other_kind]):
            return False
    return True


def _newest_activated_media_input(
    page: Any,
    *,
    before: Sequence[Mapping[str, Any]],
    media_kind: str,
    exclusive: bool = False,
    timeout_seconds: float = 8.0,
) -> tuple[Any | None, dict[str, Any]]:
    """Return only a newly created or newly enabled matching file input."""
    deadline = time.monotonic() + timeout_seconds
    last_after: list[dict[str, Any]] = []
    while time.monotonic() < deadline:
        last_after = _file_input_snapshot(page)
        try:
            locators = page.locator("input[type='file']").all()
        except Exception:
            locators = []
        for index in range(len(locators) - 1, -1, -1):
            state = last_after[index]
            if state["disabled"] or not state["connected"]:
                continue
            if not _accepts_media_kind(str(state["accept"]), media_kind, exclusive=exclusive):
                continue
            is_new = index >= len(before)
            newly_enabled = index < len(before) and bool(before[index].get("disabled"))
            accept_changed = index < len(before) and str(before[index].get("accept") or "") != str(state["accept"])
            if is_new or newly_enabled or accept_changed:
                return locators[index], {
                    "input_index": index,
                    "activation": "new_input" if is_new else "newly_enabled_or_retyped_input",
                    "input_count_before": len(before),
                    "input_count_after": len(last_after),
                }
        time.sleep(0.2)
    return None, {
        "input_index": None,
        "activation": "no_new_or_newly_enabled_matching_input",
        "input_count_before": len(before),
        "input_count_after": len(last_after),
    }


def _activate_file_upload(
    page: Any,
    *,
    trigger: Any,
    file_path: str | Path,
    media_kind: str,
    exclusive: bool = False,
    chooser_timeout_ms: int = 8000,
) -> dict[str, Any]:
    """Set a local file through Playwright without interacting with native dialogs."""
    resolved = Path(file_path).resolve()
    if not resolved.exists():
        return {"status": "file_missing", "upload_transport": None}
    before = _file_input_snapshot(page)
    chooser = None
    chooser_error_class = None
    try:
        with page.expect_file_chooser(timeout=chooser_timeout_ms) as chooser_info:
            trigger.click(timeout=6000)
        chooser = chooser_info.value
        chooser.set_files(str(resolved))
        return {
            "status": "file_set",
            "upload_transport": "playwright_file_chooser",
            "native_dialog_automation_used": False,
            "input_count_before": len(before),
        }
    except Exception as exc:
        chooser_error_class = type(exc).__name__
        if chooser is not None:
            try:
                chooser.set_files([])
            except Exception:
                pass

    input_locator, input_meta = _newest_activated_media_input(
        page,
        before=before,
        media_kind=media_kind,
        exclusive=exclusive,
    )
    if input_locator is None:
        return {
            "status": "file_input_not_found",
            "upload_transport": None,
            "chooser_error_class": chooser_error_class,
            "native_dialog_automation_used": False,
            **input_meta,
        }
    try:
        input_locator.set_input_files(str(resolved), timeout=15000)
    except Exception as exc:
        return {
            "status": "set_input_files_failed",
            "upload_transport": "newest_activated_file_input",
            "chooser_error_class": chooser_error_class,
            "set_input_error_class": type(exc).__name__,
            "native_dialog_automation_used": False,
            **input_meta,
        }
    return {
        "status": "file_set",
        "upload_transport": "newest_activated_file_input",
        "chooser_error_class": chooser_error_class,
        "native_dialog_automation_used": False,
        **input_meta,
    }


def _meaningful_image_dimensions(
    *,
    rendered_width: float,
    rendered_height: float,
    natural_width: float | None = None,
    natural_height: float | None = None,
) -> bool:
    natural_ok = True
    if natural_width is not None and natural_height is not None:
        natural_ok = natural_width >= _MEANINGFUL_IMAGE_MIN_WIDTH and natural_height >= _MEANINGFUL_IMAGE_MIN_HEIGHT
    return bool(
        rendered_width >= _MEANINGFUL_IMAGE_MIN_WIDTH
        and rendered_height >= _MEANINGFUL_IMAGE_MIN_HEIGHT
        and natural_ok
    )


def _editor_image_count(page: Any) -> int:
    try:
        return page.locator(".ProseMirror img, div.ProseMirror img").count()
    except Exception:
        return 0


def _append_editor_text(page: Any, editor: Any, text: str, *, clear: bool = False) -> None:
    if not text:
        return
    editor.click(timeout=6000)
    if clear:
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
    else:
        page.keyboard.press("Control+End")
    if not text.strip():
        page.keyboard.press("Enter")
        return
    _insert_editor_native_rich_text(editor, text)


def _substack_native_segment_html(markdown: str) -> str:
    """Serialize canonical article semantics, never Markdown source, for ProseMirror."""
    return rich_text_to_html(markdown_to_rich_text(markdown))


def _insert_editor_native_rich_text(editor: Any, markdown: str) -> None:
    document = markdown_to_rich_text(markdown)
    html_payload = rich_text_to_html(document)
    plain_payload = rich_text_to_plain_text(document)
    if not html_payload:
        return
    result = editor.evaluate(
        """(element, payload) => {
            element.focus();
            const transfer = new DataTransfer();
            transfer.setData('text/html', payload.html);
            transfer.setData('text/plain', payload.plain);
            const event = new ClipboardEvent('paste', {
                clipboardData: transfer, bubbles: true, cancelable: true
            });
            const dispatched = element.dispatchEvent(event);
            if (dispatched) {
                document.execCommand('insertHTML', false, payload.html);
                element.dispatchEvent(new InputEvent('input', {
                    bubbles: true, inputType: 'insertFromPaste', data: payload.plain
                }));
            }
            return {dispatched, defaultPrevented: event.defaultPrevented};
        }""",
        {"html": html_payload, "plain": plain_payload},
    )
    if not isinstance(result, Mapping):
        raise RuntimeError("substack_native_rich_text_insert_unverified")


def _editor_native_semantics_readback(editor: Any, body_markdown: str) -> dict[str, Any]:
    state = editor.evaluate(
        """element => ({
            headingCount: element.querySelectorAll('h2,h3,h4').length,
            linkCount: element.querySelectorAll('a[href]').length,
            listCount: element.querySelectorAll('ul,ol').length,
            text: element.innerText || '',
            html: element.innerHTML || ''
        })"""
    )
    visible = str((state or {}).get("text") or "")
    expected_headings = len(re.findall(r"(?m)^#{2,4}\s+", body_markdown or ""))
    expected_links = len(re.findall(r"\[[^\]\n]+\]\(https?://[^)\s]+\)", body_markdown or ""))
    raw_markdown_visible = bool(
        re.search(r"(?m)^#{2,4}\s+", visible)
        or re.search(r"\[[^\]\n]+\]\(https?://[^)\s]+\)", visible)
        or "[[VISUAL:" in visible
    )
    raw_html_visible = bool(re.search(r"<!DOCTYPE|<html\b|<script\b|<style\b", visible, re.I))
    native_verified = bool(
        not raw_markdown_visible
        and not raw_html_visible
        and int((state or {}).get("headingCount") or 0) >= expected_headings
        and int((state or {}).get("linkCount") or 0) >= expected_links
    )
    return {
        "native_semantics_verified": native_verified,
        "expected_heading_count": expected_headings,
        "editor_heading_count": int((state or {}).get("headingCount") or 0),
        "expected_link_count": expected_links,
        "editor_link_count": int((state or {}).get("linkCount") or 0),
        "editor_list_count": int((state or {}).get("listCount") or 0),
        "raw_markdown_visible": raw_markdown_visible,
        "raw_html_visible": raw_html_visible,
    }


def _append_editor_tail_after_media(page: Any, editor: Any, text: str) -> None:
    """Place a missing final text segment after the last ProseMirror media node."""
    if not text:
        return
    editor.scroll_into_view_if_needed(timeout=5000)
    editor.evaluate(
        """element => {
            element.focus();
            const selection = window.getSelection();
            const range = document.createRange();
            range.selectNodeContents(element);
            range.collapse(false);
            selection.removeAllRanges();
            selection.addRange(range);
        }"""
    )
    page.keyboard.press("Enter")
    _insert_editor_native_rich_text(editor, text)


def _normalise_editor_text(value: str) -> str:
    without_headings = re.sub(r"(?m)^#{1,6}\s+", "", value or "")
    # Rich-text input rules can normalize punctuation while preserving the
    # article itself. Compare stable word tokens for an in-place recovery.
    return " ".join(re.findall(r"[\w]+", without_headings.casefold()))


def _normalise_exact_listing_title(value: str) -> str:
    """Collapse layout whitespace while preserving exact title punctuation and case."""
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _split_substack_body(body_markdown: str) -> list[tuple[str, str]]:
    parts: list[tuple[str, str]] = []
    previous = 0
    for match in _VISUAL_MARKER_RE.finditer(body_markdown or ""):
        if match.start() > previous:
            parts.append(("text", body_markdown[previous:match.start()]))
        parts.append(("visual", match.group(1)))
        previous = match.end()
    if previous < len(body_markdown or ""):
        parts.append(("text", body_markdown[previous:]))
    return parts or [("text", body_markdown)]


def _segment_index_after_visual_prefix(
    segments: Sequence[tuple[str, str]], completed_visual_count: int
) -> int:
    """Return the first segment after an exact sequential visual prefix."""
    if completed_visual_count <= 0:
        return 0
    observed = 0
    for index, (kind, _value) in enumerate(segments):
        if kind != "visual":
            continue
        observed += 1
        if observed == completed_visual_count:
            return index + 1
    return len(segments)


def _substack_upload_pending(page: Any) -> bool:
    return bool(
        _first_visible(
            page,
            (
                ".ProseMirror [data-testid*='uploading']",
                ".ProseMirror [class*='uploading']",
                ".ProseMirror [aria-label*='Uploading']",
                ".ProseMirror [role='progressbar']",
            ),
        )[0]
    )


def _substack_saved(page: Any) -> bool:
    return bool(_first_visible(page, ("text=Saved", "[data-testid*='saved']"))[0])


def _editor_image_readback(image: Any) -> dict[str, Any]:
    try:
        dimensions = image.evaluate(
            "node => ({complete: Boolean(node.complete), naturalWidth: node.naturalWidth || 0, "
            "naturalHeight: node.naturalHeight || 0, inBody: Boolean(node.closest('.ProseMirror')), "
            "src: String(node.currentSrc || node.src || '')})"
        )
        box = image.bounding_box() or {}
        visible = bool(image.is_visible(timeout=1000))
    except Exception:
        return {
            "complete": False,
            "natural_width": 0,
            "natural_height": 0,
            "rendered_width": 0,
            "rendered_height": 0,
            "in_article_body": False,
            "visible": False,
            "src": None,
        }
    return {
        "complete": bool(dimensions.get("complete")),
        "natural_width": int(dimensions.get("naturalWidth") or 0),
        "natural_height": int(dimensions.get("naturalHeight") or 0),
        "rendered_width": round(float(box.get("width") or 0), 1),
        "rendered_height": round(float(box.get("height") or 0), 1),
        "in_article_body": bool(dimensions.get("inBody")),
        "visible": visible,
        "src": str(dimensions.get("src") or "") or None,
    }


def _meaningful_editor_image_rows(page: Any) -> list[tuple[int, dict[str, Any]]]:
    rows: list[tuple[int, dict[str, Any]]] = []
    images = page.locator(".ProseMirror img")
    for index in range(images.count()):
        state = _editor_image_readback(images.nth(index))
        meaningful = _meaningful_image_dimensions(
            rendered_width=float(state.get("rendered_width") or 0),
            rendered_height=float(state.get("rendered_height") or 0),
            natural_width=float(state.get("natural_width") or 0),
            natural_height=float(state.get("natural_height") or 0),
        )
        if (
            state.get("complete")
            and state.get("visible")
            and state.get("in_article_body")
            and meaningful
        ):
            rows.append((index, state))
    return rows


def _editor_image_identity_rows(page: Any) -> list[dict[str, Any]]:
    """Read every editor-body image, including unexpected or undersized objects."""
    rows: list[dict[str, Any]] = []
    images = page.locator(".ProseMirror img")
    for index in range(images.count()):
        state = _editor_image_readback(images.nth(index))
        identity = _remote_substack_image_identity(str(state.get("src") or ""))
        rows.append({"editor_image_index": index, **state, **identity})
    return rows


def _upload_substack_image(
    page: Any,
    editor: Any,
    file_path: str | Path,
    alt_text: str,
    *,
    asset_id: str,
    expected_image_index: int,
) -> dict[str, Any]:
    before = _editor_image_count(page)
    meaningful_before = len(_meaningful_editor_image_rows(page))
    editor.click(timeout=6000)
    page.keyboard.press("Control+End")
    toolbar_selector = _click_first_visible(
        page,
        (
            "button[aria-label='Image']",
            "button[aria-label*='Image']",
            "button[title*='Image']",
            "button[title*='image']",
        ),
    )
    if toolbar_selector:
        time.sleep(0.6)
    menu_item, menu_selector = _first_visible(
        page,
        (
            "[role='menuitem']:has-text('Image')",
            "[role='menuitem'] :text-is('Image')",
            "text=Image",
        ),
    )
    if not menu_item:
        return {
            "status": "file_input_not_found",
            "asset_id": asset_id,
            "toolbar_selector": toolbar_selector,
            "menu_selector": menu_selector,
            "editor_image_count_before": before,
            "editor_image_count_after": _editor_image_count(page),
            "alt_text_status": "not_attempted",
            "native_dialog_automation_used": False,
        }
    transfer = _activate_file_upload(
        page,
        trigger=menu_item,
        file_path=file_path,
        media_kind="image",
        exclusive=True,
    )
    if transfer["status"] != "file_set":
        return {
            "status": transfer["status"],
            "asset_id": asset_id,
            "toolbar_selector": toolbar_selector,
            "menu_selector": menu_selector,
            "editor_image_count_before": before,
            "editor_image_count_after": _editor_image_count(page),
            "alt_text_status": "not_attempted",
            **transfer,
        }
    deadline = time.monotonic() + 60
    after = _editor_image_count(page)
    image_state: dict[str, Any] = {}
    meaningful_after = meaningful_before
    inserted_dom_index: int | None = None
    while time.monotonic() < deadline:
        after = _editor_image_count(page)
        meaningful_rows = _meaningful_editor_image_rows(page)
        meaningful_after = len(meaningful_rows)
        if meaningful_after == meaningful_before + 1 and not _substack_upload_pending(page):
            inserted_dom_index, image_state = meaningful_rows[-1]
            break
        time.sleep(0.5)

    alt_status = "not_exposed_by_current_editor"
    if meaningful_after == meaningful_before + 1 and alt_text and inserted_dom_index is not None:
        try:
            last_image = page.locator(".ProseMirror img").nth(inserted_dom_index)
            last_image.click(timeout=3000)
            alt_input, _alt_selector = _first_visible(
                page,
                (
                    "input[placeholder*='Alt']",
                    "textarea[placeholder*='Alt']",
                    "input[aria-label*='Alt']",
                ),
            )
            if alt_input:
                alt_input.fill(alt_text)
                page.keyboard.press("Enter")
                alt_status = "set_in_editor"
        except Exception:
            alt_status = "not_exposed_by_current_editor"
    saved_deadline = time.monotonic() + 30
    draft_saved = _substack_saved(page)
    while time.monotonic() < saved_deadline and not draft_saved:
        time.sleep(0.4)
        draft_saved = _substack_saved(page)
    count_exact = meaningful_after == meaningful_before + 1
    intended_position = meaningful_before == expected_image_index and count_exact
    meaningful_dimensions = _meaningful_image_dimensions(
        rendered_width=float(image_state.get("rendered_width") or 0),
        rendered_height=float(image_state.get("rendered_height") or 0),
        natural_width=float(image_state.get("natural_width") or 0),
        natural_height=float(image_state.get("natural_height") or 0),
    )
    spinner_cleared = not _substack_upload_pending(page)
    blockers: list[str] = []
    if not count_exact:
        blockers.append("editor_image_count_did_not_increase_by_exactly_one")
    if not image_state.get("in_article_body"):
        blockers.append("inserted_image_not_in_article_body")
    if not meaningful_dimensions:
        blockers.append("inserted_image_dimensions_below_chart_threshold")
    if not image_state.get("complete") or not image_state.get("visible"):
        blockers.append("inserted_image_not_loaded_and_visible")
    if not spinner_cleared:
        blockers.append("image_upload_spinner_or_placeholder_present")
    if not draft_saved:
        blockers.append("substack_draft_not_saved_after_image_upload")
    if not intended_position:
        blockers.append("image_not_at_expected_sequential_marker_position")
    return {
        **transfer,
        "status": "uploaded" if not blockers else "upload_unverified",
        "asset_id": asset_id,
        "blockers": blockers,
        "toolbar_selector": toolbar_selector,
        "menu_selector": menu_selector,
        "editor_image_count_before": before,
        "editor_image_count_after": after,
        "meaningful_editor_image_count_before": meaningful_before,
        "meaningful_editor_image_count_after": meaningful_after,
        "editor_image_count_increment_exactly_one": count_exact,
        "inserted_image_index": meaningful_before if count_exact else None,
        "intended_marker_position_verified": intended_position,
        "image_readback": image_state,
        "meaningful_dimensions_verified": meaningful_dimensions,
        "upload_spinner_or_placeholder_cleared": spinner_cleared,
        "draft_saved_after_upload": draft_saved,
        "alt_text_status": alt_status,
    }


class _InstrumentedPersistentPage:
    """Transparent Playwright page proxy that records only sanitized interaction classes."""

    def __init__(self, page: Any) -> None:
        self._page = page

    def __getattr__(self, name: str) -> Any:
        return getattr(self._page, name)

    def goto(self, *args: Any, **kwargs: Any) -> Any:
        record_browser_interaction_event(
            "navigation", reason="EDGE_DESTINATION_NAVIGATION", destination=None
        )
        return self._page.goto(*args, **kwargs)

    def reload(self, *args: Any, **kwargs: Any) -> Any:
        record_browser_interaction_event(
            "navigation", reason="EDGE_DESTINATION_RELOAD", destination=None
        )
        return self._page.reload(*args, **kwargs)

    def close(self, *args: Any, **kwargs: Any) -> Any:
        record_browser_interaction_event(
            "tab_closed", reason="EXPLICIT_EDGE_TAB_CLOSE", destination=None
        )
        return self._page.close(*args, **kwargs)


def _reusable_canonical_page(context: Any) -> Any | None:
    allowed_hosts = {
        "capitalchronicle.substack.com", "substack.com", "x.com",
        "studio.youtube.com", "www.youtube.com", "youtube.com",
    }
    internal_schemes = {"about", "edge", "chrome"}
    for candidate in context.pages:
        try:
            parsed = urllib.parse.urlparse(str(candidate.url or ""))
            if parsed.hostname in allowed_hosts or parsed.scheme in internal_schemes:
                return candidate
        except Exception:
            continue
    return None


@contextmanager
def canonical_edge_page(cdp_port: int) -> Iterator[Any]:
    """Reuse one safe canonical tab and leave it open for probe → publish → readback."""
    assert_canonical_edge_cdp(cdp_port)
    from playwright.sync_api import sync_playwright

    playwright = sync_playwright().start()
    try:
        browser = playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{cdp_port}", timeout=15000)
        if not browser.contexts:
            raise PublishingProfileError("canonical_edge_has_no_browser_context")
        context = browser.contexts[0]
        page = _reusable_canonical_page(context)
        if page is None:
            page = context.new_page()
            record_browser_interaction_event(
                "tab_created", reason="NO_REUSABLE_CANONICAL_DESTINATION_TAB", destination=None
            )
        yield _InstrumentedPersistentPage(page)
    finally:
        # Detach only. The destination tab and operator-owned Edge process are intentionally
        # preserved so one bounded session can cover probe → publish → exact readback.
        playwright.stop()


def capture_public_destination_via_edge(
    *,
    cdp_port: int,
    public_url: str,
    screenshot_path: str | Path,
    expected_domain: str,
) -> dict[str, Any]:
    """Capture a public destination for visual QA without reading browser storage."""
    with canonical_edge_page(cdp_port) as page:
        page.goto(public_url, wait_until="domcontentloaded", timeout=45000)
        time.sleep(5)
        target = Path(screenshot_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(target), full_page=False)
        domain = urllib.parse.urlparse(page.url).netloc
        return {
            "status": "SUCCESS" if expected_domain in domain else "FAILED_PUBLIC_DESTINATION_DOMAIN_MISMATCH",
            "requested_public_url": public_url,
            "final_public_url": page.url,
            "expected_domain": expected_domain,
            "final_domain": domain,
            "public_screenshot_path": str(target),
            "browser_write_performed": False,
            "cookies_read": False,
            "storage_read": False,
        }


def probe_authenticated_platform_session(cdp_port: int, platform: str) -> dict[str, Any]:
    """Perform a light login/destination check without dumping DOM or session data."""
    targets = {
        "substack": ("https://capitalchronicle.substack.com/publish/post", ("a:has-text('Sign in')", "button:has-text('Sign in')"), ("#post-title", "div.ProseMirror", ".ProseMirror")),
        "x": ("https://x.com/home", ("a[href='/i/flow/login']", "text=Sign in"), ("[data-testid='tweetTextarea_0']", "[data-testid='AppTabBar_Profile_Link']")),
        "linkedin": ("https://www.linkedin.com/feed/", ("a:has-text('Sign in')", "a:has-text('Join now')"), ("button:has-text('Start a post')", "text=Start a post")),
        "tiktok": ("https://www.tiktok.com/tiktokstudio/upload", ("text=Log in", "button:has-text('Log in')"), ("input[type='file']", "[data-e2e*='upload']")),
        "youtube": ("https://studio.youtube.com/", ("a:has-text('Sign in')", "text=Sign in"), ("#create-icon", "ytcp-button#avatar-btn", "ytcp-button[aria-label*='Create']", "ytcp-button[aria-label*='Tạo']", "button[aria-label*='Create']", "button[aria-label*='Tạo']", "text=Channel dashboard")),
    }
    if platform not in targets:
        raise ValueError("unsupported_browser_platform_probe")
    target_url, login_selectors, authenticated_selectors = targets[platform]
    with canonical_edge_page(cdp_port) as page:
        page.goto(target_url, wait_until="domcontentloaded", timeout=45000)
        time.sleep(4)
        login_detected = bool(_first_visible(page, login_selectors)[0])
        if platform == "tiktok" and "tiktok.com/login" in page.url:
            login_detected = True
        authenticated_selector = _first_visible(page, authenticated_selectors)[1]
        identity = None
        destination_stable_id = None
        if platform == "x":
            profile_link, _selector = _first_visible(page, ("[data-testid='AppTabBar_Profile_Link']",))
            try:
                href = profile_link.get_attribute("href") if profile_link else None
                if href and href.startswith("/") and "/" not in href[1:]:
                    identity = "@" + href.lstrip("/")
            except Exception:
                pass
        elif platform == "linkedin":
            link, _selector = _first_visible(page, ("a[href*='/in/']",))
            try:
                href = link.get_attribute("href") if link else None
                match = re.search(r"/in/([^/?#]+)", href or "")
                if match:
                    identity = "linkedin:" + match.group(1)
            except Exception:
                pass
        elif platform == "youtube":
            candidates = [page.url]
            try:
                candidates.extend(
                    str(link.get_attribute("href") or "")
                    for link in page.locator("a[href*='/channel/']").all()[:12]
                )
            except Exception:
                pass
            for candidate in candidates:
                match = re.search(r"/channel/(UC[A-Za-z0-9_-]+)", candidate)
                if match:
                    destination_stable_id = match.group(1)
                    break
        authenticated = bool(authenticated_selector and not login_detected)
        if platform == "tiktok":
            authenticated = bool("tiktokstudio/upload" in page.url and authenticated_selector and not login_detected)
        return {
            "platform": platform,
            "profile_id": CANONICAL_PROFILE_ID,
            "authenticated": authenticated,
            "login_control_detected": login_detected,
            "authenticated_ui_selector": authenticated_selector,
            "destination_identity": identity,
            "destination_stable_id": destination_stable_id,
            "page_domain": urllib.parse.urlparse(page.url).netloc,
            "cookies_read": False,
            "storage_read": False,
            "dom_dump_persisted": False,
        }


def _extract_substack_public_url(page: Any) -> str | None:
    """Read only page-bound public identity, never an unrelated visible article link."""
    candidates: list[str] = [page.url]
    for selector, attribute in (("link[rel='canonical']", "href"), ("meta[property='og:url']", "content")):
        try:
            value = page.locator(selector).first.get_attribute(attribute)
            if value:
                candidates.append(value)
        except Exception:
            continue
    for candidate in candidates:
        absolute = _absolute_substack_url(candidate)
        if _is_public_substack_url(absolute):
            return absolute.split("?", 1)[0]
    return None


def _substack_draft_id(url: str) -> str | None:
    match = re.search(r"/publish/post/(\d+)", url or "")
    return match.group(1) if match else None


def _public_substack_content_checks(
    *,
    visible_text: str,
    hrefs: Sequence[str],
    meta_description: str,
    expected_title: str | None,
    expected_subtitle: str | None,
    expected_body_markdown: str | None,
    expected_image_assets: Sequence[Mapping[str, Any]] | None,
) -> dict[str, Any]:
    normalized_visible_with_urls = _normalise_editor_text(visible_text)
    visible_without_literal_markdown_links = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", visible_text or "")
    normalized_visible = _normalise_editor_text(visible_without_literal_markdown_links)
    title_visible = True if not expected_title else _normalise_editor_text(expected_title) in normalized_visible
    subtitle_visible = True if not expected_subtitle else _normalise_editor_text(expected_subtitle) in normalized_visible
    anchors: list[str] = []
    source_urls: list[str] = []
    if expected_body_markdown:
        source_urls = re.findall(r"https://[^)\s]+", expected_body_markdown)
        for kind, value in _split_substack_body(expected_body_markdown):
            if kind != "text":
                continue
            text_only = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
            for paragraph in re.split(r"\n\s*\n", text_only):
                normalized = _normalise_editor_text(paragraph)
                words = normalized.split()
                if len(words) >= 8 and not normalized.startswith("source "):
                    anchors.append(" ".join(words[: min(12, len(words))]))
    matched_anchors = [anchor for anchor in anchors if anchor in normalized_visible]
    minimum_anchor_matches = max(1, (len(anchors) + 1) // 2) if anchors else 0
    body_identity_matched = bool(
        anchors and len(matched_anchors) >= minimum_anchor_matches
    )
    captions = [
        _normalise_editor_text(str(asset.get("caption") or ""))
        for asset in expected_image_assets or []
        if str(asset.get("caption") or "").strip()
    ]
    # Visuals are optional for a valid canonical article.  When assets are present their
    # captions remain exact readback bindings; an empty asset set is not itself a content
    # failure.
    captions_visible = all(caption in normalized_visible for caption in captions)
    source_links_visible = bool(source_urls) and all(
        source_url in hrefs or _normalise_editor_text(source_url) in normalized_visible_with_urls
        for source_url in source_urls
    )
    no_process_language = not bool(_EDITORIAL_PROCESS_TEXT_RE.search(visible_text))
    # Canonical acceptance binds the correct Substack destination, public URL, title, and a
    # sufficient body fingerprint. Subtitle, captions, image count/spread, source-link DOM
    # rendering, and meta description remain quality telemetry rather than publication gates.
    content_verified = bool(title_visible and body_identity_matched and no_process_language)
    return {
        "title_visible": title_visible,
        "subtitle_visible": subtitle_visible,
        "body_complete": all(anchor in normalized_visible for anchor in anchors),
        "body_identity_fingerprint_matched": body_identity_matched,
        "body_anchor_count": len(anchors),
        "body_anchor_match_count": len(matched_anchors),
        "body_anchor_minimum_match_count": minimum_anchor_matches,
        "captions_visible": captions_visible,
        "caption_accessibility_fallback_verified": captions_visible,
        "caption_count_expected": len(captions),
        "source_links_visible": source_links_visible,
        "source_url_count_expected": len(source_urls),
        "editorial_process_language_absent": no_process_language,
        "public_meta_description_present": bool(meta_description.strip()),
        "destination_identity_verified": True,
        "content_readback_verified": content_verified,
    }


def _audit_public_substack_article(
    page: Any,
    public_url: str,
    screenshot_path: str | Path | None,
    *,
    expected_title: str | None = None,
    expected_subtitle: str | None = None,
    expected_body_markdown: str | None = None,
    expected_image_assets: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    page.goto(public_url, wait_until="domcontentloaded", timeout=45000)
    time.sleep(4)
    image_rows: list[dict[str, Any]] = []
    for selector in ("article img", "[class*='post'] img"):
        try:
            images = page.locator(selector).all()
            if images:
                for image in images:
                    image.scroll_into_view_if_needed(timeout=5000)
                    time.sleep(0.4)
                    src = image.get_attribute("src") or ""
                    if src.startswith("https"):
                        box = image.bounding_box()
                        width = float((box or {}).get("width") or 0)
                        height = float((box or {}).get("height") or 0)
                        dimensions = image.evaluate(
                            "node => ({naturalWidth: node.naturalWidth || 0, naturalHeight: node.naturalHeight || 0, complete: Boolean(node.complete)})"
                        )
                        natural_width = float(dimensions.get("naturalWidth") or 0)
                        natural_height = float(dimensions.get("naturalHeight") or 0)
                        # Ignore author avatars and UI icons; canonical media
                        # must be a chart-sized in-body image.
                        if not dimensions.get("complete") or not _meaningful_image_dimensions(
                            rendered_width=width,
                            rendered_height=height,
                            natural_width=natural_width,
                            natural_height=natural_height,
                        ):
                            continue
                        document_top = float(
                            image.evaluate("node => node.getBoundingClientRect().top + window.scrollY") or 0
                        )
                        image_rows.append(
                            {
                                "src": src,
                                "top": round(document_top, 1),
                                "width": round(width, 1),
                                "height": round(height, 1),
                                "natural_width": int(natural_width),
                                "natural_height": int(natural_height),
                                "alt_present": bool((image.get_attribute("alt") or "").strip()),
                            }
                        )
                if image_rows:
                    break
        except Exception:
            continue
    image_rows = [
        {**row, **_remote_substack_image_identity(str(row.get("src") or ""))}
        for row in image_rows
    ]
    tops = sorted(row["top"] for row in image_rows)
    expected_image_count = len(expected_image_assets or [])
    visual_spread = bool(
        len(tops) >= expected_image_count
        and (
            expected_image_count < 2
            or all((right - left) >= 240 for left, right in zip(tops, tops[1:]))
        )
    )
    visible_text = ""
    for selector in ("article", "[class*='post-content']", "body"):
        try:
            visible_text = page.locator(selector).first.inner_text(timeout=5000)
        except Exception:
            continue
        if visible_text:
            break
    hrefs: list[str] = []
    try:
        hrefs = [str(link.get_attribute("href") or "") for link in page.locator("a[href]").all()]
    except Exception:
        pass
    meta_description = ""
    for selector, attribute in (
        ("meta[name='description']", "content"),
        ("meta[property='og:description']", "content"),
    ):
        try:
            meta_description = str(page.locator(selector).first.get_attribute(attribute) or "").strip()
        except Exception:
            continue
        if meta_description:
            break
    content_checks = _public_substack_content_checks(
        visible_text=visible_text,
        hrefs=hrefs,
        meta_description=meta_description,
        expected_title=expected_title,
        expected_subtitle=expected_subtitle,
        expected_body_markdown=expected_body_markdown,
        expected_image_assets=expected_image_assets,
    )
    media_contract = _exact_substack_article_media_contract(
        expected_image_assets=expected_image_assets,
        observed_image_rows=image_rows,
        expected_manifest_supplied=expected_image_assets is not None,
    )
    text_content_verified = bool(content_checks.get("content_readback_verified"))
    strict_content_visual_verified = bool(
        text_content_verified
        and media_contract["article_media_manifest_exact_match"]
    )
    saved_screenshot = None
    if screenshot_path:
        path = Path(screenshot_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(path), full_page=True)
        saved_screenshot = str(path)
    return {
        "public_url": public_url,
        "public_image_count": len(image_rows),
        "public_image_urls": [row["src"] for row in image_rows[:3]],
        "public_image_alt_count": sum(1 for row in image_rows if row["alt_present"]),
        "public_image_alt_or_caption_count": (
            sum(1 for row in image_rows if row["alt_present"])
            if any(row["alt_present"] for row in image_rows)
            else (len(image_rows) if content_checks["caption_accessibility_fallback_verified"] else 0)
        ),
        "image_accessibility_mode": (
            "html_alt"
            if sum(1 for row in image_rows if row["alt_present"]) == len(image_rows) and image_rows
            else "visible_caption_fallback_substack_alt_control_not_exposed"
        ),
        "visual_spread_through_public_body": visual_spread,
        "public_screenshot_path": saved_screenshot,
        "visible_body_text": visible_text,
        **content_checks,
        **media_contract,
        "text_content_readback_verified": text_content_verified,
        "strict_content_visual_readback_verified": strict_content_visual_verified,
        "content_readback_verified": strict_content_visual_verified,
    }


def readback_public_substack_article_via_edge(
    *,
    cdp_port: int,
    public_url: str,
    public_screenshot_path: str | Path | None = None,
) -> dict[str, Any]:
    """Refresh public media readback without opening or publishing an editor draft."""
    if not _is_public_substack_url(public_url):
        return {"status": "BLOCKED_INVALID_PUBLIC_SUBSTACK_URL", "platform": "substack"}
    with canonical_edge_page(cdp_port) as page:
        readback = _audit_public_substack_article(page, public_url, public_screenshot_path)
    return {"status": "SUCCESS", "platform": "substack", "public_url": public_url, "readback": readback}


def _strict_substack_readback_status(readback: Mapping[str, Any]) -> str:
    if readback.get("strict_content_visual_readback_verified") is True:
        return "SUCCESS"
    if (
        readback.get("text_content_readback_verified") is True
        and readback.get("article_media_manifest_exact_match") is not True
    ):
        return "FAILED_SUBSTACK_PUBLIC_VISUAL_READBACK"
    return "FAILED_SUBSTACK_PUBLIC_CONTENT_READBACK"


def delete_threads_post_via_edge_exact(
    *,
    cdp_port: int,
    public_url: str,
    post_id: str,
    expected_text: str,
    allowed_post_ids: set[str] | frozenset[str],
    public_screenshot_path: str | Path | None = None,
) -> dict[str, Any]:
    """Delete one allowlisted Threads post through its exact public page."""
    parsed = urllib.parse.urlparse(public_url)
    if (
        post_id not in allowed_post_ids
        or parsed.netloc not in {"threads.com", "www.threads.com"}
        or parsed.path.count("/") < 3
        or not parsed.path.startswith("/@official.capitalchronicle/post/")
    ):
        return {"status": "BLOCKED_THREADS_EDGE_DELETE_TARGET_MISMATCH", "post_id": post_id, "public_url": public_url}
    with canonical_edge_page(cdp_port) as page:
        page.goto(public_url, wait_until="domcontentloaded", timeout=45000)
        time.sleep(4)
        visible = _normalised_visible_text(page.locator("body").inner_text(timeout=5000))
        expected = _normalised_visible_text(expected_text)
        if "official.capitalchronicle" not in visible.casefold() or expected.casefold() not in visible.casefold():
            return {"status": "BLOCKED_THREADS_EDGE_DELETE_IDENTITY_OR_TEXT_MISMATCH", "post_id": post_id, "public_url": public_url}
        text_anchor = page.get_by_text(expected[:120], exact=False).first
        if not text_anchor.count() or not text_anchor.is_visible(timeout=2000):
            return {"status": "BLOCKED_THREADS_EDGE_DELETE_TEXT_ANCHOR_NOT_FOUND", "post_id": post_id, "public_url": public_url}
        scope = text_anchor.locator(
            "xpath=ancestor::div[.//*[@role='button' and @aria-haspopup='menu']][1]"
        )
        menu_control = scope.locator("[role='button'][aria-haspopup='menu']").first if scope.count() else None
        if menu_control is None or not menu_control.count() or not menu_control.is_visible(timeout=2000):
            return {"status": "BLOCKED_THREADS_EDGE_DELETE_MENU_NOT_FOUND", "post_id": post_id, "public_url": public_url}
        menu_control.click(timeout=6000)
        time.sleep(1)
        delete_menu = page.locator("[role='menuitem']:has-text('Delete')").last
        if not delete_menu.count() or not delete_menu.is_visible(timeout=2000):
            return {"status": "BLOCKED_THREADS_EDGE_DELETE_ACTION_NOT_FOUND", "post_id": post_id, "public_url": public_url}
        delete_menu.click(timeout=6000)
        time.sleep(1)
        dialog = page.locator("[role='dialog']")
        confirm = dialog.locator("[role='button']:has-text('Delete')").last if dialog.count() else page.locator("[role='button']:has-text('Delete')").last
        if not confirm.count() or not confirm.is_visible(timeout=2500):
            return {"status": "BLOCKED_THREADS_EDGE_DELETE_CONFIRMATION_NOT_FOUND", "post_id": post_id, "public_url": public_url}
        confirm.click(timeout=6000)
        time.sleep(8)
        page.goto(public_url, wait_until="domcontentloaded", timeout=45000)
        time.sleep(7)
        after_text = _normalised_visible_text(page.locator("body").inner_text(timeout=5000))
        unavailable = expected.casefold() not in after_text.casefold()
        screenshot = None
        if public_screenshot_path:
            target = Path(public_screenshot_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(target), full_page=False)
            screenshot = str(target)
    return {
        "status": "SUCCESS" if unavailable else "FAILED_THREADS_EDGE_DELETE_STILL_PUBLIC",
        "platform": "threads",
        "action": "delete_exact_post_via_edge",
        "post_id": post_id,
        "public_url": public_url,
        "destination_identity": "official.capitalchronicle",
        "delete_performed": True,
        "public_unavailability_verified": unavailable,
        "public_screenshot_path": screenshot,
    }


def verify_threads_post_unavailable_via_edge(
    *,
    cdp_port: int,
    public_url: str,
    expected_text: str,
    public_screenshot_path: str | Path | None = None,
) -> dict[str, Any]:
    """Read-only confirmation that an exact Threads URL no longer exposes its prior text."""
    parsed = urllib.parse.urlparse(public_url)
    if parsed.netloc not in {"threads.com", "www.threads.com"}:
        return {"status": "BLOCKED_INVALID_THREADS_PUBLIC_URL", "public_url": public_url}
    with canonical_edge_page(cdp_port) as page:
        page.goto(public_url, wait_until="domcontentloaded", timeout=45000)
        time.sleep(5)
        visible = _normalised_visible_text(page.locator("body").inner_text(timeout=5000))
        unavailable = _normalised_visible_text(expected_text).casefold() not in visible.casefold()
        screenshot = None
        if public_screenshot_path:
            target = Path(public_screenshot_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(target), full_page=False)
            screenshot = str(target)
    return {
        "status": "SUCCESS" if unavailable else "FAILED_THREADS_POST_STILL_PUBLIC",
        "public_url": public_url,
        "public_unavailability_verified": unavailable,
        "browser_write_performed": False,
        "public_screenshot_path": screenshot,
    }


def audit_public_substack_article_via_edge(
    *,
    cdp_port: int,
    public_url: str,
    expected_title: str,
    expected_subtitle: str,
    expected_body_markdown: str,
    expected_image_assets: Sequence[Mapping[str, Any]],
    public_screenshot_path: str | Path | None = None,
) -> dict[str, Any]:
    """Strictly reconcile an already-public article without opening its editor."""
    if not _is_public_substack_url(public_url):
        return {"status": "BLOCKED_INVALID_PUBLIC_SUBSTACK_URL", "platform": "substack"}
    with canonical_edge_page(cdp_port) as page:
        readback = _audit_public_substack_article(
            page,
            public_url,
            public_screenshot_path,
            expected_title=expected_title,
            expected_subtitle=expected_subtitle,
            expected_body_markdown=expected_body_markdown,
            expected_image_assets=expected_image_assets,
        )
    verified = bool(readback.get("strict_content_visual_readback_verified"))
    return {
        "status": _strict_substack_readback_status(readback),
        "platform": "substack",
        "public_url": public_url,
        "readback": readback,
        "browser_write_performed": False,
    }


def _substack_listing_matches(
    page: Any,
    *,
    expected_title: str,
    href_predicate: Callable[[str], bool],
) -> list[dict[str, str]]:
    """Return sanitized exact-title listing matches without exposing browser material."""
    filter_input, _ = _first_visible(
        page,
        (
            "input[placeholder*='Filter']",
            "input[placeholder*='Search']",
            "input[type='search']",
        ),
    )
    if filter_input is not None:
        try:
            filter_input.fill(expected_title)
            time.sleep(2)
        except Exception:
            pass
    expected = _normalise_exact_listing_title(expected_title)
    matches_by_href: dict[str, dict[str, str]] = {}
    for link in page.locator("a[href]").all():
        try:
            href = str(link.get_attribute("href") or "").strip()
            text = str(link.inner_text(timeout=1200) or "").strip()
        except Exception:
            continue
        lines = [
            _normalise_exact_listing_title(line)
            for line in text.splitlines()
            if _normalise_exact_listing_title(line)
        ]
        if expected not in lines:
            continue
        if href_predicate(href):
            identity_href = href.split("#", 1)[0].split("?", 1)[0]
            matches_by_href.setdefault(
                identity_href,
                {"href": href, "title": expected_title},
            )
    return list(matches_by_href.values())


def _public_substack_url_from_view_post(page: Any) -> str | None:
    """Resolve the public permalink from Substack's read-only published-detail control."""
    view_post, _ = _substack_exact_enabled_button(page, labels=("View post",))
    if view_post is None:
        return None
    existing_pages = list(page.context.pages)
    try:
        view_post.click(timeout=5000)
        page.wait_for_timeout(5000)
    except Exception:
        return None
    candidates = [str(page.url or "")]
    new_pages = [candidate for candidate in page.context.pages if candidate not in existing_pages]
    for _candidate in new_pages:
        record_browser_interaction_event(
            "tab_created", reason="SUBSTACK_VIEW_POST_POPUP", destination="substack"
        )
    candidates.extend(str(candidate.url or "") for candidate in new_pages)
    public_urls = sorted(
        {
            candidate.split("?", 1)[0].split("#", 1)[0]
            for candidate in candidates
            if _is_public_substack_url(candidate)
        }
    )
    for candidate in new_pages:
        try:
            record_browser_interaction_event(
                "tab_closed", reason="SUBSTACK_VIEW_POST_POPUP_CLEANUP", destination="substack"
            )
            candidate.close()
        except Exception:
            pass
    return public_urls[0] if len(public_urls) == 1 else None


def _substack_exact_enabled_button(
    page: Any,
    *,
    labels: Sequence[str],
    preferred_test_id: str | None = None,
) -> tuple[Any | None, str | None]:
    """Return one visible enabled button whose accessible label is an exact match.

    Substack reuses broad words such as ``Publish`` across editor chrome.  Exact labels and the
    observed editor ``data-testid`` keep the public transition bounded to its intended control.
    """
    expected = {_normalise_editor_text(label): label for label in labels if str(label).strip()}
    if not expected:
        return None, None
    try:
        candidates = page.locator("button, [role='button']")
        count = min(int(candidates.count()), 64)
    except Exception:
        return None, None
    passes = (preferred_test_id, None) if preferred_test_id else (None,)
    for required_test_id in passes:
        for index in range(count):
            locator = candidates.nth(index)
            try:
                if not locator.is_visible(timeout=600) or locator.is_disabled(timeout=600):
                    continue
                if required_test_id and str(
                    locator.get_attribute("data-testid") or ""
                ) != required_test_id:
                    continue
                visible_label = str(locator.inner_text(timeout=800) or "").strip()
                if not visible_label:
                    visible_label = str(locator.get_attribute("aria-label") or "").strip()
                normalized = _normalise_editor_text(visible_label)
                if normalized in expected:
                    return locator, expected[normalized]
            except Exception:
                continue
    return None, None


def _wait_for_substack_exact_button(
    page: Any,
    *,
    labels: Sequence[str],
    timeout_seconds: float,
    preferred_test_id: str | None = None,
    poll_interval_seconds: float = 0.25,
) -> tuple[Any | None, str | None]:
    deadline = time.monotonic() + max(0.0, float(timeout_seconds))
    while True:
        locator, label = _substack_exact_enabled_button(
            page,
            labels=labels,
            preferred_test_id=preferred_test_id,
        )
        if locator is not None:
            return locator, label
        if time.monotonic() >= deadline:
            return None, None
        time.sleep(max(0.05, float(poll_interval_seconds)))


def _complete_substack_publish_transition(
    page: Any,
    *,
    draft_id: str | None,
    expected_title: str,
    transition_timeout_seconds: float = 30.0,
    listing_timeout_seconds: float = 15.0,
    poll_interval_seconds: float = 0.25,
) -> dict[str, Any]:
    """Advance one composed draft through bounded create-publication UI states.

    The final publish CTA is the public-write boundary.  Each permitted control is clicked at
    most once.  A missing/late public URL remains ambiguous and retains the draft identity so the
    coordinator can perform its normal readback-only reconciliation; this helper never retries.
    """
    stages: list[dict[str, Any]] = []
    draft_id = str(draft_id or "").strip()
    if not draft_id.isdigit():
        stages.append({"stage": "DRAFT_ID_BINDING", "outcome": "NOT_BOUND"})
        return {
            "status": "BLOCKED_SUBSTACK_DRAFT_ID_NOT_BOUND_BEFORE_PUBLIC_WRITE",
            "draft_id": None,
            "definite_no_write": True,
            "public_write_attempted": False,
            "browser_write_performed": False,
            "transition_stages": stages,
        }
    observed_draft_id = _substack_draft_id(str(getattr(page, "url", "") or ""))
    if observed_draft_id != draft_id:
        stages.append(
            {
                "stage": "DRAFT_ID_BINDING",
                "outcome": "EDITOR_ID_MISMATCH",
            }
        )
        return {
            "status": "BLOCKED_SUBSTACK_EDITOR_DRAFT_ID_MISMATCH_BEFORE_PUBLIC_WRITE",
            "draft_id": draft_id,
            "definite_no_write": True,
            "public_write_attempted": False,
            "browser_write_performed": False,
            "transition_stages": stages,
        }

    continue_button, continue_label = _wait_for_substack_exact_button(
        page,
        labels=("Continue",),
        preferred_test_id="publish-button",
        timeout_seconds=min(8.0, transition_timeout_seconds),
        poll_interval_seconds=poll_interval_seconds,
    )
    if continue_button is None:
        stages.append({"stage": "EDITOR_CONTINUE", "outcome": "CONTROL_NOT_FOUND"})
        return {
            "status": "BLOCKED_SUBSTACK_CONTINUE_CONTROL_NOT_FOUND",
            "draft_id": draft_id,
            "definite_no_write": True,
            "public_write_attempted": False,
            "browser_write_performed": False,
            "transition_stages": stages,
        }
    try:
        continue_button.click(timeout=6000)
    except Exception as exc:
        stages.append(
            {
                "stage": "EDITOR_CONTINUE",
                "control_label": continue_label,
                "outcome": "CLICK_FAILED",
                "error_class": type(exc).__name__,
            }
        )
        return {
            "status": "BLOCKED_SUBSTACK_CONTINUE_CLICK_FAILED",
            "draft_id": draft_id,
            "definite_no_write": True,
            "public_write_attempted": False,
            "browser_write_performed": False,
            "transition_stages": stages,
        }
    stages.append(
        {
            "stage": "EDITOR_CONTINUE",
            "control_label": continue_label,
            "outcome": "CLICKED_ONCE",
        }
    )

    publish_button, publish_label = _wait_for_substack_exact_button(
        page,
        labels=("Send to everyone now", "Publish now", "Publish post now"),
        timeout_seconds=transition_timeout_seconds,
        poll_interval_seconds=poll_interval_seconds,
    )
    if publish_button is None:
        stages.append({"stage": "PUBLISH_SETTINGS", "outcome": "CONTROL_NOT_FOUND"})
        return {
            "status": "BLOCKED_SUBSTACK_PUBLISH_CONTROL_NOT_FOUND",
            "draft_id": draft_id,
            "definite_no_write": True,
            "public_write_attempted": False,
            "browser_write_performed": False,
            "transition_stages": stages,
        }
    try:
        publish_button.scroll_into_view_if_needed(timeout=3000)
        publish_button.click(timeout=3000, trial=True)
    except Exception as exc:
        stages.append(
            {
                "stage": "PUBLISH_SETTINGS",
                "control_label": publish_label,
                "outcome": "CONTROL_NOT_ACTIONABLE",
                "error_class": type(exc).__name__,
            }
        )
        return {
            "status": "BLOCKED_SUBSTACK_PUBLISH_CONTROL_NOT_ACTIONABLE",
            "draft_id": draft_id,
            "definite_no_write": True,
            "public_write_attempted": False,
            "browser_write_performed": False,
            "transition_stages": stages,
        }
    try:
        publish_button.click(timeout=6000)
    except Exception as exc:
        stages.append(
            {
                "stage": "PUBLISH_SETTINGS",
                "control_label": publish_label,
                "outcome": "CLICK_FAILED",
                "error_class": type(exc).__name__,
            }
        )
        return {
            "status": "UNKNOWN_SUBSTACK_PUBLISH_CONTROL_CLICK_FAILED",
            "draft_id": draft_id,
            "public_write_attempted": True,
            "browser_write_performed": True,
            "transition_stages": stages,
        }
    stages.append(
        {
            "stage": "PUBLISH_SETTINGS",
            "control_label": publish_label,
            "outcome": "PUBLIC_WRITE_CLICKED_ONCE",
        }
    )
    public_write_attempted = True

    confirmation_checked = False
    deadline = time.monotonic() + max(0.0, float(transition_timeout_seconds))
    while True:
        public_url = _extract_substack_public_url(page)
        if _is_public_substack_url(public_url):
            stages.append(
                {
                    "stage": "PUBLIC_URL",
                    "outcome": "OBSERVED_UNBOUND_TO_EXACT_DRAFT_ID",
                }
            )
            return {
                "status": "UNKNOWN_SUBSTACK_PUBLICATION_REQUIRES_DRAFT_ID_RECONCILIATION",
                "draft_id": draft_id,
                "public_write_attempted": public_write_attempted,
                "browser_write_performed": True,
                "transition_stages": stages,
            }
        if not confirmation_checked:
            confirmation_button, confirmation_label = _substack_exact_enabled_button(
                page,
                labels=("Publish without buttons",),
            )
            if confirmation_button is not None:
                confirmation_checked = True
                try:
                    confirmation_button.click(timeout=6000)
                except Exception as exc:
                    stages.append(
                        {
                            "stage": "OPTIONAL_CONFIRMATION",
                            "control_label": confirmation_label,
                            "outcome": "CLICK_FAILED",
                            "error_class": type(exc).__name__,
                        }
                    )
                    return {
                        "status": "UNKNOWN_SUBSTACK_CONFIRMATION_CLICK_FAILED",
                        "draft_id": draft_id,
                        "public_write_attempted": True,
                        "browser_write_performed": True,
                        "transition_stages": stages,
                    }
                stages.append(
                    {
                        "stage": "OPTIONAL_CONFIRMATION",
                        "control_label": confirmation_label,
                        "outcome": "PUBLIC_WRITE_CLICKED_ONCE",
                    }
                )
        if time.monotonic() >= deadline:
            break
        time.sleep(max(0.05, float(poll_interval_seconds)))

    # The public route is not always exposed on the post-send screen.  A published-listing title
    # is useful diagnostic evidence, but it cannot bind that row to this exact draft id: an older
    # article may have identical title/content.  Therefore listing-only recovery always remains
    # UNKNOWN and leaves the candidate URL unset.  The coordinator will reconcile the exact
    # draft-id editor state read-only before it can confirm any public object.
    try:
        page.goto(
            "https://capitalchronicle.substack.com/publish/posts/published",
            wait_until="domcontentloaded",
            timeout=45000,
        )
    except Exception as exc:
        stages.append(
            {
                "stage": "EXACT_PUBLISHED_LISTING",
                "outcome": "NAVIGATION_FAILED",
                "error_class": type(exc).__name__,
            }
        )
        return {
            "status": "UNKNOWN_SUBSTACK_PUBLICATION_REQUIRES_DRAFT_ID_RECONCILIATION",
            "draft_id": draft_id,
            "public_write_attempted": True,
            "browser_write_performed": True,
            "transition_stages": stages,
        }
    listing_deadline = time.monotonic() + max(0.0, float(listing_timeout_seconds))
    last_match_count = 0
    while True:
        matches = _substack_listing_matches(
            page,
            expected_title=expected_title,
            href_predicate=lambda href: _is_public_substack_url(
                _absolute_substack_url(href)
            ),
        )
        last_match_count = len(matches)
        if len(matches) > 1:
            stages.append(
                {
                    "stage": "EXACT_PUBLISHED_LISTING",
                    "outcome": "AMBIGUOUS",
                    "match_count": len(matches),
                }
            )
            return {
                "status": "UNKNOWN_SUBSTACK_PUBLICATION_REQUIRES_DRAFT_ID_RECONCILIATION",
                "draft_id": draft_id,
                "public_write_attempted": True,
                "browser_write_performed": True,
                "published_listing_match_count": len(matches),
                "transition_stages": stages,
            }
        if len(matches) == 1:
            stages.append(
                {
                    "stage": "EXACT_PUBLISHED_LISTING",
                    "outcome": "UNBOUND_UNIQUE_PUBLIC_MATCH",
                    "match_count": 1,
                }
            )
            return {
                "status": "UNKNOWN_SUBSTACK_PUBLICATION_REQUIRES_DRAFT_ID_RECONCILIATION",
                "draft_id": draft_id,
                "public_write_attempted": True,
                "browser_write_performed": True,
                "published_listing_match_count": 1,
                "transition_stages": stages,
            }
        if time.monotonic() >= listing_deadline:
            break
        time.sleep(max(0.05, float(poll_interval_seconds)))
    stages.append(
        {
            "stage": "EXACT_PUBLISHED_LISTING",
            "outcome": "NO_UNIQUE_PUBLIC_MATCH",
            "match_count": last_match_count,
        }
    )
    return {
        "status": "UNKNOWN_SUBSTACK_PUBLICATION_REQUIRES_DRAFT_ID_RECONCILIATION",
        "draft_id": draft_id,
        "public_write_attempted": True,
        "browser_write_performed": True,
        "published_listing_match_count": last_match_count,
        "transition_stages": stages,
    }


def _complete_substack_editor_publication_transition(
    page: Any,
    *,
    draft_id: str | None,
    expected_title: str,
    transition_timeout_seconds: float = 30.0,
    listing_timeout_seconds: float = 15.0,
    poll_interval_seconds: float = 0.25,
) -> dict[str, Any]:
    """Choose exact update/create mode once, then execute without cross-mode fallback."""
    update_button, update_label = _substack_exact_enabled_button(
        page,
        labels=("Update",),
    )
    if update_button is None:
        return {
            **_complete_substack_publish_transition(
                page,
                draft_id=draft_id,
                expected_title=expected_title,
                transition_timeout_seconds=transition_timeout_seconds,
                listing_timeout_seconds=listing_timeout_seconds,
                poll_interval_seconds=poll_interval_seconds,
            ),
            "publication_write_mode": "create_new_public_article",
        }

    normalized_draft_id = str(draft_id or "").strip()
    stages: list[dict[str, Any]] = []
    if not normalized_draft_id.isdigit():
        stages.append({"stage": "DRAFT_ID_BINDING", "outcome": "NOT_BOUND"})
        return {
            "status": "BLOCKED_SUBSTACK_DRAFT_ID_NOT_BOUND_BEFORE_PUBLIC_WRITE",
            "draft_id": None,
            "definite_no_write": True,
            "public_write_attempted": False,
            "browser_write_performed": False,
            "publication_write_mode": "update_existing_public_article",
            "transition_stages": stages,
        }
    observed_draft_id = _substack_draft_id(str(getattr(page, "url", "") or ""))
    if observed_draft_id != normalized_draft_id:
        stages.append(
            {
                "stage": "DRAFT_ID_BINDING",
                "outcome": "EDITOR_ID_MISMATCH",
            }
        )
        return {
            "status": "BLOCKED_SUBSTACK_EDITOR_DRAFT_ID_MISMATCH_BEFORE_PUBLIC_WRITE",
            "draft_id": normalized_draft_id,
            "definite_no_write": True,
            "public_write_attempted": False,
            "browser_write_performed": False,
            "publication_write_mode": "update_existing_public_article",
            "transition_stages": stages,
        }

    try:
        update_button.click(timeout=6000)
    except Exception as exc:
        stages.append(
            {
                "stage": "EDITOR_UPDATE",
                "control_label": update_label,
                "outcome": "CLICK_FAILED",
                "error_class": type(exc).__name__,
            }
        )
        return {
            "status": "UNKNOWN_SUBSTACK_UPDATE_CONTROL_CLICK_FAILED",
            "draft_id": normalized_draft_id,
            "public_write_attempted": True,
            "browser_write_performed": True,
            "publication_write_mode": "update_existing_public_article",
            "transition_stages": stages,
        }
    stages.append(
        {
            "stage": "EDITOR_UPDATE",
            "control_label": update_label,
            "outcome": "PUBLIC_WRITE_CLICKED_ONCE",
        }
    )

    confirmation_button, confirmation_label = _wait_for_substack_exact_button(
        page,
        labels=("Update post", "Update now", "Confirm update"),
        timeout_seconds=min(4.0, transition_timeout_seconds),
        poll_interval_seconds=poll_interval_seconds,
    )
    if confirmation_button is not None:
        try:
            confirmation_button.click(timeout=6000)
        except Exception as exc:
            stages.append(
                {
                    "stage": "OPTIONAL_UPDATE_CONFIRMATION",
                    "control_label": confirmation_label,
                    "outcome": "CLICK_FAILED",
                    "error_class": type(exc).__name__,
                }
            )
            return {
                "status": "UNKNOWN_SUBSTACK_UPDATE_CONFIRMATION_CLICK_FAILED",
                "draft_id": normalized_draft_id,
                "public_write_attempted": True,
                "browser_write_performed": True,
                "publication_write_mode": "update_existing_public_article",
                "transition_stages": stages,
            }
        stages.append(
            {
                "stage": "OPTIONAL_UPDATE_CONFIRMATION",
                "control_label": confirmation_label,
                "outcome": "PUBLIC_WRITE_CLICKED_ONCE",
            }
        )
    return {
        "status": "SUCCESS",
        "draft_id": normalized_draft_id,
        "public_write_attempted": True,
        "browser_write_performed": True,
        "publication_write_mode": "update_existing_public_article",
        "transition_stages": stages,
    }


def reconcile_substack_publication_by_draft_id_via_edge(
    *,
    cdp_port: int,
    draft_id: str,
    expected_title: str,
    expected_subtitle: str,
    expected_body_markdown: str,
    expected_image_assets: Sequence[Mapping[str, Any]],
    public_screenshot_path: str | Path | None = None,
) -> dict[str, Any]:
    """Resolve an ambiguous Substack attempt by exact public-or-draft identity, read-only.

    A unique public title is audited through the existing strict public readback.  Otherwise an
    exact draft id/title/body/media binding proves that the intended *public* write is absent and
    is safe to classify without retrying the adapter.  Private editor URLs and session material
    are never returned or persisted.
    """
    draft_id = str(draft_id or "").strip()
    expected_title = str(expected_title or "").strip()
    if not draft_id.isdigit() or not expected_title:
        return {
            "status": "BLOCKED_SUBSTACK_DRAFT_READBACK_IDENTITY_INVALID",
            "platform": "substack",
            "verified": False,
            "write_absent": False,
            "public_object_id": draft_id or None,
            "browser_write_performed": False,
        }
    with canonical_edge_page(cdp_port) as page:
        # Bind the exact post/draft object before consulting any title-only listing.  Otherwise
        # an older public article with identical title/body could be mistaken for this attempt
        # while the intended object still exists as a draft.
        page.goto(
            f"https://capitalchronicle.substack.com/publish/post/{draft_id}"
            "?back=%2Fpublish%2Fposts%2Fdrafts",
            wait_until="domcontentloaded",
            timeout=45000,
        )
        expected_subtitle = str(expected_subtitle or "").strip()
        expected_body_anchor = ""
        for kind, value in _split_substack_body(expected_body_markdown):
            if kind != "text":
                continue
            text_only = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
            for paragraph in re.split(r"\n\s*\n", text_only):
                normalized = _normalise_editor_text(paragraph)
                words = normalized.split()
                if len(words) >= 8:
                    expected_body_anchor = " ".join(words[: min(12, len(words))])
                    break
            if expected_body_anchor:
                break

        # Substack mounts visible editor controls before the draft itself is hydrated.  Poll
        # bounded exact bindings instead of interpreting the transient blank controls as a
        # mismatch.  This loop remains strictly read-only.
        title_input = None
        subtitle_input = None
        editor = None
        actual_title = ""
        actual_subtitle = ""
        editor_text = ""
        editor_image_count = 0
        editor_media_rows: list[dict[str, Any]] = []
        exact_editor_state = ""
        exact_editor_route_verified = False
        deadline = time.monotonic() + 15.0
        while True:
            title_input, _ = _first_visible(
                page, ("#post-title", "input[name='title']", "input[placeholder*='Title']")
            )
            subtitle_input, _ = _first_visible(
                page,
                (
                    "textarea[placeholder*='subtitle']",
                    "textarea[placeholder*='Subtitle']",
                    "#post-subtitle",
                ),
            )
            editor, _ = _first_visible(
                page, ("div.ProseMirror", ".ProseMirror", "div[contenteditable='true']")
            )
            if title_input is not None and editor is not None:
                actual_title = str(title_input.input_value(timeout=3000) or "").strip()
                actual_subtitle = (
                    str(subtitle_input.input_value(timeout=3000) or "").strip()
                    if subtitle_input is not None
                    else ""
                )
                editor_text = _normalise_editor_text(
                    editor.inner_text(timeout=5000) or ""
                )
                editor_image_count = _editor_image_count(page)
                try:
                    editor_path = urllib.parse.urlsplit(str(page.url or "")).path.rstrip("/")
                except (TypeError, ValueError):
                    editor_path = ""
                exact_editor_route_verified = editor_path == f"/publish/post/{draft_id}"
                identity_binding = bool(
                    exact_editor_route_verified
                    and actual_title == expected_title
                    and (not expected_subtitle or actual_subtitle == expected_subtitle)
                )
                if identity_binding:
                    update_button, _ = _substack_exact_enabled_button(
                        page, labels=("Update",)
                    )
                    continue_button, _ = _substack_exact_enabled_button(
                        page,
                        labels=("Continue",),
                        preferred_test_id="publish-button",
                    )
                    if update_button is not None and continue_button is None:
                        exact_editor_state = "PUBLISHED"
                        break
                    if continue_button is not None and update_button is None:
                        exact_editor_state = "DRAFT"
                        break
                    if update_button is not None and continue_button is not None:
                        exact_editor_state = "AMBIGUOUS"
                        break
            if time.monotonic() >= deadline:
                break
            time.sleep(0.5)
        if title_input is None or editor is None:
            return {
                "status": "READBACK_UNAVAILABLE",
                "platform": "substack",
                "verified": False,
                "write_absent": False,
                "public_object_id": draft_id,
                "browser_write_performed": False,
            }
        subtitle_binding_verified = bool(
            not expected_subtitle or actual_subtitle == expected_subtitle
        )
        body_anchor_verified = bool(
            expected_body_anchor and expected_body_anchor in editor_text
        )
        editor_media_rows = _editor_image_identity_rows(page)
        editor_image_count = len(editor_media_rows)
        resume_media_contract = _substack_resume_media_contract(
            expected_image_assets=expected_image_assets,
            observed_image_rows=editor_media_rows,
        )
        editor_media_contract = _exact_substack_article_media_contract(
            expected_image_assets=expected_image_assets,
            observed_image_rows=editor_media_rows,
        )
        media_count_verified = bool(
            editor_media_contract["article_media_manifest_exact_match"]
        )
        exact_draft_bound = bool(
            exact_editor_route_verified
            and actual_title == expected_title
            and body_anchor_verified
            and resume_media_contract["resume_media_safe"]
        )
        partial_draft_bound = bool(
            exact_editor_route_verified
            and actual_title == expected_title
            and exact_editor_state == "DRAFT"
        )
        binding_detail = {
            "exact_editor_route_verified": exact_editor_route_verified,
            "title_binding_verified": actual_title == expected_title,
            "subtitle_binding_verified": subtitle_binding_verified,
            "body_anchor_verified": body_anchor_verified,
            "media_count_verified": media_count_verified,
            "observed_editor_image_count": editor_image_count,
            "expected_image_count": len(expected_image_assets),
            "exact_editor_state": exact_editor_state or None,
            "resume_media_contract": resume_media_contract,
            "editor_media_contract": editor_media_contract,
        }
        if partial_draft_bound and not resume_media_contract["resume_media_safe"]:
            return {
                "status": "SUBSTACK_DRAFT_UNEXPECTED_MEDIA_BLOCKED",
                "platform": "substack",
                "verified": False,
                "write_absent": True,
                "retry_safe": False,
                "public_object_id": draft_id,
                "publication_state": "draft",
                "draft_binding_verified": False,
                **binding_detail,
                "browser_write_performed": False,
                "automatic_media_cleanup_performed": False,
            }
        if partial_draft_bound and not exact_draft_bound:
            return {
                "status": "SUBSTACK_PARTIAL_DRAFT_CONFIRMED_NOT_PUBLIC",
                "platform": "substack",
                "verified": False,
                "write_absent": True,
                "public_object_id": draft_id,
                "publication_state": "draft",
                "draft_binding_verified": True,
                "draft_media_incomplete": True,
                **binding_detail,
                "browser_write_performed": False,
            }
        if exact_editor_state != "DRAFT":
            page.goto(
                "https://capitalchronicle.substack.com/publish/posts/published",
                wait_until="domcontentloaded",
                timeout=45000,
            )
            time.sleep(3)
            published_identity_matches = _substack_listing_matches(
                page,
                expected_title=expected_title,
                href_predicate=lambda href: (
                    urllib.parse.urlparse(_absolute_substack_url(href)).path.rstrip("/")
                    == f"/publish/posts/detail/{draft_id}"
                    or _is_public_substack_url(_absolute_substack_url(href))
                ),
            )
            if len(published_identity_matches) == 1:
                matched_url = _absolute_substack_url(
                    published_identity_matches[0]["href"]
                )
                public_url = (
                    matched_url
                    if _is_public_substack_url(matched_url)
                    else None
                )
                if public_url is None:
                    page.goto(
                        matched_url,
                        wait_until="domcontentloaded",
                        timeout=45000,
                    )
                    time.sleep(2)
                    public_url = _public_substack_url_from_view_post(page)
                if public_url:
                    readback = _audit_public_substack_article(
                        page,
                        public_url,
                        public_screenshot_path,
                        expected_title=expected_title,
                        expected_subtitle=expected_subtitle,
                        expected_body_markdown=expected_body_markdown,
                        expected_image_assets=expected_image_assets,
                    )
                    verified = bool(
                        readback.get("strict_content_visual_readback_verified")
                    )
                    return {
                        "status": _strict_substack_readback_status(readback),
                        "platform": "substack",
                        "verified": verified,
                        "write_absent": False,
                        "public_object_id": draft_id,
                        "public_url": public_url,
                        "readback": readback,
                        **binding_detail,
                        "browser_write_performed": False,
                    }
        if not exact_draft_bound:
            return {
                "status": "SUBSTACK_DRAFT_BINDING_MISMATCH",
                "platform": "substack",
                "verified": False,
                "write_absent": False,
                "public_object_id": draft_id,
                "draft_binding_verified": False,
                **binding_detail,
                "browser_write_performed": False,
            }
        if exact_editor_state == "DRAFT":
            return {
                "status": "SUBSTACK_DRAFT_CONFIRMED_NOT_PUBLIC",
                "platform": "substack",
                "verified": False,
                "write_absent": True,
                "public_object_id": draft_id,
                "publication_state": "draft",
                "draft_binding_verified": True,
                **binding_detail,
                "browser_write_performed": False,
            }
        if exact_editor_state != "PUBLISHED":
            return {
                "status": "READBACK_UNAVAILABLE",
                "platform": "substack",
                "verified": False,
                "write_absent": False,
                "public_object_id": draft_id,
                "draft_binding_verified": True,
                **binding_detail,
                "browser_write_performed": False,
            }

        # The exact object is proven published by its editor state.  The title listing is now
        # used only to recover its public URL; strict public content readback remains mandatory.
        page.goto(
            "https://capitalchronicle.substack.com/publish/posts/published",
            wait_until="domcontentloaded",
            timeout=45000,
        )
        time.sleep(3)
        published_matches = _substack_listing_matches(
            page,
            expected_title=expected_title,
            href_predicate=lambda href: _is_public_substack_url(
                _absolute_substack_url(href)
            ),
        )
        if len(published_matches) != 1:
            return {
                "status": (
                    "AMBIGUOUS_SUBSTACK_PUBLIC_TITLE_MATCH"
                    if len(published_matches) > 1
                    else "READBACK_UNAVAILABLE"
                ),
                "platform": "substack",
                "verified": False,
                "write_absent": False,
                "public_object_id": draft_id,
                "published_listing_match_count": len(published_matches),
                **binding_detail,
                "browser_write_performed": False,
            }
        public_url = _absolute_substack_url(published_matches[0]["href"])
        if not _is_public_substack_url(public_url):
            return {
                "status": "AMBIGUOUS_SUBSTACK_PUBLISHED_LISTING_MATCH",
                "platform": "substack",
                "verified": False,
                "write_absent": False,
                "public_object_id": draft_id,
                **binding_detail,
                "browser_write_performed": False,
            }
        public_url = str(public_url).split("?", 1)[0].split("#", 1)[0]
        readback = _audit_public_substack_article(
            page,
            public_url,
            public_screenshot_path,
            expected_title=expected_title,
            expected_subtitle=expected_subtitle,
            expected_body_markdown=expected_body_markdown,
            expected_image_assets=expected_image_assets,
        )
        verified = bool(readback.get("strict_content_visual_readback_verified"))
        return {
            "status": _strict_substack_readback_status(readback),
            "platform": "substack",
            "verified": verified,
            "write_absent": False,
            "public_object_id": draft_id,
            "public_url": public_url,
            "readback": readback,
            **binding_detail,
            "browser_write_performed": False,
        }


def capture_public_destination_screenshot_via_edge(
    *,
    cdp_port: int,
    public_url: str,
    output_path: str | Path,
    expected_text: str | None = None,
) -> dict[str, Any]:
    """Capture a public destination read-only through the canonical Edge profile."""
    parsed = urllib.parse.urlparse(public_url)
    if parsed.scheme != "https" or _PRIVATE_SUBSTACK_PATH_MARKER in parsed.path:
        return {"status": "BLOCKED_INVALID_PUBLIC_SCREENSHOT_URL", "public_url": public_url}
    navigation_url = public_url
    with canonical_edge_page(cdp_port) as page:
        try:
            page.goto(navigation_url, wait_until="domcontentloaded", timeout=45000)
        except Exception:
            if parsed.netloc.casefold() != "t.me":
                raise
            navigation_url = urllib.parse.urlunparse(parsed._replace(netloc="telegram.me"))
            page.goto(navigation_url, wait_until="domcontentloaded", timeout=45000)
        time.sleep(5)
        try:
            visible_text = _normalised_visible_text(page.locator("body").inner_text(timeout=5000))
        except Exception:
            visible_text = ""
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(target), full_page=False)
    expected_visible = True if not expected_text else _normalised_visible_text(expected_text).casefold() in visible_text.casefold()
    return {
        "status": "SUCCESS" if target.is_file() and target.stat().st_size > 0 else "FAILED_PUBLIC_SCREENSHOT_CAPTURE",
        "public_url": public_url,
        "navigation_url": navigation_url,
        "public_screenshot_path": str(target),
        "page_domain": parsed.netloc,
        "expected_text_visible": expected_visible,
        "browser_write_performed": False,
    }


def publish_substack_article_via_edge(
    *,
    cdp_port: int,
    title: str,
    subtitle: str,
    body_markdown: str,
    image_assets: Sequence[Mapping[str, Any]],
    public_screenshot_path: str | Path | None = None,
    existing_draft_id: str | None = None,
    existing_public_url: str | None = None,
    publication_mode: str = "publish",
) -> dict[str, Any]:
    """Publish one canonical article with source-backed images embedded in order."""
    if publication_mode not in {"publish", "draft_qa"}:
        return {"status": "BLOCKED_SUBSTACK_PUBLICATION_MODE_INVALID", "platform": "substack"}
    assets = {str(item.get("asset_id") or ""): dict(item) for item in image_assets}
    expected_ids = _VISUAL_MARKER_RE.findall(body_markdown)
    if len(expected_ids) != len(set(expected_ids)) or list(assets) != expected_ids:
        return {"status": "BLOCKED_INVALID_SUBSTACK_MEDIA_MANIFEST", "platform": "substack"}
    for asset_id in expected_ids:
        if not Path(str(assets[asset_id].get("local_path") or assets[asset_id].get("path") or "")).exists():
            return {"status": "BLOCKED_SUBSTACK_LOCAL_MEDIA_MISSING", "platform": "substack", "asset_id": asset_id}
    with canonical_edge_page(cdp_port) as page:
        editor_url = "https://capitalchronicle.substack.com/publish/post"
        if existing_draft_id:
            editor_url = f"{editor_url}/{existing_draft_id}"
        page.goto(editor_url, wait_until="domcontentloaded", timeout=45000)
        time.sleep(3)
        title_input, title_selector = _first_visible(page, ("#post-title", "input[name='title']", "input[placeholder*='Title']"))
        editor, editor_selector = _first_visible(page, ("div.ProseMirror", ".ProseMirror", "div[contenteditable='true']"))
        if not title_input or not editor:
            return {"status": "BLOCKED_SUBSTACK_EDITOR_NOT_READY", "platform": "substack", "title_selector": title_selector, "editor_selector": editor_selector}
        existing_media_rows: list[dict[str, Any]] = []
        if existing_draft_id:
            existing_title = title_input.input_value(timeout=3000).strip()
            if existing_title and existing_title != title:
                return {"status": "BLOCKED_SUBSTACK_RESUME_DRAFT_TITLE_MISMATCH", "platform": "substack", "draft_id": existing_draft_id}
            existing_media_rows = _editor_image_identity_rows(page)
            resume_media_contract = _substack_resume_media_contract(
                expected_image_assets=image_assets,
                observed_image_rows=existing_media_rows,
            )
            if not resume_media_contract["resume_media_safe"]:
                return {
                    "status": "BLOCKED_SUBSTACK_RESUME_UNEXPECTED_MEDIA",
                    "platform": "substack",
                    "draft_id": existing_draft_id,
                    "editor_body_image_count": len(existing_media_rows),
                    "resume_media_contract": resume_media_contract,
                    "public_write_attempted": False,
                    "public_transition_performed": False,
                    "browser_write_performed": False,
                    "automatic_media_cleanup_performed": False,
                }
            if not existing_title:
                title_input.fill(title)
        else:
            title_input.fill(title)
        subtitle_input, _subtitle_selector = _first_visible(page, ("textarea[placeholder*='subtitle']", "textarea[placeholder*='Subtitle']", "#post-subtitle"))
        if subtitle and subtitle_input:
            subtitle_input.fill(subtitle)

        segments = _split_substack_body(body_markdown)
        upload_rows: list[dict[str, Any]] = []
        first_text = True
        resume_segment_index = 0
        resume_tail_after_media = False
        if existing_draft_id:
            existing_text = _normalise_editor_text(editor.inner_text(timeout=3000) or "")
            expected_intro = _normalise_editor_text(segments[0][1] if segments and segments[0][0] == "text" else "")
            existing_image_count = len(existing_media_rows)
            expected_captions = [
                _normalise_editor_text(str(assets[asset_id].get("caption") or ""))
                for asset_id in expected_ids
            ]
            if (
                existing_image_count == len(expected_ids)
                and expected_intro
                and expected_intro[:500] in existing_text
                and all(caption and caption in existing_text for caption in expected_captions)
            ):
                # Exact recovery of a fully composed draft that stopped at a
                # readback gate. Never retype the body or reupload its media.
                resume_segment_index = len(segments)
                first_text = False
            elif existing_image_count == len(expected_ids):
                text_segment_indexes = [index for index, row in enumerate(segments) if row[0] == "text"]
                trailing_index = text_segment_indexes[-1] if text_segment_indexes else -1
                preceding_text_matches = all(
                    _normalise_editor_text(segments[index][1])[:300] in existing_text
                    for index in text_segment_indexes[:-1]
                    if _normalise_editor_text(segments[index][1])
                )
                trailing_text = _normalise_editor_text(segments[trailing_index][1]) if trailing_index >= 0 else ""
                trailing_absent = bool(trailing_text) and trailing_text[:80] not in existing_text
                if expected_intro and expected_intro[:500] in existing_text and preceding_text_matches and trailing_absent:
                    # A prior bounded upload may have stopped after the final
                    # image but before the last text segment. Append only that
                    # proven-missing tail; successful media remains untouched.
                    resume_segment_index = trailing_index
                    first_text = False
                    resume_tail_after_media = True
                else:
                    return {
                        "status": "BLOCKED_SUBSTACK_RESUME_DRAFT_BODY_UNRECOGNIZED",
                        "platform": "substack",
                        "draft_id": existing_draft_id,
                        "editor_body_image_count": existing_image_count,
                    }
            elif existing_image_count == 0 and expected_intro and expected_intro[:500] in existing_text:
                resume_segment_index = 1
                first_text = False
            elif (
                0 < existing_image_count < len(expected_ids)
                and expected_intro
                and expected_intro[:500] in existing_text
            ):
                # The publisher uploads markers strictly in order and stops at the first failed
                # upload.  Therefore a bound draft containing N meaningful images is the exact
                # sequential prefix of N requested markers. Preserve those successful uploads,
                # add any reader-visible captions that the interrupted attempt did not persist,
                # and continue only after that prefix.
                resume_segment_index = _segment_index_after_visual_prefix(
                    segments, existing_image_count
                )
                first_text = False
                for asset_id in expected_ids[:existing_image_count]:
                    caption = str(assets[asset_id].get("caption") or "").strip()
                    if caption and _normalise_editor_text(caption) not in existing_text:
                        _append_editor_tail_after_media(page, editor, caption)
                        _append_editor_text(page, editor, "\n\n")
                        existing_text = _normalise_editor_text(
                            editor.inner_text(timeout=3000) or ""
                        )
            elif existing_text:
                return {
                    "status": "BLOCKED_SUBSTACK_RESUME_DRAFT_BODY_UNRECOGNIZED",
                    "platform": "substack",
                    "draft_id": existing_draft_id,
                    "editor_body_image_count": _editor_image_count(page),
                }
        for kind, value in segments[resume_segment_index:]:
            if kind == "text":
                if resume_tail_after_media:
                    _append_editor_tail_after_media(page, editor, value)
                    resume_tail_after_media = False
                else:
                    _append_editor_text(page, editor, value, clear=first_text)
                first_text = False
                continue
            asset = assets[value]
            local_path = str(asset.get("local_path") or asset.get("path"))
            upload = _upload_substack_image(
                page,
                editor,
                local_path,
                str(asset.get("alt_text") or ""),
                asset_id=value,
                expected_image_index=expected_ids.index(value),
            )
            upload_rows.append(dict(upload))
            if upload["status"] != "uploaded":
                return {
                    "status": "FAILED_SUBSTACK_IMAGE_UPLOAD",
                    "platform": "substack",
                    "draft_id": _substack_draft_id(page.url),
                    "editor_body_image_count": _editor_image_count(page),
                    "upload_rows": upload_rows,
                }
            caption = str(asset.get("caption") or "").strip()
            if caption:
                _append_editor_tail_after_media(page, editor, caption)
            _append_editor_text(page, editor, "\n\n")

        editor_media_rows = _editor_image_identity_rows(page)
        editor_image_count = len(editor_media_rows)
        editor_media_contract = _exact_substack_article_media_contract(
            expected_image_assets=image_assets,
            observed_image_rows=editor_media_rows,
        )
        if not editor_media_contract["article_media_manifest_exact_match"]:
            return {
                "status": "BLOCKED_SUBSTACK_PREPUBLICATION_MEDIA_MISMATCH",
                "platform": "substack",
                "draft_id": _substack_draft_id(page.url),
                "editor_body_image_count": editor_image_count,
                "editor_media_contract": editor_media_contract,
                "public_write_attempted": False,
                "public_transition_performed": False,
                "automatic_media_cleanup_performed": False,
                "upload_rows": upload_rows,
            }
        if editor_image_count != len(expected_ids):
            return {"status": "FAILED_SUBSTACK_EDITOR_IMAGE_COUNT", "platform": "substack", "draft_id": _substack_draft_id(page.url), "editor_body_image_count": editor_image_count, "upload_rows": upload_rows}
        editor_text = _normalise_editor_text(editor.inner_text(timeout=5000) or "")
        missing_captions = [
            asset_id
            for asset_id in expected_ids
            if _normalise_editor_text(str(assets[asset_id].get("caption") or "")) not in editor_text
        ]
        if missing_captions:
            return {
                "status": "FAILED_SUBSTACK_CAPTION_READBACK",
                "platform": "substack",
                "draft_id": _substack_draft_id(page.url),
                "editor_body_image_count": editor_image_count,
                "missing_caption_asset_ids": missing_captions,
                "upload_rows": upload_rows,
            }
        native_readback = _editor_native_semantics_readback(editor, body_markdown)
        if not native_readback["native_semantics_verified"]:
            return {
                "status": "FAILED_SUBSTACK_NATIVE_RICH_TEXT_READBACK",
                "platform": "substack",
                "draft_id": _substack_draft_id(page.url),
                "editor_body_image_count": editor_image_count,
                "native_rich_text_readback": native_readback,
                "upload_rows": upload_rows,
            }
        if publication_mode == "draft_qa":
            draft_id = _substack_draft_id(page.url)
            if not draft_id or not _substack_saved(page):
                return {
                    "status": "FAILED_SUBSTACK_DRAFT_QA_SAVE_READBACK",
                    "platform": "substack",
                    "draft_id": draft_id,
                    "editor_body_image_count": editor_image_count,
                    "native_rich_text_readback": native_readback,
                    "public_write_attempted": False,
                    "public_transition_performed": False,
                    "upload_rows": upload_rows,
                }
            return {
                "status": "SUCCESS_DRAFT_QA",
                "platform": "substack",
                "action": "compose_draft_qa",
                "draft_id": draft_id,
                "editor_body_image_count": editor_image_count,
                "in_body_visual_asset_ids": expected_ids,
                "editor_media_contract": editor_media_contract,
                "native_rich_text_readback": native_readback,
                "public_write_attempted": False,
                "public_transition_performed": False,
                "publication_state": "draft_nonpublic",
                "upload_rows": upload_rows,
            }
        time.sleep(3)
        draft_id = _substack_draft_id(page.url)
        publish_transition = _complete_substack_editor_publication_transition(
            page,
            draft_id=draft_id,
            expected_title=title,
        )
        update_mode = (
            publish_transition.get("publication_write_mode")
            == "update_existing_public_article"
        )
        if publish_transition.get("status") != "SUCCESS":
            return {
                **publish_transition,
                "platform": "substack",
                "draft_id": draft_id,
                "editor_body_image_count": editor_image_count,
                "upload_rows": upload_rows,
            }
        time.sleep(7)
        public_url = (
            str(existing_public_url)
            if update_mode and _is_public_substack_url(str(existing_public_url or ""))
            else str((publish_transition or {}).get("public_url") or "")
        )
        if update_mode and not public_url:
            try:
                page.goto(
                    "https://capitalchronicle.substack.com/publish/posts/published",
                    wait_until="domcontentloaded",
                    timeout=45000,
                )
                time.sleep(3)
                published_matches = _substack_listing_matches(
                    page,
                    expected_title=title,
                    href_predicate=lambda href: _is_public_substack_url(
                        _absolute_substack_url(href)
                    ),
                )
                if len(published_matches) == 1:
                    public_url = _absolute_substack_url(
                        published_matches[0]["href"]
                    )
            except Exception:
                public_url = None
        if not _is_public_substack_url(public_url):
            return {"status": "FAILED_SUBSTACK_PUBLIC_URL_READBACK", "platform": "substack", "draft_id": draft_id, "editor_body_image_count": editor_image_count, "upload_rows": upload_rows, "publish_transition": publish_transition}
        readback = _audit_public_substack_article(
            page,
            public_url,
            public_screenshot_path,
            expected_title=title,
            expected_subtitle=subtitle,
            expected_body_markdown=body_markdown,
            expected_image_assets=image_assets,
        )
        expected_image_count = len(expected_ids)
        if (
            readback["public_image_count"] != expected_image_count
            or not readback["article_media_manifest_exact_match"]
            or not readback["visual_spread_through_public_body"]
        ):
            return {"status": "FAILED_SUBSTACK_PUBLIC_VISUAL_READBACK", "platform": "substack", "draft_id": draft_id, "editor_body_image_count": editor_image_count, "upload_rows": upload_rows, "public_url": public_url, "readback": readback, "publish_transition": publish_transition}
        if (
            readback["public_image_alt_or_caption_count"] < expected_image_count
            or not readback["content_readback_verified"]
        ):
            return {"status": "FAILED_SUBSTACK_PUBLIC_CONTENT_READBACK", "platform": "substack", "draft_id": draft_id, "editor_body_image_count": editor_image_count, "upload_rows": upload_rows, "public_url": public_url, "readback": readback, "publish_transition": publish_transition}
        return {
            "status": "SUCCESS",
            "platform": "substack",
            "action": "publish",
            "publication_write_mode": "update_existing_public_article" if update_mode else "create_new_public_article",
            "draft_id": draft_id,
            "public_url": public_url,
            "editor_body_image_count": editor_image_count,
            "in_body_visual_asset_ids": expected_ids,
            "editor_media_contract": editor_media_contract,
            "upload_rows": upload_rows,
            "native_rich_text_readback": native_readback,
            "readback": readback,
            "publish_transition": publish_transition,
        }


_EXACT_SUBSTACK_MEDIA_REPAIR_SCOPE = (
    "EXACT_EXISTING_SUBSTACK_UNEXPECTED_MEDIA_REMOVAL_V1"
)


def _expected_substack_editor_prose(
    body_markdown: str, expected_image_assets: Sequence[Mapping[str, Any]]
) -> str:
    assets = {
        str(row.get("asset_id") or ""): dict(row) for row in expected_image_assets
    }
    parts: list[str] = []
    for kind, value in _split_substack_body(body_markdown):
        if kind == "text":
            parts.append(rich_text_to_plain_text(markdown_to_rich_text(value)))
        else:
            caption = str((assets.get(value) or {}).get("caption") or "")
            if caption:
                parts.append(caption)
    return _normalise_editor_text("\n\n".join(parts))


def _remove_exact_substack_editor_image_node(page: Any, image: Any) -> None:
    image.evaluate(
        """element => {
            const target = element.closest('figure') ||
                element.closest('[data-node-type="image"]') || element;
            target.scrollIntoView({block: 'center'});
            const selection = window.getSelection();
            const range = document.createRange();
            range.selectNode(target);
            selection.removeAllRanges();
            selection.addRange(range);
        }"""
    )
    page.keyboard.press("Backspace")


def _repair_exact_unexpected_substack_media_via_edge(
    *,
    cdp_port: int,
    draft_id: str,
    public_url: str,
    expected_title: str,
    expected_subtitle: str,
    expected_body_markdown: str,
    expected_body_sha256: str,
    expected_image_assets: Sequence[Mapping[str, Any]],
    unexpected_media_identities: Sequence[Mapping[str, Any]],
    repair_authorization: Mapping[str, Any],
    public_screenshot_path: str | Path | None = None,
) -> dict[str, Any]:
    """Repair only exact unexpected media on one explicitly authorized public object.

    This private helper has no newsroom, scheduler, coordinator, facade, or CLI caller.  It
    cannot alter title, subtitle, or prose and never infers cleanup authority from publication
    mode.  A later exact owner task must construct every non-secret authorization binding.
    """
    draft_id = str(draft_id or "").strip()
    public_url = str(public_url or "").split("?", 1)[0].split("#", 1)[0]
    expected_title = str(expected_title or "")
    expected_subtitle = str(expected_subtitle or "")
    expected_body_sha256 = str(expected_body_sha256 or "").casefold()
    expected_rows, expected_blockers = _expected_article_media_identity_rows(
        expected_image_assets
    )
    expected_manifest = [
        {"asset_id": row["asset_id"], "sha256": row["sha256"]}
        for row in expected_rows
    ]
    expected_manifest_sha256 = _canonical_json_sha256(expected_manifest)
    unexpected_manifest = [
        {
            "src": str(row.get("src") or "") or None,
            "original_url": str(row.get("original_url") or "") or None,
            "sha256": str(row.get("sha256") or "").casefold() or None,
        }
        for row in unexpected_media_identities
    ]
    unexpected_manifest_sha256 = _canonical_json_sha256(unexpected_manifest)
    authorization = dict(repair_authorization or {})
    offline_blockers = list(expected_blockers)
    if not draft_id.isdigit() or not _is_public_substack_url(public_url):
        offline_blockers.append("exact_substack_object_identity_invalid")
    if expected_body_sha256 != _sha256(expected_body_markdown):
        offline_blockers.append("expected_body_sha256_mismatch")
    if not unexpected_manifest or any(
        not re.fullmatch(r"[0-9a-f]{64}", str(row.get("sha256") or ""))
        or not str(row.get("original_url") or "").startswith("https://")
        for row in unexpected_manifest
    ):
        offline_blockers.append("unexpected_media_identity_incomplete")
    required_authorization = {
        "scope": _EXACT_SUBSTACK_MEDIA_REPAIR_SCOPE,
        "destination": "substack",
        "draft_id": draft_id,
        "public_url": public_url,
        "expected_title_sha256": _sha256(expected_title),
        "expected_subtitle_sha256": _sha256(expected_subtitle),
        "expected_body_sha256": expected_body_sha256,
        "expected_article_media_manifest_sha256": expected_manifest_sha256,
        "unexpected_media_manifest_sha256": unexpected_manifest_sha256,
    }
    if any(
        str(authorization.get(key) or "") != str(value)
        for key, value in required_authorization.items()
    ):
        offline_blockers.append("exact_repair_authorization_binding_mismatch")
    if offline_blockers:
        return {
            "status": "BLOCKED_SUBSTACK_EXACT_MEDIA_REPAIR_AUTHORIZATION",
            "platform": "substack",
            "draft_id": draft_id or None,
            "public_url": public_url or None,
            "blockers": list(dict.fromkeys(offline_blockers)),
            "browser_write_performed": False,
            "public_write_attempted": False,
        }

    with canonical_edge_page(cdp_port) as page:
        before_public = _audit_public_substack_article(
            page,
            public_url,
            None,
            expected_title=expected_title,
            expected_subtitle=expected_subtitle,
            expected_body_markdown=expected_body_markdown,
            expected_image_assets=expected_image_assets,
        )
        if (
            not before_public.get("text_content_readback_verified")
            or before_public.get("article_media_manifest_exact_match")
            or before_public.get("missing_article_media_sha256")
            or before_public.get("unresolved_article_media_identity_count")
            or before_public.get("unexpected_article_media_identities")
            != unexpected_manifest
        ):
            return {
                "status": "BLOCKED_SUBSTACK_EXACT_MEDIA_REPAIR_PUBLIC_BINDING",
                "platform": "substack",
                "draft_id": draft_id,
                "public_url": public_url,
                "browser_write_performed": False,
                "public_write_attempted": False,
            }

        page.goto(
            f"https://capitalchronicle.substack.com/publish/post/{draft_id}",
            wait_until="domcontentloaded",
            timeout=45000,
        )
        time.sleep(3)
        title_input, _ = _first_visible(
            page, ("#post-title", "input[name='title']", "input[placeholder*='Title']")
        )
        subtitle_input, _ = _first_visible(
            page,
            (
                "textarea[placeholder*='subtitle']",
                "textarea[placeholder*='Subtitle']",
                "#post-subtitle",
            ),
        )
        editor, _ = _first_visible(
            page, ("div.ProseMirror", ".ProseMirror", "div[contenteditable='true']")
        )
        actual_title = (
            str(title_input.input_value(timeout=3000) or "") if title_input else ""
        )
        actual_subtitle = (
            str(subtitle_input.input_value(timeout=3000) or "")
            if subtitle_input
            else ""
        )
        expected_prose = _expected_substack_editor_prose(
            expected_body_markdown, expected_image_assets
        )
        prose_before = (
            _normalise_editor_text(editor.inner_text(timeout=5000) or "")
            if editor
            else ""
        )
        editor_path = urllib.parse.urlsplit(str(page.url or "")).path.rstrip("/")
        update_button, _ = _substack_exact_enabled_button(page, labels=("Update",))
        continue_button, _ = _substack_exact_enabled_button(
            page, labels=("Continue",), preferred_test_id="publish-button"
        )
        if (
            not title_input
            or not editor
            or editor_path != f"/publish/post/{draft_id}"
            or actual_title != expected_title
            or actual_subtitle != expected_subtitle
            or prose_before != expected_prose
            or update_button is None
            or continue_button is not None
        ):
            return {
                "status": "BLOCKED_SUBSTACK_EXACT_MEDIA_REPAIR_EDITOR_BINDING",
                "platform": "substack",
                "draft_id": draft_id,
                "public_url": public_url,
                "browser_write_performed": False,
                "public_write_attempted": False,
            }

        editor_rows_before = _editor_image_identity_rows(page)
        editor_contract_before = _exact_substack_article_media_contract(
            expected_image_assets=expected_image_assets,
            observed_image_rows=editor_rows_before,
        )
        if (
            editor_contract_before.get("missing_article_media_sha256")
            or editor_contract_before.get("unresolved_article_media_identity_count")
            or editor_contract_before.get("unexpected_article_media_identities")
            != unexpected_manifest
        ):
            return {
                "status": "BLOCKED_SUBSTACK_EXACT_MEDIA_REPAIR_EDITOR_MEDIA_BINDING",
                "platform": "substack",
                "draft_id": draft_id,
                "public_url": public_url,
                "browser_write_performed": False,
                "public_write_attempted": False,
            }

        expected_counter = Counter(
            str(row.get("sha256") or "") for row in expected_rows
        )
        removal_indexes: list[int] = []
        for index, row in enumerate(editor_rows_before):
            digest = str(row.get("sha256") or "")
            if digest and expected_counter[digest] > 0:
                expected_counter[digest] -= 1
            else:
                removal_indexes.append(index)
        editor_images = editor.locator("img")
        for index in reversed(removal_indexes):
            _remove_exact_substack_editor_image_node(page, editor_images.nth(index))
            time.sleep(0.8)

        deadline = time.monotonic() + 18
        while time.monotonic() < deadline and not _substack_saved(page):
            time.sleep(0.5)
        editor_rows_after = _editor_image_identity_rows(page)
        editor_contract_after = _exact_substack_article_media_contract(
            expected_image_assets=expected_image_assets,
            observed_image_rows=editor_rows_after,
        )
        title_after = str(title_input.input_value(timeout=3000) or "")
        subtitle_after = (
            str(subtitle_input.input_value(timeout=3000) or "")
            if subtitle_input
            else ""
        )
        prose_after = _normalise_editor_text(editor.inner_text(timeout=5000) or "")
        content_preserved = bool(
            title_after == actual_title == expected_title
            and subtitle_after == actual_subtitle == expected_subtitle
            and prose_after == prose_before == expected_prose
        )
        if (
            not content_preserved
            or not editor_contract_after["article_media_manifest_exact_match"]
            or not _substack_saved(page)
        ):
            return {
                "status": "FAILED_SUBSTACK_EXACT_MEDIA_REPAIR_DRAFT_READBACK",
                "platform": "substack",
                "draft_id": draft_id,
                "public_url": public_url,
                "title_subtitle_prose_preserved": content_preserved,
                "editor_media_contract": editor_contract_after,
                "browser_write_performed": True,
                "public_write_attempted": False,
            }

        transition = _complete_substack_editor_publication_transition(
            page, draft_id=draft_id, expected_title=expected_title
        )
        if (
            transition.get("status") != "SUCCESS"
            or transition.get("publication_write_mode")
            != "update_existing_public_article"
        ):
            return {
                **dict(transition),
                "status": "FAILED_SUBSTACK_EXACT_MEDIA_REPAIR_PUBLIC_TRANSITION",
                "platform": "substack",
                "draft_id": draft_id,
                "public_url": public_url,
                "title_subtitle_prose_preserved": content_preserved,
                "browser_write_performed": True,
            }
        time.sleep(7)
        after_public = _audit_public_substack_article(
            page,
            public_url,
            public_screenshot_path,
            expected_title=expected_title,
            expected_subtitle=expected_subtitle,
            expected_body_markdown=expected_body_markdown,
            expected_image_assets=expected_image_assets,
        )
        success = bool(after_public.get("strict_content_visual_readback_verified"))
        return {
            "status": "SUCCESS" if success else "FAILED_SUBSTACK_EXACT_MEDIA_REPAIR_PUBLIC_READBACK",
            "platform": "substack",
            "draft_id": draft_id,
            "public_url": public_url,
            "removed_unexpected_media_identities": unexpected_manifest,
            "removed_unexpected_media_count": len(removal_indexes),
            "title_subtitle_prose_preserved": content_preserved,
            "editor_media_contract": editor_contract_after,
            "readback": after_public,
            "publish_transition": transition,
            "browser_write_performed": True,
            "public_write_attempted": True,
        }


def repair_substack_duplicate_caption_fragment_via_edge(
    *,
    cdp_port: int,
    draft_id: str,
    expected_title: str,
    caption_prefix: str,
) -> dict[str, Any]:
    """Remove one proven short duplicate caption fragment from an exact draft."""
    if not str(draft_id).isdigit() or len(_normalise_editor_text(caption_prefix)) < 20:
        return {"status": "BLOCKED_SUBSTACK_CAPTION_REPAIR_IDENTITY_INVALID", "platform": "substack"}
    with canonical_edge_page(cdp_port) as page:
        page.goto(
            f"https://capitalchronicle.substack.com/publish/post/{draft_id}",
            wait_until="domcontentloaded",
            timeout=45000,
        )
        time.sleep(3)
        title_input, _ = _first_visible(page, ("#post-title", "input[name='title']", "input[placeholder*='Title']"))
        editor, _ = _first_visible(page, ("div.ProseMirror", ".ProseMirror", "div[contenteditable='true']"))
        if not title_input or not editor or title_input.input_value(timeout=3000).strip() != expected_title:
            return {"status": "BLOCKED_SUBSTACK_CAPTION_REPAIR_IDENTITY_MISMATCH", "platform": "substack", "draft_id": draft_id}
        expected = _normalise_editor_text(caption_prefix)
        matches: list[tuple[Any, str, str]] = []
        for node in editor.locator("p").all():
            try:
                visible = " ".join((node.inner_text(timeout=600) or "").split())
            except Exception:
                continue
            normalized = _normalise_editor_text(visible)
            if expected[:35] in normalized:
                matches.append((node, visible, normalized))
        if len(matches) == 1 and len(matches[0][1]) > 120:
            return {
                "status": "ALREADY_CLEAN_IDEMPOTENT",
                "platform": "substack",
                "draft_id": draft_id,
                "remaining_caption_node_count": 1,
                "browser_write_performed": False,
            }
        if len(matches) != 2:
            return {"status": "BLOCKED_SUBSTACK_CAPTION_REPAIR_AMBIGUOUS", "platform": "substack", "draft_id": draft_id, "matching_node_count": len(matches)}
        short = min(matches, key=lambda row: len(row[1]))
        long = max(matches, key=lambda row: len(row[1]))
        if not (0 < len(short[1]) < 80 and len(long[1]) > 150 and long[2].startswith(short[2])):
            return {"status": "BLOCKED_SUBSTACK_CAPTION_REPAIR_PREFIX_NOT_PROVEN", "platform": "substack", "draft_id": draft_id}
        short[0].evaluate(
            """element => {
                element.scrollIntoView({block: 'center'});
                const selection = window.getSelection();
                const range = document.createRange();
                range.selectNodeContents(element);
                selection.removeAllRanges();
                selection.addRange(range);
            }"""
        )
        page.keyboard.press("Backspace")
        time.sleep(2)
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline and not _substack_saved(page):
            time.sleep(0.5)
        remaining = []
        for node in editor.locator("p").all():
            try:
                normalized = _normalise_editor_text(node.inner_text(timeout=500) or "")
            except Exception:
                continue
            if expected[:35] in normalized:
                remaining.append(normalized)
        verified = len(remaining) == 1 and expected in remaining[0] and _substack_saved(page)
        return {
            "status": "SUCCESS" if verified else "FAILED_SUBSTACK_CAPTION_REPAIR_READBACK",
            "platform": "substack",
            "draft_id": draft_id,
            "removed_fragment_character_count": len(short[1]),
            "remaining_caption_node_count": len(remaining),
            "draft_saved": _substack_saved(page),
            "browser_write_performed": True,
        }


def repair_substack_editorial_paragraphs_via_edge(
    *,
    cdp_port: int,
    draft_id: str,
    expected_title: str,
    replacements: Sequence[Mapping[str, str]],
) -> dict[str, Any]:
    """Apply exact paragraph edits to one identified draft without rebuilding media."""
    if not str(draft_id).isdigit() or not replacements:
        return {"status": "BLOCKED_SUBSTACK_EDITORIAL_REPAIR_IDENTITY_INVALID", "platform": "substack"}
    normalized_rows = [
        {
            "old": " ".join(str(row.get("old") or "").split()),
            "new": " ".join(str(row.get("new") or "").split()),
        }
        for row in replacements
    ]
    if any(not row["old"] or row["old"] == row["new"] for row in normalized_rows):
        return {"status": "BLOCKED_SUBSTACK_EDITORIAL_REPAIR_REPLACEMENT_INVALID", "platform": "substack"}

    with canonical_edge_page(cdp_port) as page:
        page.goto(
            f"https://capitalchronicle.substack.com/publish/post/{draft_id}",
            wait_until="domcontentloaded",
            timeout=45000,
        )
        time.sleep(3)
        title_input, _ = _first_visible(page, ("#post-title", "input[name='title']", "input[placeholder*='Title']"))
        editor, _ = _first_visible(page, ("div.ProseMirror", ".ProseMirror", "div[contenteditable='true']"))
        if not title_input or not editor or title_input.input_value(timeout=3000).strip() != expected_title:
            return {"status": "BLOCKED_SUBSTACK_EDITORIAL_REPAIR_IDENTITY_MISMATCH", "platform": "substack", "draft_id": draft_id}

        images_before = editor.locator("img").evaluate_all(
            "nodes => nodes.map(node => ({src: node.currentSrc || node.src || '', alt: node.alt || ''}))"
        )
        paragraph_nodes = editor.locator("p").all()
        matches: list[tuple[int, Any, dict[str, str]]] = []
        for row in normalized_rows:
            row_matches: list[tuple[int, Any]] = []
            for index, node in enumerate(paragraph_nodes):
                try:
                    visible = " ".join((node.inner_text(timeout=700) or "").split())
                except Exception:
                    continue
                if visible == row["old"]:
                    row_matches.append((index, node))
            if len(row_matches) != 1:
                return {
                    "status": "BLOCKED_SUBSTACK_EDITORIAL_REPAIR_EXACT_MATCH_FAILED",
                    "platform": "substack",
                    "draft_id": draft_id,
                    "old_text_sha256": _sha256(row["old"]),
                    "matching_paragraph_count": len(row_matches),
                    "browser_write_performed": False,
                }
            matches.append((*row_matches[0], row))

        for _index, node, row in sorted(matches, key=lambda item: item[0], reverse=True):
            node.evaluate(
                """element => {
                    element.scrollIntoView({block: 'center'});
                    element.focus();
                    const selection = window.getSelection();
                    const range = document.createRange();
                    range.selectNodeContents(element);
                    selection.removeAllRanges();
                    selection.addRange(range);
                }"""
            )
            if row["new"]:
                page.keyboard.insert_text(row["new"])
            else:
                page.keyboard.press("Backspace")
            time.sleep(1)

        deadline = time.monotonic() + 18
        while time.monotonic() < deadline and not _substack_saved(page):
            time.sleep(0.5)
        editor_text = "\n".join(
            " ".join((node.inner_text(timeout=700) or "").split())
            for node in editor.locator("p").all()
        )
        images_after = editor.locator("img").evaluate_all(
            "nodes => nodes.map(node => ({src: node.currentSrc || node.src || '', alt: node.alt || ''}))"
        )
        old_absent = all(row["old"] not in editor_text for row in normalized_rows)
        new_present = all(not row["new"] or row["new"] in editor_text for row in normalized_rows)
        media_preserved = len(images_before) == 3 and images_after == images_before
        verified = bool(old_absent and new_present and media_preserved and _substack_saved(page))
        return {
            "status": "SUCCESS" if verified else "FAILED_SUBSTACK_EDITORIAL_REPAIR_READBACK",
            "platform": "substack",
            "draft_id": draft_id,
            "replacement_count": len(normalized_rows),
            "old_text_absent": old_absent,
            "new_text_present": new_present,
            "editor_body_image_count_before": len(images_before),
            "editor_body_image_count_after": len(images_after),
            "editor_image_order_preserved": images_after == images_before,
            "draft_saved": _substack_saved(page),
            "browser_write_performed": True,
        }


def _x_text_signature(value: str, *, limit: int = 6) -> tuple[str, ...]:
    first_line = next((line for line in str(value or "").splitlines() if line.strip()), value)
    return tuple(re.findall(r"[a-z0-9]+", str(first_line).casefold())[:limit])


def _x_visible_text_matches(expected_text: str, visible_text: str) -> bool:
    signature = _x_text_signature(expected_text)
    visible_tokens = tuple(re.findall(r"[a-z0-9]+", str(visible_text or "").casefold()))
    if len(signature) < 4 or sum(map(len, signature)) < 20:
        return False
    cursor = 0
    for token in visible_tokens:
        if cursor < len(signature) and token == signature[cursor]:
            cursor += 1
    return cursor == len(signature)


def _x_status_url_from_article(article: Any, handle: str) -> str | None:
    expected_handle = str(handle or "").lstrip("@").casefold()
    candidates: list[str] = []
    for link in article.locator("a[href*='/status/']").all():
        href = str(link.get_attribute("href") or "")
        candidate = _public_x_url(f"https://x.com{href}" if href.startswith("/") else href)
        if not candidate:
            continue
        parsed = urllib.parse.urlparse(candidate)
        observed_handle = parsed.path.strip("/").split("/", 1)[0].casefold()
        if observed_handle == expected_handle:
            candidates.append(candidate)
    unique = list(dict.fromkeys(candidates))
    return unique[0] if len(unique) == 1 else None


def _x_permalink_from_profile(page: Any, handle: str | None, expected_text: str) -> str | None:
    if not handle:
        return None
    page.goto(f"https://x.com/{handle.lstrip('@')}", wait_until="domcontentloaded", timeout=45000)
    time.sleep(5)
    matches: list[str] = []
    for article in page.locator("article").all():
        try:
            if not _x_visible_text_matches(expected_text, article.inner_text(timeout=1200) or ""):
                continue
            public_url = _x_status_url_from_article(article, handle)
            if public_url:
                matches.append(public_url)
        except Exception:
            continue
    unique = list(dict.fromkeys(matches))
    return unique[0] if len(unique) == 1 else None


def reconcile_x_thread_by_text_via_edge(
    *,
    cdp_port: int,
    expected_text: str,
    canonical_url: str,
    expected_reply_texts: Sequence[str],
    root_url: str | None = None,
    expected_handle: str = _X_PUBLIC_HANDLE,
    public_screenshot_path: str | Path | None = None,
) -> dict[str, Any]:
    """Find one exact X root and its replies without crossing a write boundary."""
    handle = str(expected_handle or _X_PUBLIC_HANDLE).lstrip("@")
    canonical_root = _public_x_url(root_url)
    if canonical_root:
        observed_handle = urllib.parse.urlparse(canonical_root).path.strip("/").split("/", 1)[0]
        if observed_handle.casefold() != handle.casefold():
            return {"status": "X_ROOT_IDENTITY_MISMATCH", "platform": "x"}
    with canonical_edge_page(cdp_port) as page:
        root_article = None
        if canonical_root:
            page.goto(canonical_root, wait_until="domcontentloaded", timeout=45000)
            time.sleep(5)
            root_id = canonical_root.rstrip("/").rsplit("/", 1)[-1]
            candidate = _x_article_for_status(page, root_id)
            visible = _normalised_visible_text(candidate.inner_text(timeout=2500)) if candidate else ""
            if (
                candidate
                and _x_visible_text_matches(expected_text, visible)
                and _canonical_reference_visible(visible, canonical_url)
            ):
                root_article = candidate
        else:
            page.goto(f"https://x.com/{handle}", wait_until="domcontentloaded", timeout=45000)
            time.sleep(5)
            matches: list[tuple[str, Any]] = []
            for article in page.locator("article").all():
                try:
                    visible = _normalised_visible_text(article.inner_text(timeout=1800))
                    if not (
                        _x_visible_text_matches(expected_text, visible)
                        and _canonical_reference_visible(visible, canonical_url)
                    ):
                        continue
                    candidate_url = _x_status_url_from_article(article, handle)
                    if candidate_url:
                        matches.append((candidate_url, article))
                except Exception:
                    continue
            unique_urls = list(dict.fromkeys(url for url, _article in matches))
            if len(unique_urls) != 1:
                return {
                    "status": (
                        "X_ROOT_NOT_FOUND_READBACK_INCONCLUSIVE"
                        if not unique_urls
                        else "AMBIGUOUS_X_ROOT_MATCH"
                    ),
                    "platform": "x",
                    "match_count": len(unique_urls),
                }
            canonical_root = unique_urls[0]
            root_article = next(article for url, article in matches if url == canonical_root)
            page.goto(canonical_root, wait_until="domcontentloaded", timeout=45000)
            time.sleep(5)
        root_id = str(canonical_root).rstrip("/").rsplit("/", 1)[-1]
        root_article = _x_article_for_status(page, root_id) or root_article
        root_text = _normalised_visible_text(root_article.inner_text(timeout=2500)) if root_article else ""
        replies: list[dict[str, Any]] = []
        missing_indexes: list[int] = []
        articles = page.locator("article").all()
        for index, expected_reply in enumerate(expected_reply_texts, start=1):
            reply_matches: list[tuple[str, str]] = []
            for article in articles:
                try:
                    visible = _normalised_visible_text(article.inner_text(timeout=1600))
                    if not _x_visible_text_matches(str(expected_reply), visible):
                        continue
                    candidate_url = _x_status_url_from_article(article, handle)
                    if candidate_url and candidate_url != canonical_root:
                        reply_matches.append((candidate_url, visible))
                except Exception:
                    continue
            unique_reply_urls = list(dict.fromkeys(url for url, _visible in reply_matches))
            if len(unique_reply_urls) != 1:
                missing_indexes.append(index)
                continue
            reply_url = unique_reply_urls[0]
            replies.append(
                {
                    "order": index,
                    "text": str(expected_reply),
                    "post_id": reply_url.rstrip("/").rsplit("/", 1)[-1],
                    "public_url": reply_url,
                    "parent_id": root_id if index == 1 else replies[-1]["post_id"],
                }
            )
        if public_screenshot_path:
            target = Path(public_screenshot_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(target), full_page=False)
        complete = bool(
            root_article
            and _x_visible_text_matches(expected_text, root_text)
            and _canonical_reference_visible(root_text, canonical_url)
            and not missing_indexes
            and len(replies) == len(expected_reply_texts)
        )
        return {
            "status": "SUCCESS" if complete else "X_ROOT_RECONCILED_REPLY_CHAIN_INCOMPLETE",
            "platform": "x",
            "post_id": root_id,
            "public_url": canonical_root,
            "destination_identity": "@" + handle,
            "write_exists": bool(root_article),
            "root_visible_text": root_text,
            "substack_url_visible": _canonical_reference_visible(root_text, canonical_url),
            "reply_chain": replies,
            "missing_reply_indexes": missing_indexes,
        }


def publish_x_post_via_edge(*, cdp_port: int, text: str, image_path: str | Path | None = None) -> dict[str, Any]:
    if len(text) > 280:
        return {"status": "BLOCKED_X_TEXT_OVER_280_CHARACTERS", "platform": "x"}
    with canonical_edge_page(cdp_port) as page:
        page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=45000)
        time.sleep(3)
        profile_link, _profile_selector = _first_visible(page, ("[data-testid='AppTabBar_Profile_Link']",))
        handle = None
        try:
            href = profile_link.get_attribute("href") if profile_link else None
            if href and href.startswith("/"):
                handle = href.strip("/")
        except Exception:
            pass
        page.goto("https://x.com/compose/post", wait_until="domcontentloaded", timeout=45000)
        time.sleep(2)
        composer, composer_selector = _first_visible(page, ("[data-testid='tweetTextarea_0']", "div[role='textbox'][data-testid*='tweetTextarea']"))
        if not composer:
            return {"status": "BLOCKED_X_COMPOSER_NOT_READY", "platform": "x", "composer_selector": composer_selector, "destination_identity": "@" + handle if handle else None}
        composer.click()
        page.keyboard.type(text, delay=0)
        media_status = "not_requested"
        if image_path:
            selector = _set_first_file_input(page, image_path)
            media_status = "uploaded" if selector else "file_input_not_found"
            if not selector:
                return {"status": "FAILED_X_MEDIA_UPLOAD", "platform": "x", "destination_identity": "@" + handle if handle else None, "media_status": media_status}
            time.sleep(4)
        post_selector = _click_first_visible(page, ("[data-testid='tweetButton']", "[data-testid='tweetButtonInline']"))
        if not post_selector:
            return {"status": "BLOCKED_X_POST_CONTROL_NOT_FOUND", "platform": "x", "destination_identity": "@" + handle if handle else None, "media_status": media_status}
        time.sleep(6)
        public_url = _x_permalink_from_profile(page, handle, text)
        if not public_url:
            return {"status": "FAILED_X_PERMALINK_READBACK", "platform": "x", "destination_identity": "@" + handle if handle else None, "media_status": media_status, "payload_sha256": _sha256(text)}
        return {"status": "SUCCESS", "platform": "x", "action": "post", "public_url": public_url, "post_id": public_url.rsplit("/", 1)[-1], "destination_identity": "@" + handle if handle else None, "media_status": media_status, "payload_sha256": _sha256(text)}


def _x_article_for_status(page: Any, status_id: str) -> Any | None:
    for article in page.locator("article").all():
        try:
            if article.locator(f"a[href*='/status/{status_id}']").count():
                return article
        except Exception:
            continue
    return None


def publish_x_reply_via_edge(
    *, cdp_port: int, parent_url: str, text: str, image_path: str | Path | None = None
) -> dict[str, Any]:
    if len(text) > 280 or "..." in text:
        return {"status": "BLOCKED_X_REPLY_PAYLOAD_INVALID", "platform": "x"}
    parent_id = str(parent_url).rstrip("/").rsplit("/", 1)[-1]
    if not parent_id.isdigit():
        return {"status": "BLOCKED_X_REPLY_PARENT_INVALID", "platform": "x"}
    with canonical_edge_page(cdp_port) as page:
        page.goto(parent_url, wait_until="domcontentloaded", timeout=45000)
        time.sleep(5)
        composer, composer_selector = _first_visible(
            page,
            (
                "[data-testid='tweetTextarea_0']",
                "div[role='textbox'][data-testid*='tweetTextarea']",
            ),
        )
        if not composer:
            return {"status": "BLOCKED_X_REPLY_COMPOSER_NOT_READY", "platform": "x", "parent_id": parent_id}
        composer.click(timeout=6000)
        page.keyboard.insert_text(text)
        media_status = "not_requested"
        if image_path:
            selector = _set_first_file_input(page, image_path)
            media_status = "uploaded" if selector else "file_input_not_found"
            if not selector:
                return {"status": "FAILED_X_REPLY_MEDIA_UPLOAD", "platform": "x", "parent_id": parent_id}
            time.sleep(4)
        reply_selector = _click_first_visible(page, ("[data-testid='tweetButtonInline']", "[data-testid='tweetButton']"))
        if not reply_selector:
            return {"status": "BLOCKED_X_REPLY_CONTROL_NOT_FOUND", "platform": "x", "parent_id": parent_id, "composer_selector": composer_selector}
        time.sleep(7)
        reply_url = None
        needle = _normalised_visible_text(text).casefold()[:90]
        for article in page.locator("article").all():
            try:
                if needle not in _normalised_visible_text(article.inner_text(timeout=1500)).casefold():
                    continue
                for link in article.locator("a[href*='/status/']").all():
                    href = str(link.get_attribute("href") or "")
                    candidate = _public_x_url("https://x.com" + href if href.startswith("/") else href)
                    if candidate and not candidate.rstrip("/").endswith("/" + parent_id):
                        reply_url = candidate
                        break
                if reply_url:
                    break
            except Exception:
                continue
        if not reply_url:
            return {"status": "FAILED_X_REPLY_PERMALINK_READBACK", "platform": "x", "parent_id": parent_id, "payload_sha256": _sha256(text), "media_status": media_status}
        return {
            "status": "SUCCESS",
            "platform": "x",
            "action": "reply",
            "parent_id": parent_id,
            "parent_url": parent_url,
            "post_id": reply_url.rstrip("/").rsplit("/", 1)[-1],
            "public_url": reply_url,
            "payload_sha256": _sha256(text),
            "media_status": media_status,
            "media_attached": bool(image_path),
        }


def readback_x_thread_via_edge(
    *,
    cdp_port: int,
    root_url: str,
    canonical_url: str,
    expected_chart_path: str | Path,
    replies: Sequence[Mapping[str, Any]],
    public_screenshot_path: str | Path | None = None,
) -> dict[str, Any]:
    root_id = str(root_url).rstrip("/").rsplit("/", 1)[-1]
    with canonical_edge_page(cdp_port) as page:
        page.goto(root_url, wait_until="domcontentloaded", timeout=45000)
        time.sleep(5)
        root = _x_article_for_status(page, root_id)
        root_text = _normalised_visible_text(root.inner_text(timeout=2500)) if root else ""
        root_image, root_media = _meaningful_image_in_scope(root) if root else (None, None)
        chart_similarity = _visual_similarity_to_local_image(root_image, expected_chart_path) if root_image else None
        ordered: list[dict[str, Any]] = []
        for index, reply in enumerate(replies, start=1):
            reply_url = str(reply.get("public_url") or "")
            reply_id = reply_url.rstrip("/").rsplit("/", 1)[-1]
            try:
                page.goto(reply_url, wait_until="domcontentloaded", timeout=45000)
                time.sleep(3)
                article = _x_article_for_status(page, reply_id)
                visible = _normalised_visible_text(article.inner_text(timeout=2000)) if article else ""
                parent_visible = bool(_x_article_for_status(page, str(reply.get("parent_id") or "")))
                reply_image, _reply_media = _meaningful_image_in_scope(article) if article else (None, None)
                expected_reply_media = str(reply.get("expected_media_local_path") or "")
                reply_similarity = _visual_similarity_to_local_image(reply_image, expected_reply_media) if reply_image and expected_reply_media else None
            except Exception:
                visible = ""
                parent_visible = False
                expected_reply_media = str(reply.get("expected_media_local_path") or "")
                reply_similarity = None
            expected = _normalised_visible_text(str(reply.get("text") or ""))
            ordered.append(
                {
                    "order": index,
                    "id": reply_id,
                    "public_url": reply_url,
                    "parent_id": reply.get("parent_id"),
                    "visible_body_text": visible,
                    "text_verified": bool(expected and expected.casefold() in visible.casefold()),
                    "parent_child_verified": parent_visible,
                    "expected_media_local_path": expected_reply_media or None,
                    "media_required": bool(expected_reply_media),
                    "media_verified": bool(not expected_reply_media or (reply_similarity is not None and reply_similarity >= _LINKEDIN_CHART_SIMILARITY_MINIMUM)),
                    "expected_chart_visual_similarity": reply_similarity,
                }
            )
        screenshot = None
        page.goto(root_url, wait_until="domcontentloaded", timeout=45000)
        time.sleep(3)
        if public_screenshot_path:
            target = Path(public_screenshot_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(target), full_page=False)
            screenshot = str(target)
        canonical_visible = _canonical_reference_visible(root_text, canonical_url)
        media_expected = bool(str(expected_chart_path or ""))
        media_verified = bool(
            not media_expected
            or (
                chart_similarity is not None
                and chart_similarity >= _LINKEDIN_CHART_SIMILARITY_MINIMUM
            )
        )
        verified = bool(
            root
            and canonical_visible
            and media_verified
            and ordered
            and all(row["text_verified"] and row["parent_child_verified"] and row["media_verified"] for row in ordered)
        )
        return {
            "status": "SUCCESS" if verified else "FAILED_X_THREAD_STRICT_READBACK",
            "platform": "x",
            "root_id": root_id,
            "root_public_url": root_url,
            "root_visible_text": root_text,
            "substack_url_visible": canonical_visible,
            "meaningful_media_visible": bool(media_expected and media_verified),
            "media_expected": media_expected,
            "expected_chart_visual_similarity": chart_similarity,
            "ordered_replies": ordered,
            "reply_chain_complete": bool(ordered and all(row["text_verified"] and row["parent_child_verified"] and row["media_verified"] for row in ordered)),
            "complete_article_visual_count": int(media_expected and media_verified) + sum(1 for row in ordered if row["media_required"] and row["media_verified"]),
            "public_screenshot_path": screenshot,
        }


def _normalised_visible_text(value: str) -> str:
    return " ".join(str(value or "").split())


def _canonical_reference_visible(value: str, canonical_url: str) -> bool:
    normalized = _normalised_visible_text(value)
    if canonical_url in normalized:
        return True
    compact = re.sub(r"\s+", "", normalized)
    parsed = urllib.parse.urlparse(canonical_url)
    visible_prefix = f"{parsed.netloc}{parsed.path[:28]}"
    return visible_prefix.casefold() in compact.casefold()


def _meaningful_image_in_scope(scope: Any) -> tuple[Any | None, dict[str, Any] | None]:
    try:
        images = scope.locator("img").all()
    except Exception:
        return None, None
    for image in images:
        try:
            if not image.is_visible(timeout=500):
                continue
            dimensions = image.evaluate(
                "node => ({complete: Boolean(node.complete), naturalWidth: node.naturalWidth || 0, "
                "naturalHeight: node.naturalHeight || 0})"
            )
            box = image.bounding_box() or {}
            if dimensions.get("complete") and _meaningful_image_dimensions(
                rendered_width=float(box.get("width") or 0),
                rendered_height=float(box.get("height") or 0),
                natural_width=float(dimensions.get("naturalWidth") or 0),
                natural_height=float(dimensions.get("naturalHeight") or 0),
            ):
                return image, {
                    "natural_width": int(dimensions.get("naturalWidth") or 0),
                    "natural_height": int(dimensions.get("naturalHeight") or 0),
                    "rendered_width": round(float(box.get("width") or 0), 1),
                    "rendered_height": round(float(box.get("height") or 0), 1),
                }
        except Exception:
            continue
    return None, None


def _visual_similarity_to_local_image(image: Any, reference_path: str | Path) -> float | None:
    """Compare a rendered provider image with a local source chart."""
    try:
        from PIL import Image, ImageChops, ImageFilter, ImageStat

        reference = Image.open(Path(reference_path)).convert("RGB").resize((96, 64))
        rendered = Image.open(io.BytesIO(image.screenshot(type="png"))).convert("RGB").resize((96, 64))
        grayscale_difference = ImageChops.difference(reference.convert("L"), rendered.convert("L"))
        edge_difference = ImageChops.difference(
            reference.convert("L").filter(ImageFilter.FIND_EDGES),
            rendered.convert("L").filter(ImageFilter.FIND_EDGES),
        )
        grayscale_error = float(ImageStat.Stat(grayscale_difference).mean[0]) / 255.0
        edge_error = float(ImageStat.Stat(edge_difference).mean[0]) / 255.0
        return round(max(0.0, 1.0 - (0.35 * grayscale_error + 0.65 * edge_error)), 4)
    except Exception:
        return None


def _linkedin_cards(page: Any) -> list[Any]:
    for selector in (
        ".feed-shared-update-v2[data-urn*='urn:li:activity:']",
        "[data-urn^='urn:li:activity:']",
        "article",
    ):
        try:
            cards = page.locator(selector).all()
        except Exception:
            continue
        if cards:
            return cards
    return []


def _linkedin_card_urn(card: Any) -> str | None:
    try:
        urn = str(card.get_attribute("data-urn") or "")
        if urn.startswith("urn:li:activity:"):
            return urn
    except Exception:
        pass
    try:
        nested = card.locator("[data-urn^='urn:li:activity:']").first
        urn = str(nested.get_attribute("data-urn") or "") if nested.count() else ""
        return urn if urn.startswith("urn:li:activity:") else None
    except Exception:
        return None


def _linkedin_card_permalink(card: Any) -> str | None:
    urn = _linkedin_card_urn(card)
    if urn:
        return f"https://www.linkedin.com/feed/update/{urn}/"
    try:
        for link in card.locator("a[href*='/feed/update/'], a[href*='/posts/']").all():
            href = str(link.get_attribute("href") or "")
            if href.startswith("/"):
                href = "https://www.linkedin.com" + href
            if href.startswith("https://www.linkedin.com/"):
                return href.split("?", 1)[0]
    except Exception:
        pass
    return None


def _linkedin_commentary_text(card: Any) -> str:
    for selector in (
        "[data-testid='main-feed-activity-card__commentary']",
        ".update-components-text",
        ".feed-shared-update-v2__description-wrapper",
        ".feed-shared-update-v2__description",
    ):
        try:
            locator = card.locator(selector).first
            if locator.count() and locator.is_visible(timeout=500):
                value = _normalised_visible_text(locator.inner_text(timeout=1500))
                if value:
                    return value
        except Exception:
            continue
    return ""


def _linkedin_card_author_matches(card: Any, expected_profile_slug: str) -> bool:
    try:
        if card.locator(f"a[href*='/in/{expected_profile_slug}']").count():
            return True
    except Exception:
        pass
    try:
        actor = card.locator(".update-components-actor__name, .update-components-actor__title").first
        return "jim pham" in _normalised_visible_text(actor.inner_text(timeout=1200)).casefold()
    except Exception:
        return False


def _linkedin_card_timestamp(card: Any) -> str | None:
    for selector in (
        ".update-components-actor__sub-description span[aria-hidden='true']",
        ".update-components-actor__sub-description",
        "time",
    ):
        try:
            value = _normalised_visible_text(card.locator(selector).first.inner_text(timeout=1000))
            if value:
                return value
        except Exception:
            continue
    return None


def _linkedin_card_by_post_id(page: Any, post_id: str | None) -> Any | None:
    for card in _linkedin_cards(page):
        urn = _linkedin_card_urn(card) or ""
        if not post_id or urn.endswith(":" + str(post_id)):
            return card
    return None


def _linkedin_card_readback(card: Any, *, expected_text: str, canonical_url: str) -> dict[str, Any]:
    commentary = _linkedin_commentary_text(card)
    image, image_readback = _meaningful_image_in_scope(card)
    del image
    title_line = next((line.strip() for line in expected_text.splitlines() if line.strip()), expected_text)
    body_text_visible = bool(
        commentary
        and _normalised_visible_text(title_line).casefold() in commentary.casefold()
        and len(commentary) >= min(120, max(40, len(_normalised_visible_text(title_line))))
    )
    canonical_url_text_visible = canonical_url in commentary
    canonical_link_target_verified = canonical_url_text_visible
    visible_link_text = canonical_url if canonical_url_text_visible else None
    if not canonical_link_target_verified:
        try:
            for link in card.locator("a[href]").all():
                href = str(link.get_attribute("href") or "")
                link_text = _normalised_visible_text(link.inner_text(timeout=500))
                if "lnkd.in/" not in href and "linkedin.com/redir" not in href:
                    continue
                request = urllib.request.Request(href, headers={"User-Agent": "CapitalChronicleContentOps/6.0"})
                with urllib.request.urlopen(request, timeout=12) as response:
                    final_url = str(response.geturl() or "")
                    response_body = response.read(256 * 1024).decode("utf-8", errors="ignore")
                final_parsed = urllib.parse.urlparse(final_url)
                canonical_parsed = urllib.parse.urlparse(canonical_url)
                if (
                    final_parsed.netloc == canonical_parsed.netloc
                    and final_parsed.path.rstrip("/") == canonical_parsed.path.rstrip("/")
                ) or canonical_url.rstrip("/") in response_body:
                    canonical_link_target_verified = True
                    visible_link_text = link_text or href
                    break
        except Exception:
            canonical_link_target_verified = False
    canonical_url_visible = canonical_url_text_visible or canonical_link_target_verified
    permalink = _linkedin_card_permalink(card)
    urn = _linkedin_card_urn(card) or ""
    return {
        "status": "SUCCESS" if body_text_visible and canonical_url_visible and image_readback and permalink else "FAILED_LINKEDIN_STRICT_READBACK",
        "platform": "linkedin",
        "action": "readback_existing_post",
        "post_id": urn.rsplit(":", 1)[-1] if urn else None,
        "public_url": permalink,
        "visible_body_text": commentary,
        "body_text_visible": body_text_visible,
        "substack_url_visible": canonical_url_visible,
        "canonical_url_text_visible": canonical_url_text_visible,
        "canonical_link_target_verified": canonical_link_target_verified,
        "visible_link_text": visible_link_text,
        "meaningful_media_visible": bool(image_readback),
        "media_readback": image_readback,
        "destination_identity": "linkedin:jimcc" if _linkedin_card_author_matches(card, "jimcc") else None,
    }


def _linkedin_permalink_from_feed(page: Any, expected_text: str) -> str | None:
    title_line = next((line.strip() for line in expected_text.splitlines() if line.strip()), expected_text)
    needle = " ".join(title_line.split()).casefold()[:70]
    selectors = ("[data-urn*='urn:li:activity:']", "article", ".feed-shared-update-v2")
    for selector in selectors:
        try:
            cards = page.locator(selector).all()
        except Exception:
            continue
        for card in cards:
            try:
                card_text = " ".join((card.inner_text(timeout=1500) or "").split()).casefold()
                if needle not in card_text:
                    continue
                urn = card.get_attribute("data-urn") or ""
                if not urn.startswith("urn:li:activity:"):
                    urn_locator = card.locator("[data-urn*='urn:li:activity:']").first
                    urn = urn_locator.get_attribute("data-urn") if urn_locator.count() else ""
                if urn and urn.startswith("urn:li:activity:"):
                    return f"https://www.linkedin.com/feed/update/{urn}/"
                for link in card.locator("a[href*='/feed/update/'], a[href*='/posts/']").all():
                    href = link.get_attribute("href") or ""
                    if href.startswith("/"):
                        href = "https://www.linkedin.com" + href
                    if href.startswith("https://www.linkedin.com/"):
                        return href.split("?", 1)[0]
            except Exception:
                continue
    return None


def readback_linkedin_post_via_edge(
    *,
    cdp_port: int,
    expected_text: str,
    canonical_url: str,
    public_screenshot_path: str | Path | None = None,
) -> dict[str, Any]:
    """Find an already-published LinkedIn post without performing a write."""
    return {
        "status": "READBACK_CAPABILITY_LIMITED",
        "platform": "linkedin",
        "reason_code": "LINKEDIN_CDP_TRANSPORT_RETIRED_OFFICIAL_MEMBER_API_REQUIRED",
        "browser_navigation_performed": False,
        "browser_write_performed": False,
    }
    # Historical implementation below is intentionally preserved as evidence but unreachable.
    with canonical_edge_page(cdp_port) as page:
        public_url = None
        title_line = next((line.strip() for line in expected_text.splitlines() if line.strip()), expected_text)
        for target in (
            "https://www.linkedin.com/in/jimcc/recent-activity/posts/",
            "https://www.linkedin.com/in/jimcc/recent-activity/all/",
            "https://www.linkedin.com/feed/",
            "https://www.linkedin.com/search/results/content/?keywords="
            + urllib.parse.quote(title_line)
            + "&origin=GLOBAL_SEARCH_HEADER",
        ):
            page.goto(target, wait_until="domcontentloaded", timeout=45000)
            time.sleep(4)
            for _ in range(4):
                public_url = _linkedin_permalink_from_feed(page, expected_text)
                if public_url:
                    break
                try:
                    title_locator = page.locator("text=" + title_line).first
                    if title_locator.count():
                        card = title_locator.locator("xpath=ancestor::*[@data-urn][1]")
                        urn = card.get_attribute("data-urn") if card.count() else ""
                        if urn and urn.startswith("urn:li:activity:"):
                            public_url = f"https://www.linkedin.com/feed/update/{urn}/"
                            break
                except Exception:
                    pass
                page.evaluate("window.scrollBy(0, Math.max(window.innerHeight * 1.5, 900))")
                time.sleep(1.5)
            if public_url:
                break
        if not public_url:
            screenshot = None
            if public_screenshot_path:
                target = Path(public_screenshot_path)
                target.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(target), full_page=False)
                screenshot = str(target)
            return {"status": "BLOCKED_LINKEDIN_EXISTING_POST_NOT_FOUND", "platform": "linkedin", "public_screenshot_path": screenshot}
        page.goto(public_url, wait_until="domcontentloaded", timeout=45000)
        time.sleep(4)
        match = re.search(r"urn:li:activity:(\d+)", public_url)
        card = _linkedin_card_by_post_id(page, match.group(1) if match else None)
        readback = _linkedin_card_readback(card, expected_text=expected_text, canonical_url=canonical_url) if card else {
            "status": "FAILED_LINKEDIN_STRICT_READBACK",
            "platform": "linkedin",
            "post_id": match.group(1) if match else None,
            "public_url": public_url,
            "body_text_visible": False,
            "substack_url_visible": False,
            "meaningful_media_visible": False,
        }
        screenshot = None
        if public_screenshot_path:
            target = Path(public_screenshot_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(target), full_page=False)
            screenshot = str(target)
        return {**readback, "public_screenshot_path": screenshot, "browser_write_performed": False}


def reconcile_existing_linkedin_post_via_edge(
    *,
    cdp_port: int,
    expected_text: str,
    canonical_url: str,
    chart_path: str | Path,
    expected_payload_sha256: str | None = None,
    public_screenshot_path: str | Path | None = None,
) -> dict[str, Any]:
    """Identify the existing chart post before any edit; this function never writes."""
    return {
        "status": "READBACK_CAPABILITY_LIMITED",
        "platform": "linkedin",
        "reason_code": "LINKEDIN_CDP_TRANSPORT_RETIRED_OFFICIAL_MEMBER_API_REQUIRED",
        "browser_navigation_performed": False,
        "browser_write_performed": False,
    }
    # Historical implementation below is intentionally preserved as evidence but unreachable.
    with canonical_edge_page(cdp_port) as page:
        candidate: dict[str, Any] | None = None
        candidate_card = None
        targets_visited: list[str] = []
        best_similarity: float | None = None
        for target_url in (
            "https://www.linkedin.com/in/jimcc/recent-activity/all/",
            "https://www.linkedin.com/in/jimcc/recent-activity/posts/",
            "https://www.linkedin.com/in/jimcc/recent-activity/images/",
            "https://www.linkedin.com/feed/",
        ):
            page.goto(target_url, wait_until="domcontentloaded", timeout=45000)
            targets_visited.append(page.url)
            time.sleep(5)
            if "/recent-activity/" in page.url:
                _click_first_visible(page, ("button:has-text('Posts')", "a:has-text('Posts')"))
                time.sleep(1)
            for scroll_index in range(5):
                for index, card in enumerate(_linkedin_cards(page)[:30]):
                    if not _linkedin_card_author_matches(card, "jimcc"):
                        continue
                    image, image_readback = _meaningful_image_in_scope(card)
                    if image is None or image_readback is None:
                        continue
                    similarity = _visual_similarity_to_local_image(image, chart_path)
                    if similarity is not None and (best_similarity is None or similarity > best_similarity):
                        best_similarity = similarity
                    if similarity is None or similarity < _LINKEDIN_CHART_SIMILARITY_MINIMUM:
                        continue
                    permalink = _linkedin_card_permalink(card)
                    urn = _linkedin_card_urn(card) or ""
                    if not permalink or not urn:
                        continue
                    candidate_card = card
                    candidate = {
                        "activity_index": index,
                        "scroll_index": scroll_index,
                        "reconciled_from": page.url,
                        "post_id": urn.rsplit(":", 1)[-1],
                        "public_url": permalink,
                        "publication_timestamp_readback": _linkedin_card_timestamp(card),
                        "chart_similarity_score": similarity,
                        "chart_similarity_minimum": _LINKEDIN_CHART_SIMILARITY_MINIMUM,
                        "media_readback": image_readback,
                        "destination_identity": "linkedin:jimcc",
                        "account_identity_verified": True,
                        "source_chart_verified": True,
                        "article_topic_match_via_source_chart": True,
                        "expected_payload_sha256": expected_payload_sha256,
                    }
                    break
                if candidate:
                    break
                page.evaluate("window.scrollBy(0, Math.max(window.innerHeight * 1.25, 800))")
                time.sleep(1.2)
            if candidate:
                break
        screenshot = None
        if public_screenshot_path:
            target = Path(public_screenshot_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(target), full_page=False)
            screenshot = str(target)
        if not candidate or candidate_card is None:
            return {
                "status": "BLOCKED_EXISTING_LINKEDIN_POST_NOT_RECONCILED",
                "platform": "linkedin",
                "browser_write_performed": False,
                "public_screenshot_path": screenshot,
                "targets_visited": targets_visited,
                "best_chart_similarity_score": best_similarity,
            }
        strict = _linkedin_card_readback(candidate_card, expected_text=expected_text, canonical_url=canonical_url)
        if strict.get("status") == "SUCCESS":
            return {
                **candidate,
                **strict,
                "status": "SUCCESS",
                "reconciliation_state": "ALREADY_CORRECTED_STRICT_READBACK",
                "browser_write_performed": False,
                "public_screenshot_path": screenshot,
            }
        commentary = _linkedin_commentary_text(candidate_card)
        return {
            **candidate,
            "status": "MALFORMED_EXISTING_POST_REQUIRES_EDIT",
            "platform": "linkedin",
            "action": "reconcile_existing_post",
            "visible_body_text": commentary,
            "body_text_visible": bool(commentary),
            "substack_url_visible": canonical_url in commentary,
            "meaningful_media_visible": True,
            "browser_write_performed": False,
            "public_screenshot_path": screenshot,
        }


def readback_linkedin_activity_via_edge(
    *,
    cdp_port: int,
    public_url: str,
    post_id: str,
    expected_text: str,
    canonical_url: str,
    chart_path: str | Path,
    public_screenshot_path: str | Path | None = None,
) -> dict[str, Any]:
    """Read one exact LinkedIn activity; never search, retry, or write."""
    return {
        "status": "READBACK_CAPABILITY_LIMITED",
        "platform": "linkedin",
        "reason_code": "LINKEDIN_CDP_TRANSPORT_RETIRED_OFFICIAL_MEMBER_API_REQUIRED",
        "browser_navigation_performed": False,
        "browser_write_performed": False,
    }
    # Historical implementation below is intentionally preserved as evidence but unreachable.
    if not post_id or f"urn:li:activity:{post_id}" not in public_url:
        return {"status": "BLOCKED_LINKEDIN_ACTIVITY_TARGET_MISMATCH", "platform": "linkedin", "browser_write_performed": False}
    with canonical_edge_page(cdp_port) as page:
        page.goto(public_url, wait_until="domcontentloaded", timeout=45000)
        time.sleep(5)
        card = _linkedin_card_by_post_id(page, post_id)
        screenshot = None
        if public_screenshot_path:
            target = Path(public_screenshot_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(target), full_page=False)
            screenshot = str(target)
        if card is None or not _linkedin_card_author_matches(card, "jimcc"):
            return {
                "status": "BLOCKED_LINKEDIN_EXACT_ACTIVITY_NOT_FOUND",
                "platform": "linkedin",
                "post_id": post_id,
                "public_url": public_url,
                "browser_write_performed": False,
                "public_screenshot_path": screenshot,
            }
        image, media_readback = _meaningful_image_in_scope(card)
        similarity = _visual_similarity_to_local_image(image, chart_path) if image else None
        strict = _linkedin_card_readback(card, expected_text=expected_text, canonical_url=canonical_url)
        commentary = _linkedin_commentary_text(card)
        chart_verified = bool(similarity is not None and similarity >= _LINKEDIN_CHART_SIMILARITY_MINIMUM)
        status = "SUCCESS" if strict.get("status") == "SUCCESS" and chart_verified else (
            "MALFORMED_EXISTING_POST_REQUIRES_EDIT" if chart_verified and not commentary else "FAILED_LINKEDIN_EXACT_ACTIVITY_READBACK"
        )
        return {
            **strict,
            "status": status,
            "platform": "linkedin",
            "post_id": post_id,
            "public_url": public_url,
            "visible_body_text": commentary,
            "body_text_visible": bool(commentary),
            "substack_url_visible": bool(strict.get("substack_url_visible")),
            "meaningful_media_visible": chart_verified,
            "chart_similarity_score": similarity,
            "media_readback": media_readback,
            "destination_identity": "linkedin:jimcc",
            "browser_write_performed": False,
            "public_screenshot_path": screenshot,
        }


def edit_existing_linkedin_post_via_edge(
    *,
    cdp_port: int,
    public_url: str,
    post_id: str,
    text: str,
    canonical_url: str,
    public_screenshot_path: str | Path | None = None,
) -> dict[str, Any]:
    """Edit a reconciled LinkedIn post in place. It can never create a post."""
    return {
        "status": "BLOCKED_LINKEDIN_CDP_TRANSPORT_RETIRED",
        "platform": "linkedin",
        "reason_code": "OFFICIAL_MEMBER_API_REQUIRED",
        "browser_navigation_performed": False,
        "browser_write_performed": False,
    }
    # Historical implementation below is intentionally preserved as evidence but unreachable.
    if not post_id or f"urn:li:activity:{post_id}" not in public_url:
        return {"status": "BLOCKED_LINKEDIN_EDIT_TARGET_MISMATCH", "platform": "linkedin", "public_url": public_url}
    if not text.strip() or canonical_url not in text or _TECHNICAL_PUBLIC_TEXT_RE.search(text):
        return {"status": "BLOCKED_LINKEDIN_PUBLIC_PAYLOAD_INVALID", "platform": "linkedin", "public_url": public_url}
    with canonical_edge_page(cdp_port) as page:
        page.goto(public_url, wait_until="domcontentloaded", timeout=45000)
        time.sleep(5)
        card = _linkedin_card_by_post_id(page, post_id)
        if card is None or not _linkedin_card_author_matches(card, "jimcc"):
            return {"status": "BLOCKED_EXISTING_LINKEDIN_POST_CANNOT_BE_EDITED", "platform": "linkedin", "public_url": public_url, "post_id": post_id, "reason": "reconciled_activity_card_not_available"}
        before_image, before_media = _meaningful_image_in_scope(card)
        del before_image
        if not before_media:
            return {"status": "BLOCKED_EXISTING_LINKEDIN_POST_CANNOT_BE_EDITED", "platform": "linkedin", "public_url": public_url, "post_id": post_id, "reason": "reconciled_chart_not_visible_before_edit"}
        menu, menu_selector = _first_visible(
            card,
            (
                "button[aria-label*='Open control menu']",
                "button[aria-label*='Control Menu']",
                "button[aria-label*='More actions']",
                "button.artdeco-dropdown__trigger",
            ),
        )
        if not menu:
            return {"status": "BLOCKED_EXISTING_LINKEDIN_POST_CANNOT_BE_EDITED", "platform": "linkedin", "public_url": public_url, "post_id": post_id, "reason": "post_control_menu_not_available"}
        menu.click(timeout=6000)
        time.sleep(1)
        edit_selector = _click_first_visible(
            page,
            (
                "[role='menuitem']:has-text('Edit post')",
                "[role='menuitem']:has-text('Chỉnh sửa bài đăng')",
                "div[role='button']:has-text('Edit post')",
                "div[role='button']:has-text('Chỉnh sửa bài đăng')",
                "li:has-text('Edit post')",
            ),
        )
        if not edit_selector:
            return {"status": "BLOCKED_EXISTING_LINKEDIN_POST_CANNOT_BE_EDITED", "platform": "linkedin", "public_url": public_url, "post_id": post_id, "reason": "edit_post_control_not_available", "menu_selector": menu_selector}
        time.sleep(2)
        editor, editor_selector = _first_visible(
            page,
            (
                "div[role='dialog'] div.ql-editor[contenteditable='true']",
                "div[role='dialog'] [role='textbox'][contenteditable='true']",
                "div[role='dialog'] div[contenteditable='true']",
            ),
        )
        if not editor:
            return {"status": "BLOCKED_EXISTING_LINKEDIN_POST_CANNOT_BE_EDITED", "platform": "linkedin", "public_url": public_url, "post_id": post_id, "reason": "edit_post_editor_not_available", "edit_selector": edit_selector}
        try:
            editor.fill(text)
        except Exception:
            editor.click(timeout=6000)
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            page.keyboard.insert_text(text)
        save_selector = _click_first_visible(
            page,
            (
                "div[role='dialog'] button:has-text('Save')",
                "div[role='dialog'] button:has-text('Lưu')",
                "button.share-actions__primary-action:has-text('Save')",
            ),
        )
        if not save_selector:
            return {"status": "BLOCKED_EXISTING_LINKEDIN_POST_CANNOT_BE_EDITED", "platform": "linkedin", "public_url": public_url, "post_id": post_id, "reason": "edit_post_save_control_not_available", "editor_selector": editor_selector}
        time.sleep(7)
        page.goto(public_url, wait_until="domcontentloaded", timeout=45000)
        time.sleep(5)
        card = _linkedin_card_by_post_id(page, post_id)
        readback = _linkedin_card_readback(card, expected_text=text, canonical_url=canonical_url) if card else {
            "status": "FAILED_LINKEDIN_STRICT_READBACK",
            "post_id": post_id,
            "public_url": public_url,
            "body_text_visible": False,
            "substack_url_visible": False,
            "meaningful_media_visible": False,
        }
        screenshot = None
        if public_screenshot_path:
            target = Path(public_screenshot_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(target), full_page=False)
            screenshot = str(target)
        verified = bool(
            readback.get("status") == "SUCCESS"
            and readback.get("body_text_visible")
            and readback.get("substack_url_visible")
            and readback.get("meaningful_media_visible")
            and readback.get("public_url")
        )
        return {
            "status": "SUCCESS" if verified else "FAILED_LINKEDIN_EDIT_READBACK",
            "platform": "linkedin",
            "action": "edit_existing_post",
            "post_id": post_id,
            "public_url": public_url,
            "payload_sha256": _sha256(text),
            "media_status": "preserved_existing_chart",
            "media_transfer": {"upload_transport": "preserved_existing_media_no_reupload"},
            "provider_readback_verified": verified,
            "readback": {**readback, "public_screenshot_path": screenshot},
            "new_post_created": False,
            "menu_selector": menu_selector,
            "edit_selector": edit_selector,
            "editor_selector": editor_selector,
            "save_selector": save_selector,
        }


def comment_existing_linkedin_post_via_edge(
    *,
    cdp_port: int,
    public_url: str,
    post_id: str,
    text: str,
    canonical_url: str,
    public_screenshot_path: str | Path | None = None,
) -> dict[str, Any]:
    """Add an author comment to a reconciled image-only post; never create a root."""
    return {
        "status": "BLOCKED_LINKEDIN_CDP_TRANSPORT_RETIRED",
        "platform": "linkedin",
        "reason_code": "OFFICIAL_MEMBER_API_REQUIRED",
        "browser_navigation_performed": False,
        "browser_write_performed": False,
    }
    # Historical implementation below is intentionally preserved as evidence but unreachable.
    if not post_id or canonical_url not in text or _TECHNICAL_PUBLIC_TEXT_RE.search(text):
        return {"status": "BLOCKED_LINKEDIN_COMMENT_PAYLOAD_INVALID", "platform": "linkedin"}
    with canonical_edge_page(cdp_port) as page:
        page.goto(public_url, wait_until="domcontentloaded", timeout=45000)
        time.sleep(5)
        card = _linkedin_card_by_post_id(page, post_id)
        if card is None or not _linkedin_card_author_matches(card, "jimcc"):
            return {"status": "BLOCKED_LINKEDIN_AUTHOR_COMMENT_NOT_AVAILABLE", "platform": "linkedin", "public_url": public_url}
        image, media = _meaningful_image_in_scope(card)
        del image
        if not media:
            return {"status": "BLOCKED_LINKEDIN_AUTHOR_COMMENT_NOT_AVAILABLE", "platform": "linkedin", "public_url": public_url, "reason": "root_chart_not_visible"}
        _click_first_visible(card, ("button:has-text('Comment')", "button[aria-label*='Comment']"))
        time.sleep(1)
        editor, editor_selector = _first_visible(
            card,
            (
                "div.ql-editor[contenteditable='true']",
                "[role='textbox'][contenteditable='true']",
                "div[contenteditable='true']",
            ),
        )
        if not editor:
            return {"status": "BLOCKED_LINKEDIN_AUTHOR_COMMENT_NOT_AVAILABLE", "platform": "linkedin", "public_url": public_url, "reason": "comment_editor_not_found"}
        editor.click(timeout=6000)
        page.keyboard.insert_text(text)
        submit_selector = _click_first_visible(
            card,
            (
                "button.comments-comment-box__submit-button",
                "button:has-text('Comment')",
                "button:has-text('Bình luận')",
            ),
        )
        if not submit_selector:
            return {"status": "BLOCKED_LINKEDIN_AUTHOR_COMMENT_NOT_AVAILABLE", "platform": "linkedin", "public_url": public_url, "reason": "comment_submit_not_found", "editor_selector": editor_selector}
        time.sleep(7)
        page.goto(public_url, wait_until="domcontentloaded", timeout=45000)
        time.sleep(5)
        visible = _normalised_visible_text(page.locator("main").inner_text(timeout=5000))
        comment_visible = _normalised_visible_text(text)[:120].casefold() in visible.casefold()
        canonical_visible = canonical_url in visible
        comment_id = None
        try:
            needle = next((line.strip() for line in text.splitlines() if line.strip()), text)
            locator = page.get_by_text(needle, exact=False).first
            container = locator.locator("xpath=ancestor::*[@data-id or @data-urn][1]")
            comment_id = container.get_attribute("data-id") or container.get_attribute("data-urn") if container.count() else None
        except Exception:
            comment_id = None
        screenshot = None
        if public_screenshot_path:
            target = Path(public_screenshot_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(target), full_page=False)
            screenshot = str(target)
        verified = bool(comment_visible and canonical_visible and media and public_url)
        return {
            "status": "SUCCESS" if verified else "FAILED_LINKEDIN_AUTHOR_COMMENT_READBACK",
            "platform": "linkedin",
            "action": "author_comment_repair",
            "post_id": post_id,
            "comment_id": comment_id,
            "public_url": public_url,
            "payload_sha256": _sha256(text),
            "provider_readback_verified": verified,
            "media_transfer": {"upload_transport": "preserved_existing_media_no_reupload"},
            "readback": {
                "status": "SUCCESS" if verified else "FAILED_LINKEDIN_AUTHOR_COMMENT_READBACK",
                "public_url": public_url,
                "body_text_visible": comment_visible,
                "substack_url_visible": canonical_visible,
                "meaningful_media_visible": True,
                "public_screenshot_path": screenshot,
                "comment_id": comment_id,
            },
            "new_post_created": False,
            "editor_selector": editor_selector,
            "submit_selector": submit_selector,
        }


def readback_youtube_public_video_via_edge(
    *,
    cdp_port: int,
    public_url: str,
    expected_title: str,
    public_screenshot_path: str | Path | None = None,
) -> dict[str, Any]:
    """Verify an existing public YouTube video without touching Studio."""
    video_id = _youtube_video_id_from_value(public_url)
    if not video_id:
        return {"status": "BLOCKED_INVALID_YOUTUBE_PUBLIC_URL", "platform": "youtube"}
    with canonical_edge_page(cdp_port) as page:
        page.goto(public_url, wait_until="domcontentloaded", timeout=45000)
        time.sleep(5)
        title_value = ""
        try:
            title_value = page.locator("meta[property='og:title']").first.get_attribute("content") or page.title()
        except Exception:
            pass
        title_matches = " ".join(expected_title.split()).casefold()[:60] in " ".join(str(title_value).split()).casefold()
        player_visible = bool(_first_visible(page, ("#movie_player", "video", "ytd-watch-flexy"))[0])
        private_badge_visible = bool(_first_visible(page, ("text=Riêng tư", "text=Private"))[0])
        public_visibility_verified = bool(player_visible and not private_badge_visible)
        screenshot = None
        if public_screenshot_path:
            target = Path(public_screenshot_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(target), full_page=False)
            screenshot = str(target)
        return {
            "status": "SUCCESS" if public_visibility_verified else "BLOCKED_YOUTUBE_PUBLIC_VISIBILITY_NOT_VERIFIED",
            "platform": "youtube",
            "video_id": video_id,
            "public_url": public_url,
            "title_matches": title_matches,
            "player_visible": player_visible,
            "private_badge_visible": private_badge_visible,
            "public_visibility_verified": public_visibility_verified,
            "public_screenshot_path": screenshot,
            "browser_write_performed": False,
        }


def edit_youtube_video_metadata_via_edge(
    *,
    cdp_port: int,
    video_id: str,
    title: str,
    description: str,
    public_screenshot_path: str | Path | None = None,
) -> dict[str, Any]:
    """Repair metadata on an existing video; never create or upload a video."""
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id or ""):
        return {"status": "BLOCKED_INVALID_YOUTUBE_VIDEO_ID", "platform": "youtube"}
    with canonical_edge_page(cdp_port) as page:
        page.goto(f"https://studio.youtube.com/video/{video_id}/edit", wait_until="domcontentloaded", timeout=45000)
        time.sleep(4)
        title_box, title_selector = _first_visible(
            page,
            (
                "#title-textarea #textbox",
                "ytcp-mention-textbox#title-textarea #textbox",
                "[aria-label*='Add a title']",
                "[aria-label*='Tiêu đề']",
            ),
        )
        if not title_box:
            return {"status": "BLOCKED_YOUTUBE_METADATA_TITLE_EDITOR_NOT_FOUND", "platform": "youtube"}
        title_box.fill(title[:100])
        description_box, description_selector = _first_visible(
            page,
            (
                "#description-textarea #textbox",
                "ytcp-mention-textbox#description-textarea #textbox",
                "[aria-label*='Tell viewers about your video']",
                "[aria-label*='Mô tả']",
            ),
        )
        if not description_box:
            return {"status": "BLOCKED_YOUTUBE_METADATA_DESCRIPTION_EDITOR_NOT_FOUND", "platform": "youtube", "title_selector": title_selector}
        description_box.fill(description[:4900])
        save_selector = _click_first_visible(
            page,
            (
                "#save",
                "ytcp-button#save",
                "button:has-text('Save')",
                "button:has-text('Lưu')",
            ),
        )
        if not save_selector:
            return {
                "status": "BLOCKED_YOUTUBE_METADATA_SAVE_CONTROL_NOT_FOUND",
                "platform": "youtube",
                "title_selector": title_selector,
                "description_selector": description_selector,
            }
        time.sleep(5)
    public_url = f"https://www.youtube.com/watch?v={video_id}"
    readback = readback_youtube_public_video_via_edge(
        cdp_port=cdp_port,
        public_url=public_url,
        expected_title=title,
        public_screenshot_path=public_screenshot_path,
    )
    return {
        "status": "SUCCESS" if readback.get("status") == "SUCCESS" and readback.get("title_matches") else "FAILED_YOUTUBE_METADATA_PUBLIC_READBACK",
        "platform": "youtube",
        "action": "edit_metadata",
        "video_id": video_id,
        "public_url": public_url,
        "title_selector": title_selector,
        "description_selector": description_selector,
        "save_selector": save_selector,
        "readback": readback,
        "new_video_created": False,
    }


def set_youtube_video_public_via_edge(
    *,
    cdp_port: int,
    video_id: str,
    expected_title: str,
    public_screenshot_path: str | Path | None = None,
) -> dict[str, Any]:
    """Change only the recorded video's visibility to Public."""
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id or ""):
        return {"status": "BLOCKED_INVALID_YOUTUBE_VIDEO_ID", "platform": "youtube"}
    with canonical_edge_page(cdp_port) as page:
        page.goto(f"https://studio.youtube.com/video/{video_id}/edit", wait_until="domcontentloaded", timeout=45000)
        time.sleep(4)
        current_visibility, current_selector = _first_visible(page, ("text=Riêng tư", "text=Private"))
        if not current_visibility:
            public_readback = readback_youtube_public_video_via_edge(
                cdp_port=cdp_port,
                public_url=f"https://www.youtube.com/watch?v={video_id}",
                expected_title=expected_title,
                public_screenshot_path=public_screenshot_path,
            )
            return {
                "status": "SUCCESS" if public_readback.get("public_visibility_verified") else "BLOCKED_YOUTUBE_PRIVATE_VISIBILITY_CONTROL_NOT_FOUND",
                "platform": "youtube",
                "action": "verify_or_set_public_visibility",
                "video_id": video_id,
                "public_url": f"https://www.youtube.com/watch?v={video_id}",
                "readback": public_readback,
                "new_video_created": False,
            }
        current_visibility.scroll_into_view_if_needed(timeout=5000)
        current_visibility.click(timeout=6000)
        time.sleep(1)
        public_selector = _click_first_visible(
            page,
            (
                "tp-yt-paper-radio-button[name='PUBLIC']",
                "[name='PUBLIC']",
                "text=Công khai",
                "text=Public",
            ),
        )
        if not public_selector:
            return {"status": "BLOCKED_YOUTUBE_PUBLIC_VISIBILITY_CONTROL_NOT_FOUND", "platform": "youtube", "current_visibility_selector": current_selector}
        time.sleep(0.5)
        done_selector = _click_first_visible(
            page,
            (
                "ytcp-button#done-button",
                "#done-button",
                "button:has-text('Xong')",
                "button:has-text('Done')",
            ),
        )
        time.sleep(0.8)
        save_selector = _click_first_visible(
            page,
            (
                "#save",
                "ytcp-button#save",
                "button:has-text('Save')",
                "button:has-text('Lưu')",
            ),
        )
        if not save_selector:
            return {
                "status": "BLOCKED_YOUTUBE_PUBLIC_VISIBILITY_SAVE_NOT_FOUND",
                "platform": "youtube",
                "current_visibility_selector": current_selector,
                "public_selector": public_selector,
                "done_selector": done_selector,
            }
        time.sleep(6)
    public_url = f"https://www.youtube.com/watch?v={video_id}"
    readback = readback_youtube_public_video_via_edge(
        cdp_port=cdp_port,
        public_url=public_url,
        expected_title=expected_title,
        public_screenshot_path=public_screenshot_path,
    )
    return {
        "status": "SUCCESS" if readback.get("status") == "SUCCESS" and readback.get("public_visibility_verified") else "FAILED_YOUTUBE_PUBLIC_VISIBILITY_READBACK",
        "platform": "youtube",
        "action": "set_public_visibility",
        "video_id": video_id,
        "public_url": public_url,
        "current_visibility_selector": current_selector,
        "public_selector": public_selector,
        "done_selector": done_selector,
        "save_selector": save_selector,
        "readback": readback,
        "new_video_created": False,
    }


def _wait_for_meaningful_visible_image(
    page: Any,
    selectors: Sequence[str],
    *,
    timeout_seconds: float = 20.0,
) -> dict[str, Any] | None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        for selector in selectors:
            try:
                candidates = page.locator(selector).all()
            except Exception:
                continue
            for image in candidates:
                try:
                    if not image.is_visible(timeout=500):
                        continue
                    dimensions = image.evaluate(
                        "node => ({complete: Boolean(node.complete), naturalWidth: node.naturalWidth || 0, naturalHeight: node.naturalHeight || 0})"
                    )
                    box = image.bounding_box() or {}
                    if dimensions.get("complete") and _meaningful_image_dimensions(
                        rendered_width=float(box.get("width") or 0),
                        rendered_height=float(box.get("height") or 0),
                        natural_width=float(dimensions.get("naturalWidth") or 0),
                        natural_height=float(dimensions.get("naturalHeight") or 0),
                    ):
                        return {
                            "selector": selector,
                            "natural_width": int(dimensions.get("naturalWidth") or 0),
                            "natural_height": int(dimensions.get("naturalHeight") or 0),
                            "rendered_width": round(float(box.get("width") or 0), 1),
                            "rendered_height": round(float(box.get("height") or 0), 1),
                        }
                except Exception:
                    continue
        time.sleep(0.4)
    return None


def publish_linkedin_post_via_edge(
    *,
    cdp_port: int,
    text: str,
    image_path: str | Path | None = None,
    canonical_url: str | None = None,
    public_screenshot_path: str | Path | None = None,
) -> dict[str, Any]:
    return {
        "status": "BLOCKED_LINKEDIN_CDP_TRANSPORT_RETIRED",
        "platform": "linkedin",
        "reason_code": "OFFICIAL_MEMBER_API_REQUIRED",
        "browser_navigation_performed": False,
        "browser_write_performed": False,
    }
    # Historical implementation below is intentionally preserved as evidence but unreachable.
    with canonical_edge_page(cdp_port) as page:
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=45000)
        time.sleep(4)
        start_selector = _click_first_visible(page, ("button:has-text('Start a post')", "text=Start a post", "button[aria-label*='Start a post']"))
        if not start_selector:
            return {"status": "BLOCKED_LINKEDIN_COMPOSER_NOT_READY", "platform": "linkedin"}
        time.sleep(2)
        editor, editor_selector = _first_visible(page, ("div[role='dialog'] div.ql-editor", "div[role='dialog'] [role='textbox']", "div.ql-editor"))
        if not editor:
            return {"status": "BLOCKED_LINKEDIN_EDITOR_NOT_READY", "platform": "linkedin", "editor_selector": editor_selector}
        editor.click()
        page.keyboard.type(text, delay=0)
        media_status = "not_requested"
        media_transfer: dict[str, Any] = {}
        media_preview: dict[str, Any] | None = None
        if image_path:
            media_control, media_control_selector = _first_visible(
                page,
                (
                    "button[aria-label*='Add media']",
                    "button[aria-label*='Add a photo']",
                    "button[aria-label*='Media']",
                    "button:has-text('Add media')",
                ),
            )
            if not media_control:
                return {"status": "BLOCKED_LINKEDIN_MEDIA_CONTROL_NOT_FOUND", "platform": "linkedin"}
            media_transfer = _activate_file_upload(
                page,
                trigger=media_control,
                file_path=image_path,
                media_kind="image",
                exclusive=False,
            )
            media_status = "uploaded" if media_transfer.get("status") == "file_set" else "file_input_not_found"
            if media_transfer.get("status") != "file_set":
                return {
                    "status": "FAILED_LINKEDIN_MEDIA_UPLOAD",
                    "platform": "linkedin",
                    "media_status": media_status,
                    "media_control_selector": media_control_selector,
                    "media_transfer": media_transfer,
                }
            media_preview = _wait_for_meaningful_visible_image(
                page,
                (
                    "div[role='dialog'] img",
                    ".share-creation-state__preview img",
                    "img[alt*='preview']",
                ),
                timeout_seconds=25,
            )
            if not media_preview:
                return {
                    "status": "FAILED_LINKEDIN_MEDIA_PREVIEW_READBACK",
                    "platform": "linkedin",
                    "media_status": media_status,
                    "media_control_selector": media_control_selector,
                    "media_transfer": media_transfer,
                }
            next_selector = _click_first_visible(
                page,
                (
                    "div[role='dialog'] button:has-text('Next')",
                    "button[aria-label='Next']",
                    "button:has-text('Next')",
                    "button:has-text('Tiếp')",
                ),
            )
            if next_selector:
                time.sleep(2)
        editor_before_post, _editor_before_post_selector = _first_visible(
            page,
            ("div[role='dialog'] div.ql-editor", "div[role='dialog'] [role='textbox']", "div.ql-editor"),
        )
        visible_draft_text = ""
        if editor_before_post:
            try:
                visible_draft_text = _normalised_visible_text(editor_before_post.inner_text(timeout=1500))
            except Exception:
                visible_draft_text = ""
        title_line = next((line.strip() for line in text.splitlines() if line.strip()), text)
        if title_line.casefold() not in visible_draft_text.casefold():
            if not editor_before_post:
                return {"status": "BLOCKED_LINKEDIN_TEXT_EDITOR_LOST_AFTER_MEDIA", "platform": "linkedin", "media_status": media_status}
            try:
                editor_before_post.fill(text)
            except Exception:
                editor_before_post.click(timeout=6000)
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                page.keyboard.insert_text(text)
            visible_draft_text = _normalised_visible_text(editor_before_post.inner_text(timeout=1500))
        if title_line.casefold() not in visible_draft_text.casefold() or (canonical_url and canonical_url not in visible_draft_text):
            return {
                "status": "BLOCKED_LINKEDIN_TEXT_MEDIA_PREPOST_GATE",
                "platform": "linkedin",
                "media_status": media_status,
                "body_text_present": title_line.casefold() in visible_draft_text.casefold(),
                "canonical_url_present": bool(canonical_url and canonical_url in visible_draft_text),
            }
        post_selector = _click_first_visible(page, ("div[role='dialog'] button.share-actions__primary-action", "div[role='dialog'] button:has-text('Post')", "button.share-actions__primary-action"))
        if not post_selector:
            return {"status": "BLOCKED_LINKEDIN_POST_CONTROL_NOT_FOUND", "platform": "linkedin", "media_status": media_status}
        time.sleep(8)
        permalink = _linkedin_permalink_from_feed(page, text)
        if not permalink:
            return {"status": "FAILED_LINKEDIN_PERMALINK_READBACK", "platform": "linkedin", "media_status": media_status, "media_transfer": media_transfer, "media_preview": media_preview, "payload_sha256": _sha256(text)}
        post_id = permalink.rsplit(":", 1)[-1].rstrip("/")
        page.goto(permalink, wait_until="domcontentloaded", timeout=45000)
        time.sleep(4)
        card = _linkedin_card_by_post_id(page, post_id)
        readback = _linkedin_card_readback(card, expected_text=text, canonical_url=str(canonical_url or "")) if card and canonical_url else {}
        screenshot = None
        if public_screenshot_path:
            target = Path(public_screenshot_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(target), full_page=False)
            screenshot = str(target)
        verified = bool(readback.get("status") == "SUCCESS")
        return {
            "status": "SUCCESS" if verified else "FAILED_LINKEDIN_STRICT_READBACK",
            "platform": "linkedin",
            "action": "post",
            "public_url": permalink,
            "post_id": post_id,
            "media_status": media_status,
            "media_transfer": media_transfer,
            "media_preview": media_preview,
            "provider_readback_verified": verified,
            "readback": {**readback, "public_screenshot_path": screenshot} if readback else {},
            "payload_sha256": _sha256(text),
        }


def publish_tiktok_video_via_edge(*, cdp_port: int, video_path: str | Path, caption: str) -> dict[str, Any]:
    """Upload a native short video when the canonical Edge profile is authenticated."""
    with canonical_edge_page(cdp_port) as page:
        navigation_error = None
        try:
            page.goto("https://www.tiktok.com/tiktokstudio/upload", wait_until="domcontentloaded", timeout=45000)
        except Exception as exc:
            navigation_error = exc
        time.sleep(3)
        if "tiktok.com/login" in page.url or _first_visible(page, ("text=Log in to TikTok", "button:has-text('Log in')", "text=Use phone / email / username"))[0]:
            return {"status": "BLOCKED_TIKTOK_LOGIN_REQUIRED", "platform": "tiktok", "required_unblock": "Log in to the intended Capital Chronicle TikTok creator account in the canonical Edge profile, then rerun only TikTok."}
        if navigation_error:
            return {"status": "BLOCKED_TIKTOK_STUDIO_NAVIGATION", "platform": "tiktok", "error_class": type(navigation_error).__name__}
        upload_selector = _set_first_file_input(page, video_path)
        if not upload_selector:
            return {"status": "BLOCKED_TIKTOK_UPLOAD_INPUT_NOT_FOUND", "platform": "tiktok"}
        time.sleep(8)
        caption_box, caption_selector = _first_visible(page, ("div[contenteditable='true']", "textarea[placeholder*='caption']", "textarea"))
        if not caption_box:
            return {"status": "BLOCKED_TIKTOK_CAPTION_EDITOR_NOT_FOUND", "platform": "tiktok", "upload_selector": upload_selector, "caption_selector": caption_selector}
        caption_box.click()
        page.keyboard.type(caption, delay=0)
        post_selector = _click_first_visible(page, ("button:has-text('Post')", "button:has-text('Publish')"))
        if not post_selector:
            return {"status": "BLOCKED_TIKTOK_POST_CONTROL_NOT_FOUND", "platform": "tiktok", "upload_selector": upload_selector}
        time.sleep(8)
        return {"status": "FAILED_TIKTOK_PERMALINK_READBACK", "platform": "tiktok", "payload_sha256": _sha256(caption), "upload_selector": upload_selector}


def validate_youtube_community_payload(
    *,
    text: str,
    image_path: str | Path | None,
    canonical_url: str,
) -> dict[str, Any]:
    blockers: list[str] = []
    if not _normalised_visible_text(text):
        blockers.append("non_empty_text_required")
    if not canonical_url or canonical_url not in text:
        blockers.append("canonical_substack_url_required")
    if image_path and not Path(image_path).is_file():
        blockers.append("supplied_image_path_invalid")
    if _TECHNICAL_PUBLIC_TEXT_RE.search(text):
        blockers.append("technical_run_identifier_forbidden")
    return {
        "status": "VALID" if not blockers else "INVALID",
        "blockers": blockers,
        "text_present": bool(_normalised_visible_text(text)),
        "image_present": bool(image_path and Path(image_path).is_file()),
        "text_only_supported": True,
        "canonical_url_present": bool(canonical_url and canonical_url in text),
        "technical_run_identifier_absent": not bool(_TECHNICAL_PUBLIC_TEXT_RE.search(text)),
    }


def _youtube_community_post_id(value: str | None) -> str | None:
    match = re.search(r"(?:youtube\.com)?/post/([A-Za-z0-9_-]+)", str(value or ""))
    return match.group(1) if match else None


def _youtube_community_cards(page: Any) -> list[Any]:
    for selector in (
        "ytd-backstage-post-thread-renderer",
        "ytd-backstage-post-renderer",
        "[data-post-id]",
    ):
        try:
            cards = page.locator(selector).all()
        except Exception:
            continue
        if cards:
            return cards
    return []


def _youtube_community_card_text(card: Any) -> str:
    for selector in ("#content-text", "yt-formatted-string#content-text", "#content"):
        try:
            locator = card.locator(selector).first
            if locator.count() and locator.is_visible(timeout=500):
                value = _normalised_visible_text(locator.inner_text(timeout=1500))
                if value:
                    return value
        except Exception:
            continue
    try:
        return _normalised_visible_text(card.inner_text(timeout=2000))
    except Exception:
        return ""


def _youtube_community_permalink_from_card(card: Any) -> str | None:
    try:
        for link in card.locator("a[href*='/post/']").all():
            href = str(link.get_attribute("href") or "")
            if href.startswith("/"):
                href = "https://www.youtube.com" + href
            post_id = _youtube_community_post_id(href)
            if post_id:
                return f"https://www.youtube.com/post/{post_id}"
    except Exception:
        pass
    return None


def _youtube_community_card_for_text(page: Any, expected_text: str) -> Any | None:
    title_line = next((line.strip() for line in expected_text.splitlines() if line.strip()), expected_text)
    needle = _normalised_visible_text(title_line).casefold()[:70]
    for card in _youtube_community_cards(page):
        if needle and needle in _youtube_community_card_text(card).casefold():
            return card
    return None


def _youtube_community_canonical_link_readback(card: Any, canonical_url: str) -> dict[str, Any]:
    try:
        for link in card.locator("a[href]").all():
            href = str(link.get_attribute("href") or "")
            visible_text = _normalised_visible_text(link.inner_text(timeout=500))
            parsed = urllib.parse.urlparse(href)
            candidates = [href]
            query = urllib.parse.parse_qs(parsed.query)
            for key in ("q", "url", "u"):
                candidates.extend(query.get(key) or [])
            for candidate in candidates:
                target = urllib.parse.urlparse(urllib.parse.unquote(candidate))
                canonical = urllib.parse.urlparse(canonical_url)
                if target.netloc == canonical.netloc and target.path.rstrip("/") == canonical.path.rstrip("/"):
                    return {
                        "verified": True,
                        "visible_link_text": visible_text or href,
                        "link_href_kind": "youtube_redirect" if "youtube.com/redirect" in href else "direct",
                    }
    except Exception:
        pass
    return {"verified": False, "visible_link_text": None, "link_href_kind": None}


def _youtube_channel_identity_verified(page: Any, expected_handle: str) -> bool:
    expected = expected_handle.casefold()
    if expected in page.url.casefold():
        return True
    try:
        for link in page.locator("a[href*='@']").all():
            href = str(link.get_attribute("href") or "").casefold()
            text = _normalised_visible_text(link.inner_text(timeout=500)).casefold()
            if expected in href or expected in text:
                return True
    except Exception:
        pass
    return False


def readback_youtube_community_post_via_edge(
    *,
    cdp_port: int,
    public_url: str,
    expected_text: str,
    canonical_url: str,
    expected_handle: str = _YOUTUBE_COMMUNITY_HANDLE,
    public_screenshot_path: str | Path | None = None,
    expect_media: bool = True,
) -> dict[str, Any]:
    post_id = _youtube_community_post_id(public_url)
    if not post_id:
        return {"status": "BLOCKED_INVALID_YOUTUBE_COMMUNITY_URL", "platform": "youtube", "public_url": public_url}
    with canonical_edge_page(cdp_port) as page:
        page.goto(public_url, wait_until="domcontentloaded", timeout=45000)
        time.sleep(5)
        card = _youtube_community_card_for_text(page, expected_text)
        visible_text = _youtube_community_card_text(card) if card else ""
        image, image_readback = _meaningful_image_in_scope(card) if card else (None, None)
        del image
        title_line = next((line.strip() for line in expected_text.splitlines() if line.strip()), expected_text)
        text_visible = bool(_normalised_visible_text(title_line).casefold() in visible_text.casefold())
        canonical_url_text_visible = canonical_url in visible_text
        canonical_link = _youtube_community_canonical_link_readback(card, canonical_url) if card else {"verified": False}
        canonical_url_visible = canonical_url_text_visible or bool(canonical_link.get("verified"))
        channel_identity_verified = _youtube_channel_identity_verified(page, expected_handle)
        screenshot = None
        if public_screenshot_path:
            target = Path(public_screenshot_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(target), full_page=False)
            screenshot = str(target)
        verified = bool(
            text_visible and canonical_url_visible and channel_identity_verified
            and (bool(image_readback) if expect_media else True)
        )
        return {
            "status": "SUCCESS" if verified else "FAILED_YOUTUBE_COMMUNITY_STRICT_READBACK",
            "platform": "youtube",
            "action": "readback_community_post",
            "post_id": post_id,
            "public_url": f"https://www.youtube.com/post/{post_id}",
            "destination_identity": expected_handle if channel_identity_verified else None,
            "channel_identity_verified": channel_identity_verified,
            "visible_body_text": visible_text,
            "body_text_visible": text_visible,
            "substack_url_visible": canonical_url_visible,
            "canonical_url_text_visible": canonical_url_text_visible,
            "canonical_link_target_verified": bool(canonical_link.get("verified")),
            "visible_link_text": canonical_link.get("visible_link_text"),
            "link_href_kind": canonical_link.get("link_href_kind"),
            "meaningful_media_visible": bool(image_readback),
            "media_expected": bool(expect_media),
            "media_readback": image_readback,
            "public_screenshot_path": screenshot,
            "browser_write_performed": False,
        }


def reconcile_youtube_community_post_by_text_via_edge(
    *,
    cdp_port: int,
    expected_text: str,
    canonical_url: str,
    expected_handle: str = _YOUTUBE_COMMUNITY_HANDLE,
    expect_media: bool = True,
) -> dict[str, Any]:
    """Read the exact channel feed to resolve a post attempt that returned no permalink."""
    with canonical_edge_page(cdp_port) as page:
        page.goto(
            f"https://www.youtube.com/{expected_handle}/posts",
            wait_until="domcontentloaded",
            timeout=45000,
        )
        time.sleep(5)
        identity_verified = _youtube_channel_identity_verified(page, expected_handle)
        card = _youtube_community_card_for_text(page, expected_text)
        public_url = _youtube_community_permalink_from_card(card) if card else None
    if public_url:
        return readback_youtube_community_post_via_edge(
            cdp_port=cdp_port,
            public_url=public_url,
            expected_text=expected_text,
            canonical_url=canonical_url,
            expected_handle=expected_handle,
            expect_media=expect_media,
        )
    return {
        "status": "YOUTUBE_COMMUNITY_POST_CONFIRMED_ABSENT",
        "platform": "youtube",
        "verified": False,
        "write_absent": bool(identity_verified),
        "channel_identity_verified": identity_verified,
        "browser_write_performed": False,
    }


def _youtube_community_surface_diagnostics(page: Any) -> dict[str, Any]:
    contenteditables: list[dict[str, Any]] = []
    try:
        for locator in page.locator("[contenteditable='true']").all()[:12]:
            contenteditables.append(
                {
                    "tag": locator.evaluate("node => node.tagName.toLowerCase()"),
                    "id": locator.get_attribute("id"),
                    "role": locator.get_attribute("role"),
                    "aria_label": locator.get_attribute("aria-label"),
                    "visible": locator.is_visible(timeout=300),
                }
            )
    except Exception:
        pass
    controls: list[dict[str, Any]] = []
    try:
        for locator in page.locator("button, ytd-button-renderer, tp-yt-paper-button").all()[:80]:
            try:
                if not locator.is_visible(timeout=200):
                    continue
                text_value = _normalised_visible_text(locator.inner_text(timeout=300))[:80]
                aria = str(locator.get_attribute("aria-label") or "")[:80]
                if text_value or aria:
                    controls.append({"text": text_value, "aria_label": aria})
            except Exception:
                continue
    except Exception:
        pass
    creation_text = ""
    try:
        creation = page.locator("ytd-backstage-post-creation-renderer").first
        creation_text = _normalised_visible_text(creation.inner_text(timeout=1500))[:500] if creation.count() else ""
    except Exception:
        pass
    image_control_ancestors: list[dict[str, Any]] = []
    try:
        image_control = page.get_by_text("Hình ảnh", exact=True).first
        if image_control.count():
            image_control_ancestors = image_control.evaluate(
                "node => { const rows = []; let current = node; for (let i = 0; current && i < 8; i++, current = current.parentElement) "
                "rows.push({tag: current.tagName.toLowerCase(), id: current.id || null, cls: String(current.className || '').slice(0, 160)}); return rows; }"
            )
    except Exception:
        pass
    post_related_tags: list[str] = []
    try:
        post_related_tags = page.evaluate(
            "() => Array.from(new Set(Array.from(document.querySelectorAll('*')).map(node => node.tagName.toLowerCase())"
            ".filter(tag => tag.includes('post') || tag.includes('backstage') || tag.includes('creation')))).sort()"
        )
    except Exception:
        pass
    dialog_descendants: list[dict[str, Any]] = []
    try:
        dialog = page.locator("ytd-backstage-post-dialog-renderer").first
        if dialog.count():
            for locator in dialog.locator("textarea, input, [contenteditable], [role='textbox'], [id]").all()[:80]:
                try:
                    dialog_descendants.append(
                        {
                            "tag": locator.evaluate("node => node.tagName.toLowerCase()"),
                            "id": locator.get_attribute("id"),
                            "type": locator.get_attribute("type"),
                            "contenteditable": locator.get_attribute("contenteditable"),
                            "role": locator.get_attribute("role"),
                            "aria_label": locator.get_attribute("aria-label"),
                            "disabled": locator.get_attribute("disabled"),
                            "aria_disabled": locator.get_attribute("aria-disabled"),
                            "visible": locator.is_visible(timeout=200),
                        }
                    )
                except Exception:
                    continue
    except Exception:
        pass
    post_control_state: dict[str, Any] = {}
    try:
        post_control = page.locator("ytd-backstage-post-dialog-renderer #post-button").first
        button = post_control.locator("button").first if post_control.count() else None
        post_control_state = {
            "renderer_count": post_control.count(),
            "renderer_visible": post_control.is_visible(timeout=300) if post_control.count() else False,
            "renderer_disabled": post_control.get_attribute("disabled") if post_control.count() else None,
            "button_count": button.count() if button else 0,
            "button_visible": button.is_visible(timeout=300) if button and button.count() else False,
            "button_disabled": button.is_disabled(timeout=300) if button and button.count() else None,
            "button_aria_disabled": button.get_attribute("aria-disabled") if button and button.count() else None,
            "button_text": _normalised_visible_text(button.inner_text(timeout=500)) if button and button.count() else None,
        }
    except Exception:
        pass
    return {
        "page_url": page.url,
        "creation_renderer_count": page.locator("ytd-backstage-post-creation-renderer").count(),
        "post_dialog_count": page.locator("ytd-backstage-post-dialog").count(),
        "file_input_count": page.locator("input[type='file']").count(),
        "creation_renderer_text": creation_text,
        "contenteditables": contenteditables,
        "visible_controls": controls[:30],
        "image_control_ancestors": image_control_ancestors,
        "post_related_tags": post_related_tags[:80],
        "dialog_descendants": dialog_descendants,
        "post_control_state": post_control_state,
    }


def probe_youtube_community_surface_via_edge(
    *,
    cdp_port: int,
    expected_handle: str = _YOUTUBE_COMMUNITY_HANDLE,
    screenshot_path: str | Path | None = None,
) -> dict[str, Any]:
    """Read-only selector probe for the authenticated Community composer."""
    with canonical_edge_page(cdp_port) as page:
        page.goto(f"https://www.youtube.com/{expected_handle}/posts", wait_until="domcontentloaded", timeout=45000)
        time.sleep(5)
        screenshot = None
        if screenshot_path:
            target = Path(screenshot_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(target), full_page=False)
            screenshot = str(target)
        canonical_channel_id = None
        for selector, attribute in (
            ("link[rel='canonical']", "href"),
            ("meta[property='og:url']", "content"),
        ):
            try:
                value = str(page.locator(selector).first.get_attribute(attribute) or "")
                match = re.search(r"/channel/(UC[A-Za-z0-9_-]+)", value)
                if match:
                    canonical_channel_id = match.group(1)
                    break
            except Exception:
                continue
        return {
            "status": "SUCCESS",
            "channel_identity_verified": _youtube_channel_identity_verified(page, expected_handle),
            "canonical_channel_id": canonical_channel_id,
            "diagnostics": _youtube_community_surface_diagnostics(page),
            "public_screenshot_path": screenshot,
            "browser_write_performed": False,
        }


def publish_youtube_community_post_via_edge(
    *,
    cdp_port: int,
    text: str,
    image_path: str | Path | None,
    canonical_url: str,
    expected_handle: str = _YOUTUBE_COMMUNITY_HANDLE,
    public_screenshot_path: str | Path | None = None,
) -> dict[str, Any]:
    """Publish one Community text post, optionally with an image; never create video."""
    validation = validate_youtube_community_payload(text=text, image_path=image_path, canonical_url=canonical_url)
    if validation["status"] != "VALID":
        return {"status": "BLOCKED_YOUTUBE_COMMUNITY_PAYLOAD_INVALID", "platform": "youtube", "validation": validation}
    with canonical_edge_page(cdp_port) as page:
        channel_url = f"https://www.youtube.com/{expected_handle}/posts"
        page.goto(channel_url, wait_until="domcontentloaded", timeout=45000)
        time.sleep(5)
        if _first_visible(page, ("a:has-text('Sign in')", "text=Sign in"))[0]:
            return {"status": "BLOCKED_YOUTUBE_LOGIN_REQUIRED", "platform": "youtube"}
        if not _youtube_channel_identity_verified(page, expected_handle):
            return {"status": "BLOCKED_YOUTUBE_CHANNEL_IDENTITY_MISMATCH", "platform": "youtube", "page_domain": urllib.parse.urlparse(page.url).netloc}

        composer, composer_selector = _first_visible(
            page,
            (
                "ytd-backstage-post-dialog #contenteditable-root",
                "ytd-backstage-post-dialog [contenteditable='true']",
                "ytd-backstage-post-dialog-renderer #contenteditable-root",
                "ytd-backstage-post-dialog-renderer [contenteditable='true']",
                "ytd-backstage-post-creation-renderer #contenteditable-root",
                "ytd-backstage-post-creation-renderer [contenteditable='true']",
                "#contenteditable-textarea [contenteditable='true']",
                "yt-formatted-string[contenteditable='true']",
            ),
        )
        if not composer:
            _click_first_visible(
                page,
                (
                    "ytd-backstage-post-creation-renderer #placeholder",
                    "ytd-backstage-post-dialog-renderer #commentbox-placeholder",
                    "ytd-backstage-post-dialog-renderer #placeholder-area",
                    "ytd-backstage-post-creation-renderer:has-text('Share an image')",
                    "ytd-backstage-post-creation-renderer:has-text('Chia sẻ hình ảnh')",
                    "text=Share an image to start a conversation",
                    "text=Chia sẻ hình ảnh để bắt đầu cuộc trò chuyện",
                ),
            )
            time.sleep(1.5)
            composer, composer_selector = _first_visible(
                page,
                (
                    "ytd-backstage-post-dialog #contenteditable-root",
                    "ytd-backstage-post-dialog [contenteditable='true']",
                    "ytd-backstage-post-dialog-renderer #contenteditable-root",
                    "ytd-backstage-post-dialog-renderer [contenteditable='true']",
                    "ytd-backstage-post-creation-renderer #contenteditable-root",
                    "ytd-backstage-post-creation-renderer [contenteditable='true']",
                    "#contenteditable-textarea [contenteditable='true']",
                ),
            )
        if not composer:
            screenshot = None
            if public_screenshot_path:
                target = Path(public_screenshot_path)
                target.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(target), full_page=False)
                screenshot = str(target)
            return {
                "status": "BLOCKED_YOUTUBE_COMMUNITY_NOT_AVAILABLE",
                "platform": "youtube",
                "reason": "community_text_composer_not_found",
                "diagnostics": _youtube_community_surface_diagnostics(page),
                "public_screenshot_path": screenshot,
            }
        composer.click(timeout=6000)
        try:
            composer.fill(text)
        except Exception:
            page.keyboard.insert_text(text)

        if not image_path:
            post_selector = _click_first_visible(
                page,
                (
                    "ytd-backstage-post-dialog #submit-button button",
                    "ytd-backstage-post-dialog-renderer #post-button button",
                    "ytd-backstage-post-dialog-renderer #post-button",
                    "ytd-backstage-post-dialog button:has-text('Post')",
                    "ytd-backstage-post-dialog button:has-text('Đăng')",
                    "ytd-backstage-post-creation-renderer #submit-button button",
                    "ytd-backstage-post-creation-renderer button:has-text('Post')",
                    "ytd-backstage-post-creation-renderer button:has-text('Đăng')",
                    "yt-posts-creation-options-editor-view-model button:has-text('Post')",
                    "yt-posts-creation-options-editor-view-model button:has-text('Đăng')",
                    "button:has-text('Post')",
                    "button:has-text('Đăng')",
                    "yt-button-shape:has-text('Post')",
                    "yt-button-shape:has-text('Đăng')",
                ),
            )
            if not post_selector:
                return {
                    "status": "BLOCKED_YOUTUBE_COMMUNITY_POST_CONTROL_NOT_FOUND",
                    "platform": "youtube",
                    "composer_selector": composer_selector,
                    "text_only": True,
                    "diagnostics": _youtube_community_surface_diagnostics(page),
                }
            deadline = time.monotonic() + 35
            public_url = None
            feed_refreshed = False
            while time.monotonic() < deadline and not public_url:
                card = _youtube_community_card_for_text(page, text)
                public_url = _youtube_community_permalink_from_card(card) if card else None
                if not public_url:
                    if not feed_refreshed and time.monotonic() + 20 >= deadline:
                        page.goto(channel_url, wait_until="domcontentloaded", timeout=45000)
                        time.sleep(4)
                        feed_refreshed = True
                        continue
                    time.sleep(1)
            if not public_url:
                return {
                    "status": "FAILED_YOUTUBE_COMMUNITY_POST_URL_READBACK",
                    "platform": "youtube",
                    "action": "community_text_post",
                    "text_only": True,
                    "payload_sha256": _sha256(text),
                }
            readback = readback_youtube_community_post_via_edge(
                cdp_port=cdp_port,
                public_url=public_url,
                expected_text=text,
                canonical_url=canonical_url,
                expected_handle=expected_handle,
                public_screenshot_path=public_screenshot_path,
                expect_media=False,
            )
            verified = readback.get("status") == "SUCCESS"
            return {
                "status": "SUCCESS" if verified else "FAILED_YOUTUBE_COMMUNITY_POST_READBACK",
                "platform": "youtube",
                "action": "community_text_post",
                "post_id": _youtube_community_post_id(public_url),
                "public_url": public_url,
                "destination_identity": expected_handle,
                "media_transfer": None,
                "media_preview": None,
                "provider_readback_verified": verified,
                "readback": readback,
                "payload_sha256": _sha256(text),
                "text_only": True,
                "video_or_short_created": False,
            }

        image_control, image_control_selector = _first_visible(
            page,
            (
                "ytd-backstage-post-dialog button[aria-label*='Image']",
                "ytd-backstage-post-dialog button[aria-label*='Hình ảnh']",
                "ytd-backstage-post-dialog-renderer #image-button button",
                "ytd-backstage-post-dialog-renderer button[aria-label*='Thêm hình ảnh']",
                "ytd-backstage-post-dialog-renderer button[aria-label*='Image']",
                "ytd-backstage-post-creation-renderer button[aria-label*='Image']",
                "ytd-backstage-post-creation-renderer button[aria-label*='Hình ảnh']",
                "ytd-backstage-post-dialog ytd-button-renderer:has-text('Image')",
                "ytd-backstage-post-dialog ytd-button-renderer:has-text('Hình ảnh')",
                "ytd-backstage-post-creation-renderer ytd-button-renderer:has-text('Image')",
                "ytd-backstage-post-creation-renderer ytd-button-renderer:has-text('Hình ảnh')",
            ),
        )
        if not image_control:
            return {"status": "BLOCKED_YOUTUBE_COMMUNITY_NOT_AVAILABLE", "platform": "youtube", "reason": "community_image_control_not_found", "composer_selector": composer_selector}
        upload_transfer = _activate_file_upload(
            page,
            trigger=image_control,
            file_path=image_path,
            media_kind="image",
            exclusive=True,
            chooser_timeout_ms=10000,
        )
        secondary_image_control_selector = None
        if upload_transfer.get("status") != "file_set":
            time.sleep(1)
            secondary_image_control, secondary_image_control_selector = _first_visible(
                page,
                (
                    "ytd-backstage-post-dialog-renderer #select-link",
                    "ytd-backstage-post-dialog-renderer #dropzone",
                    "ytd-backstage-post-dialog-renderer a:has-text('select')",
                    "ytd-backstage-post-dialog-renderer a:has-text('chọn')",
                ),
            )
            if secondary_image_control:
                upload_transfer = _activate_file_upload(
                    page,
                    trigger=secondary_image_control,
                    file_path=image_path,
                    media_kind="image",
                    exclusive=True,
                    chooser_timeout_ms=10000,
                )
        if upload_transfer.get("status") != "file_set":
            return {
                "status": "BLOCKED_YOUTUBE_COMMUNITY_IMAGE_UPLOAD",
                "platform": "youtube",
                "composer_selector": composer_selector,
                "image_control_selector": image_control_selector,
                "secondary_image_control_selector": secondary_image_control_selector,
                "media_transfer": upload_transfer,
                "diagnostics": _youtube_community_surface_diagnostics(page),
            }
        preview = _wait_for_meaningful_visible_image(
            page,
            (
                "ytd-backstage-post-dialog img",
                "ytd-backstage-post-dialog-renderer #attachment-preview img",
                "ytd-backstage-post-dialog-renderer ytd-backstage-image-preview-renderer img",
                "ytd-backstage-post-dialog-renderer ytd-backstage-image-renderer img",
                "ytd-backstage-post-creation-renderer img",
                "#image-preview img",
                "ytd-backstage-image-renderer img",
            ),
            timeout_seconds=30,
        )
        if not preview:
            return {"status": "FAILED_YOUTUBE_COMMUNITY_IMAGE_PREVIEW_READBACK", "platform": "youtube", "media_transfer": upload_transfer}
        post_selector = _click_first_visible(
            page,
            (
                "ytd-backstage-post-dialog #submit-button button",
                "ytd-backstage-post-dialog-renderer #post-button button",
                "ytd-backstage-post-dialog-renderer #post-button",
                "ytd-backstage-post-dialog button:has-text('Post')",
                "ytd-backstage-post-dialog button:has-text('Đăng')",
                "ytd-backstage-post-creation-renderer #submit-button button",
                "ytd-backstage-post-creation-renderer button:has-text('Post')",
                "ytd-backstage-post-creation-renderer button:has-text('Đăng')",
                "yt-posts-creation-options-editor-view-model button:has-text('Post')",
                "yt-posts-creation-options-editor-view-model button:has-text('Đăng')",
                "button:has-text('Post')",
                "button:has-text('Đăng')",
                "yt-button-shape:has-text('Post')",
                "yt-button-shape:has-text('Đăng')",
            ),
        )
        if not post_selector:
            screenshot = None
            if public_screenshot_path:
                target = Path(public_screenshot_path)
                target.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(target), full_page=False)
                screenshot = str(target)
            return {
                "status": "BLOCKED_YOUTUBE_COMMUNITY_POST_CONTROL_NOT_FOUND",
                "platform": "youtube",
                "media_transfer": upload_transfer,
                "media_preview": preview,
                "diagnostics": _youtube_community_surface_diagnostics(page),
                "public_screenshot_path": screenshot,
            }
        deadline = time.monotonic() + 35
        public_url = None
        feed_refreshed = False
        while time.monotonic() < deadline and not public_url:
            card = _youtube_community_card_for_text(page, text)
            public_url = _youtube_community_permalink_from_card(card) if card else None
            if not public_url:
                if not feed_refreshed and time.monotonic() + 20 >= deadline:
                    page.goto(
                        channel_url,
                        wait_until="domcontentloaded",
                        timeout=45000,
                    )
                    time.sleep(4)
                    feed_refreshed = True
                    continue
                time.sleep(1)
        if not public_url:
            return {
                "status": "FAILED_YOUTUBE_COMMUNITY_POST_URL_READBACK",
                "platform": "youtube",
                "action": "community_post",
                "media_transfer": upload_transfer,
                "media_preview": preview,
                "payload_sha256": _sha256(text),
            }

    readback = readback_youtube_community_post_via_edge(
        cdp_port=cdp_port,
        public_url=public_url,
        expected_text=text,
        canonical_url=canonical_url,
        expected_handle=expected_handle,
        public_screenshot_path=public_screenshot_path,
    )
    verified = readback.get("status") == "SUCCESS"
    return {
        "status": "SUCCESS" if verified else "FAILED_YOUTUBE_COMMUNITY_POST_READBACK",
        "platform": "youtube",
        "action": "community_post",
        "post_id": _youtube_community_post_id(public_url),
        "public_url": public_url,
        "destination_identity": expected_handle,
        "media_transfer": upload_transfer,
        "media_preview": preview,
        "provider_readback_verified": verified,
        "readback": readback,
        "payload_sha256": _sha256(text),
        "video_or_short_created": False,
    }


def _youtube_video_id_from_value(value: str | None) -> str | None:
    raw = str(value or "")
    for pattern in (
        r"/video/([A-Za-z0-9_-]{11})",
        r"youtu\.be/([A-Za-z0-9_-]{11})",
        r"[?&]v=([A-Za-z0-9_-]{11})",
        r"/shorts/([A-Za-z0-9_-]{11})",
    ):
        match = re.search(pattern, raw)
        if match:
            return match.group(1)
    return None


def _youtube_video_id_readback(page: Any) -> str | None:
    candidates = [page.url]
    for selector, attribute in (
        ("a[href*='youtu.be/']", "href"),
        ("a[href*='youtube.com/watch']", "href"),
        ("a[href*='/shorts/']", "href"),
        ("input[value*='youtu.be/']", "value"),
        ("input[value*='youtube.com/watch']", "value"),
    ):
        try:
            for locator in page.locator(selector).all():
                value = locator.get_attribute(attribute)
                if value:
                    candidates.append(value)
        except Exception:
            continue
    for candidate in candidates:
        video_id = _youtube_video_id_from_value(candidate)
        if video_id:
            return video_id
    return None


def publish_youtube_short_via_edge(
    *,
    cdp_port: int,
    video_path: str | Path,
    title: str,
    description: str,
    public_screenshot_path: str | Path | None = None,
) -> dict[str, Any]:
    """Upload and publish a vertical source-chart sequence as a public YouTube Short."""
    with canonical_edge_page(cdp_port) as page:
        try:
            page.goto("https://studio.youtube.com/", wait_until="domcontentloaded", timeout=45000)
        except Exception as exc:
            if "studio.youtube.com" not in page.url:
                return {"status": "BLOCKED_YOUTUBE_STUDIO_NAVIGATION", "platform": "youtube", "error_class": type(exc).__name__}
        time.sleep(3)
        if _first_visible(page, ("a:has-text('Sign in')", "text=Sign in"))[0]:
            return {"status": "BLOCKED_YOUTUBE_LOGIN_REQUIRED", "platform": "youtube"}
        create_selector = _click_first_visible(page, ("#create-icon", "ytcp-button[aria-label*='Create']", "ytcp-button[aria-label*='Tạo']", "button[aria-label*='Create']", "button[aria-label*='Tạo']", "button:has-text('Create')", "button:has-text('Tạo')"))
        if not create_selector:
            return {"status": "BLOCKED_YOUTUBE_CREATE_CONTROL_NOT_FOUND", "platform": "youtube"}
        time.sleep(0.7)
        upload_item_selector = _click_first_visible(
            page,
            (
                "tp-yt-paper-item:has-text('Tải video lên')",
                "[role='menuitem']:has-text('Tải video lên')",
                "tp-yt-paper-item:has-text('Upload videos')",
                "[role='menuitem']:has-text('Upload videos')",
            ),
        )
        if not upload_item_selector:
            return {"status": "BLOCKED_YOUTUBE_UPLOAD_MENU_ITEM_NOT_FOUND", "platform": "youtube", "create_selector": create_selector}
        time.sleep(1)
        select_files, select_files_selector = _first_visible(
            page,
            (
                "ytcp-button#select-files-button",
                "#select-files-button",
                "button:has-text('SELECT FILES')",
                "button:has-text('Select files')",
                "button:has-text('CHỌN TỆP')",
                "button:has-text('Chọn tệp')",
                "ytcp-button:has-text('CHỌN TỆP')",
                "ytcp-button:has-text('Chọn tệp')",
            ),
        )
        if not select_files:
            return {
                "status": "BLOCKED_YOUTUBE_SELECT_FILES_CONTROL_NOT_FOUND",
                "platform": "youtube",
                "create_selector": create_selector,
                "upload_item_selector": upload_item_selector,
            }
        upload_transfer = _activate_file_upload(
            page,
            trigger=select_files,
            file_path=video_path,
            media_kind="video",
            exclusive=False,
            chooser_timeout_ms=10000,
        )
        upload_selector = str(upload_transfer.get("upload_transport") or "")
        if upload_transfer.get("status") != "file_set":
            return {
                "status": "BLOCKED_YOUTUBE_UPLOAD_INPUT_NOT_FOUND",
                "platform": "youtube",
                "create_selector": create_selector,
                "upload_item_selector": upload_item_selector,
                "select_files_selector": select_files_selector,
                "upload_transfer": upload_transfer,
            }
        deadline = time.monotonic() + 40
        title_box = None
        while time.monotonic() < deadline and not title_box:
            title_box, _title_selector = _first_visible(page, ("#title-textarea #textbox", "ytcp-mention-textbox#title-textarea #textbox", "[aria-label*='Add a title']", "[aria-label*='Tiêu đề']"))
            if not title_box:
                time.sleep(1)
        if not title_box:
            return {"status": "BLOCKED_YOUTUBE_DETAILS_EDITOR_NOT_FOUND", "platform": "youtube", "upload_selector": upload_selector}
        title_box.click()
        page.keyboard.press("Control+A")
        page.keyboard.type(title[:100], delay=0)
        description_box, _description_selector = _first_visible(page, ("#description-textarea #textbox", "ytcp-mention-textbox#description-textarea #textbox", "[aria-label*='Tell viewers about your video']", "[aria-label*='Mô tả']"))
        if description_box:
            description_box.click()
            page.keyboard.type(description[:4900], delay=0)
        _click_first_visible(page, ("tp-yt-paper-radio-button[name='VIDEO_MADE_FOR_KIDS_NOT_MFK']", "text=No, it's not made for kids", "text=Không, video này không dành cho trẻ em"))
        for _ in range(3):
            selector = _click_first_visible(page, ("#next-button", "ytcp-button#next-button", "button:has-text('Next')", "button:has-text('Tiếp')"))
            if not selector:
                break
            time.sleep(2)
        visibility_selector = _click_first_visible(page, ("tp-yt-paper-radio-button[name='PUBLIC']", "text=Public", "text=Công khai"))
        if not visibility_selector:
            return {"status": "BLOCKED_YOUTUBE_PUBLIC_VISIBILITY_CONTROL_NOT_FOUND", "platform": "youtube", "upload_selector": upload_selector}
        done_selector = _click_first_visible(page, ("#done-button", "ytcp-button#done-button", "button:has-text('Publish')", "button:has-text('Save')", "button:has-text('Xuất bản')", "button:has-text('Lưu')"))
        if not done_selector:
            return {"status": "BLOCKED_YOUTUBE_PUBLISH_CONTROL_NOT_FOUND", "platform": "youtube", "upload_selector": upload_selector}
        deadline = time.monotonic() + 35
        video_id = _youtube_video_id_readback(page)
        while time.monotonic() < deadline and not video_id:
            time.sleep(1)
            video_id = _youtube_video_id_readback(page)
        if not video_id:
            return {"status": "FAILED_YOUTUBE_PUBLIC_URL_READBACK", "platform": "youtube", "upload_selector": upload_selector, "upload_transfer": upload_transfer, "payload_sha256": _sha256(title + "\n" + description)}
        public_url = f"https://www.youtube.com/watch?v={video_id}"
        screenshot = None
        public_title_readback = False
        if public_screenshot_path:
            page.goto(public_url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(5)
            try:
                public_title = page.locator("meta[property='og:title']").first.get_attribute("content") or page.title()
                public_title_readback = title[:60].casefold() in str(public_title or "").casefold()
            except Exception:
                public_title_readback = False
            target = Path(public_screenshot_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(target), full_page=False)
            screenshot = str(target)
        return {"status": "SUCCESS", "platform": "youtube", "action": "public_short", "video_id": video_id, "public_url": public_url, "upload_selector": upload_selector, "upload_transfer": upload_transfer, "public_screenshot_path": screenshot, "public_title_readback": public_title_readback, "payload_sha256": _sha256(title + "\n" + description)}
