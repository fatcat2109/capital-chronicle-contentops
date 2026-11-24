"""CC-603: dated corrections and resolved public calls in the existing post outbox.

Main owns trade scores. Held prices check what a published sentence actually said.
CR's explicitly approved view reports never turn an untraded entry into a hit.
The existing minute entry, store and DurablePublicationCoordinator own delivery.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import sqlite3

from . import plan_status_posts_v1 as posts
from . import pinned_result_scorecard_v1 as scorecard

CONTRACT = "CC603_V1"
LINK_REPLY = "missing_links_reply"
CR_CALLS = frozenset("a0380280 d7eddc84 576f57e9 52a48ae1 8479dce1 acc5894c 5a6538c6 5820e1f7 ddf94be7 0bf2a58c 106875eb".split())
ZONE_CORRECTION = "cc359-zone-correction-20261109"
GOLD_CORRECTION = "cc603-gold-timing-correction-20261112"
GOLD_ORIGINAL = "plan-status-post-37f4a7ca63df69d5864655fbe2494bae"
GOLD_PLAN = "plan_230a9464a193ca7a377d0c41"
GOLD_URL = "https://capitalchronicle.substack.com/p/gold-our-bearish-plan-39543964-entry"
BAR_STORE = Path(r"A:\Capital Chronicle\Runtime\OfficialRates\cc-078-20261101\state\intake\completed-bars\bars.sqlite3")
ROOT = posts.POST_ROOT.parent / "call-followups"
EVENT_OUTCOMES = Path(r"A:\Capital Chronicle\ResearchRuns\main-event-forecast-scores\outcomes")
_PRIVATE = re.compile(r"\b(?:targets?|demo|model|AI|profit|money|lots?|account|P&L)\b", re.I)


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)


def _hash(value):
    return sha256(_json(value).encode()).hexdigest()


def publications(store, key):
    """Confirmed objects only. A queued/absent X copy is never an original."""
    return [{"destination": d["platform"], "id": d["public_object_id"],
             "url": d.get("public_object_url"), "at_utc": d["dispatched_at"],
             "clock_basis":"CONFIRMED_DISPATCH_CLOCK"}
            for d in store.get_dispatches_for_work_item(key)
            if d["status"] == "DISPATCH_CONFIRMED" and d.get("public_object_id")]


def read_bars(symbol, start, end, *, path=BAR_STORE):
    """One held source per complete M15 bar; conflicting observations are refused."""
    with sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT open_epoch,open,high,low,close,source_sha256,known_epoch,price_basis,series_id "
            "FROM bars WHERE symbol=? AND series_id='NATIVE_BROKER' AND open_epoch>=? AND open_epoch+900<=? ORDER BY open_epoch,known_epoch",
            (symbol, posts._utc(start).timestamp(), posts._utc(end).timestamp())).fetchall()
    selected = {}
    for raw in rows:
        row = dict(raw)
        previous = selected.get(row["open_epoch"])
        if previous and any(previous[k] != row[k] for k in ("open", "high", "low", "close")):
            raise ValueError("CC603_CONFLICTING_HELD_PRICE_BAR")
        selected[row["open_epoch"]] = row
    return list(selected.values())


def check_path(candidate, bars):
    """Check the whole condition and horizon. Invalidation wins a same-bar tie.

    No return is computed. Entry and resolution in one bar cannot establish an
    as-written hit; a direction-only move is explicitly a separate CR view report.
    """
    start = posts._utc(candidate["published_at_utc"])
    if candidate.get("source_kind") == "ARTICLE" and candidate.get("condition_met") is not True:
        return {"eligible":False,"cause":"CC603_ARTICLE_CONDITION_NOT_MET"}
    if candidate.get("condition_at_utc"):
        start = max(start,posts._utc(candidate["condition_at_utc"]))
    end = posts._utc(candidate["valid_until_utc"])
    direction = candidate["direction"]
    if direction not in {"bullish", "bearish"} or start >= end:
        return {"eligible": False, "cause": "CC603_ORIGINAL_AFTER_PLAN_LIFE"}
    entered = int(start.timestamp()) if candidate.get("entry_condition_kind") == "EVENT" else None
    previous = None
    first = None
    evidence = []
    for bar in bars:
        at = datetime.fromtimestamp(bar["open_epoch"], timezone.utc)
        if at <= start or at + timedelta(minutes=15) > end:
            continue
        expected_first = (int(start.timestamp()) // 900 + 1) * 900
        if first is None and bar["open_epoch"] != expected_first:
            return {"eligible": False, "cause": "CC603_HELD_PRICE_GAP_AFTER_PUBLICATION"}
        if previous is not None and bar["open_epoch"] != previous + 900:
            return {"eligible": False, "cause": "CC603_HELD_PRICE_GAP"}
        previous = bar["open_epoch"]
        first = first or bar
        evidence.append({k: bar[k] for k in ("open_epoch", "source_sha256")})
        invalidation = candidate["invalidation"]
        field = invalidation["field"]
        if field not in {"high", "low", "close"}:
            raise ValueError("CC603_INVALIDATION_FIELD_UNSUPPORTED")
        wrong = (bar[field] >= invalidation["level"] if invalidation["side"] == "above"
                 else bar[field] <= invalidation["level"])
        if wrong and candidate.get("invalidation_test") != "AT_DEADLINE":
            return {"eligible": False, "cause": "CC603_INVALIDATION_FIRST"}
        if entered is None and bar["low"] <= candidate["zone_high"] and bar["high"] >= candidate["zone_low"]:
            entered = bar["open_epoch"]
        deadline_test = candidate.get("resolution_test") == "AT_DEADLINE"
        value = bar["close"] if deadline_test else bar["low" if direction == "bearish" else "high"]
        reached = ((value <= candidate["resolution_level"] if direction == "bearish"
                    else value >= candidate["resolution_level"])
                   and (not deadline_test or at+timedelta(minutes=15) == end))
        if not reached:
            continue
        resolved = at + timedelta(minutes=15)
        kind = candidate["source_kind"]
        if kind != "CR_VIEW" and (entered is None or entered == bar["open_epoch"]):
            return {"eligible": False, "cause": "CC603_CONDITION_NOT_PROVEN_BEFORE_MOVE"}
        if kind == "CR_VIEW":
            if candidate.get("short_id") not in CR_CALLS:
                return {"eligible": False, "cause": "CC603_VIEW_NOT_IN_APPROVED_CR_SET"}
            total_move = abs(candidate["reference_price"] - candidate["resolution_level"])
            remaining = ((first["open"] - candidate["resolution_level"]) if direction == "bearish"
                         else (candidate["resolution_level"] - first["open"]))
            if total_move <= 0 or remaining < total_move / 2 or (resolved - start).total_seconds() < 3600:
                return {"eligible": False, "cause": "CC603_MOVE_PRECEDED_ORIGINAL"}
        return {"eligible": True, "entry_traded": entered is not None,
                "resolved_at_utc": resolved.isoformat(), "bar_open_at_utc": at.isoformat(),
                "first_price": first["open"], "observed_price": value if deadline_test else candidate["resolution_level"],
                "bars_sha256": _hash(evidence), "bar_count": len(evidence),
                "evidence": evidence}
    return {"eligible": False, "cause": "CC603_NO_COMPLETE_MATCH_IN_HELD_PRICES"}


def observed_record(store, *, api=None, now=None):
    """Read the pinned object, rather than borrow counts from an older projection."""
    now = now or datetime.now(timezone.utc)
    revisions = store.list_outbox_messages(destination=scorecard.DESTINATION)
    confirmed = [r for r in revisions if r["status"] == "CONFIRMED"]
    if not confirmed:
        raise ValueError("CC603_PINNED_RECORD_NOT_CONFIRMED")
    held = json.loads(confirmed[-1]["payload"])
    obj = store.get_outbox_message(scorecard.OBJECT)
    identity = json.loads(obj["payload"]) if obj else {}
    chat = (api or scorecard.TelegramScorecardAPI()).call("getChat")
    pinned = chat.get("pinned_message") or {}
    if (chat.get("username", "").casefold() != "capitalchronicle" or chat.get("type") != "channel"
            or str(pinned.get("message_id")) != str(identity.get("message_id"))
            or pinned.get("text") != held["text"]):
        raise ValueError("CC603_PINNED_RECORD_READBACK_MISMATCH")
    counts = held["counts"]
    line = (f"Pinned call record: {counts['HIT']} hits, {counts['STOPPED']} stopped, "
            f"{counts['EXPIRED']} expiries; {counts['total']} results, {counts['scored']} scored.")
    return {"line": line, "counts": counts, "url": identity["public_url"],
            "text_sha256": sha256(held["text"].encode()).hexdigest(),
            "observed_at_utc": now.isoformat()}


def refresh_record(store, row, *, now=None):
    """A follow-up not yet registered for any destination carries the pinned record as it reads now.

    Builder L's relaunch rehearsal (24 Nov 2026): each prepared follow-up froze the record line it was prepared
    with. The relaunch's first scorecard update (results scored inside Jim's pause) changed the counts, and
    validate_intent then refused every follow-up with CC603_PUBLIC_RECORD_CHANGED_BEFORE_WRITE, on every run.
    Before any destination copy exists, the row's record and its one record line are replaced; afterwards the
    copies are frozen and the write check stays as it was.
    """
    if row.get("kind") != "call_followup" or not isinstance(row.get("record"), dict):
        return row
    key = row["key"]
    if store.get_dispatches_for_work_item(key) or any(
            m["message_id"] != key for m in store.list_outbox_messages(work_item_id=key)):
        return row
    current = observed_record(store, now=now)
    held = row["record"]
    if current["counts"] == held.get("counts") and current["url"] == held.get("url"):
        return row
    if not held.get("line") or row["text"].count(held["line"]) != 1:
        return row  # the write check names the cause
    stored = store.get_outbox_message(key)
    refreshed = {**row, "record": current, "text": row["text"].replace(held["line"], current["line"])}
    store.finalize_outbox_payload_before_dispatch(message_id=key, payload=_json(refreshed),
        status=stored["status"], expected_payload=stored["payload"])
    return posts._row_payload(store, key)


def corrections_complete(store):
    for key in (ZONE_CORRECTION, GOLD_CORRECTION):
        row = store.get_outbox_message(key)
        if not row:
            return False
        value = json.loads(row["payload"])
        if not post_complete(store,value,key=key):
            return False
    return True


def post_complete(store,row,*,key=None):
    key = key or row["key"]
    def complete_destinations(work):
        reconciled = {r['reconciliation_id'] for r in store.get_reconciliations_for_work_item(work)
                      if r['status'] == 'RECONCILED_CONFIRMED'}
        return {d['platform'] for d in store.get_dispatches_for_work_item(work)
                if d['status'] == 'DISPATCH_CONFIRMED' and d.get('public_object_id') and d.get('public_object_url')
                and 'reconciliation_'+d['dispatch_id'].removeprefix('dispatch_') in reconciled}
    required = row.get("cc603_destinations") or posts.API_DESTINATIONS
    completed = complete_destinations(key)
    # Ops Product, 16 Nov: a dropped line is supplied once in the same thread,
    # never by editing/reposting the call. Keep the root's incomplete readback.
    if set(required) - completed == {"substack_notes"}:
        held = store.get_outbox_message(key + "-missing-links")
        if held:
            reply = json.loads(held["payload"])
            try:
                validate_link_reply(store, reply)
                if post_complete(store, reply):
                    completed.add("substack_notes")
            except (ValueError, KeyError):
                pass
    if not set(required) <= completed:
        return False
    if row.get("cc603_contract"):
        for destination,payload in destination_payloads(row,card_id="bound-image",chart_credit=True).items():
            for part in range(1,len(payload.get("parts") or [])):
                if destination not in complete_destinations(f"{key}-part-{part}"):
                    return False
    return True


def _save_post(store, row):
    existing = store.get_outbox_message(row["key"])
    if existing:
        return json.loads(existing["payload"])
    store.create_work_item(story_id=row["key"], work_item_id=row["key"],
                           title=row["title"], target_surface="MULTI_PLATFORM")
    store.register_outbox_message(message_id=row["key"], work_item_id=row["key"],
        destination=posts.DESTINATION, payload=_json(row), status="CC603_PREPARED")
    return row


def validate_link_reply(store, row):
    """A text-only continuation can supply links, never replace missing facts/media."""
    from .neo_destination_handoff_v1 import _text
    parent = row["link_reply_parent"]
    original = posts._row_payload(store, parent["key"])
    if (row.get("kind") != LINK_REPLY or row.get("cc603_destinations") != ["substack_notes"]
            or row.get("key") != parent["key"] + "-missing-links"
            or original.get("kind") != "call_followup" or original.get("cc603_contract") != CONTRACT
            or _hash(original) != parent["row_sha256"]):
        raise ValueError("CC603_LINK_REPLY_PARENT_CHANGED")
    dispatch = store.get_platform_dispatch(parent["dispatch_id"]) or {}
    if (dispatch.get("message_id") != parent["message_id"] or dispatch.get("platform") != "substack_notes"
            or dispatch.get("status") != "DISPATCH_CONFIRMED"
            or dispatch.get("public_object_id") != parent["public_object_id"]
            or dispatch.get("public_object_url") != parent["public_object_url"]):
        raise ValueError("CC603_LINK_REPLY_EXACT_PARENT_REQUIRED")
    readback = next((r for r in store.list_readbacks_for_dispatch(parent["dispatch_id"])
                     if r["readback_id"] == parent["readback_id"]), None)
    observed = json.loads(readback["readback_data"])["readback"] if readback else {}
    checks = observed.get("content_binding_checks") or {}
    if (not observed.get("write_exists") or not observed.get("identity_match")
            or observed.get("observed_public_object_id") != parent["public_object_id"]
            or observed.get("observed_public_object_url") != parent["public_object_url"]
            or not observed.get("meaningful_media_visible") or checks.get("media_match") is not True
            or checks.get("thread_match") is not True):
        raise ValueError("CC603_LINK_REPLY_ILLUSTRATED_PARENT_READBACK_REQUIRED")
    urls = [original["candidate"]["original_url"], original["record"]["url"]]
    expected = destination_payloads(original, card_id="parent-chart", chart_credit=True)["substack_notes"]["full_text"]
    for url in urls:
        expected = expected.replace(url, "")
    if _text(expected) != _text(parent["observed_text"]):
        raise ValueError("CC603_LINK_REPLY_OTHER_CONTENT_MISSING")
    text = f"Original: {urls[0]}\nRecord: {urls[1]}\n\n{posts.PUBLIC_NOTICE} {posts.CONFLICTS_NOTICE}"
    if row.get("text") != text:
        raise ValueError("CC603_LINK_REPLY_COPY_CHANGED")
    return parent


def queue_missing_links_reply(store, key, *, observed_text, now=None):
    """One durable reply to an identified Note whose only dropped text is its URLs."""
    reply_key = key + "-missing-links"
    if store.get_outbox_message(reply_key):
        return {"status": "EXISTING", "key": reply_key}
    original = posts._row_payload(store, key)
    parents = [d for d in store.get_dispatches_for_work_item(key)
               if d["platform"] == "substack_notes" and d.get("public_object_id")]
    if len(parents) != 1:
        raise ValueError("CC603_LINK_REPLY_EXACT_PARENT_REQUIRED")
    parent = parents[0]
    readbacks = store.list_readbacks_for_dispatch(parent["dispatch_id"])
    if not readbacks:
        raise ValueError("CC603_LINK_REPLY_ILLUSTRATED_PARENT_READBACK_REQUIRED")
    urls = [original["candidate"]["original_url"], original["record"]["url"]]
    row = {"schema_version": posts.SCHEMA, "cc603_contract": CONTRACT, "key": reply_key,
        "kind": LINK_REPLY, "symbol": original["symbol"], "state": "FOLLOW_UP",
        "at_utc": (now or datetime.now(timezone.utc)).isoformat(),
        "title": "Links to the original call and pinned record", "conditional_calls": [],
        "text": f"Original: {urls[0]}\nRecord: {urls[1]}\n\n{posts.PUBLIC_NOTICE} {posts.CONFLICTS_NOTICE}",
        "cc603_destinations": ["substack_notes"], "counts_as_article": False, "new_post_only": True,
        "authority": "CC-603; Ops Product 16 Nov; Jim decisions 136 and 84: reply once, no edit",
        "link_reply_parent": {**{k: parent[k] for k in ("dispatch_id", "message_id", "public_object_id", "public_object_url")},
            "key": key, "row_sha256": _hash(original), "readback_id": readbacks[-1]["readback_id"],
            "observed_text": observed_text}}
    validate_link_reply(store, row)
    _save_post(store, row)
    return {"status": "QUEUED", "key": reply_key}


def prepare_gold_correction(store, *, now=None):
    """The second correction is a new object; the first correction already exists."""
    existing = store.get_outbox_message(GOLD_CORRECTION)
    if existing:
        return json.loads(existing["payload"])
    original = posts._row_payload(store, GOLD_ORIGINAL)
    originals = publications(store,GOLD_ORIGINAL)
    # The late analysis link has its own confirmed objects beside the status.
    for destination in posts.POST_DESTINATIONS:
        originals.extend(publications(store,f"plan-analysis-link-{GOLD_PLAN}-{destination}"))
    destinations = sorted({p["destination"] for p in originals})
    if not destinations:
        raise ValueError("CC603_GOLD_ORIGINAL_NOT_PUBLISHED")
    body = ("Correction: our 12 Nov gold analysis and later status post were published after the fall they described. "
            "They were late, and we will not cite them as a call made before the move. "
            "The status post should not have presented the 3,954–3,964 entry zone as a fresh opportunity.\n"
            f"Original analysis: {GOLD_URL}")
    return _save_post(store, {"schema_version": posts.SCHEMA, "cc603_contract": CONTRACT,
        "key": GOLD_CORRECTION, "symbol": "XAUUSD", "state": "CORRECTION", "kind": "correction",
        "at_utc": (now or datetime.now(timezone.utc)).isoformat(), "title": "Correction: our gold posts were late",
        "text": body + "\n\n" + posts.PUBLIC_NOTICE + " " + posts.CONFLICTS_NOTICE,
        "conditional_calls": [], "cc603_destinations": destinations,
        "original_key": GOLD_ORIGINAL, "original_sha256": _hash(original),
        "original_objects": originals,
        "new_post_only": True, "authority": "CC-603; Jim decision 136; Ops Product 14 and 16 Nov"})


def queue_followup(store, candidate, path, record, *, now=None):
    now = now or datetime.now(timezone.utc)
    if not path.get("eligible"):
        return {"status": "NOT_ELIGIBLE", "cause": path["cause"]}
    if not corrections_complete(store):
        return {"status": "CORRECTIONS_PENDING"}
    key = "cc603-followup-" + _hash(candidate["call_id"])[:32]
    existing = store.get_outbox_message(key)
    if existing:
        return {"status": "EXISTING", "key": key}
    # The explicitly named historical CR candidates are an owner-requested backfill.
    if candidate["source_kind"] != "CR_VIEW" and not 0 <= (now-posts._utc(path["resolved_at_utc"])).total_seconds() <= 3600:
        return {"status": "NOT_ELIGIBLE", "cause": "CC603_RESOLUTION_POSTING_WINDOW_PASSED"}
    quote = candidate["quote"]
    if quote not in candidate["original_text"] or _PRIVATE.search(quote):
        raise ValueError("CC603_QUOTE_NOT_EXACT_PUBLIC_TERMS")
    original_at = scorecard._utc(candidate["published_at_utc"]).astimezone(scorecard.ET)
    event_at = posts._utc(path["bar_open_at_utc"]).astimezone(scorecard.ET)
    entry = ("The stated condition and the full price-and-time test were met." if candidate["source_kind"] == "ARTICLE"
             else "The entry zone traded before the move." if path["entry_traded"]
             else "Our entry zone never traded; this was a directional view, with no trade.")
    title = f"{posts.TITLES[candidate['symbol']]}: our earlier view and what followed"
    body = (f"Original, {original_at:%d %b %Y %H:%M} ET: “{quote}”\n"
            f"By the {event_at:%d %b %H:%M} ET price bar, price reached {posts._level(path['observed_price'])}. "
            f"{entry}\nThe price check uses the original plan's prices; the TradingView chart shows the move in its own market feed.\n"
            f"Original: {candidate['original_url']}\n{record['line']}\nRecord: {record['url']}")
    held_followups = [r for r in store.list_outbox_messages(destination=posts.DESTINATION)
                      if r["message_id"].startswith("cc603-followup-")]
    # The live acceptance explicitly names Substack and X for the first post.
    # Keep the actual original destinations separate; never invent an old X object.
    acceptance_destinations = [] if held_followups else ["substack_notes","x"]
    row = {"schema_version": posts.SCHEMA, "cc603_contract": CONTRACT, "key": key,
        "kind": "call_followup", "state": "FOLLOW_UP", "symbol": candidate["symbol"],
        "at_utc": now.isoformat(), "title": title, "text": body + "\n\n" + posts.PUBLIC_NOTICE + " " + posts.CONFLICTS_NOTICE,
        "conditional_calls": [candidate["terms"]], "candidate": candidate, "price_check": path, "record": record,
        "cc603_destinations": sorted(set(candidate["destinations"])|set(acceptance_destinations)),
        "acceptance_destinations": acceptance_destinations, "counts_as_article": False,
        "new_post_only": True, "authority": "CC-603; Jim decision 136; CR amendment 14 Nov"}
    _save_post(store, row)
    return {"status": "QUEUED", "key": key}


def _whole_parts(body, notices, limit, credit=""):
    """Split between complete sentences or lines; never truncate a sentence."""
    parts, current = [], ""
    for line in body.splitlines():
        suffix = "\n\n".join(p for p in (credit if not parts else "",notices) if p)
        room = limit-len(suffix)-(2 if suffix else 0)
        units = [line] if len(line)<=room else re.findall(r".+?(?:[.!?](?=\s|$)|$)",line)
        for unit in units:
            unit=unit.strip()
            if not unit:
                continue
            suffix = "\n\n".join(p for p in (credit if not parts else "",notices) if p)
            room = limit-len(suffix)-(2 if suffix else 0)
            combined = current+"\n"+unit if current else unit
            if len(combined)>room and current:
                parts.append(current+("\n\n"+suffix if suffix else ""))
                current=""
                suffix=notices
                room=limit-len(suffix)-(2 if suffix else 0)
            if len(unit)>room:
                raise ValueError("CC603_COMPLETE_SENTENCE_EXCEEDS_DESTINATION_LIMIT")
            current=(current+"\n"+unit).strip()
    if current:
        suffix="\n\n".join(p for p in (credit if not parts else "",notices) if p)
        parts.append(current+("\n\n"+suffix if suffix else ""))
    return parts


def destination_payloads(row, *, card_id, chart_credit=False):
    """Keep complete sentences and the exact quote. X's own thread is one post object."""
    body, notices = posts._split(row["text"])
    if _PRIVATE.search(body):
        raise ValueError("CC603_PUBLIC_WORDING_FORBIDDEN")
    credit = posts.CHART_CREDIT if chart_credit else ""
    limits = {**posts.LIMITS, "facebook_page": 60000, "instagram_business": 2200, "linkedin": 3000}
    output = {}
    for destination in row["cc603_destinations"]:
        text = "\n\n".join(s for s in (body, credit, notices) if s)
        payload = {"destination": destination, "text": text, "full_text": text,
                   "media_asset_ids": [card_id] if card_id else []}
        if row.get("kind") == LINK_REPLY:
            parent = row["link_reply_parent"]
            payload.update(reply_to_id=parent["public_object_id"], reply_to_url=parent["public_object_url"])
        if destination == "x" and posts._x_length(text) > 280:
            chunks = _whole_parts(body,"",280-(len(credit)+2 if credit else 0))
            if credit:
                chunks[0] += "\n\n" + credit
            chunks.append(notices)
            payload.update(text=chunks[0], full_text="\n\n".join(chunks), root_text=chunks[0],
                reply_texts=chunks[1:], posts=[{"text": t, "order": i, "role": "root" if i == 0 else "reply",
                    "media_asset_ids": [card_id] if card_id and i == 0 else []} for i,t in enumerate(chunks)])
        elif len(text) > limits[destination]:
            payload["parts"] = _whole_parts(body,notices,limits[destination],credit)
        output[destination] = payload
    return output


