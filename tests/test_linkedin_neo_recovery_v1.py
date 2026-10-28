"""Isolated protocol fixtures only; no account, provider, or visual acceptance proof."""
import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from live_contentops.destination_transport_registry_v1 import (
    DESTINATION_TO_SURFACE, TIER1_SURFACES, V1_REQUIRED_DERIVATIVE_DESTINATIONS,
    V1_REQUIRED_PUBLICATION_DESTINATIONS, registration_for_destination, validate_registry,
)
from live_contentops.native_desktop_editorial_v1 import (
    build_dated_distribution_recovery, dated_distribution_recovery_view, final_visual_binding,
)
from live_contentops.native_neo_executor_v1 import NativeNeoExecutor, NativeNeoInputRequired
from live_contentops.neo_destination_handoff_v1 import (
    NeoDestinationHandoff, IDENTITIES, ROOTS, _public_url, destination_setup_projection,
)
from live_contentops.publication_coordinator_v1 import CanonicalDestinationTransportRuntimeV1
from test_dated_distribution_recovery_v1 import setup_recovery, accepted_recovery, CANONICAL


def linkedin_recovery(tmp_path, monkeypatch):
    store, binding, result, co, runtime, _ = setup_recovery(tmp_path, monkeypatch)
    # Reuse the prepared plan without constructing a replacement operation.
    from live_contentops.native_desktop_publication_v1 import _prepared_packet
    _, plan, _ = _prepared_packet(store, binding)
    ids = co._ids(binding["run_id"], plan["plan_hash"], "linkedin")
    message = store.get_outbox_message(ids["message_id"])
    intent = json.loads(message["payload"])
    intent["canonical_url"] = CANONICAL
    store.finalize_outbox_payload_before_dispatch(message_id=ids["message_id"], payload=json.dumps(intent), status="READY")
    store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"],
        platform="linkedin", status="UNKNOWN_WRITE")
    import live_contentops._eight_platform_substack_first_pipeline_impl_v1 as pipeline
    prior_inputs = pipeline._durable_intent_inputs
    def resolved_inputs(intent):
        data = {**prior_inputs(intent), "media_assets": result["media_assets"]}
        if intent.get("native_payload"):
            data["payloads"][intent["destination_plan"]["destination"]] = intent["native_payload"]
        return data
    monkeypatch.setattr(pipeline, "_durable_intent_inputs", resolved_inputs)
    recovery = build_dated_distribution_recovery(store, run_id=binding["run_id"],
        owner_authority_ref="human:CONTROLLED_BOTH_LINKEDIN_RECIPIENTS", destinations={"linkedin"})
    return store, binding, result, co, runtime, recovery, ids


def test_linkedin_scope_keeps_eight_routine_destinations_and_old_review(tmp_path, monkeypatch):
    store, binding, result, _, _, old = setup_recovery(tmp_path, monkeypatch)
    assert old == build_dated_distribution_recovery(store, run_id=binding["run_id"], owner_authority_ref=old["owner_authority_ref"])
    assert "destinations" not in old and "transport_override" not in old
    assert set(final_visual_binding(dated_distribution_recovery_view(store, run_id=binding["run_id"],
        result=result, recovery=old), renders=None, destinations=set(old["payloads"]))["variants"]) == set(old["payloads"])
    validate_registry()
    assert len(V1_REQUIRED_DERIVATIVE_DESTINATIONS) == 8
    assert "LINKEDIN_COMPANY_POST" not in TIER1_SURFACES
    assert registration_for_destination("linkedin").transport_type == "OFFICIAL_MEMBER_API"
    assert registration_for_destination("linkedin_company").expected_stable_id == "143198922"


