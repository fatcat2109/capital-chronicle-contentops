"""One exact correction or clarification, replied under the confirmed public objects of an earlier post.

Decision 136: a published post stays as it is, and a correction is a new post under it. CC-646 did this once, by
hand, for the 17 Nov USD/JPY result. This module takes the same steps from a small spec, so a later correction
needs no new code: the spec names the original work item, the destinations (Telegram and Discord, whose replies
the existing transports carry) and the exact body. The store proves each parent (a confirmed dispatch with its
public object), the original post's own chart goes with the reply, and the existing coordinator sends it once.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

from . import plan_status_posts_v1 as posts

CONTRACT = "CORRECTION_REPLY_V1"
KEY_PREFIX = "correction-reply-"
DESTINATIONS = frozenset({"telegram", "discord"})
PREPARED = "CORRECTION_PREPARED"


def text_for(body):
    return body + "\n\n" + posts.PUBLIC_NOTICE + " " + posts.CONFLICTS_NOTICE


def check_body(body):
    """Pre-relaunch audit (23 Nov 2026): a supplied body passes the public-copy rules every other
    post passes (no target, account, size, AI label or relative day; ET times) before it is held.
    A correction already registered keeps its exact text."""
    from .event_article_guard_v1 import check_publication_copy
    from .plan_analysis_pages_v1 import RELATIVE_DAY, public_filter
    from .public_time_v1 import require_public_time
    from . import scenario_voice_v1 as voice

    if not str(body or "").strip():
        raise ValueError("CORRECTION_BODY_REQUIRED")
    if RELATIVE_DAY.search(body):
        raise ValueError("CORRECTION_RELATIVE_DAY_FORBIDDEN")
    public_filter(body)
    voice.validate_copy(body)
    require_public_time(body)
    check_publication_copy({"body": text_for(body)})


def _parents(store, original, destinations):
    """The original post's single confirmed public object on each destination, with its Discord thread."""
    message = store.get_outbox_message(original)
    if not message:
        raise ValueError("CORRECTION_ORIGINAL_REQUIRED")
    parents, sources = {}, {}
    for dispatch in store.get_dispatches_for_work_item(original):
        destination = dispatch["platform"]
        if destination not in destinations or dispatch["status"] != "DISPATCH_CONFIRMED":
            continue
        if not dispatch["public_object_id"]:
            raise ValueError("CORRECTION_ORIGINAL_READBACK_REQUIRED:" + destination)
        if destination in parents:
            raise ValueError("CORRECTION_PARENT_AMBIGUOUS:" + destination)
        intent = json.loads(store.get_outbox_message(dispatch["message_id"])["payload"])
        thread = (intent.get("native_payload") or {}).get("discord_thread_parent_id")
        parents[destination] = {"public_object_id": dispatch["public_object_id"],
                                "public_object_url": dispatch["public_object_url"],
                                **({"thread_parent_id": thread} if destination == "discord" and thread else {})}
        sources[destination] = intent.get("output_dir")
    missing = sorted(set(destinations) - set(parents))
    if missing:
        raise ValueError("CORRECTION_PUBLIC_PARENTS_REQUIRED:" + ",".join(missing))
    return hashlib.sha256(message["payload"].encode()).hexdigest(), parents, sources


def validate(store, row):
    original_hash, parents, _ = _parents(store, row["original"], tuple(row["correction_parents"]))
    if (row.get("correction_reply_contract") != CONTRACT or not str(row.get("key", "")).startswith(KEY_PREFIX)
            or row.get("text") != text_for(row.get("body", "")) or row.get("original_sha256") != original_hash
            or row.get("correction_parents") != parents):
        raise ValueError("CORRECTION_SUPPLIED_TEXT_OR_PARENT_CHANGED")
    asset, source = row["retained_chart"], row["original_media"]
    if (hashlib.sha256(Path(source["context_path"]).read_bytes()).hexdigest() != source["context_sha256"]
            or hashlib.sha256(Path(asset["path"]).read_bytes()).hexdigest() != source["asset_sha256"]
            or asset["sha256"] != source["asset_sha256"]):
        raise ValueError("CORRECTION_ORIGINAL_CHART_CHANGED")


