# -*- coding: utf-8 -*-
"""Tests for the full north-star debug and live repair runner."""
from __future__ import annotations

import json
import re
import struct
from pathlib import Path

import pytest

from live_contentops.full_pipeline_north_star_debug_and_live_run_v0 import (
    CLASSIFICATION_BLOCKED,
    CLASSIFICATION_PARTIAL,
    REQUIRED_CAVEAT,
    build_oil_export_media_assets,
    build_root_cause_report,
    build_telegram_repair_caption,
    export_article_from_candidate_draft,
    run_full_pipeline_north_star_debug_and_live_run,
)


ROOT = Path(__file__).resolve().parents[1]


def _png_bytes(width: int = 1200, height: int = 675) -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + struct.pack(">II", width, height)


def _png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", data[16:24])


def _install_fake_visual_pack(monkeypatch: pytest.MonkeyPatch) -> None:
    import live_contentops.media_content_audit_v6 as media_audit

    def fake_build_current_macro_visual_pack(article_title: str, output_dir: str | Path, as_of_date: str | None = None):
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        assets = []
        specs = [
            ("primary", "data_chart", "primary_chart", "FRED series DCOILWTICO; underlying source U.S. Energy Information Administration"),
            ("recent_price", "data_chart", "supporting_chart", "FRED series DCOILWTICO; underlying source U.S. Energy Information Administration"),
            ("multi_year_range", "data_chart", "supporting_chart", "FRED series DCOILWTICO; underlying source U.S. Energy Information Administration"),
        ]
        for index, (asset_id, media_class, media_role, source_label) in enumerate(specs, start=1):
            path = out_dir / f"{asset_id}.png"
            path.write_bytes(_png_bytes(1200 + index, 675 + index))
            assets.append(
                {
                    "asset_id": asset_id,
                    "media_class": media_class,
                    "media_role": media_role,
                    "canonical_source_label": source_label,
                    "source_page_url": "https://fred.stlouisfed.org/series/DCOILWTICO",
                    "rights_status": "source_backed_generated_visual_cc_owned",
                    "provenance_status": "source_backed_generated_from_public_data",
                    "operator_review_required": False,
                    "caption": f"{asset_id.replace('_', ' ').title()} source-backed visual. Source: {source_label}.",
                    "alt_text": f"{asset_id.replace('_', ' ')} visual for the oil export article.",
                    "local_path": str(path),
                }
            )
        return assets

    monkeypatch.setattr(media_audit, "build_current_macro_visual_pack", fake_build_current_macro_visual_pack)


def _run_paths(tmp_path: Path) -> dict[str, Path]:
    return {
        "output_dir": tmp_path / "evidence",
        "article_md_path": tmp_path / "exports" / "daily_contentops" / "oil_export_surge_article_v0.md",
        "article_html_path": tmp_path / "exports" / "daily_contentops" / "oil_export_surge_article_v0.html",
        "ledger": tmp_path / "duplicate_ledger.jsonl",
    }


def _fake_photo_success(sent: list[dict[str, object]]):
    def fake_telegram_photo_send(**kwargs):
        sent.append(kwargs)
        assert "message" not in kwargs
        assert kwargs["dry_run"] is False
        assert kwargs["parse_mode"] == "HTML"
        assert Path(str(kwargs["photo_url"])).exists()
        assert REQUIRED_CAVEAT in str(kwargs["caption"])
        assert "Article fallback:" in str(kwargs["caption"])
        assert kwargs["approval_context"]["operator_approval_marker"]["approved_public_dispatch"] is True
        return {
            "status": "SUCCESS",
            "platform": "telegram",
            "action": "photo",
            "id": "321",
            "response": {"ok": True, "result": {"message_id": 321}},
        }

    return fake_telegram_photo_send


def test_root_cause_report_detects_previous_text_only_telegram_run():
    report, markdown = build_root_cause_report(ROOT)

    assert report["previous_defective_telegram_message_id"] == "59"
    assert report["previous_telegram_text_only_detected"] is True
    assert report["previous_telegram_missing_image"] is True
    assert report["previous_telegram_missing_article_link_or_fallback"] is True
    assert "text-only" in markdown
    assert "Build a ContentOps-owned source-backed FRED/EIA chart pack from data" in markdown


