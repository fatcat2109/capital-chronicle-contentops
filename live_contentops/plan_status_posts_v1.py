"""CC-306 (decision 79, P3): one short post per change of plan state for the six markets.

Reads Main's plan-status export (CC-307), keeps the six first-phase markets, and composes one
short public post per transition. Exactly once: one outbox row per transition in the existing
ContentOps store, keyed on plan, state and time; Codex Publisher posts from that row through the
existing publication path. Wording follows decision 40 (a directional call only in its conditional
form, with the notices) and section 4.4 (plain words, no ids or internal terms, times in New York time, ET: Jim, 6 Nov, public posts use the most common time zone).
No order, no price data and no write outside the store.
"""
from __future__ import annotations

from zoneinfo import ZoneInfo
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
# CC-330: the export also carries FILLED (our DEMO order filled). Fills, positions and P&L are DEMO details and
# never public (decision 40), so the composer reads the state and never posts it.
PRIVATE_STATES = {"FILLED"}
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
    if not plan_id or (to not in KINDS and to not in PRIVATE_STATES) or not at_utc:
        raise PlanPostError("PLAN_EXPORT_TRANSITION_INVALID")
    at = _utc(at_utc).isoformat().replace("+00:00", "Z")
    return {"key": "plan-status-post-" + hashlib.sha256(f"{plan_id}|{to}|{at}".encode()).hexdigest()[:32],
            "plan_id": plan_id, "symbol": symbol, "to": to, "at_utc": at, "cause": cause, "plan": plan}


def _level(value) -> str:
    number = Decimal(str(value)).normalize()
    text = f"{number:,f}"
    return text


PUBLIC_TZ = ZoneInfo("America/New_York")  # Jim, 6 Nov: public times in ET; GMT+7 only when talking to Jim


def _when(value) -> str:
    at = _utc(value).astimezone(PUBLIC_TZ)
    return f"{at:%a} {at.day} {at:%b}, {at:%H:%M} ET"


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
    if row["to"] in PRIVATE_STATES:
        return {"status": "NOT_POSTED", "cause": "DEMO_FILL_NOT_PUBLIC"}
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
# Ops Product, 6 Nov: a later state (triggered, cancelled, invalidated, expired, view changed) of a plan
# whose post already went out still posts after the window, up to this many hours, with its true time:
# readers who saw the setup must not be left with a plan that has ended (decision 79's live status).
LATE_STATE_HOURS = 24
# Jim, 6 Nov: a 'withdrawn' post about a plan readers never saw only confuses them (EUR/USD: a new sell plan,
# then 'view changed' about an older plan whose setup post had been refused). Such states post only for an
# announced plan, and before any new plan queued in the same run.
WITHDRAWN = {"VIEW_CHANGED", "CANCELLED", "INVALIDATED", "EXPIRED"}
PUBLIC_LEVELS = ("direction", "zone_low", "zone_high", "invalidation_level", "valid_until_utc")


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
    announced = {json.loads(r["payload"]).get("plan_id") for r in store.list_outbox_messages(destination=DESTINATION)
                 if r["status"] == "PUBLISHED"}
    for row in sorted(fresh, key=lambda r: (r["to"] not in WITHDRAWN, r["at_utc"])):
        late = False
        if _utc(row["at_utc"]).timestamp() < oldest:
            if (row["to"] != "WAITING" and row["plan_id"] in announced
                    and _utc(row["at_utc"]).timestamp() >= now.timestamp() - LATE_STATE_HOURS * 3600):
                late = True
            else:
                too_old += 1
                continue
        if row["to"] in WITHDRAWN and row["plan_id"] not in announced:
            skipped.append({"key": row["key"], "cause": "PLAN_NEVER_ANNOUNCED"})
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
                   "conditional_calls": post["conditional_calls"],
                   # CC-314: the levels the post's image shows (the chart timeframe and the
                   # fallback fact card). Never the target or the cancel level (decision 40).
                   "levels": {k: row["plan"].get(k) for k in PUBLIC_LEVELS},
                   **({"late": True} if late else {})}
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
# The minute task posts only these (no agent needed). X is registered by the agent route.
API_DESTINATIONS = ("telegram", "discord", "threads")
# Jim's decision 83 (5 Nov): a status post carries no site link, only its text and image.
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


