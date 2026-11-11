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
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from typing import Any, Mapping

from .plan_status_export_contract_v1 import (
    PlanExportContractError, rejected_export, validate_export_contract,
)

from live_contentops.event_article_guard_v1 import (
    CONFLICTS_NOTICE, PUBLIC_NOTICE, check_publication_copy, conditional_call_text,
    public_execution_copy_forbidden,
)

SCHEMA = "contentops.plan_status_post.v1"
DESTINATION = "internal:plan-status-post"
WORK_ITEM_ID = "plan-status-posts-v1"
READY = "READY_FOR_PUBLISHER"
# Decision 79's first-phase markets, as the trading system names them.
MARKETS = {
    "XAUUSD": "gold", "US500": "the S&P 500", "EURUSD": "EUR/USD",
    "USDJPY": "USD/JPY", "USOIL": "US crude oil (WTI)", "BTCUSD": "Bitcoin",
}
TITLES = {"XAUUSD": "Gold", "US500": "S&P 500", "EURUSD": "EUR/USD", "USDJPY": "USD/JPY",
          "USOIL": "US crude oil", "BTCUSD": "Bitcoin"}
KINDS = {"WAITING": "setup", "TRIGGERED": "triggered", "FILLED": "triggered", "CANCELLED": "cancelled",
         "INVALIDATED": "invalidated", "EXPIRED": "expired", "VIEW_CHANGED": "view_changed"}
# Decisions 106 and 117 permit confirming a position; account, exact fill price, size and P&L stay private.
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
# Ops Live, 9 Nov 2026: the export was not rewritten from 20:54 to 22:06Z (CC-383 slowed it), and Main's reader
# refuses only a file dated in the future, so every minute run read a file up to 72 minutes old. The export is
# written every minute, every 4-7 minutes under load: a status run reads a file written within 10 minutes or none.
EXPORT_MAX_AGE_MINUTES = 10
STALE_EXPORT = "PLAN_EXPORT_STALE"
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
    # Diagnose consumer field/version changes before the producer's generic
    # schema/hash refusal. Validate the actual returned snapshot again below.
    validate_export_contract({"status": json.loads((Path(export_dir) / "plan-status.public.json").read_bytes()),
                              "transitions": json.loads((Path(export_dir) / "plan-transitions.public.json").read_bytes())})
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    for attempt in (1, 2):
        done = subprocess.run([python or sys.executable, "-B", "-c", _READER, str(export_dir)], cwd=str(main_root),
                              capture_output=True, text=True, encoding="utf-8", timeout=120, creationflags=flags)
        if done.returncode == 0:
            export = json.loads(done.stdout)
            validate_export_contract(export)
            return export
        cause = (done.stderr.strip().splitlines() or ["PLAN_EXPORT_READER_FAILED"])[-1]
        # The two files are replaced one after the other each minute: one bounded reread.
        if attempt == 1 and "SNAPSHOT_MISMATCH" in cause:
            continue
        name = cause.split(":", 1)[-1].strip() if "PlanStatusError" in cause else cause.split(":", 1)[0]
        raise PlanPostError("PLAN_EXPORT_UNREADABLE:" + re.sub(r"[^A-Za-z0-9_]", "", name)[:80])


def rows_from_export(export: Mapping[str, Any], *, include_results: bool = True) -> list[dict]:
    plans = {p["plan_id"]: p for p in export["status"].get("plans", []) if p.get("plan_id")}
    events = export["transitions"].get("transitions", [])
    filled = {e.get("plan_id"): _utc(e["at_utc"]) for e in events if e.get("status") == "FILLED"}
    rows = []
    for event in events:
        plan = plans.get(event.get("plan_id"))
        if plan is None:
            raise PlanPostError("PLAN_EXPORT_TRANSITION_UNKNOWN_PLAN")
        status = event.get("status")
        if status == "EXPIRED" and (plan.get("outcome") or {}).get("state") == "NOT_SCORED_UNTRIGGERED":
            continue  # CC-322: one result post replaces the expiry status post.
        # CC-331 / decision 106: a fill confirms the model position at its own clock. Keep CC-360's existing
        # public TRIGGERED identity even when Main later backfills a separate trigger; this must not post twice.
        # Retain the source state/id, and every row's original event clock, for internal attribution.
        source_state = status
        if status == "FILLED":
            status = "TRIGGERED"
        row = _row(plan_id=event["plan_id"], symbol=plan.get("asset_id"), to=status,
                   at_utc=event.get("at_utc"), cause=event.get("reason_code"),
                   plan=_built_plan(plan, state=status))
        row.update(source_state=source_state, source_transition_id=event.get("transition_id"))
        if (source_state == "TRIGGERED" and event["plan_id"] in filled
                and _utc(row["at_utc"]) != filled[event["plan_id"]]):
            row["superseded_by_fill"] = True
        rows.append(row)
    return rows + (result_rows_from_export(export) if include_results else [])


def result_rows_from_export(export: Mapping[str, Any], *, include_not_triggered: bool = False) -> list[dict]:
    """CC-322: Main's explicit outcomes only; prices never decide a result here.

    Initial results have one identity per plan. Explicit corrections get a new post;
    the original outbox bytes and public calls stay intact.
    """
    status = export["status"]
    count = status.get("scored_call_count")
    rows = []
    for plan in status.get("plans", []):
        if plan.get("asset_id") not in MARKETS:
            continue
        outcome = plan.get("outcome") or {}
        score = outcome.get("score") or {}
        state = outcome.get("state")
        if state == "SCORED":
            result = outcome.get("result")
            if result == "NOT_TRIGGERED" and not include_not_triggered:
                continue  # CC-394's complete record does not add an unfilled feed post.
            if (result not in {"HIT", "STOPPED", "EXPIRED", "NOT_TRIGGERED"} or score.get("result") != result
                    or score.get("plan_id") != plan["plan_id"]
                    or score.get("asset_id") != plan["asset_id"]
                    or not outcome.get("outcome_id") or outcome["outcome_id"] != score.get("outcome_id")):
                raise PlanPostError("PLAN_RESULT_SCORE_BINDING_INVALID")
            at = score.get("resolved_at_utc")
            correction = score.get("corrects_outcome_id")
        elif state == "NOT_SCORED_UNTRIGGERED" and plan.get("status") == "EXPIRED":
            result, correction = "EXPIRED", None
            ended = [e for e in export["transitions"].get("transitions", [])
                     if e.get("plan_id") == plan["plan_id"] and e.get("status") == "EXPIRED"]
            if not ended:
                continue
            at = max(ended, key=lambda e: _utc(e["at_utc"]))["at_utc"]
        else:
            continue
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise PlanPostError("PLAN_RESULT_SCORED_COUNT_INVALID")
        at = _utc(at).isoformat().replace("+00:00", "Z")
        identity = f"{plan['plan_id']}|RESULT" + (f"|{score['outcome_id']}" if correction else "")
        rows.append({"key": "plan-result-post-" + hashlib.sha256(identity.encode()).hexdigest()[:32],
                     "plan_id": plan["plan_id"], "symbol": plan["asset_id"], "to": "RESULT", "at_utc": at,
                     "plan": _built_plan(plan), "result": result, "scored": state == "SCORED",
                     "scored_call_count": count, "outcome_id": outcome.get("outcome_id"),
                     "corrects_outcome_id": correction, "score_hash": score.get("content_hash"),
                     "source_content_hash": status.get("content_hash")})
    return rows


def compose_result(row: Mapping[str, Any]) -> dict:
    """Closed vocabulary: no source free text, execution fields or performance claims."""
    result = row["result"].lower()
    if result not in {"hit", "stopped", "expired"}:
        raise PlanPostError("PLAN_RESULT_INVALID")
    prefix = "Correction — " if row.get("corrects_outcome_id") else ""
    text = f"{prefix}{TITLES[row['symbol']]}: plan result — {result} at {_when(row['at_utc'])}."
    plan = row["plan"]
    if plan.get("zone_low") is not None and plan.get("zone_high") is not None:
        text += f" Entry zone: {_level(plan['zone_low'])}–{_level(plan['zone_high'])}."
    if not row["scored"]:
        text += " The entry condition was not met; this call is not scored."
    text += f" Scored calls: {row['scored_call_count']}.\n\n{PUBLIC_NOTICE} {CONFLICTS_NOTICE}"
    check_publication_copy({"body": text})
    return {"status": "COMPOSED", "kind": "result", "text": text, "conditional_calls": []}


def export_freshness(export: Mapping[str, Any], now: datetime | None = None) -> dict:
    """When the export was written, and its age at `now`, from the status document's own clock."""
    written = _utc(export["status"]["generated_at_utc"])
    age = ((now or datetime.now(timezone.utc)) - written).total_seconds()
    return {"export_generated_at_utc": written.isoformat().replace("+00:00", "Z"), "export_age_seconds": round(age, 1)}


def read_transitions(export_dir: Path = EXPORT_DIR, *, now: datetime | None = None,
                     max_age_minutes: float | None = None, freshness: dict | None = None, **kwargs) -> list[dict]:
    """The export's rows. With max_age_minutes, a file written longer ago than that is refused
    (PLAN_EXPORT_STALE); `freshness`, when given, receives the file's clock and age."""
    if not (Path(export_dir) / "plan-status.public.json").is_file():
        return []
    export = read_export(export_dir, **kwargs)
    if max_age_minutes is not None or freshness is not None:
        info = export_freshness(export, now)
        if freshness is not None:
            freshness.update(info)
        if max_age_minutes is not None and info["export_age_seconds"] > max_age_minutes * 60:
            raise PlanPostError(f"{STALE_EXPORT}: written at {info['export_generated_at_utc']}, "
                                f"{info['export_age_seconds']:.0f} s before this run; the limit is {max_age_minutes} minutes")
    return rows_from_export(export)


def _built_plan(plan: Mapping[str, Any], *, state: str | None = None) -> dict:
    zone = plan.get("zone") or {}
    direction = {"BULLISH": "bullish", "BEARISH": "bearish"}.get(plan.get("direction"))
    below = direction == "bullish"
    invalid = [p["threshold"] for p in plan.get("invalidation_conditions") or []
               if p.get("operator") in ({"LT", "LTE"} if below else {"GT", "GTE"})
               and p.get("field") in {"low", "close", "bid", "mid"} | ({"high", "ask"} if not below else set())]
    until = plan.get("expires_at_utc")
    if state not in {"TRIGGERED", "FILLED"} and plan.get("entry_deadline_utc"):
        until = min((v for v in (until, plan["entry_deadline_utc"]) if v), key=_utc)
    return {"direction": direction, "zone_low": zone.get("minimum"), "zone_high": zone.get("maximum"),
            "cancel_level": plan.get("cancel_level"),
            "target": plan.get("target", plan.get("target_level")),
            "invalidation_level": (max(invalid) if below else min(invalid)) if invalid else None,
            "valid_until_utc": until,
            "scenario_analysis": plan.get("scenario_analysis"),
            **_instrument_fields(plan),
            **{k: plan.get(k) for k in REASON_FIELDS},
            "invalidation_text": plan.get("invalidation_text")}


