"""Bounded read-only Substack first-party post-performance observation.

This module intentionally uses only the visible publisher dashboard DOM through the canonical
Edge ``contentops-social-main`` profile on CDP 9223.  It never reads browser storage, cookies,
request/response headers, session databases, or hidden/private APIs.  Every invocation opens one
task-owned tab for one exact reconciled post identity and closes that tab before returning.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping
from urllib.parse import urlsplit

from live_contentops.browser_interaction_budget_v1 import record_browser_interaction_event
from live_contentops.publishing_profile_registry_v1 import assert_canonical_edge_cdp


SCHEMA_VERSION = "contentops.substack_performance_observer.v1"
SOURCE_IDENTITY = "substack.first_party_post_stats.visible_dom.v1"
PUBLISHING_CDP_PORT = 9223

NATIVE_METRIC_DEFINITIONS: dict[str, str] = {
    "total_views": "Substack total views across web, email, and the Substack app.",
    "free_subscriptions": "Free subscriptions attributed by Substack to the exact post.",
    "paid_subscriptions": "Paid subscriptions attributed by Substack to the exact post.",
    "recipients": "Unique subscribers sent the post by email or push notification.",
    "open_rate": "Substack unique-recipient post open rate.",
    "delivery_rate": "Substack unique-recipient post delivery rate.",
    "likes": "Substack likes on the exact post.",
    "comments": "Substack comments on the exact post.",
    "shares": "Substack shares of the exact post.",
    "restacks": "Substack restacks of the exact post.",
}

_LABELS: dict[str, tuple[str, ...]] = {
    "total_views": ("total views", "views"),
    "free_subscriptions": ("free subscriptions", "free subscription", "new free subscribers"),
    "paid_subscriptions": ("paid subscriptions", "paid subscription", "new paid subscribers"),
    "recipients": ("recipients",),
    "open_rate": ("open rate",),
    "delivery_rate": ("delivery rate",),
    "likes": ("likes",),
    "comments": ("comments",),
    "shares": ("shares",),
    "restacks": ("restacks",),
}

_AUTH_MARKERS = (
    "sign in to substack",
    "sign in with email",
    "log in to substack",
)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _canonical_public_url(value: Any) -> str | None:
    try:
        parsed = urlsplit(str(value or "").strip())
    except ValueError:
        return None
    path = parsed.path.rstrip("/")
    if not (
        parsed.scheme == "https"
        and (parsed.hostname or "").casefold() == "capitalchronicle.substack.com"
        and path.startswith("/p/")
        and len(path.removeprefix("/p/")) > 0
        and not parsed.username
        and not parsed.password
    ):
        return None
    return f"https://capitalchronicle.substack.com{path}"


def _parse_native_number(value: str, *, percentage: bool = False) -> int | float | None:
    text = str(value or "").strip().casefold().replace("\u00a0", " ")
    if not text or text in {"-", "--", "n/a", "not available"}:
        return None
    compact = re.sub(r"\s+", "", text).replace(",", "")
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)([kmb])?(%)?", compact)
    if not match:
        return None
    number = float(match.group(1))
    multiplier = {None: 1.0, "k": 1_000.0, "m": 1_000_000.0, "b": 1_000_000_000.0}[
        match.group(2)
    ]
    number *= multiplier
    is_percentage = percentage or bool(match.group(3))
    if is_percentage:
        if not match.group(3):
            return None
        return round(number / 100.0, 6)
    rounded = round(number)
    return int(rounded) if abs(number - rounded) < 1e-9 else number


def parse_substack_post_stats_visible_text(visible_text: str) -> dict[str, Any]:
    """Extract only explicitly labelled native values from bounded visible dashboard text."""
    lines = [re.sub(r"\s+", " ", line).strip() for line in str(visible_text or "").splitlines()]
    lines = [line for line in lines if line]
    folded = [line.casefold().rstrip(":") for line in lines]
    metrics: dict[str, int | float] = {}
    availability = {name: "NOT_EXPOSED" for name in NATIVE_METRIC_DEFINITIONS}

    def candidates(index: int, label: str) -> list[str]:
        row = lines[index]
        escaped = re.escape(label)
        inline_after = re.match(rf"^\s*{escaped}\s*[:\-]?\s+(.+?)\s*$", row, re.IGNORECASE)
        inline_before = re.match(rf"^\s*(.+?)\s+{escaped}\s*$", row, re.IGNORECASE)
        values: list[str] = []
        if inline_after:
            values.append(inline_after.group(1))
        if inline_before:
            values.append(inline_before.group(1))
        if folded[index] == label:
            if index + 1 < len(lines):
                values.append(lines[index + 1])
            if index > 0:
                values.append(lines[index - 1])
        return values

    for metric, labels in _LABELS.items():
        percentage = metric in {"open_rate", "delivery_rate"}
        for label in labels:
            for index, row in enumerate(folded):
                if label not in row:
                    continue
                for raw in candidates(index, label):
                    parsed = _parse_native_number(raw, percentage=percentage)
                    if parsed is not None:
                        metrics[metric] = parsed
                        availability[metric] = "AVAILABLE"
                        break
                if metric in metrics:
                    break
            if metric in metrics:
                break

    # Explicit normalized qualified-signal mappings. Views, recipients, opens, delivery, and likes
    # intentionally remain native-only and never become qualified engagement.
    if availability["comments"] == "AVAILABLE":
        availability["comments"] = "AVAILABLE"
    if availability["shares"] == "AVAILABLE":
        availability["shares"] = "AVAILABLE"
    if availability["restacks"] == "AVAILABLE":
        metrics["reposts"] = metrics["restacks"]
        availability["reposts"] = "AVAILABLE"
    else:
        availability["reposts"] = "NOT_EXPOSED"
    if (
        availability["free_subscriptions"] == "AVAILABLE"
        and availability["paid_subscriptions"] == "AVAILABLE"
    ):
        metrics["subscriber_conversions"] = int(metrics["free_subscriptions"]) + int(
            metrics["paid_subscriptions"]
        )
        availability["subscriber_conversions"] = "AVAILABLE"
    else:
        availability["subscriber_conversions"] = "NOT_EXPOSED"
    availability["meaningful_reads"] = "NOT_EXPOSED"
    availability["completion_rate"] = "NOT_EXPOSED"
    return {"metrics": metrics, "availability": availability}


def _unavailable_result(status: str, availability_state: str, limitation: str) -> dict[str, Any]:
    availability = {
        **{name: availability_state for name in NATIVE_METRIC_DEFINITIONS},
        "reposts": availability_state,
        "subscriber_conversions": availability_state,
        "meaningful_reads": availability_state,
        "completion_rate": availability_state,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "metrics": {},
        "availability": availability,
        "source_identity": SOURCE_IDENTITY,
        "collection_method": "EDGE_CDP_9223_VISIBLE_FIRST_PARTY_DOM_READ_ONLY",
        "source_evidence_hash": None,
        "limitations": [limitation],
        "browser_write_performed": False,
    }


def _start_playwright() -> Any:
    from playwright.sync_api import sync_playwright

    return sync_playwright().start()


def collect_substack_post_metrics_via_edge(
    *,
    cdp_port: int,
    public_object_id: str,
    canonical_public_url: str,
) -> Mapping[str, Any]:
    """Collect one exact post's visible first-party metrics in a task-owned read-only tab."""
    if int(cdp_port) != PUBLISHING_CDP_PORT:
        return _unavailable_result("UNSUPPORTED", "UNSUPPORTED", "canonical_edge_9223_required")
    try:
        assert_canonical_edge_cdp(cdp_port)
    except Exception as exc:
        return _unavailable_result(
            "AUTH_REQUIRED", "AUTH_REQUIRED", f"canonical_edge_unavailable:{type(exc).__name__}"
        )
    object_id = str(public_object_id or "").strip()
    public_url = _canonical_public_url(canonical_public_url)
    if not object_id.isdigit() or public_url is None:
        return _unavailable_result(
            "IDENTITY_MISMATCH", "UNAVAILABLE", "exact_substack_object_or_canonical_url_invalid"
        )

    try:
        playwright = _start_playwright()
    except Exception as exc:
        return _unavailable_result(
            "UNSUPPORTED", "UNSUPPORTED", f"playwright_unavailable:{type(exc).__name__}"
        )
    page = None
    try:
        try:
            browser = playwright.chromium.connect_over_cdp(
                f"http://127.0.0.1:{PUBLISHING_CDP_PORT}", timeout=15_000
            )
        except Exception as exc:
            return _unavailable_result(
                "AUTH_REQUIRED", "AUTH_REQUIRED", f"canonical_edge_attach_failed:{type(exc).__name__}"
            )
        if not browser.contexts:
            return _unavailable_result(
                "AUTH_REQUIRED", "AUTH_REQUIRED", "canonical_edge_has_no_browser_context"
            )
        page = browser.contexts[0].new_page()
        record_browser_interaction_event(
            "tab_created", reason="DUE_SUBSTACK_PERFORMANCE_OBSERVATION", destination="substack"
        )
        detail_url = (
            "https://capitalchronicle.substack.com/publish/posts/detail/" + object_id
        )
        record_browser_interaction_event(
            "navigation", reason="DUE_SUBSTACK_PERFORMANCE_OBSERVATION", destination="substack"
        )
        page.goto(detail_url, wait_until="domcontentloaded", timeout=45_000)
        page.wait_for_timeout(3_000)
        current = urlsplit(str(page.url or ""))
        if (current.hostname or "").casefold() not in {
            "capitalchronicle.substack.com", "substack.com", "www.substack.com"
        }:
            return _unavailable_result(
                "IDENTITY_MISMATCH", "UNAVAILABLE", "unexpected_first_party_dashboard_host"
            )
        visible_text = str(page.locator("body").inner_text(timeout=10_000) or "")
        folded = visible_text.casefold()
        if any(marker in folded for marker in _AUTH_MARKERS) or "/sign-in" in current.path:
            return _unavailable_result(
                "AUTH_REQUIRED", "AUTH_REQUIRED", "substack_publisher_authentication_required"
            )

        hrefs = page.locator("a[href*='/p/']").evaluate_all(
            "els => els.map(el => el.href).filter(Boolean)"
        )
        bound_urls = {
            normalized for normalized in (_canonical_public_url(value) for value in (hrefs or []))
            if normalized is not None
        }
        exact_first_party_object_route = current.path.rstrip("/") in {
            f"/publish/posts/detail/{object_id}",
            f"/publish/post/{object_id}",
        }
        # The coordinator has already bound this numeric object to the exact reconciled canonical
        # URL and its stored SHA-256.  Substack's first-party detail page does not always render a
        # public permalink anchor; an exact numeric detail/editor route is therefore equivalent
        # destination-local object evidence.  Any redirect that loses that numeric identity still
        # fails closed unless the exact canonical URL is visibly present.
        if not exact_first_party_object_route and public_url not in bound_urls:
            return _unavailable_result(
                "IDENTITY_MISMATCH", "UNAVAILABLE", "canonical_public_url_not_bound_on_exact_post_detail"
            )

        parsed = parse_substack_post_stats_visible_text(visible_text)
        evidence_hash = _hash({
            "public_object_id": object_id,
            "canonical_public_url_hash": hashlib.sha256(public_url.encode("utf-8")).hexdigest(),
            "visible_text": visible_text,
        })
        available = any(state == "AVAILABLE" for state in parsed["availability"].values())
        limitations = [
            metric for metric, state in parsed["availability"].items() if state != "AVAILABLE"
        ]
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "COLLECTED" if available else "NOT_EXPOSED",
            "metrics": parsed["metrics"],
            "availability": parsed["availability"],
            "source_identity": f"{SOURCE_IDENTITY}#sha256:{evidence_hash}",
            "collection_method": "EDGE_CDP_9223_VISIBLE_FIRST_PARTY_DOM_READ_ONLY",
            "source_evidence_hash": evidence_hash,
            "limitations": limitations,
            "browser_write_performed": False,
        }
    finally:
        if page is not None:
            try:
                page.close()
                record_browser_interaction_event(
                    "tab_closed", reason="DUE_SUBSTACK_PERFORMANCE_OBSERVATION", destination="substack"
                )
            except Exception:
                pass
        playwright.stop()