def validate_intent(store, row, intent):
    """Actual-write facts: no changed original, uncorrected record or invented hit."""
    if row.get("kind") == LINK_REPLY:
        validate_link_reply(store, row)
        return
    if row["kind"] == "correction":
        if _hash(posts._row_payload(store, row["original_key"])) != row["original_sha256"]:
            raise ValueError("CC603_ORIGINAL_BYTES_CHANGED")
        return
    if not corrections_complete(store):
        raise ValueError("CC603_CORRECTIONS_NOT_READ_BACK")
    candidate = row["candidate"]
    if candidate["quote"] not in candidate["original_text"] or not row["price_check"]["eligible"]:
        raise ValueError("CC603_PUBLIC_CLAIM_NOT_VERIFIED")
    if candidate.get("original_key") and candidate.get("original_sha256"):
        if _hash(posts._row_payload(store,candidate["original_key"])) != candidate["original_sha256"]:
            raise ValueError("CC603_ORIGINAL_BYTES_CHANGED")
    current = observed_record(store)
    if current["counts"] != row["record"]["counts"] or current["url"] != row["record"]["url"]:
        raise ValueError("CC603_PUBLIC_RECORD_CHANGED_BEFORE_WRITE")
    context = json.loads((Path(intent["output_dir"])/"run_context_v1.json").read_bytes())
    if not (context.get("media") or {}).get("assets"):
        raise ValueError("CC603_REAL_TRADINGVIEW_MOVE_CHART_REQUIRED")


