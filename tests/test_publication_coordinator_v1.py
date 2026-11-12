from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def coordinator_transport_fixture_without_article_media(monkeypatch):
    """These transport fixtures have no article/media files.

    Exercise image validation with its real assets in test_publication_image_contract_cc463;
    keep this file focused on the coordinator's dispatch and recovery behavior.
    """
    from live_contentops import publication_image_contract_v1
    monkeypatch.setattr(publication_image_contract_v1, "validate_write", lambda *args: None)


@pytest.fixture
def cc401_copied_store(tmp_path):
    import sqlite3
    source, _, _ = _coordinator(tmp_path / "seed")
    copied = tmp_path / "copied.sqlite3"
    with sqlite3.connect(source.db_path) as src, sqlite3.connect(copied) as dst:
        src.backup(dst)
    return ContentOpsDurableStore(copied)


@pytest.mark.parametrize("destination", ["discord", "threads"])
@pytest.mark.parametrize("readback_raises", [False, True])
def test_cc401_provider_acceptance_does_not_file_incident(cc401_copied_store, tmp_path, monkeypatch,
                                                        destination, readback_raises):
    from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as pipeline
    from live_contentops import discord_live_adapter_v6 as discord, threads_adapter_v6 as threads
    from live_contentops import post_visuals_v1
    store = cc401_copied_store
    monkeypatch.setattr(post_visuals_v1, "require_publication_image", lambda *a: None)
    monkeypatch.setattr(pipeline, "_durable_intent_inputs", lambda intent: {
        "output_dir": tmp_path, "article": {}, "payloads": {destination: {"text": "exact text"}},
        "canonical_url": "https://capitalchronicle.substack.com/p/test", "local_media": "", "public_image_url": "", "media_assets": []})
    monkeypatch.setattr(discord, "execute_discord_post", lambda **kw: {
        "status": "SUCCESS", "id": "provider-123", "response": {"id": "provider-123", "content": ""}})
    monkeypatch.setattr(threads, "execute_threads_post", lambda **kw: {"status": "SUCCESS", "id": "provider-123"})
    def unavailable(**kw):
        if readback_raises:
            raise TimeoutError("eventual consistency")
        return {"status": "READBACK_UNAVAILABLE", "verified": False}
    monkeypatch.setattr(threads, "readback_threads_post", unavailable)
    monkeypatch.setattr(threads, "readback_threads_chain", unavailable)
    # Discord's attachment branch must also preserve acceptance if its GET fails.
    if destination == "discord" and readback_raises:
        monkeypatch.setattr(discord, "readback_discord_post", unavailable)
        monkeypatch.setattr(pipeline, "_sha256_file", lambda path: "fixture-hash")
        original = pipeline._durable_intent_inputs
        monkeypatch.setattr(pipeline, "_durable_intent_inputs", lambda intent: {**original(intent), "local_media": "fixture.png"})
    class Runtime(FixtureTransport):
        def publish(self, **kwargs):
            self.publish_calls.append(kwargs["destination"])
            return pipeline._publish_one_destination_from_durable_intent(**kwargs)
    transport = Runtime(ambiguous=True)
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=transport,
        readiness_provider=lambda d: {"readiness_state": "READY_NON_BROWSER_BINDING"})
    plan = _plan(destination)
    registered = coordinator.register_plan("work-1", plan)["registered"][0]
    message = store.get_outbox_message(registered["message_id"])
    result = coordinator._dispatch_message(message, canonical_url="https://capitalchronicle.substack.com/p/test")
    assert result["status"] == DISPATCH_CONFIRMED
    assert result["public_object_id"] == "provider-123"
    assert result["reconciliation_status"] != RECONCILED_CONFIRMED
    conn = store.get_connection()
    try:
        assert conn.execute("SELECT count(*) FROM incidents").fetchone()[0] == 0
    finally:
        conn.close()
    coordinator._dispatch_message(message, canonical_url=None)
    assert transport.publish_calls == [destination]


def test_cc401_failure_skips_destination_until_next_et_day(cc401_copied_store, monkeypatch):
    from datetime import timedelta
    import live_contentops.publication_coordinator_v1 as module
    store = cc401_copied_store
    class Clock(datetime):
        current = datetime(2026, 11, 10, 4, 59, tzinfo=timezone.utc)
        @classmethod
        def now(cls, tz=None):
            return cls.current
    monkeypatch.setattr(module, "datetime", Clock)
    class Failed(FixtureTransport):
        def publish(self, **kwargs):
            self.publish_calls.append(kwargs["destination"])
            raise TimeoutError("response lost")
    runtime = Failed(ambiguous=True)
    c = DurablePublicationCoordinator(store=store, transport_runtime=runtime,
        readiness_provider=lambda d: {"readiness_state": "READY_NON_BROWSER_BINDING"})
    def message(work, dest):
        if work != "work-1":
            store.create_work_item(story_id=work, title=work, target_surface="MULTI_PLATFORM", work_item_id=work,
                actor_ref="controlled_test", correlation_id=work)
        row = c.register_plan(work, _plan(dest))["registered"][0]
        return store.get_outbox_message(row["message_id"])
    first = message("work-1", "discord")
    assert c._dispatch_message(first, canonical_url=None)["status"] == UNKNOWN_WRITE
    second = message("second", "discord")
    skipped = c._dispatch_message(second, canonical_url=None)
    assert skipped["status"] == "DESTINATION_FAILED_ET_DAY_SKIP"
    assert skipped["first_failure"]["et_day"] == "2026-11-09"
    assert runtime.publish_calls == ["discord"]
    # Another destination continues, and the old ambiguous write is never retried.
    c._dispatch_message(message("other", "threads"), canonical_url=None)
    assert runtime.publish_calls == ["discord", "threads"]
    c._dispatch_message(first, canonical_url=None)
    assert runtime.publish_calls == ["discord", "threads"]
    Clock.current += timedelta(minutes=2)
    assert c._dispatch_message(second, canonical_url=None)["status"] == UNKNOWN_WRITE
    conn = store.get_connection()
    try:
        rows = [json.loads(r[0]) for r in conn.execute("SELECT description FROM incidents")]
    finally:
        conn.close()
    assert [(r["destination"], r["et_day"]) for r in rows] == [
        ("discord", "2026-11-09"), ("threads", "2026-11-09"), ("discord", "2026-11-10")]


@pytest.mark.parametrize("claimed", [False, True])
def test_cc401_cancel_note_only_before_native_claim(cc401_copied_store, tmp_path, claimed):
    from live_contentops.native_neo_executor_v1 import NativeNeoExecutor
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    store = cc401_copied_store
    c = DurablePublicationCoordinator(store=store, transport_runtime=FixtureTransport())
    row = c.register_plan("work-1", _plan("substack_notes"))["registered"][0]
    message = store.get_outbox_message(row["message_id"])
    intent = json.loads(message["payload"])
    intent["plan_status_post"] = True
    # Synthetic pending fixture; production payloads are never changed by cancellation.
    conn = store.get_connection()
    try:
        conn.execute("UPDATE outbox_messages SET payload=?,status=? WHERE message_id=?",
            (json.dumps(intent), "NATIVE_NEO_TOOL_PENDING", row["message_id"]))
        conn.commit()
    finally:
        conn.close()
    store.register_platform_dispatch(dispatch_id=row["dispatch_id"], message_id=row["message_id"],
        platform="substack_notes", status="NATIVE_NEO_TOOL_PENDING")
    e = NativeNeoExecutor(store, operation_id="work-1", output_dir=tmp_path,
        native_invocation_id="fixture", allow_publish=True)
    request = {"action": "PUBLISH", "destination": "substack_notes", "request_sha256": "fixture-hash",
               "intent_sha256": sha256_of(intent)}
    e._put("fixture-hash", "request", {"request": request}, "work-1")
    if claimed:
        e._put("fixture-hash", "started", {"native_invocation_id": "fixture"}, "work-1")
        with pytest.raises(ValueError, match="NOTE_ALREADY_CLAIMED"):
            c.cancel_unclaimed_note(row["message_id"], reason="CC401_STALE_STATUS_NOTE_UNCLAIMED")
        assert store.get_platform_dispatch(row["dispatch_id"])["status"] == "NATIVE_NEO_TOOL_PENDING"
    else:
        result = c.cancel_unclaimed_note(row["message_id"], reason="CC401_STALE_STATUS_NOTE_UNCLAIMED")
        assert result["status"] == DEFINITE_NO_WRITE
        assert store.get_outbox_message(row["message_id"])["payload"] == json.dumps(intent)
        with pytest.raises(ValueError, match="SUPERSEDED"):
            e.begin("fixture-hash")


def test_cc401_day_audit_waits_for_whole_day_and_detects_false_alarms(cc401_copied_store):
    import runpy
    audit = runpy.run_path(str(Path(__file__).parents[1] / "scripts/audit_publication_day_cc401.py"))["audit"]
    store = cc401_copied_store
    c = DurablePublicationCoordinator(store=store, transport_runtime=FixtureTransport())
    rows = c.register_plan("work-1", _plan("discord", "threads"))["registered"]
    for row, destination in zip(rows, ["discord", "threads"]):
        store.register_platform_dispatch(dispatch_id=row["dispatch_id"], message_id=row["message_id"],
            platform=destination, status=DISPATCH_CONFIRMED, public_object_id=destination + "-123")
    conn = store.get_connection()
    try:
        conn.execute("UPDATE platform_dispatches SET dispatched_at='2026-11-10T06:00:00+00:00'")
        conn.commit()
    finally:
        conn.close()
    assert audit(store.db_path, "2026-11-10", now=datetime(2026, 11, 10, 8, tzinfo=timezone.utc))["status"] == "OBSERVATION_PENDING"
    later = datetime(2026, 11, 11, 5, tzinfo=timezone.utc)
    result = audit(store.db_path, "2026-11-10", now=later)
    assert result["status"] == "PASS"
    assert result["confirmed_posts"] == {"discord": 1, "threads": 1}
    store.register_incident(incident_id="false-alarm", work_item_id="work-1", severity="DISPATCH_FAILURE",
        description=json.dumps({"dispatch_id": rows[0]["dispatch_id"], "destination": "discord", "status": UNKNOWN_WRITE}))
    conn = store.get_connection()
    try:
        conn.execute("UPDATE incidents SET created_at='2026-11-10T06:01:00+00:00'")
        conn.commit()
    finally:
        conn.close()
    assert audit(store.db_path, "2026-11-10", now=later)["status"] == "FAIL"


def test_cc401_day_audit_preserves_history_and_counts_actual_failures(cc401_copied_store):
    import runpy
    audit = runpy.run_path(str(Path(__file__).parents[1] / "scripts/audit_publication_day_cc401.py"))["audit"]
    store = cc401_copied_store
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=FixtureTransport())
    rows = coordinator.register_plan("work-1", _plan("discord", "threads", "substack_notes"))["registered"]
    for row, destination in zip(rows, ["discord", "threads", "substack_notes"]):
        store.register_platform_dispatch(dispatch_id=row["dispatch_id"], message_id=row["message_id"],
            platform=destination, status=DISPATCH_CONFIRMED, public_object_id=destination + "-123",
            public_object_url="https://example.com/" + destination)
        store.register_reconciliation(reconciliation_id=row["reconciliation_id"], work_item_id="work-1",
            status="RECONCILED_CONFIRMED")
    details = {
        "local-refusal": {"destination": "discord", "status": DEFINITE_NO_WRITE,
            "safe_error_classification": "DISCORD_CALL_THREAD_BOT_TOKEN_UNAVAILABLE"},
        "real-timeout": {"destination": "discord", "status": UNKNOWN_WRITE},
        "repaired-builder": {"destination": "substack", "status": UNKNOWN_WRITE,
            "safe_error_classification": "KeyError"},
        "recovered-note-1": {"destination": "substack_notes", "status": UNKNOWN_WRITE,
            "dispatch_id": rows[2]["dispatch_id"]},
        "recovered-note-2": {"destination": "substack_notes", "status": UNKNOWN_WRITE,
            "dispatch_id": rows[2]["dispatch_id"]},
    }
    for incident_id, detail in details.items():
        store.register_incident(incident_id=incident_id, work_item_id="work-1", severity="DISPATCH_FAILURE",
            description=json.dumps(detail))
    store.register_incident(incident_id="repaired-builder_local_prewrite_resolved", work_item_id="work-1",
        severity="RESOLVED_LOCAL_PREWRITE", description="{}")
    with store.get_connection() as conn:
        conn.execute("UPDATE platform_dispatches SET dispatched_at='2026-11-10T06:00:00+00:00'")
        conn.execute("UPDATE incidents SET created_at='2026-11-10T06:01:00+00:00'")
        conn.commit()
    before = hashlib.sha256(Path(store.db_path).read_bytes()).hexdigest()
    result = audit(store.db_path, "2026-11-10", now=datetime(2026, 11, 11, 5, tzinfo=timezone.utc))
    assert result["status"] == "PASS"
    assert result["destination_failure_incidents"] == {"discord": 2, "substack": 1, "substack_notes": 2}
    assert result["active_destination_failure_incidents"] == {"discord": 1}
    assert len(result["resolved_destination_failure_incidents"]) == 4
    assert hashlib.sha256(Path(store.db_path).read_bytes()).hexdigest() == before
    # Repaired history cannot hide a second genuine failure that same day.
    store.register_incident(incident_id="second-real-timeout", work_item_id="work-1", severity="DISPATCH_FAILURE",
        description=json.dumps({"destination": "discord", "status": UNKNOWN_WRITE}))
    with store.get_connection() as conn:
        conn.execute("UPDATE incidents SET created_at='2026-11-10T06:01:00+00:00'")
        conn.commit()
    result = audit(store.db_path, "2026-11-10", now=datetime(2026, 11, 11, 5, tzinfo=timezone.utc))
    assert result["status"] == "FAIL"
    assert result["active_destination_failure_incidents"] == {"discord": 2}


