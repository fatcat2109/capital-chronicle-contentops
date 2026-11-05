"""CC-306 (decision 79, P3): one short post per change of plan state for the six markets.

Reads Main's plan-status export (CC-307), keeps the six first-phase markets, and composes one
short public post per transition. Exactly once: one outbox row per transition in the existing
ContentOps store, keyed on plan, state and time; Codex Publisher posts from that row through the
existing publication path. Wording follows decision 40 (a directional call only in its conditional
form, with the notices) and section 4.4 (plain words, no ids or internal terms, times in UTC).
No order, no price data and no write outside the store.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping

from live_contentops.event_article_guard_v1 import (
    CONFLICTS_NOTICE, PUBLIC_NOTICE, check_publication_copy, conditional_call_text,
)

SCHEMA = "contentops.plan_status_post.v1"
DESTINATION = "internal:plan-status-post"
WORK_ITEM_ID = "plan-status-posts-v1"
READY = "READY_FOR_PUBLISHER"
# Decision 79's first-phase markets, as the trading system names them.
MARKETS = {
    "XAUUSD": "gold", "US500": "the US 500 index", "EURUSD": "EUR/USD",
    "USDJPY": "USD/JPY", "USOIL": "US crude oil (WTI)", "BTCUSD": "Bitcoin",
}
TITLES = {"XAUUSD": "Gold", "US500": "US 500", "EURUSD": "EUR/USD", "USDJPY": "USD/JPY",
          "USOIL": "US crude oil", "BTCUSD": "Bitcoin"}
KINDS = {"WAITING": "setup", "TRIGGERED": "triggered", "CANCELLED": "cancelled",
         "INVALIDATED": "invalidated", "EXPIRED": "expired", "VIEW_CHANGED": "view_changed"}
# Section 4.4: none of these may reach a reader.
INTERNAL = re.compile(
    r"\b(?:frozen|committee|fixture|export|admission|deterministic|watch_runtime|plan_[0-9a-f]{6,}|"
    r"transition_[0-9a-f]+|[0-9a-f]{24,}|request-[0-9a-f]+)\b|\b[a-z]+_[a-z_]+\b", re.I)
FORBIDDEN = re.compile(r"\b(?:buy now|sell now|targets?|take profit|lots?|R:R)\b", re.I)


class PlanPostError(ValueError):
    """Fixed causes only."""


def _sha(value: Any) -> str:
    # Main's canonical JSON (execution_control_plane_v1.canonical_json): non-ASCII kept as is.
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _utc(value: Any) -> datetime:
    try:
        at = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise PlanPostError("PLAN_EXPORT_CLOCK_INVALID") from exc
    if at.tzinfo is None:
        raise PlanPostError("PLAN_EXPORT_CLOCK_INVALID")
    return at.astimezone(timezone.utc)


# CC-307's contract reader runs in Main's live root, in its own process: ContentOps and Main both
# have a namespace package named "tools", which must never merge in one interpreter.
MAIN_ROOT = Path(r"A:\Capital Chronicle\main-jim-research-dashboard-20261025")
EXPORT_DIR = Path(r"A:\Capital Chronicle\ResearchRuns\plan-status-v1")
_READER = """import datetime as dt, json, sys
from tools.product.plan_status_export_v1 import read_public_status, read_public_transitions
folder = sys.argv[1]
status = read_public_status(folder + "/plan-status.public.json", as_of=dt.datetime.now(dt.timezone.utc).isoformat())
events = read_public_transitions(folder + "/plan-transitions.public.json", status=status)
sys.stdout.write(json.dumps({"status": status, "transitions": events}))
"""


def read_export(export_dir: Path = EXPORT_DIR, *, main_root: Path = MAIN_ROOT, python: str | None = None) -> dict:
    """Both export documents, validated and joined by CC-307's own read_public_transitions."""
    import subprocess
    import sys
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    for attempt in (1, 2):
        done = subprocess.run([python or sys.executable, "-B", "-c", _READER, str(export_dir)], cwd=str(main_root),
                              capture_output=True, text=True, encoding="utf-8", timeout=120, creationflags=flags)
        if done.returncode == 0:
            return json.loads(done.stdout)
        cause = (done.stderr.strip().splitlines() or ["PLAN_EXPORT_READER_FAILED"])[-1]
        # The two files are replaced one after the other each minute: one bounded reread.
        if attempt == 1 and "SNAPSHOT_MISMATCH" in cause:
            continue
        name = cause.split(":", 1)[-1].strip() if "PlanStatusError" in cause else cause.split(":", 1)[0]
        raise PlanPostError("PLAN_EXPORT_UNREADABLE:" + re.sub(r"[^A-Za-z0-9_]", "", name)[:80])


