"""Bounded canonical X-list intake capture over the locked CapitalChronicleBot CDP 9222 session.

This module reuses the EXISTING accepted `headline_ingestion/Data_Ingestion.py` extraction,
archiving, and dedupe machinery (no second ingestion system). It performs one time-boxed
capture: attach over CDP, ensure the canonical X list route is active, intercept
`ListLatestTweetsTimeline` responses, and append only NEW (deduplicated) headline rows to the
canonical sidecar/ALL_DATA files under `headline_ingestion/data`.

Safety boundary:

- read-only interception of visible network payloads; never reads cookies, localStorage,
  sessionStorage, tokens, or browser DBs;
- never closes, resets, or navigates away the operator's browser; the CDP client only
  attaches and detaches;
- login-redirect observation uses visible URLs only and reports REAUTH_REQUIRED truthfully;
- bounded by wall clock and empty-scroll count; it is a one-shot capture, never a daemon.
"""
from __future__ import annotations

import importlib.util
import json
import time
from pathlib import Path
from typing import Any, Mapping, Optional

from live_contentops.headline_data_root_v1 import canonical_headline_data_root
from live_contentops.browser_interaction_budget_v1 import record_browser_interaction_event

REPO_ROOT = Path(__file__).resolve().parent.parent
HEADLINE_INGESTION_DIR = REPO_ROOT / "headline_ingestion"
DATA_INGESTION_MODULE_PATH = HEADLINE_INGESTION_DIR / "Data_Ingestion.py"
TARGET_LIST_ID = "1843870469143048642"
TARGET_LIST_URL = "https://x.com/i/lists/1843870469143048642"
TIMELINE_RESPONSE_MARKER = "ListLatestTweetsTimeline"
CDP_URL_DEFAULT = "http://127.0.0.1:9222"
MAX_CAPTURE_SECONDS_DEFAULT = 120.0
MAX_EMPTY_SCROLLS_DEFAULT = 3
RELOAD_SETTLE_MS = 4000
SCROLL_WAIT_MS = 4200

CAPTURE_STATE_CAPTURED = "CAPTURED"
CAPTURE_STATE_REAUTH_REQUIRED = "REAUTH_REQUIRED"
CAPTURE_STATE_CDP_UNAVAILABLE = "CDP_UNAVAILABLE"
CAPTURE_STATE_NO_CONTEXT = "CAPTURE_FAILED_NO_BROWSER_CONTEXT"
CAPTURE_STATE_NO_NEW_DATA = "CAPTURED_NO_NEW_HEADLINES"
CAPTURE_STATE_FAILED = "CAPTURE_FAILED"

FAILURE_CDP_BROWSER_UNAVAILABLE = "CDP_BROWSER_UNAVAILABLE"
FAILURE_BROWSER_CONTEXT_UNAVAILABLE = "BROWSER_CONTEXT_UNAVAILABLE"
FAILURE_PAGE_LIST_NOT_READY = "PAGE_LIST_NOT_READY"
FAILURE_NAVIGATION_TARGET_LOST = "NAVIGATION_TARGET_LOST"
FAILURE_PLAYWRIGHT_TRANSPORT = "PLAYWRIGHT_TRANSPORT_FAILURE"
FAILURE_NAVIGATION = "NAVIGATION_FAILURE"
FAILURE_EXTRACTION = "EXTRACTION_FAILURE"
FAILURE_TIMEOUT = "CAPTURE_TIMEOUT"
FAILURE_MALFORMED_RESPONSE = "MALFORMED_EMPTY_CAPTURE_RESPONSE"
FAILURE_LOCAL_FILESYSTEM = "LOCAL_FILESYSTEM_FAILURE"
FAILURE_OTHER = "OTHER_CAPTURE_FAILURE"

LOGIN_REDIRECT_MARKERS = (
    "/i/jf/onboarding",
    "redirect_after_login",
    "mode=login",
    "x.com/i/flow/login",
    "/login?",
)


class IngestCaptureError(RuntimeError):
    pass


def _safe_exception_type(exc: BaseException) -> str:
    value = "".join(character for character in type(exc).__name__ if character.isalnum() or character == "_")
    return value[:40] or "Exception"


