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

    def __init__(self) -> None:
        self._dispatcher: Callable[..., Any] | None = None

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