def _entries(values) -> list[dict]:
    """CC-383's public entry fields only. Execution metadata never follows them."""
    return [{"kind": e["kind"], **{k: e.get(k) for k in
             (("zone_low", "zone_high") if e["kind"] == "LIMIT" else ("level",))}}
            for e in values or [] if isinstance(e, Mapping) and e.get("kind") in {"LIMIT", "BREAKOUT"}]


def _instrument_fields(plan) -> dict:
    fields = {}
    if "entries" in plan:
        fields["entries"] = _entries(plan["entries"])
    instrument = plan.get("public_instrument")
    if isinstance(instrument, Mapping):
        fields["public_instrument"] = {k: instrument.get(k) for k in
            ("name", "symbol", "kind", "exchange", "contract_month", "direction", "zone_low", "zone_high", "invalidation_level")}
        fields["public_instrument"]["entries"] = _entries(instrument.get("entries"))
    return fields


def _instrument_title(symbol, plan) -> str:
    instrument = plan.get("public_instrument") or {}
    code, kind = instrument.get("symbol"), instrument.get("kind")
    name = _public_reason(instrument.get("name")).rstrip(".")
    if (not name or kind not in {"FUT", "ETF", "SPOT", "INDEX"}
            or not isinstance(code, str) or not re.fullmatch(r"[A-Z0-9.]{1,16}", code)
            or INTERNAL.search(name) or FORBIDDEN.search(name) or PRIVATE_RATIONALE.search(name)):
        return TITLES[symbol]
    # Spot aliases may match the private book's symbols; the market's name is sufficient.
    label = " ".join(v for v in (code if code not in BROKER_NAMES else "",
                                  {"FUT": "futures", "ETF": "ETF", "SPOT": "spot", "INDEX": "index"}[kind]) if v)
    month = instrument.get("contract_month")
    if kind == "FUT" and isinstance(month, str) and re.fullmatch(r"\d{4}-\d{2}", month):
        try:
            label += ", " + datetime.strptime(month, "%Y-%m").strftime("%b %Y")
        except ValueError:
            pass
    return f"{name} ({label})"


def _display_plan(plan) -> dict:
    """Use one complete price basis, never convert or splice mapped and plan prices."""
    display = dict(plan)
    instrument = plan.get("public_instrument") or {}
    entries, mapped = plan.get("entries") or [], instrument.get("entries") or []
    complete = all(instrument.get(k) is not None for k in ("zone_low", "zone_high", "invalidation_level"))
    if entries:
        complete = complete and len(mapped) == len(entries) and all(
            e["kind"] == p["kind"] and all(v is not None for k, v in p.items() if k != "kind")
            for e, p in zip(entries, mapped))
    if complete:
        display.update({k: instrument[k] for k in ("zone_low", "zone_high", "invalidation_level")})
        display["entries"] = mapped if entries else []
        if instrument.get("direction") in {"BULLISH", "BEARISH"}:
            display["direction"] = instrument["direction"].lower()
    if instrument:
        display["price_basis"] = "instrument" if complete else "plan"
    return display


def _entry_condition(plan) -> str:
    entries = plan.get("entries") or []
    if not entries:
        return f"price trades into {_level(plan['zone_low'])}–{_level(plan['zone_high'])}"
    conditions = []
    for entry in entries:
        if entry["kind"] == "LIMIT" and all(entry.get(k) is not None for k in ("zone_low", "zone_high")):
            zone = (f"at {_level(entry['zone_low'])}" if entry['zone_low'] == entry['zone_high'] else
                    f"into {_level(entry['zone_low'])}–{_level(entry['zone_high'])}")
            conditions.append(f"price trades {zone}"
                              + (" (limit)" if len(entries) > 1 else ""))
        elif entry["kind"] == "BREAKOUT" and entry.get("level") is not None:
            conditions.append(f"price breaks through {_level(entry['level'])} (breakout)")
        else:
            raise PlanPostError("PLAN_ENTRY_LEVEL_MISSING")
    return " or ".join(conditions)


# CC-353 / CC-355: only named public rationale fields cross into the composer.
# In particular, never copy the whole export row (target, sizing and execution fields).
REASON_FIELDS = {
    "mechanism": "Mechanism", "priced": "What is priced", "positioning": "Positioning",
    "driver": "Today's driver", "acceptance": "Reaction so far", "zone_reason": "Why this zone",
    "invalidation_reason": "Why this invalidation level", "confirmations": "What confirms it",
    "opposite_mechanism": "Alternative mechanism",
}
# Ops Product, 9 Nov: `why_no_open` stays off public copy. Its words are the desk's own ("at the 1.11781
# capture", "below the 65-70% bar"); the post already says the plan waits for price to reach its zone.
PRIVATE_RATIONALE = re.compile(
    r"\b(?:targets?|take[ -]?profit|after[ -]?cost|risk[ /:-]*(?:reward|return)|R\s*:\s*R|"
    r"position siz\w*|fills?|filled|tickets?|P\s*&\s*L|(?:realized|unrealized)\s+(?:profit|loss)|prediction[ -]?market|"
    r"polymarket|kalshi|account|balance|equity capital)\b|https?://|"
    r"\b(?:towards?|aims? (?:at|for))\s+[$€£]?\d", re.I)

# Ops Product, 9 Nov: Main's fields name its roles ("the Primary's 1.11480", "The Critical showed") and can
# carry an empty value ("request CPI consensus null"). Neither means anything to a reader. A parenthetical
# role credit is cut; any other sentence with a role name or an empty value is left out.
ROLE_CREDIT = re.compile(r"\s*\([^()]*\b(?:Primary|Critical)\b[^()]*\)")
INTERNAL_RATIONALE = re.compile(r"\b(?:Primary|Critical|Owner)(?:'s)?\b|\b(?:null|None|NaN|undefined)\b")

# Ops Product, 9 Nov (Jim: the reasons must read cleanly). Main writes bar times in UTC ("the 9 Nov 03:00-04:30
# M15 highs") and its own labels in capitals ("a CLEAR channel", "(press, context)"). Public copy gives times in
# ET (decision 90) and plain words; a stop is the plan's invalidation level.
MONTHS = {m: i for i, m in enumerate(("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct",
                                       "Nov", "Dec"), 1)}
DATED_CLOCK = re.compile(r"\b(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{1,2}):(\d{2})"
                         r"(?:\s*[-–]\s*(\d{1,2}):(\d{2}))?(?:Z\b|\s*(?:UTC|GMT)\b(?!\+))?")
LABEL_WORDS = re.compile(r"\b(CLEAR|MIXED|UNCLEAR|ABSENT|CONFLICTED)\b")
# Jim's decision 107 (10 Nov): instruments European and US readers know, and no "CFD". Main's text uses the DEMO
# book's symbols; public copy gives the market's own name ("WTI (USOIL)" becomes "WTI").
BROKER_NAMES = {"US500": "the S&P 500", "US30": "the Dow", "USTEC": "the Nasdaq 100", "USOIL": "WTI",
                "UKOIL": "Brent", "XAUUSD": "gold", "XAGUSD": "silver", "EURUSD": "EUR/USD", "USDJPY": "USD/JPY",
                "USDCAD": "USD/CAD", "GBPUSD": "GBP/USD", "AUDUSD": "AUD/USD", "USDCHF": "USD/CHF",
                "BTCUSD": "Bitcoin", "ETHUSD": "Ether", "DE40": "the DAX", "UK100": "the FTSE 100",
                "JP225": "the Nikkei 225"}
BROKER_SYMBOL = re.compile(r"\b(" + "|".join(BROKER_NAMES) + r")\b")
BROKER_ALIAS = re.compile(r"\s*\((?:" + "|".join(BROKER_NAMES) + r")\)")
CFD_WORD = re.compile(r"\bCFDs?\b", re.I)
SOURCE_TAG = re.compile(r"\s*\((?:press|context)(?:,\s*(?:press|context))*\)|;\s*context(?=\))")


def _et_clock(match: re.Match, now: datetime | None = None) -> str:
    """A dated UTC clock from Main's text, in New York time."""
    now = now or datetime.now(timezone.utc)

    def at(hour: str, minute: str) -> datetime:
        value = datetime(now.year, MONTHS[match[2]], int(match[1]), int(hour), int(minute), tzinfo=timezone.utc)
        if value - now > timedelta(days=2):
            value = value.replace(year=now.year - 1)
        return value.astimezone(PUBLIC_TZ)

    try:
        start = at(match[3], match[4])
        text = f"{start.day} {start:%b} {start:%H:%M}"
        if match[5]:
            end = at(match[5], match[6])
            text += f"-{end:%H:%M}" if end.date() == start.date() else f" to {end.day} {end:%b} {end:%H:%M}"
    except ValueError:
        return match[0]
    return text + " ET"


def _public_reason(value: Any) -> str:
    """Keep source sentences only. A private clause never suppresses the whole post."""
    if isinstance(value, list):
        # Each item is filtered (and its clocks converted) once, never a second time as joined text.
        return " ".join(part for part in (_public_reason(v) for v in value) if part)
    if not isinstance(value, str):
        return ""
    if not re.search(r"\b(?:ET|EST|EDT)\b", value):
        value = DATED_CLOCK.sub(_et_clock, value)
    value = LABEL_WORDS.sub(lambda m: m[1].lower(), SOURCE_TAG.sub("", value))
    value = re.sub(r"\b(is|are) context\b", r"\1 background", value)
    value = BROKER_SYMBOL.sub(lambda m: BROKER_NAMES[m[1]], BROKER_ALIAS.sub("", value))
    sentences = re.split(r"(?<=[.!?;])\s+|\n+", value.strip())
    safe = []
    for sentence in sentences:
        sentence = " ".join(sentence.split())
        # A projected destination price is a target (decision 40). Keep the
        # preceding mechanism, without supplying a replacement price or direction.
        sentence = re.sub(r"\s+towards?\s+[$€£]?\d.*", "", sentence, flags=re.I)
        sentence = ROLE_CREDIT.sub("", sentence)
        sentence = re.sub(r"^Stop (?=\d)", "Invalidation at ", sentence)
        if (not sentence or PRIVATE_RATIONALE.search(sentence) or INTERNAL.search(sentence)
                or INTERNAL_RATIONALE.search(sentence)
                or FORBIDDEN.search(sentence) or public_execution_copy_forbidden(sentence)
                or re.search(r"\b(?:bullish|bearish)\b", sentence, re.I) or CFD_WORD.search(sentence)):
            continue
        # An undated UTC clock cannot be converted faithfully. Omit that sentence;
        # source date-only periods and already-labelled ET clocks remain unchanged.
        if re.search(r"\b\d{1,2}:\d{2}(?:Z|\s*(?:UTC|GMT))\b|GMT\+7|UTC\+7", sentence):
            continue
        safe.append(sentence)
    text = " ".join(safe).rstrip(" ;,:")
    return text + "." if text and text[-1] not in ".!?…" else text


