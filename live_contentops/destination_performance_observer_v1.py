"""Bounded read-only destination observations over existing authorized bindings.

Each invocation performs at most one provider request for its exact destination/public object.
Missing scope, binding, or exposed data is reported truthfully and never coerced to zero.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Mapping

METRICS = (
    "impressions", "reach", "views", "likes", "reactions", "shares", "reposts",
    "comments", "replies", "canonical_article_clicks", "subscriber_conversions",
    "search_impressions", "search_clicks", "search_ctr", "search_query",
    "search_position", "interaction_quality",
    "reply_sample_count",
)


def _result(
    destination: str, status: str, *, metrics: Mapping[str, Any] | None = None,
    available: tuple[str, ...] = (), interactions: list[dict[str, Any]] | None = None,
    limitation: str,
    missing_metrics: tuple[str, ...] = (),
    provider_requests: int | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "contentops.destination_performance_observer.v1",
        "status": status,
        "metrics": dict(metrics or {}),
        "availability": {
            name: "AVAILABLE" if name in available else "NOT_EXPOSED" if name in missing_metrics else (
                status if status in {"AUTH_REQUIRED", "PERMISSION_REQUIRED", "NOT_EXPOSED"}
                else "UNSUPPORTED"
            )
            for name in METRICS
        },
        "interactions": list(interactions or []),
        "interaction_availability": (
            "AVAILABLE" if interactions else
            status if status in {"AUTH_REQUIRED", "PERMISSION_REQUIRED", "NOT_EXPOSED"}
            else "UNSUPPORTED"
        ),
        "source_identity": f"contentops.{destination}.current_authorized_read_only.v1",
        "limitations": [limitation],
        "provider_requests": (provider_requests if provider_requests is not None else
            0 if status in {"AUTH_REQUIRED", "PERMISSION_REQUIRED", "UNSUPPORTED", "NOT_EXPOSED"} else 1),
        "public_write_performed": False,
        "additional_scope_requested": False,
    }


def _get_json(url: str, params: Mapping[str, str]) -> dict[str, Any]:
    query = urllib.parse.urlencode(dict(params))
    request = urllib.request.Request(f"{url}?{query}", method="GET")
    request.add_header("User-Agent", "CapitalChronicleContentOps/1.0")
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _http_failure(destination: str, error: Exception) -> dict[str, Any]:
    if isinstance(error, urllib.error.HTTPError):
        status = "AUTH_REQUIRED" if error.code == 401 else (
            "PERMISSION_REQUIRED" if error.code == 403 else "UNAVAILABLE"
        )
        return _result(
            destination, status,
            limitation=f"read_only_provider_http_{error.code}",
            provider_requests=1,
        )
    return _result(
        destination, "UNAVAILABLE",
        limitation=f"read_only_provider_{type(error).__name__}",
        provider_requests=1,
    )


def _meta_token(*names: str) -> str:
    return next((str(os.environ.get(name) or "") for name in names if os.environ.get(name)), "")


def _counts(values):
    # A missing field, bool or malformed counter is not a zero. Keep only an
    # explicitly supplied nonnegative native integer, including an actual zero.
    return {name: value for name, value in values.items()
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0}


def _facebook(post_id: str) -> dict[str, Any]:
    token = _meta_token("FACEBOOK_PAGE_ACCESS_TOKEN", "META_ACCESS_TOKEN")
    if not token:
        return _result("facebook_page", "AUTH_REQUIRED", limitation="current_page_token_binding_missing")
    try:
        value = _get_json(
            f"https://graph.facebook.com/v21.0/{urllib.parse.quote(post_id, safe='')}",
            {
                "fields": "id,shares,likes.limit(0).summary(true),comments.limit(25).summary(true){id,message}",
                "access_token": token,
            },
        )
    except Exception as exc:  # noqa: BLE001
        return _http_failure("facebook_page", exc)
    likes = ((value.get("likes") or {}).get("summary") or {}).get("total_count")
    comments_edge = value.get("comments") or {}
    comments = (comments_edge.get("summary") or {}).get("total_count")
    shares = (value.get("shares") or {}).get("count")
    metrics = _counts({"likes": likes, "comments": comments, "shares": shares})
    interactions = [
        {"interaction_id": str(row.get("id") or ""), "text": str(row.get("message") or ""), "platform": "facebook_page"}
        for row in (comments_edge.get("data") or []) if isinstance(row, Mapping)
    ]
    return _result(
        "facebook_page", "COLLECTED", metrics=metrics,
        available=tuple(metrics), missing_metrics=tuple({"likes", "comments", "shares"} - metrics.keys()), interactions=interactions,
        limitation="one_exact_page_post_graph_read",
    )


def _instagram(media_id: str) -> dict[str, Any]:
    token = _meta_token("INSTAGRAM_ACCESS_TOKEN", "META_ACCESS_TOKEN")
    if not token:
        return _result("instagram_business", "AUTH_REQUIRED", limitation="current_instagram_token_binding_missing")
    try:
        value = _get_json(
            f"https://graph.facebook.com/v21.0/{urllib.parse.quote(media_id, safe='')}",
            {"fields": "id,like_count,comments_count,comments.limit(25){id,text}", "access_token": token},
        )
    except Exception as exc:  # noqa: BLE001
        return _http_failure("instagram_business", exc)
    interactions = [
        {"interaction_id": str(row.get("id") or ""), "text": str(row.get("text") or ""), "platform": "instagram_business"}
        for row in ((value.get("comments") or {}).get("data") or []) if isinstance(row, Mapping)
    ]
    metrics = _counts({"likes": value.get("like_count"), "comments": value.get("comments_count")})
    return _result(
        "instagram_business", "COLLECTED",
        metrics=metrics, available=tuple(metrics), missing_metrics=tuple({"likes", "comments"} - metrics.keys()), interactions=interactions,
        limitation="one_exact_business_media_graph_read",
    )


def _threads(post_id: str) -> dict[str, Any]:
    token = _meta_token("THREADS_USER_ACCESS_TOKEN", "THREADS_ACCESS_TOKEN")
    if not token:
        return _result("threads", "AUTH_REQUIRED", limitation="current_threads_token_binding_missing")
    try:
        value = _get_json(
            f"https://graph.threads.net/v1.0/{urllib.parse.quote(post_id, safe='')}/replies",
            {"fields": "id,text", "limit": "25", "access_token": token},
        )
    except Exception as exc:  # noqa: BLE001
        return _http_failure("threads", exc)
    interactions = [
        {"interaction_id": str(row.get("id") or ""), "text": str(row.get("text") or ""), "platform": "threads"}
        for row in (value.get("data") or []) if isinstance(row, Mapping)
    ]
    metrics = {"reply_sample_count": len(interactions)} if isinstance(value.get("data"), list) else {}
    return _result(
        "threads", "COLLECTED", metrics=metrics,
        available=tuple(metrics), missing_metrics=("replies",), interactions=interactions,
        limitation="one_exact_root_replies_page_sample_not_total_replies_no_insights_scope_assumed",
    )


def _discord(message_id: str) -> dict[str, Any]:
    webhook = str(os.environ.get("DISCORD_WEBHOOK_URL") or "")
    if not webhook:
        return _result("discord", "AUTH_REQUIRED", limitation="current_webhook_binding_missing")
    request = urllib.request.Request(
        f"{webhook.rstrip('/')}/messages/{urllib.parse.quote(message_id, safe='')}", method="GET"
    )
    request.add_header("User-Agent", "CapitalChronicleContentOps/1.0")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            value = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        return _http_failure("discord", exc)
    rows = value.get("reactions")
    valid = isinstance(rows, list) and all(isinstance(row, Mapping)
        and isinstance(row.get("count"), int) and not isinstance(row["count"], bool) and row["count"] >= 0 for row in rows)
    metrics = {"reactions": sum(row["count"] for row in rows)} if valid else {}
    return _result(
        "discord", "COLLECTED", metrics=metrics,
        available=tuple(metrics), missing_metrics=("reactions",) if not valid else (),
        limitation="one_exact_webhook_message_read_reaction_summary_only",
    )


def collect_current_authorized_destination_metrics(
    *, destination: str, public_object_id: str
) -> dict[str, Any]:
    """Use only the currently configured binding; never request consent or wider scope."""
    if destination == "facebook_page":
        return _facebook(public_object_id)
    if destination == "instagram_business":
        return _instagram(public_object_id)
    if destination == "threads":
        return _threads(public_object_id)
    if destination == "discord":
        return _discord(public_object_id)
    if destination in {"telegram", "x", "youtube", "linkedin_company"}:
        return _result(
            destination, "NOT_EXPOSED",
            limitation="current_authorized_binding_exposes_no_safe_exact_object_metrics_collector",
        )
    return _result(destination, "UNSUPPORTED", limitation="destination_collector_not_implemented")
