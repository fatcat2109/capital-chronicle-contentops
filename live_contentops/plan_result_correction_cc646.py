"""The exact CC-646 correction, replied to the two confirmed wrong result objects."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

from . import plan_status_posts_v1 as posts

CONTRACT = "CC646_USDJPY_RESULT_CORRECTION_V1"
KEY = "cc646-usdjpy-result-correction-20261117"
ORIGINAL = "plan-result-post-f5ecb8c81fed4b645e17580901ac7ff0"
CANCEL_REASON = "CC646_WRONG_RESULT_CANCELLED_UNCLAIMED"
BODY = ("USD/JPY: correction. Our 02:00 ET update said this plan was not triggered. That was wrong. "
        "Price traded inside the entry zone, 159.02–159.38, from 01:29 ET until the entry window "
        "closed at 02:00 ET, so the entry condition was met. A fault in our own entry system meant "
        "no position was opened. That was our failure, not the market's.")
TEXT = BODY + "\n\n" + posts.PUBLIC_NOTICE + " " + posts.CONFLICTS_NOTICE
DELIVERY_TEXT = TEXT + "\n\n" + posts.CHART_CREDIT


def _originals(store):
    original = store.get_outbox_message(ORIGINAL)
    if not original or original["destination"] != posts.DESTINATION:
        raise ValueError("CC646_EXACT_ORIGINAL_REQUIRED")
    with store.get_read_only_connection() as conn:
        pending = conn.execute("SELECT o.destination,o.status,d.status AS dispatch_status FROM outbox_messages o "
            "LEFT JOIN platform_dispatches d USING(message_id) WHERE o.work_item_id=? "
            "AND o.destination IN ('facebook_page','instagram_business','threads','x')", (ORIGINAL,)).fetchall()
    if len(pending) != 4 or any(r["status"] != "DEFINITE_NO_WRITE" or r["dispatch_status"] != "DEFINITE_NO_WRITE" for r in pending):
        raise ValueError("CC646_ORIGINAL_PENDING_WRITES_MUST_BE_SETTLED")
    parents = {}
    for dispatch in store.get_dispatches_for_work_item(ORIGINAL):
        destination = dispatch["platform"]
        if dispatch["status"] == "DEFINITE_NO_WRITE":
            continue
        if dispatch["status"] != "DISPATCH_CONFIRMED" or not dispatch["public_object_id"]:
            raise ValueError("CC646_ORIGINAL_READBACK_REQUIRED:" + destination)
        if destination not in {"telegram", "discord"}:
            raise ValueError("CC646_ADDITIONAL_PUBLIC_COPY:" + destination)
        intent = json.loads(store.get_outbox_message(dispatch["message_id"])["payload"])
        parents[destination] = {"public_object_id": dispatch["public_object_id"],
            "public_object_url": dispatch["public_object_url"],
            **({"thread_parent_id": intent["native_payload"]["discord_thread_parent_id"]}
               if destination == "discord" else {})}
    if set(parents) != {"telegram", "discord"} or parents["telegram"]["public_object_id"] != "189":
        raise ValueError("CC646_EXACT_PUBLIC_PARENTS_REQUIRED")
    return hashlib.sha256(original["payload"].encode()).hexdigest(), parents


def validate(store, row):
    original_hash, parents = _originals(store)
    if (row.get("key") != KEY or row.get("text") != TEXT
            or row.get("correction_reply_contract") != CONTRACT
            or row.get("original_sha256") != original_hash or row.get("correction_parents") != parents):
        raise ValueError("CC646_SUPPLIED_CORRECTION_OR_PARENT_CHANGED")
    asset, source = row["retained_chart"], row["original_media"]
    if (hashlib.sha256(Path(source["context_path"]).read_bytes()).hexdigest() != source["context_sha256"]
            or hashlib.sha256(Path(asset["path"]).read_bytes()).hexdigest() != source["asset_sha256"]
            or asset["sha256"] != source["asset_sha256"]
            or posts._utc(asset["tradingview_snapshot"]["captured_at_utc"]) > posts._utc("2026-11-17T07:00:00Z")):
        raise ValueError("CC646_ORIGINAL_PLAN_CHART_CHANGED_OR_AFTER_EVENT")


def prepare(store, *, root=posts.POST_ROOT, media_source=None):
    original_hash, parents = _originals(store)
    if not store.get_outbox_message(KEY):
        if media_source is None:
            with store.get_read_only_connection() as conn:
                originals = conn.execute("SELECT o.payload FROM platform_dispatches d JOIN outbox_messages o USING(message_id) "
                    "WHERE d.platform='telegram' AND d.public_object_id='188' AND d.status='DISPATCH_CONFIRMED'").fetchall()
            if len(originals) != 1:
                raise ValueError("CC646_ORIGINAL_PLAN_CHART_REQUIRED")
            media_source = Path(json.loads(originals[0]["payload"])["output_dir"])
        media_source = Path(media_source)
        context_path = media_source / "run_context_v1.json"
        source_context = json.loads(context_path.read_bytes())
        asset = source_context["media"]["assets"][0]
        folder = Path(root) / KEY
        media = folder / "media_assets"
        media.mkdir(parents=True, exist_ok=True)
        target = media / Path(asset["path"]).name
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() != asset["sha256"]:
            raise ValueError("CC646_RETAINED_CHART_PATH_CONFLICT")
        shutil.copyfile(asset["path"], target)
        asset = {**asset, "path": str(target.resolve())}
        manifest = json.loads((media_source / "delivery_media_manifest_v1.json").read_bytes())
        for hosted in manifest["assets"]:
            if hosted.get("sha256") == asset["sha256"]:
                hosted["absolute_local_source_path"] = asset["path"]
        (folder / "delivery_media_manifest_v1.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        store.create_work_item(story_id=KEY, title="USD/JPY: correction", target_surface="MULTI_PLATFORM", work_item_id=KEY)
        row = {"schema_version": posts.SCHEMA, "key": KEY, "symbol": "USDJPY", "kind": "correction",
            "state": "CORRECTION", "title": "USD/JPY: correction", "text": TEXT, "conditional_calls": [],
            "at_utc": datetime.now(timezone.utc).isoformat(), "correction_reply_contract": CONTRACT,
            "original_sha256": original_hash, "correction_parents": parents,
            "retained_chart": asset, "original_media": {"context_path": str(context_path.resolve()),
                "context_sha256": hashlib.sha256(context_path.read_bytes()).hexdigest(), "asset_sha256": asset["sha256"]},
            "authority": "BACKLOG CC-646; exact supplied correction; decisions 84 and 136"}
        store.register_outbox_message(message_id=KEY, work_item_id=KEY, destination=posts.DESTINATION,
                                      payload=json.dumps(row, ensure_ascii=False), status="CC646_CORRECTION_PREPARED")
    validate(store, posts._row_payload(store, KEY))
    return posts.prepare_post(store, KEY, root=root, destinations=tuple(sorted(parents)))


def destination_payloads(row, *, card_id):
    if card_id != row["retained_chart"]["asset_id"]:
        raise ValueError("CC646_ORIGINAL_PLAN_CHART_REQUIRED")
    payloads = {}
    for destination, parent in row["correction_parents"].items():
        payloads[destination] = {"destination": destination, "text": DELIVERY_TEXT, "full_text": DELIVERY_TEXT,
            "media_asset_ids": [card_id], "reply_to_id": parent["public_object_id"],
            "reply_to_url": parent["public_object_url"], "correction_reply_contract": CONTRACT,
            **({"discord_thread_parent_id": parent["thread_parent_id"]} if destination == "discord" else {})}
    return payloads


def main(argv=None):
    """One exact-item action, using the existing coordinator and API transports."""
    import argparse
    from .durable_operational_store_v1 import ContentOpsDurableStore
    from .publication_coordinator_v1 import DurablePublicationCoordinator, CanonicalDestinationTransportRuntimeV1
    from .destination_transport_registry_v1 import DestinationReadinessManager
    from .published_content_v1 import PRODUCTION_STORE

    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("cancel", "prepare", "publish", "status"))
    parser.add_argument("--store", type=Path, default=PRODUCTION_STORE)
    parser.add_argument("--root", type=Path, default=posts.POST_ROOT)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args(argv)
    store = ContentOpsDurableStore(args.store, auto_migrate=False)
    if args.phase == "cancel":
        coordinator = DurablePublicationCoordinator(store=store, transport_runtime=None)
        with store.get_read_only_connection() as conn:
            rows = conn.execute("SELECT message_id,destination,status FROM outbox_messages WHERE work_item_id=? "
                "AND destination IN ('facebook_page','instagram_business','threads','x')", (ORIGINAL,)).fetchall()
        result = {"outcomes": [coordinator.cancel_unclaimed_status_post(row["message_id"], reason=CANCEL_REASON)
            if row["status"] in {"READY", "DEFINITE_NO_WRITE"} else dict(row) for row in rows]}
    elif args.phase in {"prepare", "publish"}:
        plan = prepare(store, root=args.root)
        if args.phase == "prepare":
            result = {"plan": plan, "final_text": DELIVERY_TEXT}
        else:
            runtime = CanonicalDestinationTransportRuntimeV1()
            coordinator = DurablePublicationCoordinator(store=store, transport_runtime=runtime,
                readiness_manager=DestinationReadinessManager(store=store))
            posts.scope_to_post(coordinator, KEY, plan)
            result = coordinator.execute_plan(KEY, plan)
    else:
        result = {"original": store.get_dispatches_for_work_item(ORIGINAL),
                  "correction": store.get_dispatches_for_work_item(KEY)}
    evidence = {"item": "CC-646", "phase": args.phase, "store_path": str(args.store.resolve()),
                "observed_at_utc": datetime.now(timezone.utc).isoformat(), "result": result}
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    args.evidence.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"phase": args.phase, "evidence": str(args.evidence),
        "per_destination": {k: {f: v.get(f) for f in ("status", "reason_code", "public_object_id", "public_object_url")}
                            for k, v in result.get("per_destination", {}).items()}}))


if __name__ == "__main__":
    main()