@pytest.mark.parametrize("destination", ["discord", "threads"])
def test_cc401_day_audit_never_excuses_a_confirmed_api_false_alarm(cc401_copied_store, destination):
    import runpy
    audit = runpy.run_path(str(Path(__file__).parents[1] / "scripts/audit_publication_day_cc401.py"))["audit"]
    store = cc401_copied_store
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=FixtureTransport())
    row = coordinator.register_plan("work-1", _plan(destination))["registered"][0]
    store.register_platform_dispatch(dispatch_id=row["dispatch_id"], message_id=row["message_id"],
        platform=destination, status=DISPATCH_CONFIRMED, public_object_id="provider-123",
        public_object_url="https://example.com/post")
    store.register_reconciliation(reconciliation_id=row["reconciliation_id"], work_item_id="work-1",
        status="RECONCILED_CONFIRMED")
    store.register_incident(incident_id="false-alarm", work_item_id="work-1", severity="DISPATCH_FAILURE",
        description=json.dumps({"destination": destination, "dispatch_id": row["dispatch_id"], "status": UNKNOWN_WRITE}))
    store.register_incident(incident_id="false-alarm_local_prewrite_resolved", work_item_id="work-1",
        severity="RESOLVED_LOCAL_PREWRITE", description="{}")
    with store.get_connection() as conn:
        conn.execute("UPDATE platform_dispatches SET dispatched_at='2026-11-10T06:00:00+00:00'")
        conn.execute("UPDATE incidents SET created_at='2026-11-10T06:01:00+00:00'")
        conn.commit()
    result = audit(store.db_path, "2026-11-10", now=datetime(2026, 11, 11, 5, tzinfo=timezone.utc))
    assert result["status"] == "FAIL"
    assert result["false_unknown_write_incidents"] == ["false-alarm"]


@pytest.mark.parametrize("case", ["unreconciled_identity", "wrong_destination_identity", "ambiguous_composer", "invalid_description"])
def test_cc401_day_audit_keeps_unresolved_failures_visible(cc401_copied_store, case):
    import runpy
    audit = runpy.run_path(str(Path(__file__).parents[1] / "scripts/audit_publication_day_cc401.py"))["audit"]
    store = cc401_copied_store
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=FixtureTransport())
    row = coordinator.register_plan("work-1", _plan("substack_notes"))["registered"][0]
    if case in {"unreconciled_identity", "wrong_destination_identity"}:
        store.register_platform_dispatch(dispatch_id=row["dispatch_id"], message_id=row["message_id"],
            platform="substack_notes", status=DISPATCH_CONFIRMED, public_object_id="provider-123",
            public_object_url="https://example.com/post")
    if case == "wrong_destination_identity":
        store.register_reconciliation(reconciliation_id=row["reconciliation_id"], work_item_id="work-1",
            status="RECONCILED_CONFIRMED")
    for incident_id in ["first", "second"]:
        detail = {"destination": "substack_notes", "dispatch_id": row["dispatch_id"], "status": UNKNOWN_WRITE}
        if case == "wrong_destination_identity":
            detail.update(destination="linkedin", status=DEFINITE_NO_WRITE)
        if case == "ambiguous_composer":
            detail["safe_error_classification"] = "NEO_COMPOSER_PREPARATION_FAILED"
        store.register_incident(incident_id=incident_id, work_item_id="work-1", severity="DISPATCH_FAILURE",
            description="[]" if case == "invalid_description" else json.dumps(detail))
    with store.get_connection() as conn:
        conn.execute("UPDATE incidents SET created_at='2026-11-10T06:01:00+00:00'")
        conn.commit()
    result = audit(store.db_path, "2026-11-10", now=datetime(2026, 11, 11, 5, tzinfo=timezone.utc))
    assert result["status"] == "FAIL"
    if case == "invalid_description":
        assert result["invalid_incidents"] == ["first", "second"]
    else:
        assert result["active_destination_failure_incidents"] == {"linkedin" if case == "wrong_destination_identity" else "substack_notes": 2}


@pytest.fixture(autouse=True)
def fixture_platform_permissions(monkeypatch):
    """These state-machine replays use fake transports with simulated permission.

    Actual route prohibitions, including the coordinator's pre-readiness boundary,
    are exercised with the production map by test_platform_rules_cc393.py.
    """
    from live_contentops import neo_destination_handoff_v1 as handoff
    monkeypatch.setattr(handoff, "NON_API_AUTOMATION_PROHIBITED", {})

from live_contentops.destination_transport_registry_v1 import (
    REGISTRY_VERSION,
    READY_STATES,
    V1_QUALITY_PROBATION_POLICY_ID,
    V1_REQUIRED_DERIVATIVE_DESTINATIONS,
    V1_REQUIRED_PUBLICATION_DESTINATIONS,
    DestinationReadinessManager,
    canonical_transport_registry,
    registration_for_destination,
)
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.production_runtime_v1 import build_final_daily_app_production_runtime
from live_contentops.publication_coordinator_v1 import (
    ATTEMPT_STARTED,
    DEFINITE_NO_WRITE,
    DISPATCH_CONFIRMED,
    RECONCILIATION_PENDING,
    RECONCILED_ABSENT_SAFE_TO_RETRY,
    RECONCILED_CONFIRMED,
    RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE,
    DERIVATIVE_RECOVERY_RETRY_EXHAUSTED_NO_WRITE,
    DERIVATIVE_EXPIRED_STALE_NO_WRITE,
    FULL_V1_NINE_SURFACE_PUBLICATION_CONFIRMED,
    HOLD_FULL_V1_DISTRIBUTION_NOT_READY,
    PARTIAL_DISTRIBUTION_RECOVERY_REQUIRED,
    UNKNOWN_WRITE,
    DurablePublicationCoordinator,
    normalize_dispatch_result,
    normalize_readback_result,
)


class FixtureTransport:
    def __init__(self, *, raise_after_write: bool = False, ambiguous: bool = False) -> None:
        self.publish_calls: list[str] = []
        self.readback_calls: list[str] = []
        self.metrics_calls: list[dict] = []
        self.raise_after_write = raise_after_write
        self.ambiguous = ambiguous

    def publish(self, *, destination, intent, authorization_context):
        self.publish_calls.append(destination)
        if self.raise_after_write:
            raise TimeoutError("response lost after provider acceptance")
        public_url = (
            "https://capitalchronicle.substack.com/p/fixture-article-1"
            if destination == "substack"
            else None
            if destination == "discord"
            else f"https://example.test/{destination}/1"
        )
        return {
            "status": "SUCCESS",
            "id": f"{destination}-object-1",
            "public_url": public_url,
        }

    def readback(self, *, destination, public_object_id, public_object_url, intent):
        self.readback_calls.append(destination)
        if self.ambiguous:
            return {"status": "AMBIGUOUS", "verified": False}
        observed = public_object_id or f"{destination}-object-1"
        return {
            "status": "SUCCESS",
            "verified": True,
            "public_object_id": observed,
            "public_object_url": public_object_url,
        }

    def collect_metrics(self, *args, **kwargs):
        self.metrics_calls.append(dict(kwargs))
        return {
            "status": "COLLECTED",
            "metrics": {"shares": 1},
            "availability": {"shares": "AVAILABLE"},
            "source_identity": "fixture.first_party.visible_dom.v1",
        }


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _plan(*destinations: str):
    rows = []
    for destination in destinations:
        registration = registration_for_destination(destination)
        payload = f"exact payload for {destination} https://capitalchronicle.substack.com/p/test"
        rows.append({
            "destination": destination,
            "platform": registration.platform,
            "surface": registration.surface,
            "transport_type": registration.transport_type,
            "transport_registry_version": REGISTRY_VERSION,
            "payload": payload,
            "payload_hash": _sha(payload),
            "canonical_url": "https://capitalchronicle.substack.com/p/test",
            "canonical_url_dependency": registration.canonical_url_dependency,
            "expected_destination_identity": registration.expected_identity,
            "readiness_state": (
                "READY_AUTHENTICATED" if registration.transport_type == "EDGE_CDP"
                else "READY_NON_BROWSER_BINDING"
            ),
        })
    return {
        "schema_version": "contentops.publication_plan.v1",
        "plan_hash": _sha("fixed-plan:" + ",".join(destinations)),
        "story_identity": "story-1",
        "article_identity": "article-1",
        "publication_window": {"window_identity": "window-1"},
        "package_identity": "package-1",
        "transport_registry_version": REGISTRY_VERSION,
        "policy_mode_version": "AUTONOMOUS_DEFAULT:test.v1",
        "destinations": rows,
    }


def _quality_plan():
    plan = _plan(*V1_REQUIRED_PUBLICATION_DESTINATIONS)
    plan.update({
        "quality_probation_policy_id": V1_QUALITY_PROBATION_POLICY_ID,
        "full_v1_distribution_required": True,
        "required_publication_destinations": list(
            V1_REQUIRED_PUBLICATION_DESTINATIONS
        ),
        "required_derivative_destinations": list(
            V1_REQUIRED_DERIVATIVE_DESTINATIONS
        ),
        "skipped_derivative_destinations": [],
    })
    return plan


def _coordinator(tmp_path: Path, runtime=None, readiness=None, readiness_manager=None):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    store.create_work_item(
        story_id="story-1", title="Controlled publication coordinator fixture",
        target_surface="MULTI_PLATFORM", work_item_id="work-1",
        actor_ref="controlled_test", correlation_id="correlation-1",
    )
    transport = runtime or FixtureTransport()
    states = readiness or {}
    provider = lambda destination: {  # noqa: E731
        "readiness_state": states.get(
            destination,
            "READY_AUTHENTICATED" if registration_for_destination(destination).transport_type == "EDGE_CDP"
            else "READY_NON_BROWSER_BINDING",
        )
    }
    return store, transport, DurablePublicationCoordinator(
        store=store, transport_runtime=transport, readiness_provider=provider,
        readiness_manager=readiness_manager,
    )


def _set_mode(store, mode):
    control = store.get_operating_control()
    store.update_operating_control(
        expected_state_version=control["state_version"], operating_mode=mode,
        control_source="CONTROLLED_TEST",
    )


def test_simultaneous_api_dispatchers_cross_provider_boundary_only_once(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    store, transport, coordinator = _coordinator(tmp_path)
    registered = coordinator.register_plan("work-1", _plan("telegram"))["registered"][0]
    message = store.get_outbox_message(registered["message_id"])
    gate = Barrier(2)
    def ready(*_):
        gate.wait(timeout=10)
        return "READY_NON_BROWSER_BINDING"
    coordinator._readiness = ready
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(coordinator._dispatch_message, message, canonical_url=None) for _ in range(2)]
        outcomes = [f.result(timeout=20) for f in futures]
    assert transport.publish_calls == ["telegram"]
    assert sum(r["publish_called"] is True for r in outcomes) == 1
    assert any(r.get("reason_code") == "EXACT_DISPATCH_ALREADY_CLAIMED" for r in outcomes)


@pytest.mark.parametrize("invalid", [None, "text", "account", "photo", "removal", "stale"])
def test_verified_duplicate_survivor_preserves_removed_identity_and_counts_once(tmp_path, monkeypatch, invalid):
    from datetime import timedelta
    import live_contentops._eight_platform_substack_first_pipeline_impl_v1 as pipeline
    from live_contentops.publication_coordinator_v1 import EXTERNAL_REMOVAL_REPORTED_NO_RETRY
    from live_contentops.native_desktop_publication_v1 import publication_projection
    store, transport, coordinator = _coordinator(tmp_path)
    plan = _plan("substack", "telegram")
    canonical = "https://capitalchronicle.substack.com/p/fixture-article-1"
    payload = "Exact retained report. " + canonical
    for item in plan["destinations"]:
        if item["destination"] == "telegram": item.update(payload=payload, payload_hash=_sha(payload))
    coordinator.execute_plan("work-1", plan)
    original = next(d for d in store.list_platform_dispatches() if d["platform"] == "telegram")
    monkeypatch.setattr(pipeline, "_durable_intent_inputs", lambda _: {"media_assets": [{"sha256": "original-photo"}],
        "payloads": {"telegram": {"text": payload}}})
    proof = {"public_object_id": "72", "public_object_url": "https://t.me/CapitalChronicle/72", "observed_identity": "@CapitalChronicle",
        "observed_text": payload, "photo_pixels_inspected": True, "media_sha256": "original-photo", "canonical_url": canonical,
        "removed_object_id": original["public_object_id"], "removed_object_absence_verified": True,
        "tool_name": "mcp__browseros_neo__run", "owner_authority_ref": "controlled-human-instruction",
        "observation_ref": "controlled-public-readback", "observation_source": "Actual controlled specimen",
        "observed_at_utc": datetime.now(timezone.utc).isoformat()}
    for case, change in {"text": {"observed_text": "Other story"}, "account": {"observed_identity": "@Other"},
        "photo": {"media_sha256": "changed"}, "removal": {"removed_object_absence_verified": False},
        "stale": {"observed_at_utc": (datetime.now(timezone.utc)-timedelta(hours=1)).isoformat()}}.items():
        if invalid == case: proof.update(change)
    writes = list(transport.publish_calls)
    if invalid:
        with pytest.raises(ValueError, match="EXACT_CURRENT_DUPLICATE_SURVIVOR_PROOF_REQUIRED"):
            coordinator.reconcile_existing_duplicate_survivor(original["dispatch_id"], observation=proof)
        assert store.get_platform_dispatch(original["dispatch_id"])["status"] == DISPATCH_CONFIRMED
    else:
        adopted = coordinator.reconcile_existing_duplicate_survivor(original["dispatch_id"], observation=proof)
        assert coordinator.reconcile_existing_duplicate_survivor(original["dispatch_id"], observation=proof)["reused"]
        old = store.get_platform_dispatch(original["dispatch_id"])
        assert old["public_object_id"] == original["public_object_id"] and old["status"] == EXTERNAL_REMOVAL_REPORTED_NO_RETRY
        state = coordinator.publication_state("work-1", plan)
        assert state["per_destination"]["telegram"]["public_object_id"] == "72"
        assert state["derivative_confirmed_count"] == 1
        store.register_outbox_message(message_id="native-binding-controlled", work_item_id="work-1",
            destination="internal:native-publication-binding", payload=json.dumps({"run_id":"work-1","plan_hash":plan["plan_hash"]}))
        projection = publication_projection(store.list_outbox_messages(), store.list_platform_dispatches(),
            store.get_reconciliations_for_work_item("work-1"), run_id="work-1")
        assert next(d for d in projection["destinations"] if d["destination"]=="telegram")["public_object_id"] == "72"
        assert coordinator.readback_existing_dispatch(adopted["dispatch_id"])["reconciliation_status"] == RECONCILED_CONFIRMED
        assert store.get_platform_dispatch(original["dispatch_id"])["status"] == EXTERNAL_REMOVAL_REPORTED_NO_RETRY
    assert transport.publish_calls == writes


