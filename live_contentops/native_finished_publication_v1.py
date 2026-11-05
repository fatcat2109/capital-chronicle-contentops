"""Decision 39: release a finished native piece through the existing publisher.

No queue, scheduler, model or transport is created. Source stores remain read-only.
The original promotion engine owns import; the existing coordinator owns every send.
"""
from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from live_contentops.capital_chronicle_latest_report_consumer_v1 import _private, canonical_bytes, sha256_of
from live_contentops.native_desktop_editorial_v1 import (
    NativeDesktopTurn, native_review_revision, require_current_final_visual_review,
    validate_release_media, validated_native_review,
)
from live_contentops.native_desktop_publication_v1 import (
    NativeReviewedPublication, prepare_native_publication, scheduled_publication_authority,
)
from live_contentops.native_desktop_workspace_v1 import resolve_workspace_path
from live_contentops.native_manual_candidate_v1 import manual_output_root
from live_contentops.native_publication_promotion_v1 import ReadOnlyStore, _snapshot, promote

AUTHORITY = "JIM_DECISIONS_20261030_DECISION_39"


@contextmanager
def newsroom_lease(store):
    """Serialize live CLI steps using the existing lease table, including windows."""
    owner = "native-newsroom-" + uuid4().hex
    lease = store.acquire_lease("internal:native-editorial:newsroom", owner, ttl_seconds=900)
    try:
        assert_newsroom_idle(store, own_lease=lease["lease_id"])
        yield lease
    finally:
        store.release_lease(lease["lease_id"], owner, lease["fencing_token"])