def test_neo_recovery_keeps_personal_api_setup_and_company_identity_separate(tmp_path):
    setup = destination_setup_projection(env={}, linkedin_root=tmp_path)
    assert setup["linkedin"]["chosen_transport"] == "OFFICIAL_MEMBER_API"
    assert setup["linkedin"]["browser_login_needed"] is False
    assert setup["linkedin_company"]["chosen_transport"] == "BROWSEROS_NEO_MCP"
    assert setup["linkedin_company"]["expected_identity"] == "linkedin:company:143198922"


def test_optional_company_copy_does_not_enter_routine_readiness_or_publication_plan(tmp_path, monkeypatch):
    from live_contentops.destination_transport_registry_v1 import DestinationReadinessManager
    import live_contentops._eight_platform_substack_first_pipeline_impl_v1 as pipeline
    assert set(DESTINATION_TO_SURFACE) == set(V1_REQUIRED_PUBLICATION_DESTINATIONS)
    monkeypatch.setattr(DestinationReadinessManager, "probe_all", lambda *args, **kwargs: {
        "surfaces": {surface: {"readiness_state": "READY_AUTHENTICATED"} for surface in TIER1_SURFACES}})
    readiness = pipeline._rolling_x_destination_readiness(cdp_port=9223)
    assert set(readiness["destinations"]) == set(V1_REQUIRED_PUBLICATION_DESTINATIONS)
    assert readiness["all_required_destinations_ready"] is True
    plan = pipeline._build_rolling_x_publication_plan(run_id="routine-fixture", output_dir=tmp_path,
        viability={}, readiness=readiness, preparation={"release_candidate_lock": {
            "payload_sha256": {destination: "a" * 64 for destination in V1_REQUIRED_DERIVATIVE_DESTINATIONS}},
            "context": {"media": {"assets": [{"asset_id": "fixture-original"}]}}})
    assert {row["destination"] for row in plan["destinations"]} == set(V1_REQUIRED_PUBLICATION_DESTINATIONS)
    assert plan["pre_substack_blockers"] == []


@pytest.mark.parametrize("absent_status", ["RECONCILED_ABSENT_SAFE_TO_RETRY", "DERIVATIVE_EXPIRED_STALE_NO_WRITE"])
def test_dated_linkedin_requires_exact_same_writer_review_and_absence(tmp_path, monkeypatch, absent_status):
    store, binding, result, co, runtime, recovery, ids = linkedin_recovery(tmp_path, monkeypatch)
    ref = accepted_recovery(store, binding, result, recovery, tmp_path)
    assert set(recovery["payloads"]) == {"linkedin"}
    assert recovery["recipients"] == {"linkedin": IDENTITIES["linkedin"], "linkedin_company": IDENTITIES["linkedin_company"]}
    before = store.get_outbox_message(ids["message_id"])["payload"]
    assert co.complete_dated_distribution_recovery(ids["message_id"], review_reference=ref)["publish_called"] is False
    assert runtime.publish_calls == []
    store.set_dispatch_status(ids["dispatch_id"], absent_status)
    store.register_reconciliation(reconciliation_id=ids["reconciliation_id"], work_item_id=binding["run_id"],
        status="RECONCILED_ABSENT_SAFE_TO_RETRY")
    runtime._neo_transport = SimpleNamespace(native_executor=SimpleNamespace(native_neo_protocol=True,
        readiness=lambda _: {"authenticated": True, "native_executor_bound": True,
            "proof_fresh": True, "public_handle": IDENTITIES["linkedin"]}))
    co.complete_dated_distribution_recovery(ids["message_id"], review_reference=ref)
    assert runtime.publish_calls == ["linkedin"]
    assert runtime.sent[0]["native_payload"]["text"].startswith(recovery["date_label"])
    assert store.get_outbox_message(ids["message_id"])["payload"] == before
    assert co.complete_dated_distribution_recovery(ids["message_id"], review_reference=ref)["publish_called"] is False
    assert runtime.publish_calls == ["linkedin"]


