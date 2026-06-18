import importlib
import pathlib

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_import_has_no_side_effects():
    module = importlib.import_module("live_contentops.platform_payload_preview_contract")
    assert module.TASK_LABEL.endswith("PRIMARY_PLATFORM_VARIANTS_DRY_RUN_V0")


def test_contract_packet_shape_and_safety():
    from live_contentops import platform_payload_preview_contract as c

    packet = c.build_contract_packet()
    assert packet["supported_platforms"] == ["x", "telegram", "substack"]
    assert "x_short_post" in packet["supported_payload_classes"]
    assert "telegram_operator_review_message" in packet["supported_payload_classes"]
    assert "substack_newsletter_issue" in packet["supported_payload_classes"]
    for key in ["network_performed", "env_read", "telegram_api_called", "x_api_called", "substack_api_called", "platform_api_called", "provider_api_called", "llm_provider_api_called"]:
        assert packet[key] is False


def _payload(platform="x", payload_class="x_short_post", body="body"):
    return {
        "payload_id": "p1",
        "source_brief_id": "brief1",
        "source_intent_id": "intent1",
        "platform": platform,
        "payload_class": payload_class,
        "destination_binding_id": "symbolic_fixture_only",
        "credential_handle_id": "symbolic_fixture_only",
        "body": body,
        "title": "",
        "subtitle": "",
        "thread_parts": [],
        "manual_export": {},
        "visibility_class": "review_only_payload_preview",
        "platform_formatting_metadata": {"surface": "test"},
    }


def test_payload_hash_is_deterministic_and_sensitive():
    from live_contentops import platform_payload_preview_contract as c

    payload = _payload()
    h1 = c.compute_payload_hash(payload)
    assert c.compute_payload_hash(payload) == h1
    assert c.compute_payload_hash(_payload(body="changed")) != h1
    assert c.compute_payload_hash(_payload(platform="telegram")) != h1
    assert c.compute_payload_hash(_payload(payload_class="x_thread")) != h1


def test_hash_input_contains_symbolic_binding_not_raw_secret_material():
    from live_contentops import platform_payload_preview_contract as c

    payload = _payload()
    material = c.hash_input_for_payload(payload)
    assert material["destination_binding_id"] == "symbolic_fixture_only"
    assert material["credential_handle_id"] == "symbolic_fixture_only"
    serialized = str(material).lower()
    assert "raw" not in serialized
    assert "secret" not in serialized
    assert "token" not in serialized
    assert "chat_id" not in serialized


def test_forbidden_hash_material_refused():
    from live_contentops import platform_payload_preview_contract as c

    payload = _payload(body="contains token")
    with pytest.raises(ValueError, match="forbidden_hash_input_material"):
        c.compute_payload_hash(payload)


def test_finalize_payload_safety_invariants():
    from live_contentops import platform_payload_preview_contract as c

    payload = c.finalize_payload(_payload())
    assert payload["approval_required"] is True
    assert payload["dispatch_ready"] is False
    assert payload["public_postable"] is False
    assert payload["human_review_required"] is True
    assert payload["no_financial_advice"] is True
    assert payload["no_signal_language"] is True
    assert payload["payload_hash_algorithm"] == "sha256"
    assert len(payload["payload_hash"]) == 64


def test_deterministic_generation_and_unsafe_path_refused(tmp_path):
    from live_contentops import platform_payload_preview_contract as c

    first = c.write_artifacts(REPO_ROOT)
    second = c.write_artifacts(REPO_ROOT)
    assert first == second
    with pytest.raises(ValueError, match="unsafe_output_path_refused"):
        c.write_artifacts(REPO_ROOT, tmp_path)
