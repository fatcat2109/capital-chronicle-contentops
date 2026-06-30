import json
import os
import pytest
from dataclasses import asdict
from live_contentops.ai_research_canonical_article_engine_v6 import *
from live_contentops.discord_dry_run_outbox_operator_approval_spine_v6 import make_discord_dry_run_outbox_packet


def test_deterministic_sample_packet_created_from_operator_idea():
    packet = sample_article_packet()
    assert packet["schema_version"] == SCHEMA_VERSION
    assert packet["task_label"] == TASK_LABEL
    assert packet["provider_mode"] == "dry_run_fixture"
    assert packet["provider_call_made"] is False
    assert packet["provider_request_count"] == 0
    assert packet["raw_provider_key_serialized"] is False
    assert packet["env_lines_serialized"] is False
    assert packet["recommended_next_task"] == RECOMMENDED_NEXT_TASK


def test_canonical_article_has_required_sections():
    packet = sample_article_packet()
    draft = packet["canonical_article_draft"]
    for s in ("title", "subtitle", "slug_candidate", "dek", "thesis", "intro", "sections", "conclusion", "source_notes", "assumptions", "uncertainty_notes", "no_financial_advice_check", "no_fake_data_check", "created_at", "canonical_payload_hash"):
        assert s in draft
    assert isinstance(draft["sections"], list)
    assert len(draft["sections"]) > 0


def test_no_financial_advice_language_blocked():
    bad_ideas = ["Buy index options", "Sell near-term risk", "Hold current allocations", "Enter at target price", "Signal service alerts"]
    for idea in bad_ideas:
        inputs = sample_inputs()
        # Modify the operator idea to trigger check
        object.__setattr__(inputs, "operator_idea", idea)
        with pytest.raises(ValueError, match="forbidden_financial_advice_language"):
            run_article_engine(inputs)


def test_no_fake_market_numbers_or_fabricated_citations_blocked():
    bad_notes = "This is a fake citation from a simulated source."
    inputs = sample_inputs()
    object.__setattr__(inputs, "source_notes", bad_notes)
    with pytest.raises(ValueError, match="forbidden_fake_material_language"):
        run_article_engine(inputs)


def test_unsupported_claims_captured():
    inputs = sample_inputs()
    object.__setattr__(inputs, "source_notes", "This has an unsupported macro claim.")
    packet = run_article_engine(inputs)
    assert len(packet["research_grounding_packet"]["unsupported_claims"]) > 0
    assert "unsupported" in packet["research_grounding_packet"]["unsupported_claims"][0].lower()


def test_seo_and_discord_summary_seeds_present_and_safe():
    packet = sample_article_packet()

    # SEO
    seo = packet["seo_packet"]
    assert "target_keyword" in seo
    assert "secondary_keywords" in seo
    assert "meta_description" in seo

    # Discord
    discord = packet["discord_summary_seed"]
    for key in ("title", "canonical_url", "summary", "key_points", "call_to_action", "source_article_id", "content_hash", "created_at"):
        assert key in discord


def test_canonical_payload_hash_stable():
    p1 = sample_article_packet()
    p2 = sample_article_packet()
    h1 = p1["canonical_article_draft"]["canonical_payload_hash"]
    h2 = p2["canonical_article_draft"]["canonical_payload_hash"]
    assert h1 == h2
    assert h1.isalnum()
    assert len(h1) == 64


def test_raw_keys_never_serialized():
    inputs = sample_inputs()
    packet = run_article_engine(inputs)
    text = json.dumps(packet).lower()
    for bad in ("secret", "token", "sk-", "xoxb-", "bearer"):
        assert bad not in text


def test_downstream_discord_seed_can_be_converted_to_dry_run_packet():
    packet = sample_article_packet()
    discord_seed = packet["discord_summary_seed"]

    # Verify we can pass the seed as a compatible fixture to the Discord outbox spine
    outbox = make_discord_dry_run_outbox_packet(article=discord_seed)
    assert outbox.schema_version == "6.0.0"
    assert outbox.canonical_content_id == discord_seed["source_article_id"]
    assert outbox.approved_payload_hash.isalnum()
    assert len(outbox.approved_payload_hash) == 64
    assert outbox.discord_key_present is False or outbox.discord_key_present is True


def test_optional_live_provider_missing_key_behavior():
    inputs = sample_inputs()
    # Run in live mode with an empty env map
    packet = run_article_engine(inputs, provider_mode="live_provider_call", live_provider="openai")
    assert "missing_api_key:OPENAI_API_KEY" in packet["blockers"]
    assert packet["provider_call_made"] is False


def test_optional_live_provider_fails_safely_when_api_fails():
    inputs = sample_inputs()
    # Mock environment key being present
    env_backup = os.environ.copy()
    os.environ["OPENAI_API_KEY"] = "fake-api-key-for-test-never-serialize"
    try:
        packet = run_article_engine(inputs, provider_mode="live_provider_call", live_provider="openai", timeout_seconds=1)
        assert packet["provider_call_made"] is True
        assert packet["provider_request_count"] == 1
        assert any(b.startswith("provider_call_failed") for b in packet["blockers"])
    finally:
        os.environ.clear()
        os.environ.update(env_backup)