def test_registry_locks_surface_transport_and_browser_roles():
    registry = canonical_transport_registry()
    assert registry["publishing_cdp_port"] == 9223
    assert registry["ingestion_only_cdp_port"] == 9222
    assert registry["chrome_publishing_allowed"] is False
    assert registry["silent_transport_fallback_allowed"] is False
    assert registration_for_destination("youtube").surface == "YOUTUBE_COMMUNITY_POST"
    assert registration_for_destination("youtube").transport_type == "BROWSEROS_NEO_MCP"
    assert V1_REQUIRED_DERIVATIVE_DESTINATIONS == (
        "telegram", "x", "discord", "linkedin", "facebook_page",
        "instagram_business", "threads", "youtube",
    )
    assert set(V1_REQUIRED_PUBLICATION_DESTINATIONS) == {
        "substack", "telegram", "x", "discord", "linkedin", "facebook_page",
        "instagram_business", "threads", "youtube",
    }
    assert not {"tiktok", "youtube_video", "youtube_short"}.intersection(
        V1_REQUIRED_PUBLICATION_DESTINATIONS
    )


def test_discovered_write_identity_can_clear_unknown_when_original_id_was_missing():
    result = normalize_readback_result(
        {
            "status": "X_ROOT_RECONCILED_REPLY_CHAIN_INCOMPLETE",
            "write_exists": True,
            "post_id": "2089681225246233006",
            "public_url": "https://x.com/Capitalnicle/status/2089681225246233006",
        },
        public_object_id=None,
    )

    assert result["identity_match"] is True
    assert result["write_exists"] is True
    assert result["verified"] is False


def test_quality_probation_derivative_readiness_hold_does_not_veto_canonical(
    tmp_path,
):
    store, transport, coordinator = _coordinator(
        tmp_path, readiness={"threads": "AUTH_INVALID"}
    )

    result = coordinator.execute_plan("work-1", _quality_plan())

    assert result["canonical_article_real_published"] is True
    assert result["distribution_status"] == PARTIAL_DISTRIBUTION_RECOVERY_REQUIRED
    assert result["transaction_classification"] == (
        PARTIAL_DISTRIBUTION_RECOVERY_REQUIRED
    )
    assert result["quality_preflight"]["readiness_blockers"] == []
    assert result["quality_preflight"]["derivative_readiness_deferred"] == [
        d for d in V1_REQUIRED_DERIVATIVE_DESTINATIONS if d != "x"
    ]
    assert result["recovery_required_destinations"] == ["threads"]
    assert result["per_destination"]["threads"]["status"] == "AUTH_INVALID"
    assert result["per_destination"]["threads"]["publish_called"] is False
    assert result["registered"]
    assert result["outbox_count"] == 10  # nine V1 surfaces plus the LinkedIn company-page copy
    assert transport.publish_calls[0] == "substack"
    assert "threads" not in transport.publish_calls
    assert len(transport.publish_calls) == 9  # canonical + eight derivatives + company, one held
    assert len(store.list_outbox_messages()) == 10


def test_delivery_media_preparation_is_after_canonical_readback_and_before_derivatives(
    tmp_path,
):
    class PreparingTransport(FixtureTransport):
        def __init__(self):
            super().__init__()
            self.prepare_calls = []

        def prepare_delivery_media(self, **kwargs):
            assert self.publish_calls == ["substack"]
            assert self.readback_calls == ["substack"]
            self.prepare_calls.append(kwargs)
            return {
                "status": "CLOUDINARY_DELIVERY_MEDIA_READY",
                "provider_calls": 1,
                "public_write_performed": False,
            }

    transport = PreparingTransport()
    _store_value, _transport, coordinator = _coordinator(
        tmp_path, runtime=transport
    )

    result = coordinator.execute_plan("work-1", _quality_plan())

    assert result["distribution_status"] == FULL_V1_NINE_SURFACE_PUBLICATION_CONFIRMED
    assert len(transport.prepare_calls) == 1
    preconditions = transport.prepare_calls[0]["preconditions"]
    assert preconditions == {
        "canonical_publication_status": RECONCILED_CONFIRMED,
        "unknown_write_count": 0,
    }
    assert transport.publish_calls[0] == "substack"


def test_delivery_media_preparation_failure_is_destination_local_after_canonical(tmp_path):
    class FailingPreparationTransport(FixtureTransport):
        def __init__(self):
            super().__init__()
            self.prepare_calls = 0

        def prepare_delivery_media(self, **_kwargs):
            self.prepare_calls += 1
            if self.prepare_calls > 1:
                return {
                    "status": "CLOUDINARY_DELIVERY_MEDIA_READY",
                    "provider_calls": 1,
                    "public_write_performed": False,
                }
            return {
                "status": "BLOCKED_CLOUDINARY_HOSTED_MEDIA_MISMATCH",
                "provider_calls": 1,
                "public_write_performed": False,
            }

    store, transport, coordinator = _coordinator(
        tmp_path, runtime=FailingPreparationTransport()
    )

    plan = _quality_plan()
    for row in plan["destinations"]:
        if row["destination"] == "instagram_business":
            row["delivery_media_required"] = True
    result = coordinator.execute_plan("work-1", plan)

    assert result["distribution_status"] == PARTIAL_DISTRIBUTION_RECOVERY_REQUIRED
    assert result["canonical_article_status"] == "REAL_PUBLISHED"
    assert result["canonical_article_real_published"] is True
    assert result["registered"]
    assert result["outbox_count"] == 10  # nine V1 surfaces plus the LinkedIn company-page copy
    assert result["recovery_required_destinations"] == ["instagram_business"]
    assert result["per_destination"]["instagram_business"][
        "destination_local_hold"
    ] is True
    assert result["per_destination"]["instagram_business"]["publish_called"] is False
    assert transport.publish_calls[0] == "substack"
    assert "instagram_business" not in transport.publish_calls
    assert len(store.list_outbox_messages()) == 10  # plus the LinkedIn company-page copy

    recovery = coordinator.recover_pending()
    assert recovery["backlog_remaining"] == 0
    assert recovery["per_destination"]["instagram_business"]["status"] == (
        DISPATCH_CONFIRMED
    )
    assert transport.publish_calls.count("instagram_business") == 1


def test_quality_probation_full_nine_surface_confirmation(tmp_path):
    _store_value, transport, coordinator = _coordinator(tmp_path)

    result = coordinator.execute_plan("work-1", _quality_plan())

    assert result["distribution_status"] == FULL_V1_NINE_SURFACE_PUBLICATION_CONFIRMED
    assert result["transaction_classification"] == FULL_V1_NINE_SURFACE_PUBLICATION_CONFIRMED
    assert result["derivative_attempted_count"] == len(V1_REQUIRED_DERIVATIVE_DESTINATIONS)
    assert result["derivative_confirmed_count"] == len(V1_REQUIRED_DERIVATIVE_DESTINATIONS)
    assert result["recovery_required_destinations"] == []
    assert transport.publish_calls[0] == "substack"
    # The LinkedIn company-page copy goes with the eight derivatives (4 Nov).
    assert set(transport.publish_calls[1:]) == set(V1_REQUIRED_DERIVATIVE_DESTINATIONS) | {"linkedin_company"}


def test_quality_probation_postcanonical_failure_preserves_canonical_and_continues(
    tmp_path,
):
    class OneFailureTransport(FixtureTransport):
        def publish(self, *, destination, intent, authorization_context):
            if destination == "linkedin":
                self.publish_calls.append(destination)
                return {"status": "DEFINITE_NO_WRITE", "definite_no_write": True}
            return super().publish(
                destination=destination,
                intent=intent,
                authorization_context=authorization_context,
            )

    store, transport, coordinator = _coordinator(
        tmp_path, runtime=OneFailureTransport()
    )

    result = coordinator.execute_plan("work-1", _quality_plan())

    assert result["canonical_article_real_published"] is True
    assert result["distribution_status"] == PARTIAL_DISTRIBUTION_RECOVERY_REQUIRED
    assert result["recovery_required_destinations"] == ["linkedin"]
    assert result["per_destination"]["linkedin"]["reconciliation_status"] == (
        RECONCILED_ABSENT_SAFE_TO_RETRY
    )
    assert set(transport.publish_calls) == set(V1_REQUIRED_PUBLICATION_DESTINATIONS) | {"linkedin_company"}
    assert len(store.list_platform_dispatches()) == 10  # plus the company-page copy


def test_unresolved_quality_distribution_obligation_blocks_new_canonical(tmp_path):
    class PendingLinkedInReadback(FixtureTransport):
        def readback(self, *, destination, public_object_id, public_object_url, intent):
            if destination == "linkedin":
                self.readback_calls.append(destination)
                return {"status": "AMBIGUOUS", "verified": False}
            return super().readback(
                destination=destination,
                public_object_id=public_object_id,
                public_object_url=public_object_url,
                intent=intent,
            )

    _store_value, transport, coordinator = _coordinator(
        tmp_path, runtime=PendingLinkedInReadback()
    )
    first = coordinator.execute_plan("work-1", _quality_plan())

    blocked = coordinator.execute_plan("work-2", _quality_plan())

    assert first["distribution_status"] == PARTIAL_DISTRIBUTION_RECOVERY_REQUIRED
    assert blocked["distribution_status"] == "BLOCKED_SAFE_RECOVERY_BACKLOG_REMAINS"
    assert blocked["recovery_preflight"]["backlog_remaining"] == 1
    assert blocked["recovery_preflight"]["backlog_remaining_obligations"][0][
        "destination"
    ] == "linkedin"
    assert transport.publish_calls.count("substack") == 1


def test_owner_quarantined_legacy_unknown_is_untouched_and_does_not_block_fresh_plan(
    tmp_path,
):
    class QuarantineProofTransport(FixtureTransport):
        def __init__(self):
            super().__init__()
            self.readback_work_items = []
            self.prepare_calls = []

        def readback(self, *, destination, public_object_id, public_object_url, intent):
            self.readback_work_items.append(str(intent.get("work_item_id") or ""))
            return super().readback(
                destination=destination,
                public_object_id=public_object_id,
                public_object_url=public_object_url,
                intent=intent,
            )

        def prepare_delivery_media(self, **kwargs):
            self.prepare_calls.append(kwargs)
            return {
                "status": "CLOUDINARY_DELIVERY_MEDIA_READY",
                "provider_calls": 1,
                "public_write_performed": False,
            }

    legacy_work_item = "legacy-owner-quarantined-unknown"
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    for work_item_id in (legacy_work_item, "legacy-noncanonical", "fresh-work"):
        store.create_work_item(
            story_id=f"story-{work_item_id}",
            title="Controlled quarantine fixture",
            target_surface="MULTI_PLATFORM",
            work_item_id=work_item_id,
            actor_ref="controlled_test",
            correlation_id=f"correlation-{work_item_id}",
        )
    transport = QuarantineProofTransport()
    readiness = lambda destination: {  # noqa: E731
        "readiness_state": (
            "READY_AUTHENTICATED"
            if registration_for_destination(destination).transport_type == "EDGE_CDP"
            else "READY_NON_BROWSER_BINDING"
        )
    }
    setup = DurablePublicationCoordinator(
        store=store,
        transport_runtime=transport,
        readiness_provider=readiness,
    )
    legacy_registration = setup.register_plan(legacy_work_item, _quality_plan())
    legacy_substack = next(
        row
        for row in legacy_registration["registered"]
        if row["destination"] == "substack"
    )
    store.register_platform_dispatch(
        dispatch_id=legacy_substack["dispatch_id"],
        message_id=legacy_substack["message_id"],
        platform="substack",
        status=UNKNOWN_WRITE,
        public_object_id="213355736",
    )
    store.set_outbox_status(legacy_substack["message_id"], UNKNOWN_WRITE)
    store.register_reconciliation(
        reconciliation_id=legacy_substack["reconciliation_id"],
        work_item_id=legacy_work_item,
        status=RECONCILIATION_PENDING,
    )
    store.register_outbox_message(
        message_id="legacy-noncanonical-ready",
        work_item_id="legacy-noncanonical",
        destination="substack",
        payload=json.dumps({"historical_schema": "pre_coordinator"}),
        status="READY",
    )
    dispatch_before = dict(
        store.get_platform_dispatch(legacy_substack["dispatch_id"])
    )
    outbox_before = [
        dict(row)
        for row in store.list_outbox_messages()
        if row["work_item_id"] == legacy_work_item
    ]
    reconciliation_before = store.get_reconciliations_for_work_item(legacy_work_item)
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    coordinator = DurablePublicationCoordinator(
        store=store,
        transport_runtime=transport,
        readiness_provider=readiness,
        recovery_quarantined_work_item_ids=(legacy_work_item,),
    )
    fresh_plan = _quality_plan()
    next(
        row
        for row in fresh_plan["destinations"]
        if row["destination"] == "instagram_business"
    )["delivery_media_required"] = True

    recovery = coordinator.recover_pending()
    result = coordinator.execute_plan("fresh-work", fresh_plan)

    assert result["distribution_status"] == FULL_V1_NINE_SURFACE_PUBLICATION_CONFIRMED
    assert recovery["backlog_remaining"] == 0
    assert recovery["recovery_quarantined_obligation_count"] == 10  # plus the company-page copy
    assert recovery["legacy_noncanonical_rows_skipped"] == 1
    assert transport.prepare_calls[0]["preconditions"]["unknown_write_count"] == 0
    assert legacy_work_item not in transport.readback_work_items
    assert store.get_platform_dispatch(legacy_substack["dispatch_id"]) == dispatch_before
    assert [
        dict(row)
        for row in store.list_outbox_messages()
        if row["work_item_id"] == legacy_work_item
    ] == outbox_before
    assert store.get_reconciliations_for_work_item(legacy_work_item) == (
        reconciliation_before
    )

    blocked = coordinator.execute_plan(legacy_work_item, _quality_plan())
    assert blocked["distribution_status"] == "BLOCKED_RECOVERY_QUARANTINED_WORK_ITEM"
    assert blocked["public_write_performed"] is False


