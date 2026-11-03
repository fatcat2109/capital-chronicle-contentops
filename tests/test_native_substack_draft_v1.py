"""Draft writes are fenced once and never masquerade as public canonicals."""
from copy import deepcopy
from hashlib import sha256

import pytest

from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff
from live_contentops.native_neo_executor_v1 import NativeNeoInputRequired
from live_contentops.publication_coordinator_v1 import (
    CanonicalDestinationTransportRuntimeV1, DurablePublicationCoordinator, OWNER_RETAINED_DRAFT_NO_PUBLISH,
)
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.destination_transport_registry_v1 import REGISTRY_VERSION


def intent():
    return {"work_item_id": "controlled-run", "package_identity": "controlled-package", "plan_hash": "controlled-plan",
            "native_payload": {"title": "Synthetic controlled title", "subtitle": "Synthetic subtitle",
                               "body_markdown": "Synthetic controlled body."},
            "media_assets": [{"asset_id": "synthetic", "sha256": "a" * 64}],
            "destination_plan": {"payload_hash": "controlled-hash", "surface": "SUBSTACK_ARTICLE"}}


def auth():
    return {"schema_version": "contentops.canonical_machine_authorization.v1", "action": "SAVE_DRAFT",
            "operating_mode": "AUTONOMOUS_DEFAULT", "destination": "substack", "work_item_id": "controlled-run",
            "dispatch_attempt_identity": "controlled-dispatch", "payload_hash": "controlled-hash"}


def observed(request):
    return {"request_sha256": request["request_sha256"], "observed_identity": "capitalchronicle.substack.com",
            "draft_id": "123", "draft_editor_url": "https://capitalchronicle.substack.com/publish/post/123",
            "draft_saved": True, "published": False, "publish_or_update_pressed": False,
            "observed_text": "Synthetic controlled title Synthetic subtitle Synthetic controlled body.",
            "observed_media_sha256": ["a" * 64]}


def test_draft_action_requires_coordinator_and_never_authorizes_publish():
    neo = NeoDestinationHandoff(native_executor=lambda r: observed(r))
    with pytest.raises(ValueError, match="COORDINATOR"):
        neo.save_draft(intent=intent(), authorization_context={})
    request = neo.request(destination="substack", action="SAVE_DRAFT", intent=intent(), authorization_context=auth())
    assert {"publish", "update", "read_mailbox", "enter_code"} <= set(request["forbidden"])
    assert request["action"] == "SAVE_DRAFT"
    assert neo.save_draft(intent=intent(), authorization_context=auth())["draft_verified"]


def test_draft_readback_requires_both_caption_and_full_attribution():
    value = intent()
    value["media_assets"][0].update(caption="Synthetic archive context.",
                                     attribution="Synthetic creator / archive. Public domain.")
    def only_caption(request):
        result = observed(request)
        result["observed_text"] += " Synthetic archive context."
        return result
    assert not NeoDestinationHandoff(native_executor=only_caption).save_draft(
        intent=value, authorization_context=auth())["draft_verified"]
    def full_credit(request):
        result = only_caption(request)
        result["observed_text"] += " Synthetic creator / archive. Public domain."
        return result
    assert NeoDestinationHandoff(native_executor=full_credit).save_draft(
        intent=value, authorization_context=auth())["draft_verified"]


@pytest.mark.parametrize("returned_id", ["123", "124"])
def test_credit_repair_is_bound_to_one_retained_editor_without_public_authority(returned_id):
    value, authorization = intent(), auth()
    target = {"draft_id": "123", "editor_url": "https://capitalchronicle.substack.com/publish/post/123",
              "purpose": "RESTORE_BOUND_MEDIA_CREDIT"}
    value["existing_draft_target"] = target
    authorization["existing_draft_target"] = target
    def actual(request):
        result = observed(request)
        result.update(draft_id=returned_id,
                      draft_editor_url="https://capitalchronicle.substack.com/publish/post/" + returned_id)
        return result
    neo = NeoDestinationHandoff(native_executor=actual)
    request = neo.request(destination="substack", action="SAVE_DRAFT", intent=value,
                          authorization_context=authorization)
    assert "never create or replace" in " ".join(request["steps"])
    assert neo.save_draft(intent=value, authorization_context=authorization)["draft_verified"] == (returned_id == "123")
    authorization.pop("existing_draft_target")
    with pytest.raises(ValueError, match="EXACT_RETAINED_SUBSTACK_DRAFT_REQUIRED"):
        neo.save_draft(intent=value, authorization_context=authorization)


@pytest.mark.parametrize("change", [
    {"published": True}, {"publish_or_update_pressed": True}, {"observed_identity": "wrong"},
    {"draft_editor_url": "https://wrong.invalid/publish/post/123"}, {"observed_media_sha256": []},
    {"observed_text": "Partial body"}, {"draft_saved": False}, {"draft_id": "124"},
])
def test_partial_or_wrong_object_never_becomes_a_saved_complete_draft(change):
    neo = NeoDestinationHandoff(native_executor=lambda r: {**observed(r), **change})
    result = neo.save_draft(intent=intent(), authorization_context=auth())
    assert not result["draft_verified"] and result["status"] == "UNKNOWN_WRITE"