def discover(store, export):
    """CC-530 HITs and the eleven CR views, joined to their confirmed originals."""
    plans = {p["plan_id"]: p for p in export["status"]["plans"]}
    found = {}
    for message in store.list_outbox_messages(destination=posts.DESTINATION):
        row = json.loads(message["payload"])
        if row.get("kind") != "setup" or not row.get("conditional_calls") or row.get("cc603_contract"):
            continue
        source = plans.get(row.get("plan_id"))
        if not source:
            continue
        outcome = source.get("outcome") or {}
        public_id = outcome.get("public_call_id") or ""
        short_id = (row.get("levels") or {}).get("short_id") or (public_id[5:13] if public_id.startswith("call_") else None)
        kind = "AS_WRITTEN" if outcome.get("state") == "SCORED" and outcome.get("result") == "HIT" else "CR_VIEW"
        if kind == "CR_VIEW" and short_id not in CR_CALLS:
            continue
        objects = publications(store, message["message_id"])
        linked = [p for p in objects if p["url"] and p.get("at_utc")]
        if not linked:
            continue
        # Telegram preserves the exact call sentence, whereas a run carousel
        # can share one Instagram identity across several calls.
        original = min(linked,key=lambda p:(p["destination"] != "telegram",posts._utc(p["at_utc"])))
        terms = row["conditional_calls"][0]
        from .event_article_guard_v1 import (conditional_call_text,reader_conditional_call_text,
            compact_reader_conditional_call_text,thread_reader_conditional_call_text)
        quote = next((render(terms) for render in (conditional_call_text,reader_conditional_call_text,
            compact_reader_conditional_call_text,thread_reader_conditional_call_text) if render(terms) in row["text"]),None)
        if not quote:
            continue  # A different dialect needs its exact public span, never reconstructed words.
        zone = source.get("zone") or {}
        invalidations = source.get("invalidation_conditions") or []
        if not invalidations or source.get("target_level") is None:
            continue
        wrong = invalidations[0]
        candidate = {"call_id": (outcome.get("public_call_id") or source["plan_id"]),
            "plan_id": source["plan_id"], "source_kind": kind, "short_id": short_id,
            "symbol": row["symbol"], "direction": terms["direction"], "quote": quote, "terms": terms,
            "original_key": message["message_id"], "original_text": row["text"],
            "original_sha256": _hash(row),
            "original_url": original["url"], "published_at_utc": original["at_utc"],
            "publication_clock_basis":original["clock_basis"],
            "destinations": sorted({p["destination"] for p in objects}),
            "zone_low": zone.get("minimum"), "zone_high": zone.get("maximum"),
            "resolution_level": source["target_level"],
            "reference_price": (source.get("forecast_probabilities") or {}).get("reference_price"),
            "invalidation": {"field": wrong["field"], "level": wrong["threshold"],
                "side": "above" if wrong["operator"] in {"GT", "GTE"} else "below"},
            "valid_until_utc": min([v for v in (source.get("expires_at_utc"),
                (source.get("forecast_probabilities") or {}).get("horizon_end_utc"),
                source.get("status_at_utc") if source.get("status") in {"CANCELLED","EXPIRED","INVALIDATED"} else None) if v],key=posts._utc),
            "source_content_hash": export["status"]["content_hash"]}
        if None in (candidate["zone_low"],candidate["zone_high"],candidate["reference_price"]):
            continue
        if candidate["source_kind"] == "AS_WRITTEN":
            scored = outcome.get("score") or {}
            if (scored.get("result") != "HIT" or scored.get("plan_id") != source["plan_id"]
                    or scored.get("outcome_id") != outcome.get("outcome_id")):
                continue
        # Public terms, not a later plan revision, govern this report.
        original_levels = row.get("levels") or {}
        if any(original_levels.get(k) != candidate[k] for k in ("zone_low","zone_high")):
            continue
        if original_levels.get("invalidation_level") != candidate["invalidation"]["level"]:
            continue
        original_end = [v for v in (original_levels.get("time_exit_utc"),original_levels.get("entry_deadline_utc"),
                                    original_levels.get("valid_until_utc")) if v]
        if original_end:
            candidate["valid_until_utc"] = min([candidate["valid_until_utc"],*original_end],key=posts._utc)
        found.setdefault(candidate["call_id"],candidate)
    return list(found.values())


