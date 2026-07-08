import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from live_contentops.live_production_pipeline_runner_v6 import (
    run_live_production_pipeline,
    _dispatch_summary,
    _normalize_dispatch_result,
    _apply_canonical_link,
    _instagram_image_candidates,
    _fit_telegram_photo_caption,
    _telegram_photo_delivery_evidence,
    _expected_substack_visual_placements,
    audit_substack_public_visuals,
    resolve_substack_public_url,
)
from live_contentops.public_dispatch_freeze_guard_v6 import (
    build_public_dispatch_payload_hash,
    build_public_dispatch_topic_hash,
    make_public_dispatch_approval_marker,
)


@pytest.fixture(autouse=True)
def _clear_contentops_public_dispatch_env(monkeypatch):
    monkeypatch.delenv("CONTENTOPS_CANONICAL_URL_OVERRIDE", raising=False)
    monkeypatch.delenv("CONTENTOPS_PUBLIC_IMAGE_URL_OVERRIDE", raising=False)


def _approved_article_packet() -> dict:
    intro = (
        "The current WTI evidence gives the recession-risk debate a fresh starting point. "
        "WTI crude was reported at $71.87 per barrel on 2026-06-29, and the 90-day move "
        "helps frame the energy channel without turning one chart into a cycle call."
    )
    sections = [
        {"title": "Why Now: Current Oil Evidence", "body": "FRED DCOILWTICO and EIA source rows support the current oil endpoint."},
        {"title": "Transmission Channels", "body": "Oil volatility can affect transport costs, real income, and inflation expectations."},
        {"title": "Rates and Recession Context", "body": "Federal Reserve and Treasury sources support the rates context rather than the oil chart."},
        {"title": "Limits and Counterargument", "body": "The counterargument is that oil volatility alone does not prove a recession."},
        {"title": "What to Watch Next", "body": "Watch inflation releases, policy communication, energy inventory data, and Treasury yield updates."},
    ]
    draft = {
        "title": "Oil Volatility Is Rising; Recession Risk Needs a Cleaner Evidence Map",
        "subtitle": "A source-led macro briefing on WTI, policy limits, and recession-risk evidence.",
        "slug_candidate": "oil-volatility-recession-risk-evidence-map",
        "dek": "Current WTI data help explain why oil volatility belongs in recession-risk analysis without turning one chart into a cycle call.",
        "meta_description": "Capital Chronicle maps current WTI oil volatility, recession-risk channels, source limits, and what to watch next.",
        "thesis": "Current oil volatility belongs in a recession-risk dashboard, but the thesis needs source-backed limits.",
        "intro": intro,
        "sections": sections,
        "conclusion": "The evidence supports monitoring oil volatility while keeping the recession conclusion bounded.",
        "citations": [
            "https://fred.stlouisfed.org/series/DCOILWTICO",
            "https://www.eia.gov/dnav/pet/pet_pri_spt_s1_d.htm",
            "https://www.federalreserve.gov/monetarypolicy.htm",
            "https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics",
        ],
        "source_notes_for_operator": "FRED, EIA, Federal Reserve, and Treasury sources support the article claims.",
        "source_trail": [
            {"label": "FRED DCOILWTICO", "publisher_or_origin": "FRED / EIA", "url": "https://fred.stlouisfed.org/series/DCOILWTICO", "claim_supported": "WTI latest observation and 90-day price comparison."},
            {"label": "EIA petroleum prices", "publisher_or_origin": "U.S. Energy Information Administration", "url": "https://www.eia.gov/dnav/pet/pet_pri_spt_s1_d.htm", "claim_supported": "Underlying petroleum source for WTI spot price observations."},
            {"label": "Federal Reserve policy context", "publisher_or_origin": "Federal Reserve", "url": "https://www.federalreserve.gov/monetarypolicy.htm", "claim_supported": "Policy transmission context."},
            {"label": "Treasury rates context", "publisher_or_origin": "U.S. Treasury", "url": "https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics", "claim_supported": "Yield and rates context."},
        ],
        "visual_slots": [{"asset_id": "primary"}, {"asset_id": "recent_price"}, {"asset_id": "hormuz_context"}],
    }
    return {
        "packet_id": "art_test_packet_123",
        "source_context_packet": {"operator_idea": "US recession risks rise as oil volatility spikes"},
        "canonical_article_draft": draft,
        "seo_packet": {"target_keyword": "oil volatility recession risk", "meta_description": draft["meta_description"]},
        "blockers": [],
    }


def _approval_marker_for_run(
    *,
    topic: str,
    angle: str,
    run_id: str,
    telegram_action: str | None = None,
    telegram_body: str | None = None,
    canonical_url: str | None = None,
    telegram_media: str | None = None,
) -> dict:
    topic_hash = build_public_dispatch_topic_hash(topic, angle)
    payload_hash = None
    if telegram_action and telegram_body is not None:
        payload_hash = build_public_dispatch_payload_hash(
            platform="telegram",
            action=telegram_action,
            body_text=telegram_body,
            canonical_url=canonical_url,
            media_url=telegram_media,
            topic_hash=topic_hash,
        )
    return make_public_dispatch_approval_marker(
        run_id=run_id,
        topic_hash=topic_hash,
        payload_hash=payload_hash,
        platform="telegram" if payload_hash else None,
    )


@patch("live_contentops.live_production_pipeline_runner_v6.run_article_engine")
@patch("live_contentops.live_production_pipeline_runner_v6.generate_live_platform_variants")
def test_run_live_production_pipeline(mock_generate_variants, mock_run_article, tmp_path):
    mock_run_article.return_value = {
        "packet_id": "art_test_packet_123",
        "canonical_article_draft": {"title": "Test Title"}
    }
    
    mock_generate_variants.return_value = {
        "platform_variant_packet_id": "var_test_packet_456",
        "image_path": "downloads/test_image.jpg",
        "variant_status": "VARIANT_SCAFFOLD_READY"
    }
    
    # Override output paths for test isolation
    test_article_path = tmp_path / "canonical_article_packet.json"
    audit_path = tmp_path / "latest_dispatch_audit.json"
    
    with patch("live_contentops.live_production_pipeline_runner_v6.ARTICLE_OUTPUT_PATH", test_article_path),          patch("live_contentops.live_production_pipeline_runner_v6.DISPATCH_AUDIT_PATH", audit_path):
        result = run_live_production_pipeline(
            topic="Yield rates drop",
            editorial_angle="No advice",
            live_run=False,
            timeout_seconds=42
        )
        
        assert result["article_packet_id"] == "art_test_packet_123"
        assert result["platform_variant_packet_id"] == "var_test_packet_456"
        assert result["image_path"] == "downloads/test_image.jpg"
        assert result["variant_status"] == "VARIANT_SCAFFOLD_READY"
        assert result["editorial_acceptance_status"] == "EDITORIAL_BLOCKED"
        assert result["tier1_editorial_approved"] is False
        
        assert test_article_path.exists()
        saved_data = json.loads(test_article_path.read_text(encoding="utf-8"))
        assert saved_data["packet_id"] == "art_test_packet_123"
        assert saved_data["editorial_quality_audit"]["classification"] == "EDITORIAL_BLOCKED"
        assert saved_data["editorial_review_packet"]["tier1_editorial_approved"] is False
        assert mock_run_article.call_args.kwargs["timeout_seconds"] == 42


