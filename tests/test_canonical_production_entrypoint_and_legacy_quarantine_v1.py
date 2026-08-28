from __future__ import annotations

import ast
import http.client
import importlib
import json
import sys
import threading
from http.server import HTTPServer
from pathlib import Path
from types import SimpleNamespace

import pytest

from live_contentops import live_entrypoint_registry_v1 as registry
from live_contentops.live_entrypoint_registry_v1 import LiveEntrypointQuarantined
from live_contentops.production_orchestrator_v1 import (
    CANONICAL_FUNCTION,
    CANONICAL_MODULE,
    CANONICAL_OPERATIONS,
    ContentOpsProductionOrchestrator,
    ROUTINE_EDITORIAL_OPERATION,
    ROUTINE_EDITORIAL_OWNER,
)

ROOT = Path(__file__).resolve().parents[1]
TEST_FILE = "tests/test_canonical_production_entrypoint_and_legacy_quarantine_v1.py"
LEGACY_MODULES = {
    "contentops.legacy_fast_one_cycle.v0": (
        "live_contentops.fast_one_cycle_automation_v0",
        "run_fast_one_cycle",
        {},
    ),
    "contentops.legacy_full_pipeline_debug_live.v0": (
        "live_contentops.full_pipeline_north_star_debug_and_live_run_v0",
        "run_full_pipeline_north_star_debug_and_live_run",
        {
            "operator_approved_full_live_run": True,
            "repair_previous_telegram_message_id": "not-used",
        },
    ),
    "contentops.legacy_operator_daily_live.v0": (
        "live_contentops.operator_approved_supervised_live_daily_run_v0",
        "run_operator_approved_supervised_live_daily_run",
        {"operator_approved_live_run": True},
    ),
    "contentops.legacy_terra_ultra_live.v1": (
        "live_contentops.terra_ultra_north_star_full_automation_v1",
        "run_terra_ultra_north_star_full_automation",
        {"operator_approved_full_live_run": True},
    ),
}


def _assert_quarantined(callable_, expected_id: str, **kwargs: object) -> None:
    with pytest.raises(LiveEntrypointQuarantined) as caught:
        callable_(**kwargs)
    assert caught.value.entrypoint_id == expected_id
    assert caught.value.status in {
        registry.LIVE_PATH_QUARANTINED,
        registry.HTTP_LAUNCH_QUARANTINED,
        registry.SCHEDULER_LIVE_QUARANTINED,
        registry.LEGACY_AUTOMATION_QUARANTINED,
        registry.BROWSER_PROFILE_EXECUTION_QUARANTINED,
    }
    assert caught.value.as_dict()["canonical_entrypoint_id"] == "contentops.production_orchestrator.v1"


def test_exactly_one_registry_row_is_canonical():
    registry.validate_registry()
    canonical = [row for row in registry.ENTRYPOINTS if row.canonical]
    assert len(canonical) == 1
    assert canonical[0].entrypoint_id == "contentops.production_orchestrator.v1"
    assert canonical[0].current_action == "CANONICAL"
    assert all(row.proving_tests for row in registry.ENTRYPOINTS)


def test_registry_export_is_stable_and_json_serializable(tmp_path):
    target = tmp_path / "live_entrypoint_registry_v1.json"
    payload = registry.export_registry(target)
    written = json.loads(target.read_text(encoding="utf-8"))
    assert written == json.loads(json.dumps(payload))
    assert payload["canonical_entrypoint_id"] == "contentops.production_orchestrator.v1"
    assert len(payload["entrypoints"]) == len(registry.ENTRYPOINTS)


