"""CC-689 entrypoint for one daily or Sunday wrap through the existing publisher."""
from __future__ import annotations

import argparse
from datetime import timedelta
from hashlib import sha256
import json
from pathlib import Path
import re
from uuid import uuid4

from . import market_wrap_editorial_v1 as editorial, market_wrap_sources_v1 as sources
from .capital_chronicle_latest_report_consumer_v1 import sha256_of
from .destination_transport_registry_v1 import (
    REGISTRY_VERSION, V1_REQUIRED_DERIVATIVE_DESTINATIONS, V1_REQUIRED_PUBLICATION_DESTINATIONS,
    registration_for_destination,
)
from .durable_operational_store_v1 import ContentOpsDurableStore, LeaseConflictError
from .public_market_quote_v1 import save, utcnow
from .publication_coordinator_v1 import (
    ATTEMPT_STARTED, NATIVE_NEO_PENDING, RECONCILED_CONFIRMED, UNKNOWN_WRITE,
    DurablePublicationCoordinator, V1_QUALITY_PROBATION_POLICY_ID,
)
from .published_content_v1 import PRODUCTION_STORE

DESTINATION = "internal:market-wrap"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROLLOUT = ROOT / "config/native_desktop_rollout_v1.json"
WRAP_ID = re.compile(r"cc689-(?:daily|weekly)-\d{4}-\d{2}-\d{2}")
ROUTES = (*V1_REQUIRED_PUBLICATION_DESTINATIONS, "substack_notes")
WRAP_DESTINATIONS = (*ROUTES, "linkedin_company")


def is_wrap_id(value):
    return isinstance(value, str) and WRAP_ID.fullmatch(value) is not None


def read_json(path):
    return json.loads(Path(path).read_bytes())


def output_path(rollout, slot):
    # CC-690 also scans these existing edition folders for light-call receipts.
    parent = "weekly" if slot["edition"] == "weekly" else "owner-manual"
    return Path(rollout["editorial_output_root"]) / parent / slot["id"]


def dispatch_deadline(pack):
    deadline = sources.utc(pack["slot"]["deadline_utc"])
    if pack["slot"]["edition"] == "daily" and pack["data_cutoff_utc"]:
        deadline = min(deadline, sources.utc(pack["data_cutoff_utc"]) + timedelta(minutes=60))
    return deadline


def select_media(assets, destination):
    return next((asset for asset in assets if bool(asset.get("derivative_only")) ==
                 (destination == "instagram_business" and any(a.get("derivative_only") for a in assets))), None)


def prepare_media(pack, article, markets, folder):
    if article.get("market_asset"):
        from .tradingview_snapshot_v1 import prepare_contract_article
        return prepare_contract_article(article, [], output_dir=folder)
    # The weekly visual describes the Friday closes, including crypto. A
    # Sunday live snapshot could show prices after the period being measured.
    return article, [editorial.chart_for(pack, markets, folder)]


