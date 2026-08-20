import json
import inspect
from pathlib import Path

import live_contentops._eight_platform_substack_first_pipeline_impl_v1 as pipeline
from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import (
    EXPECTED_DESTINATIONS,
    _classification,
    _dispatch_once,
    build_native_derivative_payloads,
)
from live_contentops.destination_transport_registry_v1 import (
    V1_REQUIRED_PUBLICATION_DESTINATIONS,
)
from live_contentops.media_manifest_authority_v1 import build_delivery_only_editorial_card


def _article() -> dict:
    return {"title": "Effective Fed Funds Rate Holds at 3.62% as Policy Calibration Continues", "subtitle": "FRED's latest reading keeps the policy-transmission question in focus."}


def _selection() -> dict:
    return {
        "dek": "FRED's latest effective federal funds reading keeps the policy-transmission question in focus.",
        "market_mechanism": "Funding conditions move through administered rates, the curve, credit, and discount-rate expectations.",
        "policy_context": "Policy communication frames the short end while the curve absorbs growth and inflation uncertainty.",
        "cross_asset_implications": "Cross-asset moves can reflect different repricing channels rather than one simple market verdict.",
    }


def test_exact_v1_ordinary_payloads_are_eight_derivatives_without_tiktok():
    article = {
        **_article(),
        "minimum_trustworthy_evidence_packet": {"status": "PASS", "risk_tier": "ORDINARY"},
    }
    payloads = build_native_derivative_payloads(
        article=article,
        selection=_selection(),
        canonical_url="https://capitalchronicle.substack.com/p/governed-brief",
        media_asset_ids=(),
    )
    assert set(payloads) == set(V1_REQUIRED_PUBLICATION_DESTINATIONS) - {"substack"}
    assert "tiktok" not in payloads
    assert payloads["x"]["overflow_strategy"] == "single_root"
    assert payloads["threads"]["overflow_strategy"] == "single_root"
    assert payloads["x"]["hard_truncation_used"] is False
    assert payloads["threads"]["hard_truncation_used"] is False


def _normalized_reader_text(payload: dict) -> str:
    return " ".join(str(payload.get("full_text") or payload["text"]).casefold().split())


def test_breaking_and_ordinary_briefs_are_native_self_contained_and_undispatched():
    canonical_url = "https://capitalchronicle.substack.com/p/governed-brief"
    accepted_article = {
        **_article(),
        "social_lede": "The latest official policy reading keeps the transmission question in focus.",
        "social_mechanism_summary": "The final article explains how the policy reading reaches funding conditions.",
        "social_policy_summary": "The final article places the reading in its stated policy context.",
        "social_cross_asset_summary": "The final article identifies the supported cross-asset detail to watch.",
        "unaccepted_raw_draft": "UNSUPPORTED FACT THAT MUST NEVER BE PACKAGED.",
    }
    accepted_selection = {
        **_selection(),
        "unaccepted_note": "UNSUPPORTED FACT THAT MUST NEVER BE PACKAGED.",
    }

    for mode_article in (
        {
            **accepted_article,
            "minimum_trustworthy_evidence_packet": {
                "status": "PASS", "risk_tier": "ORDINARY"
            },
        },
        {**accepted_article, "effective_article_mode": "BREAKING_BRIEF"},
    ):
        payloads = build_native_derivative_payloads(
            article=mode_article,
            selection=accepted_selection,
            canonical_url=canonical_url,
            media_asset_ids=(),
        )
        reader_texts = {
            destination: _normalized_reader_text(payload)
            for destination, payload in payloads.items()
        }

        assert set(payloads) == set(V1_REQUIRED_PUBLICATION_DESTINATIONS) - {"substack"}
        assert "tiktok" not in payloads
        assert len(set(reader_texts.values())) >= 4
        assert len({reader_texts[name] for name in ("x", "threads", "linkedin", "telegram", "discord", "instagram_business")}) >= 4
        for destination, payload in payloads.items():
            text = str(payload.get("full_text") or payload["text"])
            assert canonical_url in text
            assert text.index(canonical_url) > 0
            assert "UNSUPPORTED FACT" not in text
            assert any(
                accepted in text
                for accepted in (
                accepted_article["social_lede"],
                    accepted_article["social_mechanism_summary"],
                    accepted_article["social_policy_summary"],
                    accepted_article["social_cross_asset_summary"],
                )
            ), destination
            assert "dispatch" not in payload
            assert payload["hard_truncation_used"] is False

        for destination, limit in (("x", 280), ("threads", 500)):
            payload = payloads[destination]
            assert payload["reply_texts"]
            assert all(
                len(item) <= limit
                for item in [payload["root_text"], *payload["reply_texts"]]
            )
            assert all(
                "..." not in item
                for item in [payload["root_text"], *payload["reply_texts"]]
            )


def test_native_briefs_never_promote_pre_evidence_selection_hypotheses() -> None:
    canonical_url = "https://capitalchronicle.substack.com/p/final-article-only"
    article = {
        "title": "Final Article Confirms Supported Fact A",
        "subtitle": "Supported fact A is the final article's narrow reader-facing update.",
        "substack_body_markdown": " ".join((
            "Supported fact A is confirmed by the final article.",
            "Supported fact B supplies the article's second source-bound detail.",
            "Supported fact C explains the article's third source-bound detail.",
            "Supported fact D sets the article's final supported detail.",
        )),
        "minimum_trustworthy_evidence_packet": {"status": "PASS", "risk_tier": "ORDINARY"},
    }
    selection = {
        "dek": "UNSUPPORTED_PRE_EVIDENCE_HYPOTHESIS",
        "market_mechanism": "UNSUPPORTED_PRE_EVIDENCE_HYPOTHESIS",
        "policy_context": "UNSUPPORTED_PRE_EVIDENCE_HYPOTHESIS",
        "cross_asset_implications": "UNSUPPORTED_PRE_EVIDENCE_HYPOTHESIS",
        "selection_case": "UNSUPPORTED_PRE_EVIDENCE_HYPOTHESIS",
        "why_now": "UNSUPPORTED_PRE_EVIDENCE_HYPOTHESIS",
        "seo_intent": "UNSUPPORTED_PRE_EVIDENCE_HYPOTHESIS",
    }

    payloads = build_native_derivative_payloads(
        article=article,
        selection=selection,
        canonical_url=canonical_url,
        media_asset_ids=(),
    )
    reader_texts = {
        destination: _normalized_reader_text(payload)
        for destination, payload in payloads.items()
    }

    assert set(payloads) == set(V1_REQUIRED_PUBLICATION_DESTINATIONS) - {"substack"}
    assert "tiktok" not in payloads
    assert len(set(reader_texts.values())) >= 4
    for payload in payloads.values():
        text = str(payload.get("full_text") or payload["text"])
        assert "UNSUPPORTED_PRE_EVIDENCE_HYPOTHESIS" not in text
        assert any(
            supported in text
            for supported in (
                article["subtitle"],
                "Supported fact B supplies the article's second source-bound detail.",
                "Supported fact C explains the article's third source-bound detail.",
            )
        )
        assert "dispatch" not in payload
        assert payload["hard_truncation_used"] is False
    for destination, limit in (("x", 280), ("threads", 500)):
        payload = payloads[destination]
        assert all(
            len(item) <= limit
            for item in [payload["root_text"], *payload["reply_texts"]]
        )
        assert all(
            "..." not in item
            for item in [payload["root_text"], *payload["reply_texts"]]
        )

    narrow_payloads = build_native_derivative_payloads(
        article={
            "title": "Agency Issues One Supported Update",
            "subtitle": "The final article reports one supported official fact.",
            "minimum_trustworthy_evidence_packet": {"status": "PASS", "risk_tier": "ORDINARY"},
        },
        selection=selection,
        canonical_url=canonical_url,
        media_asset_ids=(),
    )
    assert all(
        "Watch:" not in str(payload.get("full_text") or payload["text"])
        and "What to watch:" not in str(payload.get("full_text") or payload["text"])
        for payload in narrow_payloads.values()
    )
    assert narrow_payloads["x"]["reply_texts"] == []
    assert narrow_payloads["threads"]["reply_texts"] == []


