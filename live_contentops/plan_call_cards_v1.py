"""CC-399: run announcements, source-bound call cards and their replies.

Uses the plan-status outbox and DurablePublicationCoordinator. Historical packets
keep their original composer. No analytical value is estimated here.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from functools import cache
import hashlib
import json
from pathlib import Path
import re
from typing import Mapping

from . import plan_status_posts_v1 as posts
from . import scenario_voice_v1 as voice
from .event_article_guard_v1 import PUBLIC_NOTICE, CONFLICTS_NOTICE, check_publication_copy, conditional_call_text
from .neo_destination_handoff_v1 import LINKEDIN_DESTINATIONS
from .plan_reader_copy_v1 import CURRENT_LEVEL_CONTRACT, NINE_LAYER_COPY, PHASE_LEVEL_CONTRACTS, THREAD_CONTRACT

EFFECTIVE = datetime(2026, 11, 10, 2, 11, tzinfo=timezone.utc)
LINKEDIN_PLAN_LINK_EFFECTIVE = datetime(2026, 11, 20, 4, 38, tzinfo=timezone.utc)
FORMAT = 4
API_DESTINATIONS = ("telegram", "discord", "threads", "facebook_page", "instagram_business")
DESTINATIONS = (*API_DESTINATIONS, "linkedin", "x", "substack_notes")
TERMINAL = {"CLOSED", "CANCELLED", "INVALIDATED", "EXPIRED", "VIEW_CHANGED"}
NOTICES = f"{PUBLIC_NOTICE} {CONFLICTS_NOTICE}"
# A definite no-write is a settled destination, not work that can consume every
# minute's first five card slots forever. Uncertain sends remain recovery work.
SETTLED_DISPATCHES = frozenset({"DISPATCH_CONFIRMED", "DEFINITE_NO_WRITE",
    "DERIVATIVE_EXPIRED_STALE_NO_WRITE", "DERIVATIVE_RECOVERY_RETRY_EXHAUSTED_NO_WRITE",
    "EXTERNAL_REMOVAL_REPORTED_NO_RETRY", "UNSENT_MEDIA_SUPERSEDED"})
SETTLED_POST = "SETTLED"
SETTLED_COPY = "PLAN_POST_SETTLED"
DISCORD_CHANNEL_PART = 1
ANALYSIS_FIRST_PART = 2
# Reserve a separate identity from the numbered analysis continuations.
LATE_CHART_PART = 1000
# These existing transports can attach an image to an exact own-post reply.
LATE_CHART_DESTINATIONS = frozenset({"telegram", "discord", "threads", "facebook_page", "x", "substack_notes"})
GLOSSARY = {
    "DXY": "the US dollar index", "COT": "the futures positioning report",
    "M15": "short-interval", "M5": "short-interval", "H1": "hourly",
    "risk-off": "risk aversion", "risk-on": "risk appetite",
    "invalidation": "the level that proves the idea wrong",
    "priced": "already reflected in prices", "macro": "economic",
}


# Jim, 23 Nov 2026 about 05:30 GMT+7 ("Keep targets off"): decision 40 keeps profit targets off public copy.
# Rows queued from this time carry the policy; earlier rows keep their exact bytes for validate().
NO_TARGET_POLICY = "DECISION_40_NO_TARGET"
NO_TARGET_EFFECTIVE = datetime(2026, 11, 22, 22, 30, tzinfo=timezone.utc)
# Ops Product, 23 Nov 2026: t.me/CapitalChronicle/230, a 17 Nov plan's corrected result posted on 23 Nov with no
# date, read as the 20 Nov plan. A result row queued from this time names its plan's dates and any correction.
RESULT_FRAME_POLICY = "RESULT_FRAME_V1"
RESULT_FRAME_EFFECTIVE = datetime(2026, 11, 23, 4, 0, tzinfo=timezone.utc)
# Jim, 23 Nov 2026 04:50Z (decision 66): ContentOps posts nothing until Wed 25 Nov 23:00 GMT+7. A plan that resolves
# in this window is shown by the pinned scorecard, never as a late post of its own when posting resumes.
JIM_PAUSE_START = datetime(2026, 11, 23, 4, 50, tzinfo=timezone.utc)
JIM_PAUSE_END = datetime(2026, 11, 25, 16, 0, tzinfo=timezone.utc)
# Jim, 23 Nov 09:22Z: all live work stops until next week's relaunch. The pause ends when the restore writes its
# record; until then every result after the start stays off. JIM_PAUSE_END is the fallback for an unreadable record.
JIM_PAUSE_RECORD = Path(r"A:\Capital Chronicle\Runtime\ContentOps\control\pause-20261123\restored.json")


def jim_pause_window(*, live=None):
    """(start, end) of Jim's posting pause; a test never reads the live control record."""
    import sys
    if live is None:
        live = "_pytest" not in sys.modules
    if not live:
        return JIM_PAUSE_START, JIM_PAUSE_END
    try:
        restored = json.loads(JIM_PAUSE_RECORD.read_text(encoding="utf-8-sig"))
        return JIM_PAUSE_START, posts._utc(restored["started_at_utc"])
    except FileNotFoundError:
        return JIM_PAUSE_START, OPEN_PAUSE_END
    except (OSError, ValueError, KeyError, TypeError):
        return JIM_PAUSE_START, JIM_PAUSE_END


OPEN_PAUSE_END = datetime.max.replace(tzinfo=timezone.utc)


def inside_jim_pause(at_utc, now, window):
    """A result that ended inside the pause stays off the feed (the pinned scorecard shows it).

    Audit of 23 Nov 2026: if the minute job runs again while the restore record is absent (a restore that
    stopped after enabling the tasks, or tasks enabled by hand), the window never closed and every later
    result was skipped for good. A job that is running has resumed posting: once the earliest resume
    (JIM_PAUSE_END) has passed, a result that ended within the posting window of this run is fresh news.
    """
    start, end = window
    at = posts._utc(at_utc)
    if not start <= at < end:
        return False
    fresh = 0 <= (now - at).total_seconds() <= posts.FRESHNESS_MINUTES * 60
    return not (end == OPEN_PAUSE_END and at >= JIM_PAUSE_END and fresh)


def plan_dates(start_utc, end_utc):
    """'17 Nov', '17–18 Nov' or '30 Nov–1 Dec', in the public (ET) calendar."""
    start = posts._utc(start_utc).astimezone(posts.PUBLIC_TZ)
    end = max(start, posts._utc(end_utc).astimezone(posts.PUBLIC_TZ))
    if start.date() == end.date():
        return f"{start.day} {start:%b}"
    if (start.year, start.month) == (end.year, end.month):
        return f"{start.day}–{end.day} {end:%b}"
    return f"{start.day} {start:%b}–{end.day} {end:%b}"


def result_frame(item):
    registered = item.get("registered_at_utc") or (item.get("source_plan") or {}).get("registered_at_utc")
    return {"policy": RESULT_FRAME_POLICY, "plan_dates": plan_dates(registered or item["at_utc"], item["at_utc"]),
            "correction": bool(item.get("corrects_outcome_id"))}


def _hash(value):
    return posts._sha(value)


def _clock(value):
    at = posts._utc(value).astimezone(posts.PUBLIC_TZ)
    return f"{at.day} {at:%b %H:%M} ET"


def _safe_line(value, cap=200):
    if not isinstance(value, str):
        return ""
    value = posts._public_reason(value)
    return value if value and len(value) <= cap else ""


def _tick(plan):
    """Use the exported tick; never guess a conversion from the private book."""
    value = plan.get("tick_size")
    try:
        number = Decimal(str(value))
        return number if number.is_finite() and number > 0 else None
    except InvalidOperation:
        return None


def level(value, plan):
    number = Decimal(str(value))
    if not number.is_finite():
        raise posts.PlanPostError("PLAN_CARD_LEVEL_NOT_FINITE")
    tick = _tick(plan)
    if tick:
        number = (number / tick).quantize(Decimal(1), rounding=ROUND_HALF_UP) * tick
    return posts._level(number)


def _target(value):
    if isinstance(value, Mapping):
        low = value.get("minimum", value.get("low"))
        high = value.get("maximum", value.get("high"))
        return [low, high] if low is not None and high is not None else None
    if isinstance(value, (list, tuple)):
        return list(value) if value and all(v is not None for v in value) else None
    return [value] if value is not None else None


def card_plan(raw):
    plan = posts._display_plan(posts._built_plan(raw))
    scenario = raw.get("scenario_analysis") or {}
    instrument = raw.get("public_instrument") or {}
    mapped = plan.get("price_basis") == "instrument"
    # A mapped instrument never borrows the book's target or tick. Missing
    # mapped fields remain absent, with the existing explicit price-basis line.
    basis = instrument if mapped else raw
    plan["target"] = _target(basis.get("target", basis.get("target_level")))
    plan["tick_size"] = basis.get("tick_size", basis.get("minimum_tick"))
    plan["time_exit_utc"] = (raw.get("time_exit_utc") or raw.get("horizon_end_utc")
                             or scenario.get("horizon_end_utc") or raw.get("expires_at_utc"))
    plan["entry_deadline_utc"] = raw.get("entry_deadline_utc")
    chance = raw.get("stated_chance_pct", raw.get("probability_pct"))
    plan["chance_label"] = "Stated chance"
    if chance is None:
        chance = (scenario.get("base_case") or {}).get("probability_pct")
        plan["chance_label"] = "Base-case chance"
    if isinstance(chance, (int, float)) and not isinstance(chance, bool) and 0 <= chance <= 100:
        plan["chance_pct"] = chance
    call_id = raw.get("public_call_id") or (raw.get("outcome") or {}).get("public_call_id") or raw["plan_id"]
    if raw.get("public_call_id") or (raw.get("outcome") or {}).get("public_call_id"):
        plan["public_call_id"] = str(call_id)
    plan["short_id"] = re.sub(r"^(?:call|plan)_", "", str(call_id))[:8]
    plan["registered_at_utc"] = raw.get("registered_at_utc") or raw.get("not_before_utc")
    plan["reader_reasons"] = raw.get("reader_reasons", raw.get("freeze_reasons", []))
    # CC-465 applies to new preparations; historical-clock replays retain the
    # earlier image contract and frozen packages never gain new source fields.
    if datetime.now(timezone.utc) >= datetime(2026, 11, 11, 16, 25, tzinfo=timezone.utc):
        plan["image_source_plan"] = raw
    return plan


def record_line(status):
    supplied = _safe_line(status.get("public_record_line"), 240)
    if supplied:
        return supplied
    summary = status.get("record_summary") or {}
    if all(isinstance(summary.get(k), int) and not isinstance(summary[k], bool)
           for k in ("judged_count", "right_count")):
        text = f"Record: {summary['judged_count']} calls judged, {summary['right_count']} right"
        baseline = summary.get("trend_rule_right_count")
        if isinstance(baseline, int) and not isinstance(baseline, bool):
            text += f"; trend rule: {baseline} right"
        return text + "."
    scores = {s.get("public_call_id") or s.get("plan_id"): s for s in status.get("scored_calls", [])
              if s.get("result") in {"HIT", "STOPPED", "EXPIRED", "NOT_TRIGGERED"}}
    if not scores:
        return ""
    clocks = [s.get("frozen_at_utc") for s in scores.values() if s.get("frozen_at_utc")]
    since = ""
    if clocks:
        at = min(map(posts._utc, clocks)).astimezone(posts.PUBLIC_TZ)
        since = f"Since {at.day} {at:%b}: "
    plans = {plan["plan_id"]: plan for plan in status.get("plans", []) if plan.get("plan_id")}
    counts = {result: sum(s["result"] == result for s in scores.values())
              for result in ("HIT", "STOPPED", "EXPIRED")}
    labels = {"HIT": "HIT", "STOPPED": "STOPPED", "EXPIRED": "time exits"}
    parts = [f"{counts[result]} {label}" for result, label in labels.items() if counts[result]]
    no_entries = {}
    for score in scores.values():
        if score["result"] == "NOT_TRIGGERED":
            source = score
            if entry_condition_facts(score)[0] is None:
                source = plans.get(score.get("plan_id"), score)
            words = no_entry_words(source)
            no_entries[words] = no_entries.get(words, 0) + 1
    parts.extend(f"{words}: {count}" for words, count in no_entries.items())
    return f"{since}{len(scores)} calls judged: " + ", ".join(parts) + "."


def checked_reasons(values, source):
    """Numbers must occur in this plan's own reasons, never another card."""
    result = []
    if not isinstance(values, list):
        return result
    try:
        for value in values[:3]:
            text = posts._public_reason(value)
            if not text:
                continue
            if _numbers(text) - _numbers(json.dumps(source, ensure_ascii=False)):
                return []
            for label, words in GLOSSARY.items():
                text = re.sub(r"\b" + re.escape(label) + r"\b", words, text, flags=re.I)
            text = posts._excerpt(text, 200)
            check_publication_copy({"body": text}, require_notice=False)
            result.append(text)
    except ValueError:
        return []
    return result


def _numbers(text):
    return {m.replace(",", "").rstrip(".") for m in re.findall(r"(?<!\w)\d[\d,.]*%?", text)}


def source_reasons(raw):
    supplied = raw.get("reader_reasons") or raw.get("freeze_reasons")
    if isinstance(supplied, list) and supplied:
        return supplied[:3]
    source = _reason_source(raw)
    reasons = [v for k, v in source.items() if k not in {"reader_reasons", "freeze_reasons"} and isinstance(v, str) and v.strip()]
    return reasons[:3]


def _reason_source(raw):
    scenario = raw.get("scenario_analysis") or {}
    return {k: raw.get(k) or scenario.get(k) for k in
            (*posts.REASON_FIELDS, "invalidation_text", "reader_reasons", "freeze_reasons")}


ANALYSIS_SECTIONS = (
    ("macro", "Macro"), ("fundamental", "Fundamental"), ("technical", "Technical"),
    ("geopolitical", "Geopolitical"), ("priced_in", "What is priced in"),
    ("scenarios", "Scenarios"), ("desk_process", "How the desk reached its view"),
)


def analysis_publication(raw):
    """CC-432's published result, bound to this exact plan; no run-folder read.

    A page's renderer supplies this optional envelope in the plan export. The
    card consumer does not write that page or estimate any of its contents.
    """
    value = raw.get("analysis_publication")
    if not isinstance(value, Mapping):
        return {}, "CC432_ANALYSIS_PUBLICATION_NOT_SUPPLIED"
    if value.get("plan_id") != raw["plan_id"] or not raw.get("registration_hash") \
            or value.get("registration_hash") != raw["registration_hash"]:
        return {}, "CC432_PLAN_BINDING_MISMATCH"
    url = value.get("canonical_url")
    if not isinstance(url, str) or not re.fullmatch(r"https://capitalchronicle\.substack\.com/p/[a-z0-9-]+", url):
        return {}, "CC432_CONFIRMED_ANALYSIS_URL_REQUIRED"
    sections = value.get("summary") or {}
    if not isinstance(sections, Mapping):
        return {}, "CC432_STRUCTURED_SUMMARY_INVALID"
    clean = {}
    for key, _ in ANALYSIS_SECTIONS:
        text = sections.get(key)
        if not isinstance(text, str) or not text.strip():
            continue
        text = " ".join(text.split())
        # CC-432 supplies already filtered public copy. Recheck the protections
        # common to every destination; no shortening invents a new claim.
        if posts.INTERNAL.search(text) or posts.INTERNAL_RATIONALE.search(text) \
                or re.search(r"\b(?:AI[- ]run|AI[- ]native|GPT|Claude|Opus|Gemini|Luna|Antigravity)\b", text, re.I):
            return {}, "CC432_PUBLIC_SUMMARY_FILTER_FAILED"
        try:
            check_publication_copy({"body": text}, require_notice=False)
        except ValueError:
            return {}, "CC432_PUBLIC_SUMMARY_FILTER_FAILED"
        clean[key] = text
    if not clean:
        return {}, "CC432_STRUCTURED_SUMMARY_EMPTY"
    return {"canonical_url": url, "summary": clean, "registration_hash": raw["registration_hash"]}, None