def make_plan(pack, article, assets, folder):
    from .v1_simple_gemini_newsroom_v1 import _public_copy

    identity = pack["slot"]["id"]
    targets = []
    for destination in ROUTES:
        route = registration_for_destination(destination)
        targets.append({
            "destination": destination, "surface": route.surface, "transport_type": route.transport_type,
            "adapter": route.adapter, "expected_destination_identity": route.expected_identity,
            "delivery_media_required": route.delivery_media_required,
            "canonical_url_dependency": None if destination == "substack" else "SUBSTACK_ARTICLE",
            "canonical_url_state": "CANONICAL_SUBSTACK_TO_BE_ESTABLISHED" if destination == "substack"
                                   else "PENDING_NON_DISPATCHABLE",
        })
    plan = {
        "schema_version": "contentops.publication_plan.v1", "market_wrap": identity,
        "run_id": identity, "story_identity": identity, "article_identity": sha256_of(article),
        "package_identity": sha256_of([identity, sha256_of(pack), [a["sha256"] for a in assets]]),
        "article_content_sha256": sha256(_public_copy(article).encode()).hexdigest(),
        "compiler_input_sha256": sha256_of(article), "accepted_evidence_ids": [sha256_of(pack)],
        "accepted_evidence_sha256": sha256_of(pack), "source_provenance_binding_preserved": True,
        "distribution_policy": "SUBSTACK_FIRST_V1", "substack_first_dependency": True,
        "output_dir": str(folder.resolve()), "transport_registry_version": REGISTRY_VERSION,
        "policy_mode_version": "AUTONOMOUS_DEFAULT:CC689_DECISION_98",
        "publication_window": {"window_identity": identity, "expires_at_utc": dispatch_deadline(pack).isoformat()},
        "quality_probation_policy_id": V1_QUALITY_PROBATION_POLICY_ID, "full_v1_distribution_required": True,
        "required_publication_destinations": list(V1_REQUIRED_PUBLICATION_DESTINATIONS),
        "required_derivative_destinations": list(V1_REQUIRED_DERIVATIVE_DESTINATIONS),
        "editorial_features": {"reader_format": "WEEKEND_WRAP" if pack["slot"]["edition"] == "weekly" else "PRE_US_WRAP"},
        "artifact_refs": {"article_manifest": "article_manifest_v1.json",
                          "native_derivative_previews": "native_derivative_previews_v1.json"},
        "media_asset_count": len(assets),
        "destinations": targets,
    }
    if article.get("tradingview_instagram_skip"):
        plan["image_optional_policy"] = "JIM_DECISION_124"
        plan["skipped_derivative_destinations"] = [{
            "destination": "instagram_business", "status": "SKIPPED_IMAGE_REQUIRED",
            "disposition": "SKIPPED_IMAGE_REQUIRED", "reason": article["tradingview_instagram_skip"],
        }]
    return {**plan, "plan_hash": sha256_of(plan)}


def stage(store, pack, manuscript, folder, *, media=prepare_media, claim_check=None):
    identity = pack["slot"]["id"]
    if not is_wrap_id(identity):
        raise ValueError("WRAP_SLOT_ID_INVALID")
    if held := store.get_outbox_message(identity):
        return json.loads(held["payload"])
    if claim_check:
        manuscript = editorial.review_claims(pack, manuscript, folder, call=claim_check)
    article, markets = editorial.article_for(pack, manuscript)
    article, assets = media(pack, article, markets, folder)
    plan = make_plan(pack, article, assets, folder)
    article_payloads = {destination: editorial.derivative_payload(article, select_media(assets, destination),
        "https://capitalchronicle.substack.com/p/pending-publication", destination)
        for destination in (*ROUTES[1:], "linkedin_company")}
    files = {"article_manifest_v1.json": article, "wrap-pack.json": pack, "wrap-manuscript.json": manuscript,
             "run_context_v1.json": {"article": article, "selection": {}, "media": {"assets": assets}},
             "native_derivative_previews_v1.json": {"packages": article_payloads}}
    for name, value in files.items():
        save(folder / name, value)
    packet = {"identity": identity, "plan": plan, "media_assets": assets,
              "artifact_hashes": {name: sha256((folder / name).read_bytes()).hexdigest() for name in files}}
    store.create_work_item(work_item_id=identity, story_id=identity, title=article["title"], target_surface="MULTI_PLATFORM")
    store.register_outbox_message(message_id=identity, work_item_id=identity, destination=DESTINATION,
        payload=json.dumps(packet, ensure_ascii=False, sort_keys=True), status="EDITORIAL_INTERNAL")
    return packet


