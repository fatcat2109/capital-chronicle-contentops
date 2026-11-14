"""Replay the stored gold work item and run root through their real consumers."""
from copy import deepcopy
from datetime import timedelta
import json
from pathlib import Path

import pytest

from live_contentops import plan_call_cards_v1 as cards, plan_status_posts_v1 as posts
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore

ROWS = json.loads((Path(__file__).parent / "fixtures/cc584/stored-plan-rows.json").read_bytes())


@pytest.fixture
def replay(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    store.create_work_item(story_id=posts.WORK_ITEM_ID, work_item_id=posts.WORK_ITEM_ID,
                          title="Stored public rows", target_surface="MULTI_PLATFORM")
    for held in ROWS["rows"]:
        store.register_outbox_message(message_id=held["message_id"], work_item_id=posts.WORK_ITEM_ID,
            destination=posts.DESTINATION, payload=json.dumps(held["payload"]), status=posts.READY)
    return store


@pytest.mark.parametrize("index,at", [(0, "2026-11-12T17:48:36.204344Z"), (1, "2026-11-12T05:03:46Z")])
def test_stored_late_card_and_header_never_reach_preparation(replay, tmp_path, monkeypatch, index, at):
    key = ROWS["rows"][index]["message_id"]
    for held in ROWS["rows"]:
        if held["message_id"] != key:
            replay.set_outbox_status(held["message_id"], posts.SUPERSEDED)
    seen = []
    monkeypatch.setattr(cards, "prepare_post", lambda *a, **k: seen.append(a) or
                        {"destinations": [], "deferred_destinations": [], "output_dir": str(tmp_path)})
    cards.publish_ready(replay, now=posts._utc(at), root=tmp_path)
    assert seen == []
    assert replay.get_outbox_message(key)["status"] == posts.STALE


@pytest.mark.parametrize("status", [posts.STALE, posts.SUPERSEDED])
def test_previously_issued_intent_cannot_revive_a_retired_row(replay, monkeypatch, status):
    row = deepcopy(ROWS["rows"][0]["payload"])
    replay.set_outbox_status(row["key"], status)
    class Clock(posts.datetime):
        @classmethod
        def now(cls, tz=None):
            return posts._utc(row["at_utc"]) + timedelta(minutes=1)
    monkeypatch.setattr(cards, "datetime", Clock)
    with pytest.raises(ValueError, match="STALE|SUPERSEDED"):
        cards.validate_parent_intent(replay, row, {"destination_plan": {"destination": "telegram"}})


def test_header_requires_a_viable_call_on_its_own_destination(replay, tmp_path, monkeypatch):
    row = deepcopy(ROWS["rows"][1]["payload"])
    for key in row["card_keys"]:
        replay.set_outbox_status(key, posts.SUPERSEDED)
    class Clock(posts.datetime):
        @classmethod
        def now(cls, tz=None):
            return posts._utc(row["at_utc"]) + timedelta(minutes=1)
    monkeypatch.setattr(cards, "datetime", Clock)
    with pytest.raises(ValueError, match="RUN_HAS_NO_POSTABLE_CALL"):
        cards.validate_parent_intent(replay, row, {"destination_plan": {"destination": "telegram"}})


@pytest.mark.parametrize("destination", ["telegram", "x", "substack_notes", "discord", "threads", "facebook_page"])
def test_cards_never_use_an_exhausted_capture_as_text_fallback(tmp_path, monkeypatch, destination):
    from live_contentops import post_visuals_v1 as visuals, publication_image_contract_v1 as image
    monkeypatch.setattr(image, "bounded_text_fallback", lambda *a, **k: {"status": "TEXT_ONLY"})
    with pytest.raises(ValueError, match="EVERY_POST_IMAGE_REQUIRED"):
        visuals.require_publication_image(destination, {"article": {"plan_publication_kind": "setup"},
            "output_dir": str(tmp_path), "media_assets": [], "payloads": {destination: {}}})


@pytest.mark.parametrize("status", ["UNKNOWN_WRITE", "ATTEMPT_STARTED", "NATIVE_NEO_PENDING"])
def test_stale_card_keeps_exact_readback_without_preparing_or_publishing(replay, tmp_path, monkeypatch, status):
    from hashlib import sha256
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator as Coordinator
    row = ROWS["rows"][0]["payload"]
    key = row["key"]
    replay.create_work_item(story_id=key, work_item_id=key, title="Possibly sent card", target_surface="MULTI_PLATFORM")
    ids = Coordinator._ids(key, sha256(("plan-status-post:" + key).encode()).hexdigest(), "telegram")
    replay.register_outbox_message(message_id=ids["message_id"], work_item_id=key,
        destination="telegram", payload=json.dumps({"work_item_id": key}), status=status)
    replay.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"],
        platform="telegram", status=status)
    replay.set_outbox_status(key, "PUBLISHING")
    calls = []
    class ExistingReadback:
        def readback_existing_dispatch(self, dispatch_id):
            calls.append(dispatch_id)
            return {"dispatch_id": dispatch_id, "reconciliation_status": "UNKNOWN_WRITE",
                    "publish_called": False}
    monkeypatch.setattr(cards, "prepare_post", lambda *a, **k: pytest.fail("stale card must not prepare"))
    result = cards.publish_ready(replay, now=posts._utc("2026-11-12T17:48:36.204344Z"), root=tmp_path,
                                 coordinator_for=lambda *a: ExistingReadback())
    assert calls == [ids["dispatch_id"]]
    assert replay.get_platform_dispatch(ids["dispatch_id"])["status"] == status
    assert replay.get_outbox_message(ids["message_id"])["status"] == status
    observed = next(r for r in result["posts"] if r["key"] == key)
    assert observed["readbacks"][0]["publish_called"] is False
