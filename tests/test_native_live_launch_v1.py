"""Disposable authority/recovery contracts, never real provider/publication proof."""
import json
from datetime import datetime, timezone

import pytest

from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_publication_v1 import live_publication_policy, scheduled_publication_authority
from live_contentops.publication_coordinator_v1 import (
    DISPATCH_CONFIRMED, EXTERNAL_REMOVAL_REPORTED_NO_RETRY, OWNER_RETAINED_DRAFT_NO_PUBLISH,
    RECONCILED_ABSENT_SAFE_TO_RETRY, UNKNOWN_WRITE,
)
from test_native_newsroom_owner_operation_v1 import entry
from test_publication_coordinator_v1 import _coordinator, _plan, _set_mode


def live_setup(tmp_path, monkeypatch):
    monkeypatch.setattr("live_contentops.llm_operator_control_v1.assert_llm_operator_execution_enabled", lambda: None)
    store = ContentOpsDurableStore(tmp_path / "production.sqlite3")
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    rollout = {"schema_version": "contentops.native_desktop_rollout.v1", "public_write_authority": True,
        "store_path": str(store.db_path), "editorial_output_root": str(tmp_path / "outputs"),
        "published_output_root": str(tmp_path / "outputs"), "feed_pointer_path": str(tmp_path / "feed.json"),
        "live_authority": {"scope": "V1_NATIVE_PUBLICATION", "thread_id": "human-thread",
            "turn_id": "human-turn", "message_id": "human-message", "not_before_utc": "2026-10-27T00:00:00Z"}}
    profile = {"schema_version": "contentops.native_desktop_operator_profile.v1"}
    return store, rollout, profile


def registered(store, binding):
    work = "cc-opportunity-" + sha256_of(binding["run_id"])
    store.create_work_item(story_id=work, work_item_id=work, title="Controlled live operation", target_surface="TEST")
    store.register_outbox_message(message_id="native-operation-binding-" + sha256_of(binding["run_id"]),
        work_item_id=work, destination="internal:native-desktop-editorial",
        payload=canonical_bytes(binding).decode(), status="EDITORIAL_INTERNAL")


def test_live_entry_uses_original_store_current_cutoff_and_same_binding_without_window(tmp_path, monkeypatch):
    store, rollout, profile = live_setup(tmp_path, monkeypatch)
    module = entry()
    request = "Write one defensible current story under the admitted live owner grant."
    stamp = datetime(2026, 10, 27, 3, tzinfo=timezone.utc)
    path, binding = module.resolve_owner_operation(profile, operation_id="current-live", request=request,
        live_rollout=rollout, now=stamp)
    assert path.parent == tmp_path / "outputs/owner-manual/current-live"
    assert binding["owner_manual_validation"] is False and binding["owner_manual_live"] is True
    assert binding["store_path"] == str(store.db_path) and binding["cutoff_utc"] == "2026-10-27T03:00:00Z"
    assert "window_id" not in binding and "automation_id" not in binding
    assert module.resolve_owner_operation(profile, operation_id="current-live", live_rollout=rollout)[1] == binding
    assert store.list_outbox_messages() == []
    registered(store, binding)
    scheduled_publication_authority(store, binding, rollout)
    with pytest.raises(ValueError, match="REQUEST_CHANGED"):
        module.resolve_owner_operation(profile, operation_id="current-live", live_rollout=rollout, request=request+" Changed scope")


def test_live_entry_needs_both_grant_and_applied_operating_control(tmp_path, monkeypatch):
    store, rollout, profile = live_setup(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="OWNER_LIVE_ACTIVATION"):
        entry().resolve_owner_operation(profile, operation_id="no-grant", request="One current substantive article please.",
            live_rollout={**rollout, "public_write_authority": False})
    _set_mode(store, "SHADOW_ONLY")
    with pytest.raises(ValueError, match="OPERATING_MODE_BLOCKED"):
        entry().resolve_owner_operation(profile, operation_id="no-mode", request="One current substantive article please.", live_rollout=rollout)
    assert not (tmp_path / "outputs").exists()


@pytest.mark.parametrize("change", ["authority", "store", "output", "window"])
def test_live_dispatch_rejects_redirected_or_fabricated_registered_binding(tmp_path, monkeypatch, change):
    store, rollout, profile = live_setup(tmp_path, monkeypatch)
    _, binding = entry().resolve_owner_operation(profile, operation_id="changed-"+change,
        request="One current substantive article please.", live_rollout=rollout)
    if change == "authority":
        binding["live_authority_sha256"] = "changed"
    if change == "store":
        binding["store_path"] = str(tmp_path / "other.sqlite3")
    if change == "output":
        binding["output_dir"] = str(tmp_path / "outside")
    if change == "window":
        binding["window_id"] = "invented-scheduled-window"
    registered(store, binding)
    with pytest.raises(ValueError, match="EXACT_OWNER_LIVE"):
        scheduled_publication_authority(store, binding, rollout)


