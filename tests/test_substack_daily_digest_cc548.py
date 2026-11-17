"""Carry the exact refused 12 November article to one later digest, in temporary stores."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

import pytest

from live_contentops import publication_image_contract_v1 as contract
from live_contentops import substack_daily_digest_v1 as digest
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
from live_contentops.published_content_v1 import canonical
from test_publication_coordinator_v1 import FixtureTransport, _set_mode
from test_substack_daily_digest_v1 import clock, row, setup


FIXTURES = Path(__file__).parent / "fixtures/cc548"


def held_digest(tmp_path, *, state="DEFINITE_NO_WRITE", public_id=None, public_url=None, with_feed=False):
    packet_raw = (FIXTURES / "stored-12nov-packet.json").read_text(encoding="utf-8")
    intent_raw = (FIXTURES / "stored-12nov-intent.json").read_text(encoding="utf-8")
    packet, intent = json.loads(packet_raw), json.loads(intent_raw)
    article = packet["articles"][0]
    rows = []
    if with_feed:
        public = row(article["content_id"], article["published_at_utc"])
        public.update(title=article["title"], standfirst=article["standfirst"],
                      outlets=[{"name": "substack", "url": article["url"]}])
        public.pop("content_sha256")
        public["content_sha256"] = sha256(canonical(public)).hexdigest()
        rows.append(public)
    store, feed = setup(tmp_path, rows)
    store.create_work_item(story_id=packet["digest_id"], work_item_id=packet["digest_id"],
                           title=packet["native_payload"]["title"], target_surface="SUBSTACK_ARTICLE")
    store.register_outbox_message(message_id="substack-digest-" + packet["digest_id"],
        work_item_id=packet["digest_id"], destination=digest.DESTINATION,
        payload=packet_raw, status="EDITORIAL_INTERNAL")
    ids = DurablePublicationCoordinator._ids(packet["digest_id"], packet["plan"]["plan_hash"], "substack")
    store.register_outbox_message(message_id=ids["message_id"], work_item_id=packet["digest_id"],
        destination="substack", payload=intent_raw, status=state)
    store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"],
        platform="substack", status=state, public_object_id=public_id, public_object_url=public_url)
    store.register_reconciliation(reconciliation_id=ids["reconciliation_id"], work_item_id=packet["digest_id"],
                                  status="PUBLICATION_IMAGE_CONTRACT_INVALID")
    return store, feed, packet, ids


@pytest.mark.parametrize("with_feed", [False, True])
def test_refused_digest_article_reaches_the_next_digest_consumer_once(tmp_path, monkeypatch, with_feed):
    store, feed, refused, old_ids = held_digest(tmp_path, with_feed=with_feed)
    original = deepcopy(store.get_outbox_message(old_ids["message_id"]))
    next_day = clock("2026-11-13T12:15:00Z")
    result = digest.prepare_daily_digest(store, feed, now=next_day)
    packet = result["packet"]
    assert packet["digest_id"] == "cc143-digest-2026-11-13"
    assert packet["articles"] == refused["articles"]
    assert [a["content_id"] for a in packet["articles"]] == ["substack:224293572"]
    article_url = refused["articles"][0]["url"]
    assert packet["native_payload"]["body_markdown"].count(article_url) == 1
    assert digest.prepare_daily_digest(store, feed, now=next_day)["packet"] == packet

    # Exercise the actual sole publisher and its media contract, with a local
    # fixture transport. No production store, browser action or network is used.
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    runtime, checked = FixtureTransport(), []
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=runtime,
        readiness_provider=lambda _: {"readiness_state": "READY_AUTHENTICATED"})
    coordinator._clock = lambda: next_day
    validate = contract.validate_write

    def observe(owner, intent, destination):
        checked.append((intent["work_item_id"], destination))
        return validate(owner, intent, destination)

    monkeypatch.setattr(contract, "validate_write", observe)
    published = coordinator.publish_plan(packet["digest_id"], packet["plan"])
    assert published["canonical_article_real_published"]
    assert checked == [(packet["digest_id"], "substack")]
    assert runtime.publish_calls == ["substack"]
    assert digest.digest_status(store, packet)["web_confirmed"]
    coordinator.publish_plan(packet["digest_id"], packet["plan"])
    assert runtime.publish_calls == ["substack"]
    assert digest.prepare_daily_digest(store, feed, now=clock("2026-11-14T12:15:00Z"))["state"] == "NO_CONFIRMED_ARTICLES"
    assert store.get_outbox_message(old_ids["message_id"]) == original
    assert store.get_platform_dispatch(old_ids["dispatch_id"])["status"] == "DEFINITE_NO_WRITE"


@pytest.mark.parametrize("state,public_id,public_url", [
    ("UNKNOWN_WRITE", None, None),
    ("NATIVE_NEO_TOOL_PENDING", None, None),
    ("DISPATCH_ATTEMPT_STARTED", None, None),
    ("DEFINITE_NO_WRITE", "known-object", None),
    ("DEFINITE_NO_WRITE", None, "https://capitalchronicle.substack.com/p/known-object"),
])
def test_pending_or_observed_digest_keeps_its_existing_recovery_path(tmp_path, state, public_id, public_url):
    store, feed, packet, ids = held_digest(tmp_path, state=state, public_id=public_id, public_url=public_url)
    before = store.get_platform_dispatch(ids["dispatch_id"])
    result = digest.prepare_daily_digest(store, feed, now=clock("2026-11-13T12:15:00Z"))
    assert result["packet"] == packet
    assert store.get_platform_dispatch(ids["dispatch_id"]) == before
    assert len(digest.packets(store)) == 1


@pytest.mark.parametrize("now", ["2026-11-11T12:30:00Z", "2026-11-12T12:30:00Z"])
def test_same_day_or_future_refusal_keeps_its_frozen_identity(tmp_path, now):
    store, feed, packet, _ = held_digest(tmp_path)
    result = digest.prepare_daily_digest(store, feed, now=clock(now))
    assert result["packet"] == packet
    assert len(digest.packets(store)) == 1