def destination_payloads(row: Mapping[str, Any], *, card_id: str, chart_credit: bool = False) -> dict:
    """The exact copy per destination: the post and the notices, no link (decision 83). With a
    TradingView snapshot, "Chart: TradingView" follows the post (Terms section 4, decision 82)."""
    body, notices = _split(row["text"])
    link = CHART_CREDIT if chart_credit else ""
    payloads = {}
    for destination in POST_DESTINATIONS:
        text = "\n\n".join(part for part in (body, link, notices) if part)
        if destination == "x" and _x_length(text) > LIMITS["x"]:
            # Whole sentences per post: the chart credit with the first, the notices last.
            sentences = re.split(r"(?<=\.)\s+(?=[A-Z])", body)
            chunks, current = [], ""
            for sentence in sentences:
                candidate = f"{current} {sentence}".strip()
                room = LIMITS["x"] - (_x_length(link) + 2 if link and not chunks else 0)
                if current and _x_length(candidate) > room:
                    chunks.append(current)
                    current = sentence
                else:
                    current = candidate
            chunks.append(current)
            if link:
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
            "dek": _split(row["text"])[0], "display_date": (lambda et: f"{et:%B} {et.day}, {et.year}")(at.astimezone(PUBLIC_TZ)),
            "author_identity": "Capital Chronicle", "publisher_identity": "Capital Chronicle"}


CHART_CREDIT = "Chart: TradingView"
SNAPSHOT_RUN_BUDGET_SECONDS = 150  # the minute task has 5 minutes; later posts in a busy tick use the card


def plan_facts(row: Mapping[str, Any]) -> list[tuple[str, str]]:
    """The fallback card's facts: the plan's zone, invalidation, status and time. No target."""
    levels = row.get("levels") or {}
    facts = []
    if levels.get("zone_low") is not None and levels.get("zone_high") is not None:
        facts.append(("Entry zone", f"{_level(levels['zone_low'])}–{_level(levels['zone_high'])}"))
    if levels.get("invalidation_level") is not None and levels.get("direction") in {"bullish", "bearish"}:
        side = "Below" if levels["direction"] == "bullish" else "Above"
        facts.append(("Invalidation", f"{side} {_level(levels['invalidation_level'])}"))
    state = STATE_WORDS.get(row.get("state"), "status update")
    facts.append(("Status", state[0].upper() + state[1:]))
    facts.append(("As of", _when(row["at_utc"])))
    return facts


def _post_image(row: Mapping[str, Any], folder: Path, *, snapshot=None, snapshot_allowed=None) -> tuple[dict, bool]:
    """CC-314 (decision 82): TradingView's snapshot of the market, or, if that fails, CC-290's
    fact card with the plan's numbers. Taken once per post: a resumed post reuses its image."""
    from live_contentops import tradingview_snapshot_v1 as tv
    context_path = folder / "run_context_v1.json"
    if context_path.is_file():
        prior = json.loads(context_path.read_bytes())
        assets = (prior.get("media") or {}).get("assets") or []
        if assets and Path(assets[0]["path"]).is_file() \
                and hashlib.sha256(Path(assets[0]["path"]).read_bytes()).hexdigest() == assets[0]["sha256"]:
            return assets[0], bool(prior.get("chart_credit"))
    market = row["symbol"]
    interval = tv.interval_for((row.get("levels") or {}).get("valid_until_utc"), row["at_utc"])
    media_dir = folder / "media_assets"
    outcome = {"key": row["key"], "market": market, "interval": interval}
    if snapshot_allowed is None or snapshot_allowed():
        try:
            taken = (snapshot or tv.capture)(market, interval, media_dir)
            asset = tv.snapshot_asset(market, TITLES[market], taken, media_dir)
            tv.record_outcome({**outcome, "status": "CAPTURED", "asset_id": asset["asset_id"],
                               "seconds": taken.get("seconds")})
            return asset, True
        except Exception as exc:  # noqa: BLE001 - a failed snapshot never stops the post
            tv.record_outcome({**outcome, "status": "FAILED",
                               "cause": str(exc)[:200]})
    else:
        tv.record_outcome({**outcome, "status": "SKIPPED_RUN_TIME_BUDGET"})
    at = _utc(row["at_utc"])
    card = tv.fallback_card(title=f"{TITLES[market]}: {STATE_WORDS.get(row.get('state'), 'status update')}",
                            facts=plan_facts(row), dated_line=f"{at:%B} {at.day}, {at.year}", out_dir=media_dir)
    return card, False


def _hosted(manifest_path: Path, card: Mapping[str, Any]) -> bool:
    """A verified hosted copy of exactly this card is already recorded (no provider call needed)."""
    if not manifest_path.is_file():
        return False
    try:
        manifest = json.loads(manifest_path.read_bytes())
    except ValueError:
        return False
    return any(a.get("sha256") == card["sha256"] == a.get("public_delivery_sha256")
               and a.get("local_public_hash_continuity") is True
               and str(a.get("verified_public_delivery_url") or "").startswith("https://")
               for a in manifest.get("assets") or [])


