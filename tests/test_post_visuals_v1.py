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


def test_relay_does_not_hide_private_survey_origin(tmp_path):
    article, claims, docs = packet()
    docs[0]["publisher"] = "Wire report"
    docs[0]["canonical_content_text"] = "ISM reported an index of 49.0."
    article["substack_body_markdown"] = docs[0]["canonical_content_text"]
    claims = [{"claim_id": "survey", "claim_text": docs[0]["canonical_content_text"],
        "source_id": "SOURCE_1", "support_excerpt": docs[0]["canonical_content_text"]}]
    with pytest.raises(ValueError, match="NO_ADMITTED_PUBLIC_VISUAL_FACTS"):
        build_post_data_card(article, claims, docs, output_dir=tmp_path)


def test_native_semantic_assembly_persists_card_before_preview_and_handoff(tmp_path):
    from test_v1_simple_gemini_newsroom_v1 import (
        _headlines, _candidate_ids, _selection, _article_output, _evidence_result, CUTOFF,
    )
    from live_contentops.v1_simple_gemini_newsroom_v1 import run_v1_simple_gemini_newsroom
    from live_contentops.nine_router_llm_seam_v2 import ROLE_V1_SIMPLE_SELECTION
    rolling = _headlines(1)
    selected = _selection(*_candidate_ids(rolling))
    selected["ordered_candidate_plan"][0]["article_mode"] = "BREAKING_BRIEF"
    visual = packet()[0]["visual_editorial_decision"]
    class ControlledNative:
        def frozen_request(self, stage):
            return None

        native_desktop_protocol = True
        def __call__(self, **kwargs):
            if kwargs["role_task_id"] == ROLE_V1_SIMPLE_SELECTION:
                output = selected
            else:
                output = _article_output()
                output["article"].update(reader_first_version="DATA_JOURNALISM_V1", visual_editorial_decision=visual)
            return output, {"provider": "NATIVE_CODEX_DESKTOP", "selected_model": "gpt-6.1-sol",
                "reasoning_effort": "max", "observation_source": "CONTROLLED_TEST_NOT_MODEL_PROOF"}
        def admitted_editorial_media(self):
            return []
        def telemetry(self):
            return {"observations": [{"observation_source": "CONTROLLED_TEST_NOT_MODEL_PROOF"}]}
    def evidence(request):
        result = _evidence_result()
        result["evidence_documents"][0]["source_reuse_constraints"] = packet()[2][0]["source_reuse_constraints"]
        return result
    result = run_v1_simple_gemini_newsroom(output_dir=tmp_path, cutoff_utc=CUTOFF,
        rolling_input=rolling, llm_invoke=ControlledNative(), evidence_loader=evidence, run_id="controlled-card-assembly")
    assert result["qualified_article_count"] == 1
    assert result["media_assets"][0]["modality"] == "source_bound_data_card"
    article = json.loads((tmp_path / "article_manifest_v1.json").read_bytes())
    assert article["post_visual_policy"] == POLICY
    context = json.loads((tmp_path / "run_context_v1.json").read_bytes())
    assert context["media"]["assets"][0]["sha256"] == result["media_assets"][0]["sha256"]
    previews = json.loads((tmp_path / "native_derivative_previews_v1.json").read_bytes())
    assert all(p["media_asset_ids"] for p in previews["packages"].values())
    assert result["publication_lifecycle_plan"]["skipped_derivative_destinations"] == []


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
    with pytest.raises(ValueError, match="TWO_TO_FIVE|ANALYSIS_OFFICIAL_HISTORY_CHARTS_REQUIRED"):
        validate_release_media({"article": article, "media_assets": assets, "evidence": docs})


def test_preparation_without_photo_can_reach_writer_but_final_post_needs_card(tmp_path):
    article, claims, docs = packet()
    prewriter = {"visual_editorial_decision": article["visual_editorial_decision"], "evidence": docs, "media_assets": []}
    assert validate_release_media(prewriter, prewriter=True)["photo_count"] == 0
    article["post_visual_policy"] = POLICY
    with pytest.raises(ValueError, match="DATA_CARD_REQUIRED"):
        validate_release_media({"article": article, "evidence": docs, "media_assets": []})