def test_delivery_only_card_is_rights_safe_and_never_article_media(tmp_path):
    asset = build_delivery_only_editorial_card(
        output_path=tmp_path / "delivery.png",
        title="Governed official event update",
        source_label="Official Agency",
        source_page_url="https://official.example/record",
        published_at="2026-08-17T00:00:00Z",
    )
    assert Path(asset["path"]).is_file()
    assert asset["media_role"] == "delivery_only"
    assert asset["article_inclusion"] is False
    assert asset["canonical_article_media"] is False
    assert asset["generated_documentary_imagery"] is False
    assert asset["rights_basis"] == "CONTENTOPS_OWNED_LAYOUT_SOURCE_METADATA_ONLY"


def test_zero_article_media_plan_contains_all_nine_and_no_optional_skip(tmp_path):
    delivery = build_delivery_only_editorial_card(
        output_path=tmp_path / "delivery.png",
        title="Governed official event update",
        source_label="Official Agency",
        source_page_url="https://official.example/record",
    )
    payload_hashes = {
        destination: destination * 8
        for destination in V1_REQUIRED_PUBLICATION_DESTINATIONS
        if destination != "substack"
    }
    readiness = {
        "destinations": {
            destination: {"readiness_state": "READY_NON_BROWSER_BINDING"}
            for destination in V1_REQUIRED_PUBLICATION_DESTINATIONS
        }
    }
    plan = pipeline._build_rolling_x_publication_plan(
        run_id="zero-article-media",
        output_dir=tmp_path,
        viability={"selected_cluster_id": "story-1", "selected_cluster": {}},
        preparation={
            "release_candidate_lock": {
                "article_body_sha256": "a" * 64,
                "lock_sha256": "b" * 64,
                "payload_sha256": payload_hashes,
                "artifacts": {"delivery_only_media_delivery_only_editorial_card": {}},
            },
            "context": {
                "article": {"title": "Governed update", "substack_body_markdown": "Governed body."},
                "media": {"assets": [], "delivery_only_assets": [delivery]},
            },
            "payloads": {destination: {"text": destination} for destination in payload_hashes},
        },
        readiness=readiness,
    )
    assert {row["destination"] for row in plan["destinations"]} == set(
        V1_REQUIRED_PUBLICATION_DESTINATIONS
    )
    assert plan["skipped_derivative_destinations"] == []
    assert plan["pre_substack_blockers"] == []
    assert plan["transaction_readiness"] == "READY"
    assert next(
        row for row in plan["destinations"] if row["destination"] == "instagram_business"
    )["delivery_media_required"] is True


def test_cloudinary_precondition_runs_only_after_full_nine_and_unknown_write_zero(
    tmp_path, monkeypatch
):
    delivery = build_delivery_only_editorial_card(
        output_path=tmp_path / "delivery.png",
        title="Governed official event update",
        source_label="Official Agency",
        source_page_url="https://official.example/record",
    )
    (tmp_path / "run_context_v1.json").write_text(
        json.dumps({"media": {"assets": [], "delivery_only_assets": [delivery]}}),
        encoding="utf-8",
    )
    calls = []
    manifest = {
        "status": "PASS",
        "assets": [
            {
                "media_asset_id": delivery["asset_id"],
                "media_role": "delivery_only",
                "sha256": delivery["sha256"],
                "public_delivery_sha256": delivery["sha256"],
                "local_public_hash_continuity": True,
                "verified_public_delivery_url": "https://res.cloudinary.com/example/delivery.png",
            }
        ],
    }

    def prepare(**kwargs):
        calls.append(kwargs)
        return {
            "status": "CLOUDINARY_DELIVERY_MEDIA_READY",
            "manifest": manifest,
            "provider_calls": 1,
        }

    monkeypatch.setattr(pipeline, "prepare_cloudinary_delivery_media", prepare)
    blocked = pipeline._prepare_cloudinary_delivery_media_for_plan(
        work_item_id="work-1",
        plan={"output_dir": str(tmp_path)},
        preconditions={
            "full_v1_distribution_status": "HOLD_FULL_V1_DISTRIBUTION_NOT_READY",
            "unknown_write_count": 0,
        },
    )
    assert blocked["status"] == "BLOCKED_CLOUDINARY_DELIVERY_MEDIA_PRECONDITIONS"
    assert calls == []

    ready = pipeline._prepare_cloudinary_delivery_media_for_plan(
        work_item_id="work-1",
        plan={"output_dir": str(tmp_path)},
        preconditions={
            "full_v1_distribution_status": "FULL_V1_DISTRIBUTION_READY",
            "unknown_write_count": 0,
        },
    )
    assert ready["status"] == "CLOUDINARY_DELIVERY_MEDIA_READY"
    assert len(calls) == 1
    assert json.loads(
        (tmp_path / "delivery_media_manifest_v1.json").read_text(encoding="utf-8")
    ) == manifest


def test_substack_transport_receives_only_canonical_article_media(monkeypatch, tmp_path):
    article_media = {"asset_id": "article-chart", "path": str(tmp_path / "chart.png")}
    delivery_only = {"asset_id": "delivery-card", "media_role": "delivery_only"}
    captured = {}
    monkeypatch.setattr(
        pipeline,
        "_durable_intent_inputs",
        lambda _intent: {
            "output_dir": tmp_path,
            "article": {
                "title": "Exact title",
                "subtitle": "Exact subtitle",
                "substack_body_markdown": "[[VISUAL:article-chart]]",
            },
            "payloads": {},
            "canonical_url": "",
            "local_media": article_media["path"],
            "public_image_url": "",
            "primary_media": {},
            "media_assets": [article_media],
            "delivery_only_assets": [delivery_only],
        },
    )

    def publish(**kwargs):
        captured.update(kwargs)
        return {"status": "FAILED_SUBSTACK_IMAGE_UPLOAD", "draft_id": "draft-1"}

    monkeypatch.setattr(pipeline, "publish_substack_article_via_edge", publish)
    result = pipeline._publish_one_destination_from_durable_intent(
        destination="substack",
        intent={"attempt_identity": "dispatch-1", "output_dir": str(tmp_path)},
        authorization_context={
            "operating_mode": "AUTONOMOUS_DEFAULT",
            "dispatch_attempt_identity": "dispatch-1",
        },
    )

    assert result["status"] == "FAILED_SUBSTACK_IMAGE_UPLOAD"
    assert captured["image_assets"] == [article_media]
    assert "delivery_only_assets" not in captured


def test_instagram_consumes_only_verified_delivery_manifest_media(monkeypatch, tmp_path):
    media = {
        "media_asset_id": "delivery-card",
        "verified_public_delivery_url": "https://res.cloudinary.com/example/delivery.png",
        "sha256": "a" * 64,
        "public_delivery_sha256": "a" * 64,
        "local_public_hash_continuity": True,
        "absolute_local_source_path": str(tmp_path / "delivery.png"),
    }
    captured = {}
    monkeypatch.setattr(
        pipeline,
        "_durable_intent_inputs",
        lambda _intent: {
            "output_dir": tmp_path,
            "article": {"title": "Exact title"},
            "payloads": {"instagram_business": {"text": "Caption"}},
            "canonical_url": "https://capitalchronicle.substack.com/p/exact",
            "local_media": "",
            "delivery_local_media": media["absolute_local_source_path"],
            "public_image_url": media["verified_public_delivery_url"],
            "primary_media": media,
            "media_assets": [],
            "delivery_only_assets": [],
        },
    )
    monkeypatch.setattr(
        pipeline,
        "_publish_instagram_media_verified",
        lambda **kwargs: captured.update(kwargs) or {"status": "SUCCESS"},
    )

    result = pipeline._publish_one_destination_from_durable_intent(
        destination="instagram_business",
        intent={"attempt_identity": "dispatch-1", "output_dir": str(tmp_path)},
        authorization_context={
            "operating_mode": "AUTONOMOUS_DEFAULT",
            "dispatch_attempt_identity": "dispatch-1",
        },
    )

    assert result["status"] == "SUCCESS"
    assert captured["media"] == media
    assert captured["media"]["verified_public_delivery_url"].startswith("https://")


