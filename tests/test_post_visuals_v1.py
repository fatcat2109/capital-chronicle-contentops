"""Local synthetic contracts. These fixtures are neither posts nor MAX reviews."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

import pytest

from live_contentops.post_visuals_v1 import (
    POLICY, DESTINATIONS, build_post_data_card, complete_post_visuals,
    validate_post_data_card, require_publication_image,
)
from live_contentops.native_desktop_editorial_v1 import validate_release_media, final_visual_binding
from live_contentops.v1_simple_gemini_newsroom_v1 import _native_preview_bundle
from live_contentops.publication_coordinator_v1 import CanonicalDestinationTransportRuntimeV1


def packet():
    text = "The agency reported output of 120 units in 2026, compared with 100 units in 2025. The release leaves the policy timetable open."
    doc = {"document_id": "controlled-source", "source_id": "SOURCE_1", "publisher": "Controlled agency",
        "url": "https://example.org/release", "canonical_content_text": text,
        "underlying_reuse_classification": "governed_government_public_domain", "rights_evidence_sha256": "a" * 64,
        "source_reuse_constraints": {"scope": "ATTRIBUTED_REPORTED_FACTS_ONLY_INDEPENDENT_PUBLIC_PARAPHRASE",
            "attribution_required": True, "policy_capture_sha256": "b" * 64, "source_capture_sha256": "c" * 64}}
    facts = ["The agency reported output of 120 units in 2026, compared with 100 units in 2025.",
        "The release leaves the policy timetable open."]
    article = {"title": "A dated policy announcement", "dek": facts[0],
        "substack_body_markdown": "## What was announced\n\n" + "\n\n".join(facts),
        "social_hook": "Implementation details determine what changes.",
        "social_mechanism_summary": "The announcement sets a direction; implementation details remain open.",
        "social_policy_summary": "The timetable and mechanism still need an exact announced instrument.",
        "social_cross_asset_summary": "No causal market reaction is established by the announcement alone.",
        "reader_first_version": "DATA_JOURNALISM_V1", "resolved_article_mode": "BREAKING_BRIEF",
        "public_source_bindings": [{"source_id": "SOURCE_1", "publisher": doc["publisher"], "url": doc["url"]}],
        "visual_editorial_decision": {"reader_first_version": "DATA_JOURNALISM_V1", "story_kind": "POLICY",
            "editorial_thesis": "Controlled fixture only", "charts": [], "contextual_photo_ids": [],
            "exception_reason": "A narrow policy notice; no useful quantitative comparison beyond the key facts.",
            "channel_media": {d: [] for d in DESTINATIONS}}}
    claims = [{"claim_id": f"fact-{i}", "claim_text": text, "source_id": "SOURCE_1", "support_excerpt": text}
        for i, text in enumerate(facts)]
    return article, claims, [doc]


def test_card_projects_exact_post_facts_and_is_replay_stable(tmp_path):
    article, claims, docs = packet()
    first = build_post_data_card(article, claims, docs, output_dir=tmp_path)
    second = build_post_data_card(article, claims, docs, output_dir=tmp_path)
    assert first == second
    assert [f["text"] for f in first["data_card_packet"]["facts"]] == [c["claim_text"] for c in claims]
    assert first["width"] == 1080 and first["height"] >= 1080
    assert first["source_lineage"][0]["document_id"] == docs[0]["document_id"]
    assert first["publication_authority"] is False
    validate_post_data_card(first, article, docs)


@pytest.mark.parametrize("change", ["number", "post", "source", "rights", "pixels", "packet"])
def test_changed_facts_rights_or_bytes_fail(tmp_path, change):
    article, claims, docs = packet()
    card = build_post_data_card(article, claims, docs, output_dir=tmp_path)
    if change == "number":
        card["data_card_packet"]["facts"][0]["text"] = claims[0]["claim_text"].replace("120", "121")
    elif change == "post":
        article["dek"] = "Changed"
        article["substack_body_markdown"] = "Changed"
    elif change == "source":
        docs[0]["canonical_content_text"] += " Changed source."
    elif change == "rights":
        docs[0]["rights_evidence_sha256"] = "d" * 64
    elif change == "pixels":
        Path(card["path"]).write_bytes(b"changed")
    else:
        card["data_card_packet"]["facts"][0]["publisher"] = "Wrong agency"
    with pytest.raises(ValueError, match="DATA_CARD"):
        validate_post_data_card(card, article, docs)


@pytest.mark.parametrize("publisher", ["ISM", "S&P Global PMI", "Conference Board", "UMich", "ADP"])
def test_private_surveys_never_become_cards_or_charts(tmp_path, publisher):
    article, claims, docs = packet()
    docs[0]["publisher"] = publisher
    with pytest.raises(ValueError, match="NO_ADMITTED_PUBLIC_VISUAL_FACTS"):
        build_post_data_card(article, claims, docs, output_dir=tmp_path)
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import _editorial_data_values, _typed_chart_values
    with pytest.raises(ValueError, match="PRIVATE_SURVEY_HEADLINE_ONLY"):
        _typed_chart_values(docs[0], [], "%")
    with pytest.raises(ValueError, match="PRIVATE_SURVEY_HEADLINE_ONLY"):
        _editorial_data_values({"series": [{"points": [{"inputs": [{"document_id": docs[0]["document_id"]}]}]}]}, docs)


def test_unknown_rights_excluded_and_no_number_is_inferred(tmp_path):
    article, claims, docs = packet()
    docs[0].pop("underlying_reuse_classification")
    docs[0].pop("source_reuse_constraints")
    with pytest.raises(ValueError, match="NO_ADMITTED_PUBLIC_VISUAL_FACTS"):
        build_post_data_card(article, claims, docs, output_dir=tmp_path)
    article, claims, docs = packet()
    claims[0]["claim_text"] += " Growth was 20%."
    article["substack_body_markdown"] += " Growth was 20%."
    with pytest.raises(ValueError, match="FACT_OR_NUMBER"):
        build_post_data_card(article, claims, docs, output_dir=tmp_path)


def test_no_photo_card_compiles_eight_image_packages_and_enters_final_review(tmp_path):
    article, claims, docs = packet()
    article, assets = complete_post_visuals(article, claims, docs, [], output_dir=tmp_path)
    assert article["post_visual_policy"] == POLICY
    counts = validate_release_media({"article": article, "media_assets": assets, "evidence": docs})
    assert counts["photo_count"] == 0 and counts["data_card_count"] == 1
    bundle, _ = _native_preview_bundle(article=article, article_mode="BREAKING_BRIEF", article_identity="c" * 64,
        media_assets=assets, media_asset_ids=[a["asset_id"] for a in assets])
    assert len(bundle["packages"]) == 8
    for payload in bundle["packages"].values():
        assert payload["media_asset_ids"] == [assets[0]["asset_id"]]
        assert payload.get("delivery_state") != "SKIPPED_PHOTOLESS_NEWS_POLICY"
    result = {"article": article, "article_identity": "c" * 64, "media_assets": assets,
        "previews": [{"destination": d, "payload": p} for d, p in bundle["packages"].items()],
        "simple_result": {"publication_lifecycle_plan": {"plan_hash": "controlled"}}}
    binding = final_visual_binding(result, renders=None)
    assert len(binding["variants"]) == 9
    assert binding["required_viewports"] == ["desktop", "mobile"]
    with pytest.raises(ValueError, match="COVERAGE"):
        final_visual_binding(result, renders=[])
    article["post_visual_destination_media"]["instagram_business"] = []
    with pytest.raises(ValueError, match="EVERY_DESTINATION_IMAGE"):
        validate_release_media({"article": article, "media_assets": assets, "evidence": docs})


def test_analysis_retains_two_to_five_chart_requirement(tmp_path):
    article, claims, docs = packet()
    article["visual_editorial_decision"]["story_kind"] = "ANALYSIS"
    with pytest.raises(ValueError, match="EVERY_POST_IMAGE"):
        complete_post_visuals(article, claims, docs, [], output_dir=tmp_path)
    article, assets = complete_post_visuals(article, claims, docs, [{"asset_id": "fake-chart"}], output_dir=tmp_path)
    with pytest.raises(ValueError, match="TWO_TO_FIVE"):
        validate_release_media({"article": article, "media_assets": assets, "evidence": docs})


@pytest.mark.parametrize("destination", ["substack", *DESTINATIONS, "linkedin_company"])
def test_all_shared_transport_paths_refuse_missing_images_before_external_call(monkeypatch, destination):
    import live_contentops._eight_platform_substack_first_pipeline_impl_v1 as pipeline
    monkeypatch.setattr(pipeline, "_durable_intent_inputs", lambda intent: {"media_assets": []})
    class NeverPublish:
        def publish(self, **kwargs):
            pytest.fail("external transport called with no image")
    owner = CanonicalDestinationTransportRuntimeV1(neo_transport=NeverPublish(), linkedin_transport=NeverPublish())
    outcome = owner.publish(destination=destination, intent={}, authorization_context={})
    assert outcome["definite_no_write"] is True
    assert outcome["safe_error_classification"] == "EVERY_POST_IMAGE_REQUIRED:" + destination


@pytest.mark.parametrize("destination", ["substack", *DESTINATIONS])
def test_each_channel_requires_its_selected_exact_image(tmp_path, destination):
    article, claims, docs = packet()
    card = build_post_data_card(article, claims, docs, output_dir=tmp_path)
    data = {"media_assets": [card], "payloads": {destination: {"media_asset_ids": [card["asset_id"]]}}}
    require_publication_image(destination, data)
    if destination != "substack":
        data["payloads"][destination]["media_asset_ids"] = ["unbound"]
        with pytest.raises(ValueError, match="EVERY_POST_IMAGE"):
            require_publication_image(destination, data)
    data["payloads"][destination]["media_asset_ids"] = [card["asset_id"]]
    Path(card["path"]).write_bytes(b"changed")
    with pytest.raises(ValueError, match="IMAGE_BYTES_CHANGED"):
        require_publication_image(destination, data)