def test_pre_activation_examples_and_manual_proofs_stay_private(tmp_path, monkeypatch):
    store, rollout, _ = live_setup(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="PRE_ACTIVATION"):
        live_publication_policy(rollout, cutoff_utc="2026-10-26T14:00:00Z")
    with pytest.raises(ValueError, match="OWNER_MANUAL_PUBLICATION_NOT_AUTHORIZED"):
        scheduled_publication_authority(store, {"owner_manual_validation": True}, rollout)


def test_completed_pre_activation_slot_does_not_become_a_new_live_send(tmp_path, monkeypatch):
    from test_native_desktop_publication_v1 import seeded
    from live_contentops.native_desktop_schedule_binding_v1 import _issued_state
    store, binding, rollout, _, _ = seeded(tmp_path, monkeypatch)
    rollout["live_authority"] = {"not_before_utc": "2026-10-27T00:00:00Z"}
    state = _issued_state(store, rollout, {"capacity": 1}, binding,
        tmp_path / "native_operation_binding.json")
    assert state["classification"] == "NATIVE_WINDOW_OPERATION_COMPLETE"
    assert state["source_requests"] == state["model_invocations"] == 0


def historical_dispatch(tmp_path, *, status=DISPATCH_CONFIRMED):
    store, transport, coordinator = _coordinator(tmp_path)
    plan = _plan("substack")
    coordinator.register_plan("work-1", plan)
    ids = coordinator._ids("work-1", plan["plan_hash"], "substack")
    store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"],
        platform="substack", status=status, public_object_id="old-object",
        public_object_url="https://capitalchronicle.substack.com/p/old-removed")
    store.register_reconciliation(reconciliation_id=ids["reconciliation_id"], work_item_id="work-1", status=status)
    store.register_readback(readback_id="original-proof", dispatch_id=ids["dispatch_id"], readback_data='{"historical_confirmation":true}')
    observation = {"destination": "substack", "public_object_id": "old-object",
        "authority_ref": "human-authority", "observation_ref": "cleanup-chat/actual-turn",
        "observed_at_utc": "2026-10-27T03:00:00Z", "observation_basis": "POSTING_LIST_EMPTY",
        "exact_object_absence_verified": False}
    return store, transport, coordinator, plan, ids, observation


@pytest.mark.parametrize("status,disposition", [(DISPATCH_CONFIRMED, EXTERNAL_REMOVAL_REPORTED_NO_RETRY),
    (RECONCILED_ABSENT_SAFE_TO_RETRY, OWNER_RETAINED_DRAFT_NO_PUBLISH)])
def test_removed_and_retained_draft_history_never_retries(tmp_path, status, disposition):
    store, transport, coordinator, plan, ids, observation = historical_dispatch(tmp_path, status=status)
    original = store.get_platform_dispatch(ids["dispatch_id"])
    first = coordinator.reconcile_owner_removed_object(ids["dispatch_id"], disposition=disposition, observation=observation)
    assert coordinator.reconcile_owner_removed_object(ids["dispatch_id"], disposition=disposition, observation=observation) == first
    current = store.get_platform_dispatch(ids["dispatch_id"])
    assert {k:v for k,v in current.items() if k != "status"} == {k:v for k,v in original.items() if k != "status"}
    readbacks = store.list_readbacks_for_dispatch(ids["dispatch_id"])
    assert len(readbacks) == 2 and any(r["readback_id"] == "original-proof" for r in readbacks)
    added = next(json.loads(r["readback_data"]) for r in readbacks if r["readback_id"] != "original-proof")
    assert added["previous_dispatch"]["status"] == status and added["exact_object_absence_independently_verified"] is False
    assert coordinator.recover_pending()["backlog_remaining"] == 0
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    coordinator.publish_plan("work-1", plan)
    assert transport.publish_calls == [] and transport.readback_calls == []


def test_cleanup_list_observation_cannot_erase_unknown_write(tmp_path):
    store, transport, coordinator, _, ids, observation = historical_dispatch(tmp_path, status=UNKNOWN_WRITE)
    with pytest.raises(ValueError, match="EXACT_READBACK"):
        coordinator.reconcile_owner_removed_object(ids["dispatch_id"], disposition=EXTERNAL_REMOVAL_REPORTED_NO_RETRY, observation=observation)
    assert store.get_platform_dispatch(ids["dispatch_id"])["status"] == UNKNOWN_WRITE
    assert len(store.list_readbacks_for_dispatch(ids["dispatch_id"])) == 1 and transport.publish_calls == []


def test_wrong_removed_object_cannot_change_history(tmp_path):
    store, _, coordinator, _, ids, observation = historical_dispatch(tmp_path)
    with pytest.raises(ValueError, match="EXACT_OBJECT"):
        coordinator.reconcile_owner_removed_object(ids["dispatch_id"], disposition=EXTERNAL_REMOVAL_REPORTED_NO_RETRY,
            observation={**observation, "public_object_id": "different-object"})
    assert store.get_platform_dispatch(ids["dispatch_id"])["status"] == DISPATCH_CONFIRMED
