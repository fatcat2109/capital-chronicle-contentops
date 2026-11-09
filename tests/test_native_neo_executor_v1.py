"""Controlled protocol checks only; these fixtures do not prove a browser action."""
import json
from datetime import datetime, timezone, timedelta

import pytest

from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_neo_executor_v1 import (
    NativeNeoExecutor, NativeNeoInputRequired, PENDING, TOOL, bind_native_neo_coordinator,
)
from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff
from live_contentops.publication_coordinator_v1 import (
    DurablePublicationCoordinator, CanonicalDestinationTransportRuntimeV1,
    DISPATCH_CONFIRMED, RECONCILED_CONFIRMED, UNKNOWN_WRITE,
)


def setup(tmp_path, allow_publish=False):
    store = ContentOpsDurableStore(tmp_path / "state.sqlite3")
    store.create_work_item(story_id="story", work_item_id="work", title="test", target_surface="test")
    executor = NativeNeoExecutor(store, operation_id="same-op", output_dir=tmp_path / "requests",
                                 native_invocation_id="controlled-test", allow_publish=allow_publish)
    return store, executor


def intent(destination="substack", **extra):
    return {"work_item_id": "work", "plan_hash": "plan", "package_identity": "pkg",
            "canonical_url": "https://capitalchronicle.substack.com/p/test",
            "payload": "Exact supported proposition.",
            "destination_plan": {"payload_hash": "hash", "surface": {
                "substack": "SUBSTACK_ARTICLE", "x": "X_POST", "youtube": "YOUTUBE_COMMUNITY_POST"}[destination]},
            **extra}


def response(executor, packet, result):
    request = packet["request"]
    executor.begin(request["request_sha256"])
    return {"tool_request_sha256": packet["tool_request_sha256"],
            "tool_observation": {"tool_name": TOOL, "native_invocation_id": "controlled-test",
                "surface": "CODEX_NATIVE_SUBAGENT", "observation_source": "CONTROLLED_TEST_NOT_BROWSER_PROOF",
                "observed_at_utc": datetime.now(timezone.utc).isoformat()},
            "result": {"request_sha256": request["request_sha256"], **result}}


def pending_readback(adapter, destination="substack", value=None):
    ids = {"substack": "123", "x": "123", "youtube": "Ugexample"}
    urls = {"substack": "https://capitalchronicle.substack.com/p/test", "x": "https://x.com/Capitalnicle/status/123",
            "youtube": "https://www.youtube.com/post/Ugexample"}
    with pytest.raises(NativeNeoInputRequired) as pending:
        adapter.readback(destination=destination, intent=value or intent(destination),
                         public_object_id=ids[destination], public_object_url=urls[destination])
    return pending.value.request, ids[destination], urls[destination]


@pytest.mark.parametrize("fault", [None, "number", "minus", "missing_item", "order"])
def test_substack_rendered_list_readback_preserves_values_and_order(tmp_path, fault):
    _, executor = setup(tmp_path)
    adapter = NeoDestinationHandoff(native_executor=executor)
    value = intent(native_payload={"title": "Weekend wrap", "body_markdown":
        "Markets at the reopen.\n\n- **Oil:** +2.5%.\n- **Stocks:** -0.8%.\n\nWatch CPI."})
    packet, object_id, url = pending_readback(adapter, value=value)
    items = ["Oil: +2.5%.", "Stocks: -0.8%."]
    if fault == "number":
        items[0] = "Oil: +5.2%."
    if fault == "minus":
        items[1] = "Stocks: 0.8%."
    if fault == "missing_item":
        items.pop()
    if fault == "order":
        items.reverse()
    observed = response(executor, packet, {"observed_identity": "capitalchronicle.substack.com",
        "public_object_id": object_id, "public_object_url": url, "content_verified": True,
        "observed_text": "Weekend wrap\nMarkets at the reopen.\n" + "\n".join(items) + "\nWatch CPI."})
    executor.submit(packet["request"]["request_sha256"], observed)
    result = adapter.readback(destination="substack", intent=value,
        public_object_id=object_id, public_object_url=url)
    assert result["verified"] is (fault is None)
    assert result["write_exists"] is True


def test_failed_readonly_identity_can_refresh_in_same_epoch_without_publish(tmp_path):
    store, executor = setup(tmp_path)
    with pytest.raises(NativeNeoInputRequired) as first:
        executor.readiness("SUBSTACK_ARTICLE")
    first_packet = first.value.request
    executor.submit(first_packet["request"]["request_sha256"], response(executor, first_packet,
        {"authenticated": False, "observed_identity": "capitalchronicle.substack.com"}))
    with pytest.raises(NativeNeoInputRequired) as second:
        executor.readiness("SUBSTACK_ARTICLE")
    second_packet = second.value.request
    assert second_packet["request"]["request_sha256"] != first_packet["request"]["request_sha256"]
    executor.submit(second_packet["request"]["request_sha256"], response(executor, second_packet,
        {"authenticated": True, "observed_identity": "capitalchronicle.substack.com"}))
    assert executor.readiness("SUBSTACK_ARTICLE")["authenticated"] is True
    assert executor._get(first_packet["request"]["request_sha256"], "response")["result"]["authenticated"] is False
    assert store.list_platform_dispatches() == []


def test_fresh_public_readback_survives_derived_receipt_hash_only(tmp_path):
    from copy import deepcopy
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    store, executor = setup(tmp_path)
    request = {"action": "READBACK", "work_item_id": "work", "destination": "x", "expected_identity": "@Capitalnicle",
        "content_binding": {"media_manifest": [{"sha256": "a" * 64}],
            "artifact_manifest": [{"path": "/approved/delivery_media_manifest_v1.json", "sha256": "b" * 64},
                                  {"path": "/approved/run_context_v1.json", "sha256": "c" * 64}]}}
    request["request_sha256"] = sha256_of(request)
    with pytest.raises(NativeNeoInputRequired) as pending:
        executor(request)
    executor.submit(request["request_sha256"], response(executor, pending.value.request,
        {"status": "SUCCESS", "observed_identity": "@Capitalnicle", "public_object_id": "123",
         "public_object_url": "https://x.com/Capitalnicle/status/123", "content_verified": True,
         "observed_media_sha256": ["a" * 64]}))
    current = deepcopy(request)
    current["content_binding"]["artifact_manifest"][0]["sha256"] = "d" * 64
    assert executor.fresh_readback_request(current) == request
    assert request["content_binding"]["artifact_manifest"][0]["sha256"] == "b" * 64
    current["content_binding"]["media_manifest"][0]["sha256"] = "e" * 64
    assert executor.fresh_readback_request(current) is None
    current = deepcopy(request)
    current["content_binding"]["artifact_manifest"][1]["sha256"] = "f" * 64
    assert executor.fresh_readback_request(current) is None


