"""Site-first coordinator tests with isolated stores and actual native return binding."""
from copy import deepcopy
from datetime import datetime, timezone
import json
from types import SimpleNamespace

import pytest

from live_contentops.native_neo_executor_v1 import NativeNeoExecutor, NativeNeoInputRequired, TOOL
from live_contentops.publication_coordinator_v1 import UNKNOWN_WRITE
from live_contentops.site_first_publication_v1 import (
    POLICY, candidate, confirm_site, confirmed_site, request_for_site, site_url,
)
from test_published_content_v1 import lifecycle


def setup(tmp_path):
    store, transport, coordinator, plan, article, root = lifecycle(tmp_path)
    plan["distribution_policy"] = POLICY
    executor = NativeNeoExecutor(store, operation_id="work-1", output_dir=root / "neo",
        native_invocation_id="synthetic-exec-154", allow_publish=True)
    transport._neo_transport = SimpleNamespace(native_executor=executor)
    return store, transport, coordinator, plan, executor, root


def observe(store, plan, executor, **changes):
    request = request_for_site("work-1", plan, executor.native_invocation_id)
    with pytest.raises(NativeNeoInputRequired) as pending:
        executor(request)
    packet = pending.value.request
    executor.begin(request["request_sha256"])
    result = {"request_sha256": request["request_sha256"], "verified": True,
        "observed_identity": request["expected_identity"], "public_object_url": site_url(plan),
        "article_identity": plan["article_identity"],
        "article_content_sha256": plan["article_content_sha256"], **changes}
    executor.submit(request["request_sha256"], {
        "tool_request_sha256": packet["tool_request_sha256"], "result": result,
        "tool_observation": {"tool_name": TOOL, "native_invocation_id": "synthetic-exec-154",
            "surface": "CODEX_EXEC", "observation_source": "synthetic_test_fixture",
            "observed_at_utc": datetime.now(timezone.utc).isoformat()}})
    return confirm_site(store, "work-1", plan, executor)


def test_candidate_is_not_live_proof_and_no_substack_or_social_before_site(tmp_path):
    store, transport, coordinator, plan, executor, root = setup(tmp_path)
    assert candidate("work-1", plan)["site_publication_confirmed"] is False
    with pytest.raises(NativeNeoInputRequired) as pending:
        coordinator.execute_plan("work-1", plan)
    assert pending.value.request["request"]["action"] == "READBACK"
    assert (root / "site_publication_candidate_v1.json").is_file()
    assert not transport.publish_calls
    assert not store.list_platform_dispatches()
    assert confirmed_site(store, "work-1", plan) is None


@pytest.mark.parametrize("changes", [
    {"verified": False}, {"article_content_sha256": "0" * 64},
    {"public_object_url": "https://example.com/articles/wrong/"},
    {"article_identity": "another-article"}, {"observed_identity": "wrong-account"},
])
def test_wrong_stale_or_missing_live_article_never_unlocks_social(tmp_path, changes):
    store, transport, coordinator, plan, executor, _ = setup(tmp_path)
    with pytest.raises(ValueError, match="EXACT_LIVE_SITE_ARTICLE_READBACK_REQUIRED"):
        observe(store, plan, executor, **changes)
    assert confirmed_site(store, "work-1", plan) is None
    assert not transport.publish_calls


def test_social_uses_site_and_finishes_before_substack_code_without_wait(tmp_path):
    store, transport, coordinator, plan, executor, _ = setup(tmp_path)
    observe(store, plan, executor)
    publish = transport.publish
    intents = []
    def code_screen(**kwargs):
        intents.append(deepcopy(kwargs))
        if kwargs["destination"] == "substack":
            transport.publish_calls.append("substack")
            return {"status": "PENDING_JIM_EMAIL_CODE", "draft_id": "12345", "page_id": "synthetic-page",
                "page_url": "https://capitalchronicle.substack.com/publish/post/12345"}
        return publish(**kwargs)
    transport.publish = code_screen
    result = coordinator.execute_plan("work-1", plan)
    assert transport.publish_calls[-1] == "substack"
    assert set(transport.publish_calls[:-1]) == {"telegram", "discord", "x", "facebook_page"}
    assert all(i["intent"]["canonical_url"] == site_url(plan) for i in intents if i["destination"] != "substack")
    assert result["per_destination"]["substack"]["status"] == "SUBSTACK_DRAFT_AWAITING_OWNER"
    assert result["canonical_url"] == site_url(plan)
    assert result["site_publication_confirmed"] is True
    assert result["substack_publication_confirmed"] is False
    calls = list(transport.publish_calls)
    coordinator.execute_plan("work-1", plan)
    assert transport.publish_calls == calls  # no duplicate social or draft/publish attempt
    state = coordinator.publication_state("work-1", plan)
    assert state["site_publication_confirmed"] and not state["substack_publication_confirmed"]
    # Jim publishes the same draft; an exact readback adds its real public URL.
    readback = transport.readback
    def owner_published(**kwargs):
        observed = readback(**kwargs)
        if kwargs["destination"] == "substack":
            assert kwargs["intent"]["pending_owner_screen"]["page_id"] == "synthetic-page"
            observed["public_object_url"] = "https://capitalchronicle.substack.com/p/owner-published"
        return observed
    transport.readback = owner_published
    dispatch = coordinator._ids("work-1", plan["plan_hash"], "substack")["dispatch_id"]
    coordinator.readback_existing_dispatch(dispatch)
    state = coordinator.publication_state("work-1", plan)
    assert state["substack_publication_confirmed"]
    assert state["canonical_url"] == site_url(plan)
    assert transport.publish_calls == calls


