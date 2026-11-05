"""Candidate scope inside one frozen manual native operation, over its existing outbox.

This owns no worker, binding, source ledger or publisher. Only the native owner may
append a transition, under the operation lease. Original operation records stay exact.
"""
from __future__ import annotations

import json
from hashlib import sha256

from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from live_contentops.native_desktop_workspace_v1 import resolve_workspace_path

DESTINATION = "internal:native-manual-candidate"


def manual_candidates(store, run_id):
    work = "cc-opportunity-" + sha256_of(run_id)
    values = []
    with store.get_read_only_connection() as conn:
        rows = conn.execute("SELECT message_id,payload FROM outbox_messages WHERE work_item_id=? AND destination=? ORDER BY rowid",
                            (work, DESTINATION)).fetchall()
    for row in rows:
        value = json.loads(row["payload"])
        if (value.get("run_id") != run_id or value.get("schema_version") != "contentops.native_manual_candidate.v1"
                or row["message_id"] != "native-manual-candidate-" + sha256_of(value)
                or value.get("previous_transition_sha256") != (sha256_of(values[-1]) if values else None)):
            raise ValueError("MANUAL_CANDIDATE_HISTORY_CONFLICT")
        values.append(value)
    return values


def active_manual_candidate(store, run_id):
    values = manual_candidates(store, run_id)
    return values[-1] if values else None


def native_artifact_key(store, run_id, prefix):
    active = active_manual_candidate(store, run_id)
    identity = [run_id, active["candidate_id"]] if active else run_id
    if prefix == "cc-editorial-final-":
        # A verified pre-writer recovery gets its own final artifact. The original
        # zero-writer SOURCE_BLOCKED result remains immutable and discoverable.
        work = "cc-opportunity-" + sha256_of(run_id)
        with store.get_read_only_connection() as conn:
            rows = conn.execute("SELECT payload FROM outbox_messages WHERE work_item_id=? AND destination=? ORDER BY rowid DESC",
                (work, "internal:native-desktop-source-recovery")).fetchall()
        recovery = next((v for row in rows if (v := json.loads(row["payload"]))
            and v.get("pre_writer_source_recovery")
            and (not active or v.get("candidate_id") == active["candidate_id"])), None)
        if recovery:
            identity = [identity, "source-recovery", recovery["request_sha256"]]
    return prefix + sha256_of(identity)


def candidate_root(base, candidate_id):
    return resolve_workspace_path(base) / "candidates" / sha256_of(candidate_id)


def manual_output_root(store, binding):
    active = active_manual_candidate(store, binding["run_id"])
    return candidate_root(binding["output_dir"], active["candidate_id"]) if active else resolve_workspace_path(binding["output_dir"])


def manual_source_count(turn):
    """Use durable completed source deltas and retained per-scope totals, never reset."""
    histories = manual_candidates(turn.store, turn.run_id)
    roots = [(turn.operation_root, 0)] + [(candidate_root(turn.operation_root, h["candidate_id"]), h["source_request_count_at_start"])
                                           for h in histories]
    totals = [turn.source_request_count_at_start]
    for root, start in roots:
        path = root / "simple_gemini_evidence_v1.json"
        if path.is_file():
            walk = json.loads(path.read_bytes())
            if type(walk.get("request_count")) is not int or walk["request_count"] < start:
                raise ValueError("MANUAL_SOURCE_BUDGET_REGRESSION")
            if walk.get("request_limit") != turn.volume_policy["source_request_limit"]:
                raise ValueError("MANUAL_SOURCE_LIMIT_CHANGED")
            totals.append(walk["request_count"])
    with turn.store.get_read_only_connection() as conn:
        rows = [json.loads(r["payload"]) for r in conn.execute("SELECT payload FROM outbox_messages WHERE work_item_id=?", (turn.work,))]
    sources = [r for r in rows if str(r.get("stage", "")).startswith("source:")]
    completed = {(r["stage"], r["request_sha256"]) for r in sources if "result" in r}
    if any((r["stage"], r["request_sha256"]) not in completed for r in sources):
        raise ValueError("MANUAL_SOURCE_STEP_RESULT_NOT_RECORDED")
    active = histories[-1] if histories else None
    current = active["candidate_id"] if active else None
    spent = sum(int(r["result"].get("provenance", {}).get("request_count_for_call") or 0)
                for r in sources if "result" in r and r.get("manual_candidate_id") == current)
    frozen = turn.store.get_outbox_message("native-current-input-" + sha256_of(turn.run_id))
    reviews = json.loads(frozen["payload"]).get("source_requests_before_writer_freeze", 0) if frozen else 0
    totals.append((active["source_request_count_at_start"] if active else reviews) + spent)
    totals.extend(r["source_request_count"] for r in turn.story_outcomes())
    totals.extend(r["source_request_count"] for r in rows if r.get("pre_writer_source_recovery"))
    used = max(totals)
    limit = turn.volume_policy["source_request_limit"]
    if not 0 <= used <= limit:
        raise ValueError("MANUAL_SOURCE_BUDGET_EXCEEDED")
    return used