def test_observed_missing_public_image_stays_failed_without_a_readback_loop(tmp_path):
    store, executor = setup(tmp_path)
    adapter = NeoDestinationHandoff(native_executor=executor)
    value = intent("youtube", native_payload={"text": "Exact supported proposition.", "media_asset_ids": ["chart"]},
        media_assets=[{"asset_id": "chart", "sha256": "a" * 64, "path": str(tmp_path / "chart.png")}])
    packet, object_id, url = pending_readback(adapter, "youtube", value)
    request = packet["request"]
    executor.submit(request["request_sha256"], response(executor, packet,
        {"status": "SUCCESS", "observed_identity": "@CapitalChronicleYouTube", "public_object_id": object_id,
         "public_object_url": url, "observed_text": "Exact supported proposition.", "content_verified": True,
         "public_image_urls": [], "media_check_state": "MISSING_REQUIRED_MEDIA", "missing_required_media_observed": True}))
    observed = adapter.readback(destination="youtube", intent=value, public_object_id=object_id, public_object_url=url)
    assert observed["write_exists"] is True and observed["verified"] is False
    assert observed["content_binding_checks"] == {"text_match": True, "media_match": False, "thread_match": True}
    assert executor.fresh_readback_request(request) == request


@pytest.mark.parametrize("prior_action,claimed,changed_intent", [
    ("PUBLISH", False, False), ("READBACK", False, False),
    ("PUBLISH", True, False), ("PUBLISH", False, True)])
def test_verified_object_retires_only_unclaimed_requests_for_its_exact_intent(
        tmp_path, monkeypatch, prior_action, claimed, changed_intent):
    monkeypatch.setattr("live_contentops.llm_operator_control_v1.assert_llm_operator_execution_enabled", lambda: None)
    store, executor = setup(tmp_path, allow_publish=True)
    adapter = NeoDestinationHandoff(native_executor=executor)
    value = intent("x")
    older = adapter.request(destination="x", action=prior_action,
        intent=intent("x", package_identity="different") if changed_intent else value,
        authorization_context={"schema_version": "contentops.canonical_machine_authorization.v1",
            "operating_mode": "AUTONOMOUS_DEFAULT", "destination": "x",
            "dispatch_attempt_identity": "controlled-dispatch", "work_item_id": "work",
            "payload_hash": "hash"})
    with pytest.raises(NativeNeoInputRequired):
        executor(older)
    if claimed:
        store.register_outbox_message(message_id="controlled-outbox", work_item_id="work",
            destination="x", payload=json.dumps(value), status="READY")
        store.register_platform_dispatch(dispatch_id="controlled-dispatch", message_id="controlled-outbox",
            platform="x", status=PENDING)
        monkeypatch.setattr(executor, "readiness", lambda _: {"authenticated": True, "native_executor_bound": True})
        executor.begin(older["request_sha256"])
    dispatches_before = store.list_platform_dispatches()
    packet, object_id, url = pending_readback(adapter, destination="x", value=value)
    executor.submit(packet["request"]["request_sha256"], response(executor, packet, {
        "status": "SUCCESS", "observed_identity": "@Capitalnicle", "content_verified": True,
        "public_object_id": object_id, "public_object_url": url,
        "observed_text": "Exact supported proposition."}))
    actual = adapter.readback(destination="x", intent=value,
        public_object_id=object_id, public_object_url=url)
    assert actual["verified"] is True
    pending = {p["request"]["request_sha256"] for p in executor.pending()}
    assert (older["request_sha256"] in pending) is (claimed or changed_intent)
    assert store.list_platform_dispatches() == dispatches_before


@pytest.mark.parametrize("age,retired", [(1200, True), (599, False)])
def test_only_proven_absence_retires_older_unclaimed_reads(tmp_path, monkeypatch, age, retired):
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    store, executor = setup(tmp_path)
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(store, "get_platform_dispatch", lambda key: {"status": "UNKNOWN_WRITE",
        "dispatched_at": (now - timedelta(seconds=age)).isoformat()})
    adapter = NeoDestinationHandoff(native_executor=executor)
    def read():
        return adapter.readback(destination="x", intent=intent("x"),
            public_object_id=None, public_object_url=None)
    executor.clock = lambda: now - timedelta(seconds=601)
    # The first request predates delivery-manifest metadata being refreshed.
    # Its immutable article intent and latest dispatch attempt are unchanged.
    older = adapter.request(destination="x", action="READBACK", intent=intent("x"))
    older["content_binding"]["artifact_manifest"] = [{"path": "controlled-old-manifest.json", "sha256": "a" * 64}]
    older["request_sha256"] = sha256_of({k: v for k, v in older.items() if k != "request_sha256"})
    with pytest.raises(NativeNeoInputRequired) as old:
        executor(older)
    executor.clock = lambda: now
    with pytest.raises(NativeNeoInputRequired) as current:
        read()
    packet = current.value.request
    observed = response(executor, packet, {"observed_identity": "@Capitalnicle",
        "observed_profile_url": "https://x.com/Capitalnicle", "authenticated": True,
        "activity_feed_loaded": True, "target_post_absent": True,
        "observed_text": "Own profile loaded through older posts; target absent."})
    observed["tool_observation"]["observed_at_utc"] = now.isoformat()
    executor.submit(packet["request"]["request_sha256"], observed)
    assert read()["write_absent"] is retired
    pending = {p["request"]["request_sha256"] for p in executor.pending()}
    assert (old.value.request["request"]["request_sha256"] not in pending) is retired


@pytest.mark.parametrize("destination", ["substack", "x", "youtube"])
def test_readback_action_uses_existing_window_and_task_group_without_changing_request(tmp_path, destination):
    _, executor = setup(tmp_path)
    adapter = NeoDestinationHandoff(native_executor=executor)
    packet, _, _ = pending_readback(adapter, destination=destination)
    action = executor.begin(packet["request"]["request_sha256"])
    assert action["request"] == packet["request"]
    workspace = action["browser_workspace"]
    assert workspace["policy"] == "JIM_DECISION_63"
    assert "one existing" in workspace["window"]
    assert "only if none exists" in workspace["window"]
    assert "tabs action=new" in workspace["tabs"] and "groupId" in workspace["tabs"]


@pytest.mark.parametrize("age,identity,loaded,absent", [
    (1200, "@Capitalnicle", True, True), (599, "@Capitalnicle", True, False),
    (1200, "@OTHER_ACCOUNT", True, False), (1200, "@Capitalnicle", False, False)])