def test_orchestrator_is_lazy_and_bound(monkeypatch):
    sys.modules.pop(CANONICAL_MODULE, None)
    calls: list[tuple[str, dict[str, object]]] = []

    def fake_dispatcher(operation: str, **kwargs: object) -> dict[str, object]:
        calls.append((operation, kwargs))
        return {"status": "BOUND", "operation": operation, **kwargs}

    def fake_import(name: str):
        assert name == CANONICAL_MODULE
        return SimpleNamespace(**{CANONICAL_FUNCTION: fake_dispatcher})

    monkeypatch.setattr("live_contentops.production_orchestrator_v1.import_module", fake_import)
    orchestrator = ContentOpsProductionOrchestrator()
    assert CANONICAL_MODULE not in sys.modules
    assert orchestrator.run(run_id="local-proof") == {
        "status": "BOUND",
        "operation": "run_eight_platform_substack_first_pipeline",
        "run_id": "local-proof",
    }
    assert calls == [("run_eight_platform_substack_first_pipeline", {"run_id": "local-proof"})]


def test_orchestrator_rejects_unknown_operation_before_import(monkeypatch):
    monkeypatch.setattr(
        "live_contentops.production_orchestrator_v1.import_module",
        lambda *_: pytest.fail("private implementation import reached"),
    )
    with pytest.raises(ValueError, match="unknown_canonical_contentops_operation"):
        ContentOpsProductionOrchestrator().execute("caller_supplied_bypass", enabled=True)


def test_public_compatibility_import_is_safe_and_all_live_apis_delegate_once(monkeypatch, tmp_path):
    sys.modules.pop(CANONICAL_MODULE, None)
    public_module = importlib.import_module("live_contentops.eight_platform_substack_first_pipeline_v1")
    assert CANONICAL_MODULE not in sys.modules
    calls: list[tuple[str, dict[str, object]]] = []

    class FakeOrchestrator:
        def execute(self, operation: str, **kwargs: object) -> dict[str, object]:
            calls.append((operation, kwargs))
            return {"operation": operation, **kwargs}

    monkeypatch.setattr(public_module, "ContentOpsProductionOrchestrator", FakeOrchestrator)
    invocations = {
        "prepare_text_image_release_candidate": lambda: public_module.prepare_text_image_release_candidate(run_id="r", output_dir=tmp_path),
        "prepare_generic_text_image_release_candidate": lambda: public_module.prepare_generic_text_image_release_candidate(run_id="r", output_dir=tmp_path),
        "build_operator_manual_audit_packet": lambda: public_module.build_operator_manual_audit_packet(output_dir=tmp_path),
        "ensure_canonical_edge_publishing_runtime": lambda: public_module.ensure_canonical_edge_publishing_runtime(urls=("https://substack.com/",), wait_seconds=0.0),
        "run_eight_platform_substack_first_pipeline": lambda: public_module.run_eight_platform_substack_first_pipeline(run_id="r", output_dir=tmp_path, operator_approved_full_live_run=False),
        "run_rolling_x_newsroom_cycle": lambda: public_module.run_rolling_x_newsroom_cycle(run_id="r", output_dir=tmp_path, cutoff_utc="2026-08-08T00:00:00Z", publication_enabled=False),
        "run_v1_simple_gemini_newsroom": lambda: public_module.run_v1_simple_gemini_newsroom(output_dir=tmp_path, cutoff_utc="2026-08-27T00:00:00Z", rolling_input={"headlines": []}),
        "build_native_derivative_payloads": lambda: public_module.build_native_derivative_payloads(
            article={"title": "Supported title", "subtitle": "Supported detail"},
            selection={},
            canonical_url="https://capitalchronicle.substack.com/p/pending-publication-test",
            media_asset_ids=(),
        ),
        "reconcile_public_substack_for_derivative_resume": lambda: public_module.reconcile_public_substack_for_derivative_resume(output_dir=tmp_path),
        "resume_eight_platform_derivatives": lambda: public_module.resume_eight_platform_derivatives(output_dir=tmp_path),
        "reconcile_existing_derivative_readbacks": lambda: public_module.reconcile_existing_derivative_readbacks(output_dir=tmp_path),
        "repair_exact_substack_caption_fragment": lambda: public_module.repair_exact_substack_caption_fragment(output_dir=tmp_path, cdp_port=9223),
        "repair_exact_treasury_release_candidate_editorial": lambda: public_module.repair_exact_treasury_release_candidate_editorial(output_dir=tmp_path, cdp_port=9223),
        "repair_final_treasury_auction_logic": lambda: public_module.repair_final_treasury_auction_logic(output_dir=tmp_path, cdp_port=9223),
        "reconcile_linkedin_activity_pair": lambda: public_module.reconcile_linkedin_activity_pair(output_dir=tmp_path, cdp_port=9223, accepted_url="a", accepted_id="1", latest_url="b", latest_id="2"),
    }
    for expected_operation, invoke in invocations.items():
        calls.clear()
        result = invoke()
        assert result["operation"] == expected_operation
        assert [operation for operation, _ in calls] == [expected_operation]
        assert CANONICAL_MODULE not in sys.modules
    assert set(invocations) == set(CANONICAL_OPERATIONS) - {"module_cli"}