def test_media_builder_uses_contentops_chart_pipeline_and_generates_three_assets(monkeypatch, tmp_path):
    _install_fake_visual_pack(monkeypatch)

    manifest = build_oil_export_media_assets(output_dir=tmp_path / "media_assets")

    assert manifest["contentops_built_media"] is True
    assert manifest["chart_assets_built"] is True
    assert manifest["ai_generated_image"] is False
    assert manifest["static_generated_card"] is False
    assert manifest["new_image_generated"] is False
    assert manifest["media_asset_count"] == 3
    assert manifest["minimum_required_media_asset_count"] == 3
    assert manifest["assets_spread_required"] is True
    assert manifest["media_source_kind"] == "contentops_built_fred_eia_chart_pack"
    assert manifest["generation_method"] == "live_contentops.media_content_audit_v6.build_current_macro_visual_pack"
    assert manifest["google_image_fallback_attempted"] is False
    assert manifest["google_image_fallback_required"] is False
    assert len(manifest["assets"]) == 3
    for asset in manifest["assets"]:
        media_path = Path(asset["path"])
        assert media_path.exists()
        assert _png_dimensions(media_path)[0] >= 1201
        assert len(asset["sha256"]) == 64
        assert asset["rights_status"] == "source_backed_generated_visual_cc_owned"
        assert asset["provenance_status"] == "source_backed_generated_from_public_data"


def test_media_builder_fails_closed_when_chart_pipeline_returns_too_few_assets(monkeypatch, tmp_path):
    import live_contentops.media_content_audit_v6 as media_audit

    monkeypatch.setattr(media_audit, "build_current_macro_visual_pack", lambda *args, **kwargs: [])

    with pytest.raises(ValueError, match="contentops_media_pipeline_produced_fewer_than_three_assets"):
        build_oil_export_media_assets(output_dir=tmp_path / "media_assets")


def test_article_export_embeds_three_visuals_spread_through_article(monkeypatch, tmp_path):
    _install_fake_visual_pack(monkeypatch)
    media = build_oil_export_media_assets(output_dir=tmp_path / "media_assets")

    article_manifest = export_article_from_candidate_draft(
        repo_root=ROOT,
        media_manifest=media,
        article_md_path=tmp_path / "article.md",
        article_html_path=tmp_path / "article.html",
    )

    article = Path(article_manifest["article_export_path"]).read_text(encoding="utf-8")
    html = Path(article_manifest["article_html_export_path"]).read_text(encoding="utf-8")
    assert article.count("![") == 3
    assert article_manifest["visual_asset_count"] == 3
    assert article_manifest["visual_placement_status"] == "PASS_VISUALS_SPREAD_THROUGH_ARTICLE"
    assert article_manifest["visuals_spread_through_article"] is True
    assert article.find(media["assets"][0]["path"].replace("\\", "/")) < article.find("## Why This Matters")
    assert article.find(media["assets"][1]["path"].replace("\\", "/")) < article.find("## Strategic Petroleum Reserve Context")
    assert article.find(media["assets"][2]["path"].replace("\\", "/")) < article.find("## Editorial Use")
    assert html.count("<img ") == 3
    assert REQUIRED_CAVEAT in article


