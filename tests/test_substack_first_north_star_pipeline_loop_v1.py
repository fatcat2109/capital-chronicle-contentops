from __future__ import annotations

import json
from pathlib import Path

from live_contentops.substack_browser_adapter_v6 import (
    build_supervised_substack_browser_readback,
    validate_supervised_substack_browser_readback,
)
from live_contentops.substack_first_north_star_pipeline_loop_v1 import (
    BLOCKED_CLASSIFICATION,
    PASS_PARTIAL_CLASSIFICATION,
    complete_substack_first_pipeline,
    prepare_substack_first_pipeline,
)


def _candidate(slot_index: int, rank: int, family: str) -> dict:
    return {
        "slot_index": slot_index,
        "rank": rank,
        "article_family": family,
        "title": "The Fed Funds Signal and the Market's Next Question" if slot_index == 6 else f"Unsupported candidate {slot_index}",
        "seo_title": "Fed funds policy transmission and market pricing" if slot_index == 6 else f"Unsupported macro candidate {slot_index}",
        "slug": "fed-funds-policy-transmission" if slot_index == 6 else f"unsupported-candidate-{slot_index}",
        "dek": "Why an orderly policy anchor can still leave markets repricing growth, inflation, and duration risk." if slot_index == 6 else "This candidate lacks a supported media pack.",
        "thesis": "The policy anchor is useful because it separates money-market stability from the broader repricing in the curve." if slot_index == 6 else "This is not article ready.",
        "market_mechanism": "Funding conditions transmit through administered rates, the curve, credit, and discount-rate expectations." if slot_index == 6 else "No supported mechanism.",
        "policy_context": "Official policy settings frame the discussion, while the broader market still prices uncertainty in other channels." if slot_index == 6 else "No supported policy context.",
        "cross_asset_implications": "Cross-asset moves should be read as a map of repricing channels, not as a trading instruction." if slot_index == 6 else "No supported cross-asset context.",
        "breaking_or_hotspot": False,
        "why_ranked": "The current schedule has a fresh central-bank signal and the system can build three data charts from documented sources." if slot_index == 6 else "Rejected by support check.",
    }


def _fake_ranker(_prompt: str, _provider: str) -> dict:
    return {
        "selection_rationale": "The rates item is the only current slot with a complete three-chart source-backed support path.",
        "ranked_candidates": [
            _candidate(6, 1, "fed_funds"),
            _candidate(1, 2, "unsupported"),
            _candidate(2, 3, "unsupported"),
            _candidate(3, 4, "unsupported"),
            _candidate(4, 5, "unsupported"),
            _candidate(5, 6, "unsupported"),
        ],
    }


def _fake_visual_builder(_topic: str, output_dir: Path, as_of_date=None) -> list[dict]:
    del as_of_date
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for asset_id in ("primary", "policy_corridor", "sofr_context"):
        path = output_dir / f"{asset_id}.png"
        path.write_bytes(b"source-backed-chart-fixture")
        rows.append(
            {
                "asset_id": asset_id,
                "local_path": str(path),
                "media_class": "data_chart",
                "media_role": "chart",
                "source_label": "FRED / Federal Reserve",
                "source_page_url": "https://www.federalreserve.gov/monetarypolicy/openmarket.htm" if asset_id == "policy_corridor" else "https://fred.stlouisfed.org/series/DFF",
                "provenance_status": "source_backed_generated_from_public_data",
                "caption": f"{asset_id} chart. Source: FRED / Federal Reserve.",
                "alt_text": f"{asset_id} source-backed chart",
                "why_selected": "Tests three in-body source-backed charts.",
                "latest_observation_value": 3.62,
                "latest_observation_date": "2026-07-08",
                "prior_observation_value": 3.63,
                "prior_observation_date": "2026-07-07",
                "target_lower": 3.50,
                "target_upper": 3.75,
            }
        )
    return rows


def _prepare(tmp_path: Path) -> tuple[dict, Path, Path]:
    output_dir = tmp_path / "evidence"
    result = prepare_substack_first_pipeline(
        run_id="substack_first_test_run",
        publication_mode="draft",
        output_dir=output_dir,
        llm_provider="9router",
        llm_ranker=_fake_ranker,
        visual_builder=_fake_visual_builder,
        export_root=tmp_path / "exports",
    )
    assert result["classification"] == "READY_FOR_SUPERVISED_SUBSTACK_BROWSER_ASSIST"
    return result, output_dir / "run_context_v1.json", output_dir / "substack_browser_request_v1.json"


def test_prepare_uses_llm_ranking_then_requires_three_chart_media(tmp_path: Path):
    _result, context_path, request_path = _prepare(tmp_path)
    context = json.loads(context_path.read_text(encoding="utf-8"))
    request = json.loads(request_path.read_text(encoding="utf-8"))

    assert context["selection"]["slot_index"] == 6
    assert context["selection"]["title"] == "Effective Fed Funds Rate Holds at 3.62% as Policy Calibration Continues"
    assert "3.62% on 2026-07-08" in context["article"]["substack_body_markdown"]
    assert "printed at 3.63%" not in context["article"]["substack_body_markdown"]
    assert "3.63%" not in context["selection"]["market_mechanism"]
    assert context["media"]["media_asset_count"] == 3
    assert {asset["media_class"] for asset in context["media"]["assets"]} == {"data_chart"}
    assert context["article"]["word_count"] >= 1200
    assert context["article"]["visuals_spread_through_article"] is True
    assert request["publication_mode"] == "draft"
    assert request["visual_marker_order"] == ["primary", "policy_corridor", "sofr_context"]