def test_own_profile_absence_reaches_reconciliation_only_after_ten_minutes(tmp_path, monkeypatch, age, identity, loaded, absent):
    store, executor = setup(tmp_path)
    attempted_at = (datetime.now(timezone.utc) - timedelta(seconds=age)).isoformat()
    monkeypatch.setattr(store, "get_platform_dispatch", lambda key: {"status": "UNKNOWN_WRITE",
        "dispatched_at": attempted_at})
    adapter = NeoDestinationHandoff(native_executor=executor)
    def read():
        return adapter.readback(destination="x", intent=intent("x"), public_object_id=None, public_object_url=None)
    with pytest.raises(NativeNeoInputRequired) as pending:
        read()
    packet = pending.value.request
    observed = response(executor, packet, {"observed_identity": identity,
        "observed_profile_url": "https://x.com/Capitalnicle", "authenticated": True,
        "activity_feed_loaded": loaded, "target_post_absent": True,
        "observed_text": "Own profile is loaded through older posts; the requested title and link are absent."})
    observed["tool_observation"]["surface"] = "CODEX_EXEC"
    executor.submit(packet["request"]["request_sha256"], observed)
    actual = read()
    assert actual["write_absent"] is absent
    assert store.list_platform_dispatches() == []


@pytest.mark.parametrize("retry_age,absent", [(120, False), (700, True)])
def test_profile_absence_waits_ten_minutes_after_latest_api_attempt(tmp_path, monkeypatch, retry_age, absent):
    from hashlib import sha256
    store, executor = setup(tmp_path)
    now = datetime.now(timezone.utc)
    ids = DurablePublicationCoordinator._ids("work", "plan", "x")
    monkeypatch.setattr(store, "get_platform_dispatch", lambda key: {"status": "UNKNOWN_WRITE",
        "dispatched_at": (now - timedelta(seconds=1800)).isoformat()})
    store.register_incident(incident_id="incident_dispatch_outcome_"
        + sha256(ids["dispatch_id"].encode()).hexdigest()[:24] + "_retry", work_item_id="work",
        severity="DISPATCH_FAILURE", description=json.dumps({"dispatch_id": ids["dispatch_id"],
            "attempt_started_at_utc": (now - timedelta(seconds=retry_age)).isoformat()}))
    adapter = NeoDestinationHandoff(native_executor=executor)
    def read():
        return adapter.readback(destination="x", intent=intent("x"), public_object_id=None, public_object_url=None)
    with pytest.raises(NativeNeoInputRequired) as pending:
        read()
    packet = pending.value.request
    observed = response(executor, packet, {"observed_identity": "@Capitalnicle",
        "observed_profile_url": "https://x.com/Capitalnicle", "authenticated": True,
        "activity_feed_loaded": True, "target_post_absent": True,
        "observed_text": "Own feed loaded with older posts; the requested post is absent."})
    executor.submit(packet["request"]["request_sha256"], observed)
    assert read()["write_absent"] is absent


def test_retry_invalidates_prior_absence_return_in_same_readback_epoch(tmp_path, monkeypatch):
    from hashlib import sha256
    store, executor = setup(tmp_path)
    now = datetime.now(timezone.utc)
    ids = DurablePublicationCoordinator._ids("work", "plan", "x")
    monkeypatch.setattr(store, "get_platform_dispatch", lambda key: {"status": "UNKNOWN_WRITE",
        "dispatched_at": (now - timedelta(seconds=1800)).isoformat()})
    adapter = NeoDestinationHandoff(native_executor=executor)
    def read():
        return adapter.readback(destination="x", intent=intent("x"), public_object_id=None, public_object_url=None)
    with pytest.raises(NativeNeoInputRequired) as pending:
        read()
    packet = pending.value.request
    observed = response(executor, packet, {"observed_identity": "@Capitalnicle",
        "observed_profile_url": "https://x.com/Capitalnicle", "authenticated": True,
        "activity_feed_loaded": True, "target_post_absent": True,
        "observed_text": "Own feed loaded; the target is absent."})
    executor.submit(packet["request"]["request_sha256"], observed)
    assert read()["write_absent"] is True
    store.register_incident(incident_id="incident_dispatch_outcome_"
        + sha256(ids["dispatch_id"].encode()).hexdigest()[:24] + "_retry", work_item_id="work",
        severity="DISPATCH_FAILURE", description=json.dumps({"dispatch_id": ids["dispatch_id"],
            "attempt_started_at_utc": datetime.now(timezone.utc).isoformat()}))
    with pytest.raises(NativeNeoInputRequired) as fresh:
        read()
    assert fresh.value.request["request"]["request_sha256"] != packet["request"]["request_sha256"]
    assert fresh.value.request["request"]["observation_epoch"] == packet["request"]["observation_epoch"]


@pytest.mark.parametrize("fault", [None, "unverified_link", "wrong_link", "extra_claim", "duplicate_root", "missing_notice", "wrong_order"])
def test_repaired_x_thread_uses_existing_posts_and_verified_shortlink(tmp_path, fault):
    _, executor = setup(tmp_path)
    canonical = "https://capitalchronicle.substack.com/p/test"
    expected = ["Source-backed headline.\n\n" + canonical,
        "Watch the next official release.",
        "Retrospective analysis.\n\nAnalysis, not financial advice. Readers decide whether to trade."]
    value = intent("x", native_payload={"posts": [{"text": text} for text in expected]})
    adapter = NeoDestinationHandoff(native_executor=executor)
    packet, object_id, url = pending_readback(adapter, destination="x", value=value)
    shown = "https://\ncapitalchronicle.substack.com/p/te\nst\n..."
    texts = [expected[0].replace(canonical, shown), expected[1], "Readers decide whether to trade.", expected[2]]
    if fault == "extra_claim":
        texts[2] = "Buy stocks now: guaranteed gains."
    if fault == "duplicate_root":
        texts[2] = texts[0]
    if fault == "missing_notice":
        texts.pop()
    if fault == "wrong_order":
        texts[0], texts[1] = texts[1], texts[0]
    thread = [{"public_object_id": str(123+i), "public_object_url": "https://x.com/Capitalnicle/status/" + str(123+i),
        "observed_text": text} for i, text in enumerate(texts)]
    links = [{"displayed_text": shown, "short_url": "https://t.co/realObservedLink", "target_url": canonical,
        "target_verified": fault != "unverified_link", "public_object_url": url}]
    if fault == "wrong_link":
        links[0]["target_url"] = "https://example.com/unrelated"
    observed = response(executor, packet, {"observed_identity": "@Capitalnicle", "public_object_id": object_id,
        "public_object_url": url, "content_verified": True, "observed_text": "\n\n".join(texts),
        "observed_thread": thread, "observed_link_resolutions": links})
    executor.submit(packet["request"]["request_sha256"], observed)
    result = adapter.readback(destination="x", intent=value, public_object_id=object_id, public_object_url=url)
    assert result["verified"] is (fault is None)
    assert result["write_exists"] is True


