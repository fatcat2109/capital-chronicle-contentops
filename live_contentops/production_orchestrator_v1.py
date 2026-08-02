"""Stable, import-safe interface for the one authoritative ContentOps live pipeline.

The canonical runner has intentionally live-capable browser and platform imports. This
facade keeps discovery, registry validation, and quarantined paths safe to import by
resolving the runner only when an operator explicitly invokes the canonical interface.
"""
from __future__ import annotations

from importlib import import_module
from typing import Any, Callable, Mapping

TASK_LABEL = "TASK_CONTENTOPS_CANONICAL_PRODUCTION_ENTRYPOINT_AND_LEGACY_LIVE_PATH_QUARANTINE_V1"
SCHEMA_VERSION = "contentops.production_orchestrator.v1"
CANONICAL_MODULE = "live_contentops.eight_platform_substack_first_pipeline_v1"
CANONICAL_FUNCTION = "run_eight_platform_substack_first_pipeline"


class ContentOpsProductionOrchestrator:
    """Only authoritative interface allowed to resolve the live pipeline runner."""

    schema_version = SCHEMA_VERSION
    canonical_module = CANONICAL_MODULE
    canonical_function = CANONICAL_FUNCTION

    def __init__(self, runner: Callable[..., Mapping[str, Any]] | None = None) -> None:
        self._runner = runner

    def _resolve_runner(self) -> Callable[..., Mapping[str, Any]]:
        if self._runner is None:
            module = import_module(self.canonical_module)
            self._runner = getattr(module, self.canonical_function)
        return self._runner

    def run(self, **kwargs: Any) -> Mapping[str, Any]:
        """Delegate one invocation to the accepted canonical runner unchanged."""
        return self._resolve_runner()(**kwargs)

    __call__ = run


def run_contentops_production_pipeline(**kwargs: Any) -> Mapping[str, Any]:
    """Functional production entrypoint for callers that do not retain an instance."""
    return ContentOpsProductionOrchestrator().run(**kwargs)