def _rationale(plan: Mapping[str, Any]) -> list[str]:
    scenario = plan.get("scenario_analysis") or {}
    if not isinstance(scenario, Mapping):
        scenario = {}
    lines, alternative = [], ""
    for key, label in (("base_case", "Base case"), ("main_alternative", "Main alternative")):
        branch = scenario.get(key) or {}
        if not isinstance(branch, Mapping):
            continue
        move = _public_reason(branch.get("market_move"))
        if not move:
            continue
        probability = branch.get("probability_pct")
        probability = (f" {probability:g}%" if isinstance(probability, (int, float))
                       and not isinstance(probability, bool) and 0 <= probability <= 100 else "")
        lines.append(f"{label}{probability} (Capital Chronicle model estimate): {move}")
        if key == "main_alternative":
            alternative = move.rstrip(".")
    for field, label in REASON_FIELDS.items():
        value = _public_reason(plan.get(field) or scenario.get(field))
        # Ops Product, 9 Nov: Main often repeats the main alternative as the opposite mechanism.
        if field == "opposite_mechanism" and value.rstrip(".") == alternative:
            continue
        if value:
            lines.append(f"{label}: {value}")
    invalid = _public_reason(plan.get("invalidation_text") or scenario.get("invalidation_text"))
    if invalid:
        lines.append(f"Invalidation: {invalid}")
    return lines


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


def compose(row: Mapping[str, Any], *, delayed_at: datetime | None = None,
            first_plan_post: bool = False) -> dict:
    """One short post for one transition, or a named cause it is not posted."""
    symbol, plan = row["symbol"], _display_plan(row["plan"])
    if symbol not in MARKETS:
        return {"status": "NOT_A_FIRST_PHASE_MARKET"}
    if row["to"] == "RESULT":
        return compose_result(row)
    if row.get("superseded_by_fill"):
        return {"status": "NOT_POSTED", "cause": "FILL_EVENT_SUPERSEDES_TRIGGER"}
    market, title = MARKETS[symbol], _instrument_title(symbol, plan)
    if plan.get("price_basis") == "instrument" and (plan.get("public_instrument") or {}).get("direction"):
        code = plan["public_instrument"]["symbol"]
        market = BROKER_NAMES.get(code, code)
    if plan.get("direction") not in {"bullish", "bearish"}:
        return {"status": "NOT_POSTED", "cause": "PLAN_DIRECTION_MISSING"}
    if plan.get("zone_low") is None or plan.get("zone_high") is None:
        return {"status": "NOT_POSTED", "cause": "PLAN_ZONE_MISSING"}
    if plan.get("invalidation_level") is None:
        # Decision 40: every public call shows its invalidation level.
        return {"status": "NOT_POSTED", "cause": "PLAN_INVALIDATION_LEVEL_MISSING"}
    zone = f"{_level(plan['zone_low'])}–{_level(plan['zone_high'])}"
    side = "below" if plan["direction"] == "bullish" else "above"
    if plan.get("price_basis") == "instrument":
        # Inverse expressions (e.g. yen futures) can put the stop on the other side.
        side = "below" if Decimal(str(plan['invalidation_level'])) < Decimal(str(plan['zone_low'])) else "above"
    invalid = f"price moves {side} {_level(plan['invalidation_level'])}"
    calls, kind, to = [], KINDS[row["to"]], row["to"]
    if to == "WAITING":
        if not plan.get("valid_until_utc"):
            return {"status": "NOT_POSTED", "cause": "PLAN_VALIDITY_MISSING"}
        call = {"condition": _entry_condition(plan), "direction": plan["direction"], "market": market,
                "horizon": f"the period to {_when(plan['valid_until_utc'])}", "invalidation": invalid}
        calls = [call]
        lines = [f"{title}: new plan.", conditional_call_text(call)]
        if plan.get("cancel_level") is not None and not plan.get("entries") and plan.get("price_basis") != "instrument":
            if _cancel_level_is_public(plan):
                lines.append(f"If price reaches {_level(plan['cancel_level'])} before that, the plan is cancelled.")
            else:
                lines.append("If price runs away before any pullback, the plan is cancelled and we re-assess.")
    elif to in {"TRIGGERED", "FILLED"}:
        # CC-360 (Ops Live, 9 Nov): TRIGGERED now means price traded into the zone (a market send after the
        # condition, or a resting order's fill, mapped in rows_from_export). An order placed ahead of price stays
        # WAITING, so this post never fires on placement again (9 Nov: EUR/USD and WTI were posted 20 pips and
        # 2.7 dollars away). The words say what happened, since Jim read "now active" as a touch.
        # Decisions 106 and 117: confirm the fill and position without account, size, exact fill price or P&L.
        lines = [f"{title}: the {zone} entry zone filled at {_when(row['at_utc'])}, and Capital Chronicle's"
                 " position is open.", f"It is invalidated if {invalid}."]
        if len(plan.get("entries") or []) > 1 or any(e["kind"] == "BREAKOUT" for e in plan.get("entries") or []):
            # Main's idea-level fill does not identify which leg filled. Never assert the limit zone did.
            lines[0] = f"{title}: an entry filled at {_when(row['at_utc'])}, and Capital Chronicle's position is open."
        if first_plan_post and plan.get("valid_until_utc"):
            call = {"condition": _entry_condition(plan), "direction": plan["direction"], "market": market,
                    "horizon": f"the period to {_when(plan['valid_until_utc'])}", "invalidation": invalid}
            calls = [call]
            lines = [lines[0], conditional_call_text(call)]
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
    extended = bool(plan.get("public_instrument") or plan.get("entries"))
    if delayed_at is not None:
        if extended and to == "WAITING":
            lines.insert(0, f"Registered {_when(row['at_utc'])}; delayed update {_when(delayed_at.isoformat())}.")
        else:
            lines.insert(0, f"Delayed update as of {_when(delayed_at.isoformat())}.")
            if to == "WAITING":
                lines.append(f"The plan was registered at {_when(row['at_utc'])}.")
    if plan.get("price_basis") == "plan":
        lines.insert(1, "Levels use the plan's prices.")
    why = _rationale(plan) if to == "WAITING" or (to in {"TRIGGERED", "FILLED"} and first_plan_post) else []
    lead = ("\n" if extended else " ").join(lines)
    # Ops Product, 9 Nov (Jim): one reason per line, so each block reads on its own (format 2).
    text = lead + ("\nWhy:\n" + "\n".join("• " + line for line in why) if why else "") \
        + f"\n\n{PUBLIC_NOTICE} {CONFLICTS_NOTICE}"
    check_publication_copy({"title": title, "body": text}, conditional_calls=calls)
    if INTERNAL.search(text) or FORBIDDEN.search(text):
        raise PlanPostError("PLAN_POST_INTERNAL_OR_FORBIDDEN_WORDS")
    return {"status": "COMPOSED", "kind": kind, "text": text, "conditional_calls": calls,
            **({"instrument_title": title, "price_basis": plan.get("price_basis"),
                "format": 3, "lead": lead} if extended else {}),
            **({"lead": lead, "why": why, "format": 3 if extended else 2} if why else {}),
            "rationale_cause": ("SCENARIO_ANALYSIS_MISSING" if not plan.get("scenario_analysis") else
                                "PUBLIC_RATIONALE_EMPTY" if not why and to in ACTIVE else None)}


WHY_PREFIX = "plan-status-why-"


def compose_why(row: Mapping[str, Any]) -> dict:
    """Ops Product, 9 Nov (Jim): the reasoning of a live plan whose first post went out without it."""
    post = compose(row)
    if post.get("status") != "COMPOSED" or not post.get("why"):
        return post
    title = post.get("instrument_title") or TITLES[row["symbol"]]
    lead = post["lead"].replace(f"{title}: new plan.", f"{title}: the reasoning behind our plan.", 1)
    text = lead + "\nWhy:\n" + "\n".join("• " + line for line in post["why"]) \
        + f"\n\n{PUBLIC_NOTICE} {CONFLICTS_NOTICE}"
    check_publication_copy({"title": title, "body": text}, conditional_calls=post["conditional_calls"])
    if INTERNAL.search(text) or FORBIDDEN.search(text):
        raise PlanPostError("PLAN_POST_INTERNAL_OR_FORBIDDEN_WORDS")
    return {**post, "kind": "why", "lead": lead, "text": text}


POSTING_WINDOW_MINUTES = 60
# Ops Product, 6 Nov: a later state (triggered, cancelled, invalidated, expired, view changed) of a plan
# whose post already went out still posts after the window, up to this many hours, with its true time:
# readers who saw the setup must not be left with a plan that has ended (decision 79's live status).
LATE_STATE_HOURS = 24
# Jim, 6 Nov: a 'withdrawn' post about a plan readers never saw only confuses them (EUR/USD: a new sell plan,
# then 'view changed' about an older plan whose setup post had been refused). Such states post only for an
# announced plan, and before any new plan queued in the same run.
WITHDRAWN = {"VIEW_CHANGED", "CANCELLED", "INVALIDATED", "EXPIRED"}
# Jim's decision 106 (9 Nov): one trading idea gets two or three posts (the idea with its reasons, the fill, and a
# selective exit through CC-322). A plan that ends without an entry posts nothing: its first post already gives
# its window and invalidation level. The machinery stays for a later decision.
POST_ENDED_WITHOUT_ENTRY = False
# CC-353's why block went live at 09:48Z on 9 Nov. Only plans registered before it lack their reasons, so only
# they can get a why follow-up; every later plan carries its reasons in its first post (decision 106).
WHY_FOLLOW_UP_REGISTERED_BEFORE = "2026-11-09T09:48:00Z"
# Jim's decision 106: the exit post (CC-322) is optional and selective. A plan that never filled posts nothing; an
# exit at the horizon end is not posted; a result more than a day old is not news (the week's record lists every
# scored call); a loss posts at most once in LOSS_POST_DAYS, so a reader who joins during a losing streak is not
# shown it post by post. A correction always posts.
RESULT_POSTS_SELECTIVE = True
LOSS_POST_DAYS = 7


def _recent_loss_post(outbox, now) -> bool:
    for r in outbox:
        payload = json.loads(r["payload"])
        when = r.get("created_at") or payload.get("at_utc")
        if (payload.get("kind") == "result" and payload.get("result") == "STOPPED" and when
                and r["status"] not in {STALE, SUPERSEDED}
                and (now - _utc(when)).total_seconds() < LOSS_POST_DAYS * 86400):
            return True
    return False
PUBLIC_LEVELS = ("direction", "zone_low", "zone_high", "invalidation_level", "valid_until_utc")
ACTIVE = {"WAITING", "TRIGGERED", "FILLED"}