def compose(row):
    if row.get("state_alert_contract") == "CC543_V1":
        from .plan_state_alerts_v1 import compose as compose_alert
        return compose_alert(row)
    if row.get("reader_contract") == "CC466_V1":
        from .plan_reader_copy_v1 import payloads
        if row.get("reader_fields"):
            text = payloads(row, None)["telegram"]["text"]
            return {"lead": row["reader_fields"]["hook"]["text"], "text": text,
                    "conditional_calls": row.get("conditional_calls") or []}
        return {"lead": "", "text": "", "conditional_calls": []}
    kind = row["kind"]
    if kind == "run":
        at = posts._utc(row["at_utc"]).astimezone(posts.PUBLIC_TZ)
        count = len(row["card_keys"])
        lead = f"Calls from our {at.day} {at:%b %H:%M} ET run: {count}."
        body = _run_summary(row, lead, 60000 - len(NOTICES) - 2)
        return {"lead": lead, "text": body + "\n\n" + NOTICES, "conditional_calls": []}
    plan = row["levels"]
    title = row["instrument_title"]
    identity = f"#{row['short_id']}"
    direction = "long" if plan.get("direction") == "bullish" else "short"
    registered = row.get("registered_at_utc") or row["at_utc"]
    day = posts._utc(registered).astimezone(posts.PUBLIC_TZ)
    calls = []
    if kind == "setup":
        side = "below" if Decimal(str(plan["invalidation_level"])) < Decimal(str(plan["zone_low"])) else "above"
        display = {**plan, **{k: Decimal(level(plan[k], plan).replace(",", ""))
                              for k in ("zone_low", "zone_high", "invalidation_level")}}
        display["entries"] = [{k: Decimal(level(v, plan).replace(",", "")) if k != "kind" and v is not None else v
                               for k, v in entry.items()} for entry in plan.get("entries") or []]
        entry = posts._entry_condition(display)
        horizon = row.get("time_exit_utc") or plan.get("valid_until_utc")
        call = {"condition": entry, "direction": plan["direction"], "market": title,
                "horizon": "the period to " + _clock(horizon),
                "invalidation": f"price moves {side} {level(plan['invalidation_level'], plan)}"}
        calls = [call]
        lead = f"{identity} · {direction} idea\n" + conditional_call_text(call)
        if row.get("delayed_at_utc"):
            lead = "Delayed update to the plan registered " + _clock(registered) + ":\n" + lead
        extra = []
        target = plan.get("target")
        if target and row.get("target_policy") != NO_TARGET_POLICY:
            extra.append("Model target level: " + "–".join(dict.fromkeys(level(v, plan) for v in target)) + ".")
        if row.get("entry_deadline_utc"):
            extra.append("Entry window to " + _clock(row["entry_deadline_utc"]) + ".")
        extra.append("Time exit: " + _clock(horizon) + ".")
        if plan.get("chance_pct") is not None:
            extra.append(f"{plan['chance_label']}: {plan['chance_pct']:g}% (Capital Chronicle model estimate).")
        if row.get("price_basis") == "plan":
            extra.append("Levels use the plan's prices.")
        if row.get("state") in {"TRIGGERED", "FILLED"}:
            extra.append("The position is open.")
    else:
        prefix = f"{title} {direction} of {day.day} {day:%b} ({identity}): "
        extra = []
        if kind == "result":
            lead = prefix + ending_words(row) + f". Ended {_clock(row['at_utc'])}."
        elif row["state"] in {"TRIGGERED", "FILLED"}:
            lead = prefix + f"an entry filled at {_clock(row['at_utc'])}; the position is open."
        else:
            words = {"CANCELLED": "the plan was withdrawn", "VIEW_CHANGED": "the view changed",
                     "CLOSED": "Capital Chronicle's position closed",
                     "INVALIDATED": "the idea's invalidation condition was reached",
                     "EXPIRED": "the entry window ended"}.get(row["state"], "the state changed")
            lead = prefix + f"{words} at {_clock(row['at_utc'])}."
    if kind != "setup":
        extra.extend(["Entry zone: " + level(plan["zone_low"], plan) + "–" + level(plan["zone_high"], plan) + ".",
                      "Invalidation: " + level(plan["invalidation_level"], plan) + "."])
        if plan.get("target") and row.get("target_policy") != NO_TARGET_POLICY:
            extra.append("Model target level: " + "–".join(dict.fromkeys(level(v, plan) for v in plan["target"])) + ".")
        if row.get("entry_deadline_utc"):
            extra.append("Entry window to " + _clock(row["entry_deadline_utc"]) + ".")
        horizon = row.get("time_exit_utc") or plan.get("valid_until_utc")
        if horizon:
            extra.append("Time exit: " + _clock(horizon) + ".")
    analysis = row.get("analysis_publication") or {}
    summary = analysis.get("summary") or {}
    lines = [lead, *extra]
    if summary:
        lines.extend(label + ": " + summary[key] for key, label in ANALYSIS_SECTIONS if summary.get(key))
    else:
        lines.extend("• " + reason for reason in row.get("reasons") or [])
    if analysis.get("canonical_url"):
        lines.append("Full analysis: " + analysis["canonical_url"])
    if row.get("record_line"):
        lines.append(row["record_line"])
    text = "\n".join(lines) + "\n\n" + NOTICES
    check_publication_copy({"body": text}, conditional_calls=calls)
    return {"lead": lead, "text": text, "conditional_calls": calls, "detail_lines": extra}


def destinations_for(row):
    if row.get("state_alert_contract") == "CC543_V1":
        return (*DESTINATIONS, "linkedin_company") if row.get("analysis_linkedin_page_required") else DESTINATIONS
    if row.get("reader_contract") == "CC466_V1":
        return tuple(d for d in DESTINATIONS if d != "linkedin")
    # LinkedIn receives the run and its links, rather than one duplicate root
    # for every card in that run (CC-435).
    return tuple(d for d in DESTINATIONS if d != "linkedin" or (
        row.get("kind") == "run" and row.get("analysis_distribution_version")))


def _run_summary(row, lead, limit):
    analyses = row.get("analysis_publications") or []
    if not analyses:
        return lead
    # Reserve every canonical link before allocating prose. Never shorten a URL
    # or silently drop one market from the run's index.
    blocks = [a["title"] + "\nFull analysis: " + a["canonical_url"] for a in analyses]
    base = lead + "\n\n" + "\n\n".join(blocks)
    if len(base) > limit:
        raise posts.PlanPostError("PLAN_RUN_ANALYSIS_LINKS_TOO_LONG")
    for key, label in ANALYSIS_SECTIONS:
        for index, analysis in enumerate(analyses):
            if not (analysis.get("summary") or {}).get(key):
                continue
            line = label + ": " + analysis["summary"][key]
            candidate = [*blocks[:index], blocks[index] + "\n" + line, *blocks[index + 1:]]
            if len(lead + "\n\n" + "\n\n".join(candidate)) <= limit:
                blocks = candidate
    return lead + "\n\n" + "\n\n".join(blocks)


def entry_condition_facts(plan):
    """Read Main's explicit zone-touch and blocking-cause fields."""
    outcome = plan.get("outcome") or {}
    sources = (outcome, outcome.get("score") or {}, plan)
    traded = next((source["entry_condition_traded"] for source in sources
                   if isinstance(source.get("entry_condition_traded"), bool)), None)
    cause = next((source[key] for key in ("first_blocking_cause", "first_cause") for source in sources
                  if isinstance(source.get(key), str) and source[key]), None)
    return traded, cause


def no_entry_words(plan, *, withdrawn=False):
    traded, cause = entry_condition_facts(plan)
    if traded is False:
        return "price did not reach the entry zone"
    if traded is True:
        words = "price reached the entry zone, but no position was opened"
        category = re.sub(r"[\s-]+", "_", (cause or "").upper())
        if category in {"SOFTWARE_OR_PROCESS_DEFECT", "PROTECTION_OR_RECONCILIATION_BLOCK"}:
            words += " because of a fault on our side"
        return words
    return "the plan was withdrawn without an entry" if withdrawn else "the entry window ended with no entry"


def ending_words(row, *, include_levels=False):
    source = row.get("outcome_source_plan") or row.get("source_plan") or row
    outcome = source.get("outcome") or {}
    not_executed = (row.get("not_executed") is True or outcome.get("not_executed") is True
                    or (outcome.get("score") or {}).get("not_executed") is True)
    if row.get("untriggered") or row.get("triggered_not_traded") or row.get("result") == "NOT_TRIGGERED" or not_executed:
        withdrawn = row.get("result_copy_version") == 2 and source.get("status") == "CANCELLED"
        words = no_entry_words(source, withdrawn=withdrawn)
        market_path = {"HIT": "hit the target", "STOPPED": "reached the invalidation level",
                       "EXPIRED": "ended at the time exit"}
        if not_executed and row.get("result") in market_path:
            words += "; the market path " + market_path[row["result"]]
        return words
    if row.get("result") == "HIT":
        if "TIME_EXIT" in str(row.get("score_basis") or ""):
            return "closed at its time exit" + (", on our side of the entry" if row.get("direction_correct") is True else "")
        return "hit its target"
    if row.get("result") == "STOPPED":
        if include_levels and row.get("scored"):
            levels = row["levels"]
            # The mapped stop applies after entry. The plan's cancel level does not.
            if levels.get("price_basis") == "instrument":
                return f"stopped at its {level(levels['invalidation_level'], levels)} invalidation level"
        return "stopped at its invalidation level"
    if row.get("result") == "EXPIRED":
        side = row.get("direction_correct")
        return "closed at its time exit" + (", on our side of the entry" if side is True else
                                             ", against our entry" if side is False else "")
    return "ended"


def _result_rows(export):
    result = []
    events = export["transitions"].get("transitions", [])
    for raw in export["status"].get("plans", []):
        if raw.get("asset_id") not in posts.MARKETS:
            continue
        outcome = raw.get("outcome") or {}
        score = outcome.get("score") or {}
        ended = [e for e in events if e.get("plan_id") == raw["plan_id"] and e.get("status") in TERMINAL]
        scored = outcome.get("state") in {"SCORED", "SCORED_UNTRIGGERED"} and bool(score)
        if not scored and not ended:
            continue
        if scored and (score.get("plan_id") != raw["plan_id"] or score.get("asset_id") != raw["asset_id"]
                       or score.get("outcome_id") != outcome.get("outcome_id")):
            raise posts.PlanPostError("PLAN_RESULT_SCORE_BINDING_INVALID")
        at = score.get("resolved_at_utc") if scored else max(ended, key=lambda e: posts._utc(e["at_utc"]))["at_utc"]
        untriggered = (outcome.get("state") in {"NOT_SCORED_UNTRIGGERED", "SCORED_UNTRIGGERED"}
                       or score.get("triggered") is False or score.get("result") == "NOT_TRIGGERED")
        not_traded = (score.get("execution_state") == "TRIGGERED_NOT_TRADED"
                      or outcome.get("first_cause") == "TRIGGERED_NOT_TRADED")
        not_executed = outcome.get("not_executed") is True or score.get("not_executed") is True
        if not scored and not untriggered and not not_traded and not not_executed:
            continue  # A watch ending does not establish that an open model trade closed.
        correction = score.get("corrects_outcome_id")
        traded, cause = entry_condition_facts(raw)
        identity = f"{raw['plan_id']}|RESULT" + (f"|{score.get('outcome_id')}" if correction else "")
        result.append({"key": "plan-result-post-" + hashlib.sha256(identity.encode()).hexdigest()[:32],
            "plan_id": raw["plan_id"], "symbol": raw["asset_id"], "to": "RESULT", "at_utc": at,
            "kind": "result", "untriggered": untriggered,
            "triggered_not_traded": not_traded,
            "not_executed": not_executed,
            "entry_condition_traded": traded, "first_blocking_cause": cause,
            "direction_correct": score.get("direction_correct", score.get("went_our_way")),
            "result": outcome.get("result") or score.get("result") or "NOT_TRIGGERED",
            "scored": scored, "outcome_id": outcome.get("outcome_id"),
            "corrects_outcome_id": correction, "score_hash": score.get("content_hash"),
            "score_basis": score.get("score_basis")})
    return result


def _refresh_unissued_no_entry_result(store, message, result, source_for):
    """Correct the same draft before the coordinator has registered any copy."""
    if message["status"] != posts.READY:
        return
    draft = json.loads(message["payload"])
    legacy_words = draft.get("lead", "").partition(": ")[2]
    if (draft.get("state_alert_contract") != "CC543_V1"
            or not legacy_words.startswith(("not triggered", "triggered, not traded"))
            or not (result["untriggered"] or result["triggered_not_traded"] or result["not_executed"])):
        return
    source = source_for(result["plan_id"])
    if source.get("registration_hash") != draft.get("source_plan_registration"):
        return
    updated = {**draft, **{field: result[field] for field in (
        "untriggered", "triggered_not_traded", "not_executed", "result", "scored",
        "outcome_id", "corrects_outcome_id", "score_hash", "score_basis", "direction_correct",
        "entry_condition_traded", "first_blocking_cause",
    )}, "outcome_source_plan": source, "outcome_source_sha256": _hash(source)}
    from .plan_state_alerts_v1 import validate
    try:
        if updated.get("price_basis") is None:
            updated["price_basis"] = card_plan(updated["source_plan"])["price_basis"]
        updated.update(compose(updated))
        validate(updated, store=store)
    except posts.PlanPostError:
        return  # The existing publisher records the original draft's refusal.
    store.finalize_outbox_payload_before_dispatch(
        message_id=draft["key"], status=posts.READY, expected_payload=message["payload"],
        unissued_work_item_id=draft["key"], payload=json.dumps(updated, sort_keys=True, ensure_ascii=False),
    )


