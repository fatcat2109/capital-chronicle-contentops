import json
import zlib
from pathlib import Path

from live_contentops.public_dispatch_freeze_guard_v6 import load_public_dispatch_hashes
from live_contentops.terra_ultra_north_star_full_automation_v1 import (
    BLOCKED_CLASSIFICATION,
    PASS_PARTIAL_CLASSIFICATION,
    REQUIRED_CAVEAT,
    build_media_pack,
    export_article,
    load_headline_context,
    run_terra_ultra_north_star_full_automation,
    select_north_star_idea,
)


def _png_bytes(width=640, height=360):
    raw = b"".join(b"\x00" + b"\xff\xff\xff" * width for _ in range(height))
    compressor = zlib.compressobj()
    data = compressor.compress(raw) + compressor.flush()

    def chunk(kind, payload):
        import struct

        crc = zlib.crc32(kind + payload) & 0xFFFFFFFF
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", crc)

    import struct

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", data)
        + chunk(b"IEND", b"")
    )


def _fake_visual_builder(topic, output_dir, as_of_date=None):
    del as_of_date
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    assets = []
    for idx, asset_id in enumerate(["primary", "policy_corridor", "sofr_context"], start=1):
        path = out / f"fed_funds_test_{asset_id}.png"
        path.write_bytes(_png_bytes())
        assets.append(
            {
                "asset_id": asset_id,
                "media_class": "data_chart" if idx != 2 else "policy_diagram",
                "media_role": "primary_chart",
                "source_label": "FRED / Federal Reserve Board",
                "canonical_source_label": "FRED series DFF; source Board of Governors of the Federal Reserve System H.15",
                "source_page_url": "https://fred.stlouisfed.org/series/DFF",
                "rights_status": "source_backed_generated_visual_cc_owned",
                "provenance_status": "source_backed_generated_from_public_federal_reserve_data",
                "content_authority_scope": "TEMPORARY_CONTENTOPS_FALLBACK_FIXTURE",
                "caption": f"Fed funds fixture chart {idx}. Source: FRED and Federal Reserve.",
                "alt_text": f"Fed funds chart {idx}",
                "why_selected": "Required spread visual for non-oil rates article.",
                "local_path": str(path),
            }
        )
    assert "fed funds" in str(topic).lower()
    return assets


def test_selection_chooses_fed_funds_and_rejects_oil_duplicate_lane(tmp_path):
    context = load_headline_context(output_dir=tmp_path)
    selection = select_north_star_idea(context, output_dir=tmp_path, ledger_path=tmp_path / "ledger.jsonl")

    assert "fed funds" in selection["selected_topic"].lower()
    assert "oil_family_duplicate_frozen_not_breaking_enough" in selection["why_selected"]
    assert selection["duplicate_hotspot_decision"]["oil_family_status"] == "DUPLICATE_FROZEN_SUPERSEDED_BY_FRESH_NON_OIL_TOPIC"
    assert selection["duplicate_hotspot_decision"]["selected_topic_dispatch_allowed"] is True


def test_media_builder_requires_three_assets_and_article_spreads_visuals(tmp_path):
    selection = {
        "selected_topic": "Effective fed funds rate: 3.63% July 7th vs 3.63% July 6th",
        "selected_title": "The Fed Funds Signal Hiding in Plain Sight",
        "selected_angle": "Frame the policy signal against rates, inflation expectations, and market-pricing limits.",
    }
    support = {
        "source_trail": [
            {"path": "schedule.json"},
            {"path": "sidecars.jsonl"},
        ]
    }
    media = build_media_pack(
        selection,
        output_dir=tmp_path / "media",
        evidence_output_dir=tmp_path,
        visual_builder=_fake_visual_builder,
    )
    article = export_article(
        selection,
        support,
        media,
        article_md_path=tmp_path / "article.md",
        article_html_path=tmp_path / "article.html",
        evidence_output_dir=tmp_path,
    )

    assert media["media_gate_status"] == "PASS"
    assert media["media_asset_count"] == 3
    assert media["contentops_built_media"] is True
    assert article["visual_asset_count"] == 3
    assert article["visuals_spread_through_article"] is True
    assert article["visual_placement_status"] == "PASS_VISUALS_SPREAD_THROUGH_ARTICLE"