def test_card_small_chart_uses_existing_admitted_series_owner(tmp_path):
    from test_reader_first_data_journalism_v1 import chart_packet
    series, docs = chart_packet()
    doc = docs[0]
    doc.update(source_id="SOURCE_1", underlying_reuse_classification="governed_government_public_domain",
        rights_evidence_sha256="d" * 64)
    text = doc["canonical_content_text"]
    article = {"substack_body_markdown": text}
    claims = [{"claim_id": "revenue", "source_id": "SOURCE_1", "claim_text": text, "support_excerpt": text}]
    asset = build_post_data_card(article, claims, docs, output_dir=tmp_path, series_packet=series)
    validate_post_data_card(asset, article, docs)
    assert asset["data_card_packet"]["series_asset"]["computed_values"] == [[100, 120]]
    assert asset["height"] > 1080
    assert asset["height"] <= 1350
    bad_article = {"substack_body_markdown": text.replace("120", "121")}
    bad_claims = [{**claims[0], "claim_text": bad_article["substack_body_markdown"],
        "support_excerpt": bad_article["substack_body_markdown"]}]
    with pytest.raises(ValueError, match="FACT_OR_NUMBER"):
        build_post_data_card(bad_article, bad_claims, docs, output_dir=tmp_path, series_packet=series)


def test_invalid_image_never_reaches_transport(tmp_path, monkeypatch):
    import live_contentops._eight_platform_substack_first_pipeline_impl_v1 as pipeline
    article, claims, docs = packet()
    card = build_post_data_card(article, claims, docs, output_dir=tmp_path)
    Path(card["path"]).write_bytes(b"not an image")
    card["sha256"] = sha256(Path(card["path"]).read_bytes()).hexdigest()
    monkeypatch.setattr(pipeline, "_durable_intent_inputs", lambda intent: {"media_assets": [card]})
    class NeverPublish:
        def publish(self, **kwargs):
            pytest.fail("external transport called with invalid image")
    owner = CanonicalDestinationTransportRuntimeV1(neo_transport=NeverPublish(), linkedin_transport=NeverPublish())
    assert owner.publish(destination="substack", intent={}, authorization_context={})["definite_no_write"] is True


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
    data.update(public_image_url="https://example.org/card.png", primary_media={"sha256": card["sha256"],
        "public_delivery_sha256": card["sha256"], "local_public_hash_continuity": True})
    require_publication_image(destination, data)
    if destination != "substack":
        data["payloads"][destination]["media_asset_ids"] = ["unbound"]
        with pytest.raises(ValueError, match="EVERY_POST_IMAGE"):
            require_publication_image(destination, data)
    data["payloads"][destination]["media_asset_ids"] = [card["asset_id"]]
    Path(card["path"]).write_bytes(b"changed")
    with pytest.raises(ValueError, match="IMAGE_BYTES_CHANGED"):
        require_publication_image(destination, data)


@pytest.mark.parametrize("destination", ["discord", "facebook_page", "instagram_business", "threads"])
def test_url_transport_cannot_fall_back_to_text_or_another_image(tmp_path, destination):
    article, claims, docs = packet()
    card = build_post_data_card(article, claims, docs, output_dir=tmp_path)
    data = {"media_assets": [card], "payloads": {destination: {"media_asset_ids": [card["asset_id"]]}}}
    with pytest.raises(ValueError, match="SELECTED_IMAGE_PUBLIC_DELIVERY_REQUIRED"):
        require_publication_image(destination, data)
    data.update(public_image_url="https://example.org/wrong.png", primary_media={"sha256": "e" * 64,
        "public_delivery_sha256": "e" * 64, "local_public_hash_continuity": True})
    with pytest.raises(ValueError, match="SELECTED_IMAGE_PUBLIC_DELIVERY_REQUIRED"):
        require_publication_image(destination, data)


def test_visual_request_reentry_preserves_exact_frozen_prompt(tmp_path):
    from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn, DesktopInputRequired
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    store = ContentOpsDurableStore(tmp_path / "state.sqlite3")
    run = "controlled-visual-reentry"
    work = "cc-opportunity-" + sha256_of(run)
    store.create_work_item(story_id=work, work_item_id=work, title="Controlled", target_surface="TEST")
    turn = NativeDesktopTurn(store, run_id=run, output_dir=tmp_path, owner_manual_validation=True)
    with pytest.raises(DesktopInputRequired) as light:
        turn(logical_invocation_id=run + ":media-plan", governed_input={}, prompt="Controlled Light",
            validator=lambda raw: (True, None, json.loads(raw), None))
    story = {"thesis": "Controlled proposal", "exact_series": []}
    turn.submit("media-plan", {"request_sha256": light.value.request["request_sha256"], "output": {"story_plan": story},
        "invocation_observation": {"surface": "CODEX_NATIVE_SUBAGENT", "model": "gpt-6.1-sol", "reasoning_effort": "low",
            "invocation_id": "controlled-light", "observation_source": "CONTROLLED_TEST_NOT_MODEL_PROOF"}})
    prep = {"native_plan_run_id": run, "native_plan_stage": "media-plan", "story_plan": story,
        "native_plan_request_sha256": light.value.request["request_sha256"]}
    with pytest.raises(DesktopInputRequired) as first:
        turn.request_visual_decision(source_packet={}, preparation=prep)
    with pytest.raises(DesktopInputRequired) as second:
        turn.request_visual_decision(source_packet={}, preparation=prep)
    assert first.value.request == second.value.request
    assert first.value.request["prompt"].count("CC-144 / Jim decision 42:") == 1