def test_public_rolling_x_facade_forwards_preselection_intelligence(monkeypatch, tmp_path):
    public_module = importlib.import_module("live_contentops.eight_platform_substack_first_pipeline_v1")
    calls: list[tuple[str, dict[str, object]]] = []

    class FakeOrchestrator:
        def execute(self, operation: str, **kwargs: object) -> dict[str, object]:
            calls.append((operation, kwargs))
            return {"operation": operation, **kwargs}

    monkeypatch.setattr(public_module, "ContentOpsProductionOrchestrator", FakeOrchestrator)
    corpus = [{"article_identity": "article-1"}]
    catalog = {"catalog_fingerprint": "catalog-1"}
    readiness = {"SUBSTACK_ARTICLE": {"readiness_state": "READY_AUTHENTICATED"}}
    desktop_builder = object()
    desktop_reviewer = lambda article: article

    result = public_module.run_rolling_x_newsroom_cycle(
        run_id="operator-cycle-1",
        output_dir=tmp_path,
        cutoff_utc="2026-08-11T02:00:00Z",
        publication_enabled=True,
        operating_mode="AUTONOMOUS_DEFAULT",
        published_corpus=corpus,
        cc_catalog=catalog,
        destination_readiness_override=readiness,
        article_builder=desktop_builder,
        editorial_reviewer=desktop_reviewer,
    )

    assert len(calls) == 1
    assert calls[0][0] == "run_rolling_x_newsroom_cycle"
    assert result["operating_mode"] == "AUTONOMOUS_DEFAULT"
    assert result["published_corpus"] is corpus
    assert result["cc_catalog"] is catalog
    assert result["destination_readiness_override"] is readiness
    assert result["article_builder"] is desktop_builder
    assert result["editorial_reviewer"] is desktop_reviewer
    assert result["editorial_execution_route"] == "DESKTOP_PRIMARY"
    assert result["desktop_primary_routine_authority"] is True


def test_public_rolling_x_facade_fails_closed_without_desktop_primary_builder_or_fallback_receipt(
    tmp_path,
):
    public_module = importlib.import_module("live_contentops.eight_platform_substack_first_pipeline_v1")
    with pytest.raises(ValueError, match="desktop_primary_editorial_builder_required"):
        public_module.run_rolling_x_newsroom_cycle(
            run_id="routine-primary",
            output_dir=tmp_path,
            cutoff_utc="2026-08-22T00:00:00Z",
            publication_enabled=True,
        )
    with pytest.raises(ValueError, match="desktop_primary_editorial_reviewer_required"):
        public_module.run_rolling_x_newsroom_cycle(
            run_id="routine-primary-without-review",
            output_dir=tmp_path,
            cutoff_utc="2026-08-22T00:00:00Z",
            publication_enabled=True,
            article_builder=object(),
        )
    with pytest.raises(ValueError, match="sdk_fallback_arbitration_receipt_required"):
        public_module.run_rolling_x_newsroom_cycle(
            run_id="routine-fallback",
            output_dir=tmp_path,
            cutoff_utc="2026-08-22T00:00:00Z",
            publication_enabled=True,
            editorial_execution_route="SDK_FALLBACK",
        )