def test_complete_refuses_telegram_until_substack_readback_then_repairs_existing_post(tmp_path: Path):
    _result, context_path, request_path = _prepare(tmp_path)
    request = json.loads(request_path.read_text(encoding="utf-8"))
    readback_path = request_path.with_name("substack_browser_readback_v1.json")
    build_supervised_substack_browser_readback(
        request=request,
        publication_state="draft",
        article_url="https://capitalchronicle.substack.com/p/draft-test-123?preview=1",
        editor_body_image_count=3,
        in_body_visual_asset_ids=["primary", "policy_corridor", "sofr_context"],
        output_path=readback_path,
    )
    calls = []

    def fake_caption_editor(**kwargs):
        calls.append(kwargs)
        return {"status": "SUCCESS", "platform": "telegram", "action": "edit_caption", "id": kwargs["message_id"], "media_attached": True, "response": {"ok": True, "result": {"message_id": int(kwargs["message_id"])}}}

    evidence = complete_substack_first_pipeline(
        context_path=context_path,
        substack_readback_path=readback_path,
        operator_approved_full_live_run=True,
        ledger_path=tmp_path / "ledger.jsonl",
        telegram_caption_editor=fake_caption_editor,
    )

    assert evidence["classification"] == PASS_PARTIAL_CLASSIFICATION
    assert evidence["substack"]["status"] == "SUCCESS"
    assert evidence["telegram"]["action"] == "edit_caption"
    assert evidence["telegram"]["substack_url_included"] is True
    assert calls and "https://capitalchronicle.substack.com/p/draft-test-123?preview=1" in calls[0]["caption"]
    assert evidence["x"]["status"].startswith("BLOCKED_")


def test_invalid_substack_readback_blocks_before_any_telegram_action(tmp_path: Path):
    _result, context_path, request_path = _prepare(tmp_path)
    request = json.loads(request_path.read_text(encoding="utf-8"))
    readback_path = request_path.with_name("substack_browser_readback_v1.json")
    build_supervised_substack_browser_readback(
        request=request,
        publication_state="draft",
        article_url="https://capitalchronicle.substack.com/p/draft-test-123?preview=1",
        editor_body_image_count=2,
        in_body_visual_asset_ids=["primary", "policy_corridor", "sofr_context"],
        output_path=readback_path,
    )
    calls = []
    evidence = complete_substack_first_pipeline(
        context_path=context_path,
        substack_readback_path=readback_path,
        operator_approved_full_live_run=True,
        ledger_path=tmp_path / "ledger.jsonl",
        telegram_caption_editor=lambda **kwargs: calls.append(kwargs),
    )

    assert evidence["classification"] == BLOCKED_CLASSIFICATION
    assert evidence["telegram"]["status"] == "BLOCKED_PRE_TELEGRAM_DERIVATIVE"
    assert calls == []


def test_substack_readback_rejects_browser_secret_material(tmp_path: Path):
    _result, _context_path, request_path = _prepare(tmp_path)
    request = json.loads(request_path.read_text(encoding="utf-8"))
    readback = {
        "schema_version": "contentops.substack_supervised_browser_readback.v1",
        "status": "SUCCESS",
        "run_id": request["run_id"],
        "publication_state": "draft",
        "draft_url": "https://capitalchronicle.substack.com/p/draft-test-123?preview=1",
        "title": request["title"],
        "body_markdown_sha256": request["body_markdown_sha256"],
        "editor_body_image_count": 3,
        "in_body_visual_asset_ids": request["visual_marker_order"],
        "cookie_value": "must never be recorded",
    }
    result = validate_supervised_substack_browser_readback(request, readback)

    assert result["status"].startswith("BLOCKED_")
    assert "substack_readback_contains_sensitive_browser_material" in result["blockers"]


def test_private_substack_editor_url_cannot_be_used_for_a_draft_readback(tmp_path: Path):
    _result, _context_path, request_path = _prepare(tmp_path)
    request = json.loads(request_path.read_text(encoding="utf-8"))

    try:
        build_supervised_substack_browser_readback(
            request=request,
            publication_state="draft",
            article_url="https://capitalchronicle.substack.com/publish/post/draft-test-123",
            editor_body_image_count=3,
            in_body_visual_asset_ids=request["visual_marker_order"],
            output_path=tmp_path / "private_editor_readback.json",
        )
    except ValueError as error:
        assert str(error) == "substack_readback_requires_externally_usable_preview_or_public_url"
    else:
        raise AssertionError("private editor URLs must not pass draft readback")