def test_site_proof_does_not_bypass_kill_switch_or_uncertain_social(tmp_path):
    store, transport, coordinator, plan, executor, _ = setup(tmp_path)
    observe(store, plan, executor)
    from test_publication_coordinator_v1 import _set_mode
    _set_mode(store, "KILL_SWITCH")
    coordinator.execute_plan("work-1", plan)
    assert not transport.publish_calls


def test_recovery_cannot_use_placeholder_or_substack_instead_of_site(tmp_path):
    store, transport, coordinator, plan, executor, _ = setup(tmp_path)
    registration = coordinator.register_plan("work-1", plan)
    telegram = next(r for r in registration["registered"] if r["destination"] == "telegram")
    result = coordinator._dispatch_message(store.get_outbox_message(telegram["message_id"]),
        canonical_url="https://capitalchronicle.substack.com/p/looks-valid")
    assert result["status"] == "WAITING_SITE_READBACK"
    assert not transport.publish_calls


def test_site_readback_is_bound_to_exact_plan_and_public_copy(tmp_path):
    store, _, _, plan, executor, _ = setup(tmp_path)
    observe(store, plan, executor)
    changed = {**plan, "plan_hash": "different-plan"}
    assert confirmed_site(store, "work-1", changed) is None
    changed = {**plan, "article_content_sha256": "0" * 64}
    assert confirmed_site(store, "work-1", changed) is None


def test_export_rejects_changed_article_bytes(tmp_path):
    _, _, coordinator, plan, _, root = setup(tmp_path)
    article = json.loads((root / "article_manifest_v1.json").read_bytes())
    article["title"] = "Changed facts"
    (root / "article_manifest_v1.json").write_text(json.dumps(article), encoding="utf-8")
    with pytest.raises(ValueError, match="EXACT_REVIEWED_ARTICLE_HASH_REQUIRED"):
        coordinator.execute_plan("work-1", plan)


def test_pending_social_never_opens_substack_code_tab(tmp_path):
    store, transport, coordinator, plan, executor, _ = setup(tmp_path)
    observe(store, plan, executor)
    publish = transport.publish
    def pending_social(**kwargs):
        if kwargs["destination"] == "x":
            raise NativeNeoInputRequired({"request": {"destination": "x"}})
        return publish(**kwargs)
    transport.publish = pending_social
    result = coordinator.execute_plan("work-1", plan)
    assert result["per_destination"]["substack"]["status"] == "SUBSTACK_AFTER_SOCIAL_PASS"
    assert "substack" not in transport.publish_calls
    assert "telegram" in transport.publish_calls


def test_native_social_request_accepts_only_exact_preview_article_scope():
    from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff
    intent = {"work_item_id": "work", "distribution_policy": POLICY,
        "canonical_url": "https://fatcat2109.github.io/capital-chronicle-preview/articles/" + "a" * 32 + "/",
        "payload": "Exact approved social copy.", "destination_plan": {"payload_hash": "hash", "surface": "X_POST"}}
    auth = {"schema_version": "contentops.canonical_machine_authorization.v1", "dispatch_attempt_identity": "dispatch-test",
        "operating_mode": "AUTONOMOUS_DEFAULT", "destination": "x", "work_item_id": "work", "payload_hash": "hash"}
    adapter = NeoDestinationHandoff()
    assert adapter.request(destination="x", action="PUBLISH", intent=intent, authorization_context=auth)["canonical_url"] == intent["canonical_url"]
    for wrong in ("https://example.com/articles/test/", "https://fatcat2109.github.io/other/articles/" + "a" * 32 + "/"):
        with pytest.raises(ValueError, match="RECONCILED_CANONICAL_URL_REQUIRED"):
            adapter.request(destination="x", action="PUBLISH", intent={**intent, "canonical_url": wrong}, authorization_context=auth)