def test_company_copy_is_distinct_once_and_does_not_retry_personal_unknown(tmp_path, monkeypatch):
    store, binding, result, co, runtime, recovery, personal = linkedin_recovery(tmp_path, monkeypatch)
    ref = accepted_recovery(store, binding, result, recovery, tmp_path)
    first = co.publish_reviewed_linkedin_company_copy(run_id=binding["run_id"], review_reference=ref)
    company = co._ids(binding["run_id"], recovery["plan_hash"], "linkedin_company")
    assert company["dispatch_id"] != personal["dispatch_id"]
    assert first["publish_called"] is True
    assert runtime.publish_calls == ["linkedin_company"]
    assert runtime.sent[0]["native_payload"] == recovery["payloads"]["linkedin"]
    assert store.get_platform_dispatch(personal["dispatch_id"])["status"] == "UNKNOWN_WRITE"
    assert co.publish_reviewed_linkedin_company_copy(run_id=binding["run_id"], review_reference=ref)["publish_called"] is False
    assert runtime.publish_calls == ["linkedin_company"]


def test_old_three_channel_review_cannot_authorize_company_copy(tmp_path, monkeypatch):
    store, binding, result, co, runtime, recovery = setup_recovery(tmp_path, monkeypatch)
    ref = accepted_recovery(store, binding, result, recovery, tmp_path)
    with pytest.raises(ValueError, match="EXPLICIT_SAME_REVIEW"):
        co.publish_reviewed_linkedin_company_copy(run_id=binding["run_id"], review_reference=ref)
    assert runtime.publish_calls == []


def test_company_pending_restart_and_claimed_action_never_create_again(tmp_path, monkeypatch):
    store, binding, result, co, _, recovery, _ = linkedin_recovery(tmp_path, monkeypatch)
    ref = accepted_recovery(store, binding, result, recovery, tmp_path)
    executor = NativeNeoExecutor(store, operation_id=binding["run_id"], output_dir=tmp_path/"neo",
        native_invocation_id="CONTROLLED_DESKTOP", allow_publish=True)
    monkeypatch.setattr(executor, "readiness", lambda _: {"authenticated": True, "native_executor_bound": True,
        "proof_fresh": True, "public_handle": IDENTITIES["linkedin_company"], "stable_id": "143198922"})
    co.transport_runtime = CanonicalDestinationTransportRuntimeV1(neo_transport=NeoDestinationHandoff(native_executor=executor))
    first = co.publish_reviewed_linkedin_company_copy(run_id=binding["run_id"], review_reference=ref)
    request = first["native_tool_request"]["request"]
    assert first["status"] == "NATIVE_NEO_TOOL_PENDING"
    assert request["expected_identity"] == IDENTITIES["linkedin_company"]
    assert request["content_binding"]["expected_text_segments"] == [recovery["payloads"]["linkedin"]["text"]]
    assert co.publish_reviewed_linkedin_company_copy(run_id=binding["run_id"], review_reference=ref)["native_tool_request"]["request"] == request
    executor.begin(request["request_sha256"])
    after_claim = co.publish_reviewed_linkedin_company_copy(run_id=binding["run_id"], review_reference=ref)
    assert after_claim["status"] == "UNKNOWN_WRITE"
    assert co.publish_reviewed_linkedin_company_copy(run_id=binding["run_id"], review_reference=ref)["publish_called"] is False
    with pytest.raises(ValueError, match="ALREADY_CLAIMED"):
        executor.begin(request["request_sha256"])


def test_company_queued_copy_cannot_change_after_its_review(tmp_path, monkeypatch):
    store, binding, result, co, _, recovery, _ = linkedin_recovery(tmp_path, monkeypatch)
    ref = accepted_recovery(store, binding, result, recovery, tmp_path)
    co.publish_reviewed_linkedin_company_copy(run_id=binding["run_id"], review_reference=ref)
    ids = co._ids(binding["run_id"], recovery["plan_hash"], "linkedin_company")
    original = store.get_outbox_message(ids["message_id"])
    changed = json.loads(original["payload"])
    changed["native_payload"]["text"] = "Unreviewed new text"
    with pytest.raises(ValueError, match="EXACT_REVIEWED_COPY"):
        co._dispatch_message({**original, "payload": json.dumps(changed)}, canonical_url=CANONICAL)