def rows_from_export(export: Mapping[str, Any]) -> list[dict]:
    plans = {p["plan_id"]: p for p in export["status"].get("plans", []) if p.get("plan_id")}
    rows = []
    for event in export["transitions"].get("transitions", []):
        plan = plans.get(event.get("plan_id"))
        if plan is None:
            raise PlanPostError("PLAN_EXPORT_TRANSITION_UNKNOWN_PLAN")
        rows.append(_row(plan_id=event["plan_id"], symbol=plan.get("asset_id"), to=event.get("status"),
                         at_utc=event.get("at_utc"), cause=event.get("reason_code"), plan=_built_plan(plan)))
    return rows


def read_transitions(export_dir: Path = EXPORT_DIR, **kwargs) -> list[dict]:
    if not (Path(export_dir) / "plan-status.public.json").is_file():
        return []
    return rows_from_export(read_export(export_dir, **kwargs))


def _built_plan(plan: Mapping[str, Any]) -> dict:
    zone = plan.get("zone") or {}
    direction = {"BULLISH": "bullish", "BEARISH": "bearish"}.get(plan.get("direction"))
    below = direction == "bullish"
    invalid = [p["threshold"] for p in plan.get("invalidation_conditions") or []
               if p.get("operator") in ({"LT", "LTE"} if below else {"GT", "GTE"})
               and p.get("field") in {"low", "close", "bid", "mid"} | ({"high", "ask"} if not below else set())]
    return {"direction": direction, "zone_low": zone.get("minimum"), "zone_high": zone.get("maximum"),
            "cancel_level": plan.get("cancel_level"),
            "target": plan.get("target", plan.get("target_level")),
            "invalidation_level": (max(invalid) if below else min(invalid)) if invalid else None,
            "valid_until_utc": plan.get("entry_deadline_utc") or plan.get("expires_at_utc")}


def _row(*, plan_id, symbol, to, at_utc, cause, plan):
    if not plan_id or to not in KINDS or not at_utc:
        raise PlanPostError("PLAN_EXPORT_TRANSITION_INVALID")
    at = _utc(at_utc).isoformat().replace("+00:00", "Z")
    return {"key": "plan-status-post-" + hashlib.sha256(f"{plan_id}|{to}|{at}".encode()).hexdigest()[:32],
            "plan_id": plan_id, "symbol": symbol, "to": to, "at_utc": at, "cause": cause, "plan": plan}


def _level(value) -> str:
    number = Decimal(str(value)).normalize()
    text = f"{number:,f}"
    return text


def _when(value) -> str:
    at = _utc(value)
    return f"{at:%a} {at.day} {at:%b}, {at:%H:%M} UTC"


def _cancel_level_is_public(plan: Mapping[str, Any]) -> bool:
    """Decision 40: no target in public copy. A runaway cancel often sits at the target, so the
    number prints only when a target is known and the cancel level is clear of it."""
    cancel, target = plan.get("cancel_level"), plan.get("target")
    if target is None:
        return False  # unknown target (CC-307's rows carry none today): never risk revealing it
    if isinstance(target, Mapping):
        low, high = target.get("minimum", target.get("low")), target.get("maximum", target.get("high"))
        return low is not None and high is not None and not (float(low) <= float(cancel) <= float(high))
    if isinstance(target, (list, tuple)):
        return bool(target) and not (min(map(float, target)) <= float(cancel) <= max(map(float, target)))
    return float(cancel) != float(target)


