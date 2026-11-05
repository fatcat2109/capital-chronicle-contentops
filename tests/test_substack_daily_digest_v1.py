"""CC-143 isolated checks. No browser, provider or production writes."""
import json
from datetime import datetime, timezone
from hashlib import sha256

import pytest

from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.published_content_v1 import canonical, append_record, SCHEMA
from live_contentops.event_article_guard_v1 import PUBLIC_NOTICE
from live_contentops.substack_daily_digest_v1 import (
    prepare_daily_digest, packets, digest_status, validate_digest_plan, delivery_mode_for_plan,
    delivery_policy, WEB_ONLY, EMAIL_DIGEST, continue_daily_digest,
)
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff
from test_publication_coordinator_v1 import _plan, FixtureTransport


def clock(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def row(identity="one", published="2026-11-03T03:00:00Z", recorded=None):
    value = dict(schema_version=SCHEMA, content_id=identity, type="ARTICLE",
        title="Public title " + identity, standfirst="An attributed public report.",
        published_at_utc=published, recorded_at_utc=recorded or published,
        outlets=[{"name":"substack", "url":"https://capitalchronicle.substack.com/p/"+identity}],
        event_id=None, conditional_calls=[], rights_class="CC_OWN_ANALYSIS", visibility="public",
        disclaimer=PUBLIC_NOTICE, conflicts_notice=None)
    value["content_sha256"] = sha256(canonical(value)).hexdigest()
    return value


def setup(tmp_path, rows=()):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    feed = tmp_path / "published.jsonl"
    feed.touch()
    for r in rows:
        append_record(feed, r)
    return store, feed


def prepared(store, feed, now="2026-11-03T12:00:00Z"):
    return prepare_daily_digest(store, feed, now=clock(now))


def confirm(store, packet, object_id="123", email=True):
    ids = DurablePublicationCoordinator._ids(packet["digest_id"], packet["plan"]["plan_hash"], "substack")
    store.register_outbox_message(message_id=ids["message_id"], work_item_id=packet["digest_id"],
        destination="substack", payload="{}", status="DISPATCH_CONFIRMED")
    store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"],
        platform="substack", status="DISPATCH_CONFIRMED", public_object_id=object_id,
        public_object_url="https://capitalchronicle.substack.com/p/digest-"+object_id)
    store.register_reconciliation(reconciliation_id=ids["reconciliation_id"],
        work_item_id=packet["digest_id"], status="RECONCILED_CONFIRMED")
    if email:
        from live_contentops.native_neo_executor_v1 import NativeNeoExecutor, NativeNeoInputRequired, TOOL
        executor = NativeNeoExecutor(store, operation_id=packet["digest_id"], output_dir=store.db_path.parent / "tools", native_invocation_id="controlled-email-test")
        adapter = NeoDestinationHandoff(native_executor=executor)
        value = {"work_item_id":packet["digest_id"], "daily_digest":packet["digest_id"],
                 "native_payload":packet["native_payload"], "destination_plan":{}}
        url = "https://capitalchronicle.substack.com/p/digest-"+object_id
        with pytest.raises(NativeNeoInputRequired) as pending:
            adapter.readback(destination="substack", intent=value, public_object_id=object_id, public_object_url=url)
        request = pending.value.request
        request_hash = request["request"]["request_sha256"]
        executor.begin(request_hash)
        executor.submit(request_hash, {"tool_request_sha256":request["tool_request_sha256"],
            "tool_observation":{"tool_name":TOOL, "native_invocation_id":"controlled-email-test",
                "surface":"CODEX_DESKTOP_CONVERSATION", "observation_source":"CONTROLLED_TEST_NOT_BROWSER",
                "observed_at_utc":datetime.now(timezone.utc).isoformat()},
            "result":{"request_sha256":request_hash, "public_object_id":object_id,
                "public_object_url":url, "observed_identity":"capitalchronicle.substack.com",
                "email_delivery_confirmed":True, "email_delivery_evidence_ref":"CONTROLLED_TEST_NOT_BROWSER"}})