def validated_plan(store, identity, plan_hash):
    row = store.get_outbox_message(identity)
    if (not is_wrap_id(identity) or not row or row["destination"] != DESTINATION):
        raise ValueError("WRAP_FROZEN_PACKET_REQUIRED")
    packet = json.loads(row["payload"])
    plan = packet["plan"]
    if packet["identity"] != identity or plan["plan_hash"] != plan_hash:
        raise ValueError("WRAP_FROZEN_PLAN_CHANGED")
    root = Path(plan["output_dir"]).resolve()
    for name, digest in packet["artifact_hashes"].items():
        if sha256((root / name).read_bytes()).hexdigest() != digest:
            raise ValueError("WRAP_FROZEN_ARTIFACT_CHANGED")
    for asset in packet["media_assets"]:
        path = Path(asset["path"]).resolve()
        if not path.is_relative_to(root / "media") or sha256(path.read_bytes()).hexdigest() != asset["sha256"]:
            raise ValueError("WRAP_FROZEN_CHART_CHANGED")
    return packet


def before_write(coordinator, intent, destination):
    identity = intent["work_item_id"]
    if intent["market_wrap"] != identity:
        raise ValueError("WRAP_INTENT_IDENTITY_CHANGED")
    packet = validated_plan(coordinator.store, identity, intent["plan_hash"])
    plan = packet["plan"]
    deadline = sources.utc(plan["publication_window"]["expires_at_utc"])
    now = coordinator._clock()
    if now >= deadline:
        raise ValueError("WRAP_PUBLICATION_DEADLINE_ELAPSED")
    if destination != "substack":
        canonical = coordinator._confirmed_canonical_url_for_work_item(identity, plan_hash=plan["plan_hash"])
        if not canonical or intent.get("canonical_url") != canonical:
            raise ValueError("WRAP_CANONICAL_LINK_UNCONFIRMED")
        article = read_json(Path(plan["output_dir"]) / "article_manifest_v1.json")
        expected = editorial.derivative_payload(article, select_media(packet["media_assets"], destination),
                                                canonical, destination)
        actual = intent.get("native_payload")
        if actual != expected:
            raise ValueError("WRAP_DERIVATIVE_TEXT_OR_MEDIA_CHANGED")
    from .article_publication_quality_v1 import image_register, piece_id
    if coordinator.published_content_path is not None:
        assets = packet["media_assets"]
        article = read_json(Path(plan["output_dir"]) / "article_manifest_v1.json")
        from .publication_image_contract_v1 import bounded_text_fallback
        fallback = bounded_text_fallback(article, plan["output_dir"], now=now) if not assets else None
        image_register(coordinator).reserve(piece_id=piece_id(coordinator.store, intent), assets=assets,
            lead_asset_id=assets[0]["asset_id"] if assets else None, now=now,
            canonical_url=intent.get("canonical_url"), enforce_cap=destination == "substack",
            text_fallback=fallback, market=article.get("market_asset"),
            image_contract=article.get("publication_image_contract"))
    return deadline.isoformat()


def previous_confirmed(store, coordinator, identity):
    candidates = []
    day = identity[-10:]
    for row in store.list_outbox_messages(destination=DESTINATION):
        if row["message_id"] == identity or row["message_id"][-10:] > day:
            continue
        packet = json.loads(row["payload"])
        old = packet["identity"]
        if (not is_wrap_id(old) or not coordinator._confirmed_canonical_url_for_work_item(
                old, plan_hash=packet["plan"]["plan_hash"])):
            continue
        # A daily wrap following Sunday's edition uses the actual Sunday
        # publication as the reference (its market data is Friday's close).
        candidates.append((old[-10:], old, packet))
    if not candidates:
        return None
    _, _, packet = max(candidates, key=lambda candidate: candidate[:2])
    root = Path(packet["plan"]["output_dir"])
    raw = (root / "wrap-pack.json").read_bytes()
    if sha256(raw).hexdigest() != packet["artifact_hashes"]["wrap-pack.json"]:
        raise ValueError("WRAP_PREVIOUS_SOURCE_PACK_CHANGED")
    return json.loads(raw)