def queue_posts(store, export_dir, *, now, window_minutes=60, dry_run=False, render_all=False,
                instagram_profile_reader=None, analysis_copy_root=None, queue_clock=None, **reader):
    if render_all and not dry_run:
        raise ValueError("PLAN_EXPORT_REPLAY_REQUIRES_DRY_RUN")
    try:
        export = posts.read_export(export_dir, **reader)
        seen_at = queue_clock.clock() if queue_clock is not None else None
        version = posts.validate_export_contract(export)
        quarantined = posts.record_row_failures(store, export, dry_run=dry_run)
        freshness = posts.export_freshness(export, now)
        stale = freshness["export_age_seconds"] > posts.EXPORT_MAX_AGE_MINUTES * 60
        if stale and queue_clock is None:
            return {"status": "EXPORT_STALE", "cause": posts.STALE_EXPORT, **freshness}
        observed_rows = posts.rows_from_export(export, include_results=False,
                                              include_replaced_expiries=queue_clock is not None)
        if queue_clock is not None:
            queue_clock.observe([r for r in observed_rows if r["symbol"] in posts.MARKETS],
                                freshness["export_generated_at_utc"], seen_at=seen_at)
        if stale:
            return {"status": "EXPORT_STALE", "cause": posts.STALE_EXPORT, **freshness}
        source_rows = [r for r in observed_rows if not r.get("replaced_expiry")]
        sources = {p["plan_id"]: p for p in export["status"].get("plans", []) if p.get("asset_id") in posts.MARKETS}
        records = record_line(export["status"])
    except posts.PlanExportContractError as exc:
        return posts.rejected_export(store, exc, dry_run=dry_run)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {"status": "EXPORT_UNREADABLE", "cause": str(exc) if isinstance(exc, posts.PlanPostError) else type(exc).__name__}
    existing_rows = store.list_outbox_messages(destination=posts.DESTINATION)
    prior = {r["message_id"]: r for r in existing_rows}
    cards = {}
    announced_cards = set()
    for r in existing_rows:
        p = json.loads(r["payload"])
        pid = p.get("plan_id")
        if pid not in sources:
            continue
        p.setdefault("key", r["message_id"])
        is_card = p.get("kind") == "setup" or (p.get("state") == "WAITING" and not p.get("why_follow_up")) \
            or (p.get("state") in {"TRIGGERED", "FILLED"} and p.get("conditional_calls"))
        if is_card:
            # Settling another destination or retiring unsent copies cannot
            # erase a confirmed setup. Its later state still owes that exact
            # public card an ending, even when the queue label is terminal.
            announced = r["status"] in {"PUBLISHING", "PUBLISHED"} or any(
                _reference(store, r["message_id"], d) for d in _post_destinations(p))
            if announced:
                announced_cards.add(r["message_id"])
            if r["status"] == posts.READY or announced:
                cards.setdefault(pid, p)
    latest = {}
    for row in sorted(source_rows, key=lambda r: posts._utc(r["at_utc"])):
        if row["symbol"] in posts.MARKETS:
            latest[row["plan_id"]] = row
    current_states = {pid: row["to"] for pid, row in latest.items()}
    # CC-322 omits untriggered expiry transitions from the post list, because
    # the result card replaces them. The exported current state still decides
    # whether an older setup/link is current; that omission cannot revive it.
    current_states.update({pid: raw["status"] for pid, raw in sources.items()
                           if raw.get("status") in TERMINAL})
    outcomes = _result_rows(export)
    result_keys = {r["plan_id"]: r["key"] for r in outcomes}
    ended_plans = result_keys.keys()
    current_states.update({pid: "RESULT" for pid in ended_plans if current_states.get(pid) not in TERMINAL})
    payloads, skipped, already = [], [], []
    if queue_clock is not None:
        fill_keys = {r["plan_id"]: r["key"] for r in source_rows if r.get("source_state") == "FILLED"}
        for row in observed_rows:
            pid = row["plan_id"]
            if row.get("replaced_expiry") or (row["to"] in TERMINAL and pid in ended_plans):
                queue_clock.refuse(row, "PLAN_TRANSITION_REPLACED_BY_RESULT", replacement_key=result_keys.get(pid))
            elif row.get("superseded_by_fill"):
                queue_clock.refuse(row, "FILL_EVENT_SUPERSEDES_TRIGGER", replacement_key=fill_keys[pid])
    from .secret_store_v1 import read_secret
    # Freeze the route on NEW rows only. The registered announcement channel
    # cannot create threads through a webhook; Discord permits that only on
    # forum/media channels. Existing cards keep their original thread binding.
    discord_delivery = "bot_thread" if read_secret("DISCORD_BOT_TOKEN") else "channel"

    from .plan_analysis_pages_v1 import confirmed_publication

    @cache
    def source_for(plan_id):
        # Look up the exact confirmed page when a new or corrected payload uses
        # it. An idle tick has no reason to reopen pages for the export history.
        raw = sources[plan_id]
        publication = confirmed_publication(store, raw)
        return {**raw, "analysis_publication": publication} if publication else raw

    def payload(row, kind):
        raw = source_for(row["plan_id"])
        plan = card_plan(raw)
        item = {"schema_version": posts.SCHEMA, "format": FORMAT, "key": row["key"],
                "plan_id": row["plan_id"], "symbol": row["symbol"], "state": row["to"], "kind": kind,
                "at_utc": row["at_utc"], "levels": plan, "short_id": plan["short_id"],
                "instrument_title": posts._instrument_title(row["symbol"], plan),
                "price_basis": plan.get("price_basis"), "record_line": records,
                "registered_at_utc": plan.get("registered_at_utc") or row["at_utc"],
                "time_exit_utc": plan.get("time_exit_utc"), "entry_deadline_utc": plan.get("entry_deadline_utc"),
                "source_content_hash": export["status"].get("content_hash"),
                "source_contract_version": version,
                "source_plan_hash": raw.get("registration_hash"), "reasons": [],
                "discord_delivery": discord_delivery, "analysis_distribution_version": 1}
        if now >= NO_TARGET_EFFECTIVE:
            # Jim, 23 Nov 2026 about 05:30 GMT+7: "Keep targets off." Decision 40 stands for every new row.
            item["target_policy"] = NO_TARGET_POLICY
            item["scenario_voice"] = voice.CONTRACT
        if kind != "setup" and row["plan_id"] in cards and discord_delivery == "channel":
            item["discord_delivery"] = cards[row["plan_id"]].get("discord_delivery", "bot_thread")
        if kind == "setup" and (now - posts._utc(row["at_utc"])).total_seconds() > window_minutes * 60:
            item["delayed_at_utc"] = now.isoformat().replace("+00:00", "Z")
        analysis, cause = analysis_publication(raw)
        item.update(analysis_publication=analysis, analysis_first_cause=cause)
        from .plan_reader_copy_v1 import EFFECTIVE as READER_EFFECTIVE
        if now >= READER_EFFECTIVE:
            from .plan_reader_copy_v1 import LEVEL_EFFECTIVE, thread_terms
            item.update(reader_contract="CC466_V1", source_plan=raw,
                        source_plan_registration=raw.get("registration_hash"),
                        state_alert_contract="CC543_V1", state_alert_source_sha256=_hash(raw))
            if now >= LINKEDIN_PLAN_LINK_EFFECTIVE:
                item["analysis_linkedin_page_required"] = True
            if kind == "setup":
                item["x_analysis_thread"] = True
            if all(plan.get(key) is not None for key in ("zone_low", "zone_high", "invalidation_level", "direction")):
                if now >= LEVEL_EFFECTIVE:
                    item["level_contract"] = CURRENT_LEVEL_CONTRACT
                terms = thread_terms(raw, level_contract=item.get("level_contract"))
                item.update(thread_contract=THREAD_CONTRACT, instrument_title=terms["market"],
                            entry_deadline_utc=terms["entry_deadline_utc"], time_exit_utc=terms["time_exit_utc"])
        return item

    groups = {}
    profile_link = None
    for pid, row in latest.items():
        if pid in cards or current_states.get(pid) not in posts.ACTIVE or row.get("superseded_by_fill"):
            continue
        raw = sources[pid]
        until = card_plan(raw).get("time_exit_utc")
        if (not until or now >= posts._utc(until)
                or not 0 <= (now - posts._utc(row["at_utc"])).total_seconds() <= posts.LATE_STATE_HOURS * 3600):
            if queue_clock is not None:
                queue_clock.refuse(row, "PLAN_SETUP_OUTSIDE_QUEUE_WINDOW")
            continue
        item = payload(row, "setup")
        if any(item["levels"].get(k) is None for k in ("zone_low", "zone_high", "invalidation_level", "direction")):
            skipped.append({"key": row["key"], "cause": "PLAN_CARD_CONDITIONAL_LEVELS_MISSING"})
            continue
        # A producer run id groups its calls across repeated minute invocations.
        # Older exports still work: the current consumer run owns their group.
        run = raw.get("run_id") or export["status"]["generated_at_utc"]
        run_key = "plan-run-post-" + _hash(run)[:32]
        if item.get("reader_contract"):
            item["run_key"] = run_key
        else:
            item.update(parent_key=run_key, run_key=run_key)
        groups.setdefault(run_key, []).append(item)

    for run_key, members in groups.items():
        for index, item in enumerate(members):
            item["carousel_index"] = index
            source = _reason_source(sources[item["plan_id"]])
            proposed = source_reasons(sources[item["plan_id"]])
            item["reasons"] = checked_reasons(proposed, source)
            item["reasons_cause"] = None if item["reasons"] else "PUBLIC_REASONS_NOT_SUPPLIED_OR_NUMBER_MISMATCH"
            item.update(compose(item))
        if run_key not in prior and not all(m.get("reader_contract") for m in members):
            if profile_link is None:
                profile_link = ({"verified": False, "cause": "INSTAGRAM_PROFILE_ANALYSIS_LINK_NOT_VERIFIED"}
                                if instagram_profile_reader is None else instagram_profile_reader())
            run = {"schema_version": posts.SCHEMA, "format": FORMAT, "key": run_key, "kind": "run",
                   "symbol": "MULTI", "plan_id": run_key, "state": "RUN", "at_utc": min(m["at_utc"] for m in members),
                   "card_keys": [m["key"] for m in members], "source_content_hash": export["status"].get("content_hash"),
                   "source_contract_version": version, "analysis_distribution_version": 1,
                   "instagram_profile_link_verified": profile_link.get("verified") is True,
                   "instagram_profile_link_cause": profile_link.get("cause"),
                   "analysis_publications": [{"title": m["instrument_title"], **m["analysis_publication"]}
                                             for m in members if m.get("analysis_publication")]}
            run.update(compose(run))
            payloads.append(run)
        payloads.extend(members)
        cards.update({m["plan_id"]: m for m in members})

    confirmed_fills = {json.loads(r["payload"]).get("plan_id"): r["message_id"] for r in existing_rows
                      if json.loads(r["payload"]).get("state") in {"TRIGGERED", "FILLED"}
                      and r["status"] in {"PUBLISHING", "PUBLISHED"}}
    pause = jim_pause_window()
    for row in sorted(source_rows + outcomes, key=lambda r: posts._utc(r["at_utc"])):
        pid = row["plan_id"]
        if queue_clock is not None and pid in sources and row["to"] == "WAITING":
            if latest[pid]["key"] != row["key"] or current_states.get(pid) not in posts.ACTIVE:
                queue_clock.refuse(row, "PLAN_SETUP_SUPERSEDED")
            elif pid in cards and cards[pid]["key"] != row["key"]:
                queue_clock.refuse(row, "PLAN_SETUP_ALREADY_REPRESENTED", replacement_key=cards[pid]["key"])
        if pid not in sources or row["to"] == "WAITING" or (row["to"] in TERMINAL and pid in ended_plans):
            continue
        if row["key"] in prior:
            if row["to"] == "RESULT" and not dry_run:
                _refresh_unissued_no_entry_result(store, prior[row["key"]], row, source_for)
            already.append(row["key"])
            continue
        if row["to"] == "RESULT" and inside_jim_pause(row["at_utc"], now, pause):
            skipped.append({"key": row["key"], "cause": "JIM_PAUSE_RESULT_SHOWN_IN_SCORECARD"})
            continue
        if row["to"] in posts.ACTIVE and current_states.get(pid) == "CLOSED":
            skipped.append({"key": row["key"], "cause": "POSITION_CLOSED_BEFORE_FILL_ANNOUNCEMENT"})
            continue
        if row["to"] in {"TRIGGERED", "FILLED"} and pid in confirmed_fills:
            skipped.append({"key": row["key"], "cause": "FILL_CONFIRMATION_ALREADY_PUBLISHED_OR_PENDING",
                            "prior_key": confirmed_fills[pid]})
            continue
        card = cards.get(pid)
        if not card:
            skipped.append({"key": row["key"], "cause": "PLAN_NEVER_ANNOUNCED"})
            continue
        if row["key"] == card["key"] or row.get("superseded_by_fill"):
            continue
        kind = "result" if row["to"] == "RESULT" else "update"
        if kind == "result" and card["key"] not in announced_cards:
            skipped.append({"key": row["key"], "cause": "PLAN_NEVER_ANNOUNCED"})
            continue
        item = payload(row, kind)
        if kind == "result":
            item.update({k: v for k, v in row.items() if k not in {"key", "plan_id", "symbol", "to", "at_utc", "kind"}})
            # A dated result (a correction, or one queued at a relaunch) counts its 24-hour attempt limit from now.
            item["result_queued_at_utc"] = now.isoformat().replace("+00:00", "Z")
        item.update(parent_key=card["key"], card_key=card["key"], run_key=card.get("run_key"))
        # Later posts preserve the exact card's public identity, rather than a
        # newly supplied alias or revised short id.
        item["short_id"] = card.get("short_id", item["short_id"])
        if card.get("format") == FORMAT:
            for field in ("levels", "instrument_title", "registered_at_utc"):
                item[field] = card.get(field)
            if kind != "result" or card.get("price_basis") is not None:
                item["price_basis"] = card.get("price_basis")
        if card.get("thread_contract") == THREAD_CONTRACT:
            for field in ("source_plan", "source_plan_registration", "state_alert_source_sha256",
                          "entry_deadline_utc", "time_exit_utc", "thread_contract"):
                item[field] = card[field]
            if card.get("level_contract") and not item.get("level_contract"):
                item["level_contract"] = card["level_contract"]
            if kind == "result":
                # Keep the original thread's levels while admitting the later
                # exact public outcome, including its explicitly exported R.
                outcome_source = source_for(pid)
                item.update(outcome_source_plan=outcome_source, outcome_source_sha256=_hash(outcome_source),
                            result_copy_version=2)
                if now >= RESULT_FRAME_EFFECTIVE:
                    item["result_frame"] = result_frame(item)
        item.update(compose(item))
        payloads.append(item)

    queued, rendered = [], []
    render_items = []
    if render_all:
        # Render the frozen cards too, without altering the queue's duplicate,
        # parent or fill decisions. A preview must never invent a new setup
        # for an already-announced plan whose latest transition is a fill.
        retained = [json.loads(row["payload"]) for row in existing_rows]
        retained = [row for row in retained if row.get("format") == FORMAT]
        card_keys = {row["key"] for row in retained if row.get("plan_id") in sources}
        render_items = [row for row in retained if row["key"] in card_keys or
                        (row.get("kind") == "run" and card_keys.intersection(row.get("card_keys") or []))]
    items = {item["key"]: item for item in [*render_items, *payloads]}
    for item in items.values():
        if item["key"] not in prior and item.get("state_alert_contract"):
            from .measured_odds_series_v1 import confirmed_method_page
            from .plan_reader_copy_v1 import plan_layer_candidates
            from .plan_reader_editorial_v1 import prepare_plan_layers

            plan = item["source_plan"]
            original = cards.get(item["plan_id"]) or {}
            scenario_voice = item.get("scenario_voice") == voice.CONTRACT
            if (original.get("analysis_copy_contract") == NINE_LAYER_COPY and original.get("source_plan") == plan
                    and original.get("scenario_voice") == item.get("scenario_voice")):
                quotes = original["analysis_layer_quotes"]
            else:
                folder = (Path(analysis_copy_root) / plan["plan_id"]
                          if analysis_copy_root is not None and not dry_run else None)
                quotes = prepare_plan_layers(plan, output_dir=folder, contract=NINE_LAYER_COPY,
                                            scenario_voice=scenario_voice)
            confirmed = confirmed_publication(store, plan) or {}
            item.update(analysis_copy_contract=NINE_LAYER_COPY, analysis_layer_quotes=quotes,
                        analysis_layer_gaps=plan_layer_candidates(plan, scenario_voice=scenario_voice)[1],
                        analysis_link=confirmed.get("canonical_url"))
            if item["kind"] == "setup":
                method = confirmed_method_page(store)
                if method:
                    item["method_page_reference"] = method
            item.update(compose(item))
        if render_all:
            if item.get("reader_contract") and not item.get("reader_fields") and not item.get("state_alert_contract"):
                rendered.append({"key":item["key"],"kind":item["kind"],"status":"EDITORIAL_INPUT_REQUIRED",
                    "cause":"CC466_SOURCED_FIELDS_NOT_PREPARED","destinations":{},"text":""})
                continue
            try:
                item = {**item, **compose(item)}
                # Use the publisher's complete-level layout and reserve space for chart credit.
                charted_thread = item.get("thread_contract") == THREAD_CONTRACT
                copies = destination_payloads(item, card_id="dry-run-" + item["key"],
                                              chart_credit=charted_thread, complete_levels=charted_thread)
            except posts.PlanPostError as exc:
                return {"status": "RENDER_FAILED", "cause": str(exc),
                        "failed_field": "posts." + item["key"] + ".destinations",
                        "contract_version": version}
            rendered.append({"key": item["key"], "kind": item["kind"], "text": item["text"],
                             "destinations": copies, **({"analysis_layer_gaps": item["analysis_layer_gaps"]}
                             if "analysis_layer_gaps" in item else {})})
        if item["key"] in prior:
            already.append(item["key"])
            continue
        if not dry_run:
            store.create_work_item(story_id=posts.WORK_ITEM_ID, title="Plan status posts (decision 79)",
                                   target_surface="MULTI_PLATFORM", work_item_id=posts.WORK_ITEM_ID)
            store.register_outbox_message(message_id=item["key"], work_item_id=posts.WORK_ITEM_ID,
                destination=posts.DESTINATION, payload=json.dumps(item, sort_keys=True, ensure_ascii=False), status=posts.READY)
        queued.append({k: item[k] for k in ("key", "symbol", "state", "kind", "at_utc", "text", "analysis_layer_gaps",
                                           "scenario_voice_findings")
                       if k in item})
    from .plan_reader_editorial_v1 import active_page_plan_ids

    return {"status": "OK", "dry_run": dry_run, "format": FORMAT, **freshness,
            "quarantined_rows": quarantined,
            "contract_version": version, "source_content_hash": export["status"].get("content_hash"),
            **({"rendered_posts": rendered, "rendered_count": len(rendered)} if render_all else {}),
            "max_export_age_minutes": posts.EXPORT_MAX_AGE_MINUTES, "transitions_read": len(source_rows),
            "latest_states": current_states, "active_page_plan_ids": active_page_plan_ids(export, now), "active_recoveries": {},
            "would_queue" if dry_run else "queued": queued, "already_queued": already, "not_posted": skipped}