def test_recovery_delivery_media_ignores_only_owner_quarantined_unknown(tmp_path):
    class PreparingTransport(FixtureTransport):
        def __init__(self):
            super().__init__()
            self.prepare_calls = []

        def prepare_delivery_media(self, **kwargs):
            self.prepare_calls.append(kwargs)
            return {
                "status": "CLOUDINARY_DELIVERY_MEDIA_READY",
                "provider_calls": 1,
                "public_write_performed": False,
            }

    transport = PreparingTransport()
    store, _transport, setup = _coordinator(tmp_path, runtime=transport)
    legacy_work_item = "owner-quarantined-unknown"
    recovery_work_item = "recovery-work"
    for work_item_id in (legacy_work_item, recovery_work_item):
        store.create_work_item(
            story_id=f"story-{work_item_id}",
            title="Controlled recovery quarantine fixture",
            target_surface="MULTI_PLATFORM",
            work_item_id=work_item_id,
            actor_ref="controlled_test",
            correlation_id=f"correlation-{work_item_id}",
        )
    legacy = setup.register_plan(legacy_work_item, _plan("substack"))["registered"][0]
    store.register_platform_dispatch(
        dispatch_id=legacy["dispatch_id"],
        message_id=legacy["message_id"],
        platform="substack",
        status=UNKNOWN_WRITE,
        public_object_id="213355736",
    )
    store.set_outbox_status(legacy["message_id"], UNKNOWN_WRITE)
    plan = _quality_plan()
    next(
        row
        for row in plan["destinations"]
        if row["destination"] == "instagram_business"
    )["delivery_media_required"] = True
    registered = setup.register_plan(recovery_work_item, plan)["registered"]
    canonical = next(row for row in registered if row["destination"] == "substack")
    canonical_url = "https://capitalchronicle.substack.com/p/recovery-work"
    store.register_platform_dispatch(
        dispatch_id=canonical["dispatch_id"],
        message_id=canonical["message_id"],
        platform="substack",
        status=DISPATCH_CONFIRMED,
        public_object_id="recovery-substack-object",
        public_object_url=canonical_url,
    )
    store.set_outbox_status(canonical["message_id"], DISPATCH_CONFIRMED)
    store.register_reconciliation(
        reconciliation_id=canonical["reconciliation_id"],
        work_item_id=recovery_work_item,
        status=RECONCILED_CONFIRMED,
    )
    coordinator = DurablePublicationCoordinator(
        store=store,
        transport_runtime=transport,
        readiness_provider=lambda destination: {
            "readiness_state": (
                "READY_AUTHENTICATED"
                if registration_for_destination(destination).transport_type == "EDGE_CDP"
                else "READY_NON_BROWSER_BINDING"
            )
        },
        recovery_quarantined_work_item_ids=(legacy_work_item,),
    )

    recovery = coordinator.recover_pending()

    assert recovery["backlog_remaining"] == 0
    assert recovery["publish_calls"] == 9  # eight derivatives plus the company-page copy
    assert len(transport.prepare_calls) == 1
    assert transport.prepare_calls[0]["preconditions"]["unknown_write_count"] == 0
    assert store.get_platform_dispatch(legacy["dispatch_id"])["status"] == UNKNOWN_WRITE


def test_stable_provider_id_confirms_distribution_with_readback_limitation(tmp_path):
    class LimitedLinkedInReadback(FixtureTransport):
        def readback(self, *, destination, public_object_id, public_object_url, intent):
            if destination == "linkedin":
                self.readback_calls.append(destination)
                return {
                    "status": "READBACK_CAPABILITY_LIMITED",
                    "verified": False,
                    "write_exists": True,
                    "public_object_id": public_object_id,
                }
            return super().readback(
                destination=destination,
                public_object_id=public_object_id,
                public_object_url=public_object_url,
                intent=intent,
            )

    store, transport, coordinator = _coordinator(
        tmp_path, runtime=LimitedLinkedInReadback()
    )

    result = coordinator.execute_plan("work-1", _quality_plan())

    assert result["distribution_status"] == FULL_V1_NINE_SURFACE_PUBLICATION_CONFIRMED
    assert result["readback_limitation_destinations"] == ["linkedin"]
    linkedin = result["per_destination"]["linkedin"]
    assert linkedin["public_object_id"] == "linkedin-object-1"
    assert linkedin["public_object_url"] == "https://example.test/linkedin/1"
    dispatch = next(
        row for row in store.list_platform_dispatches() if row["platform"] == "linkedin"
    )
    metrics = coordinator.collect_metrics(
        dispatch["dispatch_id"], dispatch["public_object_id"], "DAILY"
    )
    assert metrics["status"] == "UNAVAILABLE"
    assert transport.metrics_calls == []


def test_metrics_collection_requires_exact_confirmed_reconciled_dispatch_binding(tmp_path):
    store, transport, coordinator = _coordinator(tmp_path)
    coordinator.execute_plan("work-1", _plan("substack"))
    dispatch = next(row for row in store.list_platform_dispatches() if row["platform"] == "substack")

    result = coordinator.collect_metrics(
        dispatch["dispatch_id"], dispatch["public_object_id"], "DAILY"
    )

    assert result["status"] == "COLLECTED"
    assert transport.metrics_calls == [{
        "destination": "substack",
        "dispatch_id": dispatch["dispatch_id"],
        "public_object_id": dispatch["public_object_id"],
        "public_object_url": dispatch["public_object_url"],
        "public_object_url_hash": dispatch["public_object_url_hash"],
        "observation_window": "DAILY",
    }]

    blocked = coordinator.collect_metrics(
        dispatch["dispatch_id"], "wrong-object", "DAILY"
    )
    assert blocked["status"] == "UNAVAILABLE"
    assert len(transport.metrics_calls) == 1


def test_case_a_api_success_and_case_b_cdp_success(tmp_path):
    store, transport, coordinator = _coordinator(tmp_path)
    result = coordinator.execute_plan("work-1", _plan("telegram", "substack"))
    assert result["per_destination"]["telegram"]["status"] == DISPATCH_CONFIRMED
    assert result["per_destination"]["substack"]["reconciliation_status"] == RECONCILED_CONFIRMED
    assert transport.publish_calls == ["substack", "telegram"]
    assert result["distribution_status"] == "CANONICAL_PUBLISHED_DISTRIBUTION_COMPLETE"

    recovery = coordinator.recover_pending()
    assert recovery["publish_calls"] == 0
    assert sorted(transport.publish_calls) == ["substack", "telegram"]
    assert all(row["status"] == DISPATCH_CONFIRMED for row in store.list_platform_dispatches())
    assert result["canonical_article_real_published"] is True
    assert result["canonical_article_status"] == "REAL_PUBLISHED"

    recovery = coordinator.recover_pending()
    assert recovery["readbacks"] == 0
    assert all(
        row["status"] == RECONCILED_CONFIRMED
        for row in store.get_reconciliations_for_work_item("work-1")
    )


def test_complete_v1_transaction_attempts_all_eight_ready_derivatives_once(tmp_path):
    destinations = (
        "substack", "telegram", "x", "discord", "linkedin", "facebook_page",
        "instagram_business", "threads", "youtube",
    )
    store, transport, coordinator = _coordinator(tmp_path)

    result = coordinator.execute_plan("work-1", _plan(*destinations))
    coordinator.execute_plan("work-1", _plan(*destinations))

    assert result["canonical_article_real_published"] is True
    assert result["distribution_status"] == "CANONICAL_PUBLISHED_DISTRIBUTION_COMPLETE"
    assert set(result["per_destination"]) == set(destinations)
    assert result["derivative_attempted_count"] == len(V1_REQUIRED_DERIVATIVE_DESTINATIONS)
    assert result["derivative_confirmed_count"] == len(V1_REQUIRED_DERIVATIVE_DESTINATIONS)
    assert transport.publish_calls.count("substack") == 1
    assert all(transport.publish_calls.count(destination) == 1 for destination in destinations)
    assert len(store.list_platform_dispatches()) == len(destinations)


def test_one_derivative_failure_does_not_block_remaining_ready_derivatives(tmp_path):
    class OneFailureTransport(FixtureTransport):
        def publish(self, *, destination, intent, authorization_context):
            if destination == "linkedin":
                self.publish_calls.append(destination)
                return {"status": "DEFINITE_NO_WRITE", "definite_no_write": True}
            return super().publish(
                destination=destination,
                intent=intent,
                authorization_context=authorization_context,
            )

    runtime = OneFailureTransport()
    _store_value, transport, coordinator = _coordinator(tmp_path, runtime=runtime)
    result = coordinator.execute_plan(
        "work-1", _plan("substack", "linkedin", "telegram", "x")
    )

    assert result["canonical_article_real_published"] is True
    assert result["per_destination"]["linkedin"]["status"] == DEFINITE_NO_WRITE
    assert result["per_destination"]["telegram"]["status"] == DISPATCH_CONFIRMED
    assert result["per_destination"]["x"]["status"] == DISPATCH_CONFIRMED
    assert result["distribution_status"] == "CANONICAL_PUBLISHED_READY_FANOUT_ATTEMPTED"
    assert sorted(transport.publish_calls) == ["linkedin", "substack", "telegram", "x"]


def test_exact_write_exists_clears_unknown_without_claiming_strict_reconciliation(tmp_path):
    class ExistsButContentPendingTransport(FixtureTransport):
        def readback(self, *, destination, public_object_id, public_object_url, intent):
            return {
                "status": "FAILED_STRICT_CONTENT_READBACK",
                "verified": False,
                "write_exists": True,
                "public_object_id": public_object_id,
            }

    store, _transport, coordinator = _coordinator(
        tmp_path, runtime=ExistsButContentPendingTransport()
    )
    registered = coordinator.register_plan("work-1", _plan("threads"))["registered"][0]
    store.register_platform_dispatch(
        dispatch_id=registered["dispatch_id"],
        message_id=registered["message_id"],
        platform="threads",
        status=UNKNOWN_WRITE,
        public_object_id="exact-thread-object",
    )
    store.set_outbox_status(registered["message_id"], UNKNOWN_WRITE)

    result = coordinator.recover_pending()

    assert result["readbacks"] == 1
    assert store.get_platform_dispatch(registered["dispatch_id"])["status"] == (
        DISPATCH_CONFIRMED
    )
    assert store.get_reconciliations_for_work_item("work-1")[0]["status"] == (
        RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE
    )
    assert coordinator.recover_pending()["readbacks"] == 0


def test_persisted_verified_readback_replay_restores_confirmed_without_provider_call(tmp_path):
    store, transport, coordinator = _coordinator(tmp_path)
    result = coordinator.execute_plan("work-1", _plan("telegram"))
    dispatch = store.list_platform_dispatches()[0]
    reconciliation = store.get_reconciliations_for_work_item("work-1")[0]
    assert result["per_destination"]["telegram"]["reconciliation_status"] == (
        RECONCILED_CONFIRMED
    )
    store.set_reconciliation_status(
        reconciliation["reconciliation_id"], RECONCILIATION_PENDING
    )
    calls_before = len(transport.readback_calls)

    replay = coordinator.replay_persisted_verified_readback(dispatch["dispatch_id"])

    assert replay == {"status": RECONCILED_CONFIRMED, "provider_calls": 0}
    assert len(transport.readback_calls) == calls_before
    assert store.get_reconciliations_for_work_item("work-1")[0]["status"] == (
        RECONCILED_CONFIRMED
    )


def test_substack_confirmed_with_unready_derivative_is_real_partial_publication(tmp_path):
    _store, transport, coordinator = _coordinator(tmp_path)
    plan = _plan("substack")
    plan["skipped_derivative_destinations"] = [
        {
            "destination": "linkedin",
            "surface": registration_for_destination("linkedin").surface,
            "readiness_state": "REAUTH_REQUIRED",
            "disposition": "SKIPPED_NOT_READY",
            "attempted": False,
            "canonical_truth_affected": False,
        }
    ]

    result = coordinator.execute_plan("work-1", plan)

    assert result["canonical_article_real_published"] is True
    assert result["canonical_url"] == (
        "https://capitalchronicle.substack.com/p/fixture-article-1"
    )
    assert result["distribution_status"] == "CANONICAL_PUBLISHED_READY_FANOUT_ATTEMPTED"
    assert result["per_destination"]["linkedin"]["status"] == "SKIPPED_NOT_READY"
    assert result["derivative_skipped_count"] == 1
    assert transport.publish_calls == ["substack"]


def test_substack_without_valid_canonical_url_is_not_real_and_derivatives_wait(tmp_path):
    class InvalidCanonicalTransport(FixtureTransport):
        def publish(self, *, destination, intent, authorization_context):
            result = super().publish(
                destination=destination,
                intent=intent,
                authorization_context=authorization_context,
            )
            if destination == "substack":
                result["public_url"] = "https://example.test/not-canonical"
            return result

    runtime = InvalidCanonicalTransport()
    _store, transport, coordinator = _coordinator(tmp_path, runtime=runtime)
    plan = _plan("substack", "telegram")
    for row in plan["destinations"]:
        row.pop("canonical_url", None)

    result = coordinator.execute_plan("work-1", plan)

    assert result["canonical_article_real_published"] is False
    assert result["canonical_url"] is None
    assert result["canonical_publication_status"] == "CANONICAL_NOT_CONFIRMED"
    assert result["per_destination"]["substack"]["reconciliation_status"] == (
        RECONCILIATION_PENDING
    )
    assert result["per_destination"]["telegram"]["status"] == "WAITING_CANONICAL_URL"
    assert transport.publish_calls == ["substack"]


def test_substack_2xx_outcome_is_evidence_only_and_strict_unknown_still_blocks_derivatives(
    tmp_path,
):
    class OutcomeEvidenceTransport(FixtureTransport):
        def publish(self, *, destination, intent, authorization_context):
            self.publish_calls.append(destination)
            assert destination == "substack"
            dispatch_identity = authorization_context["dispatch_attempt_identity"]
            return {
                "status": "UNKNOWN_SUBSTACK_PUBLICATION_REQUIRES_DRAFT_ID_RECONCILIATION",
                "draft_id": "210865567",
                "public_url": None,
                "provider_outcome": {
                    "schema": "contentops.substack_post_write_outcome.v1",
                    "draft_id": "210865567",
                    "dispatch_identity": dispatch_identity,
                    "request_observed": True,
                    "request_started_at": "2026-08-30T10:00:00+00:00",
                    "completion_observed": True,
                    "completion_observed_at": "2026-08-30T10:00:01+00:00",
                    "status_class": "2XX",
                    "reason": "HTTP_RESPONSE_OBSERVED",
                },
            }

        def readback(self, *, destination, public_object_id, public_object_url, intent):
            self.readback_calls.append(destination)
            return {
                "status": "AMBIGUOUS",
                "verified": False,
                "public_object_id": public_object_id,
            }

    runtime = OutcomeEvidenceTransport()
    store, transport, coordinator = _coordinator(tmp_path, runtime=runtime)
    plan = _plan("substack", "telegram")
    for row in plan["destinations"]:
        row.pop("canonical_url", None)

    result = coordinator.execute_plan("work-1", plan)

    substack = next(
        row for row in store.list_platform_dispatches() if row["platform"] == "substack"
    )
    assert substack["status"] == UNKNOWN_WRITE
    assert substack["public_object_id"] == "210865567"
    assert substack["public_object_url"] is None
    assert result["canonical_article_real_published"] is False
    assert result["canonical_url"] is None
    assert result["per_destination"]["telegram"]["status"] == "WAITING_CANONICAL_URL"
    assert transport.publish_calls == ["substack"]
    readbacks = store.list_readbacks_for_dispatch(substack["dispatch_id"])
    assert len(readbacks) == 1
    packet = json.loads(readbacks[0]["readback_data"])
    assert packet["provider_outcome"]["status_class"] == "2XX"
    assert packet["provider_outcome"]["dispatch_identity"] == substack["dispatch_id"]
    assert packet["readback"]["verified"] is False
    assert packet["readback"]["canonical_url_valid"] is False


