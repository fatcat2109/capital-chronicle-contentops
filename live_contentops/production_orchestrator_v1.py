"""Stable, import-safe interface for the one authoritative ContentOps live pipeline.

Public compatibility APIs and canonical module/script CLIs delegate here before the
private implementation module—and therefore its provider/browser adapters—is imported.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
import json
import math
import pathlib
import re
from types import MappingProxyType
from typing import Any, Callable, Dict, FrozenSet, List, Mapping, Optional, Sequence

TASK_LABEL = "TASK_CONTENTOPS_CANONICAL_PRODUCTION_ENTRYPOINT_AND_LEGACY_LIVE_PATH_QUARANTINE_V1"
SCHEMA_VERSION = "contentops.production_orchestrator.v1"
CANONICAL_MODULE = "live_contentops._eight_platform_substack_first_pipeline_impl_v1"
CANONICAL_FUNCTION = "_dispatch_canonical_operation"
CANONICAL_OPERATIONS = frozenset(
    {
        "prepare_text_image_release_candidate",
        "prepare_generic_text_image_release_candidate",
        "build_operator_manual_audit_packet",
        "run_eight_platform_substack_first_pipeline",
        "reconcile_public_substack_for_derivative_resume",
        "resume_eight_platform_derivatives",
        "reconcile_existing_derivative_readbacks",
        "repair_exact_substack_caption_fragment",
        "repair_exact_treasury_release_candidate_editorial",
        "repair_final_treasury_auction_logic",
        "reconcile_linkedin_activity_pair",
        "module_cli",
    }
)


OUTPUT_EXACT_BYTES = "EXACT_BYTES"
OUTPUT_UTF8_TEXT = "UTF8_TEXT"
OUTPUT_STRUCTURED_JSON = "STRUCTURED_JSON"
OUTPUT_LOCAL_FILE = "LOCAL_FILE"
OUTPUT_FORMS = frozenset({OUTPUT_EXACT_BYTES, OUTPUT_UTF8_TEXT, OUTPUT_STRUCTURED_JSON, OUTPUT_LOCAL_FILE})
RESTART_SAFE = "RESTART_SAFE"
RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
RESTART_NOT_SUPPORTED = "RESTART_NOT_SUPPORTED"


@dataclass(frozen=True)
class OperationContract:
    """Immutable output, restart, and capability contract for one operation."""

    output_required: bool
    output_forms: FrozenSet[str]
    output_schema_version: str
    canonicalizer: str
    restart_mode: str
    capability: str
    durable_supported: bool = True


def _operation_contract(*, restart_mode: str, capability: str, durable_supported: bool = True) -> OperationContract:
    return OperationContract(
        output_required=durable_supported,
        output_forms=OUTPUT_FORMS if durable_supported else frozenset(),
        output_schema_version="contentops.operation_output.v1",
        canonicalizer="contentops.deterministic_output_canonicalizer.v1",
        restart_mode=restart_mode,
        capability=capability,
        durable_supported=durable_supported,
    )


OPERATION_CONTRACTS: Mapping[str, OperationContract] = MappingProxyType(
    {
        "prepare_text_image_release_candidate": _operation_contract(restart_mode=RESTART_SAFE, capability="LOCAL_PREPARATION"),
        "prepare_generic_text_image_release_candidate": _operation_contract(restart_mode=RESTART_SAFE, capability="LOCAL_PREPARATION"),
        "build_operator_manual_audit_packet": _operation_contract(restart_mode=RESTART_SAFE, capability="LOCAL_PREPARATION"),
        "run_eight_platform_substack_first_pipeline": _operation_contract(restart_mode=RECONCILIATION_REQUIRED, capability="LIVE_CAPABLE"),
        "reconcile_public_substack_for_derivative_resume": _operation_contract(restart_mode=RESTART_SAFE, capability="RECONCILIATION"),
        "resume_eight_platform_derivatives": _operation_contract(restart_mode=RECONCILIATION_REQUIRED, capability="LIVE_CAPABLE"),
        "reconcile_existing_derivative_readbacks": _operation_contract(restart_mode=RESTART_SAFE, capability="RECONCILIATION"),
        "repair_exact_substack_caption_fragment": _operation_contract(restart_mode=RECONCILIATION_REQUIRED, capability="LIVE_CAPABLE"),
        "repair_exact_treasury_release_candidate_editorial": _operation_contract(restart_mode=RECONCILIATION_REQUIRED, capability="LIVE_CAPABLE"),
        "repair_final_treasury_auction_logic": _operation_contract(restart_mode=RECONCILIATION_REQUIRED, capability="LIVE_CAPABLE"),
        "reconcile_linkedin_activity_pair": _operation_contract(restart_mode=RESTART_SAFE, capability="RECONCILIATION"),
        "module_cli": _operation_contract(restart_mode=RESTART_NOT_SUPPORTED, capability="CLI_BOUNDARY", durable_supported=False),
    }
)


class OperationLifecycleError(ValueError):
    """Fail-closed durable operation lifecycle contract violation."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class _CanonicalOutput:
    name: str
    output_form: str
    artifact_type: str
    schema_version: str
    content_bytes: bytes