def manual_continuation_request(turn, binding):
    """Expose current exact preconditions; no claim that the transition is permitted yet."""
    selection, selected = turn.frozen_request("select"), turn._get("select", "response")
    frozen = turn.store.get_outbox_message("native-current-input-" + sha256_of(turn.run_id))
    if not selection or not selected or not frozen:
        raise ValueError("EXACT_FROZEN_MANUAL_SELECTION_REQUIRED")
    walk = turn.root / "simple_gemini_evidence_v1.json"
    return {"binding_sha256": sha256_of(binding),
        "cutoff_utc": binding.get("input_known_at_cutoff_utc", binding["cutoff_utc"]),
        "selection_request_sha256": selection["request_sha256"], "selection_response_sha256": sha256_of(selected),
        "frozen_input_sha256": sha256_of(json.loads(frozen["payload"])),
        "outcomes_sha256": sha256_of(turn.story_outcomes()),
        "evidence_sha256": sha256(walk.read_bytes()).hexdigest() if walk.is_file() else None,
        "source_request_count": manual_source_count(turn),
        "previous_transition_sha256": sha256_of(turn.manual_candidate) if turn.manual_candidate else None}


def continue_manual_candidate(turn, binding, *, candidate_id, response, lease):
    """Validate an explicit untouched next admission; caller holds the native-operation lease."""
    from live_contentops.native_newsroom_volume_v1 import bound_volume_policy

    policy = bound_volume_policy(binding)
    if (binding.get("automation_id") or binding.get("window_id") or not policy
            or not (binding.get("owner_manual_live") or binding.get("owner_manual_validation"))):
        raise ValueError("EXACT_MANUAL_CANDIDATE_POLICY_REQUIRED")
    registered = turn.store.get_outbox_message("native-operation-binding-" + sha256_of(turn.run_id))
    if not registered or json.loads(registered["payload"]) != binding:
        raise ValueError("EXACT_REGISTERED_MANUAL_BINDING_REQUIRED")
    selection, selected = turn.frozen_request("select"), turn._get("select", "response")
    frozen = turn.store.get_outbox_message("native-current-input-" + sha256_of(turn.run_id))
    if not selection or not selected or not frozen:
        raise ValueError("EXACT_FROZEN_MANUAL_SELECTION_REQUIRED")
    frozen_value = json.loads(frozen["payload"])
    cutoff = binding.get("input_known_at_cutoff_utc", binding["cutoff_utc"])
    if (selected["request_sha256"] != selection["request_sha256"]
            or selection["governed_input"].get("cutoff_utc") != cutoff
            or frozen_value.get("run_id") != turn.run_id or frozen_value.get("cutoff_utc") != cutoff):
        raise ValueError("MANUAL_FROZEN_CUTOFF_OR_SELECTION_CHANGED")
    expected = {"binding_sha256": sha256_of(binding), "cutoff_utc": cutoff,
        "selection_request_sha256": selection["request_sha256"], "selection_response_sha256": sha256_of(selected),
        "frozen_input_sha256": sha256_of(frozen_value)}
    if not isinstance(response, dict) or any(response.get(k) != v for k, v in expected.items()):
        raise ValueError("EXACT_MANUAL_CONTINUATION_INPUT_REQUIRED")
    # Recovery always precedes another semantic intent, including an idempotent repeat.
    ambiguous = [d for d in turn.store.list_platform_dispatches()
                 if any(s in str(d.get("status", "")).upper() for s in ("UNKNOWN", "AMBIG", "STARTED", "PENDING", "SENDING"))]
    with turn.store.get_read_only_connection() as conn:
        pending = conn.execute("SELECT COUNT(*) FROM reconciliations WHERE status IN ('PENDING','STARTED','UNKNOWN_WRITE')").fetchone()[0]
    with turn.store.get_read_only_connection() as conn:
        rows = [dict(r) for r in conn.execute("SELECT * FROM outbox_messages WHERE work_item_id IN (?,?) ORDER BY rowid", (turn.work, turn.run_id))]
    ids = {r["message_id"] for r in rows}
    if ambiguous or pending or any(d["message_id"] in ids for d in turn.store.list_platform_dispatches()):
        raise ValueError("MANUAL_CONTINUATION_REQUIRES_EXISTING_PUBLICATION_RECOVERY")
    values = [json.loads(r["payload"]) for r in rows]
    if any(r.get("qualified_article_count") for r in values) or any(
            r["destination"] in {"internal:native-publication-binding", "internal:native-prepared-handoff"} for r in rows):
        raise ValueError("MANUAL_CONTINUATION_CANNOT_SKIP_QUALIFIED_ARTICLE")
    if any(r["message_id"] in {"native-window-disposition-" + sha256_of(turn.run_id),
                              "native-task-result-" + sha256_of(turn.run_id)} for r in rows):
        raise ValueError("MANUAL_OPERATION_ALREADY_CLOSED")
    active = turn.manual_candidate
    if active and candidate_id == active["candidate_id"]:
        if response != active["intent"]:
            raise ValueError("MANUAL_CANDIDATE_REPEAT_CONFLICT")
        return {**active["result"], "idempotent_replay": True}
    prior_hash = sha256_of(active) if active else None
    if response.get("previous_transition_sha256") != prior_hash:
        raise ValueError("MANUAL_CANDIDATE_TRANSITION_STALE")
    # Every issued role must have its exact accepted return before moving scope.
    requests = [r for r in values if r.get("requested_model")]
    accepted = {r.get("request_sha256") for r in values if "output" in r and r.get("invocation_observation")}
    if any(r["request_sha256"] not in accepted for r in requests):
        raise ValueError("MANUAL_CANDIDATE_HAS_PENDING_NATIVE_RETURN")
    outcomes = turn.story_outcomes()
    if (not outcomes or response.get("outcomes_sha256") != sha256_of(outcomes)
            or (active and active["candidate_id"] not in {r["candidate_id"] for r in outcomes})):
        raise ValueError("EXACT_TERMINAL_PREDECESSOR_OUTCOMES_REQUIRED")
    plan = selected["output"].get("ordered_candidate_plan", [])
    pending_ids = [p["candidate_id"] for p in plan if p["candidate_id"] not in {r["candidate_id"] for r in outcomes}]
    if not candidate_id or not pending_ids or candidate_id != pending_ids[0]:
        raise ValueError("EXACT_NEXT_UNTOUCHED_MANUAL_CANDIDATE_REQUIRED")
    if any(str(r.get("stage", "")).startswith("source:" + candidate_id) for r in values):
        raise ValueError("MANUAL_CANDIDATE_ALREADY_SOURCE_REACHED")
    walk_path = turn.root / "simple_gemini_evidence_v1.json"
    walk_hash = sha256(walk_path.read_bytes()).hexdigest() if walk_path.is_file() else None
    if response.get("evidence_sha256") != walk_hash:
        raise ValueError("MANUAL_CANDIDATE_SOURCE_WALK_CHANGED")
    used = manual_source_count(turn)
    if type(response.get("source_request_count")) is not int or response["source_request_count"] != used:
        raise ValueError("EXACT_MANUAL_SOURCE_BUDGET_REQUIRED")
    if used >= policy["source_request_limit"]:
        raise ValueError("MANUAL_CANDIDATE_SOURCE_BUDGET_EXHAUSTED")
    root = candidate_root(turn.operation_root, candidate_id)
    sourceability = turn.operation_root / "simple_sourceability_preselection_v1.json"
    if not sourceability.is_file():
        raise ValueError("FROZEN_MANUAL_SOURCEABILITY_REQUIRED")
    result = {"classification": "NATIVE_MANUAL_CANDIDATE_READY", "run_id": turn.run_id,
        "candidate_id": candidate_id, "source_request_count": used, "source_request_limit": policy["source_request_limit"],
        "next_operation": "advance same binding", "new_binding": False, "new_model_invocations": 0,
        "new_source_requests": 0, "public_write_performed": False}
    value = {"schema_version": "contentops.native_manual_candidate.v1", "run_id": turn.run_id,
        "candidate_id": candidate_id, "previous_transition_sha256": prior_hash,
        "binding_sha256": expected["binding_sha256"], "cutoff_utc": cutoff,
        "source_request_count_at_start": used, "sourceability_sha256": sha256(sourceability.read_bytes()).hexdigest(),
        "prior_outcomes": outcomes, "intent": response, "result": result}
    # Check the live fence and append in one existing-store transaction. A worker
    # whose lease expired cannot append after another worker has taken ownership.
    from live_contentops.durable_operational_store_v1 import StaleFencingTokenError
    with turn.store.get_connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            current = conn.execute("SELECT * FROM leases WHERE lease_key=?",
                ("internal:native-editorial:" + turn.run_id,)).fetchone()
            if (not lease or not current or current["status"] != "ACTIVE"
                    or current["expires_at"] <= turn.store._get_now_iso()
                    or any(current[k] != lease[k] for k in ("lease_id", "owner_ref", "fencing_token"))):
                raise StaleFencingTokenError("MANUAL_CANDIDATE_OPERATION_FENCE_CHANGED")
            latest = conn.execute("SELECT payload FROM outbox_messages WHERE work_item_id=? AND destination=? ORDER BY rowid DESC LIMIT 1",
                (turn.work, DESTINATION)).fetchone()
            if (sha256_of(json.loads(latest["payload"])) if latest else None) != prior_hash:
                raise ValueError("MANUAL_CANDIDATE_TRANSITION_STALE")
            root.mkdir(parents=True, exist_ok=True)
            target = root / sourceability.name
            if target.exists() and target.read_bytes() != sourceability.read_bytes():
                raise ValueError("MANUAL_CANDIDATE_SOURCEABILITY_CONFLICT")
            target.write_bytes(sourceability.read_bytes())
            conn.execute("INSERT INTO outbox_messages(message_id,work_item_id,destination,payload,status,created_at) VALUES (?,?,?,?,?,?)",
                ("native-manual-candidate-" + sha256_of(value), turn.work, DESTINATION,
                 canonical_bytes(value).decode(), "EDITORIAL_INTERNAL", turn.store._get_now_iso()))
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
    return {**result, "idempotent_replay": False}
