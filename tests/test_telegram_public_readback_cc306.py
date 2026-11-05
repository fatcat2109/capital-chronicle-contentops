"""Ops Product, 5 Nov (privacy): every Telegram readback reads the public channel page
https://t.me/s/CapitalChronicle with no sign-in. Telegram Web is signed in to Jim's personal
account, so no request may point an agent there. Controlled protocol checks; no browser."""
import json
from datetime import datetime, timezone, timedelta

import pytest

from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_neo_executor_v1 import NativeNeoExecutor, NativeNeoInputRequired, TOOL
from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff, TELEGRAM_PUBLIC_FEED

FEED = "https://t.me/s/CapitalChronicle"


def setup(tmp_path, monkeypatch, age=1200):
    store = ContentOpsDurableStore(tmp_path / "state.sqlite3")
    store.create_work_item(story_id="story", work_item_id="work", title="test", target_surface="test")
    executor = NativeNeoExecutor(store, operation_id="same-op", output_dir=tmp_path / "requests",
                                 native_invocation_id="controlled-test")
    attempted_at = (datetime.now(timezone.utc) - timedelta(seconds=age)).isoformat()
    monkeypatch.setattr(store, "get_platform_dispatch", lambda key: {"status": "UNKNOWN_WRITE",
                                                                     "dispatched_at": attempted_at})
    return store, executor, NeoDestinationHandoff(native_executor=executor)


INTENT = {"work_item_id": "work", "plan_hash": "plan", "package_identity": "pkg",
          "canonical_url": "https://fatcat2109.github.io/capital-chronicle-preview/assets/EURUSD.html",
          "payload": "EUR/USD: new plan.",
          "destination_plan": {"payload_hash": "hash", "surface": "TELEGRAM_CHANNEL_POST"}}


def pending_request(adapter):
    with pytest.raises(NativeNeoInputRequired) as pending:
        adapter.readback(destination="telegram", intent=INTENT, public_object_id=None, public_object_url=None)
    return pending.value.request


def submit(executor, packet, result):
    request = packet["request"]
    executor.begin(request["request_sha256"])
    executor.submit(request["request_sha256"], {"tool_request_sha256": packet["tool_request_sha256"],
        "tool_observation": {"tool_name": TOOL, "native_invocation_id": "controlled-test",
            "surface": "CODEX_EXEC", "observation_source": "CONTROLLED_TEST_NOT_BROWSER_PROOF",
            "observed_at_utc": datetime.now(timezone.utc).isoformat()},
        "result": {"request_sha256": request["request_sha256"], **result}})


def test_the_telegram_readback_request_names_only_the_public_channel_page(tmp_path, monkeypatch):
    _, _, adapter = setup(tmp_path, monkeypatch)
    request = pending_request(adapter)["request"]
    assert TELEGRAM_PUBLIC_FEED == FEED
    assert request["entry_url"] == FEED
    text = json.dumps(request)
    # The request may name Telegram Web only to forbid it.
    assert "web.telegram.org" in " ".join(request["forbidden"]) and "web.telegram.org" in request["telegram_read_rule"]
    stripped = json.loads(text)
    stripped.pop("telegram_read_rule")
    stripped["forbidden"] = [f for f in stripped["forbidden"] if "telegram" not in f]
    rest = json.dumps(stripped)
    assert "web.telegram.org" not in rest and "signed-in" not in rest.lower()
    assert {u for u in ("https://t.me/s/CapitalChronicle", "https://t.me/CapitalChronicle") if u in rest} == {FEED}


def test_absence_from_the_public_page_needs_no_sign_in(tmp_path, monkeypatch):
    _, executor, adapter = setup(tmp_path, monkeypatch)
    packet = pending_request(adapter)
    submit(executor, packet, {"status": "ABSENT", "observed_identity": "@CapitalChronicle",
        "observed_profile_url": FEED, "authenticated": False, "activity_feed_loaded": True,
        "target_post_absent": True, "observed_text": "Gold: new plan. EUR/USD: the plan is now active."})
    actual = adapter.readback(destination="telegram", intent=INTENT, public_object_id=None, public_object_url=None)
    assert actual["write_absent"] is True


@pytest.mark.parametrize("url", ["https://web.telegram.org/k/#@CapitalChronicle", "https://t.me/CapitalChronicle"])
def test_absence_read_anywhere_else_is_refused(tmp_path, monkeypatch, url):
    _, executor, adapter = setup(tmp_path, monkeypatch)
    packet = pending_request(adapter)
    submit(executor, packet, {"status": "ABSENT", "observed_identity": "@CapitalChronicle",
        "observed_profile_url": url, "authenticated": True, "activity_feed_loaded": True,
        "target_post_absent": True, "observed_text": "Gold: new plan. EUR/USD: the plan is now active."})
    actual = adapter.readback(destination="telegram", intent=INTENT, public_object_id=None, public_object_url=None)
    assert actual["write_absent"] is not True
