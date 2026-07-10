import json
import inspect
from pathlib import Path

import live_contentops.eight_platform_substack_first_pipeline_v1 as pipeline
from live_contentops.eight_platform_substack_first_pipeline_v1 import (
    EXPECTED_DESTINATIONS,
    _classification,
    _dispatch_once,
    build_native_derivative_payloads,
)


def _article() -> dict:
    return {"title": "Effective Fed Funds Rate Holds at 3.62% as Policy Calibration Continues", "subtitle": "FRED's latest reading keeps the policy-transmission question in focus."}


def _selection() -> dict:
    return {
        "dek": "FRED's latest effective federal funds reading keeps the policy-transmission question in focus.",
        "market_mechanism": "Funding conditions move through administered rates, the curve, credit, and discount-rate expectations.",
        "policy_context": "Policy communication frames the short end while the curve absorbs growth and inflation uncertainty.",
        "cross_asset_implications": "Cross-asset moves can reflect different repricing channels rather than one simple market verdict.",
    }


def test_native_payloads_are_distinct_and_carry_canonical_url():
    canonical_url = "https://capitalchronicle.substack.com/p/effective-fed-funds-rate-policy-calibration"
    payloads = build_native_derivative_payloads(article=_article(), selection=_selection(), canonical_url=canonical_url)
    assert canonical_url in payloads["x"]["text"]
    assert canonical_url in payloads["linkedin"]["text"]
    assert canonical_url in payloads["discord"]["text"]
    assert canonical_url in payloads["youtube"]["text"]
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


def test_classification_requires_every_expanded_destination_for_pass():
    results = {platform: {"status": "SUCCESS"} for platform in EXPECTED_DESTINATIONS}
    assert _classification(results) == "PASS_SUBSTACK_FIRST_TEXT_IMAGE_DISTRIBUTION_V1"
    results["tiktok"] = {"status": "BLOCKED_TIKTOK_LOGIN_REQUIRED"}
    assert _classification(results) == "PASS_SUBSTACK_FIRST_TEXT_IMAGE_DISTRIBUTION_V1"
    results["youtube"] = {"status": "BLOCKED_YOUTUBE_COMMUNITY_NOT_AVAILABLE"}
    assert _classification(results) == "PARTIAL_EIGHT_PLATFORM_FULL_CONTENTOPS_LIVE_RUN_V1"
    results["substack"] = {"status": "FAILED_SUBSTACK_PUBLIC_URL_READBACK"}
    assert _classification(results) == "FAILED_EIGHT_PLATFORM_FULL_CONTENTOPS_LIVE_RUN_V1"


def test_default_youtube_path_cannot_call_video_or_short_adapter():
    runner_source = inspect.getsource(pipeline.run_eight_platform_substack_first_pipeline)
    resume_source = inspect.getsource(pipeline.resume_eight_platform_derivatives)

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

    result = pipeline.run_eight_platform_substack_first_pipeline(
        run_id="existing-live-run",
        output_dir=tmp_path,
    )

    assert result["results"]["substack"]["public_url"] == "https://capitalchronicle.substack.com/p/example"
    assert result["reentry_guard"] == "existing_run_evidence_detected_no_automatic_canonical_republish"


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

    resumed = pipeline.resume_eight_platform_derivatives(
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

    resumed = pipeline.resume_eight_platform_derivatives(
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