@pytest.mark.parametrize("observed_stable_id", [None, "wrong-company"])
def test_company_probe_names_required_id_and_accepts_corrected_observation(tmp_path, observed_stable_id):
    store, executor = setup(tmp_path)
    with pytest.raises(NativeNeoInputRequired) as pending:
        executor.readiness("LINKEDIN_COMPANY_POST")
    packet = pending.value.request
    assert packet["request"]["expected_stable_id"] == "143198922"
    observed = response(executor, packet, {"authenticated": True,
        "observed_identity": "linkedin:company:143198922", "observed_stable_id": observed_stable_id})
    request_hash = packet["request"]["request_sha256"]
    with pytest.raises(ValueError, match="STABLE_IDENTITY_OBSERVATION_REQUIRED"):
        executor.submit(request_hash, observed)
    assert executor._get(request_hash, "response") is None
    observed["result"]["observed_stable_id"] = "143198922"
    executor.submit(request_hash, observed)
    proof = executor.readiness("LINKEDIN_COMPANY_POST")
    assert proof["authenticated"] and proof["proof_fresh"]
    assert proof["stable_id"] == "143198922"
    assert store.list_platform_dispatches() == []


def test_legacy_company_probe_without_numeric_id_does_not_hold_new_probe(tmp_path):
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of

    store, executor = setup(tmp_path)
    with pytest.raises(NativeNeoInputRequired) as pending:
        executor.readiness("LINKEDIN_COMPANY_POST")
    legacy_request = dict(pending.value.request["request"])
    legacy_request.pop("expected_stable_id")
    legacy_request.pop("request_sha256")
    legacy_request["request_sha256"] = sha256_of(legacy_request)
    with pytest.raises(NativeNeoInputRequired) as legacy_pending:
        executor(legacy_request)
    legacy_packet = legacy_pending.value.request
    observed = response(executor, legacy_packet, {"authenticated": True,
        "observed_identity": "linkedin:company:143198922"})
    executor.submit(legacy_request["request_sha256"], observed)
    with pytest.raises(NativeNeoInputRequired) as fresh:
        executor.readiness("LINKEDIN_COMPANY_POST")
    assert fresh.value.request["request"]["expected_stable_id"] == "143198922"
    assert fresh.value.request["request"]["request_sha256"] != legacy_request["request_sha256"]
    assert executor._get(legacy_request["request_sha256"], "response")["result"]["authenticated"] is True
    assert store.list_platform_dispatches() == []


def test_unidentified_linkedin_api_attempt_reaches_existing_neo_readback():
    from types import SimpleNamespace
    calls = []
    def cannot_read_unidentified(**kwargs):
        raise AssertionError("A missing post ID cannot be resolved by API token refresh")
    api = SimpleNamespace(readback=cannot_read_unidentified)
    neo = SimpleNamespace(readback=lambda **kw: calls.append(kw) or {"readback_source": "CONTROLLED_NEO"})
    runtime = CanonicalDestinationTransportRuntimeV1(linkedin_transport=api, neo_transport=neo)
    result = runtime.readback(destination="linkedin", public_object_id=None, public_object_url=None, intent=intent())
    assert result["readback_source"] == "CONTROLLED_NEO"
    assert len(calls) == 1 and calls[0]["public_object_id"] is None


def test_same_turn_gets_later_ten_minute_readback_without_another_send(tmp_path):
    store, executor = setup(tmp_path)
    now = [datetime(2026, 11, 4, 8, 0, tzinfo=timezone.utc)]
    executor.clock = lambda: now[0]
    first, _, _ = pending_readback(NeoDestinationHandoff(native_executor=executor), "x")
    now[0] += timedelta(minutes=10)
    later, _, _ = pending_readback(NeoDestinationHandoff(native_executor=executor), "x")
    assert later["request"]["request_sha256"] != first["request"]["request_sha256"]
    assert later["request"]["native_invocation_id"] == first["request"]["native_invocation_id"]
    assert store.list_platform_dispatches() == []


def test_later_native_turn_obtains_fresh_readback_without_repeating_a_write(tmp_path):
    store, executor = setup(tmp_path)
    first, object_id, url = pending_readback(NeoDestinationHandoff(native_executor=executor), "x")
    failed = response(executor, first, {"status": "BLOCKED", "observed_text": "Network unavailable"})
    executor.submit(first["request"]["request_sha256"], failed)
    later = NativeNeoExecutor(store, operation_id="same-op", output_dir=tmp_path,
        native_invocation_id="later-controlled-turn")
    fresh, _, _ = pending_readback(NeoDestinationHandoff(native_executor=later), "x")
    assert fresh["request"]["request_sha256"] != first["request"]["request_sha256"]
    assert executor._get(first["request"]["request_sha256"], "response")["result"]["status"] == "BLOCKED"
    assert store.list_platform_dispatches() == []


@pytest.mark.parametrize("destination", ["substack", "x", "youtube"])
def test_exact_readback_restart_immutable_and_no_public_action(tmp_path, destination):
    store, executor = setup(tmp_path)
    adapter = NeoDestinationHandoff(native_executor=executor)
    packet, object_id, url = pending_readback(adapter, destination)
    observed = {"status": "SUCCESS", "observed_identity": packet["request"]["expected_identity"],
                "public_object_id": object_id, "public_object_url": url,
                "observed_text": "Exact supported proposition.", "content_verified": True}
    result = response(executor, packet, observed)
    executor.submit(packet["request"]["request_sha256"], result)
    restarted = NativeNeoExecutor(store, operation_id="same-op", output_dir=tmp_path,
                                   native_invocation_id="controlled-test")
    adapter = NeoDestinationHandoff(native_executor=restarted)
    actual = adapter.readback(destination=destination, intent=intent(destination), public_object_id=object_id, public_object_url=url)
    assert actual["verified"] is True
    assert store.list_platform_dispatches() == []
    with pytest.raises(ValueError, match="CONFLICT"):
        executor.submit(packet["request"]["request_sha256"], {**result, "result": {**result["result"], "observed_text": "changed"}})


@pytest.mark.parametrize("thread_field", ["observed_thread", "thread_posts"])
def test_readback_requires_exact_text_url_media_and_thread(tmp_path, thread_field):
    _, executor = setup(tmp_path)
    adapter = NeoDestinationHandoff(native_executor=executor)
    value = intent("x", native_payload={"posts": [{"text": "First source-bound post."}, {"text": "Second useful post."}]},
                   media_assets=[{"asset_id": "card", "sha256": "media-hash"}])
    packet, object_id, url = pending_readback(adapter, "x", value)
    result = response(executor, packet, {"status": "SUCCESS", "observed_identity": "@Capitalnicle",
        "public_object_id": object_id, "public_object_url": url, "content_verified": True,
        "observed_text": "First source-bound post. Second useful post.",
        "observed_media_sha256": ["media-hash"], thread_field: [
            {"public_object_id": "123", "public_object_url": url, "observed_text": "First source-bound post."},
            {"public_object_id": "124", "public_object_url": "https://x.com/Capitalnicle/status/124", "observed_text": "Second useful post."}]})
    executor.submit(packet["request"]["request_sha256"], result)
    actual = adapter.readback(destination="x", intent=value, public_object_id=object_id, public_object_url=url)
    assert actual["verified"] is True
    # Pure verification rejects content flags without exact observed text/media/order.
    bad = NeoDestinationHandoff(native_executor=lambda req: {**result["result"], "request_sha256": req["request_sha256"],
                                                            "observed_media_sha256": []})
    assert bad.readback(destination="x", intent=value, public_object_id=object_id, public_object_url=url)["verified"] is False
    thread = result["result"][thread_field]
    for invalid_thread in (list(reversed(thread)), thread[:1], [thread[0], thread[0]]):
        invalid = NeoDestinationHandoff(native_executor=lambda req: {**result["result"],
            "request_sha256": req["request_sha256"], thread_field: invalid_thread})
        assert invalid.readback(destination="x", intent=value,
            public_object_id=object_id, public_object_url=url)["verified"] is False