def test_1900_cutoff_and_late_articles(tmp_path):
    store, feed = setup(tmp_path, [row(), row("later", "2026-11-03T12:00:01Z")])
    assert prepared(store, feed, "2026-11-03T11:59:59Z")["state"] == "NO_CONFIRMED_ARTICLES"
    first = prepared(store, feed)["packet"]
    assert [a["content_id"] for a in first["articles"]] == ["one"]
    # 4 Nov: the card names the day's pieces instead of an empty "N articles" card.
    card = first["media_assets"][0]
    assert card["visual_type"] == "DIGEST_TITLES_CARD"
    assert card["digest_card_binding"]["titles"] == ["Public title one"]
    assert card["digest_card_binding"]["accepted_evidence_sha256"] == first["plan"]["accepted_evidence_sha256"]
    assert first["cutoff_utc"] == "2026-11-03T12:00:00+00:00"
    assert first["native_payload"]["body_markdown"].count("/p/one") == 1
    confirm(store, first)
    second = prepared(store, feed, "2026-11-04T12:00:00Z")["packet"]
    assert [a["content_id"] for a in second["articles"]] == ["later"]


@pytest.mark.parametrize("defect", [None, "subtitle", "summary", "link"])
def test_frozen_long_subtitle_and_inline_card_reach_digest_consumer(tmp_path, monkeypatch, defect):
    import live_contentops.substack_daily_digest_v1 as digest
    article = row()
    article["title"] = "An already published article with a long title " * 5
    article["content_sha256"] = sha256(canonical({k:v for k,v in article.items() if k != "content_sha256"})).hexdigest()
    store, feed = setup(tmp_path, [article])
    render_subtitle = digest.substack_subtitle
    # Reproduce the 4 November packet issued before the editor limit was known.
    monkeypatch.setattr(digest, "substack_subtitle", lambda text: text)
    packet = prepared(store, feed)["packet"]
    frozen = store.get_outbox_message("substack-digest-" + packet["digest_id"])["payload"]
    monkeypatch.setattr(digest, "substack_subtitle", render_subtitle)
    assert len(packet["native_payload"]["subtitle"]) > 200
    assert len(render_subtitle(packet["native_payload"]["subtitle"])) <= 200
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=None)
    coordinator.register_plan(packet["digest_id"], packet["plan"])
    message = next(r for r in store.list_outbox_messages() if r["destination"] == "substack")
    intent = json.loads(message["payload"])
    title = packet["articles"][0]["title"]
    subtitle = render_subtitle(packet["native_payload"]["subtitle"])
    caption = packet["media_assets"][0]["caption"]
    summary = packet["articles"][0]["standfirst"]
    class Observation:
        def __init__(self):
            self.store = store
        def __call__(self, request):
            return {"request_sha256":request["request_sha256"], "observed_identity":"capitalchronicle.substack.com",
                "public_object_id":"123", "public_object_url":"https://capitalchronicle.substack.com/p/digest",
                "content_verified":True, "observed_text":" ".join([packet["native_payload"]["title"],
                    "Wrong subtitle" if defect == "subtitle" else subtitle, title, caption,
                    "Wrong summary" if defect == "summary" else summary, PUBLIC_NOTICE]),
                "observed_links":[{"text":title, "url":"https://capitalchronicle.substack.com/p/wrong"
                    if defect == "link" else packet["articles"][0]["url"]}],
                "observed_media_sha256":[a["sha256"] for a in packet["media_assets"]]}
    result = NeoDestinationHandoff(native_executor=Observation()).readback(destination="substack", intent=intent,
        public_object_id="123", public_object_url="https://capitalchronicle.substack.com/p/digest")
    assert result["verified"] is (defect is None)
    assert store.get_outbox_message("substack-digest-" + packet["digest_id"])["payload"] == frozen
    # New packets fit the field and retain each complete body title.
    fresh_store, fresh_feed = setup(tmp_path / "new", [article])
    fresh = prepared(fresh_store, fresh_feed)["packet"]
    assert len(fresh["native_payload"]["subtitle"]) <= 200
    assert title in fresh["native_payload"]["body_markdown"]


