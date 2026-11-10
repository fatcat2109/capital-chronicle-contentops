"""Queued Discord work reaches the existing consumer, with exact refusal causes."""
# ruff: noqa: F811
# Pytest fixture names are also test parameters.
from datetime import datetime, timezone
from hashlib import sha256
import json

import pytest

from live_contentops import plan_call_cards_v1 as cards, plan_status_posts_v1 as posts
from live_contentops import plan_analysis_pages_v1 as pages
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
from test_plan_call_cards_cc399 import five, main_root, queue, rows, write, NOW  # noqa: F401
from test_plan_status_publication_cc306 import fake_host
from test_publication_coordinator_v1 import FixtureTransport, _set_mode


def test_new_webhook_only_cards_confirm_through_coordinator_and_keep_their_route(five, main_root, tmp_path, monkeypatch):
    from live_contentops import secret_store_v1

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return NOW.astimezone(tz)

    # The write-boundary expiry check uses the same clock as this copied run.
    monkeypatch.setattr(cards, "datetime", Clock)
    monkeypatch.setattr(secret_store_v1, "read_secret", lambda name: None)
    store, export, _, _ = five
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    queued = queue(store, export, main_root)
    originals = {row["message_id"]: row["payload"] for row in store.list_outbox_messages(destination=posts.DESTINATION)}

    class Recorded(FixtureTransport):
        def __init__(self):
            super().__init__()
            self.intents = []

        def publish(self, *, destination, intent, authorization_context):
            self.publish_calls.append(destination)
            self.intents.append(intent)
            number = str(1000 + len(self.intents))
            if destination == "instagram_business" and intent["native_payload"].get("reuse_run_carousel"):
                number = intent["native_payload"]["carousel_parent_id"]
            return {"status": "SUCCESS", "id": number, "public_url": f"https://example.test/{destination}/{number}"}

    runtime = Recorded()
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=runtime,
        readiness_provider=lambda d: {"readiness_state": "READY_AUTHENTICATED" if d in {"x", "substack_notes"}
                                     else "READY_NON_BROWSER_BINDING"})
    result = posts.publish_ready(store, now=NOW, latest_states=queued["latest_states"], root=tmp_path / "posts",
        host=fake_host, coordinator_for=lambda key, folder: coordinator)
    assert all(row["status"] == "PUBLISHED" for row in result["posts"]), result
    discord = [intent for intent in runtime.intents if intent["destination_plan"]["destination"] == "discord"]
    assert len(discord) == 6  # the run and all five new cards reached Discord
    for intent in discord:
        payload = intent["native_payload"]
        if posts._row_payload(store, intent["work_item_id"])["kind"] == "setup":
            assert payload["discord_channel_post"] is True
            assert not {"discord_thread_parent_id", "reply_to_id"} & payload.keys()
        posts.validate_status_post_intent(store, intent)
    # A later credential change cannot alter a registered card or issue a second copy.
    monkeypatch.setattr(secret_store_v1, "read_secret", lambda name: "later-bot")
    queue(store, export, main_root)
    assert {r["message_id"]: r["payload"] for r in store.list_outbox_messages(destination=posts.DESTINATION)} == originals
    before = len(runtime.intents)
    posts.publish_ready(store, now=NOW, root=tmp_path / "posts", host=fake_host,
        coordinator_for=lambda key, folder: coordinator)
    assert len(runtime.intents) == before


def test_channel_route_refuses_a_substituted_thread_or_reply():
    row = {"kind": "update", "parent_key": "our-card", "discord_delivery": "channel"}
    intent = {"destination_plan": {"destination": "discord"},
              "native_payload": {"discord_channel_post": True, "reply_to_id": "unrelated"}}
    with pytest.raises(posts.PlanPostError, match="DISCORD_CHANNEL_ROUTE_CHANGED"):
        cards.validate_parent_intent(None, row, intent)


