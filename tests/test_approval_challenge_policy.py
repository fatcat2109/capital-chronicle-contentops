import importlib
import pathlib

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_import_has_no_side_effects():
    module = importlib.import_module("live_contentops.approval_challenge_policy")
    assert module.TASK_LABEL.endswith("APPROVAL_CHALLENGE_CANDIDATE_CONTRACT_V0")


def test_policy_packet_fields_and_safety():
    from live_contentops import approval_challenge_policy as p

    packet = p.build_policy_packet()
    assert packet["candidate_input_required_visibility_class"] == "review_only_payload_preview"
    assert packet["requires_payload_hash"] is True
    assert packet["blocks_dispatch_ready_true"] is True
    assert packet["blocks_public_postable_true"] is True
    assert packet["can_record_approval"] is False
    assert packet["can_dispatch"] is False
    assert packet["can_create_outbox"] is False
    for key in ["network_performed", "env_read", "telegram_api_called", "x_api_called", "substack_api_called", "platform_api_called", "provider_api_called", "llm_provider_api_called", "approval_ledger_mutated", "dispatch_outbox_mutated"]:
        assert packet[key] is False


def test_hash_short_and_allowed_phrases():
    from live_contentops import approval_challenge_policy as p

    payload_hash = "abcdef1234567890"
    assert p.hash_short(payload_hash) == "abcdef123456"
    phrases = p.allowed_response_phrases(payload_hash)
    assert phrases["approval_phrase_required"] == "APPROVE abcdef123456"
    assert phrases["rejection_phrase_required"] == "REJECT abcdef123456"
    assert phrases["edit_phrase_allowed"] == "EDIT abcdef123456: <instruction>"
    assert phrases["hold_phrase_allowed"] == "HOLD abcdef123456"


def _payload(**overrides):
    payload = {
        "source_brief_id": "brief_ok",
        "visibility_class": "review_only_payload_preview",
        "payload_hash": "abcdef1234567890",
        "human_review_required": True,
        "dispatch_ready": False,
        "public_postable": False,
        "approval_ledger_mutated": False,
        "dispatch_outbox_mutated": False,
        "destination_binding_id": "symbolic_fixture_only",
        "credential_handle_id": "symbolic_fixture_only",
    }
    payload.update(overrides)
    return payload


def test_policy_accepts_review_only_hash_human_review_payload():
    from live_contentops import approval_challenge_policy as p

    assert p.can_create_candidate(_payload()) is True


def test_policy_rejects_blocked_proof_dispatch_public_and_missing_hash():
    from live_contentops import approval_challenge_policy as p

    assert p.can_create_candidate(_payload(source_brief_id="brief_blocked"), {"brief_blocked"}) is False
    assert p.can_create_candidate(_payload(dispatch_ready=True)) is False
    assert p.can_create_candidate(_payload(public_postable=True)) is False
    assert p.can_create_candidate(_payload(payload_hash="")) is False
    assert p.can_create_candidate(_payload(human_review_required=False)) is False
    assert p.can_create_candidate(_payload(visibility_class="public_post")) is False


def test_policy_rejects_mutated_ledger_or_outbox():
    from live_contentops import approval_challenge_policy as p

    assert p.can_create_candidate(_payload(approval_ledger_mutated=True)) is False
    assert p.can_create_candidate(_payload(dispatch_outbox_mutated=True)) is False


def test_policy_rejects_forbidden_material():
    from live_contentops import approval_challenge_policy as p

    with pytest.raises(ValueError, match="forbidden_candidate_material"):
        p.can_create_candidate(_payload(credential_handle_id="raw_token"))


def test_deterministic_generation_and_unsafe_path_refused(tmp_path):
    from live_contentops import approval_challenge_policy as p

    first = p.write_artifacts(REPO_ROOT)
    second = p.write_artifacts(REPO_ROOT)
    assert first == second
    with pytest.raises(ValueError, match="unsafe_output_path_refused"):
        p.write_artifacts(REPO_ROOT, tmp_path)