def test_restart_and_missing_code_reuse_exact_unsent_digest(tmp_path):
    store, feed = setup(tmp_path, [row()])
    first = prepared(store, feed)["packet"]
    append_record(feed, row("next", "2026-11-04T03:00:00Z"))
    restarted = ContentOpsDurableStore(store.db_path, auto_migrate=False)
    later = prepared(restarted, feed, "2026-11-05T12:00:00Z")
    assert later["packet"] == first and len(packets(restarted)) == 1
    assert not later["confirmed"] and not later["public_write_performed"]
    confirm(store, first)
    next_packet = prepared(store, feed, "2026-11-05T12:00:00Z")["packet"]
    assert [a["content_id"] for a in next_packet["articles"]] == ["next"]


def test_public_page_confirmation_is_not_a_new_digest(tmp_path):
    store, feed = setup(tmp_path, [row()])
    first = prepared(store, feed)["packet"]
    confirm(store, first, email=False)
    status = digest_status(store, first)
    assert status["web_confirmed"] and not status["email_confirmed"] and not status["confirmed"]
    assert status["state"] == "WEB_CONFIRMED_EMAIL_READBACK_REQUIRED"
    assert prepared(store, feed)["digest_id"] == first["digest_id"]
    assert len(packets(store)) == 1


def test_feed_rights_and_seal_fail_closed_and_no_empty_digest(tmp_path):
    store, feed = setup(tmp_path)
    assert prepared(store, feed)["state"] == "NO_CONFIRMED_ARTICLES"
    assert packets(store) == []
    bad = row()
    bad["rights_class"] = "PRIVATE"
    feed.write_text(json.dumps(bad)+"\n")
    with pytest.raises(ValueError, match="RIGHTS"):
        prepared(store, feed)
    assert packets(store) == []


def test_future_publication_and_recording_not_included(tmp_path):
    store, feed = setup(tmp_path, [row("future", "2026-11-04T12:00:00Z"),
        row("late", recorded="2026-11-04T12:00:00Z")])
    assert prepared(store, feed)["state"] == "NO_CONFIRMED_ARTICLES"


def test_article_mode_forced_web_and_digest_requires_frozen_packet(tmp_path):
    store, feed = setup(tmp_path, [row()])
    p = _plan("substack")
    p["destinations"][0]["substack_delivery_mode"] = EMAIL_DIGEST
    store.create_work_item(work_item_id="work", story_id="story", title="Test", target_surface="test")
    c = DurablePublicationCoordinator(store=store, transport_runtime=None)
    c.register_plan("work", p)
    message = next(r for r in store.list_outbox_messages() if r["destination"] == "substack")
    assert json.loads(message["payload"])["destination_plan"]["substack_delivery_mode"] == WEB_ONLY
    assert c.register_plan("work", p)["outbox_count"] == 1
    frozen = prepared(store, feed)["packet"]
    assert delivery_mode_for_plan(store, frozen["digest_id"], frozen["plan"]) == EMAIL_DIGEST
    forged = {**frozen["plan"], "daily_digest": "other"}
    with pytest.raises(ValueError, match="FROZEN"):
        c.register_plan("other", forged)


