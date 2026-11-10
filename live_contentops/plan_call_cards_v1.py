"""CC-399: run announcements, source-bound call cards and their replies.

Uses the plan-status outbox and DurablePublicationCoordinator. Historical packets
keep their original composer. No analytical value is estimated here.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import re
from typing import Mapping

from . import plan_status_posts_v1 as posts
from .event_article_guard_v1 import PUBLIC_NOTICE, CONFLICTS_NOTICE, check_publication_copy, conditional_call_text

EFFECTIVE = datetime(2026, 11, 10, 2, 11, tzinfo=timezone.utc)
FORMAT = 4
API_DESTINATIONS = ("telegram", "discord", "threads", "facebook_page", "instagram_business")
DESTINATIONS = (*API_DESTINATIONS, "substack_notes")
TERMINAL = {"CANCELLED", "INVALIDATED", "EXPIRED", "VIEW_CHANGED"}
NOTICES = f"{PUBLIC_NOTICE} {CONFLICTS_NOTICE}"
GLOSSARY = {
    "DXY": "the US dollar index", "COT": "the futures positioning report",
    "M15": "short-interval", "M5": "short-interval", "H1": "hourly",
    "risk-off": "risk aversion", "risk-on": "risk appetite",
    "invalidation": "the level that proves the idea wrong",
    "priced": "already reflected in prices", "macro": "economic",
}


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
    plan["short_id"] = re.sub(r"^(?:call|plan)_", "", str(call_id))[:8]
    plan["registered_at_utc"] = raw.get("registered_at_utc") or raw.get("not_before_utc")
    plan["reader_reasons"] = raw.get("reader_reasons", raw.get("freeze_reasons", []))
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
    hits = sum(s["result"] == "HIT" for s in scores.values())
    return f"{since}{len(scores)} calls judged, {hits} hit their target."


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


def compose(row):
    kind = row["kind"]
    if kind == "run":
        at = posts._utc(row["at_utc"]).astimezone(posts.PUBLIC_TZ)
        count = len(row["card_keys"])
        lead = f"Calls from our {at.day} {at:%b %H:%M} ET run: {count}."
        return {"lead": lead, "text": lead + "\n\n" + NOTICES, "conditional_calls": []}
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
        entry = posts._entry_condition(display)
        horizon = row.get("time_exit_utc") or plan.get("valid_until_utc")
        call = {"condition": entry, "direction": plan["direction"], "market": title,
                "horizon": "the period to " + _clock(horizon),
                "invalidation": f"price moves {side} {level(plan['invalidation_level'], plan)}"}
        calls = [call]
        lead = f"{identity} · {direction} idea\n" + conditional_call_text(call)
        extra = []
        target = plan.get("target")
        if target:
            extra.append("Model target level: " + "–".join(dict.fromkeys(level(v, plan) for v in target)) + ".")
        if row.get("entry_deadline_utc"):
            extra.append("Entry window to " + _clock(row["entry_deadline_utc"]) + ".")
        extra.append("Time exit: " + _clock(horizon) + ".")
        if plan.get("chance_pct") is not None:
            extra.append(f"{plan['chance_label']}: {plan['chance_pct']:g}% (Capital Chronicle model estimate).")
        if row.get("price_basis") == "plan":
            extra.append("Levels use the plan's prices.")
        if row.get("state") in {"TRIGGERED", "FILLED"}:
            extra.append("The model position is open.")
    else:
        prefix = f"{title} {direction} of {day.day} {day:%b} ({identity}): "
        extra = []
        if kind == "result":
            lead = prefix + ending_words(row) + f". Ended {_clock(row['at_utc'])}."
        elif row["state"] in {"TRIGGERED", "FILLED"}:
            lead = prefix + f"an entry filled at {_clock(row['at_utc'])}; the model position is open."
        else:
            lead = prefix + f"state changed at {_clock(row['at_utc'])}."
    lines = [lead, *extra, *("• " + reason for reason in row.get("reasons") or [])]
    if row.get("record_line"):
        lines.append(row["record_line"])
    text = "\n".join(lines) + "\n\n" + NOTICES
    check_publication_copy({"body": text}, conditional_calls=calls)
    return {"lead": lead, "text": text, "conditional_calls": calls, "detail_lines": extra}


def ending_words(row):
    if row.get("triggered_not_traded"):
        return "triggered, not traded"
    if row.get("untriggered"):
        direction = row.get("direction_correct")
        return ("not triggered; price then went our way" if direction is True else
                "not triggered; price then went against us" if direction is False else "not triggered")
    if row.get("result") == "HIT":
        return "hit its target"
    if row.get("result") == "STOPPED":
        return "stopped at its invalidation level"
    if row.get("result") == "EXPIRED":
        side = row.get("direction_correct")
        return "closed at its time exit" + (", on our side of the entry" if side is True else
                                             ", against our entry" if side is False else "")
    return "ended"


def _result_rows(export, source_rows):
    result = []
    events = export["transitions"].get("transitions", [])
    for raw in export["status"].get("plans", []):
        if raw.get("asset_id") not in posts.MARKETS:
            continue
        outcome = raw.get("outcome") or {}
        score = outcome.get("score") or {}
        ended = [e for e in events if e.get("plan_id") == raw["plan_id"] and e.get("status") in TERMINAL]
        scored = outcome.get("state") == "SCORED" and bool(score)
        if not scored and not ended:
            continue
        if scored and (score.get("plan_id") != raw["plan_id"] or score.get("asset_id") != raw["asset_id"]
                       or score.get("outcome_id") != outcome.get("outcome_id")):
            raise posts.PlanPostError("PLAN_RESULT_SCORE_BINDING_INVALID")
        at = score.get("resolved_at_utc") if scored else max(ended, key=lambda e: posts._utc(e["at_utc"]))["at_utc"]
        untriggered = (outcome.get("state") in {"NOT_SCORED_UNTRIGGERED", "SCORED_UNTRIGGERED"}
                       or score.get("triggered") is False or score.get("result") == "NOT_TRIGGERED"
                       or (not scored and not any(e.get("plan_id") == raw["plan_id"]
                           and e.get("status") in {"TRIGGERED", "FILLED"} for e in events)))
        correction = score.get("corrects_outcome_id")
        identity = f"{raw['plan_id']}|RESULT" + (f"|{score.get('outcome_id')}" if correction else "")
        result.append({"key": "plan-result-post-" + hashlib.sha256(identity.encode()).hexdigest()[:32],
            "plan_id": raw["plan_id"], "symbol": raw["asset_id"], "to": "RESULT", "at_utc": at,
            "kind": "result", "untriggered": untriggered,
            "triggered_not_traded": score.get("execution_state") == "TRIGGERED_NOT_TRADED"
                or outcome.get("first_cause") == "TRIGGERED_NOT_TRADED",
            "direction_correct": score.get("direction_correct", score.get("went_our_way")),
            "result": outcome.get("result") or score.get("result") or "NOT_TRIGGERED",
            "scored": scored, "outcome_id": outcome.get("outcome_id"),
            "corrects_outcome_id": correction, "score_hash": score.get("content_hash")})
    return result


def queue_posts(store, export_dir, *, now, window_minutes=60, dry_run=False, **reader):
    try:
        export = posts.read_export(export_dir, **reader)
        freshness = posts.export_freshness(export, now)
        if freshness["export_age_seconds"] > posts.EXPORT_MAX_AGE_MINUTES * 60:
            return {"status": "EXPORT_STALE", "cause": posts.STALE_EXPORT, **freshness}
        source_rows = posts.rows_from_export(export, include_results=False)
        sources = {p["plan_id"]: p for p in export["status"].get("plans", []) if p.get("asset_id") in posts.MARKETS}
        records = record_line(export["status"])
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {"status": "EXPORT_UNREADABLE", "cause": str(exc) if isinstance(exc, posts.PlanPostError) else type(exc).__name__}
    existing_rows = store.list_outbox_messages(destination=posts.DESTINATION)
    prior = {r["message_id"]: r for r in existing_rows}
    cards = {}
    for r in existing_rows:
        p = json.loads(r["payload"])
        p.setdefault("key", r["message_id"])
        if p.get("kind") == "setup" or (p.get("state") == "WAITING" and not p.get("why_follow_up")):
            if r["status"] in {posts.READY, "PUBLISHING", "PUBLISHED"}:
                cards.setdefault(p.get("plan_id"), p)
    latest = {}
    for row in sorted(source_rows, key=lambda r: posts._utc(r["at_utc"])):
        if row["symbol"] in posts.MARKETS:
            latest[row["plan_id"]] = row
    payloads, skipped, already = [], [], []

    def payload(row, kind):
        raw = sources[row["plan_id"]]
        plan = card_plan(raw)
        item = {"schema_version": posts.SCHEMA, "format": FORMAT, "key": row["key"],
                "plan_id": row["plan_id"], "symbol": row["symbol"], "state": row["to"], "kind": kind,
                "at_utc": row["at_utc"], "levels": plan, "short_id": plan["short_id"],
                "instrument_title": posts._instrument_title(row["symbol"], plan),
                "price_basis": plan.get("price_basis"), "record_line": records,
                "registered_at_utc": plan.get("registered_at_utc") or row["at_utc"],
                "time_exit_utc": plan.get("time_exit_utc"), "entry_deadline_utc": plan.get("entry_deadline_utc"),
                "source_content_hash": export["status"].get("content_hash"),
                "source_plan_hash": raw.get("registration_hash"), "reasons": []}
        return item

    groups = {}
    for pid, row in latest.items():
        if pid in cards or row["to"] not in posts.ACTIVE or row.get("superseded_by_fill"):
            continue
        raw = sources[pid]
        until = card_plan(raw).get("time_exit_utc")
        if (not until or now >= posts._utc(until)
                or not 0 <= (now - posts._utc(row["at_utc"])).total_seconds() <= posts.LATE_STATE_HOURS * 3600):
            continue
        item = payload(row, "setup")
        if any(item["levels"].get(k) is None for k in ("zone_low", "zone_high", "invalidation_level", "direction")):
            skipped.append({"key": row["key"], "cause": "PLAN_CARD_CONDITIONAL_LEVELS_MISSING"})
            continue
        # A producer run id groups its calls across repeated minute invocations.
        # Older exports still work: the current consumer run owns their group.
        run = raw.get("run_id") or export["status"]["generated_at_utc"]
        run_key = "plan-run-post-" + _hash(run)[:32]
        item.update(parent_key=run_key, run_key=run_key)
        groups.setdefault(run_key, []).append(item)

    for run_key, members in groups.items():
        for item in members:
            source = _reason_source(sources[item["plan_id"]])
            proposed = source_reasons(sources[item["plan_id"]])
            item["reasons"] = checked_reasons(proposed, source)
            item["reasons_cause"] = None if item["reasons"] else "PUBLIC_REASONS_NOT_SUPPLIED_OR_NUMBER_MISMATCH"
            item.update(compose(item))
        if run_key not in prior:
            run = {"schema_version": posts.SCHEMA, "format": FORMAT, "key": run_key, "kind": "run",
                   "symbol": "MULTI", "plan_id": run_key, "state": "RUN", "at_utc": min(m["at_utc"] for m in members),
                   "card_keys": [m["key"] for m in members], "source_content_hash": export["status"].get("content_hash")}
            run.update(compose(run))
            payloads.append(run)
        payloads.extend(members)
        cards.update({m["plan_id"]: m for m in members})

    for row in sorted(source_rows + _result_rows(export, source_rows), key=lambda r: posts._utc(r["at_utc"])):
        pid = row["plan_id"]
        if pid not in sources or row["to"] in {"WAITING", *TERMINAL}:
            continue
        if row["key"] in prior:
            already.append(row["key"])
            continue
        card = cards.get(pid)
        if not card:
            skipped.append({"key": row["key"], "cause": "PLAN_NEVER_ANNOUNCED"})
            continue
        if row["key"] == card["key"] or row.get("superseded_by_fill"):
            continue
        kind = "result" if row["to"] == "RESULT" else "update"
        item = payload(row, kind)
        if kind == "result":
            item.update({k: v for k, v in row.items() if k not in {"key", "plan_id", "symbol", "to", "at_utc", "kind"}})
        item.update(parent_key=card["key"], card_key=card["key"], run_key=card.get("run_key"))
        # Later posts preserve the exact card's public identity, rather than a
        # newly supplied alias or revised short id.
        item["short_id"] = card.get("short_id", item["short_id"])
        item.update(compose(item))
        payloads.append(item)

    queued = []
    for item in payloads:
        if item["key"] in prior:
            already.append(item["key"])
            continue
        if not dry_run:
            store.create_work_item(story_id=posts.WORK_ITEM_ID, title="Call cards and their threads",
                                   target_surface="MULTI_PLATFORM", work_item_id=posts.WORK_ITEM_ID)
            store.register_outbox_message(message_id=item["key"], work_item_id=posts.WORK_ITEM_ID,
                destination=posts.DESTINATION, payload=json.dumps(item, sort_keys=True, ensure_ascii=False), status=posts.READY)
        queued.append({k: item[k] for k in ("key", "symbol", "state", "kind", "at_utc", "text")})
    return {"status": "OK", "dry_run": dry_run, "format": FORMAT, **freshness,
            "max_export_age_minutes": posts.EXPORT_MAX_AGE_MINUTES, "transitions_read": len(source_rows),
            "latest_states": {p: r["to"] for p, r in latest.items()}, "active_recoveries": {},
            "would_queue" if dry_run else "queued": queued, "already_queued": already, "not_posted": skipped}


def _reference(store, key, destination):
    from .publication_coordinator_v1 import DurablePublicationCoordinator
    plan_hash = hashlib.sha256(("plan-status-post:" + key).encode()).hexdigest()
    ids = DurablePublicationCoordinator._ids(key, plan_hash, destination)
    row = store.get_platform_dispatch(ids["dispatch_id"])
    if row and row["status"] == "DISPATCH_CONFIRMED" and row.get("public_object_id"):
        return {k: row.get(k) for k in ("public_object_id", "public_object_url", "dispatch_id")}
    return None


def _parents(store, row, destinations, previous):
    parents = dict(previous or {})
    deferred = []
    for destination in destinations:
        if destination in parents or not row.get("parent_key"):
            continue
        ref = _reference(store, row["parent_key"], destination)
        if not ref:
            deferred.append({"destination": destination, "cause": "CARD_PARENT_NOT_CONFIRMED",
                             "parent_key": row["parent_key"]})
            continue
        parent = {**ref, "parent_key": row["parent_key"]}
        if destination == "discord":
            root = _reference(store, row.get("run_key") or row["parent_key"], destination)
            if not root:
                deferred.append({"destination": destination, "cause": "RUN_PARENT_NOT_CONFIRMED"})
                continue
            parent["thread_parent_id"] = root["public_object_id"]
            parent["thread_parent_url"] = root.get("public_object_url")
        parents[destination] = parent
    return parents, deferred


def destination_payloads(row, *, card_id, parents=None):
    result = {}
    limits = {"telegram": 1024, "discord": 2000, "threads": 500,
              "facebook_page": 60000, "instagram_business": 2200, "substack_notes": 10000}
    for destination in DESTINATIONS:
        text = row["text"]
        room = limits[destination] - len(NOTICES) - 2
        body = text.split("\n\n", 1)[0]
        if len(body) > room:
            # The full card image retains every supplied field. Short copies
            # keep the conditional call, its id and the structured levels first.
            body = row["lead"]
            for line in row.get("detail_lines") or []:
                if len(body) + len(line) + 1 <= room:
                    body += "\n" + line
            for line in (row.get("record_line"), *("• " + r for r in row.get("reasons") or [])):
                if line and len(body) + len(line) + 1 <= room:
                    body += "\n" + line
            text = body + "\n\n" + NOTICES
        if len(text) > limits[destination]:
            raise posts.PlanPostError("PLAN_CARD_COPY_TOO_LONG:" + destination)
        check_publication_copy({"body": text}, conditional_calls=row.get("conditional_calls") or [])
        payload = {"destination": destination, "text": text, "full_text": text,
                   "media_asset_ids": [card_id]}
        ref = (parents or {}).get(destination)
        if ref:
            if destination in {"telegram", "threads"}:
                payload.update(reply_to_id=str(ref["public_object_id"]), reply_to_url=ref.get("public_object_url"))
            elif destination == "discord":
                payload.update(discord_thread_parent_id=str(ref["thread_parent_id"]),
                    discord_thread_name="Calls · " + _clock(row["registered_at_utc"]),
                    **({"reply_to_id": str(ref["public_object_id"])} if row["kind"] != "setup" else {}))
            elif destination in {"facebook_page", "instagram_business"}:
                if row["kind"] != "setup":
                    payload.update(reply_to_id=str(ref["public_object_id"]),
                                   reply_to_url=ref.get("public_object_url"), own_call_comment=True)
            elif destination == "substack_notes":
                payload.update(reply_to_id=str(ref["public_object_id"]), reply_to_url=ref.get("public_object_url"))
        result[destination] = payload
    return result


def prepare_post(store, key, *, root, host=None, destinations=DESTINATIONS, **ignored):
    from .capital_chronicle_latest_report_consumer_v1 import canonical_bytes
    from .destination_transport_registry_v1 import REGISTRY_VERSION, registration_for_destination
    from .plan_call_card_media_v1 import render
    row = posts._row_payload(store, key)
    folder = Path(root) / key
    context_path = folder / "run_context_v1.json"
    previous = json.loads(context_path.read_bytes()) if context_path.is_file() else {}
    parents, deferred = _parents(store, row, destinations, previous.get("status_post_parents"))
    chosen = [d for d in destinations if not row.get("parent_key") or d in parents]
    if not chosen:
        return {"destinations": [], "deferred_destinations": deferred, "output_dir": str(folder.resolve())}
    existing_assets = (previous.get("media") or {}).get("assets") or []
    card = existing_assets[0] if existing_assets else render(row, folder)
    if not Path(card["path"]).is_file() or hashlib.sha256(Path(card["path"]).read_bytes()).hexdigest() != card["sha256"]:
        raise posts.PlanPostError("PLAN_CARD_IMAGE_BYTES_CHANGED")
    title = (row["lead"] if row["kind"] == "run" else
             f"{row['instrument_title']} · #{row['short_id']} · "
             + (ending_words(row) if row["kind"] == "result" else "call card" if row["kind"] == "setup" else "update"))
    article = {"title": title, "dek": row["lead"], "body": row["text"],
               "author_identity": "Capital Chronicle", "publisher_identity": "Capital Chronicle"}
    manifest_path = folder / "delivery_media_manifest_v1.json"
    if not posts._hosted(manifest_path, card):
        if host is None:
            from .cloudinary_delivery_media_v1 import prepare_cloudinary_delivery_media as host
        delivery = host(work_item_id=key, delivery_only_assets=[card], existing_manifest=None,
                        article_assets=[], article=article, source_documents=[])
        if delivery.get("status") != "CLOUDINARY_DELIVERY_MEDIA_READY":
            raise posts.PlanPostError("PLAN_STATUS_CARD_HOSTING_" + str(delivery.get("status") or "FAILED"))
        manifest_path.write_bytes(canonical_bytes(delivery["manifest"]))
    context = {"schema_version": "contentops.plan_status_post_context.v1", "article": article,
        "selection": {}, "media": {"assets": [card]}, "plan_status_post": key, "chart_credit": False,
        "status_post_parents": parents}
    context_path.write_bytes(canonical_bytes(context))
    payloads = destination_payloads(row, card_id=card["asset_id"], parents=parents)
    plan_rows = []
    for destination in chosen:
        registration = registration_for_destination(destination)
        text = payloads[destination]["full_text"]
        plan_rows.append({"destination": destination, "platform": registration.platform,
            "surface": registration.surface, "transport_type": registration.transport_type,
            "transport_registry_version": REGISTRY_VERSION, "payload": text,
            "payload_hash": hashlib.sha256(text.encode()).hexdigest(), "canonical_url": None,
            "expected_destination_identity": registration.expected_identity})
    return {"schema_version": "contentops.publication_plan.v1", "plan_status_post": key,
        "plan_hash": hashlib.sha256(("plan-status-post:" + key).encode()).hexdigest(),
        "story_identity": key, "article_identity": key, "package_identity": key,
        "publication_window": {"window_identity": key}, "output_dir": str(folder.resolve()),
        "status_post_card_id": card["asset_id"], "transport_registry_version": REGISTRY_VERSION,
        "policy_mode_version": "AUTONOMOUS_DEFAULT:cc399.v1", "destinations": plan_rows,
        "continuations": [], "deferred_destinations": deferred}


def validate_parent_intent(store, row, intent):
    destination = intent["destination_plan"]["destination"]
    if not row.get("parent_key"):
        return
    ref = _reference(store, row["parent_key"], destination)
    payload = intent["native_payload"]
    if not ref:
        raise posts.PlanPostError("CARD_PARENT_NOT_CONFIRMED")
    reply_destination = destination in {"telegram", "threads", "substack_notes"} or (
        destination in {"facebook_page", "instagram_business"} and row["kind"] != "setup")
    if reply_destination and str(ref["public_object_id"]) != payload.get("reply_to_id"):
        raise posts.PlanPostError("PLAN_CARD_REPLY_PARENT_CHANGED")
    if destination == "discord":
        root = _reference(store, row.get("run_key") or row["parent_key"], destination)
        if not root or str(root["public_object_id"]) != payload.get("discord_thread_parent_id"):
            raise posts.PlanPostError("PLAN_CARD_DISCORD_THREAD_CHANGED")
        if row["kind"] != "setup" and str(ref["public_object_id"]) != payload.get("reply_to_id"):
            raise posts.PlanPostError("PLAN_CARD_REPLY_PARENT_CHANGED")


def readback_own_comment(destination, comment_id, parent_id, text):
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
        data = adapter._get_json(f"https://graph.facebook.com/{adapter.GRAPH_VERSION}/{parent_id}/comments",
                                {"access_token": token, "fields": f"id,{field}", "limit": 100})
        match = next((r for r in data.get("data") or [] if str(r.get("id")) == str(comment_id)), None)
        verified = bool(match and match.get(field) == text)
        return {"status": "SUCCESS" if verified else "READBACK_UNAVAILABLE", "verified": verified,
                "public_object_id": comment_id, "body_text_visible": verified, "reply_parent_verified": bool(match)}
    except Exception as exc:
        return {"status": "READBACK_UNAVAILABLE", "verified": False,
                "safe_error_classification": type(exc).__name__}


def publish_ready(store, *, now, latest_states=None, root, host=None, coordinator_for=None, limit=5):
    if coordinator_for is None:
        def coordinator_for(key, folder):
            from .native_neo_executor_v1 import bind_native_neo_coordinator
            return bind_native_neo_coordinator(store, operation_id=key, output_dir=folder / "native-neo",
                native_invocation_id="plan-status-posts-cc399", allow_publish=True)[0]
    pending = []
    for outbox in store.list_outbox_messages(destination=posts.DESTINATION):
        row = json.loads(outbox["payload"])
        if row.get("format") == FORMAT and outbox["status"] in {posts.READY, "PUBLISHING"}:
            pending.append((outbox, row))
    pending.sort(key=lambda pair: ({"run": 0, "setup": 1, "update": 2, "result": 3}[pair[1]["kind"]], pair[1]["at_utc"]))
    results, calls = [], 0
    for outbox, row in pending:
        key = row["key"]
        if row["kind"] != "run":
            if calls >= limit:
                break
            calls += 1
        # An unstarted setup cannot be backfilled after its idea has ended.
        # Once a send is uncertain, the coordinator owns recovery of its exact
        # immutable bytes. Later state/ending records remain owed.
        if row["kind"] == "setup" and outbox["status"] == posts.READY:
            current = (latest_states or {}).get(row["plan_id"])
            if (current in TERMINAL or current == "RESULT"
                    or (row.get("time_exit_utc") and now >= posts._utc(row["time_exit_utc"]))):
                store.set_outbox_status(key, posts.SUPERSEDED)
                results.append({"key": key, "status": posts.SUPERSEDED, "cause": "PLAN_ALREADY_ENDED"})
                continue
        try:
            plan = prepare_post(store, key, root=root, host=host)
            if not plan["destinations"]:
                results.append({"key": key, "status": "WAITING_FOR_CARD_PARENT",
                                "deferred_destinations": plan["deferred_destinations"]})
                continue
            store.create_work_item(story_id=key, title="Call run" if row["kind"] == "run" else "Call card",
                                   target_surface="MULTI_PLATFORM", work_item_id=key)
            coordinator = coordinator_for(key, Path(plan["output_dir"]))
            posts.scope_to_post(coordinator, key, plan)
            coordinator.register_plan(key, plan)
            outcome = coordinator.execute_plan(key, plan)
            states = {d: (o or {}).get("status") for d, o in (outcome.get("per_destination") or {}).items()}
            confirmed = {d for d in DESTINATIONS if _reference(store, key, d)}
            done = len(confirmed) == len(DESTINATIONS)
            store.set_outbox_status(key, "PUBLISHED" if done else "PUBLISHING")
            results.append({"key": key, "status": "PUBLISHED" if done else "PUBLISHING",
                "per_destination": states, "confirmed_destinations": sorted(confirmed),
                "deferred_destinations": plan["deferred_destinations"]})
        except (OSError, ValueError, KeyError, TypeError) as exc:
            results.append({"key": key, "status": "NOT_STARTED", "cause": str(exc)[:200]})
    return {"status": "OK", "posts": results}