@dataclass
class ContentOpsDurableContext:
    """Exact durable operation context required when persistent store is active."""

    story_id: str
    work_item_id: str
    correlation_id: str
    actor_ref: str
    lease_key: str
    fencing_token: int
    title: Optional[str] = None
    input_artifact_ids: List[str] = field(default_factory=list)
    output_artifact_ids: List[str] = field(default_factory=list)
    attempt_decision: Optional[str] = None
    policy_version: str = "contentops.policy.v1"
    model_version: str = "NOT_APPLICABLE"
    target_surface: str = "eight_platform_all"


class ContentOpsProductionOrchestrator:
    """Only authoritative public interface allowed to resolve canonical operations."""

    schema_version = SCHEMA_VERSION
    canonical_module = CANONICAL_MODULE
    canonical_function = CANONICAL_FUNCTION
    canonical_operations = CANONICAL_OPERATIONS

    def __init__(self, store: Any = None) -> None:
        self._dispatcher: Callable[..., Any] | None = None
        self.store = store

    def _resolve_dispatcher(self) -> Callable[..., Any]:
        if self._dispatcher is None:
            module = import_module(self.canonical_module)
            dispatcher = getattr(module, self.canonical_function)
            if not callable(dispatcher):
                raise TypeError("canonical_contentops_dispatcher_not_callable")
            self._dispatcher = dispatcher
        return self._dispatcher

    @staticmethod
    def _strict_json_bytes(value: Any) -> bytes:
        def validate(node: Any) -> None:
            if node is None or type(node) in (str, bool, int):
                return
            if type(node) is float:
                if not math.isfinite(node):
                    raise OperationLifecycleError("operation_output_non_finite_number")
                return
            if type(node) is list:
                for child in node:
                    validate(child)
                return
            if type(node) is dict:
                if any(type(key) is not str for key in node):
                    raise OperationLifecycleError("operation_output_non_string_json_key")
                for child in node.values():
                    validate(child)
                return
            raise OperationLifecycleError(f"operation_output_unsupported_json_type:{type(node).__name__}")

        validate(value)
        return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")

    @classmethod
    def _descriptor_output(cls, descriptor: Mapping[str, Any], contract: OperationContract) -> _CanonicalOutput:
        name = descriptor.get("name")
        output_form = descriptor.get("output_form")
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", name):
            raise OperationLifecycleError("operation_output_invalid_name")
        if output_form not in contract.output_forms:
            raise OperationLifecycleError("operation_output_form_not_allowed")
        value = descriptor.get("value")
        if output_form == OUTPUT_EXACT_BYTES:
            if not isinstance(value, bytes):
                raise OperationLifecycleError("operation_output_exact_bytes_required")
            content = value
        elif output_form == OUTPUT_UTF8_TEXT:
            if not isinstance(value, str):
                raise OperationLifecycleError("operation_output_utf8_text_required")
            content = value.encode("utf-8", errors="strict")
        elif output_form == OUTPUT_STRUCTURED_JSON:
            content = cls._strict_json_bytes(value)
        else:
            if not isinstance(value, (str, pathlib.Path)):
                raise OperationLifecycleError("operation_output_explicit_local_file_required")
            path = pathlib.Path(value)
            if not path.exists() or not path.is_file():
                raise OperationLifecycleError("operation_output_local_file_missing")
            content = path.read_bytes()
        artifact_type = descriptor.get("artifact_type", "OPERATION_RESULT")
        schema_version = descriptor.get("schema_version", contract.output_schema_version)
        if not isinstance(artifact_type, str) or not artifact_type or not isinstance(schema_version, str) or not schema_version:
            raise OperationLifecycleError("operation_output_invalid_metadata")
        return _CanonicalOutput(name, output_form, artifact_type, schema_version, content)

    @classmethod
    def _canonicalize_result(cls, result: Any, contract: OperationContract) -> List[_CanonicalOutput]:
        if result is None:
            return []
        if isinstance(result, bytes):
            outputs = [_CanonicalOutput("result", OUTPUT_EXACT_BYTES, "OPERATION_RESULT", contract.output_schema_version, result)]
        elif isinstance(result, str):
            outputs = [_CanonicalOutput("result", OUTPUT_UTF8_TEXT, "OPERATION_RESULT", contract.output_schema_version, result.encode("utf-8", errors="strict"))]
        elif isinstance(result, pathlib.Path):
            outputs = [cls._descriptor_output({"name": "result", "output_form": OUTPUT_LOCAL_FILE, "value": result}, contract)]
        elif isinstance(result, Mapping) and "outputs" in result:
            if set(result) - {"outputs", "manifest_schema_version"}:
                raise OperationLifecycleError("operation_output_manifest_unknown_fields")
            raw_outputs = result["outputs"]
            if not isinstance(raw_outputs, list):
                raise OperationLifecycleError("operation_output_manifest_list_required")
            outputs = [cls._descriptor_output(descriptor, contract) if isinstance(descriptor, Mapping) else (_ for _ in ()).throw(OperationLifecycleError("operation_output_descriptor_required")) for descriptor in raw_outputs]
        elif isinstance(result, Mapping) and "output_bytes" in result:
            outputs = [cls._descriptor_output({
                "name": result.get("name", "result"),
                "output_form": OUTPUT_EXACT_BYTES,
                "value": result["output_bytes"],
                "artifact_type": result.get("artifact_type", "OPERATION_RESULT"),
                "schema_version": result.get("schema_version", contract.output_schema_version),
            }, contract)]
        elif isinstance(result, Mapping):
            outputs = [_CanonicalOutput("result", OUTPUT_STRUCTURED_JSON, "OPERATION_RESULT", contract.output_schema_version, cls._strict_json_bytes(dict(result)))]
        else:
            raise OperationLifecycleError(f"operation_output_unsupported_type:{type(result).__name__}")
        names = [output.name for output in outputs]
        if len(names) != len(set(names)):
            raise OperationLifecycleError("operation_output_duplicate_name")
        return sorted(outputs, key=lambda output: output.name)

    @staticmethod
    def _validate_input_scope(artifact: Mapping[str, Any], context: ContentOpsDurableContext) -> None:
        scope = artifact.get("artifact_scope")
        if scope == "WORK_ITEM_EXACT" and (artifact.get("story_id") != context.story_id or artifact.get("work_item_id") != context.work_item_id):
            raise ValueError(f"input_artifact_work_item_scope_mismatch:{artifact['artifact_id']}")
        if scope == "STORY_EXACT" and artifact.get("story_id") != context.story_id:
            raise ValueError(f"input_artifact_story_scope_mismatch:{artifact['artifact_id']}")
        if scope not in {"WORK_ITEM_EXACT", "STORY_EXACT", "GLOBAL_REUSABLE"}:
            raise ValueError(f"input_artifact_invalid_scope:{artifact['artifact_id']}")

    @staticmethod
    def _resume_decision(contract: OperationContract) -> str:
        if contract.restart_mode == RESTART_SAFE:
            return "RESUME_RESTART_SAFE"
        if contract.restart_mode == RECONCILIATION_REQUIRED:
            return "RESUME_AFTER_RECONCILIATION"
        raise OperationLifecycleError("operation_restart_not_supported")

    @staticmethod
    def _register_outputs(active_store: Any, context: ContentOpsDurableContext, operation: str,
                          outputs: Sequence[_CanonicalOutput], compute_sha256: Callable[[Any], str]) -> List[str]:
        registered: List[Dict[str, Any]] = []
        for output in outputs:
            digest = compute_sha256(output.content_bytes)
            identity = json.dumps({"operation": operation, "name": output.name, "output_form": output.output_form,
                                   "artifact_type": output.artifact_type, "schema_version": output.schema_version,
                                   "sha256_hash": digest}, sort_keys=True, separators=(",", ":"))
            artifact_id = f"art_out_{compute_sha256(identity)[:24]}"
            active_store.register_artifact(
                artifact_id=artifact_id, artifact_type=output.artifact_type, storage_class="MEMORY",
                schema_version=output.schema_version, producer_ref=context.actor_ref,
                content_bytes=output.content_bytes, story_id=context.story_id, work_item_id=context.work_item_id,
                artifact_scope="WORK_ITEM_EXACT",
            )
            registered.append({"artifact_id": artifact_id, "name": output.name, "output_form": output.output_form,
                               "artifact_type": output.artifact_type, "schema_version": output.schema_version,
                               "byte_length": len(output.content_bytes), "sha256_hash": digest})
        ids = [entry["artifact_id"] for entry in registered]
        if len(registered) > 1:
            manifest_bytes = json.dumps({"schema_version": "contentops.operation_output_manifest.v1", "operation": operation,
                                         "outputs": registered}, sort_keys=True, separators=(",", ":")).encode("utf-8")
            manifest_id = f"art_manifest_{compute_sha256(manifest_bytes)[:24]}"
            active_store.register_artifact(
                artifact_id=manifest_id, artifact_type="OPERATION_OUTPUT_MANIFEST", storage_class="MEMORY",
                schema_version="contentops.operation_output_manifest.v1", producer_ref=context.actor_ref,
                content_bytes=manifest_bytes, story_id=context.story_id, work_item_id=context.work_item_id,
                artifact_scope="WORK_ITEM_EXACT",
            )
            ids.append(manifest_id)
        return sorted(ids)

    def execute(self, operation: str, **kwargs: Any) -> Any:
        """Validate and dispatch one exact canonical operation."""
        if operation not in self.canonical_operations:
            raise ValueError(f"unknown_canonical_contentops_operation:{operation}")

        active_store = kwargs.pop("store", self.store)
        raw_context = kwargs.pop("durable_context", None)
        if active_store is None:
            return self._resolve_dispatcher()(operation, **kwargs)

        contract = OPERATION_CONTRACTS[operation]
        if not contract.durable_supported:
            raise ValueError(f"durable_operation_not_supported:{operation}")
        if raw_context is None:
            raise ValueError("durable_context_required_when_store_active")
        if isinstance(raw_context, dict):
            ctx = ContentOpsDurableContext(**raw_context)
        elif isinstance(raw_context, ContentOpsDurableContext):
            ctx = raw_context
        else:
            raise ValueError("invalid_durable_context_type")
        if not ctx.story_id or not ctx.work_item_id or not ctx.correlation_id or not ctx.actor_ref or not ctx.lease_key:
            raise ValueError("incomplete_durable_context_fields")

        from live_contentops.durable_operational_store_v1 import WorkItemNotFoundError, compute_sha256
        try:
            item = active_store.get_work_item(ctx.work_item_id)
        except WorkItemNotFoundError:
            if not ctx.title:
                raise ValueError("title_required_to_create_work_item")
            item = active_store.create_work_item(
                story_id=ctx.story_id, title=ctx.title, target_surface=ctx.target_surface,
                work_item_id=ctx.work_item_id, actor_ref=ctx.actor_ref,
                correlation_id=ctx.correlation_id, input_artifact_ids=ctx.input_artifact_ids,
            )
        if item["current_state"] not in ("DISCOVERED", "EVIDENCE_PENDING"):
            raise ValueError(f"orchestrator_execution_forbidden_from_state:{item['current_state']}")
        if item["story_id"] != ctx.story_id:
            raise ValueError(f"story_id_mismatch: expected {item['story_id']}, got {ctx.story_id}")
        if item["target_surface"] != ctx.target_surface:
            raise ValueError(f"target_surface_mismatch: expected {item['target_surface']}, got {ctx.target_surface}")
        for artifact_id in ctx.input_artifact_ids:
            self._validate_input_scope(active_store.get_artifact(artifact_id), ctx)
        if item["current_state"] == "EVIDENCE_PENDING":
            required_decision = self._resume_decision(contract)
            if ctx.attempt_decision != required_decision:
                raise ValueError(f"explicit_resume_decision_required:{required_decision}")
        else:
            active_store.transition_state(
                work_item_id=ctx.work_item_id, expected_from_state="DISCOVERED", to_state="EVIDENCE_PENDING",
                expected_state_version=item["state_version"], actor_class="ContentOpsProductionOrchestrator",
                actor_ref=ctx.actor_ref, reason_code="ORCHESTRATOR_DISPATCH_PREPARATION",
                explanation=f"Execution of operation {operation}", lease_key=ctx.lease_key,
                fencing_token=ctx.fencing_token, input_artifact_ids=ctx.input_artifact_ids,
                output_artifact_ids=[], correlation_id=ctx.correlation_id,
                policy_version=ctx.policy_version, model_version=ctx.model_version,
            )
            item = active_store.get_work_item(ctx.work_item_id)

        registered_output_ids: List[str] = []
        try:
            result = self._resolve_dispatcher()(operation, **kwargs)
            outputs = self._canonicalize_result(result, contract)
            if contract.output_required and not outputs:
                raise OperationLifecycleError("operation_output_required")
            registered_output_ids = self._register_outputs(active_store, ctx, operation, outputs, compute_sha256)
            if ctx.output_artifact_ids and sorted(set(ctx.output_artifact_ids)) != registered_output_ids:
                raise OperationLifecycleError("operation_output_artifact_expectation_mismatch")
            latest = active_store.get_work_item(ctx.work_item_id)
            if latest["current_state"] != "EVIDENCE_PENDING":
                raise OperationLifecycleError("operation_pending_state_lost")
            active_store.transition_state(
                work_item_id=ctx.work_item_id, expected_from_state="EVIDENCE_PENDING", to_state="EVIDENCE_READY",
                expected_state_version=latest["state_version"], actor_class="ContentOpsProductionOrchestrator",
                actor_ref=ctx.actor_ref, reason_code="ORCHESTRATOR_PREPARATION_COMPLETE",
                explanation=f"Operation {operation} completed successfully", lease_key=ctx.lease_key,
                fencing_token=ctx.fencing_token, input_artifact_ids=ctx.input_artifact_ids,
                output_artifact_ids=registered_output_ids, correlation_id=ctx.correlation_id,
                policy_version=ctx.policy_version, model_version=ctx.model_version,
            )
            return result
        except Exception as exc:
            try:
                latest = active_store.get_work_item(ctx.work_item_id)
                if latest["current_state"] == "EVIDENCE_PENDING":
                    controlled = exc.code if isinstance(exc, OperationLifecycleError) else type(exc).__name__
                    reason = "ORCHESTRATOR_OUTPUT_CONTRACT_BLOCKED" if isinstance(exc, OperationLifecycleError) else "ORCHESTRATOR_OPERATION_FAILED"
                    active_store.transition_state(
                        work_item_id=ctx.work_item_id, expected_from_state="EVIDENCE_PENDING", to_state="EVIDENCE_BLOCKED",
                        expected_state_version=latest["state_version"], actor_class="ContentOpsProductionOrchestrator",
                        actor_ref=ctx.actor_ref, reason_code=reason,
                        explanation=f"Operation {operation} blocked: {controlled}", lease_key=ctx.lease_key,
                        fencing_token=ctx.fencing_token, input_artifact_ids=ctx.input_artifact_ids,
                        output_artifact_ids=registered_output_ids, correlation_id=ctx.correlation_id,
                        policy_version=ctx.policy_version, model_version=ctx.model_version,
                    )
            except Exception:
                pass
            raise

    def run(self, **kwargs: Any) -> Mapping[str, Any]:
        """Execute the full production run through the same operation boundary."""
        result = self.execute("run_eight_platform_substack_first_pipeline", **kwargs)
        if not isinstance(result, Mapping):
            raise TypeError("canonical_contentops_run_result_not_mapping")
        return result

    __call__ = run


def run_contentops_production_pipeline(**kwargs: Any) -> Mapping[str, Any]:
    """Functional production entrypoint for callers that do not retain an instance."""
    return ContentOpsProductionOrchestrator().run(**kwargs)