@patch("live_contentops.live_production_pipeline_runner_v6.run_article_engine")
@patch("live_contentops.live_production_pipeline_runner_v6.generate_live_platform_variants")
@patch("live_contentops.live_production_pipeline_runner_v6.time.sleep", return_value=None)
@patch("live_contentops.discord_live_adapter_v6.execute_discord_post")
@patch("live_contentops.threads_adapter_v6.execute_threads_post")
@patch("live_contentops.telegram_live_adapter_v6.execute_telegram_photo")
@patch("live_contentops.telegram_live_adapter_v6.execute_telegram_post")
@patch("live_contentops.facebook_page_adapter_v6.execute_facebook_photo")
@patch("live_contentops.facebook_page_adapter_v6.execute_facebook_post")
@patch("live_contentops.instagram_adapter_v6.execute_instagram_post")
@patch("live_contentops.x_browser_adapter_v6.execute_x_comment")
@patch("live_contentops.x_browser_adapter_v6.execute_x_post")
@patch("live_contentops.linkedin_browser_adapter_v6.execute_linkedin_post")
@patch("live_contentops.substack_browser_adapter_v6.execute_substack_post")
def test_run_live_production_pipeline_with_dispatch(
    mock_substack, mock_linkedin, mock_x_post, mock_x_comment, mock_ig, mock_fb, mock_fb_photo, mock_tg, mock_tg_photo, mock_threads, mock_discord, mock_sleep, mock_generate_variants, mock_run_article, tmp_path
):
    topic = "Yield rates drop"
    angle = "No advice"
    run_id = "v6_pipeline_test_dispatch"
    canonical_url = "https://substack.com/p/1"
    telegram_text = (
        "Telegram summary explains the market setup, the data limits, and the source trail "
        "before sending readers to the full article."
    )
    telegram_media = "downloads/test_image.jpg"
    telegram_body = _fit_telegram_photo_caption(
        _apply_canonical_link(telegram_text, canonical_url),
        canonical_url,
    )
    approval_marker = _approval_marker_for_run(
        topic=topic,
        angle=angle,
        run_id=run_id,
        telegram_action="photo",
        telegram_body=telegram_body,
        canonical_url=canonical_url,
        telegram_media=telegram_media,
    )
    mock_run_article.return_value = _approved_article_packet()
    
    mock_generate_variants.return_value = {
        "platform_variant_packet_id": "var_test_packet_456",
        "image_path": "downloads/test_image.jpg",
        "public_image_url": "https://example.com/test_image.jpg",
        "variant_status": "VARIANT_SCAFFOLD_READY",
        "variants": {
            "substack": "Substack body",
            "linkedin": "LinkedIn text",
            "telegram": telegram_text,
            "threads": "Threads text",
            "discord": "Discord text"
        },
        "variant_threads": {
            "x": ["Tweet 1"],
            "threads": ["Threads post 1", "Threads reply 2"]
        },
        "media_manifest": {"selected_media_by_platform": {"instagram": "https://example.com/test_image.jpg", "telegram": "https://example.com/test_image.jpg"}},
    }
    
    mock_substack.return_value = {"status": "SUCCESS", "url": canonical_url}
    mock_linkedin.return_value = {"status": "SUCCESS", "response": {"url": "https://linkedin.com/p/2"}}
    mock_x_post.return_value = {"status": "SUCCESS", "response": {"url": "https://x.com/status/3"}}
    mock_x_comment.return_value = {"status": "SUCCESS"}
    mock_ig.return_value = {"status": "SUCCESS"}
    mock_fb.return_value = {"status": "SUCCESS"}
    mock_fb_photo.return_value = {"status": "SUCCESS"}
    mock_tg.return_value = {"status": "SUCCESS"}
    mock_tg_photo.return_value = {
        "status": "SUCCESS",
        "action": "photo",
        "response": {"result": {"message_id": 88, "photo": [{"file_id": "photo_1"}]}},
    }
    mock_threads.return_value = {"status": "SUCCESS", "id": "threads_1"}
    mock_discord.return_value = {"status": "SUCCESS"}
    
    test_article_path = tmp_path / "canonical_article_packet.json"
    audit_path = tmp_path / "latest_dispatch_audit.json"
    
    with patch("live_contentops.live_production_pipeline_runner_v6.ARTICLE_OUTPUT_PATH", test_article_path), \
         patch("live_contentops.live_production_pipeline_runner_v6.DISPATCH_AUDIT_PATH", audit_path):
        result = run_live_production_pipeline(
            topic=topic,
            editorial_angle=angle,
            live_run=False,
            dispatch_live=True,
            dispatch_platforms=["substack", "linkedin", "instagram", "facebook", "telegram", "threads", "discord"],
            operator_approval_marker=approval_marker,
            run_id_override=run_id,
            public_dispatch_ledger_path=tmp_path / "ledger.jsonl",
        )
        
        assert result["dispatch_live"] is True
        assert result["dispatch_results"]["substack"]["status"] == "SUCCESS"
        assert result["dispatch_results"]["linkedin"]["status"] == "SUCCESS"
        assert result["dispatch_results"]["instagram"]["status"] == "SUCCESS"
        assert result["dispatch_results"]["facebook"]["status"] == "SUCCESS"
        assert result["dispatch_results"]["telegram"]["status"] == "SUCCESS"
        assert result["dispatch_results"]["threads"]["status"] == "SUCCESS"
        assert len(result["dispatch_results"]["threads_replies"]) == 2
        assert result["dispatch_results"]["discord"]["status"] == "SUCCESS"
        assert result["pipeline_status"] == "DISPATCH_COMPLETE"
        assert "substack" in result["dispatch_summary"]["successful_platforms"]
        mock_x_post.assert_not_called()
        mock_x_comment.assert_not_called()
        mock_tg_photo.assert_called_once()
        mock_tg.assert_not_called()
        assert mock_sleep.call_count >= 1


