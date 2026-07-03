from live_contentops.jim_content_intent_to_variant_preview_bundle_v6 import (
    build_jim_content_intent_to_variant_preview_bundle,
)


def test_variant_preview_bundle_is_review_only_and_local():
    packet = build_jim_content_intent_to_variant_preview_bundle()
    flags = packet["safety_flags"]

    assert packet["bundle_status"] == "JIM_REVIEW_REQUIRED_PREVIEW_ONLY"
    assert packet["operator_id"] == "jim"
    assert flags["local_only"] is True
    assert flags["fixture_only"] is True
    assert flags["jim_final_review_required"] is True
    assert flags["final_public_copy_created"] is False
    assert flags["public_postable"] is False
    assert flags["publish_ready"] is False
    assert flags["dispatch_ready"] is False


def test_variant_preview_bundle_creates_four_preview_placeholders_per_intent():
    packet = build_jim_content_intent_to_variant_preview_bundle()

    assert packet["intent_count"] == 3
    assert packet["platform_targets"] == ["Substack", "X", "LinkedIn", "Telegram"]
    assert packet["platform_preview_count"] == 12
    assert len(packet["platform_previews"]) == 12
    assert {p["platform"] for p in packet["platform_previews"]} == {"Substack", "X", "LinkedIn", "Telegram"}


def test_variant_preview_bundle_blocks_missing_source_and_artifact_inputs():
    packet = build_jim_content_intent_to_variant_preview_bundle()
    intents = {i["source_idea_id"]: i for i in packet["content_intents"]}

    assert intents["JDR-PA-001"]["status"] == "READY_FOR_JIM_REVIEW"
    assert intents["JDR-GN-001"]["status"] == "BLOCKED"
    assert intents["JDR-CA-001"]["status"] == "BLOCKED"
    assert "official-source citation must be confirmed by Jim" in intents["JDR-GN-001"]["blockers"]
    assert "approved artifact evidence required" in intents["JDR-CA-001"]["blockers"]


def test_variant_preview_bundle_forbids_provider_network_browser_and_dispatch_paths():
    packet = build_jim_content_intent_to_variant_preview_bundle()
    flags = packet["safety_flags"]

    assert flags["llm_provider_called"] is False
    assert flags["provider_api_called"] is False
    assert flags["network_called"] is False
    assert flags["browser_or_cdp_used"] is False
    assert flags["credential_or_env_read"] is False
    assert flags["platform_api_called"] is False
    assert flags["platform_dispatch_performed"] is False
    assert flags["scheduler_enabled"] is False
    assert flags["public_url_verified"] is False
    assert packet["forbidden_actions"] == [
        "No LLM/provider generation",
        "No final public copy",
        "No platform API",
        "No live dispatch",
        "No scheduler",
        "No public URL verification",
    ]


def test_variant_preview_text_has_no_signal_or_publish_claims():
    packet = build_jim_content_intent_to_variant_preview_bundle()
    signal_words = {"buy", "sell", "hold", "long", "short"}
    forbidden_phrases = ("price target", "publish-ready", "dispatch-ready")

    for preview in packet["platform_previews"]:
        text = preview["preview_text_excerpt"].lower()
        tokens = {"".join(ch for ch in word if ch.isalnum()) for word in text.split()}
        assert signal_words.isdisjoint(tokens)
        assert not any(term in text for term in forbidden_phrases)
        assert preview["manual_export_ready"] is False
        assert preview["dispatch_ready"] is False
        assert preview["public_postable"] is False


def test_variant_preview_bundle_hash_is_stable():
    packet_a = build_jim_content_intent_to_variant_preview_bundle()
    packet_b = build_jim_content_intent_to_variant_preview_bundle()

    assert packet_a["packet_hash"] == packet_b["packet_hash"]
    assert packet_a["packet_hash_algorithm"] == "sha256"
