"""Single durable Final Daily App public-write owner.

The newsroom produces deterministic publication plans.  This coordinator persists exact
pre-write intent, records ``DISPATCH_ATTEMPT_STARTED`` before crossing any API/CDP boundary,
routes through the versioned transport registry, and owns strict readback/reconciliation.
There is deliberately no transport fallback and no automatic retry from UNKNOWN_WRITE.
"""
from __future__ import annotations

import hashlib
import json
import re
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
from live_contentops.native_neo_executor_v1 import NativeNeoInputRequired, PENDING as NATIVE_NEO_PENDING


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
EXTERNAL_REMOVAL_REPORTED_NO_RETRY = "EXTERNAL_REMOVAL_REPORTED_NO_RETRY"
OWNER_RETAINED_DRAFT_NO_PUBLISH = "OWNER_RETAINED_DRAFT_NO_PUBLISH"
CONTROLLED_NO_PUBLIC_WRITE = "CONTROLLED_NO_PUBLIC_WRITE"
RECONCILED_CONTROLLED_NO_WRITE = "RECONCILED_CONTROLLED_NO_WRITE"
OWNER_RETIRED_STATUSES = {EXTERNAL_REMOVAL_REPORTED_NO_RETRY, OWNER_RETAINED_DRAFT_NO_PUBLISH}
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

    def reconcile_controlled_no_write_dispatch(self, dispatch_id: str) -> dict[str, Any]:
        """Repair an exact terminal fixture chain without a transport or public identity.

        Historical fixture readbacks sometimes said verified:true; that verified the
        controlled run, not a public object. Keep those original bytes, append the
        explicit no-write interpretation and repair only lifecycle statuses atomically.
        """
        conn = self.store.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            dispatch = conn.execute("SELECT * FROM platform_dispatches WHERE dispatch_id=?", (dispatch_id,)).fetchone()
            if (not dispatch or dispatch["status"] not in {"DISPATCH_CONFIRMED_NO_WRITE", CONTROLLED_NO_PUBLIC_WRITE}
                    or dispatch["public_object_id"] or dispatch["public_object_url"]):
                raise ValueError("EXACT_TERMINAL_CONTROLLED_NO_WRITE_DISPATCH_REQUIRED")
            message = conn.execute("SELECT * FROM outbox_messages WHERE message_id=?", (dispatch["message_id"],)).fetchone()
            if not message or message["status"] not in {"READY", "PENDING", CONTROLLED_NO_PUBLIC_WRITE}:
                raise ValueError("EXACT_CONTROLLED_OUTBOX_REQUIRED")
            basis = json.loads(message["payload"])
            if (set(basis) != {"window_id", "destination", "package_identity"}
                    or basis["window_id"] != message["work_item_id"]
                    or basis["destination"] != dispatch["platform"]
                    or basis["destination"] != message["destination"]):
                raise ValueError("CONTROLLED_NO_WRITE_LIFECYCLE_BINDING_REQUIRED")
            # The established supervisor hashes the JSON-encoded basis string,
            # rather than its literal bytes. Retain that exact durable identity.
            suffix = _hash(_canonical_json(json.dumps(basis, sort_keys=True)))[:32]
            if dispatch_id != "dispatch_" + suffix or message["message_id"] != "outbox_" + suffix:
                raise ValueError("CONTROLLED_NO_WRITE_LIFECYCLE_BINDING_REQUIRED")
            reconciliation_id = "reconciliation_" + suffix
            reconciliation = conn.execute("SELECT * FROM reconciliations WHERE reconciliation_id=?", (reconciliation_id,)).fetchone()
            if (not reconciliation or reconciliation["work_item_id"] != message["work_item_id"]
                    or reconciliation["status"] not in {RECONCILED_CONFIRMED, RECONCILED_CONTROLLED_NO_WRITE}):
                raise ValueError("EXISTING_TERMINAL_NO_WRITE_RECONCILIATION_REQUIRED")
            readbacks = conn.execute("SELECT * FROM readbacks WHERE dispatch_id=? ORDER BY read_at,readback_id", (dispatch_id,)).fetchall()
            matched, originals = False, []
            controlled_actor = conn.execute("SELECT 1 FROM transition_events WHERE work_item_id=? AND actor_ref LIKE 'controlled-%' LIMIT 1",
                (message["work_item_id"],)).fetchone()
            for row in readbacks:
                value = json.loads(row["readback_data"])
                if value.get("schema_version") == "contentops.controlled_no_write_reconciliation.v1":
                    continue
                if (value.get("public_write_performed") is True or value.get("public_object_id")
                        or value.get("public_object_url") or (value.get("observed") or {}).get("public_object_id")):
                    raise ValueError("CONTROLLED_NO_WRITE_CONTRADICTORY_PUBLIC_EVIDENCE")
                if value.get("dispatch_id") != dispatch_id or value.get("destination") != dispatch["platform"]:
                    raise ValueError("CONTROLLED_NO_WRITE_READBACK_BINDING_REQUIRED")
                typed = (value.get("readback_status") == CONTROLLED_NO_PUBLIC_WRITE
                    and value.get("verified") is False and value.get("public_write_performed") is False)
                historical_fixture = (dispatch["status"] == "DISPATCH_CONFIRMED_NO_WRITE"
                    and str(basis["package_identity"]).startswith("controlled-")
                    and controlled_actor and value.get("verified") is True)
                matched = matched or typed or bool(historical_fixture)
                originals.append({"readback_id": row["readback_id"], "sha256": _hash(row["readback_data"])})
            if not matched:
                raise ValueError("CONTROLLED_NO_WRITE_ORIGINAL_EVIDENCE_REQUIRED")
            evidence = {"schema_version": "contentops.controlled_no_write_reconciliation.v1",
                "dispatch_id": dispatch_id, "destination": dispatch["platform"],
                "outbox_message_id": message["message_id"], "original_payload_sha256": _hash(message["payload"]),
                "original_dispatch_status": dispatch["status"], "original_readbacks": originals,
                "verified": False, "public_write_performed": False, "real_publication": False,
                "reason": "Terminal controlled no-write dispatch has no public object; retain fixture evidence and close its stale outbox status."}
            payload = _canonical_json(evidence)
            readback_id = "readback_controlled_no_write_" + _hash(payload)[:32]
            conn.execute("INSERT OR IGNORE INTO readbacks(readback_id,dispatch_id,readback_data,read_at) VALUES(?,?,?,?)",
                (readback_id, dispatch_id, payload, self._clock().isoformat()))
            conn.execute("UPDATE outbox_messages SET status=? WHERE message_id=?", (CONTROLLED_NO_PUBLIC_WRITE, message["message_id"]))
            conn.execute("UPDATE reconciliations SET status=? WHERE reconciliation_id=?", (RECONCILED_CONTROLLED_NO_WRITE, reconciliation_id))
            conn.commit()
            return {"dispatch_id": dispatch_id, "message_id": message["message_id"],
                "status": CONTROLLED_NO_PUBLIC_WRITE, "reconciliation_status": RECONCILED_CONTROLLED_NO_WRITE,
                "readback_id": readback_id, "publish_called": False, "provider_calls": 0,
                "public_write_performed": False, "real_publication": False}
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def reconcile_owner_removed_object(self, dispatch_id: str, *, disposition: str,
                                       observation: Mapping[str, Any]) -> dict[str, Any]:
        """Append the owner's cleanup observation and retire its exact historical send.

        A posting-list observation is recorded as reported removal, not invented exact
        object readback. IDs, prior success/ambiguity and original readbacks survive.
        Neither removal nor a deliberately retained draft grants retry permission.
        """
        dispatch = self.store.get_platform_dispatch(dispatch_id)
        if disposition not in OWNER_RETIRED_STATUSES or not dispatch:
            raise ValueError("EXACT_OWNER_REMOVAL_DISPOSITION_REQUIRED")
        message = self.store.get_outbox_message(dispatch["message_id"])
        observed = dict(observation)
        if (dispatch["status"] in {UNKNOWN_WRITE, ATTEMPT_STARTED, NATIVE_NEO_PENDING}
                and observed.get("exact_object_absence_verified") is not True):
            raise ValueError("AMBIGUOUS_OBJECT_REQUIRES_EXACT_READBACK")
        if (disposition == OWNER_RETAINED_DRAFT_NO_PUBLISH
                and dispatch["status"] not in {RECONCILED_ABSENT_SAFE_TO_RETRY, OWNER_RETAINED_DRAFT_NO_PUBLISH}):
            raise ValueError("EXACT_RECONCILED_DRAFT_REQUIRED")
        if (not message or observed.get("destination") != message["destination"]
                or observed.get("public_object_id") != dispatch.get("public_object_id")
                or not dispatch.get("public_object_id")
                or not all(observed.get(k) for k in ("authority_ref", "observation_ref", "observed_at_utc", "observation_basis"))):
            raise ValueError("OWNER_REMOVAL_EXACT_OBJECT_AND_PROVENANCE_REQUIRED")
        stamp = datetime.fromisoformat(observed["observed_at_utc"].replace("Z", "+00:00"))
        if stamp.tzinfo is None or stamp > self._clock() + timedelta(seconds=30):
            raise ValueError("OWNER_REMOVAL_OBSERVATION_CLOCK_INVALID")
        readback_id = "owner-removal-" + _hash(_canonical_json([dispatch_id, disposition, observed]))
        existing = next((r for r in self.store.list_readbacks_for_dispatch(dispatch_id)
                         if r["readback_id"] == readback_id), None)
        reconciliation_id = "reconciliation_" + dispatch_id.removeprefix("dispatch_")
        prior = next((r for r in self.store.get_reconciliations_for_work_item(message["work_item_id"])
                      if r["reconciliation_id"] == reconciliation_id), None)
        if not existing:
            if dispatch["status"] in OWNER_RETIRED_STATUSES:
                raise ValueError("OWNER_REMOVAL_ALREADY_RECORDED_USE_ORIGINAL_OBSERVATION")
            self.store.register_readback(readback_id=readback_id, dispatch_id=dispatch_id,
                readback_data=_canonical_json({"schema_version": "contentops.owner_removal_observation.v1",
                    "disposition": disposition, "observation": observed,
                    "previous_dispatch": dispatch, "previous_reconciliation": prior,
                    "exact_object_absence_independently_verified": observed.get("exact_object_absence_verified") is True,
                    "retry_permitted": False}))
        elif json.loads(existing["readback_data"])["disposition"] != disposition:
            raise ValueError("OWNER_REMOVAL_OBSERVATION_CHANGED")
        if prior is None:
            self.store.register_reconciliation(reconciliation_id=reconciliation_id,
                work_item_id=message["work_item_id"], status=disposition)
        else:
            self.store.set_reconciliation_status(reconciliation_id, disposition)
        self.store.set_dispatch_status(dispatch_id, disposition)
        self.store.set_outbox_status(message["message_id"], disposition)
        return {"dispatch_id": dispatch_id, "public_object_id": dispatch["public_object_id"],
                "public_object_url": dispatch.get("public_object_url"), "status": disposition,
                "readback_id": readback_id, "retry_permitted": False, "provider_calls": 0}

    @staticmethod
    def _survivor_dispatch_id(original_id, object_id):
        return original_id + "_observed_" + _hash(str(object_id))[:16]

    @classmethod
    def effective_dispatch(cls, original, dispatches):
        """Resolve an observed survivor without changing the removed original identity."""
        if original.get("platform") != "telegram" or original.get("status") not in OWNER_RETIRED_STATUSES:
            return original
        candidates = [d for d in dispatches if d.get("message_id") == original.get("message_id")
            and d.get("platform") == "telegram" and d.get("status") == DISPATCH_CONFIRMED
            and d.get("public_object_id") and d.get("dispatch_id") == cls._survivor_dispatch_id(
                original["dispatch_id"], d["public_object_id"])]
        if len(candidates) != 1:
            return original
        return {**candidates[0], "original_dispatch_id": original["dispatch_id"],
                "original_public_object_id": original.get("public_object_id")}

    def reconcile_existing_duplicate_survivor(self, dispatch_id, *, observation):
        """Admit one actually observed Telegram duplicate; never send or replace IDs."""
        original = self.store.get_platform_dispatch(dispatch_id) or {}
        message = self.store.get_outbox_message(original.get("message_id", ""))
        if not message or original.get("platform") != "telegram" or not original.get("public_object_id"):
            raise ValueError("EXACT_ORIGINAL_TELEGRAM_DISPATCH_REQUIRED")
        intent = json.loads(message["payload"])
        proof = dict(observation)
        object_id = str(proof.get("public_object_id") or "")
        from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import _durable_intent_inputs
        data = _durable_intent_inputs(intent)
        expected = str((intent.get("native_payload") or {}).get("text") or intent.get("payload") or "")
        observed_at = _parse_utc(proof.get("observed_at_utc"))
        if (not object_id.isdigit() or object_id == original["public_object_id"]
                or proof.get("public_object_url") != "https://t.me/CapitalChronicle/" + object_id
                or proof.get("observed_identity") != "@CapitalChronicle"
                or proof.get("observed_text") not in {expected, data["payloads"]["telegram"]["text"]}
                or not expected or proof.get("photo_pixels_inspected") is not True
                or proof.get("media_sha256") not in {a["sha256"] for a in data["media_assets"]}
                or proof.get("canonical_url") != intent.get("canonical_url")
                or str(intent.get("canonical_url") or "") not in str(proof.get("observed_text") or "")
                or proof.get("removed_object_id") != original["public_object_id"]
                or proof.get("removed_object_absence_verified") is not True
                or proof.get("tool_name") != "mcp__browseros_neo__run"
                or not all(proof.get(k) for k in ("owner_authority_ref", "observation_ref", "observation_source"))
                or observed_at is None or not timedelta(0) <= self._clock() - observed_at <= timedelta(minutes=5)):
            raise ValueError("EXACT_CURRENT_DUPLICATE_SURVIVOR_PROOF_REQUIRED")
        if self._confirmed_canonical_url_for_work_item(intent["work_item_id"], plan_hash=intent["plan_hash"]) != intent["canonical_url"]:
            raise ValueError("SURVIVOR_CANONICAL_IDENTITY_REQUIRED")
        survivor_id = self._survivor_dispatch_id(dispatch_id, object_id)
        existing = self.store.get_platform_dispatch(survivor_id)
        if existing:
            return {"dispatch_id": survivor_id, "public_object_id": object_id,
                    "public_object_url": existing["public_object_url"], "new_posts": 0, "reused": True}
        self.reconcile_owner_removed_object(dispatch_id, disposition=EXTERNAL_REMOVAL_REPORTED_NO_RETRY,
            observation={"destination": "telegram", "public_object_id": original["public_object_id"],
                "authority_ref": proof["owner_authority_ref"], "observation_ref": proof["observation_ref"],
                "observed_at_utc": proof["observed_at_utc"], "observation_basis": proof["observation_source"],
                "exact_object_absence_verified": True})
        self.store.register_platform_dispatch(dispatch_id=survivor_id, message_id=message["message_id"],
            platform="telegram", status=DISPATCH_CONFIRMED, public_object_id=object_id,
            public_object_url=proof["public_object_url"])
        self.store.register_readback(readback_id="observed-survivor-" + _hash(_canonical_json(proof)),
            dispatch_id=survivor_id, readback_data=_canonical_json({"original_dispatch_id": dispatch_id,
                "observation": proof, "readback": {"verified": True, "identity_match": True,
                    "observed_public_object_id": object_id, "observed_public_object_url": proof["public_object_url"]}}))
        self.store.register_reconciliation(reconciliation_id="reconciliation_" + survivor_id.removeprefix("dispatch_"),
            work_item_id=intent["work_item_id"], status=RECONCILED_CONFIRMED)
        return {"dispatch_id": survivor_id, "original_dispatch_id": dispatch_id, "public_object_id": object_id,
                "public_object_url": proof["public_object_url"], "new_posts": 0, "reused": False}

    def _dated_distribution_message(self, message):
        """Resolve an accepted append-only amendment while retaining original intent bytes."""
        from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
        row = self.store.get_outbox_message("native-dated-distribution-" + sha256_of(message["message_id"]))
        if not row:
            return message
        amendment = json.loads(row["payload"])
        original = self.store.get_outbox_message(message["message_id"])
        if not original or amendment["original_intent_sha256"] != sha256_of(json.loads(original["payload"])):
            raise ValueError("DATED_DISTRIBUTION_ORIGINAL_INTENT_CHANGED")
        from live_contentops.native_desktop_editorial_v1 import dated_distribution_recovery_acceptance
        recovery, _ = dated_distribution_recovery_acceptance(self.store,
            run_id=message["work_item_id"], reference=amendment["review_reference"])
        intent = json.loads(original["payload"])
        destination = message["destination"]
        if destination not in recovery["payloads"] or intent["plan_hash"] != recovery["plan_hash"]:
            raise ValueError("DATED_DISTRIBUTION_EXACT_DESTINATION_REQUIRED")
        payload = recovery["payloads"][destination]
        intent.update(native_payload=payload, payload=payload["text"],
            dated_distribution_recovery=amendment["review_reference"])
        intent["destination_plan"] = {**intent["destination_plan"], "payload_hash": sha256_of(payload),
            "payload_hash_kind": "OWNER_APPROVED_DATED_DISTRIBUTION"}
        if destination == "linkedin" and recovery.get("transport_override") == "BROWSEROS_NEO_MCP":
            intent["destination_plan"]["transport_type"] = "BROWSEROS_NEO_MCP"
        return {**original, "payload": _canonical_json(intent)}

    def _reader_presentation_intent(self, message, reference):
        from live_contentops.native_desktop_editorial_v1 import reader_presentation_acceptance
        from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
        revision, view, acceptance = reader_presentation_acceptance(self.store,
            run_id=message["work_item_id"], reference=reference)
        destination = message["destination"]
        identity = revision["objects"][destination]
        if identity["message_id"] != message["message_id"]:
            raise ValueError("READER_REVISION_EXACT_MESSAGE_REQUIRED")
        intent = json.loads(self._dated_distribution_message(message)["payload"])
        from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import _durable_intent_inputs
        retained_media = _durable_intent_inputs(intent).get("media_assets", [])
        if destination == "substack":
            from live_contentops.v1_simple_gemini_newsroom_v1 import _reader_safe_native_article
            article = _reader_safe_native_article(view["article"], article_mode=view["article"].get("resolved_article_mode", ""))
            payload = {"title": article["title"], "subtitle": article["subtitle"], "body_markdown": article["substack_body_markdown"]}
        else:
            payload = revision["payloads"][destination]
        intent.update(native_payload=payload, payload=payload.get("text") or payload["body_markdown"],
            media_assets=retained_media,
            reader_presentation_review=reference, removed_reader_text=[
                re.search(r"Reporting as of [^\n]+?\d{4}\.", revision["body_before"])[0]])
        intent["destination_plan"] = {**intent["destination_plan"], "payload_hash": sha256_of(payload),
            "payload_hash_kind": "SAME_MAX_REVIEWED_PRESENTATION"}
        return intent, revision, view, acceptance

    def _effective_message(self, message):
        from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
        row = self.store.get_outbox_message("native-reader-presentation-" + sha256_of(message["message_id"]))
        if not row or row["status"] != "PRESENTATION_EDIT_CONFIRMED":
            return self._dated_distribution_message(message)
        edit = json.loads(row["payload"])
        intent, _, _, _ = self._reader_presentation_intent(message, edit["review_reference"])
        return {**message, "payload": _canonical_json(intent)}

    def amend_reader_presentation(self, dispatch_id, *, review_reference):
        """Edit the reviewed existing object once; all uncertain outcomes are readback-only."""
        from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
        dispatch = self.store.get_platform_dispatch(dispatch_id) or {}
        message = self.store.get_outbox_message(str(dispatch.get("message_id") or ""))
        if not message or dispatch.get("status") != DISPATCH_CONFIRMED or self._mode() != "AUTONOMOUS_DEFAULT":
            raise ValueError("READER_REVISION_CURRENT_LIVE_CONFIRMED_OBJECT_REQUIRED")
        intent, revision, view, acceptance = self._reader_presentation_intent(message, review_reference)
        destination = message["destination"]
        key = "native-reader-presentation-" + sha256_of(message["message_id"])
        canonical_id = revision["objects"]["substack"]["message_id"]
        if destination != "substack":
            canonical_edit = self.store.get_outbox_message("native-reader-presentation-" + sha256_of(canonical_id)) or {}
            if canonical_edit.get("status") != "PRESENTATION_EDIT_CONFIRMED":
                return {"status": "READER_REVISION_CANONICAL_EDIT_READBACK_REQUIRED", "edit_called": False}
        note = {"run_id": intent["work_item_id"], "article_identity": revision["article_identity"],
            "destination": destination, "public_message_id": message["message_id"],
            "original_intent_sha256": sha256_of(json.loads(message["payload"])),
            "review_reference": review_reference, "acceptance": acceptance,
            "public_object_id": dispatch["public_object_id"], "public_object_url": dispatch["public_object_url"],
            "article": view["article"] if destination == "substack" else None,
            "payload": intent["native_payload"], "prior_revision": revision["prior_revision"]}
        prior = self.store.get_outbox_message(key)
        if prior and json.loads(prior["payload"]) != note:
            raise ValueError("READER_REVISION_EXISTING_EDIT_IDENTITY_CHANGED")
        if prior and prior["status"] == "PRESENTATION_EDIT_CONFIRMED":
            return {"status": "PRESENTATION_EDIT_CONFIRMED", "edit_called": False, "new_post_calls": 0}
        if not prior:
            self.store.register_outbox_message(message_id=key, work_item_id=intent["work_item_id"],
                destination="internal:native-reader-presentation", payload=_canonical_json(note), status="PRESENTATION_EDIT_PENDING")
        if self.readiness_manager is not None:
            ready = self.readiness_manager.verify_destination_jit(destination, reason="PUBLICATION", persist=True)
            if ready.get("readiness_state") not in READY_STATES or ready.get("identity_match") is False:
                return {"status": "READER_REVISION_IDENTITY_NOT_READY", "edit_called": False}
        authorization = {"schema_version": "contentops.canonical_machine_authorization.v1",
            "operating_mode": self._mode(), "work_item_id": intent["work_item_id"], "destination": destination,
            "payload_hash": intent["destination_plan"]["payload_hash"], "dispatch_attempt_identity": dispatch_id,
            "action": "EDIT_EXISTING"}
        attempted = any(r["readback_id"] == key + "-api-started" for r in self.store.list_readbacks_for_dispatch(dispatch_id))
        raw = {"status": "READBACK_ONLY_AFTER_EDIT_ATTEMPT"}
        if not attempted:
            if destination == "facebook_page":
                self.store.register_readback(readback_id=key + "-api-started", dispatch_id=dispatch_id,
                    readback_data=_canonical_json({"action": "EDIT_EXISTING", "public_object_id": dispatch["public_object_id"]}))
            raw = self.transport_runtime.amend_reader_presentation(destination=destination, intent=intent,
                public_object_id=dispatch["public_object_id"], public_object_url=dispatch["public_object_url"],
                authorization_context=authorization)
        # Native executor claims fence browser edits, including restart after a lost return.
        observed = self.transport_runtime.readback(destination=destination, intent=intent,
            public_object_id=dispatch["public_object_id"], public_object_url=dispatch["public_object_url"])
        verified = observed.get("verified") is True
        self.store.register_readback(readback_id=key + "-observed-" + sha256_of(observed), dispatch_id=dispatch_id,
            readback_data=_canonical_json({"action": "EDIT_EXISTING", "result": raw, "readback": observed}))
        if verified:
            self.store.set_outbox_status(key, "PRESENTATION_EDIT_CONFIRMED")
        return {"status": "PRESENTATION_EDIT_CONFIRMED" if verified else "UNKNOWN_EDIT_READBACK_REQUIRED",
            "edit_called": not attempted, "verified": verified, "new_post_calls": 0, "readback": observed}

    def _intent_registration(self, destination, intent):
        registration = registration_for_destination(destination)
        if destination == "linkedin_company":
            from live_contentops.native_desktop_editorial_v1 import dated_distribution_recovery_acceptance
            reference = intent.get("dated_distribution_recovery")
            if not reference:
                raise ValueError("LINKEDIN_COMPANY_EXPLICIT_SAME_REVIEW_REQUIRED")
            recovery, _ = dated_distribution_recovery_acceptance(self.store,
                run_id=intent["work_item_id"], reference=reference)
            source_id = self._ids(intent["work_item_id"], recovery["plan_hash"], "linkedin")["message_id"]
            source = self.store.get_outbox_message(source_id)
            original = json.loads(source["payload"]) if source else {}
            from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
            reviewed_payload = recovery["payloads"]["linkedin"]
            if intent.get("reader_presentation_review"):
                from live_contentops.native_desktop_editorial_v1 import reader_presentation_acceptance
                revision, _, _ = reader_presentation_acceptance(self.store, run_id=intent["work_item_id"],
                    reference=intent["reader_presentation_review"])
                reviewed_payload = revision["payloads"]["linkedin_company"]
            if (recovery.get("recipients", {}).get(destination) != registration.expected_identity
                    or recovery.get("original_intent_sha256", {}).get("linkedin") != sha256_of(original)
                    or intent.get("company_copy_of_message_id") != source_id
                    or intent.get("native_payload") != reviewed_payload
                    or intent.get("payload") != reviewed_payload["text"]
                    or intent.get("canonical_url") != recovery["canonical_url"]
                    or intent.get("plan_hash") != recovery["plan_hash"]
                    or intent.get("owner_authority_ref") != recovery["owner_authority_ref"]
                    or intent.get("destination_plan", {}).get("payload_hash") != sha256_of(intent.get("native_payload"))):
                raise ValueError("LINKEDIN_COMPANY_EXACT_REVIEWED_COPY_REQUIRED")
        if destination == "linkedin" and intent.get("destination_plan", {}).get("transport_type") == "BROWSEROS_NEO_MCP":
            from dataclasses import replace
            from live_contentops.native_desktop_editorial_v1 import dated_distribution_recovery_acceptance
            reference = intent.get("dated_distribution_recovery")
            if not reference:
                raise ValueError("LINKEDIN_NEO_EXPLICIT_REVIEWED_RECOVERY_REQUIRED")
            recovery, _ = dated_distribution_recovery_acceptance(self.store,
                run_id=intent["work_item_id"], reference=reference)
            if recovery.get("transport_override") != "BROWSEROS_NEO_MCP" or recovery.get("recipients", {}).get("linkedin") != "linkedin:jimcc":
                raise ValueError("LINKEDIN_NEO_EXACT_RECIPIENT_REQUIRED")
            registration = replace(registration, transport_type="BROWSEROS_NEO_MCP",
                adapter="neo_destination_handoff_v1.NeoDestinationHandoff")
        return registration

    def reconcile_owner_confirmed_linkedin_absence(self, dispatch_id, *, owner_authority_ref, request_hash=None):
        """Combine Jim's absence report with a fresh, loaded own-profile Neo readback."""
        from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
        from live_contentops.neo_destination_handoff_v1 import ROOTS
        dispatch = self.store.get_platform_dispatch(dispatch_id) or {}
        message = self.store.get_outbox_message(dispatch.get("message_id", ""))
        if (not message or message["destination"] != "linkedin" or dispatch.get("public_object_id")
                or dispatch.get("public_object_url") or dispatch.get("status") != UNKNOWN_WRITE
                or not str(owner_authority_ref).startswith("human:")):
            raise ValueError("LINKEDIN_EXACT_UNIDENTIFIED_UNKNOWN_AND_OWNER_REPORT_REQUIRED")
        original = json.loads(message["payload"])
        context = {"dispatch_id": dispatch_id, "original_intent_sha256": sha256_of(original),
            "owner_authority_ref": owner_authority_ref, "owner_reported_absent": True,
            "profile_url": ROOTS["linkedin"], "observation_epoch": int(self._clock().timestamp()) // 300}
        transport = getattr(self.transport_runtime, "_neo_transport", None)
        executor = getattr(transport, "native_executor", None)
        if not getattr(executor, "native_neo_protocol", False) or executor.operation_id != message["work_item_id"]:
            raise ValueError("LINKEDIN_EXACT_NATIVE_READBACK_EXECUTOR_REQUIRED")
        if request_hash:
            packet = executor._get(request_hash, "request") or {}
            previous_context = packet.get("request", {}).get("owner_absence_context") or {}
            if (packet.get("operation_id") != message["work_item_id"]
                    or {k: v for k, v in previous_context.items() if k != "observation_epoch"}
                    != {k: v for k, v in context.items() if k != "observation_epoch"}):
                raise ValueError("LINKEDIN_EXACT_PRIOR_ABSENCE_REQUEST_REQUIRED")
            context = previous_context
        request = transport.request(destination="linkedin", action="READBACK",
            intent={**original, "owner_absence_context": context})
        if request_hash and request["request_sha256"] != request_hash:
            raise ValueError("LINKEDIN_EXACT_PRIOR_ABSENCE_REQUEST_REQUIRED")
        result = executor(request)
        observation = result.get("native_tool_observation") or {}
        observed = _parse_utc(observation.get("observed_at_utc"))
        age = (self._clock() - observed).total_seconds() if observed else -1
        if (result.get("request_sha256") != request["request_sha256"]
                or result.get("observed_identity") != "linkedin:jimcc"
                or result.get("observed_profile_url") != ROOTS["linkedin"]
                or result.get("authenticated") is not True or result.get("activity_feed_loaded") is not True
                or result.get("activity_feed_empty") is not True
                or "Nothing to see for now" not in str(result.get("observed_text") or "")
                or observation.get("tool_name") != "mcp__browseros_neo__run"
                or observation.get("native_invocation_id") != executor.native_invocation_id
                or not result.get("native_tool_return_sha256") or not 0 <= age <= 300):
            return {"status": "LINKEDIN_ABSENCE_NOT_ESTABLISHED_READBACK_ONLY", "publish_called": False}
        self.store.register_readback(readback_id="owner-absent-" + sha256_of([context, result]),
            dispatch_id=dispatch_id, readback_data=_canonical_json({"dispatch_id": dispatch_id,
                "absence_basis": "OWNER_REPORT_AND_FRESH_LOADED_OWN_ACTIVITY", "owner_context": context,
                "native_observation": result, "readback": {"verified": False, "write_absent": True}}))
        ids = self._ids(message["work_item_id"], original["plan_hash"], "linkedin")
        self.store.register_reconciliation(reconciliation_id=ids["reconciliation_id"],
            work_item_id=message["work_item_id"], status=RECONCILED_ABSENT_SAFE_TO_RETRY)
        self.store.set_reconciliation_status(ids["reconciliation_id"], RECONCILED_ABSENT_SAFE_TO_RETRY)
        self.store.set_dispatch_status(dispatch_id, RECONCILED_ABSENT_SAFE_TO_RETRY)
        self.store.set_outbox_status(message["message_id"], RECONCILED_ABSENT_SAFE_TO_RETRY)
        return {"status": RECONCILED_ABSENT_SAFE_TO_RETRY, "publish_called": False,
            "dispatch_id": dispatch_id, "absence_basis": "OWNER_REPORT_AND_FRESH_LOADED_OWN_ACTIVITY"}

    def publish_reviewed_linkedin_company_copy(self, *, run_id, review_reference):
        """One explicitly selected company copy of the same reviewed LinkedIn payload."""
        from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
        from live_contentops.native_desktop_editorial_v1 import dated_distribution_recovery_acceptance
        recovery, _ = dated_distribution_recovery_acceptance(self.store, run_id=run_id, reference=review_reference)
        if recovery.get("recipients", {}).get("linkedin_company") != "linkedin:company:143198922":
            raise ValueError("LINKEDIN_COMPANY_EXPLICIT_SAME_REVIEW_REQUIRED")
        if self._confirmed_canonical_url_for_work_item(run_id, plan_hash=recovery["plan_hash"]) != recovery["canonical_url"]:
            raise ValueError("DATED_DISTRIBUTION_CANONICAL_IDENTITY_CHANGED")
        source_ids = self._ids(run_id, recovery["plan_hash"], "linkedin")
        source = self.store.get_outbox_message(source_ids["message_id"])
        original = json.loads(source["payload"])
        if sha256_of(original) != recovery["original_intent_sha256"]["linkedin"]:
            raise ValueError("DATED_DISTRIBUTION_ORIGINAL_INTENT_CHANGED")
        payload = recovery["payloads"]["linkedin"]
        registration = registration_for_destination("linkedin_company")
        intent = {**original, "native_payload": payload, "payload": payload["text"],
            "dated_distribution_recovery": review_reference, "company_copy_of_message_id": source["message_id"],
            "owner_authority_ref": recovery["owner_authority_ref"],
            "destination_plan": {**original["destination_plan"], "destination": "linkedin_company",
                "surface": registration.surface, "transport_type": registration.transport_type,
                "expected_identity": registration.expected_identity, "payload_hash": sha256_of(payload),
                "payload_hash_kind": "OWNER_SELECTED_REVIEWED_LINKEDIN_COMPANY_COPY"}}
        ids = self._ids(run_id, recovery["plan_hash"], "linkedin_company")
        prior = self.store.get_outbox_message(ids["message_id"])
        if prior and json.loads(prior["payload"]) != intent:
            # Earlier generic finalization looked for a ninth compiled package
            # and replaced this reviewed, still-unclaimed copy with an empty one.
            empty = {**intent, "native_payload": {}, "payload": "",
                "destination_plan": {**intent["destination_plan"], "payload_hash": sha256_of({}),
                    "payload_hash_kind": "FINAL_CANONICAL_URL_BOUND_BYTES"}}
            if (json.loads(prior["payload"]) != empty
                    or self.store.get_platform_dispatch(ids["dispatch_id"])):
                raise ValueError("LINKEDIN_COMPANY_IMMUTABLE_COPY_CONFLICT")
            self.store.finalize_outbox_payload_before_dispatch(message_id=ids["message_id"],
                payload=_canonical_json(intent), status="READY")
        message = self.store.register_outbox_message(message_id=ids["message_id"], work_item_id=run_id,
            destination="linkedin_company", payload=_canonical_json(intent), status="READY")
        return self._dispatch_message(message, canonical_url=recovery["canonical_url"],
            explicit_transport_correction_retry=True)

    def complete_dated_distribution_recovery(self, message_id, *, review_reference):
        """One owner-approved dated send on an absent/never-attempted existing destination."""
        from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
        from live_contentops.native_desktop_editorial_v1 import dated_distribution_recovery_acceptance
        message = self.store.get_outbox_message(message_id)
        if not message or message["destination"] not in {"facebook_page", "instagram_business", "youtube", "linkedin"}:
            raise ValueError("DATED_DISTRIBUTION_EXACT_ORIGINAL_DESTINATION_REQUIRED")
        recovery, _ = dated_distribution_recovery_acceptance(self.store,
            run_id=message["work_item_id"], reference=review_reference)
        if message["destination"] not in recovery["payloads"]:
            raise ValueError("DATED_DISTRIBUTION_EXACT_ORIGINAL_DESTINATION_REQUIRED")
        intent = json.loads(message["payload"])
        ids = self._ids(message["work_item_id"], intent["plan_hash"], message["destination"])
        dispatch = self.store.get_platform_dispatch(ids["dispatch_id"])
        if dispatch and dispatch["status"] != NATIVE_NEO_PENDING:
            reconciled = any(r["reconciliation_id"] == ids["reconciliation_id"]
                and r["status"] == RECONCILED_ABSENT_SAFE_TO_RETRY
                for r in self.store.get_reconciliations_for_work_item(message["work_item_id"]))
            if (dispatch.get("public_object_id") or not reconciled or dispatch["status"] not in {
                    RECONCILED_ABSENT_SAFE_TO_RETRY, DERIVATIVE_RECOVERY_RETRY_EXHAUSTED_NO_WRITE,
                    DERIVATIVE_EXPIRED_STALE_NO_WRITE}):
                return {"status": "DATED_DISTRIBUTION_EXISTING_OR_AMBIGUOUS_OBJECT_READBACK_ONLY", "publish_called": False}
        elif not dispatch and message["status"] != DERIVATIVE_EXPIRED_STALE_NO_WRITE:
            return {"status": "DATED_DISTRIBUTION_NEVER_ATTEMPTED_EXPIRED_INTENT_REQUIRED", "publish_called": False}
        if self._confirmed_canonical_url_for_work_item(message["work_item_id"], plan_hash=intent["plan_hash"]) != recovery["canonical_url"]:
            raise ValueError("DATED_DISTRIBUTION_CANONICAL_IDENTITY_CHANGED")
        correction_id = "dated-distribution-" + review_reference["request_sha256"]
        if self._transport_correction_already_attempted(ids["dispatch_id"], correction_id):
            return {"status": "DATED_DISTRIBUTION_ALREADY_ATTEMPTED_READBACK_ONLY", "publish_called": False}
        amendment = {"original_intent_sha256": sha256_of(intent), "review_reference": review_reference}
        key = "native-dated-distribution-" + sha256_of(message_id)
        prior = self.store.get_outbox_message(key)
        if prior and json.loads(prior["payload"]) != amendment:
            raise ValueError("DATED_DISTRIBUTION_IMMUTABLE_REVIEW_CONFLICT")
        self.store.register_outbox_message(message_id=key, work_item_id=message["work_item_id"],
            destination="internal:native-desktop-editorial", payload=_canonical_json(amendment), status="EDITORIAL_INTERNAL")
        outcome = self._dispatch_message(message, canonical_url=recovery["canonical_url"],
            explicit_transport_correction_retry=True, explicit_reconciled_absent_retry=message["destination"] == "linkedin")
        if outcome.get("publish_called") is True:
            self._record_transport_correction_attempt(ids["dispatch_id"], correction_id, message["work_item_id"])
        return outcome

    def reconcile_completed_native_publish(self, dispatch_id, *, request_hash):
        """Consume an actual completed native write return; this never calls publish."""
        from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
        from live_contentops.neo_destination_handoff_v1 import _public_url, IDENTITIES
        dispatch = self.store.get_platform_dispatch(dispatch_id) or {}
        message = self.store.get_outbox_message(dispatch.get("message_id", ""))
        executor = getattr(getattr(self.transport_runtime, "_neo_transport", None), "native_executor", None)
        if (not message or not getattr(executor, "native_neo_protocol", False)
                or executor.operation_id != message["work_item_id"]):
            raise ValueError("EXACT_COMPLETED_NATIVE_PUBLISH_BINDING_REQUIRED")
        packet, response = executor._get(request_hash, "request"), executor._get(request_hash, "response")
        request, result = (packet or {}).get("request", {}), (response or {}).get("result", {})
        observed = result.get("native_tool_observation") or {}
        intent = json.loads(self._effective_message(message)["payload"])
        ids = self._ids(message["work_item_id"], intent["plan_hash"], message["destination"])
        if (dispatch_id != ids["dispatch_id"] or request.get("action") != "PUBLISH"
                or request.get("destination") != message["destination"]
                or request.get("expected_identity") != IDENTITIES.get(message["destination"])
                or request.get("dispatch_attempt_identity") != dispatch_id
                or request.get("work_item_id") != message["work_item_id"]
                or request.get("intent_sha256") != sha256_of(intent)
                or request.get("request_sha256") != request_hash or result.get("request_sha256") != request_hash
                or observed.get("tool_name") != "mcp__browseros_neo__run"
                or not executor._claim(request_hash, observed.get("native_invocation_id"))
                or not result.get("native_tool_return_sha256")
                or result.get("observed_identity") != request.get("expected_identity")
                or not result.get("public_object_id")
                or not _public_url(message["destination"], result.get("public_object_url"), result.get("public_object_id"))):
            raise ValueError("EXACT_COMPLETED_NATIVE_PUBLISH_RETURN_REQUIRED")
        registration = self._intent_registration(message["destination"], intent)
        normalized = normalize_dispatch_result(result, destination=message["destination"],
            surface=registration.surface, transport_type=registration.transport_type)
        if normalized["status"] != DISPATCH_CONFIRMED:
            raise ValueError("COMPLETED_NATIVE_PUBLISH_STABLE_IDENTITY_REQUIRED")
        self.store.register_platform_dispatch(dispatch_id=dispatch_id, message_id=message["message_id"],
            platform=message["destination"], status=dispatch["status"],
            public_object_id=normalized["public_object_id"], public_object_url=normalized["public_object_url"])
        self.store.set_dispatch_status(dispatch_id, DISPATCH_CONFIRMED)
        self.store.set_outbox_status(message["message_id"], DISPATCH_CONFIRMED)
        # A newly observed public object supersedes the old attempt's absence.
        # While native readback waits, recovery must not expire or retry it.
        if any(row["reconciliation_id"] == ids["reconciliation_id"]
                and row["status"] == RECONCILED_ABSENT_SAFE_TO_RETRY
                for row in self.store.get_reconciliations_for_work_item(message["work_item_id"])):
            self.store.set_reconciliation_status(ids["reconciliation_id"], RECONCILIATION_PENDING)
        current = self.store.get_platform_dispatch(dispatch_id)
        status = self._reconcile(current, intent)
        return {"dispatch_id": dispatch_id, "destination": message["destination"],
            "public_object_id": current["public_object_id"], "public_object_url": current["public_object_url"],
            "reconciliation_status": status, "publish_called": False, "public_write_performed": False}

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

    @classmethod
    def publication_totals(cls, outcomes: Mapping[str, Any], *, full_v1: bool = True) -> dict[str, Any]:
        """Summarize exact durable destination records, independently of the latest callback."""
        canonical = dict(outcomes.get("substack") or {})
        canonical_real = cls._confirmed_public_object(canonical, destination="substack")
        derivatives = {d: dict(o) for d, o in outcomes.items() if d != "substack"
            and (not full_v1 or d in V1_REQUIRED_DERIVATIVE_DESTINATIONS)}
        additional = {d: dict(o) for d, o in outcomes.items() if d != "substack" and d not in derivatives}
        confirmed = {d for d, o in derivatives.items() if cls._confirmed_public_object(o, destination=d)}
        required = set(V1_REQUIRED_DERIVATIVE_DESTINATIONS) if full_v1 else set(derivatives)
        missing = sorted(required - confirmed)
        distribution = (
            FULL_V1_NINE_SURFACE_PUBLICATION_CONFIRMED if full_v1 and not missing
            else PARTIAL_DISTRIBUTION_RECOVERY_REQUIRED if full_v1
            else "CANONICAL_PUBLISHED_DISTRIBUTION_COMPLETE" if not missing
            else "CANONICAL_PUBLISHED_READY_FANOUT_ATTEMPTED"
        ) if canonical_real else "CANONICAL_NOT_CONFIRMED"
        return {
            "canonical_article_status": "REAL_PUBLISHED" if canonical_real else "NOT_CONFIRMED",
            "canonical_article_real_published": canonical_real,
            "canonical_url": canonical.get("public_object_url") if canonical_real else None,
            "canonical_publication_status": distribution,
            "distribution_status": distribution,
            "transaction_classification": distribution,
            "derivative_confirmed_count": len(confirmed),
            "derivative_attempted_count": sum(bool(o.get("dispatch_recorded")) for o in derivatives.values()),
            "derivative_unknown_count": sum(o.get("status") == UNKNOWN_WRITE for o in derivatives.values()),
            "derivative_absent_safe_to_retry_count": sum(
                o.get("reconciliation_status") == RECONCILED_ABSENT_SAFE_TO_RETRY for o in derivatives.values()),
            "derivative_failed_count": sum(o.get("status") in {
                DEFINITE_NO_WRITE, DERIVATIVE_RECOVERY_RETRY_EXHAUSTED_NO_WRITE,
                DERIVATIVE_EXPIRED_STALE_NO_WRITE} for o in derivatives.values()),
            "derivative_never_attempted_count": sum(not o.get("dispatch_recorded") for o in derivatives.values()),
            "recovery_required_destinations": missing if canonical_real else [],
            "readback_limitation_destinations": sorted(d for d, o in derivatives.items()
                if o.get("reconciliation_status") == RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE),
            "unknown_write_detected": any(o.get("status") == UNKNOWN_WRITE for o in outcomes.values()),
            "unknown_write_count": sum(o.get("status") == UNKNOWN_WRITE for o in outcomes.values()),
            **({"additional_destinations": additional,
                "additional_confirmed_count": sum(cls._confirmed_public_object(o, destination=d) for d, o in additional.items()),
                "additional_recovery_required_destinations": sorted(d for d, o in additional.items()
                    if not cls._confirmed_public_object(o, destination=d))} if additional else {}),
        }

    def publication_state(self, work_item_id: str, plan: Mapping[str, Any]) -> dict[str, Any]:
        """Read this exact operation/plan from the existing store; never probe or dispatch."""
        plan_hash = str(plan.get("plan_hash") or _hash(_canonical_json(plan)))
        reconciliations = {str(r["reconciliation_id"]): r
            for r in self.store.get_reconciliations_for_work_item(work_item_id)}
        outcomes = {}
        destinations = list(plan.get("destinations") or [])
        company = self._ids(work_item_id, plan_hash, "linkedin_company")
        if self.store.get_outbox_message(company["message_id"]):
            destinations.append({"destination": "linkedin_company"})
        for item in destinations:
            destination = str(item.get("destination") or "")
            if destination not in {*V1_REQUIRED_PUBLICATION_DESTINATIONS, "linkedin_company"}:
                continue
            ids = self._ids(work_item_id, plan_hash, destination)
            message = self.store.get_outbox_message(ids["message_id"])
            intent = json.loads(str(message["payload"])) if message else {}
            admitted = (str(intent.get("work_item_id") or "") == work_item_id
                and str(intent.get("plan_hash") or "") == plan_hash)
            dispatch = (self.store.get_platform_dispatch(ids["dispatch_id"]) or {}) if admitted else {}
            dispatch = self.effective_dispatch(dispatch, self.store.list_platform_dispatches()) if dispatch.get("status") in OWNER_RETIRED_STATUSES else dispatch
            reconciliation = reconciliations.get("reconciliation_" + dispatch["dispatch_id"].removeprefix("dispatch_"), {}) if dispatch else {}
            outcomes[destination] = {
                "destination": destination, "dispatch_id": dispatch.get("dispatch_id", ids["dispatch_id"]),
                "dispatch_recorded": bool(dispatch),
                "status": dispatch.get("status", "NOT_DISPATCHED"),
                "reconciliation_status": reconciliation.get("status"),
                "public_object_id": dispatch.get("public_object_id"),
                "public_object_url": dispatch.get("public_object_url"),
                "publish_called": False,
            }
        return {"per_destination": outcomes, **self.publication_totals(
            outcomes, full_v1=self._full_v1_distribution_required(plan))}

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
        from live_contentops.native_newsroom_volume_v1 import permitted_photo_less_skip
        permitted_skips = {"instagram_business"} if permitted_photo_less_skip(plan) else set()
        structural_blockers = {
            "missing_destinations": sorted(required - observed),
            "unexpected_destinations": sorted(observed - required),
            "duplicate_destinations": duplicate_destinations,
            "skipped_derivative_destinations": [d for d in skipped if d not in permitted_skips],
            "pre_substack_blockers": sorted(
                str(value) for value in (plan.get("pre_substack_blockers") or [])
                if str(value)
            ),
        }
        plan_hash = str(plan.get("plan_hash") or _hash(_canonical_json(plan)))
        readiness_rows: dict[str, Any] = {}
        readiness_blockers: list[str] = []
        confirmed_canonical = self._confirmed_canonical_url_for_work_item(work_item_id, plan_hash=plan_hash)
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
            if confirmed_canonical:
                readiness_rows[destination] = {
                    "readiness_state": RECONCILED_CONFIRMED, "identity_match": True,
                    "write_eligible": False, "canonical_write_already_confirmed": True,
                    "public_object_url": confirmed_canonical,
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
        from live_contentops.native_newsroom_volume_v1 import permitted_photo_less_skip
        permitted_skips = {"instagram_business"} if permitted_photo_less_skip(plan) else set()
        for item in sorted(plan.get("destinations") or [], key=lambda row: (
            0 if str(row.get("destination")) == "substack" else 1,
            str(row.get("destination")),
        )):
            destination = str(item.get("destination") or "")
            if destination in permitted_skips:
                continue
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
        original_message = self.store.get_outbox_message(str(dispatch.get("message_id") or ""))
        if original_message:
            resolved = self._effective_message(original_message)
            if resolved["payload"] != original_message["payload"]:
                intent = json.loads(resolved["payload"])
        destination = str(dispatch["platform"])
        object_id = str(dispatch.get("public_object_id") or "") or None
        ids = self._ids(str(intent["work_item_id"]), str(intent["plan_hash"]), destination)
        ids["reconciliation_id"] = "reconciliation_" + dispatch_id.removeprefix("dispatch_")
        registration = self._intent_registration(destination, intent)
        self._record_runtime_activity(
            intent,
            "CANONICAL_READBACK" if destination == "substack" else "RECONCILIATION",
            destination=destination,
        )
        try:
            if registration.transport_type in {"EDGE_CDP", "BROWSEROS_NEO_MCP"} and self.readiness_manager is not None:
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
        except NativeNeoInputRequired:
            # Waiting for the active Desktop tool is not an observed readback failure.
            # Keep all existing public identity and reconciliation evidence intact.
            return RECONCILIATION_PENDING
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
        message = self._effective_message(message)
        intent = json.loads(str(message["payload"]))
        destination = str(message["destination"])
        item = dict(intent["destination_plan"])
        registration = self._intent_registration(destination, intent)
        ids = self._ids(str(intent["work_item_id"]), str(intent["plan_hash"]), destination)
        existing = self.store.get_platform_dispatch(ids["dispatch_id"])
        native_pending_resume = bool(existing and existing.get("status") == NATIVE_NEO_PENDING
            and registration.transport_type == "BROWSEROS_NEO_MCP")
        if native_pending_resume:
            # A background/default recovery owner cannot consume another Desktop's
            # claimed action through an unbound/read-only transport. Such a transport's
            # FAILED_BEFORE_WRITE result says nothing about the in-flight native action.
            executor = getattr(getattr(self.transport_runtime, "_neo_transport", None), "native_executor", None)
            if (not getattr(executor, "native_neo_protocol", False)
                    or not getattr(executor, "allow_publish", False)
                    or getattr(executor, "operation_id", None) != intent["work_item_id"]
                    or getattr(getattr(executor, "store", None), "db_path", None) != self.store.db_path):
                return {"destination": destination, "status": NATIVE_NEO_PENDING,
                    "reason_code": "EXACT_NATIVE_OPERATION_EXECUTOR_REQUIRED", "publish_called": False}
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
                        (
                            destination in {"facebook_page", "instagram_business"}
                            or (
                                destination == "linkedin"
                                and intent.get("dated_distribution_recovery")
                                and registration.transport_type == "BROWSEROS_NEO_MCP"
                            )
                        )
                        and str(existing.get("status") or "") in {
                            DERIVATIVE_RECOVERY_RETRY_EXHAUSTED_NO_WRITE,
                            RECONCILED_ABSENT_SAFE_TO_RETRY,
                            *({DERIVATIVE_EXPIRED_STALE_NO_WRITE} if intent.get("dated_distribution_recovery") else set()),
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
            if not (retry_eligible or correction_retry_eligible or native_pending_resume):
                return {
                    "destination": destination,
                    "status": str(existing["status"]),
                    "publish_called": False,
                    "public_object_id": existing.get("public_object_id"),
                    "public_object_url": existing.get("public_object_url"),
                    "reconciliation_status": reconciliation_status,
                }
            if destination == "substack" and not native_pending_resume:
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
            if explicit_reconciled_absent_retry or explicit_transport_correction_retry or native_pending_resume:
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
        mode = "AUTONOMOUS_DEFAULT" if native_pending_resume else self._mode()
        if mode != "AUTONOMOUS_DEFAULT":
            return {"destination": destination, "status": f"WRITE_BLOCKED_{mode}", "publish_called": False}
        from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
        native = self.store.get_outbox_message("native-operation-binding-" + sha256_of(intent["work_item_id"]))
        if native:
            from live_contentops.native_desktop_editorial_v1 import require_current_final_visual_review
            try:
                require_current_final_visual_review(self.store, run_id=intent["work_item_id"])
            except (ValueError, OSError, KeyError, TypeError) as visual_error:
                return {"destination": destination, "status": "FINAL_VISUAL_REPAIR_OR_REVIEW_REQUIRED",
                        "blocker": str(visual_error), "publish_called": False}
        self._record_runtime_activity(intent, "PUBLICATION_JIT", destination=destination)
        if native_pending_resume:
            # Only consume the same durable request/return. Its Desktop action claim checks
            # current mode itself; a lost claimed return becomes UNKNOWN, never another click.
            readiness = "READY_AUTHENTICATED"
        elif destination == "linkedin" and registration.transport_type == "BROWSEROS_NEO_MCP":
            executor = getattr(getattr(self.transport_runtime, "_neo_transport", None), "native_executor", None)
            if not getattr(executor, "native_neo_protocol", False):
                return {"destination": destination, "status": "EXACT_NATIVE_OPERATION_EXECUTOR_REQUIRED", "publish_called": False}
            proof = executor.readiness(registration.surface)
            readiness = "READY_AUTHENTICATED" if (proof.get("authenticated") and proof.get("native_executor_bound")
                and proof.get("proof_fresh") and proof.get("public_handle") == registration.expected_public_handle) else "SESSION_UNAVAILABLE"
        elif self.readiness_manager is not None:
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
        claimed = self.store.claim_platform_dispatch_attempt(dispatch_id=ids["dispatch_id"],
            message_id=ids["message_id"], platform=destination,
            expected_status=existing.get("status") if existing else None)
        if not claimed:
            actual = self.store.get_platform_dispatch(ids["dispatch_id"]) or {}
            return {"destination": destination, "status": actual.get("status", UNKNOWN_WRITE),
                    "publish_called": False, "reason_code": "EXACT_DISPATCH_ALREADY_CLAIMED"}
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
        registration = self._intent_registration(destination, intent)
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
        except NativeNeoInputRequired as pending:
            self.store.set_dispatch_status(ids["dispatch_id"], NATIVE_NEO_PENDING)
            self.store.set_outbox_status(ids["message_id"], NATIVE_NEO_PENDING)
            return {"destination": destination, "status": NATIVE_NEO_PENDING, "publish_called": False,
                    "native_tool_request": pending.request, "reconciliation_status": None,
                    "public_write_performed": False}
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
            and str(row.get("destination") or "") in V1_REQUIRED_PUBLICATION_DESTINATIONS
        ]
        intents = [row for row in intents if row.get("plan_hash") == intent.get("plan_hash")]
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
        if not message or destination not in {"x", "facebook_page", "instagram_business"}:
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
        canonical_url = self._confirmed_canonical_url_for_work_item(
            work_item_id, plan_hash=str(intent.get("plan_hash") or "")) or ""
        if not canonical_url or str(intent.get("canonical_url") or "") != canonical_url:
            return {
                "status": "CORRECTION_BLOCKED_CANONICAL_IDENTITY_MISMATCH",
                "publish_called": False,
            }
        # An ambiguity is local to its existing dispatch after canonical confirmation.
        # Never retry that action; an independent, proven-absent destination can repair.
        unknown_write_count = int(dispatch.get("status") in {UNKNOWN_WRITE, ATTEMPT_STARTED, NATIVE_NEO_PENDING})
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
            and str(row.get("destination") or "") in V1_REQUIRED_PUBLICATION_DESTINATIONS
        ]
        intents = [row for row in intents if row.get("plan_hash") == intent.get("plan_hash")]
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

    def refresh_confirmed_photo_attribution(self, dispatch_id: str, *, repair_missing_media: bool = False) -> dict[str, Any]:
        """Apply the owner-directed credit presentation once to an exact existing object."""
        dispatch = self.store.get_platform_dispatch(dispatch_id) or {}
        destination = str(dispatch.get("platform") or "")
        message = self.store.get_outbox_message(str(dispatch.get("message_id") or ""))
        if not message or destination not in {"telegram", "discord"} or dispatch.get("status") != DISPATCH_CONFIRMED:
            return {"status": "PHOTO_ATTRIBUTION_EXACT_CONFIRMED_OBJECT_REQUIRED", "edit_called": False}
        if repair_missing_media and destination != "discord":
            return {"status": "PHOTO_MEDIA_REPAIR_DESTINATION_NOT_SUPPORTED", "edit_called": False}
        intent = json.loads(str(message["payload"]))
        state = self.publication_state(str(intent["work_item_id"]), {
            "plan_hash": intent["plan_hash"], "destinations": [intent["destination_plan"]]})
        if not self._confirmed_public_object(state["per_destination"].get(destination) or {}, destination=destination):
            return {"status": "PHOTO_ATTRIBUTION_CURRENT_READBACK_REQUIRED", "edit_called": False}
        canonical = self._confirmed_canonical_url_for_work_item(str(intent["work_item_id"]), plan_hash=str(intent["plan_hash"]))
        if not canonical or intent.get("canonical_url") != canonical or self._mode() != "AUTONOMOUS_DEFAULT":
            return {"status": "PHOTO_ATTRIBUTION_CURRENT_LIVE_CANONICAL_REQUIRED", "edit_called": False}
        from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
        native = self.store.get_outbox_message("native-operation-binding-" + sha256_of(intent["work_item_id"]))
        if native:
            from live_contentops.native_desktop_editorial_v1 import require_current_final_visual_review
            require_current_final_visual_review(self.store, run_id=intent["work_item_id"])
        from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import _durable_intent_inputs
        rendered = _durable_intent_inputs(intent)["payloads"][destination]
        text = str(rendered.get("text") or "")
        original = str((intent.get("native_payload") or {}).get("text") or intent.get("payload") or "")
        if not text or (text == original and not repair_missing_media):
            return {"status": "PHOTO_ATTRIBUTION_NO_CHANGE", "edit_called": False}
        edit_key = "photo-attribution-" + _hash(_canonical_json([dispatch_id, text]))
        if repair_missing_media:
            # Read the exact existing object first. A failed/unknown edit, missing
            # message or changed text never authorizes another write.
            observed = self.transport_runtime.readback(destination=destination,
                public_object_id=str(dispatch["public_object_id"]),
                public_object_url=dispatch.get("public_object_url"), intent=intent)
            if not (observed.get("write_exists") is True
                    and str(observed.get("message_id")) == str(dispatch["public_object_id"])
                    and observed.get("body_text_visible") is True
                    and observed.get("substack_url_visible") is True
                    and observed.get("meaningful_media_visible") is False):
                return {"status": "PHOTO_MEDIA_REPAIR_EXACT_READBACK_REQUIRED", "edit_called": False}
            edit_key += "-missing-media-" + _hash(_canonical_json(intent.get("artifact_manifest") or []))
        prior = self.store.list_readbacks_for_dispatch(dispatch_id)
        if any(r["readback_id"] == edit_key for r in prior):
            return {"status": "PHOTO_ATTRIBUTION_ALREADY_ATTEMPTED_READBACK_ONLY", "edit_called": False}
        if self.readiness_manager is not None:
            ready = self.readiness_manager.verify_destination_jit(destination, reason="PUBLICATION", persist=True)
            if ready.get("readiness_state") not in READY_STATES or ready.get("identity_match") is False:
                return {"status": "PHOTO_ATTRIBUTION_IDENTITY_NOT_READY", "edit_called": False}
        self.store.register_readback(readback_id=edit_key, dispatch_id=dispatch_id,
            readback_data=_canonical_json({"action": "EDIT_EXISTING_PHOTO_ATTRIBUTION", "status": "STARTED",
                "public_object_id": dispatch["public_object_id"], "rendered_payload_sha256": _hash(text)}))
        try:
            kwargs = {"repair_missing_media": True} if repair_missing_media else {}
            result = dict(self.transport_runtime.amend_photo_attribution(destination=destination,
                intent=intent, public_object_id=str(dispatch["public_object_id"]), text=text, **kwargs))
        except Exception as exc:
            result = {"status": "UNKNOWN_EDIT", "safe_error_classification": type(exc).__name__}
        self.store.register_readback(readback_id=edit_key + "-return", dispatch_id=dispatch_id,
            readback_data=_canonical_json({"action": "EDIT_EXISTING_PHOTO_ATTRIBUTION", "result": result}))
        if result.get("verified") is True:
            self._reconcile(dispatch, intent)
        return {**result, "edit_called": True, "new_post_calls": 0}

    def execute_plan(self, work_item_id: str, plan: Mapping[str, Any]) -> dict[str, Any]:
        result = self._execute_plan(work_item_id, plan)
        current = self.publication_state(work_item_id, plan)
        if any(o["dispatch_recorded"] for o in current["per_destination"].values()):
            callbacks = result.get("per_destination") or {}
            merged = {d: dict(o) for d, o in callbacks.items()}
            for destination, durable in current["per_destination"].items():
                callback = dict(callbacks.get(destination) or {})
                merged[destination] = ({**callback, **durable} if durable["dispatch_recorded"]
                    else {**durable, **callback})
                merged[destination]["publish_called"] = callback.get("publish_called") is True
            current = {"per_destination": merged, **self.publication_totals(
                merged, full_v1=self._full_v1_distribution_required(plan))}
            if (not current["canonical_article_real_published"] and
                    str(result.get("distribution_status") or "").startswith(("BLOCKED_", "HOLD_"))):
                current.update({k: result[k] for k in ("distribution_status", "canonical_publication_status",
                    "transaction_classification") if k in result})
            result = {**result, **current}
        return result

    def _execute_plan(self, work_item_id: str, plan: Mapping[str, Any]) -> dict[str, Any]:
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
        messages = [m for m in self.store.list_outbox_messages() if m["work_item_id"] == work_item_id
            and m["destination"] in V1_REQUIRED_PUBLICATION_DESTINATIONS
            and json.loads(str(m["payload"])).get("plan_hash") == plan.get("plan_hash")]
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
        from live_contentops.native_newsroom_volume_v1 import permitted_photo_less_skip
        no_media_needed = permitted_photo_less_skip(plan) and plan.get("media_asset_count") == 0
        if canonical_url and callable(delivery_preparer) and quality_preflight is not None and not no_media_needed:
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

    def _confirmed_canonical_url_for_work_item(
        self, work_item_id: str, *, plan_hash: str | None = None
    ) -> Optional[str]:
        for message in self.store.list_outbox_messages():
            if str(message.get("work_item_id") or "") != work_item_id or str(
                message.get("destination") or ""
            ) != "substack":
                continue
            if plan_hash is not None and json.loads(str(message["payload"])).get("plan_hash") != plan_hash:
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
            if dispatch and dispatch.get("status") in OWNER_RETIRED_STATUSES:
                continue
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
            if status == NATIVE_NEO_PENDING:
                # Resume only the exact native tool request. No adapter retry is allocated.
                outcome = self._dispatch_message(message, canonical_url=intent.get("canonical_url"))
                summary["per_destination"][str(message["destination"])] = outcome
                continue
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
                                unknown_count = self._active_unknown_write_count()
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
            if dispatch and dispatch.get("status") in OWNER_RETIRED_STATUSES:
                continue
            destination = str(message["destination"])
            if dispatch and dispatch.get("status") == NATIVE_NEO_PENDING:
                remaining_destinations.append(destination)
                remaining_obligations.append({"work_item_id": str(intent["work_item_id"]),
                    "destination": destination, "durable_status": NATIVE_NEO_PENDING,
                    "blocking_status": NATIVE_NEO_PENDING, "reconciliation_status": ""})
                continue
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

    def readback_existing_dispatch(self, dispatch_id: str) -> dict[str, Any]:
        """Refresh one already persisted object through the existing strict reconciliation.

        This operation never calls publish, saves a draft or allocates a new dispatch. It
        also works under the paused/KILL_SWITCH mode and preserves prior proof while the
        native Desktop readback tool request is pending.
        """
        dispatch = self.store.get_platform_dispatch(dispatch_id)
        if not dispatch or dispatch.get("status") not in {DISPATCH_CONFIRMED, UNKNOWN_WRITE, ATTEMPT_STARTED}:
            raise ValueError("EXISTING_PUBLIC_OR_AMBIGUOUS_DISPATCH_REQUIRED")
        message = self.store.get_outbox_message(dispatch["message_id"])
        message = self._effective_message(message) if message else None
        intent = json.loads(message["payload"]) if message else {}
        expected = self._ids(str(intent.get("work_item_id")), str(intent.get("plan_hash")), str(dispatch["platform"]))
        survivor_id = self._survivor_dispatch_id(expected["dispatch_id"], dispatch.get("public_object_id"))
        if dispatch_id not in {expected["dispatch_id"], survivor_id} or expected["message_id"] != dispatch["message_id"]:
            raise ValueError("EXISTING_DISPATCH_INTENT_BINDING_MISMATCH")
        status = self._reconcile(dispatch, intent)
        return {"dispatch_id": dispatch_id, "destination": dispatch["platform"],
                "reconciliation_status": status, "public_write_performed": False,
                "publish_called": False}

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
    """Single transport router; explicit reviewed LinkedIn recovery may use native Neo."""

    def __init__(self, *, linkedin_transport: Any = None, neo_transport: Any = None) -> None:
        self._strict_publish_readbacks: dict[tuple[str, str], Mapping[str, Any]] = {}
        if linkedin_transport is None:
            from live_contentops.linkedin_official_member_api_v1 import (
                LinkedInOfficialMemberApiTransportV1,
            )
            linkedin_transport = LinkedInOfficialMemberApiTransportV1()
        self._linkedin_transport = linkedin_transport
        if neo_transport is None:
            from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff
            neo_transport = NeoDestinationHandoff()
        self._neo_transport = neo_transport

    def amend_reader_presentation(self, *, destination, intent, public_object_id, public_object_url,
                                  authorization_context):
        if (authorization_context.get("action") != "EDIT_EXISTING" or not intent.get("reader_presentation_review")
                or authorization_context.get("destination") != destination
                or authorization_context.get("payload_hash") != intent.get("destination_plan", {}).get("payload_hash")):
            raise ValueError("SOLE_COORDINATOR_REVIEWED_EDIT_AUTHORIZATION_REQUIRED")
        if destination == "facebook_page":
            from live_contentops.facebook_page_adapter_v6 import execute_facebook_edit
            return execute_facebook_edit(post_id=public_object_id, message=intent["native_payload"]["text"], dry_run=False)
        return self._neo_transport.amend_existing(destination=destination, intent=intent,
            public_object_id=public_object_id, public_object_url=public_object_url,
            authorization_context=authorization_context)

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

    def amend_photo_attribution(self, *, destination, intent, public_object_id, text, repair_missing_media=False):
        """Use existing exact-message edit adapters; never create or replace a public post."""
        canonical = str(intent["canonical_url"])
        if destination == "telegram":
            from live_contentops.telegram_live_adapter_v6 import execute_telegram_caption_edit
            from live_contentops.public_dispatch_freeze_guard_v6 import (
                build_public_dispatch_payload_hash, make_public_dispatch_approval_marker)
            topic = _hash(str(intent.get("package_identity") or ""))
            digest = build_public_dispatch_payload_hash(platform="telegram", action="edit_caption",
                body_text=text, canonical_url=canonical, topic_hash=topic)
            raw = execute_telegram_caption_edit(public_object_id, text, dry_run=False, approval_context={
                "operator_approval_marker": make_public_dispatch_approval_marker(run_id=intent["work_item_id"],
                    topic_hash=topic, payload_hash=digest, platform="telegram"),
                "run_id": intent["work_item_id"], "topic_hash": topic, "payload_hash": digest,
                "canonical_url": canonical, "canonical_packet_status": "PASS",
                "canonicalization_repair": True, "canonicalization_repair_message_id": public_object_id})
            observed = (raw.get("response") or {}).get("result") or {}
            verified = (raw.get("status") == "SUCCESS" and str(observed.get("message_id")) == public_object_id
                and (observed.get("chat") or {}).get("username", "").casefold() == "capitalchronicle"
                and observed.get("caption") == text and bool(observed.get("photo")))
        elif destination == "discord":
            from live_contentops.discord_live_adapter_v6 import execute_discord_edit, readback_discord_post
            kwargs = {}
            if repair_missing_media:
                from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import _durable_intent_inputs
                data = _durable_intent_inputs(intent)
                primary = data["primary_media"]
                if (not data["public_image_url"] or not data["media_assets"]
                        or primary.get("local_public_hash_continuity") is not True
                        or primary.get("sha256") != primary.get("public_delivery_sha256")
                        or primary.get("sha256") not in {a["sha256"] for a in data["media_assets"]}):
                    return {"status": "PHOTO_MEDIA_BOUND_DELIVERY_REQUIRED", "verified": False}
                kwargs["embeds"] = [{"title": data["article"].get("title"), "url": canonical,
                    "image": {"url": data["public_image_url"]}}]
            raw = execute_discord_edit(public_object_id, text, dry_run=False, **kwargs)
            observed = readback_discord_post(message_id=public_object_id, expected_text=text,
                canonical_url=canonical) if raw.get("status") == "SUCCESS" else {}
            verified = observed.get("status") == "SUCCESS"
        else:
            return {"status": "PHOTO_ATTRIBUTION_DESTINATION_NOT_SUPPORTED", "verified": False}
        if verified:
            self._strict_publish_readbacks[(destination, public_object_id)] = {"presentation_edit": True}
        return {"status": "SUCCESS" if verified else "PHOTO_ATTRIBUTION_EDIT_NOT_VERIFIED",
            "verified": bool(verified), "public_object_id": public_object_id,
            "canonical_url": canonical, "safe_error_classification": raw.get("error_code")}

    def publish(self, *, destination: str, intent: Mapping[str, Any],
                authorization_context: Mapping[str, Any]) -> Mapping[str, Any]:
        if destination in {"substack", "x", "youtube", "linkedin_company"} or (destination == "linkedin"
                and intent.get("dated_distribution_recovery")
                and intent.get("destination_plan", {}).get("transport_type") == "BROWSEROS_NEO_MCP"):
            return self._neo_transport.publish(destination=destination, intent=intent,
                                                authorization_context=authorization_context)
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
        if destination == "linkedin_company" and intent.get("dated_distribution_recovery"):
            if (canonical_url != intent.get("canonical_url")
                    or intent.get("destination_plan", {}).get("payload_hash_kind")
                    != "OWNER_SELECTED_REVIEWED_LINKEDIN_COMPANY_COPY"
                    or not intent.get("native_payload")):
                raise ValueError("LINKEDIN_COMPANY_EXACT_REVIEWED_COPY_REQUIRED")
            return finalized
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
        if intent.get("reader_presentation_review") and destination != "facebook_page":
            return self._neo_transport.readback(destination=destination, intent=intent,
                public_object_id=public_object_id, public_object_url=public_object_url)
        if destination in {"substack", "x", "youtube", "linkedin_company"} or (destination == "linkedin"
                and intent.get("dated_distribution_recovery")
                and intent.get("destination_plan", {}).get("transport_type") == "BROWSEROS_NEO_MCP"):
            result = self._neo_transport.readback(destination=destination, intent=intent,
                public_object_id=public_object_id, public_object_url=public_object_url)
            if destination == "substack" and result.get("verified") is True and result.get("public_image_urls"):
                from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import _durable_intent_inputs
                from live_contentops.media_manifest_authority_v1 import build_delivery_media_manifest
                data = _durable_intent_inputs(intent)
                delivery = build_delivery_media_manifest(media_packet={"assets": data["media_assets"]},
                    public_image_urls=result["public_image_urls"], run_id=str(intent["work_item_id"]))
                path = data["output_dir"] / "delivery_media_manifest_v1.json"
                previous = json.loads(path.read_bytes()) if path.is_file() else {}
                delivery_only = [a for a in previous.get("assets", []) if a.get("media_role") == "delivery_only"]
                delivery["assets"].extend(delivery_only)
                if any(a.get("local_public_hash_continuity") is not True for a in delivery_only):
                    delivery["status"] = "BLOCKED"
                path.write_text(_canonical_json(delivery), encoding="utf-8")
            return result
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
        if destination in {"substack", "x", "youtube"}:
            return {"status": "UNSUPPORTED", "reason": "NEO_NATIVE_METRICS_EXECUTOR_NOT_BOUND",
                    "public_write_performed": False}
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