def test_instagram_fails_definite_no_write_without_verified_delivery_media(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        pipeline,
        "_durable_intent_inputs",
        lambda _intent: {
            "output_dir": tmp_path,
            "article": {"title": "Exact title"},
            "payloads": {"instagram_business": {"text": "Caption"}},
            "canonical_url": "https://capitalchronicle.substack.com/p/exact",
            "local_media": "",
            "public_image_url": "",
            "primary_media": {},
            "media_assets": [],
            "delivery_only_assets": [],
        },
    )
    monkeypatch.setattr(
        pipeline,
        "_publish_instagram_media_verified",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("must not publish")),
    )

    result = pipeline._publish_one_destination_from_durable_intent(
        destination="instagram_business",
        intent={"attempt_identity": "dispatch-1", "output_dir": str(tmp_path)},
        authorization_context={
            "operating_mode": "AUTONOMOUS_DEFAULT",
            "dispatch_attempt_identity": "dispatch-1",
        },
    )

    assert result == {
        "status": "DEFINITE_NO_WRITE",
        "definite_no_write": True,
        "reason_code": "VERIFIED_DELIVERY_MEDIA_UNAVAILABLE",
    }


def test_treasury_rc_editorial_replacements_remove_process_copy_and_repetition() -> None:
    original = "\n\n".join(str(row["old"]) for row in pipeline.TREASURY_RC_EDITORIAL_REPLACEMENTS)
    revised = pipeline._apply_exact_editorial_replacements(
        original,
        pipeline.TREASURY_RC_EDITORIAL_REPLACEMENTS,
    )

    assert "governed" not in revised
    assert "packet timestamp" not in revised
    assert "evidence packet" not in revised
    assert "public claim permission" not in revised
    assert pipeline.TREASURY_RC_EDITORIAL_REPLACEMENTS[2]["old"] not in revised
    assert "official July 13 close rather than a live quote" in revised


def test_exact_editorial_replacement_fails_on_missing_or_ambiguous_source() -> None:
    import pytest

    replacement = ({"old": "exact paragraph", "new": "revised paragraph"},)
    with pytest.raises(ValueError, match="exact_editorial_replacement_count_invalid"):
        pipeline._apply_exact_editorial_replacements("different paragraph", replacement)
    with pytest.raises(ValueError, match="exact_editorial_replacement_count_invalid"):
        pipeline._apply_exact_editorial_replacements("exact paragraph exact paragraph", replacement)


def _final_treasury_evidence() -> dict:
    punctuation = (
        "The official table shows the 2-year yield rising five basis points from July 10, to 4.26%, "
        "while the 10-year yield rose six basis points to 4.62% and the 30-year yield rose four basis points to 5.10%."
    )
    auction = (
        "Confirmation would require more than another one-basis-point widening. "
        "A sustained rise in the 10-year and 30-year sectors relative to the 2-year, accompanied by firm demand evidence from Treasury auctions, would confirm that the long-end pressure is persistent. "
        "The next CPI release and subsequent official curve closes are named catalysts."
    )
    body = f"Opening paragraph.\n\n{punctuation}\n\n{auction}\n"
    results = {
        name: {"status": "SUCCESS", "id": f"{name}-id", "public_url": f"https://example.com/{name}", "payload_sha256": name}
        for name in pipeline.EXPECTED_DESTINATIONS
    }
    results["substack"] = {
        "status": "SUCCESS",
        "draft_id": pipeline.FINAL_TREASURY_DRAFT_ID,
        "public_url": pipeline.FINAL_TREASURY_PUBLIC_URL,
    }
    return {
        "article": {
            "title": pipeline.FINAL_TREASURY_TITLE,
            "subtitle": pipeline.FINAL_TREASURY_SUBTITLE,
            "substack_body_markdown": body,
            "rendered_body": body,
        },
        "media": {"assets": [{"asset_id": value} for value in ("one", "two", "three")]},
        "results": results,
    }


def test_final_treasury_auction_repair_is_exact_and_freezes_derivatives(tmp_path: Path, monkeypatch) -> None:
    evidence = _final_treasury_evidence()
    (tmp_path / "run_evidence_v1.json").write_text(json.dumps(evidence), encoding="utf-8")
    frozen_before = json.loads(json.dumps(evidence["results"]))
    captured: dict = {}

    def editor(**kwargs):
        captured["replacements"] = kwargs["replacements"]
        assert len(kwargs["replacements"]) == 2
        assert all(row["old"].count(".") >= 1 for row in kwargs["replacements"])
        return {"status": "SUCCESS", "browser_write_performed": True}

    revised = pipeline._apply_exact_editorial_replacements(
        evidence["article"]["substack_body_markdown"],
        pipeline.FINAL_TREASURY_AUCTION_LOGIC_REPLACEMENTS,
    )
    visible = " ".join(revised.split())
    monkeypatch.setattr(pipeline, "repair_substack_editorial_paragraphs_via_edge", editor)
    monkeypatch.setattr(
        pipeline,
        "publish_substack_article_via_edge",
        lambda **kwargs: {
            "status": "SUCCESS",
            "draft_id": pipeline.FINAL_TREASURY_DRAFT_ID,
            "public_url": pipeline.FINAL_TREASURY_PUBLIC_URL,
            "publication_write_mode": "update_existing_public_article",
            "readback": {
                "title_visible": True,
                "subtitle_visible": True,
                "body_complete": True,
                "captions_visible": True,
                "content_readback_verified": True,
                "source_links_visible": True,
                "source_url_count_expected": 6,
                "public_image_count": 3,
                "public_image_alt_or_caption_count": 3,
                "visual_spread_through_public_body": True,
                "visible_body_text": visible,
            },
        },
    )
    monkeypatch.setattr(pipeline, "_persist_final_platform_matrix", lambda *_args, **_kwargs: {})

    result = pipeline._repair_final_treasury_auction_logic(output_dir=tmp_path, cdp_port=9223)

    repair = result["final_auction_logic_repair"]
    assert repair["status"] == "SUCCESS"
    assert repair["replacement_count"] == 2
    assert repair["numeric_claims_preserved"] is True
    assert repair["frozen_derivatives_preserved"] is True
    assert repair["derivative_writes_performed"] is False
    assert repair["video_adapters_invoked"] is False
    for name, row in frozen_before.items():
        if name != "substack":
            assert result["results"][name] == row
    assert len(captured["replacements"]) == 2
    assert "July 10 to 4.26%" in result["article"]["rendered_body"]
    assert "firm demand evidence" not in result["article"]["rendered_body"]


def test_final_treasury_auction_repair_blocks_identity_mismatch_without_browser(tmp_path: Path, monkeypatch) -> None:
    evidence = _final_treasury_evidence()
    evidence["article"]["subtitle"] = "unauthorized subtitle"
    (tmp_path / "run_evidence_v1.json").write_text(json.dumps(evidence), encoding="utf-8")
    monkeypatch.setattr(
        pipeline,
        "repair_substack_editorial_paragraphs_via_edge",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("browser must not run")),
    )

    result = pipeline._repair_final_treasury_auction_logic(output_dir=tmp_path, cdp_port=9223)

    assert result["final_auction_logic_repair"]["status"] == "BLOCKED_FINAL_AUCTION_LOGIC_REPAIR_IDENTITY_MISMATCH"


def test_final_treasury_auction_repair_never_retries_unknown_write(tmp_path: Path, monkeypatch) -> None:
    evidence = _final_treasury_evidence()
    evidence["final_auction_logic_repair"] = {
        "status": "BLOCKED_FINAL_AUCTION_LOGIC_REPAIR_NOT_PUBLICLY_VERIFIED",
        "adapter_result": {"browser_write_performed": True},
    }
    (tmp_path / "run_evidence_v1.json").write_text(json.dumps(evidence), encoding="utf-8")
    monkeypatch.setattr(
        pipeline,
        "repair_substack_editorial_paragraphs_via_edge",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("unknown write must reconcile, not retry")),
    )

    result = pipeline._repair_final_treasury_auction_logic(output_dir=tmp_path, cdp_port=9223)

    repair = result["final_auction_logic_repair"]
    assert repair["status"] == "BLOCKED_FINAL_AUCTION_LOGIC_REPAIR_RECONCILIATION_REQUIRED"
    assert repair["automatic_retry_blocked"] is True


