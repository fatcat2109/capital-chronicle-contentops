"""CC-379: Main's whole weekly call record in the existing weekend article.

Resolution dates choose the ET week; publication selection never chooses the rows.
Only Main's explicit outcomes are used. No prices, scores or performance are computed.
"""
from __future__ import annotations

from datetime import datetime, time, timedelta
import hashlib
import json
import re
from zoneinfo import ZoneInfo

from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from live_contentops.event_article_guard_v1 import CONFLICTS_NOTICE, PUBLIC_NOTICE, check_publication_copy
from live_contentops.plan_status_posts_v1 import TITLES, _utc, read_export, result_rows_from_export

SCHEMA = "contentops.weekly_scored_calls.v1"
ET = ZoneInfo("America/New_York")
RESULTS = {"HIT": "hit", "STOPPED": "stopped", "EXPIRED": "closed at the end of its window",
           "NOT_TRIGGERED": "not triggered"}
WRITER_GUIDANCE = (
    "\nCC379_WHOLE_WEEK_RECORD: The SOURCE_PACK includes Main's complete weekly scored-call record. "
    "Include its canonical_content_text exactly once as a section of substack_body_markdown, "
    "adding the usual SOURCE markers to bind each paragraph and call line. "
    "Retain every call, including stops and window-end closes, and the weekly counts. Bind claims to this "
    "source as usual. These are resolved conditional calls, not new trade instructions. "
    "Do not claim a track record, alpha, returns, win rate, R, money, size, account details or performance. "
    "The usual Main-sourced scenarios and editorial roles still apply.\n"
)


def is_wrap(candidate, run_id=""):
    text = " ".join(str(candidate.get(k) or "") for k in ("title", "headline", "headline_text", "article_type"))
    tags = set(candidate.get("candidate_catalyst_tags") or [])
    return bool(candidate.get("weekly_call_record") is True or tags & {"WEEKLY_WRAP", "WEEKEND_WRAP"} or re.search(
        r"\b(?:weekend[ -]wrap|weekly[ -](?:wrap|review|roundup)|week in review)\b",
        text + " " + run_id, re.I))


def week_window(cutoff_utc):
    """Most recent complete Monday-Friday, midnight boundaries in date-correct ET."""
    local = _utc(cutoff_utc).astimezone(ET)
    saturday = local.date() - timedelta(days=(local.weekday() - 5) % 7)
    return (datetime.combine(saturday - timedelta(days=5), time(), ET),
            datetime.combine(saturday, time(), ET))


def _zone(symbol, low, high, source):
    """CC-583 (decision 40), as in the pinned scorecard: only the plan's own zone, on the
    plan's tick; a one-price zone or a row without plan levels prints no price."""
    from live_contentops.pinned_result_scorecard_v1 import plan_zone
    try:
        zone = plan_zone(symbol, {"zone_low": low, "zone_high": high}, source)
    except ValueError:
        raise ValueError("WEEKLY_CALL_ZONE_INVALID") from None
    return f"entry zone {zone[0]}–{zone[1]}; " if zone else ""