def compose(row: Mapping[str, Any]) -> dict:
    """One short post for one transition, or a named cause it is not posted."""
    symbol, plan = row["symbol"], row["plan"]
    if symbol not in MARKETS:
        return {"status": "NOT_A_FIRST_PHASE_MARKET"}
    market, title = MARKETS[symbol], TITLES[symbol]
    if plan.get("direction") not in {"bullish", "bearish"}:
        return {"status": "NOT_POSTED", "cause": "PLAN_DIRECTION_MISSING"}
    if plan.get("zone_low") is None or plan.get("zone_high") is None:
        return {"status": "NOT_POSTED", "cause": "PLAN_ZONE_MISSING"}
    if plan.get("invalidation_level") is None:
        # Decision 40: every public call shows its invalidation level.
        return {"status": "NOT_POSTED", "cause": "PLAN_INVALIDATION_LEVEL_MISSING"}
    zone = f"{_level(plan['zone_low'])}–{_level(plan['zone_high'])}"
    side = "below" if plan["direction"] == "bullish" else "above"
    invalid = f"price moves {side} {_level(plan['invalidation_level'])}"
    calls, kind, to = [], KINDS[row["to"]], row["to"]
    if to == "WAITING":
        if not plan.get("valid_until_utc"):
            return {"status": "NOT_POSTED", "cause": "PLAN_VALIDITY_MISSING"}
        call = {"condition": f"price trades into {zone}", "direction": plan["direction"], "market": market,
                "horizon": f"the period to {_when(plan['valid_until_utc'])}", "invalidation": invalid}
        calls = [call]
        lines = [f"{title}: new plan.", conditional_call_text(call)]
        if plan.get("cancel_level") is not None:
            if _cancel_level_is_public(plan):
                lines.append(f"If price reaches {_level(plan['cancel_level'])} before that, the plan is cancelled.")
            else:
                lines.append("If price runs away before any pullback, the plan is cancelled and we re-assess.")
    elif to == "TRIGGERED":
        lines = [f"{title}: the plan with the {zone} entry zone is now active.",
                 f"Price reached the zone at {_when(row['at_utc'])}.",
                 f"It is invalidated if {invalid}."]
    elif to in {"CANCELLED", "INVALIDATED"}:
        reason = {
            "RUNAWAY_CANCEL": "price moved away before reaching the zone",
            "GAP_OR_ENTRY_BOUNDS_CROSSED": "price jumped past the zone",
            "WATCH_INVALIDATED": f"{invalid} before reaching the zone".replace("price moves", "price moved"),
            "INVALIDATED": f"{invalid} before reaching the zone".replace("price moves", "price moved"),
        }.get(str(row.get("cause") or ""), "the plan was withdrawn before reaching the zone")
        lines = [f"{title}: the plan with the {zone} entry zone is {'invalidated' if to == 'INVALIDATED' else 'cancelled'}"
                 f" at {_when(row['at_utc'])}: {reason}.", "It ended without an entry. We are reassessing."]
    elif to == "EXPIRED":
        lines = [f"{title}: the plan with the {zone} entry zone expired at {_when(row['at_utc'])}"
                 " without price reaching the zone.", "It ended without an entry."]
    else:
        lines = [f"{title}: our view changed at {_when(row['at_utc'])}, so the plan with the {zone} entry zone"
                 " is withdrawn."]
    text = " ".join(lines) + f"\n\n{PUBLIC_NOTICE} {CONFLICTS_NOTICE}"
    check_publication_copy({"title": title, "body": text}, conditional_calls=calls)
    if INTERNAL.search(text) or FORBIDDEN.search(text):
        raise PlanPostError("PLAN_POST_INTERNAL_OR_FORBIDDEN_WORDS")
    return {"status": "COMPOSED", "kind": kind, "text": text, "conditional_calls": calls}


POSTING_WINDOW_MINUTES = 60