def test_native_payloads_are_distinct_and_carry_canonical_url():
    canonical_url = "https://capitalchronicle.substack.com/p/effective-fed-funds-rate-policy-calibration"
    payloads = build_native_derivative_payloads(article=_article(), selection=_selection(), canonical_url=canonical_url)
    assert canonical_url in payloads["x"]["text"]
    assert canonical_url in payloads["linkedin"]["text"]
    assert canonical_url in payloads["discord"]["text"]
    assert canonical_url in payloads["telegram"]["text"]
    assert canonical_url in payloads["youtube"]["text"]
    assert payloads["telegram"]["format"] == "channel_photo_with_caption"
    assert payloads["youtube"]["format"] == "community_text_image_post"
    assert payloads["x"]["format"] != payloads["linkedin"]["format"]
    assert payloads["discord"]["text"] != payloads["facebook_page"]["text"]
    assert len(payloads["x"]["text"]) <= 280


def test_x_and_threads_overflow_is_compiled_to_complete_ordered_replies():
    canonical_url = "https://capitalchronicle.substack.com/p/effective-fed-funds-rate-policy-calibration"
    payloads = build_native_derivative_payloads(article=_article(), selection=_selection(), canonical_url=canonical_url)

    for platform, limit in (("x", 280), ("threads", 500)):
        payload = payloads[platform]
        assert payload["hard_truncation_used"] is False
        assert payload["reply_texts"]
        assert canonical_url in payload["root_text"]
        assert all(len(item) <= limit for item in [payload["root_text"], *payload["reply_texts"]])
        assert all("..." not in item for item in [payload["root_text"], *payload["reply_texts"]])
        assert "Funding conditions move through administered rates" in payload["full_text"]
        assert len(payload["reply_texts"]) == len(set(payload["reply_texts"]))


def test_x_and_threads_use_three_coherent_posts_with_all_article_visuals():
    canonical_url = "https://capitalchronicle.substack.com/p/effective-fed-funds-rate-holds-at"
    payloads = build_native_derivative_payloads(article=_article(), selection=_selection(), canonical_url=canonical_url)

    for platform in ("x", "threads"):
        payload = payloads[platform]
        metrics = payload["quality_metrics"]
        assert len(payload["posts"]) == 3
        assert metrics["reply_count"] == 2
        assert metrics["sentence_boundary_pass"] is True
        assert metrics["orphan_fragment_count"] == 0
        assert metrics["shortest_longest_reply_ratio"] >= 0.45
        assert metrics["visual_distribution_pass"] is True
        assert metrics["complete_article_visual_count"] == 3
        assert metrics["duplicated_sentence_count"] == 0
        assert [row["media_asset_ids"] for row in payload["posts"]] == [
            ["primary"], ["policy_corridor"], ["sofr_context"]
        ]
        assert payload["posts"][0]["media_asset_ids"] == ["primary"]


def test_sentence_packer_does_not_split_normal_sentences_and_balances_chunks():
    sentences = (
        "First complete sentence explains the market signal clearly.",
        "Second complete sentence describes the policy mechanism without filler.",
        "Third complete sentence names the cross-asset consequence for readers.",
        "Fourth complete sentence states the confirmation condition precisely.",
    )
    chunks = pipeline._split_complete_chunks(sentences, limit=145)
    flattened = " ".join(chunks)
    assert all(sentence in flattened for sentence in sentences)
    assert all(chunk[-1] in ".!?" for chunk in chunks)
    assert all(len(chunk) <= 145 for chunk in chunks)
    assert min(map(len, chunks)) / max(map(len, chunks)) >= 0.45


def test_oil_thread_uses_actual_three_manifest_assets_once():
    canonical_url = "https://capitalchronicle.substack.com/p/eia-oil-forecast"
    payloads = build_native_derivative_payloads(
        article=_article(),
        selection=_selection(),
        canonical_url=canonical_url,
        media_asset_ids=["primary", "recent_price", "multi_year_range"],
    )
    for platform in ("x", "threads"):
        ids = [item for post in payloads[platform]["posts"] for item in post["media_asset_ids"]]
        assert ids == ["primary", "recent_price", "multi_year_range"]
        assert payloads[platform]["quality_metrics"]["visual_distribution_pass"] is True


def test_x_oil_thread_uses_complete_source_grounded_summaries_without_fake_sentences():
    canonical_url = "https://capitalchronicle.substack.com/p/eia-sees-oil-supply-nearing-pre-war-levels-as-hormuz-flows-resume"
    article = {
        "title": "EIA Sees Oil Supply Nearing Pre-War Levels as Hormuz Flows Resume",
        "subtitle": "The agency expects crude output and trade to recover near pre-conflict levels by year-end, shifting the market test from disruption to inventories and demand.",
        "social_lede": "EIA expects crude flows to approach pre-conflict levels by year-end.",
        "social_mechanism_summary": "Reopened Hormuz transit and restored output will test whether inventories rebuild and crude prices keep falling.",
        "social_policy_summary": "Cheaper gasoline can ease headline inflation without settling Federal Reserve policy.",
        "social_cross_asset_summary": "Lower oil can help energy importers while pressuring producer revenues.",
    }
    payload = build_native_derivative_payloads(
        article=article,
        selection=_selection(),
        canonical_url=canonical_url,
        media_asset_ids=["primary", "recent_price", "multi_year_range"],
    )["x"]
    public_text = "\n".join(post["text"] for post in payload["posts"])
    assert "shifting the." not in public_text
    assert "support large energy." not in public_text
    assert article["social_lede"] in public_text
    assert article["social_mechanism_summary"] in public_text
    assert article["social_policy_summary"] in public_text
    assert article["social_cross_asset_summary"] in public_text
    assert payload["quality_metrics"]["sentence_boundary_pass"] is True
    assert payload["quality_metrics"]["hard_character_slicing_used"] is False
    assert all(len(post["text"]) <= 280 for post in payload["posts"])


def test_social_summary_compiler_fails_closed_instead_of_word_slicing():
    oversized = "A deliberately oversized sentence " + "with unresolved context " * 20 + "."
    try:
        pipeline._concise_semantic_sentence(oversized, maximum=80)
    except ValueError as exc:
        assert str(exc) == "sentence_complete_semantic_summary_required"
    else:
        raise AssertionError("oversized sentence must not be converted into a fake complete sentence")


def test_prepare_only_release_candidate_never_calls_publishers(tmp_path: Path, monkeypatch):
    context = {
        "article": {**_article(), "canonical_url": "https://capitalchronicle.substack.com/p/eia-oil-forecast", "word_count": 800, "substack_body_markdown_sha256": "d" * 64},
        "selection": {**_selection(), "topic_hash": "topic", "duplicate_hotspot_decision": {"publish_allowed": True}},
        "media": {"assets": [
            {"asset_id": "primary", "sha256": "a" * 64},
            {"asset_id": "recent_price", "sha256": "b" * 64},
            {"asset_id": "multi_year_range", "sha256": "c" * 64},
        ]},
        "editorial_gate": {"combined_gate": {"classification": "PASS"}},
    }
    context_path = tmp_path / "run_context_v1.json"
    context_path.write_text(json.dumps(context), encoding="utf-8")
    for name in pipeline._RELEASE_PREPARATION_ARTIFACTS:
        path = tmp_path / name
        if path != context_path and name != "native_payloads_rehearsal_v1.json":
            path.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(pipeline, "browser_doctor", lambda: {"status": "READY_TO_ATTACH", "recommended_cdp_port": 9223})
    monkeypatch.setattr(
        pipeline,
        "_release_account_preflight",
        lambda _port: {
            "substack": {"authenticated": True},
            "x": {"authenticated": True, "destination_identity": "@Capitalnicle"},
            "linkedin": {"authenticated": True, "destination_identity": "linkedin:jimcc"},
            "youtube": {"authenticated": True},
        },
    )
    monkeypatch.setattr(
        pipeline,
        "_capability_presence",
        lambda: {name: True for name in ("telegram", "discord", "facebook_page", "instagram_business", "threads")},
    )
    monkeypatch.setattr(
        pipeline,
        "prepare_substack_first_pipeline",
        lambda **kwargs: {"classification": "READY_FOR_SUPERVISED_SUBSTACK_BROWSER_ASSIST", "context_path": str(context_path)},
    )
    monkeypatch.setattr(pipeline, "publish_substack_article_via_edge", lambda **kwargs: (_ for _ in ()).throw(AssertionError("no write")))
    packet = pipeline._prepare_text_image_release_candidate(run_id="rc-no-write", output_dir=tmp_path)
    assert packet["classification"] == "PASS_TEXT_IMAGE_RELEASE_CANDIDATE_REHEARSAL"
    assert packet["public_write_performed"] is False
    assert packet["publishing_adapter_called"] is False
    assert packet["video_or_tiktok_adapter_called"] is False
    assert pipeline._verify_release_candidate_lock(tmp_path)["status"] == "PASS_RELEASE_CANDIDATE_LOCK"

    (tmp_path / "article_manifest_v1.json").write_text('{"tampered":true}\n', encoding="utf-8")
    verification = pipeline._verify_release_candidate_lock(tmp_path)
    assert verification["status"] == "BLOCKED_RELEASE_CANDIDATE_LOCK"
    assert "locked_artifact_hash_mismatch:article_manifest_v1.json" in verification["blockers"]


