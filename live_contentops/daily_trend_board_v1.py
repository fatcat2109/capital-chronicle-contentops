"""CC-537: the public desk board, consumed by the existing minute entry.

Main supplies all states, levels and measured results. This module formats them;
it never estimates a level, return, probability or missing sample window.
The existing outbox, leases, Neo transports and coordinator own delivery/recovery.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import shutil
from uuid import uuid4
from zoneinfo import ZoneInfo

from .capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from .event_article_guard_v1 import PUBLIC_NOTICE, CONFLICTS_NOTICE

POLICY = "CC537_DAILY_TREND_BOARD_V1"
SOURCE = Path(r"A:\Capital Chronicle\ResearchRuns\plan-status-v1\desk-board.public.json")
DESTINATION = "internal:daily-trend-board"
ET = ZoneInfo("America/New_York")
MARKETS = {"XAUUSD": "Gold", "US500": "S&P 500", "EURUSD": "EUR/USD",
           "USDJPY": "USD/JPY", "USOIL": "WTI oil", "BTCUSD": "Bitcoin"}
BEHAVIOURS = {
    "LONG_WHILE_UP_20": "Long with trend, 20 sessions",
    "SHORT_WHILE_DOWN_20": "Short with trend, 20 sessions",
    "WITH_YARDSTICK_5": "With trend, 5 sessions",
    "AGAINST_YARDSTICK_5": "Against trend, 5 sessions",
    "BREAKOUT_WITH_TREND_20": "Breakout with trend, 20 sessions",
    "BUY_PULLBACK_IN_UPTREND_10": "Buy pullback, 10 sessions",
    "SELL_RALLY_IN_DOWNTREND_10": "Sell rally, 10 sessions",
    "FOLLOW_LARGE_DAY_3": "Follow a large day, 3 sessions",
    "FADE_LARGE_DAY_3": "Fade a large day, 3 sessions",
}


class BoardSourceError(ValueError):
    def __init__(self, cause, **details):
        super().__init__(cause)
        self.details = details


def utc(value):
    stamp = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise BoardSourceError("BOARD_SOURCE_TIMEZONE_REQUIRED")
    return stamp.astimezone(timezone.utc)


def trading_age(first, last):
    """Completed weekday sessions; the six-market board is not an NYSE calendar."""
    first, last = date.fromisoformat(str(first)), date.fromisoformat(str(last))
    return sum((first + timedelta(days=i)).weekday() < 5 for i in range(1, (last - first).days + 1))


def latest_close(now):
    local = utc(now).astimezone(ET)
    day = local.date() if local.time() >= time(17) else local.date() - timedelta(days=1)
    while day.weekday() >= 5:
        day -= timedelta(days=1)
    return day.isoformat()


def identity(day):
    return "daily-trend-board-" + date.fromisoformat(day).isoformat()


def number(value, *, signed=False):
    result = Decimal(str(value))
    if not result.is_finite():
        raise BoardSourceError("BOARD_NUMBER_NOT_FINITE")
    text = format(result, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return ("+" if signed and result > 0 else "") + text


def project(board, *, now):
    """Whitelist the public scope and report exact absent producer fields."""
    if board.get("schema") != "CapitalChronicleDeskBoardPublicV1":
        raise BoardSourceError("BOARD_PUBLIC_PROJECTION_REQUIRED")
    content = {k: v for k, v in board.items() if k != "content_hash"}
    if sha256_of(content) != board.get("content_hash"):
        raise BoardSourceError("BOARD_CONTENT_HASH_CHANGED")
    now, captured = utc(now), utc(board["as_of_utc"])
    if captured > now:
        raise BoardSourceError("BOARD_FROM_FUTURE")
    age = trading_age(captured.astimezone(ET).date(), now.astimezone(ET).date())
    age_seconds = (now - captured).total_seconds()
    if age > 1:
        raise BoardSourceError("BOARD_OLDER_THAN_ONE_TRADING_DAY", trading_days=age, age_seconds=age_seconds)
    missing, markets, sessions = [], {}, {}
    if not board.get("yardstick_rule"):
        missing.append("/yardstick_rule")
    table = board.get("measured_table") or {}
    for symbol in MARKETS:
        row = board.get("markets", {}).get(symbol) or {}
        yard = row.get("yardstick") or {}
        prefix = "/markets/" + symbol
        state = yard.get("yardstick")
        if yard.get("state") != "AVAILABLE" or state not in {"UP", "DOWN", "MIXED"}:
            missing.append(prefix + "/yardstick/yardstick")
        opened = yard.get("last_completed_bar_utc")
        if not opened:
            missing.append(prefix + "/yardstick/last_completed_bar_utc")
        else:
            # CC-528 defines this as D1 bar OPEN; completion is one day later.
            completed = utc(opened) + timedelta(days=1)
            if completed > now:
                raise BoardSourceError("BOARD_BAR_NOT_COMPLETED", market=symbol)
            sessions[symbol] = completed.astimezone(ET).date().isoformat()
        means = {}
        for length in (20, 50):
            field = "mean_close_" + str(length)
            if yard.get(field) is None:
                missing.append(prefix + "/yardstick/" + field)
            else:
                means[field] = number(yard[field])
        measured = []
        for index, result in enumerate(row.get("rows_whose_condition_holds_now") or []):
            field = prefix + "/rows_whose_condition_holds_now/" + str(index)
            sample = result.get("this_side")
            if sample is None:
                missing.append(field + "/this_side")
                continue
            # Main's public V1 side tuple is n, win fraction, mean R, t,
            # first-half R, second-half R, read. Do not use pooled-side means.
            if isinstance(sample, list):
                if len(sample) != 7:
                    raise BoardSourceError("BOARD_SIDE_TUPLE_CHANGED", field=field + "/this_side")
                count, mean = sample[0], sample[2]
            else:
                count, mean = sample.get("n"), sample.get("mean_r")
            if not isinstance(count, int) or isinstance(count, bool) or count <= 0 or mean is None:
                missing.append(field + "/this_side/n_or_mean_r")
                continue
            period = result.get("sample_period") or row.get("sample_period") or table.get("sample_period")
            if not period or not period.get("start") or not period.get("end"):
                missing.append(field + "/sample_period")
                continue
            start, end = date.fromisoformat(period["start"]), date.fromisoformat(period["end"])
            if start > end or end > now.astimezone(ET).date():
                raise BoardSourceError("BOARD_SAMPLE_PERIOD_INVALID", field=field + "/sample_period")
            behaviour = result.get("behaviour")
            if behaviour not in BEHAVIOURS or result.get("side") not in {"LONG", "SHORT"}:
                raise BoardSourceError("BOARD_MEASURED_ROW_UNRECOGNISED", field=field)
            measured.append({"behaviour": behaviour, "side": result["side"], "n": count,
                             "mean_r": number(mean, signed=True), "sample_period": deepcopy(period)})
        # MIXED can legitimately have no qualifying historical row.
        markets[symbol] = {"state": state, "means": means, "rows": measured}
    if len(set(sessions.values())) > 1:
        raise BoardSourceError("BOARD_MARKET_SESSIONS_DIFFER", market_sessions=sessions)
    day = next(iter(sessions.values()), None)
    if day and (day > latest_close(now) or date.fromisoformat(day).weekday() >= 5):
        raise BoardSourceError("BOARD_NEW_YORK_CLOSE_NOT_DUE", day_et=day, latest_close_et=latest_close(now))
    session_age = trading_age(day, latest_close(now)) if day else None
    if session_age is not None and session_age > 1:
        raise BoardSourceError("BOARD_MARKET_DATA_OLDER_THAN_ONE_TRADING_DAY", day_et=day, trading_days=session_age)
    if missing:
        raise BoardSourceError("BOARD_PUBLIC_FIELDS_ABSENT", missing_fields=missing,
                               as_of_utc=board["as_of_utc"], day_et=day, age_seconds=age_seconds)
    if any(r["sample_period"]["end"] > day for m in markets.values() for r in m["rows"]):
        raise BoardSourceError("BOARD_SAMPLE_ENDS_AFTER_SESSION", day_et=day)
    return {"policy": POLICY, "day_et": day, "as_of_utc": board["as_of_utc"],
            "board_content_hash": board["content_hash"], "yardstick_rule": board["yardstick_rule"],
            "table_hash": table.get("table_content_hash"), "markets": markets}


def compose(current, previous=None):
    previous = previous if previous and trading_age(previous["day_et"], current["day_et"]) == 1 else None
    changes = [s for s in MARKETS if previous and current["markets"][s]["state"] != previous["markets"][s]["state"]]
    headline = ("; ".join(MARKETS[s] + " turns " + current["markets"][s]["state"] for s in changes)
                if changes else "Daily trend board")
    dated = date.fromisoformat(current["day_et"]).strftime("%d %b %Y") + " close, ET"
    summary = "; ".join(MARKETS[s] + " " + current["markets"][s]["state"] for s in MARKETS)
    changed = ("Changed since the previous session: " + "; ".join(MARKETS[s] + " " +
               previous["markets"][s]["state"] + " to " + current["markets"][s]["state"] for s in changes) + "."
               if changes else "No state changes since the previous session." if previous
               else "Previous-session comparison is not available for this first board.")
    blocks = []
    for symbol, name in MARKETS.items():
        market = current["markets"][symbol]
        lines = [name + " " + market["state"] + ". Mean closes: 20 sessions " + market["means"]["mean_close_20"]
                 + "; 50 sessions " + market["means"]["mean_close_50"] + "."]
        for row in market["rows"]:
            period = row["sample_period"]
            lines.append(BEHAVIOURS[row["behaviour"]] + " (" + row["side"].lower() + "): " + row["mean_r"]
                         + "R mean on " + str(row["n"]) + " cases, " + period["start"] + " to " + period["end"] + ".")
        if not market["rows"]:
            lines.append("No measured condition holds.")
        blocks.append("\n".join(lines))
    return {"headline": headline, "dated": dated, "summary": summary, "changes": changed,
            "blocks": blocks, "lead_market": changes[0] if changes else next(iter(MARKETS))}


def chunks(lines, limit):
    result, held = [], ""
    for line in lines:
        if len(line) > limit:
            raise ValueError("BOARD_COMPLETE_LINE_EXCEEDS_PLATFORM_LIMIT")
        if held and len(held) + 1 + len(line) > limit:
            result.append(held)
            held = ""
        held += ("\n" if held else "") + line
    return [*result, *([held] if held else [])]


def payloads(current, previous, reference, asset):
    copy = compose(current, previous)
    credit = "Chart: TradingView" if asset.get("tradingview_snapshot") else "Graphic: Capital Chronicle"
    method = "Method and limits: " + reference["canonical_url"]
    explanation = "Historical model estimates after costs; R is the stop distance. Past results are not forecasts."
    body = "\n\n".join([copy["headline"], copy["dated"], copy["summary"], copy["changes"],
        current["yardstick_rule"], *copy["blocks"],
        explanation, method, PUBLIC_NOTICE, CONFLICTS_NOTICE, credit])
    root = copy["headline"] + "\n" + copy["dated"] + "\n" + copy["summary"]
    # A large change headline goes into complete replies, never a cut sentence.
    if len(root) > 280:
        root = "Daily trend board\n" + copy["dated"] + "\n" + copy["summary"]
    replies = chunks([method, PUBLIC_NOTICE, CONFLICTS_NOTICE, credit, copy["changes"],
                      current["yardstick_rule"], explanation,
                      *[line for block in copy["blocks"] for line in block.splitlines()]], 280)
    posts = [{"text": text, "media_asset_ids": [asset["asset_id"]] if i == 0 else [],
              "order": i, "role": "root" if i == 0 else "reply"} for i, text in enumerate([root, *replies])]
    common = {"media_asset_ids": [asset["asset_id"]]}
    return {"x": [{"destination": "x", "text": root, "full_text": "\n\n".join([root, *replies]),
                    "posts": posts, "reply_texts": replies, **common}],
            "substack_notes": [{"destination": "substack_notes", "text": body, "full_text": body, **common}],
            "discord": [{"destination": "discord", "text": text, "full_text": text, **common}
                        for text in chunks(body.splitlines(), 1900)]}


def neo_snapshot(market, interval, folder):
    """One guest Download image in Neo; no native dialog or private layout."""
    from .neo_endpoint_executor_v1 import NeoMcpClient
    from . import tradingview_snapshot_v1 as tv
    client = NeoMcpClient(task_name="cc537 trend board", group_title="codex/cc537-trend-board")

    def worker(args):
        page = client.open("tradingview", args["url"])
        observed = client.snapshot(page)
        if "Sign in" not in observed.get("text", ""):
            raise tv.SnapshotError("TRADINGVIEW_GUEST_CHART_REQUIRED")
        button = next((r for r in observed["refs"] if r["role"] == "button"
                       and "snapshot" in r["name"].lower()), None)
        if not button:
            raise tv.SnapshotError("TRADINGVIEW_SNAPSHOT_CONTROL_UNAVAILABLE")
        client.act(page, "click", ref=button["ref"])
        menu = client.snapshot(page)
        download = next((r for r in menu["refs"] if "Download image" in r["name"]), None)
        if not download:
            raise tv.SnapshotError("TRADINGVIEW_DOWNLOAD_IMAGE_UNAVAILABLE")
        result = client.value(client.call("download", {"page": page, "ref": download["ref"]})) or {}
        if isinstance(result.get("value"), dict):
            result = result["value"]
        source = Path(result.get("path") or result.get("filePath") or "")
        if not source.is_file():
            raise tv.SnapshotError("TRADINGVIEW_DOWNLOAD_PATH_UNAVAILABLE")
        target = Path(args["out_dir"]) / source.name
        shutil.copyfile(source, target)
        return {"path": str(target), "suggested_filename": source.name,
                "legend": observed.get("text", ""), "page_title": observed.get("title"),
                "captured_at_utc": datetime.now(timezone.utc).isoformat()}

    taken = tv.capture(market, interval, folder, worker=worker)
    from .publication_image_contract_v1 import bind_scale
    return bind_scale(market, taken)


def prepare_media(current, previous, folder, *, snapshot=None):
    from . import tradingview_snapshot_v1 as tv
    copy = compose(current, previous)
    row = {"key": identity(current["day_et"]), "symbol": copy["lead_market"],
           "at_utc": current["as_of_utc"], "levels": {"valid_until_utc":
           (utc(current["as_of_utc"]) + timedelta(days=10)).isoformat()}}
    asset = tv.plan_snapshot(row, folder, snapshot=snapshot or neo_snapshot)
    if asset:
        return asset
    state = json.loads((folder / "tradingview_capture_v1.json").read_bytes())
    asset = tv.fallback_card(title="Daily trend board", facts=[
        (MARKETS[s], current["markets"][s]["state"] + "; 20-session mean " +
         current["markets"][s]["means"]["mean_close_20"] + "; 50-session mean " +
         current["markets"][s]["means"]["mean_close_50"]) for s in MARKETS],
        dated_line=copy["dated"], out_dir=folder / "media_assets", kicker="Market trends")
    asset["snapshot_failure"] = {"cause": state.get("first_cause") or state["cause"],
                                 "attempts": state["attempts"], "decision": 82}
    asset["provenance_status"] = "VERIFIED_CAPITAL_CHRONICLE_DESK_BOARD"
    asset["rights_basis"] = "Capital Chronicle's own computed states and mean levels from CC-528's public board (CC-537, decision 82)."
    return asset


def register(store, board, *, source_path, output_root, now, snapshot=None):
    from .destination_transport_registry_v1 import REGISTRY_VERSION, registration_for_destination
    from .measured_odds_series_v1 import confirmed_method_page
    current = project(board, now=now)
    key = identity(current["day_et"])
    held = store.get_outbox_message(key)
    if held:
        return json.loads(held["payload"])
    reference = confirmed_method_page(store)
    if not reference:
        raise BoardSourceError("CC536_METHOD_PAGE_NOT_CONFIRMED")
    previous = None
    for row in store.list_outbox_messages(destination=DESTINATION):
        candidate = json.loads(row["payload"])["current"]
        if candidate["day_et"] < current["day_et"] and (previous is None or candidate["day_et"] > previous["day_et"]):
            previous = candidate
    folder = Path(output_root).resolve() / current["day_et"] / current["board_content_hash"][:16]
    folder.mkdir(parents=True, exist_ok=True)
    frozen = folder / "board.public.json"
    raw = canonical_bytes(board)
    if frozen.exists() and frozen.read_bytes() != raw:
        # Before registration, a producer correction may complete missing fields.
        # No issued package exists yet; retain that source under its own hash.
        frozen = folder / ("board-" + sha256(raw).hexdigest()[:16] + ".public.json")
    frozen.write_bytes(raw)
    asset = prepare_media(current, previous, folder, snapshot=snapshot)
    copies = payloads(current, previous, reference, asset)
    value = {"policy": POLICY, "board_id": key, "current": current, "previous": previous,
             "source_path": str(source_path), "frozen_path": str(frozen), "frozen_sha256": sha256(raw).hexdigest(),
             "reference": reference, "media_assets": [asset], "links": [], "counts_as_article": False}
    # The established per-destination link plans keep failures local and make
    # all Discord parts exactly-once, including a lost response to a later part.
    for destination in ("discord", "substack_notes", "x"):
        for index, payload in enumerate(copies[destination]):
            link_id = key + "-" + destination + "-" + str(index)
            route = registration_for_destination(destination)
            plan = {"schema_version": "contentops.publication_plan.v1", "plan_analysis_link": link_id,
                "story_identity": key, "article_identity": key, "package_identity": link_id,
                "output_dir": str(folder), "transport_registry_version": REGISTRY_VERSION,
                "policy_mode_version": "AUTONOMOUS_DEFAULT:CC537", "publication_window": {"window_identity": key},
                "destinations": [{"destination": destination, "surface": route.surface,
                    "transport_type": route.transport_type, "payload": payload["full_text"],
                    "payload_hash": sha256(payload["full_text"].encode()).hexdigest(),
                    "canonical_url": reference["canonical_url"]}]}
            plan["plan_hash"] = sha256_of(plan)
            link = {"kind": "daily_trend_board", "policy": POLICY, "board_id": key, "link_id": link_id,
                    "destination": destination, "part": index, "canonical_url": reference["canonical_url"],
                    "native_payload": payload, "media_assets": [asset], "plan": plan}
            value["links"].append(link)
    context = {"article": {"title": compose(current, previous)["headline"],
                           "market_asset": compose(current, previous)["lead_market"]}, "media": {"assets": [asset]}}
    (folder / "run_context_v1.json").write_bytes(canonical_bytes(context))
    # Save the root before its links; a crash resumes the same sealed payload.
    store.create_work_item(story_id=key, work_item_id=key, title="Daily trend board", target_surface="MULTI_PLATFORM")
    store.register_outbox_message(message_id=key, work_item_id=key, destination=DESTINATION,
                                 payload=canonical_bytes(value).decode(), status="EDITORIAL_INTERNAL")
    return value


def validate_link(store, link, *, now=None):
    root = store.get_outbox_message(link.get("board_id", ""))
    value = json.loads(root["payload"]) if root else {}
    if value.get("policy") != POLICY or link not in value.get("links", []):
        raise ValueError("BOARD_EXACT_FROZEN_LINK_REQUIRED")
    raw = Path(value["frozen_path"]).read_bytes()
    if sha256(raw).hexdigest() != value["frozen_sha256"]:
        raise ValueError("BOARD_FROZEN_SOURCE_CHANGED")
    current = project(json.loads(raw), now=now or utc(value["current"]["as_of_utc"]))
    if current != value["current"]:
        raise ValueError("BOARD_PUBLIC_PROJECTION_CHANGED")
    copies = payloads(current, value["previous"], value["reference"], value["media_assets"][0])
    if link["native_payload"] != copies[link["destination"]][link["part"]]:
        raise ValueError("BOARD_PUBLIC_COPY_CHANGED")
    if now is not None and current["day_et"] != latest_close(now):
        raise BoardSourceError("BOARD_PUBLIC_DAY_EXPIRED", day_et=current["day_et"], latest_close_et=latest_close(now))
    return value


def validate_media(store, intent):
    link = json.loads(store.get_outbox_message(intent["work_item_id"])["payload"])
    value = validate_link(store, link)
    if intent.get("media_assets") != value["media_assets"]:
        raise ValueError("BOARD_MEDIA_SELECTION_CHANGED")
    asset, = value["media_assets"]
    if sha256(Path(asset["path"]).read_bytes()).hexdigest() != asset["sha256"]:
        raise ValueError("BOARD_MEDIA_BYTES_CHANGED")
    if asset.get("tradingview_snapshot"):
        from .tradingview_snapshot_v1 import validate_snapshot_asset
        from .publication_image_contract_v1 import validate_scale
        market = compose(value["current"], value["previous"])["lead_market"]
        validate_snapshot_asset(asset, {"market_asset": market})
        validate_scale(market, asset["tradingview_snapshot"])
    else:
        failure = asset.get("snapshot_failure") or {}
        packet = asset.get("data_card_packet") or {}
        expected = [[MARKETS[s], value["current"]["markets"][s]["state"] + "; 20-session mean " +
                     value["current"]["markets"][s]["means"]["mean_close_20"] + "; 50-session mean " +
                     value["current"]["markets"][s]["means"]["mean_close_50"]] for s in MARKETS]
        if (failure.get("decision") != 82 or not failure.get("cause") or failure.get("attempts", 0) < 2
                or packet.get("facts") != expected or asset.get("modality") != "plan_fact_card"):
            raise ValueError("BOARD_DECISION82_FACT_CARD_REQUIRED")
    return {"policy": POLICY, "image_sha256": asset["sha256"]}


def run_due(store, *, output_root, board_path=SOURCE, now=None, publish=True, automatic_neo=False,
            snapshot=None, deliver=None):
    """One cheap minute slice; always recover uncertain issued objects first."""
    from .durable_operational_store_v1 import LeaseConflictError
    now = utc(now or datetime.now(timezone.utc))
    owner = "cc537-" + uuid4().hex
    try:
        lease = store.acquire_lease(POLICY, owner, ttl_seconds=300)
    except LeaseConflictError:
        return {"state": "BOARD_ALREADY_RUNNING"}
    outcomes = []
    try:
        # Complete/reconcile exact issued packets even if the source moved,
        # disappeared, expired or was corrected. Fresh writes recheck their day.
        for row in store.list_outbox_messages(destination=DESTINATION):
            value = json.loads(row["payload"])
            outcomes.extend(_deliver(store, value, publish, automatic_neo, deliver, now))
        held = store.get_outbox_message(identity(latest_close(now)))
        if held:
            return {"state": "BOARD_REUSED", "day_et": latest_close(now), "outcomes": outcomes,
                    "acceptance": acceptance(store)}
        board = json.loads(Path(board_path).read_bytes())
        current = project(board, now=now)
        if current["day_et"] != latest_close(now):
            return {"state": "BOARD_NEXT_CLOSE_NOT_AVAILABLE", "day_et": current["day_et"],
                    "latest_close_et": latest_close(now), "outcomes": outcomes}
        value = register(store, board, source_path=board_path, output_root=output_root, now=now, snapshot=snapshot)
        outcomes.extend(_deliver(store, value, publish, automatic_neo, deliver, now))
        return {"state": "BOARD_COORDINATOR_RETURNED" if publish else "BOARD_PREPARED",
                "day_et": current["day_et"], "board_id": value["board_id"], "outcomes": outcomes,
                "acceptance": acceptance(store)}
    except BoardSourceError as exc:
        return {"state": "BOARD_SOURCE_UNAVAILABLE", "cause": str(exc), **exc.details, "outcomes": outcomes}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {"state": "BOARD_NOT_COMPLETED", "cause": type(exc).__name__ + ":" + str(exc)[:200], "outcomes": outcomes}
    finally:
        store.release_lease(lease["lease_id"], owner, lease["fencing_token"])


def _deliver(store, value, publish, automatic_neo, deliver, now):
    from . import plan_analysis_pages_v1 as pages
    outcomes = []
    for link in value["links"]:
        if not store.get_outbox_message(link["link_id"]):
            store.create_work_item(story_id=value["board_id"], work_item_id=link["link_id"],
                                   title="Daily trend board", target_surface="MULTI_PLATFORM")
            store.register_outbox_message(message_id=link["link_id"], work_item_id=link["link_id"],
                destination=pages.DESTINATION, payload=canonical_bytes(link).decode(), status="EDITORIAL_INTERNAL")
        status = pages.link_status(store, link)
        outcome = status
        if publish and not status["confirmed"]:
            # A stale unsent packet does not starve today's board. An identified
            # or uncertain attempt still takes the existing exact readback path.
            uncertain = status["status"] in {"UNKNOWN_WRITE", "DISPATCH_ATTEMPT_STARTED", "NATIVE_NEO_PENDING",
                                             "DISPATCH_CONFIRMED", "NATIVE_NEO_TOOL_PENDING"}
            if value["current"]["day_et"] != latest_close(now) and not uncertain:
                outcome = {"state": "BOARD_PUBLIC_DAY_EXPIRED", "day_et": value["current"]["day_et"]}
            else:
                try:
                    options = {"command": "readback"} if uncertain else {}
                    outcome = (deliver or pages.continue_link)(store, link, invocation_id="cc537-minute-consumer",
                                                               automatic_neo=automatic_neo, **options)
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    outcome = {"state": "BOARD_DESTINATION_NOT_COMPLETED", "cause": str(exc)[:200]}
        outcomes.append({"link_id": link["link_id"], "destination": link["destination"],
                         "outcome": outcome, "readback": pages.link_status(store, link)})
    return outcomes


def acceptance(store):
    """Only reconciled public identities count; fixtures never become live days."""
    from . import plan_analysis_pages_v1 as pages
    days = []
    for row in store.list_outbox_messages(destination=DESTINATION):
        value = json.loads(row["payload"])
        states = [{"destination": link["destination"], **pages.link_status(store, link)} for link in value["links"]]
        complete = bool(states) and all(s["confirmed"] and s.get("public_object_id") and s.get("public_object_url")
                                        for s in states)
        days.append({"day_et": value["current"]["day_et"], "board_sha256": value["frozen_sha256"],
                     "complete": complete, "channels": states})
    days.sort(key=lambda d: d["day_et"])
    streak, best, previous, objects = 0, 0, None, set()
    for day in days:
        identities = [(s["destination"], s["public_object_id"]) for s in day["channels"] if s.get("public_object_id")]
        if any(key in objects for key in identities) or len(set(identities)) != len(identities):
            day["complete"] = False
            day["cause"] = "PUBLIC_OBJECT_REUSED_FOR_DIFFERENT_BOARD"
        objects.update(identities)
        streak = (streak + 1 if previous and trading_age(previous, day["day_et"]) == 1 else 1) if day["complete"] else 0
        best = max(best, streak)
        previous = day["day_et"]
    return {"required_consecutive_trading_days": 3, "observed_consecutive_trading_days": best,
            "passed": best >= 3, "days": days}
