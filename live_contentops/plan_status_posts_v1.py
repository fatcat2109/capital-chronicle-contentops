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
            lines.append(f"If price reaches {_level(plan['cancel_level'])} before that, the plan is cancelled.")
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
        payload = {"schema_version": SCHEMA, "key": row["key"], "symbol": row["symbol"], "state": row["to"],
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
    return {"status": "OK", "dry_run": dry_run, "transitions_read": len(rows), "six_market_transitions": len(fresh),
            "older_than_window": too_old, "window_minutes": window_minutes,
            "queued" if not dry_run else "would_queue": queued,
            "already_queued": existing, "not_posted": skipped}
