"""Bind App-owned calendar invocations to existing window/day/slot identities.

No timer, App configuration write or model invocation lives here. The native App is the
only routine scheduler. These receipts reuse the canonical outbox and Simple slot hashes.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from live_contentops.daily_app_supervisor_v1 import build_bootstrap_editorial_window_policy
from live_contentops.llm_operator_control_v1 import llm_operator_pause_active
from live_contentops.newsroom_production_day_v1 import (
    bounded_deficit_work_needed, count_reconciled_published_articles, newsroom_production_day_id,
)
from live_contentops.published_corpus_read_model_v1 import load_canonical_published_memory_read_only
from live_contentops.v1_simple_gemini_scheduler_v1 import simple_gemini_slot_id
from live_contentops.native_brief_windows_v1 import automation_sessions, native_opportunities, observed_quota_stop
from live_contentops.native_newsroom_volume_v1 import volume_policy, window_progress

SCHEMA = "contentops.native_desktop_rollout.v1"
# App delivery may precede its nominal calendar second by a few seconds. Admit
# only that same window identity; its nominal cutoff and actual entry stay distinct.
EARLY_DELIVERY_TOLERANCE_SECONDS = 30


def _expected_binding(rollout, automation_id, checkpoint, ordinal, attempted, progress=None):
    window, day = checkpoint["window"], checkpoint["production_day_id"]
    run_id = simple_gemini_slot_id(production_day_id=day, window_id=window["opportunity_id"], slot_ordinal=ordinal)
    binding = {"schema_version": "contentops.native_desktop_operation_binding.v1", "run_id": run_id,
        "store_path": rollout["store_path"],
        "output_dir": str(Path(rollout["editorial_output_root"]) / day / window["opportunity_id"] / run_id),
        "feed_pointer_path": rollout["feed_pointer_path"], "published_memory_store": rollout["store_path"],
        "published_memory_output_root": rollout["published_output_root"], "cutoff_utc": window["start_utc"],
        "owner_manual_validation": False, "automation_id": automation_id,
        "window_id": window["opportunity_id"], "slot_ordinal": ordinal,
        "attempted_candidate_ids": sorted(set(attempted))}
    if checkpoint.get("volume_policy"):
        binding.update(volume_policy=checkpoint["volume_policy"], source_request_count_at_start=(progress or {}).get("source_request_count", 0))
        if (progress or {}).get("selection_origin_run_id"):
            binding.update({k: progress[k] for k in ("selection_origin_run_id", "selection_origin_output_dir")})
    return binding


def _issued_slots(store, rollout, automation_id, checkpoint):
    """Read only the bounded slots of one admitted window; never repair their bytes."""
    issued, attempted = [], []
    with store.get_read_only_connection() as conn:
        for ordinal in range(1, int(checkpoint["capacity"]) + 1):
            progress = window_progress(store, issued) if checkpoint.get("volume_policy") else None
            expected = _expected_binding(rollout, automation_id, checkpoint, ordinal, attempted, progress)
            path = Path(expected["output_dir"]) / "native_operation_binding.json"
            registered = conn.execute("SELECT payload FROM outbox_messages WHERE message_id=?",
                ("native-operation-binding-" + sha256_of(expected["run_id"]),)).fetchone()
            if not path.is_file():
                if registered:
                    raise ValueError("NATIVE_SCHEDULE_ISSUED_BINDING_MISSING")
                break
            binding = json.loads(path.read_bytes())
            if binding != expected or (registered and json.loads(registered["payload"]) != binding):
                raise ValueError("NATIVE_SCHEDULE_SLOT_BINDING_CHANGED")
            issued.append((binding, path))
            result = conn.execute("SELECT payload FROM outbox_messages WHERE message_id=?",
                ("cc-editorial-final-" + sha256_of(binding["run_id"]),)).fetchone()
            if result:
                value = json.loads(result["payload"])
                semantic = value.get("simple_result", value)
                attempted += [r["candidate_id"] for r in semantic.get("candidate_attempt_history", [])
                              if r.get("status") == "SOURCE_BLOCKED"]
                if semantic.get("qualified_article_count") and semantic.get("selected_candidate"):
                    attempted.append(semantic["selected_candidate"]["candidate_id"])
                attempted += [r["candidate_id"] for r in semantic.get("candidate_outcomes", [])
                              if r.get("candidate_id") and r.get("outcome") in {"HOLD", "SOURCE_BLOCKED", "REJECT"}]
    return issued, attempted


def _issued_state(store, rollout, checkpoint, binding, path):
    """Return the next existing boundary, including terminal replay without new work."""
    with store.get_read_only_connection() as conn:
        result = conn.execute("SELECT * FROM outbox_messages WHERE message_id=?",
            ("cc-editorial-final-" + sha256_of(binding["run_id"]),)).fetchone()
        review = conn.execute("SELECT * FROM review_records WHERE work_item_id=? AND reviewer_ref=? ORDER BY rowid DESC LIMIT 1",
            (result["work_item_id"], "NATIVE_DESKTOP_ARTICLE_REVIEW")).fetchone() if result else None
    classification = "NATIVE_WINDOW_SLOT_READY"
    if result:
        value = json.loads(result["payload"])
        semantic = value.get("simple_result", value)
        classification = "NATIVE_WINDOW_OPERATION_COMPLETE"
        if semantic.get("qualified_article_count"):
            if not review or review["decision"] == "REVISE":
                classification = "NATIVE_WINDOW_REVIEW_REQUIRED"
            elif review["decision"] == "KEEP":
                from live_contentops.native_desktop_publication_v1 import _prepared_packet
                try:
                    _prepared_packet(store, binding)
                except (ValueError, OSError, KeyError, TypeError):
                    classification = "NATIVE_WINDOW_HANDOFF_REQUIRED"
                if (classification == "NATIVE_WINDOW_OPERATION_COMPLETE"
                        and rollout.get("public_write_authority") is True
                        and binding["cutoff_utc"] >= (rollout.get("live_authority") or {}).get("not_before_utc", "")
                        and store.get_operating_control()["operating_mode"] == "AUTONOMOUS_DEFAULT"):
                    from live_contentops.native_desktop_publication_v1 import publication_projection
                    publication = publication_projection(store.list_outbox_messages(), store.list_platform_dispatches(),
                        store.get_reconciliations_for_work_item(binding["run_id"]), run_id=binding["run_id"])
                    if publication["state"] != "RECONCILED":
                        classification = "NATIVE_WINDOW_PUBLICATION_REQUIRED"
                        if binding.get("volume_policy") and not publication.get("pending_requests"):
                            from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
                            entries = publication.get("destinations", [])
                            canonical = next((e for e in entries if e["destination"] == "substack"), {})
                            unsafe = {"UNKNOWN_WRITE", "DISPATCH_ATTEMPT_STARTED", "NATIVE_NEO_TOOL_PENDING"}
                            if (canonical.get("reconciliation_status") == "RECONCILED_CONFIRMED"
                                    and DurablePublicationCoordinator._confirmed_public_object(canonical, destination="substack")
                                    and not any(e["status"] in unsafe for e in entries)):
                                classification = "NATIVE_WINDOW_OPERATION_COMPLETE"
    return {"classification": classification, "binding_path": str(path), "run_id": binding["run_id"],
        "capacity": checkpoint["capacity"], "slot_ordinal": binding["slot_ordinal"],
        "window_id": binding["window_id"], "cutoff_utc": binding["cutoff_utc"],
        "resumed_existing_binding": True, "model_invocations": 0, "source_requests": 0,
        "public_write_performed": False}


def _latest_window(store, session, *, opportunity_id=None):
    from live_contentops.native_desktop_editorial_v1 import DESTINATION
    with store.get_read_only_connection() as conn:
        rows = conn.execute("SELECT message_id,payload FROM outbox_messages WHERE destination=? AND message_id LIKE 'native-window-%'",
            (DESTINATION,)).fetchall()
    saved = []
    for row in rows:
        value = json.loads(row["payload"])
        if (value["window"]["session"] == session
                and (opportunity_id is None or value["window"]["opportunity_id"] == opportunity_id)):
            if (row["message_id"] != "native-window-" + sha256_of(value["window"]["opportunity_id"])
                    or value["production_day_id"] != newsroom_production_day_id(value["window"]["start_utc"])):
                raise ValueError("NATIVE_SCHEDULE_WINDOW_BINDING_CHANGED")
            saved.append(value)
    return max(saved, key=lambda v: v["window"]["start_utc"], default=None)


def scheduled_binding(rollout, automation_id, *, now=None, continue_after=None):
    # This check precedes directory creation, opening/migrating the production store,
    # polling Main, or reading a source. Engineering preparation does not release it.
    if llm_operator_pause_active():
        return {"classification": "LLM_OPERATOR_PAUSED", "public_write_performed": False}
    if rollout.get("schema_version") != SCHEMA or automation_id not in automation_sessions():
        raise ValueError("NATIVE_SCHEDULE_BINDING_INVALID")
    now = now or datetime.now(timezone.utc)
    now = now.replace(tzinfo=timezone.utc) if now.tzinfo is None else now.astimezone(timezone.utc)
    session = automation_sessions()[automation_id]
    rows = native_opportunities(build_bootstrap_editorial_window_policy(),
        reference_utc=now, through_utc=now + timedelta(seconds=EARLY_DELIVERY_TOLERANCE_SECONDS), capacity=12)
    due = [r for r in rows if r["session"] == session]
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    # Read issued identities before due/grace gating. No migration, source discovery,
    # new slot, cutoff change or lease is needed for a pending/completed replay.
    store_path = Path(rollout["store_path"])
    store = ContentOpsDurableStore(store_path, auto_migrate=False) if store_path.is_file() else None
    # An older unfinished operation remains resumable by its binding, but it must
    # not suppress a different currently eligible calendar window of this session.
    checkpoint = (_latest_window(store, session, opportunity_id=due[0]["opportunity_id"])
                  if store and len(due) == 1 and not continue_after else
                  _latest_window(store, session) if store else None)
    issued, _ = _issued_slots(store, rollout, automation_id, checkpoint) if checkpoint else ([], [])
    if issued:
        target = len(issued) - 1
        if continue_after:
            prior = next((i for i, (binding, _) in enumerate(issued) if binding["run_id"] == continue_after), None)
            if prior is None:
                raise ValueError("EXACT_COMPLETED_NATIVE_SLOT_REQUIRED")
            previous = _issued_state(store, rollout, checkpoint, *issued[prior])
            if previous["classification"] != "NATIVE_WINDOW_OPERATION_COMPLETE":
                raise ValueError("EXACT_COMPLETED_NATIVE_SLOT_REQUIRED")
            target = prior + 1
        if target < len(issued):
            replay = _issued_state(store, rollout, checkpoint, *issued[target])
            same_due = len(due) == 1 and due[0]["opportunity_id"] == checkpoint["window"]["opportunity_id"]
            if (continue_after or replay["classification"] != "NATIVE_WINDOW_OPERATION_COMPLETE"
                    or not due or same_due):
                replay["next_slot_eligible"] = bool(same_due and target + 1 < checkpoint["capacity"]
                    and replay["classification"] == "NATIVE_WINDOW_OPERATION_COMPLETE")
                return replay
        elif target >= checkpoint["capacity"]:
            return {"classification": "NATIVE_WINDOW_COMPLETE", "capacity": checkpoint["capacity"],
                "window_id": checkpoint["window"]["opportunity_id"], "public_write_performed": False}
    elif continue_after:
        raise ValueError("EXACT_COMPLETED_NATIVE_SLOT_REQUIRED")
    if len(due) != 1 or (continue_after and due[0]["opportunity_id"] != checkpoint["window"]["opportunity_id"]):
        upcoming = native_opportunities(build_bootstrap_editorial_window_policy(),
            reference_utc=now, through_utc=now + timedelta(days=8))
        next_window = next((r for r in upcoming if r["session"] == session
            and datetime.fromisoformat(r["start_utc"].replace("Z", "+00:00")) > now), None)
        return {"classification": "OUTSIDE_EXACT_NATIVE_WINDOW", "actual_entry_utc": now.isoformat(),
            "next_calendar_opportunity": ({k: next_window[k] for k in
                ("opportunity_id", "session", "start_utc", "end_utc")} if next_window else None),
            "public_write_performed": False}
    window = due[0]
    start = datetime.fromisoformat(window["start_utc"].replace("Z", "+00:00"))
    day = newsroom_production_day_id(start)
    memory, _ = load_canonical_published_memory_read_only(store_path=rollout["store_path"],
                                                       output_root=rollout["published_output_root"])
    store = ContentOpsDurableStore(store_path)
    if window.get("brief_only") and (quota := observed_quota_stop(store, cutoff_utc=window["start_utc"])):
        return {"classification": "BRIEF_WINDOW_SKIPPED_QUOTA", "first_blocking_cause": "CODEX_QUOTA_STOP",
            "observation": quota, "window_id": window["opportunity_id"], "public_write_performed": False}
    owner = "native-schedule-" + uuid4().hex
    work = window["opportunity_id"]
    lease = store.acquire_lease("internal:native-window:" + work, owner, ttl_seconds=60)
    try:
        return _issue_due_slot(store, rollout, automation_id, window, day, memory, continue_after, now=now)
    finally:
        store.release_lease(lease["lease_id"], owner, lease["fencing_token"])


def _issue_due_slot(store, rollout, automation_id, window, day, memory, continue_after, *, now=None):
    from live_contentops.native_desktop_editorial_v1 import DESTINATION
    work = window["opportunity_id"]
    key = "native-window-" + sha256_of(work)
    prior = store.get_outbox_message(key)
    checkpoint = json.loads(prior["payload"]) if prior else None
    if checkpoint is None:
        count = count_reconciled_published_articles(memory, production_day_id=day)
        checkpoint = {"window": window, "production_day_id": day,
            "capacity": bounded_deficit_work_needed(session=window["session"], published_articles_today=count),
            "published_at_window_start": count, "rollout_sha256": sha256_of(rollout)}
        if policy := volume_policy(window["start_utc"], brief_only=bool(window.get("brief_only"))):
            checkpoint.update(volume_policy=policy, capacity=policy["max_admitted_candidates"])
        if now is not None:
            nominal = datetime.fromisoformat(window["start_utc"].replace("Z", "+00:00"))
            checkpoint.update(actual_entry_utc=now.isoformat(),
                early_delivery_seconds=max(0, (nominal - now).total_seconds()))
        store.create_work_item(story_id=work, work_item_id=work, title="Native Desktop scheduled window",
                               target_surface="CONTENTOPS_EDITORIAL_ONLY")
        store.register_outbox_message(message_id=key, work_item_id=work, destination=DESTINATION,
            payload=canonical_bytes(checkpoint).decode(), status="EDITORIAL_INTERNAL")
    elif checkpoint["rollout_sha256"] != sha256_of(rollout):
        raise ValueError("NATIVE_WINDOW_ROLLOUT_CHANGED")
    issued, attempted = _issued_slots(store, rollout, automation_id, checkpoint)
    ordinal = 1
    if issued:
        if not continue_after:
            return _issued_state(store, rollout, checkpoint, *issued[-1])
        prior = next((i for i, (binding, _) in enumerate(issued) if binding["run_id"] == continue_after), None)
        if prior is None:
            raise ValueError("EXACT_COMPLETED_NATIVE_SLOT_REQUIRED")
        if _issued_state(store, rollout, checkpoint, *issued[prior])["classification"] != "NATIVE_WINDOW_OPERATION_COMPLETE":
            raise ValueError("EXACT_COMPLETED_NATIVE_SLOT_REQUIRED")
        ordinal = prior + 2
        if ordinal <= len(issued):
            return _issued_state(store, rollout, checkpoint, *issued[ordinal - 1])
    if ordinal > int(checkpoint["capacity"]):
        return {"classification": "NATIVE_WINDOW_COMPLETE", "capacity": checkpoint["capacity"],
            "window_id": work, "public_write_performed": False}
    progress = window_progress(store, issued) if checkpoint.get("volume_policy") else None
    if progress and (progress["published_article_count"] >= checkpoint["volume_policy"]["max_articles"]
            or (progress["selection_origin_run_id"] and not set(progress["admitted_candidate_ids"]) - set(progress["attempted_candidate_ids"]))):
        return {"classification": "NATIVE_WINDOW_COMPLETE", "window_id": work, "capacity": checkpoint["capacity"],
            "window_progress": progress, "public_write_performed": False}
    binding = _expected_binding(rollout, automation_id, checkpoint, ordinal, attempted, progress)
    root = Path(binding["output_dir"])
    root.mkdir(parents=True, exist_ok=True)
    path = root / "native_operation_binding.json"
    path.write_bytes(canonical_bytes(binding))
    return {"classification": "NATIVE_WINDOW_SLOT_READY", "binding_path": str(path), "run_id": binding["run_id"],
        "capacity": checkpoint["capacity"], "slot_ordinal": ordinal, "window_id": work,
        "cutoff_utc": binding["cutoff_utc"], "resumed_existing_binding": False, "public_write_performed": False}
