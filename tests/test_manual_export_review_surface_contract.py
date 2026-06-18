import importlib
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def _result():
    from live_contentops import manual_export_review_surface_contract as c

    return c.write_artifacts(REPO_ROOT)


def test_import_has_no_side_effects():
    module = importlib.import_module("live_contentops.manual_export_review_surface_contract")
    assert module.NEXT_BATCH_PROMPT == "TASK_CONTENTOPS_0174YF_YG_YH_COCKPIT_READ_MODEL_CONTRACT_V0"


def test_surface_readiness_and_manual_status():
    result = _result()
    surface = result["surface"]
    assert surface["readiness_class"] == "NOT_READY_FOR_LIVE_DISPATCH"
    assert surface["manual_export_status"] == "REVIEW_ONLY_READY_FOR_OPERATOR"
    assert surface["live_dispatch_status"] == "BLOCKED"
    assert surface["can_dispatch"] is False
    assert surface["public_postable"] is False


def test_substack_manual_export_required_fields():
    result = _result()
    substack = [item for item in result["fixture_outputs"] if item["platform"] == "substack"]
    assert substack
    for item in substack:
        assert item["operator_action"] == "copy_markdown_for_substack"
        assert item["markdown_body"].startswith("# ")
        assert item["title"]
        assert "subtitle" in item
        assert item["seo_metadata"].get("robots") == "noindex_review_only"
        assert item["source_notes"]
        assert item["limitations"]
        assert "No financial advice" in item["no_signal_disclaimer"]
        assert item["manual_export"]["format"] == "markdown"
        assert item["manual_export"]["platform_api_called"] is False


def test_x_preview_only_surface():
    result = _result()
    x_items = [item for item in result["fixture_outputs"] if item["platform"] == "x"]
    assert x_items
    assert any(item["short_post_preview"] for item in x_items)
    assert any(item["thread_preview"] for item in x_items)
    for item in x_items:
        assert item["preview_only"] is True
        assert item["can_dispatch"] is False
        assert item["manual_export"] == {}
        assert item["surface_status"] == "preview_only_no_api"


def test_telegram_review_and_channel_distinct():
    result = _result()
    telegram = [item for item in result["fixture_outputs"] if item["platform"] == "telegram"]
    assert telegram
    operator = [item for item in telegram if item["payload_class"] == "telegram_operator_review_message"]
    channel = [item for item in telegram if item["payload_class"] == "telegram_channel_update"]
    assert operator
    assert channel
    assert all(item["operator_review_message_preview"] and not item["channel_update_preview"] for item in operator)
    assert all(item["channel_update_preview"] and not item["operator_review_message_preview"] for item in channel)
    assert all(item["telegram_review_and_channel_distinct"] is True for item in telegram)


def test_future_gates_operator_and_forbidden_actions():
    result = _result()
    surface = result["surface"]
    for gate in ["kill_switch_activation", "redacted_audit_packet", "manual_fallback_proof", "operator_supervision_window", "live_dispatch_separate_approval"]:
        assert gate in surface["required_future_gates"]
    assert "copy_markdown_for_substack" in surface["operator_actions"]
    assert "live_dispatch" in surface["forbidden_actions"]
    assert "credential_hydration" in surface["forbidden_actions"]
    assert "platform_api_call" in surface["forbidden_actions"]


def test_every_payload_safety_booleans_and_hash_binding():
    result = _result()
    outputs = result["fixture_outputs"]
    assert outputs
    for item in outputs:
        assert item["payload_hash"]
        assert item["payload_hash_short"] == item["payload_hash"][:12]
        assert item["review_only_payload"] is True
        assert item["public_postable"] is False
        assert item["human_review_required"] is True
        assert item["no_financial_advice"] is True
        assert item["no_signal_language"] is True
        assert item["can_dispatch"] is False
        assert item["live_ready_state_created"] is False
        assert item["is_local_only"] is True
        for key, value in item.items():
            if key.endswith("_api_called") or key in {"network_performed", "env_read", "dotenv_read", "credential_read", "credential_hydration_performed", "scheduler_enabled", "live_post_performed", "autonomous_replies_or_dms", "scraping_performed", "platform_dispatch_performed", "raw_request_persisted", "raw_response_persisted", "token_logged"}:
                assert value is False


def test_forbidden_claims_and_material_absent():
    from live_contentops import manual_export_review_policy as p

    result = _result()
    p.validate_no_forbidden_readiness_claims(result["surface"])
    p.validate_no_forbidden_material(result["surface"])
    p.validate_no_forbidden_readiness_claims(result["fixture_outputs"])
    p.validate_no_forbidden_material(result["fixture_outputs"])
    p.validate_no_forbidden_readiness_claims(result["next_packet"])
    p.validate_no_forbidden_material(result["next_packet"])


def test_deterministic_and_unsafe_output_refused(tmp_path):
    from live_contentops import manual_export_review_surface_contract as c

    first = c.write_artifacts(REPO_ROOT)
    second = c.write_artifacts(REPO_ROOT)
    assert first == second
    assert first["surface"]["manual_export_review_surface_checksum"]
    assert first["surface"]["manual_export_review_fixture_outputs_checksum"]
    assert first["next_packet"]["next_cockpit_read_model_contract_checksum"]
    with pytest.raises(ValueError, match="unsafe_output_path_refused"):
        c.write_artifacts(REPO_ROOT, tmp_path)


def test_next_contract_points_to_cockpit_read_model_only():
    result = _result()
    next_packet = result["next_packet"]
    assert next_packet["next_batch_prompt"] == "TASK_CONTENTOPS_0174YF_YG_YH_COCKPIT_READ_MODEL_CONTRACT_V0"
    assert next_packet["cockpit_must_be_read_model_only"] is True
    assert "live_dispatch" in next_packet["forbidden_outputs"]
    assert "platform_api_call" in next_packet["forbidden_outputs"]
    assert next_packet["readiness_class"] == "NOT_READY_FOR_LIVE_DISPATCH"