def test_legacy_registered_cards_keep_exact_thread_parent(monkeypatch):
    monkeypatch.setattr(cards, "_reference", lambda *a: {"public_object_id": "123", "public_object_url": "https://example.test/123"})
    row = {"kind": "setup", "parent_key": "run", "run_key": "run"}
    parents, deferred = cards._parents(None, row, ["discord"], {"discord": {
        "public_object_id": "123", "thread_parent_id": "123", "parent_key": "run"}})
    assert not deferred and parents["discord"]["thread_parent_id"] == "123"
    assert "delivery_mode" not in parents["discord"]


def test_settled_discord_failures_and_parent_waits_do_not_starve_the_next_card(tmp_path, monkeypatch):
    payloads = [{"key": f"old-{i}", "format": 4, "kind": "setup", "plan_id": f"plan-{i}",
                 "at_utc": "2026-11-10T07:00:00Z"} for i in range(5)]
    payloads.append({"key": "blocked-result", "format": 4, "kind": "result", "parent_key": "missing",
                     "at_utc": "2026-11-10T07:01:00Z"})
    payloads.append({"key": "new", "format": 4, "kind": "setup", "plan_id": "plan-new",
                     "at_utc": "2026-11-10T07:30:00Z"})

    class Store:
        def list_outbox_messages(self, **kw):
            return [{"message_id": p["key"], "status": "PUBLISHING", "payload": json.dumps(p)} for p in payloads]

        def set_outbox_status(self, *a):
            pass

        def create_work_item(self, **kw):
            pass

    def dispatch(store, key, destination):
        if key.startswith("old-") and destination in cards.API_DESTINATIONS:
            return {"status": "DEFINITE_NO_WRITE" if destination == "discord" else "DISPATCH_CONFIRMED"}
        return None

    reached = []
    monkeypatch.setattr(cards, "_dispatch", dispatch)
    monkeypatch.setattr(cards, "_reference", lambda store, key, d: None)
    monkeypatch.setattr(cards, "prepare_post", lambda store, key, **kw: {
        "destinations": [{"destination": "discord"}], "output_dir": str(tmp_path), "deferred_destinations": []})

    class Coordinator:
        def register_plan(self, *a):
            pass

        def execute_plan(self, key, plan):
            reached.append(key)
            return {"per_destination": {"discord": {"status": "DISPATCH_CONFIRMED"}}}

    result = cards.publish_ready(Store(), now=NOW, root=tmp_path, coordinator_for=lambda *a: Coordinator(), limit=1)
    assert "new" in reached
    waiting = {row["key"]: row for row in result["posts"] if row["status"].startswith("WAITING")}
    assert waiting["blocked-result"]["cause"] == "CARD_PARENT_NOT_CONFIRMED"
    assert all(row.get("cause") for row in waiting.values())


def test_run_record_retains_card_keys_preparation_errors_and_each_wait(tmp_path):
    outcomes = [{"key": "bad-card", "status": "NOT_STARTED", "cause": "PLAN_CARD_IMAGE_BYTES_CHANGED"},
        {"key": "waiting-card", "status": "WAITING_FOR_CARD_PARENT", "cause": "CARD_PARENT_NOT_CONFIRMED",
         "deferred_destinations": [{"destination": "discord", "cause": "CARD_PARENT_NOT_CONFIRMED", "parent_key": "run"}]},
        {"key": "limited", "status": "WAITING", "cause": "CARD_WORK_LIMIT_THIS_RUN"},
        {"key": "partial", "status": "PUBLISHING", "per_destination": {"discord": "DEFINITE_NO_WRITE"},
         "destination_causes": {"discord": "DISCORD_CALL_THREAD_BOT_TOKEN_UNAVAILABLE"}}]
    path = posts.record_run({"status": "OK", "publication": {"status": "OK", "posts": outcomes}}, tmp_path, now=NOW)
    line = json.loads(path.read_text(encoding="utf-8"))
    assert line["posts"] == outcomes
    assert line["posts_by_status"] == {"NOT_STARTED": 1, "WAITING_FOR_CARD_PARENT": 1, "WAITING": 1, "PUBLISHING": 1}