def test_public_rolling_x_facade_starts_sdk_only_with_bound_fallback_arbitration(
    monkeypatch, tmp_path
):
    public_module = importlib.import_module("live_contentops.eight_platform_substack_first_pipeline_v1")
    provider_module = importlib.import_module("live_contentops.official_codex_provider_v1")
    from live_contentops.codex_desktop_newsroom_operator_v1 import (
        arbitrate_hybrid_editorial_execution,
        build_hybrid_editorial_run_identity,
    )

    calls: list[tuple[str, dict[str, object]]] = []

    class FakeOrchestrator:
        def execute(self, operation: str, **kwargs: object) -> dict[str, object]:
            calls.append((operation, kwargs))
            return {"operation": operation, **kwargs}

    class FakeSdkBuilder:
        def __init__(self, *, output_dir: Path):
            self.output_dir = output_dir

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(public_module, "ContentOpsProductionOrchestrator", FakeOrchestrator)
    monkeypatch.setattr(provider_module, "OfficialCodexEditorialArticleBuilder", FakeSdkBuilder)
    identity = build_hybrid_editorial_run_identity(
        runtime_run_id="routine-fallback",
        production_day_id="2026-08-22",
        opportunity_id="new-york-0100",
        story_identity="official-primary-ffb8e742e0932254c29d",
        governed_input_hash="e" * 64,
    )
    arbitration = arbitrate_hybrid_editorial_execution(
        run_identity=identity,
        observed_at_utc="2026-08-22T01:01:00Z",
        valid_window_ends_at_utc="2026-08-22T01:00:00Z",
        desktop_primary_receipt={
            "canonical_run_identity": identity["canonical_run_identity"],
            "state": "MISSED_VALID_WINDOW",
        },
    )

    result = public_module.run_rolling_x_newsroom_cycle(
        run_id="routine-fallback",
        output_dir=tmp_path,
        cutoff_utc="2026-08-22T00:00:00Z",
        publication_enabled=True,
        editorial_execution_route="SDK_FALLBACK",
        hybrid_arbitration_receipt=arbitration,
    )

    assert len(calls) == 1
    assert isinstance(result["article_builder"], FakeSdkBuilder)
    assert result["editorial_execution_route"] == "SDK_FALLBACK"
    assert result["hybrid_editorial_arbitration"]["decision"] == "START_SDK_FALLBACK"


@pytest.mark.parametrize(
    "argv",
    [
        ["--run-id", "r", "--output-dir", "out", "--operator-approved-full-live-run"],
        ["--run-id", "r", "--output-dir", "out", "--resume-derivatives"],
        ["--run-id", "r", "--output-dir", "out", "--reconcile-readbacks"],
        ["--run-id", "r", "--output-dir", "out", "--reconcile-linkedin-pair"],
        ["--run-id", "r", "--output-dir", "out", "--repair-substack-caption-fragment"],
        ["--run-id", "r", "--output-dir", "out", "--repair-treasury-rc-editorial"],
        ["--run-id", "r", "--output-dir", "out", "--repair-final-treasury-auction-logic"],
        ["--run-id", "r", "--output-dir", "out", "--prepare-only"],
        ["--run-id", "r", "--output-dir", "out", "--prepare-generic-live-release"],
        ["--run-id", "r", "--output-dir", "out", "--build-operator-audit-packet"],
        ["--run-id", "r", "--output-dir", "out", "--closure-historical-repair"],
        ["--run-id", "r", "--output-dir", "out", "--finalize-v1-tag"],
    ],
)
def test_every_live_capable_canonical_cli_family_delegates_once(monkeypatch, argv):
    sys.modules.pop(CANONICAL_MODULE, None)
    public_module = importlib.import_module("live_contentops.eight_platform_substack_first_pipeline_v1")
    calls: list[tuple[str, dict[str, object]]] = []

    class FakeOrchestrator:
        def execute(self, operation: str, **kwargs: object) -> int:
            calls.append((operation, kwargs))
            return 0

    monkeypatch.setattr(public_module, "ContentOpsProductionOrchestrator", FakeOrchestrator)
    assert public_module.main(argv) == 0
    assert calls == [("module_cli", {"argv": argv})]
    assert CANONICAL_MODULE not in sys.modules


