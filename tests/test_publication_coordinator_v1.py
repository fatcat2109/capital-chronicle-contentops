from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from live_contentops.destination_transport_registry_v1 import (
    REGISTRY_VERSION,
    READY_STATES,
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
    UNKNOWN_WRITE,
    DurablePublicationCoordinator,
    normalize_dispatch_result,
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


def test_registry_locks_surface_transport_and_browser_roles():
    registry = canonical_transport_registry()
    assert registry["publishing_cdp_port"] == 9223
    assert registry["ingestion_only_cdp_port"] == 9222
    assert registry["chrome_publishing_allowed"] is False
    assert registry["silent_transport_fallback_allowed"] is False
    assert registration_for_destination("youtube").surface == "YOUTUBE_COMMUNITY_POST"
    assert registration_for_destination("youtube").transport_type == "EDGE_CDP"


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
    assert result["per_destination"]["telegram"]["status"] == "ASYNC_DERIVATIVE_QUEUED"
    assert result["per_destination"]["substack"]["reconciliation_status"] == RECONCILED_CONFIRMED
    assert transport.publish_calls == ["substack"]
    assert result["distribution_status"] == "CANONICAL_PUBLISHED_DERIVATIVES_ASYNC"

    recovery = coordinator.recover_pending()
    assert recovery["publish_calls"] == 1
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
    assert result["distribution_status"] == "CANONICAL_PUBLISHED_DERIVATIVES_ASYNC"
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
    assert transport.publish_calls == ["substack"]
    assert coordinator.recover_pending()["publish_calls"] == 1
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
    assert result["distribution_status"] == "CANONICAL_PUBLISHED_DERIVATIVES_ASYNC"
    assert result["per_destination"]["linkedin"]["status"] == "ASYNC_DERIVATIVE_QUEUED"
    coordinator.recover_pending()
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


def test_cases_h_i_edge_crash_bootstrap_and_reauth_classification(tmp_path, monkeypatch):
    import live_contentops.edge_cdp_publishing_adapter_v1 as adapter
    import live_contentops.publishing_profile_registry_v1 as profiles

    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    doctor_calls = [0]
    def doctor(**kwargs):
        doctor_calls[0] += 1
        if doctor_calls[0] == 1:
            return {"status": "READY_TO_LAUNCH", "recommended_cdp_port": 9223}
        return {"status": "READY_TO_ATTACH", "recommended_cdp_port": 9223}
    recoveries = []
    manager = DestinationReadinessManager(
        store=store, env={},
        edge_runtime_ensurer=lambda: recoveries.append(9223) or {"status": "LAUNCHED_CANONICAL_EDGE"},
    )
    monkeypatch.setattr(profiles, "browser_doctor", doctor)
    monkeypatch.setattr(adapter, "probe_authenticated_platform_session", lambda port, key: {
        "authenticated": True, "destination_identity": "@Capitalnicle",
        "login_control_detected": False,
    })
    row = manager.probe_surface("X_THREAD")
    assert row["readiness_state"] == "READY_AUTHENTICATED"
    assert recoveries == [9223]
    assert row["sanitized_detail"]["edge_recovery_status"] == "LAUNCHED_CANONICAL_EDGE"
    monkeypatch.setattr(adapter, "probe_authenticated_platform_session", lambda port, key: {
        "authenticated": False, "destination_identity": None, "login_control_detected": True,
    })
    row = manager.probe_surface("X_THREAD")
    assert row["readiness_state"] == "REAUTH_REQUIRED"


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
    assert sum(row["publish_calls"] for row in recoveries) == 4
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
    assert smoke["public_write_performed"] is False


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