def cpi_article_candidate(record, *, outcomes=EVENT_OUTCOMES, bars_reader=read_bars):
    """Recover the published CPI sentence even when its old call array was empty.

    The retained BLS API response proves the core condition. Exact held
    prices decide the endpoint, so an intrahour dip alone never wins this call.
    """
    match = re.match(r"(If (\w+) core CPI is ([\d.]+)% or higher, gold falls at least ([\d.]+)% in (\d+) minutes)",
                     record.get("title", ""))
    event = re.fullmatch(r"(?:US_CPI_|bls-cpi-)(\d{8})",str(record.get("event_id", "")),re.I)
    if not match or not event:
        return None
    event_id = "US_CPI_"+event[1]
    outcome_files = sorted(Path(outcomes).glob(event_id+"-*.json"))
    if not outcome_files:
        return None
    outcome = json.loads(outcome_files[0].read_bytes())
    capture_path = Path(outcome["api_capture"])
    capture = json.loads(capture_path.read_bytes())
    response_path = Path(capture["response_path"])
    response_path = response_path if response_path.is_absolute() else capture_path.parent/response_path
    raw = response_path.read_bytes()
    if sha256(raw).hexdigest() != capture["response_sha256"] or capture["http_status"] != 200:
        raise ValueError("CC603_CPI_OFFICIAL_CAPTURE_CHANGED")
    response = json.loads(raw)
    if response.get("status") != "REQUEST_SUCCEEDED":
        raise ValueError("CC603_CPI_OFFICIAL_CAPTURE_NOT_SUCCESSFUL")
    core = next((s for s in response["Results"]["series"] if s["seriesID"] == "CUSR0000SA0L1E"),None)
    if not core:
        return None
    period = datetime.strptime(outcome["reference_period"],"%Y-%m")
    if period.strftime("%B").casefold() != match[2].casefold():
        raise ValueError("CC603_CPI_PUBLIC_PERIOD_MISMATCH")
    previous = period.replace(day=1)-timedelta(days=1)
    values = {}
    for row in core["data"]:
        try:
            value = Decimal(row["value"])
        except InvalidOperation:
            continue  # BLS's dash is absence, never a fabricated index.
        if value.is_finite():
            values[(int(row["year"]),row["period"])] = value
    current_index = values.get((period.year,f"M{period.month:02}"))
    previous_index = values.get((previous.year,f"M{previous.month:02}"))
    if current_index is None or previous_index is None:
        return None
    actual = ((current_index/previous_index-1)*100).quantize(Decimal("0.1"),rounding=ROUND_HALF_UP)
    event_at = posts._utc(outcome["released_at_utc"])
    end = event_at+timedelta(minutes=int(match[5]))
    if posts._utc(record["published_at_utc"]) >= event_at:
        return None
    reference_bars = bars_reader("XAUUSD",event_at.isoformat(),(event_at+timedelta(minutes=15)).isoformat())
    reference = next((b["open"] for b in reference_bars if b["open_epoch"] == int(event_at.timestamp())),None)
    if reference is None:
        return None
    level = float(Decimal(str(reference))*(1-Decimal(match[4])/100))
    terms = {"condition":f"{match[2]} core CPI is {match[3]}% or higher","market":"Gold","direction":"bearish",
             "horizon":f"{match[5]} minutes after the release","invalidation":f"gold falls less than {match[4]}% after {match[5]} minutes"}
    linked = [o for o in record["outlets"] if o.get("url")]
    if not linked:
        return None
    return {"call_id":record["content_id"]+":core-cpi-gold","source_kind":"ARTICLE","symbol":"XAUUSD",
        "terms":terms,"quote":match[1],"original_text":record["title"],"direction":"bearish",
        "original_url":next((o["url"] for o in linked if o["name"]=="substack"),linked[0]["url"]),
        "published_at_utc":record["published_at_utc"],"valid_until_utc":end.isoformat(),
        "destinations":sorted({"substack_notes" if o["name"]=="substack" else o["name"] for o in linked}),
        "condition_met":actual>=Decimal(match[3]),"condition_at_utc":event_at.isoformat(),
        "condition_source_hash":capture["response_sha256"],"actual_known_at_utc":outcome["known_at_utc"],
        "actual_core_mom_pct":str(actual),"entry_condition_kind":"EVENT","reference_price":reference,
        "zone_low":reference,"zone_high":reference,"resolution_level":level,
        "resolution_test":"AT_DEADLINE","invalidation_test":"AT_DEADLINE",
        "invalidation":{"field":"close","side":"above","level":level}}


