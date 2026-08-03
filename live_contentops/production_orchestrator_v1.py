"""Stable, import-safe interface for the one authoritative ContentOps live pipeline.

Public compatibility APIs and canonical module/script CLIs delegate here before the
private implementation module—and therefore its provider/browser adapters—is imported.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from typing import Any, Callable, Dict, List, Mapping, Optional

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

    def execute(self, operation: str, **kwargs: Any) -> Any:
        """Validate and dispatch one exact canonical operation."""
        if operation not in self.canonical_operations:
            raise ValueError(f"unknown_canonical_contentops_operation:{operation}")

        active_store = kwargs.pop("store", self.store)
        raw_context = kwargs.pop("durable_context", None)

        if active_store is not None:
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

            # Import WorkItemNotFoundError explicitly
            from live_contentops.durable_operational_store_v1 import WorkItemNotFoundError, compute_sha256

            # Catch ONLY WorkItemNotFoundError when fetching item
            try:
                item = active_store.get_work_item(ctx.work_item_id)
            except WorkItemNotFoundError:
                if not ctx.title:
                    raise ValueError("title_required_to_create_work_item")
                item = active_store.create_work_item(
                    story_id=ctx.story_id,
                    title=ctx.title,
                    target_surface=ctx.target_surface,
                    work_item_id=ctx.work_item_id,
                    actor_ref=ctx.actor_ref,
                    correlation_id=ctx.correlation_id,
                    input_artifact_ids=ctx.input_artifact_ids,
                )

            # Validate context matching
            if item["story_id"] != ctx.story_id:
                raise ValueError(f"story_id_mismatch: expected {item['story_id']}, got {ctx.story_id}")
            if item["target_surface"] != ctx.target_surface:
                raise ValueError(f"target_surface_mismatch: expected {item['target_surface']}, got {ctx.target_surface}")

            if item["current_state"] == "DISCOVERED":
                active_store.transition_state(
                    work_item_id=ctx.work_item_id,
                    expected_from_state="DISCOVERED",
                    to_state="EVIDENCE_PENDING",
                    expected_state_version=item["state_version"],
                    actor_class="ContentOpsProductionOrchestrator",
                    actor_ref=ctx.actor_ref,
                    reason_code="ORCHESTRATOR_DISPATCH_PREPARATION",
                    explanation=f"Execution of operation {operation}",
                    lease_key=ctx.lease_key,
                    fencing_token=ctx.fencing_token,
                    input_artifact_ids=ctx.input_artifact_ids,
                    output_artifact_ids=[],
                    correlation_id=ctx.correlation_id,
                    policy_version=ctx.policy_version,
                    model_version=ctx.model_version,
                )
                item = active_store.get_work_item(ctx.work_item_id)

            try:
                result = self._resolve_dispatcher()(operation, **kwargs)
            except Exception as exc:
                if active_store is not None and item["current_state"] == "EVIDENCE_PENDING":
                    active_store.transition_state(
                        work_item_id=ctx.work_item_id,
                        expected_from_state="EVIDENCE_PENDING",
                        to_state="EVIDENCE_BLOCKED",
                        expected_state_version=item["state_version"],
                        actor_class="ContentOpsProductionOrchestrator",
                        actor_ref=ctx.actor_ref,
                        reason_code="ORCHESTRATOR_OPERATION_FAILED",
                        explanation=f"Operation {operation} failed: {exc}",
                        lease_key=ctx.lease_key,
                        fencing_token=ctx.fencing_token,
                        input_artifact_ids=ctx.input_artifact_ids,
                        output_artifact_ids=[],
                        correlation_id=ctx.correlation_id,
                    )
                raise

            registered_output_ids = []
            if isinstance(result, dict) and "output_bytes" in result:
                out_bytes = result["output_bytes"]
                art_id = f"art_out_{compute_sha256(out_bytes)[:16]}"
                active_store.register_artifact(
                    artifact_id=art_id,
                    artifact_type=result.get("artifact_type", "OPERATION_RESULT"),
                    storage_class="MEMORY",
                    schema_version="1.0.0",
                    producer_ref=ctx.actor_ref,
                    content_bytes=out_bytes,
                    story_id=ctx.story_id,
                    work_item_id=ctx.work_item_id,
                )
                registered_output_ids.append(art_id)

            if item["current_state"] == "EVIDENCE_PENDING":
                active_store.transition_state(
                    work_item_id=ctx.work_item_id,
                    expected_from_state="EVIDENCE_PENDING",
                    to_state="EVIDENCE_READY",
                    expected_state_version=item["state_version"],
                    actor_class="ContentOpsProductionOrchestrator",
                    actor_ref=ctx.actor_ref,
                    reason_code="ORCHESTRATOR_PREPARATION_COMPLETE",
                    explanation=f"Operation {operation} completed successfully",
                    lease_key=ctx.lease_key,
                    fencing_token=ctx.fencing_token,
                    input_artifact_ids=ctx.input_artifact_ids,
                    output_artifact_ids=registered_output_ids,
                    correlation_id=ctx.correlation_id,
                )
            return result

        return self._resolve_dispatcher()(operation, **kwargs)

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
