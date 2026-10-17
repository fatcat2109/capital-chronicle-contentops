from __future__ import annotations

import importlib.util
from pathlib import Path

from live_contentops.browser_rendered_source_recovery_v1 import BROWSER_UNAVAILABLE
from live_contentops.destination_readback_shadow_gate_v1 import (
    CONFIRMED_SHADOW,
    DISABLED_BY_DEFAULT,
    HUMAN_REQUIRED,
    MISMATCH,
    MISSING,
    UNKNOWN_WRITE,
    evaluate_destination_readback_shadow,
)
from live_contentops.hybrid_pipeline_shadow_v1 import (
    CONFIRMED_SHADOW as PIPELINE_CONFIRMED_SHADOW,
    DISABLED_BY_DEFAULT as PIPELINE_DISABLED,
    FAIL_CLOSED as PIPELINE_FAIL_CLOSED,
    HUMAN_REQUIRED as PIPELINE_HUMAN_REQUIRED,
    MISMATCH as PIPELINE_MISMATCH,
    MISSING as PIPELINE_MISSING,
    UNKNOWN_WRITE as PIPELINE_UNKNOWN_WRITE,
    evaluate_hybrid_pipeline_shadow,
)
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


def _substack_readback(**overrides):
    value = {
        "platform": "substack",
        "destination_kind": "CANONICAL_SUBSTACK",
        "destination_binding_id": "substack:canonical",
        "public_object_id": "post-123",
        "public_object_url": "https://capitalchronicle.substack.com/p/market-signal",
        "payload_sha256": "a" * 64,
        "readback_sha256": "b" * 64,
        "reconciliation_status": "RECONCILED_CONFIRMED",
        "public_write_performed": False,
    }
    value.update(overrides)
    return value


def _substack_expected():
    return {
        "expected_platform": "substack",
        "expected_destination_kind": "CANONICAL_SUBSTACK",
        "expected_destination_binding_id": "substack:canonical",
        "expected_public_object_id": "post-123",
        "expected_public_object_url": "https://capitalchronicle.substack.com/p/market-signal",
        "expected_payload_sha256": "a" * 64,
    }


def test_destination_shadow_confirms_exact_substack_readback_without_public_write_claim():
    result = evaluate_destination_readback_shadow(
        enabled=True,
        readback=_substack_readback(),
        **_substack_expected(),
    )

    assert result["status"] == CONFIRMED_SHADOW
    assert result["shadow_only"] is True
    assert result["account_identity_proven"] is False
    assert result["publication_success_proven"] is False
    assert result["public_write_performed"] is False
    assert len(result["readback_evidence_sha256"]) == 64
    assert len(result["reconciliation_identity_sha256"]) == 64


def test_destination_shadow_marks_destination_and_object_payload_mismatch():
    destination_mismatch = evaluate_destination_readback_shadow(
        enabled=True,
        readback=_substack_readback(platform="telegram"),
        **_substack_expected(),
    )
    object_payload_mismatch = evaluate_destination_readback_shadow(
        enabled=True,
        readback=_substack_readback(public_object_id="post-other", payload_sha256="c" * 64),
        **_substack_expected(),
    )

    assert destination_mismatch["status"] == MISMATCH
    assert "platform" in destination_mismatch["failure_detail"]
    assert object_payload_mismatch["status"] == MISMATCH
    assert "public_object_id" in object_payload_mismatch["failure_detail"]
    assert "payload_sha256" in object_payload_mismatch["failure_detail"]


def test_destination_shadow_handles_missing_truncated_and_unknown_write_fail_closed():
    missing = evaluate_destination_readback_shadow(
        enabled=True,
        readback={"platform": "substack"},
        **_substack_expected(),
    )
    human_required = evaluate_destination_readback_shadow(
        enabled=True,
        readback=_substack_readback(truncated=True),
        **_substack_expected(),
    )
    unknown = evaluate_destination_readback_shadow(
        enabled=True,
        readback=_substack_readback(status=UNKNOWN_WRITE, unknown_write=True),
        **_substack_expected(),
    )

    assert missing["status"] == MISSING
    assert human_required["status"] == HUMAN_REQUIRED
    assert unknown["status"] == UNKNOWN_WRITE
    assert unknown["retry_forbidden"] is True


def test_destination_shadow_redacts_sensitive_fields_before_hashing():
    result = evaluate_destination_readback_shadow(
        enabled=True,
        readback=_substack_readback(
            visible_note="authorization=SECRET_TOKEN_VALUE cookie=SECRET_COOKIE_VALUE"
        ),
        **_substack_expected(),
    )

    assert result["status"] == CONFIRMED_SHADOW
    assert result["redaction_applied"] is True
    assert "SECRET_TOKEN_VALUE" not in str(result)
    assert "SECRET_COOKIE_VALUE" not in str(result)