def utc(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("EXPLICIT_UTC_CLOCK_REQUIRED")
    return result.astimezone(timezone.utc)


def assert_newsroom_idle(store, *, own_lease=None):
    with store.get_read_only_connection() as conn:
        active = conn.execute(
            "SELECT lease_key FROM leases WHERE status='ACTIVE' AND expires_at>? "
            "AND lease_id!=? LIMIT 1", (store._get_now_iso(), own_lease or ""),
        ).fetchone()
    if active:
        raise ValueError("NEWSROOM_LEASE_ACTIVE:" + active[0])


def confirmed_canonicals(store):
    """Yield exact reconciled objects with separate publication and readback clocks."""
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
    from live_contentops.published_content_v1 import DEFAULT_FEED, read_records
    try:
        records = read_records(DEFAULT_FEED)
    except FileNotFoundError:
        records = []
    publication_clocks = {(r["content_id"], o["url"]): utc(r["published_at_utc"])
        for r in records for o in r["outlets"] if o["name"] == "substack"}
    for dispatch in store.list_platform_dispatches():
        if dispatch.get("platform") != "substack" or dispatch.get("status") != "DISPATCH_CONFIRMED":
            continue
        row = store.get_outbox_message(dispatch["message_id"])
        if not row:
            continue
        intent = json.loads(row["payload"])
        # The daily digest recaps existing articles. It is a real public object,
        # but does not satisfy the newsroom's target for distinct originals.
        if intent.get("daily_digest"):
            continue
        ids = DurablePublicationCoordinator._ids(row["work_item_id"], intent["plan_hash"], "substack")
        reconciled = store.get_reconciliations_for_work_item(row["work_item_id"])
        if dispatch["dispatch_id"] != ids["dispatch_id"] or not any(r["reconciliation_id"] == ids["reconciliation_id"]
                   and r["status"] == "RECONCILED_CONFIRMED" for r in reconciled):
            continue
        if not DurablePublicationCoordinator._confirmed_public_object(
                {**dispatch, "reconciliation_status": "RECONCILED_CONFIRMED"}, destination="substack"):
            continue
        times = []
        for rowback in store.list_readbacks_for_dispatch(dispatch["dispatch_id"]):
            data = json.loads(rowback["readback_data"])
            proof = data.get("readback", data)
            if proof.get("verified") is True:
                times.append(utc(rowback["read_at"]))
        # The first verified readback starts the interval; rereading never refreshes it.
        if times:
            yield {"run_id": row["work_item_id"], "dispatch_id": dispatch["dispatch_id"],
                   "article_identity": intent.get("article_identity") or row["work_item_id"],
                   "published_at_utc": publication_clocks.get(("substack:" + str(dispatch["public_object_id"]),
                                                               dispatch["public_object_url"])),
                   "first_readback_utc": min(times)}


def publication_due(store, *, run_id=None, now=None):
    """A finished, reviewed piece is due now (CC-199 / decision 53)."""
    now = now or datetime.now(timezone.utc)
    return {"due": True, "next_publication_utc": now.isoformat(),
            "spacing_hours": 0, "clock_basis": "REVIEWED_PIECE_READY"}


def standing_binding(profile, rollout, *, operation_id, resolver, request=None, now=None, report_only=False):
    """Reuse the live owner-manual entry; no schedule, queue or second store."""
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    from live_contentops.native_desktop_publication_v1 import live_publication_policy
    from live_contentops.newsroom_production_day_v1 import newsroom_production_day_id
    live_publication_policy(rollout)
    store = ContentOpsDurableStore(rollout["store_path"], auto_migrate=False)
    now = now or datetime.now(timezone.utc)
    with newsroom_lease(store):
        published = list(confirmed_canonicals(store))
        completed = {p["run_id"] for p in published}
        day = newsroom_production_day_id(now)
        identities = {p["article_identity"] for p in published
                      if newsroom_production_day_id(p.get("published_at_utc") or p["first_readback_utc"]) == day}
        if len(identities) >= 8 and operation_id not in completed:
            raise ValueError("STANDING_DAILY_TARGET_REACHED")
        return resolver(profile, operation_id=operation_id, request=request, now=now,
                        live_rollout=rollout, standing=True, report_only=report_only)


def check_finished_piece(store, binding):
    """Recheck the exact writer return, facts, clocks, public text and chart lineage."""
    from live_contentops.event_article_guard_v1 import check_publication_copy, check_public_event_article
    from live_contentops.v1_simple_gemini_newsroom_v1 import (
        _normalize_relay_attribution, _public_copy, _validate_article_against_source_pack,
    )
    result, _, review = validated_native_review(store, run_id=binding["run_id"])
    from live_contentops.native_publication_latency_v1 import validate_publication_media
    validate_publication_media(store, run_id=binding["run_id"], result=result)
    require_current_final_visual_review(store, run_id=binding["run_id"])
    turn = NativeDesktopTurn(store, run_id=binding["run_id"],
        output_dir=binding["output_dir"], owner_manual_validation=True)
    request = turn.frozen_request("write")
    stage = "revise" if result.get("simple_result", {}).get("revision_performed") else "write"
    response, exact = turn._get(stage, "response"), turn.frozen_request(stage)
    if not request or not exact or not response or response["request_sha256"] != exact["request_sha256"]:
        raise ValueError("FINISHED_PIECE_EXACT_NATIVE_WRITER_REQUIRED")
    for packet in (request, exact):
        if packet["request_sha256"] != sha256_of({k: v for k, v in packet.items() if k != "request_sha256"}):
            raise ValueError("FINISHED_PIECE_NATIVE_REQUEST_CHANGED")
    observation = response.get("invocation_observation") or {}
    model = observation.get("model") or observation.get("configured_model")
    effort = observation.get("reasoning_effort") or observation.get("configured_reasoning_effort")
    if not observation.get("invocation_id") or model != "gpt-6.1-sol" or effort != "max":
        raise ValueError("FINISHED_PIECE_APPROVED_WRITER_REQUIRED")
    governed = request["governed_input"]
    cutoff = utc(governed["cutoff_utc"])
    if cutoff != utc(binding["cutoff_utc"]):
        raise ValueError("FINISHED_PIECE_CUTOFF_CHANGED")
    for document in governed["source_pack"]:
        clocks = [document[k] for k in ("published_at_utc", "known_at_utc") if document.get(k)]
        if not clocks or any(utc(c) > cutoff for c in clocks):
            raise ValueError("FINISHED_PIECE_SOURCE_CLOCK_INVALID:" + document["source_id"])
        if document.get("public_claim_allowed") is False:
            raise ValueError("FINISHED_PIECE_SOURCE_REMAINS_PRIVATE")
    output, _ = _normalize_relay_attribution(response["output"], governed.get("epistemic_state"))
    checked, validation = _validate_article_against_source_pack(output, governed["source_pack"],
        selected_candidate=governed.get("selected_candidate"), article_mode=governed.get("article_mode"),
        epistemic_state=governed.get("epistemic_state"))
    if _public_copy(checked) != _public_copy(result["article"]):
        raise ValueError("FINISHED_PIECE_DIFFERS_FROM_FACT_CHECKED_COPY")
    surfaces = [_public_copy(result["article"]), *[json.dumps(p["payload"], ensure_ascii=False)
                 for p in result.get("previews", [])]]
    check_publication_copy({"body": surfaces[0]},
        conditional_calls=result["article"].get("conditional_calls", []), require_notice=False)
    for surface in surfaces[1:]:
        check_publication_copy({"body": surface},
            conditional_calls=result["article"].get("conditional_calls", []),
            require_notice=False, require_call_text=False)
    if _private(result["article"]):
        raise ValueError("FINISHED_PIECE_PUBLIC_OUTPUT_GUARD")
    if "analysis, not financial advice" not in surfaces[0].casefold():
        raise ValueError("FINISHED_PIECE_ANALYSIS_NOTICE_REQUIRED")
    event_packet = response["output"].get("event_article")
    if result["article"].get("article_type") in {"EVENT_PREVIEW", "EVENT_REVIEW"} and not event_packet:
        raise ValueError("FINISHED_EVENT_EXACT_PUBLIC_PACKET_REQUIRED")
    event_check = None
    if event_packet:
        admission = governed.get("public_event_evidence")
        event_check = check_public_event_article(event_packet, evidence=admission)
        if event_packet["copy"]["headline"] != result["article"]["title"]:
            raise ValueError("FINISHED_EVENT_COPY_CHANGED")
        def strings(value):
            if isinstance(value, str):
                yield value
            elif isinstance(value, dict):
                for child in value.values():
                    yield from strings(child)
        if any(t not in surfaces[0] for t in strings(event_packet["copy"])):
            raise ValueError("FINISHED_EVENT_SECTIONS_CHANGED")
    return {"status": "PASS", "article_identity": result["article_identity"],
            "package_revision": native_review_revision(result), "review_id": review["review_id"],
            "writer_request_sha256": exact["request_sha256"], "writer_observation": observation,
            "fact_check": validation, "event_check": event_check,
            "public_copy_sha256": sha256_of(surfaces), "cutoff_utc": cutoff.isoformat()}


def release_finished_piece(binding_path, rollout):
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    store = ContentOpsDurableStore(rollout["store_path"], auto_migrate=False)
    with newsroom_lease(store) as lease:
        return _release_finished_piece(binding_path, rollout, own_lease=lease["lease_id"])


def _release_finished_piece(binding_path, rollout, *, own_lease):
    """One command: validate and import if needed, then prepare the sole coordinator."""
    path = resolve_workspace_path(binding_path)
    binding = json.loads(path.read_bytes())
    source = ReadOnlyStore(binding["store_path"])
    registered = source.get_outbox_message("native-operation-binding-" + sha256_of(binding["run_id"]))
    if not registered or json.loads(registered["payload"]) != binding:
        raise ValueError("EXACT_REGISTERED_SOURCE_BINDING_REQUIRED")
    check = check_finished_piece(source, binding)
    target = ReadOnlyStore(rollout["store_path"])
    assert_newsroom_idle(target, own_lease=own_lease)
    # Already-live articles retain their exact operation, including CC-074's older promotion.
    existing = target.get_outbox_message("native-operation-binding-" + sha256_of(binding["run_id"]))
    if existing:
        live = json.loads(existing["payload"])
        if (live != binding and live.get("promoted_from_binding_sha256") != sha256_of(binding)):
            raise ValueError("FINISHED_PIECE_TARGET_BINDING_CONFLICT")
        current = check_finished_piece(target, live)
        if current["package_revision"] != check["package_revision"]:
            raise ValueError("FINISHED_PIECE_TARGET_REVISION_CONFLICT")
        scheduled_publication_authority(target, live, rollout)
    else:
        rows, reviews, item = _snapshot(source, binding["run_id"])
        root = manual_output_root(source, binding)
        record = root / "qualified_article_record_v1.json"
        pin = {"run_id": binding["run_id"], "article_identity": check["article_identity"],
            "package_revision": check["package_revision"], "authority_ref": AUTHORITY,
            "source_binding_sha256": sha256_of(binding), "qualified_record_sha256": sha256_of(json.loads(record.read_bytes()))}
        # The engine binds the actual file digest, not the JSON logical hash.
        from hashlib import sha256
        pin["qualified_record_sha256"] = sha256(record.read_bytes()).hexdigest()
        operation = {"binding": binding,
            "rows": rows, "reviews": reviews, "item": item, "pin": pin, "files": [],
            "qualified_record": str(record), "source_check": check, "artifact_root": str(root),
            "release_authority": AUTHORITY,
            "publication_eligibility_utc": datetime.now(timezone.utc).isoformat(),
            "_own_newsroom_lease": own_lease}
        plan = promote(operation, rollout)
        applied = promote(operation, rollout, apply=True, expected_plan_sha256=plan["plan_sha256"])
        live = json.loads(Path(applied["binding_path"]).read_bytes())
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    live_store = ContentOpsDurableStore(live["store_path"], auto_migrate=False)
    marker = {"run_id": live["run_id"], "authority_ref": AUTHORITY,
              "article_identity": check["article_identity"], "binding_sha256": sha256_of(live)}
    live_store.register_outbox_message(message_id="native-finished-release-" + sha256_of(live["run_id"]),
        work_item_id="cc-opportunity-" + sha256_of(live["run_id"]),
        destination="internal:native-finished-release", payload=canonical_bytes(marker).decode(),
        status="EDITORIAL_INTERNAL")
    # Existing attempts are projected only. Recovery never rematerializes a sent plan.
    state = NativeReviewedPublication(live_store, live, native_invocation_id=None).projection()
    attempted = any(d.get("dispatch_recorded") for d in state.get("destinations", []))
    prepared = (prepare_native_publication(live_store, live)
                if not attempted and state["state"] in {"REVIEWED_HANDOFF_REQUIRED", "INVALIDATED"} else None)
    return {"classification": "FINISHED_PIECE_READY_FOR_COORDINATOR", "binding": live,
            "binding_path": str(resolve_workspace_path(live["output_dir"]) /
                ("native_operation_binding.json" if live.get("automation_id") else "binding.json")),
            "check": check, "prepared": prepared, "publication": state,
            "publication_due": publication_due(live_store, run_id=live["run_id"]),
            "next_operation": "publication-resume", "public_write_performed": False}
