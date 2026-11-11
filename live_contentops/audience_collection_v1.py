"""CC-402: bounded read-only collection in the existing minute consumer.

One current snapshot per public object/day for seven days. A late first collection
keeps today's clock and never pretends to be a missed historical checkpoint.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import re
import time
from uuid import uuid4
from zoneinfo import ZoneInfo

from . import daily_app_performance_v1 as perf
from .channel_engagement_v1 import verified_dispatch_readback, verified_dispatch_identity
from .destination_performance_observer_v1 import collect_current_authorized_destination_metrics, collect_account_metrics
from .durable_operational_store_v1 import LeaseConflictError

ROUTES = ("threads", "facebook_page", "instagram_business", "discord", "telegram")
CAPABILITY = "contentops.audience_collector.cc402.v1"
GROUP = "codex/audience-metrics"


def utc(value):
    at = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if at.tzinfo is None:
        raise ValueError("AUDIENCE_CLOCK_OFFSET_REQUIRED")
    return at.astimezone(timezone.utc)


def dispatch_call_ids(store, dispatch, message=None):
    """Join CC-399's retained record; never guess a call from article prose."""
    message = message or store.get_outbox_message(dispatch["message_id"])
    intent = json.loads((message or {}).get("payload") or "{}")
    if not isinstance(intent, dict):
        return []
    key = intent.get("plan_status_post")
    if key:
        record = store.get_outbox_message(key)
        payload = json.loads((record or {}).get("payload") or "{}")
        members = [(key, payload)]
        if payload.get("kind") == "run":
            members = [(child, json.loads((store.get_outbox_message(child) or {}).get("payload") or "{}"))
                       for child in payload.get("card_keys", [])]
        result = []
        for source, card in members:
            if not card.get("plan_id"):
                continue
            # A run post binds its actual cards, never a fictitious run-shaped call.
            full = card.get("public_call_id") or card.get("levels", {}).get("public_call_id")
            result.append({"call_id": full or card.get("short_id") or card["plan_id"],
                     "call_id_kind": "PUBLIC_CALL_ID" if full else "CC399_RETAINED_SHORT_ID" if card.get("short_id") else "PLAN_ID",
                     "plan_id": card["plan_id"], "source_record_id": source,
                     **({"run_record_id": key} if source != key else {})})
        if result:
            return result
    # Analysis pages have an exact plan binding rather than a status-card record.
    with store.get_read_only_connection() as conn:
        records = conn.execute("SELECT message_id,payload FROM outbox_messages WHERE destination='internal:plan-analysis-page' AND work_item_id=?",
                               ((message or {}).get("work_item_id"),)).fetchall()
    result = []
    for row in records:
        value = json.loads(row["payload"])
        if value.get("plan_id"):
            result.append({"call_id": value.get("public_call_id") or value.get("short_id") or value["plan_id"],
                           "plan_id": value["plan_id"], "source_record_id": row["message_id"]})
    return result


def _schedule(store, now, *, published_day=None):
    day = now.astimezone(ZoneInfo("Asia/Bangkok")).date().isoformat()
    window = "AUDIENCE_DAILY:" + day
    existing = {(r["dispatch_id"], r["observation_window"]) for r in store.list_performance_observations()}
    scheduled, excluded = 0, {}
    for dispatch in store.list_platform_dispatches():
        if dispatch["platform"] not in ROUTES or dispatch["status"] != "DISPATCH_CONFIRMED" or not dispatch.get("public_object_id"):
            continue
        at = utc(dispatch["dispatched_at"])
        if not now - timedelta(days=7) <= at <= now:
            continue
        if published_day and at.astimezone(ZoneInfo("Asia/Bangkok")).date().isoformat() != published_day:
            continue
        if (dispatch["dispatch_id"], window) in existing:
            continue
        message = store.get_outbox_message(dispatch["message_id"])
        if not message:
            continue
        reconciliation_id = "reconciliation_" + dispatch["dispatch_id"].removeprefix("dispatch_")
        reconciliation = next((r for r in store.get_reconciliations_for_work_item(message["work_item_id"])
                               if r["reconciliation_id"] == reconciliation_id), {})
        readbacks = store.list_readbacks_for_dispatch(dispatch["dispatch_id"])
        learning_eligible = reconciliation.get("status") == "RECONCILED_CONFIRMED" and any(
            verified_dispatch_readback(r, dispatch) for r in readbacks)
        if not learning_eligible and not any(verified_dispatch_identity(r, dispatch) for r in readbacks):
            excluded[dispatch["dispatch_id"]] = "EXACT_CONFIRMED_READBACK_NOT_RECORDED"
            continue
        calls = dispatch_call_ids(store, dispatch, message)
        observation = {
            "observation_id": perf.observation_identity(dispatch_id=dispatch["dispatch_id"], public_object_id=dispatch["public_object_id"],
                platform=dispatch["platform"], observation_window=window, collector_capability_version=CAPABILITY),
            "schema_version": perf.OBSERVATION_SCHEMA_VERSION, "dispatch_id": dispatch["dispatch_id"],
            "work_item_id": message["work_item_id"], "platform": dispatch["platform"], "public_object_id": dispatch["public_object_id"],
            "public_object_url_hash": dispatch.get("public_object_url_hash"), "observation_window": window,
            "scheduled_for_utc": now.isoformat(), "collected_at_utc": None, "collector_capability_version": CAPABILITY,
            "collection_status": "SCHEDULED", "metrics_native_json": json.dumps({"_call_ids": calls}),
            "metric_availability_json": "{}", "source_identity": "contentops.audience_collection.cc402.v1", "learning_eligible": int(learning_eligible),
        }
        observation["observation_hash"] = perf.observation_hash(observation)
        store.register_performance_observation(observation=observation)
        scheduled += 1
    return scheduled, excluded


