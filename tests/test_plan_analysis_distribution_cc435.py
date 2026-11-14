"""Confirmed plan pages reach the existing run and transport consumers."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json

import pytest

from live_contentops import plan_analysis_pages_v1 as pages
from live_contentops import plan_call_cards_v1 as cards
from live_contentops import plan_status_posts_v1 as posts
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator as Coordinator
from test_plan_analysis_pages_cc432 import source, rendered  # noqa: F401
from test_plan_call_cards_cc399 import five, main_root  # noqa: F401


def confirm(store, key, plan_hash, destination, number, url):
    ids = Coordinator._ids(key, plan_hash, destination)
    store.register_outbox_message(message_id=ids["message_id"], work_item_id=key,
                                  destination=destination, payload="{}")
    store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"],
        platform=destination, status="DISPATCH_CONFIRMED", public_object_id=number, public_object_url=url)
    store.register_reconciliation(reconciliation_id=ids["reconciliation_id"], work_item_id=key,
                                  status="RECONCILED_CONFIRMED")


@pytest.fixture
def ready(source, tmp_path):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    packet = pages.register_page(store, rendered(source, tmp_path))
    confirm(store, packet["page_id"], packet["plan"]["plan_hash"], "substack", "123",
            "https://capitalchronicle.substack.com/p/full-original-plan")
    original = "original-call"
    store.create_work_item(story_id=original, work_item_id=original, title="Original call", target_surface="MULTI_PLATFORM")
    store.register_outbox_message(message_id=original, work_item_id=original, destination=posts.DESTINATION,
        payload=json.dumps({"key": original, "plan_id": packet["plan_id"], "kind": "setup", "state": "WAITING"}),
        status="PUBLISHED")
    for destination in ("telegram", "discord", "threads", "facebook_page", "instagram_business", "x"):
        confirm(store, original, sha256(("plan-status-post:" + original).encode()).hexdigest(), destination,
                "parent-" + destination, "https://example.test/" + destination + "/parent")
    return store, packet, original


def test_installed_status_run_distributes_all_eight_and_resumes_without_duplicate(ready, monkeypatch, tmp_path):
    from test_publication_coordinator_v1 import FixtureTransport, _set_mode
    store, packet, _ = ready
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    runtime = FixtureTransport()
    coordinator = Coordinator(store=store, transport_runtime=runtime,
        readiness_provider=lambda d: {"readiness_state": "READY_AUTHENTICATED"},
        clock=lambda: datetime(2026, 11, 10, 2, tzinfo=timezone.utc))
    coordinator.allow_prior_confirmed_distribution = True

    def publish(value_store, value):
        assert value_store is store
        coordinator.recovery_scope = {"work_item_id": value["link_id"], "plan": value["plan"], "exact_work_item_only": True}
        return coordinator.publish_plan(value["link_id"], value["plan"])

    monkeypatch.setattr(pages, "publish_link", publish)
    first = posts.publish_ready(store, now=datetime.now(timezone.utc), root=tmp_path / "posts")
    assert {r["destination"] for r in first["analysis_distribution"]["links"]} == set(cards.DESTINATIONS)
    assert set(runtime.publish_calls) == set(cards.DESTINATIONS)
    assert len(runtime.publish_calls) == 8
    intents = [json.loads(r["payload"]) for d in cards.DESTINATIONS for r in store.list_outbox_messages(destination=d)
               if json.loads(r["payload"]).get("plan_analysis_link")]
    assert len(intents) == 8
    assert all(packet["summary"]["macro"] in i["native_payload"]["full_text"] for i in intents
               if i["native_payload"]["destination"] != "threads")
    thread = next(i["native_payload"]["text"] for i in intents if i["native_payload"]["destination"] == "threads")
    assert len(thread) <= 500
    assert all(label + ":" in thread for label in ("Macro", "Fundamental", "Technical", "Geopolitical",
                                                   "Priced in", "Scenarios", "Desk review"))
    assert all("https://capitalchronicle.substack.com/p/full-original-plan" in i["native_payload"]["full_text"] for i in intents)
    posts.publish_ready(store, now=datetime.now(timezone.utc), root=tmp_path / "posts")
    assert len(runtime.publish_calls) == 8


@pytest.mark.parametrize("destination", ["facebook_page", "instagram_business"])
def test_analysis_link_calls_the_existing_official_comment_route(ready, monkeypatch, destination):
    from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as pipeline
    from live_contentops import facebook_page_adapter_v6 as facebook, instagram_adapter_v6 as instagram
    store, packet, original = ready
    value = pages.register_link(store, packet, original_key=original, destination=destination)
    Coordinator(store=store, transport_runtime=None).register_plan(value["link_id"], value["plan"])
    row = store.list_outbox_messages(work_item_id=value["link_id"], destination=destination)[0]
    intent = json.loads(row["payload"])
    calls = []
    adapter = facebook if destination == "facebook_page" else instagram
    name = "execute_facebook_comment" if destination == "facebook_page" else "execute_instagram_comment"
    monkeypatch.setattr(adapter, name, lambda **kw: calls.append(kw) or {"status": "SUCCESS", "id": "comment"})
    result = pipeline._publish_one_destination_from_durable_intent(destination=destination, intent=intent,
        authorization_context={"operating_mode": "AUTONOMOUS_DEFAULT", "dispatch_attempt_identity": intent["attempt_identity"]})
    assert result["status"] == "SUCCESS"
    assert calls[0]["message"] == value["native_payload"]["text"]
    assert calls[0]["post_id" if destination == "facebook_page" else "media_id"] == "parent-" + destination


def test_x_reply_thread_keeps_all_sections_links_and_weighted_limits(ready):
    store, packet, original = ready
    value = pages.register_link(store, packet, original_key=original, destination="x")
    payload = value["native_payload"]
    assert payload["reply_to_id"] == "parent-x"
    assert all(posts._x_length(p["text"]) <= 280 for p in payload["posts"])
    assert all(label in payload["full_text"] for label in ("Macro", "Technical", "Scenarios", "Desk review"))
    assert packet["summary"]["macro"] in payload["full_text"]
    assert value["plan"]["destinations"][0]["payload"] == payload["full_text"]
    assert pages.validate_link_plan(store, value["link_id"], value["plan"]) == value


def test_cc536_new_plan_post_durable_consumer_carries_confirmed_method_page(ready, tmp_path):
    from test_measured_odds_series_cc536 import confirm_method
    store, packet, original = ready
    reference = confirm_method(store, tmp_path)
    value = pages.register_link(store, packet, original_key=original, destination="x")
    assert value["method_page_reference"] == reference
    assert reference["canonical_url"] in value["native_payload"]["reply_texts"][-1]
    assert pages.validate_link_plan(store, value["link_id"], value["plan"]) == value
    co = Coordinator(store=store, transport_runtime=None)
    co.register_plan(value["link_id"], value["plan"])
    durable = store.get_outbox_message(Coordinator._ids(value["link_id"], value["plan"]["plan_hash"], "x")["message_id"])
    intent = json.loads(durable["payload"])
    assert reference["canonical_url"] in intent["native_payload"]["full_text"]
    assert value["parent"]["public_object_id"] == "parent-x"


@pytest.mark.parametrize("destination", ["telegram", "discord", "threads", "x", "substack_notes"])
def test_new_reader_links_use_held_layers_without_legacy_section_requirements(source, tmp_path, destination):
    root, _, plan, old = source
    manuscript = {**old, "reader_contract": "CC466_V1", "title": "Rates shape the euro.",
        "sections": {key: deepcopy(old["sections"]["macro"]) for key, _ in pages.READER_SECTIONS}}
    labels = dict(pages.READER_SECTIONS)
    for key, label in labels.items():
        manuscript["sections"][key]["summary"] = "The " + label.lower() + " matters."
    manuscript["sections"]["scenarios"]["summary"] = "Main (55%): conditions hold. Alternative (35%): conditions change."
    store = ContentOpsDurableStore(tmp_path / "reader.sqlite3")
    packet = pages.register_page(store, pages.render(plan, manuscript, run_root=root, output_dir=tmp_path / "reader"))
    confirm(store, packet["page_id"], packet["plan"]["plan_hash"], "substack", "123",
            "https://capitalchronicle.substack.com/p/full-original-plan")
    original = "original-call"
    store.create_work_item(story_id=original, work_item_id=original, title="Original call", target_surface="MULTI_PLATFORM")
    store.register_outbox_message(message_id=original, work_item_id=original, destination=posts.DESTINATION,
        payload=json.dumps({"key": original, "plan_id": packet["plan_id"], "kind": "setup", "state": "WAITING"}),
        status="PUBLISHED")
    confirm(store, original, sha256(("plan-status-post:" + original).encode()).hexdigest(), destination,
            "parent-" + destination, "https://example.test/" + destination + "/parent")
    value = pages.register_link(store, packet, original_key=original, destination=destination)
    text = value["native_payload"]["full_text"]
    assert "Fundamental:" not in text and "Geopolitical:" not in text and "Desk review:" not in text
    assert "Main (55%):" in text and "Alternative (35%):" in text
    forces = [line for line in text.splitlines() if any(line.startswith(label + ":")
        for label in ("Macro", "Priced in", "Positioning", "Fear", "Story", "Structure"))]
    assert 0 < len(forces) <= (3 if destination in {"x", "threads"} else 5)
    assert all(line.split(": ", 1)[1] in packet["summary"].values() for line in forces)
    assert pages.validate_link_plan(store, value["link_id"], value["plan"]) == value
    before = store.get_outbox_message(value["link_id"])["payload"]
    packet["summary"]["macro"] = "A later revision must not replace this issued link."
    assert pages.register_link(store, packet, original_key=original, destination=destination) == value
    assert store.get_outbox_message(value["link_id"])["payload"] == before


@pytest.mark.parametrize("hours,closed", [(1, False), (25, True)])
def test_late_analysis_link_leaves_automatic_work_but_preserves_unknown_readback(ready, tmp_path, monkeypatch, hours, closed):
    from live_contentops import neo_endpoint_executor_v1 as neo
    from live_contentops.native_neo_executor_v1 import NativeNeoExecutor, SCHEMA, DESTINATION
    store, packet, original = ready
    value = pages.register_link(store, packet, original_key=original, destination="substack_notes")
    parent = json.loads(store.get_outbox_message(original)["payload"])
    parent["at_utc"] = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    with store.get_connection() as conn:
        conn.execute("UPDATE outbox_messages SET payload=? WHERE message_id=?", (json.dumps(parent), original))
    ids = Coordinator._ids(value["link_id"], value["plan"]["plan_hash"], "substack_notes")
    coordinator = Coordinator(store=store, transport_runtime=object())
    coordinator.register_plan(value["link_id"], value["plan"])
    store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"],
        platform="substack_notes", status="UNKNOWN_WRITE")
    dispatch_before = store.get_platform_dispatch(ids["dispatch_id"])
    payload_before = store.get_outbox_message(value["link_id"])["payload"]
    result = pages.settle_late_link(store, value)
    assert bool(result) is closed
    assert store.get_platform_dispatch(ids["dispatch_id"]) == dispatch_before
    assert store.get_outbox_message(value["link_id"])["payload"] == payload_before
    recovery_ids = {r["message_id"] for r in coordinator._recovery_messages()}
    assert (ids["message_id"] not in recovery_ids) is closed
    if closed:
        assert result["status"] == "SETTLED"
        assert store.get_outbox_message(ids["message_id"])["status"] == "PLAN_POST_SETTLED"
        assert pages._resume_link(store, value, True)["status"] == "SETTLED"
        path = posts.record_run({"status": "OK", "publication": {"analysis_distribution": {"links": [
            {"link_id": value["link_id"], "destination": "substack_notes", "outcome": result}]}}}, tmp_path / "runs")
        assert json.loads(path.read_text())["analysis_links"][0]["cause"] == result["cause"]
        executor = NativeNeoExecutor(store, operation_id=value["link_id"], output_dir=tmp_path,
                                     native_invocation_id="fixture")
        request = {"action": "READBACK", "destination": "substack_notes", "request_sha256": "b" * 64,
                   "work_item_id": value["link_id"], "dispatch_attempt_identity": ids["dispatch_id"]}
        store.register_outbox_message(message_id=executor._key(request["request_sha256"], "request"),
            work_item_id=value["link_id"], destination=DESTINATION, status="NATIVE_NEO_INTERNAL",
            payload=json.dumps({"schema_version": SCHEMA, "operation_id": value["link_id"], "request": request}))
        monkeypatch.setattr(__import__("live_contentops.native_neo_executor_v1", fromlist=["bind_native_neo_coordinator"]),
            "bind_native_neo_coordinator", lambda *a, **kw: pytest.fail("settled link cannot bind browser"))
        assert neo.resume_stored_requests(store)["requests"] == []
        observed = []
        monkeypatch.setattr(coordinator, "_reconcile", lambda dispatch, intent:
            observed.append(dispatch["dispatch_id"]) or "RECONCILIATION_PENDING")
        assert coordinator.readback_existing_dispatch(ids["dispatch_id"])["publish_called"] is False
        assert observed == [ids["dispatch_id"]]


@pytest.mark.parametrize("parent", ["correct", "wrong", "missing"])
def test_x_analysis_readback_requires_the_original_card_parent(parent):
    from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff, IDENTITIES
    parent_id, parent_url = "2120015650529964275", "https://x.com/Capitalnicle/status/2120015650529964275"
    post_id, post_url = "2120015650529964299", "https://x.com/Capitalnicle/status/2120015650529964299"
    intent = {"work_item_id": "analysis-reply", "plan_analysis_link": "analysis-reply",
        "canonical_url": "https://capitalchronicle.substack.com/p/full-plan",
        "native_payload": {"text": "The original plan analysis", "full_text": "The original plan analysis",
                           "reply_to_id": parent_id, "reply_to_url": parent_url}}
    requests = []
    def observed(request):
        requests.append(request)
        result = {"request_sha256": request["request_sha256"], "status": "SUCCESS", "observed_identity": IDENTITIES["x"],
            "public_object_id": post_id, "public_object_url": post_url, "content_verified": True,
            "observed_text": intent["native_payload"]["text"]}
        if parent != "missing":
            result.update(observed_reply_parent_id=parent_id if parent == "correct" else "wrong",
                          observed_reply_parent_url=parent_url)
        return result
    result = NeoDestinationHandoff(native_executor=observed).readback(destination="x", intent=intent,
        public_object_id=post_id, public_object_url=post_url)
    assert requests[0]["entry_url"] == parent_url
    assert requests[0]["reply_parent"] == {"public_object_id": parent_id, "public_object_url": parent_url}
    assert result["verified"] is (parent == "correct")


@pytest.mark.parametrize("card", ["correct", "wrong", "missing", "rendered", "changed_number"])
def test_note_needs_its_own_visible_canonical_link_card(ready, card):
    from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff, IDENTITIES
    store, packet, original = ready
    value = pages.register_link(store, packet, original_key=original, destination="substack_notes")
    Coordinator(store=store, transport_runtime=None).register_plan(value["link_id"], value["plan"])
    row = store.list_outbox_messages(work_item_id=value["link_id"], destination="substack_notes")[0]
    intent = json.loads(row["payload"])
    assert "reply_to_id" not in intent["native_payload"]
    url = "https://substack.com/@capitalchronicle/note/c-12345"

    def observed(request):
        text = value["native_payload"]["text"]
        if card in {"rendered", "changed_number"}:
            text = text.replace(value["canonical_url"], "")
        if card == "changed_number":
            text = text.replace("55%", "56%")
        return {"request_sha256": request["request_sha256"], "status": "SUCCESS",
            "observed_identity": IDENTITIES["substack_notes"], "public_object_id": "c-12345", "public_object_url": url,
            "content_verified": True, "observed_text": text,
            "observed_link_cards": [] if card == "missing" else [{"url": value["canonical_url"] if card != "wrong" else
                "https://capitalchronicle.substack.com/p/wrong-plan", "public_object_url": url, "card_visible": True}]}

    result = NeoDestinationHandoff(native_executor=observed, store=store).readback(destination="substack_notes",
        intent=intent, public_object_id="c-12345", public_object_url=url)
    assert result["verified"] is (card in {"correct", "rendered"})


def test_parent_change_never_turns_an_analysis_comment_into_a_new_root(ready, monkeypatch):
    store, packet, original = ready
    value = pages.register_link(store, packet, original_key=original, destination="facebook_page")
    monkeypatch.setattr(pages, "_analysis_parent", lambda *a: {
        **value["parent"], "public_object_id": "wrong-parent"})
    with pytest.raises(ValueError, match="LINK_PARENT_CHANGED"):
        pages.validate_link_plan(store, value["link_id"], value["plan"])


def test_linkedin_index_keeps_all_links_with_source_bound_summary_and_no_duplicate(ready, source, tmp_path):
    store, packet, _ = ready
    run_root, _, plan, manuscript = source
    other = deepcopy(manuscript)
    other["plan_id"] = "plan_second"
    other["title"] = "The second original plan"
    second = pages.register_page(store, pages.render({**plan, "plan_id": other["plan_id"]}, other,
        run_root=run_root, output_dir=tmp_path / "second"))
    confirm(store, second["page_id"], second["plan"]["plan_hash"], "substack", "124",
            "https://capitalchronicle.substack.com/p/second-original-plan")
    value = pages.register_run_link(store, [second, packet])
    assert len(value["native_payload"]["text"]) <= 3000
    assert all(url in value["native_payload"]["text"] for url in value["canonical_urls"])
    assert pages.validate_link_plan(store, value["link_id"], value["plan"]) == value
    assert pages.register_run_link(store, [packet, second]) == value
    Coordinator(store=store, transport_runtime=None).register_plan(value["link_id"], value["plan"])
    intent = json.loads(store.list_outbox_messages(work_item_id=value["link_id"], destination="linkedin")[0]["payload"])
    from live_contentops.linkedin_official_member_api_v1 import build_linkedin_ugc_post_payload
    api_payload = build_linkedin_ugc_post_payload(intent, person_urn="urn:li:person:test")
    assert api_payload["specificContent"]["com.linkedin.ugc.ShareContent"]["shareCommentary"]["text"] == value["native_payload"]["text"]


def test_new_instagram_run_caption_and_linkedin_run_have_the_confirmed_links():
    run = {"kind": "run", "at_utc": "2026-11-10T13:00:00Z", "card_keys": ["one"],
        "analysis_distribution_version": 1, "instagram_profile_link_verified": True,
        "analysis_publications": [{"title": "EUR/USD", "summary": {"macro": "Rates drive the view."},
            "canonical_url": "https://capitalchronicle.substack.com/p/the-original-view"}]}
    run.update(cards.compose(run))
    payloads = cards.destination_payloads(run, card_id="card")
    assert "link in our profile" in payloads["instagram_business"]["text"]
    assert run["analysis_publications"][0]["canonical_url"] in payloads["linkedin"]["text"]
    assert "Macro: Rates drive the view." in payloads["linkedin"]["text"]
    assert "Full analysis:" in payloads["x"]["full_text"]
    assert "Macro: Rates drive the view." in payloads["x"]["full_text"]
    run["instagram_profile_link_verified"] = False
    caption = cards.destination_payloads(run, card_id="card")["instagram_business"]["text"]
    assert "link in our profile" not in caption
    assert "link is in the comments" in caption


@pytest.mark.parametrize("website,username,verified", [
    ("https://capitalchronicle.substack.com/", "official.capitalchronicle", True),
    ("https://capitalchronicle.substack.com/archive", "official.capitalchronicle", True),
    ("", "official.capitalchronicle", False),
    ("https://capitalchronicle.substack.com/p/one-article", "official.capitalchronicle", False),
    ("https://capitalchronicle.substack.com.evil.test/", "official.capitalchronicle", False),
    ("https://capitalchronicle.substack.com/", "someone_else", False),
])
def test_profile_caption_uses_an_official_identity_and_publication_index(monkeypatch, website, username, verified):
    from live_contentops import instagram_adapter_v6 as adapter
    monkeypatch.setattr(adapter, "_instagram_token", lambda: "fixture")
    monkeypatch.setattr(adapter, "_instagram_id", lambda: "account-fixture")
    monkeypatch.setattr(adapter, "_get_json", lambda *a: {"website": website, "username": username})
    assert adapter.readback_analysis_profile_link()["verified"] is verified


def test_scheduled_queue_binds_profile_readback_and_keeps_all_run_links(five, main_root):
    from test_plan_call_cards_cc399 import write, queue, rows
    store, folder, plans, events = five
    for index, raw in enumerate(plans):
        raw["registration_hash"] = "b" * 64
        raw["analysis_publication"] = {"plan_id": raw["plan_id"], "registration_hash": "b" * 64,
            "canonical_url": "https://capitalchronicle.substack.com/p/the-full-original-analysis-for-plan-" + str(index),
            "summary": {key: "The source-bound explanation remains conditional." for key, _ in pages.SECTIONS}}
    write(folder, plans, events)
    calls = []
    def profile():
        calls.append(True)
        return {"verified": True, "cause": None}
    queue(store, folder, main_root, instagram_profile_reader=profile)
    assert calls == [True]
    run = next(r for r in rows(store) if r["kind"] == "run")
    assert run["instagram_profile_link_verified"] is True
    payloads = cards.destination_payloads(run, card_id="run-card")
    assert len(payloads["threads"]["reply_texts"]) == len(plans)
    assert all(len(text) <= 500 for text in [payloads["threads"]["text"], *payloads["threads"]["reply_texts"]])
    for payload in payloads.values():
        assert all(raw["analysis_publication"]["canonical_url"] in payload["full_text"] for raw in plans)


def test_new_discord_analysis_inherits_confirmed_card_channel_route(ready):
    store, packet, original = ready
    row = store.get_outbox_message(original)
    value = json.loads(row["payload"])
    value["discord_delivery"] = "channel"
    # This fixture declares the delivery route before creating its link.
    with store.get_connection() as connection:
        connection.execute("UPDATE outbox_messages SET payload=? WHERE message_id=?",
                           (json.dumps(value), original))
    link = pages.register_link(store, packet, original_key=original, destination="discord")
    assert link["native_payload"]["discord_channel_post"] is True
    assert "discord_thread_parent_id" not in link["native_payload"]
    assert "reply_to_id" not in link["native_payload"]
    assert pages.validate_link_plan(store, link["link_id"], link["plan"]) == link


def test_retired_analysis_link_is_not_published_again(ready, monkeypatch):
    store, packet, original = ready
    link = pages.register_link(store, packet, original_key=original, destination="discord")
    Coordinator(store=store, transport_runtime=None).register_plan(link["link_id"], link["plan"])
    ids = Coordinator._ids(link["link_id"], link["plan"]["plan_hash"], "discord")
    store.set_outbox_status(ids["message_id"], "DERIVATIVE_EXPIRED_STALE_NO_WRITE")
    monkeypatch.setattr(pages, "publish_link", lambda *a: pytest.fail("retired link was republished"))
    assert pages._resume_link(store, link, True)["status"] == "DERIVATIVE_EXPIRED_STALE_NO_WRITE"


def test_confirmed_linkedin_run_does_not_get_a_duplicate_analysis_index(ready):
    store, packet, _ = ready
    key = "confirmed-run"
    url = pages.page_status(store, packet)["canonical_url"]
    store.create_work_item(story_id=key, work_item_id=key, title="Run", target_surface="MULTI_PLATFORM")
    store.register_outbox_message(message_id=key, work_item_id=key, destination=posts.DESTINATION,
        payload=json.dumps({"kind": "run", "analysis_publications": [{"canonical_url": url}]}), status="PUBLISHED")
    confirm(store, key, sha256(("plan-status-post:" + key).encode()).hexdigest(), "linkedin", "run-li",
            "https://www.linkedin.com/feed/update/urn:li:share:123")
    result = pages.distribute_links(store, publish=False)
    assert next(r for r in result["links"] if r["destination"] == "linkedin")["state"] == "CONFIRMED_IN_RUN_POST"
    assert not any(json.loads(r["payload"]).get("kind") == "run"
                   for r in store.list_outbox_messages(destination=pages.DESTINATION))


def test_minute_record_keeps_exact_analysis_link_and_first_transport_failure(tmp_path):
    result = {"status": "OK", "publication": {"status": "OK", "analysis_distribution": {"links": [
        {"link_id": "exact-index", "destination": "linkedin", "outcome": {
            "distribution_status": "BLOCKED_SAFE_RECOVERY_BACKLOG_REMAINS", "recovery_preflight": {
                "per_destination": {"linkedin": {"status": "DESTINATION_FAILED_ET_DAY_SKIP",
                    "first_failure": {"safe_error_classification": "TRANSPORT_TLS_HANDSHAKE_UNAVAILABLE"}}}}}}]}}}
    path = posts.record_run(result, tmp_path)
    saved = json.loads(path.read_text(encoding="utf-8"))["analysis_links"][0]
    assert saved["link_id"] == "exact-index"
    assert saved["destination_causes"]["linkedin"] == "DESTINATION_FAILED_ET_DAY_SKIP"
    assert saved["first_failures"]["linkedin"]["safe_error_classification"] == "TRANSPORT_TLS_HANDSHAKE_UNAVAILABLE"


def test_link_resume_returns_the_already_queued_native_request(ready, monkeypatch):
    from live_contentops import native_neo_executor_v1 as native
    from types import SimpleNamespace
    store, packet, original = ready
    value = pages.register_link(store, packet, original_key=original, destination="substack_notes")
    pending = [{"request": {"action": "PUBLISH", "request_sha256": "frozen-request"}}]
    coordinator = SimpleNamespace(publish_plan=lambda *a: {"distribution_status": "RECOVERY_REQUIRED"})
    executor = SimpleNamespace(pending=lambda: pending)
    monkeypatch.setattr(native, "bind_native_neo_coordinator", lambda *a, **kw: (coordinator, executor))
    result = pages.continue_link(store, value, invocation_id="test-native-turn")
    assert result["pending_requests"] == pending
    assert result["distribution_status"] == "RECOVERY_REQUIRED"


def test_note_host_case_rendering_requires_the_exact_objects_observed_link():
    from live_contentops.neo_destination_handoff_v1 import _note_rendered_text
    public = "https://substack.com/@capitalchronicle/note/c-12345"
    links = [{"text": "investing.com", "url": "https://investing.com/", "public_object_url": public}]
    assert _note_rendered_text("Investing.com: 0.3%", "unused", links, public) == "investing.com: 0.3%"
    assert _note_rendered_text("Investing.com: 0.3%", "unused", links, "other-object") == "Investing.com: 0.3%"