@pytest.mark.parametrize("destination", ["x", "youtube"])
@pytest.mark.parametrize("changed,verified", [
    ({}, True),
    ({"source_asset_sha256": "c" * 64}, False),
    ({"public_image_url": "https://example.org/media/chart.jpg"}, False),
    ({"public_image_url": "https://pbs.twimg.com/profile_images/chart.jpg"}, False),
    ({"public_image_url": "http://pbs.twimg.com/media/chart.jpg"}, False),
    ({"platform_sha256": "unverified"}, False),
    ({"public_object_url": "https://x.com/Capitalnicle/status/124"}, False),
    ({"pixels_inspected": False}, False),
    ({"source_pixels_match": False}, False),
])
@pytest.mark.parametrize("discover_object", [False, True])
def test_transcoded_chart_needs_exact_public_object_and_pixel_inspection(destination, changed, verified, discover_object):
    source_hash = "a" * 64
    url = "https://x.com/Capitalnicle/status/123" if destination == "x" else "https://www.youtube.com/post/123"
    identity = "@Capitalnicle" if destination == "x" else "@CapitalChronicleYouTube"
    image = ("https://pbs.twimg.com/media/chart?format=jpg&name=small" if destination == "x"
             else "https://yt3.ggpht.com/chart=s640-rw-nd-v1")
    value = intent(destination, media_assets=[{"asset_id": "card", "sha256": source_hash}])
    comparison = {"source_asset_sha256": source_hash, "platform_sha256": "b" * 64,
        "public_image_url": image,
        "public_object_url": url, "pixels_inspected": True, "source_pixels_match": True, **changed}
    def observed(request):
        return {"request_sha256": request["request_sha256"], "observed_identity": identity,
            "status": "SUCCESS", "public_object_id": "123", "public_object_url": url,
            "observed_text": "Exact supported proposition.", "content_verified": True,
            "observed_media_sha256": ["b" * 64], "media_comparisons": [comparison]}
    result = NeoDestinationHandoff(native_executor=observed).readback(destination=destination, intent=value,
        public_object_id=None if discover_object else "123", public_object_url=None if discover_object else url)
    assert result["verified"] is verified


@pytest.mark.parametrize("fault", [None, "identity", "handle", "id", "number", "link", "pinned_object"])
def test_discovered_x_thread_recovers_exact_links_media_and_identity(fault):
    canonical = "https://capitalchronicle.substack.com/p/test"
    url = "https://x.com/Capitalnicle/status/123"
    shown = "capitalchronicle.substack.com/p/test..."
    texts = ["Oil and the reopen. " + canonical, "Base case: 55% model estimate."]
    value = intent("x", native_payload={"posts": [{"text": t} for t in texts]},
                   media_assets=[{"asset_id": "chart", "sha256": "a" * 64}])
    actual_url = url.replace("Capitalnicle", "OtherAccount") if fault == "handle" else url
    comparison = {"source_asset_sha256": "a" * 64, "platform_sha256": "b" * 64,
        "public_image_url": "https://pbs.twimg.com/media/chart?format=png&name=small",
        "public_object_url": actual_url, "pixels_inspected": True, "source_pixels_match": True}
    observed_texts = ["Oil and the reopen. " + shown,
                      "Base case: 50% model estimate." if fault == "number" else texts[1]]
    def observed(request):
        return {"request_sha256": request["request_sha256"], "status": "SUCCESS",
            "observed_identity": "@OtherAccount" if fault == "identity" else "@Capitalnicle",
            "public_object_id": "999" if fault == "id" else "123", "public_object_url": actual_url,
            "content_verified": True, "observed_text": "\n".join(observed_texts),
            "media_comparisons": [comparison],
            "observed_link_resolutions": [{"displayed_text": shown, "short_url": "https://t.co/abc",
                "target_verified": True, "public_object_url": actual_url,
                "target_url": canonical + "-wrong" if fault == "link" else canonical}],
            "observed_thread": [{"public_object_id": str(123+i),
                "public_object_url": actual_url if i == 0 else "https://x.com/Capitalnicle/status/124",
                "observed_text": text} for i, text in enumerate(observed_texts)]}
    result = NeoDestinationHandoff(native_executor=observed).readback(destination="x", intent=value,
        public_object_id="999" if fault == "pinned_object" else None,
        public_object_url="https://x.com/Capitalnicle/status/999" if fault == "pinned_object" else None)
    assert result["verified"] is (fault is None)
    if fault is None:
        assert result["write_exists"] is True
        assert result["content_binding_checks"] == {"text_match": True, "media_match": True, "thread_match": True}


def test_lost_readonly_observation_resumes_in_new_turn_without_reclaiming_write(tmp_path):
    store, first = setup(tmp_path)
    packet, object_id, url = pending_readback(NeoDestinationHandoff(native_executor=first))
    request_hash = packet["request"]["request_sha256"]
    first.begin(request_hash)
    original_claim = first._get(request_hash, "started")
    restarted = NativeNeoExecutor(store, operation_id="same-op", output_dir=tmp_path / "resume",
                                  native_invocation_id="resumed-readonly-turn")
    assert restarted.begin(request_hash)["tool_request_sha256"] == packet["tool_request_sha256"]
    with pytest.raises(ValueError, match="ALREADY_CLAIMED"):
        restarted.begin(request_hash)
    returned = {
        "tool_request_sha256": packet["tool_request_sha256"],
        "tool_observation": {"tool_name": TOOL, "native_invocation_id": "resumed-readonly-turn",
            "surface": "CODEX_DESKTOP_CONVERSATION", "observation_source": "CONTROLLED_TEST_NOT_BROWSER_PROOF",
            "observed_at_utc": datetime.now(timezone.utc).isoformat()},
        "result": {"request_sha256": request_hash, "status": "SUCCESS", "observed_identity": "capitalchronicle.substack.com",
            "public_object_id": object_id, "public_object_url": url, "observed_text": "Exact supported proposition.",
            "content_verified": True},
    }
    restarted.submit(request_hash, returned)
    result = NeoDestinationHandoff(native_executor=restarted).readback(destination="substack", intent=intent(),
        public_object_id=object_id, public_object_url=url)
    assert result["verified"] is True
    assert first._get(request_hash, "started") == original_claim
    assert store.list_platform_dispatches() == []