def test_closure_historical_repair_cli_delegates_once_without_private_import(monkeypatch):
    sys.modules.pop(CANONICAL_MODULE, None)
    public_module = importlib.import_module("live_contentops.eight_platform_substack_first_pipeline_v1")
    calls: list[tuple[str, dict[str, object]]] = []

    class FakeOrchestrator:
        def execute(self, operation: str, **kwargs: object) -> int:
            calls.append((operation, kwargs))
            return 0

    monkeypatch.setattr(public_module, "ContentOpsProductionOrchestrator", FakeOrchestrator)
    argv = ["--run-id", "r", "--output-dir", "out", "--closure-historical-repair"]
    assert public_module.main(argv) == 0
    assert calls == [("module_cli", {"argv": argv})]
    assert CANONICAL_MODULE not in sys.modules


def test_finalize_v1_tag_cli_delegates_once_without_private_import(monkeypatch):
    sys.modules.pop(CANONICAL_MODULE, None)
    public_module = importlib.import_module("live_contentops.eight_platform_substack_first_pipeline_v1")
    calls: list[tuple[str, dict[str, object]]] = []

    class FakeOrchestrator:
        def execute(self, operation: str, **kwargs: object) -> int:
            calls.append((operation, kwargs))
            return 0

    monkeypatch.setattr(public_module, "ContentOpsProductionOrchestrator", FakeOrchestrator)
    argv = ["--run-id", "r", "--output-dir", "out", "--finalize-v1-tag"]
    assert public_module.main(argv) == 0
    assert calls == [("module_cli", {"argv": argv})]
    assert CANONICAL_MODULE not in sys.modules


def test_private_dispatcher_exact_map_has_no_public_wrapper_targets():
    implementation = importlib.import_module(CANONICAL_MODULE)
    operation_map = implementation._CANONICAL_OPERATIONS
    assert set(operation_map) == set(CANONICAL_OPERATIONS)
    assert all(callable(target) for target in operation_map.values())
    assert all(target.__module__ == CANONICAL_MODULE for target in operation_map.values())
    assert all(target.__name__.startswith("_") for target in operation_map.values())
    with pytest.raises(ValueError, match="unknown_canonical_contentops_operation"):
        implementation._dispatch_canonical_operation("not_registered")


def test_legacy_live_flags_fail_before_pipeline_body(monkeypatch):
    from live_contentops import live_production_pipeline_runner_v6 as legacy

    monkeypatch.setattr(legacy, "_load_live_env_if_needed", lambda *_: pytest.fail("env load reached"))
    for flags in ({"live_run": True}, {"dispatch_live": True}, {"dispatch_rehearsal": True}):
        _assert_quarantined(
            legacy.run_live_production_pipeline,
            "contentops.legacy_v6_runner.v1",
            topic="topic",
            editorial_angle="angle",
            **flags,
        )


def test_server_post_is_machine_readable_and_cannot_launch():
    from live_contentops.server import PipelineServerHandler

    server = HTTPServer(("127.0.0.1", 0), PipelineServerHandler)
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()
    try:
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
        connection.request("POST", "/api/run-pipeline", body=b"{}", headers={"Content-Type": "application/json"})
        response = connection.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
    finally:
        server.server_close()
        thread.join(timeout=3)
    assert response.status == 423
    assert payload["status"] == registry.HTTP_LAUNCH_QUARANTINED
    assert payload["thread_created"] is False
    assert payload["subprocess_created"] is False
    assert payload["live_launch_authorized"] is False