def test_issued_historical_intent_unchanged(tmp_path):
    store, feed = setup(tmp_path)
    store.create_work_item(work_item_id="work", story_id="story", title="Test", target_surface="test")
    p = _plan("substack")
    c = DurablePublicationCoordinator(store=store, transport_runtime=None)
    c.register_plan("work", p)
    ids = c._ids("work", p["plan_hash"], "substack")
    current = store.get_outbox_message(ids["message_id"])
    # Simulate the exact historical pre-mode intent in a separate disposable store.
    old = json.loads(current["payload"])
    old["destination_plan"].pop("substack_delivery_mode")
    other = ContentOpsDurableStore(tmp_path / "old.sqlite3")
    other.create_work_item(work_item_id="work", story_id="story", title="Test", target_surface="test")
    other.register_outbox_message(message_id=ids["message_id"], work_item_id="work",
        destination="substack", payload=json.dumps(old, sort_keys=True, separators=(",", ":")), status="READY")
    before = other.get_outbox_message(ids["message_id"])["payload"]
    DurablePublicationCoordinator(store=other, transport_runtime=None).register_plan("work", p)
    assert other.get_outbox_message(ids["message_id"])["payload"] == before


def test_digest_uses_only_substack_through_existing_coordinator(tmp_path, monkeypatch):
    monkeypatch.setattr("live_contentops.llm_operator_control_v1.assert_llm_operator_execution_enabled", lambda: None)
    store, feed = setup(tmp_path, [row()])
    packet = prepared(store, feed)["packet"]
    control = store.get_operating_control()
    store.update_operating_control(operating_mode="AUTONOMOUS_DEFAULT", expected_state_version=control["state_version"], control_source="TEST")
    runtime = FixtureTransport()
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=runtime,
        readiness_provider=lambda _: {"readiness_state":"READY_AUTHENTICATED"})
    result = coordinator.publish_plan(packet["digest_id"], packet["plan"])
    assert runtime.publish_calls == ["substack"]
    assert result["canonical_article_real_published"]
    coordinator.publish_plan(packet["digest_id"], packet["plan"])
    assert runtime.publish_calls == ["substack"]
    status = digest_status(store, packet)
    assert status["web_confirmed"] and not status["email_confirmed"]


@pytest.mark.parametrize("mode", [WEB_ONLY, EMAIL_DIGEST])
@pytest.mark.parametrize("matches", [True, False])
def test_success_requires_observed_delivery_controls(mode, matches):
    value = {"work_item_id":"work", "payload":"Reviewed exact copy.",
             "destination_plan":{"payload_hash":"hash", "substack_delivery_mode":mode}}
    auth = {"schema_version":"contentops.canonical_machine_authorization.v1", "operating_mode":"AUTONOMOUS_DEFAULT",
            "destination":"substack", "dispatch_attempt_identity":"dispatch", "work_item_id":"work", "payload_hash":"hash"}
    def executor(request):
        assert request["substack_delivery_policy"]["mode"] == mode
        return {"request_sha256":request["request_sha256"], "observed_identity":"capitalchronicle.substack.com",
                "status":"SUCCESS", "public_object_id":"123", "delivery_observation":{
                    "email_send_enabled": (mode == EMAIL_DIGEST) if matches else (mode != EMAIL_DIGEST),
                    "web_publish_enabled":True, "evidence_ref":"CONTROLLED_TEST_NOT_BROWSER"}}
    result = NeoDestinationHandoff(native_executor=executor).publish(destination="substack", intent=value, authorization_context=auth)
    assert result["status"] == ("SUCCESS" if matches else "UNKNOWN_WRITE")


def test_digest_uses_native_identity_request_not_another_publisher(tmp_path, monkeypatch):
    monkeypatch.setattr("live_contentops.native_desktop_publication_v1.live_publication_policy", lambda _: None)
    monkeypatch.setattr("live_contentops.llm_operator_control_v1.assert_llm_operator_execution_enabled", lambda: None)
    store, feed = setup(tmp_path, [row()])
    packet = prepared(store, feed)["packet"]
    control = store.get_operating_control()
    store.update_operating_control(operating_mode="AUTONOMOUS_DEFAULT", expected_state_version=control["state_version"], control_source="TEST")
    result = continue_daily_digest(store, packet, output_dir=tmp_path / "tools", invocation_id="controlled-test", rollout={"store_path":str(store.db_path)})
    assert result["state"] == "NATIVE_NEO_TOOL_PENDING"
    assert result["native_tool_request"]["request"]["action"] == "VERIFY_IDENTITY"
    assert store.list_platform_dispatches() == []