def test_destination_shadow_disabled_does_not_iterate_readback():
    class ExplodingReadback(dict):
        def items(self):
            raise AssertionError("disabled destination shadow must not inspect readback")

    result = evaluate_destination_readback_shadow(
        enabled=False,
        readback=ExplodingReadback(),
        **_substack_expected(),
    )

    assert result["status"] == DISABLED_BY_DEFAULT
    assert result["readback_evidence_sha256"] is None


def test_scheduled_receipt_includes_destination_shadow_without_scheduler_side_effects():
    result = run_scheduled_browseros_dry_run(
        enabled=True,
        preflight_runner=_healthy_preflight,
        destination_shadow_enabled=True,
        destination_shadow_readback=_substack_readback(),
        destination_shadow_expected_platform="substack",
        destination_shadow_expected_destination_kind="CANONICAL_SUBSTACK",
        destination_shadow_expected_binding_id="substack:canonical",
        destination_shadow_expected_public_object_id="post-123",
        destination_shadow_expected_public_object_url=(
            "https://capitalchronicle.substack.com/p/market-signal"
        ),
        destination_shadow_expected_payload_sha256="a" * 64,
    )

    assert result["status"] == "PASS"
    assert result["destination_shadow"]["status"] == CONFIRMED_SHADOW
    assert result["scheduler_started"] is False
    assert result["durable_store_write_count"] == 0


def _pipeline_components():
    return {
        "source_recovery": {
            "status": "BROWSER_RENDERED_RECOVERY_DRY_RUN_PASS",
            "http_first": True,
            "shared_request_budget": True,
            "browser_rendered_recovery_attempt_count": 1,
            "public_write_performed": False,
            "publication_authority": False,
        },
        "browser_preflight": {
            "status": "PASS",
            "read_only": True,
            "credential_or_session_material_read": False,
            "public_write_performed": False,
            "publication_authority": False,
        },
        "identity_shadow": {
            "status": "CONFIRMED",
            "account_identity_proven": True,
            "public_write_performed": False,
            "publication_authority": False,
        },
        "destination_shadow": {
            "status": "CONFIRMED_SHADOW",
            "public_write_performed": False,
            "publication_authority": False,
        },
        "x_ingestion_boundary": {
            "status": "INGESTION_ONLY_READY",
            "cdp_port": 9222,
            "ingestion_only": True,
            "public_write_performed": False,
            "publication_authority": False,
        },
    }


def test_hybrid_pipeline_shadow_confirms_all_existing_owner_contracts():
    result = evaluate_hybrid_pipeline_shadow(enabled=True, **_pipeline_components())

    assert result["status"] == PIPELINE_CONFIRMED_SHADOW
    assert result["source_order"] == ["HTTP_OR_OFFICIAL_API", "BROWSEROS_RENDERED_RECOVERY_IF_ELIGIBLE"]
    assert result["x_ingestion_cdp_port"] == 9222
    assert result["x_ingestion_only"] is True
    assert result["scheduler_started"] is False
    assert result["durable_store_write_count"] == 0
    assert result["public_write_performed"] is False
    assert len(result["pipeline_identity_sha256"]) == 64


def test_hybrid_pipeline_shadow_is_disabled_without_inspecting_components():
    result = evaluate_hybrid_pipeline_shadow(enabled=False)

    assert result["status"] == PIPELINE_DISABLED
    assert result["evidence_sha256"]
    assert result["pipeline_identity_sha256"] is None


def test_hybrid_pipeline_shadow_classifies_missing_mismatch_and_unknown_write():
    missing = evaluate_hybrid_pipeline_shadow(enabled=True)
    mismatch_components = _pipeline_components()
    mismatch_components["destination_shadow"] = {"status": "MISMATCH"}
    mismatch = evaluate_hybrid_pipeline_shadow(enabled=True, **mismatch_components)
    unknown_components = _pipeline_components()
    unknown_components["destination_shadow"] = {"status": "UNKNOWN_WRITE"}
    unknown = evaluate_hybrid_pipeline_shadow(enabled=True, **unknown_components)

    assert missing["status"] == PIPELINE_MISSING
    assert mismatch["status"] == PIPELINE_MISMATCH
    assert unknown["status"] == PIPELINE_UNKNOWN_WRITE
    assert unknown["failure_detail"]


def test_hybrid_pipeline_shadow_rejects_human_required_and_side_effect_flags():
    human_components = _pipeline_components()
    human_components["identity_shadow"] = {"status": "HUMAN_REQUIRED"}
    human = evaluate_hybrid_pipeline_shadow(enabled=True, **human_components)
    side_effect_components = _pipeline_components()
    side_effect_components["destination_shadow"] = {
        "status": "CONFIRMED_SHADOW",
        "public_write_performed": True,
    }
    side_effect = evaluate_hybrid_pipeline_shadow(enabled=True, **side_effect_components)

    assert human["status"] == PIPELINE_HUMAN_REQUIRED
    assert side_effect["status"] == PIPELINE_FAIL_CLOSED


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