def article_candidates(store, *, feed_path=None):
    """Read the same published feed and verified public-span annotations as the scorecard.

    A call's optional trigger carries its source-bound numeric price test. A
    free-text explanation without a measurable horizon is never invented into
    a test. Explicit event tests retain both their observed condition and its
    bound source hash; getting just the direction right remains a partial match.
    """
    from .published_content_v1 import DEFAULT_FEED, read_records
    from .public_call_scorecard_v1 import ANNOTATIONS
    articles, recovered = [], []
    for record in read_records(feed_path or DEFAULT_FEED):
        articles.append((record["content_id"], record["published_at_utc"], record["outlets"], record["conditional_calls"]))
        if not record["conditional_calls"]:
            candidate = cpi_article_candidate(record)
            if candidate:
                recovered.append(candidate)
    for message in store.list_outbox_messages(destination=ANNOTATIONS):
        packet = json.loads(message["payload"])
        articles.append((packet["content_id"],packet["published_at_utc"],packet["outlets"],packet["annotation"]["calls"]))
    candidates, checks = [], []
    for candidate in recovered:
        if candidate["condition_met"]:
            candidates.append(candidate)
        else:
            checks.append({"call_id":candidate["call_id"],"cause":"CC603_ARTICLE_CONDITION_NOT_MET"})
    for identity, at, outlets, calls in articles:
        for index, call in enumerate(calls):
            test = call.get("trigger") or {}
            if not isinstance(test,dict) or test.get("kind") != "PRICE_PATH_V1":
                continue
            required = {"symbol","condition_met","condition_source_hash","condition_at_utc","zone_low","zone_high",
                        "resolution_level","invalidation","valid_until_utc","reference_price"}
            if not required <= test.keys() or not test["condition_source_hash"]:
                checks.append({"call_id":call.get("call_id",identity+str(index)),"cause":"CC603_ARTICLE_TEST_INCOMPLETE"})
                continue
            if test["condition_met"] is not True:
                checks.append({"call_id":call.get("call_id",identity+str(index)),"cause":"CC603_ARTICLE_CONDITION_NOT_MET"})
                continue
            quote = call.get("original_text") or posts.conditional_call_text(call)
            linked = [o for o in outlets if o.get("url")]
            if not linked:
                continue
            candidates.append({**test,"call_id":call.get("call_id",identity+":"+str(index)),
                "source_kind":"ARTICLE","symbol":test["symbol"],"direction":call["direction"],
                "terms":{k:call[k] for k in ("condition","direction","market","horizon","invalidation")},
                "quote":quote,"original_text":quote,"original_url":linked[0]["url"],
                "published_at_utc":at,"destinations":sorted({"substack_notes" if o["name"]=="substack" else o["name"] for o in outlets}),
                "source_content_hash":identity})
    return candidates, checks


def held_chart(store, row, *, root=ROOT):
    """Copy the original unannotated download into this post's own media folder.

    A pre-move image cannot illustrate a resolved move. Later charts enter via
    the existing media owner, with the exact visible-window binding retained.
    """
    from . import tradingview_snapshot_v1 as tv
    folder = Path(root)/row["key"]
    binding = folder/"reviewed_chart.json"
    if binding.is_file():
        bound = json.loads(binding.read_bytes())
        asset = bound["asset"]
        tv.validate_snapshot_asset(asset,{"market_asset":row["symbol"]})
        if row["kind"] == "call_followup":
            first = posts._utc(row["candidate"]["published_at_utc"])
            last = posts._utc(row["price_check"]["resolved_at_utc"])
            if not posts._utc(bound["visible_from_utc"]) <= first < last <= posts._utc(bound["visible_to_utc"]):
                raise ValueError("CC603_CHART_DOES_NOT_SHOW_RESOLVED_MOVE")
        return asset
    if row["kind"] != "correction":
        return None
    objects = store.get_dispatches_for_work_item(row["original_key"])
    if not objects:
        return None
    intent = json.loads(store.get_outbox_message(objects[0]["message_id"])["payload"])
    context = json.loads((Path(intent["output_dir"])/"run_context_v1.json").read_bytes())
    source = next((a for a in context.get("media",{}).get("assets",[]) if a.get("tradingview_snapshot")),None)
    if not source:
        return None
    snap = source["tradingview_snapshot"]
    original = Path(snap["path"])
    if sha256(original.read_bytes()).hexdigest() != snap["sha256"]:
        raise ValueError("CC603_ORIGINAL_CHART_BYTES_CHANGED")
    media = folder/"media_assets"
    media.mkdir(parents=True,exist_ok=True)
    copied = media/original.name
    shutil.copyfile(original,copied)
    asset = tv.snapshot_asset(row["symbol"],posts.TITLES[row["symbol"]],{**snap,"path":str(copied)},media)
    tv.validate_snapshot_asset(asset,{"market_asset":row["symbol"]})
    return asset


def minute_due(store, load_export, **options):
    """An owed historical correction does not depend on a fresh Main export."""
    export = load_export() if corrections_complete(store) and not pending_link_replies(store) else {"status":{"plans":[]}}
    return run_due(store,export,**options)


def pending_link_replies(store):
    return [r["message_id"] for r in store.list_outbox_messages(destination=posts.DESTINATION)
            if r["status"] == "CC603_PREPARED" and json.loads(r["payload"]).get("kind") == LINK_REPLY]


def settle_link_reply_gap(store, row):
    """Ops Product, 16 Nov: record the dropped line after the one allowed reply."""
    if row.get("kind") != LINK_REPLY:
        return False
    validate_link_reply(store, row)
    for dispatch in store.get_dispatches_for_work_item(row["key"]):
        if dispatch["platform"] != "substack_notes" or dispatch["status"] != "DISPATCH_CONFIRMED":
            continue
        reconciled = any(r["reconciliation_id"] == "reconciliation_" + dispatch["dispatch_id"].removeprefix("dispatch_")
            and r["status"] == "RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE"
            for r in store.get_reconciliations_for_work_item(row["key"]))
        readbacks = store.list_readbacks_for_dispatch(dispatch["dispatch_id"])
        observed = json.loads(readbacks[-1]["readback_data"])["readback"] if readbacks else {}
        if (reconciled and observed.get("write_exists") and observed.get("identity_match")
                and observed.get("observed_public_object_id") == dispatch.get("public_object_id")
                and observed.get("observed_public_object_url") == dispatch.get("public_object_url")
                and (observed.get("content_binding_checks") or {}).get("link_reply_gap") is True):
            store.set_outbox_status(row["key"], "SETTLED")
            store.set_outbox_status(row["link_reply_parent"]["key"], "SETTLED")
            return True
    return False


def run_record(result):
    """Keep progress in the minute task's existing record, without copy or media bytes."""
    def publication(value):
        return {**{k:value[k] for k in ("status","state","pending_destination","request_sha256","cause") if k in value},
            "per_destination":{d:{k:v[k] for k in ("status","reason_code","public_object_id","public_object_url") if k in v}
                for d,v in value.get("per_destination",{}).items() if isinstance(v,dict)}}
    return {**{k:result[k] for k in ("status","cause","corrections_complete") if k in result},"posts":[
        {**{k:row[k] for k in ("key","call_id","status","cause","media_request") if k in row},
            **({"publication":publication(row["publication"])} if row.get("publication") else {}),
            **({"continuations":[{"key":child["key"],"publication":publication(child["publication"])}
                for child in row["continuations"]]} if row.get("continuations") else {})}
        for row in result.get("posts",[])]}


def delivery_plan(store, row, asset, *, root, host, destinations):
    """Repair a local image refusal with a new package, retaining every old byte."""
    from .publication_coordinator_v1 import DurablePublicationCoordinator as Coordinator
    key = row['key']
    original_hash = sha256(('plan-status-post:'+key).encode()).hexdigest()
    original_ids = {Coordinator._ids(key,original_hash,d)['dispatch_id'] for d in destinations}
    dispatches = store.get_dispatches_for_work_item(key)
    originals = [d for d in dispatches if d['dispatch_id'] in original_ids]
    causes = {r['reconciliation_id']:r['status'] for r in store.get_reconciliations_for_work_item(key)}
    safe = originals and all(d['status']=='DEFINITE_NO_WRITE' and not d.get('public_object_id')
        and not d.get('public_object_url') and causes.get('reconciliation_'+d['dispatch_id'].removeprefix('dispatch_'))
            == 'TRADINGVIEW_PRICE_SCALE_CHECK_REQUIRED' for d in originals)
    repair = None
    if safe:
        from .publication_image_contract_v1 import validate_scale
        validate_scale(row['symbol'],asset['tradingview_snapshot'])
        repair_hash = _hash(['cc603-reviewed-media-repair',key,asset])
        repair_ids = {Coordinator._ids(key,repair_hash,d)['dispatch_id'] for d in destinations}
        if any(d['dispatch_id'] not in original_ids|repair_ids and d['status']!='DEFINITE_NO_WRITE'
               for d in dispatches):
            raise ValueError('CC603_EXISTING_PUBLIC_MEDIA_REQUIRES_EXACT_RECOVERY')
        root = Path(root)/'reviewed-media'/repair_hash
        repair = {'original_plan_hash':original_hash,'asset_sha256':asset['sha256'],
                  'refused_dispatches':[d['dispatch_id'] for d in originals]}
    plan = posts.prepare_post(store,key,root=Path(root),host=host,destinations=tuple(destinations),cc603_asset=asset)
    if repair:
        plan.update(plan_hash=repair_hash,cc603_media_repair=repair)
    return plan