@patch("live_contentops.live_production_pipeline_runner_v6.run_article_engine")
@patch("live_contentops.live_production_pipeline_runner_v6.generate_live_platform_variants")
@patch("live_contentops.substack_browser_adapter_v6.execute_substack_post")
@patch("live_contentops.telegram_live_adapter_v6.execute_telegram_photo")
def test_dispatch_live_without_operator_marker_blocks_before_platform_adapters(
    mock_tg_photo, mock_substack, mock_generate_variants, mock_run_article, tmp_path
):
    mock_run_article.return_value = _approved_article_packet()
    mock_generate_variants.return_value = {
        "platform_variant_packet_id": "var_test_packet_456",
        "image_path": "downloads/test_image.jpg",
        "public_image_url": "https://example.com/test_image.jpg",
        "variant_status": "VARIANT_READY",
        "variants": {
            "substack": "Substack body",
            "telegram": "Meaningful Telegram text that would otherwise be eligible.",
        },
        "variant_threads": {},
    }

    audit_path = tmp_path / "audit.json"
    with patch("live_contentops.live_production_pipeline_runner_v6.ARTICLE_OUTPUT_PATH", tmp_path / "article.json"), \
         patch("live_contentops.live_production_pipeline_runner_v6.DISPATCH_AUDIT_PATH", audit_path):
        result = run_live_production_pipeline(
            topic="Yield rates drop",
            editorial_angle="No advice",
            live_run=False,
            dispatch_live=True,
        )

    audit = json.loads(audit_path.read_text(encoding="utf-8"))

    assert result["pipeline_status"] == "DISPATCH_BLOCKED"
    assert result["dispatch_live"] is False
    assert result["dispatch_blocked"] is True
    assert result["dispatch_audit_path"] == str(audit_path)
    assert result["dispatch_summary"] == {
        "attempted_platforms": [],
        "successful_platforms": [],
        "failed_platforms": [],
        "blocked_platforms": ["pipeline"],
    }
    assert "public_dispatch_freeze_guard:operator_approval_marker_missing" in result["dispatch_blockers"]
    assert audit["run_id"] == result["run_id"]
    assert audit["pipeline_status"] == result["pipeline_status"]
    assert audit["dispatch_blocked"] is True
    assert audit["dispatch_live"] is False
    assert audit["dispatch_blockers"] == result["dispatch_blockers"]
    assert audit["dispatch_summary"] == result["dispatch_summary"]
    mock_substack.assert_not_called()
    mock_tg_photo.assert_not_called()


@patch("live_contentops.live_production_pipeline_runner_v6.run_article_engine")
@patch("live_contentops.live_production_pipeline_runner_v6.generate_live_platform_variants")
@patch("live_contentops.live_production_pipeline_runner_v6.time.sleep", return_value=None)
@patch("live_contentops.substack_browser_adapter_v6.execute_substack_post", return_value={"status": "SUCCESS", "url": "https://substack.test/p/unit"})
@patch("live_contentops.linkedin_browser_adapter_v6.execute_linkedin_post", return_value={"status": "SUCCESS"})
@patch("live_contentops.x_browser_adapter_v6.execute_x_post", return_value={"status": "SUCCESS"})
@patch("live_contentops.instagram_adapter_v6.execute_instagram_post", return_value={"status": "SUCCESS"})
@patch("live_contentops.facebook_page_adapter_v6.execute_facebook_photo", return_value={"status": "SUCCESS"})
@patch("live_contentops.facebook_page_adapter_v6.execute_facebook_post", return_value={"status": "SUCCESS"})
@patch("live_contentops.telegram_live_adapter_v6.execute_telegram_post", return_value={"status": "SUCCESS"})
@patch("live_contentops.threads_adapter_v6.execute_threads_post", return_value={"status": "SUCCESS", "id": "threads_1"})
@patch("live_contentops.discord_live_adapter_v6.execute_discord_post", return_value={"status": "SUCCESS"})
def test_dispatch_uses_reachable_instagram_fallback_when_public_image_missing(
    mock_discord, mock_threads, mock_tg, mock_fb, mock_fb_photo, mock_ig, mock_x_post, mock_linkedin, mock_substack, mock_sleep, mock_generate_variants, mock_run_article, tmp_path
):
    run_id = "v6_pipeline_test_instagram_fallback"
    approval_marker = _approval_marker_for_run(
        topic="Topic",
        angle="Angle",
        run_id=run_id,
        telegram_action="post",
        telegram_body="Telegram summary",
    )
    mock_run_article.return_value = _approved_article_packet()
    mock_generate_variants.return_value = {
        "platform_variant_packet_id": "var_test_packet_456",
        "public_image_url": None,
        "variant_status": "VARIANT_READY",
        "variants": {
            "substack": "Substack body",
            "linkedin": "LinkedIn text",
            "telegram": "Telegram summary",
            "discord": "Discord text",
            "instagram_caption": "Instagram caption",
        },
        "variant_threads": {"x": [], "threads": ["Threads post 1"]},
    }
    with patch("live_contentops.live_production_pipeline_runner_v6.extract_og_image", return_value=None), \
         patch("live_contentops.live_production_pipeline_runner_v6.ARTICLE_OUTPUT_PATH", tmp_path / "article.json"), \
         patch("live_contentops.live_production_pipeline_runner_v6.DISPATCH_AUDIT_PATH", tmp_path / "audit.json"):
        result = run_live_production_pipeline(
            "Topic",
            "Angle",
            live_run=False,
            dispatch_live=True,
            operator_approval_marker=approval_marker,
            run_id_override=run_id,
            public_dispatch_ledger_path=tmp_path / "ledger.jsonl",
        )
    assert result["dispatch_results"]["instagram"]["status"] == "BLOCKED"
    mock_ig.assert_not_called()