def test_live_transport_compiler_uses_confirmed_site_url_in_social_copy(tmp_path):
    from live_contentops.publication_coordinator_v1 import CanonicalDestinationTransportRuntimeV1
    store, _, coordinator, plan, executor, root = setup(tmp_path)
    observe(store, plan, executor)
    article = json.loads((root / "article_manifest_v1.json").read_bytes())
    article["article_mode"] = "BREAKING_BRIEF"
    (root / "run_context_v1.json").write_text(json.dumps({
        "article": article, "selection": {}, "media": {"assets": []},
        "accepted_evidence_sha256": "a" * 64,
    }), encoding="utf-8")
    rows = coordinator.register_plan("work-1", plan)["registered"]
    message = next(r for r in rows if r["destination"] == "telegram")
    intent = json.loads(store.get_outbox_message(message["message_id"])["payload"])
    value = CanonicalDestinationTransportRuntimeV1().finalize_intent(
        destination="telegram", intent=intent, canonical_url=confirmed_site(store, "work-1", plan))
    assert value["canonical_url"] == site_url(plan)
    assert site_url(plan) in value["native_payload"]["text"]
    assert "pending-publication" not in json.dumps(value["native_payload"])
    assert value["rematerialization_model_call_count"] == value["rematerialization_source_get_count"] == 0


def test_new_invocation_can_recheck_site_after_external_deployment(tmp_path):
    store, _, _, plan, executor, root = setup(tmp_path)
    with pytest.raises(ValueError, match="EXACT_LIVE_SITE_ARTICLE_READBACK_REQUIRED"):
        observe(store, plan, executor, verified=False)
    restarted = NativeNeoExecutor(store, operation_id="work-1", output_dir=root / "neo",
        native_invocation_id="later-exec", allow_publish=True)
    with pytest.raises(NativeNeoInputRequired) as pending:
        confirm_site(store, "work-1", plan, restarted)
    assert pending.value.request["request"]["native_invocation_id"] == "later-exec"


def test_full_distribution_substack_unavailable_never_vetoes_social(tmp_path):
    store, transport, coordinator, plan, executor, _ = setup(tmp_path)
    from test_publication_coordinator_v1 import _quality_plan
    from live_contentops.destination_transport_registry_v1 import (
        V1_REQUIRED_DERIVATIVE_DESTINATIONS, registration_for_destination,
    )
    plan.update(_quality_plan())
    observe(store, plan, executor)
    executor.readiness = lambda surface: {"authenticated": True, "native_executor_bound": True,
        "proof_fresh": True, "public_handle": registration_for_destination("linkedin").expected_public_handle}
    provider = coordinator.readiness_provider
    coordinator.readiness_provider = lambda destination: {"readiness_state": "SESSION_UNAVAILABLE"} if destination == "substack" else provider(destination)
    result = coordinator.execute_plan("work-1", plan)
    assert "substack" not in transport.publish_calls
    # The full route also mirrors LinkedIn to Capital Chronicle's company page.
    expected = set(V1_REQUIRED_DERIVATIVE_DESTINATIONS) | {"linkedin_company"}
    assert set(transport.publish_calls) == expected
    assert all(transport.publish_calls.count(d) == 1 for d in expected)
    assert all(result["per_destination"][d]["status"] == "DISPATCH_CONFIRMED" for d in expected)
    assert result["canonical_url"] == site_url(plan)
    assert result["site_publication_confirmed"]
    assert not result["substack_publication_confirmed"]
    calls = list(transport.publish_calls)
    coordinator.execute_plan("work-1", plan)
    assert transport.publish_calls == calls


def test_unknown_social_preserves_readback_before_retry_and_defers_substack(tmp_path):
    store, transport, coordinator, plan, executor, _ = setup(tmp_path)
    observe(store, plan, executor)
    publish = transport.publish
    def uncertain(**kwargs):
        if kwargs["destination"] == "x":
            raise TimeoutError("synthetic lost response")
        return publish(**kwargs)
    transport.publish = uncertain
    readback = transport.readback
    transport.readback = lambda **kwargs: {"verified": False} if kwargs["destination"] == "x" else readback(**kwargs)
    result = coordinator.execute_plan("work-1", plan)
    assert result["per_destination"]["x"]["status"] == UNKNOWN_WRITE
    assert result["per_destination"]["substack"]["status"] == "SUBSTACK_AFTER_SOCIAL_PASS"
    assert "substack" not in transport.publish_calls
    assert set(transport.publish_calls) == {"telegram", "discord", "facebook_page"}
