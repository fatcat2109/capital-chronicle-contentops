"""Single durable Final Daily App public-write owner.

The newsroom produces deterministic publication plans.  This coordinator persists exact
pre-write intent, records ``DISPATCH_ATTEMPT_STARTED`` before crossing any API/CDP boundary,
routes through the versioned transport registry, and owns strict readback/reconciliation.
There is deliberately no transport fallback and no automatic retry from UNKNOWN_WRITE.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from live_contentops.destination_transport_registry_v1 import (
    READY_STATES,
    REGISTRY_VERSION,
    registration_for_destination,
)


ATTEMPT_STARTED = "DISPATCH_ATTEMPT_STARTED"
DISPATCH_CONFIRMED = "DISPATCH_CONFIRMED"
UNKNOWN_WRITE = "UNKNOWN_WRITE"
DEFINITE_NO_WRITE = "DEFINITE_NO_WRITE"
RECONCILED_CONFIRMED = "RECONCILED_CONFIRMED"
RECONCILIATION_PENDING = "RECONCILIATION_PENDING"
RECONCILED_ABSENT_SAFE_TO_RETRY = "RECONCILED_ABSENT_SAFE_TO_RETRY"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True, default=str)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


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
    return {
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


def normalize_readback_result(
    result: Mapping[str, Any], *, public_object_id: Optional[str]
) -> dict[str, Any]:
    raw = dict(result or {})
    observed_id = next((str(raw.get(k)) for k in (
        "public_object_id", "post_id", "message_id", "media_id", "id", "activity_id",
        "root_post_id",
    ) if raw.get(k) not in (None, "")), None)
    absent = raw.get("write_absent") is True or str(raw.get("status") or "").upper() in {
        "NOT_FOUND", "ABSENT", "RECONCILED_ABSENT_SAFE_TO_RETRY",
    }
    verified_flag = any(raw.get(k) is True for k in (
        "verified", "readback_verified", "public_readback_verified", "strict_readback_verified",
        "identity_verified",
    )) or str(raw.get("status") or "").upper() in {"SUCCESS", "PASS", "RECONCILED_CONFIRMED"}
    matching = bool(
        observed_id
        and (
            (public_object_id and observed_id == str(public_object_id))
            or (not public_object_id and verified_flag)
        )
    )
    return {
        "verified": bool(verified_flag and matching),
        "write_absent": bool(absent),
        "observed_public_object_id": observed_id,
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
    ) -> None:
        self.store = store
        self.transport_runtime = transport_runtime
        self.readiness_provider = readiness_provider
        self.readiness_manager = readiness_manager
        self.readiness_refresh_seconds = max(30.0, float(readiness_refresh_seconds))

    def _refresh_readiness_if_due(self) -> bool:
        if self.readiness_manager is None:
            return False
        rows = self.store.list_destination_readiness()
        latest = None
        for row in rows:
            try:
                value = datetime.fromisoformat(str(row["probed_at_utc"]).replace("Z", "+00:00"))
                value = value.replace(tzinfo=value.tzinfo or timezone.utc).astimezone(timezone.utc)
                latest = value if latest is None or value > latest else latest
            except Exception:
                continue
        now = datetime.now(timezone.utc)
        if latest is not None and (now - latest).total_seconds() < self.readiness_refresh_seconds:
            return False
        self.readiness_manager.probe_all(persist=True)
        return True

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
                "publication_window": plan.get("publication_window"),
                "package_identity": plan.get("package_identity"),
                "plan_hash": plan_hash,
                "output_dir": plan.get("output_dir"),
                "artifact_refs": plan.get("artifact_refs") or {},
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

    def _reconcile(self, dispatch: Mapping[str, Any], intent: Mapping[str, Any]) -> str:
        dispatch_id = str(dispatch["dispatch_id"])
        destination = str(dispatch["platform"])
        object_id = str(dispatch.get("public_object_id") or "") or None
        ids = self._ids(str(intent["work_item_id"]), str(intent["plan_hash"]), destination)
        try:
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
                "observed_public_object_id": None, "error_class": type(exc).__name__,
            }
        readback_data = _canonical_json({
            "dispatch_id": dispatch_id, "destination": destination, "readback": normalized,
        })
        self.store.register_readback(
            readback_id="readback_" + _hash(readback_data)[:32],
            dispatch_id=dispatch_id,
            readback_data=readback_data,
        )
        if normalized.get("verified") is True:
            status = RECONCILED_CONFIRMED
            if not object_id and normalized.get("observed_public_object_id"):
                self.store.register_platform_dispatch(
                    dispatch_id=dispatch_id,
                    message_id=str(dispatch["message_id"]),
                    platform=destination,
                    status=str(dispatch["status"]),
                    public_object_id=str(normalized["observed_public_object_id"]),
                    public_object_url=str(dispatch.get("public_object_url") or "") or None,
                )
        elif normalized.get("write_absent") is True:
            status = RECONCILED_ABSENT_SAFE_TO_RETRY
        else:
            status = RECONCILIATION_PENDING
        self.store.register_reconciliation(
            reconciliation_id=ids["reconciliation_id"],
            work_item_id=str(intent["work_item_id"]), status=status,
        )
        self.store.set_reconciliation_status(ids["reconciliation_id"], status)
        return status

    def _dispatch_message(self, message: Mapping[str, Any], *, canonical_url: Optional[str]) -> dict[str, Any]:
        intent = json.loads(str(message["payload"]))
        destination = str(message["destination"])
        item = dict(intent["destination_plan"])
        ids = self._ids(str(intent["work_item_id"]), str(intent["plan_hash"]), destination)
        existing = self.store.get_platform_dispatch(ids["dispatch_id"])
        if existing:
            return {"destination": destination, "status": str(existing["status"]), "publish_called": False}
        dependency = item.get("canonical_url_dependency")
        if dependency and not (canonical_url or intent.get("canonical_url")):
            return {"destination": destination, "status": "WAITING_CANONICAL_URL", "publish_called": False}
        if dependency and canonical_url:
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
        readiness = self._readiness(destination, item)
        if readiness not in READY_STATES:
            return {"destination": destination, "status": readiness or "READINESS_UNKNOWN", "publish_called": False}
        # Re-read durable mode immediately before every new adapter write.
        mode = self._mode()
        if mode != "AUTONOMOUS_DEFAULT":
            return {"destination": destination, "status": f"WRITE_BLOCKED_{mode}", "publish_called": False}
        self.store.register_platform_dispatch(
            dispatch_id=ids["dispatch_id"], message_id=ids["message_id"],
            platform=destination, status=ATTEMPT_STARTED,
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
        try:
            raw = self.transport_runtime.publish(
                destination=destination,
                intent={**intent, "canonical_url": canonical_url or intent.get("canonical_url")},
                authorization_context=authorization,
            )
            registration = registration_for_destination(destination)
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
        reconciliation = self._reconcile(dispatch, intent) if result["status"] in {
            DISPATCH_CONFIRMED, UNKNOWN_WRITE,
        } else RECONCILED_ABSENT_SAFE_TO_RETRY
        return {
            "destination": destination, "status": result["status"], "publish_called": True,
            "public_object_id": result.get("public_object_id"),
            "public_object_url": result.get("public_object_url"),
            "reconciliation_status": reconciliation,
        }

    def execute_plan(self, work_item_id: str, plan: Mapping[str, Any]) -> dict[str, Any]:
        registration = self.register_plan(work_item_id, plan)
        outcomes: dict[str, Any] = {}
        canonical_url: Optional[str] = None
        messages = [m for m in self.store.list_outbox_messages() if m["work_item_id"] == work_item_id]
        messages.sort(key=lambda m: (0 if m["destination"] == "substack" else 1, m["destination"]))
        for message in messages:
            outcome = self._dispatch_message(message, canonical_url=canonical_url)
            outcomes[str(message["destination"])] = outcome
            if message["destination"] == "substack" and outcome.get("reconciliation_status") == RECONCILED_CONFIRMED:
                canonical_url = str(outcome.get("public_object_url") or "") or None
        return {
            **registration,
            "per_destination": outcomes,
            "public_write_performed": any(
                o.get("status") == DISPATCH_CONFIRMED and o.get("publish_called") is True
                for o in outcomes.values()
            ),
            "unknown_write_detected": any(o.get("status") == UNKNOWN_WRITE for o in outcomes.values()),
        }

    def recover_pending(self) -> dict[str, Any]:
        """Restart recovery: safe pre-marker resume; post-marker readback only."""
        summary = {"safe_resumes": 0, "marked_unknown": 0, "readbacks": 0, "publish_calls": 0,
                   "readiness_probe_performed": False}
        try:
            summary["readiness_probe_performed"] = self._refresh_readiness_if_due()
        except Exception:
            # Destination-health failure never creates write authority and does not stop exact
            # durable UNKNOWN_WRITE recovery for other destinations.
            summary["readiness_probe_performed"] = False
        messages = self.store.list_outbox_messages()
        dispatch_by_message = {str(d["message_id"]): d for d in self.store.list_platform_dispatches()}
        for message in messages:
            intent = json.loads(str(message["payload"]))
            dispatch = dispatch_by_message.get(str(message["message_id"]))
            if dispatch is None and str(message["status"]) == "READY":
                outcome = self._dispatch_message(message, canonical_url=intent.get("canonical_url"))
                summary["safe_resumes"] += 1
                summary["publish_calls"] += int(bool(outcome.get("publish_called")))
                continue
            if dispatch is None:
                continue
            status = str(dispatch["status"])
            if status == ATTEMPT_STARTED:
                self.store.set_dispatch_status(str(dispatch["dispatch_id"]), UNKNOWN_WRITE)
                self.store.set_outbox_status(str(message["message_id"]), UNKNOWN_WRITE)
                dispatch = self.store.get_platform_dispatch(str(dispatch["dispatch_id"]))
                summary["marked_unknown"] += 1
                status = UNKNOWN_WRITE
            if status in {UNKNOWN_WRITE, DISPATCH_CONFIRMED}:
                self._reconcile(dispatch, intent)
                summary["readbacks"] += 1
        return summary

    def publish_plan(self, work_item_id: str, plan: Mapping[str, Any]) -> dict[str, Any]:
        return self.execute_plan(work_item_id, plan)

    def readback(self, *args: Any, **kwargs: Any) -> Mapping[str, Any]:
        """Production wiring seam: readback is owned by this coordinator/router."""
        return self.transport_runtime.readback(*args, **kwargs)

    def collect_metrics(self, *args: Any, **kwargs: Any) -> Mapping[str, Any]:
        collector = getattr(self.transport_runtime, "collect_metrics", None)
        return collector(*args, **kwargs) if callable(collector) else {"status": "METRICS_UNAVAILABLE"}


class HistoricalAdapterTransportRuntime:
    """Thin production wrapper over the accepted adapter family; no alternate transports."""

    def __init__(self) -> None:
        self._strict_publish_readbacks: dict[tuple[str, str], Mapping[str, Any]] = {}

    def publish(self, *, destination: str, intent: Mapping[str, Any],
                authorization_context: Mapping[str, Any]) -> Mapping[str, Any]:
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
        payload = str((data["payloads"].get(destination) or {}).get("text") or "")
        destination_plan = dict(finalized["destination_plan"])
        destination_plan["payload_hash"] = _hash(payload)
        destination_plan["payload_hash_kind"] = "FINAL_CANONICAL_URL_BOUND_BYTES"
        finalized["destination_plan"] = destination_plan
        finalized["payload"] = payload
        return finalized

    def readback(self, *, destination: str, public_object_id: Optional[str],
                 public_object_url: Optional[str], intent: Mapping[str, Any]) -> Mapping[str, Any]:
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

    def collect_metrics(self, *args: Any, **kwargs: Any) -> Mapping[str, Any]:
        return {"status": "BOUNDED_PLATFORM_METRICS_ROUTER_AVAILABLE", "observations": []}
