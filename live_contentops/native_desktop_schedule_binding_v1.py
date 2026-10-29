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
from live_contentops.native_brief_windows_v1 import automation_sessions, brief_effective_guard, native_opportunities, observed_quota_stop
from live_contentops.native_newsroom_volume_v1 import volume_policy, window_progress

SCHEMA = "contentops.native_desktop_rollout.v1"
# App delivery has been observed almost five minutes before its calendar time. Admit
# only that same window identity; its nominal cutoff and actual entry stay distinct.
EARLY_DELIVERY_TOLERANCE_SECONDS = 300


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
    if checkpoint.get("input_known_at_cutoff_utc"):
        binding["input_known_at_cutoff_utc"] = checkpoint["input_known_at_cutoff_utc"]
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
    disposition = store.get_outbox_message("native-window-disposition-" + sha256_of(binding["run_id"]))
    classification = "NATIVE_WINDOW_OPERATION_COMPLETE" if disposition else "NATIVE_WINDOW_SLOT_READY"
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
    moment = now or datetime.now(timezone.utc)
    moment = moment.replace(tzinfo=timezone.utc) if moment.tzinfo is None else moment.astimezone(timezone.utc)
    result = _scheduled_binding(rollout, automation_id, now=moment, continue_after=continue_after)
    # Callback observation only: issued window/operation/request bytes stay unchanged.
    return {**result, "actual_entry_utc": result.get("actual_entry_utc", moment.isoformat())}


def _scheduled_binding(rollout, automation_id, *, now=None, continue_after=None):
    # This check precedes directory creation, opening/migrating the production store,
    # polling Main, or reading a source. Engineering preparation does not release it.
    if llm_operator_pause_active():
        return {"classification": "LLM_OPERATOR_PAUSED", "public_write_performed": False}
    if rollout.get("schema_version") != SCHEMA or automation_id not in automation_sessions():
        raise ValueError("NATIVE_SCHEDULE_BINDING_INVALID")
    now = now or datetime.now(timezone.utc)
    now = now.replace(tzinfo=timezone.utc) if now.tzinfo is None else now.astimezone(timezone.utc)
    if guarded := brief_effective_guard(automation_id, now):
        return guarded
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
            if now < nominal:
                checkpoint["input_known_at_cutoff_utc"] = now.isoformat()
        store.create_work_item(story_id=work, work_item_id=work, title="Native Desktop scheduled window",
                               target_surface="CONTENTOPS_EDITORIAL_ONLY")
        store.register_outbox_message(message_id=key, work_item_id=work, destination=DESTINATION,
            payload=canonical_bytes(checkpoint).decode(), status="EDITORIAL_INTERNAL")
    elif checkpoint["rollout_sha256"] != sha256_of(rollout):
        compatibility = rollout.get("terminal_reporting_prompt_compatibility", {})
        routing = {k:v for k,v in rollout.items() if k != "terminal_reporting_prompt_compatibility"}
        routing["tasks"] = [{k:v for k,v in task.items() if k != "prompt"} for task in routing.get("tasks", [])]
        admitted = {compatibility.get("previous_rollout_sha256"), *compatibility.get("previous_rollout_sha256s", [])}
        if (checkpoint["rollout_sha256"] not in admitted
                or sha256_of(routing) != compatibility.get("unchanged_routing_sha256")):
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


# Jim's 29 October reporting exception applies to scheduled task chats only.
# These functions use the existing window/result outbox, never a notification service.
WINDOW_REPORT_L2 = "01a1657e-f5d0-76a1-b52b-ec6c78b6fe35"
WINDOW_REPORT_HOST = "local"


def _window_result_key(binding):
    if not binding.get("automation_id"):
        return "native-task-result-" + sha256_of(binding["run_id"])
    return "scheduled-result-" + sha256_of([binding["automation_id"],
        newsroom_production_day_id(binding["cutoff_utc"]), binding["window_id"]])


def _window_result_path(binding):
    if not binding.get("automation_id"):
        return Path(binding["output_dir"]) / "native_task_result.json"
    return Path(binding["output_dir"]).parent / "native_window_result.json"


def _save_window_result(store, binding, value):
    from live_contentops.native_desktop_editorial_v1 import DESTINATION
    key, path = _window_result_key(binding), _window_result_path(binding)
    raw = canonical_bytes(value)
    if store.get_outbox_message(key):
        store.finalize_outbox_payload_before_dispatch(message_id=key, payload=raw.decode(), status="EDITORIAL_INTERNAL")
    else:
        store.register_outbox_message(message_id=key, work_item_id=binding.get("window_id") or "cc-opportunity-"+sha256_of(binding["run_id"]),
            destination=DESTINATION, payload=raw.decode(), status="EDITORIAL_INTERNAL")
    temporary = path.with_suffix(".json.tmp")
    temporary.write_bytes(raw)
    temporary.replace(path)