def prepare(store, spec, *, root=posts.POST_ROOT, media_source=None):
    """Register the correction once from its spec, then plan it through the existing status-post preparation."""
    key = spec["key"]
    if not str(key).startswith(KEY_PREFIX):
        raise ValueError("CORRECTION_KEY_PREFIX_REQUIRED")
    destinations = tuple(sorted(spec["destinations"]))
    if not destinations or not set(destinations) <= DESTINATIONS:
        raise ValueError("CORRECTION_DESTINATIONS_UNSUPPORTED")
    original_hash, parents, sources = _parents(store, spec["original"], destinations)
    if not store.get_outbox_message(key):
        check_body(spec["body"])
        if media_source is None:
            folders = {s for s in sources.values() if s}
            if len(folders) != 1:
                raise ValueError("CORRECTION_ORIGINAL_POST_FOLDER_REQUIRED")
            media_source = folders.pop()
        media_source = Path(media_source)
        context_path = media_source / "run_context_v1.json"
        assets = (json.loads(context_path.read_bytes()).get("media") or {}).get("assets") or []
        if not assets:
            raise ValueError("CORRECTION_ORIGINAL_CHART_REQUIRED")
        asset = assets[0]
        folder = Path(root) / key
        media = folder / "media_assets"
        media.mkdir(parents=True, exist_ok=True)
        target = media / Path(asset["path"]).name
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() != asset["sha256"]:
            raise ValueError("CORRECTION_RETAINED_CHART_PATH_CONFLICT")
        shutil.copyfile(asset["path"], target)
        asset = {**asset, "path": str(target.resolve())}
        manifest = json.loads((media_source / "delivery_media_manifest_v1.json").read_bytes())
        for hosted in manifest.get("assets", []):
            if hosted.get("sha256") == asset["sha256"]:
                hosted["absolute_local_source_path"] = asset["path"]
        (folder / "delivery_media_manifest_v1.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        store.create_work_item(story_id=key, title=spec["title"], target_surface="MULTI_PLATFORM", work_item_id=key)
        row = {"schema_version": posts.SCHEMA, "key": key, "symbol": spec["symbol"], "kind": "correction",
               "state": "CORRECTION", "title": spec["title"], "body": spec["body"], "text": text_for(spec["body"]),
               "conditional_calls": [], "at_utc": datetime.now(timezone.utc).isoformat(),
               "correction_reply_contract": CONTRACT, "original": spec["original"], "original_sha256": original_hash,
               "correction_parents": parents, "retained_chart": asset,
               "original_media": {"context_path": str(context_path.resolve()),
                                  "context_sha256": hashlib.sha256(context_path.read_bytes()).hexdigest(),
                                  "asset_sha256": asset["sha256"]},
               "authority": spec["authority"]}
        store.register_outbox_message(message_id=key, work_item_id=key, destination=posts.DESTINATION,
                                      payload=json.dumps(row, ensure_ascii=False), status=PREPARED)
    row = posts._row_payload(store, key)
    if (row.get("original") != spec["original"] or row.get("body") != spec["body"]
            or tuple(sorted(row["correction_parents"])) != destinations):
        raise ValueError("CORRECTION_KEY_HOLDS_ANOTHER_SPEC")
    validate(store, row)
    return posts.prepare_post(store, key, root=root, destinations=destinations)


def destination_payloads(row, *, card_id):
    if card_id != row["retained_chart"]["asset_id"]:
        raise ValueError("CORRECTION_ORIGINAL_CHART_REQUIRED")
    text = row["text"] + "\n\n" + posts.CHART_CREDIT
    payloads = {}
    for destination, parent in row["correction_parents"].items():
        payloads[destination] = {"destination": destination, "text": text, "full_text": text,
                                 "media_asset_ids": [card_id], "reply_to_id": parent["public_object_id"],
                                 "reply_to_url": parent["public_object_url"], "correction_reply_contract": CONTRACT,
                                 **({"discord_thread_parent_id": parent["thread_parent_id"]}
                                    if "thread_parent_id" in parent else {})}
    return payloads


def main(argv=None):
    """prepare | publish | status for one spec file, through the existing coordinator and API transports."""
    import argparse
    from .durable_operational_store_v1 import ContentOpsDurableStore
    from .publication_coordinator_v1 import DurablePublicationCoordinator, CanonicalDestinationTransportRuntimeV1
    from .destination_transport_registry_v1 import DestinationReadinessManager
    from .published_content_v1 import PRODUCTION_STORE

    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("prepare", "publish", "status"))
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--store", type=Path, default=PRODUCTION_STORE)
    parser.add_argument("--root", type=Path, default=posts.POST_ROOT)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args(argv)
    spec = json.loads(args.spec.read_bytes())
    store = ContentOpsDurableStore(args.store, auto_migrate=False)
    if args.phase == "status":
        result = {"original": store.get_dispatches_for_work_item(spec["original"]),
                  "correction": store.get_dispatches_for_work_item(spec["key"])}
    else:
        plan = prepare(store, spec, root=args.root)
        if args.phase == "prepare":
            result = {"plan": plan, "final_text": posts._row_payload(store, spec["key"])["text"]}
        else:
            runtime = CanonicalDestinationTransportRuntimeV1()
            coordinator = DurablePublicationCoordinator(store=store, transport_runtime=runtime,
                                                        readiness_manager=DestinationReadinessManager(store=store))
            posts.scope_to_post(coordinator, spec["key"], plan)
            result = coordinator.execute_plan(spec["key"], plan)
    evidence = {"contract": CONTRACT, "key": spec["key"], "phase": args.phase, "store_path": str(args.store.resolve()),
                "observed_at_utc": datetime.now(timezone.utc).isoformat(), "result": result}
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    args.evidence.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"phase": args.phase, "evidence": str(args.evidence),
        "per_destination": {k: {f: v.get(f) for f in ("status", "reason_code", "public_object_id", "public_object_url")}
                            for k, v in (result.get("per_destination") or {}).items()}}))


if __name__ == "__main__":
    main()