def test_new_turn_gets_its_own_identity_probe_even_in_same_five_minute_epoch(tmp_path):
    store, first = setup(tmp_path)
    now = datetime(2026, 10, 24, 0, 1, tzinfo=timezone.utc)
    first.clock = lambda: now
    with pytest.raises(NativeNeoInputRequired) as pending:
        first.readiness("SUBSTACK_ARTICLE")
    packet = pending.value.request
    first.begin(packet["request"]["request_sha256"])
    restarted = NativeNeoExecutor(store, operation_id="same-op", output_dir=tmp_path / "resume",
        native_invocation_id="new-identity-turn", clock=lambda: now)
    with pytest.raises(NativeNeoInputRequired) as fresh:
        restarted.readiness("SUBSTACK_ARTICLE")
    assert fresh.value.request["request"]["request_sha256"] != packet["request"]["request_sha256"]
    assert first._get(packet["request"]["request_sha256"], "started")["native_invocation_id"] == "controlled-test"
    assert [p["request"]["request_sha256"] for p in restarted.pending()] == [fresh.value.request["request"]["request_sha256"]]
    assert store.list_platform_dispatches() == []


def test_late_exact_readback_satisfies_a_new_bucket_request_without_another_action(tmp_path):
    store, executor = setup(tmp_path)
    now = datetime(2026, 11, 4, 14, 39, 59, tzinfo=timezone.utc)
    executor.clock = lambda: now
    adapter = NeoDestinationHandoff(native_executor=executor)
    packet, object_id, url = pending_readback(adapter)
    request_hash = packet["request"]["request_sha256"]
    executor.begin(request_hash)
    now += timedelta(seconds=2)
    later, _, _ = pending_readback(adapter)
    assert later["request"]["request_sha256"] != request_hash
    executor.submit(request_hash, {
        "tool_request_sha256": packet["tool_request_sha256"],
        "tool_observation": {"tool_name": TOOL, "native_invocation_id": "controlled-test",
            "surface": "CODEX_EXEC", "observation_source": "CONTROLLED_TEST_NOT_BROWSER_PROOF",
            "observed_at_utc": now.isoformat()},
        "result": {"request_sha256": request_hash, "status": "SUCCESS",
            "observed_identity": "capitalchronicle.substack.com",
            "public_object_id": object_id, "public_object_url": url,
            "observed_text": "Exact supported proposition.", "content_verified": True}})
    assert adapter.readback(destination="substack", intent=intent(),
        public_object_id=object_id, public_object_url=url)["verified"] is True
    assert executor.pending() == []
    assert executor._get(later["request"]["request_sha256"], "request") is not None
    retired = store.get_outbox_message(executor._key(later["request"]["request_sha256"], "request"))
    assert retired["status"] == "NATIVE_NEO_SUPERSEDED"
    now += timedelta(seconds=601)
    assert executor.pending() == []
    assert store.list_platform_dispatches() == []


@pytest.mark.parametrize("fault", [None, "stale", "invocation", "identity", "object", "unverified", "content", "media"])
def test_successful_exact_readback_survives_bucket_change_by_observation_time(tmp_path, fault):
    store, executor = setup(tmp_path)
    now = datetime(2026, 11, 4, 14, 39, 59, tzinfo=timezone.utc)
    executor.clock = lambda: now
    adapter = NeoDestinationHandoff(native_executor=executor)
    packet, object_id, url = pending_readback(adapter)
    request_hash = packet["request"]["request_sha256"]
    executor.begin(request_hash)
    now += timedelta(seconds=2)
    executor.submit(request_hash, {
        "tool_request_sha256": packet["tool_request_sha256"],
        "tool_observation": {"tool_name": TOOL, "native_invocation_id": "controlled-test",
            "surface": "CODEX_EXEC", "observation_source": "CONTROLLED_TEST_NOT_BROWSER_PROOF",
            "observed_at_utc": now.isoformat()},
        "result": {"request_sha256": request_hash, "status": "SUCCESS",
            "observed_identity": "wrong-account" if fault == "identity" else "capitalchronicle.substack.com",
            "public_object_id": "wrong-object" if fault == "object" else object_id, "public_object_url": url,
            "observed_text": "Exact supported proposition.", "content_verified": fault != "unverified"}})
    now += timedelta(seconds=601 if fault == "stale" else 1)
    if fault == "invocation":
        executor.native_invocation_id = "another-turn"
    value = intent()
    if fault == "content":
        value["payload"] = "A changed proposition."
    if fault == "media":
        value["media_assets"] = [{"asset_id": "different-chart", "sha256": "d" * 64}]
    before = len(store.list_outbox_messages())
    if fault:
        with pytest.raises(NativeNeoInputRequired):
            adapter.readback(destination="substack", intent=value,
                public_object_id=object_id, public_object_url=url)
    else:
        result = adapter.readback(destination="substack", intent=value,
            public_object_id=object_id, public_object_url=url)
        assert result["verified"] is True
        assert len(store.list_outbox_messages()) == before
    assert store.list_platform_dispatches() == []


def test_requested_publication_clock_can_complete_an_immutable_partial_readback(tmp_path):
    store, executor = setup(tmp_path)
    adapter = NeoDestinationHandoff(native_executor=executor)
    value = intent(published_content_export="contentops.published_content.v1")
    packet, object_id, url = pending_readback(adapter, value=value)
    result = {"status": "SUCCESS", "observed_identity": "capitalchronicle.substack.com",
        "public_object_id": object_id, "public_object_url": url, "content_verified": True,
        "observed_text": "Exact supported proposition."}
    executor.submit(packet["request"]["request_sha256"], response(executor, packet, result))
    original = executor._get(packet["request"]["request_sha256"], "response")
    fresh, _, _ = pending_readback(adapter, value=value)
    assert fresh["request"]["request_sha256"] != packet["request"]["request_sha256"]
    executor.submit(fresh["request"]["request_sha256"], response(executor, fresh,
        {**result, "published_at_utc": datetime.now(timezone.utc).isoformat()}))
    assert adapter.readback(destination="substack", intent=value,
        public_object_id=object_id, public_object_url=url)["verified"] is True
    assert executor._get(packet["request"]["request_sha256"], "response") == original
    assert store.list_platform_dispatches() == []


