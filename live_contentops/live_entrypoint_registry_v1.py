"""Executable inventory and fail-closed policy for ContentOps live-capable entrypoints."""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final, Literal

TASK_LABEL = "TASK_CONTENTOPS_CANONICAL_PRODUCTION_ENTRYPOINT_AND_LEGACY_LIVE_PATH_QUARANTINE_V1"
SCHEMA_VERSION = "contentops.live_entrypoint_registry.v1"
Action = Literal["CANONICAL", "DELEGATE", "QUARANTINED"]

LIVE_PATH_QUARANTINED = "BLOCKED_LEGACY_LIVE_PATH_USE_CANONICAL_PRODUCTION_ORCHESTRATOR"
HTTP_LAUNCH_QUARANTINED = "BLOCKED_HTTP_LIVE_LAUNCH_QUARANTINED"
SCHEDULER_LIVE_QUARANTINED = "BLOCKED_SCHEDULER_LIVE_UNTIL_DURABLE_OUTBOX_AUTHORITY"
LEGACY_AUTOMATION_QUARANTINED = "BLOCKED_LEGACY_AUTOMATION_USE_CANONICAL_PRODUCTION_ORCHESTRATOR"
BROWSER_PROFILE_EXECUTION_QUARANTINED = "BLOCKED_DIRECT_BROWSER_PROFILE_EXECUTION_USE_CANONICAL_PRODUCTION_ORCHESTRATOR"


class LiveEntrypointQuarantined(RuntimeError):
    """Raised before a noncanonical path can load credentials or reach an adapter."""

    def __init__(self, entrypoint_id: str, status: str, message: str) -> None:
        super().__init__(message)
        self.entrypoint_id = entrypoint_id
        self.status = status

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "entrypoint_id": self.entrypoint_id,
            "canonical_entrypoint_id": "contentops.production_orchestrator.v1",
            "retryable": False,
            "message": str(self),
        }


@dataclass(frozen=True)
class LiveEntrypoint:
    entrypoint_id: str
    module_or_path: str
    function_or_route: str
    invocation_surface: str
    canonical: bool
    current_action: Action
    live_capability: str
    credential_provider_browser_reachability: str
    required_guard: str
    failure_behavior: str
    proving_tests: tuple[str, ...]


