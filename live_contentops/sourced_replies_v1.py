"""CC-386: selected, source-bound replies in the existing store and sole publisher.

No discovery trigger, scheduler, model call or direct transport. The publication
coordinator retains exactly-once, identity, KILL_SWITCH and readback ownership.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo

from live_contentops.event_article_guard_v1 import check_publication_copy

DESTINATION = "internal:sourced-reply"
RESERVATIONS = "internal:sourced-reply-reservation"
WARNINGS = "internal:sourced-reply-platform-warning"
X_CAUSE = "X_RULES_API_ONLY_OPT_IN_AND_PRIOR_WRITTEN_AI_APPROVAL_REQUIRED"
ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps\sourced-replies")


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    ).hexdigest()


def clock(value):
    at = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if at.tzinfo is None:
        raise ValueError("REPLY_OFFSET_REQUIRED")
    return at.astimezone(timezone.utc)


def _rows(store, destination=DESTINATION):
    return [
        json.loads(r["payload"])
        for r in store.list_outbox_messages(destination=destination)
    ]


def _row(store, key):
    r = store.get_outbox_message(key)
    if not r or r["destination"] != DESTINATION:
        raise ValueError("REPLY_NOT_FOUND")
    return json.loads(r["payload"])


def validate(row, *, store=None):
    if row.get("x_api_mention"):
        from live_contentops.x_mention_responder_v1 import validate_row
        return validate_row(row, store=store)
    platform, text = row["platform"], row["text"]
    if platform not in {"x", "threads"}:
        raise ValueError("REPLY_PLATFORM_INVALID")
    pattern = (
        r"https://(?:www\.)?x\.com/([A-Za-z0-9_]+)/status/(\d+)"
        if platform == "x"
        else r"https://www\.threads\.(?:com|net)/@([A-Za-z0-9_.]+)/post/([A-Za-z0-9_-]+)"
    )
    m = re.fullmatch(pattern, row["target_url"])
    if not m or m[1].casefold() != row["target_author"].lstrip("@").casefold():
        raise ValueError("REPLY_TARGET_IDENTITY_MISMATCH")
    if not str(row["target_id"]).isdigit():
        raise ValueError("REPLY_PROVIDER_TARGET_ID_REQUIRED")
    if platform == "x" and m[2] != str(row["target_id"]):
        raise ValueError("REPLY_TARGET_IDENTITY_MISMATCH")
    if re.search(
        r"(?:https?://|www\.|\b[a-z0-9-]+\.(?:com|net|org|io|app)\b|follow us|buy now|\bCFDs?\b)",
        text,
        re.I,
    ):
        raise ValueError("REPLY_LINK_PROMOTION_OR_CFD_FORBIDDEN")
    if len(text) > (280 if platform == "x" else 500):
        raise ValueError("REPLY_PLATFORM_LENGTH_EXCEEDED")
    if not row.get("point") or not row.get("target_claim"):
        raise ValueError("REPLY_THREAD_SPECIFIC_POINT_REQUIRED")
    for field in ("stance", "addition", "source_label"):
        if not row.get(field) or row[field] not in text:
            raise ValueError("REPLY_SOURCED_ARGUMENT_REQUIRED:" + field)
    source = row["source"]
    raw = Path(source["path"]).read_bytes()
    if hashlib.sha256(raw).hexdigest() != source["sha256"] or source[
        "excerpt"
    ] not in raw.decode("utf-8-sig"):
        raise ValueError("REPLY_SOURCE_BINDING_CHANGED")
    if row.get("image"):
        image = row["image"]
        local = Path(image["path"]).resolve()
        if "media" not in {
            p.casefold() for p in local.parts
        } or "CC-386".casefold() not in {p.casefold() for p in local.parts}:
            raise ValueError("REPLY_IMAGE_OUTSIDE_ITEM_MEDIA_FOLDER")
        if hashlib.sha256(local.read_bytes()).hexdigest() != image["sha256"]:
            raise ValueError("REPLY_IMAGE_BYTES_CHANGED")
        if (
            not image.get("rights_source")
            or image.get("public_redistribution_allowed") is not True
        ):
            raise ValueError("PUBLIC_REDISTRIBUTION_NOT_LICENSED")
    clock(source["known_at_utc"])
    check_publication_copy(
        {"reply": text}, conditional_calls=row.get("conditional_calls", [])
    )
    return row


def stage(store, candidate, *, feed, now=None):
    """Freeze authored text and exact target/source bindings; never writes publicly."""
    now = now or datetime.now(timezone.utc)
    row = dict(candidate)
    row["kind"] = "reply"
    author = row["list_author"].lstrip("@").casefold()
    if author not in {str(r["handle"]).lstrip("@").casefold() for r in feed["rows"]}:
        raise ValueError("REPLY_AUTHOR_NOT_IN_HELD_X_LIST")
    row["list_feed_generated_at_utc"] = feed["generated_at_utc"]
    validate(row)
    if clock(row["source"]["known_at_utc"]) > now:
        raise ValueError("REPLY_SOURCE_KNOWN_AFTER_PREPARATION")
    if row.get("debate_parent_key"):
        parent = _row(store, row["debate_parent_key"])
        if (
            parent["platform"] != row["platform"]
            or parent["list_author"].casefold() != row["list_author"].casefold()
        ):
            raise ValueError("REPLY_DEBATE_PARENT_MISMATCH")
        if not report_one(store, parent)["readback_url"]:
            raise ValueError("REPLY_DEBATE_REQUIRES_CONFIRMED_PARENT")
    key = "reply-" + digest([row["platform"], row["target_url"], row["point"]])
    existing = store.get_outbox_message(key)
    if existing:
        prior = json.loads(existing["payload"])
        if {
            k: v
            for k, v in prior.items()
            if k not in {"key", "created_at_utc", "list_feed_generated_at_utc"}
        } != {k: v for k, v in row.items() if k != "list_feed_generated_at_utc"}:
            raise ValueError("REPLY_FROZEN_COPY_OR_TARGET_CHANGED")
        return prior
    for prior in _rows(store):
        if (
            prior["platform"] == row["platform"]
            and prior["target_url"] == row["target_url"]
        ):
            raise ValueError("REPLY_ALREADY_SELECTED_FOR_INTERACTION")
    row.update(key=key, created_at_utc=now.isoformat())
    store.create_work_item(
        story_id=key,
        title="Reply: " + row["target_author"],
        target_surface="MULTI_PLATFORM",
        work_item_id=key,
    )
    store.register_outbox_message(
        message_id=key,
        work_item_id=key,
        destination=DESTINATION,
        payload=json.dumps(row, sort_keys=True),
        status="READY_FOR_PUBLISHER",
    )
    return row


def payload(row):
    return {
        "destination": row["platform"],
        "text": row["text"],
        "full_text": row["text"],
        "reply_to_id": str(row["target_id"]),
        "reply_to_url": row["target_url"],
        "media_asset_ids": [row["image"]["asset_id"]] if row.get("image") else [],
    }


def plan_for(store, key, *, root=ROOT):
    from live_contentops.destination_transport_registry_v1 import (
        REGISTRY_VERSION,
        registration_for_destination,
    )

    row = validate(_row(store, key), store=store)
    folder = Path(root) / key
    folder.mkdir(parents=True, exist_ok=True)
    if row.get("image"):
        manifest = row["image"]["delivery_manifest"]
        # Manifest was produced by the existing media owner; exact bytes are copied, not rehosted.
        raw = Path(manifest["path"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != manifest["sha256"]:
            raise ValueError("REPLY_IMAGE_DELIVERY_BINDING_CHANGED")
        (folder / "delivery_media_manifest_v1.json").write_bytes(raw)
    (folder / "run_context_v1.json").write_text(
        json.dumps(
            {
                "article": {},
                "selection": {},
                "media": {"assets": [row["image"]] if row.get("image") else []},
            }
        ),
        encoding="utf-8",
    )
    r = registration_for_destination(row["platform"])
    if row.get("x_api_mention"):
        from live_contentops.x_mention_responder_v1 import api_registration
        r = api_registration()
    plan = {
        "schema_version": "contentops.publication_plan.v1",
        "sourced_reply": key,
        "plan_hash": digest(row),
        "story_identity": key,
        "article_identity": key,
        "package_identity": key,
        "publication_window": {"window_identity": key},
        "output_dir": str(folder.resolve()),
        "transport_registry_version": REGISTRY_VERSION,
        "policy_mode_version": "AUTONOMOUS_DEFAULT:cc386.v1",
        "destinations": [
            {
                "destination": row["platform"],
                "platform": r.platform,
                "surface": r.surface,
                "transport_type": r.transport_type,
                "transport_registry_version": REGISTRY_VERSION,
                "expected_destination_identity": r.expected_identity,
                "payload": row["text"],
                "payload_hash": hashlib.sha256(row["text"].encode()).hexdigest(),
                "canonical_url": None,
            }
        ],
    }


    if row.get("x_api_mention"):
        plan["x_api_mention"] = row["x_api_mention"]
    return plan


def validate_plan(store, work_item_id, plan):
    key = plan["sourced_reply"]
    expected = plan_for(store, key, root=Path(plan["output_dir"]).parent)
    if work_item_id != key or dict(plan) != expected:
        raise ValueError("REPLY_PLAN_CHANGED")
    return _row(store, key)


def validate_intent(store, intent):
    row = validate(_row(store, intent["sourced_reply"]), store=store)
    if (
        intent["work_item_id"] != row["key"]
        or intent["native_payload"] != payload(row)
        or intent["plan_hash"] != digest(row)
        or intent.get("canonical_url")
    ):
        raise ValueError("REPLY_INTENT_CHANGED")
    return row


def reserve(store, row, now):
    """Count attempted replies as well as confirmed ones, under the existing store lease."""
    if row.get("x_api_mention"):
        from live_contentops.x_mention_responder_v1 import require_publishable
        require_publishable(store, row, now)
        return
    if row["platform"] == "x":
        raise ValueError(X_CAUSE)
    if any(r["platform"] == row["platform"] for r in _rows(store, WARNINGS)):
        raise ValueError("REPLY_PLATFORM_WARNING_STOP")
    day = now.astimezone(ZoneInfo("Asia/Bangkok")).date().isoformat()
    lease = store.acquire_lease("sourced-replies-budget", row["key"], ttl_seconds=30)
    try:
        rows = [
            r
            for r in _rows(store, RESERVATIONS)
            if r["day"] == day and r["platform"] == row["platform"]
        ]
        if any(r["key"] == row["key"] for r in rows):
            return
        if len(rows) >= 5:
            raise ValueError("JIM_DECISION_108_FIVE_REPLIES_PER_DAY")
        if any(r["author"].casefold() == row["target_author"].casefold() for r in rows):
            raise ValueError("JIM_DECISION_108_ONE_REPLY_PER_AUTHOR_PER_DAY")
        value = {
            "key": row["key"],
            "day": day,
            "platform": row["platform"],
            "author": row["target_author"],
            "reserved_at_utc": now.isoformat(),
        }
        store.register_outbox_message(
            message_id="reply-reserve-" + digest(value),
            work_item_id=row["key"],
            destination=RESERVATIONS,
            payload=json.dumps(value),
            status="RESERVED",
        )
    finally:
        store.release_lease(lease["lease_id"], row["key"], lease["fencing_token"])


def read_target(row, *, store=None):
    """Provider identity, permalink and claim must match before any new reply write."""
    if row.get("x_api_mention"):
        return validate(row, store=store)  # Official adapter re-reads the target before POST.
    if row["platform"] == "x":
        raise ValueError(X_CAUSE)
    from live_contentops.threads_adapter_v6 import (
        _get_json,
        _threads_token,
        THREADS_GRAPH_VERSION,
    )
    from urllib.error import HTTPError

    try:
        value = _get_json(
            f"https://graph.threads.net/{THREADS_GRAPH_VERSION}/{row['target_id']}",
            {"fields": "id,text,username,permalink", "access_token": _threads_token()},
        )
    except HTTPError as exc:
        # Do not serialize provider bodies, token-bearing requests or exception URLs.
        raise ValueError("THREADS_TARGET_READ_HTTP_" + str(exc.code)) from None
    except Exception as exc:
        raise ValueError("THREADS_TARGET_READ_" + type(exc).__name__) from None

    def normalize(value):
        return str(value).replace("threads.net/", "threads.com/").rstrip("/")

    if (
        str(value.get("id")) != str(row["target_id"])
        or normalize(value.get("permalink")) != normalize(row["target_url"])
        or str(value.get("username", "")).casefold()
        != row["target_author"].lstrip("@").casefold()
        or row["target_claim"] not in str(value.get("text", ""))
    ):
        raise ValueError("REPLY_PROVIDER_TARGET_IDENTITY_OR_CLAIM_CHANGED")
    return value


def stop_on_warning(store, row, cause):
    value = {
        "platform": row["platform"],
        "key": row["key"],
        "cause": cause,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    store.register_outbox_message(
        message_id="reply-warning-" + digest(value),
        work_item_id=row["key"],
        destination=WARNINGS,
        payload=json.dumps(value),
        status="STOPPED",
    )


def publish(store, key, *, coordinator, root=ROOT, now=None):
    row = _row(store, key)
    if report_one(store, row)["readback_url"]:
        return {
            "publication": {"status": "ALREADY_CONFIRMED"},
            "reply": report_one(store, row),
        }
    plan = plan_for(store, key, root=root)
    if row.get("x_api_mention"):
        from live_contentops.x_mention_responder_v1 import interaction_status
        if not interaction_status(store, row["target_id"]):
            reserve(store, row, now or datetime.now(timezone.utc))
    else:
        reserve(store, row, now or datetime.now(timezone.utc))
    coordinator.allow_prior_confirmed_distribution = True
    coordinator.recovery_scope = {
        "work_item_id": key,
        "plan": plan,
        "exact_work_item_only": True,
    }
    coordinator.register_plan(key, plan)
    try:
        result = coordinator.execute_plan(key, plan)
    except ValueError as exc:
        if any(
            token in str(exc).upper()
            for token in ("429", "RATE_LIMIT", "SUSPEND", "WARNING")
        ):
            stop_on_warning(store, row, str(exc))
        raise
    states = json.dumps(result).upper()
    if any(
        token in states for token in ("RATE_LIMIT", "SUSPEND", "WARNING", "HTTP_429")
    ):
        value = {
            "platform": row["platform"],
            "key": key,
            "cause": "PLATFORM_LIMIT_OR_WARNING",
            "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        store.register_outbox_message(
            message_id="reply-warning-" + digest(value),
            work_item_id=key,
            destination=WARNINGS,
            payload=json.dumps(value),
            status="STOPPED",
        )
    return {"publication": result, "reply": report_one(store, row)}


def report_one(store, row):
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator

    ids = DurablePublicationCoordinator._ids(row["key"], digest(row), row["platform"])
    dispatch = store.get_platform_dispatch(ids["dispatch_id"]) or {}
    reconciled = any(
        r["reconciliation_id"] == ids["reconciliation_id"]
        and r["status"] == "RECONCILED_CONFIRMED"
        for r in store.get_reconciliations_for_work_item(row["key"])
    )
    observations = [
        r
        for r in store.list_performance_observations()
        if r["dispatch_id"] == ids["dispatch_id"] and r["observation_window"] == "DAILY"
    ]
    return {
        "key": row["key"],
        "platform": row["platform"],
        "target_url": row["target_url"],
        "target_author": row["target_author"],
        "text": row["text"],
        "image": row.get("image"),
        "posted_at_utc": dispatch.get("dispatched_at"),
        "readback_url": dispatch.get("public_object_url") if reconciled else None,
        "status": dispatch.get("status", "PREPARED"),
        "audience_24h": observations,
        "debate_parent_key": row.get("debate_parent_key"),
    }


def report(store):
    return [report_one(store, r) for r in _rows(store)]