def test_runner_exports_article_and_repairs_telegram_with_contentops_chart_photo(monkeypatch, tmp_path):
    _install_fake_visual_pack(monkeypatch)
    paths = _run_paths(tmp_path)
    sent: list[dict[str, object]] = []

    result = run_full_pipeline_north_star_debug_and_live_run(
        repo_root=ROOT,
        output_dir=paths["output_dir"],
        article_md_path=paths["article_md_path"],
        article_html_path=paths["article_html_path"],
        duplicate_ledger_path=paths["ledger"],
        operator_approved_full_live_run=True,
        repair_previous_telegram_message_id="59",
        max_send_attempts_per_platform=1,
        telegram_photo_send_func=_fake_photo_success(sent),
        current_head="c5448c26ede0afdf2b50d7ce2abc800dbe1dca45",
        started_at="2026-07-10T00:00:00+00:00",
    )

    media = result["generated_media_manifest"]
    assert result["classification"] == CLASSIFICATION_PARTIAL
    assert paths["article_md_path"].exists()
    assert paths["article_html_path"].exists()
    article = paths["article_md_path"].read_text(encoding="utf-8")
    assert REQUIRED_CAVEAT in article
    assert "not financial, investment, trading, or portfolio advice" in article
    assert article.count("![") == 3
    assert sent and Path(str(sent[0]["photo_url"])) == Path(str(media["path"]))
    assert "source-backed chart media" in str(sent[0]["caption"])
    assert "Article fallback:" in str(sent[0]["caption"])
    dispatch = result["full_live_dispatch_results"]
    assert dispatch["contentops_built_media"] is True
    assert dispatch["chart_assets_built"] is True
    assert dispatch["media_asset_count"] == 3
    assert dispatch["media_generated"] is True
    assert dispatch["media_source_kind"] == "contentops_built_fred_eia_chart_pack"
    assert dispatch["ai_generated_image"] is False
    assert dispatch["static_generated_card"] is False
    assert dispatch["new_image_generated"] is False
    assert dispatch["article_visual_asset_count"] == 3
    assert dispatch["article_visuals_spread_through_article"] is True
    assert dispatch["telegram_repair_status"] == "REPAIRED_WITH_PHOTO"
    assert dispatch["telegram_image_attached"] is True
    assert dispatch["telegram_link_or_article_fallback_included"] is True
    assert dispatch["duplicate_guard_result"] == "PASS"
    assert dispatch["substack_status"] == "SKIPPED_REQUIRES_OPERATOR_BROWSER_ASSIST"
    assert dispatch["x_status"] == "SKIPPED_REQUIRES_OPERATOR_BROWSER_ASSIST"
    assert result["full_live_safety_review"]["text_only_live_output_repaired"] is True


def test_telegram_repair_payload_requires_image_and_article_fallback(monkeypatch, tmp_path):
    _install_fake_visual_pack(monkeypatch)
    media = build_oil_export_media_assets(output_dir=tmp_path / "media_assets")
    article_manifest = {
        "public_article_url": None,
        "article_fallback_reference": str(tmp_path / "article.md"),
        "article_export_path": str(tmp_path / "article.md"),
    }
    caption, content_hash = build_telegram_repair_caption(
        article_manifest=article_manifest,
        media_manifest=media,
        previous_message_id="59",
    )

    assert REQUIRED_CAVEAT in caption
    assert "Article fallback:" in caption
    assert len(content_hash) == 16

    no_image = dict(media)
    no_image.pop("path")
    with pytest.raises(ValueError, match="requires_image_path"):
        build_telegram_repair_caption(
            article_manifest=article_manifest,
            media_manifest=no_image,
            previous_message_id="59",
        )

    with pytest.raises(ValueError, match="requires_article_url_or_fallback"):
        build_telegram_repair_caption(
            article_manifest={"public_article_url": None, "article_fallback_reference": None},
            media_manifest=media,
            previous_message_id="59",
        )


def test_duplicate_guard_prevents_repeat_repair_and_text_only_adapter_path(monkeypatch, tmp_path):
    _install_fake_visual_pack(monkeypatch)
    paths = _run_paths(tmp_path)
    sent: list[dict[str, object]] = []
    run_full_pipeline_north_star_debug_and_live_run(
        repo_root=ROOT,
        output_dir=paths["output_dir"] / "first",
        article_md_path=paths["article_md_path"],
        article_html_path=paths["article_html_path"],
        duplicate_ledger_path=paths["ledger"],
        operator_approved_full_live_run=True,
        repair_previous_telegram_message_id="59",
        max_send_attempts_per_platform=1,
        telegram_photo_send_func=_fake_photo_success(sent),
        current_head="c5448c26ede0afdf2b50d7ce2abc800dbe1dca45",
        started_at="2026-07-10T00:00:00+00:00",
    )

    def should_not_send(**kwargs):
        raise AssertionError("duplicate guard should block before any Telegram adapter call")

    second = run_full_pipeline_north_star_debug_and_live_run(
        repo_root=ROOT,
        output_dir=paths["output_dir"] / "second",
        article_md_path=paths["article_md_path"],
        article_html_path=paths["article_html_path"],
        duplicate_ledger_path=paths["ledger"],
        operator_approved_full_live_run=True,
        repair_previous_telegram_message_id="59",
        max_send_attempts_per_platform=1,
        telegram_photo_send_func=should_not_send,
        current_head="c5448c26ede0afdf2b50d7ce2abc800dbe1dca45",
        started_at="2026-07-10T00:01:00+00:00",
    )

    assert sent and "photo_url" in sent[0]
    assert "message" not in sent[0]
    assert second["classification"] == CLASSIFICATION_BLOCKED
    assert second["full_live_dispatch_results"]["telegram_repair_status"] == "FAILED_DUPLICATE_GUARD_BLOCKED"
    assert "duplicate_topic_hash" in second["full_live_dispatch_results"]["duplicate_guard_blockers"]