def test_telegram_and_discord_require_strict_provider_readback(monkeypatch):
    import live_contentops.discord_live_adapter_v6 as discord_adapter
    import live_contentops.telegram_live_adapter_v6 as telegram_adapter

    canonical_url = "https://capitalchronicle.substack.com/p/eia-oil-supply"
    monkeypatch.setattr(pipeline, "load_public_dispatch_hashes", lambda _path: set())
    monkeypatch.setattr(pipeline, "append_public_dispatch_ledger", lambda **kwargs: None)
    monkeypatch.setattr(
        telegram_adapter,
        "execute_telegram_photo",
        lambda **kwargs: {
            "status": "SUCCESS",
            "id": "77",
            "response": {"result": {
                "message_id": 77,
                "chat": {"username": "CapitalChronicle"},
                "caption": kwargs["caption"],
                "photo": [{"file_id": "chart"}],
            }},
        },
    )
    telegram = pipeline._publish_telegram_photo_verified(
        run_id="rc-test",
        topic_hash="topic",
        text=f"Oil supply analysis {canonical_url}",
        canonical_url=canonical_url,
        image_path="C:/chart.png",
    )
    assert telegram["status"] == "SUCCESS"
    assert telegram["readback"]["meaningful_media_visible"] is True

    monkeypatch.setattr(
        discord_adapter,
        "execute_discord_post",
        lambda **kwargs: {
            "status": "SUCCESS",
            "id": "88",
            "response": {
                "id": "88",
                "channel_id": "22",
                "guild_id": "11",
                "content": kwargs["message"],
                "embeds": kwargs["embeds"],
            },
        },
    )
    discord = pipeline._publish_discord_verified(
        text=f"Oil supply analysis {canonical_url}",
        canonical_url=canonical_url,
        image_url="https://example.com/chart.png",
        title="Oil supply analysis",
    )
    assert discord["status"] == "SUCCESS"
    assert discord["readback"]["rich_preview_behavior"] == "article_chart"


def test_operator_audit_gate_requires_all_nine_strict_public_surfaces(tmp_path: Path, monkeypatch):
    canonical_url = "https://capitalchronicle.substack.com/p/eia-oil-supply"
    payloads = {
        platform: {"text": f"{platform} oil supply analysis {canonical_url}"}
        for platform in pipeline.TEXT_IMAGE_PASS_DESTINATIONS
        if platform != "substack"
    }
    (tmp_path / "native_payloads_v1.json").write_text(json.dumps(payloads), encoding="utf-8")
    (tmp_path / "idea_selection_v1.json").write_text(json.dumps({"rejected_alternatives": []}), encoding="utf-8")

    def result(platform: str) -> dict:
        return {
            "status": "SUCCESS",
            "id": f"{platform}-id",
            "public_url": f"https://example.com/{platform}",
            "destination_identity": f"{platform}-account",
            "substack_url_included": True,
            "provider_readback_verified": True,
            "media_asset_id": "primary",
            "media_sha256": "a" * 64,
            "readback": {
                "status": "SUCCESS",
                "visible_body_text": payloads.get(platform, {}).get("text"),
                "substack_url_visible": True,
                "meaningful_media_visible": True,
            },
        }

    results = {platform: result(platform) for platform in pipeline.TEXT_IMAGE_PASS_DESTINATIONS}
    results["substack"] = {
        "status": "SUCCESS",
        "draft_id": "1",
        "public_url": canonical_url,
        "readback": {
            "content_readback_verified": True,
            "public_image_count": 3,
            "public_image_alt_count": 3,
            "visual_spread_through_public_body": True,
            "visible_body_text": "Complete public oil article",
        },
    }
    x_replies = [
        {"id": f"x-reply-{index}", "public_url": f"https://example.com/x/reply/{index}", "text": f"X reply {index}"}
        for index in (1, 2)
    ]
    results["x"]["reply_chain"] = x_replies
    results["x"]["readback"].update({
        "root_visible_text": payloads["x"]["text"],
        "reply_chain_complete": True,
        "complete_article_visual_count": 3,
        "ordered_replies": [{"visible_body_text": row["text"]} for row in x_replies],
    })
    threads_replies = [
        {"id": f"threads-reply-{index}", "public_url": f"https://example.com/threads/reply/{index}", "text": f"Threads reply {index}"}
        for index in (1, 2)
    ]
    results["threads"]["reply_chain"] = threads_replies
    results["threads"]["readback"] = {
        "root": {"visible_body_text": payloads["threads"]["text"], "substack_url_visible": True, "meaningful_media_visible": True},
        "chain": {
            "provider_order_verified": True,
            "complete_article_visual_count": 3,
            "ordered_replies": [{"visible_body_text": row["text"]} for row in threads_replies],
        },
    }
    results["discord"]["readback"]["rich_preview_behavior"] = "article_chart"
    evidence = {
        "run_id": "rc-audit",
        "classification": "PASS_SUBSTACK_FIRST_TEXT_IMAGE_DISTRIBUTION_V1",
        "article": {"title": "EIA Oil Supply", "subtitle": "Supply is recovering.", "word_count": 700, "substack_body_markdown": "Complete article"},
        "selected_idea": {"topic": "EIA oil supply"},
        "editorial_gate": {"deterministic_review": {"editorial_score": 95, "seo_score": 100}},
        "delivery_media_manifest": {"assets": [{
            "media_asset_id": "primary",
            "sha256": "a" * 64,
            "absolute_local_source_path": str(tmp_path / "chart.png"),
            "source_provenance": {"caption": "WTI chart"},
        }]},
        "results": results,
    }
    (tmp_path / "run_evidence_v1.json").write_text(json.dumps(evidence), encoding="utf-8")

    def capture(**kwargs):
        target = Path(kwargs["output_path"])
        if "telegram_root" in target.name:
            raise RuntimeError("simulated t.me DNS failure")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"png")
        return {"status": "SUCCESS", "public_url": kwargs["public_url"], "public_screenshot_path": str(target), "browser_write_performed": False}

    monkeypatch.setattr(pipeline, "capture_public_destination_screenshot_via_edge", capture)
    packet = pipeline._build_operator_manual_audit_packet(output_dir=tmp_path)
    assert packet["classification"] == "AWAITING_OPERATOR_MANUAL_AUDIT_TEXT_IMAGE_V1_0_RC"
    assert packet["machine_qa"]["status"] == "PASS"
    assert packet["screenshots"]["telegram"][0]["status"] == "NOT_APPLICABLE_PUBLIC_DNS_UNAVAILABLE_PROVIDER_READBACK_VERIFIED"
    assert len(packet["screenshots"]["x"]) == 3
    assert len(packet["screenshots"]["threads"]) == 3


def test_classification_requires_every_expanded_destination_for_pass():
    results = {platform: {"status": "SUCCESS"} for platform in EXPECTED_DESTINATIONS}
    assert _classification(results) == "PASS_SUBSTACK_FIRST_TEXT_IMAGE_DISTRIBUTION_V1"
    results["tiktok"] = {"status": "BLOCKED_TIKTOK_LOGIN_REQUIRED"}
    assert _classification(results) == "PASS_SUBSTACK_FIRST_TEXT_IMAGE_DISTRIBUTION_V1"
    results["youtube"] = {"status": "BLOCKED_YOUTUBE_COMMUNITY_NOT_AVAILABLE"}
    assert _classification(results) == "PARTIAL_EIGHT_PLATFORM_FULL_CONTENTOPS_LIVE_RUN_V1"
    results["substack"] = {"status": "FAILED_SUBSTACK_PUBLIC_URL_READBACK"}
    assert _classification(results) == "FAILED_EIGHT_PLATFORM_FULL_CONTENTOPS_LIVE_RUN_V1"