@pytest.mark.parametrize("elapsed,authenticated,reuse", [(1800, True, True), (599, True, False), (1800, False, False)])
def test_loaded_absence_reuses_exact_attempt_across_clock_bucket(tmp_path, elapsed, authenticated, reuse):
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    from live_contentops.native_neo_executor_v1 import SCHEMA
    store, executor = setup(tmp_path)
    now = datetime.now(timezone.utc)
    executor.clock = lambda: now
    prior = {"action": "READBACK", "destination": "linkedin", "work_item_id": "work",
        "expected_identity": "linkedin:jimcc", "entry_url": "https://www.linkedin.com/in/jimcc/recent-activity/all/",
        "public_object_id": None, "public_object_url": None, "native_invocation_id": "controlled-test",
        "content_binding": {"media_manifest": [{"sha256": "a" * 64}]},
        "latest_dispatch_attempt_at_utc": (now - timedelta(seconds=elapsed+60)).isoformat(),
        "observation_epoch": int(now.timestamp()) // 600 - 1}
    prior["request_sha256"] = sha256_of(prior)
    executor._put(prior["request_sha256"], "request", {"schema_version": SCHEMA,
        "operation_id": "same-op", "request": prior}, "work")
    result = {"status": "SUCCESS", "target_post_absent": True, "authenticated": authenticated,
        "activity_feed_loaded": True, "observed_profile_url": prior["entry_url"],
        "observed_identity": "linkedin:jimcc", "content_verified": False,
        "native_tool_observation": {"observed_at_utc": (now-timedelta(seconds=60)).isoformat(),
            "native_invocation_id": "controlled-test"}}
    executor._put(prior["request_sha256"], "response", {"result": result}, "work")
    request = {**prior, "observation_epoch": int(now.timestamp()) // 600}
    request.pop("request_sha256")
    actual = executor.fresh_readback_request(request)
    assert (actual == prior) is reuse
    assert store.list_platform_dispatches() == []


@pytest.mark.parametrize("marked_pending", [False, True])
def test_pending_media_readback_accepts_completed_evidence_without_clock_wait(tmp_path, marked_pending):
    store, executor = setup(tmp_path)
    now = datetime.now(timezone.utc)
    executor.clock = lambda: now
    adapter = NeoDestinationHandoff(native_executor=executor)
    value = intent(media_assets=[{"asset_id": "chart", "sha256": "a" * 64}])
    packet, object_id, url = pending_readback(adapter, value=value)

    def submit(packet, **extra):
        request_hash = packet["request"]["request_sha256"]
        executor.begin(request_hash)
        executor.submit(request_hash, {
            "tool_request_sha256": packet["tool_request_sha256"],
            "tool_observation": {"tool_name": TOOL, "native_invocation_id": "controlled-test",
                "surface": "CODEX_EXEC", "observation_source": "CONTROLLED_TEST_NOT_BROWSER_PROOF",
                "observed_at_utc": now.isoformat()},
            "result": {"request_sha256": request_hash, "status": "SUCCESS",
                "observed_identity": "capitalchronicle.substack.com", "public_object_id": object_id,
                "public_object_url": url, "observed_text": "Exact supported proposition.",
                "content_verified": True, **extra}})

    submit(packet, **({"media_check_state": "PENDING_BINARY_COMPARISON"} if marked_pending else {}))
    original = executor._get(packet["request"]["request_sha256"], "response")
    fresh, _, _ = pending_readback(adapter, value=value)
    assert fresh["request"]["request_sha256"] != packet["request"]["request_sha256"]
    assert fresh["request"]["supersedes_incomplete_readback_sha256"]
    submit(fresh, observed_media_sha256=["a" * 64])
    result = adapter.readback(destination="substack", intent=value, public_object_id=object_id, public_object_url=url)
    assert result["verified"] is True
    assert executor._get(packet["request"]["request_sha256"], "response") == original
    assert store.list_platform_dispatches() == []


def test_coordinator_pending_publish_and_claimed_loss_enters_readback_only(tmp_path, monkeypatch):
    monkeypatch.setattr("live_contentops.llm_operator_control_v1.assert_llm_operator_execution_enabled", lambda: None)
    store, executor = setup(tmp_path, allow_publish=True)
    executor.operation_id = "work"
    control = store.get_operating_control()
    store.update_operating_control(operating_mode="AUTONOMOUS_DEFAULT", expected_state_version=control["state_version"],
        control_source="CONTROLLED_TEST")
    adapter = NeoDestinationHandoff(native_executor=executor)
    runtime = CanonicalDestinationTransportRuntimeV1(neo_transport=adapter)
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=runtime,
                                               readiness_provider=lambda _: {"readiness_state": "READY_AUTHENTICATED"})
    value = intent()
    ids = coordinator._ids("work", "plan", "substack")
    store.register_outbox_message(message_id=ids["message_id"], work_item_id="work", destination="substack",
                                  payload=json.dumps(value), status="READY")
    message = store.get_outbox_message(ids["message_id"])
    first = coordinator._dispatch_message(message, canonical_url=value["canonical_url"])
    assert first["status"] == PENDING and first["publish_called"] is False
    assert coordinator.recover_pending()["backlog_blocking_new_publication"] is True
    packet = executor.pending()[0]
    # Controlled boundary fixture; actual identity observations are separately proven in Neo.
    monkeypatch.setattr(executor, "readiness", lambda surface: {"authenticated": True, "native_executor_bound": True})
    action = executor.begin(packet["request"]["request_sha256"])
    routine = action["substack_publish_routine"]
    assert action["browser_workspace"]["policy"] == "JIM_DECISION_63"
    assert routine["policy"] == "JIM_DECISIONS_48_52_63"
    assert "one existing" in routine["window"]
    assert "continue other destinations" in routine["email_code_dialog"]
    assert routine["email_code_return"]["automatic_wait"] is False
    # CC-199: the run's step clocks come back in its own return, with no extra turn.
    assert routine["step_clocks"]["return_as"] == "result.step_clocks"
    assert routine["step_clocks"]["fields"] == ["draft_ready_utc", "images_uploaded_utc", "publish_clicked_utc",
                                                "email_setting_confirmed_utc", "share_center_reached_utc"]
    with pytest.raises(ValueError, match="ALREADY_CLAIMED"):
        executor.begin(packet["request"]["request_sha256"])
    restarted = NativeNeoExecutor(store, operation_id="work", output_dir=tmp_path / "resume",
                                  native_invocation_id="new-publish-turn", allow_publish=True)
    with pytest.raises(ValueError, match="ALREADY_CLAIMED"):
        restarted.begin(packet["request"]["request_sha256"])
    recovered = coordinator.recover_pending()
    assert recovered["publish_calls"] == 0
    assert store.get_platform_dispatch(ids["dispatch_id"])["status"] == UNKNOWN_WRITE
    assert any(p["request"]["action"] == "READBACK" for p in executor.pending())


@pytest.mark.parametrize('recovery_owner', ['unbound', 'readonly', 'other-operation'])
def test_unrelated_recovery_preserves_claimed_native_write_and_late_return(tmp_path, monkeypatch, recovery_owner):
    monkeypatch.setattr('live_contentops.llm_operator_control_v1.assert_llm_operator_execution_enabled', lambda: None)
    store, executor = setup(tmp_path, allow_publish=True)
    executor.operation_id = 'work'
    control = store.get_operating_control()
    store.update_operating_control(operating_mode='AUTONOMOUS_DEFAULT',
        expected_state_version=control['state_version'], control_source='CONTROLLED_TEST')
    coordinator = DurablePublicationCoordinator(store=store,
        transport_runtime=CanonicalDestinationTransportRuntimeV1(
            neo_transport=NeoDestinationHandoff(native_executor=executor)),
        readiness_provider=lambda _: {'readiness_state': 'READY_AUTHENTICATED'})
    value = intent()
    ids = coordinator._ids('work', 'plan', 'substack')
    store.register_outbox_message(message_id=ids['message_id'], work_item_id='work', destination='substack',
        payload=json.dumps(value), status='READY')
    message = store.get_outbox_message(ids['message_id'])
    assert coordinator._dispatch_message(message, canonical_url=value['canonical_url'])['status'] == PENDING
    packet = executor.pending()[0]
    monkeypatch.setattr(executor, 'readiness', lambda _: {'authenticated': True, 'native_executor_bound': True})
    executor.begin(packet['request']['request_sha256'])
    claim = executor._get(packet['request']['request_sha256'], 'started')

    foreign = None if recovery_owner == 'unbound' else NativeNeoExecutor(store,
        operation_id='another-work' if recovery_owner == 'other-operation' else 'work',
        output_dir=tmp_path/'foreign', native_invocation_id='unrelated-recovery',
        allow_publish=recovery_owner != 'readonly')
    recovery = DurablePublicationCoordinator(store=store,
        transport_runtime=CanonicalDestinationTransportRuntimeV1(
            neo_transport=NeoDestinationHandoff(native_executor=foreign)))
    outcome = recovery.recover_pending()
    assert outcome['publish_calls'] == 0
    assert store.get_platform_dispatch(ids['dispatch_id'])['status'] == PENDING
    assert executor._get(packet['request']['request_sha256'], 'started') == claim

    executor.submit(packet['request']['request_sha256'], {
        'tool_request_sha256': packet['tool_request_sha256'],
        'tool_observation': {'tool_name': TOOL, 'native_invocation_id': executor.native_invocation_id,
            'surface': 'CODEX_NATIVE_SUBAGENT', 'observation_source': 'CONTROLLED_TEST_NOT_BROWSER_PROOF',
            'observed_at_utc': datetime.now(timezone.utc).isoformat()},
        'result': {'request_sha256': packet['request']['request_sha256'], 'status': 'SUCCESS',
            'observed_identity': 'capitalchronicle.substack.com', 'public_object_id': '123',
            'public_object_url': value['canonical_url']}})
    resumed = coordinator.recover_pending()
    assert store.get_platform_dispatch(ids['dispatch_id'])['public_object_id'] == '123'
    assert any(p['request']['action'] == 'READBACK' for p in executor.pending())
    assert resumed['publish_calls'] == 0  # Consumes the saved return; no second native action.


def test_existing_dispatch_readback_stays_in_coordinator_without_write(tmp_path):
    store, executor = setup(tmp_path)
    coordinator, bound = bind_native_neo_coordinator(store, operation_id="same-op", output_dir=tmp_path,
                                                    native_invocation_id="controlled-test")
    value = intent()
    ids = coordinator._ids("work", "plan", "substack")
    store.register_outbox_message(message_id=ids["message_id"], work_item_id="work", destination="substack",
                                  payload=json.dumps(value), status=DISPATCH_CONFIRMED)
    store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"], platform="substack",
        status=DISPATCH_CONFIRMED, public_object_id="123", public_object_url=value["canonical_url"])
    first = coordinator.readback_existing_dispatch(ids["dispatch_id"])
    assert first["publish_called"] is False and first["reconciliation_status"] != RECONCILED_CONFIRMED
    packet = bound.pending()[0]
    bound.submit(packet["request"]["request_sha256"], response(bound, packet, {
        "status": "SUCCESS", "observed_identity": "capitalchronicle.substack.com", "public_object_id": "123",
        "public_object_url": value["canonical_url"], "observed_text": value["payload"], "content_verified": True}))
    second = coordinator.readback_existing_dispatch(ids["dispatch_id"])
    assert second["reconciliation_status"] == RECONCILED_CONFIRMED
    assert second["public_write_performed"] is False
    assert len(store.list_platform_dispatches()) == 1


