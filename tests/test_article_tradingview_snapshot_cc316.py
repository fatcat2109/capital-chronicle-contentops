"""Article -> frozen plan -> actual transport inputs. All captures/transports are controlled."""
from copy import deepcopy
import json
from pathlib import Path
import shutil

import pytest

from live_contentops import tradingview_snapshot_v1 as tv
from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as pipeline
from live_contentops.destination_transport_registry_v1 import V1_REQUIRED_DERIVATIVE_DESTINATIONS
from live_contentops.rolling_x_grounded_article_media_builder_v1 import build_post_image_card, post_image_view
from live_contentops.v1_simple_gemini_newsroom_v1 import _build_simple_publication_lifecycle_plan, _native_preview_bundle
from test_post_image_policy_v1 import packet

FIXTURE = Path(__file__).parent / "fixtures/cc314/SPX500USD_2026-11-05_13-21-11.png"
CANONICAL = "https://capitalchronicle.substack.com/p/cc316-controlled"


@pytest.fixture
def capture(monkeypatch, tmp_path):
    """The saved US500 image tests byte transport; other symbols test mapping only."""
    original = tv.capture
    calls = []
    def controlled(market, interval, folder):
        calls.append((market, interval))
        def worker(args):
            folder = Path(args["out_dir"])
            name = tv.SYMBOLS[market].split(":")[1] + "_2026-11-05_13-21-11.png"
            target = folder / name
            shutil.copyfile(FIXTURE, target)
            return {"path": str(target), "suggested_filename": name, "legend": "4h",
                    "captured_at_utc": "2026-11-05T13:21:11Z"}
        return original(market, interval, folder, worker=worker)
    monkeypatch.setattr(tv, "capture", controlled)
    monkeypatch.setattr(tv, "OUTCOMES", tmp_path / "outcomes.jsonl")
    return calls


def prepared(tmp_path, *, release=False, market="US500"):
    article = {**packet()["article"], "market_asset": market, "resolved_article_mode": "BREAKING_BRIEF"}
    assets = []
    if release:
        assets = [build_post_image_card(article, output_dir=tmp_path / "cards", accepted_evidence_sha256="a" * 64)]
    return tv.prepare_article_snapshot(article, assets, output_dir=tmp_path)


def plan_for(tmp_path, article, assets):
    previews, _ = _native_preview_bundle(article=article, article_mode="BREAKING_BRIEF", article_identity="b" * 64,
        media_asset_ids=[a["asset_id"] for a in assets], media_assets=assets)
    plan = _build_simple_publication_lifecycle_plan(run_id="cc316", output_dir=tmp_path,
        selected_candidate={"story_identity": "cc316"}, selected_plan_entry={"article_mode": "BREAKING_BRIEF"},
        article=article, article_identity="b" * 64, native_previews=previews,
        qualified_record={"accepted_evidence_ids": [], "accepted_evidence_sha256": "a" * 64},
        epistemic_state=None, media_assets=assets)
    return plan, previews


@pytest.mark.parametrize("market", list(tv.SYMBOLS))
def test_daily_market_freezes_and_delivers_snapshot_to_every_image_destination(tmp_path, capture, market):
    article, assets = prepared(tmp_path, market=market)
    plan, previews = plan_for(tmp_path, article, assets)
    snapshot_id = article["tradingview_snapshot_asset_ids"][0]
    context = json.loads((tmp_path / "run_context_v1.json").read_bytes())
    assert context["article"]["market_asset"] == market
    assert context["media"]["assets"][0]["asset_id"] == snapshot_id
    assert context["media"]["delivery_only_assets"][0]["asset_id"] == snapshot_id
    for destination in V1_REQUIRED_DERIVATIVE_DESTINATIONS:
        payload = previews["packages"][destination]
        assert payload["media_asset_ids"] == [snapshot_id]
        assert "Chart: TradingView" in (payload.get("full_text") or payload.get("text") or "")
        data = pipeline._durable_intent_inputs({"output_dir": str(tmp_path), "canonical_url": CANONICAL,
            "destination_plan": {"destination": destination}, "native_payload": payload})
        assert data["local_media"] == assets[0]["path"]
        assert data["media_assets"][0]["asset_id"] == snapshot_id
    # Immutable context/plan generated before any transport registers the package.
    assert plan["package_identity"] and capture == [(market, "240")]


