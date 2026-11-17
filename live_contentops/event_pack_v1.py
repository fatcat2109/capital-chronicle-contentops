"""CC-404 structured event records, using Main's public projections and sole publisher.

Code assembles supplied facts and maps. It does not forecast, choose a branch,
infer an armed plan or score a call. Each stage is an immutable outbox object.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re

from .capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from .event_article_guard_v1 import PUBLIC_NOTICE, CONFLICTS_NOTICE, check_publication_copy, reader_conditional_call_text
from .event_public_record_v1 import load_record
from .public_call_scorecard_v1 import public_time
from .published_content_v1 import utc

DESTINATION = "internal:event-public-pack"
PACK_ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\event-packs")
LEDGER_PATH = Path(r"A:\Capital Chronicle\ResearchRuns\plan-status-v1\calls-ledger.public.json")
STATUS_PATH = LEDGER_PATH.with_name("plan-status.public.json")
STAGES = {"preview", "arrival", "review"}


def review_due_at(release):
    from zoneinfo import ZoneInfo
    local = release.astimezone(ZoneInfo("Asia/Bangkok"))
    return (local+timedelta(days=1)).replace(hour=7, minute=0, second=0, microsecond=0).astimezone(timezone.utc)


def _read(spec):
    raw = Path(spec["path"]).read_bytes()
    if len(raw) > 2_000_000 or sha256(raw).hexdigest() != spec["sha256"]:
        raise ValueError("EVENT_PACK_SOURCE_BYTES_CHANGED")
    return json.loads(raw)


def public_ledger(spec):
    doc = _read(spec)
    keys = {"calls", "chain_tip", "content_hash", "generated_at_utc", "notice", "registrations", "results", "schema", "state_changes"}
    if set(doc) != keys or doc["schema"] != "CapitalChronicleCallsLedgerPublicV1":
        raise ValueError("EVENT_PUBLIC_LEDGER_SCHEMA_INVALID")
    if sha256_of({k: v for k, v in doc.items() if k != "content_hash"}) != doc["content_hash"]:
        raise ValueError("EVENT_PUBLIC_LEDGER_HASH_INVALID")
    # Recheck the producer projection rather than admitting a private ledger
    # merely because its filename ends in public.json.
    from .plan_analysis_pages_v1 import public_filter
    public_filter(json.dumps(doc, ensure_ascii=False))
    return doc


def _arrival(spec, record, *, now):
    value = _read(spec)
    keys = {"schema_version", "event_id", "event_time_utc", "known_at_utc", "frozen_sha256",
            "print", "matched_branches", "armed_plan_ids"}
    if (set(value) != keys or value["schema_version"] != "contentops.event_arrival.public.v1"
            or value["event_id"] != record["event_id"] or value["frozen_sha256"] != record["sha256"]
            or utc(value["event_time_utc"]) != utc(record["event_time_utc"])
            or not utc(record["event_time_utc"]) <= utc(value["known_at_utc"]) <= now):
        raise ValueError("EVENT_ARRIVAL_EVENT_OR_CLOCK_INVALID")
    fact = value["print"]
    if set(fact) != {"display", "label", "publisher", "source_url", "source", "excerpt", "rights_class"}:
        raise ValueError("EVENT_ARRIVAL_PRINT_SCHEMA_INVALID")
    raw = Path(fact["source"]["path"]).read_bytes()
    if sha256(raw).hexdigest() != fact["source"]["sha256"]:
        raise ValueError("EVENT_ARRIVAL_PRINT_BYTES_CHANGED")
    text = raw.decode("utf-8-sig")
    if (not fact["display"] or fact["display"] not in fact["excerpt"] or fact["excerpt"] not in text
            or not fact["source_url"].startswith("https://")
            or fact["rights_class"] not in {"BLS_US_FEDERAL_PUBLIC_DOMAIN_TEXT", "US_FEDERAL_PUBLIC_DOMAIN"}):
        raise ValueError("EVENT_ARRIVAL_PUBLIC_PRINT_BINDING_INVALID")
    size = len(record["record"]["reaction_map"])
    if (not isinstance(value["matched_branches"], list)
            or any(type(i) is not int or not 0 <= i < size for i in value["matched_branches"])
            or len(set(value["matched_branches"])) != len(value["matched_branches"])):
        raise ValueError("MAIN_EVENT_MATCHED_BRANCH_REQUIRED")
    return value


def compose(packet, stage, *, now=None):
    """Pure structured rendering. Input bindings remain metadata, never copy."""
    now = now or datetime.now(timezone.utc)
    if stage not in STAGES:
        raise ValueError("EVENT_PACK_STAGE_INVALID")
    record = load_record(packet["frozen_public_record"], event_id=packet["event_id"],
        event_time_utc=packet["planned_release_utc"], cutoff_utc=now.isoformat())
    release = utc(record["event_time_utc"])
    rows = record["record"]["reaction_map"]
    calls = [{k: r[k] for k in ("condition", "market", "direction", "horizon", "invalidation")} for r in rows]
    name = packet["title"]
    lines, source_specs, review_rows = [], [packet["frozen_public_record"]], []
    if stage == "preview":
        if now > release - timedelta(hours=2):
            raise ValueError("EVENT_PREVIEW_DEADLINE_MISSED_USE_NEXT_EVENT")
        lines = [reader_conditional_call_text(calls[0])]
        selected = range(len(rows))
    else:
        if now < release:
            raise ValueError("EVENT_RELEASE_NOT_ARRIVED")
        arrival = _arrival(packet["event_arrival_record"], record, now=now)
        source_specs.extend([packet["event_arrival_record"], arrival["print"]["source"]])
        fact = arrival["print"]
        lines = [f"We compare {fact['publisher']}'s {fact['label']} print of {fact['display']} with our frozen map.",
                 f"Released {public_time(record['event_time_utc'])} ({fact['publisher']})."]
        selected = arrival["matched_branches"]
        status_spec = packet["plan_status_record"]
        status = _read(status_spec)
        if (sha256_of({k: v for k, v in status.items() if k != "content_hash"}) != status["content_hash"]
                or not utc(arrival["known_at_utc"]) <= utc(status["generated_at_utc"]) <= now
                or (stage == "arrival" and now - utc(status["generated_at_utc"]) > timedelta(minutes=10))):
            raise ValueError("EVENT_PLAN_STATUS_SOURCE_INVALID_OR_STALE")
        source_specs.append(status_spec)
        plans = {p["plan_id"]: p for p in status["plans"]}
        armed = []
        for plan_id in arrival["armed_plan_ids"]:
            p = plans.get(plan_id, {})
            if p.get("status") not in {"TRIGGERED", "FILLED"}:
                raise ValueError("EVENT_ARMED_PLAN_NOT_RECOGNISED_BY_MAIN")
            armed.append(p["asset_id"])
        lines.append("Plans armed: " + (", ".join(armed) if armed else "none in Main's supplied event record") + ".")
        if stage == "arrival" and now - release > timedelta(minutes=15):
            raise ValueError("EVENT_ARRIVAL_OLDER_THAN_15_MINUTES")
        if stage == "review":
            if now < review_due_at(release):
                raise ValueError("EVENT_REVIEW_NEXT_MORNING_NOT_DUE")
            ledger_spec = packet["calls_ledger_record"]
            ledger = public_ledger(ledger_spec)
            source_specs.append(ledger_spec)
            # G05 binds its plan hashes in source_ref. Join all ledger calls
            # from those exact plans, never a hand-picked ID list or date/market.
            plans = {h for r in rows for h in re.findall(r"plan_sha256=([a-f0-9]{64})", r["source_ref"])}
            wanted = {c["public_call_id"] for c in ledger["calls"] if c.get("source_plan_hash") in plans}
            if not wanted:
                raise ValueError("EVENT_REVIEW_MAIN_CALL_BINDINGS_REQUIRED")
            score_spec = packet.get("score_status_record", status_spec)
            scores = _read(score_spec)
            if (sha256_of({k:v for k,v in scores.items() if k != "content_hash"}) != scores["content_hash"]
                    or utc(scores["generated_at_utc"]) > now):
                raise ValueError("EVENT_MAIN_SCORE_EXPORT_INVALID")
            source_specs.append(score_spec)
            scored = {r["public_call_id"]: r for r in scores.get("scored_calls", [])}
            endings = {r["public_call_id"]: r for r in ledger["results"]}
            for call in ledger["calls"]:
                if call["public_call_id"] not in wanted:
                    continue
                result = scored.get(call["public_call_id"])
                ending = endings.get(call["public_call_id"], {})
                review_rows.append({"call": call, "score": result,
                    "result_text": result["result"] if result else "Not triggered; not scored"
                        if ending.get("state") == "NOT_SCORED_UNTRIGGERED" else "Unresolved"})
            lines += ["", "Our complete event call record", "| Public call | Market | Main's result |", "| --- | --- | --- |"]
            lines += [f"| {r['call']['public_call_id']} | {r['call']['market']} | {r['result_text']} |" for r in review_rows]
            lines.append(f"Total event calls: {len(review_rows)}. Scored by Main: {sum(r['score'] is not None for r in review_rows)}.")
    if consensus := packet.get("single_consensus_fact"):
        from .contentops_editorial_desk_v1 import _retain_consensus_fact
        bound = _retain_consensus_fact(consensus, cutoff_utc=now.isoformat(), event_time_utc=record["event_time_utc"])
        fact = bound["retained_record"]
        lines.append(f"Consensus: {fact['source_value_text']} ({fact['source']}, {fact['reference_period']}).")
    elif stage != "preview":
        lines.append("No pre-release consensus was retained for this event.")
    lines += ["", "Our map (Capital Chronicle model estimate)"]
    if not list(selected):
        lines.append("No branch matched in Main's supplied event record.")
    for index in selected:
        row = rows[index]
        if stage != "preview" or index:
            lines.append(reader_conditional_call_text(calls[index]))
        lines += [f"Minimum move: {row['minimum_move']}.", f"> Naive release beta: {row['naive_release_beta']}"]
    if stage == "preview":
        for p in record["record"]["q1_probabilities"]:
            lines.append(f"{p['question']}: {p['outcome']}, {p['probability']} (Capital Chronicle model estimate).")
    lines += ["", "So what: the conditions and invalidations above define how we judge this map.",
              f"Frozen {record['frozen_at_et']}. SHA-256: {record['sha256']}."]
    if packet.get("calls_ledger_record"):
        ledger = public_ledger(packet["calls_ledger_record"])
        if utc(ledger["generated_at_utc"]) > now:
            raise ValueError("EVENT_PUBLIC_LEDGER_AFTER_CUTOFF")
        source_specs.append(packet["calls_ledger_record"])
        lines.append(f"Calls ledger observed {public_time(ledger['generated_at_utc'])}. SHA-256: {packet['calls_ledger_record']['sha256']}. Chain tip: {ledger['chain_tip']}.")
    lines += ["", PUBLIC_NOTICE, CONFLICTS_NOTICE]
    body = "\n\n".join(lines)
    check_publication_copy({"body": body}, conditional_calls=calls, require_call_text=False)
    from .plan_analysis_pages_v1 import public_filter
    public_filter(body)
    title = {"preview": "Our reaction map", "arrival": "The release against our map", "review": "Our event call record"}[stage] + ": " + name
    return {"event_id": record["event_id"], "stage": stage, "title": title, "subtitle": lines[0],
        "body_markdown": body, "conditional_calls": calls, "record": record,
        "source_specs": source_specs, "review_rows": review_rows}


def register_pack(store, packet, stage, *, root=PACK_ROOT, now=None):
    """One immutable stage per event. Its original public hash is never edited."""
    identity = "event-pack-" + packet["event_id"] + "-" + stage
    previous = store.get_outbox_message(identity)
    if previous:
        held = json.loads(previous["payload"])
        if held["input_identity"] != sha256_of(packet):
            raise ValueError("EVENT_PUBLIC_STAGE_IMMUTABLE")
        return held
    input_identity = sha256_of(packet)
    folder = Path(root) / identity
    folder.mkdir(parents=True, exist_ok=True)
    packet = _snapshot_inputs(packet, folder / "sources")
    view = compose(packet, stage, now=now)
    article = {"title": view["title"], "subtitle": view["subtitle"], "dek": view["subtitle"],
        "substack_body_markdown": view["body_markdown"], "conditional_calls": view["conditional_calls"],
        "event_id": packet["event_id"], "article_type": "EVENT_PREVIEW" if stage == "preview" else "EVENT_REVIEW" if stage == "review" else "ARTICLE",
        "rights_class": "CC_OWN_ANALYSIS", "frozen_public_record": {k:v for k,v in view["record"].items() if k != "record"},
        "event_pack_stage": stage,
        **({"calls_ledger_record": packet["calls_ledger_record"]} if packet.get("calls_ledger_record") else {})}
    (folder / "article_manifest_v1.json").write_bytes(canonical_bytes(article))
    (folder / "article.md").write_text("# " + view["title"] + "\n\n" + view["body_markdown"], encoding="utf-8")
    (folder / "article.html").write_text('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
        '<style>body{font:18px/1.6 Georgia;max-width:750px;margin:2em auto;padding:0 20px;overflow-wrap:anywhere}</style>'
        '<h1>'+escape(view["title"])+ '</h1><pre style="white-space:pre-wrap;font:inherit">'+escape(view["body_markdown"])+ '</pre>', encoding="utf-8")
    from .fact_card_design_v1 import CardSpec, render_fact_card
    media = folder / "media"
    media.mkdir(exist_ok=True)
    path = media / "event-map.png"
    first = view["record"]["record"]["reaction_map"][0]
    facts = [("Our conditional map", reader_conditional_call_text(view["conditional_calls"][0])),
             ("Minimum move", first["minimum_move"])]
    key_label, key_value = "Minimum move", first["minimum_move"]
    source_line = "Capital Chronicle model estimate"
    card_clock = view["record"]["frozen_at_utc"]
    if stage == "arrival":
        arrival = _read(packet["event_arrival_record"])
        fact = arrival["print"]
        facts = [(fact["label"], fact["display"])]
        for index in arrival["matched_branches"][:1]:
            facts.append(("Our matched call", reader_conditional_call_text(view["conditional_calls"][index])))
        key_label, key_value = fact["label"], fact["display"]
        source_line = fact["publisher"] + "; Capital Chronicle model estimate"
        card_clock = view["record"]["event_time_utc"]
    elif stage == "review":
        total = len(view["review_rows"])
        scored = sum(r["score"] is not None for r in view["review_rows"])
        key_label, key_value = "Scored by Main", f"{scored} of {total}"
        facts = [("Our complete event record", f"{scored} of {total} calls scored; every call retained.")]
        source_line = "Capital Chronicle call record"
        card_clock = _read(packet.get("score_status_record", packet["plan_status_record"]))["generated_at_utc"]
    render_fact_card(path, CardSpec(title=view["title"], facts=facts, key_label=key_label,
        key_value=key_value, source_line=source_line, dated_line=public_time(card_clock)))
    asset = {"asset_id": identity+"-card", "path": str(path.resolve()), "sha256": sha256(path.read_bytes()).hexdigest(),
        "modality": "data_card", "rights_status": "CC_OWN_ANALYSIS", "caption": "Capital Chronicle model estimate",
        "alt_text": " ".join(text for _,text in facts), "source_sha256": view["record"]["sha256"],
        "card_facts": [{"label": label, "text": text} for label,text in facts], "source_bindings": view["source_specs"]}
    assets = [asset]
    from .publication_image_contract_v1 import EFFECTIVE_FROM
    if (now or datetime.now(timezone.utc)) >= EFFECTIVE_FROM:
        from .tradingview_snapshot_v1 import prepare_contract_article
        article.update(macro_data_post=True,
            **({"macro_chart_symbol": packet["macro_chart_symbol"]} if packet.get("macro_chart_symbol") else {}))
        article, assets = prepare_contract_article(article, packet.get("macro_chart_assets") or [], output_dir=folder)
        (folder / "article_manifest_v1.json").write_bytes(canonical_bytes(article))
    (folder / "run_context_v1.json").write_bytes(canonical_bytes({"article": article, "selection": {}, "media": {"assets": assets}}))
    from .destination_transport_registry_v1 import REGISTRY_VERSION, registration_for_destination
    from .v1_simple_gemini_newsroom_v1 import _public_copy
    registration = registration_for_destination("substack")
    plan = {"schema_version": "contentops.publication_plan.v1", "event_pack": identity,
        "story_identity": identity, "article_identity": identity, "package_identity": identity,
        "article_content_sha256": sha256(_public_copy(article).encode()).hexdigest(),
        "output_dir": str(folder.resolve()), "transport_registry_version": REGISTRY_VERSION,
        "policy_mode_version": "AUTONOMOUS_DEFAULT:CC404", "publication_window": {"window_identity": identity},
        "destinations": [{"destination": "substack", "surface": registration.surface,
            "transport_type": registration.transport_type, "payload": view["body_markdown"],
            "payload_hash": sha256(view["body_markdown"].encode()).hexdigest()}]}
    plan["plan_hash"] = sha256_of(plan)
    value = {"identity": identity, "input_identity": input_identity, "inputs": packet, "stage": stage,
        "assembled_at_utc": (now or datetime.now(timezone.utc)).isoformat(),
        "native_payload": {k:view[k] for k in ("title", "subtitle", "body_markdown")},
        "source_specs": view["source_specs"], "media_assets": assets, "plan": plan}
    store.create_work_item(story_id=identity, work_item_id=identity, title=view["title"], target_surface="SUBSTACK_ARTICLE")
    store.register_outbox_message(message_id=identity, work_item_id=identity, destination=DESTINATION,
        payload=canonical_bytes(value).decode(), status="EDITORIAL_INTERNAL")
    return value


def validate_plan(store, work_item_id, plan):
    row = store.get_outbox_message(work_item_id)
    value = json.loads(row["payload"]) if row else {}
    if value.get("identity") != work_item_id or value.get("plan") != plan:
        raise ValueError("EVENT_PACK_EXACT_STORED_STAGE_REQUIRED")
    for source in value["source_specs"]:
        if sha256(Path(source["path"]).read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError("EVENT_PACK_SOURCE_BYTES_CHANGED")
    if value.get("canonical_parent"):
        parent = json.loads(store.get_outbox_message(value["canonical_parent"])["payload"])
        validate_plan(store, parent["identity"], parent["plan"])
        if stage_status(store, parent).get("canonical_url") != value["canonical_url"]:
            raise ValueError("EVENT_PACK_CANONICAL_NOT_CONFIRMED")
        if value["payloads"] != derivative_payloads(parent, value["canonical_url"], value["image_url"]):
            raise ValueError("EVENT_PACK_DERIVATIVE_CHANGED")
        return value
    expected = compose(value["inputs"], value["stage"], now=utc(value["assembled_at_utc"]))
    if value["native_payload"] != {k:expected[k] for k in ("title", "subtitle", "body_markdown")}:
        raise ValueError("EVENT_PACK_PUBLIC_COPY_CHANGED")
    for asset in value["media_assets"]:
        if sha256(Path(asset["path"]).read_bytes()).hexdigest() != asset["sha256"]:
            raise ValueError("EVENT_PACK_MEDIA_CHANGED")
    return value


def validate_intent(store, intent):
    row = store.get_outbox_message(intent["event_pack"])
    value = json.loads(row["payload"])
    validate_plan(store, value["identity"], value["plan"])
    destination = intent["destination_plan"]["destination"]
    expected = value["payloads"][destination] if value.get("payloads") else value["native_payload"]
    if intent.get("native_payload") != expected:
        raise ValueError("EVENT_PACK_INTENT_CHANGED")
    return value


def _snapshot_inputs(value, folder):
    """Freeze mutable public exports as exact bytes before registering a stage."""
    if isinstance(value, dict):
        if set(value) == {"path", "sha256"}:
            raw = Path(value["path"]).read_bytes()
            if sha256(raw).hexdigest() != value["sha256"]:
                raise ValueError("EVENT_PACK_SOURCE_BYTES_CHANGED")
            folder.mkdir(parents=True, exist_ok=True)
            target = folder / (value["sha256"] + Path(value["path"]).suffix)
            from .event_timestamp_v1 import _retain
            _retain(target, raw)
            return {"path": str(target.resolve()), "sha256": value["sha256"]}
        return {k:_snapshot_inputs(v, folder) for k,v in value.items()}
    if isinstance(value, list):
        return [_snapshot_inputs(v, folder) for v in value]
    return value


def stage_status(store, value):
    from .publication_coordinator_v1 import DurablePublicationCoordinator as Coordinator
    per = {}
    for item in value["plan"]["destinations"]:
        dest = item["destination"]
        ids = Coordinator._ids(value["identity"], value["plan"]["plan_hash"], dest)
        dispatch = store.get_platform_dispatch(ids["dispatch_id"]) or {}
        reconciliation = next((r for r in store.get_reconciliations_for_work_item(value["identity"])
            if r["reconciliation_id"] == ids["reconciliation_id"]), {})
        per[dest] = {"status": dispatch.get("status", "NOT_STARTED"),
            "reconciliation_status": reconciliation.get("status"),
            "public_object_id": dispatch.get("public_object_id"), "public_object_url": dispatch.get("public_object_url"),
            "confirmed": dispatch.get("status") == "DISPATCH_CONFIRMED" and reconciliation.get("status") == "RECONCILED_CONFIRMED"}
    canonical = per.get("substack", {})
    return {"identity": value["identity"], "stage": value["stage"], "per_destination": per,
        "canonical_url": canonical.get("public_object_url") if canonical.get("confirmed") else None}


def derivative_payloads(parent, canonical_url, image_url):
    from .plan_status_posts_v1 import _text_parts, _x_pack
    body = parent["native_payload"]["body_markdown"]
    notices = PUBLIC_NOTICE + " " + CONFLICTS_NOTICE
    body = body.replace("\n\n"+PUBLIC_NOTICE+"\n\n"+CONFLICTS_NOTICE, "").strip()
    body += "\n\n" + canonical_url
    card = parent["media_assets"][0]["asset_id"] if parent["media_assets"] else None
    values = {}
    # These are the existing registered routes and text limits. Every part is
    # sourced from the same structured piece and keeps the canonical link.
    limits = {"telegram": 1024, "discord": 2000, "threads": 500, "facebook_page": 60000,
              "instagram_business": 2200, "linkedin": 3000, "x": 280, "youtube": 1000}
    for dest, limit in limits.items():
        parts = _x_pack(body+"\n\n"+notices, limit) if dest == "x" else _text_parts(body, notices, limit)
        if dest in {"linkedin", "facebook_page", "instagram_business"} and len(parts) > 1:
            # Their current adapters have no text thread. Preserve the hash and
            # canonical rather than silently dropping part of the public map.
            lead = parent["native_payload"]["title"] + "\nSHA-256: " + parent["inputs"]["frozen_public_record"]["sha256"]
            parts = [lead+"\n"+canonical_url+"\n\n"+notices]
        posts = [{"text": t, "media_asset_ids": [card] if i == 0 and card else [],
                  **({"image_url": image_url} if i == 0 else {})} for i,t in enumerate(parts)]
        selected = [card] if card else []
        if dest == "instagram_business":
            selected = [a["asset_id"] for a in parent["media_assets"]
                if (a.get("tradingview_snapshot") or {}).get("capture_ratio") == "4:5"] or selected
        value = {"text": parts[0], "full_text": "\n\n".join(parts), "media_asset_ids": selected, "image_url": image_url}
        if len(posts) > 1:
            value["posts"] = posts
        if dest == "x":
            value.update(thread=[p["text"] for p in posts], posts=posts)
        values[dest] = value
    return values


def register_derivatives(store, parent):
    from .destination_transport_registry_v1 import registration_for_destination
    from .publication_coordinator_v1 import V1_REQUIRED_DERIVATIVE_DESTINATIONS
    status = stage_status(store, parent)
    canonical = status["canonical_url"]
    if not canonical:
        return {"status": "EVENT_PACK_CANONICAL_NOT_CONFIRMED"}
    identity = parent["identity"] + "-derivatives"
    previous = store.get_outbox_message(identity)
    if previous:
        return json.loads(previous["payload"])
    image_url = None
    primary = parent["media_assets"][0] if parent["media_assets"] else None
    for row in store.list_outbox_messages(destination="internal:native-neo-tool", work_item_id=parent["identity"]):
        result = json.loads(row["payload"]).get("result", {})
        if (primary and result.get("public_object_url") == canonical and primary["sha256"] in result.get("observed_media_sha256", [])
                and result.get("public_image_urls")):
            image_url = result["public_image_urls"][0]
    if primary and not image_url:
        return {"status": "EVENT_PACK_CANONICAL_IMAGE_NOT_OBSERVED"}
    payloads = derivative_payloads(parent, canonical, image_url)
    rows = []
    from .article_publication_quality_v1 import article_inputs
    article, _, _ = article_inputs({"output_dir": parent["plan"]["output_dir"]})
    for dest in V1_REQUIRED_DERIVATIVE_DESTINATIONS:
        if dest == "instagram_business" and article.get("tradingview_instagram_skip"):
            continue
        registration = registration_for_destination(dest)
        text = payloads[dest]["full_text"]
        rows.append({"destination": dest, "surface": registration.surface, "transport_type": registration.transport_type,
            "canonical_url": canonical, "payload": text, "payload_hash": sha256(text.encode()).hexdigest()})
    plan = {**parent["plan"], "event_pack": identity, "story_identity": identity,
        "article_identity": identity, "package_identity": identity, "destinations": rows}
    plan.pop("plan_hash")
    plan["plan_hash"] = sha256_of(plan)
    value = {**parent, "identity": identity, "canonical_parent": parent["identity"], "canonical_url": canonical,
        "image_url": image_url, "payloads": payloads, "plan": plan}
    store.create_work_item(story_id=identity, work_item_id=identity, title=parent["native_payload"]["title"], target_surface="MULTI_PLATFORM")
    store.register_outbox_message(message_id=identity, work_item_id=identity, destination=DESTINATION,
        payload=canonical_bytes(value).decode(), status="EDITORIAL_INTERNAL")
    return value


def require_mutable(intent):
    """Decision CC-404: a public preview/hash record is never edited."""
    path = Path(str(intent.get("output_dir") or "")) / "article_manifest_v1.json"
    if intent.get("output_dir") and path.is_file():
        article = json.loads(path.read_bytes())
        if article.get("article_type") == "EVENT_PREVIEW" and article.get("frozen_public_record"):
            raise ValueError("CC404_PUBLIC_PREVIEW_IMMUTABLE")


def require_action_clock(article, *, now):
    record = article.get("frozen_public_record") or {}
    if article.get("event_pack_stage") == "arrival" and record:
        if utc(now) > utc(record["event_time_utc"])+timedelta(minutes=15):
            raise ValueError("EVENT_ARRIVAL_PUBLISH_DEADLINE_MISSED")


def resume_pack(store, value, *, invocation_id, command="resume", request_hash=None, response=None):
    from .native_neo_executor_v1 import bind_native_neo_coordinator, NativeNeoInputRequired
    coordinator, executor = bind_native_neo_coordinator(store, operation_id=value["identity"],
        output_dir=Path(value["plan"]["output_dir"]) / "native-neo", native_invocation_id=invocation_id, allow_publish=True)
    coordinator.recovery_scope = {"work_item_id": value["identity"], "plan": value["plan"], "exact_work_item_only": True}
    coordinator.allow_prior_confirmed_distribution = True
    try:
        if command in {"begin", "submit"}:
            request = (executor._get(request_hash, "request") or {}).get("request", {})
            if request.get("work_item_id") not in {value["identity"], "native-neo-operation-"+sha256_of(value["identity"])}:
                raise ValueError("EVENT_PACK_TOOL_REQUEST_MISMATCH")
            return executor.begin(request_hash) if command == "begin" else executor.submit(request_hash, response)
        if command == "readback":
            results = {}
            for item in value["plan"]["destinations"]:
                dispatch = coordinator._ids(value["identity"], value["plan"]["plan_hash"], item["destination"])
                results[item["destination"]] = coordinator.readback_existing_dispatch(dispatch["dispatch_id"])
            return results
        return coordinator.publish_plan(value["identity"], value["plan"])
    except NativeNeoInputRequired as pending:
        return {"state": "NATIVE_NEO_TOOL_PENDING", "native_tool_request": pending.request}


def freeze_ledger(packet, *, root=PACK_ROOT, path=LEDGER_PATH, now=None):
    """Retain the current *public* ledger and its own observed clock/hash."""
    path = Path(path)
    if not path.is_file():
        return packet
    raw = path.read_bytes()
    spec = {"path": str(path), "sha256": sha256(raw).hexdigest()}
    ledger = public_ledger(spec)
    folder = Path(root) / ("ledger-" + packet["event_id"])
    retained = _snapshot_inputs(spec, folder)
    from .event_timestamp_v1 import retain_and_stamp
    retain_and_stamp(retained, event_id=packet["event_id"]+"-ledger", frozen_at_utc=ledger["generated_at_utc"],
        event_time_utc=packet["planned_release_utc"], now=now)
    return {**packet, "calls_ledger_record": retained}


def run_due_packs(store, *, now=None, root=PACK_ROOT, publish=False, resume=resume_pack):
    """One bounded pass inside the existing minute entry, using its store/outbox."""
    from .contentops_editorial_desk_v1 import STORY_PREPARATION
    now = now or datetime.now(timezone.utc)
    latest = {}
    for row in store.list_outbox_messages(destination=STORY_PREPARATION):
        packet = json.loads(row["payload"])
        latest[packet["event_id"]] = packet
    outcomes = []
    for packet in latest.values():
        if not packet.get("event_pack_enabled") or not packet.get("frozen_public_record"):
            continue
        release = utc(packet["planned_release_utc"])
        held_value = None
        for old_stage in ("preview", "arrival", "review"):
            row = store.get_outbox_message("event-pack-"+packet["event_id"]+"-"+old_stage)
            if not row:
                continue
            value = json.loads(row["payload"])
            status = stage_status(store, value)
            derived = store.get_outbox_message(value["identity"]+"-derivatives")
            per = stage_status(store, json.loads(derived["payload"]))["per_destination"] if derived else {}
            if per and all(v["confirmed"] for v in per.values()):
                continue
            canonical = status["per_destination"]["substack"]
            if canonical["status"] == "NOT_STARTED" and (
                    old_stage == "preview" and now > release-timedelta(hours=2)
                    or old_stage == "arrival" and now > release+timedelta(minutes=15)):
                continue
            held_value = value
            break
        stage = held_value["stage"] if held_value else ("preview" if now <= release-timedelta(hours=2) else
                 "arrival" if release <= now <= release+timedelta(minutes=15) else
                 "review" if now >= review_due_at(release) else None)
        if stage is None:
            continue
        if not held_value and stage != "preview" and not packet.get("event_arrival_record"):
            continue
        try:
            if not held_value and stage == "review" and packet.get("event_pack_live_sources"):
                # The preview retains its original ledger snapshot. The review
                # reads today's scored rows and endings, then freezes its own.
                for key,path in (("score_status_record", STATUS_PATH), ("calls_ledger_record", LEDGER_PATH)):
                    raw = path.read_bytes()
                    packet = {**packet, key: {"path": str(path), "sha256": sha256(raw).hexdigest()}}
            # The caller's publication/grant checks remain in the coordinator.
            value = held_value or register_pack(store, packet, stage, root=root, now=now)
            derivative_row = store.get_outbox_message(value["identity"]+"-derivatives")
            if derivative_row:
                per = stage_status(store, json.loads(derivative_row["payload"]))["per_destination"]
                if per and all(v["confirmed"] for v in per.values()):
                    continue
            result = {"identity": value["identity"], "stage": stage, "status": stage_status(store, value)}
            if publish:
                result["publication"] = resume(store, value, invocation_id="event-pack-minute-cc404")
                if stage_status(store, value)["canonical_url"]:
                    derivatives = register_derivatives(store, value)
                    if derivatives.get("plan"):
                        result["derivatives"] = resume(store, derivatives, invocation_id="event-pack-minute-cc404")
                    else:
                        result["derivatives"] = derivatives
            outcomes.append(result)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            outcomes.append({"event_id": packet["event_id"], "stage": stage, "cause": type(exc).__name__+":"+str(exc)[:180]})
        break  # one event per tick; no polling or new job
    return {"events": outcomes, "status": "EVENT_PACK_PASS" if outcomes else "NO_EVENT_PACK_DUE"}
