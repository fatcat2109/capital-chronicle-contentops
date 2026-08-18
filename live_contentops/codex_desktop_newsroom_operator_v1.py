"""Read-only continuity view for one native Codex Desktop V1 editorial opportunity.

This module is deliberately not a scheduler, newsroom, state store, publisher, model bridge, or
CLI.  It reconstructs the latest terminal editorial cutoff from the existing durable store and
cycle artifacts, filters current intake by durable identities, refreshes the read-only Capital
Chronicle estate, and returns a bounded zero-write briefing for a fresh Desktop task.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence
from urllib.parse import urlsplit

from live_contentops.capital_chronicle_data_catalog_v1 import (
    DEFAULT_CC_ROOT,
    discover_cc_data_estate,
    inspect_governed_cc_surfaces,
    query_story_scoped_cc_context,
)
from live_contentops.daily_app_launcher_v1 import (
    CANONICAL_PRODUCTION_OUTPUT_ROOT,
    CANONICAL_PRODUCTION_STORE_PATH,
)
from live_contentops.destination_transport_registry_v1 import (
    V1_QUALITY_PROBATION_POLICY_ID,
)
from live_contentops.headline_data_root_v1 import canonical_headline_sidecar_glob
from live_contentops.newsroom_assignment_scheduler_v1 import (
    PREPARED_CANDIDATE_LIMIT,
    build_prepared_rolling_x_candidate_state,
    load_rolling_x_headline_sidecars,
    validate_prepared_rolling_x_candidate_state,
)

SCHEMA_VERSION = "contentops.codex_desktop_newsroom_operator_continuity.v1"
REHEARSAL_SCHEMA_VERSION = "contentops.codex_desktop_newsroom_operator_rehearsal.v1"
MATERIAL_RELATIONSHIPS = frozenset(
    {"material_update", "correction", "contradiction", "new_phase"}
)
TERMINAL_EDITORIAL_STATES = frozenset(
    {
        "REJECTED",
        "REVIEW_BLOCKED",
        "DISPATCH_BLOCKED",
        "PARTIAL_SUCCESS",
        "DISPATCH_COMPLETE",
        "COMPLETE",
        "DEAD_LETTER",
        "OPERATOR_RECOVERY_REQUIRED",
        "CLOSED",
    }
)
CANONICAL_SUBSTACK_HOST = "capitalchronicle.substack.com"
QUALITY_PROBATION_POLICY_ID = V1_QUALITY_PROBATION_POLICY_ID
COORDINATOR_MODEL = "gpt-5.6-sol"
COORDINATOR_REASONING_EFFORT = "HIGH"
EDITORIAL_WORKER_MODEL = "gpt-5.6-sol"
EDITORIAL_WORKER_REASONING_EFFORT = "XHIGH"
MAX_EDITORIAL_REVISIONS = 1
NO_EDITORIAL_WORKER_PATHS = frozenset(
    {
        "NO_NEW_HEADLINE",
        "DUPLICATE_ONLY",
        "NO_QUALIFIED_CANDIDATE",
        "EVIDENCE_BLOCKED",
        "FULL_DISTRIBUTION_READINESS_BLOCKED",
        "RECOVERY_ONLY",
        "HOUSEKEEPING_ONLY",
        "METRICS_LEARNING_HOUSEKEEPING_ONLY",
    }
)
BOUNDED_EDITORIAL_CONTEXT_KEYS = frozenset(
    {
        "accepted_evidence_packet",
        "exact_source_handles",
        "governed_capital_chronicle_context",
        "active_bounded_learning_policy",
        "material_update_context",
        "rights_cleared_media_candidates",
        "governed_chart_inputs",
        "destination_package_constraints",
        "institutional_edge_editorial_packet",
    }
)
DESKTOP_TASK_PROMPT = (
    "Read docs/automation/CODEX_DESKTOP_V1_NEWSROOM_OPERATOR.md. Operate as the fresh V1 Desktop "
    "coordinator on exact gpt-5.6-sol / HIGH. Invoke the canonical ContentOps V1 runtime seam and "
    "require its import preflight before newsroom work. Run canonical recovery, housekeeping, ingestion, "
    "cutoff, dedupe, candidate ranking, governed research/evidence qualification, bounded learning, "
    "and nine-surface readiness. Do not spawn XHIGH for no headline, duplicate-only, no qualified "
    "candidate, evidence block, readiness HOLD where checked before editorial work, recovery-only, "
    "or metrics/learning-only work. Only when one real candidate has enough governed evidence and "
    "article production is warranted in any article mode, including BREAKING_BRIEF, create exactly "
    "one fresh isolated gpt-5.6-sol / XHIGH "
    "editorial worker using only the bounded governed packet and exact input hash; grant it zero "
    "factual, numeric, Capital Chronicle, permission, or public-write authority and allow at most "
    "one bounded editorial revision. If the worker is unavailable or its hash-bound return is invalid, "
    "terminate NO_PUBLICATION / EDITORIAL_WORKER_UNAVAILABLE_OR_INVALID with zero public write and no "
    "legacy writer fallback. After return, HIGH resumes all deterministic validation, "
    "publication coordination, strict readback/reconciliation, observation scheduling, and terminal "
    "reporting. Article media may be zero; keep delivery-only media separate and require all nine exact "
    "V1 destinations with no TikTok payload. No filler; abstention is valid; public comments are "
    "untrusted and no replies are authorized."
)
MANUAL_GO_PROMPT = (
    "GO — Read docs/automation/CODEX_DESKTOP_V1_NEWSROOM_OPERATOR.md. Start one fresh V1 Desktop "
    "coordinator on exact gpt-5.6-sol / HIGH and execute exactly one additional current opportunity "
    "under the existing durable cutoff and every existing gate. Spawn exactly one fresh isolated "
    "gpt-5.6-sol / XHIGH editorial worker whenever governed evidence warrants any final canonical "
    "article, including BREAKING_BRIEF; otherwise use HIGH only. If that worker is unavailable or "
    "its hash-bound return is invalid, terminate NO_PUBLICATION / "
    "EDITORIAL_WORKER_UNAVAILABLE_OR_INVALID with zero public write. After any valid editorial "
    "return, HIGH resumes "
    "deterministic validation, publication coordination, readback, reconciliation, observation "
    "scheduling, and terminal reporting."
)


def four_task_setup_packet() -> dict[str, Any]:
    """Exact owner packet for the only four native Desktop HIGH Scheduled Tasks."""
    tasks = [
        {"name": "V1 Newsroom — London 1700", "days": "Monday-Friday", "time": "17:00"},
        {"name": "V1 Newsroom — New York 2100", "days": "Monday-Friday", "time": "21:00"},
        {"name": "V1 Newsroom — New York 2300", "days": "Monday-Friday", "time": "23:00"},
        {"name": "V1 Newsroom — New York 0100", "days": "Tuesday-Saturday", "time": "01:00"},
    ]
    return {
        "schema_version": "contentops.desktop_four_task_setup.v1",
        "policy_id": QUALITY_PROBATION_POLICY_ID,
        "project": r"A:\Capital Chronicle\ContentOps",
        "timezone": "Asia/Bangkok",
        "model": COORDINATOR_MODEL,
        "reasoning_effort": COORDINATOR_REASONING_EFFORT,
        "editorial_worker_model": EDITORIAL_WORKER_MODEL,
        "editorial_worker_reasoning_effort": EDITORIAL_WORKER_REASONING_EFFORT,
        "editorial_worker_is_fresh_and_isolated": True,
        "editorial_worker_only_when_article_warranted": True,
        "tasks": tasks,
        "routine_task_count": len(tasks),
        "publication_minimum": 0,
        "automatic_scale_up": False,
        "material_event_creates_extra_task": False,
        "manual_go_is_explicit_exception": True,
        "prompt": DESKTOP_TASK_PROMPT,
    }


def _logical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def prepared_candidate_continuity_binding(
    *,
    continuity: Mapping[str, Any],
    evaluated_headline_ids: Sequence[str],
    reentry_headline_ids: Sequence[str],
) -> dict[str, Any]:
    """Build the shared durable-continuity binding for canonical frontier preparation."""
    evaluated = sorted(str(value) for value in evaluated_headline_ids if str(value))
    reentry = sorted(str(value) for value in reentry_headline_ids if str(value))
    return {
        "terminal_window_id": continuity.get("terminal_window_id"),
        "last_terminal_cutoff_utc": continuity.get("last_terminal_cutoff_utc"),
        "evaluated_headline_count": len(evaluated),
        "evaluated_headline_ids_hash": _logical_hash(evaluated),
        "material_reentry_headline_count": len(reentry),
        "material_reentry_headline_ids_hash": _logical_hash(reentry),
        "continuity_logical_hash": continuity.get("continuity_logical_hash"),
    }


from live_contentops.execution_framework_v1 import (
    DEFAULT_EXECUTION_FRAMEWORK,
    FRAMEWORK_MAIN_CODEX,
    FRAMEWORK_SUB_ANTIGRAVITY,
    validate_execution_framework,
)


def build_editorial_worker_routing_packet(
    *,
    opportunity_state: str,
    governed_context: Mapping[str, Any] | None = None,
    readiness_checked_before_editorial: bool = False,
    readiness_state: str = "UNKNOWN",
    article_mode: str = "STANDARD_ANALYSIS",
    execution_framework: str = DEFAULT_EXECUTION_FRAMEWORK,
) -> dict[str, Any]:
    """Return a deterministic routing decision without spawning or calling a model.

    In MAIN_CODEX, the native HIGH coordinator consumes this contract and spawns a fresh
    isolated XHIGH editorial worker. In SUB_ANTIGRAVITY, the single active Antigravity conversation
    performs all task reasoning and authors the article directly.
    """
    framework_info = validate_execution_framework(execution_framework)
    active_framework = str(framework_info["framework"])
    is_main = bool(framework_info["is_main"])
    coordinator_model = str(framework_info["coordinator_model"])
    coordinator_effort = str(framework_info["coordinator_reasoning_effort"])
    worker_model = str(framework_info["editorial_worker_model"])
    worker_effort = str(framework_info["editorial_worker_reasoning_effort"])

    state = str(opportunity_state or "").strip().upper()
    current_readiness = str(readiness_state or "UNKNOWN").strip().upper()
    if state == "ARTICLE_QUALIFIED" and readiness_checked_before_editorial and current_readiness != "READY":
        state = "FULL_DISTRIBUTION_READINESS_BLOCKED"
    if state not in NO_EDITORIAL_WORKER_PATHS and state != "ARTICLE_QUALIFIED":
        raise ValueError("desktop_editorial_opportunity_state_unknown")

    base = {
        "schema_version": "contentops.desktop_editorial_worker_routing.v1",
        "execution_framework": active_framework,
        "coordinator": {
            "model": coordinator_model,
            "reasoning_effort": coordinator_effort,
            "owns_deterministic_validation_after_return": True,
            "owns_publication_coordination": True,
        },
        "opportunity_state": state,
        "readiness_checked_before_editorial": bool(readiness_checked_before_editorial),
        "readiness_state": current_readiness,
        "desktop_bridge_created": False,
        "scheduler_or_queue_created": False,
        "public_write_performed": False,
    }
    if state in NO_EDITORIAL_WORKER_PATHS:
        result = {
            **base,
            "decision": "HIGH_ONLY_NO_EDITORIAL_WORKER" if is_main else "COORDINATOR_ONLY_NO_EDITORIAL_WORKER",
            "xhigh_worker_count_requested": 0,
            "editorial_worker_count_requested": 0,
            "worker_request": None,
            "governed_input_hash": None,
        }
        result["routing_logical_hash"] = _logical_hash(result)
        return result

    if not isinstance(governed_context, Mapping):
        raise ValueError("desktop_editorial_governed_context_required")
    extra_keys = sorted(set(governed_context).difference(BOUNDED_EDITORIAL_CONTEXT_KEYS))
    if extra_keys:
        raise ValueError("desktop_editorial_context_unbounded_keys:" + ",".join(extra_keys))
    bounded_context = {
        key: governed_context[key]
        for key in sorted(BOUNDED_EDITORIAL_CONTEXT_KEYS)
        if key in governed_context
    }
    if not bounded_context.get("accepted_evidence_packet"):
        raise ValueError("desktop_editorial_accepted_evidence_packet_required")
    if not bounded_context.get("exact_source_handles"):
        raise ValueError("desktop_editorial_exact_source_handles_required")
    from live_contentops.capital_chronicle_institutional_edge_v1 import (
        build_institutional_edge_editorial_packet,
        validate_institutional_edge_packet,
    )

    supplied_editorial_packet = bounded_context.get("institutional_edge_editorial_packet")
    editorial_packet = build_institutional_edge_editorial_packet(
        article_mode=article_mode,
        accepted_evidence_packet=bounded_context.get("accepted_evidence_packet"),
        structured_data_supported=True,
    )
    if supplied_editorial_packet is not None and supplied_editorial_packet != editorial_packet:
        raise ValueError("desktop_editorial_authority_packet_override_forbidden")
    packet_blockers = validate_institutional_edge_packet(editorial_packet)
    if packet_blockers:
        raise ValueError("desktop_editorial_authority_packet_invalid:" + ",".join(packet_blockers))
    bounded_context["institutional_edge_editorial_packet"] = editorial_packet
    governed_input_hash = _logical_hash(bounded_context)

    decision = (
        "SPAWN_ONE_FRESH_ISOLATED_XHIGH_EDITORIAL_WORKER"
        if is_main
        else "EXECUTE_IN_ACTIVE_ANTIGRAVITY_CONVERSATION"
    )
    worker_request = {
        "execution_framework": active_framework,
        "model": worker_model,
        "reasoning_effort": worker_effort,
        "fresh": is_main,
        "isolated": is_main,
        "logical_role_isolated": True,
        "resume_existing": False,
        "governed_input_hash": governed_input_hash,
        "bounded_governed_context": bounded_context,
        "max_bounded_editorial_revisions": MAX_EDITORIAL_REVISIONS,
        "grants_factual_authority": False,
        "grants_numeric_authority": False,
        "grants_capital_chronicle_authority": False,
        "grants_permission_authority": False,
        "grants_public_write_authority": False,
    }
    result = {
        **base,
        "decision": decision,
        "xhigh_worker_count_requested": 1 if is_main else 0,
        "editorial_worker_count_requested": 1,
        "governed_input_hash": governed_input_hash,
        "worker_request": worker_request,
    }
    result["routing_logical_hash"] = _logical_hash(result)
    return result


def validate_editorial_worker_return(
    *,
    worker_return: Mapping[str, Any],
    expected_governed_input_hash: str,
    expected_editorial_packet: Mapping[str, Any] | None = None,
    accepted_evidence_packet: Mapping[str, Any] | None = None,
    execution_framework: str = DEFAULT_EXECUTION_FRAMEWORK,
) -> dict[str, Any]:
    """Bind one editorial result to its exact input and return control to the coordinator."""
    if str(worker_return.get("governed_input_hash") or "") != expected_governed_input_hash:
        raise ValueError("desktop_editorial_worker_input_hash_mismatch")

    framework_info = validate_execution_framework(execution_framework)
    active_framework = str(framework_info["framework"])
    is_main = bool(framework_info["is_main"])

    return_framework = str(
        worker_return.get("execution_framework") or (FRAMEWORK_MAIN_CODEX if is_main else "")
    ).strip().upper()

    if is_main:
        if return_framework != FRAMEWORK_MAIN_CODEX:
            raise ValueError("desktop_editorial_worker_framework_invalid")
        if str(worker_return.get("model") or "") != EDITORIAL_WORKER_MODEL:
            raise ValueError("desktop_editorial_worker_model_invalid")
        if str(worker_return.get("reasoning_effort") or "").upper() != EDITORIAL_WORKER_REASONING_EFFORT:
            raise ValueError("desktop_editorial_worker_reasoning_effort_invalid")
        if worker_return.get("fresh") is not True or worker_return.get("isolated") is not True:
            raise ValueError("desktop_editorial_worker_fresh_isolated_receipt_required")
    else:
        if return_framework != FRAMEWORK_SUB_ANTIGRAVITY:
            raise ValueError("sub_editorial_worker_framework_invalid")

    revision_count = int(worker_return.get("bounded_revision_count") or 0)
    if revision_count < 0 or revision_count > MAX_EDITORIAL_REVISIONS:
        raise ValueError("desktop_editorial_worker_revision_limit_exceeded")
    if bool(worker_return.get("public_write_attempted")):
        raise ValueError("desktop_editorial_worker_public_write_forbidden")
    article = worker_return.get("article")
    if not isinstance(article, Mapping) or not str(article.get("title") or "").strip():
        raise ValueError("desktop_editorial_worker_article_invalid")
    editorial_validation: dict[str, Any] | None = None
    if expected_editorial_packet is not None:
        from live_contentops.capital_chronicle_institutional_edge_v1 import (
            validate_institutional_edge_article,
        )

        editorial_validation = validate_institutional_edge_article(
            article,
            editorial_packet=expected_editorial_packet,
            accepted_evidence_packet=accepted_evidence_packet,
        )
        if editorial_validation.get("classification") != "PASS":
            raise ValueError(
                "desktop_editorial_worker_institutional_edge_invalid:"
                + ",".join(editorial_validation.get("blockers") or [])
            )
    return_hash = _logical_hash(worker_return)
    classification = (
        "PASS_BOUND_XHIGH_EDITORIAL_RETURN"
        if is_main
        else "PASS_BOUND_SUB_ANTIGRAVITY_EDITORIAL_RETURN"
    )
    return {
        "schema_version": "contentops.desktop_editorial_worker_return_validation.v1",
        "classification": classification,
        "execution_framework": active_framework,
        "governed_input_hash": expected_governed_input_hash,
        "worker_return_hash": return_hash,
        "worker_model": framework_info["editorial_worker_model"],
        "worker_reasoning_effort": framework_info["editorial_worker_reasoning_effort"],
        "worker_fresh_and_isolated": is_main,
        "bounded_revision_count": revision_count,
        "xhigh_publication_authority": False,
        "sub_framework_publication_authority": False,
        "coordinator_resumes": True,
        "coordinator_model": framework_info["coordinator_model"],
        "coordinator_reasoning_effort": framework_info["coordinator_reasoning_effort"],
        "deterministic_validation_required": True,
        "institutional_edge_editorial_validation": editorial_validation,
        "publication_coordinator_remains_sole_public_writer": True,
        "public_write_performed": False,
    }


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError, TypeError):
        return None
    return dict(value) if isinstance(value, Mapping) else None


def _parse_utc(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso_utc(value: datetime) -> str:
    moment = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
    return moment.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


@contextmanager
def _read_only_store(path: Path) -> Iterator[sqlite3.Connection]:
    resolved = path.resolve()
    connection = sqlite3.connect(
        f"file:{resolved.as_posix()}?mode=ro",
        uri=True,
        isolation_level=None,
        cached_statements=0,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    try:
        yield connection
    finally:
        connection.close()


def _table_names(connection: sqlite3.Connection) -> set[str]:
    return {
        str(row["name"])
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }


def _canonical_public_substack_url(value: Any) -> bool:
    try:
        parsed = urlsplit(str(value or ""))
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and (parsed.hostname or "").casefold() == CANONICAL_SUBSTACK_HOST
        and parsed.path.startswith("/p/")
        and len(parsed.path) > 3
    )


def _published_memory_from_store(connection: sqlite3.Connection) -> dict[str, Any]:
    required = {
        "work_items", "outbox_messages", "platform_dispatches", "reconciliations"
    }
    if not required.issubset(_table_names(connection)):
        return {
            "confirmed_canonical_count": 0,
            "story_identities": [],
            "update_chain_identities": [],
            "state": "REQUIRED_TABLES_UNAVAILABLE",
        }
    rows = connection.execute(
        "SELECT w.story_id,o.payload,d.public_object_url,r.status AS reconciliation_status "
        "FROM work_items w JOIN outbox_messages o ON o.work_item_id=w.work_item_id "
        "JOIN platform_dispatches d ON d.message_id=o.message_id "
        "JOIN reconciliations r ON r.work_item_id=w.work_item_id "
        "WHERE o.destination='substack' AND d.platform='substack' "
        "AND r.status='RECONCILED_CONFIRMED'"
    ).fetchall()
    story_ids: set[str] = set()
    chain_ids: set[str] = set()
    object_urls: set[str] = set()
    for row in rows:
        public_url = str(row["public_object_url"] or "")
        if not _canonical_public_substack_url(public_url):
            continue
        object_urls.add(public_url)
        payload: Mapping[str, Any] = {}
        try:
            parsed_payload = json.loads(str(row["payload"] or "{}"))
            if isinstance(parsed_payload, Mapping):
                payload = parsed_payload
        except (TypeError, ValueError):
            pass
        story_identity = str(payload.get("story_identity") or "").strip()
        update_chain_identity = str(payload.get("update_chain_identity") or "").strip()
        if story_identity:
            story_ids.add(story_identity)
        if update_chain_identity:
            chain_ids.add(update_chain_identity)
    return {
        "confirmed_canonical_count": len(object_urls),
        "story_identities": sorted(story_ids),
        "update_chain_identities": sorted(chain_ids),
        "canonical_url_hashes": sorted(
            hashlib.sha256(value.encode("utf-8")).hexdigest() for value in object_urls
        ),
        "state": "READ_ONLY_DURABLE_RECONCILED_SUBSTACK_MEMORY",
    }


def _active_learning_policy_from_store(connection: sqlite3.Connection) -> dict[str, Any]:
    from live_contentops.daily_app_performance_v1 import (
        BOOTSTRAP_POLICY_VERSION,
        QUALIFIED_ENGAGEMENT_FORMULA_VERSION,
        _bootstrap_policy_payload,
        _normalized_policy_payload,
    )

    if "learning_policy_versions" not in _table_names(connection):
        payload = _bootstrap_policy_payload()
        return {
            "policy_version": BOOTSTRAP_POLICY_VERSION,
            "decision": "CONFIGURED_DEFAULT",
            "sample_count": 0,
            "confidence": 0.0,
            "formula_version": QUALIFIED_ENGAGEMENT_FORMULA_VERSION,
            "timing": payload["timing"],
            "content": payload["content"],
            "seo": payload["seo"],
            "package": payload["package"],
            "grants_factual_or_numeric_authority": False,
            "grants_publication_authority": False,
        }
    row = connection.execute(
        "SELECT * FROM learning_policy_versions WHERE status='ACTIVE' "
        "ORDER BY created_at_utc DESC,policy_version DESC LIMIT 1"
    ).fetchone()
    if row is None:
        payload = _bootstrap_policy_payload()
        return {
            "policy_version": BOOTSTRAP_POLICY_VERSION,
            "decision": "CONFIGURED_DEFAULT",
            "sample_count": 0,
            "confidence": 0.0,
            "formula_version": QUALIFIED_ENGAGEMENT_FORMULA_VERSION,
            "timing": payload["timing"],
            "content": payload["content"],
            "seo": payload["seo"],
            "package": payload["package"],
            "grants_factual_or_numeric_authority": False,
            "grants_publication_authority": False,
        }
    try:
        payload = _normalized_policy_payload(
            dict(json.loads(str(row["policy_payload_json"] or "{}")))
        )
    except (TypeError, ValueError):
        payload = _bootstrap_policy_payload()
    return {
        "policy_version": str(row["policy_version"]),
        "parent_policy_version": row["parent_policy_version"],
        "decision": str(row["decision"]),
        "decision_reason": str(row["decision_reason"]),
        "sample_count": int(row["sample_count"]),
        "confidence": float(row["confidence"]),
        "formula_version": str(row["formula_version"]),
        "timing": dict(payload.get("timing") or {}),
        "content": dict(payload.get("content") or {}),
        "seo": dict(payload.get("seo") or {}),
        "package": dict(payload.get("package") or {}),
        "grants_factual_or_numeric_authority": False,
        "grants_publication_authority": False,
    }


def load_terminal_editorial_continuity(
    *,
    store_path: str | Path = CANONICAL_PRODUCTION_STORE_PATH,
    output_root: str | Path = CANONICAL_PRODUCTION_OUTPUT_ROOT,
) -> dict[str, Any]:
    """Reconstruct cutoff/evaluated/publication memory without modifying the canonical store."""
    store = Path(store_path)
    outputs = Path(output_root)
    base: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "store_path": str(store.resolve()),
        "output_root": str(outputs.resolve()),
        "store_open_mode": "SQLITE_URI_MODE_RO_QUERY_ONLY",
        "database_writes_performed": False,
        "filesystem_writes_performed": False,
        "parallel_state_authority_created": False,
    }
    if not store.is_file():
        from live_contentops.daily_app_performance_v1 import (
            BOOTSTRAP_POLICY_VERSION,
            _bootstrap_policy_payload,
        )
        bootstrap_payload = _bootstrap_policy_payload()
        result = {
            **base,
            "state": "CANONICAL_STORE_MISSING",
            "last_terminal_cutoff_utc": None,
            "terminal_window_id": None,
            "terminal_records": [],
            "evaluated_headline_ids": [],
            "evaluated_update_chain_identities": [],
            "published_memory": {
                "confirmed_canonical_count": 0,
                "story_identities": [],
                "update_chain_identities": [],
                "state": "CANONICAL_STORE_MISSING",
            },
            "active_learning_policy": {
                "policy_version": BOOTSTRAP_POLICY_VERSION,
                "decision": "CONFIGURED_DEFAULT",
                "sample_count": 0,
                "confidence": 0.0,
                "timing": bootstrap_payload["timing"],
                "content": bootstrap_payload["content"],
                "seo": bootstrap_payload["seo"],
                "package": bootstrap_payload["package"],
                "grants_factual_or_numeric_authority": False,
                "grants_publication_authority": False,
            },
            "prior_cc_catalog_fingerprint": None,
            "material_event_priority": {
                "priority_ids": [], "headline_ids": [], "update_chain_identities": [],
                "priority_count": 0, "grants_evidence_or_publication_authority": False,
            },
        }
        result["continuity_logical_hash"] = _logical_hash(result)
        return result

    with _read_only_store(store) as connection:
        tables = _table_names(connection)
        if "work_items" not in tables:
            raise ValueError("desktop_continuity_work_items_table_missing")
        placeholders = ",".join("?" for _ in TERMINAL_EDITORIAL_STATES)
        rows = connection.execute(
            "SELECT work_item_id,current_state,updated_at FROM work_items "
            "WHERE target_surface IN "
            "('daily_app_editorial_window','daily_app_material_event_window') "
            f"AND current_state IN ({placeholders}) "
            "ORDER BY updated_at DESC,work_item_id DESC",
            tuple(sorted(TERMINAL_EDITORIAL_STATES)),
        ).fetchall()
        published_memory = _published_memory_from_store(connection)
        active_learning_policy = _active_learning_policy_from_store(connection)
        pending_material_rows = connection.execute(
            "SELECT work_item_id FROM work_items "
            "WHERE target_surface='daily_app_material_event_window' "
            "AND current_state='DISCOVERED' ORDER BY work_item_id"
        ).fetchall()

    material_priorities: list[dict[str, Any]] = []
    for pending in pending_material_rows:
        priority = _read_json_object(
            outputs / str(pending["work_item_id"]) / "material_event_priority_v1.json"
        )
        if priority:
            material_priorities.append(priority)
    material_event_priority = {
        "priority_ids": sorted({str(row.get("priority_id") or "") for row in material_priorities if str(row.get("priority_id") or "")}),
        "headline_ids": sorted({str(value) for row in material_priorities for value in (row.get("headline_ids") or []) if str(value)}),
        "update_chain_identities": sorted({str(value) for row in material_priorities for value in (row.get("update_chain_identities") or []) if str(value)}),
        "priority_count": len(material_priorities),
        "grants_evidence_or_publication_authority": False,
    }

    evaluated_ids: set[str] = set()
    evaluated_chains: set[str] = set()
    terminal_records: list[dict[str, Any]] = []
    published_story_ids = set(published_memory.get("story_identities") or [])
    published_chain_ids = set(published_memory.get("update_chain_identities") or [])
    for row in rows:
        window_id = str(row["work_item_id"])
        output_dir = outputs / window_id
        intake = _read_json_object(output_dir / "rolling_x_intake_v1.json")
        evidence = _read_json_object(
            output_dir / "rolling_x_newsroom_cycle_evidence_v1.json"
        )
        if not intake or not evidence:
            continue
        cutoff = _parse_utc(intake.get("cutoff_time_utc"))
        if cutoff is None:
            continue
        assignment = _read_json_object(output_dir / "rolling_x_assignment_v1.json") or {}
        prepared = _read_json_object(
            output_dir / "rolling_x_prepared_candidate_state_v1.json"
        ) or {}
        clusters_by_id = {
            str(cluster.get("cluster_id") or ""): dict(cluster)
            for cluster in assignment.get("ranked_clusters") or []
            if isinstance(cluster, Mapping) and str(cluster.get("cluster_id") or "")
        }
        attempted_cluster_ids = {
            str(attempt.get("cluster_id") or "")
            for attempt in (
                *((evidence.get("candidate_walk") or {}).get("candidate_attempts") or []),
                *((evidence.get("ranked_viability") or {}).get("rank_attempts") or []),
            )
            if isinstance(attempt, Mapping) and str(attempt.get("cluster_id") or "")
        }
        if attempted_cluster_ids:
            evaluated_clusters = [
                clusters_by_id[cluster_id]
                for cluster_id in sorted(attempted_cluster_ids)
                if cluster_id in clusters_by_id
            ]
            headline_ids = {
                str(value)
                for cluster in evaluated_clusters
                for value in cluster.get("headline_ids") or []
                if str(value)
            }
            evaluated_identity_source = "CANDIDATE_WALK_ATTEMPTS"
        elif prepared:
            headline_ids = {
                str(value)
                for value in (
                    (prepared.get("prepared_frontier") or {}).get(
                        "selected_headline_ids"
                    )
                    or (prepared.get("prepared_input") or {}).get(
                        "unique_headline_ids"
                    )
                    or []
                )
                if str(value)
            }
            evaluated_clusters = [
                cluster for cluster in clusters_by_id.values()
                if set(str(value) for value in cluster.get("headline_ids") or []).intersection(
                    headline_ids
                )
            ]
            evaluated_identity_source = "PREPARED_FRONTIER"
        else:
            # Legacy cycles may lack candidate-walk telemetry. The ranked assignment is the
            # narrowest durable proof of consideration; the full intake universe is not.
            evaluated_clusters = list(clusters_by_id.values())
            headline_ids = {
                str(value)
                for cluster in evaluated_clusters
                for value in cluster.get("headline_ids") or []
                if str(value)
            }
            evaluated_identity_source = "LEGACY_RANKED_ASSIGNMENT"
        evaluated_ids.update(headline_ids)
        for cluster in evaluated_clusters:
            if not isinstance(cluster, Mapping):
                continue
            chain = str(
                cluster.get("update_chain_identity") or cluster.get("cluster_id") or ""
            ).strip()
            if chain:
                evaluated_chains.add(chain)
        memory_proof = _read_json_object(
            output_dir / "published_memory_cycle_proof_v1.json"
        ) or {}
        observed = memory_proof.get("canonical_article_observed_after_lifecycle") or {}
        if isinstance(observed, Mapping):
            story_identity = str(observed.get("story_identity") or "").strip()
            update_chain_identity = str(
                observed.get("update_chain_identity") or ""
            ).strip()
            if story_identity:
                published_story_ids.add(story_identity)
            if update_chain_identity:
                published_chain_ids.add(update_chain_identity)
        portfolio = _read_json_object(output_dir / "editorial_portfolio_context_v1.json") or {}
        cc_model = portfolio.get("capital_chronicle_read_model") or {}
        terminal_records.append({
            "window_id": window_id,
            "terminal_state": str(row["current_state"]),
            "updated_at_utc": str(row["updated_at"]),
            "cutoff_utc": _iso_utc(cutoff),
            "classification": evidence.get("classification"),
            "evaluated_headline_count": len(headline_ids),
            "evaluated_identity_source": evaluated_identity_source,
            "cc_catalog_fingerprint": cc_model.get("catalog_fingerprint")
            if isinstance(cc_model, Mapping) else None,
        })
    terminal_records.sort(
        key=lambda value: (
            _parse_utc(value.get("cutoff_utc")) or datetime.min.replace(tzinfo=timezone.utc),
            str(value.get("window_id") or ""),
        ),
        reverse=True,
    )
    latest = terminal_records[0] if terminal_records else None
    published_memory = {
        **published_memory,
        "story_identities": sorted(published_story_ids),
        "update_chain_identities": sorted(published_chain_ids),
    }
    result = {
        **base,
        "state": "READY" if latest else "NO_PRIOR_TERMINAL_EDITORIAL_WINDOW",
        "last_terminal_cutoff_utc": latest.get("cutoff_utc") if latest else None,
        "terminal_window_id": latest.get("window_id") if latest else None,
        "terminal_state": latest.get("terminal_state") if latest else None,
        "terminal_classification": latest.get("classification") if latest else None,
        "terminal_record_count": len(terminal_records),
        "terminal_records": terminal_records,
        "evaluated_headline_ids": sorted(evaluated_ids),
        "evaluated_headline_count": len(evaluated_ids),
        "evaluated_update_chain_identities": sorted(evaluated_chains),
        "published_memory": published_memory,
        "active_learning_policy": active_learning_policy,
        "prior_cc_catalog_fingerprint": latest.get("cc_catalog_fingerprint")
        if latest else None,
        "material_event_priority": material_event_priority,
    }
    result["continuity_logical_hash"] = _logical_hash(result)
    return result


def _cluster_relationship(cluster: Mapping[str, Any]) -> str:
    for container in (
        cluster.get("update_chain"),
        cluster.get("duplicate_update_chain"),
    ):
        if isinstance(container, Mapping) and container.get("relationship"):
            return str(container["relationship"]).casefold()
    return str(cluster.get("relationship") or "distinct").casefold()


def classify_desktop_candidate_universe(
    *,
    current_headlines: Sequence[Mapping[str, Any]],
    current_clusters: Sequence[Mapping[str, Any]],
    continuity: Mapping[str, Any],
) -> dict[str, Any]:
    """Include unseen identity or governed material delta; hold unchanged/published repeats."""
    rows_by_id: dict[str, dict[str, Any]] = {}
    duplicate_current_ids: set[str] = set()
    for value in current_headlines:
        headline_id = str(value.get("headline_id") or "")
        if not headline_id:
            raise ValueError("desktop_candidate_headline_id_missing")
        if headline_id in rows_by_id:
            duplicate_current_ids.add(headline_id)
            continue
        rows_by_id[headline_id] = dict(value)
    evaluated_ids = {
        str(value) for value in (continuity.get("evaluated_headline_ids") or [])
    }
    published = continuity.get("published_memory") or {}
    published_story_ids = {
        str(value) for value in (published.get("story_identities") or [])
    }
    published_chain_ids = {
        str(value) for value in (published.get("update_chain_identities") or [])
    }
    last_cutoff = _parse_utc(continuity.get("last_terminal_cutoff_utc"))
    priority = dict(continuity.get("material_event_priority") or {})
    priority_headline_ids = {str(value) for value in (priority.get("headline_ids") or [])}
    priority_update_chains = {
        str(value) for value in (priority.get("update_chain_identities") or [])
    }
    included: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    assigned_ids: set[str] = set()
    for position, value in enumerate(current_clusters, start=1):
        cluster = dict(value)
        cluster_id = str(cluster.get("cluster_id") or f"desktop-cluster-{position}")
        headline_ids = [str(item) for item in (cluster.get("headline_ids") or [])]
        if not headline_ids or any(item not in rows_by_id for item in headline_ids):
            raise ValueError("desktop_candidate_cluster_binding_invalid")
        if assigned_ids.intersection(headline_ids):
            raise ValueError("desktop_candidate_headline_assigned_twice")
        assigned_ids.update(headline_ids)
        relationship = _cluster_relationship(cluster)
        material_update = relationship in MATERIAL_RELATIONSHIPS
        unseen_ids = sorted(set(headline_ids) - evaluated_ids)
        chain_identity = str(
            cluster.get("update_chain_identity") or cluster_id
        )
        published_match = (
            cluster_id in published_story_ids or chain_identity in published_chain_ids
        )
        material_priority_match = bool(
            set(headline_ids).intersection(priority_headline_ids)
            or chain_identity in priority_update_chains
        )
        source_times = [
            _parse_utc(rows_by_id[item].get("source_timestamp_utc"))
            for item in headline_ids
        ]
        late_unseen = sorted(
            item for item in unseen_ids
            if last_cutoff is not None
            and (_parse_utc(rows_by_id[item].get("source_timestamp_utc")) or last_cutoff)
            <= last_cutoff
        )
        record = {
            "cluster_id": cluster_id,
            "update_chain_identity": chain_identity,
            "relationship": relationship,
            "headline_ids": headline_ids,
            "unseen_headline_ids": unseen_ids,
            "late_arriving_unseen_headline_ids": late_unseen,
            "published_memory_match": published_match,
            "material_event_priority_match": material_priority_match,
            "material_event_priority_ids": list(priority.get("priority_ids") or [])
            if material_priority_match else [],
            "source_timestamp_max_utc": _iso_utc(max(
                value for value in source_times if value is not None
            )) if any(value is not None for value in source_times) else None,
            "rank": int(cluster.get("rank") or position),
            "entities_topics": list(cluster.get("entities_topics") or []),
        }
        if published_match and not material_update:
            record["decision"] = "EXCLUDE_PUBLISHED_WITHOUT_MATERIAL_DELTA"
            excluded.append(record)
        elif material_update:
            record["decision"] = "INCLUDE_MATERIAL_UPDATE_CHAIN"
            included.append(record)
        elif material_priority_match:
            record["decision"] = "INCLUDE_MATERIAL_EVENT_PRIORITY"
            included.append(record)
        elif unseen_ids:
            record["decision"] = "INCLUDE_UNSEEN_HEADLINE_IDENTITY"
            included.append(record)
        else:
            record["decision"] = "EXCLUDE_UNCHANGED_PREVIOUSLY_EVALUATED"
            excluded.append(record)
    included.sort(key=lambda value: (
        0 if value.get("material_event_priority_match") else 1,
        0 if value["decision"] == "INCLUDE_MATERIAL_UPDATE_CHAIN" else 1,
        int(value["rank"]),
        str(value["cluster_id"]),
    ))
    result = {
        "schema_version": "contentops.codex_desktop_candidate_universe.v1",
        "current_unique_headline_count": len(rows_by_id),
        "current_duplicate_headline_ids": sorted(duplicate_current_ids),
        "evaluated_headline_count": len(evaluated_ids),
        "included_clusters": included,
        "excluded_clusters": excluded,
        "included_cluster_count": len(included),
        "material_update_cluster_count": sum(
            row["decision"] == "INCLUDE_MATERIAL_UPDATE_CHAIN" for row in included
        ),
        "unseen_headline_ids": sorted({
            item for row in included for item in row["unseen_headline_ids"]
        }),
        "late_arriving_unseen_headline_ids": sorted({
            item for row in included for item in row["late_arriving_unseen_headline_ids"]
        }),
        "unchanged_or_published_excluded_count": len(excluded),
        "timestamp_only_filter_used": False,
        "material_event_priority": priority,
        "material_event_priority_changes_truth_or_publication_authority": False,
        "publication_authority_granted": False,
    }
    result["candidate_universe_logical_hash"] = _logical_hash(result)
    return result


def _executed_editorial_window_ids(
    store_path: Path,
    opportunity_ids: Sequence[str],
    *,
    executed_states: frozenset[str],
) -> set[str]:
    identifiers = sorted({str(value) for value in opportunity_ids if str(value)})
    if not identifiers or not store_path.exists():
        return set()
    try:
        with _read_only_store(store_path) as connection:
            if "work_items" not in _table_names(connection):
                return set()
            placeholders = ",".join("?" for _value in identifiers)
            rows = connection.execute(
                f"SELECT work_item_id, current_state FROM work_items "
                f"WHERE work_item_id IN ({placeholders})",
                identifiers,
            ).fetchall()
    except (OSError, sqlite3.Error):
        return set()
    return {
        str(row["work_item_id"])
        for row in rows
        if str(row["current_state"] or "") in executed_states
    }


def _continuous_prepared_checkpoint(
    *,
    output_root: Path,
    checkpoint_name: str,
) -> tuple[Path, dict[str, Any] | None]:
    path = output_root / "_continuous_newsroom" / checkpoint_name
    return path, _read_json_object(path)


def _checkpoint_matches_live_authority(
    state: Mapping[str, Any],
    *,
    current_input: Mapping[str, Any],
    continuity: Mapping[str, Any],
    opportunities: Sequence[Mapping[str, Any]],
) -> bool:
    frontier = state.get("prepared_frontier") or {}
    binding = state.get("continuity_binding") or {}
    selected_ids = {
        str(value) for value in frontier.get("selected_headline_ids") or [] if str(value)
    }
    current_rows = {
        str(row.get("headline_id") or ""): {
            key: value for key, value in row.items() if key != "source_locator"
        }
        for row in current_input.get("headlines") or []
        if isinstance(row, Mapping) and str(row.get("headline_id") or "")
    }
    prepared_rows = {
        str(row.get("headline_id") or ""): {
            key: value for key, value in row.items() if key != "source_locator"
        }
        for row in (state.get("prepared_input") or {}).get("headlines") or []
        if isinstance(row, Mapping) and str(row.get("headline_id") or "")
    }
    expected_binding = prepared_candidate_continuity_binding(
        continuity=continuity,
        evaluated_headline_ids=continuity.get("evaluated_headline_ids") or [],
        reentry_headline_ids=(
            continuity.get("material_event_priority") or {}
        ).get("headline_ids") or [],
    )
    expected_target = dict(opportunities[0]) if opportunities else None
    target = frontier.get("target_editorial_opportunity")
    return bool(
        frontier.get("opportunity_schedule_derived_from_policy") is True
        and target == expected_target
        and set(prepared_rows) == selected_ids
        and all(current_rows.get(headline_id) == prepared_rows[headline_id] for headline_id in selected_ids)
        and binding == expected_binding
    )


def build_live_zero_write_rehearsal(
    *,
    cutoff_utc: datetime | str | None = None,
    store_path: str | Path = CANONICAL_PRODUCTION_STORE_PATH,
    output_root: str | Path = CANONICAL_PRODUCTION_OUTPUT_ROOT,
    sidecar_glob: str = canonical_headline_sidecar_glob(),
    cc_root: str | Path = DEFAULT_CC_ROOT,
    current_clusters: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build one real-state, bounded, read-only opportunity rehearsal; never execute a write."""
    if cutoff_utc is None:
        cutoff = datetime.now(timezone.utc)
    elif isinstance(cutoff_utc, datetime):
        cutoff = cutoff_utc
    else:
        cutoff = _parse_utc(cutoff_utc)
        if cutoff is None:
            raise ValueError("desktop_rehearsal_cutoff_invalid")
    if cutoff.tzinfo is None:
        cutoff = cutoff.replace(tzinfo=timezone.utc)
    cutoff = cutoff.astimezone(timezone.utc)
    continuity = load_terminal_editorial_continuity(
        store_path=store_path, output_root=output_root
    )
    current_input = load_rolling_x_headline_sidecars(
        cutoff_utc=cutoff,
        sidecar_glob=sidecar_glob,
        window_hours=24.0,
    )
    headlines = list(current_input.get("headlines") or [])
    if current_clusters is None:
        ordered = sorted(
            headlines,
            key=lambda row: (
                str(row.get("source_timestamp_utc") or ""),
                str(row.get("headline_id") or ""),
            ),
            reverse=True,
        )
        clusters = [
            {
                "cluster_id": "desktop-unclustered-" + str(row["headline_id"]),
                "rank": index,
                "headline_ids": [str(row["headline_id"])],
                "relationship": "distinct",
                "entities_topics": [],
            }
            for index, row in enumerate(ordered, start=1)
        ]
    else:
        clusters = [dict(value) for value in current_clusters]
    universe = classify_desktop_candidate_universe(
        current_headlines=headlines,
        current_clusters=clusters,
        continuity=continuity,
    )
    material_reentry_ids = sorted({
        str(headline_id)
        for row in universe.get("included_clusters") or []
        if str(row.get("relationship") or "").casefold() in MATERIAL_RELATIONSHIPS
        for headline_id in row.get("headline_ids") or []
        if str(headline_id)
    })
    excluded_ids = {
        str(headline_id)
        for row in universe.get("excluded_clusters") or []
        for headline_id in row.get("headline_ids") or []
        if str(headline_id)
    }
    continuity_evaluated_ids = {
        str(value) for value in continuity.get("evaluated_headline_ids") or [] if str(value)
    }
    from live_contentops.daily_app_supervisor_v1 import (
        PREPARED_CANDIDATE_CHECKPOINT_NAME,
        WINDOW_EXECUTED_STATES,
        build_bootstrap_editorial_window_policy,
        owner_locked_editorial_opportunities,
    )

    evaluated_ids = sorted(continuity_evaluated_ids.union(excluded_ids))
    priority_reentry_ids = {
        str(value)
        for value in (continuity.get("material_event_priority") or {}).get("headline_ids") or []
        if str(value)
    }
    reentry_ids = sorted(set(material_reentry_ids).union(priority_reentry_ids))
    policy = build_bootstrap_editorial_window_policy(
        effective_at_utc=_iso_utc(cutoff)
    )
    opportunities = owner_locked_editorial_opportunities(
        policy,
        reference_utc=cutoff,
        through_utc=cutoff + timedelta(
            hours=float(current_input.get("window_hours") or 24.0)
        ),
        capacity=PREPARED_CANDIDATE_LIMIT,
    )
    executed_ids = _executed_editorial_window_ids(
        Path(store_path),
        [str(row.get("opportunity_id") or "") for row in opportunities],
        executed_states=WINDOW_EXECUTED_STATES,
    )
    opportunities = [
        row for row in opportunities
        if str(row.get("opportunity_id") or "") not in executed_ids
    ]
    checkpoint_path, prior_prepared_state = _continuous_prepared_checkpoint(
        output_root=Path(output_root),
        checkpoint_name=PREPARED_CANDIDATE_CHECKPOINT_NAME,
    )
    prepared_preview: dict[str, Any] | None = None
    prepared_state_source = "REBUILT_FROM_CANONICAL_FRONTIER_INPUTS"
    if prior_prepared_state is not None:
        try:
            validated = validate_prepared_rolling_x_candidate_state(
                prior_prepared_state,
                publication_cutoff_utc=cutoff,
            )
            if _checkpoint_matches_live_authority(
                validated,
                current_input=current_input,
                continuity=continuity,
                opportunities=opportunities,
            ):
                prepared_preview = validated
                prepared_state_source = "REUSED_VALID_CONTINUOUS_CHECKPOINT"
        except (TypeError, ValueError):
            prepared_preview = None
    if prepared_preview is None:
        prepared_preview = build_prepared_rolling_x_candidate_state(
            rolling_input=current_input,
            prepared_at_utc=cutoff,
            evaluated_headline_ids=evaluated_ids,
            reentry_headline_ids=reentry_ids,
            editorial_opportunities=opportunities,
            prior_prepared_state=prior_prepared_state,
            continuity_binding=prepared_candidate_continuity_binding(
                continuity=continuity,
                evaluated_headline_ids=evaluated_ids,
                reentry_headline_ids=reentry_ids,
            ),
        )
    catalog = discover_cc_data_estate(cc_root=cc_root, use_cache=False)
    governed = inspect_governed_cc_surfaces(catalog)
    selected_frontier_ids = {
        str(value)
        for value in (prepared_preview.get("prepared_frontier") or {}).get(
            "selected_headline_ids"
        ) or []
        if str(value)
    }
    selected_assignment = next(
        iter((prepared_preview.get("assignment") or {}).get("ranked_clusters") or []),
        None,
    )
    selected_headline_ids = [
        str(value)
        for value in (selected_assignment or {}).get("headline_ids") or []
        if str(value) in selected_frontier_ids
    ]
    selected = (
        {
            "cluster_id": (selected_assignment or {}).get("cluster_id"),
            "headline_ids": selected_headline_ids,
            "relationship": "prepared_frontier",
        }
        if selected_assignment and selected_headline_ids
        else None
    )
    raw_selected = next(
        (
            row for row in universe.get("included_clusters") or []
            if selected_headline_ids
            and selected_headline_ids[0] in {
                str(value) for value in row.get("headline_ids") or []
            }
        ),
        None,
    )
    entities: list[str] = []
    if selected:
        entities = [str(value) for value in (raw_selected or {}).get("entities_topics") or []]
        if not entities:
            selected_id = next(iter(selected.get("headline_ids") or []), None)
            selected_row = next(
                (row for row in headlines if row.get("headline_id") == selected_id), {}
            )
            headline_text = str(
                (selected_row.get("external_content") or {}).get("headline_text") or ""
            ).strip()
            if headline_text:
                entities = [headline_text]
    cc_context = query_story_scoped_cc_context(catalog, entities) if entities else {
        "schema_version": "contentops.story_scoped_cc_context.v2",
        "queried_entities": [],
        "matches": [],
        "catalog_fingerprint": catalog.get("catalog_fingerprint"),
        "grants_factual_or_numeric_authority": False,
        "mutated_upstream": False,
    }
    prior_fingerprint = continuity.get("prior_cc_catalog_fingerprint")
    current_fingerprint = catalog.get("catalog_fingerprint")
    result = {
        "schema_version": REHEARSAL_SCHEMA_VERSION,
        "cutoff_utc": _iso_utc(cutoff),
        "continuity": continuity,
        "current_intake": {
            "canonical_input_hash": current_input.get("canonical_input_hash"),
            "headline_count": int((current_input.get("counts") or {}).get("accepted") or 0),
            "deduplicated_input_count": int(
                (current_input.get("counts") or {}).get("duplicates") or 0
            ),
        },
        "candidate_universe": universe,
        "prepared_candidate_state_preview": prepared_preview,
        "prepared_candidate_state_source": prepared_state_source,
        "prepared_candidate_checkpoint_path": str(checkpoint_path.resolve()),
        "prepared_checkpoint_written_by_rehearsal": False,
        "prepared_candidate_count": int(
            prepared_preview.get("prepared_candidate_count") or 0
        ),
        "deferred_candidate_count": int(
            (prepared_preview.get("prepared_frontier") or {}).get(
                "deferred_identity_count"
            )
            or 0
        ),
        "prepared_frontier_is_continuity_bound": True,
        "active_learning_policy": continuity.get("active_learning_policy"),
        "material_event_priority": continuity.get("material_event_priority"),
        "material_event_priority_consumed_by_briefing": bool(
            (continuity.get("material_event_priority") or {}).get("priority_count")
        ),
        "learning_policy_consumed_by_next_opportunity": True,
        "learning_policy_grants_factual_or_numeric_authority": False,
        "candidate_or_abstention": (
            {
                "decision": "CANDIDATE_FOR_DESKTOP_EDITORIAL_JUDGMENT",
                "cluster_id": selected.get("cluster_id"),
                "headline_ids": selected.get("headline_ids"),
                "relationship": selected.get("relationship"),
                "prepared_frontier_bound": True,
            }
            if selected else {"decision": "ABSTAIN_NO_CURRENT_UNSEEN_OR_MATERIAL_UPDATE"}
        ),
        "capital_chronicle": {
            "root": str(Path(cc_root).resolve()),
            "store_count_total": catalog.get("store_count_total"),
            "store_count_discovered": catalog.get("store_count_discovered"),
            "discovery_complete": catalog.get("discovery_complete"),
            "connection_mode": catalog.get("connection_mode"),
            "catalog_fingerprint": current_fingerprint,
            "prior_terminal_catalog_fingerprint": prior_fingerprint,
            "catalog_changed_since_prior_terminal": (
                None if not prior_fingerprint else prior_fingerprint != current_fingerprint
            ),
            "cache_state": (catalog.get("cache") or {}).get("state"),
            "governed_surfaces": governed,
            "story_scoped_context": cc_context,
            "arbitrary_database_context_grants_authority": False,
        },
        "next_terminal_cutoff_constructible": True,
        "next_terminal_cutoff_utc": _iso_utc(cutoff),
        "database_writes_performed": False,
        "filesystem_writes_performed": False,
        "provider_or_model_calls": 0,
        "model_calls": 0,
        "provider_calls": 0,
        "public_requests": 0,
        "public_writes": 0,
        "unknown_write_detected": False,
        "publication_coordinator_sole_public_writer_unchanged": True,
        "v2_mutations": 0,
    }
    result["rehearsal_logical_hash"] = _logical_hash(result)
    return result