def coordinator(tmp_path, monkeypatch, transport):
    monkeypatch.setattr("live_contentops.llm_operator_control_v1.assert_llm_operator_execution_enabled", lambda: None)
    store = ContentOpsDurableStore(tmp_path / "controlled.sqlite3")
    control = store.get_operating_control()
    store.update_operating_control(operating_mode="AUTONOMOUS_DEFAULT", expected_state_version=control["state_version"],
                                   control_source="CONTROLLED_TEST")
    plan = {"plan_hash": "controlled-plan", "transport_registry_version": REGISTRY_VERSION,
            "destinations": [{"destination": "substack", "surface": "SUBSTACK_ARTICLE",
                              "transport_type": "BROWSEROS_NEO_MCP", "payload": "Synthetic controlled draft.",
                              "payload_hash": sha256(b"Synthetic controlled draft.").hexdigest()}]}
    return DurablePublicationCoordinator(store=store, transport_runtime=transport), store, plan


class DraftTransport:
    def __init__(self, unknown=False):
        self.calls = 0
        self.unknown = unknown

    def save_substack_draft(self, **kwargs):
        self.calls += 1
        return {"draft_verified": not self.unknown, "draft_id": "123",
                "draft_editor_url": "https://capitalchronicle.substack.com/publish/post/123",
                "public_write_performed": False}

    def publish(self, **kwargs):
        pytest.fail("Draft-only operation attempted a public send")


@pytest.mark.parametrize("unknown", [False, True])
def test_draft_is_once_only_and_never_counted_as_public_or_retried(tmp_path, monkeypatch, unknown):
    transport = DraftTransport(unknown)
    co, store, plan = coordinator(tmp_path, monkeypatch, transport)
    first = co.save_substack_draft("controlled-run", plan)
    assert first["canonical_confirmed"] is False and first["published_article_count"] == 0
    second = co.save_substack_draft("controlled-run", deepcopy(plan))
    assert not second["new_draft_call"] and transport.calls == 1
    dispatch = store.list_platform_dispatches()[0]
    assert dispatch["status"] == ("UNKNOWN_WRITE" if unknown else OWNER_RETAINED_DRAFT_NO_PUBLISH)
    assert dispatch["public_object_url"] is None
    assert store.get_reconciliations_for_work_item("controlled-run") == []


def test_existing_uncertain_canonical_is_not_replaced_by_a_draft(tmp_path, monkeypatch):
    transport = DraftTransport()
    co, store, plan = coordinator(tmp_path, monkeypatch, transport)
    store.create_work_item(story_id="controlled-run", work_item_id="controlled-run", title="test", target_surface="TEST")
    co.register_plan("controlled-run", plan)
    ids = co._ids("controlled-run", plan["plan_hash"], "substack")
    store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"],
                                     platform="substack", status="UNKNOWN_WRITE")
    assert not co.save_substack_draft("controlled-run", plan)["new_draft_call"]
    assert transport.calls == 0


def test_coordinator_credit_repair_uses_one_retained_object_once(tmp_path, monkeypatch):
    transport = DraftTransport()
    co, store, plan = coordinator(tmp_path, monkeypatch, transport)
    co.save_substack_draft("controlled-run", plan)
    result = co.save_substack_draft("controlled-run", plan, repair_media_credit=True)
    assert result["media_credit_restored"] and result["draft_id"] == "123"
    assert not co.save_substack_draft("controlled-run", plan, repair_media_credit=True)["new_draft_call"]
    assert transport.calls == 2  # one creation, one exact-object repair; no repeated repair
    assert len(store.list_platform_dispatches()) == 1
    assert store.list_platform_dispatches()[0]["public_object_url"] is None


def test_ambiguous_credit_repair_preserves_the_draft_id_and_refuses_more_writes(tmp_path, monkeypatch):
    transport = DraftTransport()
    co, store, plan = coordinator(tmp_path, monkeypatch, transport)
    co.save_substack_draft("controlled-run", plan)
    transport.unknown = True
    result = co.save_substack_draft("controlled-run", plan, repair_media_credit=True)
    assert result["state"] == "UNKNOWN_WRITE"
    dispatch = store.list_platform_dispatches()[0]
    assert dispatch["public_object_id"] == "123" and dispatch["public_object_url"] is None
    with pytest.raises(ValueError, match="EXACT_RETAINED_SUBSTACK_DRAFT_REQUIRED"):
        co.save_substack_draft("controlled-run", plan, repair_media_credit=True)
    assert not co.save_substack_draft("controlled-run", plan)["new_draft_call"]
    assert transport.calls == 2