def test_substack_draft_id_readback_uses_exact_read_only_resolver(
    monkeypatch, tmp_path
):
    expected_title = "Deutsche becomes European clearing bank for RMB"
    seen = {}
    monkeypatch.setattr(
        pipeline,
        "_durable_intent_inputs",
        lambda _intent: {
            "output_dir": tmp_path,
            "article": {
                "title": expected_title,
                "subtitle": "A source-backed banking update.",
                "substack_body_markdown": "The FT reported the banking update.",
            },
            "payloads": {"substack": {"text": ""}},
            "canonical_url": "",
            "local_media": "",
            "media_assets": [],
        },
    )

    def reconcile(**kwargs):
        seen.update(kwargs)
        return {
            "status": "SUBSTACK_DRAFT_CONFIRMED_NOT_PUBLIC",
            "verified": False,
            "write_absent": True,
            "public_object_id": kwargs["draft_id"],
            "browser_write_performed": False,
        }

    monkeypatch.setattr(
        pipeline, "reconcile_substack_publication_by_draft_id_via_edge", reconcile
    )

    result = pipeline._readback_one_destination_from_durable_intent(
        destination="substack",
        public_object_id="210796285",
        public_object_url=None,
        intent={"output_dir": str(tmp_path)},
    )

    assert seen["draft_id"] == "210796285"
    assert seen["expected_title"] == expected_title
    assert seen["expected_image_assets"] == []
    assert result["status"] == "SUBSTACK_DRAFT_CONFIRMED_NOT_PUBLIC"
    assert result["verified"] is False
    assert result["write_absent"] is True
    assert result["public_object_id"] == "210796285"


def test_text_only_substack_readback_preserves_delivery_only_manifest(
    monkeypatch, tmp_path
):
    existing = {
        "status": "PASS",
        "assets": [
            {
                "media_asset_id": "delivery_only_editorial_card",
                "media_role": "delivery_only",
                "local_public_hash_continuity": True,
                "verified_public_delivery_url": "https://res.cloudinary.com/example/card.png",
            }
        ],
    }
    manifest_path = tmp_path / "delivery_media_manifest_v1.json"
    manifest_path.write_text(json.dumps(existing), encoding="utf-8")
    monkeypatch.setattr(
        pipeline,
        "_durable_intent_inputs",
        lambda _intent: {
            "output_dir": tmp_path,
            "article": {
                "title": "Exact title",
                "subtitle": "Exact subtitle",
                "substack_body_markdown": "Exact body",
            },
            "payloads": {"substack": {"text": ""}},
            "canonical_url": "https://capitalchronicle.substack.com/p/exact",
            "local_media": "",
            "delivery_local_media": "",
            "media_assets": [],
            "primary_media": existing["assets"][0],
        },
    )
    monkeypatch.setattr(
        pipeline,
        "audit_public_substack_article_via_edge",
        lambda **_kwargs: {
            "status": "SUCCESS",
            "post_id": "123",
            "public_url": "https://capitalchronicle.substack.com/p/exact",
            "readback": {"public_image_urls": ["https://substackcdn.example/old.png"]},
        },
    )

    pipeline._readback_one_destination_from_durable_intent(
        destination="substack",
        public_object_id="123",
        public_object_url="https://capitalchronicle.substack.com/p/exact",
        intent={"output_dir": str(tmp_path)},
    )

    assert json.loads(manifest_path.read_text(encoding="utf-8")) == existing


def test_substack_transport_attempt_persists_only_sanitized_transition_facts(
    monkeypatch, tmp_path
):
    publish_call = {}
    monkeypatch.setattr(
        pipeline,
        "_durable_intent_inputs",
        lambda _intent: {
            "output_dir": tmp_path,
            "article": {
                "title": "Exact governed title",
                "subtitle": "Exact governed subtitle",
                "substack_body_markdown": "Governed body.",
            },
            "payloads": {"substack": {"text": "must never be persisted"}},
            "canonical_url": "",
            "local_media": "",
            "public_image_url": "",
            "media_assets": [],
        },
    )
    def publish_substack(**kwargs):
        publish_call.update(kwargs)
        return {
            "status": "UNKNOWN_SUBSTACK_PUBLISH_CONTROL_CLICK_FAILED",
            "draft_id": "210865567",
            "public_write_attempted": True,
            "browser_write_performed": True,
            "payload": "must never be persisted",
            "raw_error": "secret-bearing diagnostic must never be persisted",
            "transition_stages": [
                {
                    "stage": "PUBLISH_SETTINGS",
                    "control_label": "Send to everyone now",
                    "outcome": "CLICK_FAILED",
                    "error_class": "TimeoutError",
                    "raw_error": "must never be persisted",
                }
            ],
        }

    monkeypatch.setattr(pipeline, "publish_substack_article_via_edge", publish_substack)

    result = pipeline._publish_one_destination_from_durable_intent(
        destination="substack",
        intent={
            "attempt_identity": "dispatch-1",
            "output_dir": str(tmp_path),
            "recovery_public_object_id": "210865567",
        },
        authorization_context={
            "operating_mode": "AUTONOMOUS_DEFAULT",
            "dispatch_attempt_identity": "dispatch-1",
        },
    )

    assert result["status"] == "UNKNOWN_SUBSTACK_PUBLISH_CONTROL_CLICK_FAILED"
    assert publish_call["existing_draft_id"] == "210865567"
    packet = json.loads(
        (tmp_path / "transport_attempt_substack_v1.json").read_text(encoding="utf-8")
    )
    assert packet["draft_id"] == "210865567"
    assert packet["public_write_attempted"] is True
    assert packet["browser_write_performed"] is True
    assert packet["transition_stages"] == [
        {
            "control_label": "Send to everyone now",
            "error_class": "TimeoutError",
            "outcome": "CLICK_FAILED",
            "stage": "PUBLISH_SETTINGS",
        }
    ]
    serialized = json.dumps(packet, sort_keys=True)
    assert "must never be persisted" not in serialized
    assert packet["payload_persisted"] is False
    assert packet["browser_session_material_persisted"] is False
    assert packet["raw_error_text_persisted"] is False


def test_default_youtube_path_cannot_call_video_or_short_adapter():
    runner_source = inspect.getsource(pipeline._run_eight_platform_substack_first_pipeline)
    resume_source = inspect.getsource(pipeline._resume_eight_platform_derivatives)

    assert "publish_youtube_short_via_edge" not in runner_source + resume_source
    assert "build_source_chart_short_video" not in runner_source + resume_source
    assert not hasattr(pipeline, "publish_youtube_short_via_edge")
    assert not hasattr(pipeline, "build_source_chart_short_video")


def test_linkedin_success_gate_requires_text_image_url_permalink_and_readback():
    canonical_url = "https://capitalchronicle.substack.com/p/example"
    payload = f"Strong opening.\n\nPolicy transmission and curve context.\n\n{canonical_url}"
    image_only = pipeline._safe_provider_result(
        {
            "status": "SUCCESS",
            "action": "edit_existing_post",
            "public_url": "https://www.linkedin.com/feed/update/urn:li:activity:123/",
            "post_id": "123",
            "provider_readback_verified": True,
            "readback": {
                "public_url": "https://www.linkedin.com/feed/update/urn:li:activity:123/",
                "body_text_visible": False,
                "meaningful_media_visible": True,
                "substack_url_visible": False,
            },
        },
        platform="linkedin",
        payload=payload,
        canonical_url=canonical_url,
        media_attached=True,
    )
    complete = pipeline._safe_provider_result(
        {
            "status": "SUCCESS",
            "action": "edit_existing_post",
            "public_url": "https://www.linkedin.com/feed/update/urn:li:activity:123/",
            "post_id": "123",
            "provider_readback_verified": True,
            "readback": {
                "public_url": "https://www.linkedin.com/feed/update/urn:li:activity:123/",
                "body_text_visible": True,
                "meaningful_media_visible": True,
                "substack_url_visible": True,
            },
        },
        platform="linkedin",
        payload=payload,
        canonical_url=canonical_url,
        media_attached=True,
    )

    assert image_only["status"] == "FAILED_LINKEDIN_STRICT_READBACK"
    assert image_only["provider_readback_verified"] is False
    assert complete["status"] == "SUCCESS"
    assert complete["provider_readback_verified"] is True


