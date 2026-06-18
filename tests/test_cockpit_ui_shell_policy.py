import importlib
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_import_has_no_side_effects():
    module = importlib.import_module("live_contentops.cockpit_ui_shell_policy")
    assert module.TASK_LABEL == "TASK_CONTENTOPS_0174YL_YM_YN_COCKPIT_UI_SHELL_CONTRACT_V0"


def test_policy_packet_regions_and_safety():
    from live_contentops import cockpit_ui_shell_policy as policy

    packet = policy.build_policy_packet()
    assert packet["readiness_class"] == "NOT_READY_FOR_LIVE_DISPATCH"
    assert packet["live_dispatch_status"] == "BLOCKED"
    assert packet["can_dispatch"] is False
    assert packet["public_postable"] is False
    assert packet["runtime_network_allowed"] is False
    assert packet["external_assets_allowed"] is False
    assert packet["iframe_allowed"] is False
    assert packet["tracking_allowed"] is False
    assert packet["shell_regions"] == [
        "CommandHero",
        "SignalLockStrip",
        "OperationalTruthRail",
        "BlockerStack",
        "ContentLane",
        "EvidenceCard",
        "AuditTable",
        "NextActionPanel",
    ]
    assert "EvidenceCard" in packet["semantic_components"]
    assert "payload_hash_short" in packet["semantic_components"]["EvidenceCard"]


def test_policy_allows_review_language_and_forbids_readiness_claims():
    from live_contentops import cockpit_ui_shell_policy as policy

    assert policy.validate_no_forbidden_readiness_claims({"x": "review-only local-only dry-run preview-only manual export"}) is True
    for text in ["production-ready", "live-ready", "dispatch-ready", "ready to send", "public-postable", "approved for posting"]:
        with pytest.raises(ValueError):
            policy.validate_no_forbidden_readiness_claims({"x": text})


def test_policy_forbids_live_material_and_actions():
    from live_contentops import cockpit_ui_shell_policy as policy

    packet = policy.build_policy_packet()
    assert "live_dispatch" in packet["forbidden_actions"]
    assert "approve_for_posting" in packet["forbidden_actions"]
    assert "credential_hydration" in packet["forbidden_actions"]
    assert "platform_api_call" in packet["forbidden_actions"]
    for material in ["bot123:abcdefghijklmnopqrstuvwxyz", "chat_id", "raw_destination", "https://example.test", "<iframe src=x>", "<form>", "cdn.example"]:
        with pytest.raises(ValueError):
            policy.validate_no_forbidden_material({"x": material})


def test_policy_generation_deterministic_and_path_guard():
    from live_contentops import cockpit_ui_shell_policy as policy

    first = policy.write_artifacts(REPO_ROOT)
    second = policy.write_artifacts(REPO_ROOT)
    assert first == second
    assert len(first["cockpit_ui_shell_policy_checksum"]) == 64
    with pytest.raises(ValueError, match="unsafe_output_path_refused"):
        policy.write_artifacts(REPO_ROOT, REPO_ROOT / "docs" / "automation")