@pytest.mark.parametrize("draft_id,status", [
    ("123", OWNER_RETAINED_DRAFT_NO_PUBLISH), ("124", OWNER_RETAINED_DRAFT_NO_PUBLISH),
    ("123", "UNKNOWN_WRITE"),
])
def test_native_credit_repair_claim_requires_the_exact_retained_private_draft(tmp_path, monkeypatch, draft_id, status):
    import json
    from live_contentops.native_neo_executor_v1 import NativeNeoExecutor
    co, store, plan = coordinator(tmp_path, monkeypatch, DraftTransport())
    co.save_substack_draft("controlled-run", plan)
    dispatch = store.list_platform_dispatches()[0]
    store.set_dispatch_status(dispatch["dispatch_id"], status)
    value = json.loads(store.get_outbox_message(dispatch["message_id"])["payload"])
    target = {"draft_id": draft_id,
              "editor_url": "https://capitalchronicle.substack.com/publish/post/" + draft_id,
              "purpose": "RESTORE_BOUND_MEDIA_CREDIT"}
    value["existing_draft_target"] = target
    authorization = {**auth(), "dispatch_attempt_identity": dispatch["dispatch_id"],
                     "payload_hash": value["destination_plan"]["payload_hash"], "existing_draft_target": target}
    request = NeoDestinationHandoff().request(destination="substack", action="SAVE_DRAFT",
        intent=value, authorization_context=authorization)
    executor = NativeNeoExecutor(store, operation_id="controlled-run", output_dir=tmp_path,
                                 native_invocation_id="controlled-native", allow_publish=True)
    monkeypatch.setattr(executor, "readiness", lambda surface: {"authenticated": True, "native_executor_bound": True})
    with pytest.raises(NativeNeoInputRequired):
        executor(request)
    if draft_id == "123" and status == OWNER_RETAINED_DRAFT_NO_PUBLISH:
        assert executor.begin(request["request_sha256"])["request"]["existing_draft_target"] == target
        with pytest.raises(ValueError, match="ALREADY_CLAIMED"):
            executor.begin(request["request_sha256"])
        assert executor(request)["status"] == "UNKNOWN_WRITE"
    else:
        with pytest.raises(ValueError, match="EXACT_RETAINED_SUBSTACK_DRAFT_REQUIRED|EXACT_COORDINATOR_PENDING_DISPATCH"):
            executor.begin(request["request_sha256"])
    assert len(store.list_platform_dispatches()) == 1


def test_native_draft_requires_current_same_writer_final_review(tmp_path, monkeypatch):
    from test_native_desktop_publication_v1 import seeded
    from live_contentops.native_desktop_publication_v1 import NativeReviewedPublication
    store, binding, rollout, _, _ = seeded(tmp_path, monkeypatch, final_visual=False)
    continuation = NativeReviewedPublication(store, binding, rollout=rollout,
                                            native_invocation_id="controlled-native")
    with pytest.raises(ValueError, match="FINAL_MAX_VISUAL"):
        continuation.save_draft()
    assert store.list_platform_dispatches() == []


def test_native_claimed_draft_lost_return_cannot_create_a_second_draft(tmp_path, monkeypatch):
    from live_contentops.native_neo_executor_v1 import NativeNeoExecutor
    from datetime import datetime, timezone
    co, store, plan = coordinator(tmp_path, monkeypatch, None)
    executor = NativeNeoExecutor(store, operation_id="controlled-run", output_dir=tmp_path,
                                 native_invocation_id="controlled-native", allow_publish=True)
    co.transport_runtime = CanonicalDestinationTransportRuntimeV1(neo_transport=NeoDestinationHandoff(native_executor=executor))
    first = co.save_substack_draft("controlled-run", plan)
    request = first["native_tool_request"]["request"]
    assert request["action"] == "SAVE_DRAFT"
    assert not first["native_tool_request"]["public_write_authorized"]
    assert first["native_tool_request"]["external_draft_write_authorized"]
    # Install the actual simulated identity probe return through the native protocol.
    with pytest.raises(NativeNeoInputRequired) as probe:
        executor.begin(request["request_sha256"])
    packet = probe.value.request
    h = packet["request"]["request_sha256"]
    executor.begin(h)
    executor.submit(h, {"tool_request_sha256": packet["tool_request_sha256"],
        "tool_observation": {"tool_name": "mcp__browseros_neo__run", "native_invocation_id": "controlled-native",
          "surface": "CODEX_NATIVE_SUBAGENT", "observation_source": "CONTROLLED_TEST_NOT_BROWSER_PROOF",
          "observed_at_utc": datetime.now(timezone.utc).isoformat()},
        "result": {"request_sha256": h, "authenticated": True,
                   "observed_identity": "capitalchronicle.substack.com"}})
    executor.begin(request["request_sha256"])
    result = co.save_substack_draft("controlled-run", plan)
    assert result["state"] == "UNKNOWN_WRITE"
    assert len(store.list_platform_dispatches()) == 1
    assert not co.save_substack_draft("controlled-run", plan)["new_draft_call"]