@patch("live_contentops.live_production_pipeline_runner_v6.run_article_engine")
@patch("live_contentops.live_production_pipeline_runner_v6.generate_live_platform_variants")
@patch("live_contentops.live_production_pipeline_runner_v6.time.sleep", return_value=None)
@patch("live_contentops.substack_browser_adapter_v6.execute_substack_post", return_value={"status": "SUCCESS"})
@patch("live_contentops.linkedin_browser_adapter_v6.execute_linkedin_post", return_value={"status": "SUCCESS"})
@patch("live_contentops.x_browser_adapter_v6.execute_x_post", return_value={"status": "SUCCESS"})
@patch("live_contentops.instagram_adapter_v6.execute_instagram_post", return_value={"status": "SUCCESS"})
@patch("live_contentops.facebook_page_adapter_v6.execute_facebook_post", return_value={"status": "SUCCESS"})
@patch("live_contentops.telegram_live_adapter_v6.execute_telegram_post", return_value={"status": "SUCCESS"})
@patch("live_contentops.threads_adapter_v6.execute_threads_post", return_value={"status": "SUCCESS", "id": "threads_1"})
@patch("live_contentops.discord_live_adapter_v6.execute_discord_post", return_value={"status": "SUCCESS"})
def test_dispatch_platform_scope_retries_instagram_only_without_reposting_successes(
    mock_discord, mock_threads, mock_tg, mock_fb, mock_ig, mock_x_post, mock_linkedin, mock_substack, mock_sleep, mock_generate_variants, mock_run_article, tmp_path
):
    run_id = "v6_pipeline_test_instagram_scope"
    approval_marker = _approval_marker_for_run(topic="Topic", angle="Angle", run_id=run_id)
    mock_run_article.return_value = _approved_article_packet()
    mock_generate_variants.return_value = {
        "platform_variant_packet_id": "var_test_packet_456",
        "public_image_url": None,
        "variant_status": "VARIANT_READY",
        "variants": {
            "substack": "Substack body",
            "linkedin": "LinkedIn text",
            "telegram": "Telegram summary",
            "discord": "Discord text",
            "instagram_caption": "Instagram caption",
        },
        "variant_threads": {"x": ["Tweet 1"], "threads": ["Threads post 1"]},
    }
    audit_path = tmp_path / "audit.json"
    with patch("live_contentops.live_production_pipeline_runner_v6.ARTICLE_OUTPUT_PATH", tmp_path / "article.json"), \
         patch("live_contentops.live_production_pipeline_runner_v6.DISPATCH_AUDIT_PATH", audit_path):
        result = run_live_production_pipeline(
            "Topic",
            "Angle",
            live_run=False,
            dispatch_live=True,
            dispatch_platforms=["instagram"],
            operator_approval_marker=approval_marker,
            run_id_override=run_id,
            public_dispatch_ledger_path=tmp_path / "ledger.jsonl",
        )
    assert result["pipeline_status"] == "DISPATCH_PARTIAL_FAILURE"
    assert result["dispatch_platform_scope"] == ["instagram"]
    assert result["dispatch_summary"]["attempted_platforms"] == ["instagram"]
    assert result["dispatch_summary"]["blocked_platforms"] == ["instagram"]
    assert set(result["dispatch_results"]) == {"instagram"}
    mock_ig.assert_not_called()
    for skipped in (mock_substack, mock_linkedin, mock_x_post, mock_fb, mock_tg, mock_threads, mock_discord):
        skipped.assert_not_called()
    saved = json.loads(audit_path.read_text(encoding="utf-8"))
    assert saved["dispatch_platform_scope"] == ["instagram"]
    assert saved["dispatch_idempotency_control"] == "platform_scope_allowlist"


@patch("live_contentops.live_production_pipeline_runner_v6.run_article_engine")
@patch("live_contentops.live_production_pipeline_runner_v6.generate_live_platform_variants")
@patch("live_contentops.live_production_pipeline_runner_v6.time.sleep", return_value=None)
@patch("live_contentops.instagram_adapter_v6.execute_instagram_post")
def test_instagram_dispatch_retries_media_candidate_failure(
    mock_ig, mock_sleep, mock_generate_variants, mock_run_article, tmp_path
):
    run_id = "v6_pipeline_test_instagram_retry"
    approval_marker = _approval_marker_for_run(topic="Topic", angle="Angle", run_id=run_id)
    mock_run_article.return_value = _approved_article_packet()
    mock_generate_variants.return_value = {
        "platform_variant_packet_id": "var_test_packet_456",
        "public_image_url": "https://example.com/wide.png",
        "variant_status": "VARIANT_READY",
        "variants": {"instagram_caption": "Instagram caption"},
        "variant_threads": {},
        "media_manifest": {
            "news_image_source_url": "https://example.com/wide.png",
            "selected_media_by_platform": {"instagram": "https://example.com/wide.png"},
        },
    }
    mock_ig.side_effect = [
        {"status": "VALIDATION_FAILED", "validation_failures": ["image_aspect_ratio_unsupported:1168x466:2.506"]},
        {"status": "SUCCESS", "id": "ig_media_1"},
    ]

    with patch("live_contentops.live_production_pipeline_runner_v6.ARTICLE_OUTPUT_PATH", tmp_path / "article.json"), \
         patch("live_contentops.live_production_pipeline_runner_v6.DISPATCH_AUDIT_PATH", tmp_path / "audit.json"):
        result = run_live_production_pipeline(
            "Topic",
            "Angle",
            live_run=False,
            dispatch_live=True,
            dispatch_platforms=["instagram"],
            operator_approval_marker=approval_marker,
            run_id_override=run_id,
            public_dispatch_ledger_path=tmp_path / "ledger.jsonl",
        )

    assert result["pipeline_status"] == "DISPATCH_COMPLETE"
    assert result["dispatch_results"]["instagram"]["status"] == "SUCCESS"
    assert mock_ig.call_count == 2
    assert mock_ig.call_args_list[1].kwargs["image_url"].startswith("https://images.weserv.nl/")


def test_dispatch_summary_normalizes_success_failure_and_blocked():
    failed = _normalize_dispatch_result("linkedin", error=RuntimeError("boom"))
    summary = _dispatch_summary({
        "substack": _normalize_dispatch_result("substack", {"status": "SUCCESS"}),
        "linkedin": failed,
        "x_replies": [_normalize_dispatch_result("x_reply_1", {"status": "SUCCESS"})],
        "instagram": {"platform": "instagram", "status": "BLOCKED", "ok": False},
        "telegram": {"platform": "telegram", "status": "PUBLIC_DISPATCH_FROZEN", "ok": False},
    })
    assert summary["successful_platforms"] == ["substack", "x_reply_1"]
    assert summary["failed_platforms"] == ["linkedin"]
    assert summary["blocked_platforms"] == ["instagram", "telegram"]