class PublicTelegramMetrics:
    """Neo's public channel page only. No Telegram Web, bot session or sign-in."""

    def __init__(self, client=None):
        if client is None:
            from .neo_endpoint_executor_v1 import NeoMcpClient
            client = NeoMcpClient()
        self.client, self.page, self.group = client, None, None

    def _open(self, object_id):
        if not re.fullmatch(r"[1-9]\d*", str(object_id)):
            raise ValueError("TELEGRAM_NUMERIC_PUBLIC_MESSAGE_REQUIRED")
        url = "https://t.me/s/CapitalChronicle?before=" + str(int(object_id) + 1)
        if self.page is None:
            self.client.call("name_session", {"name": "audience metrics", "category": "data-extraction"})
            listing = self.client.text(self.client.call("tabs", {"action": "list"}))
            groups = self.client.text(self.client.call("tab_groups", {"action": "list"}))
            group = re.search(r'^\[([^]]+)\] "' + re.escape(GROUP) + r'"[^\n]*pages: ([\d, ]+)', groups, re.M)
            if group:
                self.group = group[1]
                ids = set(re.findall(r"\d+", group[2]))
                for line in listing.splitlines():
                    match = re.match(r"\[(\d+)\] (https://t.me/s/CapitalChronicle(?:\?\S*)?)(?: |$)", line)
                    if match and match[1] in ids:
                        self.page = int(match[1])
                        break
        if self.page is not None:
            self.client.call("navigate", {"page": self.page, "url": url})
        else:
            result = self.client.text(self.client.call("tabs", {"action": "new", "url": url,
                **({"groupId": self.group} if self.group else {})}))
            match = re.search(r"opened page (\d+)", result)
            if not match:
                raise ValueError("TELEGRAM_PUBLIC_TAB_NOT_OPENED")
            self.page = int(match[1])
        return url

    def __call__(self, object_id):
        url = self._open(object_id)
        # read() can answer this exactly. No evaluateInPage or page script is needed.
        selector = '.tgme_widget_message[data-post="CapitalChronicle/' + str(object_id) + '"] .tgme_widget_message_views'
        code = "const page=browser.page(" + str(self.page) + "); return {views:await page.read({selector:" + json.dumps(selector) + "}),members:await page.read({selector:'.tgme_channel_info_counters'})};"
        result = self.client.value(self.client.call("run", {"code": code}))
        if not isinstance(result, dict) or result.get("ok") is not True:
            raise ValueError("TELEGRAM_PUBLIC_METRIC_READ_FAILED")
        value = result.get("value") or {}
        def body(text):
            return re.sub(r"\[END_UNTRUSTED_PAGE_CONTENT[^\]]*\]", "", str(text).split("\n", 1)[-1]).strip()
        raw = body(value.get("views", ""))
        metrics = {"views": int(raw)} if re.fullmatch(r"\d+", raw) else {}
        members = re.search(r"\b(\d+)\s+subscribers(?![A-Za-z])", body(value.get("members", "")))
        return {"status": "COLLECTED" if metrics else "NOT_EXPOSED", "metrics": metrics,
                "availability": {"views": "AVAILABLE" if metrics else "NOT_EXPOSED"},
                "account_metrics": {"members_count": int(members[1])} if members else {},
                "source_identity": "telegram.public_channel_page.neo.v1", "source_url": url,
                "limitations": [] if metrics else ["public_view_counter_not_an_exact_integer"],
                "provider_requests": 0, "public_write_performed": False}