def test_ui_route_is_registered_and_server_route_is_quarantined():
    ui = (ROOT / "ui/contentops_v5/src/views/V6CommandCenter.tsx").read_text(encoding="utf-8")
    server = (ROOT / "live_contentops/server.py").read_text(encoding="utf-8")
    assert "/api/run-pipeline" in ui
    assert registry.HTTP_LAUNCH_QUARANTINED in ui
    assert "/api/run-pipeline" in server
    server_tree = ast.parse(server)
    imported_modules = {
        alias.name
        for node in ast.walk(server_tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert "subprocess" not in imported_modules
    assert "threading" not in imported_modules


def test_scheduler_live_dispatch_fails_before_import(monkeypatch):
    from live_contentops.scheduler_v6 import dispatch_platform_action

    original_import = __import__

    def guarded_import(name, *args, **kwargs):
        if name.endswith("telegram_live_adapter_v6"):
            pytest.fail("adapter import reached")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", guarded_import)
    _assert_quarantined(
        dispatch_platform_action,
        "contentops.scheduler_dispatch_function.v1",
        platform_id="telegram",
        action="post",
        payload={},
        dry_run=False,
    )




def test_scheduler_unsupported_platform_fixture_is_never_live_success():
    from live_contentops.scheduler_v6 import dispatch_platform_action

    result = dispatch_platform_action(
        platform_id="unsupported_platform",
        action="post",
        payload={},
        dry_run=True,
    )

    assert result == {
        "status": "DRY_RUN_UNSUPPORTED_PLATFORM",
        "id": None,
        "response": {"mocked": True, "live_success": False},
    }
    assert result["status"] != "SUCCESS"
    assert result["response"]["live_success"] is False


def test_scheduler_live_tick_fails_before_load_or_save(monkeypatch, tmp_path):
    from live_contentops.scheduler_v6 import OutboxScheduler

    scheduler = OutboxScheduler(tmp_path / "must-not-exist.json")
    monkeypatch.setattr(scheduler, "load_entries", lambda: pytest.fail("load reached"))
    monkeypatch.setattr(scheduler, "save_entries", lambda *_: pytest.fail("save reached"))
    _assert_quarantined(
        scheduler.reconcile_outbox_timing,
        "contentops.scheduler_tick.v1",
        dry_run=False,
    )
    assert not scheduler.registry_path.exists()


def test_cli_fast_ship_scheduler_fails_before_scheduler_import(monkeypatch):
    from live_contentops import cli

    sys.modules.pop("live_contentops.scheduler_v6", None)
    original_import = __import__

    def guarded_import(name, *args, **kwargs):
        if name.endswith("scheduler_v6"):
            pytest.fail("scheduler import reached")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", guarded_import)
    _assert_quarantined(
        cli.scheduler_tick_command,
        "contentops.cli_scheduler_fast_ship.v1",
        argv=["--fast-ship"],
    )
    assert "live_contentops.scheduler_v6" not in sys.modules


def test_registry_covers_direct_cli_adapter_families():
    row = registry.get_entrypoint("contentops.cli_direct_platform_adapters.v1")
    for family in ("x", "substack", "telegram", "discord", "facebook", "instagram", "threads"):
        assert family in row.function_or_route


def test_cli_telegram_pilot_fails_before_env_or_pilot_import(monkeypatch):
    from live_contentops import cli

    sys.modules.pop("live_contentops.telegram_live_pilot", None)
    monkeypatch.setattr("os.getenv", lambda *_: pytest.fail("environment read reached"))
    _assert_quarantined(cli.telegram_live_pilot_execute, "contentops.cli_direct_platform_adapters.v1")
    assert "live_contentops.telegram_live_pilot" not in sys.modules


@pytest.mark.parametrize(
    "entrypoint_id,module_name,function_name,kwargs",
    [(entrypoint_id, *value) for entrypoint_id, value in LEGACY_MODULES.items()],
)
def test_legacy_automation_callables_fail_before_io_env_or_adapter_import(
    monkeypatch, entrypoint_id, module_name, function_name, kwargs
):
    forbidden = {
        "live_contentops.telegram_live_adapter_v6",
        "live_contentops.discord_live_adapter_v6",
        "live_contentops.substack_browser_adapter_v6",
    }
    for name in forbidden:
        sys.modules.pop(name, None)
    monkeypatch.setattr(Path, "mkdir", lambda *_args, **_kwargs: pytest.fail("filesystem mutation reached"))
    monkeypatch.setattr("os.getenv", lambda *_: pytest.fail("environment read reached"))
    module = importlib.import_module(module_name)
    _assert_quarantined(getattr(module, function_name), entrypoint_id, **kwargs)
    assert forbidden.isdisjoint(sys.modules)


def test_legacy_substack_loop_entrypoints_fail_before_io_env_or_adapter_import(monkeypatch):
    module_name = "live_contentops.substack_first_north_star_pipeline_loop_v1"
    forbidden = {
        "live_contentops.ai_provider_gate_v6",
        "live_contentops.current_oil_release_source_v1",
        "live_contentops.substack_browser_adapter_v6",
        "live_contentops.telegram_live_adapter_v6",
    }
    for name in forbidden:
        sys.modules.pop(name, None)
    module = importlib.import_module(module_name)
    monkeypatch.setattr(module, "_load_dotenv_safely", lambda: pytest.fail("dotenv reached"))
    monkeypatch.setattr(Path, "mkdir", lambda *_args, **_kwargs: pytest.fail("filesystem mutation reached"))
    _assert_quarantined(
        module.prepare_substack_first_pipeline,
        "contentops.legacy_substack_first_loop.v1",
        run_id="not-used",
        publication_mode="draft",
        output_dir=Path("not-written"),
    )
    _assert_quarantined(
        module.complete_substack_first_pipeline,
        "contentops.legacy_substack_first_loop.v1",
        context_path=Path("not-read.json"),
        substack_readback_path=Path("not-read-readback.json"),
        operator_approved_full_live_run=True,
    )
    _assert_quarantined(module.main, "contentops.legacy_substack_first_loop.v1", argv=["--prepare"])
    assert forbidden.isdisjoint(sys.modules)


def test_direct_browser_profile_execution_fails_before_process_or_network_access(monkeypatch):
    from live_contentops import publishing_profile_registry_v1 as profiles

    monkeypatch.setattr(profiles, "browser_doctor", lambda **_: pytest.fail("doctor/process/CDP reached"))
    _assert_quarantined(
        profiles.open_or_attach_canonical_edge,
        "contentops.direct_browser_profile_execution.v1",
        urls=["https://example.invalid/"],
    )
    _assert_quarantined(profiles.main, "contentops.direct_browser_profile_execution.v1", argv=["open"])


def test_script_wrappers_delegate_only_to_quarantined_legacy_callables():
    expected = {
        "scripts/run_fast_one_cycle_automation_v0.py": "run_fast_one_cycle",
        "scripts/run_full_pipeline_north_star_debug_and_live_run_v0.py": "run_full_pipeline_north_star_debug_and_live_run",
        "scripts/run_terra_ultra_north_star_full_automation_v1.py": "main",
        "scripts/run_substack_first_north_star_pipeline_loop_v1.py": "main",
    }
    for relative_path, callable_name in expected.items():
        tree = ast.parse((ROOT / relative_path).read_text(encoding="utf-8"))
        imported = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        }
        assert callable_name in imported
        assert all("adapter" not in name.lower() for name in imported)


def test_ast_live_path_scan_has_no_unguarded_http_launcher():
    server_tree = ast.parse((ROOT / "live_contentops/server.py").read_text(encoding="utf-8"))
    called = {
        node.func.id
        for node in ast.walk(server_tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    imported_modules = {
        alias.name
        for node in ast.walk(server_tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert "Popen" not in called
    assert "Thread" not in called
    assert "subprocess" not in imported_modules
    assert "threading" not in imported_modules


def test_every_registry_proving_test_resolves_to_this_suite():
    source = Path(__file__).read_text(encoding="utf-8")
    for row in registry.ENTRYPOINTS:
        for proving_test in row.proving_tests:
            path, _, test_name = proving_test.partition("::")
            assert path == TEST_FILE
            assert f"def {test_name}(" in source


def test_orchestrator_marks_simple_as_the_only_current_routine_owner():
    orchestrator = ContentOpsProductionOrchestrator()
    assert (
        orchestrator.routine_editorial_owner
        == ROUTINE_EDITORIAL_OWNER
        == "SIMPLE_GEMINI_RUNTIME"
    )
    assert (
        orchestrator.routine_editorial_operation
        == ROUTINE_EDITORIAL_OPERATION
        == "run_v1_simple_gemini_newsroom"
    )
