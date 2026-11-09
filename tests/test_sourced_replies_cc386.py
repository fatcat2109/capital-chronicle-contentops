from datetime import datetime, timezone, timedelta
import hashlib
import json

import pytest
from live_contentops import sourced_replies_v1 as replies
from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import (
    _durable_intent_inputs,
)
from test_publication_coordinator_v1 import FixtureTransport, _coordinator, _set_mode

NOW = datetime.now(timezone.utc)
FEED = {"generated_at_utc": NOW.isoformat(), "rows": [{"handle": "Author"}]}


def candidate(tmp_path, author="author", target="123", platform="threads"):
    source = tmp_path / "official-report.txt"
    source.write_text("Official release: core prices rose 0.2% in the month.")
    return {
        "platform": platform,
        "target_author": author,
        "list_author": "Author",
        "target_id": target,
        "target_url": f"https://www.threads.com/@{author}/post/Code{target}"
        if platform == "threads"
        else f"https://x.com/{author}/status/{target}",
        "point": "monthly versus annual",
        "target_claim": "annual inflation is all that matters",
        "stance": "The monthly trend matters",
        "addition": "core prices rose 0.2%",
        "source_label": "Official release",
        "text": "The monthly trend matters: core prices rose 0.2% (Official release). Analysis, not financial advice.",
        "image": None,
        "source": {
            "path": str(source),
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "known_at_utc": (NOW - timedelta(hours=1)).isoformat(),
            "excerpt": "core prices rose 0.2%",
        },
        "editorial_model": {
            "model": "recorded-native-model",
            "effort": "recorded-effort",
            "invocation_id": "fixture",
        },
    }


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    monkeypatch.setattr(replies, "read_target", lambda row: {})
    transport = FixtureTransport()
    store, _, coordinator = _coordinator(tmp_path, runtime=transport)
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    coordinator.published_content_path = tmp_path / "published.jsonl"
    row = replies.stage(store, candidate(tmp_path), feed=FEED, now=NOW)
    return store, coordinator, transport, row


def test_live_consumer_gets_exact_reply_and_schedules_existing_daily_audience(
    prepared, tmp_path
):
    store, coordinator, transport, row = prepared
    result = replies.publish(
        store, row["key"], coordinator=coordinator, root=tmp_path / "replies", now=NOW
    )
    assert transport.publish_calls == ["threads"], result
    message = next(r for r in store.list_outbox_messages(destination="threads"))
    intent = json.loads(message["payload"])
    assert intent["sourced_reply"] == row["key"] and "plan_status_post" not in intent
    assert intent["native_payload"]["reply_to_id"] == "123"
    assert _durable_intent_inputs(intent)["payloads"]["threads"]["text"] == row["text"]
    assert "published_content_export" not in intent
    assert result["reply"]["readback_url"]
    from test_daily_app_performance_learning_v1 import _supervisor

    supervisor = _supervisor(tmp_path, store=store, clock=lambda: NOW)
    supervisor._run_performance_observations(NOW)
    result["reply"] = replies.report_one(store, row)
    assert len(result["reply"]["audience_24h"]) == 1
    replies.publish(
        store, row["key"], coordinator=coordinator, root=tmp_path / "replies", now=NOW
    )
    assert transport.publish_calls == ["threads"]


def test_unknown_write_does_not_repeat(prepared, tmp_path):
    store, coordinator, transport, row = prepared
    transport.raise_after_write = True
    transport.ambiguous = True
    for _ in range(2):
        replies.publish(
            store,
            row["key"],
            coordinator=coordinator,
            root=tmp_path / "replies",
            now=NOW,
        )
    assert transport.publish_calls == ["threads"]
    assert not replies.report(store)[0]["readback_url"]


def test_frozen_target_and_source_are_rechecked(prepared, tmp_path):
    store, coordinator, _, row = prepared
    plan = replies.plan_for(store, row["key"], root=tmp_path)
    plan["destinations"][0]["payload"] = "changed"
    with pytest.raises(ValueError, match="REPLY_PLAN_CHANGED"):
        coordinator.register_plan(row["key"], plan)
    Path = __import__("pathlib").Path
    Path(row["source"]["path"]).write_text("changed")
    with pytest.raises(ValueError, match="REPLY_SOURCE_BINDING_CHANGED"):
        replies.plan_for(store, row["key"], root=tmp_path)


def test_daily_author_and_total_attempt_caps(prepared, tmp_path):
    store, _, _, row = prepared
    replies.reserve(store, row, NOW)
    with pytest.raises(ValueError, match="ONE_REPLY_PER_AUTHOR"):
        replies.reserve(store, {**row, "key": "another"}, NOW)
    for i in range(1, 5):
        store.create_work_item(
            story_id=str(i),
            title="Reply",
            target_surface="MULTI_PLATFORM",
            work_item_id=str(i),
        )
        replies.reserve(store, {**row, "key": str(i), "target_author": str(i)}, NOW)
    with pytest.raises(ValueError, match="FIVE_REPLIES"):
        replies.reserve(store, {**row, "key": "six", "target_author": "six"}, NOW)