def prepare_post(store, key: str, *, root: Path = POST_ROOT, host=None,
                 destinations: tuple = POST_DESTINATIONS, snapshot=None, snapshot_allowed=None) -> dict:
    """The post's package (its image, hosted copy, run context) and its coordinator plan."""
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes
    from live_contentops.destination_transport_registry_v1 import REGISTRY_VERSION, registration_for_destination
    row = _row_payload(store, key)
    folder = Path(root) / key
    article = card_article(row)
    card, chart_credit = _post_image(row, folder, snapshot=snapshot, snapshot_allowed=snapshot_allowed)
    if host is None:
        from live_contentops.cloudinary_delivery_media_v1 import prepare_cloudinary_delivery_media as host
    manifest_path = folder / "delivery_media_manifest_v1.json"
    if not _hosted(manifest_path, card):
        existing = json.loads(manifest_path.read_bytes()) if manifest_path.is_file() else None
        # The snapshot and the plan card are post images only (never on a site page). An older
        # package's title card keeps its article-asset route.
        delivery_only = card.get("delivery_only") is True
        delivery = host(work_item_id=key, delivery_only_assets=[card] if delivery_only else [],
                        existing_manifest=existing, article_assets=[] if delivery_only else [card],
                        article=article, source_documents=[])
        if delivery.get("status") != "CLOUDINARY_DELIVERY_MEDIA_READY":  # cloudinary_delivery_media_v1.READY
            raise PlanPostError("PLAN_STATUS_CARD_HOSTING_" + str(delivery.get("status") or "FAILED"))
        manifest_path.write_bytes(canonical_bytes(delivery["manifest"]))  # the hosting result wraps it
    payloads = destination_payloads(row, card_id=card["asset_id"], chart_credit=chart_credit)
    context = {"schema_version": "contentops.plan_status_post_context.v1", "article": {**article, "body": row["text"]},
               "selection": {}, "media": {"assets": [card]}, "plan_status_post": key,
               "chart_credit": chart_credit}
    (folder / "run_context_v1.json").write_bytes(canonical_bytes(context))
    rows = []
    for destination in destinations:
        registration = registration_for_destination(destination)
        text = payloads[destination]["full_text"]
        rows.append({"destination": destination, "platform": registration.platform,
                     "surface": registration.surface, "transport_type": registration.transport_type,
                     "transport_registry_version": REGISTRY_VERSION, "payload": text,
                     "payload_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(), "canonical_url": None,
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
    return row, destination_payloads(row, card_id=card_id, chart_credit=bool(context.get("chart_credit")))


def validate_status_post_plan(store, work_item_id: str, plan: Mapping[str, Any]) -> dict:
    key = str(plan.get("plan_status_post") or "")
    if work_item_id != key:
        raise PlanPostError("PLAN_STATUS_POST_WORK_ITEM_MISMATCH")
    row, payloads = _expected(store, key, str(plan.get("output_dir") or ""))
    for item in plan.get("destinations") or []:
        destination = item.get("destination")
        if (destination not in payloads or item.get("payload") != payloads[destination]["full_text"]
                or item.get("canonical_url")):
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


def freshness_limit_minutes(payload) -> int:
    """60 minutes for a new post; a later state of an announced plan keeps LATE_STATE_HOURS."""
    return LATE_STATE_HOURS * 60 if payload.get("late") else FRESHNESS_MINUTES
SUPERSEDED = "SUPERSEDED_NOT_POSTED"


def _age_minutes(payload, now):
    return (now - _utc(payload["at_utc"])).total_seconds() / 60


def scope_to_post(coordinator, key: str, plan: Mapping[str, Any]) -> None:
    """Recovery sees this post's own rows only, as the daily digest does (5 Nov first post: a
    store-wide pass filed other pieces' Threads and LinkedIn readbacks under this post and its
    backlog held X). Exactly-once and the global store checks are unchanged."""
    coordinator.allow_prior_confirmed_distribution = True
    coordinator.recovery_scope = {"work_item_id": key, "plan": plan, "exact_work_item_only": True}


def _api_confirmed(store, key: str) -> bool:
    plan_hash = hashlib.sha256(("plan-status-post:" + key).encode()).hexdigest()
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
    for destination in API_DESTINATIONS:
        dispatch = store.get_platform_dispatch(DurablePublicationCoordinator._ids(key, plan_hash, destination)["dispatch_id"])
        if not dispatch or dispatch["status"] != "DISPATCH_CONFIRMED":
            return False
    return True


def publish_ready(store, *, latest_states=None, now: datetime | None = None, coordinator_for=None,
                  root: Path = POST_ROOT, host=None, limit: int = 5, snapshot=None) -> dict:
    """Post fresh rows to the API destinations (Telegram, Discord, Threads) through the sole
    coordinator, and exit. Never waits on agent work: X is not in this plan (see start_x).

    Freshness (Ops Product, 5 Nov): a row whose transition is older than 60 minutes when the
    poster reaches it is marked stale and never posted. A "new plan" post whose plan has since
    moved on (triggered, cancelled, expired) is marked superseded and never posted. A fresh row
    whose API copies are not all confirmed yet is resumed (the coordinator reads back before any
    retry); a row with all three confirmed is done, so an idle run touches nothing.
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
    candidates = []
    for row in store.list_outbox_messages(destination=DESTINATION):
        if row["status"] not in {READY, "PUBLISHING"}:
            continue
        payload = json.loads(row["payload"])
        if row["status"] == READY:
            cause = None
            if _age_minutes(payload, now) > freshness_limit_minutes(payload):
                cause = (STALE, "TRANSITION_OLDER_THAN_60_MINUTES_WHEN_POSTER_REACHED_IT")
            elif (payload.get("state") == "WAITING" and latest_states is not None
                    and latest_states.get(payload.get("plan_id"), "WAITING") != "WAITING"):
                cause = (SUPERSEDED, "PLAN_ALREADY_" + str(latest_states[payload["plan_id"]]))
            if cause:
                store.set_outbox_status(row["message_id"], cause[0])
                results.append({"key": row["message_id"], "status": cause[0], "cause": cause[1]})
                continue
        elif _api_confirmed(store, row["message_id"]):
            store.set_outbox_status(row["message_id"], "PUBLISHED")
            continue
        elif _age_minutes(payload, now) > freshness_limit_minutes(payload):
            continue  # an unresolved old copy is left to the coordinator's own recovery, not this tick
        candidates.append(row)
    import time
    started = time.monotonic()
    for row in candidates[:limit]:
        key = row["message_id"]
        try:
            plan = prepare_post(store, key, root=root, host=host, destinations=API_DESTINATIONS, snapshot=snapshot,
                                snapshot_allowed=lambda: time.monotonic() - started < SNAPSHOT_RUN_BUDGET_SECONDS)
            store.create_work_item(story_id=key, title="Plan status post", target_surface="MULTI_PLATFORM",
                                   work_item_id=key)
            coordinator = coordinator_for(key, Path(plan["output_dir"]))
            scope_to_post(coordinator, key, plan)
            coordinator.register_plan(key, plan)
            outcome = coordinator.execute_plan(key, plan)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            results.append({"key": key, "status": "NOT_STARTED", "cause": str(exc)[:200]})
            continue
        per = {d: (o or {}).get("status") for d, o in (outcome.get("per_destination") or {}).items()}
        done = all(per.get(d) == "DISPATCH_CONFIRMED" for d in API_DESTINATIONS)
        store.set_outbox_status(key, "PUBLISHED" if done else "PUBLISHING")
        results.append({"key": key, "status": "PUBLISHED" if done else "PUBLISHING", "per_destination": per})
    return {"status": "OK", "posts": results}


def start_x(store, key: str, *, native_invocation_id: str, now: datetime | None = None, root: Path = POST_ROOT,
            host=None, snapshot=None) -> dict:
    """The agent route registers and issues a fresh status post's X copy (a Neo request)."""
    from live_contentops.native_neo_executor_v1 import bind_native_neo_coordinator
    now = now or datetime.now(timezone.utc)
    if _age_minutes(_row_payload(store, key), now) > FRESHNESS_MINUTES:
        raise PlanPostError("PLAN_STATUS_X_STALE_NOT_POSTED: transition older than 60 minutes")
    plan = prepare_post(store, key, root=root, host=host, destinations=("x",), snapshot=snapshot)
    coordinator, _ = bind_native_neo_coordinator(
        store, operation_id=key, output_dir=Path(plan["output_dir"]) / "native-neo",
        native_invocation_id=native_invocation_id, allow_publish=True)
    scope_to_post(coordinator, key, plan)
    coordinator.register_plan(key, plan)
    outcome = coordinator.execute_plan(key, plan)
    return {"key": key, "x": (outcome.get("per_destination") or {}).get("x")}


def pending_x(store, *, now: datetime | None = None) -> list[dict]:
    """X requests of status posts still waiting for an agent turn, freshest first."""
    from live_contentops.native_neo_executor_v1 import NativeNeoExecutor
    now = now or datetime.now(timezone.utc)
    pending = []
    for row in store.list_outbox_messages(destination=DESTINATION):
        if row["status"] not in {"PUBLISHING", "PUBLISHED"}:
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
    scope_to_post(coordinator, key, {"plan_status_post": key})
    submitted = executor.submit(request_sha256, response)
    packet = executor._get(request_sha256, "request")
    result = response.get("result") or {}
    if (packet["request"]["action"] == "PUBLISH" and result.get("status") == "SUCCESS"
            and result.get("public_object_id") and result.get("public_object_url")):
        submitted["completed_write_reconciliation"] = coordinator.reconcile_completed_native_publish(
            packet["request"]["dispatch_attempt_identity"], request_hash=request_sha256)
    return submitted
