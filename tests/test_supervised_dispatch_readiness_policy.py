import importlib
import pathlib

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_import_has_no_side_effects():
    module = importlib.import_module("live_contentops.supervised_dispatch_readiness_policy")
    assert module.READINESS_CLASS == "NOT_READY_FOR_LIVE_DISPATCH"


def test_fixed_policy_statuses():
    from live_contentops import supervised_dispatch_readiness_policy as p

    values = p.readiness_values()
    assert values["readiness_class"] == "NOT_READY_FOR_LIVE_DISPATCH"
    assert values["local_governance_status"] == "PASS_DRY_RUN_CHAIN"
    assert values["live_dispatch_status"] == "BLOCKED"
    assert values["supported_primary_platforms"] == ["x", "telegram", "substack"]


def test_platform_readiness_values():
    from live_contentops import supervised_dispatch_readiness_policy as p

    assert p.PLATFORM_READINESS["telegram"] == "DISPATCH_PROVEN_FROZEN_NO_SEND"
    assert p.PLATFORM_READINESS["x"] == "DRY_RUN_ONLY_NO_API"
    assert p.PLATFORM_READINESS["substack"] == "MANUAL_EXPORT_ONLY_NO_API"


def test_live_blockers_include_all_required_items():
    from live_contentops import supervised_dispatch_readiness_policy as p

    required = [
        "kill switch activation missing",
        "redacted audit packet for real platform response missing",
        "manual fallback proof missing",
        "operator supervision window missing",
        "live dispatch separate approval missing",
        "credential hydration forbidden in current chain",
        "platform API calls forbidden in current chain",
        "provider response not called",
        "request budget used is 0",
        "final URL not verified",
    ]
    for item in required:
        assert item in p.LIVE_BLOCKERS


def test_required_future_gates():
    from live_contentops import supervised_dispatch_readiness_policy as p

    assert p.REQUIRED_FUTURE_GATES == ["kill_switch_activation", "redacted_audit_packet", "manual_fallback_proof", "operator_supervision_window", "live_dispatch_separate_approval"]


def test_forbidden_capabilities_include_autonomous_behavior():
    from live_contentops import supervised_dispatch_readiness_policy as p

    for item in ["autonomous posting", "scheduling", "autonomous replies", "direct messages", "scraping", "trading or signal behavior"]:
        assert item in p.FORBIDDEN_CAPABILITIES


def test_forbidden_readiness_claim_guard():
    from live_contentops import supervised_dispatch_readiness_policy as p

    for claim in ["production-ready", "live-ready", "dispatch-ready", "public-postable", "ready to send"]:
        with pytest.raises(ValueError, match="forbidden_readiness_claim"):
            p.validate_no_forbidden_readiness_claims({"bad": claim})


def test_policy_packet_has_no_forbidden_ready_claims():
    from live_contentops import supervised_dispatch_readiness_policy as p

    packet = p.build_policy_packet()
    p.validate_no_forbidden_readiness_claims(packet)
    assert packet["readiness_class"] == "NOT_READY_FOR_LIVE_DISPATCH"
    assert packet["summary_must_not_create_live_readiness"] is True


def test_safety_flags_false_and_local_only():
    from live_contentops import supervised_dispatch_readiness_policy as p

    flags = p.safety_flags()
    assert flags["is_local_only"] is True
    for key, value in flags.items():
        if key != "is_local_only":
            assert value is False


def test_deterministic_generation_and_unsafe_path_refused(tmp_path):
    from live_contentops import supervised_dispatch_readiness_policy as p

    first = p.write_artifacts(REPO_ROOT)
    second = p.write_artifacts(REPO_ROOT)
    assert first == second
    with pytest.raises(ValueError, match="unsafe_output_path_refused"):
        p.write_artifacts(REPO_ROOT, tmp_path)
