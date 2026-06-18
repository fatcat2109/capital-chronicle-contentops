import importlib
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_import_has_no_side_effects():
    module = importlib.import_module("live_contentops.manual_export_review_policy")
    assert module.MANUAL_EXPORT_STATUS == "REVIEW_ONLY_READY_FOR_OPERATOR"


def test_fixed_policy_values():
    from live_contentops import manual_export_review_policy as p

    values = p.policy_values()
    assert values["readiness_class"] == "NOT_READY_FOR_LIVE_DISPATCH"
    assert values["local_governance_status"] == "PASS_DRY_RUN_CHAIN"
    assert values["live_dispatch_status"] == "BLOCKED"
    assert values["manual_export_status"] == "REVIEW_ONLY_READY_FOR_OPERATOR"
    assert values["platforms"] == ["substack", "x", "telegram"]


def test_operator_actions_manual_local_only():
    from live_contentops import manual_export_review_policy as p

    assert p.OPERATOR_ACTIONS == ["copy_markdown_for_substack", "inspect_x_thread_preview", "inspect_telegram_channel_update_preview", "record_manual_publish_later", "request_revision", "hold"]
    forbidden_terms = " ".join(p.OPERATOR_ACTIONS)
    for term in ["api", "dispatch", "hydrate", "schedule", "reply", "dm", "scrape"]:
        assert term not in forbidden_terms


def test_forbidden_actions_include_required_items():
    from live_contentops import manual_export_review_policy as p

    for action in ["live_dispatch", "credential_hydration", "platform_api_call", "autonomous_posting", "scheduling", "reply_or_dm", "scraping"]:
        assert action in p.FORBIDDEN_ACTIONS


def test_safety_flags_local_only_and_false():
    from live_contentops import manual_export_review_policy as p

    flags = p.safety_flags()
    assert flags["is_local_only"] is True
    for key, value in flags.items():
        if key != "is_local_only":
            assert value is False


def test_forbidden_readiness_claim_guard():
    from live_contentops import manual_export_review_policy as p

    for claim in ["production-ready", "live-ready", "dispatch-ready", "ready to send", "public-postable"]:
        with pytest.raises(ValueError, match="forbidden_readiness_claim"):
            p.validate_no_forbidden_readiness_claims({"bad": claim})


def test_forbidden_material_guard():
    from live_contentops import manual_export_review_policy as p

    for value in ["bot123:abcdefghijklmnopqrstuvwxyz", "chat_id", "raw_destination", "secret", ".env", "https://example.com/live"]:
        with pytest.raises(ValueError, match="forbidden_material"):
            p.validate_no_forbidden_material({"bad": value})


def test_policy_packet_deterministic_and_safe(tmp_path):
    from live_contentops import manual_export_review_policy as p

    first = p.write_artifacts(REPO_ROOT)
    second = p.write_artifacts(REPO_ROOT)
    assert first == second
    assert first["manual_export_review_policy_checksum"]
    p.validate_no_forbidden_readiness_claims(first)
    p.validate_no_forbidden_material(first)
    with pytest.raises(ValueError, match="unsafe_output_path_refused"):
        p.write_artifacts(REPO_ROOT, tmp_path)


def test_platform_surface_statuses():
    from live_contentops import manual_export_review_policy as p

    assert p.PLATFORM_SURFACE_STATUSES["substack"] == "manual_export_review_strongest_path_no_api"
    assert p.PLATFORM_SURFACE_STATUSES["x"] == "preview_only_no_api"
    assert p.PLATFORM_SURFACE_STATUSES["telegram"] == "operator_and_channel_preview_only_no_send"