def classify_capture_exception(exc: BaseException, *, phase: str) -> tuple[str, str]:
    """Classify an exception without returning its raw message or any browser/session data."""

    exception_type = _safe_exception_type(exc)
    text = str(exc).casefold()
    phase_label = str(phase or "UNKNOWN").upper()
    if "timeout" in exception_type.casefold() or "timeout" in text:
        return FAILURE_TIMEOUT, f"{phase_label}_TIMEOUT:{exception_type}"
    if any(marker in text for marker in (
        "epipe", "broken pipe", "pipe closed", "connection closed", "driver closed",
        "playwright connection", "transport closed",
    )):
        return FAILURE_PLAYWRIGHT_TRANSPORT, f"{phase_label}_TRANSPORT_CLOSED:{exception_type}"
    if any(marker in text for marker in (
        "target page, context or browser has been closed", "target closed", "page has been closed",
        "browser has been closed", "context has been closed",
    )):
        return FAILURE_NAVIGATION_TARGET_LOST, f"{phase_label}_TARGET_CLOSED:{exception_type}"
    if isinstance(exc, OSError) and phase_label in {"LOAD_DATA_MODULE", "RESPONSE_EXTRACTION", "EXTRACTION_SCROLL"}:
        return FAILURE_LOCAL_FILESYSTEM, f"{phase_label}_FILESYSTEM_ERROR:{exception_type}"
    if isinstance(exc, (json.JSONDecodeError, ValueError)) and phase_label == "RESPONSE_EXTRACTION":
        return FAILURE_MALFORMED_RESPONSE, f"TIMELINE_RESPONSE_DECODE_FAILED:{exception_type}"
    if phase_label in {"TARGET_ACQUISITION", "NAVIGATION", "RELOAD"}:
        return FAILURE_NAVIGATION, f"{phase_label}_FAILED:{exception_type}"
    if phase_label in {"RESPONSE_EXTRACTION", "EXTRACTION_SCROLL"}:
        return FAILURE_EXTRACTION, f"{phase_label}_FAILED:{exception_type}"
    return FAILURE_OTHER, f"{phase_label}_FAILED:{exception_type}"


