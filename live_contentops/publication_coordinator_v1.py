"""Single durable Final Daily App public-write owner.

The newsroom produces deterministic publication plans.  This coordinator persists exact
pre-write intent, records ``DISPATCH_ATTEMPT_STARTED`` before crossing any API/CDP boundary,
routes through the versioned transport registry, and owns strict readback/reconciliation.
There is deliberately no transport fallback and no automatic retry from UNKNOWN_WRITE.
"""
from __future__ import annotations

import hashlib
import json
from contextlib import nullcontext
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Optional
from urllib.parse import urlsplit

from live_contentops.destination_transport_registry_v1 import (
    READY_STATES,
    REGISTRY_VERSION,
    V1_QUALITY_PROBATION_POLICY_ID,
    V1_REQUIRED_DERIVATIVE_DESTINATIONS,
    V1_REQUIRED_PUBLICATION_DESTINATIONS,
    registration_for_destination,
)
from live_contentops.browser_interaction_budget_v1 import browser_activity


ATTEMPT_STARTED = "DISPATCH_ATTEMPT_STARTED"
DISPATCH_CONFIRMED = "DISPATCH_CONFIRMED"
UNKNOWN_WRITE = "UNKNOWN_WRITE"
DEFINITE_NO_WRITE = "DEFINITE_NO_WRITE"
RECONCILED_CONFIRMED = "RECONCILED_CONFIRMED"
RECONCILIATION_PENDING = "RECONCILIATION_PENDING"
RECONCILED_ABSENT_SAFE_TO_RETRY = "RECONCILED_ABSENT_SAFE_TO_RETRY"
RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE = (
    "RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE"
)
DERIVATIVE_EXPIRED_STALE_NO_WRITE = "DERIVATIVE_EXPIRED_STALE_NO_WRITE"
DERIVATIVE_RECOVERY_RETRY_EXHAUSTED_NO_WRITE = (
    "DERIVATIVE_RECOVERY_RETRY_EXHAUSTED_NO_WRITE"
)
RECOVERY_ATTEMPT_BUDGET = 9
HOLD_FULL_V1_DISTRIBUTION_NOT_READY = "HOLD_FULL_V1_DISTRIBUTION_NOT_READY"
CANONICAL_SUBSTACK_READY_DERIVATIVES_DEFERRED = (
    "CANONICAL_SUBSTACK_READY_DERIVATIVES_DEFERRED"
)
PARTIAL_DISTRIBUTION_RECOVERY_REQUIRED = "PARTIAL_DISTRIBUTION_RECOVERY_REQUIRED"
FULL_V1_NINE_SURFACE_PUBLICATION_CONFIRMED = (
    "FULL_V1_NINE_SURFACE_PUBLICATION_CONFIRMED"
)
_PUBLICATION_CONFIRMED_RECONCILIATIONS = {
    RECONCILED_CONFIRMED,
    RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE,
}
_SUBSTACK_POST_WRITE_OUTCOME_SCHEMA = "contentops.substack_post_write_outcome.v1"
_SUBSTACK_POST_WRITE_STATUS_CLASSES = frozenset(
    {"2XX", "4XX", "5XX", "NETWORK_ERROR", "TIMEOUT", "ABORTED", "UNKNOWN"}
)
_SUBSTACK_POST_WRITE_REASONS = frozenset(
    {
        "HTTP_RESPONSE_OBSERVED",
        "REQUEST_FAILED_NETWORK",
        "REQUEST_FAILED_TIMEOUT",
        "REQUEST_FAILED_ABORTED",
        "REQUEST_OBSERVED_COMPLETION_NOT_OBSERVED",
        "EXACT_REQUEST_NOT_OBSERVED",
        "OBSERVATION_SURFACE_UNAVAILABLE",
        "MULTIPLE_EXACT_REQUESTS_OBSERVED",
        "HTTP_STATUS_OUTSIDE_BOUNDED_CLASSES",
        "UNKNOWN",
    }
)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True, default=str)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _valid_substack_canonical_url(value: Any) -> bool:
    try:
        parsed = urlsplit(str(value or "").strip())
    except ValueError:
        return False
    path = parsed.path.rstrip("/")
    return bool(
        parsed.scheme == "https"
        and (parsed.hostname or "").casefold() == "capitalchronicle.substack.com"
        and path.startswith("/p/")
        and len(path.removeprefix("/p/")) > 0
        and path != "/p/pending-publication"
        and not parsed.username
        and not parsed.password
    )