def active_recoveries(rows, now: datetime) -> dict:
    """CC-340: only each plan's latest still-valid active state can recover a missed post.

    A missing outbox row already covers both composer refusal and an unreadable export;
    no separate failure ledger or replay of all the missed transitions is needed.
    """
    latest = {}
    for row in sorted(rows, key=lambda r: _utc(r["at_utc"])):
        latest[row["plan_id"]] = row
    result = {}
    for row in latest.values():
        until = row["plan"].get("valid_until_utc")
        if (row["symbol"] in MARKETS and row["to"] in ACTIVE and until
                and 0 <= (now - _utc(row["at_utc"])).total_seconds() <= LATE_STATE_HOURS * 3600
                and now < _utc(until)):
            result[row["key"]] = {"plan_id": row["plan_id"], "state": row["to"],
                                  "at_utc": row["at_utc"], "valid_until_utc": until}
    return result


def _recoverable(payload, recoveries, now) -> bool:
    current = (recoveries or {}).get(payload["key"])
    return bool(current and all(current[k] == payload[k] for k in ("plan_id", "state", "at_utc"))
                and 0 <= _age_minutes(payload, now) <= LATE_STATE_HOURS * 60
                and now < _utc(current["valid_until_utc"]))


def queue_posts(store, export_dir: Path = EXPORT_DIR, *, now: datetime | None = None,
                window_minutes: int = POSTING_WINDOW_MINUTES, dry_run: bool = False,
                render_all: bool = False, instagram_profile_reader=None, **reader) -> dict:
    """Register one outbox row per new transition for the six markets; repeats change nothing.

    The export carries every plan's whole history (back to 27 Oct on 5 Nov). A status post is
    news while recent. CC-340 also recovers the latest active state for up to 24 hours while
    still valid; CC-306 retains late updates of announced plans. A dry run writes nothing.
    An export written more than EXPORT_MAX_AGE_MINUTES before `now` is refused (EXPORT_STALE):
    nothing is queued, and the caller posts nothing in that run.
    """
    now = now or datetime.now(timezone.utc)
    if render_all and not dry_run:
        raise ValueError("PLAN_EXPORT_REPLAY_REQUIRES_DRY_RUN")
    from live_contentops import plan_call_cards_v1 as cards
    if now >= cards.EFFECTIVE:
        return cards.queue_posts(store, export_dir, now=now, window_minutes=window_minutes,
                                 dry_run=dry_run, render_all=render_all,
                                 instagram_profile_reader=instagram_profile_reader, **reader)
    limit = EXPORT_MAX_AGE_MINUTES
    freshness = {}
    try:
        rows = read_transitions(export_dir, now=now, max_age_minutes=limit, freshness=freshness, **reader)
    except PlanExportContractError as exc:
        return rejected_export(store, exc, dry_run=dry_run)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        cause = str(exc) if isinstance(exc, PlanPostError) else type(exc).__name__
        if cause.startswith(STALE_EXPORT):
            return {"status": "EXPORT_STALE", "cause": cause, **freshness, "max_export_age_minutes": limit}
        return {"status": "EXPORT_UNREADABLE", "cause": cause}
    freshness["max_export_age_minutes"] = limit
    oldest = now.timestamp() - window_minutes * 60
    queued, existing, skipped, too_old = [], [], [], 0
    rationale_causes = {}
    fresh = [row for row in rows if row["symbol"] in MARKETS]
    recoveries = active_recoveries(fresh, now)
    outbox = store.list_outbox_messages(destination=DESTINATION)
    announced = {json.loads(r["payload"]).get("plan_id") for r in outbox if r["status"] == "PUBLISHED"}
    loss_recent = _recent_loss_post(outbox, now)
    prior_confirmations = {}
    for row in fresh:
        if row.get("superseded_by_fill"):
            prior = store.get_outbox_message(row["key"])
            if prior and prior["status"] in {"PUBLISHING", "PUBLISHED"}:
                prior_confirmations[row["plan_id"]] = prior
    for row in sorted(fresh, key=lambda r: (r["to"] not in WITHDRAWN, r["at_utc"])):
        late = False
        is_result = row["to"] == "RESULT"
        if row.get("superseded_by_fill"):
            # A previous tick may have queued the trigger before Main supplied its fill. Retire only an
            # unsent row; frozen published bytes and ambiguous writes remain with the existing coordinator.
            prior = store.get_outbox_message(row["key"])
            if not dry_run and prior and prior["status"] == READY:
                store.set_outbox_status(row["key"], SUPERSEDED)
            skipped.append({"key": row["key"], "cause": "FILL_EVENT_SUPERSEDES_TRIGGER"})
            continue
        if row.get("source_state") == "FILLED" and row["plan_id"] in prior_confirmations:
            prior = prior_confirmations[row["plan_id"]]
            skipped.append({"key": row["key"], "prior_key": prior["message_id"],
                            "cause": "FILL_CONFIRMATION_PENDING_READBACK" if prior["status"] == "PUBLISHING"
                            else "FILL_CONFIRMATION_ALREADY_PUBLISHED"})
            continue  # No second confirmation while a prior send is ambiguous, or after it is confirmed.
        if (is_result and RESULT_POSTS_SELECTIVE and not row.get("corrects_outcome_id")
                and not store.get_outbox_message(row["key"])):
            cause = ("ENDED_WITHOUT_ENTRY_NOT_POSTED_DECISION_106" if not row["scored"] else
                     "EXIT_AT_HORIZON_END_NOT_POSTED_DECISION_106" if row["result"] == "EXPIRED" else
                     "RESULT_OLDER_THAN_A_DAY_NOT_POSTED_DECISION_106"
                     if (now - _utc(row["at_utc"])).total_seconds() > LATE_STATE_HOURS * 3600 else
                     "LOSS_POST_LIMIT_DECISION_106" if row["result"] == "STOPPED" and loss_recent else None)
            if cause:
                skipped.append({"key": row["key"], "cause": cause})
                continue
            if row["result"] == "STOPPED":
                loss_recent = True
        if is_result and not row["scored"] and row["plan_id"] not in announced:
            skipped.append({"key": row["key"], "cause": "PLAN_NEVER_ANNOUNCED"})
            continue
        if not is_result and _utc(row["at_utc"]).timestamp() < oldest:
            if (row["key"] in recoveries or (row["to"] != "WAITING" and row["plan_id"] in announced
                    and _utc(row["at_utc"]).timestamp() >= now.timestamp() - LATE_STATE_HOURS * 3600)):
                late = True
            else:
                too_old += 1
                continue
        if row["to"] in WITHDRAWN and not POST_ENDED_WITHOUT_ENTRY:
            skipped.append({"key": row["key"], "cause": "ENDED_WITHOUT_ENTRY_NOT_POSTED_DECISION_106"})
            continue
        if row["to"] in WITHDRAWN and row["plan_id"] not in announced:
            skipped.append({"key": row["key"], "cause": "PLAN_NEVER_ANNOUNCED"})
            continue
        post = compose(row, delayed_at=now if late and row["key"] in recoveries else None,
                       first_plan_post=row["plan_id"] not in announced)
        if post["status"] != "COMPOSED":
            skipped.append({"key": row["key"], "cause": post.get("cause")})
            continue
        prior = store.get_outbox_message(row["key"])
        if prior:
            # Keep the exact identity and bytes; the coordinator still reconciles prior writes.
            if not dry_run and row["key"] in recoveries and prior["status"] == STALE:
                store.set_outbox_status(row["key"], READY)
            existing.append(row["key"])
            continue
        rationale_cause = post.get("rationale_cause") if row["to"] in ACTIVE else None
        if rationale_cause:
            rationale_causes[rationale_cause] = rationale_causes.get(rationale_cause, 0) + 1
        display = _display_plan(row["plan"]) if post.get("instrument_title") else row["plan"]
        payload = {"schema_version": SCHEMA, "key": row["key"], "plan_id": row["plan_id"],
                   "symbol": row["symbol"], "state": row["to"],
                   **{k: row[k] for k in ("source_state", "source_transition_id") if row.get(k)},
                   "at_utc": row["at_utc"], "kind": post["kind"], "text": post["text"],
                   "conditional_calls": post["conditional_calls"],
                    **{k: post[k] for k in ("lead", "why", "rationale_cause", "format", "instrument_title",
                                          "price_basis") if post.get(k)},
                   **({"format": 3, "lead": post.get("lead") or _split(post["text"])[0]}
                      if post.get("instrument_title") else {}),
                   # CC-314: the levels the post's image shows (the chart timeframe and the
                   # fallback fact card). Never the target or the cancel level (decision 40).
                   "levels": {k: display.get(k) for k in PUBLIC_LEVELS},
                   **({"entries": display["entries"]} if display.get("entries") else {}),
                   **({k: row[k] for k in ("result", "scored", "scored_call_count", "outcome_id",
                                          "corrects_outcome_id", "score_hash", "source_content_hash")}
                      if is_result else {}),
                   **({"late": True} if late else {}),
                   **({"late_active": True, "queued_at_utc": now.isoformat().replace("+00:00", "Z")}
                      if late and row["key"] in recoveries else {})}
        queued.append({"key": row["key"], "symbol": row["symbol"], "state": row["to"], "at_utc": row["at_utc"],
                       "text": post["text"]})
        if dry_run:
            continue
        store.create_work_item(story_id=WORK_ITEM_ID, title="Plan status posts (decision 79)",
                               target_surface="MULTI_PLATFORM", work_item_id=WORK_ITEM_ID)
        store.register_outbox_message(message_id=row["key"], work_item_id=WORK_ITEM_ID, destination=DESTINATION,
                                      payload=json.dumps(payload, sort_keys=True, ensure_ascii=False), status=READY)
    # Ops Product, 9 Nov (Jim: the posts must say why). A live plan announced before the why block went live
    # (CC-353, 16:48 GMT+7) gets its reasoning once, while it still waits for its zone and is valid. The key is
    # fixed per plan, so it never repeats; the plan's own posts are never sent again.
    with_why = {json.loads(r["payload"]).get("plan_id") for r in outbox
                if json.loads(r["payload"]).get("why") and r["status"] not in {STALE, SUPERSEDED}}
    last = {}
    for row in sorted(fresh, key=lambda r: _utc(r["at_utc"])):
        last[row["plan_id"]] = row
    for plan_id, row in last.items():
        until = row["plan"].get("valid_until_utc")
        if (row["to"] != "WAITING" or plan_id not in announced or plan_id in with_why
                or not until or now >= _utc(until)
                or _utc(row["at_utc"]) >= _utc(WHY_FOLLOW_UP_REGISTERED_BEFORE)):
            continue
        key = WHY_PREFIX + hashlib.sha256(f"{plan_id}|WHY".encode()).hexdigest()[:32]
        if store.get_outbox_message(key):
            existing.append(key)
            continue
        try:
            post = compose_why(row)
        except ValueError as exc:
            skipped.append({"key": key, "cause": str(exc)[:120]})
            continue
        if post.get("kind") != "why":
            skipped.append({"key": key, "cause": post.get("cause") or post.get("rationale_cause")
                            or "PUBLIC_RATIONALE_EMPTY"})
            continue
        at = now.isoformat().replace("+00:00", "Z")
        payload = {"schema_version": SCHEMA, "key": key, "plan_id": plan_id, "symbol": row["symbol"],
                   "state": "WAITING", "at_utc": at, "registered_at_utc": row["at_utc"], "kind": "why",
                   "why_follow_up": True, "format": 2, "text": post["text"], "lead": post["lead"],
                   "why": post["why"], "conditional_calls": post["conditional_calls"],
                   "levels": {k: row["plan"].get(k) for k in PUBLIC_LEVELS}}
        queued.append({"key": key, "symbol": row["symbol"], "state": "WHY", "at_utc": at, "text": post["text"]})
        if dry_run:
            continue
        store.create_work_item(story_id=WORK_ITEM_ID, title="Plan status posts (decision 79)",
                               target_surface="MULTI_PLATFORM", work_item_id=WORK_ITEM_ID)
        store.register_outbox_message(message_id=key, work_item_id=WORK_ITEM_ID, destination=DESTINATION,
                                      payload=json.dumps(payload, sort_keys=True, ensure_ascii=False), status=READY)
    latest = {}
    for row in sorted(fresh, key=lambda r: r["at_utc"]):
        latest[row["plan_id"]] = row["to"]
    return {"status": "OK", "dry_run": dry_run, "transitions_read": len(rows), "six_market_transitions": len(fresh),
            **freshness, "latest_states": latest, "active_recoveries": recoveries,
            "older_than_window": too_old, "window_minutes": window_minutes,
            "queued" if not dry_run else "would_queue": queued,
            "already_queued": existing, "not_posted": skipped, "rationale_causes": rationale_causes}


