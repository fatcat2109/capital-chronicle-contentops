# -*- coding: utf-8 -*-
"""Tests for the full north-star debug and live repair runner."""
from __future__ import annotations

import json
import re
import struct
from pathlib import Path

from live_contentops.full_pipeline_north_star_debug_and_live_run_v0 import (
    CLASSIFICATION_BLOCKED,
    CLASSIFICATION_PARTIAL,
    REQUIRED_CAVEAT,
    build_root_cause_report,
    build_telegram_repair_caption,
    generate_oil_export_hero_card,
    run_full_pipeline_north_star_debug_and_live_run,
)


ROOT = Path(__file__).resolve().parents[1]


def _png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", data[16:24])


def _run_paths(tmp_path: Path) -> dict[str, Path]:
    return {
        "output_dir": tmp_path / "evidence",
        "media_path": tmp_path / "generated_media" / "daily_contentops" / "oil_export_surge_hero_card_v0.png",
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


def test_media_generation_creates_real_png_manifest(tmp_path):
    media_path = tmp_path / "oil_export_surge_hero_card_v0.png"
    manifest = generate_oil_export_hero_card(media_path)

    assert manifest["media_generated"] is True
    assert media_path.exists()
    assert _png_dimensions(media_path) == (1200, 675)
    assert manifest["dimensions"] == {"width": 1200, "height": 675}
    assert len(manifest["sha256"]) == 64
    assert manifest["label_visible"] == "Candidate editorial"


def test_runner_exports_article_and_repairs_telegram_with_photo(tmp_path):
    paths = _run_paths(tmp_path)
    sent: list[dict[str, object]] = []

    result = run_full_pipeline_north_star_debug_and_live_run(
        repo_root=ROOT,
        output_dir=paths["output_dir"],
        media_path=paths["media_path"],
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

    assert result["classification"] == CLASSIFICATION_PARTIAL
    assert paths["article_md_path"].exists()
    assert paths["article_html_path"].exists()
    article = paths["article_md_path"].read_text(encoding="utf-8")
    assert REQUIRED_CAVEAT in article
    assert "not financial, investment, trading, or portfolio advice" in article
    assert sent and Path(str(sent[0]["photo_url"])) == paths["media_path"]
    assert "Article fallback:" in str(sent[0]["caption"])
    dispatch = result["full_live_dispatch_results"]
    assert dispatch["telegram_repair_status"] == "REPAIRED_WITH_PHOTO"
    assert dispatch["telegram_image_attached"] is True
    assert dispatch["telegram_link_or_article_fallback_included"] is True
    assert dispatch["duplicate_guard_result"] == "PASS"
    assert dispatch["substack_status"] == "SKIPPED_REQUIRES_OPERATOR_BROWSER_ASSIST"
    assert dispatch["x_status"] == "SKIPPED_REQUIRES_OPERATOR_BROWSER_ASSIST"
    assert result["full_live_safety_review"]["text_only_live_output_repaired"] is True


def test_telegram_repair_payload_requires_image_and_article_fallback(tmp_path):
    media = generate_oil_export_hero_card(tmp_path / "card.png")
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
    try:
        build_telegram_repair_caption(
            article_manifest=article_manifest,
            media_manifest=no_image,
            previous_message_id="59",
        )
    except ValueError as exc:
        assert "requires_image_path" in str(exc)
    else:
        raise AssertionError("missing image path must block Telegram repair")

    try:
        build_telegram_repair_caption(
            article_manifest={"public_article_url": None, "article_fallback_reference": None},
            media_manifest=media,
            previous_message_id="59",
        )
    except ValueError as exc:
        assert "requires_article_url_or_fallback" in str(exc)
    else:
        raise AssertionError("missing article reference must block Telegram repair")


def test_duplicate_guard_prevents_repeat_repair_and_text_only_adapter_path(tmp_path):
    paths = _run_paths(tmp_path)
    sent: list[dict[str, object]] = []
    run_full_pipeline_north_star_debug_and_live_run(
        repo_root=ROOT,
        output_dir=paths["output_dir"] / "first",
        media_path=paths["media_path"],
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
        media_path=paths["media_path"],
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
    assert "duplicate_payload_hash" in second["full_live_dispatch_results"]["duplicate_guard_blockers"]


def test_outputs_have_explicit_skips_and_no_secret_or_advice_claims(tmp_path):
    paths = _run_paths(tmp_path)
    result = run_full_pipeline_north_star_debug_and_live_run(
        repo_root=ROOT,
        output_dir=paths["output_dir"],
        media_path=paths["media_path"],
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