def queue_posts(store, export_dir: Path = EXPORT_DIR, *, now: datetime | None = None,
                window_minutes: int = POSTING_WINDOW_MINUTES, dry_run: bool = False, **reader) -> dict:
    """Register one outbox row per new transition for the six markets; repeats change nothing.

    The export carries every plan's whole history (back to 27 Oct on 5 Nov). A status post is
    news only while it is recent, so a transition older than the posting window is counted and
    never posted. A dry run reads the store but writes nothing.
    """
    try:
        rows = read_transitions(export_dir, **reader)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {"status": "EXPORT_UNREADABLE", "cause": str(exc) if isinstance(exc, PlanPostError) else type(exc).__name__}
    now = now or datetime.now(timezone.utc)
    oldest = now.timestamp() - window_minutes * 60
    queued, existing, skipped, too_old = [], [], [], 0
    fresh = [row for row in rows if row["symbol"] in MARKETS]
    for row in fresh:
        if _utc(row["at_utc"]).timestamp() < oldest:
            too_old += 1
            continue
        post = compose(row)
        if post["status"] != "COMPOSED":
            skipped.append({"key": row["key"], "cause": post.get("cause")})
            continue
        if store.get_outbox_message(row["key"]):
            existing.append(row["key"])
            continue
        payload = {"schema_version": SCHEMA, "key": row["key"], "plan_id": row["plan_id"],
                   "symbol": row["symbol"], "state": row["to"],
                   "at_utc": row["at_utc"], "kind": post["kind"], "text": post["text"],
                   "conditional_calls": post["conditional_calls"]}
        queued.append({"key": row["key"], "symbol": row["symbol"], "state": row["to"], "at_utc": row["at_utc"],
                       "text": post["text"]})
        if dry_run:
            continue
        store.create_work_item(story_id=WORK_ITEM_ID, title="Plan status posts (decision 79)",
                               target_surface="MULTI_PLATFORM", work_item_id=WORK_ITEM_ID)
        store.register_outbox_message(message_id=row["key"], work_item_id=WORK_ITEM_ID, destination=DESTINATION,
                                      payload=json.dumps(payload, sort_keys=True, ensure_ascii=False), status=READY)
    latest = {}
    for row in sorted(fresh, key=lambda r: r["at_utc"]):
        latest[row["plan_id"]] = row["to"]
    return {"status": "OK", "dry_run": dry_run, "transitions_read": len(rows), "six_market_transitions": len(fresh),
            "latest_states": latest,
            "older_than_window": too_old, "window_minutes": window_minutes,
            "queued" if not dry_run else "would_queue": queued,
            "already_queued": existing, "not_posted": skipped}


# ---------------------------------------------------------------------------------------------
# CC-306 posting step: one READY_FOR_PUBLISHER row becomes one coordinator plan for X, Threads,
# Telegram and Discord (Ops Product, 5 Nov: status posts stay off LinkedIn, Facebook and
# Instagram). Like the daily digest, the plan freezes its validated copy per destination; the
# sole coordinator owns exactly-once, UNKNOWN_WRITE and readback. No Substack canonical: the
# link is the market's page on the site (the preview until CC-305 publishes).
# ---------------------------------------------------------------------------------------------
POST_DESTINATIONS = ("telegram", "discord", "threads", "x")
SITE_ASSET_URL = "https://fatcat2109.github.io/capital-chronicle-preview/assets/{symbol}.html"
POST_ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\plan-status-posts")
STATE_WORDS = {"WAITING": "new plan", "TRIGGERED": "plan now active", "CANCELLED": "plan cancelled",
               "INVALIDATED": "plan invalidated", "EXPIRED": "plan expired", "VIEW_CHANGED": "view changed"}
LIMITS = {"x": 280, "threads": 500, "telegram": 1024, "discord": 2000}
X_URL_LENGTH = 23  # X counts every link as 23 characters


def _row_payload(store, key: str) -> dict:
    row = store.get_outbox_message(key)
    if not row or row["destination"] != DESTINATION:
        raise PlanPostError("PLAN_STATUS_POST_ROW_REQUIRED")
    payload = json.loads(row["payload"])
    if payload.get("schema_version") != SCHEMA or payload.get("key") != key or payload.get("symbol") not in MARKETS:
        raise PlanPostError("PLAN_STATUS_POST_ROW_INVALID")
    return payload


def _split(text: str) -> tuple[str, str]:
    body, _, notices = text.partition("\n\n")
    if notices.strip() != f"{PUBLIC_NOTICE} {CONFLICTS_NOTICE}":
        raise PlanPostError("PLAN_STATUS_POST_NOTICES_REQUIRED")
    return body.strip(), notices.strip()


def _x_length(text: str) -> int:
    return len(re.sub(r"https://\S+", "x" * X_URL_LENGTH, text))