def _dispatch(store, key, destination):
    return store.get_platform_dispatch(_dispatch_ids(key, destination)["dispatch_id"])


def _dispatch_ids(key, destination):
    from .publication_coordinator_v1 import DurablePublicationCoordinator
    plan_hash = hashlib.sha256(("plan-status-post:" + key).encode()).hexdigest()
    return DurablePublicationCoordinator._ids(key, plan_hash, destination)


def _reference(store, key, destination):
    row = _dispatch(store, key, destination)
    if row and row["status"] == "DISPATCH_CONFIRMED" and row.get("public_object_id"):
        return {k: row.get(k) for k in ("public_object_id", "public_object_url", "dispatch_id")}
    return None


def _discord_channel_update(row):
    return (row.get("state_alert_contract") == "CC543_V1" and row.get("parent_key")
            and not row.get("correction_reply_contract")
            and (row["kind"] == "result"
                 or row["kind"] == "update" and row["state"] in {"FILLED", "TRIGGERED"}))


def _destination_dispatches(store, row, destination, root):
    key = row["key"]
    copies = [(key, _dispatch(store, key, destination) or {})]
    discord_update = destination == "discord" and _discord_channel_update(row)
    layer_copy = row.get("analysis_copy_contract") == NINE_LAYER_COPY
    context = {}
    if root is not None and (discord_update or layer_copy):
        context_path = Path(root) / key / "run_context_v1.json"
        if context_path.is_file():
            context = json.loads(context_path.read_bytes())
    if discord_update:
        channel_key = f"{key}-part-{DISCORD_CHANNEL_PART}"
        channel = _dispatch(store, channel_key, destination)
        parent = (context.get("status_post_parents") or {}).get("discord") or {}
        if channel or parent.get("channel_reply"):
            copies.append((channel_key, channel or {}))
    if layer_copy and copies[0][1].get("status") == "DISPATCH_CONFIRMED":
        count = (context.get("status_post_layer_reply_counts") or {}).get(destination, 0)
        for part in range(ANALYSIS_FIRST_PART, ANALYSIS_FIRST_PART + count):
            reply_key = f"{key}-part-{part}"
            copies.append((reply_key, _dispatch(store, reply_key, destination) or {}))
    return copies


def _skipped_images(root, row):
    """Destination-local image failure, retained in the existing post artifact."""
    if root is None:
        return []
    keys = (row["key"],) if row.get("state_alert_contract") else (row["key"], row.get("parent_key"))
    for key in keys:
        if not key:
            continue
        path = Path(root) / key / "run_context_v1.json"
        if path.is_file():
            skipped = json.loads(path.read_bytes()).get("status_post_skipped_destinations") or []
            if skipped:
                return skipped
    return []


def _settlement_id(key, destination):
    return "plan-post-settled-" + hashlib.sha256((key + "|" + destination).encode()).hexdigest()[:32]


def _post_destinations(row):
    return destinations_for(row) if row.get("format") == FORMAT else posts.POST_DESTINATIONS


def settled_destinations(store, row):
    """CC-515: destination closures in the existing incident audit, not send evidence."""
    if not hasattr(store, "get_read_only_connection"):
        return {}
    with store.get_read_only_connection() as conn:
        return read_settled_destinations(conn, row)


def read_settled_destinations(conn, row):
    ids = {_settlement_id(row["key"], d): d for d in _post_destinations(row)}
    records = conn.execute("SELECT incident_id, description FROM incidents WHERE incident_id IN ("
        + ",".join("?" for _ in ids) + ")", tuple(ids)).fetchall()
    details = {ids[r["incident_id"]]: json.loads(r["description"]) for r in records}
    if row.get("state_alert_contract"):
        # The previous minute consumer closed some current copies solely
        # because the parent was unavailable. Their own dispatch never began.
        return {d: v for d, v in details.items()
                if not (v["cause"].startswith("CARD_PARENT_") and not v.get("dispatch_id"))}
    return details


def settle_pending(store, outbox, row, *, now, root=None, image_cause=None):
    """Close dead destination work; retain exact dispatch/claim/object truth.

    A late UNKNOWN_WRITE remains UNKNOWN_WRITE, available to explicit readback.
    Settling its minute-work obligation never asserts an absent public write.
    """
    settled = settled_destinations(store, row)
    age = posts._age_minutes(row, now)
    if row.get("kind") == "result" and row.get("result_queued_at_utc"):
        # Audit of 23 Nov 2026: a dated result (a correction, or a result queued at a relaunch) reached
        # Telegram and Discord in the immediate pass, then its other destinations were closed in the same
        # minute because its ending was older than 24 hours. The attempt's age starts when it was queued.
        age = min(age, (now - posts._utc(row["result_queued_at_utc"])).total_seconds() / 60)
    # Dated results remain owed (the publication freshness contract). CC-515
    # still closes an attempted PUBLISHING row after 24 hours and dead parents.
    late = age > posts.LATE_STATE_HOURS * 60 and not (row.get("kind") == "result" and outbox["status"] == posts.READY)
    confirmed = set()
    resumable = set(_ready_destinations(store, row, root=root)) if not late and row.get("format") == FORMAT else set()
    parent_message = store.get_outbox_message(row["parent_key"]) if row.get("parent_key") else None
    parent_row = json.loads(parent_message["payload"]) if parent_message else {}
    parent_late = bool(parent_row.get("at_utc") and posts._age_minutes(parent_row, now) > posts.LATE_STATE_HOURS * 60)
    for destination in _post_destinations(row):
        copies = _destination_dispatches(store, row, destination, root)
        dispatch = copies[0][1]
        if all(copy.get("status") == "DISPATCH_CONFIRMED" for _, copy in copies):
            confirmed.add(destination)
            continue
        if dispatch.get("status") == "DISPATCH_CONFIRMED":
            dispatch = copies[-1][1]
        if destination in settled:
            continue
        cause = image_cause if not dispatch else None
        # A possibly-sent child keeps its readback until the late-state limit.
        unstarted = not dispatch or dispatch.get("status") in SETTLED_DISPATCHES
        parent_needed = bool(row.get("parent_key") and not row.get("state_alert_contract") and not
            (destination == "discord" and row.get("discord_delivery") == "channel"))
        if parent_needed and not _reference(store, row["parent_key"], destination):
            parent = _dispatch(store, row["parent_key"], destination) or {}
            if (unstarted and parent.get("status") in SETTLED_DISPATCHES - {"DISPATCH_CONFIRMED"}
                    and not parent.get("public_object_id") and not parent.get("public_object_url")):
                cause = "CARD_PARENT_" + parent["status"]
            elif late or (parent_late and unstarted):
                cause = "CARD_PARENT_NOT_CONFIRMED"
        if cause is None and late:
            cause = "PUBLISHING_OLDER_THAN_24_HOURS" if outbox["status"] == "PUBLISHING" else "LATE_STATE_LIMIT_24_HOURS"
        if cause is None and destination not in resumable:
            failed = next((copy for _, copy in copies
                           if copy.get("status") in SETTLED_DISPATCHES - {"DISPATCH_CONFIRMED"}
                           and not copy.get("public_object_id") and not copy.get("public_object_url")), None)
            if failed:
                dispatch = failed
                cause = "DESTINATION_" + failed["status"]
        if cause is None:
            continue
        detail = {"key": row["key"], "destination": destination, "cause": cause,
            "parent_key": row.get("parent_key"), "source_at_utc": row["at_utc"],
            "late_state_hours": posts.LATE_STATE_HOURS,
            "dispatch_id": (dispatch or {}).get("dispatch_id"),
            "dispatch_status": (dispatch or {}).get("status"),
            "public_object_id": (dispatch or {}).get("public_object_id"),
            "public_object_url": (dispatch or {}).get("public_object_url"),
            "public_write_performed": False, "automatic_work_closed": True}
        store.register_incident(incident_id=_settlement_id(row["key"], destination),
            work_item_id=outbox.get("work_item_id"), severity="RECOVERY_AUDIT",
            description=json.dumps(detail, sort_keys=True))
        settled[destination] = detail
        for copy_key, copy in copies:
            if copy.get("status") != "DISPATCH_CONFIRMED":
                ids = _dispatch_ids(copy_key, destination)
                if store.get_outbox_message(ids["message_id"]):
                    store.set_outbox_status(ids["message_id"], SETTLED_COPY)
    skipped = {d["destination"]: d["cause"] for d in _skipped_images(root, row)}
    if set(_post_destinations(row)) <= confirmed | set(settled) | set(skipped):
        causes = {**skipped, **{d: v["cause"] for d, v in settled.items()}}
        status = SETTLED_POST if settled or (row.get("state_alert_contract") and skipped) else "PUBLISHED"
        store.set_outbox_status(row["key"], status)
        return {"key": row["key"], "status": status,
            "cause": next(iter(causes.values()), "ALL_DESTINATIONS_CONFIRMED"),
            "per_destination": {d: "DISPATCH_CONFIRMED" if d in confirmed else SETTLED_POST
                for d in _post_destinations(row)},
            "destination_causes": causes}
    return None


def _linkedin_plan_url(store, row):
    from .plan_analysis_pages_v1 import confirmed_publication

    return (confirmed_publication(store, row["source_plan"]) or {}).get("canonical_url")


def _ready_destinations(store, row, root=None):
    """A settled/parent-waiting copy cannot starve unrelated cards of a slot."""
    ready = []
    skipped = {s["destination"] for s in _skipped_images(root, row)}
    if row.get("analysis_linkedin_page_required") and not _linkedin_plan_url(store, row):
        skipped.update(d for d in LINKEDIN_DESTINATIONS if not _dispatch(store, row["key"], d))
    settled = settled_destinations(store, row)
    for destination in destinations_for(row):
        if destination in skipped or destination in settled:
            continue
        copies = _destination_dispatches(store, row, destination, root)
        dispatch = copies[0][1]
        channel_suffix = f"-part-{DISCORD_CHANNEL_PART}"
        channel = [copy for key, copy in copies[1:] if key.endswith(channel_suffix)]
        layers = [copy for key, copy in copies[1:] if not key.endswith(channel_suffix)]
        next_layer = next((copy for copy in layers if copy.get("status") != "DISPATCH_CONFIRMED"), None)
        if (any(copy.get("status") not in SETTLED_DISPATCHES for copy in channel)
                or next_layer is not None and next_layer.get("status") not in SETTLED_DISPATCHES):
            ready.append(destination)
            continue
        if dispatch and dispatch.get("status") in SETTLED_DISPATCHES:
            if destination in {"x", "substack_notes"} and dispatch["status"] == "DEFINITE_NO_WRITE":
                from .neo_endpoint_executor_v1 import repaired_prewrite_request
                if repaired_prewrite_request(store, dispatch):
                    ready.append(destination)
                    continue
            # Decision 112's exact former X policy no-write remains resumable.
            # Other definite no-writes retain their original terminal cause.
            if (destination == "x" and dispatch["status"] == "DEFINITE_NO_WRITE"
                    and not dispatch.get("public_object_id") and not dispatch.get("public_object_url")):
                reconciliation_id = "reconciliation_" + str(dispatch.get("dispatch_id") or "").removeprefix("dispatch_")
                if any(r["reconciliation_id"] == reconciliation_id and r["status"] == "X_NON_API_AUTOMATION_PROHIBITED"
                        for r in store.get_reconciliations_for_work_item(row["key"])):
                    ready.append(destination)
            continue
        if (dispatch or not row.get("parent_key") or row.get("state_alert_contract")
                or _reference(store, row["parent_key"], destination)
                or (destination == "discord" and row.get("discord_delivery") == "channel")):
            ready.append(destination)
    return ready


def _can_retire_unstarted(store, row, root=None):
    """Keep confirmed and possibly sent copies with their exact recovery owner."""
    for destination in destinations_for(row):
        for _, dispatch in _destination_dispatches(store, row, destination, root):
            if dispatch and (dispatch.get("public_object_id") or dispatch.get("public_object_url")
                    or dispatch.get("status") not in SETTLED_DISPATCHES - {"DISPATCH_CONFIRMED"}):
                return False
    return True


def postable_run_members(store, row, destination, *, now=None, latest_states=None, root=None, current=False):
    """Do not announce an empty run, including a destination's definite refusals."""
    now = now or datetime.now(timezone.utc)
    members = []
    for key in row.get("card_keys") or []:
        held = store.get_outbox_message(key)
        if not held or held["status"] not in {posts.READY, "PUBLISHING", "PUBLISHED"}:
            continue
        child = posts._row_payload(store, key)
        states = latest_states
        if current:
            observed = posts.current_public_plan(child["plan_id"], now=now,
                registration_hash=child.get("source_plan_registration") or child.get("source_plan_hash"))
            states = {child["plan_id"]: observed.get("status")}
        if (destination not in destinations_for(child)
                or posts.publication_refusal(store, child, now=now, latest_states=states)
                or destination in settled_destinations(store, child)
                or destination in {s["destination"] for s in _skipped_images(root, child)}):
            continue
        dispatch = _dispatch(store, key, destination) or {}
        if dispatch.get("status") in SETTLED_DISPATCHES - {"DISPATCH_CONFIRMED"}:
            continue
        members.append(child)
    return members


def _discord_message_location(reference):
    match = re.fullmatch(r"https://discord\.com/channels/([0-9]+)/([0-9]+)/([0-9]+)",
                         str((reference or {}).get("public_object_url") or ""))
    if match and match[3] == str(reference["public_object_id"]):
        return match.groups()
    return None


def _discord_channel_anchor(card, starter):
    from .destination_transport_registry_v1 import registration_for_destination

    original = _discord_message_location(card)
    root = _discord_message_location(starter)
    if not original or not root:
        return None
    guild, channel, message = root
    if channel != registration_for_destination("discord").expected_stable_id:
        return None
    # Older cards can live in a shared run thread. Reply to that thread's
    # channel starter and link to the exact card inside it.
    if original == root:
        link = f"https://discord.com/channels/{guild}/{message}"
    elif original[:2] == (guild, message):
        link = card["public_object_url"]
    else:
        return None
    return {"reply_to_id": message, "reply_to_url": starter["public_object_url"], "thread_url": link}


def _discord_thread_root(store, row, card):
    parent_key, run_key = row["parent_key"], row.get("run_key")
    if run_key and run_key != parent_key:
        run = _reference(store, run_key, "discord")
        if not row.get("state_alert_contract") or _discord_channel_anchor(card, run):
            return run
    return card