def _unfinished_window_roles(store, issued):
    """A pending native request cannot be relabelled a completed child."""
    from live_contentops.native_desktop_editorial_v1 import DESTINATION, NativeDesktopTurn
    rows = store.list_outbox_messages()
    for binding, _ in issued:
        if store.get_outbox_message("native-window-disposition-" + sha256_of(binding["run_id"])):
            continue  # Explicit expired process closure; pending native returns remain unaccepted.
        work = "cc-opportunity-" + sha256_of(binding["run_id"])
        turn = NativeDesktopTurn(store, run_id=binding["run_id"], output_dir=binding["output_dir"])
        for row in rows:
            if row["work_item_id"] != work or row["destination"] != DESTINATION:
                continue
            value = json.loads(row["payload"])
            if not (value.get("stage") and value.get("request_sha256") and "governed_input" in value):
                continue
            if turn.frozen_request(value["stage"]) == value and not turn._get(value["stage"], "response"):
                return True
    return False


def _window_notice(value, artifact):
    result = value["terminal_result"]
    return (
        ("Standalone V1 task result — " if result.get("standalone_task") else "Scheduled V1 window result — ") + result["finished_at_gmt7"] + "\n"
        + "Automation: " + result["automation_id"] + "; production day: " + result["production_day_id"] + "\n"
        + "Window: " + str(result["window_id"] or "NOT_SCHEDULED") + "; runs: " + ", ".join(result["run_ids"]) + "\n"
        + "Source chat/session: " + json.dumps(result.get("source_context",{}), separators=(",", ":")) + "\n"
        + "Nominal window: " + result.get("nominal_window_gmt7","UNOBSERVED")
        + "; actual entry: " + result.get("actual_entry_gmt7","UNOBSERVED") + "\n"
        + "Outcome: " + result["outcome"] + "; distinct canonical items: " + str(len(result["canonical_items"]))
        + "; objects: " + json.dumps(result["canonical_items"], separators=(",", ":")) + "\n"
        + "Channels: " + json.dumps(result["channels"], separators=(",", ":")) + "\n"
        + "First blocking causes: " + json.dumps(result["first_blocking_causes"], separators=(",", ":")) + "\n"
        + "Artifact: " + str(artifact) + "\nNext action: " + result["next_action"]
        + "; actor: " + result.get("next_actor","L2 ContentOps / existing operation owner")
    )


def prepare_window_result(store, rollout, binding, response, *, now=None):
    owner = "window-result-" + uuid4().hex
    lease = store.acquire_lease("internal:native-window:" + binding["window_id"], owner, ttl_seconds=60)
    try:
        return _prepare_window_result(store, rollout, binding, response, now=now)
    finally:
        store.release_lease(lease["lease_id"], owner, lease["fencing_token"])