def destination_payloads(row: Mapping[str, Any], *, card_id: str) -> dict:
    """The exact copy per destination: the post, the market page link and the notices."""
    body, notices = _split(row["text"])
    url = SITE_ASSET_URL.format(symbol=row["symbol"])
    link = f"The live plan: {url}"
    payloads = {}
    for destination in POST_DESTINATIONS:
        text = f"{body}\n\n{link}\n\n{notices}"
        if destination == "x" and _x_length(text) > LIMITS["x"]:
            # Whole sentences per post: the link with the first, the notices last.
            sentences = re.split(r"(?<=\.)\s+(?=[A-Z])", body)
            chunks, current = [], ""
            for sentence in sentences:
                candidate = f"{current} {sentence}".strip()
                room = LIMITS["x"] - (X_URL_LENGTH + len("The live plan: ") + 2 if not chunks else 0)
                if current and _x_length(candidate) > room:
                    chunks.append(current)
                    current = sentence
                else:
                    current = candidate
            chunks.append(current)
            chunks[0] = f"{chunks[0]}\n\n{link}"
            chunks.append(notices)
            if any(_x_length(c) > LIMITS["x"] for c in chunks):
                raise PlanPostError("PLAN_STATUS_POST_TOO_LONG_FOR_X")
            posts = [{"text": c, "media_asset_ids": [card_id] if i == 0 else [], "order": i,
                      "role": "root" if i == 0 else "reply"} for i, c in enumerate(chunks)]
            payloads[destination] = {"destination": destination, "text": chunks[0], "posts": posts,
                                     "root_text": chunks[0], "reply_texts": chunks[1:],
                                     "full_text": "\n\n".join(chunks), "media_asset_ids": [card_id]}
            continue
        if (_x_length(text) if destination == "x" else len(text)) > LIMITS[destination]:
            raise PlanPostError("PLAN_STATUS_POST_TOO_LONG:" + destination)
        payloads[destination] = {"destination": destination, "text": text, "full_text": text,
                                 "media_asset_ids": [card_id]}
    return payloads


def card_article(row: Mapping[str, Any]) -> dict:
    at = _utc(row["at_utc"])
    return {"title": f"{TITLES[row['symbol']]}: {STATE_WORDS[row['state']]}",
            "dek": _split(row["text"])[0], "display_date": f"{at:%B} {at.day}, {at.year}",
            "author_identity": "Capital Chronicle", "publisher_identity": "Capital Chronicle"}


def prepare_post(store, key: str, *, root: Path = POST_ROOT, host=None) -> dict:
    """The post's package (title card, hosted copy, run context) and its coordinator plan."""
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes
    from live_contentops.destination_transport_registry_v1 import REGISTRY_VERSION, registration_for_destination
    from live_contentops.post_visuals_v1 import build_post_title_card
    row = _row_payload(store, key)
    folder = Path(root) / key
    article = card_article(row)
    card = build_post_title_card(article, [], [], output_dir=folder, reason="CC306_PLAN_STATUS_POST")
    if host is None:
        from live_contentops.cloudinary_delivery_media_v1 import prepare_cloudinary_delivery_media as host
    manifest_path = folder / "delivery_media_manifest_v1.json"
    existing = json.loads(manifest_path.read_bytes()) if manifest_path.is_file() else None
    delivery = host(work_item_id=key, delivery_only_assets=[], existing_manifest=existing,
                    article_assets=[card], article=article, source_documents=[])
    if delivery.get("status") != "CLOUDINARY_DELIVERY_MEDIA_READY":  # cloudinary_delivery_media_v1.READY
        raise PlanPostError("PLAN_STATUS_CARD_HOSTING_" + str(delivery.get("status") or "FAILED"))
    manifest_path.write_bytes(canonical_bytes(delivery["manifest"]))  # the hosting result wraps it
    payloads = destination_payloads(row, card_id=card["asset_id"])
    context = {"schema_version": "contentops.plan_status_post_context.v1", "article": {**article, "body": row["text"]},
               "selection": {}, "media": {"assets": [card]}, "plan_status_post": key}
    (folder / "run_context_v1.json").write_bytes(canonical_bytes(context))
    url = SITE_ASSET_URL.format(symbol=row["symbol"])
    rows = []
    for destination in POST_DESTINATIONS:
        registration = registration_for_destination(destination)
        text = payloads[destination]["full_text"]
        rows.append({"destination": destination, "platform": registration.platform,
                     "surface": registration.surface, "transport_type": registration.transport_type,
                     "transport_registry_version": REGISTRY_VERSION, "payload": text,
                     "payload_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(), "canonical_url": url,
                     "expected_destination_identity": registration.expected_identity})
    return {"schema_version": "contentops.publication_plan.v1", "plan_status_post": key,
            "plan_hash": hashlib.sha256(("plan-status-post:" + key).encode()).hexdigest(),
            "story_identity": key, "article_identity": key, "package_identity": key,
            "publication_window": {"window_identity": key}, "output_dir": str(folder.resolve()),
            "status_post_card_id": card["asset_id"], "transport_registry_version": REGISTRY_VERSION,
            "policy_mode_version": "AUTONOMOUS_DEFAULT:cc306.v1", "destinations": rows}