def project(export, *, cutoff_utc):
    status = export["status"]
    count = status.get("scored_call_count")
    plans = [p for p in status.get("plans", []) if (p.get("outcome") or {}).get("state") == "SCORED"]
    ids = [p["plan_id"] for p in plans]
    if (not isinstance(count, int) or isinstance(count, bool) or count < 0
            or count != len(plans) or len(set(ids)) != len(ids)):
        raise ValueError("WEEKLY_CALL_EXPORT_COUNT_MISMATCH")
    start, end = week_window(cutoff_utc)
    cutoff = _utc(cutoff_utc)
    rows = []
    for plan in plans:
        outcome = plan["outcome"]
        score = outcome.get("score") or {}
        result = outcome.get("result")
        if (result not in RESULTS or score.get("result") != result
                or score.get("plan_id") != plan["plan_id"] or score.get("asset_id") != plan["asset_id"]
                or score.get("direction") != plan.get("direction")
                or not outcome.get("outcome_id") or score.get("outcome_id") != outcome["outcome_id"]):
            raise ValueError("WEEKLY_CALL_SCORE_BINDING_INVALID")
        resolved = _utc(score.get("resolved_at_utc"))
        known = _utc(score.get("scored_at_utc"))
        if not start <= resolved < end or resolved > cutoff or known > cutoff:
            continue
        direction = {"BULLISH": "bullish", "BEARISH": "bearish"}.get(plan.get("direction"))
        symbol = plan["asset_id"]
        if not direction or not re.fullmatch(r"[A-Z][A-Z0-9]{1,14}", symbol):
            raise ValueError("WEEKLY_CALL_MARKET_OR_DIRECTION_INVALID")
        zone = plan.get("zone") or {}
        levels = _zone(symbol, zone.get("minimum"), zone.get("maximum"), plan)
        local = resolved.astimezone(ET)
        day = f"{local:%a} {local.day} {local:%b}"
        line = (f"- {day} ET: {TITLES.get(symbol, symbol)}; original direction was {direction}; "
                f"{levels}{RESULTS[result]}.")
        rows.append({"plan_id": plan["plan_id"], "outcome_id": outcome["outcome_id"],
                     "source_plan_hash": score.get("source_plan_hash"), "score_hash": score.get("content_hash"),
                     "resolved_at_utc": score["resolved_at_utc"], "scored_at_utc": score["scored_at_utc"],
                     "market": symbol, "direction": direction, "zone": dict(zone), "result": result,
                     "scored": True, "line": line})
    # CC-394's pinned message overflows into this same complete weekly record.
    # Preserve the reader's explicit legacy expiries as unscored, until Main
    # supplies scored NOT_TRIGGERED outcomes. Never count them as scored calls.
    sources = {p.get("plan_id"): p for p in status.get("plans", [])}
    for row in result_rows_from_export(export, include_not_triggered=True):
        if row["scored"]:
            continue
        resolved = _utc(row["at_utc"])
        if not start <= resolved < end or resolved > cutoff or _utc(status["generated_at_utc"]) > cutoff:
            continue
        plan = row["plan"]
        if plan.get("direction") not in {"bullish", "bearish"}:
            raise ValueError("WEEKLY_CALL_MARKET_OR_DIRECTION_INVALID")
        local = resolved.astimezone(ET)
        levels = _zone(row["symbol"], plan["zone_low"], plan["zone_high"], sources.get(row["plan_id"]) or {})
        line = (f"- {local:%a} {local.day} {local:%b} ET: {TITLES[row['symbol']]}; "
                f"original direction was {plan['direction']}; {levels}expired without entry; not scored.")
        rows.append({"plan_id": row["plan_id"], "outcome_id": None, "score_hash": None,
            "resolved_at_utc": row["at_utc"], "scored_at_utc": None, "market": row["symbol"],
            "direction": plan["direction"], "zone": {"minimum": plan["zone_low"], "maximum": plan["zone_high"]},
            "result": row["result"], "scored": False, "line": line})
    rows.sort(key=lambda r: (_utc(r["resolved_at_utc"]), r["plan_id"]))
    counts = {"scored_calls": sum(r["scored"] for r in rows), "hits": sum(r["result"] == "HIT" for r in rows),
              "stops": sum(r["result"] == "STOPPED" for r in rows)}
    unscored = sum(not r["scored"] for r in rows)
    if unscored:
        counts["unscored_expiries"] = unscored
    friday = (end - timedelta(days=1)).date()
    period = f"{start.day} {start:%b}–{friday.day} {friday:%b %Y} ET"
    text = (f"## The week's call results ({period})\n\n"
            f"Scored calls: {counts['scored_calls']}. Hits: {counts['hits']}. Stops: {counts['stops']}."
            + (f" Unscored expiries: {unscored}." if unscored else "") + "\n\n"
            + ("\n".join(r["line"] for r in rows) if rows else "No conditional calls were scored for this week.")
            + f"\n\nResults refer to resolved conditional calls.\n\n{PUBLIC_NOTICE} {CONFLICTS_NOTICE}")
    check_publication_copy({"body": text})
    return {"schema_version": SCHEMA, "cutoff_utc": cutoff_utc,
            "week_start_et": start.isoformat(), "week_end_exclusive_et": end.isoformat(),
            "export_content_hash": status.get("content_hash"), "export_generated_at_utc": status.get("generated_at_utc"),
            "export_scored_call_count": count, "counts": counts, "rows": rows, "text": text}


def document(record, source_id):
    text = record["text"]
    digest = hashlib.sha256(text.encode()).hexdigest()
    url = "urn:cc-public-report:weekly-scored-calls:" + sha256_of(record)
    return {"source_id": source_id, "document_id": "weekly-scored-calls-" + digest,
            "url": url, "source_url": url, "publisher": "Capital Chronicle",
            "published_at_utc": max((r.get("scored_at_utc") or record["export_generated_at_utc"]
                                     for r in record["rows"]), key=_utc,
                                    default=record["export_generated_at_utc"]),
            "canonical_content_text": text, "canonical_content_sha256": digest,
            "raw_sha256": record["export_content_hash"], "content_truncated": False,
            "public_claim_allowed": True, "source_authority_class": "governed_capital_chronicle_report_only",
            "weekly_scored_calls": record,
            "source_reuse_constraints": {"public_expression_reuse_allowed": True,
                "scope": "CAPITAL_CHRONICLE_OWN_PUBLIC_CALL_RESULTS", "authority_ref": "JIM_DECISIONS_40_84_106"}}


def enrich_source_pack(turn, *, source_pack, selected_candidate, cutoff_utc):
    if not is_wrap(selected_candidate, turn.run_id):
        return source_pack
    path = turn.root / "weekly_scored_calls_v1.json"
    if turn.frozen_request("write") and not path.exists():
        return source_pack  # Historical frozen requests retain their exact input.
    if path.exists():
        record = json.loads(path.read_bytes())
        if record["cutoff_utc"] != cutoff_utc:
            raise ValueError("WEEKLY_CALL_FROZEN_CUTOFF_CHANGED")
    else:
        record = project(read_export(), cutoff_utc=cutoff_utc)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(canonical_bytes(record))
    return [*source_pack, document(record, f"SOURCE_{len(source_pack) + 1}")]


def validate_article(article, documents):
    """Reject selective omission or altered numbers; source metadata is never writer-certified."""
    records = [d for d in documents if d.get("weekly_scored_calls")]
    if not records:
        return None
    if len(records) != 1:
        raise ValueError("WEEKLY_CALL_SINGLE_RECORD_REQUIRED")
    doc = records[0]
    expected = document(doc["weekly_scored_calls"], doc["source_id"])
    if doc != expected:
        raise ValueError("WEEKLY_CALL_SOURCE_CHANGED")
    text = doc["canonical_content_text"]
    body = re.sub(r"\[\[SOURCE:SOURCE_\d+\]\]", "", article.get("substack_body_markdown") or "")
    def normal(value):
        return " ".join(value.split())
    if normal(body).count(normal(text)) != 1:
        raise ValueError("WEEKLY_CALL_COMPLETE_RECORD_REQUIRED")
    return {"source_id": doc["source_id"], "source_sha256": doc["canonical_content_sha256"],
            "week_start_et": doc["weekly_scored_calls"]["week_start_et"],
            "counts": doc["weekly_scored_calls"]["counts"]}