def test_outputs_have_explicit_skips_and_no_secret_or_advice_claims(monkeypatch, tmp_path):
    _install_fake_visual_pack(monkeypatch)
    paths = _run_paths(tmp_path)
    result = run_full_pipeline_north_star_debug_and_live_run(
        repo_root=ROOT,
        output_dir=paths["output_dir"],
        article_md_path=paths["article_md_path"],
        article_html_path=paths["article_html_path"],
        duplicate_ledger_path=paths["ledger"],
        operator_approved_full_live_run=True,
        repair_previous_telegram_message_id="59",
        max_send_attempts_per_platform=1,
        telegram_photo_send_func=_fake_photo_success([]),
        current_head="c5448c26ede0afdf2b50d7ce2abc800dbe1dca45",
        started_at="2026-07-10T00:00:00+00:00",
    )

    assert result["full_live_dispatch_results"]["substack_status"] in {
        "SKIPPED_NO_SAFE_ADAPTER",
        "SKIPPED_REQUIRES_OPERATOR_BROWSER_ASSIST",
        "BLOCKED_CREDENTIAL_UNAVAILABLE",
        "FAILED_SAFE_ATTEMPT",
    }
    assert result["full_live_dispatch_results"]["x_status"] in {
        "SKIPPED_NO_SAFE_ADAPTER",
        "SKIPPED_REQUIRES_OPERATOR_BROWSER_ASSIST",
        "BLOCKED_CREDENTIAL_UNAVAILABLE",
        "FAILED_SAFE_ATTEMPT",
    }
    safety = result["full_live_safety_review"]
    assert safety["raw_secret_printed"] is False
    assert safety["browser_session_secret_dumped"] is False
    assert safety["exact_numeric_claims_made"] is False
    assert safety["financial_advice_detected"] is False
    assert safety["trading_signal_detected"] is False
    assert safety["price_target_detected"] is False
    assert safety["contentops_built_media"] is True
    assert safety["media_asset_count"] == 3
    assert safety["article_visuals_spread_through_article"] is True

    combined = json.dumps(result, sort_keys=True, default=str) + "\n" + paths["article_md_path"].read_text(encoding="utf-8")
    forbidden = [
        r"https://discord(?:app)?\.com/api/webhooks/",
        r"\b\d{6,12}:[A-Za-z0-9_-]{20,}\b",
        r"\bsk-[A-Za-z0-9_-]{20,}\b",
        r"\bBearer\s+[A-Za-z0-9._-]{12,}\b",
        r"cookie\s*[:=]",
        r"localStorage\s*[:=]",
        r"sessionStorage\s*[:=]",
        r"browser session data\s*[:=]",
    ]
    assert not any(re.search(pattern, combined, re.IGNORECASE) for pattern in forbidden)
    numeric_truth = r"\b\d+(?:\.\d+)?\s*(million|billion|barrels?|bpd|mb/d|percent|%|basis points?|dollars?|usd)\b"
    assert not re.search(numeric_truth, paths["article_md_path"].read_text(encoding="utf-8"), re.IGNORECASE)
    assert not re.search(r"\b(buy|sell|hold|short|go long|go short|price target|position sizing)\b", combined, re.IGNORECASE)