def run_collection(store, *, now=None, limit=4, published_day=None, collector=None, account_collector=None, telegram=None):
    """One bounded batch. Reuse the store's lease to avoid concurrent collectors."""
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    owner = "audience-" + uuid4().hex
    try:
        lease = store.acquire_lease("audience-collection-cc402", owner, ttl_seconds=180)
    except LeaseConflictError:
        return {"state": "EXISTING_COLLECTION_ACTIVE", "collected": 0}
    try:
        scheduled, excluded = _schedule(store, now, published_day=published_day)
        rows = [r for r in store.list_performance_observations(collection_status="SCHEDULED")
                if r["collector_capability_version"] == CAPABILITY and utc(r["scheduled_for_utc"]) <= now]
        if published_day:
            dispatch_ids = {d["dispatch_id"] for d in store.list_platform_dispatches()
                if utc(d["dispatched_at"]).astimezone(ZoneInfo("Asia/Bangkok")).date().isoformat() == published_day}
            rows = [r for r in rows if r["dispatch_id"] in dispatch_ids]
        # Complete every route fairly during recovery, rather than all one route first.
        buckets = {route: [r for r in rows if r["platform"] == route] for route in ROUTES}
        selected = []
        while len(selected) < limit and any(buckets.values()):
            for route in ROUTES:
                if buckets[route] and len(selected) < limit:
                    selected.append(buckets[route].pop(0))
        outcomes = []
        deadline = time.monotonic() + 45
        account_seen = set()
        observations = store.list_performance_observations()
        object_cache = {}
        for row in observations:
            if row.get("collected_at_utc") and utc(row["collected_at_utc"]).date() == now.date():
                if json.loads(row["metrics_native_json"]).get("_account_snapshot", {}).get("metrics"):
                    account_seen.add(row["platform"])
                if row["collector_capability_version"] == CAPABILITY and row["collection_status"] == "COLLECTED":
                    object_cache[(row["platform"], row["public_object_id"])] = row
        for row in selected:
            if time.monotonic() >= deadline:
                break
            route = row["platform"]
            dispatch = store.get_platform_dispatch(row["dispatch_id"])
            intent = json.loads(store.get_outbox_message(dispatch["message_id"])["payload"])
            native = intent.get("native_payload") or {}
            object_kind = "comment" if route in {"facebook_page", "instagram_business"} and (native.get("own_call_comment") or native.get("reply_to_id")) else "post"
            def collect(*_args):
                nonlocal telegram
                cached = object_cache.get((route, row["public_object_id"]))
                if cached:
                    result = {"status": cached["collection_status"], "metrics": json.loads(cached["metrics_native_json"]),
                              "availability": json.loads(cached["metric_availability_json"]), "source_identity": cached["source_identity"],
                              "provider_requests": 0, "limitations": ["shared_public_object_snapshot:" + cached["observation_id"]]}
                elif collector:
                    result = dict(collector(destination=route, public_object_id=row["public_object_id"]))
                elif route == "telegram":
                    telegram = telegram or PublicTelegramMetrics()
                    result = dict(telegram(row["public_object_id"]))
                else:
                    result = dict(collect_current_authorized_destination_metrics(destination=route, public_object_id=row["public_object_id"], object_kind=object_kind))
                metrics = dict(result.get("metrics") or {})
                metrics.pop("_account_snapshot", None)
                metrics["_source_observed_at_utc"] = (metrics.get("_source_observed_at_utc") or cached["collected_at_utc"]
                    if cached else datetime.now(timezone.utc).isoformat())
                metrics["_call_ids"] = json.loads(row["metrics_native_json"]).get("_call_ids", [])
                metrics["_collection_details"] = {k: result[k] for k in ("source_url", "limitations", "insights_status", "provider_requests", "provider_error", "insights_error") if k in result}
                metrics["_object_kind"] = object_kind
                metrics["_shared_public_object"] = bool(native.get("reuse_run_carousel"))
                if route not in account_seen:
                    account = ({"metrics": result["account_metrics"], "status": "COLLECTED"} if result.get("account_metrics")
                               else (account_collector or collect_account_metrics)(route))
                    metrics["_account_snapshot"] = {"metrics": account.get("metrics") or {}, "status": account.get("status"),
                        "collected_at_utc": datetime.now(timezone.utc).isoformat(), "limitations": account.get("limitations") or []}
                    account_seen.add(route)
                return {**result, "metrics": metrics, "interactions": []}
            result = perf.collect_observation(store, observation_id=row["observation_id"], collector=collect,
                                              now=datetime.now(timezone.utc), collection_clock=lambda: datetime.now(timezone.utc))
            if result["collection_status"] == "COLLECTED":
                object_cache[(route, row["public_object_id"])] = result
            outcomes.append({"observation_id": row["observation_id"], "platform": route, "status": result["collection_status"]})
        return {"state": "COLLECTED", "scheduled": scheduled, "collected": len(outcomes),
                "pending": len(rows) - len(outcomes), "outcomes": outcomes, "excluded": excluded,
                "model_calls": 0, "public_write_performed": False}
    finally:
        store.release_lease(lease["lease_id"], owner, lease["fencing_token"])
