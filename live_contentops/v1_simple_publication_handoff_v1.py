"""Restart-safe adapter from one qualified Simple slot to the existing publication coordinator.

This module creates no publisher, scheduler, transport, or durable-store authority. It binds the
persistent Simple scheduler to the existing ``DurablePublicationCoordinator`` and the canonical
``ContentOpsDurableStore``. The Simple newsroom remains a zero-write semantic producer.

The handoff is deliberately deterministic:

* the Simple slot id is the durable work-item id;
* the publication plan is persisted/reconstructed from already-qualified local artifacts without
  another model/source call;
* coordinator recovery runs before fresh work and before interrupted-slot resume;
* partial registration is completed idempotently through the existing coordinator before recovery;
* ambiguous writes are never blind-retried by this adapter.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

from live_contentops.destination_transport_registry_v1 import (
    DestinationReadinessManager,
    V1_REQUIRED_PUBLICATION_DESTINATIONS,
    registration_for_destination,
    validate_registry,
)
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.newsroom_production_day_v1 import load_qualified_article_records
from live_contentops.production_orchestrator_v1 import ContentOpsProductionOrchestrator
from live_contentops.publication_coordinator_v1 import (
    FULL_V1_NINE_SURFACE_PUBLICATION_CONFIRMED,
    CanonicalDestinationTransportRuntimeV1,
    DurablePublicationCoordinator,
)
from live_contentops.v1_simple_gemini_newsroom_v1 import (
    _build_simple_publication_lifecycle_plan,
)

SCHEMA_VERSION = "contentops.v1_simple_publication_handoff.v1"
PLAN_FILENAME = "publication_lifecycle_plan_v1.json"
RECEIPT_FILENAME = "simple_gemini_newsroom_receipt_v1.json"
QUALIFIED_FILENAME = "qualified_article_record_v1.json"
ARTICLE_FILENAME = "article_manifest_v1.json"
PREVIEWS_FILENAME = "native_derivative_previews_v1.json"


class SimplePublicationHandoffError(RuntimeError):
    """Fail-closed deterministic handoff error."""

    def __init__(self, code: str) -> None:
        self.code = str(code)
        super().__init__(self.code)


def _hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError):
        return {}
    return dict(value) if isinstance(value, Mapping) else {}


def _write_immutable_json(path: Path, value: Mapping[str, Any]) -> None:
    payload = json.dumps(dict(value), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != payload:
            raise SimplePublicationHandoffError("publication_plan_identity_conflict")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{uuid4().hex}.tmp")
    with temporary.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _validated_qualified_record(slot_output_dir: Path, slot_id: str) -> dict[str, Any]:
    raw = _read_json(slot_output_dir / QUALIFIED_FILENAME)
    day_id = str(raw.get("newsroom_production_day_id") or "")
    if not day_id:
        raise SimplePublicationHandoffError("qualified_record_missing")
    valid = load_qualified_article_records(
        slot_output_dir,
        production_day_id=day_id,
    )
    record = next(
        (
            dict(row)
            for row in valid
            if str(row.get("attempt_run_id") or "") == slot_id
            and str(row.get("parent_window_id") or "") == slot_id
        ),
        None,
    )
    if record is None:
        raise SimplePublicationHandoffError("qualified_record_not_valid_for_slot")
    return record


def _validate_plan(plan: Mapping[str, Any], *, slot_id: str, record: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(plan)
    material = {key: item for key, item in value.items() if key != "plan_hash"}
    if value.get("schema_version") != "contentops.publication_plan.v1":
        raise SimplePublicationHandoffError("publication_plan_schema_invalid")
    if str(value.get("run_id") or "") != slot_id:
        raise SimplePublicationHandoffError("publication_plan_slot_identity_mismatch")
    if str(value.get("plan_hash") or "") != _hash(material):
        raise SimplePublicationHandoffError("publication_plan_hash_invalid")
    if str(value.get("article_identity") or "") != str(record.get("article_identity") or ""):
        raise SimplePublicationHandoffError("publication_plan_article_identity_mismatch")
    if str(value.get("story_identity") or "") != str(record.get("story_identity") or ""):
        raise SimplePublicationHandoffError("publication_plan_story_identity_mismatch")
    destinations = {
        str(row.get("destination") or "")
        for row in value.get("destinations") or []
        if isinstance(row, Mapping)
    }
    if destinations != set(V1_REQUIRED_PUBLICATION_DESTINATIONS):
        raise SimplePublicationHandoffError("publication_plan_destination_contract_invalid")
    if value.get("source_provenance_binding_preserved") is not True:
        raise SimplePublicationHandoffError("publication_plan_source_binding_missing")
    if int(value.get("bridge_model_call_count") or 0) != 0:
        raise SimplePublicationHandoffError("publication_bridge_model_call_detected")
    if int(value.get("bridge_source_get_count") or 0) != 0:
        raise SimplePublicationHandoffError("publication_bridge_source_get_detected")
    return value


class SimplePublicationHandoffV1:
    """Bind qualified Simple artifacts to the existing durable publication owner."""

    def __init__(self, *, store: Any, coordinator: Any) -> None:
        self.store = store
        self.coordinator = coordinator

    def recover_preflight(self) -> dict[str, Any]:
        """Run the coordinator's canonical recovery before any fresh semantic opportunity."""
        try:
            result = dict(self.coordinator.recover_pending() or {})
        except Exception as exc:  # fail closed; never expose exception text/session material
            return {
                "schema_version": SCHEMA_VERSION,
                "backlog_remaining": 1,
                "backlog_blocking_new_publication": True,
                "safe_error_classification": type(exc).__name__,
                "publish_calls": 0,
            }
        return {
            "schema_version": SCHEMA_VERSION,
            **result,
            "backlog_blocking_new_publication": bool(
                result.get("backlog_blocking_new_publication")
                or int(result.get("backlog_remaining") or 0) > 0
            ),
        }

    def ensure_plan(
        self,
        *,
        slot_id: str,
        slot_output_dir: str | Path,
        returned_plan: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Persist or reconstruct the exact plan without semantic/model/source re-execution."""
        root = Path(slot_output_dir).resolve()
        record = _validated_qualified_record(root, slot_id)
        persisted = _read_json(root / PLAN_FILENAME)
        if persisted:
            plan = _validate_plan(persisted, slot_id=slot_id, record=record)
            if returned_plan is not None and str(returned_plan.get("plan_hash") or "") != str(
                plan.get("plan_hash") or ""
            ):
                raise SimplePublicationHandoffError("returned_and_persisted_plan_hash_mismatch")
            return plan

        candidate = dict(returned_plan or {})
        if not candidate:
            receipt = _read_json(root / RECEIPT_FILENAME)
            if isinstance(receipt.get("publication_lifecycle_plan"), Mapping):
                candidate = dict(receipt["publication_lifecycle_plan"])
        if not candidate:
            article = _read_json(root / ARTICLE_FILENAME)
            previews = _read_json(root / PREVIEWS_FILENAME)
            if not article or not previews:
                raise SimplePublicationHandoffError("publication_plan_reconstruction_artifacts_missing")
            candidate = _build_simple_publication_lifecycle_plan(
                run_id=slot_id,
                output_dir=root,
                selected_candidate={"story_identity": record.get("story_identity")},
                selected_plan_entry={"article_mode": record.get("resolved_article_mode")},
                article=article,
                article_identity=str(record.get("article_identity") or ""),
                native_previews=previews,
                qualified_record=record,
                epistemic_state=(
                    dict(record.get("epistemic_state") or {})
                    if isinstance(record.get("epistemic_state"), Mapping)
                    else {}
                ),
            )
        plan = _validate_plan(candidate, slot_id=slot_id, record=record)
        _write_immutable_json(root / PLAN_FILENAME, plan)
        return plan

    def _ensure_work_item(self, *, slot_id: str, plan: Mapping[str, Any]) -> dict[str, Any]:
        return dict(
            self.store.create_work_item(
                story_id=str(plan.get("story_identity") or slot_id),
                title=(
                    "Simple Gemini publication "
                    + str(plan.get("article_identity") or "")[:16]
                ),
                target_surface="MULTI_PLATFORM",
                work_item_id=slot_id,
                actor_ref="SimpleGeminiLocalScheduler",
                correlation_id=f"simple-publication:{slot_id}",
            )
        )

    @staticmethod
    def _summary(
        *,
        slot_id: str,
        plan: Mapping[str, Any],
        result: Mapping[str, Any],
        recovery_preflight: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        canonical_real = result.get("canonical_article_real_published") is True
        distribution = str(result.get("distribution_status") or "")
        unknown = bool(result.get("unknown_write_detected"))
        complete = bool(
            canonical_real
            and not unknown
            and (
                distribution == FULL_V1_NINE_SURFACE_PUBLICATION_CONFIRMED
                or int(result.get("derivative_confirmed_count") or 0) == 8
            )
        )
        if complete:
            state = "PUBLISHED"
        elif unknown or "RECOVERY" in distribution or distribution == "BLOCKED_SAFE_RECOVERY_BACKLOG_REMAINS":
            state = "PUBLICATION_RECOVERY_REQUIRED"
        else:
            state = "PUBLICATION_BLOCKED"
        return {
            "schema_version": SCHEMA_VERSION,
            "state": state,
            "work_item_id": slot_id,
            "plan_hash": str(plan.get("plan_hash") or ""),
            "article_identity": str(plan.get("article_identity") or ""),
            "canonical_article_real_published": canonical_real,
            "canonical_url": result.get("canonical_url"),
            "distribution_status": distribution or None,
            "derivative_confirmed_count": int(result.get("derivative_confirmed_count") or 0),
            "derivative_attempted_count": int(result.get("derivative_attempted_count") or 0),
            "public_write_performed": bool(result.get("public_write_performed")),
            "unknown_write_detected": unknown,
            "publication_coordinator_dispatched": True,
            "bridge_model_call_count": 0,
            "bridge_source_get_count": 0,
            "recovery_preflight": dict(recovery_preflight or {}),
        }

    def publish(
        self,
        *,
        slot_id: str,
        slot_output_dir: str | Path,
        returned_plan: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        plan = self.ensure_plan(
            slot_id=slot_id,
            slot_output_dir=slot_output_dir,
            returned_plan=returned_plan,
        )
        self._ensure_work_item(slot_id=slot_id, plan=plan)
        # ``publish_plan`` itself begins with ``recover_pending`` before registering fresh intent.
        result = dict(self.coordinator.publish_plan(slot_id, plan) or {})
        return self._summary(slot_id=slot_id, plan=plan, result=result)

    def resume(
        self,
        *,
        slot_id: str,
        slot_output_dir: str | Path,
    ) -> dict[str, Any]:
        """Resume an interrupted handoff without ever re-running the Simple semantic operation."""
        recovery = self.recover_preflight()
        if int(recovery.get("backlog_remaining") or 0) > 0:
            plan = self.ensure_plan(slot_id=slot_id, slot_output_dir=slot_output_dir)
            return {
                "schema_version": SCHEMA_VERSION,
                "state": "PUBLICATION_RECOVERY_REQUIRED",
                "work_item_id": slot_id,
                "plan_hash": str(plan.get("plan_hash") or ""),
                "article_identity": str(plan.get("article_identity") or ""),
                "canonical_article_real_published": False,
                "canonical_url": None,
                "distribution_status": "BLOCKED_SAFE_RECOVERY_BACKLOG_REMAINS",
                "derivative_confirmed_count": 0,
                "derivative_attempted_count": 0,
                "public_write_performed": bool(recovery.get("publish_calls")),
                "unknown_write_detected": True,
                "publication_coordinator_dispatched": False,
                "bridge_model_call_count": 0,
                "bridge_source_get_count": 0,
                "recovery_preflight": recovery,
            }
        plan = self.ensure_plan(slot_id=slot_id, slot_output_dir=slot_output_dir)
        self._ensure_work_item(slot_id=slot_id, plan=plan)
        # Complete any crash-interrupted partial outbox registration idempotently. Existing
        # finalized/dispatch rows are never rewritten by ``register_plan``.
        self.coordinator.register_plan(slot_id, plan)
        result = dict(self.coordinator.publish_plan(slot_id, plan) or {})
        return self._summary(
            slot_id=slot_id,
            plan=plan,
            result=result,
            recovery_preflight=recovery,
        )


def build_canonical_simple_publication_handoff(
    *, store_path: str | Path
) -> SimplePublicationHandoffV1:
    """Bind the scheduler process to the canonical V1 store/coordinator stack.

    Construction performs no readiness probe, browser/provider call, or public write. Destination
    readiness remains coordinator-owned JIT behavior at the exact publication/readback boundary.
    """
    validate_registry()
    store = ContentOpsDurableStore(store_path)
    orchestrator = ContentOpsProductionOrchestrator()
    readiness = DestinationReadinessManager(
        store=store,
        edge_runtime_ensurer=lambda **kwargs: orchestrator.execute(
            "ensure_canonical_edge_publishing_runtime",
            urls=tuple(kwargs.get("urls") or ()),
        ),
    )
    transport = CanonicalDestinationTransportRuntimeV1()

    def readiness_by_destination(destination: str) -> Mapping[str, Any]:
        surface = registration_for_destination(destination).surface
        return next(
            (
                row
                for row in store.list_destination_readiness()
                if row["surface"] == surface
            ),
            {},
        )

    coordinator = DurablePublicationCoordinator(
        store=store,
        transport_runtime=transport,
        readiness_provider=readiness_by_destination,
        readiness_manager=readiness,
    )
    return SimplePublicationHandoffV1(store=store, coordinator=coordinator)