def test_uncertain_write_readback_is_never_retried_automatically(tmp_path: Path):
    ledger = tmp_path / "dispatch.jsonl"
    calls = 0

    def uncertain_executor() -> dict:
        nonlocal calls
        calls += 1
        return {"status": "FAILED_X_PERMALINK_READBACK", "platform": "x", "action": "post"}

    first = _dispatch_once(
        ledger_path=ledger,
        platform="x",
        payload="Source-backed note https://capitalchronicle.substack.com/p/example",
        canonical_url="https://capitalchronicle.substack.com/p/example",
        media_attached=True,
        executor=uncertain_executor,
    )
    second = _dispatch_once(
        ledger_path=ledger,
        platform="x",
        payload="Source-backed note https://capitalchronicle.substack.com/p/example",
        canonical_url="https://capitalchronicle.substack.com/p/example",
        media_attached=True,
        executor=uncertain_executor,
    )

    assert first["status"] == "FAILED_X_PERMALINK_READBACK"
    assert second["status"] == "FAILED_X_PERMALINK_READBACK"
    assert second["automatic_retry_blocked"] is True
    assert calls == 1

    payload_hash = first["payload_sha256"]
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "platform": "x",
                    "payload_sha256": payload_hash,
                    "success": True,
                    "status": "SUCCESS_RECONCILED_PUBLIC_READBACK",
                    "action": "post",
                    "id": "123",
                    "public_url": "https://x.com/Capitalnicle/status/123",
                    "media_attached": True,
                    "substack_url_included": True,
                    "write_outcome_certainty": "reconciled",
                }
            )
            + "\n"
        )
    third = _dispatch_once(
        ledger_path=ledger,
        platform="x",
        payload="Source-backed note https://capitalchronicle.substack.com/p/example",
        canonical_url="https://capitalchronicle.substack.com/p/example",
        media_attached=True,
        executor=uncertain_executor,
    )

    assert third["status"] == "ALREADY_SUCCESSFUL_IDEMPOTENT"
    assert third["public_url"] == "https://x.com/Capitalnicle/status/123"
    assert calls == 1


def test_existing_run_evidence_prevents_duplicate_substack_publication(tmp_path: Path, monkeypatch):
    evidence = {
        "classification": "PARTIAL_EIGHT_PLATFORM_FULL_CONTENTOPS_LIVE_RUN_V1",
        "run_id": "existing-live-run",
        "results": {"substack": {"status": "SUCCESS", "public_url": "https://capitalchronicle.substack.com/p/example"}},
    }
    (tmp_path / "run_evidence_v1.json").write_text(json.dumps(evidence), encoding="utf-8")
    monkeypatch.setattr(pipeline, "browser_doctor", lambda: (_ for _ in ()).throw(AssertionError("browser must not be opened")))
    monkeypatch.setattr(pipeline, "publish_substack_article_via_edge", lambda **kwargs: (_ for _ in ()).throw(AssertionError("canonical publisher must not run")))

    result = pipeline._run_eight_platform_substack_first_pipeline(
        run_id="existing-live-run",
        output_dir=tmp_path,
    )

    assert result["results"]["substack"]["public_url"] == "https://capitalchronicle.substack.com/p/example"
    assert result["reentry_guard"] == "existing_run_evidence_detected_no_automatic_canonical_republish"


def test_linkedin_pair_reconciliation_edits_exact_latest_without_third_post(tmp_path: Path, monkeypatch):
    canonical_url = "https://capitalchronicle.substack.com/p/example"
    chart_path = tmp_path / "chart.png"
    chart_path.write_bytes(b"chart")
    evidence = {
        "run_id": "pair-run",
        "article": _article(),
        "selected_idea": _selection(),
        "media": {"assets": [{"path": str(chart_path)}]},
        "results": {"substack": {"status": "SUCCESS", "public_url": canonical_url, "readback": {"public_image_urls": ["https://example.com/chart.png"]}}},
        "superseded_malformed_posts": {"linkedin_unintended_replacement": {"id": "222", "status": "SUPERSEDED_IMAGE_ONLY"}},
    }
    (tmp_path / "run_evidence_v1.json").write_text(json.dumps(evidence), encoding="utf-8")
    media = {"media_asset_id": "primary", "absolute_local_source_path": str(chart_path), "sha256": "a" * 64}
    monkeypatch.setattr(pipeline, "build_delivery_media_manifest", lambda **kwargs: {"status": "PASS", "assets": [media]})
    monkeypatch.setattr(pipeline, "select_primary_chart", lambda manifest: dict(media))
    reads = iter([
        {"status": "SUCCESS", "post_id": "111", "public_url": "https://www.linkedin.com/feed/update/urn:li:activity:111/"},
        {"status": "MALFORMED_EXISTING_POST_REQUIRES_EDIT", "post_id": "222", "public_url": "https://www.linkedin.com/feed/update/urn:li:activity:222/"},
    ])
    monkeypatch.setattr(pipeline, "readback_linkedin_activity_via_edge", lambda **kwargs: next(reads))
    monkeypatch.setattr(
        pipeline,
        "edit_existing_linkedin_post_via_edge",
        lambda **kwargs: {
            "status": "SUCCESS",
            "readback": {"status": "SUCCESS", "body_text_visible": True, "meaningful_media_visible": True, "substack_url_visible": True},
        },
    )
    monkeypatch.setattr(pipeline, "publish_linkedin_post_via_edge", lambda **kwargs: (_ for _ in ()).throw(AssertionError("third root forbidden")))
    packet = pipeline._reconcile_linkedin_activity_pair(
        output_dir=tmp_path,
        cdp_port=9223,
        accepted_url="https://www.linkedin.com/feed/update/urn:li:activity:111/",
        accepted_id="111",
        latest_url="https://www.linkedin.com/feed/update/urn:li:activity:222/",
        latest_id="222",
    )
    assert packet["classification"] == "PASS_LINKEDIN_PAIR_RECONCILED"
    assert packet["third_post_created"] is False
    assert packet["publish_adapter_called"] is False
    assert packet["relationship"] == "EARLIER_ACCEPTED_AND_LATEST_CORRECTED_IN_PLACE"
    updated = json.loads((tmp_path / "run_evidence_v1.json").read_text(encoding="utf-8"))
    assert updated["results"]["linkedin"]["id"] == "222"
    assert "linkedin_unintended_replacement" not in updated["superseded_malformed_posts"]


def test_compile_variant_reliability_evidence_is_no_write_and_three_media(tmp_path: Path, monkeypatch):
    canonical_url = "https://capitalchronicle.substack.com/p/example"
    evidence = {
        "run_id": "variant-audit",
        "article": _article(),
        "selected_idea": _selection(),
        "media": {"assets": [
            {"asset_id": "primary"},
            {"asset_id": "policy_corridor"},
            {"asset_id": "sofr_context"},
        ]},
        "results": {"substack": {"status": "SUCCESS", "public_url": canonical_url}},
    }
    (tmp_path / "run_evidence_v1.json").write_text(json.dumps(evidence), encoding="utf-8")
    monkeypatch.setattr(pipeline, "publish_x_post_via_edge", lambda **kwargs: (_ for _ in ()).throw(AssertionError("no X write")))
    monkeypatch.setattr(pipeline, "publish_substack_article_via_edge", lambda **kwargs: (_ for _ in ()).throw(AssertionError("no canonical write")))
    packet = pipeline.compile_variant_reliability_evidence(output_dir=tmp_path)
    assert packet["classification"] == "PASS_SEMANTIC_VARIANT_RELIABILITY"
    assert packet["public_write_performed"] is False
    assert packet["live_outputs_modified"] is False
    for platform in ("x", "threads"):
        metrics = packet["planned_layouts"][platform]["quality_metrics"]
        assert metrics["reply_count"] == 2
        assert metrics["complete_article_visual_count"] == 3


