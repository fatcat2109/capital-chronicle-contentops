from __future__ import annotations

import importlib.util
from pathlib import Path

from live_contentops.browser_rendered_source_recovery_v1 import BROWSER_UNAVAILABLE
from live_contentops.browseros_identity_shadow_gate_v1 import (
    STATUS_AMBIGUOUS,
    STATUS_CONFIRMED,
    STATUS_DISABLED,
    STATUS_HUMAN_REQUIRED,
    STATUS_MISSING,
    evaluate_browseros_identity_shadow,
)
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


def test_identity_shadow_confirms_exact_visible_account_and_destination():
    result = evaluate_browseros_identity_shadow(
        enabled=True,
        expected_account_label="contentops-social-main",
        expected_destination="X",
        visible_ui_metadata={
            "account_label": "contentops-social-main",
            "destination": "X",
        },
        snapshot_text="Account: contentops-social-main\nDestination: X",
    )

    assert result["status"] == STATUS_CONFIRMED
    assert result["account_identity_proven"] is True
    assert result["observed_account_label"] == "contentops-social-main"
    assert result["observed_destination"] == "X"
    assert len(result["visible_ui_sha256"]) == 64
    assert len(result["snapshot_sha256"]) == 64
    assert len(result["identity_evidence_sha256"]) == 64


def test_identity_shadow_marks_visible_mismatch_ambiguous():
    result = evaluate_browseros_identity_shadow(
        enabled=True,
        expected_account_label="contentops-social-main",
        expected_destination="X",
        visible_ui_metadata={
            "account_label": "different-account",
            "destination": "X",
        },
    )

    assert result["status"] == STATUS_AMBIGUOUS
    assert result["failure_detail"] == "visible_identity_mismatch"
    assert result["account_identity_proven"] is False


def test_identity_shadow_returns_missing_or_human_required_for_absent_or_truncated_ui():
    missing = evaluate_browseros_identity_shadow(
        enabled=True,
        expected_account_label="contentops-social-main",
        expected_destination="X",
    )
    truncated = evaluate_browseros_identity_shadow(
        enabled=True,
        expected_account_label="contentops-social-main",
        expected_destination="X",
        snapshot_text=(
            "Account: contentops-social-main\nDestination: X\n"
            "Content truncated at 5000 chars."
        ),
    )

    assert missing["status"] == STATUS_MISSING
    assert missing["account_identity_proven"] is False
    assert truncated["status"] == STATUS_HUMAN_REQUIRED
    assert truncated["account_identity_proven"] is False


def test_identity_shadow_redacts_credentials_before_hashing_or_returning_evidence():
    result = evaluate_browseros_identity_shadow(
        enabled=True,
        expected_account_label="contentops-social-main",
        expected_destination="X",
        visible_ui_metadata={
            "account_label": "contentops-social-main",
            "destination": "X",
            "access_token": "SECRET_TOKEN_VALUE",
            "cookie": "SECRET_COOKIE_VALUE",
        },
        snapshot_text=(
            "Account: contentops-social-main\nDestination: X\n"
            "authorization=SECRET_AUTH_VALUE"
        ),
    )

    serialized = str(result)
    assert result["status"] == STATUS_CONFIRMED
    assert result["redaction_applied"] is True
    assert result["credential_or_session_material_read"] is False
    assert "SECRET_TOKEN_VALUE" not in serialized
    assert "SECRET_COOKIE_VALUE" not in serialized
    assert "SECRET_AUTH_VALUE" not in serialized


def test_identity_shadow_disabled_does_not_iterate_visible_metadata():
    class ExplodingMetadata(dict):
        def items(self):
            raise AssertionError("disabled identity shadow must not inspect UI metadata")

    result = evaluate_browseros_identity_shadow(
        enabled=False,
        expected_account_label="contentops-social-main",
        expected_destination="X",
        visible_ui_metadata=ExplodingMetadata(),
    )

    assert result["status"] == STATUS_DISABLED
    assert result["account_identity_proven"] is False
    assert result["visible_ui_sha256"] is None


def test_scheduled_dry_run_receipt_includes_optional_identity_shadow_gate():
    result = run_scheduled_browseros_dry_run(
        enabled=True,
        preflight_runner=_healthy_preflight,
        identity_shadow_enabled=True,
        identity_shadow_expected_account_label="contentops-social-main",
        identity_shadow_expected_destination="X",
        identity_shadow_visible_ui_metadata={
            "account_label": "contentops-social-main",
            "destination": "X",
        },
    )

    assert result["status"] == "PASS"
    assert result["identity_shadow"]["status"] == STATUS_CONFIRMED
    assert result["identity_shadow"]["account_identity_proven"] is True
    assert result["scheduler_started"] is False