def test_strict_readback_can_recover_valid_substack_url_and_idempotent_status(tmp_path):
    class ReadbackRecoversCanonicalTransport(FixtureTransport):
        def publish(self, *, destination, intent, authorization_context):
            result = super().publish(
                destination=destination,
                intent=intent,
                authorization_context=authorization_context,
            )
            if destination == "substack":
                result["public_url"] = None
            return result

        def readback(self, *, destination, public_object_id, public_object_url, intent):
            result = super().readback(
                destination=destination,
                public_object_id=public_object_id,
                public_object_url=public_object_url,
                intent=intent,
            )
            if destination == "substack":
                result["public_object_url"] = (
                    "https://capitalchronicle.substack.com/p/recovered-article-1"
                )
            return result

    runtime = ReadbackRecoversCanonicalTransport()
    store, transport, coordinator = _coordinator(tmp_path, runtime=runtime)
    plan = _plan("substack", "telegram")
    for row in plan["destinations"]:
        row.pop("canonical_url", None)

    first = coordinator.execute_plan("work-1", plan)
    second = coordinator.execute_plan("work-1", plan)

    assert first["canonical_article_real_published"] is True
    assert first["canonical_url"] == (
        "https://capitalchronicle.substack.com/p/recovered-article-1"
    )
    assert second["canonical_article_real_published"] is True
    assert second["canonical_url"] == first["canonical_url"]
    assert transport.publish_calls == ["substack", "telegram"]
    assert coordinator.recover_pending()["publish_calls"] == 0
    assert transport.publish_calls == ["substack", "telegram"]
    substack = next(
        row for row in store.list_platform_dispatches() if row["platform"] == "substack"
    )
    assert substack["public_object_url"] == first["canonical_url"]


@pytest.mark.parametrize("derivative_mode", ["definite_failure", "unknown_write"])
def test_derivative_failure_never_erases_reconciled_substack_truth(
    tmp_path, derivative_mode
):
    class DerivativeFailureTransport(FixtureTransport):
        def publish(self, *, destination, intent, authorization_context):
            if destination != "linkedin":
                return super().publish(
                    destination=destination,
                    intent=intent,
                    authorization_context=authorization_context,
                )
            self.publish_calls.append(destination)
            if derivative_mode == "unknown_write":
                raise TimeoutError("ambiguous derivative response")
            return {"status": "DEFINITE_NO_WRITE", "definite_no_write": True}

        def readback(self, *, destination, public_object_id, public_object_url, intent):
            if destination == "linkedin" and derivative_mode == "unknown_write":
                self.readback_calls.append(destination)
                return {"status": "AMBIGUOUS", "verified": False}
            return super().readback(
                destination=destination,
                public_object_id=public_object_id,
                public_object_url=public_object_url,
                intent=intent,
            )

    runtime = DerivativeFailureTransport()
    store, _transport, coordinator = _coordinator(tmp_path, runtime=runtime)
    plan = _plan("substack", "linkedin")
    for row in plan["destinations"]:
        row.pop("canonical_url", None)

    result = coordinator.execute_plan("work-1", plan)

    assert result["canonical_article_real_published"] is True
    assert result["canonical_article_status"] == "REAL_PUBLISHED"
    assert result["distribution_status"] == "CANONICAL_PUBLISHED_READY_FANOUT_ATTEMPTED"
    derivative = next(
        row for row in store.list_platform_dispatches() if row["platform"] == "linkedin"
    )
    if derivative_mode == "unknown_write":
        assert derivative["status"] == UNKNOWN_WRITE
        assert store.get_reconciliations_for_work_item("work-1")[-1]["status"] == (
            RECONCILIATION_PENDING
        )
    else:
        assert derivative["status"] == DEFINITE_NO_WRITE


@pytest.mark.parametrize("condition,allowed", [
    ("decision39", True), ("legacy", False), ("same_article", False),
    ("unknown_canonical", False), ("unverified_canonical", False),
    ("missing_readback", False), ("unbound_obligation", False),
    ("incomplete", True), ("incomplete_same_article", False),
    ("incomplete_wrong_id", False), ("incomplete_missing_url", False),
    ("incomplete_missing_proof", False),
    ("incomplete_legacy", False),
])
def test_decision39_prior_distribution_gap_keeps_unknown_write_and_allows_distinct_canonical(
    tmp_path, condition, allowed
):
    class PriorGap(FixtureTransport):
        def publish(self, *, destination, intent, authorization_context):
            if destination == "linkedin":
                self.publish_calls.append(destination)
                raise TimeoutError("CONTROLLED lost derivative return")
            result = super().publish(destination=destination, intent=intent,
                                     authorization_context=authorization_context)
            if destination == "substack":
                result.update(id="100" if intent["work_item_id"] == "work-1" else "200",
                    public_url="https://capitalchronicle.substack.com/p/" + intent["work_item_id"])
            return result

        def readback(self, *, destination, public_object_id, public_object_url, intent):
            if condition.startswith("incomplete") and destination == "substack" and intent["work_item_id"] == "work-1":
                return {"status": "BLOCKED", "verified": False,
                    "write_exists": condition != "incomplete_missing_proof",
                    "public_object_id": "wrong" if condition == "incomplete_wrong_id" else public_object_id,
                    "public_object_url": None if condition == "incomplete_missing_url" else public_object_url}
            if destination == "linkedin" or (condition in {"unknown_canonical", "unverified_canonical"}
                    and destination == "substack" and intent["work_item_id"] == "work-1"):
                return {"status": "AMBIGUOUS", "verified": False}
            return super().readback(destination=destination, public_object_id=public_object_id,
                public_object_url=public_object_url, intent=intent)

    # First prove the old canonical and create one genuinely ambiguous derivative.
    transport = PriorGap()
    store, _, coordinator = _coordinator(tmp_path, runtime=transport)
    original_readback = transport.readback
    if condition in {"unknown_canonical", "unverified_canonical"} or condition.startswith("incomplete"):
        transport.readback = lambda **kwargs: (FixtureTransport.readback(transport, **kwargs)
            if kwargs["destination"] == "substack" else original_readback(**kwargs))
    old_plan = _quality_plan()
    first = coordinator.execute_plan("work-1", old_plan)
    assert first["canonical_article_real_published"] is True
    transport.readback = original_readback
    old_ids = coordinator._ids("work-1", old_plan["plan_hash"], "substack")
    if condition.startswith("incomplete"):
        coordinator.readback_existing_dispatch(old_ids["dispatch_id"])
    if condition == "unknown_canonical":
        store.set_dispatch_status(old_ids["dispatch_id"], UNKNOWN_WRITE)
    elif condition == "unverified_canonical":
        store.set_reconciliation_status(old_ids["reconciliation_id"], RECONCILIATION_PENDING)
    elif condition == "missing_readback":
        with store.get_connection() as conn:
            conn.execute("DELETE FROM readbacks WHERE dispatch_id=?", (old_ids["dispatch_id"],))
    store.create_work_item(story_id="story-2", work_item_id="work-2", title="Next controlled article",
                           target_surface="MULTI_PLATFORM")
    new_plan = _plan("substack")
    new_plan.update(plan_hash=_sha("new-plan"), article_identity=("article-1"
                    if condition in {"same_article", "incomplete_same_article"} else "article-2"),
                    story_identity="story-2", package_identity="package-2")
    coordinator.allow_prior_confirmed_distribution = condition not in {"legacy", "incomplete_legacy"}
    if condition == "unbound_obligation":
        coordinator.recover_pending = lambda: {"backlog_remaining": 1, "publish_calls": 0}
    result = coordinator.execute_plan("work-2", new_plan)
    assert result["canonical_article_real_published"] is allowed
    assert transport.publish_calls.count("substack") == (2 if allowed else 1)
    assert transport.publish_calls.count("linkedin") == 1
    assert store.get_platform_dispatch(coordinator._ids("work-1", old_plan["plan_hash"], "linkedin")["dispatch_id"])["status"] == UNKNOWN_WRITE
    if condition == "incomplete":
        reconciliation = next(row for row in store.get_reconciliations_for_work_item("work-1")
            if row["reconciliation_id"] == old_ids["reconciliation_id"])
        assert reconciliation["status"] == RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE


def test_case_c_crash_before_adapter_safe_resume_once(tmp_path):
    store, transport, coordinator = _coordinator(tmp_path)
    coordinator.register_plan("work-1", _plan("telegram"))
    assert transport.publish_calls == []
    first = coordinator.recover_pending()
    second = coordinator.recover_pending()
    assert first["publish_calls"] == 1
    assert second["publish_calls"] == 0
    assert transport.publish_calls == ["telegram"]


def test_case_d_attempt_marker_restart_never_republishes(tmp_path):
    store, transport, coordinator = _coordinator(tmp_path)
    registered = coordinator.register_plan("work-1", _plan("telegram"))["registered"][0]
    store.register_platform_dispatch(
        dispatch_id=registered["dispatch_id"], message_id=registered["message_id"],
        platform="telegram", status=ATTEMPT_STARTED,
    )
    recovery = coordinator.recover_pending()
    assert recovery["marked_unknown"] == 1
    assert recovery["publish_calls"] == 0
    assert transport.publish_calls == []
    assert store.get_platform_dispatch(registered["dispatch_id"])["status"] == (
        DISPATCH_CONFIRMED
    )
    assert store.get_reconciliations_for_work_item("work-1")[0]["status"] == (
        RECONCILED_CONFIRMED
    )


def test_case_e_provider_accepted_response_lost_reconciles_without_duplicate(tmp_path):
    runtime = FixtureTransport(raise_after_write=True)
    store, transport, coordinator = _coordinator(tmp_path, runtime=runtime)
    result = coordinator.execute_plan("work-1", _plan("telegram"))
    row = result["per_destination"]["telegram"]
    assert row["status"] == DISPATCH_CONFIRMED
    assert row["reconciliation_status"] == RECONCILED_CONFIRMED
    assert result["unknown_write_detected"] is False
    coordinator.execute_plan("work-1", _plan("telegram"))
    assert transport.publish_calls == ["telegram"]
    assert store.list_platform_dispatches()[0]["public_object_id"] == "telegram-object-1"


def test_case_f_ambiguous_write_remains_pending_without_retry(tmp_path):
    runtime = FixtureTransport(raise_after_write=True, ambiguous=True)
    _store, transport, coordinator = _coordinator(tmp_path, runtime=runtime)
    result = coordinator.execute_plan("work-1", _plan("telegram"))
    assert result["per_destination"]["telegram"]["reconciliation_status"] == RECONCILIATION_PENDING
    coordinator.recover_pending()
    assert transport.publish_calls == ["telegram"]


def test_exact_draft_readback_clears_unknown_without_retry(tmp_path):
    class DraftAbsentTransport(FixtureTransport):
        def readback(self, *, destination, public_object_id, public_object_url, intent):
            self.readback_calls.append(destination)
            assert destination == "substack"
            assert public_object_id == "210796285"
            assert public_object_url is None
            return {
                "status": "SUBSTACK_DRAFT_CONFIRMED_NOT_PUBLIC",
                "verified": False,
                "write_absent": True,
                "public_object_id": public_object_id,
            }

    store, transport, coordinator = _coordinator(
        tmp_path, runtime=DraftAbsentTransport()
    )
    registered = coordinator.register_plan("work-1", _plan("substack"))["registered"][0]
    store.register_platform_dispatch(
        dispatch_id=registered["dispatch_id"],
        message_id=registered["message_id"],
        platform="substack",
        status=UNKNOWN_WRITE,
        public_object_id="210796285",
    )
    store.set_outbox_status(registered["message_id"], UNKNOWN_WRITE)

    first = coordinator.recover_pending()
    second = coordinator.recover_pending()

    assert first["readbacks"] == 1
    assert first["publish_calls"] == 0
    assert second["readbacks"] == 0
    assert transport.publish_calls == []
    assert transport.readback_calls == ["substack"]
    assert store.get_platform_dispatch(registered["dispatch_id"])["status"] == (
        RECONCILED_ABSENT_SAFE_TO_RETRY
    )
    assert next(
        row
        for row in store.list_outbox_messages()
        if row["message_id"] == registered["message_id"]
    )["status"] == RECONCILED_ABSENT_SAFE_TO_RETRY
    assert store.get_reconciliations_for_work_item("work-1")[0]["status"] == (
        RECONCILED_ABSENT_SAFE_TO_RETRY
    )


def test_case_g_expired_destination_isolated(tmp_path):
    _store, transport, coordinator = _coordinator(
        tmp_path, readiness={"linkedin": "REAUTH_REQUIRED"},
    )
    result = coordinator.execute_plan("work-1", _plan("linkedin", "telegram"))
    assert result["per_destination"]["linkedin"]["status"] == "REAUTH_REQUIRED"
    assert result["per_destination"]["telegram"]["status"] == DISPATCH_CONFIRMED
    assert transport.publish_calls == ["telegram"]


