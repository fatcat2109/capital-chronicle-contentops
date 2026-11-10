"""CC-394: Main's outcomes in one pinned Telegram message, outside feed cadence.

The existing minute consumer calls the sole publication coordinator. Its existing
store/outbox holds immutable revisions, one public-object binding and readbacks.
No price lookup, scoring, scheduler, feed post or separate publication store.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import urllib.error
import urllib.request
from uuid import uuid4
from zoneinfo import ZoneInfo

from .event_article_guard_v1 import PUBLIC_NOTICE, CONFLICTS_NOTICE, check_publication_copy
from .plan_status_export_contract_v1 import validate_export_contract
from .plan_status_posts_v1 import (
    EXPORT_DIR, MAIN_ROOT, EXPORT_MAX_AGE_MINUTES, _display_plan, _instrument_title,
    _level, _utc, export_freshness, read_export, result_rows_from_export,
)

TITLE = "Capital Chronicle | Public call results"
WORK = "pinned-result-scorecard-v1"
DESTINATION = "internal:pinned-result-scorecard"
ANCHOR = WORK + "-anchor"
OBJECT = WORK + "-object"
CHAT = "@CapitalChronicle"
LIMIT = 4096
ET = ZoneInfo("America/New_York")
RESULTS = ("HIT", "STOPPED", "EXPIRED", "NOT_TRIGGERED")


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _hash(value):
    return hashlib.sha256(_json(value).encode()).hexdigest()


def text_length(text):
    # Telegram entity offsets use UTF-16. This also bounds supplementary letters.
    return len(text.encode("utf-16-le")) // 2


def project(export, *, now=None, retained_rows=()):
    """All explicit outcomes, irrespective of result-post selection or age."""
    validate_export_contract(export)
    now = now or datetime.now(timezone.utc)
    freshness = export_freshness(export, now)
    if not 0 <= freshness["export_age_seconds"] <= EXPORT_MAX_AGE_MINUTES * 60:
        raise ValueError("SCORECARD_EXPORT_STALE_OR_FUTURE")
    plans = {p["plan_id"]: p for p in export["status"]["plans"]}
    rows = {r["plan_id"]: r for r in retained_rows}
    for row in result_rows_from_export(export, include_not_triggered=True):
        plan = plans[row["plan_id"]]
        score = (plan.get("outcome") or {}).get("score") or {}
        if (_utc(row["at_utc"]) > now
                or (score.get("scored_at_utc") and _utc(score["scored_at_utc"]) > now)):
            raise ValueError("SCORECARD_RESULT_FROM_FUTURE")
        display = _display_plan(row["plan"])
        direction = display.get("direction")
        if direction not in {"bullish", "bearish"}:
            raise ValueError("SCORECARD_DIRECTION_INVALID")
        low, high = display.get("zone_low"), display.get("zone_high")
        try:
            lower, upper = Decimal(str(low)), Decimal(str(high))
        except InvalidOperation:
            raise ValueError("SCORECARD_ZONE_INVALID") from None
        if not lower.is_finite() or not upper.is_finite() or lower > upper:
            raise ValueError("SCORECARD_ZONE_INVALID")
        # This field remains absent until Main exports it. Never infer it from prices.
        end_direction = score.get("direction_at_window_end")
        if end_direction not in {None, "BULLISH", "BEARISH", "FLAT"}:
            raise ValueError("SCORECARD_END_DIRECTION_INVALID")
        line = (f"{_utc(row['at_utc']).astimezone(ET):%Y-%m-%d} ET | "
                f"{_instrument_title(row['symbol'], row['plan'])} | original direction was {direction} | "
                f"entry zone {_level(low)}–{_level(high)}"
                + (" (plan levels)" if display.get("price_basis") == "plan" else "")
                + f" | {row['result'].replace('_', ' ')}"
                + (" (untriggered; not scored)" if not row["scored"] else "")
                + (" (correction)" if row.get("corrects_outcome_id") else "")
                + (" | end direction: " + end_direction.lower() if end_direction else ""))
        projected = {k: row.get(k) for k in (
            "plan_id", "outcome_id", "score_hash", "at_utc", "result", "scored", "corrects_outcome_id")}
        projected.update(line=line, scored_at_utc=score.get("scored_at_utc"),
                         direction_at_window_end=end_direction)
        previous = rows.get(row["plan_id"])
        # A temporary incomplete export cannot erase a held, explicit score.
        if previous and previous["scored"] and not row["scored"]:
            continue
        if previous and previous.get("scored_at_utc") and projected.get("scored_at_utc"):
            if _utc(previous["scored_at_utc"]) > _utc(projected["scored_at_utc"]):
                continue
        rows[row["plan_id"]] = projected
    ordered = sorted(rows.values(), key=lambda r: (_utc(r["at_utc"]), r["plan_id"]), reverse=True)
    counts = {key: Counter(r["result"] for r in ordered)[key] for key in RESULTS}
    counts.update(total=len(ordered), scored=sum(r["scored"] for r in ordered))
    text, shown = render(ordered, counts)
    return {"schema_version": "contentops.pinned_result_scorecard.v1", "rows": ordered,
            "counts": counts, "text": text, "shown": shown,
            "export_content_hash": export["status"]["content_hash"], **freshness}


def render(rows, counts):
    header = (f"{TITLE}\nResults: {counts['total']} | HIT: {counts['HIT']} | STOPPED: {counts['STOPPED']} | "
              f"EXPIRED: {counts['EXPIRED']} | NOT TRIGGERED: {counts['NOT_TRIGGERED']}\n"
              f"Scored: {counts['scored']}; unscored expiries: {counts['total'] - counts['scored']}.\n\n")
    footer = ("\n\nNewest results first; the weekly wrap keeps the complete record. "
              "Results describe resolved conditional model calls.\n\n"
              f"{PUBLIC_NOTICE} {CONFLICTS_NOTICE}")
    selected = []
    for row in rows:
        if text_length(header + "\n".join([*selected, row["line"]]) + footer) > LIMIT:
            break  # Keep whole newest lines; never silently favour a result type.
        selected.append(row["line"])
    if rows and not selected:
        raise ValueError("SCORECARD_RESULT_LINE_EXCEEDS_MESSAGE_LIMIT")
    body = "\n".join(selected) if selected else "No resolved calls supplied by Main yet."
    text = header + body + footer
    if text_length(text) > LIMIT:
        raise ValueError("SCORECARD_MESSAGE_EXCEEDS_LIMIT")
    check_publication_copy({"body": text})
    return text, len(selected)


class TelegramScorecardError(ValueError):
    def __init__(self, cause, *, definite=False):
        self.definite = definite
        super().__init__(cause)


class TelegramScorecardAPI:
    """Official Bot API only. Exceptions never expose token-bearing URLs."""
    def call(self, method, **fields):
        from .secret_store_v1 import read_secret
        if method not in {"getChat", "sendMessage", "editMessageText", "pinChatMessage"}:
            raise ValueError("SCORECARD_BOT_METHOD_NOT_ALLOWED")
        token = read_secret("TELEGRAM_BOT_TOKEN")
        if not token:
            raise TelegramScorecardError("TELEGRAM_BOT_TOKEN_UNAVAILABLE", definite=True)
        request = urllib.request.Request("https://api.telegram.org/bot" + token + "/" + method,
            data=_json({"chat_id": CHAT, **fields}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                data = json.load(response)
        except urllib.error.HTTPError as exc:
            try:
                data = json.loads(exc.read())
            except (ValueError, OSError):
                data = {}
            if exc.code == 400 and "message is not modified" in str(data.get("description", "")).lower():
                return {"not_modified": True}
            raise TelegramScorecardError(f"TELEGRAM_SCORECARD_HTTP_{exc.code}",
                                        definite=400 <= exc.code < 500) from None
        except Exception:
            raise TelegramScorecardError("TELEGRAM_SCORECARD_TRANSPORT_UNCERTAIN") from None
        if data.get("ok") is not True:
            raise TelegramScorecardError("TELEGRAM_SCORECARD_API_NOT_CONFIRMED")
        return data.get("result")


def _message_matches(message, text, object_id=None):
    return (isinstance(message, dict) and message.get("text") == text
            and (object_id is None or str(message.get("message_id")) == str(object_id))
            and str(message.get("message_id", "")).isdigit()
            and (message.get("chat") or {}).get("username", "").casefold() == "capitalchronicle"
            and (message.get("chat") or {}).get("type") == "channel")


def _save(store, key, destination, payload, status):
    return store.register_outbox_message(message_id=key, work_item_id=WORK,
        destination=destination, payload=_json(payload), status=status)


def _confirm(store, revision, object_id, message, now):
    # Recovery also covers a crash after saving the readback but before the
    # revision status changes. Do not rewrite the first observation's clock.
    existing = store.get_outbox_message(revision + "-readback")
    if existing:
        observation = json.loads(existing["payload"])
        if observation["message_id"] != str(object_id) or observation["text"] != message["text"]:
            raise ValueError("SCORECARD_READBACK_IDENTITY_CONFLICT")
    else:
        _save(store, revision + "-readback", DESTINATION + "-readback",
            {"message_id": str(object_id), "text": message["text"],
             "chat_username": "CapitalChronicle", "pinned": True,
             "observed_at_utc": now.isoformat()}, "CONFIRMED")
    store.set_outbox_status(revision, "CONFIRMED")


def update_scorecard(coordinator, export, *, now=None, api=None):
    """Called by DurablePublicationCoordinator, serialized by its existing store lease."""
    now = now or datetime.now(timezone.utc)
    store = coordinator.store
    if coordinator._mode() != "AUTONOMOUS_DEFAULT":
        return {"status": "CONTROLLED_NO_PUBLIC_WRITE", "cause": "SCORECARD_KILL_SWITCH"}
    from .durable_operational_store_v1 import LeaseConflictError
    owner = "scorecard-" + uuid4().hex
    try:
        lease = store.acquire_lease(WORK, owner, ttl_seconds=180)
    except LeaseConflictError:
        return {"status": "IN_PROGRESS", "cause": "SCORECARD_EXACT_OBJECT_UPDATE_ACTIVE"}
    try:
        revisions = store.list_outbox_messages(destination=DESTINATION)
        retained = json.loads(revisions[-1]["payload"])["rows"] if revisions else []
        record = project(export, now=now, retained_rows=retained)
        revision = WORK + "-" + _hash({k: record[k] for k in ("rows", "counts", "text")})
        store.create_work_item(story_id=WORK, title="Pinned public call results", target_surface="TELEGRAM",
                               work_item_id=WORK)
        prior = store.get_outbox_message(revision)
        if not prior:
            _save(store, revision, DESTINATION, record, "READY")
        api = api or TelegramScorecardAPI()

        def write(method, **fields):
            # The fuse may change while a network read is in flight.
            if coordinator._mode() != "AUTONOMOUS_DEFAULT":
                raise TelegramScorecardError("SCORECARD_KILL_SWITCH", definite=True)
            return api.call(method, **fields)

        chat = api.call("getChat")
        if (chat.get("username", "").casefold() != "capitalchronicle" or chat.get("type") != "channel"):
            raise TelegramScorecardError("SCORECARD_DESTINATION_IDENTITY_MISMATCH", definite=True)
        pinned = chat.get("pinned_message") or {}
        binding = store.get_outbox_message(OBJECT)
        bootstrap = store.get_outbox_message(ANCHOR)
        created = 0
        if not binding:
            if bootstrap and bootstrap["status"] in {"ATTEMPT_STARTED", "UNKNOWN_WRITE"}:
                initial = store.get_outbox_message(json.loads(bootstrap["payload"])["revision"])
                if not _message_matches(pinned, json.loads(initial["payload"])["text"]):
                    return {"status": "UNKNOWN_WRITE", "cause": "SCORECARD_BOOTSTRAP_EXACT_MESSAGE_READBACK_REQUIRED"}
                message = pinned
            else:
                if not bootstrap:
                    _save(store, ANCHOR, DESTINATION + "-anchor", {"revision": revision}, "READY")
                store.set_outbox_status(ANCHOR, "ATTEMPT_STARTED")
                try:
                    message = write("sendMessage", text=record["text"], disable_notification=True,
                                       link_preview_options={"is_disabled": True})
                except TelegramScorecardError as exc:
                    store.set_outbox_status(ANCHOR, "READY" if exc.definite else "UNKNOWN_WRITE")
                    return {"status": "DEFINITE_NO_WRITE" if exc.definite else "UNKNOWN_WRITE", "cause": str(exc)}
                if not _message_matches(message, record["text"]):
                    store.set_outbox_status(ANCHOR, "UNKNOWN_WRITE")
                    return {"status": "UNKNOWN_WRITE", "cause": "SCORECARD_BOOTSTRAP_RETURN_NOT_VERIFIED"}
                created = 1
            object_id = str(message["message_id"])
            _save(store, OBJECT, DESTINATION + "-object", {"message_id": object_id,
                "public_url": "https://t.me/CapitalChronicle/" + object_id}, "BOUND")
            store.set_outbox_status(ANCHOR, "BOUND")
        else:
            object_id = json.loads(binding["payload"])["message_id"]

        # Resolve every interrupted revision before another write. A returned old,
        # confirmed text is exact absence proof; an unrecognised edit stays uncertain.
        for pending in revisions:
            if pending["status"] not in {"ATTEMPT_STARTED", "UNKNOWN_WRITE"}:
                continue
            expected = json.loads(pending["payload"])["text"]
            if _message_matches(pinned, expected, object_id):
                _confirm(store, pending["message_id"], object_id, pinned, now)
            elif any(r["status"] == "CONFIRMED" and _message_matches(
                    pinned, json.loads(r["payload"])["text"], object_id) for r in revisions):
                store.set_outbox_status(pending["message_id"], "RECONCILED_ABSENT_SAFE_TO_RETRY")
            else:
                return {"status": "UNKNOWN_WRITE", "cause": "SCORECARD_EDIT_EXACT_MESSAGE_READBACK_REQUIRED",
                        "message_id": object_id}

        edited = 0
        if created:
            pass  # The send's exact Message is the Bot API text readback.
        elif _message_matches(pinned, record["text"], object_id):
            message = pinned
        else:
            store.set_outbox_status(revision, "ATTEMPT_STARTED")
            try:
                message = write("editMessageText", message_id=int(object_id), text=record["text"],
                                   link_preview_options={"is_disabled": True})
            except TelegramScorecardError as exc:
                store.set_outbox_status(revision, "READY" if exc.definite else "UNKNOWN_WRITE")
                return {"status": "DEFINITE_NO_WRITE" if exc.definite else "UNKNOWN_WRITE",
                        "cause": str(exc), "message_id": object_id}
            if not (message == {"not_modified": True} or _message_matches(message, record["text"], object_id)):
                store.set_outbox_status(revision, "UNKNOWN_WRITE")
                return {"status": "UNKNOWN_WRITE", "cause": "SCORECARD_EDIT_RETURN_NOT_VERIFIED",
                        "message_id": object_id}
            edited = int(message != {"not_modified": True})
        if not _message_matches(pinned, record["text"], object_id):
            write("pinChatMessage", message_id=int(object_id), disable_notification=True)
            pinned = (api.call("getChat") or {}).get("pinned_message") or {}
        if not _message_matches(pinned, record["text"], object_id):
            return {"status": "PIN_READBACK_REQUIRED", "message_id": object_id}
        if (store.get_outbox_message(revision) or {}).get("status") != "CONFIRMED":
            _confirm(store, revision, object_id, pinned, now)
        return {"status": "CONFIRMED", "message_id": object_id,
                "public_url": "https://t.me/CapitalChronicle/" + object_id,
                "counts": record["counts"], "shown": record["shown"], "characters": text_length(record["text"]),
                "revision": revision, "created_messages": created, "edited_messages": edited,
                "extra_result_feed_posts": 0}
    except TelegramScorecardError as exc:
        return {"status": "NOT_CONFIRMED", "cause": str(exc)}
    finally:
        store.release_lease(lease["lease_id"], owner, lease["fencing_token"])


def refresh_scorecard(store, export_dir=EXPORT_DIR, *, main_root=MAIN_ROOT, python=None, now=None, api=None,
                      dry_run=False):
    """One existing minute tick; failures stay local to the scorecard."""
    from .publication_coordinator_v1 import DurablePublicationCoordinator
    try:
        export = read_export(export_dir, main_root=main_root, python=python)
        if dry_run:
            return {"status": "PREVIEW", **project(export, now=now)}
        coordinator = DurablePublicationCoordinator(store=store, transport_runtime=None)
        return coordinator.update_pinned_result_scorecard(export, now=now, api=api)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        # Fixed local/contract errors only; transport exceptions are sanitized above.
        return {"status": "NOT_CONFIRMED", "cause": str(exc)[:240]}