@patch("live_contentops.live_production_pipeline_runner_v6.run_article_engine")
@patch("live_contentops.live_production_pipeline_runner_v6.generate_live_platform_variants")
def test_run_live_production_pipeline_blocked_dispatch_writes_audit(mock_generate_variants, mock_run_article, tmp_path):
    mock_run_article.return_value = {
        "packet_id": "art_test_packet_123",
        "canonical_article_draft": {"title": "Short", "body_markdown": "too short"},
    }
    mock_generate_variants.return_value = {
        "platform_variant_packet_id": "var_test_packet_456",
        "variant_status": "VARIANT_VALIDATION_FAILED",
        "validation_failures": ["linkedin_too_short:0<120"],
        "variants": {},
        "variant_threads": {},
    }
    audit_path = tmp_path / "latest_dispatch_audit.json"
    with patch("live_contentops.live_production_pipeline_runner_v6.ARTICLE_OUTPUT_PATH", tmp_path / "article.json"), \
         patch("live_contentops.live_production_pipeline_runner_v6.DISPATCH_AUDIT_PATH", audit_path):
        result = run_live_production_pipeline("Topic", "Angle", live_run=True, dispatch_live=True)
    assert result["pipeline_status"] == "DISPATCH_BLOCKED"
    assert result["dispatch_summary"]["blocked_platforms"] == ["pipeline"]
    assert json.loads(audit_path.read_text(encoding="utf-8"))["run_id"] == result["run_id"]


@patch("live_contentops.live_production_pipeline_runner_v6.run_article_engine")
@patch("live_contentops.live_production_pipeline_runner_v6.generate_live_platform_variants")
@patch("live_contentops.live_production_pipeline_runner_v6.time.sleep", return_value=None)
@patch("live_contentops.substack_browser_adapter_v6.execute_substack_post")
@patch("live_contentops.linkedin_browser_adapter_v6.execute_linkedin_post", side_effect=RuntimeError("linkedin down"))
@patch("live_contentops.x_browser_adapter_v6.execute_x_post")
@patch("live_contentops.instagram_adapter_v6.execute_instagram_post")
@patch("live_contentops.facebook_page_adapter_v6.execute_facebook_photo")
@patch("live_contentops.facebook_page_adapter_v6.execute_facebook_post")
@patch("live_contentops.telegram_live_adapter_v6.execute_telegram_post")
@patch("live_contentops.threads_adapter_v6.execute_threads_post")
@patch("live_contentops.discord_live_adapter_v6.execute_discord_post")
def test_run_live_production_pipeline_partial_failure_is_structured(
    mock_discord, mock_threads, mock_tg, mock_fb, mock_fb_photo, mock_ig, mock_x_post, mock_linkedin, mock_substack, mock_sleep, mock_generate_variants, mock_run_article, tmp_path
):
    run_id = "v6_pipeline_test_partial_failure"
    approval_marker = _approval_marker_for_run(topic="Topic", angle="Angle", run_id=run_id)
    mock_run_article.return_value = _approved_article_packet()
    mock_generate_variants.return_value = {
        "platform_variant_packet_id": "var_test_packet_456",
        "public_image_url": "https://example.com/test_image.jpg",
        "variant_status": "VARIANT_READY",
        "variants": {
            "substack": "Substack body",
            "linkedin": "LinkedIn text",
            "telegram": "",
            "threads": "",
            "discord": "",
            "instagram_caption": "Instagram caption",
        },
        "variant_threads": {"x": [], "threads": []},
    }
    mock_substack.return_value = {"status": "SUCCESS", "url": "https://substack.test/p/unit"}
    mock_x_post.return_value = {"status": "SUCCESS"}
    mock_ig.return_value = {"status": "SUCCESS"}
    mock_fb.return_value = {"status": "SUCCESS"}
    mock_fb_photo.return_value = {"status": "SUCCESS"}
    mock_tg.return_value = {"status": "SUCCESS"}
    mock_threads.return_value = {"status": "SUCCESS", "id": "threads_1"}
    mock_discord.return_value = {"status": "SUCCESS"}
    audit_path = tmp_path / "latest_dispatch_audit.json"
    with patch("live_contentops.live_production_pipeline_runner_v6.ARTICLE_OUTPUT_PATH", tmp_path / "article.json"), \
         patch("live_contentops.live_production_pipeline_runner_v6.DISPATCH_AUDIT_PATH", audit_path):
        result = run_live_production_pipeline(
            "Topic",
            "Angle",
            live_run=False,
            dispatch_live=True,
            operator_approval_marker=approval_marker,
            run_id_override=run_id,
            public_dispatch_ledger_path=tmp_path / "ledger.jsonl",
        )
    assert result["pipeline_status"] == "DISPATCH_PARTIAL_FAILURE"
    assert result["dispatch_results"]["linkedin"]["error_class"] == "RuntimeError"
    assert "linkedin" in result["dispatch_summary"]["failed_platforms"]
    assert "threads" in result["dispatch_summary"]["blocked_platforms"]


@patch("live_contentops.live_production_pipeline_runner_v6.run_live_production_pipeline")
def test_cli_main_returns_nonzero_on_blocked_launch(mock_run):
    from live_contentops.live_production_pipeline_runner_v6 import main
    mock_run.return_value = {
        "run_id": "v6_pipeline_abc",
        "pipeline_status": "DISPATCH_BLOCKED",
        "dispatch_live": False,
        "dispatch_summary": {"blocked_platforms": ["pipeline"]},
        "dispatch_blockers": ["article_too_short_words:127<2000"],
    }
    assert main(["--live-run", "--dispatch-live"]) == 1


@patch("live_contentops.live_production_pipeline_runner_v6.run_live_production_pipeline")
def test_cli_main_returns_zero_on_complete_launch(mock_run):
    from live_contentops.live_production_pipeline_runner_v6 import main
    mock_run.return_value = {
        "run_id": "v6_pipeline_abc",
        "pipeline_status": "DISPATCH_COMPLETE",
        "dispatch_live": True,
        "dispatch_summary": {"successful_platforms": ["substack"]},
    }
    assert main(["--live-run", "--dispatch-live"]) == 0


def test_apply_canonical_link_replaces_token():
    assert _apply_canonical_link("See more [Link] today", "https://x.io/p/1") == "See more https://x.io/p/1 today"