def test_run_record_keeps_the_coordinators_safe_adapter_error(tmp_path):
    outcome = {"per_destination": {"discord": {"status": "DEFINITE_NO_WRITE",
        "reconciliation_status": "RECONCILED_ABSENT_SAFE_TO_RETRY",
        "safe_error_classification": "DISCORD_CALL_THREAD_BOT_TOKEN_UNAVAILABLE"}}}
    post = {"key": "legacy-card", "status": "PUBLISHING",
            "destination_causes": posts.destination_causes(outcome)}
    path = posts.record_run({"status": "OK", "publication": {"posts": [post]}}, tmp_path, now=NOW)
    line = json.loads(path.read_text(encoding="utf-8"))
    assert line["posts"][0]["destination_causes"] == {
        "discord": "DISCORD_CALL_THREAD_BOT_TOKEN_UNAVAILABLE"}


def test_unstarted_run_is_retired_when_all_its_cards_have_ended(five, main_root, tmp_path, monkeypatch):
    store, export, _, _ = five
    queue(store, export, main_root)
    members = [r for r in rows(store) if r["kind"] == "setup"]
    for row in members:
        store.set_outbox_status(row["key"], posts.SUPERSEDED)
    monkeypatch.setattr(cards, "prepare_post", lambda *a, **kw: pytest.fail("an ended run must not render or send"))
    result = cards.publish_ready(store, now=NOW, root=tmp_path,
        latest_states={row["plan_id"]: "EXPIRED" for row in members})
    assert len(result["posts"]) == 1
    assert result["posts"][0]["cause"] == "RUN_HAS_NO_CURRENT_CARDS"


def test_exact_former_x_policy_no_write_remains_resumable(monkeypatch):
    class Store:
        def get_reconciliations_for_work_item(self, key):
            return [{"reconciliation_id": "reconciliation_former-bar", "status": "X_NON_API_AUTOMATION_PROHIBITED"}]
    monkeypatch.setattr(cards, "_dispatch", lambda s, k, d: {
        "status": "DEFINITE_NO_WRITE" if d == "x" else "DISPATCH_CONFIRMED", "dispatch_id": "dispatch_former-bar"})
    assert cards._ready_destinations(Store(), {"key": "card"}) == ["x"]


