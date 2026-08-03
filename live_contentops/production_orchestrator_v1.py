"""Stable, import-safe interface for the one authoritative ContentOps live pipeline.

Public compatibility APIs and canonical module/script CLIs delegate here before the
private implementation module—and therefore its provider/browser adapters—is imported.
"""
from __future__ import annotations

from importlib import import_module
from typing import Any, Callable, Mapping

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
        story_id = kwargs.get("story_id", "treasury_release_candidate_20260714")
        target_surface = kwargs.get("target_surface", "eight_platform_all")
        # Remove store-only metadata kwargs if operation is prepare_text_image_release_candidate
        if operation == "prepare_text_image_release_candidate":
            kwargs.pop("story_id", None)
            kwargs.pop("target_surface", None)

        if active_store is not None:
            title = f"Operation {operation} on {story_id}"
            item = active_store.create_work_item(story_id=story_id, title=title, target_surface=target_surface)
            item_id = item["work_item_id"]
            state_ver = item["state_version"]
            dummy_hash = "a" * 64
            if item["current_state"] == "DISCOVERED":
                item = active_store.transition_state(
                    work_item_id=item_id,
                    expected_from_state="DISCOVERED",
                    to_state="EVIDENCE_PENDING",
                    expected_state_version=state_ver,
                    actor_class="ContentOpsProductionOrchestrator",
                    actor_ref="orchestrator_v1",
                    reason_code="ORCHESTRATOR_DISPATCH_PREPARATION",
                    explanation=f"Execution of operation {operation}",
                    artifact_hash_set=[dummy_hash],
                    correlation_id=f"corr_{operation}",
                    authority_granted=False,
                )

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