def test_readonly_publish_and_unclaimed_or_wrong_return_fail_closed(tmp_path):
    _, executor = setup(tmp_path)
    adapter = NeoDestinationHandoff(native_executor=executor)
    value = intent()
    auth = {"schema_version": "contentops.canonical_machine_authorization.v1", "operating_mode": "AUTONOMOUS_DEFAULT",
            "destination": "substack", "dispatch_attempt_identity": "attempt", "work_item_id": "work", "payload_hash": "hash"}
    assert adapter.publish(destination="substack", intent=value, authorization_context=auth)["definite_no_write"] is True
    packet, _, _ = pending_readback(adapter)
    with pytest.raises(ValueError, match="BINDING"):
        executor.submit(packet["request"]["request_sha256"], {})


@pytest.mark.parametrize("fault", [None, "stale", "invocation", "identity", "unauthenticated"])
def test_identity_observation_survives_epoch_boundary_only_while_exact_and_fresh(tmp_path, fault):
    from datetime import timedelta
    store, executor = setup(tmp_path)
    now = datetime(2026, 11, 2, 22, 34, 59, tzinfo=timezone.utc)
    executor.clock = lambda: now
    with pytest.raises(NativeNeoInputRequired) as pending:
        executor.readiness("SUBSTACK_ARTICLE")
    packet = pending.value.request
    executor.begin(packet["request"]["request_sha256"])
    observed = {"tool_request_sha256": packet["tool_request_sha256"],
        "tool_observation": {"tool_name": TOOL, "native_invocation_id": "controlled-test",
            "surface": "CODEX_NATIVE_SUBAGENT", "observation_source": "CONTROLLED_NOT_BROWSER_PROOF",
            "observed_at_utc": now.isoformat()},
        "result": {"request_sha256": packet["request"]["request_sha256"],
            "authenticated": fault != "unauthenticated",
            "observed_identity": "WRONG_IDENTITY" if fault == "identity" else "capitalchronicle.substack.com"}}
    executor.submit(packet["request"]["request_sha256"], observed)
    before = len(store.list_outbox_messages())
    now += timedelta(seconds=302 if fault == "stale" else 2)
    if fault == "invocation":
        executor.native_invocation_id = "different-native-turn"
    if fault:
        with pytest.raises(NativeNeoInputRequired):
            executor.readiness("SUBSTACK_ARTICLE")
    else:
        result = executor.readiness("SUBSTACK_ARTICLE")
        assert result["authenticated"] and result["proof_fresh"]
        assert len(store.list_outbox_messages()) == before
    assert store.list_platform_dispatches() == []