_TEST = "tests/test_canonical_production_entrypoint_and_legacy_quarantine_v1.py"
ENTRYPOINTS: Final[tuple[LiveEntrypoint, ...]] = (
    LiveEntrypoint("contentops.production_orchestrator.v1", "live_contentops.production_orchestrator_v1", "ContentOpsProductionOrchestrator.run", "Python API", True, "CANONICAL", "Canonical Substack-first publication and configured derivative writes", "Reachable only after explicit canonical invocation", "Accepted canonical runner approval/freeze/publication guards", "Canonical runner fail-closed behavior", (_TEST + "::test_exactly_one_registry_row_is_canonical", _TEST + "::test_orchestrator_is_lazy_and_bound")),
    LiveEntrypoint("contentops.canonical_module_cli.v1", "live_contentops.eight_platform_substack_first_pipeline_v1", "main / run_eight_platform_substack_first_pipeline", "Module CLI and historical Python API", False, "DELEGATE", "Same canonical pipeline for historical replay compatibility", "Canonical module retains accepted provider/browser reachability", "ContentOpsProductionOrchestrator is the authoritative public interface", "No independent implementation; function is the orchestrator binding target", (_TEST + "::test_orchestrator_is_lazy_and_bound",)),
    LiveEntrypoint("contentops.legacy_v6_runner.v1", "live_contentops.live_production_pipeline_runner_v6", "run_live_production_pipeline / module CLI", "Legacy Python API and module CLI", False, "QUARANTINED", "Historical direct platform dispatch", "Historical module imports live adapters", "Reject live_run, dispatch_live, and dispatch_rehearsal before preparation or env access", LIVE_PATH_QUARANTINED, (_TEST + "::test_legacy_live_flags_fail_before_pipeline_body",)),
    LiveEntrypoint("contentops.local_http_run_pipeline.v1", "live_contentops.server", "POST /api/run-pipeline", "Unauthenticated local HTTP / UI launch", False, "QUARANTINED", "Former subprocess launch of legacy live runner", "None after quarantine", "Always deny POST", HTTP_LAUNCH_QUARANTINED, (_TEST + "::test_server_post_is_machine_readable_and_cannot_launch",)),
    LiveEntrypoint("contentops.v6_command_center_launch.v1", "ui/contentops_v5/src/views/V6CommandCenter.tsx", "launchFullPipeline -> POST /api/run-pipeline", "Operator UI", False, "QUARANTINED", "Former unauthenticated local HTTP launch", "None; UI receives explicit blocked response", "Render server quarantine status without polling", HTTP_LAUNCH_QUARANTINED, (_TEST + "::test_ui_route_is_registered_and_server_route_is_quarantined",)),
    LiveEntrypoint("contentops.scheduler_dispatch_function.v1", "live_contentops.scheduler_v6", "dispatch_platform_action", "Python API", False, "QUARANTINED", "Direct adapter post/comment/edit execution", "Adapter imports are reachable only in dry-run mode", "Reject dry_run=False before adapter imports", SCHEDULER_LIVE_QUARANTINED, (_TEST + "::test_scheduler_live_dispatch_fails_before_import",)),
    LiveEntrypoint("contentops.scheduler_tick.v1", "live_contentops.scheduler_v6", "OutboxScheduler.reconcile_outbox_timing", "Python scheduler API", False, "QUARANTINED", "Due-entry dispatch and output mutation", "None in live mode after quarantine", "Reject dry_run=False before registry read/write or adapter dispatch", SCHEDULER_LIVE_QUARANTINED, (_TEST + "::test_scheduler_live_tick_fails_before_load_or_save",)),
    LiveEntrypoint("contentops.cli_scheduler_fast_ship.v1", "live_contentops.cli", "scheduler tick --fast-ship", "CLI", False, "QUARANTINED", "Former scheduler non-dry-run dispatch", "None after command-boundary quarantine", "Reject --fast-ship before scheduler construction", SCHEDULER_LIVE_QUARANTINED, (_TEST + "::test_cli_fast_ship_scheduler_fails_before_scheduler_import",)),
    LiveEntrypoint("contentops.cli_direct_platform_adapters.v1", "live_contentops.cli", "x / substack / telegram / discord / facebook / instagram / threads commands", "CLI command families", False, "QUARANTINED", "Direct platform adapter execution including live pilot commands", "Adapter imports remain test/rehearsal compatibility only", "No command grants production authority; live-capable flags and pilots fail closed", LIVE_PATH_QUARANTINED, (_TEST + "::test_registry_covers_direct_cli_adapter_families",)),
    LiveEntrypoint("contentops.legacy_fast_one_cycle.v0", "live_contentops.fast_one_cycle_automation_v0", "run_fast_one_cycle / scripts/run_fast_one_cycle_automation_v0.py", "Legacy Python API and script CLI", False, "QUARANTINED", "Discord webhook dispatch plus preview/output mutation", "Legacy module formerly imported the Discord adapter and read webhook environment values at import/run reachability", "Reject at the callable boundary before packet/output/env/adapter access", LEGACY_AUTOMATION_QUARANTINED, (_TEST + "::test_legacy_automation_callables_fail_before_io_env_or_adapter_import",)),
    LiveEntrypoint("contentops.legacy_full_pipeline_debug_live.v0", "live_contentops.full_pipeline_north_star_debug_and_live_run_v0", "run_full_pipeline_north_star_debug_and_live_run / scripts/run_full_pipeline_north_star_debug_and_live_run_v0.py", "Legacy Python API and script CLI", False, "QUARANTINED", "Telegram photo repair and evidence/output mutation", "Legacy module can lazily import Telegram live adapter", "Reject at the callable boundary before repo/output/adapter access", LEGACY_AUTOMATION_QUARANTINED, (_TEST + "::test_legacy_automation_callables_fail_before_io_env_or_adapter_import",)),
    LiveEntrypoint("contentops.legacy_operator_daily_live.v0", "live_contentops.operator_approved_supervised_live_daily_run_v0", "run_operator_approved_supervised_live_daily_run", "Legacy Python API", False, "QUARANTINED", "Telegram post and evidence/output mutation", "Legacy module can lazily import Telegram live adapter", "Reject at the callable boundary before repo/output/adapter access", LEGACY_AUTOMATION_QUARANTINED, (_TEST + "::test_legacy_automation_callables_fail_before_io_env_or_adapter_import",)),
    LiveEntrypoint("contentops.legacy_terra_ultra_live.v1", "live_contentops.terra_ultra_north_star_full_automation_v1", "run_terra_ultra_north_star_full_automation / main / scripts/run_terra_ultra_north_star_full_automation_v1.py", "Legacy Python API, module CLI, and script CLI", False, "QUARANTINED", "Telegram photo dispatch plus source/article/media/evidence mutation", "Legacy module imports Telegram adapter and can load dotenv", "Reject at the callable boundary before dotenv/output/provider/adapter access", LEGACY_AUTOMATION_QUARANTINED, (_TEST + "::test_legacy_automation_callables_fail_before_io_env_or_adapter_import",)),
    LiveEntrypoint("contentops.legacy_substack_first_loop.v1", "live_contentops.substack_first_north_star_pipeline_loop_v1", "prepare_substack_first_pipeline / complete_substack_first_pipeline / main / scripts/run_substack_first_north_star_pipeline_loop_v1.py", "Legacy Python API, module CLI, and script CLI", False, "QUARANTINED", "Provider-backed preparation, Substack browser request mutation, and Telegram derivative dispatch", "Legacy module imports Telegram adapters and loads dotenv", "Reject prepare/complete/main before dotenv/output/provider/browser/adapter access", LEGACY_AUTOMATION_QUARANTINED, (_TEST + "::test_legacy_substack_loop_entrypoints_fail_before_io_env_or_adapter_import",)),
    LiveEntrypoint("contentops.direct_browser_profile_execution.v1", "live_contentops.publishing_profile_registry_v1", "open_or_attach_canonical_edge / main", "Python API and module CLI", False, "QUARANTINED", "Direct browser-process launch or CDP attachment", "Canonical Edge profile and browser process are directly reachable", "Reject before process discovery, CDP probing, or browser launch", BROWSER_PROFILE_EXECUTION_QUARANTINED, (_TEST + "::test_direct_browser_profile_execution_fails_before_process_or_network_access",)),
)