def test_apply_canonical_link_appends_when_absent():
    out = _apply_canonical_link("Body text", "https://x.io/p/1")
    assert out.endswith("Read the full editorial analysis: https://x.io/p/1")


def test_apply_canonical_link_strips_dead_token_when_no_url():
    # No dangling placeholder may ship when there is no real URL.
    out = _apply_canonical_link("Body text\nRead more: [Link]", None)
    assert "[Link]" not in out
    assert "[link]" not in out.lower()


def test_apply_canonical_link_strips_generated_noncanonical_urls():
    canonical = "https://capitalchronicle.substack.com/p/the-crude-catalyst"
    out = _apply_canonical_link(
        "Read below:\nhttps://capitalchronicle.com/crude-catalyst-recession-risks",
        canonical,
    )
    assert "capitalchronicle.com/crude-catalyst" not in out
    assert out.count(canonical) == 1
    assert out.endswith(canonical)


def test_fit_telegram_photo_caption_preserves_canonical_link_under_limit():
    canonical = "https://capitalchronicle.substack.com/p/crude-awakening"
    body = ("Long macro paragraph. " * 80) + f"\n\nRead the full editorial analysis: {canonical}"
    out = _fit_telegram_photo_caption(body, canonical, limit=300)
    assert len(out) <= 300
    assert out.endswith(canonical)
    assert "..." in out