# CC-778 (Builder K, 24 Nov 2026; Jim's 14 Nov request, CC-603): the prepared follow-ups post with a TradingView
# chart of their own move, captured through the existing snapshot path, at most two a day, oldest call first, never
# in Jim's pause or the hour after it ends. A failed capture keeps the follow-up waiting with its cause; it never
# posts text only (decision 82). The plan's entry zone and invalidation are drawn where the chart's own axis places
# them exactly; a target never is (decisions 40 and 157).
MOVE_CHART = "CC778_MOVE_CHART_V1"
BACKFILL_PER_DAY = 2
BACKFILL_DAY = timedelta(hours=24)
RESTORE_GRACE = timedelta(hours=1)
CAPTURE_ROUND_ATTEMPTS = 2
CAPTURE_RETRY_AFTER = timedelta(hours=6)
VISIBLE_LEAD = timedelta(hours=1)
VISIBLE_MIN_SPAN = timedelta(hours=12)
# SP:SPX and NASDAQ:NDX have bars in New York cash hours only (ET); a move that resolved outside them is not on
# that chart (CC-788 gives the Nasdaq 100 the S&P 500's rule).
CASH_SESSIONS = {"US500": ((9, 30), (16, 0)), "USTEC": ((9, 30), (16, 0))}
INTERVAL_WORDS = {"15": "15-minute", "60": "hourly", "240": "4-hour", "D": "daily"}


def _floor(at, step):
    epoch = int(at.timestamp())
    return datetime.fromtimestamp(epoch - epoch % step, timezone.utc)


def overlay_levels(row):
    """The levels CC-459's overlay binds for this follow-up (entry zone, invalidation; never a target)."""
    from .tradingview_plan_overlay_v1 import source_binding
    return source_binding({**row, "kind": "call_followup", "cc603_contract": CONTRACT})["levels"]


def move_chart_request(row):
    """The chart a follow-up needs: its market, interval, dated window and the plan levels to draw."""
    from . import tradingview_snapshot_v1 as tv
    candidate, check, symbol = row["candidate"], row["price_check"], row["symbol"]
    published, resolved = posts._utc(candidate["published_at_utc"]), posts._utc(check["resolved_at_utc"])
    span = resolved - published
    interval = ("15" if span <= timedelta(days=4) else "60" if span <= timedelta(days=16)
                else "240" if span <= timedelta(days=60) else "D")
    step = tv.INTERVAL_SECONDS[interval]
    show_from = _floor(published, step)
    last_open = _floor(resolved - timedelta(seconds=1), step)
    visible_to = last_open + timedelta(seconds=step)
    # Some context before the call; a short move still fills a readable chart (about 48 bars at 15 minutes).
    start = _floor(show_from - max(VISIBLE_LEAD, VISIBLE_MIN_SPAN - (visible_to - show_from)), step)
    request = {"contract": MOVE_CHART, "key": row["key"], "symbol": symbol, "tv_symbol": tv.SYMBOLS[symbol],
        "interval": interval, "published_at_utc": published.isoformat(), "resolved_at_utc": resolved.isoformat(),
        "visible_range": {"from_utc": start.isoformat(), "show_from_utc": show_from.isoformat(),
                          "last_bar_open_utc": last_open.isoformat()},
        "visible_to_utc": visible_to.isoformat(),
        "levels": overlay_levels(row),
        "ratios": ["16:9", *(["4:5"] if "instagram_business" in row["cc603_destinations"] else [])]}
    session = CASH_SESSIONS.get(symbol)
    if session:
        local = last_open.astimezone(scorecard.ET)
        opens, closes = (local.replace(hour=h, minute=m, second=0, microsecond=0) for h, m in session)
        if local.weekday() >= 5 or not (opens <= local and local + timedelta(seconds=step) <= closes):
            request["refusal"] = "CC778_CHART_MARKET_CLOSED_AT_RESOLUTION:" + request["tv_symbol"]
    return request


def held_close_quote(symbol, at, *, bars_reader=read_bars):
    """The held plan-feed close of the 15-minute bar ending at the chart window's close, or None."""
    end = posts._utc(at)
    opening = int(end.timestamp()) - 900
    bars = [b for b in bars_reader(symbol, (end - timedelta(minutes=15)).isoformat(), end.isoformat())
            if b["open_epoch"] == opening]
    if not bars:
        return None
    bar = bars[-1]
    known = bar.get("known_epoch")
    return {"market": symbol, "instrument": symbol, "price": bar["close"], "quoted_at_utc": end.isoformat(),
            "known_at_utc": (datetime.fromtimestamp(known, timezone.utc) if known else end).isoformat(),
            "source_path": str(BAR_STORE), "source_sha256": bar["source_sha256"],
            "source_record_sha256": _hash({k: bar[k] for k in sorted(bar)}),
            "price_basis": "plan_bar_close", "source_kind": "HELD_M15_RESOLUTION_CLOSE"}


def bind_move_chart(row, request, taken, media, ratio, *, now):
    """The checked download as this follow-up's image, with the plan's levels where they place exactly."""
    from . import tradingview_snapshot_v1 as tv
    from . import tradingview_plan_overlay_v1 as overlay
    from .publication_image_contract_v1 import validate_scale
    from .public_time_v1 import public_timestamp
    symbol = row["symbol"]
    first, last = posts._utc(request["published_at_utc"]), posts._utc(request["resolved_at_utc"])
    shown_from, shown_to = posts._utc(taken["visible_from_utc"]), posts._utc(taken["visible_to_utc"])
    if not shown_from <= first < last <= shown_to or shown_to != posts._utc(request["visible_to_utc"]):
        raise ValueError("CC603_CHART_DOES_NOT_SHOW_RESOLVED_MOVE")
    validate_scale(symbol, taken)
    title = posts.TITLES[symbol]
    asset = tv.snapshot_asset(symbol, title, taken, media, ratio)
    words = INTERVAL_WORDS[request["interval"]]
    a, b = shown_from.astimezone(scorecard.ET), shown_to.astimezone(scorecard.ET)
    asset.update(
        caption=f"{title}: {words} bars from {a:%d %b %H:%M} ET to {b:%d %b %Y %H:%M} ET, from before our "
                f"original view to the move it described. {tv.CREDIT}.",
        alt_text=f"TradingView {words} chart of {tv.NAMES[symbol]}, from {a:%d %b %H:%M} ET through "
                 f"{b:%d %b %H:%M} ET: the period from the original view to the move it described, with no later "
                 f"bars. Captured {public_timestamp(posts._utc(taken['captured_at_utc']) or now)}.")
    drawn, cause = [], None
    if taken.get("chart_geometry"):
        try:
            # The stored row itself: the write boundary re-reads it and redraws these exact levels.
            asset = overlay.apply(asset, row)
            drawn = [m["label"] for m in asset["plan_overlay"]["markers"]]
            if not drawn:
                cause = "CC778_LEVELS_NOT_PLACEABLE_ON_THIS_CHART_BASIS"
        except (ValueError, KeyError, OSError) as exc:
            cause = str(exc)[:200]
    else:
        cause = taken.get("chart_geometry_cause") or "TRADINGVIEW_PRICE_SCALE_NOT_CAPTURED"
    tv.validate_snapshot_asset(asset, {"market_asset": symbol})
    check = taken["price_scale_check"]
    review = {"kind": "CC778_AUTOMATIC_CHECKS", "checked_at_utc": now.isoformat(), "ratio": ratio,
        "window": {"requested": request["visible_range"], "observed": taken.get("visible_range_observed"),
                   "visible_to_utc": taken["visible_to_utc"]},
        "price_scale": {k: check[k] for k in ("comparison_basis", "difference_pct", "maximum_difference_pct",
                                              "level_offset", "quote_absent_cause") if k in check},
        "levels_drawn": drawn, "target_drawn": False, "live_values_hidden": taken.get("live_values_hidden") is True,
        **({"levels_cause": cause} if cause else {}),
        "readback": "Ops Product reads back the first real capture after the relaunch (CC-778)."}
    return asset, review