def test_explicit_substack_retry_requires_reconciled_absent_exact_draft(tmp_path):
    class ReconciledDraftTransport(FixtureTransport):
        def __init__(self):
            super().__init__()
            self.recovery_ids = []

        def publish(self, *, destination, intent, authorization_context):
            self.publish_calls.append(destination)
            self.recovery_ids.append(intent.get("recovery_public_object_id"))
            return {
                "status": "SUCCESS",
                "draft_id": "210915784",
                "public_url": "https://capitalchronicle.substack.com/p/recovered-article",
            }

        def readback(self, *, destination, public_object_id, public_object_url, intent):
            self.readback_calls.append(destination)
            if not self.publish_calls:
                return {"verified": False, "write_absent": True}
            return {
                "verified": True,
                "public_object_id": public_object_id,
                "public_object_url": public_object_url,
            }

    store, transport, coordinator = _coordinator(
        tmp_path, runtime=ReconciledDraftTransport()
    )
    registered = coordinator.register_plan("work-1", _plan("substack"))["registered"][0]
    store.register_platform_dispatch(
        dispatch_id=registered["dispatch_id"],
        message_id=registered["message_id"],
        platform="substack",
        status=UNKNOWN_WRITE,
        public_object_id="210915784",
    )
    store.set_outbox_status(registered["message_id"], UNKNOWN_WRITE)
    assert coordinator.recover_pending()["readbacks"] == 1

    first = coordinator.retry_reconciled_absent_substack(registered["dispatch_id"])
    second = coordinator.retry_reconciled_absent_substack(registered["dispatch_id"])

    assert first["status"] == DISPATCH_CONFIRMED
    assert first["reconciliation_status"] == RECONCILED_CONFIRMED
    assert second["publish_called"] is False
    assert transport.publish_calls == ["substack"]
    assert transport.recovery_ids == ["210915784"]


def test_next_run_drains_reconciled_absent_derivative_once_under_same_identity(tmp_path):
    store, transport, coordinator = _coordinator(tmp_path)
    registered = coordinator.register_plan("work-1", _plan("telegram"))["registered"][0]
    store.register_platform_dispatch(
        dispatch_id=registered["dispatch_id"],
        message_id=registered["message_id"],
        platform="telegram",
        status=RECONCILED_ABSENT_SAFE_TO_RETRY,
    )
    store.set_outbox_status(registered["message_id"], RECONCILED_ABSENT_SAFE_TO_RETRY)
    store.register_reconciliation(
        reconciliation_id=registered["reconciliation_id"],
        work_item_id="work-1",
        status=RECONCILED_ABSENT_SAFE_TO_RETRY,
    )

    first = coordinator.recover_pending()
    second = coordinator.recover_pending()

    assert first["publish_calls"] == 1
    assert first["per_destination"]["telegram"]["status"] == DISPATCH_CONFIRMED
    assert second["publish_calls"] == 0
    assert transport.publish_calls == ["telegram"]
    assert len(store.list_platform_dispatches()) == 1


def test_stale_absence_safe_derivative_expires_with_zero_write_and_history_retained(tmp_path):
    store, transport, coordinator = _coordinator(tmp_path)
    registered = coordinator.register_plan("work-1", _plan("telegram"))["registered"][0]
    store.register_platform_dispatch(
        dispatch_id=registered["dispatch_id"], message_id=registered["message_id"],
        platform="telegram", status=RECONCILED_ABSENT_SAFE_TO_RETRY,
    )
    store.set_outbox_status(registered["message_id"], RECONCILED_ABSENT_SAFE_TO_RETRY)
    store.register_reconciliation(
        reconciliation_id=registered["reconciliation_id"], work_item_id="work-1",
        status=RECONCILED_ABSENT_SAFE_TO_RETRY,
    )
    coordinator._clock = lambda: datetime(2030, 1, 1, tzinfo=timezone.utc)

    recovery = coordinator.recover_pending()

    assert recovery["stale_expired"] == 1
    assert recovery["publish_calls"] == 0
    assert recovery["backlog_remaining"] == 0
    assert transport.publish_calls == []
    assert store.get_platform_dispatch(registered["dispatch_id"])["status"] == (
        DERIVATIVE_EXPIRED_STALE_NO_WRITE
    )
    assert store.get_reconciliations_for_work_item("work-1")[0]["status"] == (
        RECONCILED_ABSENT_SAFE_TO_RETRY
    )


def test_unknown_write_is_read_back_even_when_old_and_never_blindly_retried(tmp_path):
    store, transport, coordinator = _coordinator(tmp_path)
    registered = coordinator.register_plan("work-1", _plan("telegram"))["registered"][0]
    store.register_platform_dispatch(
        dispatch_id=registered["dispatch_id"], message_id=registered["message_id"],
        platform="telegram", status=UNKNOWN_WRITE, public_object_id="telegram-object-1",
    )
    store.set_outbox_status(registered["message_id"], UNKNOWN_WRITE)
    coordinator._clock = lambda: datetime(2030, 1, 1, tzinfo=timezone.utc)

    recovery = coordinator.recover_pending()

    assert recovery["readbacks"] == 1
    assert recovery["publish_calls"] == 0
    assert transport.readback_calls == ["telegram"]
    assert transport.publish_calls == []


def _quarantined_derivative_fixture(tmp_path):
    store, transport, coordinator = _coordinator(tmp_path)
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    plan = _plan("substack", "linkedin")
    coordinator.execute_plan("work-1", plan)
    ids = coordinator._ids("work-1", plan["plan_hash"], "linkedin")
    store.set_dispatch_status(ids["dispatch_id"], UNKNOWN_WRITE)
    store.set_outbox_status(ids["message_id"], UNKNOWN_WRITE)
    transport.ambiguous = True
    coordinator.readback_existing_dispatch(ids["dispatch_id"])
    coordinator.quarantine_unresolved_dispatch(ids["dispatch_id"], cause="READBACK_UNRESOLVED",
        next_owner="Jim", next_action="Check the exact account activity", evidence_ref="fixture-readback.json")
    return store, transport, coordinator, ids


def test_exact_dispatch_quarantine_survives_restart_and_allows_other_operations(tmp_path):
    store, transport, coordinator, ids = _quarantined_derivative_fixture(tmp_path)
    before = store.get_platform_dispatch(ids["dispatch_id"])
    calls = list(transport.publish_calls)
    restarted = DurablePublicationCoordinator(store=store, transport_runtime=transport)
    recovery = restarted.recover_pending()
    assert recovery["backlog_remaining"] == 0
    assert recovery["quarantined_dispatches"][0]["readback_owed"] is True
    assert restarted._active_unknown_write_count() == 0
    assert store.get_platform_dispatch(ids["dispatch_id"]) == before
    outcome = restarted._dispatch_message(store.get_outbox_message(ids["message_id"]), canonical_url=None)
    assert outcome["publish_called"] is False
    assert outcome["status"] == "QUARANTINED_UNKNOWN_WRITE_READBACK_OWED"
    transport.ambiguous = False
    store.create_work_item(story_id="other", title="Other article", target_surface="MULTI_PLATFORM", work_item_id="other")
    result = restarted.execute_plan("other", _plan("telegram"))
    assert result["per_destination"]["telegram"]["publish_called"] is True
    assert transport.publish_calls == calls + ["telegram"]
    # Explicit readback is still owed and allowed; successful reconciliation ends isolation.
    restarted.readback_existing_dispatch(ids["dispatch_id"])
    assert store.get_platform_dispatch(ids["dispatch_id"])["status"] == DISPATCH_CONFIRMED
    assert restarted._dispatch_quarantine(store.get_platform_dispatch(ids["dispatch_id"])) is None


def test_quarantine_does_not_hide_another_unknown_or_allow_canonical_isolation(tmp_path):
    store, transport, coordinator, ids = _quarantined_derivative_fixture(tmp_path)
    plan = _plan("discord")
    other = coordinator.register_plan("work-1", plan)["registered"][0]
    store.register_platform_dispatch(dispatch_id=other["dispatch_id"], message_id=other["message_id"],
        platform="discord", status=UNKNOWN_WRITE)
    store.set_outbox_status(other["message_id"], UNKNOWN_WRITE)
    assert coordinator._active_unknown_write_count() == 1
    # Canonical ambiguity cannot be hidden by the derivative-only operation.
    canonical = next(r for r in store.list_platform_dispatches() if r["platform"] == "substack")
    store.set_dispatch_status(canonical["dispatch_id"], UNKNOWN_WRITE)
    with pytest.raises(ValueError, match="EXACT_UNRESOLVED_DERIVATIVE_READBACK_REQUIRED"):
        coordinator.quarantine_unresolved_dispatch(canonical["dispatch_id"], cause="test", next_owner="Jim",
            next_action="Read back", evidence_ref="test")


def test_new_article_refuses_to_start_while_safe_backlog_remains_after_budget(tmp_path):
    store, transport, coordinator = _coordinator(tmp_path)
    for index in range(20):
        work_item_id = f"backlog-work-{index}"
        store.create_work_item(
            story_id=f"backlog-story-{index}", title="Backlog fixture",
            target_surface="MULTI_PLATFORM", work_item_id=work_item_id,
            actor_ref="controlled_test", correlation_id=f"backlog-{index}",
        )
        coordinator.register_plan(work_item_id, _plan("telegram"))
    store.create_work_item(
        story_id="new-story", title="New article fixture", target_surface="MULTI_PLATFORM",
        work_item_id="new-work", actor_ref="controlled_test", correlation_id="new-work",
    )

    result = coordinator.execute_plan("new-work", _plan("telegram"))

    assert result["distribution_status"] == "BLOCKED_SAFE_RECOVERY_BACKLOG_REMAINS"
    assert result["registered"] == []
    assert result["recovery_preflight"]["safely_attempted"] == 9
    assert result["recovery_preflight"]["backlog_remaining"] == 11
    assert len(transport.publish_calls) == 9


