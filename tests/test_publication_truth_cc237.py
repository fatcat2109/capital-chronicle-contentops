"""CC-237: publication records tell the truth. No live store, provider or model call."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.destination_transport_registry_v1 import registration_for_destination
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_publication_v1 import DESTINATION, publication_projection
from live_contentops.native_newsroom_volume_v1 import persist_native_day_measurement
from live_contentops.publication_coordinator_v1 import (
    DEFINITE_NO_WRITE, DISPATCH_CONFIRMED, UNKNOWN_WRITE, DurablePublicationCoordinator,
    normalize_dispatch_result,
)
from live_contentops.published_content_v1 import (
    PublishedContentError, append_outlet_update, canonical, current_outlets, outlets_path,
    read_current_records, read_records, sync_confirmed_piece,
)
from test_native_volume_window_v1 import CUTOFF, make_turn
from test_published_content_v1 import ORIGINAL, publish_with_original_clock, sealed, lifecycle
from test_publication_coordinator_v1 import FixtureTransport


def normalized(destination, raw):
    registration = registration_for_destination(destination)
    return normalize_dispatch_result(raw, destination=destination, surface=registration.surface,
                                     transport_type=registration.transport_type)


@pytest.mark.parametrize("destination,raw", [
    ("substack", {"status": "NOT_PUBLISHED", "ok": False, "draft_id": "223293057"}),
    ("substack", {"status": "NOT_CONFIRMED", "ok": False, "draft_id": "223293057",
                  "public_url": "https://capitalchronicle.substack.com/p/a"}),
    ("telegram", {"status": "NOT_PUBLISHED", "id": "61"}),
    ("telegram", {"status": "NOT_CONFIRMED", "ok": False, "id": "61"}),
    ("discord", {"status": "DRY_RUN_PASS", "id": "12001"}),
    ("facebook_page", {"status": "UNSUCCESSFUL", "post_id": "page_1"}),
    ("telegram", {"status": "SUCCESS", "ok": False, "id": "61"}),
    ("x", {"status": "SUCCESS", "success": False, "id": "18001"}),
    ("threads", {"id": "th_1", "published": False}),
    # A draft id is not a public object: alone, or at the editor.
    ("substack", {"status": "SUCCESS", "draft_id": "223293057"}),
    ("substack", {"status": "SUCCESS", "draft_id": "223293057",
                  "page_url": "https://capitalchronicle.substack.com/publish/post/223293057",
                  "url": "https://capitalchronicle.substack.com/publish/post/223293057"}),
    # Words are matched per adapter: PUBLISHED is a Neo word, not a Bot API word.
    ("telegram", {"status": "PUBLISHED", "id": "61"}),
])
def test_a_failure_word_or_flag_or_draft_id_never_confirms(destination, raw):
    result = normalized(destination, raw)
    assert result["status"] != DISPATCH_CONFIRMED
    assert result["write_outcome_certainty"] != "PROVIDER_ACCEPTED"


def test_an_ambiguous_failure_keeps_its_identity_for_readback():
    result = normalized("substack", {"status": "NOT_PUBLISHED", "ok": False, "draft_id": "223293057"})
    assert result["status"] == UNKNOWN_WRITE and result["public_object_id"] == "223293057"
    assert normalized("telegram", {"status": "FAILED_BEFORE_WRITE", "ok": False,
                                   "definite_no_write": True})["status"] == DEFINITE_NO_WRITE


@pytest.mark.parametrize("destination,raw", [
    # The shapes the live adapters return (edge_cdp, linkedin_official_member_api, Neo, Meta).
    ("substack", {"status": "SUCCESS", "platform": "substack", "draft_id": "223293057",
                  "public_url": "https://capitalchronicle.substack.com/p/midterm"}),
    ("substack", {"status": "PUBLISHED", "public_object_id": "223293057",
                  "public_object_url": "https://capitalchronicle.substack.com/p/midterm"}),
    ("x", {"status": "DISPATCH_CONFIRMED", "public_object_id": "18001"}),
    ("linkedin", {"status": "SUCCESS", "public_object_id": "urn:li:share:1",
                  "public_object_url": "https://www.linkedin.com/feed/update/urn:li:share:1/"}),
    ("instagram_business", {"status": "ALREADY_SUCCESSFUL_IDEMPOTENT", "media_id": "ig_1"}),
    ("telegram", {"status": "SUCCESS", "ok": True, "id": "61"}),
    ("discord", {"id": "12001"}),
])
def test_each_adapters_exact_success_still_confirms(destination, raw):
    result = normalized(destination, raw)
    assert result["status"] == DISPATCH_CONFIRMED and result["public_object_id"]


def test_the_coordinator_records_a_failure_word_as_unknown_not_confirmed(tmp_path):
    class NotPublishedTelegram(FixtureTransport):
        def publish(self, *, destination, intent, authorization_context):
            result = super().publish(destination=destination, intent=intent,
                                     authorization_context=authorization_context)
            return {**result, "status": "NOT_PUBLISHED", "ok": False} if destination == "telegram" else result

        def readback(self, *, destination, public_object_id, public_object_url, intent):
            if destination == "telegram":
                self.readback_calls.append(destination)
                return {"status": "AMBIGUOUS", "verified": False}
            result = super().readback(destination=destination, public_object_id=public_object_id,
                                      public_object_url=public_object_url, intent=intent)
            result["published_at_utc"] = ORIGINAL
            if destination == "discord":
                result["public_object_url"] = "https://discord.com/channels/111/222/333"
            return result

    store, transport, coordinator, plan, article, root = lifecycle(tmp_path, transport=NotPublishedTelegram())
    result = coordinator.execute_plan("work-1", plan)
    dispatches = {d["platform"]: d for d in store.list_platform_dispatches()}
    assert dispatches["telegram"]["status"] == UNKNOWN_WRITE
    assert result["per_destination"]["telegram"]["status"] != DISPATCH_CONFIRMED
    for destination in ("substack", "discord", "x", "facebook_page"):
        assert dispatches[destination]["status"] == DISPATCH_CONFIRMED
    # The confirmed piece reaches the feed with its four real outlets only.
    outlets = {o["name"] for o in read_records(coordinator.published_content_path)[0]["outlets"]}
    assert "telegram" not in outlets and {"substack", "discord", "x", "facebook_page"} <= outlets


def first_snapshot_with_substack_only(feed):
    """Rewrite the test feed as a first recording made before the derivatives confirmed (CPI, 3 Nov)."""
    row = read_records(feed)[0]
    first = {k: v for k, v in row.items() if k != "content_sha256"}
    first["outlets"] = [o for o in row["outlets"] if o["name"] == "substack"]
    from hashlib import sha256
    first["content_sha256"] = sha256(canonical(first)).hexdigest()
    feed.write_bytes(canonical(first) + b"\n")
    return first, row["outlets"]


def test_later_confirmed_outlets_are_appended_beside_the_unchanged_first_recording(tmp_path):
    store, transport, coordinator, plan, result = publish_with_original_clock(tmp_path)
    feed = coordinator.published_content_path
    first, confirmed = first_snapshot_with_substack_only(feed)
    before = feed.read_bytes()
    synced = sync_confirmed_piece(store, feed, "work-1", recorded_at_utc="2026-11-05T06:00:00+00:00")
    assert synced["status"] == "ALREADY_RECORDED" and synced["outlet_count"] == 1
    assert synced["outlet_update"]["status"] == "OUTLETS_UPDATED"
    assert synced["outlet_update"]["outlet_count"] == 5 and synced["outlet_update"]["previous_outlet_count"] == 1
    assert feed.read_bytes() == before  # the seal and the one-row-per-piece feed are unchanged
    assert current_outlets(feed)[first["content_id"]] == confirmed
    current = read_current_records(feed)
    assert len(current) == 1 and current[0]["outlets"] == confirmed
    assert current[0]["content_sha256"] == first["content_sha256"]
    updates = outlets_path(feed).read_bytes()
    again = sync_confirmed_piece(store, feed, "work-1", recorded_at_utc="2026-11-05T07:00:00+00:00")
    assert again["outlet_update"]["status"] == "OUTLETS_UNCHANGED"
    assert outlets_path(feed).read_bytes() == updates


def test_outlet_updates_refuse_an_unknown_piece_a_changed_canonical_or_a_broken_seal(tmp_path):
    feed = tmp_path / "feed.jsonl"
    from live_contentops.published_content_v1 import append_record
    record = sealed()
    append_record(feed, record)
    x = {"name": "x", "url": "https://x.com/test/status/123"}
    with pytest.raises(PublishedContentError, match="OUTLET_UPDATE_RECORD_UNKNOWN"):
        append_outlet_update(feed, {**record, "content_sha256": "0" * 64}, [*record["outlets"], x],
                             recorded_at_utc="2026-11-04T00:00:00Z")
    with pytest.raises(PublishedContentError, match="OUTLET_UPDATE_CANONICAL_CHANGED"):
        append_outlet_update(feed, record, [{"name": "substack",
            "url": "https://capitalchronicle.substack.com/p/another"}, x], recorded_at_utc="2026-11-04T00:00:00Z")
    with pytest.raises(PublishedContentError, match="OUTLET_UPDATE_PRECEDES_RECORD"):
        append_outlet_update(feed, record, [*record["outlets"], x], recorded_at_utc="2026-11-01T00:00:00Z")
    assert not outlets_path(feed).exists() or outlets_path(feed).read_bytes() == b""
    assert append_outlet_update(feed, record, [*record["outlets"], x],
                                recorded_at_utc="2026-11-04T00:00:00Z")["status"] == "OUTLETS_UPDATED"
    line = json.loads(outlets_path(feed).read_bytes())
    line["outlets"] = record["outlets"]
    outlets_path(feed).write_bytes(canonical(line) + b"\n")
    with pytest.raises(PublishedContentError, match="OUTLET_UPDATE_SEAL_MISMATCH"):
        current_outlets(feed)
    outlets_path(feed).write_bytes(b'{"partial":')
    with pytest.raises(PublishedContentError, match="TORN_OUTLET_UPDATE_TAIL"):
        current_outlets(feed)


def test_the_outlet_file_sits_beside_the_production_feed():
    assert outlets_path(Path(r"A:\Capital Chronicle\Runtime\ContentOps\published_content_v1.jsonl")).name \
        == "published_content_outlets_v1.jsonl"


def test_the_projection_blocker_names_the_recorded_state_or_no_registration():
    ids = lambda destination: DurablePublicationCoordinator._ids("work", "plan", destination)  # noqa: E731
    rows = [{"message_id": "binding", "work_item_id": "work", "destination": DESTINATION,
             "payload": json.dumps({"run_id": "work", "plan_hash": "plan"})},
            {"message_id": ids("telegram")["message_id"], "work_item_id": "work", "destination": "telegram",
             "status": "QUEUED_AFTER_CANONICAL", "payload": "{}"}]
    dispatches = [
        {"dispatch_id": ids("x")["dispatch_id"], "message_id": ids("x")["message_id"], "platform": "x",
         "status": UNKNOWN_WRITE, "public_object_id": None, "public_object_url": None},
        {"dispatch_id": ids("discord")["dispatch_id"], "message_id": ids("discord")["message_id"],
         "platform": "discord", "status": DISPATCH_CONFIRMED, "public_object_id": "1", "public_object_url": None},
        {"dispatch_id": ids("substack")["dispatch_id"], "message_id": ids("substack")["message_id"],
         "platform": "substack", "status": DISPATCH_CONFIRMED, "public_object_id": "2",
         "public_object_url": "https://capitalchronicle.substack.com/p/a"}]
    reconciliations = [
        {"reconciliation_id": ids("discord")["reconciliation_id"], "status": "RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE"},
        {"reconciliation_id": ids("substack")["reconciliation_id"], "status": "RECONCILED_CONFIRMED"}]
    entries = {e["destination"]: e for e in publication_projection(rows, dispatches, reconciliations,
                                                                    run_id="work")["destinations"]}
    assert entries["substack"]["blocker"] is None
    assert entries["discord"]["blocker"] == "RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE"
    assert entries["x"]["blocker"] == UNKNOWN_WRITE
    assert entries["telegram"]["blocker"] == "QUEUED_AFTER_CANONICAL"
    assert entries["youtube"]["blocker"] == "NOT_REGISTERED"
    assert not any(e["blocker"] == "CURRENT_EXTERNAL_IDENTITY_AND_READBACK_NOT_VERIFIED" for e in entries.values())


@pytest.mark.parametrize("ended,causes", [
    (True, {"WINDOW_ENDED_WITHOUT_EDITORIAL_RESULT": 1}), (False, {})])
def test_a_window_that_ended_with_no_result_is_counted_with_its_cause(tmp_path, ended, causes):
    from live_contentops.newsroom_production_day_v1 import newsroom_production_day_id
    store = ContentOpsDurableStore(tmp_path / "day-state.sqlite3")
    day = newsroom_production_day_id(CUTOFF)
    root = tmp_path / day / "window" / "run"
    root.mkdir(parents=True)
    _, binding = make_turn(store, root, "run", window_id="window")
    work = "cc-opportunity-" + sha256_of("run")
    store.register_outbox_message(message_id="native-operation-binding-" + sha256_of("run"),
        work_item_id=work, destination="internal:native-desktop-editorial",
        payload=json.dumps(binding), status="EDITORIAL_INTERNAL")
    end = (datetime.now(timezone.utc) + timedelta(hours=-1 if ended else 1)).isoformat()
    store.register_outbox_message(message_id="native-window-" + sha256_of("window"),
        work_item_id=work, destination="internal:native-desktop-editorial",
        payload=json.dumps({"window": {"end_utc": end}}), status="EDITORIAL_INTERNAL")
    path = persist_native_day_measurement(store, binding)
    measurement = json.loads(Path(path).read_bytes())["native_volume_measurement"]
    assert measurement["first_blocking_causes"] == causes