def publication_coordinator(store, plan, *, allow_publish=True):
    from .native_neo_executor_v1 import bind_native_neo_coordinator
    from .neo_endpoint_executor_v1 import NeoMcpClient
    identity = plan["market_wrap"]
    client = NeoMcpClient(task_name=identity, group_title="codex/" + identity)
    coordinator, _ = bind_native_neo_coordinator(store, operation_id=identity,
        output_dir=Path(plan["output_dir"]) / "native-neo", native_invocation_id=None,
        allow_publish=allow_publish, automatic=True, endpoint_client=client)
    coordinator.recovery_scope = {"work_item_id": identity, "plan": plan, "exact_work_item_only": True}
    coordinator.allow_prior_confirmed_distribution = True
    return coordinator


def continue_wrap(store, packet, *, clock=utcnow, factory=publication_coordinator):
    from .native_neo_executor_v1 import NativeNeoInputRequired

    identity, plan = packet["identity"], packet["plan"]
    expired = clock() >= sources.utc(plan["publication_window"]["expires_at_utc"])
    coordinator = factory(store, plan, allow_publish=not expired)

    def pending_request(pending):
        return {k: pending.request.get(k)
                for k in ("request_sha256", "destination", "action", "endpoint_cause")}

    if expired:
        # Reconcile exactly the actions that could have started. A pending
        # readback on one surface does not suppress the others.
        recovery = {}
        for dispatch in store.get_dispatches_for_work_item(identity):
            if dispatch["status"] not in {UNKNOWN_WRITE, ATTEMPT_STARTED, NATIVE_NEO_PENDING,
                                          "SUBSTACK_DRAFT_AWAITING_OWNER"}:
                continue
            try:
                recovery[dispatch["platform"]] = coordinator.readback_existing_dispatch(dispatch["dispatch_id"])
            except NativeNeoInputRequired as pending:
                recovery[dispatch["platform"]] = {"pending_native_request": pending_request(pending)}
        publication = {**coordinator.publication_state(identity, plan), "recovery": recovery, "deadline_elapsed": True}
    else:
        try:
            publication = coordinator.publish_plan(identity, plan)
        except NativeNeoInputRequired as pending:
            publication = {**coordinator.publication_state(identity, plan),
                           "pending_native_request": pending_request(pending)}
    outcomes = publication.get("per_destination") or {}
    unconfirmed = {}
    for destination in WRAP_DESTINATIONS:
        outcome = outcomes.get(destination) or {}
        if not (DurablePublicationCoordinator._confirmed_public_object(outcome, destination=destination)
                and outcome.get("reconciliation_status") == RECONCILED_CONFIRMED):
            unconfirmed[destination] = (outcome.get("reason_code") or outcome.get("reconciliation_status")
                                        or outcome.get("status") or "NOT_DISPATCHED")
    return {**publication, "unconfirmed_wrap_destinations": unconfirmed}