def test_native_projection_keeps_selected_company_copy_pending_without_changing_routine_count():
    from live_contentops.native_desktop_publication_v1 import publication_projection, DESTINATION
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
    run, plan = "CONTROLLED_PROJECTION", "CONTROLLED_PLAN"
    rows = [{"message_id": "fixture-native-publication", "destination": DESTINATION,
        "payload": json.dumps({"run_id": run, "plan_hash": plan})}]
    dispatches, reconciliations = [], []
    for destination in ["substack", *V1_REQUIRED_DERIVATIVE_DESTINATIONS]:
        ids = DurablePublicationCoordinator._ids(run, plan, destination)
        dispatches.append({**ids, "platform": destination, "status": "DISPATCH_CONFIRMED",
            "public_object_id": "fixture-" + destination,
            "public_object_url": CANONICAL if destination == "substack" else "https://example.test/"+destination})
        reconciliations.append({"reconciliation_id": ids["reconciliation_id"], "status": "RECONCILED_CONFIRMED"})
    original = publication_projection(rows, dispatches, reconciliations, run_id=run)
    assert original["state"] == "RECONCILED" and original["derivative_confirmed_count"] == 8
    ids = DurablePublicationCoordinator._ids(run, plan, "linkedin_company")
    rows.append({"message_id": ids["message_id"], "work_item_id": run, "destination": "linkedin_company",
        "payload": json.dumps({"plan_hash": plan})})
    incomplete = publication_projection(rows, dispatches, reconciliations, run_id=run)
    assert incomplete["state"] != "RECONCILED" and incomplete["next_operation"] != "none"
    assert incomplete["derivative_confirmed_count"] == 8
    assert incomplete["additional_recovery_required_destinations"] == ["linkedin_company"]
    dispatches.append({**ids, "platform": "linkedin_company", "status": "DISPATCH_CONFIRMED",
        "public_object_id": "urn:li:activity:123", "public_object_url": "https://www.linkedin.com/feed/update/urn:li:activity:123/"})
    reconciliations.append({"reconciliation_id": ids["reconciliation_id"], "status": "RECONCILED_CONFIRMED"})
    final = publication_projection(rows, dispatches, reconciliations, run_id=run)
    assert final["state"] == "RECONCILED" and final["derivative_confirmed_count"] == 8
    assert final["additional_confirmed_count"] == 1


