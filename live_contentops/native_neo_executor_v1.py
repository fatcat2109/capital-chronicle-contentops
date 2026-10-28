"""Durable tool requests for the active Codex Desktop Neo executor.

Python does not call MCP. The active conversation begins the exact persisted request,
executes BrowserOS Neo, submits the observed return, and resumes the same coordinator.
Requests, action claims and returns use the existing outbox. A claimed publish with no
return is ambiguous and can only enter the coordinator's readback/recovery path.
"""
from __future__ import annotations

import json
from hashlib import sha256
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

from live_contentops.capital_chronicle_latest_report_consumer_v1 import (
    _private, canonical_bytes, sha256_of,
)

SCHEMA = "contentops.native_neo_tool_request.v1"
DESTINATION = "internal:native-neo-tool"
PENDING = "NATIVE_NEO_TOOL_PENDING"
TOOL = "mcp__browseros_neo__run"


class NativeNeoInputRequired(Exception):
    def __init__(self, request: Mapping[str, Any]):
        self.request = dict(request)
        super().__init__(PENDING)


class NativeNeoExecutor:
    """Callable executor and readiness provider bound to one active Desktop operation."""

    native_neo_protocol = True

    def __init__(self, store, *, operation_id: str, output_dir: str | Path,
                 native_invocation_id: str, allow_publish: bool = False, clock=None):
        if not operation_id or not native_invocation_id:
            raise ValueError("NATIVE_NEO_ACTIVE_INVOCATION_REQUIRED")
        self.store = store
        self.operation_id = operation_id
        self.root = Path(output_dir)
        self.native_invocation_id = native_invocation_id
        self.allow_publish = allow_publish
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def _key(self, request_hash, kind):
        return "native-neo-" + sha256_of([self.operation_id, request_hash, kind])

    def _get(self, request_hash, kind):
        row = self.store.get_outbox_message(self._key(request_hash, kind))
        return json.loads(row["payload"]) if row else None

    def _claim(self, request_hash, invocation_id):
        original = self._get(request_hash, "started")
        if original and original["native_invocation_id"] == invocation_id:
            return original
        return self._get(request_hash, "started-readonly-" + sha256_of(invocation_id))

    def _put(self, request_hash, kind, value, work):
        if _private(value):
            raise ValueError("PRIVATE_NATIVE_NEO_MATERIAL_EXCLUDED")
        previous = self._get(request_hash, kind)
        if previous is not None and previous != value:
            raise ValueError("NATIVE_NEO_IMMUTABLE_RETURN_CONFLICT")
        row = self.store.register_outbox_message(
            message_id=self._key(request_hash, kind), work_item_id=work,
            destination=DESTINATION, payload=canonical_bytes(value).decode(),
            status="NATIVE_NEO_INTERNAL",
        )
        if json.loads(row["payload"]) != value:
            raise ValueError("NATIVE_NEO_IMMUTABLE_RETURN_CONFLICT")

    def __call__(self, request):
        request = dict(request)
        request_hash = request.get("request_sha256")
        if request_hash != sha256_of({k: v for k, v in request.items() if k != "request_sha256"}):
            raise ValueError("NATIVE_NEO_REQUEST_HASH_INVALID")
        if request["action"] == "PUBLISH" and not self.allow_publish:
            return {"status": "FAILED_BEFORE_WRITE", "definite_no_write": True,
                    "request_sha256": request_hash, "observed_identity": request["expected_identity"],
                    "reason_code": "NATIVE_NEO_OPERATION_READ_ONLY", "public_write_performed": False}
        work = request["work_item_id"]
        packet = {"schema_version": SCHEMA, "operation_id": self.operation_id,
                  "required_tool": TOOL, "request": request,
                  "action_boundary": "BEGIN_BEFORE_TOOL_ACTION; SUBMIT_OBSERVED_RETURN; RESUME_COORDINATOR",
                  "public_write_authorized": request["action"] == "PUBLISH" and self.allow_publish}
        packet["tool_request_sha256"] = sha256_of(packet)
        self._put(request_hash, "request", packet, work)
        response = self._get(request_hash, "response")
        if response:
            return dict(response["result"])
        started = self._get(request_hash, "started")
        if started and request["action"] == "PUBLISH":
            return {"status": "UNKNOWN_WRITE", "request_sha256": request_hash,
                    "observed_identity": request["expected_identity"],
                    "reason_code": "NATIVE_NEO_CLAIMED_ACTION_WITHOUT_RETURN", "retry_permitted": False}
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / (request_hash + ".request.json")
        path.write_bytes(canonical_bytes(packet))
        raise NativeNeoInputRequired({**packet, "request_path": str(path)})

    def begin(self, request_hash: str):
        """Claim once before a platform action; a restart never repeats a claimed write."""
        packet = self._get(request_hash, "request")
        if not packet:
            raise ValueError("NATIVE_NEO_REQUEST_NOT_FOUND")
        request = packet["request"]
        original = self._get(request_hash, "started")
        claim_kind = "started"
        if original:
            # Lost observations can be reacquired by a later native turn. Keep the
            # original claim immutable; a claimed public write is NEVER reclaimed.
            if request["action"] not in {"READBACK", "VERIFY_IDENTITY"} or self._claim(request_hash, self.native_invocation_id):
                raise ValueError("NATIVE_NEO_ACTION_ALREADY_CLAIMED_READBACK_ONLY")
            claim_kind = "started-readonly-" + sha256_of(self.native_invocation_id)
        if request["action"] == "PUBLISH":
            from live_contentops.llm_operator_control_v1 import assert_llm_operator_execution_enabled
            assert_llm_operator_execution_enabled()
            if not self.allow_publish or self.store.get_operating_control()["operating_mode"] != "AUTONOMOUS_DEFAULT":
                raise ValueError("NATIVE_NEO_PUBLIC_WRITE_NOT_AUTHORIZED")
            dispatch = self.store.get_platform_dispatch(request["dispatch_attempt_identity"])
            if not dispatch or dispatch["status"] != PENDING:
                raise ValueError("NATIVE_NEO_EXACT_COORDINATOR_PENDING_DISPATCH_REQUIRED")
            content = request.get("content_binding") or {}
            if not content.get("expected_text_segments"):
                raise ValueError("NATIVE_NEO_EXACT_PAYLOAD_REQUIRED")
            # Fresh native account proof is rechecked at the action boundary, after any
            # pending Desktop delay. A configured login/executor flag grants no write.
            proof = self.readiness(request["surface"])
            if not proof["authenticated"] or not proof["native_executor_bound"]:
                raise ValueError("NATIVE_NEO_CURRENT_IDENTITY_REQUIRED")
            for artifact in [*content.get("artifact_manifest", []), *content.get("media_manifest", [])]:
                path = Path(str(artifact.get("path") or ""))
                if not artifact.get("sha256") or not path.is_file() or sha256(path.read_bytes()).hexdigest() != artifact["sha256"]:
                    raise ValueError("NATIVE_NEO_PAYLOAD_OR_MEDIA_BYTES_CHANGED")
        claim = {"tool_request_sha256": packet["tool_request_sha256"],
                 "native_invocation_id": self.native_invocation_id,
                 "begun_at_utc": self.clock().isoformat(), "required_tool": TOOL}
        # The unique immutable outbox key fences simultaneous Desktop claimers too.
        self._put(request_hash, claim_kind, claim, request["work_item_id"])
        return packet

    def submit(self, request_hash: str, response: Mapping[str, Any]):
        packet = self._get(request_hash, "request")
        observation = dict(response.get("tool_observation") or {})
        claim = self._claim(request_hash, observation.get("native_invocation_id"))
        if not packet or not claim or response.get("tool_request_sha256") != packet["tool_request_sha256"]:
            raise ValueError("NATIVE_NEO_TOOL_RETURN_BINDING_REQUIRED")
        if (observation.get("tool_name") != TOOL
                or observation.get("native_invocation_id") != claim["native_invocation_id"]
                or observation.get("surface") not in {"CODEX_DESKTOP_CONVERSATION", "CODEX_NATIVE_SUBAGENT"}
                or not observation.get("observation_source") or not observation.get("observed_at_utc")):
            raise ValueError("NATIVE_NEO_ACTUAL_TOOL_OBSERVATION_REQUIRED")
        observed_at = datetime.fromisoformat(observation["observed_at_utc"].replace("Z", "+00:00"))
        begun_at = datetime.fromisoformat(claim["begun_at_utc"])
        if not begun_at <= observed_at <= self.clock() + timedelta(seconds=30):
            raise ValueError("NATIVE_NEO_OBSERVATION_TIME_INVALID")
        result = dict(response["result"])
        if result.get("request_sha256") != request_hash:
            raise ValueError("NATIVE_NEO_RETURN_REQUEST_MISMATCH")
        result["native_tool_observation"] = observation
        result["native_tool_return_sha256"] = sha256_of(response)
        self._put(request_hash, "response", {"result": result}, packet["request"]["work_item_id"])
        return {"request_sha256": request_hash, "tool_return_sha256": sha256_of(response)}

    def readiness(self, surface):
        from live_contentops.destination_transport_registry_v1 import SURFACE_REGISTRY
        from live_contentops.neo_destination_handoff_v1 import IDENTITIES, ROOTS
        registration = SURFACE_REGISTRY[surface]
        destination = registration.destination_key
        work = "native-neo-operation-" + sha256_of(self.operation_id)
        self.store.create_work_item(story_id=work, work_item_id=work,
                                   title="Native Neo exact identity observation", target_surface="CONTENTOPS_READ_ONLY")
        request = {"schema_version": "contentops.neo_identity_probe.v1", "destination": destination,
                   "probe_epoch": int(self.clock().timestamp()) // 300,
                   "native_invocation_id": self.native_invocation_id,
                   "action": "VERIFY_IDENTITY", "surface": surface, "expected_identity": IDENTITIES[destination],
                   "entry_url": ROOTS[destination], "work_item_id": work,
                   "forbidden": ["login", "account_switch", "public_write", "saved_draft", "private_storage"]}
        request["request_sha256"] = sha256_of(request)
        result = self(request)
        observed = result.get("native_tool_observation") or {}
        age = self.clock() - datetime.fromisoformat(observed["observed_at_utc"].replace("Z", "+00:00"))
        current = (observed.get("native_invocation_id") == self.native_invocation_id
                   and timedelta(0) <= age <= timedelta(minutes=5))
        matched = (result.get("observed_identity") == IDENTITIES[destination]
            and (not registration.expected_stable_id or result.get("observed_stable_id") == registration.expected_stable_id))
        return {"authenticated": bool(current and matched and result.get("authenticated") is True),
                "native_executor_bound": current, "domain": result.get("observed_identity") if destination == "substack" else None,
                "public_handle": result.get("observed_identity") if destination != "substack" else None,
                "stable_id": result.get("observed_stable_id"),
                "native_invocation_id": observed.get("native_invocation_id"),
                "observation_sha256": result.get("native_tool_return_sha256"), "proof_fresh": current}

    def pending(self):
        rows = []
        for row in self.store.list_outbox_messages():
            if row["destination"] != DESTINATION:
                continue
            payload = json.loads(row["payload"])
            if payload.get("schema_version") != SCHEMA or payload.get("operation_id") != self.operation_id:
                continue
            absence = payload["request"].get("owner_absence_context")
            if payload["request"]["action"] == "READBACK" and absence:
                prior = self.store.get_platform_dispatch(absence.get("dispatch_id", "")) or {}
                if prior and prior.get("status") != "UNKNOWN_WRITE":
                    continue
            if (payload["request"]["action"] == "VERIFY_IDENTITY"
                    and payload["request"].get("native_invocation_id") not in {None, self.native_invocation_id}):
                continue
            request_hash = payload["request"]["request_sha256"]
            if self._get(request_hash, "response") is None:
                claim = (self._get(request_hash, "started") if payload["request"]["action"] == "PUBLISH"
                         else self._claim(request_hash, self.native_invocation_id))
                rows.append({**payload, "action_claimed": claim is not None})
        return rows


def bind_native_neo_coordinator(store, *, operation_id, output_dir, native_invocation_id,
                                allow_publish=False):
    """One concrete supported composition; existing API routes and sole owner are reused."""
    from live_contentops.destination_transport_registry_v1 import DestinationReadinessManager
    from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff
    from live_contentops.publication_coordinator_v1 import (
        CanonicalDestinationTransportRuntimeV1, DurablePublicationCoordinator,
    )
    executor = NativeNeoExecutor(store, operation_id=operation_id, output_dir=output_dir,
                                 native_invocation_id=native_invocation_id, allow_publish=allow_publish)
    runtime = CanonicalDestinationTransportRuntimeV1(neo_transport=NeoDestinationHandoff(native_executor=executor))
    readiness = DestinationReadinessManager(store=store, neo_readiness_provider=executor.readiness)
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=runtime, readiness_manager=readiness)
    return coordinator, executor