def test_resolve_substack_public_url_uses_feed_for_admin_url(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b"""<?xml version='1.0'?><rss><channel><item><title>Capital Chronicle Educational Briefing: US recession risks rise as oil volatility spikes</title><link>https://capitalchronicle.substack.com/p/us-recession-risks-oil-volatility</link></item></channel></rss>"""

    monkeypatch.setattr("urllib.request.urlopen", lambda *_args, **_kwargs: FakeResponse())
    resolved = resolve_substack_public_url(
        "https://capitalchronicle.substack.com/publish/post/205708785",
        "Capital Chronicle Educational Briefing: US recession risks rise as oil volatility spikes",
    )
    assert resolved == "https://capitalchronicle.substack.com/p/us-recession-risks-oil-volatility"


def test_instagram_image_candidates_prefer_safe_proxy():
    candidates = _instagram_image_candidates(
        public_image_url="https://substackcdn.com/image/fetch/w_1200,h_675/https%3A%2F%2Fexample.com%2Fwide.png",
        selected_media={"instagram": "https://images.weserv.nl/?url=https://example.com/wide.png&w=1080&h=1080&fit=contain&bg=white&output=jpg"},
        media_manifest={"news_image_source_url": "https://example.com/wide.png"},
    )
    assert candidates[0].startswith("https://images.weserv.nl/")
    assert any(candidate.startswith("https://wsrv.nl/") for candidate in candidates)
    assert candidates[-1] == "https://example.com/wide.png"


def test_audit_substack_public_visuals_counts_distinct_public_images(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b"""
            <html><body>
              <article>
                <img src="https://substackcdn.com/image/fetch/w_1200/https%3A%2F%2Fexample.com%2Fprimary.png">
                <img srcset="https://substackcdn.com/image/fetch/w_640/https%3A%2F%2Fexample.com%2Frecent.png 640w,
                             https://substackcdn.com/image/fetch/w_1200/https%3A%2F%2Fexample.com%2Frecent.png 1200w">
                <img src="https://substackcdn.com/image/fetch/w_32/https%3A%2F%2Fexample.com%2Favatar.png">
              </article>
            </body></html>
            """

    monkeypatch.setattr("urllib.request.urlopen", lambda *_args, **_kwargs: FakeResponse())
    audit = audit_substack_public_visuals(
        "https://capitalchronicle.substack.com/p/current-oil-risk",
        expected_visual_count=2,
        retries=1,
    )
    assert audit["status"] == "PASS"
    assert audit["public_image_count"] == 2
    assert audit["meets_expected_visual_count"] is True
    assert audit["public_image_urls"] == ["https://example.com/primary.png", "https://example.com/recent.png"]


def test_audit_substack_public_visuals_passes_in_body_visual_order(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b"""
            <html><body><article>
              <p>Intro setup.</p>
              <img src="https://substackcdn.com/image/fetch/w_1200/https%3A%2F%2Fexample.com%2Fprimary.png">
              <h2>The Macro Setup: Current Oil Evidence Before Narrative</h2>
              <p>Macro body.</p>
              <h2>Market Implications Without Directional Noise</h2>
              <p>Market body.</p>
              <img src="https://substackcdn.com/image/fetch/w_1200/https%3A%2F%2Fexample.com%2Frecent.png">
              <h2>How to Read the Source Trail</h2>
              <p>Source explanation.</p>
              <h2>Source trail</h2>
            </article></body></html>
            """

    monkeypatch.setattr("urllib.request.urlopen", lambda *_args, **_kwargs: FakeResponse())
    audit = audit_substack_public_visuals(
        "https://capitalchronicle.substack.com/p/current-oil-risk",
        expected_visual_count=2,
        expected_placements=[
            {"asset_id": "primary", "placement_after_section": "intro"},
            {"asset_id": "recent_price", "placement_after_section": "Market Implications Without Directional Noise"},
        ],
        retries=1,
    )

    assert audit["status"] == "PASS"
    assert audit["placement_order_status"] == "PASS"
    assert audit["meets_visual_placement_expectations"] is True
    assert [check["passed"] for check in audit["placement_checks"]] == [True, True]


def test_audit_substack_public_visuals_fails_when_images_are_only_at_end(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b"""
            <html><body><article>
              <p>Intro setup.</p>
              <h2>The Macro Setup: Current Oil Evidence Before Narrative</h2>
              <p>Macro body.</p>
              <h2>Market Implications Without Directional Noise</h2>
              <p>Market body.</p>
              <h2>Source trail</h2>
              <p>Sources.</p>
              <img src="https://substackcdn.com/image/fetch/w_1200/https%3A%2F%2Fexample.com%2Fprimary.png">
              <img src="https://substackcdn.com/image/fetch/w_1200/https%3A%2F%2Fexample.com%2Frecent.png">
            </article></body></html>
            """

    monkeypatch.setattr("urllib.request.urlopen", lambda *_args, **_kwargs: FakeResponse())
    audit = audit_substack_public_visuals(
        "https://capitalchronicle.substack.com/p/current-oil-risk",
        expected_visual_count=2,
        expected_placements=[
            {"asset_id": "primary", "placement_after_section": "intro"},
            {"asset_id": "recent_price", "placement_after_section": "Market Implications Without Directional Noise"},
        ],
        retries=1,
    )

    assert audit["meets_expected_visual_count"] is True
    assert audit["status"] == "PLACEMENT_MISMATCH"
    assert audit["placement_order_status"] == "PLACEMENT_MISMATCH"
    assert audit["meets_visual_placement_expectations"] is False
    assert audit["all_images_after_source_trail"] is True


def test_expected_substack_visual_placements_infer_missing_slot_from_marker_heading():
    body = (
        "Intro\n\n[[VISUAL:primary]]\n\n"
        "### Data Transparency and the Retail Reality\n"
        "Section body.\n\n[[VISUAL:recent_price]]\n\n"
        "### Geopolitical Tremors and Energy Security\n"
    )

    placements = _expected_substack_visual_placements(
        ["primary", "recent_price"],
        [{"asset_id": "primary", "placement_after_section": "intro"}],
        body,
    )

    assert placements[0]["placement_after_section"] == "intro"
    assert placements[0]["placement_source"] == "visual_slot"
    assert placements[1]["placement_after_section"] == "Data Transparency and the Retail Reality"
    assert placements[1]["placement_source"] == "marker_heading_inference"


@patch("live_contentops.live_production_pipeline_runner_v6.run_article_engine")
@patch("live_contentops.live_production_pipeline_runner_v6.generate_live_platform_variants")
@patch("live_contentops.live_production_pipeline_runner_v6.time.sleep", return_value=None)
@patch("live_contentops.substack_browser_adapter_v6.execute_substack_post")
@patch("live_contentops.linkedin_browser_adapter_v6.execute_linkedin_post", return_value={"status": "SUCCESS"})
@patch("live_contentops.x_browser_adapter_v6.execute_x_post", return_value={"status": "SUCCESS"})
@patch("live_contentops.x_browser_adapter_v6.execute_x_comment", return_value={"status": "SUCCESS"})
@patch("live_contentops.instagram_adapter_v6.execute_instagram_post", return_value={"status": "SUCCESS"})
@patch("live_contentops.facebook_page_adapter_v6.execute_facebook_photo", return_value={"status": "SUCCESS"})
@patch("live_contentops.facebook_page_adapter_v6.execute_facebook_post", return_value={"status": "SUCCESS"})
@patch(
    "live_contentops.telegram_live_adapter_v6.execute_telegram_photo",
    return_value={
        "status": "SUCCESS",
        "action": "photo",
        "response": {"result": {"message_id": 88, "photo": [{"file_id": "photo_1"}]}},
    },
)
@patch("live_contentops.threads_adapter_v6.execute_threads_post", return_value={"status": "SUCCESS", "id": "t1"})
@patch("live_contentops.discord_live_adapter_v6.execute_discord_post", return_value={"status": "SUCCESS"})
def test_dispatch_passes_media_and_canonical_link(
    mock_discord, mock_threads, mock_tg_photo, mock_fb, mock_fb_photo, mock_ig, mock_x_comment, mock_x_post,
    mock_linkedin, mock_substack, mock_sleep, mock_generate_variants, mock_run_article, tmp_path
):
    topic = "Topic"
    angle = "Angle"
    run_id = "v6_pipeline_test_media_link"
    canonical_url = "https://sub.stack/p/live"
    telegram_text = (
        "Telegram summary connects the source evidence, chart context, and operator-reviewed "
        "takeaways before linking to the full briefing."
    )
    telegram_media = "downloads/hero.jpg"
    telegram_body = _fit_telegram_photo_caption(
        _apply_canonical_link(telegram_text, canonical_url),
        canonical_url,
    )
    approval_marker = _approval_marker_for_run(
        topic=topic,
        angle=angle,
        run_id=run_id,
        telegram_action="photo",
        telegram_body=telegram_body,
        canonical_url=canonical_url,
        telegram_media=telegram_media,
    )
    mock_run_article.return_value = _approved_article_packet()
    mock_generate_variants.return_value = {
        "platform_variant_packet_id": "var_1",
        "image_path": "downloads/hero.jpg",
        "public_image_url": "https://cdn.example.com/hero.jpg",
        "variant_status": "VARIANT_READY",
        "variants": {
            "substack": "Substack body",
            "linkedin": "LinkedIn text",
            "facebook": "Facebook text",
            "telegram": telegram_text,
            "discord": "Discord text",
            "instagram_caption": "IG caption",
        },
        "variant_threads": {"x": [], "threads": ["Threads 1"]},
        "media_manifest": {
            "news_image_path": "downloads/hero.jpg",
            "media_assets": [{"asset_id": "primary", "local_path": "downloads/hero.jpg"}],
            "selected_media_by_platform": {"instagram": "https://cdn.example.com/hero.jpg", "telegram": "https://cdn.example.com/hero.jpg"},
        },
    }
    mock_substack.return_value = {"status": "SUCCESS", "url": canonical_url}
    with patch("live_contentops.live_production_pipeline_runner_v6.ARTICLE_OUTPUT_PATH", tmp_path / "a.json"), \
         patch("live_contentops.live_production_pipeline_runner_v6.DISPATCH_AUDIT_PATH", tmp_path / "audit.json"):
        run_live_production_pipeline(
            topic,
            angle,
            live_run=False,
            dispatch_live=True,
            operator_approval_marker=approval_marker,
            run_id_override=run_id,
            public_dispatch_ledger_path=tmp_path / "ledger.jsonl",
        )

    # Substack receives the local hero image for browser upload.
    assert mock_substack.call_args.kwargs["image_path"] == "downloads/hero.jpg"
    assert mock_substack.call_args.kwargs["image_assets"] == [{"asset_id": "primary", "local_path": "downloads/hero.jpg"}]
    # LinkedIn gets the image and the canonical link appended to the body.
    assert mock_linkedin.call_args.kwargs["image_path"] == "downloads/hero.jpg"
    assert "https://sub.stack/p/live" in mock_linkedin.call_args.kwargs["text"]
    # Facebook gets a true photo post with the canonical link in the caption.
    assert mock_fb_photo.call_args.kwargs["image_url"] == "https://cdn.example.com/hero.jpg"
    assert "https://sub.stack/p/live" in mock_fb_photo.call_args.kwargs["message"]
    # Threads first post carries a public image URL.
    assert mock_threads.call_args_list[0].kwargs["image_url"] == "https://cdn.example.com/hero.jpg"
    # Discord builds a rich embed with the canonical URL and hero image.
    embeds = mock_discord.call_args.kwargs["embeds"]
    assert embeds and embeds[0]["url"] == "https://sub.stack/p/live"
    assert embeds[0]["image"]["url"] == "https://cdn.example.com/hero.jpg"


@patch("live_contentops.live_production_pipeline_runner_v6.run_article_engine")
@patch("live_contentops.live_production_pipeline_runner_v6.generate_live_platform_variants")
@patch("live_contentops.live_production_pipeline_runner_v6.time.sleep", return_value=None)
@patch("live_contentops.telegram_live_adapter_v6.execute_telegram_photo")
def test_telegram_preview_only_caption_blocks_before_adapter(
    mock_tg_photo, mock_sleep, mock_generate_variants, mock_run_article, tmp_path, monkeypatch
):
    topic = "Preview-only caption incident"
    angle = "No advice"
    run_id = "v6_pipeline_test_preview_only"
    canonical_url = "https://capitalchronicle.substack.com/p/preview-only-test"
    telegram_text = f"Read the full editorial analysis: {canonical_url}"
    telegram_media = "downloads/hero.jpg"
    telegram_body = _fit_telegram_photo_caption(
        _apply_canonical_link(telegram_text, canonical_url),
        canonical_url,
    )
    approval_marker = _approval_marker_for_run(
        topic=topic,
        angle=angle,
        run_id=run_id,
        telegram_action="photo",
        telegram_body=telegram_body,
        canonical_url=canonical_url,
        telegram_media=telegram_media,
    )
    monkeypatch.setenv("CONTENTOPS_CANONICAL_URL_OVERRIDE", canonical_url)
    mock_run_article.return_value = _approved_article_packet()
    mock_generate_variants.return_value = {
        "platform_variant_packet_id": "var_preview",
        "image_path": telegram_media,
        "variant_status": "VARIANT_READY",
        "variants": {"telegram": telegram_text},
        "variant_threads": {},
    }

    with patch("live_contentops.live_production_pipeline_runner_v6.ARTICLE_OUTPUT_PATH", tmp_path / "article.json"), \
         patch("live_contentops.live_production_pipeline_runner_v6.DISPATCH_AUDIT_PATH", tmp_path / "audit.json"):
        result = run_live_production_pipeline(
            topic,
            angle,
            live_run=False,
            dispatch_live=True,
            dispatch_platforms=["telegram"],
            operator_approval_marker=approval_marker,
            run_id_override=run_id,
            public_dispatch_ledger_path=tmp_path / "ledger.jsonl",
        )

    assert result["dispatch_results"]["telegram"]["status"] == "PUBLIC_DISPATCH_FROZEN"
    assert "telegram_preview_only_body" in result["dispatch_results"]["telegram"]["error"]
    mock_tg_photo.assert_not_called()


@patch("live_contentops.live_production_pipeline_runner_v6.run_article_engine")
@patch("live_contentops.live_production_pipeline_runner_v6.generate_live_platform_variants")
@patch("live_contentops.live_production_pipeline_runner_v6.time.sleep", return_value=None)
@patch("live_contentops.telegram_live_adapter_v6.execute_telegram_photo")
def test_telegram_duplicate_canonical_url_blocks_before_adapter(
    mock_tg_photo, mock_sleep, mock_generate_variants, mock_run_article, tmp_path, monkeypatch
):
    topic = "Crude awakening how spiking oil volatility"
    angle = "No advice"
    run_id = "v6_pipeline_test_duplicate_crude"
    canonical_url = "https://capitalchronicle.substack.com/p/crude-awakening-how-spiking-oil-volatility-05f"
    telegram_text = (
        "Telegram summary explains the oil-volatility evidence, why the chart matters, "
        "and what readers should verify before drawing conclusions."
    )
    telegram_media = "downloads/wti.png"
    telegram_body = _fit_telegram_photo_caption(
        _apply_canonical_link(telegram_text, canonical_url),
        canonical_url,
    )
    approval_marker = _approval_marker_for_run(
        topic=topic,
        angle=angle,
        run_id=run_id,
        telegram_action="photo",
        telegram_body=telegram_body,
        canonical_url=canonical_url,
        telegram_media=telegram_media,
    )
    monkeypatch.setenv("CONTENTOPS_CANONICAL_URL_OVERRIDE", canonical_url)
    mock_run_article.return_value = _approved_article_packet()
    mock_generate_variants.return_value = {
        "platform_variant_packet_id": "var_duplicate",
        "image_path": telegram_media,
        "variant_status": "VARIANT_READY",
        "variants": {"telegram": telegram_text},
        "variant_threads": {},
    }

    with patch("live_contentops.live_production_pipeline_runner_v6.ARTICLE_OUTPUT_PATH", tmp_path / "article.json"), \
         patch("live_contentops.live_production_pipeline_runner_v6.DISPATCH_AUDIT_PATH", tmp_path / "audit.json"):
        result = run_live_production_pipeline(
            topic,
            angle,
            live_run=False,
            dispatch_live=True,
            dispatch_platforms=["telegram"],
            operator_approval_marker=approval_marker,
            run_id_override=run_id,
        )

    assert result["dispatch_results"]["telegram"]["status"] == "PUBLIC_DISPATCH_FROZEN"
    assert "duplicate_canonical_url_hash" in result["dispatch_results"]["telegram"]["error"]
    mock_tg_photo.assert_not_called()


def test_telegram_photo_delivery_evidence_requires_bot_api_photo_result():
    ok = _telegram_photo_delivery_evidence(
        {
            "platform": "telegram",
            "status": "SUCCESS",
            "ok": True,
            "raw": {
                "action": "photo",
                "id": "88",
                "response": {"result": {"message_id": 88, "photo": [{"file_id": "photo_1"}]}},
            },
        },
        "downloads/hero.jpg",
    )
    missing = _telegram_photo_delivery_evidence(
        {"platform": "telegram", "status": "SUCCESS", "ok": True, "raw": {"action": "photo", "response": {"result": {"message_id": 88}}}},
        "downloads/hero.jpg",
    )

    assert ok["visual_delivery_status"] == "PASS"
    assert ok["photo_size_count"] == 1
    assert missing["visual_delivery_status"] == "MISSING_PHOTO_PROOF"