def test_neo_identity_must_be_current_and_does_not_bootstrap_edge(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    manager = DestinationReadinessManager(store=store, env={},
        edge_runtime_ensurer=lambda: pytest.fail("Neo must never bootstrap Edge"),
        neo_readiness_provider=lambda surface: {"public_handle": "@Capitalnicle", "authenticated": True,
            "native_executor_bound": True, "proof_fresh": True, "observation_sha256": "controlled-test-observation"})
    assert manager.probe_surface("X_THREAD")["readiness_state"] == "READY_AUTHENTICATED"
    manager.neo_readiness_provider = lambda surface: {"public_handle": "@Capitalnicle", "authenticated": False}
    assert manager.probe_surface("X_THREAD")["write_eligible"] is False


@pytest.mark.parametrize("mode", ["KILL_SWITCH", "SUPERVISED_OPERATOR_GATE", "SHADOW_ONLY"])
def test_cases_j_k_l_non_autonomous_modes_never_publish(tmp_path, mode):
    store, transport, coordinator = _coordinator(tmp_path)
    _set_mode(store, mode)
    result = coordinator.execute_plan("work-1", _plan("telegram"))
    assert result["per_destination"]["telegram"]["status"] == f"WRITE_BLOCKED_{mode}"
    assert transport.publish_calls == []


def test_exactly_one_write_mixed_transport_duplicate_restart_recovery(tmp_path):
    store, transport, coordinator = _coordinator(tmp_path)
    plan = _plan("substack", "x", "telegram", "discord", "facebook_page")
    first = coordinator.execute_plan("work-1", plan)
    second = coordinator.execute_plan("work-1", plan)
    restarted = DurablePublicationCoordinator(
        store=store, transport_runtime=transport,
        readiness_provider=lambda destination: {"readiness_state": "READY_AUTHENTICATED"},
    )
    recoveries = [restarted.recover_pending() for _ in range(4)]
    assert len(first["registered"]) == 5
    assert len(store.list_outbox_messages()) == 5
    assert len(store.list_platform_dispatches()) == 5
    assert len(transport.publish_calls) == 5
    assert second["public_write_performed"] is False
    assert sum(row["publish_calls"] for row in recoveries) == 0
    assert len({row["public_object_id"] for row in store.list_platform_dispatches()}) == 5
    assert len(store.get_reconciliations_for_work_item("work-1")) == 5


@pytest.mark.parametrize("destination,shape", [
    ("substack", {"status": "SUCCESS", "draft_id": "206403125", "public_url": "https://x/p/a"}),
    ("telegram", {"status": "SUCCESS", "id": "61", "public_url": "https://t.me/c/61"}),
    ("discord", {"status": "SUCCESS", "id": "12001"}),
    ("x", {"status": "SUCCESS", "id": "18001", "public_url": "https://x.com/a/status/18001"}),
    ("linkedin", {"status": "SUCCESS", "activity_id": "urn:li:activity:1", "public_url": "https://linkedin.com/feed/update/1"}),
    ("facebook_page", {"status": "SUCCESS", "post_id": "page_1", "public_url": "https://facebook.com/1"}),
    ("instagram_business", {"status": "SUCCESS", "media_id": "ig_1", "permalink": "https://instagram.com/p/1"}),
    ("threads", {"status": "SUCCESS", "id": "th_1", "permalink": "https://threads.net/post/1"}),
    ("youtube", {"status": "SUCCESS", "post_id": "yt_1", "public_url": "https://youtube.com/post/1"}),
])
def test_historical_adapter_result_compatibility(destination, shape):
    registration = registration_for_destination(destination)
    result = normalize_dispatch_result(
        shape, destination=destination, surface=registration.surface,
        transport_type=registration.transport_type,
    )
    assert result["status"] == DISPATCH_CONFIRMED
    assert result["public_object_id"]
    if destination == "discord":
        assert result["public_object_url"] is None


def test_substack_pre_public_failure_normalizes_as_definite_no_write():
    registration = registration_for_destination("substack")
    result = normalize_dispatch_result(
        {
            "status": "BLOCKED_SUBSTACK_CONTINUE_CONTROL_NOT_FOUND",
            "draft_id": "210796285",
            "definite_no_write": True,
            "public_write_attempted": False,
        },
        destination="substack",
        surface=registration.surface,
        transport_type=registration.transport_type,
    )

    assert result["status"] == DEFINITE_NO_WRITE
    assert result["public_object_id"] is None
    assert result["public_object_url"] is None
    assert result["write_outcome_certainty"] == "DEFINITE_NO_WRITE"


def test_legacy_substack_unknown_without_outcome_remains_unknown():
    registration = registration_for_destination("substack")
    result = normalize_dispatch_result(
        {
            "status": "UNKNOWN_SUBSTACK_PUBLICATION_REQUIRES_DRAFT_ID_RECONCILIATION",
            "draft_id": "210865567",
        },
        destination="substack",
        surface=registration.surface,
        transport_type=registration.transport_type,
    )

    assert result["status"] == UNKNOWN_WRITE
    assert result["public_object_id"] == "210865567"
    assert "provider_outcome" not in result


def test_real_production_composition_has_no_fixture_or_none_wiring(tmp_path):
    runtime = build_final_daily_app_production_runtime(
        store_path=tmp_path / "store.sqlite3", output_root=tmp_path / "output",
        ensure_edge_runtime=False, run_readiness_probes=False,
    )
    smoke = runtime.smoke_snapshot()
    assert smoke["schema_version"] == 9
    assert smoke["publisher_is_real_coordinator"] is True
    assert smoke["publisher_wiring_not_none"] is True
    assert smoke["readback_wiring_not_none"] is True
    assert smoke["performance_wiring_not_none"] is True
    assert smoke["learning_enabled"] is True
    assert smoke["scheduled_editorial_owner"] == "NATIVE_CODEX_DESKTOP"
    assert smoke["exactly_one_routine_editorial_owner"] is True
    assert smoke["routine_editorial_owner"] == "NATIVE_CODEX_DESKTOP"
    assert smoke["native_desktop_routine_invocation_count"] == 0
    assert smoke["legacy_rolling_x_routine_invocation_count"] == 0
    assert smoke["codex_runtime_model_call_count"] == 0
    assert smoke["codex_runtime_model_calls"] == 0
    assert smoke["simple_semantic_model_source_call_count"] == 0
    assert smoke["simple_semantic_model_source_calls"] == 0
    assert smoke["public_provider_coordinator_writes"] == 0
    assert smoke["public_provider_coordinator_write_count"] == 0
    assert smoke["public_write_count"] == 0
    assert smoke["provider_write_count"] == 0
    assert smoke["coordinator_write_count"] == 0
    assert smoke["unknown_write_count"] == 0
    assert smoke["UNKNOWN_WRITE"] == 0
    assert smoke["routine_scheduler"] == "CODEX_DESKTOP_FOUR_NATIVE_AUTOMATIONS"
    assert smoke["public_write_performed"] is False
    assert callable(runtime.execute_native_desktop_scheduled_opportunity)
    assert callable(runtime.prepare_native_desktop_scheduled_opportunity)
    assert callable(runtime.complete_native_desktop_scheduled_opportunity)


def test_native_desktop_runtime_compatibility_seams_are_non_routing(tmp_path):
    runtime = build_final_daily_app_production_runtime(
        store_path=tmp_path / "store.sqlite3", output_root=tmp_path / "output",
    )
    result = runtime.execute_native_desktop_scheduled_opportunity(
        automation_id="v1-newsroom-new-york-2100",
    )
    assert result["executed"] is False
    assert result["reason"] == "native_desktop_non_routing_current_composition"
    assert result["routine_editorial_owner"] == "NATIVE_CODEX_DESKTOP"
    assert result["public_write_performed"] is False
    assert result["unknown_write_detected"] is False


def test_default_production_startup_does_not_ensure_or_navigate_edge(tmp_path, monkeypatch):
    import live_contentops.production_runtime_v1 as production

    monkeypatch.setattr(
        production.ContentOpsProductionOrchestrator,
        "execute",
        lambda *_args, **_kwargs: pytest.fail("startup attempted Edge/browser operation"),
    )
    runtime = production.build_final_daily_app_production_runtime(
        store_path=tmp_path / "store.sqlite3",
        output_root=tmp_path / "output",
    )
    assert runtime.smoke_snapshot()["public_write_performed"] is False


class _ExactJitReadiness:
    def __init__(self, *, state=None):
        self.jit_destinations = []
        self.readback_destinations = []
        self.probe_all_calls = 0
        self.state = state
        self.failed_attempts = {}

    def cached_failed_jit_attempt(self, destination, *, attempt_identity):
        return self.failed_attempts.get((destination, attempt_identity))

    def verify_destination_jit(
        self, destination, *, reason, persist=True, attempt_identity=None
    ):
        self.jit_destinations.append((destination, reason, persist, attempt_identity))
        row = {"readiness_state": self.state or (
            "READY_AUTHENTICATED"
            if registration_for_destination(destination).transport_type == "EDGE_CDP"
            else "READY_NON_BROWSER_BINDING"
        )}
        if row["readiness_state"] not in READY_STATES and attempt_identity:
            self.failed_attempts[(destination, attempt_identity)] = row
        return row

    def ensure_destination_runtime_for_readback(self, destination):
        self.readback_destinations.append(destination)
        return {"status": "ATTACHED_CANONICAL_EDGE", "external_probe_performed": False}

    def probe_all(self, **_kwargs):
        self.probe_all_calls += 1
        raise AssertionError("global probe_all must never be used by coordinator recovery")


def test_idle_recovery_performs_no_global_or_destination_probe(tmp_path):
    readiness = _ExactJitReadiness()
    _store_value, transport, coordinator = _coordinator(
        tmp_path, readiness_manager=readiness
    )

    recovery = coordinator.recover_pending()

    assert recovery["readiness_probe_performed"] is False
    assert recovery["readbacks"] == 0
    assert readiness.probe_all_calls == 0
    assert readiness.jit_destinations == []
    assert readiness.readback_destinations == []
    assert transport.publish_calls == []
    assert transport.readback_calls == []


def test_exact_work_item_recovery_reads_only_its_payloads(tmp_path, monkeypatch):
    store, transport, coordinator = _coordinator(tmp_path)
    plan = _plan("substack")
    first = coordinator.execute_plan("work-1", plan)
    assert first["canonical_article_real_published"] is True
    store.create_work_item(story_id="old", work_item_id="old", title="Old edition", target_surface="TEST")
    store.register_outbox_message(message_id="old-retained-media", work_item_id="old",
        destination="internal:old", payload=json.dumps({"retained_media": "x" * 100000}), status="EDITORIAL_INTERNAL")
    coordinator.recovery_scope = {"work_item_id": "work-1", "plan": plan, "exact_work_item_only": True}
    original = store.list_outbox_messages
    calls = []

    def scoped_only(**kwargs):
        assert kwargs.get("work_item_id") == "work-1", "unbounded historical payload scan"
        rows = original(**kwargs)
        assert all(r["work_item_id"] == "work-1" for r in rows)
        calls.append(kwargs)
        return rows

    monkeypatch.setattr(store, "list_outbox_messages", scoped_only)
    recovery = coordinator.recover_pending()
    assert calls
    assert recovery["backlog_remaining"] == 0
    assert transport.publish_calls == ["substack"]


def test_browser_publication_uses_exact_destination_jit_only(tmp_path):
    readiness = _ExactJitReadiness()
    _store_value, transport, coordinator = _coordinator(
        tmp_path, readiness_manager=readiness
    )

    result = coordinator.execute_plan("work-1", _plan("substack"))

    assert result["canonical_article_real_published"] is True
    assert len(readiness.jit_destinations) == 1
    assert readiness.jit_destinations[0][:3] == ("substack", "PUBLICATION", True)
    assert readiness.jit_destinations[0][3].startswith("dispatch_")
    assert readiness.readback_destinations == ["substack"]
    assert readiness.probe_all_calls == 0
    assert transport.publish_calls == ["substack"]
    assert transport.readback_calls == ["substack"]


def test_kill_switch_blocks_before_jit_and_run_now_cannot_bypass(tmp_path):
    readiness = _ExactJitReadiness()
    store, transport, coordinator = _coordinator(tmp_path, readiness_manager=readiness)
    _set_mode(store, "KILL_SWITCH")

    result = coordinator.execute_plan("work-1", _plan("substack"))

    assert result["per_destination"]["substack"]["status"] == "WRITE_BLOCKED_KILL_SWITCH"
    assert readiness.jit_destinations == []
    assert readiness.readback_destinations == []
    assert readiness.probe_all_calls == 0
    assert transport.publish_calls == []


def test_failed_jit_is_not_reprobed_on_every_recovery_tick(tmp_path):
    readiness = _ExactJitReadiness(state="REAUTH_REQUIRED")
    store, transport, coordinator = _coordinator(tmp_path, readiness_manager=readiness)
    coordinator.register_plan("work-1", _plan("substack"))

    first = coordinator.recover_pending()
    second = coordinator.recover_pending()

    assert first["publish_calls"] == 0
    assert second["publish_calls"] == 0
    assert len(readiness.jit_destinations) == 1
    assert store.list_platform_dispatches() == []
    assert transport.publish_calls == []


def test_pending_unknown_write_uses_exact_destination_readback_only(tmp_path):
    readiness = _ExactJitReadiness()
    store, transport, coordinator = _coordinator(tmp_path, readiness_manager=readiness)
    registered = coordinator.register_plan("work-1", _plan("x"))["registered"][0]
    store.register_platform_dispatch(
        dispatch_id=registered["dispatch_id"], message_id=registered["message_id"],
        platform="x", status=UNKNOWN_WRITE, public_object_id="x-object-1",
    )
    store.set_outbox_status(registered["message_id"], UNKNOWN_WRITE)

    recovery = coordinator.recover_pending()

    assert recovery["readbacks"] == 1
    assert readiness.readback_destinations == ["x"]
    assert readiness.jit_destinations == []
    assert readiness.probe_all_calls == 0
    assert transport.readback_calls == ["x"]


@pytest.mark.parametrize(
    ("destination", "durable_status", "reconciliation_status"),
    (
        (
            "instagram_business",
            DERIVATIVE_RECOVERY_RETRY_EXHAUSTED_NO_WRITE,
            RECONCILED_ABSENT_SAFE_TO_RETRY,
        ),
        (
            "facebook_page",
            DERIVATIVE_RECOVERY_RETRY_EXHAUSTED_NO_WRITE,
            RECONCILED_ABSENT_SAFE_TO_RETRY,
        ),
    ),
)
@pytest.mark.parametrize("other_destination_unknown", [False, True])
def test_explicit_transport_correction_is_exact_and_one_shot(
    tmp_path, destination, durable_status, reconciliation_status, other_destination_unknown
):
    class ExactXUrlTransport(FixtureTransport):
        def publish(self, *, destination, intent, authorization_context):
            result = super().publish(
                destination=destination,
                intent=intent,
                authorization_context=authorization_context,
            )
            if destination == "x":
                result["public_url"] = (
                    "https://x.com/Capitalnicle/status/2089681225246233006"
                )
            return result

    store, transport, coordinator = _coordinator(
        tmp_path, runtime=ExactXUrlTransport()
    )
    coordinator.execute_plan("work-1", _quality_plan())
    dispatch = next(
        row
        for row in store.list_platform_dispatches()
        if row["platform"] == destination
    )
    message = store.get_outbox_message(dispatch["message_id"])
    intent = json.loads(message["payload"])
    ids = coordinator._ids("work-1", intent["plan_hash"], destination)
    store.register_platform_dispatch(
        dispatch_id=dispatch["dispatch_id"],
        message_id=dispatch["message_id"],
        platform=destination,
        status=durable_status,
        public_object_id=dispatch["public_object_id"],
        public_object_url=dispatch["public_object_url"],
    )
    store.set_dispatch_status(dispatch["dispatch_id"], durable_status)
    store.set_outbox_status(dispatch["message_id"], durable_status)
    store.set_reconciliation_status(ids["reconciliation_id"], reconciliation_status)
    if other_destination_unknown:
        unrelated = next(d for d in store.list_platform_dispatches() if d["platform"] == "linkedin")
        store.set_dispatch_status(unrelated["dispatch_id"], UNKNOWN_WRITE)
        store.set_outbox_status(unrelated["message_id"], UNKNOWN_WRITE)
    before = transport.publish_calls.count(destination)

    # Native requests share the work item but are not publication destinations.
    store.register_outbox_message(message_id="controlled-native-request", work_item_id="work-1",
        destination="internal:native-neo-tool", payload='{"request":"controlled"}', status="NATIVE_NEO_INTERNAL")
    provider = coordinator.readiness_provider
    coordinator.readiness_provider = lambda d: {"readiness_state": "AUTH_INVALID"} if d == "substack" else provider(d)

    store.set_dispatch_status(dispatch["dispatch_id"], UNKNOWN_WRITE)
    blocked = coordinator.complete_derivative_after_transport_correction(
        dispatch["dispatch_id"], correction_id="owner-frozen-canary-platform-fix-v1")
    assert blocked["status"] == "CORRECTION_BLOCKED_UNKNOWN_WRITE_PRESENT"
    assert blocked["publish_called"] is False
    assert transport.publish_calls.count(destination) == before
    store.set_dispatch_status(dispatch["dispatch_id"], durable_status)

    first = coordinator.complete_derivative_after_transport_correction(
        dispatch["dispatch_id"], correction_id="owner-frozen-canary-platform-fix-v1"
    )
    second = coordinator.complete_derivative_after_transport_correction(
        dispatch["dispatch_id"], correction_id="owner-frozen-canary-platform-fix-v1"
    )

    assert first["status"] == DISPATCH_CONFIRMED
    assert first["publish_called"] is True
    assert second["status"] == "CORRECTION_ALREADY_ATTEMPTED_NO_WRITE"
    assert second["publish_called"] is False
    assert transport.publish_calls.count(destination) == before + 1


@pytest.mark.parametrize("recovered", [False, True])
def test_linkedin_ambiguous_provider_cause_reaches_durable_incident(tmp_path, recovered):
    from live_contentops.linkedin_official_member_api_v1 import LinkedInAmbiguousWriteError
    class FailedMemberTransport(FixtureTransport):
        def publish(self, *, destination, intent, authorization_context):
            if destination == "linkedin":
                raise LinkedInAmbiguousWriteError("UNKNOWN_WRITE_PROVIDER_REQUEST_REJECTED", http_status=503)
            return super().publish(destination=destination, intent=intent, authorization_context=authorization_context)
        def readback(self, **kwargs):
            if kwargs["destination"] == "linkedin" and not recovered:
                return {"status": "AMBIGUOUS", "verified": False}
            return super().readback(**kwargs)
    store, _, coordinator = _coordinator(tmp_path, runtime=FailedMemberTransport())
    coordinator.execute_plan("work-1", _quality_plan())
    with store.get_read_only_connection() as conn:
        rows = conn.execute("SELECT description FROM incidents WHERE severity='DISPATCH_FAILURE'").fetchall()
    assert any(json.loads(row[0]).get("safe_error_classification") ==
        "UNKNOWN_WRITE_PROVIDER_REQUEST_REJECTED;http_status:503" for row in rows) is (not recovered)


@pytest.mark.parametrize("absence_proved", [True, False])
def test_explicit_member_transport_correction_needs_absence_and_is_one_shot(tmp_path, absence_proved, monkeypatch):
    class InitiallyUnavailable(FixtureTransport):
        unavailable = True
        def publish(self, *, destination, intent, authorization_context):
            if destination == "linkedin" and self.unavailable:
                return {"status": "DEFINITE_NO_WRITE", "definite_no_write": True}
            return super().publish(destination=destination, intent=intent, authorization_context=authorization_context)
    runtime = InitiallyUnavailable()
    store, _, coordinator = _coordinator(tmp_path, runtime=runtime)
    plan = _quality_plan()
    coordinator.execute_plan("work-1", plan)
    runtime.unavailable = False
    ids = coordinator._ids("work-1", plan["plan_hash"], "linkedin")
    status = RECONCILED_ABSENT_SAFE_TO_RETRY if absence_proved else UNKNOWN_WRITE
    store.set_dispatch_status(ids["dispatch_id"], status)
    store.set_reconciliation_status(ids["reconciliation_id"], status)
    held = coordinator.complete_derivative_after_transport_correction(ids["dispatch_id"], correction_id="cc296-controlled-tls-fix")
    assert held["publish_called"] is False
    assert held["status"] == ("DESTINATION_FAILED_ET_DAY_SKIP" if absence_proved else "CORRECTION_BLOCKED_UNKNOWN_WRITE_PRESENT")
    # The same correction budget is still available on the following ET day.
    from datetime import timedelta
    failure_key = coordinator._destination_failure_key
    tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
    monkeypatch.setattr(coordinator, "_destination_failure_key", lambda destination, instant=None: failure_key(destination, tomorrow))
    first = coordinator.complete_derivative_after_transport_correction(ids["dispatch_id"], correction_id="cc296-controlled-tls-fix")
    assert first["publish_called"] is absence_proved
    second = coordinator.complete_derivative_after_transport_correction(ids["dispatch_id"], correction_id="cc296-controlled-tls-fix")
    assert second["publish_called"] is False
    assert runtime.publish_calls.count("linkedin") == int(absence_proved)


@pytest.mark.parametrize("status", [DERIVATIVE_RECOVERY_RETRY_EXHAUSTED_NO_WRITE, DERIVATIVE_EXPIRED_STALE_NO_WRITE])
def test_terminal_no_write_dispatch_can_refresh_absence_without_publishing(tmp_path, status):
    store, runtime, coordinator = _coordinator(tmp_path)
    registered = coordinator.register_plan("work-1", _plan("linkedin"))["registered"][0]
    store.register_platform_dispatch(dispatch_id=registered["dispatch_id"], message_id=registered["message_id"],
        platform="linkedin", status=status)
    before = list(runtime.publish_calls)
    coordinator.readback_existing_dispatch(registered["dispatch_id"])
    assert runtime.readback_calls == ["linkedin"]
    assert runtime.publish_calls == before


def test_durable_totals_survive_pending_callback_and_duplicate_resume(tmp_path):
    store, transport, coordinator = _coordinator(tmp_path)
    plan = _quality_plan()
    coordinator.register_plan("work-1", plan)
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    canonical = "https://capitalchronicle.substack.com/p/fixture-article-1"
    for destination in ("substack", "telegram", "discord", "threads", "x"):
        ids = coordinator._ids("work-1", plan["plan_hash"], destination)
        coordinator._dispatch_message(store.get_outbox_message(ids["message_id"]),
            canonical_url=None if destination == "substack" else canonical)
    for destination, status, reconciliation in (
        ("linkedin", UNKNOWN_WRITE, RECONCILIATION_PENDING),
        ("facebook_page", DERIVATIVE_RECOVERY_RETRY_EXHAUSTED_NO_WRITE, RECONCILED_ABSENT_SAFE_TO_RETRY),
        ("instagram_business", RECONCILED_ABSENT_SAFE_TO_RETRY, RECONCILED_ABSENT_SAFE_TO_RETRY),
    ):
        ids = coordinator._ids("work-1", plan["plan_hash"], destination)
        store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"],
            platform=destination, status=status)
        store.set_outbox_status(ids["message_id"], status)
        store.register_reconciliation(reconciliation_id=ids["reconciliation_id"],
            work_item_id="work-1", status=reconciliation)
    before = list(transport.publish_calls)
    state = coordinator.publication_state("work-1", plan)
    assert state["canonical_article_real_published"] is True
    assert state["canonical_url"] == canonical
    assert state["derivative_confirmed_count"] == 4
    assert state["derivative_unknown_count"] == 1
    assert state["derivative_failed_count"] == 1
    assert state["derivative_absent_safe_to_retry_count"] == 2
    assert state["derivative_never_attempted_count"] == 1
    assert state["per_destination"]["youtube"]["status"] == "NOT_DISPATCHED"
    assert coordinator.publication_state("other-operation", plan)["derivative_confirmed_count"] == 0
    coordinator.recover_pending = lambda: {"backlog_remaining": 1, "publish_calls": 0}
    for _ in range(2):
        result = coordinator.execute_plan("work-1", plan)
        assert result["canonical_article_real_published"] is True
        assert result["derivative_confirmed_count"] == 4
        assert result["per_destination"]["linkedin"]["status"] == UNKNOWN_WRITE
    assert transport.publish_calls == before