def _registered_link(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    key, original, pid = "analysis-link", "original-card", "plan-original"
    store.create_work_item(story_id=key, title="Analysis link", target_surface="MULTI_PLATFORM", work_item_id=key)
    row = {"schema_version": posts.SCHEMA, "key": original, "symbol": "EURUSD", "levels": {}}
    store.register_outbox_message(message_id=original, work_item_id=key, destination=posts.DESTINATION,
        payload=json.dumps(row), status="PUBLISHED")
    plan = {"plan_hash": sha256(key.encode()).hexdigest(), "output_dir": str(tmp_path)}
    value = {"link_id": key, "original_key": original, "plan_id": pid, "plan": plan}
    store.register_outbox_message(message_id=key, work_item_id=key, destination=pages.DESTINATION,
        payload=json.dumps(value), status="EDITORIAL_INTERNAL")
    ids = DurablePublicationCoordinator._ids(key, plan["plan_hash"], "discord")
    intent = {"work_item_id": key, "plan_hash": plan["plan_hash"], "plan_analysis_link": key}
    store.register_outbox_message(message_id=ids["message_id"], work_item_id=key, destination="discord",
        payload=json.dumps(intent), status="READY")
    return store, key, pid, plan, ids


def test_ended_unattempted_analysis_link_is_retired_with_its_cause(tmp_path):
    store, key, pid, _, ids = _registered_link(tmp_path)
    result = pages.resume_discord_links(store, latest_states={pid: "EXPIRED"}, now=NOW)
    assert result[0]["key"] == key and result[0]["cause"] == "PLAN_ALREADY_EXPIRED"
    assert store.get_outbox_message(ids["message_id"])["status"] == "DERIVATIVE_EXPIRED_STALE_NO_WRITE"
    assert store.get_platform_dispatch(ids["dispatch_id"]) is None
    assert pages.resume_discord_links(store, latest_states={pid: "EXPIRED"}, now=NOW) == []


@pytest.mark.parametrize("dispatch_state", [None, "UNKNOWN_WRITE"])
def test_analysis_resume_uses_exact_plan_and_preserves_uncertain_attempt(tmp_path, dispatch_state):
    store, key, pid, plan, ids = _registered_link(tmp_path)
    if dispatch_state:
        store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"],
            platform="discord", status=dispatch_state)
    observed = []

    class Coordinator:
        _ids = staticmethod(DurablePublicationCoordinator._ids)

        def execute_plan(self, work, exact):
            observed.append((work, exact))
            return {"per_destination": {"discord": {"status": dispatch_state or "DISPATCH_CONFIRMED"}}}

    result = pages.resume_discord_links(store, latest_states={pid: "EXPIRED" if dispatch_state else "WAITING"},
        now=NOW, coordinator_for=lambda *a: Coordinator())
    assert observed == [(key, plan)]
    assert result[0]["status"] == (dispatch_state or "DISPATCH_CONFIRMED")
    if dispatch_state:
        assert store.get_platform_dispatch(ids["dispatch_id"])["status"] == "UNKNOWN_WRITE"


def test_delayed_new_card_keeps_its_original_registration_clock(five, main_root):
    store, export, _, _ = five
    queue(store, export, main_root)
    row = next(r for r in rows(store) if r["kind"] == "setup")
    row["delayed_at_utc"] = datetime(2026, 11, 10, 10, tzinfo=timezone.utc).isoformat()
    copy = cards.compose(row)
    assert "Delayed update to the plan registered 10 Nov 02:45 ET" in copy["text"]
    assert "10 Nov 05:00 ET" not in copy["text"]


def test_expiry_omitted_from_post_events_does_not_revive_a_setup(five, main_root):
    store, export, plans, events = five
    raw = plans[0]
    raw.update(status="EXPIRED", outcome={"state": "NOT_SCORED_UNTRIGGERED"})
    from test_plan_status_posts_cc306 import event
    events.append(event(raw["plan_id"], "EXPIRED", "2026-11-10T07:59:00Z"))
    write(export, plans, events)
    result = queue(store, export, main_root)
    assert result["latest_states"][raw["plan_id"]] == "EXPIRED"
    assert not any(row["kind"] == "setup" and row["plan_id"] == raw["plan_id"] for row in rows(store))


def test_frozen_copy_survives_a_formatter_change_but_changed_intents_and_private_copy_do_not(monkeypatch):
    row = {"format": 4, "kind": "update", "key": "frozen-update", "conditional_calls": [],
           "text": "Gold: the call is active.\n\n" + cards.NOTICES}
    native = {"full_text": row["text"]}
    monkeypatch.setattr(posts, "_expected", lambda *a: (row, {"discord": native}))
    monkeypatch.setattr(cards, "compose", lambda *a: pytest.fail("frozen text must not be recomposed"))
    intent = {"plan_status_post": row["key"], "work_item_id": row["key"],
              "destination_plan": {"destination": "discord"}, "native_payload": dict(native)}
    posts.validate_status_post_intent(None, intent)
    with pytest.raises(posts.PlanPostError, match="INTENT_COPY_CHANGED"):
        posts.validate_status_post_intent(None, {**intent, "native_payload": {"full_text": "Changed copy"}})
    row["text"] = "Positions we mention are model positions on a demo account.\n\n" + cards.NOTICES
    native["full_text"] = row["text"]
    with pytest.raises(ValueError, match="PRIVATE_OR_EXECUTION_COPY_FORBIDDEN"):
        posts.validate_status_post_intent(None, {**intent, "native_payload": dict(native)})


