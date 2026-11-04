"""A completed first send binds the exact finalized envelope without another send."""
import json
from types import SimpleNamespace
import pytest
from test_native_neo_executor_v1 import setup, intent
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator


@pytest.mark.parametrize("changed", [False, True])
def test_completed_return_requires_exact_original_or_finalized_intent(tmp_path, monkeypatch, changed):
    store, _ = setup(tmp_path)
    original = intent()
    finalized = {**original, "rematerialization_model_call_count": 0}
    co = DurablePublicationCoordinator(store=store, transport_runtime=None)
    ids = co._ids("work", "plan", "substack")
    store.register_outbox_message(message_id=ids["message_id"], work_item_id="work", destination="substack",
        payload=json.dumps(original), status="NATIVE_NEO_TOOL_PENDING")
    store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"],
        platform="substack", status="NATIVE_NEO_TOOL_PENDING")
    request_hash = "a" * 64
    request = {"action": "PUBLISH", "destination": "substack", "expected_identity": "capitalchronicle.substack.com",
        "dispatch_attempt_identity": ids["dispatch_id"], "work_item_id": "work", "request_sha256": request_hash,
        "intent_sha256": sha256_of({**finalized, "payload": "Changed fact"} if changed else finalized)}
    result = {"status": "SUCCESS", "request_sha256": request_hash, "observed_identity": "capitalchronicle.substack.com",
        "public_object_id": "123", "public_object_url": original["canonical_url"], "native_tool_return_sha256": "b" * 64,
        "native_tool_observation": {"tool_name": "mcp__browseros_neo__run", "native_invocation_id": "controlled"}}
    executor = SimpleNamespace(operation_id="work", native_neo_protocol=True, _claim=lambda *a: True,
        _get=lambda h, kind: {"request": request} if kind == "request" else {"result": result})
    co.transport_runtime = SimpleNamespace(_neo_transport=SimpleNamespace(native_executor=executor),
        finalize_intent=lambda **kw: finalized)
    monkeypatch.setattr(co, "_reconcile", lambda *a: "RECONCILED_CONFIRMED")
    if changed:
        with pytest.raises(ValueError, match="EXACT_COMPLETED_NATIVE_PUBLISH_RETURN_REQUIRED"):
            co.reconcile_completed_native_publish(ids["dispatch_id"], request_hash=request_hash)
        assert store.get_platform_dispatch(ids["dispatch_id"])["public_object_id"] is None
    else:
        result = co.reconcile_completed_native_publish(ids["dispatch_id"], request_hash=request_hash)
        assert result["publish_called"] is False
        assert result["public_object_id"] == "123"