def test_release_card_first_and_single_image_transports_include_the_snapshot(tmp_path, capture, monkeypatch):
    article, assets = prepared(tmp_path, release=True)
    assert assets[0]["post_card_binding"]
    snapshot, panel = assets[1:]
    assert snapshot["placement_after"] == "standfirst"
    assert panel["preceding_card"]["asset_id"] == assets[0]["asset_id"]
    tv.validate_snapshot_asset(panel, article)  # Verifies both originals' complete pixels.
    _, previews = plan_for(tmp_path, article, assets)
    canonical = pipeline._durable_intent_inputs({"output_dir": str(tmp_path), "canonical_url": CANONICAL,
        "destination_plan": {"destination": "substack"}})
    assert [a["asset_id"] for a in canonical["media_assets"]] == [assets[0]["asset_id"], snapshot["asset_id"]]
    from live_contentops.neo_destination_handoff_v1 import _payload_binding
    _, binding = _payload_binding({"output_dir": str(tmp_path), "canonical_url": CANONICAL,
        "destination_plan": {"destination": "substack"}}, "substack")
    assert binding["media_manifest"][1]["placement_after"] == "standfirst"
    observed = []
    monkeypatch.setattr(pipeline, "_publish_telegram_photo_verified", lambda **kw: observed.append(kw) or {"status": "SUCCESS"})
    intent = {"output_dir": str(tmp_path), "canonical_url": CANONICAL, "attempt_identity": "controlled",
        "work_item_id": "cc316", "destination_plan": {"destination": "telegram"},
        "native_payload": previews["packages"]["telegram"]}
    sent = pipeline._publish_one_destination_from_durable_intent(destination="telegram", intent=intent,
        authorization_context={"operating_mode": "AUTONOMOUS_DEFAULT", "dispatch_attempt_identity": "controlled"})
    assert sent["status"] == "SUCCESS" and observed[0]["image_path"] == panel["path"]
    assert "Chart: TradingView" in observed[0]["text"]
    view = post_image_view({"article": article, "media_assets": assets, "accepted_evidence_sha256": "a" * 64},
        output_dir=tmp_path / "view")
    assert not view["post_image_policy"]["excluded_optional_assets"]


def test_failed_capture_is_reused_and_current_card_still_reaches_publish(tmp_path, monkeypatch):
    calls = []
    def broken(*args):
        calls.append(args)
        raise tv.SnapshotError("TRADINGVIEW_SNAPSHOT_TIMEOUT")
    monkeypatch.setattr(tv, "capture", broken)
    monkeypatch.setattr(tv, "OUTCOMES", tmp_path / "outcomes.jsonl")
    article, assets = prepared(tmp_path, release=True)
    again, repeated = tv.prepare_article_snapshot(article, assets, output_dir=tmp_path)
    assert len(calls) == 1 and assets == repeated and len(assets) == 1
    assert again["tradingview_snapshot_outcome"]["cause"] == "TRADINGVIEW_SNAPSHOT_TIMEOUT"
    _, previews = plan_for(tmp_path, article, assets)
    observed = []
    monkeypatch.setattr(pipeline, "_publish_telegram_photo_verified", lambda **kw: observed.append(kw) or {"status": "SUCCESS"})
    result = pipeline._publish_one_destination_from_durable_intent(destination="telegram",
        intent={"output_dir": str(tmp_path), "canonical_url": CANONICAL, "attempt_identity": "controlled",
                "destination_plan": {"destination": "telegram"}, "native_payload": previews["packages"]["telegram"]},
        authorization_context={"operating_mode": "AUTONOMOUS_DEFAULT", "dispatch_attempt_identity": "controlled"})
    assert result["status"] == "SUCCESS" and observed[0]["image_path"] == assets[0]["path"]


