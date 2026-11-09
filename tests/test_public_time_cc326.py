"""Decision 90: live builders and write boundaries, using disposable stores/transports."""
from copy import deepcopy
from datetime import datetime
import json

import pytest

from live_contentops.public_time_v1 import (
    REASON, WRITER_GUIDANCE, find_forbidden_public_time, public_date, public_timestamp,
)
from live_contentops.retrospective_piece_v1 import retrospective_notice
from live_contentops.fact_card_design_v1 import CardSpec, card_date, reader_date, render_fact_card
from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff
from live_contentops.native_neo_executor_v1 import NativeNeoExecutor
from test_publication_coordinator_v1 import _coordinator, _plan, _set_mode
from test_substack_daily_digest_v1 import setup, row, prepared


@pytest.mark.parametrize("instant,expected", [
    ("2026-01-15T04:30:00Z", "23:30 ET on 14 January 2026"),
    ("2026-07-15T04:30:00Z", "00:30 ET on 15 July 2026"),
    ("2026-03-08T06:59:00Z", "01:59 ET on 8 March 2026"),
    ("2026-03-08T07:00:00Z", "03:00 ET on 8 March 2026"),
    ("2026-11-01T05:59:00Z", "01:59 ET on 1 November 2026"),
    ("2026-11-01T06:00:00Z", "01:00 ET on 1 November 2026"),
])
def test_actual_dst_and_midnight(instant, expected):
    assert public_timestamp(instant) == expected


def test_public_dates_convert_the_instant_but_date_only_periods_keep_precision():
    at = "2026-11-06T02:00:00Z"
    assert public_date(at) == card_date(datetime.fromisoformat(at)) == reader_date(at) == "November 5, 2026"
    assert reader_date("2026-11-06") == "November 6, 2026"
    assert retrospective_notice(at) == "Retrospective analysis, written on 5 November 2026 (ET)"
    with pytest.raises(ValueError, match="AWARE_INSTANT"):
        public_timestamp("2026-11-06T02:00:00")


@pytest.mark.parametrize("bad", ["GMT+7", "UTC+7", "GMT +07:00", "gmt＋7", "UTC&#43;7", "Bangkok time", "Vietnam time", "14:00 Bangkok"])
def test_guard_refuses_public_copy(bad):
    assert find_forbidden_public_time({"posts": [{"text": "Written at " + bad}]})
    assert find_forbidden_public_time("A report from Bangkok", "08:30 ET") is None


@pytest.mark.parametrize("destination", ["substack", "telegram", "discord", "x", "linkedin", "facebook_page", "instagram_business", "threads", "youtube"])
@pytest.mark.parametrize("bad", ["GMT+7", "UTC+7"])
def test_final_coordinator_payload_refused_before_adapter_or_claim(tmp_path, destination, bad):
    store, transport, coordinator = _coordinator(tmp_path)
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    registered = coordinator.register_plan("work-1", _plan(destination))["registered"][0]
    message = store.get_outbox_message(registered["message_id"])
    intent = json.loads(message["payload"])
    intent["native_payload"] = {"text": "Written at 14:00 " + bad}
    outcome = coordinator._dispatch_message({**message, "payload": json.dumps(intent)}, canonical_url=None)
    assert outcome["status"] == REASON and outcome["publish_called"] is False
    assert transport.publish_calls == [] and store.list_platform_dispatches() == []


@pytest.mark.parametrize("destination", ["substack", "x", "linkedin", "linkedin_company", "youtube"])
def test_browser_write_checks_resolved_copy(tmp_path, monkeypatch, destination):
    monkeypatch.setattr("live_contentops.neo_destination_handoff_v1._payload_binding",
        lambda *a: ({"text": "Written at 14:00 GMT+7"}, {"media_manifest": []}))
    intent = {"work_item_id": "work", "canonical_url": "https://capitalchronicle.substack.com/p/test",
        "payload": "Unchanged", "destination_plan": {"payload_hash": "hash"}}
    auth = {"schema_version": "contentops.canonical_machine_authorization.v1", "operating_mode": "AUTONOMOUS_DEFAULT",
        "destination": destination, "dispatch_attempt_identity": "dispatch", "work_item_id": "work", "payload_hash": "hash"}
    with pytest.raises(ValueError, match=REASON):
        NeoDestinationHandoff().request(destination=destination, action="PUBLISH", intent=intent, authorization_context=auth)


def test_previously_frozen_browser_request_is_checked_at_actual_begin(tmp_path):
    store, _, _ = _coordinator(tmp_path)
    executor = NativeNeoExecutor(store, operation_id="work-1", output_dir=tmp_path, native_invocation_id="controlled")
    packet = {"request": {"action": "PUBLISH", "native_payload": {"body_markdown": "14:00 UTC+7"}}}
    executor._put("request-hash", "request", packet, "work-1")
    with pytest.raises(ValueError, match=REASON):
        executor.begin("request-hash")
    assert executor._get("request-hash", "started") is None


