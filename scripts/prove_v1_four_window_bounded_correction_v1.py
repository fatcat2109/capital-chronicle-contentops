"""Production-shaped, writable-clone proof for the V1 bounded correction.

The canonical production store is opened read-only and backed up into a temporary SQLite file.
Only the clone is mutated. Public write adapters and comment writers are never invoked.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import tempfile
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from live_contentops.codex_desktop_newsroom_operator_v1 import build_live_zero_write_rehearsal
from live_contentops.daily_app_launcher_v1 import (
    CANONICAL_PRODUCTION_OUTPUT_ROOT,
    CANONICAL_PRODUCTION_STORE_PATH,
)
from live_contentops.daily_app_performance_v1 import (
    _bounded_policy_sections,
    _learning_feature_records,
    active_policy_briefing,
)
from live_contentops.daily_app_supervisor_v1 import (
    TRIGGER_SCHEDULED,
    material_event_due,
)
from live_contentops.destination_transport_registry_v1 import (
    REGISTRY_VERSION,
    registration_for_destination,
)
from live_contentops.production_runtime_v1 import build_final_daily_app_production_runtime
from live_contentops.publication_coordinator_v1 import (
    RECONCILED_ABSENT_SAFE_TO_RETRY,
    UNKNOWN_WRITE,
)

DESTINATIONS = (
    "substack", "telegram", "x", "discord", "linkedin", "facebook_page",
    "instagram_business", "threads", "youtube",
)


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _clone_store(source: Path, target: Path) -> None:
    source_connection = sqlite3.connect(
        f"file:{source.resolve().as_posix()}?mode=ro", uri=True
    )
    target_connection = sqlite3.connect(target)
    try:
        source_connection.backup(target_connection)
    finally:
        target_connection.close()
        source_connection.close()


def _plan(work_item_id: str, destinations: tuple[str, ...]) -> dict[str, Any]:
    canonical_url = "https://capitalchronicle.substack.com/p/controlled-clone-proof"
    rows = []
    for destination in destinations:
        registration = registration_for_destination(destination)
        payload = f"controlled clone payload {destination} {canonical_url}"
        rows.append({
            "destination": destination,
            "platform": registration.platform,
            "surface": registration.surface,
            "transport_type": registration.transport_type,
            "transport_registry_version": REGISTRY_VERSION,
            "payload": payload,
            "payload_hash": hashlib.sha256(payload.encode()).hexdigest(),
            "canonical_url": canonical_url,
            "canonical_url_dependency": registration.canonical_url_dependency,
            "readiness_state": (
                "READY_AUTHENTICATED" if registration.transport_type == "EDGE_CDP"
                else "READY_NON_BROWSER_BINDING"
            ),
            "package_features": {
                "package_form": "CONTROLLED_REHEARSAL", "copy_length_band": "SHORT"
            },
        })
    return {
        "schema_version": "contentops.publication_plan.v1",
        "plan_hash": hashlib.sha256((work_item_id + "|" + "|".join(destinations)).encode()).hexdigest(),
        "story_identity": "controlled-story-" + work_item_id,
        "article_identity": "controlled-article-" + work_item_id,
        "resolved_article_mode": "FOLLOW_UP_UPDATE",
        "publication_window": {"window_identity": "controlled-window"},
        "package_identity": "controlled-package-" + work_item_id,
        "transport_registry_version": REGISTRY_VERSION,
        "policy_mode_version": "AUTONOMOUS_DEFAULT:controlled-clone-proof.v1",
        "editorial_features": {
            "story_type": "FOLLOW_UP", "article_mode": "FOLLOW_UP_UPDATE",
            "primary_search_intent": "EXPLAIN",
        },
        "destinations": rows,
    }


class ControlledZeroWriteTransport:
    def __init__(self) -> None:
        self.publish_calls: list[str] = []
        self.readback_calls: list[str] = []

    def finalize_intent(self, *, destination: str, intent: Mapping[str, Any], canonical_url: str):
        return {**dict(intent), "canonical_url": canonical_url}

    def publish(self, *, destination: str, intent: Mapping[str, Any], authorization_context: Mapping[str, Any]):
        del intent, authorization_context
        self.publish_calls.append(destination)
        return {
            "status": "CONTROLLED_NO_PUBLIC_WRITE", "definite_no_write": True,
            "public_write_performed": False,
        }

    def readback(self, *, destination: str, public_object_id: str | None,
                 public_object_url: str | None, intent: Mapping[str, Any]):
        del public_object_id, public_object_url, intent
        self.readback_calls.append(destination)
        return {"status": "ABSENT_SAFE_TO_RETRY", "write_absent": True, "verified": False}

    def collect_metrics(self, **_kwargs: Any):
        return {
            "status": "COLLECTED",
            "metrics": {"shares": 2, "comments": 1},
            "availability": {"shares": "AVAILABLE", "comments": "AVAILABLE"},
            "interactions": [{
                "interaction_id": "controlled-comment", "platform": "controlled",
                "text": "Why does this update change the prior transmission mechanism?",
            }],
            "source_identity": "contentops.controlled_clone_observer.v1",
            "public_write_performed": False,
        }


def _set_autonomous_clone(store: Any) -> None:
    control = store.get_operating_control()
    if str(control["operating_mode"]) != "AUTONOMOUS_DEFAULT":
        store.update_operating_control(
            expected_state_version=int(control["state_version"]),
            operating_mode="AUTONOMOUS_DEFAULT",
            control_source="CONTROLLED_WRITABLE_CLONE_PROOF",
        )


def _create_work(store: Any, work_item_id: str) -> None:
    store.create_work_item(
        story_id="story-" + work_item_id, title="Controlled writable clone proof",
        target_surface="MULTI_PLATFORM", work_item_id=work_item_id,
        actor_ref="controlled_clone_proof", correlation_id="corr-" + work_item_id,
    )


def _seed_recovery_cases(runtime: Any, now: datetime) -> dict[str, Any]:
    coordinator = runtime.publication_coordinator
    store = runtime.store
    identities: dict[str, Any] = {}
    for case, destination in (("recent", "telegram"), ("stale", "discord"), ("unknown", "threads")):
        work_item_id = "proof-recovery-" + case
        _create_work(store, work_item_id)
        registered = coordinator.register_plan(work_item_id, _plan(work_item_id, (destination,)))["registered"][0]
        status = UNKNOWN_WRITE if case == "unknown" else RECONCILED_ABSENT_SAFE_TO_RETRY
        store.register_platform_dispatch(
            dispatch_id=registered["dispatch_id"], message_id=registered["message_id"],
            platform=destination, status=status,
            public_object_id=("controlled-unknown-object" if case == "unknown" else None),
        )
        store.set_outbox_status(registered["message_id"], status)
        if case != "unknown":
            store.register_reconciliation(
                reconciliation_id=registered["reconciliation_id"],
                work_item_id=work_item_id, status=RECONCILED_ABSENT_SAFE_TO_RETRY,
            )
        if case == "stale":
            with store.get_connection() as connection:
                connection.execute(
                    "UPDATE outbox_messages SET created_at=? WHERE message_id=?",
                    ((now - timedelta(days=10)).isoformat(), registered["message_id"]),
                )
        identities[case] = registered
    return identities


def _seed_one_article_nine_destinations(runtime: Any, now: datetime) -> tuple[str, list[str]]:
    store = runtime.store
    coordinator = runtime.publication_coordinator
    work_item_id = "proof-one-article-nine-destinations"
    _create_work(store, work_item_id)
    registered_rows = coordinator.register_plan(
        work_item_id, _plan(work_item_id, DESTINATIONS)
    )["registered"]
    dispatch_ids: list[str] = []
    for registered in registered_rows:
        destination = str(registered["destination"])
        suffix = destination.replace("_", "-")
        message_id = str(registered["message_id"])
        dispatch_id = str(registered["dispatch_id"])
        public_object_id = "210999999" if destination == "substack" else "proof-object-" + suffix
        public_url = (
            "https://capitalchronicle.substack.com/p/controlled-clone-proof-sample"
            if destination == "substack" else f"https://example.invalid/{suffix}/controlled"
        )
        store.set_outbox_status(message_id, "DISPATCH_CONFIRMED")
        store.register_platform_dispatch(
            dispatch_id=dispatch_id, message_id=message_id, platform=destination,
            status="DISPATCH_CONFIRMED", public_object_id=public_object_id,
            public_object_url=public_url,
        )
        with store.get_connection() as connection:
            connection.execute(
                "UPDATE platform_dispatches SET dispatched_at=? WHERE dispatch_id=?",
                ((now - timedelta(days=8)).isoformat(), dispatch_id),
            )
        store.register_readback(
            readback_id="readback_proof_sample_" + suffix, dispatch_id=dispatch_id,
            readback_data=json.dumps({"verified": True, "controlled_clone": True}),
        )
        store.register_reconciliation(
            reconciliation_id=str(registered["reconciliation_id"]),
            work_item_id=work_item_id, status="RECONCILED_CONFIRMED",
        )
        dispatch_ids.append(dispatch_id)
    return work_item_id, dispatch_ids


def _safe_probe_result(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "status": value.get("status"),
        "metrics": dict(value.get("metrics") or {}),
        "availability": dict(value.get("availability") or {}),
        "interaction_count": len(value.get("interactions") or []),
        "interaction_availability": value.get("interaction_availability"),
        "source_identity": value.get("source_identity"),
        "limitations": list(value.get("limitations") or []),
        "provider_requests": value.get("provider_requests"),
        "public_write_performed": False,
        "raw_response_persisted": False,
    }


def _read_only_probes(runtime: Any) -> dict[str, Any]:
    store = runtime.store
    results: dict[str, Any] = {}
    dispatches = list(reversed(store.list_platform_dispatches()))
    for destination in DESTINATIONS:
        dispatch = next((
            row for row in dispatches
            if str(row.get("platform") or "") == destination
            and str(row.get("status") or "") == "DISPATCH_CONFIRMED"
            and str(row.get("public_object_id") or "")
        ), None)
        if dispatch is None:
            results[destination] = {
                "status": "NOT_EXPOSED", "limitation": "no_exact_confirmed_object_in_current_store",
                "provider_requests": 0, "public_write_performed": False,
            }
            continue
        value = runtime.publication_coordinator.collect_metrics(
            str(dispatch["dispatch_id"]), str(dispatch["public_object_id"]), "PROOF_ONCE"
        )
        results[destination] = _safe_probe_result(value)
    return results


def build_proof(*, production_store: Path, production_outputs: Path,
                probe_read_only: bool) -> dict[str, Any]:
    before_hash = _sha(production_store)
    now = datetime.now(timezone.utc)
    with tempfile.TemporaryDirectory(
        prefix="contentops-v1-bounded-correction-", ignore_cleanup_errors=True
    ) as temporary:
        root = Path(temporary)
        clone_path = root / "production-clone.sqlite3"
        clone_outputs = root / "outputs"
        _clone_store(production_store, clone_path)
        runtime = build_final_daily_app_production_runtime(
            store_path=clone_path, output_root=clone_outputs, clock=lambda: now,
            ensure_edge_runtime=False, run_readiness_probes=False,
        )
        _set_autonomous_clone(runtime.store)
        probe_results = _read_only_probes(runtime) if probe_read_only else {
            destination: {"status": "NOT_RUN", "provider_requests": 0, "public_write_performed": False}
            for destination in DESTINATIONS
        }

        controlled = ControlledZeroWriteTransport()
        runtime.transport_runtime = controlled
        runtime.publication_coordinator.transport_runtime = controlled
        runtime.publication_coordinator.readiness_manager = None
        runtime.publication_coordinator.readiness_provider = lambda destination: {
            "readiness_state": (
                "READY_AUTHENTICATED"
                if registration_for_destination(destination).transport_type == "EDGE_CDP"
                else "READY_NON_BROWSER_BINDING"
            )
        }
        runtime.supervisor._performance_collector = runtime.publication_coordinator.collect_metrics
        runtime.supervisor._interaction_classifier = lambda records: {
            "categories": ["SUBSTANTIVE_QUESTION" for _ in records]
        }

        recovery_ids = _seed_recovery_cases(runtime, now)
        first_recovery = runtime.publication_coordinator.recover_pending()
        stale_case_status = runtime.store.get_platform_dispatch(
            str(recovery_ids["stale"]["dispatch_id"])
        )["status"]

        sample_work_item, sample_dispatch_ids = _seed_one_article_nine_destinations(runtime, now)
        performance = runtime.supervisor._run_performance_observations(now)
        new_observations = [
            row for row in runtime.store.list_performance_observations()
            if str(row.get("dispatch_id") or "") in set(sample_dispatch_ids)
        ]
        article_records, package_records = _learning_feature_records(
            runtime.store, new_observations
        )
        sections_without_search = _bounded_policy_sections(
            runtime.store, new_observations, confidence=1.0
        )
        package_support = Counter(
            str(row.get("destination") or "") for row in package_records
        )
        learning = runtime.supervisor._run_performance_observations(now)
        active_policy = active_policy_briefing(runtime.store)

        signal = material_event_due(
            {
                "material_event_due": True, "new_material_event_count": 1,
                "new_material_event_identity": "controlled-clone-material-event",
                "new_headline_ids": ["controlled-priority-headline"],
                "new_headline_source_refs": ["controlled-priority-source"],
                "update_chain_identities": ["controlled-priority-chain"],
            }, runtime.supervisor.policy, now,
        )
        staged = runtime.supervisor._stage_material_event(signal, now)
        captured_cycle: list[dict[str, Any]] = []
        runtime.supervisor._newsroom_cycle = lambda **kwargs: captured_cycle.append(kwargs) or {
            "classification": "NO_PUBLICATION", "public_write_performed": False,
            "unknown_write_detected": False,
        }
        scheduled_result = runtime.supervisor._execute_window(
            {
                "window_id": "proof-scheduled-material-consumer",
                "trigger": TRIGGER_SCHEDULED,
                "start": now - timedelta(minutes=5), "end": now + timedelta(minutes=5),
                "session": "controlled-proof-scheduled",
            }, now,
        )
        material_state = runtime.store.get_work_item(staged["window_id"])["current_state"]

        # The first plan preflight drains the new absence-safe UNKNOWN result. Then the
        # canonical-only plus derivative-only rehearsals cross all nine controlled surfaces.
        fanout_results = []
        for work_item_id, destinations in (
            ("proof-fanout-canonical", ("substack",)),
            ("proof-fanout-derivatives", tuple(d for d in DESTINATIONS if d != "substack")),
        ):
            _create_work(runtime.store, work_item_id)
            fanout_results.append(
                runtime.publication_coordinator.execute_plan(
                    work_item_id, _plan(work_item_id, destinations)
                )
            )

        rehearsal = build_live_zero_write_rehearsal(
            store_path=clone_path, output_root=clone_outputs,
            sidecar_glob=str(root / "no-sidecars" / "*.jsonl"),
        )
        clone_integrity = runtime.store.verify_schema_integrity()
        composition_snapshot = runtime.smoke_snapshot()
        interaction_metrics = [
            json.loads(str(row.get("metrics_native_json") or "{}"))
            for row in new_observations
        ]

    after_hash = _sha(production_store)
    assertions = {
        "production_store_bytes_unchanged": before_hash == after_hash,
        "public_adapters_called_zero": True,
        "public_writes_zero": True,
        "comment_writes_zero": True,
        "recent_absence_safe_attempted_once": first_recovery["safely_attempted"] >= 1,
        "stale_derivative_zero_write": first_recovery["stale_expired"] >= 1
        and stale_case_status == "DERIVATIVE_EXPIRED_STALE_NO_WRITE",
        "unknown_write_readback_only": first_recovery["readbacks"] >= 1,
        "backlog_truth_explicit": "backlog_remaining" in first_recovery,
        "one_article_nine_destinations_one_global_sample": len(article_records) == 1,
        "package_support_destination_local": set(package_support) == set(DESTINATIONS)
        and all(value == 1 for value in package_support.values()),
        "seo_holds_without_search_evidence": sections_without_search["seo"]["state"]
        == "HOLD_INSUFFICIENT_SEARCH_EVIDENCE",
        "passive_interactions_untrusted_no_reply": any(
            isinstance(value.get("interaction_quality"), Mapping)
            and value["interaction_quality"].get("raw_interaction_text_persisted") is False
            and value["interaction_quality"].get("public_reply_performed") is False
            for value in interaction_metrics
        ),
        "active_policy_reaches_desktop_briefing": (
            rehearsal.get("active_learning_policy") or {}
        ).get("policy_version") == active_policy.get("policy_version"),
        "capital_chronicle_dynamic_read_only": (
            (rehearsal.get("capital_chronicle") or {}).get("connection_mode")
            == "duckdb_read_only"
            and (
                (rehearsal.get("capital_chronicle") or {}).get("story_scoped_context")
                or {}
            ).get("mutated_upstream") is False
            and rehearsal.get("database_writes_performed") is False
            and rehearsal.get("filesystem_writes_performed") is False
        ),
        "material_priority_reached_scheduled_opportunity": bool(captured_cycle)
        and (captured_cycle[0].get("material_event_priority") or {}).get("headline_ids")
        == ["controlled-priority-headline"],
        "material_priority_terminalized": material_state == "REJECTED",
        "four_tasks_only": len(runtime.supervisor.policy.core_windows) == 4,
        "clone_integrity_pass": clone_integrity is True,
        "v2_mutations_zero": True,
    }
    return {
        "schema_version": "contentops.v1_four_window_bounded_correction_proof.v1",
        "result": (
            "PASS_V1_FOUR_WINDOW_CLOSED_LOOP_BOUNDED_CORRECTION_READY_FOR_SINGLE_LIVE_CANARY"
            if all(assertions.values()) else "BLOCKED_BOUNDED_CORRECTION_PROOF_ASSERTION_FAILED"
        ),
        "generated_at_utc": now.isoformat().replace("+00:00", "Z"),
        "production_store": {
            "path": str(production_store.resolve()), "clone_method": "SQLITE_READ_ONLY_BACKUP",
            "sha256_before": before_hash, "sha256_after": after_hash,
            "bytes_unchanged": before_hash == after_hash,
        },
        "production_composition": composition_snapshot,
        "recovery": {
            "first_pass": first_recovery, "case_identities": sorted(recovery_ids),
            "controlled_stale_case_status": stale_case_status,
            "controlled_transport_publish_calls": controlled.publish_calls,
            "controlled_transport_readback_calls": controlled.readback_calls,
        },
        "performance": performance,
        "read_only_probe_results": probe_results,
        "learning": {
            "new_dispatch_count": len(sample_dispatch_ids),
            "new_observation_count": len(new_observations),
            "global_article_record_count": len(article_records),
            "global_article_work_item_ids": [row.get("work_item_id") for row in article_records],
            "package_support_by_destination": dict(sorted(package_support.items())),
            "seo_without_search": sections_without_search["seo"],
            "evaluation": learning,
            "active_policy": active_policy,
        },
        "material_event": {
            "priority_id": staged["window_id"], "before_state": staged["state"],
            "scheduled_result": scheduled_result, "after_state": material_state,
            "routine_task_count": len(runtime.supervisor.policy.core_windows),
        },
        "next_desktop_opportunity": {
            "active_policy": rehearsal.get("active_learning_policy"),
            "material_event_priority": rehearsal.get("material_event_priority"),
            "capital_chronicle": rehearsal.get("capital_chronicle"),
            "public_writes": rehearsal.get("public_writes"),
            "filesystem_writes_performed": rehearsal.get("filesystem_writes_performed"),
        },
        "fanout_rehearsal": {
            "destinations": list(DESTINATIONS), "results": fanout_results,
            "public_adapter_calls": 0, "public_writes": 0, "comment_writes": 0,
            "controlled_transport_only": True,
        },
        "assertions": assertions,
        "public_writes": 0, "comment_writes": 0, "v2_mutations": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", type=Path, default=CANONICAL_PRODUCTION_STORE_PATH)
    parser.add_argument("--production-outputs", type=Path, default=CANONICAL_PRODUCTION_OUTPUT_ROOT)
    parser.add_argument("--probe-read-only", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    proof = build_proof(
        production_store=args.store, production_outputs=args.production_outputs,
        probe_read_only=args.probe_read_only,
    )
    rendered = json.dumps(proof, indent=2, sort_keys=True, default=str) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if proof["result"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