def test_resume_reuses_download_and_rejects_changed_snapshot_bytes(tmp_path, capture):
    article, assets = prepared(tmp_path)
    again, repeated = prepared(tmp_path)
    assert article == again and assets == repeated and len(capture) == 1
    Path(assets[0]["path"]).write_bytes(b"changed")
    with pytest.raises(ValueError, match="BYTES_CHANGED"):
        tv.validate_snapshot_asset(assets[0], article)


def test_release_card_is_first_even_when_the_media_compiler_appended_it(tmp_path, capture):
    article = {**packet()["article"], "market_asset": "US500"}
    chart = build_post_image_card(article, output_dir=tmp_path / "chart", accepted_evidence_sha256="a" * 64)
    card = {**deepcopy(chart), "asset_id": "controlled-appended-release-card", "modality": "source_bound_data_card"}
    _, assets = tv.prepare_article_snapshot(article, [chart, card], output_dir=tmp_path)
    assert assets[0]["asset_id"] == card["asset_id"]
    assert assets[1]["modality"] == "tradingview_chart_snapshot" and not assets[1].get("derivative_only")
    assert assets[-1]["preceding_card"]["asset_id"] == card["asset_id"]


def test_current_reader_first_review_accepts_snapshot_without_replacing_official_charts(tmp_path, capture):
    from test_reader_first_data_journalism_v1 import decision
    from live_contentops.native_desktop_editorial_v1 import validate_release_media
    article = {**packet()["article"], "market_asset": "US500", "reader_first_version": "DATA_JOURNALISM_V1"}
    card = build_post_image_card(article, output_dir=tmp_path / "cards", accepted_evidence_sha256="a" * 64)
    chosen = decision("NEWS", 0)
    chosen["charts"] = [{"asset_id": card["asset_id"], "question": "What was reported?",
        "why_useful": "Shows the admitted facts.", "placement_after": "introduction", "data_spec": {"owned": True}}]
    chosen["channel_media"] = {d: [card["asset_id"]] for d in V1_REQUIRED_DERIVATIVE_DESTINATIONS}
    article["visual_editorial_decision"] = chosen
    article, assets = tv.prepare_article_snapshot(article, [card], output_dir=tmp_path)
    view = post_image_view({"article": article, "media_assets": assets, "accepted_evidence_sha256": "a" * 64},
        output_dir=tmp_path / "view")
    validate_release_media(view, require_pixel_review=False)
    _, previews = plan_for(tmp_path, article, assets)
    assert all("Chart: TradingView" in (p.get("full_text") or p.get("text") or "") for p in previews["packages"].values())
    view["article"]["news_item_kind"] = "ANALYSIS"
    view["article"]["visual_editorial_decision"]["story_kind"] = "ANALYSIS"
    with pytest.raises(ValueError, match="OFFICIAL_HISTORY_CHARTS_REQUIRED"):
        validate_release_media(view, require_pixel_review=False)


@pytest.mark.parametrize("extra,status", [({"paid": True}, "PUBLIC_REDISTRIBUTION_NOT_LICENSED"),
    ({"retrospective": True}, "JIM_DECISION_19B_NO_POST_EVENT_CHART")])
def test_rights_and_historical_event_clocks_still_apply(tmp_path, capture, extra, status):
    article = {**packet()["article"], "market_asset": "US500", **extra}
    result, assets = tv.prepare_article_snapshot(article, [], output_dir=tmp_path)
    assert not capture and not assets and result["tradingview_snapshot_outcome"]["status"] == status


