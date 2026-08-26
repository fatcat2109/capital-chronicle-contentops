"""Final Daily App production composition and one-process launcher."""
from __future__ import annotations

import threading
from dataclasses import dataclass
from http.server import HTTPServer
from pathlib import Path
from typing import Any, Mapping, Optional

from live_contentops.daily_app_supervisor_v1 import ContentOpsDailyAppSupervisor
from live_contentops.daily_app_supervisor_v1 import (
    SCHEDULED_EDITORIAL_OWNER_NATIVE_DESKTOP,
)
from live_contentops.native_llm_first_daily_app_supervisor_v1 import (
    NativeLlmFirstContentOpsDailyAppSupervisor,
)
from live_contentops.browser_interaction_budget_v1 import (
    configure_browser_interaction_telemetry,
)
from live_contentops.destination_transport_registry_v1 import (
    DestinationReadinessManager,
    REGISTRY_VERSION,
    validate_registry,
    registration_for_destination,
)
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.production_orchestrator_v1 import ContentOpsProductionOrchestrator
from live_contentops.publication_coordinator_v1 import (
    CanonicalDestinationTransportRuntimeV1,
    DurablePublicationCoordinator,
)
from live_contentops.daily_app_performance_v1 import (
    classify_interactions_with_nine_router,
)
from live_contentops.server import make_handler


@dataclass
class FinalDailyAppProductionRuntime:
    store: ContentOpsDurableStore
    orchestrator: ContentOpsProductionOrchestrator
    readiness_manager: DestinationReadinessManager
    transport_runtime: CanonicalDestinationTransportRuntimeV1
    publication_coordinator: DurablePublicationCoordinator
    supervisor: ContentOpsDailyAppSupervisor
    api_server: Optional[HTTPServer] = None
    api_thread: Optional[threading.Thread] = None

    def start_api(self, *, port: int = 5174) -> None:
        if self.api_server is not None:
            return
        self.api_server = HTTPServer(("127.0.0.1", int(port)), make_handler(self.store.db_path))
        self.api_thread = threading.Thread(
            target=self.api_server.serve_forever,
            name="contentops-daily-app-loopback-api",
            daemon=True,
        )
        self.api_thread.start()

    def close(self) -> None:
        if self.api_server is not None:
            self.api_server.shutdown()
            self.api_server.server_close()
            self.api_server = None

    def execute_native_desktop_scheduled_opportunity(
        self,
        *,
        automation_id: str,
        now: Any = None,
        coordinator_selection: Optional[Mapping[str, Any]] = None,
    ) -> dict[str, Any]:
        """Compatibility alias for the native LLM-first public PREPARE seam."""
        return self.supervisor.execute_native_desktop_scheduled_opportunity(
            automation_id=automation_id,
            now=now,
            coordinator_selection=coordinator_selection,
        )

    def prepare_native_desktop_scheduled_opportunity(
        self,
        *,
        automation_id: str,
        now: Any = None,
        coordinator_selection: Optional[Mapping[str, Any]] = None,
    ) -> dict[str, Any]:
        """Select first, then hydrate only the exact HIGH-selected story."""
        return self.supervisor.prepare_native_desktop_scheduled_opportunity(
            automation_id=automation_id,
            now=now,
            coordinator_selection=coordinator_selection,
        )

    def complete_native_desktop_scheduled_opportunity(
        self,
        *,
        automation_id: str,
        canonical_opportunity_id: str,
        worker_return: Mapping[str, Any],
        coordinator_review_receipt: Mapping[str, Any],
        now: Any = None,
    ) -> dict[str, Any]:
        """Resume the same opportunity with its exact worker and HIGH review receipts."""
        return self.supervisor.complete_native_desktop_scheduled_opportunity(
            automation_id=automation_id,
            canonical_opportunity_id=canonical_opportunity_id,
            worker_return=worker_return,
            coordinator_review_receipt=coordinator_review_receipt,
            now=now,
        )

    def smoke_snapshot(self) -> dict[str, Any]:
        control = self.store.get_operating_control()
        return {
            "status": "PRODUCTION_COMPOSITION_READY_NO_WRITE",
            "schema_version": self.store.get_current_schema_version(),
            "transport_registry_version": REGISTRY_VERSION,
            "operating_mode": control["operating_mode"],
            "publisher_is_real_coordinator": self.supervisor._publication_coordinator is self.publication_coordinator,
            "publisher_wiring_not_none": self.supervisor._publication_publisher is not None,
            "readback_wiring_not_none": self.supervisor._publication_readback_provider is not None,
            "performance_wiring_not_none": self.supervisor._performance_collector is not None,
            "learning_enabled": self.supervisor._performance_learning_enabled,
            "scheduled_editorial_owner": self.supervisor._scheduled_editorial_owner,
            "native_llm_first_selection_before_hydration": isinstance(
                self.supervisor, NativeLlmFirstContentOpsDailyAppSupervisor
            ),
            "next_wake_utc": self.supervisor._next_wake(self.supervisor._clock()).isoformat().replace("+00:00", "Z"),
            "public_write_performed": False,
        }


def build_final_daily_app_production_runtime(
    *,
    store_path: str | Path,
    output_root: str | Path,
    operating_mode: Optional[str] = None,
    sidecar_glob: Optional[str] = None,
    clock: Any = None,
    ensure_edge_runtime: bool = False,
    run_readiness_probes: bool = False,
) -> FinalDailyAppProductionRuntime:
    validate_registry()
    store = ContentOpsDurableStore(store_path)
    configure_browser_interaction_telemetry(
        Path(store_path).resolve().parent / "control" / "browser_interaction_budget_v1"
    )
    orchestrator = ContentOpsProductionOrchestrator()
    # Compatibility-only explicit bootstrap.  The permanent Daily App path leaves this false;
    # Edge is ensured only by an exact destination JIT publication/reconciliation request.
    if ensure_edge_runtime:
        orchestrator.execute("ensure_canonical_edge_publishing_runtime", urls=())
    readiness = DestinationReadinessManager(
        store=store,
        edge_runtime_ensurer=lambda **kwargs: orchestrator.execute(
            "ensure_canonical_edge_publishing_runtime", urls=tuple(kwargs.get("urls") or ())
        ),
    )
    if run_readiness_probes:
        readiness.probe_all(persist=True)
    transport = CanonicalDestinationTransportRuntimeV1()
    readiness_by_destination = lambda destination: (  # noqa: E731
        next((
            row for row in store.list_destination_readiness()
            if row["surface"] == registration_for_destination(destination).surface
        ), {})
    )
    coordinator = DurablePublicationCoordinator(
        store=store, transport_runtime=transport, readiness_provider=readiness_by_destination,
        readiness_manager=readiness,
    )
    supervisor = NativeLlmFirstContentOpsDailyAppSupervisor(
        store_path=store_path,
        output_root=output_root,
        operating_mode=operating_mode,
        clock=clock,
        store=store,
        sidecar_glob=sidecar_glob,
        enable_publication_lifecycle=True,
        publication_publisher=coordinator.publish_plan,
        publication_readback_provider=coordinator.readback,
        publication_coordinator=coordinator,
        enable_performance_observation=True,
        performance_collector=coordinator.collect_metrics,
        interaction_classifier=classify_interactions_with_nine_router,
        performance_learning_enabled=True,
        scheduled_editorial_owner=SCHEDULED_EDITORIAL_OWNER_NATIVE_DESKTOP,
    )
    return FinalDailyAppProductionRuntime(
        store=store, orchestrator=orchestrator, readiness_manager=readiness,
        transport_runtime=transport, publication_coordinator=coordinator,
        supervisor=supervisor,
    )