def test_x_is_staged_but_requested_neo_route_obeys_actual_platform_rules(
    prepared, tmp_path
):
    store, _, _, _ = prepared
    row = replies.stage(store, candidate(tmp_path, platform="x"), feed=FEED, now=NOW)
    with pytest.raises(ValueError, match="X_RULES_API_ONLY"):
        replies.reserve(store, row, NOW)


def test_unique_interaction_and_no_links_or_private_copy(prepared, tmp_path):
    store, _, _, row = prepared
    assert replies.stage(store, candidate(tmp_path), feed=FEED, now=NOW) == row
    other = candidate(tmp_path)
    other["point"] = "another point"
    with pytest.raises(ValueError, match="ALREADY_SELECTED"):
        replies.stage(store, other, feed=FEED, now=NOW)
    for text in [" https://example.com", " follow us", " CFD"]:
        with pytest.raises(ValueError, match="LINK_PROMOTION_OR_CFD"):
            replies.validate({**row, "text": row["text"] + text})


def test_debate_needs_a_confirmed_real_parent(prepared, tmp_path):
    store, _, _, row = prepared
    other = candidate(tmp_path, target="456")
    other["debate_parent_key"] = row["key"]
    with pytest.raises(ValueError, match="CONFIRMED_PARENT"):
        replies.stage(store, other, feed=FEED, now=NOW)


def test_provider_target_must_match_real_permalink_author_and_claim(
    tmp_path, monkeypatch
):
    from live_contentops import threads_adapter_v6 as api

    row = candidate(tmp_path)
    monkeypatch.setattr(api, "_threads_token", lambda: "fixture-token")
    monkeypatch.setattr(
        api,
        "_get_json",
        lambda *a, **k: {
            "id": "123",
            "text": row["target_claim"],
            "username": "wrong-author",
            "permalink": row["target_url"],
        },
    )
    with pytest.raises(ValueError, match="PROVIDER_TARGET_IDENTITY"):
        replies.read_target(row)


def test_provider_readback_proves_the_reply_edge(monkeypatch):
    from live_contentops import threads_adapter_v6 as api

    monkeypatch.setattr(
        api,
        "_get_json",
        lambda *a, **k: {
            "id": "456",
            "text": "specific reply",
            "username": "official.capitalchronicle",
            "permalink": "https://www.threads.com/@official.capitalchronicle/post/Code",
        },
    )
    monkeypatch.setattr(
        api,
        "readback_threads_chain",
        lambda **k: {"status": "FAILED_THREADS_REPLY_CHAIN_READBACK"},
    )
    result = api.readback_threads_post(
        post_id="456",
        expected_text="specific reply",
        access_token="fixture",
        expected_parent_id="123",
    )
    assert result["status"] != "SUCCESS"
    assert result["content_binding_checks"]["reply_parent_match"] is False


def test_warning_stops_platform_even_for_another_author(prepared):
    store, _, _, row = prepared
    replies.stop_on_warning(store, row, "HTTP_429")
    with pytest.raises(ValueError, match="PLATFORM_WARNING_STOP"):
        replies.reserve(store, {**row, "target_author": "other"}, NOW)


def test_owned_image_uses_existing_delivery_manifest_and_reply_payload(
    prepared, tmp_path
):
    store, coordinator, _, _ = prepared
    folder = tmp_path / "CC-386" / "media"
    folder.mkdir(parents=True)
    image = folder / "card.png"
    image.write_bytes(b"fixture PNG bytes")
    sha = hashlib.sha256(image.read_bytes()).hexdigest()
    manifest = folder / "delivery.json"
    manifest.write_text(
        json.dumps(
            {
                "assets": [
                    {
                        "sha256": sha,
                        "public_delivery_sha256": sha,
                        "verified_public_delivery_url": "https://res.cloudinary.com/fixture/image/upload/card.png",
                        "local_public_hash_continuity": True,
                        "absolute_local_source_path": str(image),
                    }
                ]
            }
        )
    )
    candidate_ = candidate(tmp_path, target="789")
    candidate_["image"] = {
        "asset_id": "owned-card",
        "path": str(image),
        "sha256": sha,
        "rights_source": "Capital Chronicle owned fact card",
        "public_redistribution_allowed": True,
        "delivery_manifest": {
            "path": str(manifest),
            "sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
        },
    }
    row = replies.stage(store, candidate_, feed=FEED, now=NOW)
    plan = replies.plan_for(store, row["key"], root=tmp_path / "replies")
    coordinator.register_plan(row["key"], plan)
    intent = next(
        json.loads(m["payload"])
        for m in store.list_outbox_messages(destination="threads")
        if m["work_item_id"] == row["key"]
    )
    data = _durable_intent_inputs(intent)
    assert data["local_media"] == str(image)
    assert data["public_image_url"].endswith("card.png")
    assert data["payloads"]["threads"]["reply_to_id"] == "789"