def _pending_update(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "pending.sqlite3")
    row = {"schema_version": posts.SCHEMA, "key": "pending-update", "format": 4,
           "kind": "update", "symbol": "EURUSD", "plan_id": "our-plan", "state": "TRIGGERED",
           "at_utc": NOW.isoformat(), "text": "Exact retained copy"}
    store.create_work_item(story_id=row["key"], title="Call update", target_surface="MULTI_PLATFORM",
                           work_item_id=row["key"])
    store.register_outbox_message(message_id=row["key"], work_item_id=row["key"],
        destination=posts.DESTINATION, payload=json.dumps(row), status=posts.READY)
    return store, row


def test_ended_unstarted_fill_update_retires_before_preparation_without_changing_bytes(tmp_path, monkeypatch):
    store, row = _pending_update(tmp_path)
    before = store.get_outbox_message(row["key"])["payload"]
    monkeypatch.setattr(cards, "prepare_post", lambda *a, **kw: pytest.fail("an ended fill is not current news"))
    result = cards.publish_ready(store, now=NOW, latest_states={row["plan_id"]: "RESULT"}, root=tmp_path)
    assert result["posts"] == [{"key": row["key"], "status": posts.SUPERSEDED,
                                "cause": "PLAN_UPDATE_SUPERSEDED_BY_RESULT"}]
    assert store.get_outbox_message(row["key"])["payload"] == before
    assert store.get_outbox_message(row["key"])["status"] == posts.SUPERSEDED


@pytest.mark.parametrize("dispatch_status", [None, "UNKNOWN_WRITE", "DISPATCH_CONFIRMED"])
def test_private_frozen_copy_closes_only_when_no_send_needs_recovery(tmp_path, monkeypatch, dispatch_status):
    store, row = _pending_update(tmp_path)
    before = store.get_outbox_message(row["key"])["payload"]
    if dispatch_status:
        ids = DurablePublicationCoordinator._ids(row["key"], sha256(("plan-status-post:" + row["key"]).encode()).hexdigest(), "discord")
        store.register_outbox_message(message_id=ids["message_id"], work_item_id=row["key"], destination="discord",
            payload="{}", status=dispatch_status)
        store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"],
            platform="discord", status=dispatch_status)

    def refused(*args, **kwargs):
        raise posts.PlanPostError("PRIVATE_OR_EXECUTION_COPY_FORBIDDEN")

    monkeypatch.setattr(cards, "prepare_post", refused)
    result = cards.publish_ready(store, now=NOW, latest_states={row["plan_id"]: "TRIGGERED"}, root=tmp_path)
    expected = "NOT_STARTED" if dispatch_status else posts.SUPERSEDED
    assert result["posts"][0]["status"] == expected
    assert result["posts"][0]["cause"] == "PRIVATE_OR_EXECUTION_COPY_FORBIDDEN"
    assert store.get_outbox_message(row["key"])["payload"] == before
    if dispatch_status:
        assert store.get_platform_dispatch(ids["dispatch_id"])["status"] == dispatch_status
        assert store.get_outbox_message(row["key"])["status"] == posts.READY


def test_current_scored_ending_prevents_an_old_fill_from_becoming_a_new_setup(five, main_root, monkeypatch):
    store, export, plans, _ = five
    pid = plans[0]["plan_id"]
    monkeypatch.setattr(cards, "_result_rows", lambda export: [{"plan_id": pid, "key": "ending",
        "to": "RESULT", "at_utc": NOW.isoformat(), "symbol": "EURUSD"}])
    result = queue(store, export, main_root)
    assert result["latest_states"][pid] == "RESULT"
    assert not any(row["kind"] == "setup" and row["plan_id"] == pid for row in rows(store))