def test_hosting_routes_snapshots_through_validated_delivery_only(tmp_path, capture, monkeypatch):
    article, assets = prepared(tmp_path, release=True)
    plan_for(tmp_path, article, assets)
    observed = []
    monkeypatch.setattr(pipeline, "prepare_cloudinary_delivery_media", lambda **kw: observed.append(kw) or {"status": "CONTROLLED"})
    pipeline._prepare_cloudinary_delivery_media_for_plan(work_item_id="cc316", plan={"output_dir": str(tmp_path)},
        preconditions={"canonical_publication_status": "RECONCILED_CONFIRMED", "unknown_write_count": 0})
    assert len(observed[0]["delivery_only_assets"]) == 2
    assert all(a["modality"] != "tradingview_chart_snapshot" for a in observed[0]["article_assets"])
    from live_contentops.cloudinary_delivery_media_v1 import _validated_local_asset
    for asset in observed[0]["delivery_only_assets"]:
        _, blockers = _validated_local_asset(asset, article=article)
        assert not blockers
    changed = deepcopy(observed[0]["delivery_only_assets"][0])
    changed["credit"] = ""
    assert _validated_local_asset(changed, article=article)[1]


def test_cc124_native_article_run_attaches_before_the_plan_freezes(tmp_path, capture):
    from test_v1_simple_gemini_newsroom_v1 import (
        _headlines, _candidate_ids, _selection, _article_output, _receipt, _evidence_result, CUTOFF,
        ROLE_V1_SIMPLE_SELECTION,
    )
    from live_contentops.v1_simple_gemini_newsroom_v1 import run_v1_simple_gemini_newsroom
    rolling = _headlines(1)
    ids = _candidate_ids(rolling)
    class NativeReturn:
        native_desktop_protocol = True
        def telemetry(self):
            return {"observations": [{"invocation_id": "controlled-test", "model": "gpt-6.1-sol",
                "reasoning_effort": "max", "observation_source": "CONTROLLED_TEST_NOT_ACTUAL_MODEL_CALL"}]}
        def __call__(self, **kw):
            receipt = {**_receipt(kw["role_task_id"]), "provider": "NATIVE_CODEX_DESKTOP",
                "selected_model": "gpt-6.1-sol", "reasoning_effort": "max"}
            if kw["role_task_id"] == ROLE_V1_SIMPLE_SELECTION:
                return _selection(ids[0]), receipt
            output = _article_output()
            output["article"]["market_asset"] = "US500"
            return output, receipt
    result = run_v1_simple_gemini_newsroom(output_dir=tmp_path, cutoff_utc=CUTOFF,
        rolling_input=rolling, llm_invoke=NativeReturn(), evidence_loader=lambda _: _evidence_result(), run_id="cc316-native")
    assert result["qualified_article_count"] == 1
    context = json.loads((tmp_path / "run_context_v1.json").read_bytes())
    assert context["article"]["market_asset"] == "US500"
    assert context["media"]["delivery_only_assets"][0]["modality"] == "tradingview_chart_snapshot"
    assert capture == [("US500", "240")]


@pytest.mark.parametrize("event", [False, True])
def test_decision93_market_lead_and_release_lead_survive_snapshot_delivery(tmp_path, capture, event):
    article = {**packet()["article"], "market_asset": "US500",
               "publication_quality_policy": "JIM_DECISION_93"}
    if event:
        article["article_type"] = "EVENT_REVIEW"
    card = build_post_image_card(article, output_dir=tmp_path / "cards", accepted_evidence_sha256="a" * 64)
    article, assets = tv.prepare_article_snapshot(article, [card], output_dir=tmp_path)
    snapshot = next(a for a in assets if a.get("modality") == "tradingview_chart_snapshot"
                    and not a.get("derivative_only"))
    assert snapshot["article_inclusion"] is True
    assert article["lead_image_asset_id"] == (card if event else snapshot)["asset_id"]
    plan_for(tmp_path, article, assets)
    canonical = pipeline._durable_intent_inputs({"output_dir": str(tmp_path), "canonical_url": CANONICAL,
        "destination_plan": {"destination": "substack"}})
    assert canonical["media_assets"][0]["asset_id"] == article["lead_image_asset_id"]
    assert all(not a.get("derivative_only") for a in canonical["media_assets"])
    if event:
        panel = next(a for a in assets if a.get("derivative_only"))
        assert panel["article_inclusion"] is False
        tv.validate_snapshot_asset(panel, article)
        assert all(ids == [panel["asset_id"]] for ids in article["native_destination_media"].values())
    else:
        assert all(ids == [snapshot["asset_id"]] for ids in article["native_destination_media"].values())