def test_full_native_digest_restart_loop_and_email_readback(tmp_path, monkeypatch):
    from live_contentops.native_neo_executor_v1 import TOOL
    monkeypatch.setattr("live_contentops.native_desktop_publication_v1.live_publication_policy", lambda _: None)
    monkeypatch.setattr("live_contentops.llm_operator_control_v1.assert_llm_operator_execution_enabled", lambda: None)
    store, feed = setup(tmp_path, [row()])
    packet = prepared(store, feed)["packet"]
    control = store.get_operating_control()
    store.update_operating_control(operating_mode="AUTONOMOUS_DEFAULT", expected_state_version=control["state_version"], control_source="TEST")
    args = dict(output_dir=tmp_path / "tools", invocation_id="controlled-native-loop", rollout={"store_path":str(store.db_path)})
    seen = []
    public_url = "https://capitalchronicle.substack.com/p/controlled-digest"
    for _ in range(8):
        result = continue_daily_digest(store, packet, **args)
        if result.get("confirmed"):
            break
        pending = result.get("native_tool_request")
        if not pending:
            pending = next(iter(result.get("pending_requests", [])), None)
        assert pending, result
        request = pending["request"]
        request_hash = request["request_sha256"]
        action = request["action"]
        seen.append(action)
        begun = continue_daily_digest(store, packet, command="begin", request_hash=request_hash, **args)
        if action == "PUBLISH":
            assert begun["substack_publish_routine"]["delivery"]["email_send_enabled"] is True
            assert begun["request"]["content_binding"]["media_manifest"][0]["sha256"] == packet["media_assets"][0]["sha256"]
        returned = {"request_sha256":request_hash, "observed_identity":"capitalchronicle.substack.com", "status":"SUCCESS"}
        if action == "VERIFY_IDENTITY":
            returned["authenticated"] = True
        else:
            returned.update(public_object_id="123", public_object_url=public_url)
            if action == "PUBLISH":
                returned["delivery_observation"] = {"email_send_enabled":True, "web_publish_enabled":True,
                    "evidence_ref":"CONTROLLED_TEST_NOT_BROWSER"}
            else:
                returned.update(content_verified=True,
                    observed_text=" ".join(request["content_binding"]["expected_text_segments"]),
                    observed_links=[{"text": a["title"], "url": a["url"]} for a in packet["articles"]],
                    observed_media_sha256=[a["sha256"] for a in packet["media_assets"]],
                    public_image_urls=["https://substack-post-media.s3.amazonaws.com/public/images/controlled-digest.png"],
                    email_delivery_confirmed=True, email_delivery_evidence_ref="CONTROLLED_TEST_NOT_BROWSER")
        response = {"tool_request_sha256":pending["tool_request_sha256"],
            "tool_observation":{"tool_name":TOOL, "native_invocation_id":"controlled-native-loop",
                "surface":"CODEX_DESKTOP_CONVERSATION", "observation_source":"CONTROLLED_TEST_NOT_BROWSER",
                "observed_at_utc":datetime.now(timezone.utc).isoformat()}, "result":returned}
        continue_daily_digest(store, packet, command="submit", request_hash=request_hash, response=response, **args)
    else:
        pytest.fail("native digest did not complete in the bounded controlled loop")
    assert seen == ["VERIFY_IDENTITY", "PUBLISH", "READBACK"]
    assert result["web_confirmed"] and result["email_confirmed"] and result["confirmed"]
    assert len(store.list_platform_dispatches()) == 1
    assert continue_daily_digest(store, packet, **args)["confirmed"]
    assert len(store.list_platform_dispatches()) == 1