def load_data_ingestion_module() -> Any:
    """Import the existing accepted ingestion module with canonically pinned data directories."""
    if not DATA_INGESTION_MODULE_PATH.is_file():
        raise IngestCaptureError("headline_ingestion/Data_Ingestion.py missing")
    spec = importlib.util.spec_from_file_location(
        "contentops_headline_ingestion_data_ingestion", DATA_INGESTION_MODULE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    original_cwd = Path.cwd()
    try:
        import os

        os.chdir(HEADLINE_INGESTION_DIR)
        assert spec.loader is not None
        spec.loader.exec_module(module)
    finally:
        import os

        os.chdir(original_cwd)
    data_dir = canonical_headline_data_root()
    data_dir.mkdir(parents=True, exist_ok=True)
    module.DATA_DIR = str(data_dir)
    module.STATE_DIR = str(data_dir / "state" / "current")
    module.SIDECAR_DIR = str(data_dir / "intake" / "headline_sidecars")
    module.RAW_ARCHIVE_DIR = str(data_dir / "raw_archive" / "headline_cdp")
    return module


def count_all_data_rows(module: Any) -> int:
    path = Path(module.DATA_DIR) / "capital_chronicle_ALL_DATA.json"
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return len(data) if isinstance(data, list) else 0
    except (FileNotFoundError, ValueError, OSError):
        return 0


def count_sidecar_rows(module: Any) -> int:
    sidecar_dir = Path(module.SIDECAR_DIR)
    total = 0
    if not sidecar_dir.is_dir():
        return 0
    for sidecar_path in sorted(sidecar_dir.glob("*.jsonl")):
        try:
            with open(sidecar_path, "r", encoding="utf-8") as handle:
                total += sum(1 for line in handle if line.strip())
        except OSError:
            continue
    return total


def _existing_dedup_keys(module: Any) -> set:
    sidecar_dir = Path(module.SIDECAR_DIR)
    keys: set = set()
    if not sidecar_dir.is_dir():
        return keys
    for sidecar_path in sorted(sidecar_dir.glob("*.jsonl")):
        try:
            with open(sidecar_path, "r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        row = json.loads(line)
                    except ValueError:
                        continue
                    key = row.get("dedup_key") or str(row.get("headline_id") or "")
                    if key:
                        keys.add(str(key))
        except OSError:
            continue
    return keys


def append_deduped_sidecar_rows(
    module: Any,
    tweets: list,
    raw_payload_metadata: Mapping[str, Any] | None = None,
    appended_row_summaries: list[dict[str, Any]] | None = None,
) -> int:
    """Append ONLY new headlines to the canonical single-folder per-day sidecar files.

    Headline-file consistency invariant (owner decision 2026-08-10): one folder
    (the stable runtime root's `intake/headline_sidecars`), one file per day with the fixed
    `step1_headline_sidecar_<YYYY>_<MM>_<DD>.jsonl` name format, and zero duplicate headlines
    across captures. No other headline file families are created by this capture path.
    """
    if not tweets:
        return 0
    existing = _existing_dedup_keys(module)
    context = module.build_headline_sidecar_context()
    raw_meta = dict(raw_payload_metadata) if raw_payload_metadata else {
        "raw_payload_ref": None,
        "raw_payload_sha256": None,
        "raw_payload_byte_size": None,
        "source_url_or_ref": "bounded_run_now_capture_without_raw_payload",
    }
    Path(module.SIDECAR_DIR).mkdir(parents=True, exist_ok=True)
    captured_at_utc = module._utc_now_iso()
    rows_by_path: dict = {}
    for tweet in tweets:
        text = module._tweet_text(tweet)
        if not text:
            continue
        metadata = module._tweet_sidecar_metadata(tweet)
        dedup_key = str(metadata.get("dedup_key") or "")
        if dedup_key and dedup_key in existing:
            continue
        if dedup_key:
            existing.add(dedup_key)
        timestamp = module._tweet_timestamp(tweet)
        row = {
            "schema_version": "step1_headline_catalyst_sidecar_v1",
            "headline_id": module._headline_id(timestamp, text),
            "headline_text": text,
            "headline_timestamp": timestamp,
            "source_platform": "x_cdp_list_latest_tweets_timeline",
            "captured_at_utc": captured_at_utc,
            **raw_meta,
            **metadata,
            **context,
        }
        rows_by_path.setdefault(module._sidecar_path_for_timestamp(timestamp), []).append(row)
    written = 0
    for sidecar_path, rows in rows_by_path.items():
        with open(sidecar_path, "a", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
                written += 1
                if appended_row_summaries is not None:
                    appended_row_summaries.append({
                        "headline_id": str(row.get("headline_id") or ""),
                        "dedup_key": str(row.get("dedup_key") or ""),
                        "headline_timestamp": str(row.get("headline_timestamp") or ""),
                        "source_platform": str(row.get("source_platform") or ""),
                    })
    return written


def _visible_url_is_login_redirect(url: str) -> bool:
    return any(marker in str(url or "") for marker in LOGIN_REDIRECT_MARKERS)


def probe_session_visible_state(
    *,
    cdp_url: str = CDP_URL_DEFAULT,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    """Cheap visible-URL session probe over CDP /json/list. Never opens tabs, never reads
    cookies/storage; only classifies visible target URLs. INCONCLUSIVE means no X target is
    open to classify; callers may proceed (capture opens the canonical route itself)."""
    import json as _json
    import urllib.request as _urllib_request

    try:
        with _urllib_request.urlopen(f"{cdp_url}/json/list", timeout=min(timeout_seconds, 15.0)) as response:
            targets = _json.loads(response.read().decode("utf-8"))
    except Exception:  # noqa: BLE001
        return {"session_state": "CDP_UNAVAILABLE", "detail": "cdp_list_unreachable"}
    x_urls = [
        str(row.get("url") or "")
        for row in (targets if isinstance(targets, list) else [])
        if isinstance(row, dict) and ("x.com" in str(row.get("url") or "") or "twitter.com" in str(row.get("url") or ""))
    ]
    if not x_urls:
        return {"session_state": "INCONCLUSIVE", "detail": "no_x_target_open"}
    for url in x_urls:
        if _visible_url_is_login_redirect(url):
            return {"session_state": "REAUTH_REQUIRED", "detail": "LOGIN_REDIRECT_OBSERVED"}
    if any(TARGET_LIST_ID in url for url in x_urls):
        return {"session_state": "READY", "detail": "CANONICAL_LIST_ROUTE_ACTIVE_NO_LOGIN_REDIRECT"}
    return {"session_state": "INCONCLUSIVE", "detail": "x_target_open_not_canonical_route"}


def select_reusable_x_page(context: Any) -> Any | None:
    """Prefer the exact locked list tab, then another existing X tab; never create here."""

    return next(
        (candidate for candidate in context.pages if TARGET_LIST_ID in str(candidate.url or "")),
        None,
    ) or next(
        (
            candidate for candidate in context.pages
            if "x.com" in str(candidate.url or "") or "twitter.com" in str(candidate.url or "")
        ),
        None,
    )


def run_bounded_x_list_capture(
    *,
    max_seconds: float = MAX_CAPTURE_SECONDS_DEFAULT,
    max_empty_scrolls: int = MAX_EMPTY_SCROLLS_DEFAULT,
    cdp_url: str = CDP_URL_DEFAULT,
    playwright: Any = None,
) -> dict[str, Any]:
    """One bounded capture. Returns a nonsecret summary; never closes the operator browser."""
    from playwright.sync_api import sync_playwright

    started = time.monotonic()
    result: dict[str, Any] = {
        "capture_state": CAPTURE_STATE_FAILED,
        "target_list_id": TARGET_LIST_ID,
        "timeline_responses_observed": 0,
        "new_headlines": 0,
        "sidecar_rows_before": 0,
        "sidecar_rows_after": 0,
        "duration_seconds": 0.0,
        "login_automation": False,
        "browser_closed": False,
        "tab_created": False,
        "tab_closed": False,
        "navigation_count": 0,
        "detail": None,
        "capture_phase": "LOAD_DATA_MODULE",
        "timeline_responses_seen": 0,
        "failure_class": None,
        "failure_detail": None,
    }
    try:
        module = load_data_ingestion_module()
    except Exception as exc:  # noqa: BLE001
        failure_class, failure_detail = classify_capture_exception(exc, phase="LOAD_DATA_MODULE")
        result.update({
            "failure_class": failure_class,
            "failure_detail": failure_detail,
            "detail": failure_detail,
            "duration_seconds": round(time.monotonic() - started, 2),
        })
        return result
    result["sidecar_rows_before"] = count_sidecar_rows(module)
    state = {
        "responses": 0,
        "responses_seen": 0,
        "appended_rows": [],
        "failure_class": None,
        "failure_detail": None,
    }

    def _on_response(response) -> None:
        if TIMELINE_RESPONSE_MARKER not in str(response.url or ""):
            return
        state["responses_seen"] += 1
        if response.status != 200:
            status_class = "HTTP_4XX" if 400 <= int(response.status) < 500 else (
                "HTTP_5XX" if 500 <= int(response.status) < 600 else "HTTP_NON_200"
            )
            state["failure_class"] = FAILURE_PAGE_LIST_NOT_READY
            state["failure_detail"] = f"TIMELINE_RESPONSE_{status_class}"
            return
        try:
            state["responses"] += 1
            payload = response.json()
            raw_metadata = module.archive_raw_payload(payload, response.url)
            tweets = module.recursive_tweet_extractor(payload)
            if tweets:
                append_deduped_sidecar_rows(
                    module, tweets, raw_metadata, state["appended_rows"]
                )
        except Exception as exc:  # noqa: BLE001 - retain only bounded sanitized classification
            failure_class, failure_detail = classify_capture_exception(
                exc, phase="RESPONSE_EXTRACTION"
            )
            state["failure_class"] = failure_class
            state["failure_detail"] = failure_detail

    context_manager = playwright if playwright is not None else sync_playwright()
    with context_manager as driver:
        result["capture_phase"] = "CDP_CONNECT"
        try:
            browser = driver.chromium.connect_over_cdp(cdp_url, timeout=10_000)
        except Exception as exc:  # noqa: BLE001
            _classified, failure_detail = classify_capture_exception(exc, phase="CDP_CONNECT")
            result["capture_state"] = CAPTURE_STATE_CDP_UNAVAILABLE
            result["failure_class"] = FAILURE_CDP_BROWSER_UNAVAILABLE
            result["failure_detail"] = failure_detail
            result["detail"] = failure_detail
            result["duration_seconds"] = round(time.monotonic() - started, 2)
            return result
        try:
            result["capture_phase"] = "BROWSER_CONTEXT"
            context = browser.contexts[0] if browser.contexts else None
            if context is None:
                result["capture_state"] = CAPTURE_STATE_NO_CONTEXT
                result["failure_class"] = FAILURE_BROWSER_CONTEXT_UNAVAILABLE
                result["failure_detail"] = "NO_BROWSER_CONTEXT_ON_CDP"
                result["detail"] = result["failure_detail"]
                return result
            # Prefer the exact locked list tab. Fall back to another existing X tab; only create
            # one page when no reusable X page exists at all.
            result["capture_phase"] = "TARGET_ACQUISITION"
            page = select_reusable_x_page(context)
            if page is None:
                page = context.new_page()
                result["tab_created"] = True
                record_browser_interaction_event(
                    "tab_created", reason="NO_REUSABLE_X_LIST_TAB", destination="x_ingestion"
                )
            page.on("response", _on_response)
            try:
                if TARGET_LIST_ID not in page.url:
                    result["capture_phase"] = "NAVIGATION"
                    result["navigation_count"] += 1
                    record_browser_interaction_event(
                        "navigation", reason="X_CANONICAL_LIST_ROUTE", destination="x_ingestion"
                    )
                    page.goto(TARGET_LIST_URL, timeout=30_000, wait_until="domcontentloaded")
                if _visible_url_is_login_redirect(page.url):
                    result["capture_state"] = CAPTURE_STATE_REAUTH_REQUIRED
                    result["detail"] = "LOGIN_REDIRECT_OBSERVED"
                    return result
                if TARGET_LIST_ID not in str(page.url or ""):
                    result["failure_class"] = FAILURE_PAGE_LIST_NOT_READY
                    result["failure_detail"] = "CANONICAL_LIST_ROUTE_NOT_ACTIVE_AFTER_NAVIGATION"
                    result["detail"] = result["failure_detail"]
                    return result
                result["capture_phase"] = "RELOAD"
                result["navigation_count"] += 1
                record_browser_interaction_event(
                    "navigation", reason="X_DUE_CAPTURE_RELOAD", destination="x_ingestion"
                )
                page.reload(timeout=30_000)
                page.wait_for_timeout(RELOAD_SETTLE_MS)
                empty_scrolls = 0
                while (
                    empty_scrolls < max_empty_scrolls
                    and (time.monotonic() - started) < max_seconds
                ):
                    result["capture_phase"] = "EXTRACTION_SCROLL"
                    before = count_sidecar_rows(module)
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(SCROLL_WAIT_MS)
                    after = count_sidecar_rows(module)
                    empty_scrolls = 0 if after > before else empty_scrolls + 1
                    if _visible_url_is_login_redirect(page.url):
                        result["capture_state"] = CAPTURE_STATE_REAUTH_REQUIRED
                        result["detail"] = "LOGIN_REDIRECT_OBSERVED"
                        return result
            finally:
                try:
                    page.remove_listener("response", _on_response)
                except Exception:  # noqa: BLE001
                    pass
        except Exception as exc:  # noqa: BLE001
            failure_class, failure_detail = classify_capture_exception(
                exc, phase=str(result.get("capture_phase") or "CAPTURE")
            )
            result["failure_class"] = failure_class
            result["failure_detail"] = failure_detail
            result["detail"] = failure_detail
        # NOTE: browser.close() is intentionally never called; the operator's browser stays
        # running. Detaching happens when the playwright driver context exits.
        result["timeline_responses_observed"] = state["responses"]
        result["timeline_responses_seen"] = state["responses_seen"]

    if state["failure_class"]:
        result["failure_class"] = state["failure_class"]
        result["failure_detail"] = state["failure_detail"]
        result["detail"] = state["failure_detail"]

    result["sidecar_rows_after"] = count_sidecar_rows(module)
    result["new_headlines"] = max(0, result["sidecar_rows_after"] - result["sidecar_rows_before"])
    result["new_headline_ids"] = sorted({
        str(row.get("headline_id") or "")
        for row in state["appended_rows"]
        if str(row.get("headline_id") or "")
    })
    result["new_headline_source_refs"] = sorted(
        (
            {
                "headline_id": str(row.get("headline_id") or ""),
                "dedup_key": str(row.get("dedup_key") or ""),
                "headline_timestamp": str(row.get("headline_timestamp") or ""),
                "source_platform": str(row.get("source_platform") or ""),
            }
            for row in state["appended_rows"]
            if str(row.get("headline_id") or "")
        ),
        key=lambda row: row["headline_id"],
    )
    result["duration_seconds"] = round(time.monotonic() - started, 2)
    if result["capture_state"] == CAPTURE_STATE_FAILED:
        if result["failure_class"]:
            return result
        if result["timeline_responses_observed"] > 0:
            result["capture_state"] = CAPTURE_STATE_CAPTURED if result["new_headlines"] > 0 else CAPTURE_STATE_NO_NEW_DATA
        else:
            result["failure_class"] = FAILURE_MALFORMED_RESPONSE
            result["failure_detail"] = "NO_TIMELINE_RESPONSE_OBSERVED_AFTER_RELOAD"
            result["detail"] = result["failure_detail"]
        return result
    if result["capture_state"] == CAPTURE_STATE_REAUTH_REQUIRED:
        return result
    result["capture_phase"] = "COMPLETE"
    result["capture_state"] = CAPTURE_STATE_CAPTURED if result["new_headlines"] > 0 else CAPTURE_STATE_NO_NEW_DATA
    return result