def _expected(store, key: str, output_dir: str) -> tuple[dict, dict]:
    row = _row_payload(store, key)
    context = json.loads((Path(output_dir) / "run_context_v1.json").read_bytes())
    if context.get("plan_status_post") != key:
        raise PlanPostError("PLAN_STATUS_POST_PACKAGE_MISMATCH")
    card_id = context["media"]["assets"][0]["asset_id"]
    return row, destination_payloads(row, card_id=card_id)


def validate_status_post_plan(store, work_item_id: str, plan: Mapping[str, Any]) -> dict:
    key = str(plan.get("plan_status_post") or "")
    if work_item_id != key:
        raise PlanPostError("PLAN_STATUS_POST_WORK_ITEM_MISMATCH")
    row, payloads = _expected(store, key, str(plan.get("output_dir") or ""))
    for item in plan.get("destinations") or []:
        destination = item.get("destination")
        if (destination not in payloads or item.get("payload") != payloads[destination]["full_text"]
                or item.get("canonical_url") != SITE_ASSET_URL.format(symbol=row["symbol"])):
            raise PlanPostError("PLAN_STATUS_POST_PLAN_COPY_CHANGED")
    return {"key": key, "payloads": payloads}


def validate_status_post_intent(store, intent: Mapping[str, Any]) -> None:
    """Re-checked immediately before every write: the frozen copy is still the stored post's."""
    key = str(intent.get("plan_status_post") or "")
    row, payloads = _expected(store, key, str(intent.get("output_dir") or ""))
    destination = str((intent.get("destination_plan") or {}).get("destination") or "")
    if intent.get("work_item_id") != key or intent.get("native_payload") != payloads.get(destination):
        raise PlanPostError("PLAN_STATUS_POST_INTENT_COPY_CHANGED")
    check_publication_copy({"post": payloads[destination]["full_text"]},
                           conditional_calls=row.get("conditional_calls") or [])


FRESHNESS_MINUTES = 60
STALE = "STALE_NOT_POSTED"
SUPERSEDED = "SUPERSEDED_NOT_POSTED"


def _age_minutes(payload, now):
    return (now - _utc(payload["at_utc"])).total_seconds() / 60


def publish_ready(store, *, latest_states=None, now: datetime | None = None, coordinator_for=None,
                  root: Path = POST_ROOT, host=None, limit: int = 5) -> dict:
    """Run each READY_FOR_PUBLISHER row through the sole coordinator. API destinations post now;
    X's BrowserOS Neo request waits for an agent turn. Repeats only resume the same dispatches.

    Freshness (Ops Product, 5 Nov): a row whose transition is older than 60 minutes when the
    poster first reaches it is marked stale and never posted. A "new plan" post whose plan has
    since moved on (triggered, cancelled, expired) is marked superseded and never posted.
    """
    now = now or datetime.now(timezone.utc)
    if coordinator_for is None:
        def coordinator_for(key, folder):
            from live_contentops.native_neo_executor_v1 import bind_native_neo_coordinator
            coordinator, _ = bind_native_neo_coordinator(
                store, operation_id=key, output_dir=folder / "native-neo",
                native_invocation_id="plan-status-posts-cc306", allow_publish=True)
            return coordinator
    results = []
    rows = [r for r in store.list_outbox_messages(destination=DESTINATION)
            if r["status"] in {READY, "PUBLISHING"}][:limit]
    for row in rows:
        key = row["message_id"]
        payload = json.loads(row["payload"])
        if row["status"] == READY:
            cause = None
            if _age_minutes(payload, now) > FRESHNESS_MINUTES:
                cause = (STALE, "TRANSITION_OLDER_THAN_60_MINUTES_WHEN_POSTER_REACHED_IT")
            elif (payload.get("state") == "WAITING" and latest_states is not None
                    and latest_states.get(payload.get("plan_id"), "WAITING") != "WAITING"):
                cause = (SUPERSEDED, "PLAN_ALREADY_" + str(latest_states[payload["plan_id"]]))
            if cause:
                store.set_outbox_status(key, cause[0])
                results.append({"key": key, "status": cause[0], "cause": cause[1]})
                continue
        try:
            plan = prepare_post(store, key, root=root, host=host)
            store.create_work_item(story_id=key, title="Plan status post", target_surface="MULTI_PLATFORM",
                                   work_item_id=key)
            coordinator = coordinator_for(key, Path(plan["output_dir"]))
            coordinator.register_plan(key, plan)
            outcome = coordinator.execute_plan(key, plan)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            results.append({"key": key, "status": "NOT_STARTED", "cause": str(exc)[:200]})
            continue
        per = {d: (o or {}).get("status") for d, o in (outcome.get("per_destination") or {}).items()}
        done = all(per.get(d) == "DISPATCH_CONFIRMED" for d in POST_DESTINATIONS)
        store.set_outbox_status(key, "PUBLISHED" if done else "PUBLISHING")
        results.append({"key": key, "status": "PUBLISHED" if done else "PUBLISHING", "per_destination": per})
    return {"status": "OK", "posts": results}