def _parents(store, row, destinations, previous):
    parents = dict(previous or {})
    deferred = []
    settled = settled_destinations(store, row)
    for destination in destinations:
        if destination in settled:
            parents.pop(destination, None)
            continue
        if (destination in LINKEDIN_DESTINATIONS and row.get("analysis_linkedin_page_required")
                and not _dispatch(store, row["key"], destination) and not _linkedin_plan_url(store, row)):
            deferred.append({"destination": destination, "cause": "CC684_LINKEDIN_PLAN_PAGE_NOT_CONFIRMED"})
            continue
        if destination == "discord" and row.get("discord_delivery") == "channel":
            # A channel post needs no run/thread parent. Its route was frozen
            # when this new card entered the existing outbox.
            parents[destination] = {"delivery_mode": "channel"}
            continue
        if destination in parents or not row.get("parent_key"):
            continue
        ref = _reference(store, row["parent_key"], destination)
        if not ref:
            if row.get("state_alert_contract") and not _dispatch(store, row["key"], destination):
                parents[destination] = {"delivery_mode": "standalone"}
                continue
            parent_dispatch = _dispatch(store, row["parent_key"], destination) or {}
            cause = ("CARD_PARENT_" + parent_dispatch["status"] if
                parent_dispatch.get("status") in SETTLED_DISPATCHES else "CARD_PARENT_NOT_CONFIRMED")
            deferred.append({"destination": destination, "cause": cause,
                             "parent_key": row["parent_key"]})
            continue
        parent = {**ref, "parent_key": row["parent_key"]}
        if destination == "discord":
            root = _discord_thread_root(store, row, ref)
            if not root:
                deferred.append({"destination": destination, "cause": "RUN_PARENT_NOT_CONFIRMED"})
                continue
            parent["thread_parent_id"] = root["public_object_id"]
            parent["thread_parent_url"] = root.get("public_object_url")
            # An issued thread-only copy stays byte-for-byte replayable. Stage
            # the second intent only when preparing a fresh Discord copy.
            if _discord_channel_update(row) and not store.get_outbox_message(
                    _dispatch_ids(row["key"], destination)["message_id"]):
                anchor = _discord_channel_anchor(ref, root)
                if anchor:
                    parent["channel_reply"] = anchor
        parents[destination] = parent
    return parents, deferred


