import importlib
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_import_has_no_side_effects():
    module = importlib.import_module("live_contentops.cockpit_read_model_policy")
    assert module.TASK_LABEL == "TASK_CONTENTOPS_0174YF_YG_YH_COCKPIT_READ_MODEL_CONTRACT_V0"


def test_policy_statuses_and_platform_statuses():
    from live_contentops import cockpit_read_model_policy as policy

    packet = policy.build_policy_packet()
    assert packet["readiness_class"] == "NOT_READY_FOR_LIVE_DISPATCH"
    assert packet["local_governance_status"] == "PASS_DRY_RUN_CHAIN"
    assert packet["live_dispatch_status"] == "BLOCKED"
    assert packet["manual_export_status"] == "REVIEW_ONLY_READY_FOR_OPERATOR"
    assert packet["platform_statuses"] == {
        "substack": "MANUAL_EXPORT_ONLY_NO_API",
        "x": "PREVIEW_ONLY_NO_API",
        "telegram": "PREVIEW_ONLY_FROZEN_NO_SEND",
    }


def test_allowed_actions_are_manual_local_only_and_forbidden_actions_present():
    from live_contentops import cockpit_read_model_policy as policy

    packet = policy.build_policy_packet()
    assert "copy_markdown_for_substack" in packet["allowed_actions"]
    assert "open_static_cockpit_surface_preview" in packet["allowed_actions"]
    for forbidden in [
        "live_dispatch",
        "credential_hydration",
        "platform_api_call",
        "autonomous_posting",
        "scheduling",
        "reply_or_dm",
        "scraping",
    ]:
        assert forbidden in packet["forbidden_actions"]
        assert forbidden not in packet["allowed_actions"]


def test_safety_flags_are_false_and_blocked():
    from live_contentops import cockpit_read_model_policy as policy

    flags = policy.safety_flags()
    assert flags["is_local_only"] is True
    for key, value in flags.items():
        if key != "is_local_only":
            assert value is False


def test_forbidden_readiness_claim_validator():
    from live_contentops import cockpit_read_model_policy as policy

    assert policy.validate_no_forbidden_readiness_claims({"status": "review-only local governance pass"}) is True
    with pytest.raises(ValueError, match="forbidden_readiness_claim"):
        policy.validate_no_forbidden_readiness_claims({"status": "production-ready"})


def test_forbidden_material_validator():
    from live_contentops import cockpit_read_model_policy as policy

    assert policy.validate_no_forbidden_material({"payload_hash": "a" * 64}) is True
    with pytest.raises(ValueError, match="forbidden_material"):
        policy.validate_no_forbidden_material({"token": "https://platform.example/live"})
    with pytest.raises(ValueError, match="forbidden_material"):
        policy.validate_no_forbidden_material({"provider_response": "raw provider_response body"})


def test_policy_generation_is_deterministic_and_path_protected():
    from live_contentops import cockpit_read_model_policy as policy

    first = policy.write_artifacts(REPO_ROOT)
    second = policy.write_artifacts(REPO_ROOT)
    assert first == second
    assert first["cockpit_read_model_policy_checksum"] == second["cockpit_read_model_policy_checksum"]
    with pytest.raises(ValueError, match="unsafe_output_path_refused"):
        policy.write_artifacts(REPO_ROOT, REPO_ROOT)
