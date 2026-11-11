"""Bounded read-only destination observations over existing authorized bindings.

Each invocation performs bounded GETs for its exact destination/public object.
Missing scope, binding, or exposed data is reported truthfully and never coerced to zero.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Mapping

from live_contentops.secret_store_v1 import first_secret, read_secret

METRICS = (
    "impressions", "reach", "views", "likes", "reactions", "shares", "reposts",
    "comments", "replies", "canonical_article_clicks", "subscriber_conversions",
    "search_impressions", "search_clicks", "search_ctr", "search_query",
    "search_position", "interaction_quality",
    "reply_sample_count",
    "quotes", "followers_count", "members_count",
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
        result = _result(
            destination, status,
            limitation=f"read_only_provider_http_{error.code}",
            provider_requests=1,
        )
        try:
            detail = json.loads(error.read(8192)).get("error", {})
            message = re.sub(r"https?://\S+|[A-Za-z0-9_-]{48,}", "<redacted>", str(detail.get("message", "")))[:500]
            result["provider_error"] = {"code": detail.get("code"), "subcode": detail.get("error_subcode"), "message": message}
        except (ValueError, AttributeError, TypeError):
            pass
        return result
    return _result(
        destination, "UNAVAILABLE",
        limitation=f"read_only_provider_{type(error).__name__}",
        provider_requests=1,
    )


def _meta_token(*names: str) -> str:
    # CC-297: Credential Manager, then the live user environment, then the process environment.
    return first_secret(*names)


def _counts(values):
    # A missing field, bool or malformed counter is not a zero. Keep only an
    # explicitly supplied nonnegative native integer, including an actual zero.
    return {name: value for name, value in values.items()
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0}


def _insight_values(value: Mapping[str, Any]) -> dict[str, int]:
    """One lifetime scalar per metric; never add periods, breakdowns or pages."""
    result = {}
    for row in value.get("data") or []:
        if not isinstance(row, Mapping):
            continue
        values = row.get("values")
        count = (values[0].get("value") if isinstance(values, list) and len(values) == 1
                 and isinstance(values[0], Mapping) else (row.get("total_value") or {}).get("value"))
        result.update(_counts({str(row.get("name")): count}))
    return result


def _add_insights(result, destination, object_id, token, names):
    """A rejected insight never erases independently observed interaction counts."""
    host = "graph.threads.net/v1.0" if destination == "threads" else "graph.facebook.com/v21.0"
    try:
        value = _get_json(f"https://{host}/{urllib.parse.quote(object_id, safe='')}/insights",
                          {"metric": ",".join(names), "access_token": token})
        if value.get("error"):
            raise ValueError("INSIGHTS_PROVIDER_ERROR")
        metrics = _insight_values(value)
        aliases = {"post_media_view": "views", "post_impressions_unique": "reach", "saved": "saves"}
        metrics = {aliases.get(name, name): count for name, count in metrics.items()}
        result["metrics"].update(metrics)
        result["availability"].update({aliases.get(name, name): "AVAILABLE" if aliases.get(name, name) in metrics else "NOT_EXPOSED" for name in names})
        result["insights_status"] = "COLLECTED" if metrics else "NOT_EXPOSED"
        if metrics:
            result["status"] = "COLLECTED"
    except Exception as exc:  # noqa: BLE001 - never serialize provider URLs/tokens
        failure = _http_failure(destination, exc)
        aliases = {"post_media_view": "views", "post_impressions_unique": "reach", "saved": "saves"}
        result["availability"].update({aliases.get(name, name): failure["status"] for name in names if aliases.get(name, name) not in result["metrics"]})
        result["insights_status"] = failure["status"]
        if failure.get("provider_error"):
            result["insights_error"] = failure["provider_error"]
        result["limitations"].extend(failure["limitations"])
    result["provider_requests"] += 1
    return result


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
        return _add_insights(_http_failure("facebook_page", exc), "facebook_page", post_id, token,
                             ("post_media_view", "post_impressions_unique"))
    likes = ((value.get("likes") or {}).get("summary") or {}).get("total_count")
    comments_edge = value.get("comments") or {}
    comments = (comments_edge.get("summary") or {}).get("total_count")
    shares = (value.get("shares") or {}).get("count")
    metrics = _counts({"likes": likes, "comments": comments, "shares": shares})
    interactions = [
        {"interaction_id": str(row.get("id") or ""), "text": str(row.get("message") or ""), "platform": "facebook_page"}
        for row in (comments_edge.get("data") or []) if isinstance(row, Mapping)
    ]
    result = _result(
        "facebook_page", "COLLECTED", metrics=metrics,
        available=tuple(metrics), missing_metrics=tuple({"likes", "comments", "shares"} - metrics.keys()), interactions=interactions,
        limitation="one_exact_page_post_graph_read",
    )
    return _add_insights(result, "facebook_page", post_id, token,
                         ("post_media_view", "post_impressions_unique"))


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
        return _add_insights(_http_failure("instagram_business", exc), "instagram_business", media_id, token,
                             ("views", "reach", "saved", "shares"))
    interactions = [
        {"interaction_id": str(row.get("id") or ""), "text": str(row.get("text") or ""), "platform": "instagram_business"}
        for row in ((value.get("comments") or {}).get("data") or []) if isinstance(row, Mapping)
    ]
    metrics = _counts({"likes": value.get("like_count"), "comments": value.get("comments_count")})
    result = _result(
        "instagram_business", "COLLECTED",
        metrics=metrics, available=tuple(metrics), missing_metrics=tuple({"likes", "comments"} - metrics.keys()), interactions=interactions,
        limitation="one_exact_business_media_graph_read",
    )
    return _add_insights(result, "instagram_business", media_id, token, ("views", "reach", "saved", "shares"))


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
        return _add_insights(_http_failure("threads", exc), "threads", post_id, token,
                             ("views", "likes", "replies", "reposts", "quotes"))
    interactions = [
        {"interaction_id": str(row.get("id") or ""), "text": str(row.get("text") or ""), "platform": "threads"}
        for row in (value.get("data") or []) if isinstance(row, Mapping)
    ]
    metrics = {"reply_sample_count": len(interactions)} if isinstance(value.get("data"), list) else {}
    result = _result(
        "threads", "COLLECTED", metrics=metrics,
        available=tuple(metrics), missing_metrics=("replies",), interactions=interactions,
        limitation="one_exact_root_replies_page_sample_not_total_replies_no_insights_scope_assumed",
    )
    return _add_insights(result, "threads", post_id, token, ("views", "likes", "replies", "reposts", "quotes"))


def _discord(message_id: str) -> dict[str, Any]:
    webhook = first_secret("DISCORD_WEBHOOK_URL", "DISCORD_ANNOUNCEMENTS_WEBHOOK_URL")
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
    *, destination: str, public_object_id: str, object_kind: str = "post"
) -> dict[str, Any]:
    """Use only the currently configured binding; never request consent or wider scope."""
    if object_kind == "comment" and destination in {"facebook_page", "instagram_business"}:
        tokens = ("FACEBOOK_PAGE_ACCESS_TOKEN", "META_ACCESS_TOKEN") if destination == "facebook_page" else ("INSTAGRAM_ACCESS_TOKEN", "META_ACCESS_TOKEN")
        token = _meta_token(*tokens)
        if not token:
            return _result(destination, "AUTH_REQUIRED", limitation="existing_comment_read_binding_missing")
        fields = "id,like_count,comment_count" if destination == "facebook_page" else "id,like_count"
        try:
            value = _get_json(f"https://graph.facebook.com/v21.0/{urllib.parse.quote(public_object_id, safe='')}",
                              {"fields": fields, "access_token": token})
            metrics = _counts({"likes": value.get("like_count"), "replies": value.get("comment_count")})
            return _result(destination, "COLLECTED", metrics=metrics, available=tuple(metrics),
                           missing_metrics=("views", "reach", "replies") if destination == "instagram_business" else ("views", "reach"),
                           limitation="exact_comment_counters_no_post_insights_on_comment")
        except Exception as exc:
            return _http_failure(destination, exc)
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


def collect_account_metrics(destination: str) -> dict[str, Any]:
    """A separate daily account snapshot; never sum this count once per post."""
    bindings = {
        "facebook_page": (("FACEBOOK_PAGE_ACCESS_TOKEN", "META_ACCESS_TOKEN"), ("FACEBOOK_PAGE_ID",), "followers_count"),
        "instagram_business": (("INSTAGRAM_ACCESS_TOKEN", "META_ACCESS_TOKEN"), ("INSTAGRAM_BUSINESS_ACCOUNT_ID", "INSTAGRAM_IG_ID"), "followers_count"),
        "threads": (("THREADS_USER_ACCESS_TOKEN", "THREADS_ACCESS_TOKEN"), ("THREADS_USER_ID",), "followers_count"),
    }
    if destination not in bindings:
        return _result(destination, "NOT_EXPOSED", limitation="account_count_not_exposed_by_current_route")
    tokens, ids, field = bindings[destination]
    token, account = first_secret(*tokens), first_secret(*ids)
    if not token or not account:
        return _result(destination, "AUTH_REQUIRED", limitation="existing_account_binding_missing")
    try:
        host = "graph.threads.net/v1.0" if destination == "threads" else "graph.facebook.com/v21.0"
        if destination == "threads":
            value = _get_json(f"https://{host}/{urllib.parse.quote(account, safe='')}/threads_insights",
                              {"metric": "followers_count", "access_token": token})
            metrics = _insight_values(value)
        else:
            value = _get_json(f"https://{host}/{urllib.parse.quote(account, safe='')}",
                              {"fields": field, "access_token": token})
            metrics = _counts({field: value.get(field)})
        return _result(destination, "COLLECTED" if metrics else "NOT_EXPOSED", metrics=metrics,
                       available=tuple(metrics), limitation="daily_account_snapshot_not_post_metric", provider_requests=1)
    except Exception as exc:
        return _http_failure(destination, exc)
