"""CC-468: one source-bound daily Note, through the existing link coordinator.

The minute consumer calls run_due; no timer, transport or parallel store lives
here. A native MAX text call chooses among public, fresh Main analyses and
writes the copy. Code carries exact source, image and public-object bindings.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
from uuid import uuid4
from zoneinfo import ZoneInfo

from .capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from .event_article_guard_v1 import PUBLIC_NOTICE, CONFLICTS_NOTICE
from . import plan_analysis_pages_v1 as pages

POLICY = "CC468_DAILY_SUBSTACK_NOTE_V1"
ET = ZoneInfo("America/New_York")
FORCES = ("macro", "priced_in", "positioning", "fundamental", "geopolitical")
MONTH = re.compile(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\b", re.I)
# The voice guide's terms, with whole-word matching. Unknown capitals are never
# a refusal: Ops Product's 11 Nov amendment expressly keeps real acronyms usable.
BANNED = (
    "model estimate", "base-case chance", "the model", "our model", "model position", "demo account", "demo",
    "paper account", "paper trading", "AI-run", "AI-generated", "as an AI", "language model", "LLM", "GPT",
    "Claude", "Fable", "Opus", "Gemini", "Codex", "Antigravity", "Anthropic", "OpenAI", "system prompt",
    "the prompt", "AI agent", "subagent", "vol-normalised", "volatility-normalised", "z-score", "sd over",
    "ATR", "SMA", "EFFR", "USD leg", "front-end gap", "context about", "clear by D1 sign", "calls judged",
    "time exits", "not triggered", "Levels use the plan's prices", "over the period to", "the desk is bullish on",
    "the desk is bearish on", "from our", "ET run", "analysis run", "frozen call", "freeze id", "known-at",
    "cost admission", "admission check", "armed plan", "arming run", "Guardian pass", "kernel", "our ledger",
    "shadow call", "short-term lane", "mid-term lane", "long-term lane", "role pack", "reply pack",
    "our account", "trading account", "account balance", "account size", "our balance", "equity curve",
    "lot size", "position size", "our leverage", "CFD", "Exness", "MT5", "IBKR", "Interactive Brokers",
    "buy now", "sell now", "you should", "we recommend", "guaranteed", "risk-free", "will definitely", "Jim",
    "GMT+7", "UTC",
)


def utc(value):
    result = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("NOTE_SOURCE_CLOCK_TIMEZONE_REQUIRED")
    return result.astimezone(timezone.utc)


def day_at(now):
    return utc(now).astimezone(ET).date().isoformat()


def identity(day):
    # Parsing also prevents path traversal in the operator CLI.
    if datetime.strptime(day, "%Y-%m-%d").date().isoformat() != day:
        raise ValueError("NOTE_DAY_INVALID")
    return "substack-daily-note-" + day


def capture_clock(packet):
    """Original capture clock, never report generation or refreshed media time."""
    spec = packet["source_manifest"]["role-pack.json"]
    raw = Path(spec["path"]).read_bytes()
    if sha256(raw).hexdigest() != spec["sha256"]:
        raise ValueError("NOTE_SOURCE_ROLE_PACK_CHANGED")
    role = json.loads(raw)
    expected = (role.get("sources") or {}).get("capture.json") or {}
    capture_path = Path(spec["path"]).parent / "capture.json"
    raw = capture_path.read_bytes()
    if sha256(raw).hexdigest() != expected.get("sha256"):
        raise ValueError("NOTE_SOURCE_CAPTURE_CHANGED")
    capture = json.loads(raw)
    return {"data_cutoff_utc": utc(capture["known_at_utc"]).isoformat(),
            "path": str(capture_path), "sha256": expected["sha256"], "field": "/known_at_utc"}


def check_fresh(clock, now):
    age = utc(now) - utc(clock["data_cutoff_utc"])
    if not timedelta(0) <= age <= timedelta(minutes=60):
        raise ValueError("NOTE_DATA_CUTOFF_EXPIRED_OR_FUTURE")


def validate_copy(authored, page):
    sentences = authored.get("sentences") or []
    if not 2 <= len(sentences) <= 4:
        raise ValueError("NOTE_TWO_TO_FOUR_SENTENCES_REQUIRED")
    parts, dated, technical = [], False, 0
    for index, item in enumerate(sentences):
        text, excerpt, section = item.get("text", ""), item.get("source_excerpt", ""), item.get("section")
        paragraphs = (page["manuscript"]["sections"].get(section) or {}).get("paragraphs") or []
        if not excerpt or not any(excerpt in p["text"] for p in paragraphs):
            raise ValueError("NOTE_SENTENCE_SOURCE_UNBOUND")
        if pages._numbers(text) - pages._numbers(excerpt):
            raise ValueError("NOTE_NUMBER_UNBOUND")
        if index == 0 and section not in FORCES:
            raise ValueError("NOTE_MUST_LEAD_WITH_MARKET_FORCE")
        technical += section == "technical"
        if section not in (*FORCES, "technical", "scenarios") or technical > 1:
            raise ValueError("NOTE_FORCE_LAYER_INVALID")
        if not text.strip() or text != text.strip() or not re.search(r"[.!?]$", text) or len(text.split()) > 35:
            raise ValueError("NOTE_COMPLETE_SHORT_SENTENCE_REQUIRED")
        date = item.get("fact_date", "")
        if date:
            if not MONTH.search(date) or date not in text or date not in excerpt or not pages._numbers(text):
                raise ValueError("NOTE_DATED_FIGURE_UNBOUND")
            dated = True
        parts.append(text)
    body = " ".join(parts)
    if not dated:
        raise ValueError("NOTE_DATED_FIGURE_REQUIRED")
    if len(body) > 400 or re.search(r"[\r\n]|…|\.\.\.|[{}]|(?:^|\s)[•]", body):
        raise ValueError("NOTE_SHAPE_OR_LENGTH_INVALID")
    if re.search(r"\b[A-Z]{2,}(?:_[A-Z0-9]+)+\b|#[0-9a-f]{6,}|\b(?:M1|M5|M15|M30|H1|H4|D1|W1)\b", body):
        raise ValueError("NOTE_INTERNAL_TERM_FORBIDDEN")
    if any(re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", body, re.I) for term in BANNED):
        raise ValueError("NOTE_INTERNAL_TERM_FORBIDDEN")
    if not all(isinstance(authored.get(k), str) and authored[k] and authored[k] in body
               for k in ("view", "invalidation")):
        raise ValueError("NOTE_VIEW_AND_INVALIDATION_REQUIRED")
    pages.public_filter(body)
    return body


def writer_prompt(candidates):
    public = [{"page_id": p["page_id"], "market": p["source_plan"]["asset_id"],
               "sections": p["manuscript"]["sections"]} for p in candidates]
    return ("Write today's one Substack Note. Choose the main market from the supplied public analyses. "
        "Return JSON only: {page_id, sentences:[{text,section,source_excerpt,fact_date}],view,invalidation}. "
        "Two to four complete sentences, 400 characters maximum in total before notices; no bullets, title or link. "
        "Each sentence has at most 35 words. Lead with the force driving the market: prefer macro/policy, then "
        "priced_in, positioning/flows, fundamental, geopolitical. At most one technical sentence. Give one dated "
        "figure, our conditional view and the level that ends it. Copy a supporting source_excerpt verbatim from "
        "the selected section's paragraph for each sentence. fact_date is the exact public date, e.g. '3 Nov', "
        "in that excerpt and sentence; omit it on other sentences. Every number and analytical claim comes from "
        "the supplied analysis. Preserve its sign, units, horizon and conditions. Never manufacture a scenario, "
        "odds, date, causal explanation or new invalidation. view and invalidation are exact substrings of your "
        "sentences. Use plain reader language, no internal terms, model labels, ellipses or clipped sentences. "
        "The chart and the two notices are attached by code. Banned terms: " + ", ".join(BANNED)
        + "\nPUBLIC MAIN ANALYSES:\n" + json.dumps(public, ensure_ascii=False))


def _copy_chart(page, folder):
    from .tradingview_snapshot_v1 import validate_snapshot_asset
    asset = next((a for a in page.get("media_assets", []) if a.get("modality") == "tradingview_chart_snapshot"), None)
    if not asset:
        raise ValueError("NOTE_TRADINGVIEW_CHART_REQUIRED")
    asset = deepcopy(asset)
    validate_snapshot_asset(asset, {"market_asset": page["source_plan"]["asset_id"]})
    media = folder / "media"
    media.mkdir(parents=True, exist_ok=True)
    for container, field, prefix in ((asset, "path", "note-chart-"), (asset["tradingview_snapshot"], "path", "original-")):
        old = Path(container[field])
        target = media / (prefix + asset["sha256"][:16] + old.suffix)
        if target.exists() and target.read_bytes() != old.read_bytes():
            raise ValueError("NOTE_RETAINED_CHART_CHANGED")
        shutil.copyfile(old, target)
        container[field] = str(target.resolve())
    return asset


def register_note(store, page, authored, *, output_root, now):
    from .destination_transport_registry_v1 import REGISTRY_VERSION, registration_for_destination
    day = day_at(now)
    key = identity(day)
    prior = store.get_outbox_message(key)
    if prior:
        return json.loads(prior["payload"])
    pages.validate_plan(store, page["page_id"], page["plan"])
    status = pages.page_status(store, page)
    if not status["confirmed"]:
        raise ValueError("NOTE_SOURCE_PAGE_NOT_CONFIRMED")
    clock = capture_clock(page)
    check_fresh(clock, now)
    body = validate_copy(authored, page)
    folder = Path(output_root).resolve() / day
    folder.mkdir(parents=True, exist_ok=True)
    asset = _copy_chart(page, folder)
    text = body + "\n\n" + PUBLIC_NOTICE + "\n" + CONFLICTS_NOTICE + "\nChart: TradingView"
    payload = {"destination": "substack_notes", "text": text, "full_text": text,
               "media_asset_ids": [asset["asset_id"]]}
    route = registration_for_destination("substack_notes")
    plan = {"schema_version": "contentops.publication_plan.v1", "plan_analysis_link": key,
        "story_identity": key, "article_identity": key, "package_identity": key, "output_dir": str(folder),
        "transport_registry_version": REGISTRY_VERSION, "policy_mode_version": "AUTONOMOUS_DEFAULT:CC468",
        "publication_window": {"window_identity": key},
        "destinations": [{"destination": "substack_notes", "surface": route.surface,
            "transport_type": route.transport_type, "payload": text, "payload_hash": sha256(text.encode()).hexdigest(),
            "canonical_url": status["canonical_url"]}]}
    plan["plan_hash"] = sha256_of(plan)
    value = {"policy": POLICY, "kind": "daily_note", "link_id": key, "day_et": day,
        "page_id": page["page_id"], "plan_id": page["plan_id"], "destination": "substack_notes",
        "canonical_url": status["canonical_url"], "source_clock": clock,
        "source_page_sha256": sha256_of(page), "authored": authored, "body": body,
        "native_payload": payload, "media_assets": [asset], "plan": plan}
    context = {"article": {"title": "Daily market Note", "market_asset": page["source_plan"]["asset_id"]},
               "media": {"assets": [asset]}}
    (folder / "run_context_v1.json").write_bytes(canonical_bytes(context))
    (folder / "note.txt").write_text(text, encoding="utf-8")
    store.create_work_item(story_id=key, work_item_id=key, title="Daily market Note", target_surface="SUBSTACK_NOTE")
    store.register_outbox_message(message_id=key, work_item_id=key, destination=pages.DESTINATION,
        payload=canonical_bytes(value).decode(), status="EDITORIAL_INTERNAL")
    return value


def validate_note(store, value, *, now=None):
    page = json.loads(store.get_outbox_message(value["page_id"])["payload"])
    pages.validate_plan(store, page["page_id"], page["plan"])
    if (value.get("policy") != POLICY or value["link_id"] != identity(value["day_et"])
            or sha256_of(page) != value["source_page_sha256"]
            or capture_clock(page) != value["source_clock"]
            or pages.page_status(store, page)["canonical_url"] != value["canonical_url"]):
        raise ValueError("NOTE_SOURCE_BINDING_CHANGED")
    body = validate_copy(value["authored"], page)
    text = body + "\n\n" + PUBLIC_NOTICE + "\n" + CONFLICTS_NOTICE + "\nChart: TradingView"
    asset, = value["media_assets"]
    original = next((a for a in page["media_assets"] if a["sha256"] == asset["sha256"]), None)
    from .tradingview_snapshot_v1 import validate_snapshot_asset
    validate_snapshot_asset(asset, {"market_asset": page["source_plan"]["asset_id"]})
    expected = {"destination": "substack_notes", "text": text, "full_text": text, "media_asset_ids": [asset["asset_id"]]}
    destination, = value["plan"]["destinations"]
    if (not original or body != value["body"] or expected != value["native_payload"]
            or destination["destination"] != "substack_notes" or destination["payload"] != text
            or destination["payload_hash"] != sha256(text.encode()).hexdigest()
            or destination["canonical_url"] != value["canonical_url"]):
        raise ValueError("NOTE_COPY_OR_CHART_CHANGED")
    if now is not None:
        check_fresh(value["source_clock"], now)
        if day_at(now) != value["day_et"]:
            raise ValueError("NOTE_PUBLIC_DAY_EXPIRED")
    return value


def run_due(store, *, output_root, now=None, writer=None, publish=True, automatic_neo=False):
    """One bounded pass under the existing store lease; returns its exact cause."""
    from .durable_operational_store_v1 import LeaseConflictError
    now = utc(now or datetime.now(timezone.utc))
    key = identity(day_at(now))
    owner = "cc468-" + uuid4().hex
    try:
        lease = store.acquire_lease(key, owner, ttl_seconds=180)
    except LeaseConflictError:
        return {"state": "NOTE_ALREADY_RUNNING", "day_et": day_at(now)}
    try:
        held = store.get_outbox_message(key)
        if held:
            value = json.loads(held["payload"])
        else:
            candidates, causes = [], []
            for row in store.list_outbox_messages(destination=pages.DESTINATION):
                page = json.loads(row["payload"])
                if row["message_id"] != page.get("page_id"):
                    continue
                try:
                    clock = capture_clock(page)
                    check_fresh(clock, now)
                    if not pages.page_status(store, page)["confirmed"]:
                        continue
                    pages.validate_plan(store, page["page_id"], page["plan"])
                    if not any(a.get("modality") == "tradingview_chart_snapshot" for a in page.get("media_assets", [])):
                        raise ValueError("NOTE_TRADINGVIEW_CHART_REQUIRED")
                    candidates.append(page)
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    causes.append({"page_id": page.get("page_id"), "cause": str(exc)[:160]})
            if not candidates:
                return {"state": "NOTE_WAITING_SOURCE", "day_et": day_at(now), "source_causes": causes}
            # Freshest edition of each market; the actual writer chooses today's
            # main market on the public argument, not a hard-coded market rank.
            candidates.sort(key=lambda p: (p["freeze"]["frozen_at_utc"], p["page_id"]), reverse=True)
            latest = {}
            for page in candidates:
                latest.setdefault(page["source_plan"]["asset_id"], page)
            candidates = list(latest.values())
            edition = sha256_of([p["page_id"] + sha256_of(p) for p in candidates])
            folder = Path(output_root).resolve() / day_at(now) / ("writer-" + edition[:16])
            call_file = folder / "call.json"
            if call_file.is_file() and not (folder / "response.json").is_file():
                return {"state": "NOTE_WRITER_FAILED", "call_path": str(call_file), "day_et": day_at(now)}
            if (folder / "response.json").is_file():
                authored = json.loads((folder / "response.json").read_bytes())
            else:
                from .x_reply_bot_v1 import _text_call
                authored, _ = (writer or _text_call)(writer_prompt(candidates), root=folder, writer=True)
            page = next((p for p in candidates if p["page_id"] == authored.get("page_id")), None)
            if not page:
                raise ValueError("NOTE_WRITER_SOURCE_PAGE_NOT_SELECTED")
            value = register_note(store, page, authored, output_root=output_root, now=now)
        if not publish:
            return {"state": "NOTE_PREPARED", "note_id": key, "day_et": value["day_et"]}
        outcome = pages.continue_link(store, value, invocation_id="cc468-daily-note",
                                      automatic_neo=automatic_neo)
        return {"state": "NOTE_COORDINATOR_RETURNED", "note_id": key, "day_et": value["day_et"], "outcome": outcome}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {"state": "NOTE_NOT_SENT", "day_et": day_at(now), "cause": str(exc)[:200]}
    finally:
        store.release_lease(lease["lease_id"], owner, lease["fencing_token"])