def test_delivery_url_is_selected_by_the_channel_asset_hash(tmp_path):
    from live_contentops.v1_simple_gemini_newsroom_v1 import _build_simple_publication_lifecycle_plan
    from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import _durable_intent_inputs
    article, claims, docs = packet()
    article, assets = complete_post_visuals(article, claims, docs, [], output_dir=tmp_path)
    previews, _ = _native_preview_bundle(article=article, article_mode="BREAKING_BRIEF", article_identity="c" * 64,
        media_assets=assets, media_asset_ids=[assets[0]["asset_id"]])
    _build_simple_publication_lifecycle_plan(run_id="controlled-selection", output_dir=tmp_path,
        selected_candidate={"story_identity": "controlled"}, selected_plan_entry={"article_mode": "BREAKING_BRIEF"},
        article=article, article_identity="c" * 64, native_previews=previews,
        qualified_record={"accepted_evidence_ids": [docs[0]["document_id"]]}, epistemic_state=None, media_assets=assets)
    rows = [{"asset_id": "not-selected", "sha256": "e" * 64, "public_delivery_sha256": "e" * 64,
        "verified_public_delivery_url": "https://example.org/wrong.png", "local_public_hash_continuity": True},
        {"asset_id": assets[0]["asset_id"], "sha256": assets[0]["sha256"], "public_delivery_sha256": assets[0]["sha256"],
        "verified_public_delivery_url": "https://example.org/card.png", "local_public_hash_continuity": True}]
    (tmp_path / "delivery_media_manifest_v1.json").write_text(json.dumps({"assets": rows}))
    data = _durable_intent_inputs({"output_dir": str(tmp_path), "canonical_url": "https://capitalchronicle.substack.com/p/controlled",
        "destination_plan": {"destination": "instagram_business"}, "native_payload": previews["packages"]["instagram_business"]})
    assert data["public_image_url"] == "https://example.org/card.png"
    assert data["primary_media"]["sha256"] == assets[0]["sha256"]
    require_publication_image("instagram_business", data)
    data.update(public_image_url="https://example.org/wrong.png", primary_media={"sha256": "e" * 64,
        "public_delivery_sha256": "e" * 64, "local_public_hash_continuity": True})
    with pytest.raises(ValueError, match="SELECTED_IMAGE_PUBLIC_DELIVERY_REQUIRED"):
        require_publication_image("instagram_business", data)


def test_long_cards_keep_complete_claims_in_bounded_readable_layout(tmp_path):
    article, claims, docs = packet()
    texts = [("Agency " + letter + " reported " + "unchanged implementation details and timing limits " * 5).strip()
        for letter in ("A", "B", "C")]
    docs[0]["publisher"] = "Controlled public agency with a long source attribution kept readable in the card"
    docs[0]["canonical_content_text"] = " ".join(texts)
    article["substack_body_markdown"] = "\n\n".join(texts)
    claims = [{"claim_id": "fact-" + str(i), "source_id": "SOURCE_1", "claim_text": text, "support_excerpt": text}
        for i, text in enumerate(texts)]
    card = build_post_data_card(article, claims, docs, output_dir=tmp_path)
    assert 1080 <= card["height"] <= 1350
    assert card["width"] == 1080
    assert all(f["text"] in texts for f in card["data_card_packet"]["facts"])
    validate_post_data_card(card, article, docs)


def test_source_bound_card_survives_existing_live_image_selection(tmp_path):
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import post_image_view
    article, claims, docs = packet()
    article, assets = complete_post_visuals(article, claims, docs, [], output_dir=tmp_path)
    result = post_image_view({"article": article, "media_assets": assets, "evidence": docs,
        "accepted_evidence_sha256": "f" * 64}, output_dir=tmp_path / "consumer")
    assert result["media_assets"] == assets
    assert result["post_image_policy"]["excluded_optional_assets"] == []
    assert result["post_image_policy"]["default_asset_id"] == assets[0]["asset_id"]
    assert all(ids == [assets[0]["asset_id"]] for ids in result["article"]["native_destination_media"].values())
    payloads, intents = _native_preview_bundle(article=result["article"], article_mode="BREAKING_BRIEF",
        article_identity="controlled", epistemic_state={}, media_asset_ids=[a["asset_id"] for a in assets],
        media_assets=assets)
    assert len(payloads["packages"]) == 8
    assert all(p["media_asset_ids"] == [assets[0]["asset_id"]] for p in payloads["packages"].values())
    validate_post_data_card(result["media_assets"][0], article, docs)
