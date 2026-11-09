"""Decision 93 at the real coordinator, compiler and media-preparation seams.

Temporary stores and an observed TradingView download fixture; no network/public writes.
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import random
import shutil

from PIL import Image
import pytest

from live_contentops.article_publication_quality_v1 import (
    before_article_write, image_register, piece_id, prepare_market_snapshot, validate_snapshot_asset,
)
from live_contentops.article_scenarios_v1 import (
    MARKETS, MODEL_LABEL, NOTICES, payload_text, validate_article_scenarios, validate_social_scenarios,
)
from live_contentops.published_images_v1 import ImagePolicyError, PublishedImages, day_of
from live_contentops.v1_simple_gemini_newsroom_v1 import _public_copy, _native_preview_bundle
from test_publication_coordinator_v1 import FixtureTransport, _coordinator, _plan, _set_mode

NOW = datetime(2026, 11, 6, 14, 10, tzinfo=timezone.utc)
TV_FIXTURE = Path(__file__).parent / "fixtures/cc314/SPX_2026-11-09_17-50-41.png"


def image_asset(tmp_path, seed=1):
    """Distinct deterministic texture, so a resize/re-encode keeps visual identity."""
    rng = random.Random(seed)
    pixels = bytes(rng.randrange(256) for _ in range(120 * 80 * 3))
    path = tmp_path / f"image-{seed}.png"
    Image.frombytes("RGB", (120, 80), pixels).resize((720, 480)).save(path)
    return {"asset_id": f"image-{seed}", "path": str(path), "sha256": sha256(path.read_bytes()).hexdigest()}


def scenario_article():
    scenarios, passages = [], []
    for name, role, probability in (("Base policy path", "base_case", "60%"),
                                     ("Growth alternative", "alternative", "40%")):
        values = {"probability": probability, "confirmation": name + " confirmed by the next official release",
                  "invalidation": name + " invalidated by a contrary official release"}
        values.update({"market_moves." + market: name + ": " + market + " follows its stated conditional path"
                       for market in MARKETS})
        passage = ". ".join([name, MODEL_LABEL, *values.values()])
        passages.append(passage)
        scenarios.append({"name": name, "role": role, "probability": probability,
            "confirmation": values["confirmation"], "invalidation": values["invalidation"],
            "market_moves": {m: values["market_moves." + m] for m in MARKETS},
            "source_bindings": {k: {"document_id": "main-report", "support_excerpt": passage} for k in values}})
    source = "\n".join(passages)
    article = {"title": "A conditional market review", "dek": "What confirms each path matters.",
               "substack_body_markdown": "## Scenarios\n\n" + source + "\n\n" + "\n".join(NOTICES),
               "author_identity": "Capital Chronicle", "publisher_identity": "Capital Chronicle",
               "rights_class": "CC_OWN_ANALYSIS", "scenario_analysis": scenarios,
               "social_scenarios": {"base_case": "Base case: 60% model estimate; the policy path holds.",
                                    "alternative": "Alternative: 40% model estimate; growth changes the path."}}
    documents = [{"document_id": "main-report", "publisher": "Capital Chronicle",
                  "canonical_content_text": source, "canonical_content_sha256": sha256(source.encode()).hexdigest()}]
    return article, documents


def publication(tmp_path, *, asset_seed=1, assets=True, transport=None, destination="substack", social_payload=None):
    class ArticleTransport(FixtureTransport):
        def publish(self, *, destination, intent, authorization_context):
            result = super().publish(destination=destination, intent=intent, authorization_context=authorization_context)
            if destination == "substack":
                result.update(id="article-" + str(asset_seed),
                              public_url="https://capitalchronicle.substack.com/p/piece-" + str(asset_seed))
            return result
    store, runtime, coordinator = _coordinator(tmp_path, runtime=transport or ArticleTransport())
    coordinator._clock = lambda: NOW
    coordinator.published_content_path = tmp_path / "published_content_v1.jsonl"
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    article, documents = scenario_article()
    media = [image_asset(tmp_path, asset_seed)] if assets else []
    folder = tmp_path / "article"
    folder.mkdir()
    (folder / "article_manifest_v1.json").write_text(json.dumps(article), encoding="utf-8")
    (folder / "run_context_v1.json").write_text(json.dumps({"article": article, "media": {"assets": media},
        "source_documents": documents}), encoding="utf-8")
    plan = _plan(destination)
    plan.update(output_dir=str(folder), article_content_sha256=sha256(_public_copy(article).encode()).hexdigest())
    registered = coordinator.register_plan("work-1", plan)["registered"][0]
    message = store.get_outbox_message(registered["message_id"])
    if social_payload is not None:
        intent = json.loads(message["payload"])
        intent["native_payload"] = social_payload
        store.finalize_outbox_payload_before_dispatch(message_id=message["message_id"], payload=json.dumps(intent), status="READY")
        message = store.get_outbox_message(message["message_id"])
    return store, runtime, coordinator, message, media, article, documents


def test_real_coordinator_publishes_fresh_image_and_records_confirmed_fingerprints(tmp_path):
    _, runtime, coordinator, message, media, _, _ = publication(tmp_path)
    result = coordinator._dispatch_message(message, canonical_url=None)
    assert result["status"] == "DISPATCH_CONFIRMED"
    assert runtime.publish_calls == ["substack"]
    record = image_register(coordinator).records()[-1]
    assert record["state"] == "PUBLISHED"
    assert record["canonical_url"] == result["public_object_url"]
    assert record["images"][0]["sha256"] == media[0]["sha256"]
    assert len(record["images"][0]["perceptual_hash"]) == 16


def test_fingerprint_recording_failure_cannot_disable_public_readback(tmp_path, monkeypatch):
    from live_contentops import article_publication_quality_v1 as quality
    _, runtime, coordinator, message, *_ = publication(tmp_path)
    def unavailable(*args, **kwargs):
        raise OSError("fixture file unavailable")
    monkeypatch.setattr(quality, "observe_published_images", unavailable)
    result = coordinator._dispatch_message(message, canonical_url=None)
    assert result["status"] == "DISPATCH_CONFIRMED"
    assert result["reconciliation_status"] == "RECONCILED_CONFIRMED"
    assert runtime.publish_calls == ["substack"]


def test_native_resume_consumes_an_existing_return_without_blocking_on_new_media_policy(tmp_path):
    from types import SimpleNamespace
    store, runtime, coordinator, message, *_ = publication(tmp_path, assets=False)
    intent = json.loads(message["payload"])
    runtime._neo_transport = SimpleNamespace(native_executor=SimpleNamespace(
        native_neo_protocol=True, allow_publish=True, operation_id="work-1", store=store))
    assert intent["destination_plan"]["transport_type"] == "BROWSEROS_NEO_MCP"
    assert store.claim_platform_dispatch_attempt(dispatch_id=intent["attempt_identity"],
        message_id=message["message_id"], platform="substack")
    store.set_dispatch_status(intent["attempt_identity"], "NATIVE_NEO_TOOL_PENDING")
    result = coordinator._dispatch_message(message, canonical_url=None)
    assert result["status"] == "DISPATCH_CONFIRMED"
    assert result["reconciliation_status"] == "RECONCILED_CONFIRMED"
    # The fixture stands for consuming the existing executor return. A real
    # browser action still goes through the separately tested executor.begin.
    assert runtime.publish_calls == ["substack"]


@pytest.mark.parametrize("variant", ["exact", "resized", "jpeg"])
def test_real_coordinator_refuses_published_or_near_duplicate_image(tmp_path, variant):
    _, runtime, coordinator, message, media, _, _ = publication(tmp_path)
    previous = tmp_path / ("old.jpeg" if variant == "jpeg" else "old.png")
    with Image.open(media[0]["path"]) as image:
        if variant == "resized":
            image = image.resize((360, 240))
        image.save(previous, quality=88)
    image_register(coordinator).seed(piece_id="old-piece", canonical_url="https://capitalchronicle.substack.com/p/old",
        images=[{"path": str(previous)}], published_at="2026-11-05T08:00:00Z", observation_ref="observed-old-object")
    result = coordinator._dispatch_message(message, canonical_url=None)
    assert result["status"] == "IMAGE_REUSED"
    assert result["publish_called"] is False
    assert runtime.publish_calls == []


def test_real_coordinator_refuses_missing_image_without_adapter_write(tmp_path):
    _, runtime, coordinator, message, *_ = publication(tmp_path, assets=False)
    assert coordinator._dispatch_message(message, canonical_url=None)["status"] == "IMAGE_MISSING"
    assert runtime.publish_calls == []


def test_daily_cap_uses_the_live_register_before_an_event_article_write(tmp_path):
    _, runtime, coordinator, message, media, *_ = publication(tmp_path)
    registry = image_register(coordinator)
    for number in (2, 3):
        asset = image_asset(tmp_path, number)
        registry.seed(piece_id=str(number), canonical_url="https://capitalchronicle.substack.com/p/" + str(number),
            images=[asset], published_at=NOW.isoformat(), observation_ref="observed-" + str(number))
    result = coordinator._dispatch_message(message, canonical_url=None)
    assert result["status"] == "DAILY_ARTICLE_CAP_REACHED"
    assert runtime.publish_calls == []
    assert media[0]["sha256"] not in {i["sha256"] for row in registry.records() for i in row["images"]}


def test_weekend_cap_refuses_second_piece_but_keeps_own_social_distribution(tmp_path):
    from live_contentops.published_images_v1 import daily_limit
    weekend = datetime(2026, 11, 7, 8, 1, tzinfo=timezone.utc)
    _, runtime, coordinator, message, media, *_ = publication(tmp_path)
    coordinator._clock = lambda: weekend
    register = image_register(coordinator)
    register.seed(piece_id="first-weekend-piece", canonical_url="https://capitalchronicle.substack.com/p/weekend-first",
        images=[image_asset(tmp_path, 2)], published_at=weekend.isoformat(), observation_ref="weekend-readback")
    assert coordinator._dispatch_message(message, canonical_url=None)["status"] == "DAILY_ARTICLE_CAP_REACHED"
    assert runtime.publish_calls == [] and daily_limit(weekend) == 1
    first = image_asset(tmp_path, 2)
    # Reaching this article's own remaining channels is still ordinary distribution.
    register.reserve(piece_id="first-weekend-piece", assets=[first], lead_asset_id=first["asset_id"], now=weekend,
        canonical_url="https://capitalchronicle.substack.com/p/weekend-first", enforce_cap=False)


@pytest.mark.parametrize("instant,limit", [
    ("2026-11-06T16:59:59Z", 2), ("2026-11-06T17:00:00Z", 1),
    ("2026-11-08T17:59:59Z", 1), ("2026-11-08T18:00:00Z", 2),
])
def test_weekend_limit_feeds_existing_production_day_read_model(tmp_path, instant, limit):
    from live_contentops.newsroom_production_day_v1 import build_production_day_snapshot
    from live_contentops.published_images_v1 import daily_limit
    result = build_production_day_snapshot(reference=instant, output_root=tmp_path)
    assert result.final_published_target_max == daily_limit(instant) == limit


def test_reserved_unknown_write_occupies_cap_until_exact_absence(tmp_path):
    registry = PublishedImages(tmp_path / "images.jsonl")
    for number in (1, 2):
        asset = image_asset(tmp_path, number)
        registry.reserve(piece_id=str(number), assets=[asset], lead_asset_id=asset["asset_id"], now=NOW)
    third = image_asset(tmp_path, 3)
    with pytest.raises(ImagePolicyError, match="DAILY_ARTICLE_CAP_REACHED"):
        registry.reserve(piece_id="3", assets=[third], lead_asset_id=third["asset_id"], now=NOW)
    registry.settle("1", state="ABSENT", now=NOW)
    registry.reserve(piece_id="3", assets=[third], lead_asset_id=third["asset_id"], now=NOW)


def test_daily_cap_is_shared_between_owner_operations_and_event_runs(tmp_path):
    shared_feed = tmp_path / "published_content_v1.jsonl"
    for index in range(3):
        folder = tmp_path / str(index)
        folder.mkdir()
        _, runtime, coordinator, message, *_ = publication(folder, asset_seed=index + 1)
        coordinator.published_content_path = shared_feed
        result = coordinator._dispatch_message(message, canonical_url=None)
        assert result["status"] == ("DISPATCH_CONFIRMED" if index < 2 else "DAILY_ARTICLE_CAP_REACHED")
        assert runtime.publish_calls == (["substack"] if index < 2 else [])


def test_production_day_rollover_preserves_following_0100_window():
    assert day_of("2026-11-06T18:00:00Z") == "2026-11-06"
    assert day_of("2026-11-06T18:59:59Z") == "2026-11-06"
    assert day_of("2026-11-06T19:00:00Z") == "2026-11-07"


def test_same_article_distributes_its_image_without_counting_another_article(tmp_path):
    _, _, coordinator, message, media, article, docs = publication(tmp_path)
    intent = json.loads(message["payload"])
    before_article_write(coordinator, intent, "substack")
    intent.update(native_payload={"text": "\n".join(article["social_scenarios"].values())},
                  canonical_url="https://capitalchronicle.substack.com/p/fixture-article-1")
    before_article_write(coordinator, intent, "telegram")
    assert {r["piece_id"] for r in image_register(coordinator).records()} == {piece_id(coordinator.store, intent)}


@pytest.mark.parametrize("missing", ["all", "body", "probability", "confirmation", "invalidation", "market", "source", "label", "notice"])
def test_scenario_requirement_refuses_missing_or_unbound_fields(missing):
    article, docs = scenario_article()
    if missing == "all":
        article.pop("scenario_analysis")
    elif missing == "body":
        article["substack_body_markdown"] = "A piece without scenarios."
    elif missing in {"probability", "confirmation", "invalidation"}:
        article["scenario_analysis"][0].pop(missing)
    elif missing == "market":
        article["scenario_analysis"][0]["market_moves"].pop("BTCUSD")
    elif missing == "source":
        article["scenario_analysis"][0]["source_bindings"]["probability"]["support_excerpt"] = "Invented 99%"
    elif missing == "label":
        article["substack_body_markdown"] = article["substack_body_markdown"].replace(MODEL_LABEL, "")
    elif missing == "notice":
        article["substack_body_markdown"] = article["substack_body_markdown"].replace(NOTICES[1], "")
    with pytest.raises(ValueError):
        validate_article_scenarios(article, docs)


def test_probability_cannot_be_invented_as_an_unreported_complement():
    article, docs = scenario_article()
    article["scenario_analysis"][1]["probability"] = "35%"
    article["substack_body_markdown"] = article["substack_body_markdown"].replace("40%", "35%")
    with pytest.raises(ValueError, match="SCENARIO_MAIN_SOURCE_BINDING_REQUIRED"):
        validate_article_scenarios(article, docs)


def test_probability_token_cannot_match_only_the_tail_of_a_source_number():
    article, docs = scenario_article()
    article["scenario_analysis"][0]["probability"] = "0%"
    with pytest.raises(ValueError, match="SCENARIO_MAIN_SOURCE_BINDING_REQUIRED"):
        validate_article_scenarios(article, docs)


def test_current_daily_consumer_uses_the_two_article_ceiling(tmp_path):
    from live_contentops.newsroom_production_day_v1 import build_production_day_snapshot
    snapshot = build_production_day_snapshot(reference=NOW, output_root=tmp_path,
        routine_opportunities_used_override=4)
    assert snapshot.final_published_target_min == 0
    assert snapshot.final_published_target_max == 2
    assert snapshot.production_day_state == "WITHIN_DAILY_ARTICLE_CAP"
    assert snapshot.remaining_published_deficit == 0


def test_current_read_model_shows_the_ceiling_without_an_old_output_deficit(tmp_path):
    from live_contentops.continuous_headline_ingest_v1 import OUTCOME_CAPTURED_NONE, write_ingestion_checkpoint
    from live_contentops.daily_app_ui_read_model_v1 import build_daily_app_snapshot
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    store = ContentOpsDurableStore(tmp_path / "read-model.sqlite3", now_fn=lambda: NOW)
    store.upsert_heartbeat("daily-supervisor")
    write_ingestion_checkpoint(store, now=NOW, last_success_epoch=NOW.timestamp(),
        last_attempt_epoch=NOW.timestamp(), outcome_code=OUTCOME_CAPTURED_NONE, consecutive_empty=1, rows_iteration=0)
    snapshot = build_daily_app_snapshot(store.db_path, now=NOW)
    assert snapshot["today"]["final_published_target_min"] == 0
    assert snapshot["today"]["final_published_target_max"] == 2
    assert snapshot["today"]["remaining_published_deficit"] == 0
    cockpit = snapshot["runtime"]["operator_cockpit"]
    assert cockpit["output_health"] == "WITHIN_DAILY_ARTICLE_CAP"
    assert cockpit["schedule"]["idle_healthy"] is True


def test_native_action_begin_rechecks_image_policy_without_claiming_a_bad_write(tmp_path, monkeypatch):
    from live_contentops import published_content_v1 as feed
    from live_contentops import llm_operator_control_v1 as control
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    from live_contentops.native_neo_executor_v1 import NativeNeoExecutor, NativeNeoInputRequired, PENDING
    store, _, _, message, *_ = publication(tmp_path, assets=False)
    monkeypatch.setattr(feed, "PRODUCTION_STORE", store.db_path)
    monkeypatch.setattr(feed, "DEFAULT_FEED", tmp_path / "published_content_v1.jsonl")
    monkeypatch.setattr(control, "assert_llm_operator_execution_enabled", lambda: None)
    intent = json.loads(message["payload"])
    dispatch_id = intent["attempt_identity"]
    store.claim_platform_dispatch_attempt(dispatch_id=dispatch_id, message_id=message["message_id"], platform="substack")
    store.set_dispatch_status(dispatch_id, PENDING)
    executor = NativeNeoExecutor(store, operation_id="operation", output_dir=tmp_path / "neo",
        native_invocation_id="fixture-invocation", allow_publish=True, clock=lambda: NOW)
    request = {"work_item_id": "work-1", "action": "PUBLISH", "destination": "substack",
        "dispatch_attempt_identity": dispatch_id, "expected_identity": "capitalchronicle.substack.com",
        "surface": "SUBSTACK_ARTICLE", "native_payload": {"body_markdown": "Fixture copy."},
        "content_binding": {"expected_text_segments": ["Fixture copy."]}}
    request["request_sha256"] = sha256_of(request)
    with pytest.raises(NativeNeoInputRequired):
        executor(request)
    with pytest.raises(ValueError, match="IMAGE_MISSING"):
        executor.begin(request["request_sha256"])
    assert executor._get(request["request_sha256"], "started") is None


def test_real_eight_channel_compiler_carries_both_authored_scenarios():
    article, _ = scenario_article()
    bundle, _ = _native_preview_bundle(article=article, article_mode="STANDARD_NEWS_ANALYSIS",
                                     article_identity="a" * 64, media_asset_ids=["image-1"])
    assert len(bundle["packages"]) == 8
    for payload in bundle["packages"].values():
        validate_social_scenarios(article, payload)
        assert "60%" in payload_text(payload) and "40%" in payload_text(payload)


def test_a_transport_cannot_hide_an_incomplete_copy_behind_a_complete_alias():
    article, _ = scenario_article()
    with pytest.raises(ValueError, match="SOCIAL_SCENARIOS_REQUIRED"):
        validate_social_scenarios(article, {"text": "\n".join(article["social_scenarios"].values()),
                                           "full_text": "Only a headline."})


@pytest.mark.parametrize("destination", ["telegram", "discord", "x", "linkedin", "facebook_page", "instagram_business", "threads", "youtube"])
def test_social_copy_must_carry_both_cases_in_delivered_text(destination):
    article, _ = scenario_article()
    with pytest.raises(ValueError, match="SOCIAL_SCENARIOS_REQUIRED"):
        validate_social_scenarios(article, {"destination": destination, "text": article["social_scenarios"]["base_case"],
                                            "unused_metadata": article["social_scenarios"]["alternative"]})


@pytest.mark.parametrize("destination", ["telegram", "discord", "x", "linkedin", "facebook_page", "instagram_business", "threads", "youtube"])
def test_coordinator_refuses_social_copy_missing_alternative_before_transport(tmp_path, destination):
    article, _ = scenario_article()
    _, runtime, coordinator, message, *_ = publication(tmp_path, destination=destination,
        social_payload={"text": article["social_scenarios"]["base_case"], "media_asset_ids": ["image-1"]})
    outcome = coordinator._dispatch_message(message, canonical_url="https://capitalchronicle.substack.com/p/test")
    assert outcome["status"] == "SOCIAL_SCENARIOS_REQUIRED"
    assert runtime.publish_calls == []


def captured_snapshot(tmp_path, now=NOW):
    path = tmp_path / TV_FIXTURE.name
    shutil.copyfile(TV_FIXTURE, path)
    return {"path": str(path), "sha256": sha256(path.read_bytes()).hexdigest(), "tv_symbol": "SP:SPX",
            "interval": "240", "interval_label": "4h", "chart_url": "https://www.tradingview.com/chart/?symbol=SP:SPX&interval=240",
            "captured_at_utc": now.isoformat()}


def test_market_snapshot_reaches_canonical_and_all_destination_media(tmp_path):
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import post_image_view
    article, _ = scenario_article()
    article.update(market_asset="US500", native_destination_media={d: [] for d in
        ("telegram", "discord", "x", "linkedin", "facebook_page", "instagram_business", "threads", "youtube")})
    captured = captured_snapshot(tmp_path)
    article, assets = prepare_market_snapshot(article, [], output_dir=tmp_path, now=NOW,
                                              capture=lambda *a: captured)
    view = post_image_view({"article": article, "media_assets": assets}, output_dir=tmp_path)
    snapshot = view["media_assets"][0]
    assert snapshot["modality"] == "tradingview_chart_snapshot"
    assert snapshot["article_inclusion"] is True and snapshot["canonical_article_media"] is True
    assert view["post_image_policy"]["default_asset_id"] == snapshot["asset_id"]
    assert all(snapshot["asset_id"] in ids for ids in view["article"]["native_destination_media"].values())
    assert " ET " in snapshot["alt_text"]
    validate_snapshot_asset(snapshot, market="US500", now=NOW)
    bundle, _ = _native_preview_bundle(article=view["article"], article_mode="STANDARD_NEWS_ANALYSIS",
        article_identity="b" * 64, media_asset_ids=[snapshot["asset_id"]], media_assets=[snapshot])
    assert all("Chart: TradingView" in payload_text(payload) for payload in bundle["packages"].values())


def test_release_card_stays_first_and_snapshot_is_added(tmp_path):
    article, _ = scenario_article()
    article.update(market_asset="US500", article_type="EVENT_REVIEW")
    release = image_asset(tmp_path)
    article, assets = prepare_market_snapshot(article, [release], output_dir=tmp_path, now=NOW,
                                              capture=lambda *a: captured_snapshot(tmp_path))
    assert article["lead_image_asset_id"] == release["asset_id"]
    assert assets[0] == release
    assert assets[1]["modality"] == "tradingview_chart_snapshot"


def test_refresh_consumes_completed_capture_clock_and_replaces_old_channel_binding(tmp_path, monkeypatch):
    from live_contentops import article_publication_quality_v1 as quality
    from live_contentops.tradingview_snapshot_v1 import snapshot_asset
    old = snapshot_asset("US500", "Controlled snapshot", captured_snapshot(tmp_path, NOW - timedelta(minutes=16)), tmp_path)
    old["asset_id"] = "controlled-old-snapshot"
    article, _ = scenario_article()
    article.update(market_asset="US500", native_destination_media={"x": [old["asset_id"]]})
    elapsed = iter((100.0, 140.0))
    monkeypatch.setattr(quality, "monotonic", lambda: next(elapsed))
    article, assets = prepare_market_snapshot(article, [old], output_dir=tmp_path, now=NOW,
        capture=lambda *a: captured_snapshot(tmp_path, NOW + timedelta(seconds=40)))
    assert article["native_destination_media"]["x"] == [assets[0]["asset_id"]]
    assert old["asset_id"] not in article["native_destination_media"]["x"]
    validate_snapshot_asset(assets[0], market="US500", now=NOW + timedelta(seconds=40))


def test_existing_hosting_consumer_receives_snapshot_as_delivery_media(tmp_path, monkeypatch):
    from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as pipeline
    article, _ = scenario_article()
    article["market_asset"] = "US500"
    article, assets = prepare_market_snapshot(article, [], output_dir=tmp_path, now=NOW,
                                              capture=lambda *a: captured_snapshot(tmp_path))
    (tmp_path / "run_context_v1.json").write_text(json.dumps({"article": article,
        "media": {"assets": assets, "delivery_only_assets": []}}), encoding="utf-8")
    calls = []
    def host(**kwargs):
        calls.append(kwargs)
        return {"status": "CLOUDINARY_DELIVERY_MEDIA_READY", "manifest": {"assets": [
            {"sha256": assets[0]["sha256"], "local_public_hash_continuity": True}]}}
    monkeypatch.setattr(pipeline, "prepare_cloudinary_delivery_media", host)
    result = pipeline._prepare_cloudinary_delivery_media_for_plan(work_item_id="work", plan={"output_dir": str(tmp_path)},
        preconditions={"canonical_publication_status": "RECONCILED_CONFIRMED", "unknown_write_count": 0})
    assert result["status"] == "CLOUDINARY_DELIVERY_MEDIA_READY"
    assert calls[0]["article_assets"] == []
    delivered = calls[0]["delivery_only_assets"][0]
    assert delivered["sha256"] == assets[0]["sha256"]
    assert delivered["modality"] == "tradingview_chart_snapshot"
    assert delivered["article_inclusion"] is False


def test_snapshot_staleness_and_cropped_attribution_are_refused(tmp_path):
    article, _ = scenario_article()
    article["market_asset"] = "US500"
    _, assets = prepare_market_snapshot(article, [], output_dir=tmp_path, now=NOW,
                                         capture=lambda *a: captured_snapshot(tmp_path))
    with pytest.raises(ImagePolicyError, match="TRADINGVIEW_SNAPSHOT_STALE"):
        validate_snapshot_asset(assets[0], market="US500", now=NOW + timedelta(minutes=16))
    changed = deepcopy(assets[0])
    changed["tradingview_snapshot"]["framing"]["original_box"][1] += 20
    with pytest.raises(ImagePolicyError, match="TRADINGVIEW_ATTRIBUTION_CROPPED"):
        validate_snapshot_asset(changed, market="US500", now=NOW)
