import importlib
import pathlib

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_import_has_no_side_effects():
    module = importlib.import_module("live_contentops.primary_platform_variant_dry_run")
    assert module.NEXT_BATCH_PROMPT.endswith("APPROVAL_CHALLENGE_CANDIDATE_CONTRACT_V0")


def _generated():
    from live_contentops import primary_platform_variant_dry_run as p

    briefs = p.load_briefs(REPO_ROOT)
    variants, blocked = p.build_all_variants(briefs)
    packet = p.build_run_packet(briefs, variants, blocked)
    return variants, blocked, packet


def test_generates_substack_newsletter_manual_export_from_grounded_news_brief():
    variants, _, _ = _generated()
    substack = [v for v in variants if v["platform"] == "substack" and v["payload_class"] == "substack_newsletter_issue"]
    assert substack
    first = substack[0]
    assert first["title"]
    assert first["subtitle"]
    assert first["manual_export"]["format"] == "markdown"
    assert "# " in first["manual_export"]["markdown_body"]


def test_generates_x_short_and_thread_preview_from_x_safe_brief_only():
    variants, _, _ = _generated()
    x_variants = [v for v in variants if v["platform"] == "x"]
    assert {v["payload_class"] for v in x_variants} == {"x_short_post", "x_thread"}
    assert all("signal" in " ".join(v["platform_warnings"]) or v["no_signal_language"] for v in x_variants)
    assert all("price target" in v["body"].lower() or "market call" in v["body"].lower() or v["payload_class"] == "x_thread" for v in x_variants)


def test_generates_telegram_channel_update_and_operator_review_distinct():
    variants, _, _ = _generated()
    channel = [v for v in variants if v["payload_class"] == "telegram_channel_update"]
    review = [v for v in variants if v["payload_class"] == "telegram_operator_review_message"]
    assert channel and review
    assert channel[0]["body"] != review[0]["body"]
    assert channel[0]["platform_formatting_metadata"]["surface"] != review[0]["platform_formatting_metadata"]["surface"]


def test_blocked_direct_dispatch_approval_signal_and_future_artifact_no_variants():
    variants, blocked, packet = _generated()
    source_ids = {v["source_brief_id"] for v in variants}
    for group in ["direct_dispatch", "approval_candidate", "signal_advice", "future_artifact"]:
        assert blocked[group]
        assert not (source_ids & {b["brief_id"] for b in blocked[group]})
    assert packet["blocked_direct_dispatch_proof"]
    assert packet["blocked_approval_candidate_proof"]
    assert packet["blocked_signal_advice_proof"]
    assert packet["blocked_future_artifact_proof"]


def test_every_payload_preview_safety_flags():
    variants, _, _ = _generated()
    assert variants
    for payload in variants:
        assert payload["approval_required"] is True
        assert payload["dispatch_ready"] is False
        assert payload["public_postable"] is False
        assert payload["human_review_required"] is True
        assert payload["no_financial_advice"] is True
        assert payload["no_signal_language"] is True
        assert payload["network_performed"] is False
        assert payload["platform_api_called"] is False
        assert payload["provider_api_called"] is False


def test_substack_manual_export_has_required_metadata():
    variants, _, _ = _generated()
    substack = next(v for v in variants if v["payload_class"] == "substack_newsletter_issue")
    assert substack["source_notes"]
    assert substack["limitations"]
    assert substack["manual_export"]["no_signal_disclaimer"]
    assert substack["seo_metadata"]["robots"] == "noindex_review_only"


def test_generated_platforms_classes_limited_to_primary_scope():
    variants, _, packet = _generated()
    assert set(packet["platforms_generated"]) == {"substack", "telegram", "x"}
    assert set(packet["payload_classes_generated"]) == {v["payload_class"] for v in variants}
    assert "linkedin" not in packet["platforms_generated"]
    assert "threads" not in packet["platforms_generated"]
    assert "instagram" not in packet["platforms_generated"]
    assert "facebook_page" not in packet["platforms_generated"]


def test_payload_hash_determinism_proof():
    _, _, packet = _generated()
    proof = packet["payload_hash_determinism_proof"]
    assert proof == {
        "same_payload_same_hash": True,
        "body_change_changes_hash": True,
        "platform_change_changes_hash": True,
        "class_change_changes_hash": True,
    }


def test_no_live_network_env_provider_platform_behavior():
    _, _, packet = _generated()
    for key in ["network_performed", "env_read", "dotenv_read", "telegram_api_called", "x_api_called", "substack_api_called", "platform_api_called", "provider_api_called", "llm_provider_api_called", "live_post_performed", "approval_ledger_mutated", "dispatch_outbox_mutated"]:
        assert packet[key] is False


def test_deterministic_generation_and_unsafe_path_refused(tmp_path):
    from live_contentops import primary_platform_variant_dry_run as p

    first = p.write_artifacts(REPO_ROOT)
    second = p.write_artifacts(REPO_ROOT)
    assert first == second
    with pytest.raises(ValueError, match="unsafe_output_path_refused"):
        p.write_artifacts(REPO_ROOT, tmp_path)


def test_next_approval_challenge_candidate_contract():
    from live_contentops import primary_platform_variant_dry_run as p

    result = p.write_artifacts(REPO_ROOT)
    next_packet = result["next_packet"]
    assert next_packet["next_batch_prompt"] == p.NEXT_BATCH_PROMPT
    assert "approval" in next_packet["forbidden_outputs"]
    assert next_packet["network_performed"] is False