RUN_RECORD_FOLDER = Path("daily_app_outputs") / "plan_status_post_runs"


def record_run(result: Mapping[str, Any], folder: Path, *, now: datetime | None = None) -> Path:
    """One line per minute run, beside the store. The task runs under pythonw, which has no stdout,
    so without this a refused export (EXPORT_STALE, EXPORT_UNREADABLE) left no trace."""
    now = now or datetime.now(timezone.utc)
    posts = (result.get("publication") or {}).get("posts") or []
    published = {}
    for post in posts:
        published[post.get("status")] = published.get(post.get("status"), 0) + 1
    line = {"at_utc": now.isoformat().replace("+00:00", "Z"), "status": result.get("status"),
            "cause": result.get("cause"),
            "contract_version": result.get("contract_version"), "failed_field": result.get("failed_field"),
            "incident_id": result.get("incident_id"),
            "export_generated_at_utc": result.get("export_generated_at_utc"),
            "export_age_seconds": result.get("export_age_seconds"),
            "max_export_age_minutes": result.get("max_export_age_minutes"),
            "queued": len(result.get("queued") or []), "not_posted": len(result.get("not_posted") or []),
            "publication": (result.get("publication") or {}).get("status"), "posts_by_status": published,
            # CC-437: pythonw has no stdout. Counts hid the exact cards that
            # repeatedly failed preparation or waited behind a parent/limit.
            "posts": [{k: post[k] for k in ("key", "status", "cause", "per_destination",
                "destination_causes", "deferred_destinations") if k in post} for post in posts],
            "not_posted_details": [{k: row[k] for k in ("key", "plan_id", "cause") if k in row}
                                   for row in result.get("not_posted") or []]}
    if "scorecard" in result:
        line["scorecard"] = result["scorecard"]
    if "event_timestamp" in result:
        line["event_timestamp"] = result["event_timestamp"]
    if "audience_collection" in result:
        line["audience_collection"] = {k: v for k, v in result["audience_collection"].items()
            if k in {"state", "scheduled", "collected", "pending", "cause", "outcomes", "public_write_performed", "model_calls"}}
    for name in ("model_usage", "weekly_audience"):
        if name in result:
            line[name] = result[name]
    if "event_packs" in result:
        line["event_packs"] = {"status": result["event_packs"].get("status"), "events": []}
        for event in result["event_packs"].get("events") or []:
            publication = event.get("publication") or {}
            per = (event.get("status") or {}).get("per_destination", {})
            line["event_packs"]["events"].append({
                **{k:event[k] for k in ("event_id", "identity", "stage", "cause") if k in event},
                "publication_state": publication.get("state") or publication.get("status"),
                "per_destination": {d:v.get("status") for d,v in per.items()}})
    neo = (result.get("publication") or {}).get("neo_stored_requests")
    if neo is not None:
        # CC-436: the installed pythonw tick has no stdout. Preserve its exact
        # drain outcome in the existing run record, without request copy/media.
        line["neo_stored_requests"] = {"status":neo.get("status"),"requests":[
            {k:row[k] for k in ("operation_id","destination","request_sha256","status","cause") if k in row}
            for row in neo.get("requests") or []]}
    analysis = (result.get("publication") or {}).get("analysis_distribution")
    if analysis is not None:
        line["analysis_links"] = []
        for row in analysis.get("links") or []:
            outcome = row.get("outcome") or {}
            per = outcome.get("per_destination") or (outcome.get("recovery_preflight") or {}).get("per_destination") or {}
            line["analysis_links"].append({
                **{k: row[k] for k in ("page_id", "destination", "link_id", "state", "cause") if k in row},
                "status": (outcome.get("state") or outcome.get("status")
                           or outcome.get("distribution_status") or row.get("state")),
                "per_destination": {d: v.get("status") for d, v in per.items()},
                "destination_causes": destination_causes({"per_destination": per}),
                "first_failures": {d: v["first_failure"] for d, v in per.items() if v.get("first_failure")}})
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"runs-{now:%Y%m%d}.jsonl"
    with open(path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(line, sort_keys=True, ensure_ascii=False) + "\n")
    return path


# ---------------------------------------------------------------------------------------------
# CC-306 posting step: one READY_FOR_PUBLISHER row becomes one coordinator plan for X, Threads,
# Telegram and Discord (Ops Product, 5 Nov: status posts stay off LinkedIn, Facebook and
# Instagram). Like the daily digest, the plan freezes its validated copy per destination; the
# sole coordinator owns exactly-once, UNKNOWN_WRITE and readback. No Substack canonical: the
# link is the market's page on the site (the preview until CC-305 publishes).
# ---------------------------------------------------------------------------------------------
POST_DESTINATIONS = ("telegram", "discord", "threads", "x", "substack_notes")
# The minute task posts only these; X and Substack Notes use the native agent route.
API_DESTINATIONS = ("telegram", "discord", "threads")
# Jim's decision 83 (5 Nov): a status post carries no site link, only its text and image.
POST_ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\plan-status-posts")
STATE_WORDS = {"WAITING": "new plan", "TRIGGERED": "entry filled", "FILLED": "entry filled", "CANCELLED": "plan cancelled",
               "INVALIDATED": "plan invalidated", "EXPIRED": "plan expired", "VIEW_CHANGED": "view changed"}
LIMITS = {"x": 280, "threads": 500, "telegram": 1024, "discord": 2000, "substack_notes": 10000}
# Every part carries the post image (decision 61's post-image policy), so a Telegram part is a photo caption
# (1024) like the first. Format 2 posts no parts on Telegram or Discord: see _compact_body.
REST_LIMITS: dict = {}
# Decision 106 (9 Nov): the order in which a one-post why keeps its reasons. Jim, 9 Nov: macro, sentiment,
# what is priced, fundamentals and the technical levels (why this zone, why this stop).
COMPACT_ORDER = ("Mechanism", "Positioning", "What is priced", "Why this zone", "Why this invalidation level",
                 "Today's driver", "What confirms it", "Reaction so far", "Invalidation", "Alternative mechanism")
X_URL_LENGTH = 23  # X counts every link as 23 characters


def _row_payload(store, key: str) -> dict:
    row = store.get_outbox_message(key)
    if not row or row["destination"] != DESTINATION:
        raise PlanPostError("PLAN_STATUS_POST_ROW_REQUIRED")
    payload = json.loads(row["payload"])
    multi = payload.get("format") == 4 and payload.get("kind") == "run" and payload.get("symbol") == "MULTI"
    if payload.get("schema_version") != SCHEMA or payload.get("key") != key or not (multi or payload.get("symbol") in MARKETS):
        raise PlanPostError("PLAN_STATUS_POST_ROW_INVALID")
    return payload


def _split(text: str) -> tuple[str, str]:
    body, _, notices = text.rpartition("\n\n")
    # Already-frozen posts retain the disclosure they were issued with.
    if notices.strip() not in {f"{analysis} {CONFLICTS_NOTICE}"
            for analysis in (PUBLIC_NOTICE, "Analysis, not financial advice.")}:
        raise PlanPostError("PLAN_STATUS_POST_NOTICES_REQUIRED")
    return body.strip(), notices.strip()


def _x_length(text: str) -> int:
    # twitter/twitter-text config/v3.json: common ranges weigh one, the rest
    # two, and a transformed URL weighs 23. CC-431's live WTI composer exposed
    # the old len() undercount for bullets. Counting each emoji code point is
    # an upper bound for multi-code-point emoji sequences, never an undercount.
    text = re.sub(r"https?://\S+", "x" * X_URL_LENGTH, unicodedata.normalize("NFC", text))
    ranges = ((0, 4351), (8192, 8205), (8208, 8223), (8242, 8247))
    return sum(1 if any(start <= ord(char) <= end for start, end in ranges) else 2 for char in text)


def _excerpt(text: str, room: int) -> str:
    if len(text) <= room:
        return text
    if room < 2:
        return ""
    return text[:room - 1].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"


def _text_parts(body: str, notices: str, limit: int, credit: str = "", *, lines: bool = False,
                rest_limit: int | None = None) -> list[str]:
    """Full source text, bounded parts. Each part retains the public notices. With `lines` a part ends at a
    line where it can; `rest_limit` bounds the parts after the first (a Telegram text message after the photo)."""
    parts = []
    while body:
        suffix = "\n\n" + "\n\n".join(p for p in (credit if not parts else "", notices) if p)
        room = (limit if not parts or rest_limit is None else rest_limit) - len(suffix)
        if room < 1:
            raise PlanPostError("PLAN_STATUS_NOTICES_EXCEED_LIMIT")
        if len(body) <= room:
            end = len(body)
        else:
            end = body.rfind("\n", 0, room + 1) if lines else -1
            if end < room // 2:
                end = body.rfind(" ", 0, room + 1)
            if end <= 0:
                end = room
        parts.append(body[:end].rstrip() + suffix)
        body = body[end:].lstrip()
    return parts