def destination_payloads(row, *, card_id, parents=None, carousel=None, chart_credit=False, complete_levels=False,
                         portrait_id=None, x_analysis=None, destinations=None, discord_channel_reply=None,
                         repeat_threads_notices=False, facebook_reply_images=False):
    if row.get("state_alert_contract") == "CC543_V1":
        from .plan_state_alerts_v1 import payloads as alert_payloads
        result = alert_payloads(row, card_id=card_id, parents=parents, carousel=carousel,
            chart_credit=chart_credit, complete_levels=complete_levels, portrait_id=portrait_id,
            repeat_threads_notices=repeat_threads_notices, facebook_reply_images=facebook_reply_images)
        if row.get("x_analysis_thread") and x_analysis:
            from .plan_reader_copy_v1 import payloads
            result.update(payloads({**row, **x_analysis}, card_id, chart_credit=chart_credit, destinations=("x",)))
            result["x"]["alt_text"] = x_analysis["reader_fields"]["alt_text"]["text"]
        return result
    if row.get("reader_contract") == "CC466_V1":
        from .plan_reader_copy_v1 import payloads
        return payloads(row, card_id, chart_credit=chart_credit, parents=parents, portrait_id=portrait_id)
    result = {}
    linkedin_analysis_url = row.get("linkedin_analysis_url")
    limits = {"telegram": 1024, "discord": 2000, "threads": 500, "x": 280,
              "facebook_page": 60000, "instagram_business": 2200, "substack_notes": 10000,
              "linkedin": 3000, "linkedin_company": 3000}
    if (row.get("analysis_publication") or {}).get("canonical_url") or row.get("analysis_publications"):
        # Decision 113: use Telegram's text allowance with the hosted card as
        # its explicit large preview, rather than the photo caption allowance.
        limits["telegram"] = 4096
    if row.get("analysis_copy_contract"):
        limits["telegram"] = 4096
    reply_limits = limits.copy()
    credit = "\n\n" + posts.CHART_CREDIT if chart_credit else ""
    limits = {d: n - len(credit) for d, n in limits.items()}
    thread_link = ""
    if discord_channel_reply:
        thread_link = f"\n\nPlan thread: <{discord_channel_reply['thread_url']}>"
        limits["discord"] -= len(thread_link)
    layers = None
    cases = 0
    if row.get("analysis_copy_contract") == NINE_LAYER_COPY:
        from .plan_state_alerts_v1 import analysis_lines, nine_layer_parts, scenario_case_count

        layers = analysis_lines(row)
        cases = scenario_case_count(row, layers)
        if row["kind"] == "result" and row.get("level_contract") == CURRENT_LEVEL_CONTRACT:
            # CC-682: the result leads the body (plan_state_alerts_v1.compose), so it opens the first object too.
            layers = [row["text"].splitlines()[0], *layers]
    for destination in destinations if destinations is not None else destinations_for(row):
        text = row["text"]
        if destination in LINKEDIN_DESTINATIONS and linkedin_analysis_url and not row.get("analysis_link"):
            body, notices = posts._split(text)
            text = body + "\nFull analysis: " + linkedin_analysis_url + "\n\n" + notices
        layer_parts = None
        if layers is not None:
            body, notices = posts._split(text)
            layer_parts = nine_layer_parts(layers, body, notices, destination=destination,
                                           limit=limits[destination], reply_limit=reply_limits[destination],
                                           cases=cases, whole_lines=row.get("scenario_voice") == voice.CONTRACT)
        if destination == "threads" and row["kind"] != "run" and (complete_levels or row.get("analysis_copy_contract")):
            # The image no longer carries the only copy of a level/window.
            # Preserve every supplied line in the platform's existing thread route.
            body, notices = posts._split(text)
            if layer_parts is not None:
                parts = layer_parts
            elif row.get("analysis_copy_contract"):
                from .plan_state_alerts_v1 import analysis_thread_parts
                parts = analysis_thread_parts(row, body, notices, destination=destination, limit=limits[destination])
            elif row.get("thread_contract") == THREAD_CONTRACT and row.get("level_contract") in PHASE_LEVEL_CONTRACTS:
                # CC-682's condition and its two clocks are source-bound
                # sentences. Keep each line whole before the shared notices
                # and chart-credit suffix are added to the first reply.
                # CC-729: a package prepared after it carries the notices once, on its first part.
                room = limits[destination] - len(notices) - 2
                parts, current = [], []
                for line in body.splitlines():
                    if current and len("\n".join([*current, line])) > room:
                        parts.append("\n".join(current) + ("\n\n" + notices if repeat_threads_notices or not parts else ""))
                        current = []
                    if len(line) > room:
                        if current:
                            parts.append("\n".join(current) + ("\n\n" + notices if repeat_threads_notices or not parts else ""))
                            current = []
                        parts.extend(posts._text_parts(line, notices if repeat_threads_notices or not parts else "",
                                                        limits[destination], repeat_notices=repeat_threads_notices))
                    else:
                        current.append(line)
                if current:
                    parts.append("\n".join(current) + ("\n\n" + notices if repeat_threads_notices or not parts else ""))
            else:
                parts = posts._text_parts(body, NOTICES, limits[destination], lines=True,
                                          repeat_notices=repeat_threads_notices)
            payload = {"destination": destination, "text": parts[0], "root_text": parts[0],
                       "full_text": "\n\n".join(parts), "reply_texts": parts[1:], "media_asset_ids": [card_id]}
            ref = (parents or {}).get(destination)
            if ref:
                payload.update(reply_to_id=str(ref["public_object_id"]), reply_to_url=ref.get("public_object_url"))
            result[destination] = payload
            continue
        if destination == "threads" and row["kind"] == "run" and row.get("analysis_publications"):
            root = row["lead"] + "\n\n" + NOTICES
            reply_footer = "\n\n" + NOTICES if repeat_threads_notices else ""
            replies = [_run_summary({"analysis_publications": [analysis]}, "",
                                    500 - len(reply_footer)).lstrip() + reply_footer
                       for analysis in row["analysis_publications"]]
            for index, part in enumerate((root, *replies)):
                check_publication_copy({"body": part}, conditional_calls=[],
                                       require_notice=index == 0 or repeat_threads_notices)
                if len(part) > 500:
                    raise posts.PlanPostError("PLAN_CARD_COPY_TOO_LONG:threads")
            result[destination] = {"destination": destination, "text": root, "root_text": root,
                "reply_texts": replies, "full_text": "\n\n".join([root, *replies]), "media_asset_ids": [card_id]}
            continue
        if row["kind"] == "run" and row.get("analysis_publications") and destination != "x":
            text = _run_summary(row, row["lead"], limits[destination] - len(NOTICES) - 2) + "\n\n" + NOTICES
        if destination == "instagram_business" and row["kind"] == "run" and row.get("analysis_publications"):
            caption = ("Full analysis: link in our profile; each plan's link is in the comments."
                       if row.get("instagram_profile_link_verified") else
                       "Each plan's full-analysis link is in the comments.")
            body = _run_summary(row, row["lead"], limits[destination] - len(NOTICES) - len(caption) - 3)
            text = body + "\n" + caption + "\n\n" + NOTICES
        if destination == "x":
            body, notices = posts._split(text)
            if layer_parts is not None:
                chunks = layer_parts
            elif row.get("analysis_copy_contract"):
                from .plan_state_alerts_v1 import analysis_thread_parts
                chunks = analysis_thread_parts(row, body, notices, destination=destination, limit=limits["x"])
            else:
                chunks = posts._x_pack(body, limits["x"], preserve_lines=True) + [notices]
            if any(posts._x_length(part) > (reply_limits["x"] if layer_parts and index else limits["x"])
                   for index, part in enumerate(chunks)):
                raise posts.PlanPostError("PLAN_CARD_COPY_TOO_LONG:x")
            payload = {"destination": "x", "text": chunks[0], "root_text": chunks[0],
                "full_text": "\n\n".join(chunks), "reply_texts": chunks[1:], "media_asset_ids": [card_id],
                "posts": [{"text": part, "order": i, "role": "root" if i == 0 else "reply",
                    "media_asset_ids": [] if i else [card_id]} for i, part in enumerate(chunks)]}
            ref = (parents or {}).get(destination)
            if ref:
                payload.update(reply_to_id=str(ref["public_object_id"]), reply_to_url=ref.get("public_object_url"))
            result[destination] = payload
            continue
        room = limits[destination] - len(NOTICES) - 2
        body = text.rsplit("\n\n", 1)[0]
        if layer_parts is not None:
            text = layer_parts[0]
        elif len(body) > room:
            # The full card image retains every supplied field. Short copies
            # keep the conditional call, its id and the structured levels first.
            body = row["lead"]
            analysis = row.get("analysis_publication") or {}
            link = "Full analysis: " + analysis["canonical_url"] if analysis.get("canonical_url") else ""
            content_room = room - len(link) - (1 if link else 0)
            for line in row.get("detail_lines") or []:
                if len(body) + len(line) + 1 <= content_room:
                    body += "\n" + line
            sections = [label + ": " + analysis["summary"][key] for key, label in ANALYSIS_SECTIONS
                        if (analysis.get("summary") or {}).get(key)]
            if sections:
                available = content_room - len(body) - len(sections)
                for line in sections:
                    excerpt = posts._excerpt(line, max(0, available // len(sections)))
                    if excerpt:
                        body += "\n" + excerpt
            for line in (row.get("record_line"), *("• " + r for r in row.get("reasons") or [] if not sections)):
                if line and len(body) + len(line) + 1 <= content_room:
                    body += "\n" + line
            if link:
                if len(body) + len(link) + 1 > room:
                    raise posts.PlanPostError("PLAN_CARD_CONDITIONAL_AND_ANALYSIS_LINK_TOO_LONG:" + destination)
                body += "\n" + link
            text = body + "\n\n" + NOTICES
        if len(text) > limits[destination]:
            raise posts.PlanPostError("PLAN_CARD_COPY_TOO_LONG:" + destination)
        if destination == "discord":
            text += thread_link
        check_publication_copy({"body": text}, conditional_calls=row.get("conditional_calls") or [])
        payload = {"destination": destination, "text": text, "full_text": text,
                   "media_asset_ids": [card_id]}
        if layer_parts and len(layer_parts) > 1 and not discord_channel_reply:
            payload["parts"] = [text, *layer_parts[1:]]
            payload["full_text"] = "\n\n".join(payload["parts"])
        if destination == "telegram" and (len(text) + (len(credit) if layer_parts else 0) > 1024):
            payload["telegram_text_with_card_preview"] = True
        if destination == "instagram_business" and carousel:
            payload["media_asset_ids"] = [a["asset_id"] for a in carousel]
            if row["kind"] == "run":
                payload["carousel_images"] = carousel
        ref = (parents or {}).get(destination)
        if destination == "discord" and discord_channel_reply:
            payload.update(discord_channel_reply=True, reply_to_id=discord_channel_reply["reply_to_id"],
                reply_to_url=discord_channel_reply["reply_to_url"],
                discord_thread_name="Calls · " + _clock(row["registered_at_utc"]))
        elif destination == "discord" and row.get("discord_delivery") == "channel":
            payload["discord_channel_post"] = True
        elif ref:
            if destination in {"telegram", "threads"}:
                payload.update(reply_to_id=str(ref["public_object_id"]), reply_to_url=ref.get("public_object_url"))
            elif destination == "discord":
                payload.update(discord_thread_parent_id=str(ref["thread_parent_id"]),
                    discord_thread_name="Calls · " + _clock(row["registered_at_utc"]),
                    **({"reply_to_id": str(ref["public_object_id"])} if row["kind"] != "setup" else {}))
            elif destination == "facebook_page":
                payload.update(reply_to_id=str(ref["public_object_id"]), reply_to_url=ref.get("public_object_url"),
                    own_call_comment=True,
                    comment_card_image=bool(card_id) if facebook_reply_images else row["kind"] == "setup")
            elif destination == "instagram_business":
                if row["kind"] == "setup":
                    payload.update(reuse_run_carousel=True, carousel_index=row.get("carousel_index", 0),
                        carousel_parent_id=str(ref["public_object_id"]), carousel_parent_url=ref.get("public_object_url"))
                else:
                    payload.update(reply_to_id=str(ref["public_object_id"]),
                                   reply_to_url=ref.get("public_object_url"), own_call_comment=True)
            elif destination == "substack_notes":
                payload.update(reply_to_id=str(ref["public_object_id"]), reply_to_url=ref.get("public_object_url"))
        result[destination] = payload
    for destination,payload in result.items():
        if destination == "threads" and portrait_id:
            payload["media_asset_ids"] = [portrait_id]
            if payload.get("posts"):
                payload["posts"][0]["media_asset_ids"] = [portrait_id]
        imageless_facebook_reply = (facebook_reply_images and destination == "facebook_page"
                                    and payload.get("own_call_comment") and not payload.get("comment_card_image"))
        if credit and not imageless_facebook_reply:
            first = payload["text"]
            payload["text"] = first + credit
            payload["full_text"] = payload["text"] + payload["full_text"][len(first):]
            if payload.get("parts"):
                payload["parts"][0] = payload["text"]
            if "root_text" in payload:
                payload["root_text"] += credit
            if payload.get("posts"):
                payload["posts"][0]["text"] += credit
        if not card_id:
            payload["media_asset_ids"] = []
            for part in payload.get("posts") or []:
                part["media_asset_ids"] = []
    return result


def analysis_reply_payloads(store, row, payloads, part):
    """Resolve the overflow under the exact confirmed post, or its owning comment thread."""
    index = part - ANALYSIS_FIRST_PART + 1
    result = {}
    for destination, payload in payloads.items():
        parts = payload.get("parts") or ()
        if index >= len(parts):
            continue
        ref = _reference(store, row["key"], destination)
        if not ref:
            continue
        parent_id, parent_url = str(ref["public_object_id"]), ref["public_object_url"]
        if destination in {"facebook_page", "instagram_business"} and payload.get("own_call_comment"):
            parent_id, parent_url = payload["reply_to_id"], payload["reply_to_url"]
        text = parts[index]
        reply = {"destination": destination, "text": text, "full_text": text, "media_asset_ids": [],
                 "plan_layer_reply": True,
                 "reply_to_id": parent_id, "reply_to_url": parent_url}
        if destination in {"facebook_page", "instagram_business"}:
            reply["own_call_comment"] = True
        elif destination == "discord":
            reply.update(discord_thread_parent_id=payload.get("discord_thread_parent_id", parent_id),
                         discord_thread_name="Calls · " + _clock(row["registered_at_utc"]))
        result[destination] = reply
    return result


def discord_channel_payload(row, *, card_id, parents, chart_credit):
    anchor = ((parents or {}).get("discord") or {}).get("channel_reply")
    if not anchor or not _discord_channel_update(row):
        return {}
    # Both placements use the same frozen state alert and the same chart.
    compiled = {**row, "state_alert_contract": None, "reader_contract": None}
    return destination_payloads(compiled, card_id=card_id, chart_credit=chart_credit,
                                destinations=("discord",), discord_channel_reply=anchor)


def route_payloads(row, *, instagram_chart_credit=None, **kwargs):
    payloads = destination_payloads(row, **kwargs)
    if (instagram_chart_credit is not None and "instagram_business" in payloads
            and instagram_chart_credit != kwargs.get("chart_credit")):
        payloads["instagram_business"] = destination_payloads(
            row, **{**kwargs, "chart_credit": instagram_chart_credit})["instagram_business"]
    return payloads


def _late_chart_parent(store, row, destination, context):
    if destination not in LATE_CHART_DESTINATIONS:
        return None
    dispatch = _dispatch(store, row["key"], destination) or {}
    if (dispatch.get("status") != "DISPATCH_CONFIRMED" or not dispatch.get("public_object_id")
            or (destination in {"x", "substack_notes"} and not dispatch.get("public_object_url"))):
        return None
    issued = store.get_outbox_message(dispatch["message_id"])
    if not issued:
        return None
    native = json.loads(issued["payload"])["native_payload"]
    selected = set(native.get("media_asset_ids") or [])
    if native.get("own_call_comment") and destination == "facebook_page":
        return None  # Graph's image comment route targets a post, not another comment.
    if not any(a["asset_id"] in selected and (a.get("plan_chart_fallback") or
            (a.get("tradingview_snapshot") or {}).get("plain_price_scale_cause"))
            for a in context["media"]["assets"]):
        return None
    parent = {"reply_to_id": str(dispatch["public_object_id"]), "reply_to_url": dispatch.get("public_object_url")}
    if destination == "discord":
        if thread := native.get("discord_thread_parent_id"):
            parent.update(discord_thread_parent_id=thread, discord_thread_name="Plan chart")
        else:
            parent["discord_channel_reply"] = True
    elif destination == "facebook_page":
        parent.update(own_call_comment=True, comment_card_image=True)
    return parent


def late_chart_payloads(store, row, folder, context):
    from . import tradingview_snapshot_v1 as tv

    assets = context["media"]["assets"]
    chart, = assets
    snap = chart["tradingview_snapshot"]
    if (chart.get("plan_overlay") or snap.get("plain_price_scale_cause")
            or tv._utc(snap["captured_at_utc"]) <= posts._utc(row["at_utc"])):
        raise posts.PlanPostError("PLAN_LATE_CHART_CAPTURE_INVALID")
    text = f"Updated chart for {row['instrument_title']}.\n\n{tv.CREDIT}"
    original = json.loads((folder.parent / "run_context_v1.json").read_bytes())
    return {d: {"destination": d, "text": text, "full_text": text,
                "media_asset_ids": [chart["asset_id"]], **parent}
            for d in destinations_for(row)
            if (parent := _late_chart_parent(store, row, d, original))}


def _publish_late_chart(store, row, folder, coordinator_for, *, host, snapshot, snapshot_allowed):
    from . import tradingview_snapshot_v1 as tv
    from .capital_chronicle_latest_report_consumer_v1 import canonical_bytes
    from .destination_transport_registry_v1 import REGISTRY_VERSION, registration_for_destination

    key = row["key"]
    child = f"{key}-part-{LATE_CHART_PART}"
    path = folder / "run_context_v1.json"
    if not path.is_file():
        return None
    original = json.loads(path.read_bytes())
    if not any(a.get("plan_chart_fallback") or (a.get("tradingview_snapshot") or {}).get("plain_price_scale_cause")
               for a in original["media"]["assets"]):
        return None
    chosen = [d for d in destinations_for(row) if _late_chart_parent(store, row, d, original)
              and (_dispatch(store, child, d) or {}).get("status") not in SETTLED_DISPATCHES]
    if not chosen:
        return None
    late = folder / "late-chart"
    context_path = late / "run_context_v1.json"
    if context_path.is_file():
        context = json.loads(context_path.read_bytes())
    else:
        state_path = late / "tradingview_capture_v1.json"
        first_later_attempt = not state_path.is_file()
        chart = tv.late_plan_snapshot(row, folder, late, snapshot=snapshot, snapshot_allowed=snapshot_allowed)
        if not chart:
            if first_later_attempt and state_path.is_file():
                state = json.loads(state_path.read_bytes())
                if state.get("status") == "FAILED":
                    return {"status": "PLAN_LATE_CHART_CAPTURE_FAILED", "cause": state["cause"]}
            return None
        article = {"title": f"{row['instrument_title']} chart update", "body": tv.CREDIT}
        if host is None:
            from .cloudinary_delivery_media_v1 import prepare_cloudinary_delivery_media as host
        delivery = host(work_item_id=child, delivery_only_assets=[chart], existing_manifest=None,
                        article_assets=[], article=article, source_documents=[])
        if delivery.get("status") != "CLOUDINARY_DELIVERY_MEDIA_READY":
            raise posts.PlanPostError("PLAN_LATE_CHART_HOSTING_" + str(delivery.get("status") or "FAILED"))
        (late / "delivery_media_manifest_v1.json").write_bytes(canonical_bytes(delivery["manifest"]))
        context = {"article": article, "media": {"assets": [chart]}, "plan_status_post": key}
        context_path.write_bytes(canonical_bytes(context))
    payloads = late_chart_payloads(store, row, late, context)
    destinations = []
    for destination in chosen:
        registration = registration_for_destination(destination)
        text = payloads[destination]["full_text"]
        destinations.append({"destination": destination, "platform": registration.platform,
            "surface": registration.surface, "transport_type": registration.transport_type,
            "transport_registry_version": REGISTRY_VERSION, "payload": text,
            "payload_hash": hashlib.sha256(text.encode()).hexdigest(), "canonical_url": None,
            "expected_destination_identity": registration.expected_identity})
    plan = {"schema_version": "contentops.publication_plan.v1", "plan_status_post": key,
        "plan_status_part": LATE_CHART_PART, "work_item_id": child,
        "plan_hash": hashlib.sha256(("plan-status-post:" + child).encode()).hexdigest(),
        "story_identity": child, "article_identity": child, "package_identity": child,
        "publication_window": {"window_identity": child}, "output_dir": str(late.resolve()),
        "transport_registry_version": REGISTRY_VERSION, "policy_mode_version": "AUTONOMOUS_DEFAULT:cc399.v1",
        "destinations": destinations}
    return _publish_card_plan(store, row, plan, coordinator_for, parallel=False, immediate=False)


def _confirmed_page_snapshot(store, row, *, ratio="16:9"):
    """Reuse this exact plan's confirmed article chart for its social card."""
    if not row.get("analysis_publication") or not row.get("source_plan"):
        return None
    from . import plan_analysis_pages_v1 as pages
    publication = pages.confirmed_publication(store, row["source_plan"])
    if not publication or publication["canonical_url"] != row["analysis_publication"]["canonical_url"]:
        return None
    held = store.get_outbox_message("plan-analysis-" + row["plan_id"])
    packet = json.loads(held["payload"])
    from .tradingview_snapshot_v1 import validate_snapshot_asset, SYMBOLS
    for asset in packet.get("media_assets") or []:
        source = asset.get("tradingview_snapshot") or {}
        if (source.get("tv_symbol") == SYMBOLS.get(row["symbol"])
                and source.get("capture_ratio", "16:9") == ratio):
            validate_snapshot_asset(asset)
            return source
    return None


def prepare_post(store, key, *, root, host=None, destinations=None,
                 snapshot=None, snapshot_allowed=None, fast_alert=False, **ignored):
    from .capital_chronicle_latest_report_consumer_v1 import canonical_bytes
    from .destination_transport_registry_v1 import REGISTRY_VERSION, registration_for_destination
    from . import tradingview_snapshot_v1 as tv
    row = posts._row_payload(store, key)
    if destinations is None:
        destinations = destinations_for(row)
    refusal = posts.publication_refusal(store, row, now=datetime.now(timezone.utc))
    if refusal:
        raise posts.PlanPostError(refusal[1])
    settled = settled_destinations(store, row)
    destinations = tuple(d for d in destinations if d in destinations_for(row) and d not in settled)
    folder = Path(root) / key
    folder.mkdir(parents=True, exist_ok=True)
    context_path = folder / "run_context_v1.json"
    previous = json.loads(context_path.read_bytes()) if context_path.is_file() else {}
    if row.get("state_alert_contract") == "CC543_V1":
        from .plan_state_alerts_v1 import validate as validate_alert
        validate_alert(row, store=store)
    elif row.get("reader_contract") == "CC466_V1":
        from .plan_reader_editorial_v1 import validate_reader_row
        validate_reader_row(store, row)
    parents, deferred = _parents(store, row, destinations, previous.get("status_post_parents"))
    chosen = [d for d in destinations if not row.get("parent_key") or d in parents]
    linkedin_url = previous.get("status_post_linkedin_analysis_url")
    if set(chosen).intersection(LINKEDIN_DESTINATIONS) and row.get("analysis_linkedin_page_required"):
        linkedin_url = linkedin_url or _linkedin_plan_url(store, row)
        if not linkedin_url:
            chosen = [d for d in chosen if d not in LINKEDIN_DESTINATIONS]
    unpostable = []
    if row["kind"] == "run":
        unpostable = [{"destination": d, "cause": "RUN_HAS_NO_POSTABLE_CALL"} for d in chosen
                     if not postable_run_members(store, row, d, root=root)]
        chosen = [d for d in chosen if postable_run_members(store, row, d, root=root)]
    x_analysis = previous.get("status_post_x_analysis")
    if (row.get("x_analysis_thread") and "x" in chosen and not x_analysis and not row.get("analysis_copy_contract")
            and not fast_alert and not _dispatch(store, key, "x")):
        from .plan_analysis_pages_v1 import confirmed_publication
        from .plan_reader_editorial_v1 import prepare_social_copy
        if confirmed_publication(store, row["source_plan"]):
            prepared = prepare_social_copy(store, row, root=root)
            if prepared["status"] == "PREPARED":
                x_analysis = {k: prepared["row"][k] for k in (
                    "reader_fields", "reader_source", "reader_call_line", "analysis_publication",
                    "variant_calls", "unknown_acronyms_logged")}
    if not chosen:
        return {"destinations": [], "deferred_destinations": deferred, "output_dir": str(folder.resolve())}
    title = (row["lead"] if row["kind"] == "run" else
             f"{row['instrument_title']} · #{row['short_id']} · "
             + (ending_words(row) if row["kind"] == "result" else "call card" if row["kind"] == "setup" else "update"))
    if row.get("reader_contract") and not row.get("state_alert_contract"):
        title = row["reader_fields"]["hook"]["text"]
    if row["kind"] == "result" and row.get("level_contract") == CURRENT_LEVEL_CONTRACT:
        title = row["lead"]
    article = {"title": title, "dek": row["lead"], "body": row["text"], "plan_publication_kind": row["kind"],
               "author_identity": "Capital Chronicle", "publisher_identity": "Capital Chronicle"}
    # Registered packages keep exact bytes for readback/reconciliation. This
    # cannot create a new drawn image; fresh packages always use CC-314.
    threads_intent = previous and store.get_outbox_message(_dispatch_ids(key, "threads")["message_id"])
    frozen = bool(previous and (threads_intent or any(_dispatch(store, key, d) for d in destinations_for(row))))
    assets, carousel, skipped = [], [], _skipped_images(root, row)
    instagram_chart_credit = previous.get("status_post_instagram_chart_credit")
    first_image_failure = None
    manifest_path = folder / "delivery_media_manifest_v1.json"
    if frozen:
        assets = (previous.get("media") or {}).get("assets") or []
        carousel = previous.get("status_post_instagram_carousel") or []
        skipped = previous.get("status_post_skipped_destinations") or []
        chart_credit = bool(previous.get("chart_credit"))
    else:
        members = list({m["key"]: m for d in chosen for m in
            postable_run_members(store, row, d, root=root)}.values()) if row["kind"] == "run" else [row]
        image_ready_keys = set()
        all_carousel_images = True
        manifest = {"status": "PASS", "assets": []}
        for member in members:
            member_folder = Path(root) / member["key"]
            source_snapshot = _confirmed_page_snapshot(store, member)
            try:
                card, _ = posts._post_image(member, member_folder, snapshot=snapshot,
                    snapshot_allowed=snapshot_allowed, source_snapshot=source_snapshot,
                    required_chart=True, plan_post=True)
            except tv.SnapshotUnavailable as exc:
                if row["kind"] != "run":
                    raise
                first_image_failure = first_image_failure or str(exc)
                all_carousel_images = False
                continue
            if card is None:
                all_carousel_images = False
                continue
            image_ready_keys.add(member["key"])
            if row.get("reader_fields") and row["reader_fields"].get("alt_text"):
                card = {**card, "alt_text": row["reader_fields"]["alt_text"]["text"]}
            if host is None:
                from .cloudinary_delivery_media_v1 import prepare_cloudinary_delivery_media as host
            local_manifest_path = member_folder / "delivery_media_manifest_v1.json"
            if not posts._hosted(local_manifest_path, card):
                delivery = host(work_item_id=member["key"], delivery_only_assets=[card], existing_manifest=None,
                                article_assets=[], article=article, source_documents=[])
                if delivery.get("status") != "CLOUDINARY_DELIVERY_MEDIA_READY":
                    raise posts.PlanPostError("PLAN_STATUS_CHART_HOSTING_" + str(delivery.get("status") or "FAILED"))
                local_manifest_path.write_bytes(canonical_bytes(delivery["manifest"]))
            local_manifest = json.loads(local_manifest_path.read_bytes())
            assets.append(card)
            carousel_card = card
            native_templates = bool(card.get("image_template"))
            if not row.get("state_alert_contract") and (
                    "instagram_business" in chosen or native_templates and "threads" in chosen):
                # CC-463: a separate native portrait capture from the same
                # service. A failed portrait affects only Instagram.
                carousel_card, _ = posts._post_image(member, member_folder, snapshot=snapshot,
                    snapshot_allowed=snapshot_allowed, ratio="4:5", required_chart=True, plan_post=True)
                if carousel_card is None:
                    all_carousel_images = False
                    for hosted in local_manifest["assets"]:
                        if hosted["media_asset_id"] not in {a["media_asset_id"] for a in manifest["assets"]}:
                            manifest["assets"].append(hosted)
                    continue
                if row.get("reader_fields") and row["reader_fields"].get("alt_text"):
                    carousel_card = {**carousel_card, "alt_text": row["reader_fields"]["alt_text"]["text"]}
                if not posts._hosted(local_manifest_path, carousel_card):
                    delivery = host(work_item_id=member["key"], delivery_only_assets=[carousel_card], existing_manifest=None,
                                    article_assets=[], article=article, source_documents=[])
                    if delivery.get("status") != "CLOUDINARY_DELIVERY_MEDIA_READY":
                        raise posts.PlanPostError("PLAN_STATUS_CHART_HOSTING_" + str(delivery.get("status") or "FAILED"))
                    local_manifest["assets"].extend(delivery["manifest"]["assets"])
                    local_manifest_path.write_bytes(canonical_bytes(local_manifest))
                assets.append(carousel_card)
            for hosted in local_manifest["assets"]:
                if hosted["media_asset_id"] not in {a["media_asset_id"] for a in manifest["assets"]}:
                    manifest["assets"].append(hosted)
            hosted = next(a for a in local_manifest["assets"] if a["sha256"] == carousel_card["sha256"])
            carousel.append({"asset_id": carousel_card["asset_id"], "path": carousel_card["path"],
                "sha256": carousel_card["sha256"], "url": hosted["verified_public_delivery_url"]})
        if assets:
            manifest_path.write_bytes(canonical_bytes(manifest))
        if not assets or not all_carousel_images:
            skipped = [{"destination": "instagram_business", "cause": "TRADINGVIEW_CAPTURE_FAILED_IMAGE_REQUIRED"}]
            tv.record_outcome({"key": key, "market": row["symbol"], "destination": "instagram_business",
                               "status": "SKIPPED_IMAGE_REQUIRED", "cause": skipped[0]["cause"]})
        chart_credit = bool(assets and assets[0].get("tradingview_snapshot"))
        if carousel:
            selected_ids = {item["asset_id"] for item in carousel}
            instagram_chart_credit = any(a.get("tradingview_snapshot") for a in assets if a["asset_id"] in selected_ids)
        if row["kind"] == "run":
            image_unpostable = [d for d in chosen if not image_ready_keys.intersection(
                m["key"] for m in postable_run_members(store, row, d, root=root))]
            unpostable.extend({"destination": d, "cause": "RUN_HAS_NO_POSTABLE_CALL_IMAGE"} for d in image_unpostable)
            chosen = [d for d in chosen if d not in image_unpostable]
    skipped = list({s["destination"]: s for s in [*skipped, *unpostable]}.values())
    if not assets:
        raise tv.SnapshotUnavailable(first_image_failure or "EVERY_POST_IMAGE_REQUIRED:PLAN_" + row["kind"].upper())
    alert_portrait = previous.get("status_post_alert_portrait")
    alert_portrait_destinations = [d for d in chosen if d == "instagram_business"
                                   or d == "threads" and assets and assets[0].get("image_template")]
    if row.get("state_alert_contract") and alert_portrait_destinations and not alert_portrait:
        # The fast API pass freezes its landscape bytes. Complete Instagram's
        # separate portrait afterwards; append media without changing those
        # already-issued payloads or their original chart.
        try:
            portrait, _ = posts._post_image(row, folder, snapshot=snapshot,
                snapshot_allowed=snapshot_allowed, ratio="4:5", required_chart=True, plan_post=True)
            if not portrait:
                raise tv.SnapshotUnavailable("TRADINGVIEW_CAPTURE_FAILED_IMAGE_REQUIRED")
            if host is None:
                from .cloudinary_delivery_media_v1 import prepare_cloudinary_delivery_media as host
            delivery = host(work_item_id=key, delivery_only_assets=[portrait], existing_manifest=None,
                article_assets=[], article=article, source_documents=[])
            if delivery.get("status") != "CLOUDINARY_DELIVERY_MEDIA_READY":
                raise posts.PlanPostError("PLAN_STATUS_CHART_HOSTING_" + str(delivery.get("status") or "FAILED"))
            manifest = json.loads(manifest_path.read_bytes())
            manifest["assets"].extend(delivery["manifest"]["assets"])
            manifest_path.write_bytes(canonical_bytes(manifest))
            assets.append(portrait)
            hosted = delivery["manifest"]["assets"][0]
            carousel = [{"asset_id": portrait["asset_id"], "path": portrait["path"],
                "sha256": portrait["sha256"], "url": hosted["verified_public_delivery_url"]}]
            alert_portrait = portrait["asset_id"]
            instagram_chart_credit = bool(portrait.get("tradingview_snapshot"))
            previous.update(media={"assets": assets}, status_post_instagram_carousel=carousel,
                            status_post_alert_portrait=alert_portrait,
                            status_post_instagram_chart_credit=instagram_chart_credit)
            if "threads" in alert_portrait_destinations or portrait.get("image_template"):
                previous["status_post_threads_image"] = alert_portrait
        except tv.SnapshotUnavailable as exc:
            skipped.extend({"destination": d, "cause": str(exc)[:200]} for d in alert_portrait_destinations)
        except tv.SnapshotPending as exc:
            deferred.extend({"destination": d, "cause": str(exc)[:200]} for d in alert_portrait_destinations)
            chosen = [d for d in chosen if d not in alert_portrait_destinations]
        except (OSError, ValueError, KeyError, TypeError) as exc:
            skipped.extend({"destination": d, "cause": str(exc)[:200]} for d in alert_portrait_destinations)
        if frozen:
            previous["status_post_skipped_destinations"] = skipped
            context_path.write_bytes(canonical_bytes(previous))
    skipped_names = {s["destination"] for s in skipped}
    chosen = [d for d in chosen if d not in skipped_names]
    card = assets[0] if assets else None
    portrait_id = previous.get("status_post_threads_image") if frozen else next(
        (a["asset_id"] for a in assets if (a.get("image_template") or {}).get("master") == "T"),None)
    context = previous
    if not frozen:
        context = {"schema_version": "contentops.plan_status_post_context.v1", "article": article,
            "selection": {}, "media": {"assets": assets}, "plan_status_post": key,
            "chart_credit": chart_credit, "status_post_chart_policy": "CC459_TRADINGVIEW",
            "status_post_threads_single_notice": True,
            "status_post_facebook_reply_images": True,
            "status_post_parents": parents, "status_post_instagram_carousel": carousel,
            "status_post_skipped_destinations": skipped, "status_post_threads_image": portrait_id,
            "status_post_instagram_chart_credit": instagram_chart_credit}
        if alert_portrait:
            context["status_post_alert_portrait"] = alert_portrait
        if row.get("reader_contract") and not row.get("state_alert_contract"):
            context["reader_contract"] = row["reader_contract"]
            context["reader_source"] = row["reader_source"]
            context["reader_fields"] = row["reader_fields"]
        if x_analysis:
            context["status_post_x_analysis"] = x_analysis
        if linkedin_url:
            context["status_post_linkedin_analysis_url"] = linkedin_url
        context_path.write_bytes(canonical_bytes(context))
    elif row.get("parent_key"):
        # A sibling dispatch can freeze the chart before this destination's
        # setup is confirmed. Add only parents for copies yet to be issued.
        frozen_parents = previous.get("status_post_parents") or {}
        new_parents = {d: parents[d] for d in chosen
                       if d in parents and d not in frozen_parents and not _dispatch(store, key, d)}
        if new_parents:
            previous["status_post_parents"] = {**frozen_parents, **new_parents}
            context_path.write_bytes(canonical_bytes(previous))
    if frozen and x_analysis and not previous.get("status_post_x_analysis"):
        previous["status_post_x_analysis"] = x_analysis
        context_path.write_bytes(canonical_bytes(previous))
    if frozen and linkedin_url and not previous.get("status_post_linkedin_analysis_url"):
        previous["status_post_linkedin_analysis_url"] = linkedin_url
        context_path.write_bytes(canonical_bytes(previous))
    # A sibling can freeze the package before Threads receives an intent.
    # Only an issued Threads copy needs its original notice layout.
    if (frozen and "threads" in chosen and not context.get("status_post_threads_single_notice")
            and not threads_intent and not _dispatch(store, key, "threads")):
        context["status_post_threads_single_notice"] = True
        context_path.write_bytes(canonical_bytes(context))
    payloads = route_payloads({**row, "linkedin_analysis_url": linkedin_url}, card_id=card["asset_id"] if card else None,
                                  parents=parents, carousel=carousel, chart_credit=chart_credit,
                                  instagram_chart_credit=instagram_chart_credit,
                                  portrait_id=portrait_id, x_analysis=x_analysis,
                                  complete_levels=context.get("status_post_chart_policy") == "CC459_TRADINGVIEW",
                                   repeat_threads_notices=not context.get("status_post_threads_single_notice"),
                                   facebook_reply_images=bool(context.get("status_post_facebook_reply_images")))
    if row.get("analysis_copy_contract") == NINE_LAYER_COPY:
        counts = context.setdefault("status_post_layer_reply_counts", {})
        for destination in chosen:
            if parts := payloads[destination].get("parts"):
                counts[destination] = len(parts) - 1
        context_path.write_bytes(canonical_bytes(context))
    roots = posts._part_payloads(payloads)
    plan_rows = []
    for destination in chosen:
        registration = registration_for_destination(destination)
        text = roots[destination]["full_text"]
        plan_rows.append({"destination": destination, "platform": registration.platform,
            "surface": registration.surface, "transport_type": registration.transport_type,
            "transport_registry_version": REGISTRY_VERSION, "payload": text,
            "payload_hash": hashlib.sha256(text.encode()).hexdigest(),
            "canonical_url": linkedin_url if destination in LINKEDIN_DESTINATIONS else None,
            "expected_destination_identity": registration.expected_identity})
    plan = {"schema_version": "contentops.publication_plan.v1", "plan_status_post": key,
        "plan_hash": hashlib.sha256(("plan-status-post:" + key).encode()).hexdigest(),
        "story_identity": key, "article_identity": key, "package_identity": key,
        "publication_window": {"window_identity": key}, "output_dir": str(folder.resolve()),
        "status_post_card_id": card["asset_id"] if card else None, "transport_registry_version": REGISTRY_VERSION,
        "policy_mode_version": "AUTONOMOUS_DEFAULT:cc399.v1", "destinations": plan_rows,
        "continuations": [], "deferred_destinations": deferred, "skipped_destinations": skipped}
    discord = next((item for item in plan_rows if item["destination"] == "discord"), None)
    if discord:
        channel = discord_channel_payload(row, card_id=plan["status_post_card_id"],
                                          parents=parents, chart_credit=chart_credit)
        if channel:
            text = channel["discord"]["full_text"]
            plan["continuations"].append(_card_continuation(plan, DISCORD_CHANNEL_PART, [
                {**discord, "payload": text, "payload_hash": hashlib.sha256(text.encode()).hexdigest()}]))
    reply_count = max((len(payloads[d]["parts"]) - 1 for d in chosen if payloads[d].get("parts")), default=0)
    for part in range(ANALYSIS_FIRST_PART, ANALYSIS_FIRST_PART + reply_count):
        children = []
        for entry in plan_rows:
            parts = payloads[entry["destination"]].get("parts") or ()
            index = part - ANALYSIS_FIRST_PART + 1
            if index < len(parts):
                text = parts[index]
                children.append({**entry, "payload": text, "payload_hash": hashlib.sha256(text.encode()).hexdigest()})
        plan["continuations"].append(_card_continuation(plan, part, children))
    return plan


def _card_continuation(plan, part, destinations):
    child = f"{plan['plan_status_post']}-part-{part}"
    return {**plan, "plan_status_part": part, "continuations": [], "work_item_id": child,
            "story_identity": child, "article_identity": child, "package_identity": child,
            "plan_hash": hashlib.sha256(("plan-status-post:" + child).encode()).hexdigest(),
            "destinations": destinations}



def validate_parent_intent(store, row, intent, *, parent_route=None):
    destination = intent["destination_plan"]["destination"]
    refusal = posts.publication_refusal(store, row, now=datetime.now(timezone.utc))
    if refusal:
        raise posts.PlanPostError(refusal[1])
    if row["kind"] == "run" and not postable_run_members(store, row, destination,
            now=datetime.now(timezone.utc), root=Path(intent.get("output_dir") or ".").parent, current=True):
        raise posts.PlanPostError("RUN_HAS_NO_POSTABLE_CALL:" + destination)
    if row.get("source_plan_registration"):
        now = datetime.now(timezone.utc)
        current = posts.current_public_plan(row["plan_id"], registration_hash=row["source_plan_registration"], now=now)
        refusal = posts.publication_refusal(store, row, now=now, latest_states={row["plan_id"]: current.get("status")})
        if refusal:
            raise posts.PlanPostError(refusal[1])
    if row.get("state_alert_contract") == "CC543_V1":
        from .plan_state_alerts_v1 import validate as validate_alert
        validate_alert(row, store=store)
    elif row.get("reader_contract") == "CC466_V1":
        from .plan_reader_editorial_v1 import validate_reader_row
        validate_reader_row(store, row)
    if row["kind"] == "setup" and row.get("time_exit_utc") and datetime.now(timezone.utc) >= posts._utc(row["time_exit_utc"]):
        raise posts.PlanPostError("PLAN_CARD_ALREADY_ENDED_BEFORE_WRITE")
    if intent.get("plan_status_part", 0) >= ANALYSIS_FIRST_PART:
        # The caller recomputes the exact reply route from the confirmed dispatch.
        return
    if not row.get("parent_key"):
        return
    payload = intent["native_payload"]
    standalone = row.get("state_alert_contract") and (parent_route or {}).get("delivery_mode") == "standalone"
    if destination == "discord" and (row.get("discord_delivery") == "channel" or standalone):
        if (payload.get("discord_channel_post") is not True
                or any(payload.get(k) for k in ("discord_thread_parent_id", "reply_to_id", "discord_thread_name"))):
            raise posts.PlanPostError("PLAN_CARD_DISCORD_CHANNEL_ROUTE_CHANGED")
        return
    if standalone:
        if any(payload.get(k) for k in ("reply_to_id", "reply_to_url", "own_call_comment",
                                        "carousel_parent_id", "reuse_run_carousel")):
            raise posts.PlanPostError("PLAN_CARD_STANDALONE_ROUTE_CHANGED")
        return
    ref = _reference(store, row["parent_key"], destination)
    if not ref:
        raise posts.PlanPostError("CARD_PARENT_NOT_CONFIRMED")
    reply_destination = destination in {"telegram", "threads", "substack_notes", "facebook_page"} or (
        destination == "instagram_business" and row["kind"] != "setup")
    if reply_destination and str(ref["public_object_id"]) != payload.get("reply_to_id"):
        raise posts.PlanPostError("PLAN_CARD_REPLY_PARENT_CHANGED")
    if destination == "instagram_business" and row["kind"] == "setup" and (
            not payload.get("reuse_run_carousel") or str(ref["public_object_id"]) != payload.get("carousel_parent_id")):
        raise posts.PlanPostError("PLAN_CARD_CAROUSEL_PARENT_CHANGED")
    if destination == "discord":
        frozen_thread = (parent_route or {}).get("thread_parent_id")
        root = ref if row.get("state_alert_contract") and frozen_thread == ref["public_object_id"] else (
            _discord_thread_root(store, row, ref))
        if intent.get("plan_status_part") == DISCORD_CHANNEL_PART:
            anchor = _discord_channel_anchor(ref, root)
            if (not anchor or anchor != (parent_route or {}).get("channel_reply")
                    or str(anchor["reply_to_id"]) != payload.get("reply_to_id")
                    or payload.get("discord_channel_reply") is not True):
                raise posts.PlanPostError("PLAN_CARD_DISCORD_CHANNEL_REPLY_PARENT_CHANGED")
            return
        if not root or str(root["public_object_id"]) != payload.get("discord_thread_parent_id"):
            raise posts.PlanPostError("PLAN_CARD_DISCORD_THREAD_CHANGED")
        if row["kind"] != "setup" and str(ref["public_object_id"]) != payload.get("reply_to_id"):
            raise posts.PlanPostError("PLAN_CARD_REPLY_PARENT_CHANGED")


def _publish_discord_channel_reply(store, row, continuation, coordinator_for, *, immediate):
    key = continuation["work_item_id"]
    dispatch = _dispatch(store, key, "discord") or {}
    if dispatch.get("status") in SETTLED_DISPATCHES:
        coordinator = coordinator_for(key, Path(continuation["output_dir"]))
        outcome = coordinator.publication_state(key, continuation)
    else:
        outcome = _publish_card_plan(store, row, continuation, coordinator_for,
                                     parallel=False, immediate=immediate)
    detail = (outcome.get("per_destination") or {}).get("discord") or {}
    return {"status": detail.get("status") or outcome.get("distribution_status") or "NOT_STARTED",
            "dispatch_id": detail.get("dispatch_id"), "public_object_url": detail.get("public_object_url"),
            "reconciliation_status": detail.get("reconciliation_status"),
            "cause": posts.destination_causes(outcome).get("discord")}


def readback_own_comment(destination, comment_id, parent_id, text, *, chart_path=None, observe_images=False):
    """Read the exact comment in its confirmed business card's comment list."""
    if destination == "facebook_page":
        from . import facebook_page_adapter_v6 as adapter
        token, field = adapter._facebook_token(), "message"
    elif destination == "instagram_business":
        from . import instagram_adapter_v6 as adapter
        token, field = adapter._instagram_token(), "text"
    else:
        raise posts.PlanPostError("PLAN_CARD_COMMENT_DESTINATION_INVALID")
    try:
        inspect_attachment = destination == "facebook_page" and (chart_path or observe_images)
        fields = f"id,{field},attachment{{type,media}}" if inspect_attachment else f"id,{field}"
        data = adapter._get_json(f"https://graph.facebook.com/{adapter.GRAPH_VERSION}/{parent_id}/comments",
                                 {"access_token": token, "fields": fields, "limit": 100})
        match = next((r for r in data.get("data") or [] if str(r.get("id")) == str(comment_id)), None)
        text_matches = bool(match and match.get(field) == text)
        attachment = (match or {}).get("attachment")
        image_url = (((attachment or {}).get("media") or {}).get("image") or {}).get("src")
        verified = text_matches
        if chart_path and text_matches:
            verified = bool(image_url and adapter.visual_similarity_to_local_file(
                adapter.read_public_image_bytes(image_url), chart_path) >= adapter.PUBLIC_CHART_VISUAL_SIMILARITY_MINIMUM)
        observed = {}
        if observe_images and inspect_attachment and text_matches and (image_url or not attachment):
            observed["observed_image_urls"] = [image_url] if image_url else []
        return {"status": "SUCCESS" if verified else "READBACK_UNAVAILABLE", "verified": verified,
                "public_object_id": comment_id, "body_text_visible": text_matches, "reply_parent_verified": bool(match),
                **({"meaningful_media_visible": verified} if chart_path else {}), **observed}
    except Exception as exc:
        return {"status": "READBACK_UNAVAILABLE", "verified": False,
                "safe_error_classification": type(exc).__name__}


def _publish_card_plan(store, row, plan, coordinator_for, *, parallel, immediate):
    key = plan.get("work_item_id", row["key"])
    if row.get("state_alert_contract") == "CC543_V1":
        plan["state_alert_contract"] = row["state_alert_contract"]
        plan["defer_alert_recovery"] = immediate
    part = plan.get("plan_status_part")
    title = ("Plan chart update" if part == LATE_CHART_PART else
             "Plan analysis continuation" if part is not None and part >= ANALYSIS_FIRST_PART else
             "Discord plan reply in #announcements" if part else "Call run" if row["kind"] == "run" else "Call card")
    store.create_work_item(story_id=key, title=title, target_surface="MULTI_PLATFORM", work_item_id=key)

    def scoped_coordinator():
        coordinator = coordinator_for(key, Path(plan["output_dir"]))
        posts.scope_to_post(coordinator, key, plan)
        return coordinator

    coordinator = scoped_coordinator()
    coordinator.register_plan(key, plan)
    if parallel:
        return coordinator.execute_plan(key, plan, alert_worker_for=scoped_coordinator)
    return coordinator.execute_plan(key, plan)


def _analysis_reply_destinations(store, row, plan):
    part = plan["plan_status_part"]
    parent = row["key"] if part == ANALYSIS_FIRST_PART else f"{row['key']}-part-{part - 1}"
    return [entry for entry in plan["destinations"] if _reference(store, parent, entry["destination"])
            and (_dispatch(store, plan["work_item_id"], entry["destination"]) or {}).get("status")
            not in SETTLED_DISPATCHES]


def publish_ready(store, *, now, latest_states=None, root, host=None, coordinator_for=None, limit=5, automatic_neo=False,
                  snapshot=None, snapshot_allowed=None, destinations=None, alert_filter=None, claim_checker=None):
    from .public_draft_claims_v1 import try_plan_check
    from .tradingview_snapshot_v1 import SnapshotPending, SnapshotUnavailable
    if coordinator_for is None:
        def coordinator_for(key, folder):
            from .native_neo_executor_v1 import bind_native_neo_coordinator
            return bind_native_neo_coordinator(store, operation_id=key, output_dir=folder / "native-neo",
                native_invocation_id="plan-status-posts-cc399", allow_publish=True, automatic=automatic_neo)[0]
    pending, late_charts = [], []
    for outbox in store.list_outbox_messages(destination=posts.DESTINATION):
        row = json.loads(outbox["payload"])
        if row.get("format") == FORMAT and outbox["status"] in {posts.READY, "PUBLISHING"}:
            alert = row.get("state_alert_contract") == "CC543_V1"
            if alert_filter is None or alert == alert_filter:
                pending.append((outbox, row))
        if (destinations is None and automatic_neo and row.get("format") == FORMAT
                and row.get("kind") != "run" and outbox["status"] in {"PUBLISHED", "PUBLISHING", SETTLED_POST}
                and (alert_filter is None or alert_filter == bool(row.get("state_alert_contract")))
                and posts._age_minutes(row, now) <= posts.LATE_STATE_HOURS * 60):
            late_charts.append(row)
    def priority(pair):
        _, row = pair
        # Run roots can supply replies. An alert recovering from a refused
        # parent goes first, then newer alerts get the remaining time.
        refused_parent = bool(row.get("state_alert_contract") and row.get("parent_key") and any(
            (_dispatch(store, row["parent_key"], d) or {}).get("status") == "DEFINITE_NO_WRITE"
            for d in ("telegram", "discord")))
        return (0 if row["kind"] == "run" or refused_parent else 1, -posts._utc(row["at_utc"]).timestamp(),
                {"run": 0, "setup": 1, "update": 2, "result": 3}[row["kind"]])
    pending.sort(key=priority)
    results, retired, calls, browser_only = [], [], 0, 0
    for outbox, row in pending:
        key = row["key"]
        refusal = posts.publication_refusal(store, row, now=now, latest_states=latest_states)
        if refusal:
            outcome = {"key": key, "status": refusal[0], "cause": refusal[1], "readbacks": []}
            results.append(outcome)
            if _can_retire_unstarted(store, row, root):
                store.set_outbox_status(key, refusal[0])
            elif destinations is None:
                retired.append((outbox, row, outcome))
            continue
        settled = settle_pending(store, outbox, row, now=now, root=root)
        if settled:
            results.append(settled)
            continue
        # The immediate pass never opens a page, calls a model or starts a
        # browser route. Frozen historical packets retain their own recovery.
        if destinations is not None and row.get("state_alert_contract") != "CC543_V1":
            continue
        if (row.get("reader_contract") == "CC466_V1" and not row.get("reader_fields")
                and not row.get("state_alert_contract")):
            from .plan_reader_editorial_v1 import prepare_social_row
            prepared = prepare_social_row(store, row, root=root)
            if prepared["status"] != "PREPARED":
                results.append({"key": key, **prepared})
                continue
            row = prepared["row"]
        if row["kind"] == "run" and outbox["status"] == posts.READY and latest_states is not None:
            try:
                members = [posts._row_payload(store, child) for child in row["card_keys"]]
            except (OSError, ValueError, KeyError, TypeError) as exc:
                results.append({"key": key, "status": "NOT_STARTED", "cause": str(exc)[:200]})
                continue
            if members and all(latest_states.get(child["plan_id"]) in TERMINAL | {"RESULT"}
                    or (child.get("time_exit_utc") and now >= posts._utc(child["time_exit_utc"]))
                    for child in members):
                store.set_outbox_status(key, posts.SUPERSEDED)
                results.append({"key": key, "status": posts.SUPERSEDED, "cause": "RUN_HAS_NO_CURRENT_CARDS"})
                continue
        # An ended setup is retired before it can consume a fresh-card slot.
        if row["kind"] == "setup" and outbox["status"] == posts.READY:
            current = (latest_states or {}).get(row["plan_id"])
            if (current in TERMINAL or current == "RESULT"
                    or (row.get("time_exit_utc") and now >= posts._utc(row["time_exit_utc"]))):
                store.set_outbox_status(key, posts.SUPERSEDED)
                results.append({"key": key, "status": posts.SUPERSEDED, "cause": "PLAN_ALREADY_ENDED"})
                continue
        if (row["kind"] == "update" and outbox["status"] == posts.READY
                and row.get("state") in posts.ACTIVE
                and (latest_states or {}).get(row["plan_id"]) in TERMINAL | {"RESULT"}
                and _can_retire_unstarted(store, row, root)):
            store.set_outbox_status(key, posts.SUPERSEDED)
            results.append({"key": key, "status": posts.SUPERSEDED,
                "cause": "PLAN_UPDATE_SUPERSEDED_BY_" + latest_states[row["plan_id"]]})
            continue
        ready = _ready_destinations(store, row, root=root)
        if row["kind"] == "run":
            ready = [d for d in ready if postable_run_members(store, row, d, now=now,
                latest_states=latest_states, root=root)]
        if destinations is not None:
            ready = [d for d in ready if d in destinations]
            if not ready:
                continue
        if not ready:
            if row["kind"] == "run":
                results.append({"key": key, "status": "WAITING", "cause": "RUN_HAS_NO_POSTABLE_CALL"})
                continue
            _, deferred = _parents(store, row, destinations_for(row), {})
            results.append({"key": key, "status": "WAITING" if deferred else "SETTLED",
                "cause": deferred[0]["cause"] if deferred else "ALL_DESTINATIONS_SETTLED",
                "deferred_destinations": deferred})
            continue
        api_done = not any(d in API_DESTINATIONS for d in ready)
        if api_done and browser_only >= limit:
            results.append({"key": key, "status": "WAITING", "cause": "BROWSER_WORK_LIMIT_THIS_RUN"})
            continue
        if not api_done and row["kind"] != "run" and calls >= limit:
            results.append({"key": key, "status": "WAITING", "cause": "CARD_WORK_LIMIT_THIS_RUN"})
            continue
        try:
            # Source mismatches stop before chart or transport work. A row
            # refused here must leave the delivery slot available to others.
            if row.get("state_alert_contract") == "CC543_V1":
                from .plan_state_alerts_v1 import validate as validate_alert
                validate_alert(row, store=store)
            if api_done:
                browser_only += 1
            elif row["kind"] != "run":
                calls += 1
            groups = [tuple(ready)]
            portrait = "instagram_business"
            parallel = automatic_neo and alert_filter is True
            if (parallel and row.get("state_alert_contract") and len(ready) > 1 and portrait in ready
                    and not _dispatch(store, key, portrait)):
                # The portrait needs a separate capture and upload. Dispatch the
                # landscape copies first so Instagram's input cannot delay them.
                groups = [tuple(d for d in ready if d != portrait), (portrait,)]
            per_destination, media, deferred = {}, {}, []
            channel_reply = None
            attempted = False
            for group in groups:
                selected = {"destinations": group} if row.get("state_alert_contract") or destinations is not None else {}
                plan = prepare_post(store, key, root=root, host=host, snapshot=snapshot,
                                    snapshot_allowed=snapshot_allowed, fast_alert=alert_filter is True, **selected)
                media.update({d["destination"]: d for d in plan.get("skipped_destinations") or []})
                deferred.extend(plan["deferred_destinations"])
                if plan["destinations"]:
                    try_plan_check(claim_checker, store, row, plan)
                    outcome = _publish_card_plan(store, row, plan, coordinator_for, parallel=parallel,
                                                 immediate=destinations is not None)
                    per_destination.update(outcome.get("per_destination") or {})
                    for continuation in plan["continuations"]:
                        try_plan_check(claim_checker, store, row, continuation, key=continuation["work_item_id"])
                        if continuation["plan_status_part"] == DISCORD_CHANNEL_PART:
                            channel_reply = _publish_discord_channel_reply(store, row, continuation, coordinator_for,
                                                                            immediate=destinations is not None)
                            continue
                        replies = _analysis_reply_destinations(store, row, continuation)
                        if replies:
                            reply_outcome = _publish_card_plan(store, row, {**continuation, "destinations": replies},
                                coordinator_for, parallel=parallel, immediate=destinations is not None)
                            per_destination.update(reply_outcome.get("per_destination") or {})
                    attempted = True

            skipped_details = list(media.values())
            if not attempted:
                settled = settle_pending(store, outbox, row, now=now, root=root) if skipped_details else None
                if settled:
                    results.append(settled)
                    continue
                cause = (deferred or skipped_details or [{}])[0].get("cause", "CARD_PARENT_NOT_CONFIRMED")
                results.append({"key": key,
                                "status": "WAITING_FOR_TRADINGVIEW_CHART" if cause.startswith("TRADINGVIEW")
                                else "WAITING_FOR_CARD_PARENT",
                                "cause": cause,
                                "deferred_destinations": deferred,
                                "skipped_destinations": skipped_details})
                continue
            states = {d: (o or {}).get("status") for d, o in per_destination.items()}
            if channel_reply and states.get("discord") == "DISPATCH_CONFIRMED":
                states["discord"] = channel_reply["status"]
            required = destinations_for(row)
            confirmed = {d for d in required if all(
                copy.get("status") == "DISPATCH_CONFIRMED" and copy.get("public_object_id")
                for _, copy in _destination_dispatches(store, row, d, root))}
            skipped = set(media)
            settled = settled_destinations(store, row)
            done = set(required) <= confirmed | skipped | set(settled)
            closed_copy = settled or (row.get("state_alert_contract") and skipped)
            status = SETTLED_POST if done and closed_copy else "PUBLISHED" if done else "PUBLISHING"
            store.set_outbox_status(key, status)
            results.append({"key": key, "status": status,
                "per_destination": states, "confirmed_destinations": sorted(confirmed),
                "destination_causes": {**posts.destination_causes({"per_destination": per_destination}),
                    **({"discord": channel_reply["cause"]} if channel_reply and channel_reply["cause"] else {}),
                    **{d: item["cause"] for d, item in media.items()}, **{d: v["cause"] for d, v in settled.items()}},
                **({"discord_channel_reply": channel_reply} if channel_reply else {}),
                "deferred_destinations": deferred,
                "skipped_destinations": skipped_details})
        except SnapshotUnavailable as exc:
            cause = str(exc)[:200]
            results.append(settle_pending(store, outbox, row, now=now, root=root, image_cause=cause)
                           or {"key": key, "status": "TRADINGVIEW_CHART_UNAVAILABLE", "cause": cause})
        except SnapshotPending as exc:
            results.append({"key": key, "status": "WAITING_FOR_TRADINGVIEW_CHART", "cause": str(exc)[:200]})
        except (OSError, ValueError, KeyError, TypeError) as exc:
            cause = str(exc)[:200]
            status = "NOT_STARTED"
            if (cause == "PRIVATE_OR_EXECUTION_COPY_FORBIDDEN" and outbox["status"] == posts.READY
                    and _can_retire_unstarted(store, row, root)):
                # Old queued disclosures can identify the private DEMO account.
                # Preserve their bytes and close the unsent copy with its real
                # public-output refusal instead of spending every minute on it.
                status = posts.SUPERSEDED
                store.set_outbox_status(key, status)
            results.append({"key": key, "status": status, "cause": cause})
    # The API-only pass leaves issued copies for the existing full fanout.
    # Within that pass, an expired copy's network readback follows fresh sends.
    from .publication_coordinator_v1 import UNKNOWN_WRITE, ATTEMPT_STARTED, NATIVE_NEO_PENDING
    readback_count = 0
    for outbox, row, outcome in retired:
        copies = ((destination, copy_key, dispatch) for destination in destinations_for(row)
                  for copy_key, dispatch in _destination_dispatches(store, row, destination, root))
        for destination, copy_key, dispatch in copies:
            if readback_count >= limit:
                break
            if dispatch.get("status") not in {UNKNOWN_WRITE, ATTEMPT_STARTED, NATIVE_NEO_PENDING}:
                continue
            readback_count += 1
            try:
                coordinator = coordinator_for(copy_key, Path(root) / row["key"])
                outcome["readbacks"].append(coordinator.readback_existing_dispatch(dispatch["dispatch_id"]))
            except (OSError, ValueError, KeyError, TypeError) as exc:
                outcome["readbacks"].append({"destination": destination, "dispatch_id": dispatch["dispatch_id"],
                    "status": "READBACK_PENDING", "cause": str(exc)[:200], "publish_called": False})
        settle_pending(store, outbox, row, now=now, root=root)
        if row.get("state_alert_contract"):
            store.set_outbox_status(row["key"], outcome["status"])
    for row in reversed(late_charts):
        try:
            reply = _publish_late_chart(store, row, Path(root) / row["key"], coordinator_for,
                                        host=host, snapshot=snapshot, snapshot_allowed=snapshot_allowed)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            reply = {"status": "PLAN_LATE_CHART_UNCONFIRMED", "cause": str(exc)[:200]}
        if reply:
            results.append({"key": row["key"], "late_chart_reply": reply})
            break  # This optional attachment follows the ordinary fanout, one per tick.
    return {"status": "OK", "posts": results}