def pending_x(store, *, now: datetime | None = None) -> list[dict]:
    """X requests of status posts still waiting for an agent turn, freshest first."""
    from live_contentops.native_neo_executor_v1 import NativeNeoExecutor
    now = now or datetime.now(timezone.utc)
    pending = []
    for row in store.list_outbox_messages(destination=DESTINATION):
        if row["status"] != "PUBLISHING":
            continue
        payload = json.loads(row["payload"])
        executor = NativeNeoExecutor(store, operation_id=row["message_id"], output_dir=POST_ROOT / row["message_id"]
                                     / "native-neo", native_invocation_id="plan-status-posts-cc306",
                                     allow_publish=True, identity_at_action=True)
        for packet in executor.pending():
            request = packet["request"]
            if request.get("destination") == "x":
                pending.append({"key": row["message_id"], "request_sha256": request["request_sha256"],
                                "action": request["action"], "age_minutes": round(_age_minutes(payload, now), 1),
                                "fresh": _age_minutes(payload, now) <= FRESHNESS_MINUTES})
    return sorted(pending, key=lambda p: p["age_minutes"])


def begin_x(store, key: str, request_sha256: str, *, native_invocation_id: str, now: datetime | None = None):
    """The agent's claim for a status post's X request; a stale post is never claimed for a write."""
    from live_contentops.native_neo_executor_v1 import NativeNeoExecutor
    now = now or datetime.now(timezone.utc)
    payload = _row_payload(store, key)
    executor = NativeNeoExecutor(store, operation_id=key, output_dir=POST_ROOT / key / "native-neo",
                                 native_invocation_id=native_invocation_id, allow_publish=True,
                                 identity_at_action=True)
    packet = executor._get(request_sha256, "request")
    if not packet or packet["request"].get("destination") != "x":
        raise PlanPostError("PLAN_STATUS_X_REQUEST_REQUIRED")
    if packet["request"]["action"] == "PUBLISH" and _age_minutes(payload, now) > FRESHNESS_MINUTES:
        raise PlanPostError("PLAN_STATUS_X_STALE_NOT_POSTED: transition older than 60 minutes")
    return executor.begin(request_sha256)


def submit_x(store, key: str, request_sha256: str, response: Mapping[str, Any], *, native_invocation_id: str):
    """Save the agent's observed X return, then let the coordinator reconcile it."""
    from live_contentops.native_neo_executor_v1 import bind_native_neo_coordinator
    coordinator, executor = bind_native_neo_coordinator(
        store, operation_id=key, output_dir=POST_ROOT / key / "native-neo",
        native_invocation_id=native_invocation_id, allow_publish=True)
    submitted = executor.submit(request_sha256, response)
    packet = executor._get(request_sha256, "request")
    result = response.get("result") or {}
    if (packet["request"]["action"] == "PUBLISH" and result.get("status") == "SUCCESS"
            and result.get("public_object_id") and result.get("public_object_url")):
        submitted["completed_write_reconciliation"] = coordinator.reconcile_completed_native_publish(
            packet["request"]["dispatch_attempt_identity"], request_hash=request_sha256)
    return submitted