@pytest.mark.parametrize("link_state", ["exact", "duplicate", "wrong", "missing"])
def test_digest_paragraph_render_checks_exact_links_once(tmp_path, link_state):
    store, feed = setup(tmp_path, [row()])
    packet = prepared(store, feed)["packet"]
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=None)
    coordinator.register_plan(packet["digest_id"], packet["plan"])
    message = next(r for r in store.list_outbox_messages() if r["destination"] == "substack")
    intent = json.loads(message["payload"])
    observed = [{"text": a["title"], "url": a["url"]} for a in packet["articles"]]
    if link_state == "duplicate":
        observed += observed
    elif link_state == "wrong":
        observed[0]["url"] = "https://capitalchronicle.substack.com/p/wrong"
    elif link_state == "missing":
        observed = []
    class Observation:
        def __init__(self):
            self.store = store
        def __call__(self, request):
            return {"request_sha256": request["request_sha256"], "observed_identity": "capitalchronicle.substack.com",
                "public_object_id": "123", "public_object_url": "https://capitalchronicle.substack.com/p/digest",
                "content_verified": True, "observed_text": packet["native_payload"]["title"] + " "
                    + packet["native_payload"]["subtitle"] + " " + packet["articles"][0]["title"] + " "
                    + packet["articles"][0]["standfirst"] + " " + PUBLIC_NOTICE,
                "observed_links": observed, "observed_media_sha256": [a["sha256"] for a in packet["media_assets"]]}
    result = NeoDestinationHandoff(native_executor=Observation()).readback(destination="substack", intent=intent,
        public_object_id="123", public_object_url="https://capitalchronicle.substack.com/p/digest")
    assert result["verified"] is (link_state == "exact")


def test_existing_host_tick_prepares_due_digest_once_without_browser_or_cycle(tmp_path, monkeypatch):
    from test_daily_app_supervisor_v1 import _supervisor, SCHEDULED_EDITORIAL_OWNER_NATIVE_DESKTOP
    import live_contentops.published_content_v1 as published
    supervisor, calls = _supervisor(tmp_path, scheduled_editorial_owner=SCHEDULED_EDITORIAL_OWNER_NATIVE_DESKTOP)
    store = supervisor._store
    control = store.get_operating_control()
    if control["operating_mode"] != "AUTONOMOUS_DEFAULT":
        store.update_operating_control(operating_mode="AUTONOMOUS_DEFAULT", expected_state_version=control["state_version"], control_source="TEST")
    feed = tmp_path / "feed.jsonl"
    append_record(feed, row())
    monkeypatch.setattr(published, "PRODUCTION_STORE", store.db_path)
    monkeypatch.setattr(published, "DEFAULT_FEED", feed)
    supervisor._intake_housekeeping_override = lambda *args, **kwargs: {}
    early = supervisor.tick(now=clock("2026-11-03T11:59:59Z"))
    assert early["daily_email_digest"]["state"] == "NO_CONFIRMED_ARTICLES"
    due = supervisor.tick(now=clock("2026-11-03T12:00:00Z"))
    assert due["daily_email_digest"]["state"] == "PREPARED_NATIVE_INPUT_REQUIRED"
    later = supervisor.tick(now=clock("2026-11-03T12:01:00Z"))
    assert later["daily_email_digest"]["digest_id"] == due["daily_email_digest"]["digest_id"]
    assert due["daily_email_digest"]["native_continuation"]["command"] == "digest-resume"
    assert len(packets(store)) == 1 and store.list_platform_dispatches() == []
    assert calls == []