def test_card_refuses_bad_time_before_image_creation(tmp_path):
    path = tmp_path / "bad.png"
    with pytest.raises(ValueError, match=REASON):
        render_fact_card(path, CardSpec(title="Report", facts=[("Time", "14:00 GMT+7")]))
    assert not path.exists()


def test_digest_title_card_and_schedule_clock(tmp_path):
    store, feed = setup(tmp_path, [row()])
    packet = prepared(store, feed)["packet"]
    assert packet["native_payload"]["title"].endswith("November 3, 2026 (ET)")
    assert packet["media_assets"][0]["caption"].endswith("November 3, 2026 (ET)")
    assert packet["cutoff_utc"] == "2026-11-03T12:00:00+00:00"
    assert packet["digest_id"] == "cc143-digest-2026-11-03"
    assert find_forbidden_public_time(packet["native_payload"]) is None


def test_source_clocks_do_not_reach_the_public_guard():
    from live_contentops.public_time_v1 import public_article_text
    article = {"title": "Report", "source_date_notice": "Internal cutoff GMT+7", "display_date": "November 5, 2026"}
    assert find_forbidden_public_time(public_article_text(article)) is None


@pytest.mark.parametrize("destination", ["substack", "telegram", "discord", "x", "facebook_page", "threads", "youtube"])
def test_et_copy_reaches_live_coordinator_consumer(tmp_path, destination):
    store, transport, coordinator = _coordinator(tmp_path)
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    plan = _plan(destination)
    plan["destinations"][0]["payload"] = "Reporting as of " + public_timestamp("2026-11-06T12:00:00Z")
    from hashlib import sha256
    plan["destinations"][0]["payload_hash"] = sha256(plan["destinations"][0]["payload"].encode()).hexdigest()
    registered = coordinator.register_plan("work-1", plan)["registered"][0]
    message = store.get_outbox_message(registered["message_id"])
    outcome = coordinator._dispatch_message(message, canonical_url=None)
    assert outcome["publish_called"] is True
    assert transport.publish_calls == [destination]


@pytest.mark.parametrize("bad", ["GMT+7", "UTC+7"])
def test_router_checks_resolved_article_and_derivative_payload(tmp_path, monkeypatch, bad):
    from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import _publish_one_destination_from_durable_intent
    data = {"output_dir": tmp_path, "article": {"title": "Report", "substack_body_markdown": "14:00 " + bad},
        "payloads": {"substack": {}, "telegram": {"text": "14:00 " + bad}},
        "canonical_url": None, "local_media": None, "public_image_url": None, "media_assets": []}
    monkeypatch.setattr("live_contentops._eight_platform_substack_first_pipeline_impl_v1._durable_intent_inputs", lambda intent: data)
    for destination in ("substack", "telegram"):
        result = _publish_one_destination_from_durable_intent(destination=destination, intent={"attempt_identity": "controlled"},
            authorization_context={"operating_mode": "AUTONOMOUS_DEFAULT", "dispatch_attempt_identity": "controlled"})
        assert result["reason_code"] == REASON and result["public_write_performed"] is False


@pytest.mark.parametrize("instant,expected", [
    ("2026-11-06T02:00:00Z", "November 5, 2026"),
    ("2026-07-15T04:30:00Z", "July 15, 2026"),
    ("2026-11-06", "November 6, 2026"),
])
def test_delivery_media_source_date_converts_instants_only(instant, expected):
    from live_contentops.media_manifest_authority_v1 import _reader_facing_source_date
    assert _reader_facing_source_date(instant) == expected


def test_et_retrospective_notice_survives_all_eight_native_packages():
    from pathlib import Path
    from live_contentops.v1_simple_gemini_newsroom_v1 import _native_preview_bundle
    from test_retrospective_piece_v1 import retained_json
    root = Path(__file__).resolve().parents[1] / "docs/publisher/CC-074-private-20261101"
    source = (root / "native/desktop_response_write.json").read_bytes()
    # An in-memory regression fixture; the historical article and all files stay sealed.
    old = "Retrospective analysis, written on 1 November 2026 (GMT+7)"
    notice = "Retrospective analysis, written on 1 November 2026 (ET)"
    article = json.loads(source)["output"]["article"]
    article = json.loads(json.dumps(article).replace(old, notice))
    article["public_source_bindings"] = [{k: d[k] for k in ("source_id", "publisher", "url")}
        for d in retained_json("source-packet.json")]
    assets = retained_json("chart-assets.json")
    bundle, _ = _native_preview_bundle(article=article, article_mode="DATA_OR_DOCUMENT_LENS",
        article_identity="a" * 64, epistemic_state={"reader_visible_epistemic_label": "CONFIRMED",
            "event_confirmation_state": "CONFIRMED", "primary_reporting_publisher": "Federal Reserve Board"},
        media_asset_ids=[a["asset_id"] for a in assets], media_assets=assets)
    assert len(bundle["packages"]) == 8
    for payload in bundle["packages"].values():
        text = payload.get("full_text") or payload["text"]
        assert notice in " ".join(text.split())
        assert find_forbidden_public_time(text) is None
    assert (root / "native/desktop_response_write.json").read_bytes() == source