def _short_body(row: Mapping[str, Any], room: int) -> str:
    """A sourced excerpt, never a newly authored explanation or probability."""
    calls = row.get("conditional_calls") or []
    lead = (f"{TITLES[row['symbol']]}: {STATE_WORDS[row['state']]}. "
            + " ".join(conditional_call_text(c) for c in calls)) if calls else row["lead"]
    branches = []
    for line in row["why"]:
        match = re.fullmatch(r"(Base case|Main alternative)(.*?) \(Capital Chronicle model estimate\): (.*)", line)
        if match:
            branches.append((match[1] + match[2] + ": ", match[3]))
    label = " Capital Chronicle model estimate: " if branches else " Why: "
    if not branches:
        branches = [("", row["why"][0])]
    available = room - len(lead) - len(label) - sum(len(prefix) for prefix, _ in branches) - (len(branches) - 1) * 2
    if available < len(branches) * 8:
        # The full conditional call is mandatory. X can use its existing ordered
        # thread; Threads can use its attached chart plus a concise conditional call.
        raise PlanPostError("PLAN_STATUS_SHORT_CONDITION_TOO_LONG")
    excerpts = [_excerpt(value, available // len(branches)) for _, value in branches]
    return lead + label + "; ".join(prefix + value for (prefix, _), value in zip(branches, excerpts))


def _short_reasons(row: Mapping[str, Any], room: int) -> str:
    """Format 2 on Threads (500 characters): the full call, then the mechanism and the zone's reason as far as
    they fit. The whole reasoning is in the Telegram, Discord, Substack Notes and X copies."""
    calls = row.get("conditional_calls") or []
    title = row.get("instrument_title") or TITLES[row['symbol']]
    head = (f"{title}: the reasoning behind our plan." if row.get("kind") == "why"
            else f"{title}: {STATE_WORDS[row['state']]}.")
    lead = row["lead"] if row.get("format") == 3 else (
        (head + " " + " ".join(conditional_call_text(c) for c in calls)) if calls else row["lead"])
    picks = [line.split(": ", 1)[1] for line in row["why"]
             if line.split(": ", 1)[0] in {"Mechanism", "Why this zone"}] or [row["why"][0]]
    tail = " Full reasoning on our Telegram channel."
    available = room - len(lead) - len(" Why: ") - len(tail)
    if available < 40 and row.get("format") == 3:
        # Both entry conditions, horizon, invalidation and instrument survive the short destination.
        tail = ""
        if len(lead) > room:
            lead = lead.replace(f"{title}: new plan.", f"{title}.", 1)
        available = room - len(lead) - len(" Why: ")
        if len(lead) > room:
            raise PlanPostError("PLAN_STATUS_SHORT_CONDITION_TOO_LONG")
        if available < 15:
            return lead
        return lead + " Why: " + _excerpt(" ".join(picks), available)
    if available < 40:
        raise PlanPostError("PLAN_STATUS_SHORT_CONDITION_TOO_LONG")
    return lead + " Why: " + _excerpt(" ".join(picks), available) + tail


def _compact_body(row: Mapping[str, Any], room: int) -> str:
    """Decision 106: the reasons in one post of at most `room` characters. The odds first, then COMPACT_ORDER;
    every line is shortened (at a word, with an ellipsis) before the last one is dropped."""
    odds, reasons = [], {}
    for line in row["why"]:
        head = line.partition(": ")[0]
        if head.startswith(("Base case", "Main alternative")):
            odds.append(line)
        else:
            reasons[head] = line
    lines = (odds + [reasons[h] for h in COMPACT_ORDER if h in reasons]
             + [line for h, line in reasons.items() if h not in COMPACT_ORDER])
    budget = room - len(row["lead"]) - len("\nWhy:")
    while lines:
        for cap in range(max(map(len, lines)), 59, -5):
            fitted = [_excerpt(line, cap) for line in lines]
            if sum(len(line) + 3 for line in fitted) <= budget:  # each line adds "\n• "
                return row["lead"] + "\nWhy:" + "".join("\n• " + line for line in fitted)
        lines = lines[:-1]
    return row["lead"]


def _x_pack(text: str, limit: int, *, preserve_lines: bool = False) -> list[str]:
    """X thread posts: whole lines where they fit, otherwise whole words."""
    chunks, current = [], ""
    for line in text.split("\n"):
        if preserve_lines and _x_length(line) <= limit:
            if current and _x_length(current + "\n" + line) > limit:
                chunks.append(current)
                current = ""
            current = (current + "\n" + line).strip()
            continue
        for index, word in enumerate(line.split(" ")):
            joiner = ("\n" if index == 0 else " ") if current else ""
            if _x_length(current + joiner + word) <= limit:
                current += joiner + word
                continue
            if current:
                chunks.append(current)
            current = word
    if current:
        chunks.append(current)
    return chunks


def destination_payloads(row: Mapping[str, Any], *, card_id: str, chart_credit: bool = False) -> dict:
    """The exact copy per destination: the post and the notices, no link (decision 83). With a
    TradingView snapshot, "Chart: TradingView" follows the post (Terms section 4, decision 82)."""
    if row.get("format") == 4:
        from .plan_call_cards_v1 import destination_payloads as card_payloads
        return card_payloads(row, card_id=card_id, chart_credit=chart_credit)
    body, notices = _split(row["text"])
    link = CHART_CREDIT if chart_credit else ""
    payloads = {}
    v2 = row.get("format") in {2, 3}  # format 3 carries CC-383's instrument/entry fields
    for destination in (API_DESTINATIONS if row.get("kind") == "result" else POST_DESTINATIONS):
        destination_body = body
        if row.get("why") and destination == "threads" and v2:
            destination_body = _short_reasons(row, LIMITS["threads"] - len(notices) - 2 - (len(link) + 2 if link else 0))
        elif row.get("why") and destination in {"threads", "x"} and not v2:
            destination_body = _short_body(row, LIMITS["threads"] - len(notices) - 2 - (len(link) + 2 if link else 0))
        elif row.get("why") and destination in {"telegram", "discord"} and v2:
            room = LIMITS[destination] - len(notices) - 2 - (len(link) + 2 if link else 0)
            if len(destination_body) > room:
                destination_body = _compact_body(row, room)
        text = "\n\n".join(part for part in (destination_body, link, notices) if part)
        if destination == "x" and _x_length(text) > LIMITS["x"]:
            # Whole sentences per post: the chart credit with the first, the notices last. Format 2 posts the
            # whole reasoning as an X thread, packed by line and word.
            chunks, current = [], ""
            if v2:
                chunks = _x_pack(destination_body, LIMITS["x"] - (_x_length(link) + 2 if link else 0),
                                 preserve_lines=row.get("format") == 3)
            else:
                sentences = re.split(r"(?<=\.)\s+(?=[A-Z])", destination_body)
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
            posts = [{"text": c, "media_asset_ids": [card_id] if card_id else [] if i == 0 and card_id else [], "order": i,
                      "role": "root" if i == 0 else "reply"} for i, c in enumerate(chunks)]
            payloads[destination] = {"destination": destination, "text": chunks[0], "posts": posts,
                                     "root_text": chunks[0], "reply_texts": chunks[1:],
                                     "full_text": "\n\n".join(chunks), "media_asset_ids": [card_id] if card_id else []}
            continue
        if (_x_length(text) if destination == "x" else len(text)) > LIMITS[destination]:
            if row.get("why") and destination in {"telegram", "discord", "substack_notes"}:
                parts = _text_parts(body, notices, LIMITS[destination], link, lines=v2,
                                    rest_limit=REST_LIMITS.get(destination) if v2 else None)
                payloads[destination] = {"destination": destination, "text": text, "full_text": text,
                                         "media_asset_ids": [card_id] if card_id else [], "parts": parts}
                continue
            raise PlanPostError("PLAN_STATUS_POST_TOO_LONG:" + destination)
        payloads[destination] = {"destination": destination, "text": text, "full_text": text,
                                 "media_asset_ids": [card_id] if card_id else []}
    if row.get("correction_of"):
        for destination, payload in payloads.items():
            originals = row["correction_of"].get(destination) or []
            payload["correction_of"] = originals
            if originals and destination in {"telegram", "threads", "x", "substack_notes"}:
                payload["reply_to_id"] = originals[0]["public_object_id"]
                payload["reply_to_url"] = originals[0].get("public_object_url")
    return payloads


def _part_payloads(payloads: dict, part: int = 0) -> dict:
    result = {}
    for destination, payload in payloads.items():
        if not payload.get("parts"):
            if part == 0:
                result[destination] = dict(payload)
            continue
        parts = payload.get("parts") or [payload["full_text"]]
        if part >= len(parts):
            continue
        result[destination] = {k: v for k, v in payload.items() if k != "parts"}
        result[destination].update(text=parts[part], full_text=parts[part],
                                   media_asset_ids=payload["media_asset_ids"] if part == 0 else [])
    return result


def card_article(row: Mapping[str, Any]) -> dict:
    at = _utc(row["at_utc"])
    if row.get("kind") == "result":
        return {"title": f"{TITLES[row['symbol']]}: plan result — {row['result'].lower()}",
                "dek": _split(row["text"])[0], "display_date": f"{at.astimezone(PUBLIC_TZ):%B %d, %Y}",
                "author_identity": "Capital Chronicle", "publisher_identity": "Capital Chronicle"}
    if row.get("correction_of"):
        return {"title": "Correction: price had not reached either zone", "dek": _split(row["text"])[0],
                "display_date": f"{at.astimezone(PUBLIC_TZ):%B %d, %Y}",
                "author_identity": "Capital Chronicle", "publisher_identity": "Capital Chronicle"}
    words = "the reasoning behind our plan" if row.get("kind") == "why" else STATE_WORDS[row["state"]]
    return {"title": f"{row.get('instrument_title') or TITLES[row['symbol']]}: {words}",
            "dek": _split(row["text"])[0], "display_date": (lambda et: f"{et:%B} {et.day}, {et.year}")(at.astimezone(PUBLIC_TZ)),
            "author_identity": "Capital Chronicle", "publisher_identity": "Capital Chronicle"}


CHART_CREDIT = "Chart: TradingView"
SNAPSHOT_RUN_BUDGET_SECONDS = 150  # later captures wait for the next existing minute tick


def plan_facts(row: Mapping[str, Any]) -> list[tuple[str, str]]:
    """The fallback card's facts: the plan's zone, invalidation, status and time. No target."""
    levels = row.get("levels") or {}
    facts = []
    if row.get("instrument_title"):
        facts.append(("Instrument", row["instrument_title"]))
        if row.get("price_basis") == "plan":
            facts.append(("Prices", "Plan-price levels"))
    if row.get("kind") == "result":
        facts.extend([("Result", row["result"].lower()), ("Scored calls", str(row["scored_call_count"]))])
    if levels.get("zone_low") is not None and levels.get("zone_high") is not None:
        facts.append(("Entry zone", f"{_level(levels['zone_low'])}–{_level(levels['zone_high'])}"))
    if levels.get("invalidation_level") is not None and levels.get("direction") in {"bullish", "bearish"}:
        side = "Below" if levels["direction"] == "bullish" else "Above"
        if row.get("price_basis") == "instrument":
            side = "Below" if Decimal(str(levels["invalidation_level"])) < Decimal(str(levels["zone_low"])) else "Above"
        facts.append(("Invalidation", f"{side} {_level(levels['invalidation_level'])}"))
    for entry in row.get("entries") or []:
        if entry["kind"] == "BREAKOUT":
            facts.append(("Breakout", _level(entry["level"])))
    state = ("scored" if row.get("kind") == "result" and row.get("scored") else
             "not scored — entry condition not met" if row.get("kind") == "result" else
             "waiting for price to reach the zone" if row.get("kind") == "why"
             else STATE_WORDS.get(row.get("state"), "status update"))
    facts.append(("Status", state[0].upper() + state[1:]))
    facts.append(("As of", _when(row["at_utc"])))
    return facts


def _post_image(row: Mapping[str, Any], folder: Path, *, snapshot=None, snapshot_allowed=None,
                ratio: str = "16:9") -> tuple[dict | None, bool]:
    """CC-459: every new plan image is TradingView; after two failures use text."""
    from live_contentops import tradingview_snapshot_v1 as tv
    image_input = None
    if (row.get("levels") or {}).get("image_source_plan") and row.get("kind") in {"setup", "result"}:
        from .image_template_inputs_v1 import from_plan, from_result
        image_input = from_result(row) if row.get("kind") == "result" else from_plan(row)
    asset = tv.plan_snapshot(row, folder, snapshot=snapshot, snapshot_allowed=snapshot_allowed, ratio=ratio,
                             **({"image_input": image_input} if image_input else {}))
    if image_input:
        return asset, asset is not None
    if asset:
        from live_contentops import tradingview_plan_overlay_v1 as overlay
        try:
            asset = overlay.apply(asset, row)
        except (ValueError, KeyError, OSError) as exc:
            tv.record_outcome({"key": row["key"], "market": row["symbol"], "status": "PLAIN_SNAPSHOT",
                               "cause": str(exc)[:200]})
    return asset, asset is not None



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
    if row.get("format") == 4:
        from .plan_call_cards_v1 import prepare_post as card_post, DESTINATIONS as card_destinations
        if destinations == POST_DESTINATIONS:
            destinations = card_destinations
        return card_post(store, key, root=root, host=host, destinations=destinations,
                         snapshot=snapshot, snapshot_allowed=snapshot_allowed)
    if row.get("kind") == "result":
        if any(d not in API_DESTINATIONS for d in destinations):
            if destinations != POST_DESTINATIONS:
                raise PlanPostError("PLAN_RESULT_DESTINATION_INVALID")
            destinations = API_DESTINATIONS
    folder = Path(root) / key
    article = card_article(row)
    context_path = folder / "run_context_v1.json"
    prior_context = json.loads(context_path.read_bytes()) if context_path.is_file() else {}
    frozen_context = bool(prior_context and store.get_dispatches_for_work_item(key))
    if frozen_context:
        prior_assets = (prior_context.get("media") or {}).get("assets") or []
        card = prior_assets[0] if prior_assets else None
        chart_credit = bool(prior_context.get("chart_credit"))
    else:
        card, chart_credit = _post_image(row, folder, snapshot=snapshot, snapshot_allowed=snapshot_allowed)
    if host is None:
        from live_contentops.cloudinary_delivery_media_v1 import prepare_cloudinary_delivery_media as host
    manifest_path = folder / "delivery_media_manifest_v1.json"
    if card and not _hosted(manifest_path, card):
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
    full_payloads = destination_payloads(row, card_id=card["asset_id"] if card else None, chart_credit=chart_credit)
    payloads = _part_payloads(full_payloads)
    context = {"schema_version": "contentops.plan_status_post_context.v1", "article": {**article, "body": row["text"]},
               "selection": {}, "media": {"assets": [card] if card else []}, "plan_status_post": key,
               "chart_credit": chart_credit,
               **({"status_post_continuations": prior_context["status_post_continuations"]}
                  if prior_context.get("status_post_continuations") else {})}
    if not frozen_context:
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
    plan = {"schema_version": "contentops.publication_plan.v1", "plan_status_post": key,
            "plan_hash": hashlib.sha256(("plan-status-post:" + key).encode()).hexdigest(),
            "story_identity": key, "article_identity": key, "package_identity": key,
            "publication_window": {"window_identity": key}, "output_dir": str(folder.resolve()),
            "status_post_card_id": card["asset_id"] if card else None, "transport_registry_version": REGISTRY_VERSION,
            "policy_mode_version": "AUTONOMOUS_DEFAULT:cc306.v1", "destinations": rows}
    continuations = []
    for part in range(1, max(len(p.get("parts") or [p]) for p in full_payloads.values())):
        chosen = _part_payloads(full_payloads, part)
        child = f"{key}-part-{part}"
        child_rows = [{**r, "payload": chosen[r["destination"]]["full_text"],
                       "payload_hash": hashlib.sha256(chosen[r["destination"]]["full_text"].encode()).hexdigest()}
                      for r in rows if r["destination"] in chosen]
        if child_rows:
            continuations.append({**plan, "plan_status_part": part, "work_item_id": child,
                "story_identity": child, "article_identity": child, "package_identity": child,
                "plan_hash": hashlib.sha256(("plan-status-post:" + child).encode()).hexdigest(),
                "destinations": child_rows})
    if set(destinations) == set(API_DESTINATIONS) and not frozen_context:
        context["status_post_continuations"] = continuations
        (folder / "run_context_v1.json").write_bytes(canonical_bytes(context))
    return {**plan, "continuations": continuations}


def _expected(store, key: str, output_dir: str, part: int = 0) -> tuple[dict, dict]:
    row = _row_payload(store, key)
    context = json.loads((Path(output_dir) / "run_context_v1.json").read_bytes())
    if context.get("plan_status_post") != key:
        raise PlanPostError("PLAN_STATUS_POST_PACKAGE_MISMATCH")
    card_id = (context["media"]["assets"][0]["asset_id"] if context["media"]["assets"] else None)
    if row.get("format") == 4:
        from .plan_call_cards_v1 import destination_payloads as card_payloads
        return row, card_payloads(row, card_id=card_id, parents=context.get("status_post_parents"),
                                 carousel=context.get("status_post_instagram_carousel"),
                                  portrait_id=context.get("status_post_threads_image"),
                                 chart_credit=bool(context.get("chart_credit")),
                                 complete_levels=context.get("status_post_chart_policy") == "CC459_TRADINGVIEW")
    return row, _part_payloads(destination_payloads(row, card_id=card_id,
                              chart_credit=bool(context.get("chart_credit"))), part)


def validate_status_post_plan(store, work_item_id: str, plan: Mapping[str, Any]) -> dict:
    key = str(plan.get("plan_status_post") or "")
    part = plan.get("plan_status_part", 0)
    if not isinstance(part, int) or part < 0 or work_item_id != (f"{key}-part-{part}" if part else key):
        raise PlanPostError("PLAN_STATUS_POST_WORK_ITEM_MISMATCH")
    row, payloads = _expected(store, key, str(plan.get("output_dir") or ""), part)
    context = json.loads((Path(plan["output_dir"]) / "run_context_v1.json").read_bytes())
    from .tradingview_plan_overlay_v1 import validate as validate_overlay
    for asset in (context.get("media") or {}).get("assets") or []:
        if asset.get("plan_overlay"):
            validate_overlay(asset, _row_payload(store, asset["plan_overlay"]["source"]["key"]))
    for item in plan.get("destinations") or []:
        destination = item.get("destination")
        if (destination not in payloads or item.get("payload") != payloads[destination]["full_text"]
                or item.get("canonical_url")):
            raise PlanPostError("PLAN_STATUS_POST_PLAN_COPY_CHANGED")
    return {"key": key, "part": part, "payloads": payloads}


def validate_status_post_intent(store, intent: Mapping[str, Any]) -> None:
    """Re-checked immediately before every write: the frozen copy is still the stored post's."""
    key = str(intent.get("plan_status_post") or "")
    part = intent.get("plan_status_part", 0)
    row, payloads = _expected(store, key, str(intent.get("output_dir") or ""), part)
    # Decision 82 / CC-459: exact readback remains available for old objects,
    # while a fresh write can never send the parked drawn levels picture.
    context = json.loads((Path(intent["output_dir"]) / "run_context_v1.json").read_bytes())
    if any(a.get("modality") != "tradingview_chart_snapshot" for a in (context.get("media") or {}).get("assets") or []):
        raise PlanPostError("JIM_DECISION_82_TRADINGVIEW_CHART_REQUIRED")
    if row.get("format") == 4:
        # Frozen copy is the authority. A later formatter or disclosure change
        # cannot rewrite it or make an exact historical intent fail comparison.
        # The intent/parent equality and current public-copy checks below stay.
        from .plan_call_cards_v1 import validate_parent_intent
        validate_parent_intent(store, row, intent)
    elif row.get("kind") == "result":
        expected = compose_result({**row, "plan": row["levels"]})["text"]
        if row["text"] != expected:
            raise PlanPostError("PLAN_RESULT_COPY_CHANGED")
    destination = str((intent.get("destination_plan") or {}).get("destination") or "")
    if (intent.get("work_item_id") != (f"{key}-part-{part}" if part else key)
            or intent.get("native_payload") != payloads.get(destination)):
        raise PlanPostError("PLAN_STATUS_POST_INTENT_COPY_CHANGED")
    check_publication_copy({"post": payloads[destination]["full_text"]},
                           conditional_calls=(row.get("conditional_calls") or []) if not part else [])


FRESHNESS_MINUTES = 60
STALE = "STALE_NOT_POSTED"


def freshness_limit_minutes(payload) -> int:
    """60 minutes for a new post; a later state of an announced plan keeps LATE_STATE_HOURS. A why follow-up
    stays postable while its plan is valid, up to LATE_STATE_HOURS; a change of the plan's state supersedes it."""
    if payload.get("format") == 4 and payload.get("kind") in {"result", "update"}:
        return float("inf")  # An announced call's dated updates and ending remain owed.
    if payload.get("kind") == "result":
        return float("inf")  # Dated results remain owed; age never turns them into a fresh call.
    if payload.get("why_follow_up"):
        until = (payload.get("levels") or {}).get("valid_until_utc")
        if not until:
            return 0
        return max(0, min(LATE_STATE_HOURS * 60, int((_utc(until) - _utc(payload["at_utc"])).total_seconds() // 60)))
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


def _api_confirmed(store, key: str, *, root: Path = POST_ROOT) -> bool:
    plan_hash = hashlib.sha256(("plan-status-post:" + key).encode()).hexdigest()
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
    for destination in API_DESTINATIONS:
        dispatch = store.get_platform_dispatch(DurablePublicationCoordinator._ids(key, plan_hash, destination)["dispatch_id"])
        if not dispatch or dispatch["status"] != "DISPATCH_CONFIRMED":
            return False
    context = root / key / "run_context_v1.json"
    if context.is_file():
        for continuation in json.loads(context.read_bytes()).get("status_post_continuations") or []:
            for item in continuation["destinations"]:
                dispatch = store.get_platform_dispatch(DurablePublicationCoordinator._ids(
                    continuation["work_item_id"], continuation["plan_hash"], item["destination"])["dispatch_id"])
                if not dispatch or dispatch["status"] != "DISPATCH_CONFIRMED":
                    return False
    return True


def publish_ready(store, *, latest_states=None, active_recoveries=None, now: datetime | None = None, coordinator_for=None,
                  root: Path = POST_ROOT, host=None, limit: int = 5, snapshot=None, automatic_neo=False) -> dict:
    """Post fresh rows to the API destinations (Telegram, Discord, Threads) through the sole
    coordinator, and exit. Never waits on agent work: X is not in this plan (see start_x).

    Freshness: ordinary rows keep 60 minutes; CC-340's current active recovery and CC-306's
    late announced state keep up to 24 hours. A "new plan" post whose plan has since
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
                native_invocation_id="plan-status-posts-cc306", allow_publish=True, automatic=automatic_neo)
            return coordinator
    results = []
    candidates = []
    for row in store.list_outbox_messages(destination=DESTINATION):
        if row["status"] not in {READY, "PUBLISHING"}:
            continue
        payload = json.loads(row["payload"])
        if payload.get("format") == 4:
            continue  # CC-399 uses run -> card -> later-post dependency ordering below.
        recovered = _recoverable(payload, active_recoveries, now)
        freshness = LATE_STATE_HOURS * 60 if recovered else freshness_limit_minutes(payload)
        if row["status"] == READY:
            cause = None
            if payload.get("late_active") and not recovered:
                cause = (SUPERSEDED, "LATE_ACTIVE_PLAN_NO_LONGER_CURRENT_OR_VALID")
            elif _age_minutes(payload, now) > freshness:
                cause = (STALE, "TRANSITION_OLDER_THAN_60_MINUTES_WHEN_POSTER_REACHED_IT")
            elif (payload.get("state") == "WAITING" and latest_states is not None
                    and latest_states.get(payload.get("plan_id"), "WAITING") != "WAITING"):
                cause = (SUPERSEDED, "PLAN_ALREADY_" + str(latest_states[payload["plan_id"]]))
            if cause:
                store.set_outbox_status(row["message_id"], cause[0])
                results.append({"key": row["message_id"], "status": cause[0], "cause": cause[1]})
                continue
        elif _api_confirmed(store, row["message_id"], root=root):
            store.set_outbox_status(row["message_id"], "PUBLISHED")
            continue
        elif (payload.get("late_active") and not recovered) or _age_minutes(payload, now) > freshness:
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
            if all((outcome.get("per_destination", {}).get(d) or {}).get("status") == "DISPATCH_CONFIRMED"
                   for d in API_DESTINATIONS):
                for continuation in plan.get("continuations") or []:
                    child = continuation["work_item_id"]
                    store.create_work_item(story_id=child, title="Plan status continuation", target_surface="MULTI_PLATFORM",
                                           work_item_id=child)
                    scope_to_post(coordinator, child, continuation)
                    coordinator.register_plan(child, continuation)
                    more = coordinator.execute_plan(child, continuation)
                    if not all((more.get("per_destination", {}).get(d["destination"]) or {}).get("status")
                               == "DISPATCH_CONFIRMED" for d in continuation["destinations"]):
                        outcome["per_destination"].update(more.get("per_destination") or {})
                        break
            # The existing minute run issues browser requests; it never waits on
            # an agent. Both destinations are resumed through this same outbox.
            if (_row_payload(store, key).get("why")
                    and all((outcome.get("per_destination", {}).get(d) or {}).get("status") == "DISPATCH_CONFIRMED"
                            for d in API_DESTINATIONS)):
                browser_plan = prepare_post(store, key, root=root, host=host,
                    destinations=("x", "substack_notes"), snapshot=snapshot)
                scope_to_post(coordinator, key, browser_plan)
                coordinator.register_plan(key, browser_plan)
                browser_result = coordinator.execute_plan(key, browser_plan)
                outcome["per_destination"].update(browser_result.get("per_destination") or {})
        except (OSError, ValueError, KeyError, TypeError) as exc:
            results.append({"key": key, "status": "NOT_STARTED", "cause": str(exc)[:200]})
            continue
        per = {d: (o or {}).get("status") for d, o in (outcome.get("per_destination") or {}).items()}
        causes = destination_causes(outcome)
        done = all(per.get(d) == "DISPATCH_CONFIRMED" for d in API_DESTINATIONS)
        store.set_outbox_status(key, "PUBLISHED" if done else "PUBLISHING")
        results.append({"key": key, "status": "PUBLISHED" if done else "PUBLISHING", "per_destination": per,
                        "destination_causes": causes})
    from .plan_call_cards_v1 import publish_ready as publish_cards
    card_results = publish_cards(store, now=now, latest_states=latest_states, root=root,
                                 host=host, coordinator_for=coordinator_for, limit=limit, automatic_neo=automatic_neo,
                                 snapshot=snapshot, snapshot_allowed=lambda: time.monotonic() - started < SNAPSHOT_RUN_BUDGET_SECONDS)
    from .plan_analysis_pages_v1 import distribute_links
    links = distribute_links(store, **({"automatic_neo": True} if automatic_neo else {}))
    return {"status": "OK", "posts": results + card_results["posts"], "analysis_distribution": links}


def destination_causes(outcome: Mapping[str, Any]) -> dict:
    """Retain fixed pre-write/recovery causes, without copy, credentials or tool returns."""
    per = dict(outcome.get("per_destination") or {})
    for destination, recovered in (outcome.get("recovery_preflight") or {}).get("per_destination", {}).items():
        if not per.get(destination) or per[destination].get("status") == "NOT_DISPATCHED":
            per[destination] = recovered
    return {destination: str(value.get("reason_code") or value.get("blocker")
        or value.get("safe_error_classification") or value.get("reconciliation_status")
        or value.get("status") or "DESTINATION_OUTCOME_UNAVAILABLE")[:200]
        for destination, value in per.items()
        if isinstance(value, Mapping) and value.get("status") != "DISPATCH_CONFIRMED"}


def start_x(store, key: str, *, native_invocation_id: str, now: datetime | None = None, root: Path = POST_ROOT,
            host=None, snapshot=None, destination: str = "x") -> dict:
    """Register and issue a status post's X or Substack Notes copy through Neo."""
    from live_contentops.native_neo_executor_v1 import bind_native_neo_coordinator
    now = now or datetime.now(timezone.utc)
    payload = _row_payload(store, key)
    if _age_minutes(payload, now) > _x_freshness_limit(payload, now):
        raise PlanPostError("PLAN_STATUS_X_STALE_NOT_POSTED: transition older than 60 minutes")
    if destination not in {"x", "substack_notes"}:
        raise PlanPostError("PLAN_STATUS_AGENT_DESTINATION_INVALID")
    plan = prepare_post(store, key, root=root, host=host, destinations=(destination,), snapshot=snapshot)
    store.create_work_item(story_id=key, title="Plan status post", target_surface="MULTI_PLATFORM", work_item_id=key)
    coordinator, _ = bind_native_neo_coordinator(
        store, operation_id=key, output_dir=Path(plan["output_dir"]) / "native-neo",
        native_invocation_id=native_invocation_id, allow_publish=True)
    scope_to_post(coordinator, key, plan)
    coordinator.register_plan(key, plan)
    outcome = coordinator.execute_plan(key, plan)
    return {"key": key, destination: (outcome.get("per_destination") or {}).get(destination)}


def pending_x(store, *, now: datetime | None = None, destination: str = "x") -> list[dict]:
    """Status posts' pending browser requests, freshest first."""
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
            if request.get("destination") == destination:
                pending.append({"key": row["message_id"], "request_sha256": request["request_sha256"],
                                "action": request["action"], "age_minutes": round(_age_minutes(payload, now), 1),
                                "fresh": _age_minutes(payload, now) <= _x_freshness_limit(payload, now)})
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
    if not packet or packet["request"].get("destination") not in {"x", "substack_notes"}:
        raise PlanPostError("PLAN_STATUS_X_REQUEST_REQUIRED")
    if packet["request"]["action"] == "PUBLISH" and packet["request"].get("destination") == "x":
        dispatch = store.get_platform_dispatch(packet["request"].get("dispatch_attempt_identity") or "")
        message = store.get_outbox_message(dispatch["message_id"]) if dispatch else None
        if message:
            intent = json.loads(message["payload"])
            from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
            ids = DurablePublicationCoordinator._ids(intent["work_item_id"], intent["plan_hash"], "x")
            if any(r["reconciliation_id"] == ids["reconciliation_id"]
                   and r["status"] == "X_NON_API_AUTOMATION_PROHIBITED"
                   for r in store.get_reconciliations_for_work_item(key)):
                require_active_x_restoration(store, intent, now=now)
    if (packet["request"]["action"] == "PUBLISH"
            and _age_minutes(payload, now) > _x_freshness_limit(payload, now)):
        raise PlanPostError("PLAN_STATUS_X_STALE_NOT_POSTED: transition older than 60 minutes")
    return executor.begin(request_sha256)


def _current_rows(now) -> list[dict] | None:
    """The export as it stands, for the X route's late checks; None when the file is stale, so a stale
    export never extends a post's freshness."""
    try:
        return read_transitions(EXPORT_DIR, main_root=MAIN_ROOT, now=now, max_age_minutes=EXPORT_MAX_AGE_MINUTES)
    except PlanPostError as exc:
        if str(exc).startswith(STALE_EXPORT):
            return None
        raise


def require_active_x_restoration(store, intent, *, now=None) -> None:
    """Decision 112: an exact prior X no-write resumes only for its still-active plan.

    Keep its frozen event time/copy and the new actual dispatch clock separate.
    Readback remains available after the plan ends; only a fresh write is checked.
    """
    now = now or datetime.now(timezone.utc)
    key = intent.get("plan_status_post")
    if not key:
        raise PlanPostError("X_RESTORATION_STATUS_POST_REQUIRED")
    payload = _row_payload(store, key)
    current = _current_rows(now)
    if current is None:
        raise PlanPostError("X_RESTORATION_CURRENT_PLAN_EXPORT_STALE")
    if not _recoverable(payload, active_recoveries(current, now), now):
        raise PlanPostError("X_RESTORATION_PLAN_NO_LONGER_ACTIVE_OR_VALID")


def _x_freshness_limit(payload, now) -> int:
    # X's agent may arrive after the minute tick. Re-read Main before a late active write;
    # identity/readback requests remain available even if the public state has since ended.
    if payload.get("why_follow_up"):
        rows = [r for r in _current_rows(now) or [] if r["plan_id"] == payload.get("plan_id")]
        if not rows or max(rows, key=lambda r: _utc(r["at_utc"]))["to"] != "WAITING":
            return 0
        return freshness_limit_minutes(payload)
    if payload.get("state") in ACTIVE and _age_minutes(payload, now) > FRESHNESS_MINUTES:
        current = _current_rows(now)
        if current is not None and _recoverable(payload, active_recoveries(current, now), now):
            return LATE_STATE_HOURS * 60
        return FRESHNESS_MINUTES
    return freshness_limit_minutes(payload)


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
