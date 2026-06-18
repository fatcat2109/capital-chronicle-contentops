import importlib
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_import_has_no_side_effects():
    module = importlib.import_module("live_contentops.static_cockpit_surface_policy")
    assert module.TASK_LABEL == "TASK_CONTENTOPS_0174YI_YJ_YK_STATIC_COCKPIT_SURFACE_CONTRACT_V0"


def test_policy_packet_fixed_safety_and_statuses():
    from live_contentops import static_cockpit_surface_policy as policy

    packet = policy.build_policy_packet()
    assert packet["readiness_class"] == "NOT_READY_FOR_LIVE_DISPATCH"
    assert packet["live_dispatch_status"] == "BLOCKED"
    assert packet["manual_export_status"] == "REVIEW_ONLY_READY_FOR_OPERATOR"
    assert packet["platform_statuses"] == {
        "substack": "MANUAL_EXPORT_ONLY_NO_API",
        "x": "PREVIEW_ONLY_NO_API",
        "telegram": "PREVIEW_ONLY_FROZEN_NO_SEND",
    }
    assert packet["can_dispatch"] is False
    assert packet["public_postable"] is False
    assert packet["html_scripts_allowed"] is False
    assert packet["html_forms_allowed"] is False
    assert packet["external_assets_allowed"] is False


def test_policy_forbids_live_behavior_and_material():
    from live_contentops import static_cockpit_surface_policy as policy

    packet = policy.build_policy_packet()
    assert "live_dispatch" in packet["forbidden_actions"]
    assert "platform_api_call" in packet["forbidden_actions"]
    assert "provider_api_call" in packet["forbidden_actions"]
    assert "credential_hydration" in packet["forbidden_actions"]
    with pytest.raises(ValueError):
        policy.validate_no_forbidden_readiness_claims({"x": "this is live-ready"})
    with pytest.raises(ValueError):
        policy.validate_no_forbidden_material({"x": "<script>alert(1)</script>"})
    with pytest.raises(ValueError):
        policy.validate_no_forbidden_material({"x": "https://example.test"})


def test_policy_generation_deterministic_and_safe_path_guard():
    from live_contentops import static_cockpit_surface_policy as policy

    first = policy.write_artifacts(REPO_ROOT)
    second = policy.write_artifacts(REPO_ROOT)
    assert first == second
    assert first["static_cockpit_surface_policy_checksum"] == second["static_cockpit_surface_policy_checksum"]
    with pytest.raises(ValueError, match="unsafe_output_path_refused"):
        policy.write_artifacts(REPO_ROOT, REPO_ROOT / "docs" / "automation")