def capture_move_chart(row, *, root=ROOT, now=None, ratio="16:9", worker=None, bars_reader=read_bars):
    """One bounded capture attempt for a follow-up's chart; the result binds it or records why not.

    Two attempts make a round; a round that fails waits CAPTURE_RETRY_AFTER before the next. The state file keeps
    every attempt's cause beside the follow-up, as plan posts keep theirs.
    """
    from . import tradingview_snapshot_v1 as tv
    now = now or datetime.now(timezone.utc)
    folder = Path(root) / row["key"]
    portrait = ratio != "16:9"
    binding_path = folder / ("reviewed_portrait.json" if portrait else "reviewed_chart.json")
    request = move_chart_request(row)
    base = {"key": row["key"], "ratio": ratio, "media_request": {**{k: request[k] for k in (
        "symbol", "tv_symbol", "interval", "visible_range", "visible_to_utc", "levels")},
        "binding_path": str(binding_path), "visible_from_utc": request["visible_range"]["from_utc"]}}
    if binding_path.is_file():
        return {**base, "status": "BOUND", "attempted": False}
    state_path = folder / ("move_chart_capture_4x5_v1.json" if portrait else "move_chart_capture_v1.json")
    request_sha = _hash(request)
    state = (json.loads(state_path.read_bytes()) if state_path.is_file() else
             {"key": row["key"], "ratio": ratio, "request_sha256": request_sha, "attempts": 0, "round_attempts": 0,
              "attempt_causes": [], "status": "PENDING", "started_at_utc": now.isoformat()})
    if state.get("request_sha256") != request_sha or state.get("key") != row["key"]:
        raise ValueError("CC778_MOVE_CHART_REQUEST_CHANGED")

    def save():
        folder.mkdir(parents=True, exist_ok=True)
        staged = state_path.with_suffix(".tmp")
        staged.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")
        staged.replace(state_path)

    def pending(attempted):
        return {**base, "status": "MEDIA_PENDING", "cause": state["cause"], "attempted": attempted,
                **({"retry_after_utc": state["retry_after_utc"]} if state.get("retry_after_utc") else {})}

    lost = state["attempts"] - len(state["attempt_causes"])
    if lost > 0:
        # The run stopped during an attempt and saved no cause: name it, as plan_snapshot does.
        state["attempt_causes"] += [tv.CAPTURE_INTERRUPTED] * lost
        state.setdefault("first_cause", tv.CAPTURE_INTERRUPTED)
        state["cause"] = tv.CAPTURE_INTERRUPTED
        if state["round_attempts"] >= CAPTURE_ROUND_ATTEMPTS:
            state.update(status="FAILED", retry_after_utc=(now + CAPTURE_RETRY_AFTER).isoformat())
        save()
    if request.get("refusal"):
        if state.get("cause") != request["refusal"]:
            state.update(status="FAILED", cause=request["refusal"])
            state.setdefault("first_cause", request["refusal"])
            save()
            tv.record_outcome({"status": "MOVE_CHART_REFUSED", "key": row["key"], "ratio": ratio,
                               "cause": request["refusal"]})
        return pending(False)
    if state["status"] == "FAILED":
        if now < posts._utc(state["retry_after_utc"]):
            return pending(False)
        state.update(status="PENDING", round_attempts=0)
    state["attempts"] += 1
    state["round_attempts"] += 1
    state["last_attempt_at_utc"] = now.isoformat()
    save()
    try:
        taken = tv.capture(row["symbol"], request["interval"],
            folder / "media_assets" / f"move{'-4x5' if portrait else ''}-attempt-{state['attempts']}",
            timeout=tv.PLAN_ATTEMPT_TIMEOUT_SECONDS, worker=worker, ratio=ratio,
            visible_range=request["visible_range"],
            quote_provider=lambda market, at: held_close_quote(market, at, bars_reader=bars_reader))
        asset, review = bind_move_chart(row, request, taken, folder / "media_assets", ratio, now=now)
    except Exception as exc:  # every cause is recorded; the follow-up keeps waiting (decision 82)
        cause = str(exc)[:200] or type(exc).__name__
        state["attempt_causes"].append(cause)
        state.setdefault("first_cause", cause)
        state["cause"] = cause
        if state["round_attempts"] >= CAPTURE_ROUND_ATTEMPTS:
            state.update(status="FAILED", retry_after_utc=(now + CAPTURE_RETRY_AFTER).isoformat())
        else:
            state.update(status="RETRY")
        save()
        tv.record_outcome({"status": "MOVE_CHART_FAILED", "key": row["key"], "ratio": ratio, "cause": cause,
                           "attempts": state["attempts"]})
        return pending(True)
    binding = {"contract": MOVE_CHART, "asset": asset, "visible_from_utc": taken["visible_from_utc"],
               "visible_to_utc": taken["visible_to_utc"], "last_bar_open_utc": taken["last_bar_open_utc"],
               "request_sha256": request_sha, "review": review}
    staged = binding_path.with_suffix(".tmp")
    staged.write_text(json.dumps(binding, sort_keys=True, ensure_ascii=False), encoding="utf-8")
    staged.replace(binding_path)
    state["attempt_causes"].append("CAPTURED")
    state.update(status="CAPTURED", cause=None, binding_sha256=sha256(binding_path.read_bytes()).hexdigest(),
                 asset_id=asset["asset_id"])
    save()
    tv.record_outcome({"status": "MOVE_CHART_CAPTURED", "key": row["key"], "ratio": ratio,
                       "asset_id": asset["asset_id"], "levels_drawn": review["levels_drawn"]})
    return {**base, "status": "CAPTURED", "attempted": True, "levels_drawn": review["levels_drawn"]}


def backfill_hold(now, window):
    """Why no backfill follow-up may post now, or None: Jim's pause, then the first hour after its restore."""
    start, end = window
    if now < start:
        return None
    if end >= datetime.max.replace(tzinfo=timezone.utc) - RESTORE_GRACE or now < end:
        return "CC778_BACKFILL_PAUSED"
    if now < end + RESTORE_GRACE:
        return "CC778_BACKFILL_FIRST_HOUR_AFTER_RESTORE"
    return None


def backfill_order(store, keys, *, now, pause_window):
    """Started follow-ups finish first; new ones start oldest call first, at most two in any 24 hours."""
    hold = backfill_hold(now, pause_window)
    if hold:
        return [], [{"key": key, "status": "BACKFILL_HELD", "cause": hold} for key in keys]
    starts = {}
    for message in store.list_outbox_messages(destination=posts.DESTINATION):
        if not message["message_id"].startswith("cc603-followup-"):
            continue
        if json.loads(message["payload"]).get("kind") != "call_followup":
            continue
        times = [posts._utc(d["dispatched_at"]) for d in store.get_dispatches_for_work_item(message["message_id"])]
        if times:
            starts[message["message_id"]] = min(times)
    called = {key: posts._utc(posts._row_payload(store, key)["candidate"]["published_at_utc"]) for key in keys}
    started = sorted((k for k in keys if k in starts), key=called.get)
    fresh = sorted((k for k in keys if k not in starts), key=called.get)
    # A start stamped after `now` (clock skew) still counts: pacing errs toward fewer posts.
    recent = sorted(t for t in starts.values() if now - BACKFILL_DAY < t)
    if len(recent) < BACKFILL_PER_DAY:
        return started + fresh, []
    next_due = (recent[-BACKFILL_PER_DAY] + BACKFILL_DAY).isoformat()
    return started, [{"key": key, "status": "BACKFILL_PACED", "cause": "CC778_BACKFILL_TWO_A_DAY",
                      "next_due_utc": next_due} for key in fresh]