def test_publisher_entry_consumes_due_digest_and_reuses_packet(tmp_path, monkeypatch, capsys):
    from test_native_newsroom_owner_operation_v1 import entry
    import live_contentops.published_content_v1 as published
    module = entry()
    store, feed = setup(tmp_path, [row()])
    control = store.get_operating_control()
    store.update_operating_control(operating_mode="AUTONOMOUS_DEFAULT",
        expected_state_version=control["state_version"], control_source="TEST")
    monkeypatch.setattr(published, "PRODUCTION_STORE", store.db_path)
    monkeypatch.setattr(published, "DEFAULT_FEED", feed)
    from live_contentops.substack_daily_digest_v1 import production_digest_housekeeping
    monkeypatch.setattr("live_contentops.substack_daily_digest_v1.production_digest_housekeeping",
        lambda store: production_digest_housekeeping(store, now=clock("2026-11-03T12:00:00Z")))
    rollout = tmp_path / "rollout.json"
    rollout.write_text(json.dumps({"store_path": str(store.db_path)}))
    binding = tmp_path / "binding.json"
    binding.write_text("{}")
    monkeypatch.setattr(module, "operation", lambda *a, **kw: {"article": "unchanged"})
    args = ["publication-resume", "--binding", str(binding), "--rollout", str(rollout)]
    assert module.main(args) == 0
    first = json.loads(capsys.readouterr().out)
    digest = first["daily_email_digest"]
    assert digest["native_continuation"]["command"] == "digest-resume"
    assert digest["state"] == "PREPARED_NATIVE_INPUT_REQUIRED"
    assert first["article"] == "unchanged"
    assert module.main(args) == 0
    again = json.loads(capsys.readouterr().out)
    assert again["daily_email_digest"]["digest_id"] == digest["digest_id"]
    assert len(packets(store)) == 1
    packet = packets(store)[0]
    assert packet["articles"][0]["url"] in packet["native_payload"]["body_markdown"]


def test_digest_uses_live_recovery_scope_with_prior_unknown_social(tmp_path, monkeypatch):
    monkeypatch.setattr("live_contentops.native_desktop_publication_v1.live_publication_policy", lambda _: None)
    monkeypatch.setattr("live_contentops.llm_operator_control_v1.assert_llm_operator_execution_enabled", lambda: None)
    store, feed = setup(tmp_path, [row()])
    control = store.get_operating_control()
    store.update_operating_control(operating_mode="AUTONOMOUS_DEFAULT",
        expected_state_version=control["state_version"], control_source="TEST")
    store.create_work_item(story_id="prior", work_item_id="prior", title="Prior article", target_surface="MULTI_PLATFORM")

    class PriorSocialGap(FixtureTransport):
        def publish(self, *, destination, intent, authorization_context):
            if destination == "linkedin":
                raise TimeoutError("CONTROLLED lost prior social return")
            return super().publish(destination=destination, intent=intent, authorization_context=authorization_context)

        def readback(self, *, destination, public_object_id, public_object_url, intent):
            if destination == "linkedin":
                return {"status": "AMBIGUOUS", "verified": False}
            return super().readback(destination=destination, public_object_id=public_object_id,
                public_object_url=public_object_url, intent=intent)

    old_plan = _plan("substack", "linkedin")
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=PriorSocialGap(),
        readiness_provider=lambda _: {"readiness_state": "READY_AUTHENTICATED"})
    assert coordinator.publish_plan("prior", old_plan)["canonical_article_real_published"]
    old_dispatch = coordinator._ids("prior", old_plan["plan_hash"], "linkedin")["dispatch_id"]
    assert store.get_platform_dispatch(old_dispatch)["status"] == "UNKNOWN_WRITE"
    packet = prepared(store, feed)["packet"]
    result = continue_daily_digest(store, packet, output_dir=tmp_path / "tools", invocation_id="controlled-digest",
        rollout={"store_path": str(store.db_path)})
    assert result["state"] == "NATIVE_NEO_TOOL_PENDING"
    request = result["native_tool_request"]["request"]
    assert request["action"] == "VERIFY_IDENTITY" and request["destination"] == "substack"
    assert store.get_platform_dispatch(old_dispatch)["status"] == "UNKNOWN_WRITE"