@pytest.mark.parametrize("invalid", [None, "identity", "profile", "not_loaded", "not_empty", "unrelated_text", "stale"])
def test_unknown_absence_needs_owner_report_and_fresh_loaded_own_activity(tmp_path, monkeypatch, invalid):
    store, binding, _, co, runtime, _, ids = linkedin_recovery(tmp_path, monkeypatch)
    fixed = datetime(2026, 10, 28, 4, 4, 59, tzinfo=timezone.utc)
    co._clock = lambda: fixed
    executor = NativeNeoExecutor(store, operation_id=binding["run_id"], output_dir=tmp_path/"neo",
        native_invocation_id="CONTROLLED_NATIVE_READONLY", clock=lambda: fixed)
    runtime._neo_transport = NeoDestinationHandoff(native_executor=executor)
    before = store.get_outbox_message(ids["message_id"])["payload"]
    with pytest.raises(NativeNeoInputRequired) as pending:
        co.reconcile_owner_confirmed_linkedin_absence(ids["dispatch_id"], owner_authority_ref="human:CONTROLLED_OWNER_ABSENCE")
    packet = pending.value.request
    request_hash = packet["request"]["request_sha256"]
    executor.begin(request_hash)
    result = {"request_sha256": request_hash, "observed_identity": IDENTITIES["linkedin"],
        "observed_profile_url": ROOTS["linkedin"], "authenticated": True, "activity_feed_loaded": True,
        "activity_feed_empty": True, "observed_text": "Activity. Nothing to see for now."}
    changes = {"identity": {"observed_identity": IDENTITIES["linkedin_company"]},
        "profile": {"observed_profile_url": ROOTS["linkedin_company"]}, "not_loaded": {"activity_feed_loaded": False},
        "not_empty": {"activity_feed_empty": False}, "unrelated_text": {"observed_text": "An empty search result"}}
    result.update(changes.get(invalid, {}))
    executor.submit(request_hash, {"tool_request_sha256": packet["tool_request_sha256"],
        "tool_observation": {"tool_name": "mcp__browseros_neo__run", "native_invocation_id": executor.native_invocation_id,
            "surface": "CODEX_DESKTOP_CONVERSATION", "observation_source": "SYNTHETIC_PROTOCOL_FIXTURE_NOT_BROWSER_PROOF",
            "observed_at_utc": fixed.isoformat()}, "result": result})
    from datetime import timedelta
    fixed += timedelta(seconds=301 if invalid == "stale" else 2)
    observed = co.reconcile_owner_confirmed_linkedin_absence(ids["dispatch_id"],
        owner_authority_ref="human:CONTROLLED_OWNER_ABSENCE", request_hash=request_hash)
    assert (observed["status"] == "RECONCILED_ABSENT_SAFE_TO_RETRY") == (invalid is None)
    assert (store.get_platform_dispatch(ids["dispatch_id"])["status"] == "UNKNOWN_WRITE") == (invalid is not None)
    assert store.get_outbox_message(ids["message_id"])["payload"] == before
    assert runtime.publish_calls == []
    assert not executor.pending()


def test_unknown_with_object_identity_is_never_owner_absence_retried(tmp_path, monkeypatch):
    store, _, _, co, runtime, _, ids = linkedin_recovery(tmp_path, monkeypatch)
    store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"], platform="linkedin",
        status="UNKNOWN_WRITE", public_object_id="urn:li:activity:123")
    with pytest.raises(ValueError, match="UNIDENTIFIED_UNKNOWN"):
        co.reconcile_owner_confirmed_linkedin_absence(ids["dispatch_id"], owner_authority_ref="human:CONTROLLED")
    assert runtime.publish_calls == []


def test_company_public_readback_requires_actor_text_and_real_media_observation():
    url = "https://www.linkedin.com/feed/update/urn:li:activity:123/"
    intent = {"work_item_id": "fixture", "native_payload": {"text": "Dated report. " + CANONICAL,
        "media_asset_ids": ["photo"]}, "media_assets": [{"asset_id": "photo", "sha256": "source-photo"}],
        "destination_plan": {"surface": "LINKEDIN_COMPANY_POST"}}
    base = {"observed_identity": IDENTITIES["linkedin_company"], "public_object_id": "urn:li:activity:123",
        "public_object_url": url, "content_verified": True, "observed_text": "Dated report. " + CANONICAL,
        "observed_media_sha256": ["actual-platform-reencoding"], "media_comparisons": [{
            "source_asset_sha256": "source-photo", "platform_sha256": "a" * 64,
            "pixels_inspected": True, "source_pixels_match": True, "public_object_url": url,
            "public_image_url": "https://media.licdn.com/dms/image/fixture"}]}
    for invalid in [None, "actor", "pixels", "source"]:
        observed = json.loads(json.dumps(base))
        if invalid == "actor":
            observed["observed_identity"] = IDENTITIES["linkedin"]
        if invalid == "pixels":
            observed["media_comparisons"][0]["pixels_inspected"] = False
        if invalid == "source":
            observed["media_comparisons"][0]["source_asset_sha256"] = "other-photo"
        neo = NeoDestinationHandoff(native_executor=lambda request: {**observed, "request_sha256": request["request_sha256"]})
        assert neo.readback(destination="linkedin_company", intent=intent, public_object_id="urn:li:activity:123",
            public_object_url=url)["verified"] == (invalid is None)
    assert _public_url("linkedin_company", url, "urn:li:activity:123")
    assert not _public_url("linkedin_company", url, "urn:li:activity:124")