def get_entrypoint(entrypoint_id: str) -> LiveEntrypoint:
    for entrypoint in ENTRYPOINTS:
        if entrypoint.entrypoint_id == entrypoint_id:
            return entrypoint
    raise KeyError(entrypoint_id)


def quarantine(entrypoint_id: str, status: str, message: str) -> None:
    get_entrypoint(entrypoint_id)
    raise LiveEntrypointQuarantined(entrypoint_id, status, message)


def export_registry(path: str | Path | None = None) -> dict[str, object]:
    payload: dict[str, object] = {"schema_version": SCHEMA_VERSION, "task_label": TASK_LABEL, "canonical_entrypoint_id": "contentops.production_orchestrator.v1", "entrypoints": [asdict(entrypoint) for entrypoint in ENTRYPOINTS]}
    if path is not None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def validate_registry() -> None:
    canonical = [row for row in ENTRYPOINTS if row.canonical]
    if len(canonical) != 1 or canonical[0].current_action != "CANONICAL":
        raise ValueError("Registry must contain exactly one CANONICAL row")
    ids = [row.entrypoint_id for row in ENTRYPOINTS]
    if len(ids) != len(set(ids)):
        raise ValueError("Registry entrypoint IDs must be unique")
    if any(not row.proving_tests for row in ENTRYPOINTS):
        raise ValueError("Every registry row must bind proving tests")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate or export the live-entrypoint registry")
    parser.add_argument("--export", help="Optional JSON export path")
    args = parser.parse_args(argv)
    validate_registry()
    payload = export_registry(args.export)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