def _parse_utc(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _bounded_substack_provider_outcome(
    value: Any,
    *,
    expected_dispatch_id: str | None = None,
    expected_draft_id: str | None = None,
) -> dict[str, Any] | None:
    """Accept only the closed sanitized outcome contract; it is never write certainty."""
    if not isinstance(value, Mapping):
        return None
    if str(value.get("schema") or "") != _SUBSTACK_POST_WRITE_OUTCOME_SCHEMA:
        return None
    draft_id = str(value.get("draft_id") or "").strip()
    dispatch_identity = str(value.get("dispatch_identity") or "").strip()
    if not draft_id.isdigit() or not dispatch_identity.startswith("dispatch_"):
        return None
    if expected_dispatch_id and dispatch_identity != str(expected_dispatch_id):
        return None
    if expected_draft_id and draft_id != str(expected_draft_id):
        return None
    status_class = str(value.get("status_class") or "").upper()
    reason = str(value.get("reason") or "").upper()
    if status_class not in _SUBSTACK_POST_WRITE_STATUS_CLASSES:
        return None
    if reason not in _SUBSTACK_POST_WRITE_REASONS:
        return None
    request_observed = value.get("request_observed") is True
    completion_observed = value.get("completion_observed") is True
    request_started_at = str(value.get("request_started_at") or "") or None
    completion_observed_at = str(value.get("completion_observed_at") or "") or None
    if request_started_at and (
        len(request_started_at) > 40 or _parse_utc(request_started_at) is None
    ):
        return None
    if completion_observed_at and (
        len(completion_observed_at) > 40 or _parse_utc(completion_observed_at) is None
    ):
        return None
    if not request_observed and (request_started_at or completion_observed):
        return None
    if request_observed and not request_started_at:
        return None
    if not completion_observed and completion_observed_at:
        return None
    if completion_observed and not completion_observed_at:
        return None
    if status_class != "UNKNOWN" and not completion_observed:
        return None
    return {
        "schema": _SUBSTACK_POST_WRITE_OUTCOME_SCHEMA,
        "observation_source": "PLAYWRIGHT_EXACT_SUBSTACK_PUBLISH_REQUEST_EVENTS",
        "draft_id": draft_id,
        "dispatch_identity": dispatch_identity,
        "request_observed": request_observed,
        "request_started_at": request_started_at,
        "completion_observed": completion_observed,
        "completion_observed_at": completion_observed_at,
        "status_class": status_class,
        "reason": reason,
        "request_url_persisted": False,
        "request_query_persisted": False,
        "request_body_persisted": False,
        "response_body_persisted": False,
        "headers_persisted": False,
        "cookies_persisted": False,
        "tokens_persisted": False,
        "browser_storage_persisted": False,
        "auth_material_persisted": False,
        "raw_error_persisted": False,
        "arbitrary_network_log_persisted": False,
    }


def normalize_dispatch_result(
    result: Mapping[str, Any], *, destination: str, surface: str, transport_type: str
) -> dict[str, Any]:
    """Normalize current and accepted historical adapter result shapes.

    Stable provider IDs are sufficient identity authority; a URL is intentionally optional.
    HTTP/browser success without a stable object identity remains UNKNOWN_WRITE.
    """
    raw = dict(result or {})
    object_id = next((str(raw.get(k)) for k in (
        "public_object_id", "post_id", "message_id", "media_id", "id", "activity_id",
        "root_post_id", "draft_id",
    ) if raw.get(k) not in (None, "")), None)
    object_url = next((str(raw.get(k)) for k in (
        "public_object_url", "public_url", "post_url", "permalink", "url", "root_url",
    ) if raw.get(k) not in (None, "")), None)
    status_text = str(raw.get("status") or raw.get("classification") or "").upper()
    explicit_no_write = bool(raw.get("definite_no_write")) or status_text in {
        "DEFINITE_NO_WRITE", "FAILED_BEFORE_WRITE", "CONTROLLED_NO_PUBLIC_WRITE",
        "DISPATCH_CONFIRMED_NO_WRITE",
    }
    explicit_success = (
        raw.get("ok") is True
        or raw.get("success") is True
        or raw.get("published") is True
        or any(token in status_text for token in ("PASS", "PUBLISHED", "CONFIRMED", "SUCCESS"))
    )
    if explicit_no_write:
        status, certainty = DEFINITE_NO_WRITE, "DEFINITE_NO_WRITE"
        object_id = object_url = None
    elif object_id and (explicit_success or not status_text):
        status, certainty = DISPATCH_CONFIRMED, "PROVIDER_ACCEPTED"
    else:
        status, certainty = UNKNOWN_WRITE, "AMBIGUOUS"
    normalized = {
        "destination": destination,
        "surface": surface,
        "transport_type": transport_type,
        "adapter_version": str(raw.get("adapter_version") or raw.get("schema_version") or "historical_adapter_compatible"),
        "status": status,
        "public_object_id": object_id,
        "public_object_url": object_url,
        "write_outcome_certainty": certainty,
        "safe_error_classification": str(raw.get("error_class") or raw.get("reason_code") or "") or None,
        "provider_metadata": {
            "source_status": status_text or None,
            "stable_provider_identity_present": bool(object_id),
            "public_url_present": bool(object_url),
        },
    }
    provider_outcome = (
        _bounded_substack_provider_outcome(raw.get("provider_outcome"))
        if destination == "substack"
        else None
    )
    if provider_outcome is not None:
        normalized["provider_outcome"] = provider_outcome
    return normalized


def normalize_readback_result(
    result: Mapping[str, Any], *, public_object_id: Optional[str]
) -> dict[str, Any]:
    raw = dict(result or {})
    observed_id = next((str(raw.get(k)) for k in (
        "public_object_id", "post_id", "message_id", "media_id", "id", "activity_id",
        "root_post_id",
    ) if raw.get(k) not in (None, "")), None)
    observed_url = next((str(raw.get(k)) for k in (
        "public_object_url", "public_url", "post_url", "permalink", "url", "root_url",
    ) if raw.get(k) not in (None, "")), None)
    absent = raw.get("write_absent") is True or str(raw.get("status") or "").upper() in {
        "NOT_FOUND", "ABSENT", "ABSENT_SAFE_TO_RETRY", "RECONCILED_ABSENT_SAFE_TO_RETRY",
    }
    verified_flag = any(raw.get(k) is True for k in (
        "verified", "readback_verified", "public_readback_verified", "strict_readback_verified",
        "identity_verified",
    )) or str(raw.get("status") or "").upper() in {"SUCCESS", "PASS", "RECONCILED_CONFIRMED"}
    matching = bool(
        observed_id
        and (
            (public_object_id and observed_id == str(public_object_id))
            or (
                not public_object_id
                and (verified_flag or raw.get("write_exists") is True)
            )
        )
    )
    return {
        "verified": bool(verified_flag and matching),
        "write_absent": bool(absent),
        "write_exists": bool(raw.get("write_exists") is True and matching),
        "observed_public_object_id": observed_id,
        "observed_public_object_url": observed_url,
        "identity_match": matching,
        "source_status": str(raw.get("status") or raw.get("classification") or "") or None,
    }


class DurablePublicationCoordinator:
    """Exactly-one write owner for all Final Daily App destinations."""

    def __init__(
        self,
        *,
        store: Any,
        transport_runtime: Any,
        readiness_provider: Optional[Callable[[str], Mapping[str, Any]]] = None,
        readiness_manager: Any = None,
        readiness_refresh_seconds: float = 300.0,
        clock: Optional[Callable[[], datetime]] = None,
        recovery_quarantined_work_item_ids: tuple[str, ...] = (),
    ) -> None:
        self.store = store
        self.transport_runtime = transport_runtime
        self.readiness_provider = readiness_provider
        self.readiness_manager = readiness_manager
        self.readiness_refresh_seconds = max(30.0, float(readiness_refresh_seconds))
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._recovery_quarantined_work_item_ids = frozenset(
            str(value).strip()
            for value in recovery_quarantined_work_item_ids
            if str(value).strip()
        )

    def _recovery_is_quarantined(self, work_item_id: Any) -> bool:
        return str(work_item_id or "") in self._recovery_quarantined_work_item_ids

    def _active_unknown_write_count(self) -> int:
        """Count UNKNOWN writes that are allowed to participate in current recovery.

        An explicitly quarantined historical lifecycle remains byte-for-byte durable evidence,
        but it cannot poison delivery-media preconditions for a distinct fresh work item. Missing
        message ownership remains fail-closed and is counted as active UNKNOWN.
        """
        count = 0
        for dispatch in self.store.list_platform_dispatches():
            if str(dispatch.get("status") or "") != UNKNOWN_WRITE:
                continue
            message = self.store.get_outbox_message(str(dispatch.get("message_id") or ""))
            if message is not None and self._recovery_is_quarantined(
                message.get("work_item_id")
            ):
                continue
            count += 1
        return count

    @staticmethod
    def _freshness_horizon(intent: Mapping[str, Any]) -> timedelta:
        mode = str(intent.get("resolved_article_mode") or "").upper()
        if "BREAKING" in mode:
            return timedelta(hours=6)
        if "FOLLOW_UP" in mode or "UPDATE" in mode:
            return timedelta(hours=24)
        if "DEEP_DIVE" in mode:
            return timedelta(hours=72)
        if "EVERGREEN" in mode:
            return timedelta(days=7)
        return timedelta(hours=24)

    def _message_is_stale(
        self, message: Mapping[str, Any], intent: Mapping[str, Any]
    ) -> bool:
        publication_window = intent.get("publication_window") or {}
        if isinstance(publication_window, Mapping):
            explicit_expiry = _parse_utc(
                publication_window.get("expires_at_utc")
                or publication_window.get("fresh_until_utc")
            )
            if explicit_expiry is not None:
                return self._clock().astimezone(timezone.utc) >= explicit_expiry
        created = _parse_utc(message.get("created_at"))
        return bool(
            created is not None
            and self._clock().astimezone(timezone.utc)
            >= created + self._freshness_horizon(intent)
        )

    def _retry_incident_id(self, dispatch_id: str) -> str:
        return "incident_derivative_recovery_retry_" + _hash(dispatch_id)[:24]

    def _retry_already_attempted(self, dispatch_id: str) -> bool:
        try:
            with self.store.get_read_only_connection() as conn:
                return conn.execute(
                    "SELECT 1 FROM incidents WHERE incident_id=?",
                    (self._retry_incident_id(dispatch_id),),
                ).fetchone() is not None
        except Exception:
            return True

    def _record_retry_attempt(self, dispatch_id: str, work_item_id: str) -> None:
        self.store.register_incident(
            incident_id=self._retry_incident_id(dispatch_id),
            work_item_id=work_item_id,
            severity="RECOVERY_AUDIT",
            description="One bounded absence-safe derivative retry crossed the write boundary.",
        )

    def _transport_correction_incident_id(
        self, dispatch_id: str, correction_id: str
    ) -> str:
        return "incident_transport_correction_" + _hash(
            f"{dispatch_id}:{correction_id}"
        )[:24]

    def _transport_correction_already_attempted(
        self, dispatch_id: str, correction_id: str
    ) -> bool:
        try:
            with self.store.get_read_only_connection() as conn:
                return conn.execute(
                    "SELECT 1 FROM incidents WHERE incident_id=?",
                    (self._transport_correction_incident_id(dispatch_id, correction_id),),
                ).fetchone() is not None
        except Exception:
            return True

    def _record_transport_correction_attempt(
        self, dispatch_id: str, correction_id: str, work_item_id: str
    ) -> None:
        self.store.register_incident(
            incident_id=self._transport_correction_incident_id(
                dispatch_id, correction_id
            ),
            work_item_id=work_item_id,
            severity="RECOVERY_AUDIT",
            description=(
                "One explicit transport-correction derivative completion crossed "
                "the write boundary under the preserved dispatch identity."
            ),
        )

    def _expire_stale_derivative(
        self, message: Mapping[str, Any], dispatch: Mapping[str, Any] | None
    ) -> None:
        message_id = str(message["message_id"])
        self.store.set_outbox_status(message_id, DERIVATIVE_EXPIRED_STALE_NO_WRITE)
        if dispatch is not None:
            self.store.set_dispatch_status(
                str(dispatch["dispatch_id"]), DERIVATIVE_EXPIRED_STALE_NO_WRITE
            )
        self.store.register_incident(
            incident_id="incident_derivative_stale_" + _hash(message_id)[:24],
            work_item_id=str(message.get("work_item_id") or "") or None,
            severity="RECOVERY_AUDIT",
            description="Stale derivative expired with zero public write; prior readback history retained.",
        )

    def _refresh_readiness_if_due(self) -> bool:
        """Compatibility seam: periodic active/global readiness refresh is disabled."""
        return False

    @staticmethod
    def _ids(work_item_id: str, plan_hash: str, destination: str) -> dict[str, str]:
        stem = _hash(_canonical_json({
            "work_item_id": work_item_id, "plan_hash": plan_hash, "destination": destination,
        }))[:32]
        return {
            "message_id": f"outbox_{stem}",
            "dispatch_id": f"dispatch_{stem}",
            "reconciliation_id": f"reconciliation_{stem}",
        }

    def _mode(self) -> str:
        try:
            return str(self.store.get_operating_control()["operating_mode"])
        except Exception:
            return "KILL_SWITCH"

    def _readiness(self, destination: str, planned: Mapping[str, Any]) -> str:
        if callable(self.readiness_provider):
            row = dict(self.readiness_provider(destination) or {})
            return str(row.get("readiness_state") or row.get("status") or "")
        surface = registration_for_destination(destination).surface
        rows = {str(row["surface"]): row for row in self.store.list_destination_readiness()}
        if surface in rows:
            return str(rows[surface].get("readiness_state") or "")
        # A plan may carry a freshly probed readiness decision.  Unknown is never READY.
        return str(planned.get("readiness_state") or "")

    @staticmethod
    def _full_v1_distribution_required(plan_or_intent: Mapping[str, Any]) -> bool:
        return bool(
            plan_or_intent.get("full_v1_distribution_required") is True
            and str(plan_or_intent.get("quality_probation_policy_id") or "")
            == V1_QUALITY_PROBATION_POLICY_ID
        )

    @staticmethod
    def _confirmed_public_object(
        outcome: Mapping[str, Any], *, destination: str
    ) -> bool:
        if (
            outcome.get("status") != DISPATCH_CONFIRMED
            or not str(outcome.get("public_object_id") or "")
            or outcome.get("reconciliation_status")
            not in _PUBLICATION_CONFIRMED_RECONCILIATIONS
        ):
            return False
        if destination == "substack":
            return bool(
                outcome.get("reconciliation_status") == RECONCILED_CONFIRMED
                and _valid_substack_canonical_url(outcome.get("public_object_url"))
            )
        return True

    def _full_v1_distribution_preflight(
        self, work_item_id: str, plan: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Validate nine-surface structure and JIT only canonical Substack before its write.

        Derivative readiness is intentionally deferred until after canonical confirmation.  The
        exact eight destination identities/packages remain structural requirements, but a local
        derivative outage is a hold/recovery obligation rather than a canonical veto.
        """

        destinations = [
            str(row.get("destination") or "")
            for row in (plan.get("destinations") or [])
            if isinstance(row, Mapping)
        ]
        item_by_destination = {
            str(row.get("destination") or ""): dict(row)
            for row in (plan.get("destinations") or [])
            if isinstance(row, Mapping) and str(row.get("destination") or "")
        }
        required = set(V1_REQUIRED_PUBLICATION_DESTINATIONS)
        observed = set(destinations)
        duplicate_destinations = sorted(
            destination
            for destination in observed
            if destinations.count(destination) > 1
        )
        skipped = sorted(
            str(row.get("destination") or "")
            for row in (plan.get("skipped_derivative_destinations") or [])
            if isinstance(row, Mapping) and str(row.get("destination") or "")
        )
        structural_blockers = {
            "missing_destinations": sorted(required - observed),
            "unexpected_destinations": sorted(observed - required),
            "duplicate_destinations": duplicate_destinations,
            "skipped_derivative_destinations": skipped,
            "pre_substack_blockers": sorted(
                str(value) for value in (plan.get("pre_substack_blockers") or [])
                if str(value)
            ),
        }
        plan_hash = str(plan.get("plan_hash") or _hash(_canonical_json(plan)))
        readiness_rows: dict[str, Any] = {}
        readiness_blockers: list[str] = []
        for destination in V1_REQUIRED_PUBLICATION_DESTINATIONS:
            item = item_by_destination.get(destination, {})
            if destination != "substack":
                readiness_rows[destination] = {
                    "readiness_state": "JIT_DEFERRED_UNTIL_CANONICAL_CONFIRMED",
                    "identity_match": None,
                    "write_eligible": False,
                    "jit_deferred_until_after_canonical": True,
                    "planned_readiness_state": str(item.get("readiness_state") or ""),
                    "safe_error_classification": None,
                    "sanitized_detail": {},
                }
                continue
            try:
                if self.readiness_manager is not None:
                    row = dict(
                        self.readiness_manager.verify_destination_jit(
                            destination,
                            reason="PUBLICATION",
                            persist=True,
                            attempt_identity=self._ids(
                                work_item_id, plan_hash, destination
                            )["dispatch_id"],
                        )
                        or {}
                    )
                elif callable(self.readiness_provider):
                    row = dict(self.readiness_provider(destination) or {})
                else:
                    row = {"readiness_state": self._readiness(destination, item)}
            except Exception as exc:
                row = {
                    "readiness_state": "READINESS_CHECK_FAILED",
                    "identity_match": False,
                    "safe_error_classification": type(exc).__name__,
                }
            state = str(row.get("readiness_state") or row.get("status") or "")
            identity_match = row.get("identity_match")
            write_eligible = row.get("write_eligible")
            ready = bool(
                state in READY_STATES
                and identity_match not in (False, 0, "false", "False")
                and write_eligible not in (False, 0, "false", "False")
            )
            readiness_rows[destination] = {
                "readiness_state": state or "READINESS_UNKNOWN",
                "identity_match": identity_match,
                "write_eligible": ready,
                "safe_error_classification": row.get("safe_error_classification"),
                "sanitized_detail": dict(row.get("sanitized_detail") or {})
                if isinstance(row.get("sanitized_detail"), Mapping)
                else {},
            }
            if not ready:
                readiness_blockers.append(destination)
        structural_ready = not any(structural_blockers.values())
        return {
            "status": (
                CANONICAL_SUBSTACK_READY_DERIVATIVES_DEFERRED
                if structural_ready and not readiness_blockers
                else HOLD_FULL_V1_DISTRIBUTION_NOT_READY
            ),
            "required_destinations": list(V1_REQUIRED_PUBLICATION_DESTINATIONS),
            "required_derivative_destinations": list(
                V1_REQUIRED_DERIVATIVE_DESTINATIONS
            ),
            "structural_blockers": structural_blockers,
            "readiness_blockers": readiness_blockers,
            "derivative_readiness_deferred": list(
                V1_REQUIRED_DERIVATIVE_DESTINATIONS
            ),
            "per_destination": readiness_rows,
            "public_write_performed": False,
        }

    @staticmethod
    def _record_runtime_activity(
        intent: Mapping[str, Any], stage: str, *, destination: str | None = None
    ) -> None:
        """Best-effort presentation telemetry; durable publication truth stays authoritative."""
        output_dir = str(intent.get("output_dir") or "").strip()
        work_item_id = str(intent.get("work_item_id") or "").strip()
        if not output_dir or not work_item_id:
            return
        try:
            from live_contentops.runtime_activity_projection_v1 import RuntimeActivityRecorderV1

            RuntimeActivityRecorderV1(
                output_dir=Path(output_dir), work_item_id=work_item_id
            ).record(stage, destination=destination)
        except (OSError, TypeError, ValueError):
            # Cockpit telemetry can never interrupt a canonical publication or recovery path.
            return

    def register_plan(self, work_item_id: str, plan: Mapping[str, Any]) -> dict[str, Any]:
        if str(plan.get("transport_registry_version") or "") != REGISTRY_VERSION:
            raise ValueError("publication_plan_transport_registry_version_mismatch")
        plan_hash = str(plan.get("plan_hash") or _hash(_canonical_json(plan)))
        registered = []
        for item in sorted(plan.get("destinations") or [], key=lambda row: (
            0 if str(row.get("destination")) == "substack" else 1,
            str(row.get("destination")),
        )):
            destination = str(item.get("destination") or "")
            registration = registration_for_destination(destination)
            if str(item.get("surface") or "") != registration.surface:
                raise ValueError(f"publication_plan_surface_mismatch:{destination}")
            if str(item.get("transport_type") or "") != registration.transport_type:
                raise ValueError(f"publication_plan_transport_mismatch:{destination}")
            ids = self._ids(work_item_id, plan_hash, destination)
            intent = {
                "schema_version": "contentops.prewrite_intent.v1",
                "work_item_id": work_item_id,
                "story_identity": plan.get("story_identity"),
                "update_chain_identity": plan.get("update_chain_identity"),
                "resolved_article_mode": plan.get("resolved_article_mode"),
                "editorial_classification": plan.get("editorial_classification"),
                "article_identity": plan.get("article_identity"),
                "article_content_sha256": plan.get("article_content_sha256"),
                "compiler_input_sha256": plan.get("compiler_input_sha256"),
                "accepted_evidence_ids": list(
                    plan.get("accepted_evidence_ids") or []
                ),
                "accepted_evidence_sha256": plan.get("accepted_evidence_sha256"),
                "source_provenance_binding_preserved": (
                    plan.get("source_provenance_binding_preserved") is True
                ),
                "epistemic_state": dict(plan.get("epistemic_state") or {}),
                "bridge_schema_version": plan.get("bridge_schema_version"),
                "bridge_model_call_count": int(
                    plan.get("bridge_model_call_count") or 0
                ),
                "bridge_source_get_count": int(
                    plan.get("bridge_source_get_count") or 0
                ),
                "publication_window": plan.get("publication_window"),
                "package_identity": plan.get("package_identity"),
                "plan_hash": plan_hash,
                "output_dir": plan.get("output_dir"),
                "artifact_refs": plan.get("artifact_refs") or {},
                "editorial_features": plan.get("editorial_features") or {},
                "learning_policy_version": plan.get("learning_policy_version"),
                "quality_probation_policy_id": plan.get("quality_probation_policy_id"),
                "full_v1_distribution_required": plan.get(
                    "full_v1_distribution_required"
                ) is True,
                "required_publication_destinations": list(
                    plan.get("required_publication_destinations") or []
                ),
                "required_derivative_destinations": list(
                    plan.get("required_derivative_destinations") or []
                ),
                "destination_plan": dict(item),
                "payload": item.get("payload"),
                "canonical_url": item.get("canonical_url"),
                "transport_registry_version": REGISTRY_VERSION,
                "policy_mode_version": plan.get("policy_mode_version"),
                "attempt_identity": ids["dispatch_id"],
                "callables_persisted": False,
                "secrets_persisted": False,
            }
            payload = _canonical_json(intent)
            expected_hash = str(item.get("payload_hash") or "")
            if item.get("payload") is not None and expected_hash:
                actual_hash = _hash(str(item.get("payload")))
                if actual_hash != expected_hash:
                    raise ValueError(f"publication_plan_payload_hash_mismatch:{destination}")
            self.store.register_outbox_message(
                message_id=ids["message_id"], work_item_id=work_item_id,
                destination=destination, payload=payload, status="READY",
            )
            registered.append({"destination": destination, **ids})
        return {"plan_hash": plan_hash, "registered": registered, "outbox_count": len(registered)}

    def _reconcile(
        self,
        dispatch: Mapping[str, Any],
        intent: Mapping[str, Any],
        *,
        provider_outcome: Mapping[str, Any] | None = None,
    ) -> str:
        dispatch_id = str(dispatch["dispatch_id"])
        destination = str(dispatch["platform"])
        object_id = str(dispatch.get("public_object_id") or "") or None
        ids = self._ids(str(intent["work_item_id"]), str(intent["plan_hash"]), destination)
        registration = registration_for_destination(destination)
        self._record_runtime_activity(
            intent,
            "CANONICAL_READBACK" if destination == "substack" else "RECONCILIATION",
            destination=destination,
        )
        try:
            if registration.transport_type == "EDGE_CDP" and self.readiness_manager is not None:
                self.readiness_manager.ensure_destination_runtime_for_readback(destination)
            activity = (
                browser_activity(
                    "RECONCILIATION_ACTIVE",
                    reason="EXACT_DESTINATION_READBACK",
                    destination=destination,
                )
                if registration.transport_type == "EDGE_CDP" else nullcontext()
            )
            with activity:
                raw = self.transport_runtime.readback(
                    destination=destination,
                    public_object_id=object_id,
                    public_object_url=str(dispatch.get("public_object_url") or "") or None,
                    intent=intent,
                )
            normalized = normalize_readback_result(raw or {}, public_object_id=object_id)
        except Exception as exc:
            normalized = {
                "verified": False, "write_absent": False, "identity_match": False,
                "observed_public_object_id": None, "observed_public_object_url": None,
                "error_class": type(exc).__name__,
            }
        self._record_runtime_activity(intent, "RECONCILIATION", destination=destination)
        observed_url = str(
            normalized.get("observed_public_object_url")
            or dispatch.get("public_object_url")
            or ""
        ) or None
        if destination == "substack":
            normalized["canonical_url_valid"] = _valid_substack_canonical_url(observed_url)
            if normalized.get("verified") is True and not normalized["canonical_url_valid"]:
                normalized["verified"] = False
                normalized["identity_match"] = False
                normalized["error_class"] = "substack_canonical_url_missing_or_invalid"
        readback_packet = {
            "dispatch_id": dispatch_id,
            "destination": destination,
            "readback": normalized,
        }
        bounded_provider_outcome = (
            _bounded_substack_provider_outcome(
                provider_outcome,
                expected_dispatch_id=dispatch_id,
                expected_draft_id=object_id,
            )
            if destination == "substack"
            else None
        )
        if bounded_provider_outcome is not None:
            # Evidence about request completion is retained beside strict readback. It does not
            # alter the reconciliation branch or supply public object/URL authority.
            readback_packet["provider_outcome"] = bounded_provider_outcome
        readback_data = _canonical_json(readback_packet)
        self.store.register_readback(
            readback_id="readback_" + _hash(readback_data)[:32],
            dispatch_id=dispatch_id,
            readback_data=readback_data,
        )
        if normalized.get("verified") is True:
            status = RECONCILED_CONFIRMED
            recovered_id = str(normalized.get("observed_public_object_id") or "") or object_id
            if recovered_id:
                self.store.register_platform_dispatch(
                    dispatch_id=dispatch_id,
                    message_id=str(dispatch["message_id"]),
                    platform=destination,
                    status=DISPATCH_CONFIRMED,
                    public_object_id=recovered_id,
                    public_object_url=observed_url,
                )
            self.store.set_dispatch_status(dispatch_id, DISPATCH_CONFIRMED)
            self.store.set_outbox_status(str(dispatch["message_id"]), DISPATCH_CONFIRMED)
        elif normalized.get("write_absent") is True:
            status = RECONCILED_ABSENT_SAFE_TO_RETRY
            # The exact readback proved that the intended public write did not occur.  Clear
            # UNKNOWN_WRITE durably while preserving the stable draft/object id for audit. A
            # later bounded recovery pass may make one explicit retry under this same identity.
            self.store.set_dispatch_status(dispatch_id, RECONCILED_ABSENT_SAFE_TO_RETRY)
            self.store.set_outbox_status(
                str(dispatch["message_id"]), RECONCILED_ABSENT_SAFE_TO_RETRY
            )
        elif normalized.get("write_exists") is True:
            # Exact object identity proves the write occurred even when a stricter content/media
            # gate failed. Clear UNKNOWN_WRITE and end retry recovery without overstating strict
            # content/metrics readback. Stable provider identity still confirms publication.
            status = RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE
            recovered_id = str(normalized.get("observed_public_object_id") or "") or object_id
            if recovered_id:
                self.store.register_platform_dispatch(
                    dispatch_id=dispatch_id,
                    message_id=str(dispatch["message_id"]),
                    platform=destination,
                    status=DISPATCH_CONFIRMED,
                    public_object_id=recovered_id,
                    public_object_url=observed_url,
                )
            self.store.set_dispatch_status(dispatch_id, DISPATCH_CONFIRMED)
            self.store.set_outbox_status(str(dispatch["message_id"]), DISPATCH_CONFIRMED)
        else:
            status = RECONCILIATION_PENDING
        self.store.register_reconciliation(
            reconciliation_id=ids["reconciliation_id"],
            work_item_id=str(intent["work_item_id"]), status=status,
        )
        self.store.set_reconciliation_status(ids["reconciliation_id"], status)
        return status

    def _dispatch_message(
        self,
        message: Mapping[str, Any],
        *,
        canonical_url: Optional[str],
        explicit_reconciled_absent_retry: bool = False,
        explicit_transport_correction_retry: bool = False,
        recovery_public_object_url: Optional[str] = None,
    ) -> dict[str, Any]:
        intent = json.loads(str(message["payload"]))
        destination = str(message["destination"])
        item = dict(intent["destination_plan"])
        ids = self._ids(str(intent["work_item_id"]), str(intent["plan_hash"]), destination)
        existing = self.store.get_platform_dispatch(ids["dispatch_id"])
        if existing:
            reconciliation_status = None
            getter = getattr(self.store, "get_reconciliations_for_work_item", None)
            if callable(getter):
                reconciliation_status = next(
                    (
                        str(row.get("status") or "")
                        for row in getter(str(intent["work_item_id"]))
                        if str(row.get("reconciliation_id") or "")
                        == ids["reconciliation_id"]
                    ),
                    None,
                )
            recovery_object_id = str(existing.get("public_object_id") or "") or None
            retry_eligible = bool(
                explicit_reconciled_absent_retry
                and str(existing.get("status") or "") == RECONCILED_ABSENT_SAFE_TO_RETRY
                and reconciliation_status == RECONCILED_ABSENT_SAFE_TO_RETRY
                and (destination != "substack" or recovery_object_id)
            )
            correction_retry_eligible = bool(
                explicit_transport_correction_retry
                and (
                    (
                        destination == "instagram_business"
                        and str(existing.get("status") or "") in {
                            DERIVATIVE_RECOVERY_RETRY_EXHAUSTED_NO_WRITE,
                            RECONCILED_ABSENT_SAFE_TO_RETRY,
                        }
                        and reconciliation_status == RECONCILED_ABSENT_SAFE_TO_RETRY
                    )
                    or (
                        destination == "x"
                        and str(existing.get("status") or "") == DISPATCH_CONFIRMED
                        and reconciliation_status
                        == RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE
                        and str(
                            recovery_public_object_url
                            or existing.get("public_object_url")
                            or ""
                        ).startswith("https://x.com/")
                    )
                )
            )
            if not (retry_eligible or correction_retry_eligible):
                return {
                    "destination": destination,
                    "status": str(existing["status"]),
                    "publish_called": False,
                    "public_object_id": existing.get("public_object_id"),
                    "public_object_url": existing.get("public_object_url"),
                    "reconciliation_status": reconciliation_status,
                }
            if destination == "substack":
                intent = {**intent, "recovery_public_object_id": recovery_object_id}
            elif correction_retry_eligible and destination == "x":
                intent = {
                    **intent,
                    "recovery_public_object_url": str(
                        recovery_public_object_url
                        or existing.get("public_object_url")
                        or ""
                    ),
                }
        dependency = item.get("canonical_url_dependency")
        if dependency and not (canonical_url or intent.get("canonical_url")):
            return {"destination": destination, "status": "WAITING_CANONICAL_URL", "publish_called": False}
        if dependency and canonical_url:
            if explicit_reconciled_absent_retry or explicit_transport_correction_retry:
                # The original attempt already froze exact canonical-bound bytes before its
                # dispatch marker. Recovery must reuse them byte-for-byte, never mutate them.
                if str(intent.get("canonical_url") or "") != canonical_url:
                    return {
                        "destination": destination,
                        "status": "RETRY_BLOCKED_CANONICAL_PAYLOAD_IDENTITY_MISMATCH",
                        "publish_called": False,
                    }
            else:
                finalizer = getattr(self.transport_runtime, "finalize_intent", None)
                if callable(finalizer):
                    intent = dict(finalizer(destination=destination, intent=intent, canonical_url=canonical_url))
                else:
                    intent["canonical_url"] = canonical_url
                finalized_payload = _canonical_json(intent)
                self.store.finalize_outbox_payload_before_dispatch(
                    message_id=ids["message_id"], payload=finalized_payload, status="READY",
                )
            item = dict(intent["destination_plan"])
        # Re-read durable mode immediately before every new adapter write.
        mode = self._mode()
        if mode != "AUTONOMOUS_DEFAULT":
            return {"destination": destination, "status": f"WRITE_BLOCKED_{mode}", "publish_called": False}
        self._record_runtime_activity(intent, "PUBLICATION_JIT", destination=destination)
        if self.readiness_manager is not None:
            cached_failure = None
            cached_failure_fn = getattr(self.readiness_manager, "cached_failed_jit_attempt", None)
            if callable(cached_failure_fn):
                cached_failure = cached_failure_fn(
                    destination, attempt_identity=ids["dispatch_id"]
                )
            readiness_row = cached_failure or self.readiness_manager.verify_destination_jit(
                destination,
                reason="PUBLICATION",
                persist=True,
                attempt_identity=ids["dispatch_id"],
            )
            readiness = str(readiness_row.get("readiness_state") or "")
        else:
            readiness = self._readiness(destination, item)
        if readiness not in READY_STATES:
            return {"destination": destination, "status": readiness or "READINESS_UNKNOWN", "publish_called": False}
        self.store.register_platform_dispatch(
            dispatch_id=ids["dispatch_id"], message_id=ids["message_id"],
            platform=destination, status=ATTEMPT_STARTED,
            public_object_id=(existing or {}).get("public_object_id"),
            public_object_url=(existing or {}).get("public_object_url"),
        )
        authorization = {
            "schema_version": "contentops.canonical_machine_authorization.v1",
            "operating_mode": mode,
            "work_item_id": intent["work_item_id"],
            "package_identity": intent.get("package_identity"),
            "payload_hash": item.get("payload_hash"),
            "destination": destination,
            "policy_version": intent.get("policy_mode_version"),
            "dispatch_attempt_identity": ids["dispatch_id"],
        }
        registration = registration_for_destination(destination)
        self._record_runtime_activity(
            intent,
            "CANONICAL_DISPATCH" if destination == "substack" else "DERIVATIVE_DISPATCH",
            destination=destination,
        )
        try:
            activity = (
                browser_activity(
                    "PUBLICATION_ACTIVE",
                    reason="EXACT_DESTINATION_PUBLICATION",
                    destination=destination,
                )
                if registration.transport_type == "EDGE_CDP" else nullcontext()
            )
            with activity:
                raw = self.transport_runtime.publish(
                    destination=destination,
                    intent={**intent, "canonical_url": canonical_url or intent.get("canonical_url")},
                    authorization_context=authorization,
                )
            result = normalize_dispatch_result(
                raw or {}, destination=destination, surface=registration.surface,
                transport_type=registration.transport_type,
            )
        except Exception as exc:
            result = {
                "status": UNKNOWN_WRITE, "public_object_id": None,
                "public_object_url": None, "safe_error_classification": type(exc).__name__,
            }
        self.store.register_platform_dispatch(
            dispatch_id=ids["dispatch_id"], message_id=ids["message_id"],
            platform=destination, status=ATTEMPT_STARTED,
            public_object_id=result.get("public_object_id"),
            public_object_url=result.get("public_object_url"),
        )
        self.store.set_dispatch_status(ids["dispatch_id"], str(result["status"]))
        self.store.set_outbox_status(ids["message_id"], str(result["status"]))
        dispatch = self.store.get_platform_dispatch(ids["dispatch_id"])
        if result["status"] in {DISPATCH_CONFIRMED, UNKNOWN_WRITE}:
            reconciliation = self._reconcile(
                dispatch,
                intent,
                provider_outcome=result.get("provider_outcome"),
            )
        elif (
            result["status"] == DEFINITE_NO_WRITE
            and destination != "substack"
            and self._full_v1_distribution_required(intent)
        ):
            # A definite pre-write failure is a recoverable quality-probation derivative
            # obligation, not an ambiguity and not permission to abandon the destination.
            reconciliation = RECONCILED_ABSENT_SAFE_TO_RETRY
            self.store.set_dispatch_status(
                ids["dispatch_id"], RECONCILED_ABSENT_SAFE_TO_RETRY
            )
            self.store.set_outbox_status(
                ids["message_id"], RECONCILED_ABSENT_SAFE_TO_RETRY
            )
            self.store.register_reconciliation(
                reconciliation_id=ids["reconciliation_id"],
                work_item_id=str(intent["work_item_id"]),
                status=reconciliation,
            )
            self.store.set_reconciliation_status(
                ids["reconciliation_id"], reconciliation
            )
        else:
            reconciliation = RECONCILED_ABSENT_SAFE_TO_RETRY
        persisted = self.store.get_platform_dispatch(ids["dispatch_id"]) or dispatch
        return {
            "destination": destination, "status": str(persisted.get("status") or result["status"]),
            "publish_called": True,
            "public_object_id": persisted.get("public_object_id") or result.get("public_object_id"),
            "public_object_url": persisted.get("public_object_url") or result.get("public_object_url"),
            "reconciliation_status": reconciliation,
        }

    def _finalize_derivative_intent(
        self, message: Mapping[str, Any], *, canonical_url: str
    ) -> str:
        """Persist final canonical-URL-bound derivative bytes without dispatching them."""
        if str(message.get("destination") or "") == "substack":
            return "NOT_DERIVATIVE"
        intent = json.loads(str(message["payload"]))
        if intent.get("canonical_url") == canonical_url:
            return "READY"
        destination = str(message["destination"])
        try:
            finalizer = getattr(self.transport_runtime, "finalize_intent", None)
            if callable(finalizer):
                intent = dict(
                    finalizer(
                        destination=destination,
                        intent=intent,
                        canonical_url=canonical_url,
                    )
                )
            else:
                intent["canonical_url"] = canonical_url
            self.store.finalize_outbox_payload_before_dispatch(
                message_id=str(message["message_id"]),
                payload=_canonical_json(intent),
                status="READY",
            )
            return "READY"
        except Exception:
            self.store.set_outbox_status(
                str(message["message_id"]), "ASYNC_DERIVATIVE_FINALIZATION_FAILED"
            )
            return "ASYNC_DERIVATIVE_FINALIZATION_FAILED"

    def retry_reconciled_absent_substack(self, dispatch_id: str) -> dict[str, Any]:
        """Explicitly resume one exact Substack draft only after absent reconciliation.

        The existing exact dispatch, outbox payload, reconciliation state, and draft identity must
        all agree before the coordinator can cross the adapter boundary once.
        """
        dispatch = self.store.get_platform_dispatch(str(dispatch_id))
        if not dispatch:
            return {"status": "RETRY_BLOCKED_DISPATCH_NOT_FOUND", "publish_called": False}
        message = self.store.get_outbox_message(str(dispatch.get("message_id") or ""))
        if not message or str(message.get("destination") or "") != "substack":
            return {"status": "RETRY_BLOCKED_NOT_EXACT_SUBSTACK_OUTBOX", "publish_called": False}
        intent = json.loads(str(message["payload"]))
        work_item_id = str(intent.get("work_item_id") or "")
        if not self._full_v1_distribution_required(intent):
            return self._dispatch_message(
                message,
                canonical_url=None,
                explicit_reconciled_absent_retry=True,
            )
        intents = [
            json.loads(str(row["payload"]))
            for row in self.store.list_outbox_messages()
            if str(row.get("work_item_id") or "") == work_item_id
        ]
        retry_plan = {
            "plan_hash": intent.get("plan_hash"),
            "output_dir": intent.get("output_dir"),
            "quality_probation_policy_id": intent.get("quality_probation_policy_id"),
            "full_v1_distribution_required": intent.get("full_v1_distribution_required") is True,
            "destinations": [
                dict(row.get("destination_plan") or {}) for row in intents
            ],
            "skipped_derivative_destinations": [],
            "pre_substack_blockers": [],
        }
        quality_preflight = self._full_v1_distribution_preflight(
            work_item_id, retry_plan
        )
        if quality_preflight["status"] != CANONICAL_SUBSTACK_READY_DERIVATIVES_DEFERRED:
            return {
                "status": HOLD_FULL_V1_DISTRIBUTION_NOT_READY,
                "publish_called": False,
                "quality_preflight": quality_preflight,
            }
        unknown_write_count = sum(
            str(row.get("status") or "") == UNKNOWN_WRITE
            for row in self.store.list_platform_dispatches()
        )
        if unknown_write_count:
            return {
                "status": "RETRY_BLOCKED_UNKNOWN_WRITE_PRESENT",
                "publish_called": False,
                "unknown_write_count": unknown_write_count,
            }
        return self._dispatch_message(
            message,
            canonical_url=None,
            explicit_reconciled_absent_retry=True,
        )

    def complete_derivative_after_transport_correction(
        self, dispatch_id: str, *, correction_id: str
    ) -> dict[str, Any]:
        """Spend one explicit, durable correction budget for an exact incomplete derivative."""
        dispatch = self.store.get_platform_dispatch(str(dispatch_id))
        if not dispatch:
            return {
                "status": "CORRECTION_BLOCKED_DISPATCH_NOT_FOUND",
                "publish_called": False,
            }
        message = self.store.get_outbox_message(str(dispatch.get("message_id") or ""))
        destination = str((message or {}).get("destination") or "")
        if not message or destination not in {"x", "instagram_business"}:
            return {
                "status": "CORRECTION_BLOCKED_DESTINATION_NOT_AUTHORIZED",
                "publish_called": False,
            }
        normalized_correction_id = str(correction_id or "").strip()
        if not normalized_correction_id:
            return {
                "status": "CORRECTION_BLOCKED_ID_REQUIRED",
                "publish_called": False,
            }
        if self._transport_correction_already_attempted(
            str(dispatch_id), normalized_correction_id
        ):
            return {
                "status": "CORRECTION_ALREADY_ATTEMPTED_NO_WRITE",
                "publish_called": False,
            }
        intent = json.loads(str(message["payload"]))
        work_item_id = str(intent.get("work_item_id") or "")
        if not self._full_v1_distribution_required(intent):
            return {
                "status": "CORRECTION_BLOCKED_NOT_FULL_V1_OBLIGATION",
                "publish_called": False,
            }
        if self._message_is_stale(message, intent):
            return {
                "status": "CORRECTION_BLOCKED_DERIVATIVE_STALE",
                "publish_called": False,
            }
        canonical_url = self._confirmed_canonical_url_for_work_item(work_item_id) or ""
        if not canonical_url or str(intent.get("canonical_url") or "") != canonical_url:
            return {
                "status": "CORRECTION_BLOCKED_CANONICAL_IDENTITY_MISMATCH",
                "publish_called": False,
            }
        unknown_write_count = sum(
            str(row.get("status") or "") == UNKNOWN_WRITE
            for row in self.store.list_platform_dispatches()
        )
        if unknown_write_count:
            return {
                "status": "CORRECTION_BLOCKED_UNKNOWN_WRITE_PRESENT",
                "publish_called": False,
                "unknown_write_count": unknown_write_count,
            }
        intents = [
            json.loads(str(row["payload"]))
            for row in self.store.list_outbox_messages()
            if str(row.get("work_item_id") or "") == work_item_id
        ]
        correction_plan = {
            "plan_hash": intent.get("plan_hash"),
            "output_dir": intent.get("output_dir"),
            "quality_probation_policy_id": intent.get(
                "quality_probation_policy_id"
            ),
            "full_v1_distribution_required": True,
            "destinations": [
                dict(row.get("destination_plan") or {}) for row in intents
            ],
            "skipped_derivative_destinations": [],
            "pre_substack_blockers": [],
        }
        quality_preflight = self._full_v1_distribution_preflight(
            work_item_id, correction_plan
        )
        if quality_preflight["status"] != CANONICAL_SUBSTACK_READY_DERIVATIVES_DEFERRED:
            return {
                "status": HOLD_FULL_V1_DISTRIBUTION_NOT_READY,
                "publish_called": False,
                "quality_preflight": quality_preflight,
            }
        delivery_preparer = getattr(self.transport_runtime, "prepare_delivery_media", None)
        if callable(delivery_preparer):
            delivery = dict(
                delivery_preparer(
                    work_item_id=work_item_id,
                    plan=correction_plan,
                    preconditions={
                        "canonical_publication_status": RECONCILED_CONFIRMED,
                        "unknown_write_count": 0,
                    },
                )
                or {}
            )
            if str(delivery.get("status") or "") not in {
                "CLOUDINARY_DELIVERY_MEDIA_READY",
                "CLOUDINARY_DELIVERY_MEDIA_NOT_REQUIRED",
            }:
                return {
                    "status": str(
                        delivery.get("status")
                        or "CORRECTION_BLOCKED_DELIVERY_MEDIA_PREPARATION"
                    ),
                    "publish_called": False,
                    "delivery_media_preparation": delivery,
                }
        outcome = self._dispatch_message(
            message,
            canonical_url=canonical_url,
            explicit_transport_correction_retry=True,
            recovery_public_object_url=str(dispatch.get("public_object_url") or "")
            or None,
        )
        if outcome.get("publish_called") is True:
            self._record_transport_correction_attempt(
                str(dispatch_id), normalized_correction_id, work_item_id
            )
        return {**outcome, "correction_id": normalized_correction_id}

    def replay_persisted_verified_readback(self, dispatch_id: str) -> dict[str, Any]:
        """Restore monotonic confirmed state from an earlier durable verified readback."""
        dispatch = self.store.get_platform_dispatch(str(dispatch_id))
        if not dispatch:
            return {"status": "REPLAY_BLOCKED_DISPATCH_NOT_FOUND", "provider_calls": 0}
        object_id = str(dispatch.get("public_object_id") or "")
        message = self.store.get_outbox_message(str(dispatch.get("message_id") or ""))
        if not object_id or not message:
            return {"status": "REPLAY_BLOCKED_EXACT_IDENTITY_UNAVAILABLE", "provider_calls": 0}
        intent = json.loads(str(message["payload"]))
        ids = self._ids(
            str(intent["work_item_id"]),
            str(intent["plan_hash"]),
            str(dispatch["platform"]),
        )
        for row in reversed(self.store.list_readbacks_for_dispatch(str(dispatch_id))):
            try:
                payload = json.loads(str(row["readback_data"]))
                readback = dict(payload.get("readback") or {})
            except (TypeError, ValueError, KeyError):
                continue
            if not (
                readback.get("verified") is True
                and readback.get("identity_match") is True
                and str(readback.get("observed_public_object_id") or "") == object_id
            ):
                continue
            observed_url = str(readback.get("observed_public_object_url") or "") or None
            if str(dispatch["platform"]) == "substack" and not _valid_substack_canonical_url(
                observed_url
            ):
                continue
            self.store.register_platform_dispatch(
                dispatch_id=str(dispatch_id),
                message_id=str(dispatch["message_id"]),
                platform=str(dispatch["platform"]),
                status=DISPATCH_CONFIRMED,
                public_object_id=object_id,
                public_object_url=observed_url,
            )
            self.store.set_dispatch_status(str(dispatch_id), DISPATCH_CONFIRMED)
            self.store.set_outbox_status(str(dispatch["message_id"]), DISPATCH_CONFIRMED)
            self.store.register_reconciliation(
                reconciliation_id=ids["reconciliation_id"],
                work_item_id=str(intent["work_item_id"]),
                status=RECONCILED_CONFIRMED,
            )
            self.store.set_reconciliation_status(
                ids["reconciliation_id"], RECONCILED_CONFIRMED
            )
            return {"status": RECONCILED_CONFIRMED, "provider_calls": 0}
        return {"status": "REPLAY_VERIFIED_READBACK_NOT_FOUND", "provider_calls": 0}

    def execute_plan(self, work_item_id: str, plan: Mapping[str, Any]) -> dict[str, Any]:
        if self._recovery_is_quarantined(work_item_id):
            return {
                "plan_hash": str(plan.get("plan_hash") or _hash(_canonical_json(plan))),
                "registered": [],
                "outbox_count": 0,
                "per_destination": {},
                "canonical_article_status": "NOT_STARTED",
                "canonical_article_real_published": False,
                "canonical_url": None,
                "canonical_publication_status": "BLOCKED_RECOVERY_QUARANTINED_WORK_ITEM",
                "distribution_status": "BLOCKED_RECOVERY_QUARANTINED_WORK_ITEM",
                "public_write_performed": False,
                "unknown_write_detected": True,
            }
        recovery_preflight = self.recover_pending()
        if int(recovery_preflight.get("backlog_remaining") or 0) > 0:
            return {
                "plan_hash": str(plan.get("plan_hash") or _hash(_canonical_json(plan))),
                "registered": [],
                "outbox_count": 0,
                "per_destination": {},
                "canonical_article_status": "NOT_STARTED",
                "canonical_article_real_published": False,
                "canonical_url": None,
                "canonical_publication_status": "BLOCKED_SAFE_RECOVERY_BACKLOG_REMAINS",
                "distribution_status": "BLOCKED_SAFE_RECOVERY_BACKLOG_REMAINS",
                "recovery_preflight": recovery_preflight,
                "public_write_performed": bool(
                    recovery_preflight.get("publish_calls")
                ),
                "unknown_write_detected": False,
            }
        quality_preflight = None
        if self._full_v1_distribution_required(plan):
            quality_preflight = self._full_v1_distribution_preflight(work_item_id, plan)
            if quality_preflight["status"] != CANONICAL_SUBSTACK_READY_DERIVATIVES_DEFERRED:
                return {
                    "plan_hash": str(
                        plan.get("plan_hash") or _hash(_canonical_json(plan))
                    ),
                    "registered": [],
                    "outbox_count": 0,
                    "per_destination": quality_preflight["per_destination"],
                    "canonical_article_status": "NOT_STARTED",
                    "canonical_article_real_published": False,
                    "canonical_url": None,
                    "canonical_publication_status": HOLD_FULL_V1_DISTRIBUTION_NOT_READY,
                    "distribution_status": HOLD_FULL_V1_DISTRIBUTION_NOT_READY,
                    "transaction_classification": HOLD_FULL_V1_DISTRIBUTION_NOT_READY,
                    "quality_preflight": quality_preflight,
                    "recovery_preflight": recovery_preflight,
                    "current_transaction_public_write_performed": False,
                    "public_write_performed": bool(
                        recovery_preflight.get("publish_calls")
                    ),
                    "unknown_write_detected": False,
                }
        delivery_media_preparation: dict[str, Any] = {
            "status": "DELIVERY_MEDIA_PREPARATION_NOT_REQUIRED_BY_TRANSPORT",
            "provider_calls": 0,
            "public_write_performed": False,
        }
        registration = self.register_plan(work_item_id, plan)
        outcomes: dict[str, Any] = {
            str(row.get("destination") or ""): {
                **dict(row),
                "status": str(row.get("disposition") or "SKIPPED_NOT_READY"),
                "publish_called": False,
                "reconciliation_status": None,
            }
            for row in (plan.get("skipped_derivative_destinations") or [])
            if isinstance(row, Mapping) and str(row.get("destination") or "")
        }
        canonical_url: Optional[str] = None
        messages = [m for m in self.store.list_outbox_messages() if m["work_item_id"] == work_item_id]
        messages.sort(key=lambda m: (0 if m["destination"] == "substack" else 1, m["destination"]))
        canonical_message = next(
            (message for message in messages if message["destination"] == "substack"),
            None,
        )
        if canonical_message is not None:
            outcome = self._dispatch_message(canonical_message, canonical_url=None)
            outcomes["substack"] = outcome
            if (
                outcome.get("status") == DISPATCH_CONFIRMED
                and outcome.get("reconciliation_status") == RECONCILED_CONFIRMED
                and _valid_substack_canonical_url(outcome.get("public_object_url"))
            ):
                canonical_url = str(outcome["public_object_url"])
        delivery_preparer = getattr(self.transport_runtime, "prepare_delivery_media", None)
        if canonical_url and callable(delivery_preparer) and quality_preflight is not None:
            unknown_write_count = self._active_unknown_write_count()
            delivery_media_preparation = dict(
                delivery_preparer(
                    work_item_id=work_item_id,
                    plan=plan,
                    preconditions={
                        "canonical_publication_status": RECONCILED_CONFIRMED,
                        "unknown_write_count": unknown_write_count,
                    },
                )
                or {}
            )
        delivery_media_blocked = str(
            delivery_media_preparation.get("status") or ""
        ) not in {
            "DELIVERY_MEDIA_PREPARATION_NOT_REQUIRED_BY_TRANSPORT",
            "CLOUDINARY_DELIVERY_MEDIA_READY",
            "CLOUDINARY_DELIVERY_MEDIA_NOT_REQUIRED",
        }
        for message in messages:
            if message["destination"] == "substack":
                continue
            intent = json.loads(str(message["payload"]))
            destination_plan = dict(intent.get("destination_plan") or {})
            if delivery_media_blocked and destination_plan.get(
                "delivery_media_required"
            ) is True:
                outcomes[str(message["destination"])] = {
                    "destination": str(message["destination"]),
                    "status": str(
                        delivery_media_preparation.get("status")
                        or "DESTINATION_LOCAL_DELIVERY_MEDIA_HOLD"
                    ),
                    "publish_called": False,
                    "reconciliation_status": None,
                    "destination_local_hold": True,
                }
                continue
            if canonical_message is None:
                outcomes[str(message["destination"])] = self._dispatch_message(
                    message, canonical_url=intent.get("canonical_url")
                )
                continue
            existing = self.store.get_platform_dispatch(
                self._ids(work_item_id, registration["plan_hash"], str(message["destination"]))[
                    "dispatch_id"
                ]
            )
            if existing is not None:
                outcomes[str(message["destination"])] = self._dispatch_message(
                    message, canonical_url=canonical_url
                )
                continue
            if canonical_url:
                queued_status = self._finalize_derivative_intent(
                    message, canonical_url=canonical_url
                )
                if queued_status == "READY":
                    # The same scheduled opportunity must drive one bounded attempt for every
                    # currently READY destination. Destination-local failure never blocks the
                    # remaining fanout and never revokes confirmed canonical truth.
                    refreshed = self.store.get_outbox_message(str(message["message_id"])) or message
                    outcomes[str(message["destination"])] = self._dispatch_message(
                        refreshed, canonical_url=canonical_url
                    )
                else:
                    outcomes[str(message["destination"])] = {
                        "destination": str(message["destination"]),
                        "status": queued_status,
                        "publish_called": False,
                        "reconciliation_status": None,
                    }
            else:
                outcomes[str(message["destination"])] = {
                    "destination": str(message["destination"]),
                    "status": "WAITING_CANONICAL_URL",
                    "publish_called": False,
                    "reconciliation_status": None,
                }
        canonical = dict(outcomes.get("substack") or {})
        canonical_real = bool(
            canonical.get("status") == DISPATCH_CONFIRMED
            and canonical.get("reconciliation_status") == RECONCILED_CONFIRMED
            and _valid_substack_canonical_url(canonical.get("public_object_url"))
        )
        derivatives = {
            destination: outcome
            for destination, outcome in outcomes.items()
            if destination != "substack"
        }
        full_distribution_required = self._full_v1_distribution_required(plan)
        derivative_confirmed = sum(
            self._confirmed_public_object(outcome, destination=destination)
            if full_distribution_required
            else (
                outcome.get("status") == DISPATCH_CONFIRMED
                and outcome.get("reconciliation_status") == RECONCILED_CONFIRMED
            )
            for destination, outcome in derivatives.items()
        )
        derivative_attempted = sum(
            outcome.get("publish_called") is True for outcome in derivatives.values()
        )
        derivative_unknown = sum(
            outcome.get("status") == UNKNOWN_WRITE for outcome in derivatives.values()
        )
        derivative_skipped = sum(
            outcome.get("publish_called") is not True
            and not (
                self._confirmed_public_object(outcome, destination=destination)
                if full_distribution_required
                else (
                    outcome.get("status") == DISPATCH_CONFIRMED
                    and outcome.get("reconciliation_status") == RECONCILED_CONFIRMED
                )
            )
            for destination, outcome in derivatives.items()
        )
        derivative_failed = sum(
            outcome.get("publish_called") is True
            and outcome.get("status") not in {DISPATCH_CONFIRMED, UNKNOWN_WRITE}
            for outcome in derivatives.values()
        )
        recovery_destinations = sorted(
            destination
            for destination in V1_REQUIRED_DERIVATIVE_DESTINATIONS
            if full_distribution_required
            and not self._confirmed_public_object(
                derivatives.get(destination) or {}, destination=destination
            )
        )
        readback_limitation_destinations = sorted(
            destination
            for destination, outcome in derivatives.items()
            if outcome.get("reconciliation_status")
            == RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE
        )
        if canonical_real and full_distribution_required:
            distribution_status = (
                FULL_V1_NINE_SURFACE_PUBLICATION_CONFIRMED
                if not recovery_destinations and len(derivatives) == 8
                else PARTIAL_DISTRIBUTION_RECOVERY_REQUIRED
            )
        elif canonical_real:
            distribution_status = (
                "CANONICAL_PUBLISHED_DISTRIBUTION_COMPLETE"
                if derivatives
                and derivative_confirmed == len(derivatives)
                else "CANONICAL_PUBLISHED_READY_FANOUT_ATTEMPTED"
            )
        else:
            distribution_status = "CANONICAL_NOT_CONFIRMED"
        return {
            **registration,
            "per_destination": outcomes,
            "canonical_article_status": "REAL_PUBLISHED" if canonical_real else "NOT_CONFIRMED",
            "canonical_article_real_published": canonical_real,
            "canonical_url": canonical_url if canonical_real else None,
            "canonical_publication_status": distribution_status,
            "distribution_status": distribution_status,
            "transaction_classification": distribution_status,
            "quality_preflight": quality_preflight,
            "delivery_media_preparation": delivery_media_preparation,
            "recovery_required_destinations": recovery_destinations,
            "readback_limitation_destinations": readback_limitation_destinations,
            "metrics_availability_independent_from_publication_confirmation": True,
            "derivative_attempted_count": derivative_attempted,
            "derivative_confirmed_count": derivative_confirmed,
            "derivative_skipped_count": derivative_skipped,
            "derivative_failed_count": derivative_failed,
            "derivative_unknown_count": derivative_unknown,
            "public_write_performed": any(
                o.get("status") == DISPATCH_CONFIRMED and o.get("publish_called") is True
                for o in outcomes.values()
            ),
            "unknown_write_detected": any(o.get("status") == UNKNOWN_WRITE for o in outcomes.values()),
        }

    def _confirmed_canonical_url_for_work_item(self, work_item_id: str) -> Optional[str]:
        for message in self.store.list_outbox_messages():
            if str(message.get("work_item_id") or "") != work_item_id or str(
                message.get("destination") or ""
            ) != "substack":
                continue
            dispatch = self.store.get_platform_dispatch(
                "dispatch_" + str(message["message_id"]).removeprefix("outbox_")
            )
            if not dispatch or str(dispatch.get("status") or "") != DISPATCH_CONFIRMED:
                continue
            url = str(dispatch.get("public_object_url") or "")
            if not _valid_substack_canonical_url(url):
                continue
            expected = "reconciliation_" + str(dispatch["dispatch_id"]).removeprefix("dispatch_")
            reconciliation = next((
                row for row in self.store.get_reconciliations_for_work_item(work_item_id)
                if str(row.get("reconciliation_id") or "") == expected
            ), None)
            if reconciliation and str(reconciliation.get("status") or "") == RECONCILED_CONFIRMED:
                return url
        return None

    def recover_pending(self) -> dict[str, Any]:
        """Reconcile every ambiguity, then spend one bounded freshness-safe recovery budget."""
        summary = {
            "safe_resumes": 0, "safely_attempted": 0, "stale_expired": 0,
            "marked_unknown": 0, "readbacks": 0, "publish_calls": 0,
            "readiness_probe_performed": False, "per_destination": {},
            "recovery_attempt_budget": RECOVERY_ATTEMPT_BUDGET,
            "backlog_remaining": 0,
        }
        messages = self.store.list_outbox_messages()
        dispatch_by_message = {str(d["message_id"]): d for d in self.store.list_platform_dispatches()}
        ready_messages: list[tuple[Mapping[str, Any], bool]] = []
        quarantined_obligations: set[tuple[str, str, str]] = set()
        for message in messages:
            intent = json.loads(str(message["payload"]))
            if not intent.get("work_item_id") or not intent.get("plan_hash"):
                summary["legacy_noncanonical_rows_skipped"] = int(
                    summary.get("legacy_noncanonical_rows_skipped") or 0
                ) + 1
                continue
            if self._recovery_is_quarantined(intent.get("work_item_id")):
                dispatch = dispatch_by_message.get(str(message["message_id"]))
                quarantined_obligations.add(
                    (
                        str(intent["work_item_id"]),
                        str(message["destination"]),
                        str((dispatch or {}).get("status") or message.get("status") or ""),
                    )
                )
                continue
            dispatch = dispatch_by_message.get(str(message["message_id"]))
            if dispatch is None and str(message["status"]) == "READY":
                if (
                    str(message["destination"]) != "substack"
                    and self._message_is_stale(message, intent)
                ):
                    self._expire_stale_derivative(message, None)
                    summary["stale_expired"] += 1
                    continue
                ready_messages.append((message, False))
                continue
            if dispatch is None:
                continue
            status = str(dispatch["status"])
            ids = self._ids(
                str(intent["work_item_id"]),
                str(intent["plan_hash"]),
                str(message["destination"]),
            )
            reconciliations = self.store.get_reconciliations_for_work_item(
                str(intent["work_item_id"])
            )
            current_reconciliation = next(
                (
                    str(row.get("status") or "")
                    for row in reconciliations
                    if str(row.get("reconciliation_id") or "")
                    == ids["reconciliation_id"]
                ),
                None,
            )
            if current_reconciliation == RECONCILED_ABSENT_SAFE_TO_RETRY:
                # A strict readback proved absence. Preserve the same logical dispatch identity
                # and allow one explicit bounded retry for a destination-local derivative in
                # this recovery pass. Substack requires its narrower operator-authorized
                # ``retry_reconciled_absent_substack`` route because a preserved draft ID may
                # be deliberately non-public.
                if str(message["destination"]) != "substack":
                    if self._retry_already_attempted(str(dispatch["dispatch_id"])):
                        self.store.set_dispatch_status(
                            str(dispatch["dispatch_id"]),
                            DERIVATIVE_RECOVERY_RETRY_EXHAUSTED_NO_WRITE,
                        )
                        self.store.set_outbox_status(
                            str(message["message_id"]),
                            DERIVATIVE_RECOVERY_RETRY_EXHAUSTED_NO_WRITE,
                        )
                    elif self._message_is_stale(message, intent):
                        self._expire_stale_derivative(message, dispatch)
                        summary["stale_expired"] += 1
                    else:
                        ready_messages.append((message, True))
                continue
            if current_reconciliation in {
                RECONCILED_CONFIRMED,
                RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE,
            }:
                continue
            if status == ATTEMPT_STARTED:
                self.store.set_dispatch_status(str(dispatch["dispatch_id"]), UNKNOWN_WRITE)
                self.store.set_outbox_status(str(message["message_id"]), UNKNOWN_WRITE)
                dispatch = self.store.get_platform_dispatch(str(dispatch["dispatch_id"]))
                summary["marked_unknown"] += 1
                status = UNKNOWN_WRITE
            if status in {UNKNOWN_WRITE, DISPATCH_CONFIRMED}:
                self._reconcile(dispatch, intent)
                summary["readbacks"] += 1
        if ready_messages:
            ready_messages.sort(
                key=lambda entry: (
                    str(entry[0].get("work_item_id") or ""),
                    0 if str(entry[0]["destination"]) == "substack" else 1,
                    str(entry[0]["destination"]),
                )
            )
            canonical_urls: dict[str, str] = {}
            delivery_media_by_work_item: dict[str, dict[str, Any]] = {}
            for message, explicit_retry in ready_messages[:RECOVERY_ATTEMPT_BUDGET]:
                work_item_id = str(message.get("work_item_id") or "")
                intent = json.loads(str(message["payload"]))
                destination = str(message["destination"])
                canonical_url = canonical_urls.get(work_item_id) or str(
                    intent.get("canonical_url") or ""
                )
                if not canonical_url:
                    canonical_url = self._confirmed_canonical_url_for_work_item(work_item_id) or ""
                if destination != "substack" and not canonical_url:
                    summary["per_destination"][destination] = {
                        "status": "WAITING_CANONICAL_URL",
                        "publish_called": False,
                    }
                    continue
                if destination != "substack":
                    finalized = self._finalize_derivative_intent(
                        message, canonical_url=canonical_url
                    )
                    if finalized != "READY":
                        summary["per_destination"][destination] = {
                            "status": finalized,
                            "publish_called": False,
                        }
                        continue
                    message = self.store.get_outbox_message(str(message["message_id"])) or message
                    intent = json.loads(str(message["payload"]))
                    destination_plan = dict(intent.get("destination_plan") or {})
                    if destination_plan.get("delivery_media_required") is True:
                        delivery = delivery_media_by_work_item.get(work_item_id)
                        if delivery is None:
                            preparer = getattr(
                                self.transport_runtime, "prepare_delivery_media", None
                            )
                            if callable(preparer):
                                work_item_intents = [
                                    json.loads(str(row["payload"]))
                                    for row in self.store.list_outbox_messages()
                                    if str(row.get("work_item_id") or "") == work_item_id
                                ]
                                recovery_plan = {
                                    "plan_hash": intent.get("plan_hash"),
                                    "output_dir": intent.get("output_dir"),
                                    "quality_probation_policy_id": intent.get(
                                        "quality_probation_policy_id"
                                    ),
                                    "full_v1_distribution_required": (
                                        intent.get("full_v1_distribution_required") is True
                                    ),
                                    "destinations": [
                                        dict(row.get("destination_plan") or {})
                                        for row in work_item_intents
                                    ],
                                    "skipped_derivative_destinations": [],
                                    "pre_substack_blockers": [],
                                }
                                unknown_count = sum(
                                    str(row.get("status") or "") == UNKNOWN_WRITE
                                    for row in self.store.list_platform_dispatches()
                                )
                                if unknown_count:
                                    delivery = {
                                        "status": "DELIVERY_MEDIA_RECOVERY_BLOCKED_UNKNOWN_WRITE",
                                        "unknown_write_count": unknown_count,
                                        "public_write_performed": False,
                                    }
                                else:
                                    delivery = dict(
                                        preparer(
                                            work_item_id=work_item_id,
                                            plan=recovery_plan,
                                            preconditions={
                                                "canonical_publication_status": (
                                                    RECONCILED_CONFIRMED
                                                ),
                                                "unknown_write_count": 0,
                                            },
                                        )
                                        or {}
                                    )
                            else:
                                delivery = {
                                    "status": (
                                        "DELIVERY_MEDIA_PREPARATION_NOT_REQUIRED_BY_TRANSPORT"
                                    ),
                                    "public_write_performed": False,
                                }
                            delivery_media_by_work_item[work_item_id] = delivery
                        if str(delivery.get("status") or "") not in {
                            "DELIVERY_MEDIA_PREPARATION_NOT_REQUIRED_BY_TRANSPORT",
                            "CLOUDINARY_DELIVERY_MEDIA_READY",
                            "CLOUDINARY_DELIVERY_MEDIA_NOT_REQUIRED",
                        }:
                            summary["per_destination"][destination] = {
                                "destination": destination,
                                "status": str(
                                    delivery.get("status")
                                    or "DESTINATION_LOCAL_DELIVERY_MEDIA_HOLD"
                                ),
                                "publish_called": False,
                                "destination_local_hold": True,
                                "delivery_media_preparation": delivery,
                            }
                            continue
                outcome = self._dispatch_message(
                    message,
                    canonical_url=canonical_url or None,
                    explicit_reconciled_absent_retry=explicit_retry,
                )
                summary["per_destination"][destination] = outcome
                summary["safe_resumes"] += 1
                summary["safely_attempted"] += 1
                summary["publish_calls"] += int(bool(outcome.get("publish_called")))
                if explicit_retry and outcome.get("publish_called") is True:
                    dispatch = self.store.get_platform_dispatch(
                        self._ids(
                            str(intent["work_item_id"]),
                            str(intent["plan_hash"]), destination,
                        )["dispatch_id"]
                    )
                    if dispatch is not None:
                        self._record_retry_attempt(
                            str(dispatch["dispatch_id"]), work_item_id
                        )
                if (
                    destination == "substack"
                    and outcome.get("status") == DISPATCH_CONFIRMED
                    and outcome.get("reconciliation_status") == RECONCILED_CONFIRMED
                    and _valid_substack_canonical_url(outcome.get("public_object_url"))
                ):
                    canonical_urls[work_item_id] = str(outcome["public_object_url"])
        remaining_destinations: list[str] = []
        remaining_obligations: list[dict[str, str]] = []
        refreshed_dispatches = {
            str(row["message_id"]): row for row in self.store.list_platform_dispatches()
        }
        for message in self.store.list_outbox_messages():
            try:
                intent = json.loads(str(message["payload"]))
            except (TypeError, ValueError, KeyError):
                continue
            if not intent.get("work_item_id") or not intent.get("plan_hash"):
                # The recovery pass above deliberately excludes pre-coordinator legacy rows.
                # Do not reintroduce those same noncanonical rows as fresh-publication blockers
                # while computing the terminal backlog summary.
                continue
            if self._recovery_is_quarantined(intent.get("work_item_id")):
                continue
            dispatch = refreshed_dispatches.get(str(message["message_id"]))
            destination = str(message["destination"])
            if (
                self._full_v1_distribution_required(intent)
                and destination in V1_REQUIRED_DERIVATIVE_DESTINATIONS
            ):
                terminal_statuses = {
                    DERIVATIVE_EXPIRED_STALE_NO_WRITE,
                    DERIVATIVE_RECOVERY_RETRY_EXHAUSTED_NO_WRITE,
                }
                durable_status = str(
                    (dispatch or {}).get("status") or message.get("status") or ""
                )
                if durable_status in terminal_statuses:
                    continue
                reconciliation = None
                if dispatch is not None:
                    ids = self._ids(
                        str(intent["work_item_id"]),
                        str(intent["plan_hash"]),
                        destination,
                    )
                    reconciliation = next((
                        str(row.get("status") or "")
                        for row in self.store.get_reconciliations_for_work_item(
                            str(intent["work_item_id"])
                        )
                        if str(row.get("reconciliation_id") or "")
                        == ids["reconciliation_id"]
                    ), None)
                confirmed = bool(
                    dispatch is not None
                    and str(dispatch.get("status") or "") == DISPATCH_CONFIRMED
                    and str(dispatch.get("public_object_id") or "")
                    and reconciliation in _PUBLICATION_CONFIRMED_RECONCILIATIONS
                )
                if not confirmed:
                    latest_outcome = dict(
                        summary["per_destination"].get(destination) or {}
                    )
                    remaining_destinations.append(destination)
                    remaining_obligations.append({
                        "work_item_id": str(intent.get("work_item_id") or ""),
                        "destination": destination,
                        "durable_status": durable_status or "MISSING_DISPATCH",
                        "blocking_status": str(
                            latest_outcome.get("status")
                            or durable_status
                            or "MISSING_DISPATCH"
                        ),
                        "reconciliation_status": str(reconciliation or ""),
                    })
                continue
            if dispatch is None:
                if str(message.get("status") or "") == "READY":
                    remaining_destinations.append(destination)
                continue
            if destination == "substack":
                continue
            if str(dispatch.get("status") or "") in {
                DERIVATIVE_EXPIRED_STALE_NO_WRITE,
                DERIVATIVE_RECOVERY_RETRY_EXHAUSTED_NO_WRITE,
            }:
                continue
            if not intent.get("work_item_id") or not intent.get("plan_hash"):
                continue
            ids = self._ids(
                str(intent["work_item_id"]), str(intent["plan_hash"]),
                str(message["destination"]),
            )
            reconciliation = next((
                str(row.get("status") or "")
                for row in self.store.get_reconciliations_for_work_item(
                    str(intent["work_item_id"])
                )
                if str(row.get("reconciliation_id") or "") == ids["reconciliation_id"]
            ), None)
            if (
                reconciliation == RECONCILED_ABSENT_SAFE_TO_RETRY
                and not self._retry_already_attempted(str(dispatch["dispatch_id"]))
            ):
                remaining_destinations.append(str(message["destination"]))
        summary["backlog_remaining"] = len(remaining_destinations)
        summary["backlog_remaining_by_destination"] = sorted(remaining_destinations)
        summary["backlog_remaining_obligations"] = sorted(
            remaining_obligations,
            key=lambda row: (row["work_item_id"], row["destination"]),
        )
        summary["recovery_quarantined_obligations"] = [
            {
                "work_item_id": work_item_id,
                "destination": destination,
                "durable_status": durable_status,
            }
            for work_item_id, destination, durable_status in sorted(
                quarantined_obligations
            )
        ]
        summary["recovery_quarantined_obligation_count"] = len(
            quarantined_obligations
        )
        summary["backlog_blocking_new_publication"] = bool(remaining_destinations)
        return summary

    def publish_plan(self, work_item_id: str, plan: Mapping[str, Any]) -> dict[str, Any]:
        return self.execute_plan(work_item_id, plan)

    def readback(self, *args: Any, **kwargs: Any) -> Mapping[str, Any]:
        """Production wiring seam: readback is owned by this coordinator/router."""
        return self.transport_runtime.readback(*args, **kwargs)

    def collect_metrics(self, *args: Any, **kwargs: Any) -> Mapping[str, Any]:
        """Resolve one exact durable public object before destination-local read-only collection."""
        dispatch_id = str(args[0] if len(args) > 0 else kwargs.get("dispatch_id") or "")
        public_object_id = str(args[1] if len(args) > 1 else kwargs.get("public_object_id") or "")
        observation_window = str(
            args[2] if len(args) > 2 else kwargs.get("observation_window") or ""
        )
        unavailable = {
            "status": "UNAVAILABLE",
            "metrics": {},
            "availability": {name: "UNAVAILABLE" for name in (
                "total_views", "free_subscriptions", "paid_subscriptions", "recipients",
                "open_rate", "delivery_rate", "likes", "comments", "shares", "restacks",
                "reposts", "subscriber_conversions", "meaningful_reads", "completion_rate",
            )},
            "source_identity": "contentops.destination_metrics_router.v1",
            "limitations": ["exact_confirmed_reconciled_public_object_required"],
        }
        dispatch = self.store.get_platform_dispatch(dispatch_id)
        if not dispatch:
            return unavailable
        if (
            str(dispatch.get("status") or "") != DISPATCH_CONFIRMED
            or str(dispatch.get("public_object_id") or "") != public_object_id
        ):
            return unavailable
        message = self.store.get_outbox_message(str(dispatch["message_id"]))
        if not message:
            return unavailable
        expected_reconciliation_id = "reconciliation_" + dispatch_id.removeprefix("dispatch_")
        reconciliation = next((
            row for row in self.store.get_reconciliations_for_work_item(str(message["work_item_id"]))
            if str(row.get("reconciliation_id") or "") == expected_reconciliation_id
        ), None)
        if not reconciliation or str(reconciliation.get("status") or "") != RECONCILED_CONFIRMED:
            return unavailable
        public_object_url = str(dispatch.get("public_object_url") or "")
        if str(dispatch.get("platform") or "") == "substack":
            if (
                not _valid_substack_canonical_url(public_object_url)
                or str(dispatch.get("public_object_url_hash") or "") != _hash(public_object_url)
            ):
                return unavailable
        collector = getattr(self.transport_runtime, "collect_metrics", None)
        if not callable(collector):
            return unavailable
        destination = str(dispatch["platform"])
        if destination == "substack" and self.readiness_manager is not None:
            try:
                self.readiness_manager.ensure_destination_runtime_for_readback(destination)
            except Exception as exc:
                return {
                    **unavailable,
                    "status": "AUTH_REQUIRED",
                    "availability": {name: "AUTH_REQUIRED" for name in (
                        "total_views", "free_subscriptions", "paid_subscriptions", "recipients",
                        "open_rate", "delivery_rate", "likes", "comments", "shares", "restacks",
                        "reposts", "subscriber_conversions", "meaningful_reads", "completion_rate",
                    )},
                    "limitations": [f"canonical_edge_readiness:{type(exc).__name__}"],
                }
        with browser_activity(
            "PERFORMANCE_OBSERVATION_ACTIVE",
            reason="DUE_DESTINATION_LOCAL_PERFORMANCE_OBSERVATION",
            destination=destination,
        ):
            return collector(
                destination=destination,
                dispatch_id=dispatch_id,
                public_object_id=public_object_id,
                public_object_url=public_object_url,
                public_object_url_hash=str(dispatch.get("public_object_url_hash") or "") or None,
                observation_window=observation_window,
            )


class CanonicalDestinationTransportRuntimeV1:
    """Single coordinator transport router; LinkedIn is official-member API only."""

    def __init__(self, *, linkedin_transport: Any = None) -> None:
        self._strict_publish_readbacks: dict[tuple[str, str], Mapping[str, Any]] = {}
        if linkedin_transport is None:
            from live_contentops.linkedin_official_member_api_v1 import (
                LinkedInOfficialMemberApiTransportV1,
            )
            linkedin_transport = LinkedInOfficialMemberApiTransportV1()
        self._linkedin_transport = linkedin_transport

    def prepare_delivery_media(
        self,
        *,
        work_item_id: str,
        plan: Mapping[str, Any],
        preconditions: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import (
            _prepare_cloudinary_delivery_media_for_plan,
        )

        return _prepare_cloudinary_delivery_media_for_plan(
            work_item_id=work_item_id,
            plan=plan,
            preconditions=preconditions,
        )

    def publish(self, *, destination: str, intent: Mapping[str, Any],
                authorization_context: Mapping[str, Any]) -> Mapping[str, Any]:
        if destination == "linkedin":
            return self._linkedin_transport.publish(
                intent=intent, authorization_context=authorization_context,
            )
        from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import (
            _publish_one_destination_from_durable_intent,
        )
        result = _publish_one_destination_from_durable_intent(
            destination=destination, intent=intent,
            authorization_context=authorization_context,
        )
        object_id = next((str(result.get(key)) for key in (
            "public_object_id", "post_id", "message_id", "media_id", "id", "activity_id", "draft_id",
        ) if result.get(key) not in (None, "")), None)
        if object_id and (
            result.get("provider_readback_verified") is True
            or result.get("strict_readback_verified") is True
            or str((result.get("readback") or {}).get("status") if isinstance(result.get("readback"), Mapping) else "").upper() == "SUCCESS"
        ):
            self._strict_publish_readbacks[(destination, object_id)] = dict(result)
        return result

    def finalize_intent(self, *, destination: str, intent: Mapping[str, Any],
                        canonical_url: str) -> Mapping[str, Any]:
        from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import (
            _durable_intent_inputs,
        )
        finalized = dict(intent)
        finalized["canonical_url"] = canonical_url
        data = _durable_intent_inputs(finalized)
        native_payload = dict(data["payloads"].get(destination) or {})
        payload = str(native_payload.get("text") or "")
        destination_plan = dict(finalized["destination_plan"])
        destination_plan["payload_hash"] = _hash(_canonical_json(native_payload))
        destination_plan["payload_hash_kind"] = "FINAL_CANONICAL_URL_BOUND_BYTES"
        destination_plan["canonical_url_state"] = "RECONCILED_CANONICAL_URL_BOUND"
        finalized["destination_plan"] = destination_plan
        finalized["payload"] = payload
        finalized["native_payload"] = native_payload
        finalized["rematerialization_model_call_count"] = 0
        finalized["rematerialization_source_get_count"] = 0
        return finalized

    def readback(self, *, destination: str, public_object_id: Optional[str],
                 public_object_url: Optional[str], intent: Mapping[str, Any]) -> Mapping[str, Any]:
        if destination == "linkedin":
            return self._linkedin_transport.readback(
                public_object_id=public_object_id,
                public_object_url=public_object_url,
                intent=intent,
            )
        cached = self._strict_publish_readbacks.get((destination, str(public_object_id or "")))
        if cached is not None:
            return {
                "status": "SUCCESS", "verified": True,
                "public_object_id": public_object_id,
                "public_object_url": public_object_url,
                "readback_source": "STRICT_PROVIDER_OR_BROWSER_RESULT_FROM_CURRENT_ATTEMPT",
            }
        from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import (
            _readback_one_destination_from_durable_intent,
        )
        return _readback_one_destination_from_durable_intent(
            destination=destination, public_object_id=public_object_id,
            public_object_url=public_object_url, intent=intent,
        )

    def collect_metrics(
        self,
        *,
        destination: str,
        dispatch_id: str,
        public_object_id: str,
        public_object_url: str,
        public_object_url_hash: Optional[str],
        observation_window: str,
    ) -> Mapping[str, Any]:
        if destination == "linkedin":
            return self._linkedin_transport.collect_metrics(
                public_object_id=public_object_id
            )
        if destination != "substack":
            from live_contentops.destination_performance_observer_v1 import (
                collect_current_authorized_destination_metrics,
            )

            return collect_current_authorized_destination_metrics(
                destination=destination, public_object_id=public_object_id
            )
        from live_contentops.substack_performance_observer_v1 import (
            collect_substack_post_metrics_via_edge,
        )

        return collect_substack_post_metrics_via_edge(
            cdp_port=9223,
            public_object_id=public_object_id,
            canonical_public_url=public_object_url,
        )


# Compatibility import only. Runtime composition uses the canonical name above; the alias does
# not restore or route LinkedIn to the historical CDP implementation.
HistoricalAdapterTransportRuntime = CanonicalDestinationTransportRuntimeV1
