import importlib
import pathlib

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_import_has_no_side_effects():
    module = importlib.import_module("live_contentops.approval_challenge_candidate_contract")
    assert module.NEXT_BATCH_PROMPT.endswith("APPROVAL_LEDGER_CONTRACT_V0")


def _result():
    from live_contentops import approval_challenge_candidate_contract as c

    return c.write_artifacts(REPO_ROOT)


def test_creates_substack_newsletter_and_longform_candidates():
    candidates = _result()["candidates"]
    classes = {c["payload_class"] for c in candidates if c["platform"] == "substack"}
    assert "substack_newsletter_issue" in classes
    assert "substack_longform_post" in classes
    for item in [c for c in candidates if c["platform"] == "substack"]:
        assert item["manual_export"]
        assert item["manual_export"]["no_signal_disclaimer"]
        assert item["limitations"]
        assert item["source_notes"]


def test_creates_x_short_and_thread_candidates():
    candidates = _result()["candidates"]
    classes = {c["payload_class"] for c in candidates if c["platform"] == "x"}
    assert classes == {"x_short_post", "x_thread"}
    for item in [c for c in candidates if c["platform"] == "x"]:
        warnings = " ".join(item["platform_warnings"]).lower()
        assert "no_signal" in warnings or item["no_signal_language"] is True


def test_creates_telegram_candidates_with_distinct_roles():
    candidates = _result()["candidates"]
    channel = [c for c in candidates if c["payload_class"] == "telegram_channel_update"]
    review = [c for c in candidates if c["payload_class"] == "telegram_operator_review_message"]
    assert channel and review
    assert channel[0]["challenge_channel"] == "local_ui_fixture"
    assert review[0]["challenge_channel"] == "telegram_future"
    assert channel[0]["destination_summary_redacted"] != review[0]["destination_summary_redacted"]


def test_blocked_proofs_create_no_candidates():
    result = _result()
    candidates = result["candidates"]
    packet = result["contract_packet"]
    source_ids = {c["source_brief_id"] for c in candidates}
    for key in ["blocked_direct_dispatch_proof", "blocked_approval_candidate_proof", "blocked_signal_advice_proof", "blocked_future_artifact_proof"]:
        assert packet[key]
        assert not (source_ids & set(packet[key]))


def test_hash_short_and_challenge_text_phrases():
    candidates = _result()["candidates"]
    for item in candidates:
        assert item["payload_hash_short"] == item["payload_hash"][:12]
        text = item["challenge_text"]
        assert item["payload_hash_short"] in text
        assert item["approval_phrase_required"] in text
        assert item["rejection_phrase_required"] in text
        assert item["edit_phrase_allowed"] in text
        assert item["hold_phrase_allowed"] in text
        assert "Platform:" in text
        assert "Payload class:" in text


def test_candidate_safety_flags_and_authority_blocks():
    candidates = _result()["candidates"]
    assert candidates
    for item in candidates:
        assert item["can_record_approval"] is False
        assert item["can_dispatch"] is False
        assert item["can_create_outbox"] is False
        assert item["public_postable"] is False
        assert item["human_review_required"] is True
        assert item["approval_ledger_mutated"] is False
        assert item["dispatch_outbox_mutated"] is False
        assert item["network_performed"] is False
        assert item["platform_api_called"] is False
        assert item["provider_api_called"] is False


def test_no_raw_credential_token_chat_id_env_secret_live_url_material():
    candidates = _result()["candidates"]
    text = str(candidates).lower()
    forbidden = ["raw_credential", "raw_token", "raw_chat_id", "raw_destination", "env_var", "secret_path", "live_url", "chat_id", "token", "secret"]
    for item in forbidden:
        assert item not in text


def test_contract_packet_safety_and_counts():
    result = _result()
    packet = result["contract_packet"]
    assert packet["generated_candidate_count"] == len(result["candidates"])
    assert set(packet["supported_platforms"]) == {"substack", "telegram", "x"}
    assert packet["all_can_record_approval_false"] is True
    assert packet["all_can_dispatch_false"] is True
    assert packet["all_can_create_outbox_false"] is True
    for key in ["network_performed", "env_read", "telegram_api_called", "x_api_called", "substack_api_called", "platform_api_called", "provider_api_called", "llm_provider_api_called", "live_post_performed", "approval_ledger_mutated", "dispatch_outbox_mutated"]:
        assert packet[key] is False


def test_next_approval_ledger_contract():
    result = _result()
    next_packet = result["next_packet"]
    assert next_packet["next_batch_prompt"].endswith("APPROVAL_LEDGER_CONTRACT_V0")
    assert "autonomous_approval" in next_packet["forbidden_outputs"]
    assert next_packet["approval_ledger_mutated"] is False
    assert next_packet["dispatch_outbox_mutated"] is False


def test_deterministic_generation_and_unsafe_path_refused(tmp_path):
    from live_contentops import approval_challenge_candidate_contract as c

    first = c.write_artifacts(REPO_ROOT)
    second = c.write_artifacts(REPO_ROOT)
    assert first == second
    with pytest.raises(ValueError, match="unsafe_output_path_refused"):
        c.write_artifacts(REPO_ROOT, tmp_path)