def run_due(store, export, *, now=None, root=ROOT, coordinator_for=None, host=None, asset_for=None, bars_reader=read_bars,
            claim_checker=None, pause_window=None, move_chart_worker=None, move_charts=True):
    """One bounded slice in the existing minute task. No schedule, loop or second publisher."""
    now = now or datetime.now(timezone.utc)
    from .native_neo_executor_v1 import NativeNeoInputRequired
    from .public_draft_claims_v1 import try_plan_check
    correction = prepare_gold_correction(store, now=now)
    results = []
    replies = pending_link_replies(store)
    if replies:
        keys = replies
    elif not corrections_complete(store):
        keys = [correction["key"]]
    else:
        article_calls, article_checks = article_candidates(store)
        candidates = discover(store, export) + article_calls
        priority = {"a0380280":0,"d7eddc84":1,"576f57e9":2,"52a48ae1":3,"8479dce1":4}
        candidates.sort(key=lambda c:(c["source_kind"]=="CR_VIEW",priority.get(c.get("short_id"),10),
                                      posts._utc(c["published_at_utc"])))
        results.extend(article_checks)
        record = observed_record(store, now=now) if candidates else None
        for candidate in candidates:
            try:
                checked = check_path(candidate, bars_reader(candidate["symbol"],candidate["published_at_utc"],
                    min(posts._utc(candidate["valid_until_utc"]),now).isoformat()))
                results.append(queue_followup(store,candidate,checked,record,now=now))
            except (ValueError,OSError,KeyError,sqlite3.Error) as exc:
                results.append({"call_id":candidate["call_id"],"status":"NOT_COMPLETED","cause":str(exc)[:160]})
        keys = [r["message_id"] for r in store.list_outbox_messages(destination=posts.DESTINATION)
                if r["status"] == "CC603_PREPARED" and json.loads(r["payload"]).get("kind") == "call_followup"]
        if pause_window is None:
            from .plan_call_cards_v1 import jim_pause_window
            pause_window = jim_pause_window()
        keys, held = backfill_order(store, keys, now=now, pause_window=pause_window)
        results.extend(held)
    captured_this_run = False
    for key in keys:
        row = posts._row_payload(store,key)
        if post_complete(store,row):
            store.set_outbox_status(key,"PUBLISHED")
            continue
        link_reply = row.get("kind") == LINK_REPLY
        if link_reply and settle_link_reply_gap(store, row):
            results.append({"key":key,"status":"PUBLISHED_WITH_LINK_GAP",
                "cause":"SUBSTACK_NOTES_DROPPED_ORIGINAL_LINK; ONE_REPLY_USED; NO_EDIT_DECISIONS_136_84"})
            break
        asset = None if link_reply else asset_for(row) if asset_for else held_chart(store,row,root=root)
        capture = (move_charts and not asset_for and not link_reply and row.get("kind") == "call_followup"
                   and not captured_this_run)
        if not asset and capture:
            # CC-778: one bounded capture per minute run. A bound chart posts in the next run; a failed one keeps
            # waiting with its cause, and the next follow-up in line is tried.
            try:
                taken = capture_move_chart(row, root=root, now=now, worker=move_chart_worker, bars_reader=bars_reader)
            except (ValueError, KeyError, TypeError, OSError) as exc:
                results.append({"key":key,"status":"MEDIA_PENDING","cause":str(exc)[:160] or type(exc).__name__})
                continue
            captured_this_run = taken["attempted"]
            results.append({"key":key,"status":"MEDIA_CAPTURED" if taken["status"] == "CAPTURED" else "MEDIA_PENDING",
                **({} if taken["status"] == "CAPTURED" else
                   {"cause":taken.get("cause") or "CC603_REAL_TRADINGVIEW_MOVE_CHART_REQUIRED"}),
                "media_request":taken["media_request"]})
            if captured_this_run:
                break
            continue
        if (asset and capture and "4:5" in move_chart_request(row)["ratios"]
                and not (Path(root)/key/"reviewed_portrait.json").is_file()
                and not any(p["destination"] == "instagram_business" for p in publications(store,key))):
            # Instagram takes a native 4:5 chart of the same window (the BTC follow-up's refusal of 16 Nov).
            portrait = capture_move_chart(row, root=root, now=now, ratio="4:5", worker=move_chart_worker,
                                          bars_reader=bars_reader)
            if portrait["attempted"]:
                results.append({"key":key,"status":"PORTRAIT_"+portrait["status"],
                    **({"cause":portrait["cause"]} if portrait.get("cause") else {}),
                    "media_request":portrait["media_request"]})
                break
        if not asset and not link_reply:
            results.append({"key":key,"status":"MEDIA_PENDING","cause":"CC603_REAL_TRADINGVIEW_MOVE_CHART_REQUIRED",
                "media_request":{"symbol":row["symbol"],"binding_path":str(Path(root)/key/"reviewed_chart.json"),
                    "visible_from_utc":(row.get("candidate") or {}).get("published_at_utc"),
                    "visible_to_utc":(row.get("price_check") or {}).get("resolved_at_utc")}})
            continue
        if not link_reply:
            row = refresh_record(store, row, now=now)
        destinations = sorted(row["cc603_destinations"],key=lambda d:(d in {"x","substack_notes"},d))
        plan = (posts.prepare_post(store,key,root=root,host=host,destinations=tuple(destinations)) if link_reply
                else delivery_plan(store,row,asset,root=root,host=host,destinations=destinations))
        try_plan_check(claim_checker, store, row, plan)
        if coordinator_for:
            coordinator = coordinator_for(key,Path(plan["output_dir"]))
        else:
            from .native_neo_executor_v1 import bind_native_neo_coordinator
            from .neo_endpoint_executor_v1 import NeoMcpClient
            coordinator,_ = bind_native_neo_coordinator(store,operation_id=key,output_dir=Path(plan["output_dir"])/"native-neo",
                native_invocation_id="cc603-minute-consumer",allow_publish=True,automatic=True,
                endpoint_client=NeoMcpClient(task_name="cc603 corrections followups",group_title="codex/cc603-corrections-followups"))
        posts.scope_to_post(coordinator,key,plan)
        try:
            if any(d['status'] in {'UNKNOWN_WRITE', 'DISPATCH_ATTEMPT_STARTED', 'RECONCILED_ABSENT_SAFE_TO_RETRY'}
                   for d in store.get_dispatches_for_work_item(key)):
                coordinator.recover_pending()
            outcome = coordinator.publish_plan(key,plan)
        except NativeNeoInputRequired as pending:
            outcome = {"status":"NATIVE_NEO_TOOL_PENDING","request_sha256":pending.request.get("request_sha256"),
                "pending_destination":pending.request.get("destination"),
                "per_destination":{p["destination"]:{"status":"DISPATCH_CONFIRMED"} for p in publications(store,key)}}
        # Threads/Telegram continuations retain their own durable dispatches.
        # No subsequent part goes out until its predecessor has read back.
        continuation_outcomes = []
        preceding = outcome.get("per_destination",{})
        for continuation in plan.get("continuations") or []:
            if any((preceding.get(d["destination"]) or {}).get("status") != "DISPATCH_CONFIRMED"
                   for d in continuation["destinations"]):
                break
            child = continuation["work_item_id"]
            try_plan_check(claim_checker, store, row, continuation, key=child)
            store.create_work_item(story_id=child,work_item_id=child,title=row["title"],target_surface="MULTI_PLATFORM")
            posts.scope_to_post(coordinator,child,continuation)
            child_outcome = coordinator.publish_plan(child,continuation)
            continuation_outcomes.append({"key":child,"publication":child_outcome})
            preceding = child_outcome.get("per_destination",{})
        results.append({"key":key,"publication":outcome,"continuations":continuation_outcomes})
        portrait_path=Path(root)/key/'reviewed_portrait.json'
        if 'instagram_business' in destinations and portrait_path.is_file() and not any(
                p['destination']=='instagram_business' for p in publications(store,key)):
            portrait=json.loads(portrait_path.read_bytes())['asset']
            from .tradingview_snapshot_v1 import validate_snapshot_asset
            from .publication_image_contract_v1 import validate_scale
            validate_snapshot_asset(portrait,{'market_asset':row['symbol']})
            validate_scale(row['symbol'],portrait['tradingview_snapshot'])
            portrait_hash=_hash(['cc603-native-portrait',key,portrait])
            portrait_plan=posts.prepare_post(store,key,root=Path(root)/'portrait'/portrait_hash,host=host,
                destinations=('instagram_business',),cc603_asset=portrait)
            portrait_plan.update(plan_hash=portrait_hash,cc603_portrait=True)
            posts.scope_to_post(coordinator,key,portrait_plan)
            results[-1]['portrait_publication']=coordinator.publish_plan(key,portrait_plan)
        if post_complete(store,row):
            store.set_outbox_status(key,"PUBLISHED")
            if link_reply:
                parent = row["link_reply_parent"]["key"]
                if post_complete(store, posts._row_payload(store, parent)):
                    store.set_outbox_status(parent, "PUBLISHED")
        elif link_reply and settle_link_reply_gap(store, row):
            results[-1].update(status="PUBLISHED_WITH_LINK_GAP",
                cause="SUBSTACK_NOTES_DROPPED_ORIGINAL_LINK; ONE_REPLY_USED; NO_EDIT_DECISIONS_136_84")
        break  # One actual publication slice per existing minute, not one blocked candidate.
    return {"status":"OK","corrections_complete":corrections_complete(store),"posts":results}