def _prepare_window_result(store, rollout, binding, response, *, now=None):
    """Save a real whole-window terminal result before offering one native tool send.

    response.startup_result is the exact saved initial `scheduled` result from this
    task turn. It distinguishes resumed work from stale/duplicate terminal callbacks.
    A fatal process result may be supplied by exact saved CLI error artifact; a quota
    stop or unfinished role is never converted into a terminal failure.
    """
    from collections import Counter, defaultdict
    from live_contentops.native_desktop_publication_v1 import publication_projection
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
    moment = now or datetime.now(timezone.utc)
    moment = moment.replace(tzinfo=timezone.utc) if moment.tzinfo is None else moment.astimezone(timezone.utc)
    entry = response.get("startup_result", {})
    def suppressed(reason):
        return {"classification":"WINDOW_NOTICE_SUPPRESSED", "reason":reason, "public_write_performed":False}
    auto = binding.get("automation_id")
    if not auto or auto not in automation_sessions() or binding.get("owner_manual_validation"):
        return suppressed("SCHEDULED_TASK_ONLY")
    if brief_effective_guard(auto, moment):
        return suppressed("NOT_YET_EFFECTIVE")
    allowed = {"NATIVE_WINDOW_SLOT_READY", "NATIVE_WINDOW_REVIEW_REQUIRED", "NATIVE_WINDOW_HANDOFF_REQUIRED",
        "NATIVE_WINDOW_PUBLICATION_REQUIRED", "NATIVE_WINDOW_OPERATION_COMPLETE"}
    owner_closure = bool(entry.get("classification") == "EXPIRED_ISSUED_WINDOW_OWNER_CLOSURE"
        and store.get_outbox_message("native-window-disposition-"+sha256_of(binding["run_id"])))
    if entry.get("classification") not in allowed and not owner_closure:
        return suppressed(entry.get("classification") or "EXACT_STARTUP_RESULT_REQUIRED")
    if entry.get("window_id") != binding.get("window_id") or not entry.get("actual_entry_utc"):
        return suppressed("STARTUP_WINDOW_IDENTITY_MISSING_OR_CHANGED")
    prior = store.get_outbox_message(_window_result_key(binding))
    if prior:
        value = json.loads(prior["payload"])
        return {"classification":"WINDOW_NOTICE_SUPPRESSED", "reason":"RESULT_ALREADY_SAVED",
            "delivery_state":value["notice_delivery"]["state"], "artifact_path":str(_window_result_path(binding))}
    checkpoint = store.get_outbox_message("native-window-" + sha256_of(binding["window_id"]))
    if not checkpoint:
        return suppressed("EXACT_ISSUED_WINDOW_REQUIRED")
    checkpoint = json.loads(checkpoint["payload"])
    entered = datetime.fromisoformat(entry["actual_entry_utc"].replace("Z", "+00:00"))
    start = datetime.fromisoformat(checkpoint["window"]["start_utc"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(checkpoint["window"]["end_utc"].replace("Z", "+00:00")) + timedelta(hours=1)
    if (not owner_closure and not start - timedelta(seconds=EARLY_DELIVERY_TOLERANCE_SECONDS) <= entered <= end) or entered > moment:
        return suppressed("STALE_CALLBACK")
    issued, _ = _issued_slots(store, rollout, auto, checkpoint)
    if not issued or binding != issued[-1][0]:
        return suppressed("EXACT_LAST_ISSUED_RUN_REQUIRED")
    if (entry["classification"] == "NATIVE_WINDOW_OPERATION_COMPLETE"
            and entry.get("run_id") == binding["run_id"]):
        return suppressed("DUPLICATE_OR_UNCHANGED_TERMINAL_CALLBACK")
    if _unfinished_window_roles(store, issued):
        return suppressed("UNFINISHED_NATIVE_ROLE")
    # A historical quota observation is not a permanent bar after genuine resume.
    for current, _ in issued:
        final = store.get_outbox_message("cc-editorial-final-" + sha256_of(current["run_id"]))
        if final:
            saved = json.loads(final["payload"])
            semantic = saved.get("simple_result", saved)
            if any(word in str(semantic.get("classification", "")).upper() for word in ("QUOTA", "INTERRUPTED")):
                return suppressed("CODEX_QUOTA_STOP_OR_INTERRUPTED_STAGE")
    states = [_issued_state(store, rollout, checkpoint, b, p)["classification"] for b, p in issued]
    failure = response.get("terminal_failure")
    fatal = None
    if failure:
        fatal = json.loads(Path(failure["artifact_path"]).read_bytes())
        error = str(fatal.get("blocker") or fatal.get("error") or "")
        if (fatal.get("classification") not in {"NATIVE_DESKTOP_BLOCKED", "NATIVE_WINDOW_PROCESS_FAILED"}
                or fatal.get("run_id") != binding["run_id"]
                or fatal.get("command") != failure.get("operation")
                or failure.get("continuation_possible") is not False or not failure.get("why_terminal")
                or not failure.get("operation") or not error):
            return suppressed("EXACT_TERMINAL_PROCESS_ERROR_REQUIRED")
        if any(word in error.upper() for word in ("QUOTA", "USAGE_LIMIT", "TOKEN_LIMIT", "CAPACITY")):
            return suppressed("CODEX_QUOTA_STOP")
        fatal = {"operation":failure["operation"], "error":error, "artifact_path":failure["artifact_path"],
            "why_terminal":failure["why_terminal"], "continuation_possible":False}
    if not fatal and any(state != "NATIVE_WINDOW_OPERATION_COMPLETE" for state in states):
        return suppressed("PARTIAL_WINDOW")
    progress = window_progress(store, issued) if checkpoint.get("volume_policy") else None
    exhausted = len(issued) >= checkpoint["capacity"] or moment > end
    if progress:
        exhausted |= (progress["published_article_count"] >= checkpoint["volume_policy"]["max_articles"]
            or bool(progress["selection_origin_run_id"] and not set(progress["admitted_candidate_ids"])
                - set(progress["attempted_candidate_ids"])))
    if not fatal and not exhausted:
        return suppressed("ANOTHER_ADMITTED_CANDIDATE_OR_SLOT_ELIGIBLE")
    canonical, causes = {}, {}
    channels = {k:defaultdict(set) for k in ("confirmed", "skipped", "failed", "unresolved")}
    rows, dispatches = store.list_outbox_messages(), store.list_platform_dispatches()
    final_locators = []
    for current, _ in issued:
        run = current["run_id"]
        final_key = "cc-editorial-final-" + sha256_of(run)
        final = store.get_outbox_message(final_key)
        if final:
            value = json.loads(final["payload"])
            semantic = value.get("simple_result", value)
            final_locators.append({"run_id":run, "outbox_message_id":final_key,
                "artifact_path":str(Path(current["output_dir"])/"native_desktop_result.json")})
            for outcome in semantic.get("candidate_outcomes", []):
                causes.setdefault(outcome.get("candidate_id", run), outcome.get("primary_cause") or "UNKNOWN_TERMINAL_CAUSE")
            for attempt in semantic.get("candidate_attempt_history", []):
                if attempt.get("status") == "SOURCE_BLOCKED":
                    causes.setdefault(attempt.get("candidate_id", run), attempt.get("primary_cause")
                        or next(iter(attempt.get("blockers", [])), "UNKNOWN_TERMINAL_CAUSE"))
            if not semantic.get("qualified_article_count") and not semantic.get("candidate_outcomes"):
                if not semantic.get("candidate_attempt_history"):
                    causes.setdefault(run, semantic.get("first_blocking_cause") or semantic.get("primary_cause")
                        or "UNKNOWN_TERMINAL_CAUSE")
        projection = publication_projection(rows, dispatches, store.get_reconciliations_for_work_item(run), run_id=run)
        for item in projection.get("destinations", []):
            dest, status = item["destination"], item["status"]
            if (item.get("reconciliation_status") == "RECONCILED_CONFIRMED"
                    and DurablePublicationCoordinator._confirmed_public_object(item, destination=dest)):
                channels["confirmed"][dest].add(str(item["public_object_id"]))
                if dest == "substack":
                    canonical[str(item["public_object_id"])] = item.get("public_object_url")
            elif status.startswith("SKIPPED_"):
                channels["skipped"][dest].add(run)
            elif "FAILED" in status or item.get("reconciliation_status") == "RECONCILED_ABSENT_SAFE_TO_RETRY":
                channels["failed"][dest].add(run)
            else:
                channels["unresolved"][dest].add(run)
    if fatal:
        causes["terminal_process_failure"] = "SOFTWARE_PROCESS_DEFECT"
    process_failure = any(store.get_outbox_message("native-window-disposition-"+sha256_of(b["run_id"])) for b,_ in issued)
    result = {"automation_id":auto, "production_day_id":checkpoint["production_day_id"],
        "window_id":binding["window_id"], "run_ids":[b["run_id"] for b, _ in issued],
        "finished_at_utc":moment.isoformat(),
        "finished_at_gmt7":moment.astimezone(timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S GMT+7"),
        "outcome":"TERMINAL_PROCESS_FAILURE" if fatal or process_failure else "PUBLISHED" if canonical else "NO_ARTICLE",
        "canonical_items":[{"id":key, "url":url} for key, url in canonical.items()],
        "channels":{kind:{dest:len(ids) for dest, ids in values.items()} for kind, values in channels.items()},
        "first_blocking_causes":dict(Counter(causes.values())), "terminal_process_failure":fatal,
        "slot_results":final_locators, "window_progress":progress,
        "next_action":("Repair " + fatal["operation"] + ": " + fatal["error"]) if fatal else
            "Review named unresolved/failed channels through the existing coordinator; no blind retry." if any(
                channels[k] for k in ("unresolved", "failed")) else "No remaining action in this terminal window."}
    result["source_context"] = response.get("source_context",{})
    result["nominal_window_gmt7"] = start.astimezone(timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S GMT+7")
    original_entry = checkpoint.get("actual_entry_utc")
    result["actual_entry_gmt7"] = (datetime.fromisoformat(original_entry.replace("Z","+00:00"))
        .astimezone(timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S GMT+7") if original_entry else "UNOBSERVED")
    value = {"schema_version":"contentops.native_scheduled_window_result.v1", "terminal_result":result,
        "startup_result":entry, "notice_delivery":{"state":"READY", "target_thread_id":WINDOW_REPORT_L2,
            "target_host_id":WINDOW_REPORT_HOST}, "public_write_performed":False}
    result["operation_health"] = "DEGRADED_PROCESS_FAILURE" if process_failure or fatal else "TERMINAL_ACCOUNTED"
    result["stability_evidence_scope"] = "ONE_WINDOW_ONLY_NOT_THREE_DAY_STABILITY"
    _save_window_result(store, binding, value)
    return {"classification":"WINDOW_RESULT_SAVED", "artifact_path":str(_window_result_path(binding)),
        "notice_state":"READY", "next_operation":"window-notice-begin", "terminal_result":result}


def window_notice_delivery(store, binding, *, response=None, begin=False):
    """One fenced tool attempt; the scheduled chat executes the existing native tool."""
    key = _window_result_key(binding)
    lease_owner = "window-notice-" + uuid4().hex
    lease = store.acquire_lease("internal:native-window:" + (binding.get("window_id") or binding["run_id"]), lease_owner, ttl_seconds=60)
    try:
        row = store.get_outbox_message(key)
        if not row:
            raise ValueError("SAVED_TERMINAL_WINDOW_RESULT_REQUIRED")
        value = json.loads(row["payload"])
        if not value.get("terminal_result"):
            raise ValueError("SAVED_TERMINAL_WINDOW_RESULT_REQUIRED")
        if value["terminal_result"]["run_ids"][-1] != binding["run_id"]:
            raise ValueError("EXACT_TERMINAL_WINDOW_RUN_REQUIRED")
        delivery = value["notice_delivery"]
        if begin:
            if delivery["state"] != "READY":
                return {"classification":"WINDOW_NOTICE_SUPPRESSED", "reason":delivery["state"],
                    "artifact_path":str(_window_result_path(binding))}
            if not value["terminal_result"].get("source_context"):
                disposition_row = store.get_outbox_message("native-window-disposition-"+sha256_of(binding["run_id"]))
                if disposition_row:
                    disposition = json.loads(disposition_row["payload"])
                    evidence = json.loads(Path(disposition["evidence_path"]).read_bytes())
                    if evidence.get("run_id") != binding["run_id"]:
                        raise ValueError("EXACT_TERMINAL_SOURCE_CONTEXT_REQUIRED")
                    result = value["terminal_result"]
                    result["source_context"] = {k:evidence[k] for k in ("source_thread_id","source_turn_id")}
                    checkpoint = json.loads(store.get_outbox_message("native-window-"+sha256_of(binding["window_id"]))["payload"])
                    for source,target in ((checkpoint["window"]["start_utc"],"nominal_window_gmt7"),(checkpoint.get("actual_entry_utc"),"actual_entry_gmt7")):
                        result[target] = (datetime.fromisoformat(source.replace("Z","+00:00")).astimezone(timezone(timedelta(hours=7)))
                            .strftime("%Y-%m-%d %H:%M:%S GMT+7") if source else "UNOBSERVED")
            args = {"threadId":WINDOW_REPORT_L2, "hostId":WINDOW_REPORT_HOST,
                "prompt":_window_notice(value, _window_result_path(binding))}
            delivery.update(state="ATTEMPT_STARTED", tool="send_message_to_thread", arguments=args,
                attempt_started_at_utc=datetime.now(timezone.utc).isoformat())
            _save_window_result(store, binding, value)
            return {"classification":"WINDOW_NOTICE_SEND_ONCE", "tool":"send_message_to_thread", "arguments":args,
                "artifact_path":str(_window_result_path(binding))}
        if delivery["state"] != "ATTEMPT_STARTED":
            return {"classification":"WINDOW_NOTICE_SUPPRESSED", "reason":delivery["state"]}
        tool_result = response or {}
        def targets(item):
            if isinstance(item, dict):
                return [v for k, v in item.items() if k in {"threadId", "thread_id"}] + [
                    v for child in item.values() for v in targets(child)]
            if isinstance(item, list):
                return [v for child in item for v in targets(child)]
            if isinstance(item, str):
                try:
                    return targets(json.loads(item))
                except (ValueError, TypeError):
                    return []
            return []
        ok = tool_result.get("isError") is False and WINDOW_REPORT_L2 in targets(tool_result)
        delivery.update(state="DELIVERED" if ok else "FAILED", tool_result=tool_result,
            recorded_at_utc=datetime.now(timezone.utc).isoformat(),
            failure=None if ok else "TOOL_FAILED_OR_TARGET_NOT_CONFIRMED_NO_AUTOMATIC_RETRY")
        _save_window_result(store, binding, value)
        return {"classification":"WINDOW_NOTICE_" + delivery["state"],
            "artifact_path":str(_window_result_path(binding)), "retry_allowed":False}
    finally:
        store.release_lease(lease["lease_id"], lease_owner, lease["fencing_token"])


def close_expired_window(store, rollout, binding, response, *, now=None):
    owner = "window-close-" + uuid4().hex
    lease = store.acquire_lease("internal:native-editorial:"+binding["run_id"],owner,ttl_seconds=60)
    try:
        return _close_expired_window(store,rollout,binding,response,now=now)
    finally:
        store.release_lease(lease["lease_id"],owner,lease["fencing_token"])


def _close_expired_window(store, rollout, binding, response, *, now=None):
    """Account for an expired, stopped operation without inventing native returns."""
    from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn, DESTINATION
    moment = now or datetime.now(timezone.utc)
    checkpoint_row = store.get_outbox_message("native-window-" + sha256_of(binding["window_id"]))
    checkpoint = json.loads(checkpoint_row["payload"])
    issued, _ = _issued_slots(store, rollout, binding["automation_id"], checkpoint)
    end = datetime.fromisoformat(checkpoint["window"]["end_utc"].replace("Z", "+00:00")) + timedelta(hours=1)
    if moment <= end or not issued or binding != issued[-1][0]:
        raise ValueError("EXPIRED_EXACT_LAST_WINDOW_REQUIRED")
    evidence = json.loads(Path(response["artifact_path"]).read_bytes())
    if (evidence.get("run_id") != binding["run_id"] or evidence.get("turn_status") != "completed"
            or evidence.get("active_native_role") is not False or not evidence.get("observation_source")
            or not evidence.get("source_thread_id") or not evidence.get("source_turn_id")
            or response.get("outcome") not in {"LATE", "PROCESS_FAILURE"}
            or not response.get("first_cause") or not response.get("reason")):
        raise ValueError("ACTUAL_STOPPED_WINDOW_DISPOSITION_REQUIRED")
    if any(x in response["first_cause"].upper() for x in ("QUOTA", "USAGE_LIMIT")):
        raise ValueError("QUOTA_IS_NOT_TERMINAL_WINDOW_FAILURE")
    turn = NativeDesktopTurn(store, run_id=binding["run_id"], output_dir=binding["output_dir"])
    pending = turn.frozen_request(evidence.get("pending_stage", ""))
    if not pending or pending["request_sha256"] != evidence.get("pending_request_sha256"):
        raise ValueError("EXACT_UNFINISHED_NATIVE_STAGE_REQUIRED")
    if turn._get(pending["stage"], "response"):
        raise ValueError("PENDING_STAGE_ALREADY_ACCEPTED")
    owner_key = "native-window-disposition-" + sha256_of(binding["run_id"])
    existing = store.get_outbox_message(owner_key)
    if not existing:
        final_key = "cc-editorial-final-" + sha256_of(binding["run_id"])
        if store.get_outbox_message(final_key):
            raise ValueError("EXISTING_EDITORIAL_RESULT_CANNOT_BE_REPLACED")
        disposition = {"classification":"NATIVE_WINDOW_PROCESS_DISPOSITION", "run_id":binding["run_id"],
            "outcome":response["outcome"], "first_cause":response["first_cause"], "reason":response["reason"],
            "evidence_path":response["artifact_path"], "closed_at_utc":moment.isoformat(),
            "unanswered_request_state":"ABANDONED_EXPIRED_NOT_A_NATIVE_RETURN",
            "pending_stage":pending["stage"], "pending_request_sha256":pending["request_sha256"],
            "accepted_native_history_preserved":True, "qualified_article_count":0, "public_write_performed":False}
        store.register_outbox_message(message_id=owner_key,work_item_id=turn.work,destination=DESTINATION,
            status="EDITORIAL_INTERNAL",payload=canonical_bytes(disposition).decode())
        final = {**disposition,"classification":"NATIVE_WINDOW_PROCESS_FAILURE",
            "first_blocking_cause":response["first_cause"],"derivative_intent_count":0}
        store.register_outbox_message(message_id=final_key,work_item_id=turn.work,destination=DESTINATION,
            status="EDITORIAL_INTERNAL",payload=canonical_bytes(final).decode())
        Path(binding["output_dir"],"native_desktop_result.json").write_bytes(canonical_bytes(final))
    entry = response.get("startup_result") or {"classification":"EXPIRED_ISSUED_WINDOW_OWNER_CLOSURE",
        "window_id":binding["window_id"],"run_id":binding["run_id"],
        "actual_entry_utc":moment.isoformat(),
        "original_actual_entry_utc":checkpoint.get("actual_entry_utc"),
        "observation_source":"CURRENT_EXPIRED_OWNER_CLOSURE_NOT_HISTORICAL_STARTUP_CLI"}
    return prepare_window_result(store,rollout,binding,{"startup_result":entry,
        "source_context":{k:evidence[k] for k in ("source_thread_id","source_turn_id")}},now=moment)


def window_blocked_notice(store, binding, response, *, begin=False, record=False):
    """One distinct real blocker in the existing window record; never terminal proof."""
    from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn
    scheduled = bool(binding.get("automation_id"))
    key = "native-window-" + sha256_of(binding["window_id"]) if scheduled else _window_result_key(binding)
    owner = "window-blocked-" + uuid4().hex
    lease = store.acquire_lease("internal:native-window:"+(binding.get("window_id") or binding["run_id"]),owner,ttl_seconds=60)
    try:
        row = store.get_outbox_message(key)
        if not scheduled and not begin and not record:
            _standalone_context(response)
            if not row:
                _save_window_result(store,binding,{"schema_version":"contentops.native_task_result.v1","blocked_notices":{}})
                row = store.get_outbox_message(key)
        if not row:
            raise ValueError("EXACT_SCHEDULED_WINDOW_REQUIRED")
        checkpoint = json.loads(row["payload"])
        notices = checkpoint.setdefault("blocked_notices",{})
        blocker_id = response.get("blocker_id")
        if begin or record:
            item = notices[blocker_id]
            delivery = item["notice_delivery"]
            if begin:
                if delivery["state"] != "READY":
                    return {"classification":"WINDOW_BLOCKED_SUPPRESSED","reason":delivery["state"]}
                args = {"threadId":WINDOW_REPORT_L2,"hostId":WINDOW_REPORT_HOST,"prompt":item["notice_text"]}
                delivery.update(state="ATTEMPT_STARTED",arguments=args)
                result = {"classification":"WINDOW_BLOCKED_SEND_ONCE","blocker_id":blocker_id,"arguments":args}
            else:
                if delivery["state"] != "ATTEMPT_STARTED":
                    return {"classification":"WINDOW_BLOCKED_SUPPRESSED","reason":delivery["state"]}
                actual = response["tool_result"]
                ok = actual.get("isError") is False and _tool_target_confirmed(actual,WINDOW_REPORT_L2)
                delivery.update(state="DELIVERED" if ok else "FAILED",tool_result=actual)
                result = {"classification":"WINDOW_BLOCKED_"+delivery["state"],"retry_allowed":False}
        else:
            cause = response.get("first_cause", "")
            if (response.get("interruption_kind") in {"QUOTA","TURN_END","GUARD","DUPLICATE","EARLY"}
                    or any(x in (cause+str(response.get("blocker",""))).upper() for x in ("QUOTA","USAGE_LIMIT","TURN_END","GUARD","DUPLICATE","PREMATURE"))):
                return {"classification":"WINDOW_BLOCKED_SUPPRESSED","reason":"NON_ACTIONABLE_INTERRUPTION"}
            if (response.get("unable_to_continue") is not True or response.get("active_native_role") is not False
                    or cause not in {"FUTURE_EVENT","OTHER_LANE","OWNER_DECISION","UNRESOLVED_PROCESS_DEFECT","NATIVE_PLATFORM_UNAVAILABLE","SOURCE_ACCESS_BLOCKED"}
                    or not all(response.get(k) for k in ("stage","blocker","smallest_next_action","responsible_owner","artifact_path"))):
                raise ValueError("GENUINE_BLOCKED_WINDOW_EVIDENCE_REQUIRED")
            artifact = json.loads(Path(response["artifact_path"]).read_bytes())
            if artifact.get("run_id") != binding["run_id"] or not artifact.get("observation_source"):
                raise ValueError("EXACT_BLOCKED_ARTIFACT_REQUIRED")
            stage, request_hash = response["stage"], response.get("request_sha256")
            if request_hash:
                pending = NativeDesktopTurn(store,run_id=binding["run_id"],output_dir=binding["output_dir"]).frozen_request(stage)
                if not pending or pending["request_sha256"] != request_hash:
                    raise ValueError("EXACT_BLOCKED_PENDING_REQUEST_REQUIRED")
            blocker_id = sha256_of([binding["run_id"],stage,request_hash,cause,
                response.get("blocker_identity",cause),response["responsible_owner"]])
            if blocker_id in notices:
                return {"classification":"WINDOW_BLOCKED_SUPPRESSED","reason":"BLOCKER_ALREADY_SAVED","blocker_id":blocker_id}
            text = (("BLOCKED — scheduled V1 window; " if scheduled else "BLOCKED — standalone V1 task; ") + datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S GMT+7")
                + "\nWindow: "+str(binding.get("window_id") or "NOT_SCHEDULED")+"; run: "+binding["run_id"]
                + "\nSource chat/session: "+str(artifact.get("source_thread_id","UNOBSERVED"))
                + "\nDelivered: "+response.get("delivered","See saved operation")
                + "\nStage: "+stage+"; pending request: "+str(request_hash)
                + "\nFirst cause: "+cause+"; "+response["blocker"]
                + "\nNext/resume condition: "+response["smallest_next_action"]+"; owner: "+response["responsible_owner"]
                + "\nArtifact: "+response["artifact_path"]+"\nThis is not a terminal-window or engineering completion notice.")
            item = {"blocker_id":blocker_id,"evidence":response,"notice_text":text,
                "notice_delivery":{"state":"READY"},"terminal_window":False}
            notices[blocker_id] = item
            result = {"classification":"WINDOW_BLOCKED_SAVED","blocker_id":blocker_id}
        if scheduled:
            store.finalize_outbox_payload_before_dispatch(message_id=key,payload=canonical_bytes(checkpoint).decode(),status="EDITORIAL_INTERNAL")
        else:
            _save_window_result(store,binding,checkpoint)
        path = (Path(binding["output_dir"]).parent if scheduled else Path(binding["output_dir"]))/("native_window_blocked_"+blocker_id+".json")
        path.write_bytes(canonical_bytes(item))
        return {**result,"artifact_path":str(path)}
    finally:
        store.release_lease(lease["lease_id"],owner,lease["fencing_token"])


def _tool_target_confirmed(value, target):
    if isinstance(value,dict):
        return any((k in {"threadId","thread_id"} and v == target) or _tool_target_confirmed(v,target) for k,v in value.items())
    if isinstance(value,list):
        return any(_tool_target_confirmed(v,target) for v in value)
    if isinstance(value,str):
        try:
            return _tool_target_confirmed(json.loads(value),target)
        except (ValueError,TypeError):
            return False
    return False


def _standalone_context(response):
    from uuid import UUID
    context = response.get("source_context") or {}
    if context.get("source_role") != "STANDALONE_TASK" or not context.get("source_thread_id"):
        raise ValueError("ACTUAL_STANDALONE_TASK_CONTEXT_REQUIRED_NOT_ENGINEERING_COMPLETION")
    UUID(context["source_thread_id"])
    return context


def prepare_standalone_result(store, binding, response):
    """Same result/outbox and fenced native sender for current standalone triggers."""
    context = _standalone_context(response)
    if binding.get("automation_id") or response.get("entry_path") not in {"newsroom","follow-up","editorial-revision"}:
        raise ValueError("EXACT_CURRENT_STANDALONE_ENTRY_REQUIRED")
    registered = store.get_outbox_message("native-operation-binding-"+sha256_of(binding["run_id"]))
    if not registered or json.loads(registered["payload"]) != binding:
        raise ValueError("EXACT_REGISTERED_STANDALONE_BINDING_REQUIRED")
    key = _window_result_key(binding)
    prior = store.get_outbox_message(key)
    saved = json.loads(prior["payload"]) if prior else {}
    if saved.get("terminal_result"):
        return {"classification":"WINDOW_NOTICE_SUPPRESSED","reason":"RESULT_ALREADY_SAVED","artifact_path":str(_window_result_path(binding))}
    final = store.get_outbox_message("cc-editorial-final-"+sha256_of(binding["run_id"]))
    if not final or _unfinished_window_roles(store,[(binding,None)]):
        raise ValueError("ACTUAL_TERMINAL_STANDALONE_RESULT_REQUIRED")
    value = json.loads(final["payload"])
    semantic = value.get("simple_result",value)
    if any(s in str(semantic.get("classification","")).upper() for s in ("QUOTA","INTERRUPTED")):
        return {"classification":"WINDOW_BLOCKED_SUPPRESSED","reason":"QUOTA_OR_TURN_END"}
    if semantic.get("qualified_article_count"):
        with store.get_read_only_connection() as conn:
            review = conn.execute("SELECT decision FROM review_records WHERE work_item_id=? AND reviewer_ref=? ORDER BY rowid DESC LIMIT 1",
                (final["work_item_id"],"NATIVE_DESKTOP_ARTICLE_REVIEW")).fetchone()
        if not review or review["decision"] != "KEEP":
            raise ValueError("STANDALONE_ARTICLE_CURRENT_REVIEW_REQUIRED")
        from live_contentops.native_desktop_publication_v1 import _prepared_packet
        _prepared_packet(store,binding)  # Exact article/media/final-render review, not a stale KEEP.
    from collections import Counter
    causes = Counter(o["primary_cause"] for o in semantic.get("candidate_outcomes",[]))
    if not causes and not semantic.get("qualified_article_count"):
        causes[semantic.get("first_blocking_cause") or semantic.get("exact_next_blocker") or "NO_MATERIAL_STORY"] += 1
    now = datetime.now(timezone.utc)
    result = {"standalone_task":True,"automation_id":response["entry_path"],"window_id":None,
        "production_day_id":newsroom_production_day_id(binding["cutoff_utc"]),"run_ids":[binding["run_id"]],
        "source_context":context,"finished_at_utc":now.isoformat(),
        "finished_at_gmt7":now.astimezone(timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S GMT+7"),
        "actual_entry_gmt7":response.get("actual_entry_gmt7","UNOBSERVED"),
        "outcome":"EDITORIAL_ARTIFACT_DELIVERED" if semantic.get("qualified_article_count") else semantic.get("classification","NO_STORY"),
        "canonical_items":[],"channels":{},"first_blocking_causes":dict(causes),
        "evidence_result_key":final["message_id"],"evidence_path":str(Path(binding["output_dir"])/"native_desktop_result.json"),
        "next_action":response.get("next_action","Review the exact dated task result; no automatic public write."),
        "next_actor":response.get("next_actor","L2 ContentOps")}
    from live_contentops.native_desktop_publication_v1 import publication_projection
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
    projection = publication_projection(store.list_outbox_messages(),store.list_platform_dispatches(),
        store.get_reconciliations_for_work_item(binding["run_id"]),run_id=binding["run_id"])
    for destination in projection.get("destinations",[]):
        if (destination["destination"] == "substack"
                and DurablePublicationCoordinator._confirmed_public_object(destination,destination="substack")):
            result["canonical_items"].append({"id":destination["public_object_id"],"url":destination["public_object_url"]})
    if result["canonical_items"]:
        result["outcome"] = "PUBLISHED"
    saved.update(schema_version="contentops.native_task_result.v1",terminal_result=result,
        notice_delivery={"state":"READY","target_thread_id":WINDOW_REPORT_L2,"target_host_id":WINDOW_REPORT_HOST})
    _save_window_result(store,binding,saved)
    return {"classification":"WINDOW_RESULT_SAVED","artifact_path":str(_window_result_path(binding)),"terminal_result":result}
