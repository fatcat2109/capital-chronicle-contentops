from __future__ import annotations

import importlib.util
from pathlib import Path

from live_contentops.browser_rendered_source_recovery_v1 import BROWSER_UNAVAILABLE
from live_contentops.v1_simple_gemini_scheduler_process_v1 import (
    SCHEDULED_BROWSEROS_DRY_RUN_FAIL_CLOSED,
    SCHEDULED_BROWSEROS_DRY_RUN_FEATURE_DISABLED,
    SCHEDULED_BROWSEROS_DRY_RUN_PROFILE_AMBIGUOUS,
    run_scheduled_browseros_dry_run,
)


def _healthy_preflight(**_kwargs) -> dict:
    return {
        "status": "PASS",
        "lifecycle_state": "HEALTHY",
        "server_name": "browseros-neo",
        "server_version": "0.0.test",
        "mcp_protocol_version": "2025-06-18",
        "allowed_tools": ["name_session", "read", "tabs"],
        "read_only": True,
        "credential_or_session_material_read": False,
        "model_call_count": 0,
        "public_write_performed": False,
        "publication_authority": False,
    }


def _load_scheduler_script_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "run_v1_simple_gemini_scheduler.py"
    spec = importlib.util.spec_from_file_location("run_v1_simple_gemini_scheduler_wave4", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_disabled_by_default_never_invokes_preflight_or_recovery():
    calls: list[str] = []

    def preflight(**_kwargs):
        calls.append("preflight")
        raise AssertionError("disabled seam must not call BrowserOS")

    def recovery(_preflight):
        calls.append("recovery")
        raise AssertionError("disabled seam must not call resolver recovery")

    result = run_scheduled_browseros_dry_run(
        enabled=False,
        preflight_runner=preflight,
        recovery_runner=recovery,
    )

    assert result["status"] == SCHEDULED_BROWSEROS_DRY_RUN_FAIL_CLOSED
    assert result["failure_class"] == SCHEDULED_BROWSEROS_DRY_RUN_FEATURE_DISABLED
    assert result["feature_enabled"] is False
    assert result["preflight_invocation_count"] == 0
    assert result["scheduler_started"] is False
    assert result["durable_store_write_count"] == 0
    assert calls == []


def test_healthy_preflight_without_candidate_is_pass_and_does_not_construct_scheduler():
    result = run_scheduled_browseros_dry_run(
        enabled=True,
        preflight_runner=_healthy_preflight,
    )

    assert result["status"] == "PASS"
    assert result["preflight"]["status"] == "PASS"
    assert result["recovery"]["status"] == "NOT_REQUESTED"
    assert result["recovery_contract"]["http_first"] is True
    assert result["recovery_contract"]["shared_request_budget"] is True
    assert result["recovery_contract"]["max_browser_rendered_recovery_attempts"] == 1
    assert result["scheduler_started"] is False
    assert result["durable_store_write_count"] == 0
    assert result["model_call_count"] == 0
    assert result["public_write_performed"] is False


def test_injected_resolver_recovery_preserves_http_first_and_one_attempt():
    recovery_calls: list[dict] = []

    def recovery(preflight):
        recovery_calls.append(dict(preflight))
        return {
            "status": "BROWSER_RENDERED_RECOVERY_DRY_RUN_PASS",
            "http_first": True,
            "shared_request_budget": True,
            "browser_rendered_recovery_attempt_count": 1,
            "public_write_performed": False,
            "publication_authority": False,
        }

    result = run_scheduled_browseros_dry_run(
        enabled=True,
        preflight_runner=_healthy_preflight,
        recovery_runner=recovery,
    )

    assert result["status"] == "PASS"
    assert len(recovery_calls) == 1
    assert result["recovery"]["browser_rendered_recovery_attempt_count"] == 1


def test_browser_unavailable_preflight_is_terminal_and_skips_recovery():
    recovery_calls: list[str] = []

    def preflight(**_kwargs):
        return {
            "status": BROWSER_UNAVAILABLE,
            "failure_detail": "browseros_neo_mcp_unavailable",
        }

    result = run_scheduled_browseros_dry_run(
        enabled=True,
        preflight_runner=preflight,
        recovery_runner=lambda _preflight: recovery_calls.append("recovery"),
    )

    assert result["status"] == BROWSER_UNAVAILABLE
    assert result["failure_class"] == BROWSER_UNAVAILABLE
    assert result["fail_closed"] is True
    assert recovery_calls == []


def test_preflight_timeout_is_structured_browser_unavailable():
    def preflight(**_kwargs):
        raise TimeoutError("preflight timed out")

    result = run_scheduled_browseros_dry_run(
        enabled=True,
        preflight_runner=preflight,
    )

    assert result["status"] == BROWSER_UNAVAILABLE
    assert result["failure_class"] == BROWSER_UNAVAILABLE
    assert result["failure_detail"] == "preflight timed out"
    assert result["preflight_invocation_count"] == 1


def test_preflight_unavailable_exception_is_structured_browser_unavailable():
    def preflight(**_kwargs):
        raise RuntimeError("browseros_neo_mcp_unavailable")

    result = run_scheduled_browseros_dry_run(
        enabled=True,
        preflight_runner=preflight,
    )

    assert result["status"] == BROWSER_UNAVAILABLE
    assert result["failure_class"] == BROWSER_UNAVAILABLE
    assert result["preflight_invocation_count"] == 1


def test_profile_ambiguous_is_fail_closed_before_recovery():
    recovery_calls: list[str] = []
    preflight = {**_healthy_preflight(), "profile_identity_status": "AMBIGUOUS"}

    result = run_scheduled_browseros_dry_run(
        enabled=True,
        preflight_runner=lambda **_kwargs: preflight,
        recovery_runner=lambda _preflight: recovery_calls.append("recovery"),
    )

    assert result["status"] == SCHEDULED_BROWSEROS_DRY_RUN_FAIL_CLOSED
    assert result["failure_class"] == SCHEDULED_BROWSEROS_DRY_RUN_PROFILE_AMBIGUOUS
    assert recovery_calls == []


def test_recovery_attempt_budget_violation_is_fail_closed():
    result = run_scheduled_browseros_dry_run(
        enabled=True,
        preflight_runner=_healthy_preflight,
        recovery_runner=lambda _preflight: {
            "status": "BROWSER_RENDERED_RECOVERY_DRY_RUN_PASS",
            "http_first": True,
            "shared_request_budget": True,
            "browser_rendered_recovery_attempt_count": 2,
        },
    )

    assert result["status"] == SCHEDULED_BROWSEROS_DRY_RUN_FAIL_CLOSED
    assert result["failure_class"] == "RECOVERY_CONTRACT_INVALID"


def test_entrypoint_flag_is_explicit_and_exits_before_scheduler_construction(monkeypatch):
    module = _load_scheduler_script_module()
    parsed = module.build_parser().parse_args(["--browseros-dry-run"])
    assert parsed.browseros_dry_run is True
    assert module.build_parser().parse_args([]).browseros_dry_run is False

    monkeypatch.setattr(
        module,
        "run_scheduled_browseros_dry_run",
        lambda *, enabled: {"status": "PASS", "feature_enabled": enabled},
    )
    monkeypatch.setattr(
        module,
        "SimpleGeminiLocalScheduler",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("dry-run must exit before scheduler construction")
        ),
    )
    monkeypatch.setattr(
        module,
        "build_canonical_simple_publication_handoff",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("dry-run must not construct publication handoff")
        ),
    )

    assert module.main(["--browseros-dry-run"]) == 0