def run_due(store, *, rollout, now=None, clock=utcnow, cash_calendar=None, gather=sources.collect,
            writer=editorial.draft, publish=continue_wrap, media=prepare_media, resume=None, claim_check=None):
    now = sources.utc(now or clock())
    if resume:
        if not is_wrap_id(resume):
            raise ValueError("WRAP_SLOT_ID_INVALID")
        identity = resume
    else:
        cash_calendar = cash_calendar if cash_calendar is not None else read_json(sources.CASH_CALENDAR)
        slot = sources.slot_at(now, cash_calendar)
        if slot is None:
            return {"state": "WRAP_NO_EDITION_DUE"}
        if now < sources.utc(slot["start_utc"]):
            return {"state": "WRAP_NOT_YET_DUE", "slot": slot}
        identity = slot["id"]
    lease_owner = identity + ":" + uuid4().hex
    try:
        lease = store.acquire_lease(identity, lease_owner, ttl_seconds=3 * 3600 + 300)
    except LeaseConflictError:
        return {"state": "WRAP_ALREADY_RUNNING", "identity": identity}
    try:
        held = store.get_outbox_message(identity)
        if held:
            if held["destination"] != DESTINATION:
                raise ValueError("WRAP_FROZEN_PACKET_REQUIRED")
            packet = json.loads(held["payload"])
            folder = Path(packet["plan"]["output_dir"])
            pack = read_json(folder / "wrap-pack.json")
            slot = pack["slot"]
        elif resume:
            return {"state": "WRAP_NO_RETAINED_EDITION", "identity": identity}
        elif now < sources.utc(slot["deadline_utc"]):
            folder = output_path(rollout, slot)
            # Existing prior editions and frozen artifacts survive process
            # restarts. Never call either provider again for a staged edition.
            pack_file, draft_file = folder / "source-pack.json", folder / "section-draft.json"
            coordinator = DurablePublicationCoordinator(store=store, transport_runtime=None)
            previous = previous_confirmed(store, coordinator, identity)
            if pack_file.is_file():
                pack = read_json(pack_file)
            else:
                pack = gather(slot, now=now, cash_calendar=cash_calendar, previous=previous, clock=clock)
                save(pack_file, pack)
            if clock() >= dispatch_deadline(pack):
                return {"state": "WRAP_SOURCE_WINDOW_EXPIRED", "slot": slot, "source_gaps": pack["gaps"]}
            manuscript = read_json(draft_file) if draft_file.is_file() else writer(pack, folder)
            if not draft_file.is_file():
                save(draft_file, manuscript)
            if clock() >= dispatch_deadline(pack):
                return {"state": "WRAP_EDITORIAL_WINDOW_EXPIRED", "slot": slot, "source_gaps": pack["gaps"]}
            if claim_check is None and writer is editorial.draft:
                from .public_draft_claims_v1 import check_draft
                claim_check = check_draft
            packet = stage(store, pack, manuscript, folder, media=media, claim_check=claim_check)
        else:
            return {"state": "WRAP_WINDOW_ELAPSED_WITHOUT_PACKET", "slot": slot}
        result = {"slot": slot, "identity": identity, "data_cutoff_utc": pack["data_cutoff_utc"],
                  "source_gaps": pack["gaps"], "publication": publish(store, packet, clock=clock),
                  "plan_hash": packet["plan"]["plan_hash"], "recorded_at_utc": clock().isoformat()}
        save(folder / "wrap-result.json", result)
        return result
    finally:
        store.release_lease(lease["lease_id"], lease_owner, lease["fencing_token"])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rollout", type=Path, default=DEFAULT_ROLLOUT)
    parser.add_argument("--resume", help="Read or continue one retained edition under its original deadline")
    parser.add_argument("--publish", action="store_true", help="Run the scheduled job through the live rollout")
    args = parser.parse_args(argv)
    rollout = read_json(args.rollout)
    if not args.publish:
        print(json.dumps({"state": "PREFLIGHT", "slot": sources.slot_at(utcnow(), read_json(sources.CASH_CALENDAR))}))
        return 0
    from .native_desktop_publication_v1 import live_publication_policy
    from .llm_operator_control_v1 import llm_operator_pause_active
    live_publication_policy(rollout)
    if Path(rollout["store_path"]).resolve() != PRODUCTION_STORE.resolve():
        raise ValueError("WRAP_EXACT_PRODUCTION_STORE_REQUIRED")
    if llm_operator_pause_active() and not args.resume:
        print(json.dumps({"state": "LLM_OPERATOR_PAUSED"}))
        return 0
    store = ContentOpsDurableStore(rollout["store_path"], auto_migrate=False)
    result = run_due(store, rollout=rollout, resume=args.resume)
    # Keep sensitive tool transports and bulky artifacts in the retained
    # operation. The task's stdout reports only its bounded disposition.
    publication = result.get("publication") or {}
    print(json.dumps({k: result[k] for k in ("state", "identity", "slot", "source_gaps") if k in result}
        | {"canonical_url": publication.get("canonical_url"),
           "distribution_status": publication.get("distribution_status"),
           "unconfirmed_wrap_destinations": publication.get("unconfirmed_wrap_destinations")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