def test_runner_partial_pass_sends_telegram_photo_and_blocks_browser_platforms(tmp_path):
    calls = []

    def fake_telegram(**kwargs):
        calls.append(kwargs)
        return {
            "status": "SUCCESS",
            "platform": "telegram",
            "action": "photo",
            "id": "98765",
            "response": {"ok": True, "result": {"message_id": 98765, "photo": [{"file_id": "redacted"}]}},
        }

    evidence = run_terra_ultra_north_star_full_automation(
        operator_approved_full_live_run=True,
        max_send_attempts_per_platform=1,
        run_id="test_terra_partial_pass",
        output_dir=tmp_path / "evidence",
        article_md_path=tmp_path / "evidence" / "article.md",
        article_html_path=tmp_path / "evidence" / "article.html",
        ledger_path=tmp_path / "ledger.jsonl",
        telegram_photo_executor=fake_telegram,
        visual_builder=_fake_visual_builder,
    )

    assert evidence["classification"] == PASS_PARTIAL_CLASSIFICATION
    assert calls and Path(calls[0]["photo_url"]).exists()
    assert calls[0]["dry_run"] is False
    assert REQUIRED_CAVEAT in calls[0]["caption"]
    assert "Full local article fallback:" in calls[0]["caption"]
    assert evidence["telegram"]["message_id"] == "98765"
    assert evidence["telegram"]["image_attached"] is True
    assert evidence["substack"]["status"].startswith("BLOCKED_")
    assert evidence["x"]["status"].startswith("BLOCKED_")
    assert load_public_dispatch_hashes(tmp_path / "ledger.jsonl")["topic_hashes"]


def test_duplicate_guard_blocks_second_run_before_adapter_call(tmp_path):
    call_count = 0

    def fake_telegram(**kwargs):
        nonlocal call_count
        call_count += 1
        return {
            "status": "SUCCESS",
            "platform": "telegram",
            "action": "photo",
            "id": f"msg_{call_count}",
            "response": {"ok": True, "result": {"message_id": call_count, "photo": [{"file_id": "redacted"}]}},
        }

    ledger = tmp_path / "ledger.jsonl"
    first = run_terra_ultra_north_star_full_automation(
        operator_approved_full_live_run=True,
        run_id="test_terra_duplicate_first",
        output_dir=tmp_path / "first",
        article_md_path=tmp_path / "first" / "article.md",
        article_html_path=tmp_path / "first" / "article.html",
        ledger_path=ledger,
        telegram_photo_executor=fake_telegram,
        visual_builder=_fake_visual_builder,
    )
    second = run_terra_ultra_north_star_full_automation(
        operator_approved_full_live_run=True,
        run_id="test_terra_duplicate_second",
        output_dir=tmp_path / "second",
        article_md_path=tmp_path / "second" / "article.md",
        article_html_path=tmp_path / "second" / "article.html",
        ledger_path=ledger,
        telegram_photo_executor=fake_telegram,
        visual_builder=_fake_visual_builder,
    )

    assert first["classification"] == PASS_PARTIAL_CLASSIFICATION
    assert second["classification"] == BLOCKED_CLASSIFICATION
    assert second["telegram"]["status"] == "BLOCKED_PRE_TELEGRAM_ADAPTER"
    assert "duplicate_topic_hash" in second["telegram"]["duplicate_guard"]["blockers"]
    assert call_count == 1


def test_outputs_have_no_advice_or_secret_markers(tmp_path):
    evidence = run_terra_ultra_north_star_full_automation(
        operator_approved_full_live_run=False,
        run_id="test_terra_safety",
        output_dir=tmp_path / "safety",
        article_md_path=tmp_path / "safety" / "article.md",
        article_html_path=tmp_path / "safety" / "article.html",
        ledger_path=tmp_path / "ledger.jsonl",
        telegram_photo_executor=lambda **kwargs: {"status": "SHOULD_NOT_SEND"},
        visual_builder=_fake_visual_builder,
    )

    assert evidence["classification"] == BLOCKED_CLASSIFICATION
    assert evidence["safety"]["financial_advice_detected"] is False
    assert evidence["safety"]["forbidden_secret_material_detected"] is False
    article_text = Path(evidence["article"]["article_export_path"]).read_text(encoding="utf-8")
    blob = json.dumps(evidence) + article_text
    assert "not financial advice" not in blob.lower()
    assert "TELEGRAM_BOT_TOKEN=" not in blob