@pytest.mark.parametrize("destination", ["linkedin", "linkedin_company"])
@pytest.mark.parametrize("invalid", [None, "missing", "unverified", "wrong_target", "wrong_post", "wrong_display", "wrong_host"])
def test_shortened_canonical_requires_actual_exact_post_link_target(destination, invalid):
    url = "https://www.linkedin.com/feed/update/urn:li:activity:123/"
    short = "https://lnkd.in/fixture-link"
    intent = {"work_item_id": "fixture", "canonical_url": CANONICAL,
        "native_payload": {"text": "Dated report. " + CANONICAL}}
    link = {"displayed_url": short, "target_url": CANONICAL, "target_verified": True,
        "public_object_url": url}
    if invalid == "unverified":
        link["target_verified"] = False
    elif invalid == "wrong_target":
        link["target_url"] = "https://example.test/wrong"
    elif invalid == "wrong_post":
        link["public_object_url"] = url.replace("123", "124")
    elif invalid == "wrong_display":
        link["displayed_url"] = short + "other"
    elif invalid == "wrong_host":
        link["displayed_url"] = short.replace("lnkd.in", "example.test")
    observed = {"observed_identity": IDENTITIES[destination], "public_object_id": "urn:li:activity:123",
        "public_object_url": url, "content_verified": True, "observed_text": "Dated report. " + short,
        "observed_link_resolutions": [] if invalid == "missing" else [link]}
    neo = NeoDestinationHandoff(native_executor=lambda request: {**observed, "request_sha256": request["request_sha256"]})
    actual = neo.readback(destination=destination, intent=intent, public_object_id="urn:li:activity:123", public_object_url=url)
    assert actual["verified"] == (invalid is None)
    assert actual["observed_text"] == observed["observed_text"]


def test_normal_linkedin_runtime_keeps_api_and_only_explicit_recovery_routes_neo():
    called = []
    api = SimpleNamespace(publish=lambda **_: called.append("api") or {"status": "fixture"})
    neo = SimpleNamespace(publish=lambda **_: called.append("neo") or {"status": "fixture"})
    runtime = CanonicalDestinationTransportRuntimeV1(linkedin_transport=api, neo_transport=neo)
    runtime.publish(destination="linkedin", intent={}, authorization_context={})
    runtime.publish(destination="linkedin", intent={"dated_distribution_recovery": {"fixture": True},
        "destination_plan": {"transport_type": "BROWSEROS_NEO_MCP"}}, authorization_context={})
    assert called == ["api", "neo"]


@pytest.mark.parametrize("stable_id", ["143198922", "wrong-company", None])
def test_company_native_identity_requires_same_exact_stable_page(tmp_path, monkeypatch, stable_id):
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    fixed = datetime.now(timezone.utc)
    store = ContentOpsDurableStore(tmp_path/"isolated.sqlite3")
    executor = NativeNeoExecutor(store, operation_id="controlled", output_dir=tmp_path,
        native_invocation_id="CONTROLLED_TEST", clock=lambda: fixed)
    monkeypatch.setattr(NativeNeoExecutor, "__call__", lambda self, request: {
        "observed_identity": IDENTITIES["linkedin_company"], "observed_stable_id": stable_id,
        "authenticated": True, "native_tool_return_sha256": "fixture-observation",
        "native_tool_observation": {"native_invocation_id": self.native_invocation_id,
            "observed_at_utc": fixed.isoformat()}})
    assert executor.readiness("LINKEDIN_COMPANY_POST")["authenticated"] == (stable_id == "143198922")