def test_confirmed_photo_credit_edit_is_exact_once_and_never_a_new_post(tmp_path, monkeypatch):
    import live_contentops._eight_platform_substack_first_pipeline_impl_v1 as pipeline
    class EditingTransport(FixtureTransport):
        def __init__(self):
            super().__init__()
            self.edits = []
        def amend_photo_attribution(self, **kwargs):
            self.edits.append(kwargs)
            return {"status": "SUCCESS", "verified": True, "public_object_id": kwargs["public_object_id"]}
    transport = EditingTransport()
    store, _, coordinator = _coordinator(tmp_path, runtime=transport)
    plan = _quality_plan()
    coordinator.execute_plan("work-1", plan)
    dispatch = next(d for d in store.list_platform_dispatches() if d["platform"] == "telegram")
    text = "Unconfirmed report. Archive photograph, 2017. https://capitalchronicle.substack.com/p/fixture-article-1"
    monkeypatch.setattr(pipeline, "_durable_intent_inputs", lambda _: {"payloads": {"telegram": {"text": text}}})
    calls = list(transport.publish_calls)
    first = coordinator.refresh_confirmed_photo_attribution(dispatch["dispatch_id"])
    second = coordinator.refresh_confirmed_photo_attribution(dispatch["dispatch_id"])
    assert first["verified"] is True and first["new_post_calls"] == 0
    assert second["status"] == "PHOTO_ATTRIBUTION_ALREADY_ATTEMPTED_READBACK_ONLY"
    assert second["edit_called"] is False
    assert len(transport.edits) == 1
    assert transport.edits[0]["public_object_id"] == dispatch["public_object_id"]
    assert transport.publish_calls == calls
    store.set_dispatch_status(dispatch["dispatch_id"], UNKNOWN_WRITE)
    blocked = coordinator.refresh_confirmed_photo_attribution(dispatch["dispatch_id"])
    assert blocked["edit_called"] is False and len(transport.edits) == 1


@pytest.mark.parametrize("mismatch", [None, "identity", "text", "media_present", "missing"])
def test_missing_discord_photo_repair_requires_exact_existing_readback_and_is_once(tmp_path, monkeypatch, mismatch):
    import live_contentops._eight_platform_substack_first_pipeline_impl_v1 as pipeline
    transport = FixtureTransport()
    transport.edits = []
    transport.amend_photo_attribution = lambda **kw: transport.edits.append(kw) or {"verified": True}
    store, _, coordinator = _coordinator(tmp_path, runtime=transport)
    plan = _quality_plan()
    coordinator.execute_plan("work-1", plan)
    dispatch = next(d for d in store.list_platform_dispatches() if d["platform"] == "discord")
    text = "Exact unchanged copy. https://capitalchronicle.substack.com/p/fixture-article-1"
    monkeypatch.setattr(pipeline, "_durable_intent_inputs", lambda _: {"payloads": {"discord": {"text": text}}})
    proof = {"write_exists": True, "message_id": dispatch["public_object_id"],
        "body_text_visible": True, "substack_url_visible": True, "meaningful_media_visible": False}
    if mismatch == "identity": proof["message_id"] = "other"
    if mismatch == "text": proof["body_text_visible"] = False
    if mismatch == "media_present": proof["meaningful_media_visible"] = True
    if mismatch == "missing": proof["write_exists"] = False
    transport.readback = lambda **_: proof
    posts = list(transport.publish_calls)
    first = coordinator.refresh_confirmed_photo_attribution(dispatch["dispatch_id"], repair_missing_media=True)
    second = coordinator.refresh_confirmed_photo_attribution(dispatch["dispatch_id"], repair_missing_media=True)
    assert len(transport.edits) == (1 if mismatch is None else 0)
    assert transport.publish_calls == posts
    assert second["edit_called"] is False
    if mismatch is None:
        assert first["edit_called"] is True and first["new_post_calls"] == 0
        assert transport.edits[0]["repair_missing_media"] is True
        assert transport.edits[0]["public_object_id"] == dispatch["public_object_id"]


@pytest.mark.parametrize("verified_delivery", [True, False])
def test_discord_media_repair_uses_only_hash_bound_original_delivery(monkeypatch, verified_delivery):
    from live_contentops.publication_coordinator_v1 import CanonicalDestinationTransportRuntimeV1
    import live_contentops._eight_platform_substack_first_pipeline_impl_v1 as pipeline
    import live_contentops.discord_live_adapter_v6 as adapter
    url = "https://example.test/exact-original.jpeg"
    data = {"article": {"title": "Dated report"}, "media_assets": [{"sha256": "original"}],
        "public_image_url": url, "primary_media": {"sha256": "original", "public_delivery_sha256": "original",
                                                  "local_public_hash_continuity": verified_delivery}}
    monkeypatch.setattr(pipeline, "_durable_intent_inputs", lambda _: data)
    edits = []
    monkeypatch.setattr(adapter, "execute_discord_edit", lambda *a, **kw: edits.append((a, kw)) or {"status": "SUCCESS"})
    monkeypatch.setattr(adapter, "readback_discord_post", lambda **_: {"status": "SUCCESS"})
    runtime = CanonicalDestinationTransportRuntimeV1(linkedin_transport=object(), neo_transport=object())
    canonical = "https://capitalchronicle.substack.com/p/exact"
    result = runtime.amend_photo_attribution(destination="discord", intent={"canonical_url": canonical},
        public_object_id="123", text="Exact source-bound copy", repair_missing_media=True)
    assert result["verified"] is verified_delivery
    assert len(edits) == int(verified_delivery)
    if verified_delivery:
        assert edits[0][0] == ("123", "Exact source-bound copy")
        assert edits[0][1]["embeds"] == [{"title": "Dated report", "url": canonical, "image": {"url": url}}]


def test_native_internal_records_never_become_dispatch_destinations(tmp_path):
    store, transport, coordinator = _coordinator(tmp_path)
    store.register_outbox_message(message_id="native-request", work_item_id="work-1",
        destination="internal:native-neo-tool", payload='{"request":"native"}', status="NATIVE_NEO_INTERNAL")
    store.register_outbox_message(message_id="native-return", work_item_id="work-1",
        destination="internal:native-neo-tool", payload='{"result":"native"}', status="NATIVE_NEO_INTERNAL")
    plan = _quality_plan()
    result = coordinator.execute_plan("work-1", plan)
    before = list(transport.publish_calls)
    assert result["distribution_status"] == FULL_V1_NINE_SURFACE_PUBLICATION_CONFIRMED
    assert set(result["per_destination"]) == set(V1_REQUIRED_PUBLICATION_DESTINATIONS) | {"linkedin_company", "x", "youtube"}
    repeated = coordinator.execute_plan("work-1", plan)
    assert repeated["derivative_confirmed_count"] == len(V1_REQUIRED_DERIVATIVE_DESTINATIONS)
    assert transport.publish_calls == before
    assert len(store.list_platform_dispatches()) == 10  # plus the company-page copy


def test_prior_distribution_policy_does_not_decode_internal_editorial_payloads(tmp_path, monkeypatch):
    store = ContentOpsDurableStore(tmp_path / "controlled.sqlite3")
    store.create_work_item(story_id="internal", work_item_id="internal", title="controlled", target_surface="TEST")
    raw = json.dumps({"work_item_id": "old", "plan_hash": "old-plan", "marker": "CONTROLLED-internal-editorial"})
    store.register_outbox_message(message_id="internal", work_item_id="internal",
        destination="internal:native-desktop-editorial", payload=raw, status="EDITORIAL_INTERNAL")
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=None,
        allow_prior_confirmed_distribution=True)
    original_loads = json.loads
    def decode(value, *args, **kwargs):
        assert value != raw, "Internal editorial payload must not enter public intent policy"
        return original_loads(value, *args, **kwargs)
    monkeypatch.setattr(json, "loads", decode)
    assert coordinator.recovery_blocks_new_publication({"backlog_remaining": 0}, "current",
        plan={"article_identity": "new"}) is False
    coordinator.recovery_scope = {"work_item_id": "current", "plan": {"article_identity": "new"}}
    def unexpected(*args, **kwargs):
        raise AssertionError("A non-deferable row must not rescan publication history")
    monkeypatch.setattr(coordinator, "recovery_blocks_new_publication", unexpected)
    assert not coordinator._defer_prior_distribution_recovery({"work_item_id": "old"}, "internal:native-desktop-editorial")
    assert not coordinator._defer_prior_distribution_recovery({"work_item_id": "old"}, "substack")
    assert not coordinator._defer_prior_distribution_recovery({"work_item_id": "current"}, "linkedin")


def test_recovery_policy_uses_its_supplied_snapshot_without_reloading_store(tmp_path, monkeypatch):
    store = ContentOpsDurableStore(tmp_path / "controlled.sqlite3")
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=None,
        allow_prior_confirmed_distribution=True)
    def unexpected():
        raise AssertionError("The same recovery snapshot must not be reloaded for each row")
    monkeypatch.setattr(store, "list_outbox_messages", unexpected)
    snapshot = []
    assert not coordinator.recovery_blocks_new_publication({"backlog_remaining": 0}, "current",
        plan={"article_identity": "new"}, evidence_messages=snapshot)
    coordinator.recovery_scope = {"work_item_id": "current", "plan": {"article_identity": "new"}}
    calls = []
    def guard(recovery, work_item_id, *, plan, evidence_messages=None):
        assert evidence_messages is snapshot
        calls.append((recovery, work_item_id, plan))
        return False
    monkeypatch.setattr(coordinator, "recovery_blocks_new_publication", guard)
    assert coordinator._defer_prior_distribution_recovery({"work_item_id": "old"}, "linkedin",
        evidence_messages=snapshot)
    assert len(calls) == 1