def test_derivative_only_resume_preserves_successful_destinations(tmp_path: Path, monkeypatch):
    canonical_url = "https://capitalchronicle.substack.com/p/example"
    chart_path = tmp_path / "chart.png"
    chart_path.write_bytes(b"chart")
    successful_x = {"status": "SUCCESS", "id": "x-123", "public_url": "https://x.com/Capitalnicle/status/123"}
    results = {platform: {"status": "SUCCESS", "id": f"{platform}-id"} for platform in EXPECTED_DESTINATIONS}
    results["substack"] = {"status": "SUCCESS", "draft_id": "206418070", "public_url": canonical_url}
    results["x"] = dict(successful_x)
    results["linkedin"] = {"status": "FAILED_LINKEDIN_MEDIA_UPLOAD"}
    results["tiktok"] = {"status": "BLOCKED_TIKTOK_LOGIN_REQUIRED"}
    evidence = {
        "classification": "PARTIAL_EIGHT_PLATFORM_FULL_CONTENTOPS_LIVE_RUN_V1",
        "run_id": "resume-live-run",
        "article": _article(),
        "selected_idea": _selection(),
        "media": {"assets": [{"path": str(chart_path)}]},
        "results": results,
    }
    (tmp_path / "run_evidence_v1.json").write_text(json.dumps(evidence), encoding="utf-8")
    calls = []
    monkeypatch.setattr(pipeline, "browser_doctor", lambda: {"status": "READY_TO_ATTACH", "recommended_cdp_port": 9223})
    approved_media = {
        "media_asset_id": "primary",
        "media_role": "primary_chart",
        "absolute_local_source_path": str(chart_path),
        "sha256": "a" * 64,
        "verified_public_delivery_url": "https://example.com/chart.png",
    }
    monkeypatch.setattr(pipeline, "build_delivery_media_manifest", lambda **kwargs: {"status": "PASS", "assets": [approved_media]})
    monkeypatch.setattr(pipeline, "select_primary_chart", lambda manifest: dict(approved_media))
    monkeypatch.setattr(
        pipeline,
        "reconcile_existing_linkedin_post_via_edge",
        lambda **kwargs: {
            "status": "MALFORMED_EXISTING_POST_REQUIRES_EDIT",
            "post_id": "123",
            "public_url": "https://www.linkedin.com/feed/update/urn:li:activity:123/",
            "meaningful_media_visible": True,
            "chart_similarity_score": 0.99,
        },
    )
    monkeypatch.setattr(
        pipeline,
        "readback_linkedin_post_via_edge",
        lambda **kwargs: {"status": "FAILED_LINKEDIN_POST_NOT_FOUND"},
    )
    monkeypatch.setattr(
        pipeline,
        "edit_existing_linkedin_post_via_edge",
        lambda **kwargs: calls.append(kwargs)
        or {
            "status": "SUCCESS",
            "platform": "linkedin",
            "action": "edit_existing_post",
            "public_url": "https://www.linkedin.com/feed/update/urn:li:activity:123/",
            "post_id": "123",
            "destination_identity": "linkedin:jimcc",
            "media_transfer": {"upload_transport": "preserved_existing_media_no_reupload"},
            "provider_readback_verified": True,
            "readback": {
                "status": "SUCCESS",
                "public_url": "https://www.linkedin.com/feed/update/urn:li:activity:123/",
                "body_text_visible": True,
                "meaningful_media_visible": True,
                "substack_url_visible": True,
            },
        },
    )
    monkeypatch.setattr(pipeline, "publish_linkedin_post_via_edge", lambda **kwargs: (_ for _ in ()).throw(AssertionError("must edit existing post, not create")))
    monkeypatch.setattr(pipeline, "publish_substack_article_via_edge", lambda **kwargs: (_ for _ in ()).throw(AssertionError("canonical publisher must not run")))

    resumed = pipeline._resume_eight_platform_derivatives(
        output_dir=tmp_path,
        cdp_port=9223,
        platforms=["linkedin"],
    )

    assert resumed["results"]["x"] == successful_x
    assert resumed["results"]["linkedin"]["status"] == "SUCCESS"
    assert resumed["results"]["linkedin"]["media_upload_transport"] == "preserved_existing_media_no_reupload"
    assert resumed["results"]["substack"]["draft_id"] == "206418070"
    assert resumed["derivative_resume"]["canonical_republished"] is False
    assert resumed["derivative_resume"]["substack_adapter_called"] is False
    assert resumed["derivative_resume"]["successful_destinations_frozen"] is True
    assert resumed["derivative_resume"]["targets"] == ["linkedin"]
    assert len(calls) == 1
    ledger = [json.loads(line) for line in (tmp_path / "platform_dispatch_ledger_v1.jsonl").read_text(encoding="utf-8").splitlines()]
    assert ledger[-1]["idempotency_scope"] == "edit_existing_post:123"
    assert ledger[-1]["action"] == "edit_existing_post"


def test_youtube_correction_records_wrong_short_and_uses_community_adapter_only(tmp_path: Path, monkeypatch):
    canonical_url = "https://capitalchronicle.substack.com/p/example"
    chart_path = tmp_path / "chart.png"
    chart_path.write_bytes(b"chart")
    results = {platform: {"status": "SUCCESS", "id": f"{platform}-id"} for platform in EXPECTED_DESTINATIONS}
    results["substack"] = {"status": "SUCCESS", "draft_id": "206418070", "public_url": canonical_url}
    results["tiktok"] = {"status": "BLOCKED_TIKTOK_LOGIN_REQUIRED"}
    results["youtube"] = {
        "status": "SUCCESS",
        "action": "public_short",
        "id": "FvasNsZ1F2U",
        "public_url": "https://www.youtube.com/watch?v=FvasNsZ1F2U",
    }
    evidence = {
        "classification": "PARTIAL_EIGHT_PLATFORM_FULL_CONTENTOPS_LIVE_RUN_V1",
        "run_id": "resume-live-run",
        "article": _article(),
        "selected_idea": _selection(),
        "media": {"assets": [{"path": str(chart_path)}]},
        "results": results,
    }
    (tmp_path / "run_evidence_v1.json").write_text(json.dumps(evidence), encoding="utf-8")
    calls = []
    monkeypatch.setattr(pipeline, "browser_doctor", lambda: {"status": "READY_TO_ATTACH", "recommended_cdp_port": 9223})
    approved_media = {
        "media_asset_id": "primary",
        "media_role": "primary_chart",
        "absolute_local_source_path": str(chart_path),
        "sha256": "a" * 64,
        "verified_public_delivery_url": "https://example.com/chart.png",
    }
    monkeypatch.setattr(pipeline, "build_delivery_media_manifest", lambda **kwargs: {"status": "PASS", "assets": [approved_media]})
    monkeypatch.setattr(pipeline, "select_primary_chart", lambda manifest: dict(approved_media))
    monkeypatch.setattr(
        pipeline,
        "publish_youtube_community_post_via_edge",
        lambda **kwargs: calls.append(kwargs)
        or {
            "status": "SUCCESS",
            "platform": "youtube",
            "action": "community_post",
            "post_id": "UgkxCommunity123",
            "public_url": "https://www.youtube.com/post/UgkxCommunity123",
            "destination_identity": "@CapitalChronicleYouTube",
            "media_transfer": {"upload_transport": "playwright_file_chooser"},
            "provider_readback_verified": True,
            "readback": {
                "status": "SUCCESS",
                "public_url": "https://www.youtube.com/post/UgkxCommunity123",
                "body_text_visible": True,
                "meaningful_media_visible": True,
                "substack_url_visible": True,
                "channel_identity_verified": True,
            },
        },
    )
    monkeypatch.setattr(pipeline, "publish_substack_article_via_edge", lambda **kwargs: (_ for _ in ()).throw(AssertionError("canonical publisher must not run")))

    resumed = pipeline._resume_eight_platform_derivatives(
        output_dir=tmp_path,
        cdp_port=9223,
        platforms=["youtube"],
    )

    assert resumed["classification"] == "PASS_SUBSTACK_FIRST_TEXT_IMAGE_DISTRIBUTION_V1"
    assert resumed["results"]["youtube"]["action"] == "community_post"
    assert resumed["results"]["youtube"]["public_url"] == "https://www.youtube.com/post/UgkxCommunity123"
    assert resumed["wrong_surface_executions"]["youtube"]["status"] == "WRONG_SURFACE_EXECUTION_NOT_ACCEPTED"
    assert resumed["wrong_surface_executions"]["youtube"]["public_url"].endswith("FvasNsZ1F2U")
    assert resumed["derivative_resume"]["youtube_video_or_short_adapter_called"] is False
    assert len(calls) == 1
    ledger = [json.loads(line) for line in (tmp_path / "platform_dispatch_ledger_v1.jsonl").read_text(encoding="utf-8").splitlines()]
    assert ledger[-1]["idempotency_scope"] == "youtube_community_post"
    assert ledger[-1]["action"] == "community_post"
