"""Complete the measured image-floor no-write through the sole coordinator."""
from datetime import datetime, timezone
import json

import pytest

from live_contentops import plan_analysis_pages_v1 as pages
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator as Coordinator
from test_plan_analysis_pages_cc432 import source  # noqa: F401
from test_plan_analysis_distribution_cc435 import ready  # noqa: F401
from test_publication_coordinator_v1 import FixtureTransport, _set_mode


@pytest.fixture
def refused(ready):
    store, packet, original = ready
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    runtime = FixtureTransport()
    coordinator = Coordinator(store=store, transport_runtime=runtime,
        readiness_provider=lambda d: {"readiness_state": "READY_AUTHENTICATED"},
        clock=lambda: datetime(2026, 11, 14, 5, tzinfo=timezone.utc))
    return store, packet, original, runtime, coordinator


def held_link(refused, destination):
    store, packet, original, runtime, coordinator = refused
    value = pages.register_link(store, packet, original_key=original, destination=destination)
    coordinator.register_plan(value["link_id"], value["plan"])
    ids = coordinator._ids(value["link_id"], value["plan"]["plan_hash"], destination)
    store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"],
        platform=destination, status="DEFINITE_NO_WRITE")
    store.register_reconciliation(reconciliation_id=ids["reconciliation_id"], work_item_id=value["link_id"],
        status="TRADINGVIEW_FIRST_IMAGE_REQUIRED")
    store.set_outbox_status(ids["message_id"], "DEFINITE_NO_WRITE")
    return value, ids


@pytest.mark.parametrize("destination", ["telegram", "substack_notes"])
def test_exact_refused_link_posts_once_without_new_bytes_or_identity(refused, destination):
    store, packet, original, runtime, coordinator = refused
    value, ids = held_link(refused, destination)
    before = store.get_outbox_message(ids["message_id"])["payload"]
    result = pages.repair_image_refused_link(coordinator, value)
    assert result["status"] == "DISPATCH_CONFIRMED", result
    assert runtime.publish_calls == [destination]
    assert store.get_outbox_message(ids["message_id"])["payload"] == before
    assert pages.link_status(store, value)["confirmed"] is True
    assert pages.repair_image_refused_link(coordinator, value)["publish_called"] is False
    assert runtime.publish_calls == [destination]
    proof, = [json.loads(r["readback_data"]) for r in store.list_readbacks_for_dispatch(ids["dispatch_id"])
              if r["readback_id"].startswith("cc584-image-refusal-")]
    assert proof["original_reconciliation"]["status"] == "TRADINGVIEW_FIRST_IMAGE_REQUIRED"


@pytest.mark.parametrize("status", ["UNKNOWN_WRITE", "ATTEMPT_STARTED", "DISPATCH_CONFIRMED"])
def test_uncertain_or_confirmed_link_never_reopens_as_image_refusal(refused, status):
    store, _, _, runtime, coordinator = refused
    value, ids = held_link(refused, "telegram")
    store.set_dispatch_status(ids["dispatch_id"], status)
    result = pages.repair_image_refused_link(coordinator, value)
    assert result["publish_called"] is False
    assert runtime.publish_calls == []
    assert store.get_platform_dispatch(ids["dispatch_id"])["status"] == status


def test_native_write_request_requires_existing_readback(refused):
    store, _, _, runtime, coordinator = refused
    value, ids = held_link(refused, "substack_notes")
    store.register_outbox_message(message_id="existing-native-write", work_item_id=value["link_id"],
        destination="internal:native-neo-tool", payload=json.dumps({"request": {"action": "PUBLISH"}}))
    with pytest.raises(ValueError, match="NATIVE_WRITE_EXISTS_READBACK_REQUIRED"):
        pages.repair_image_refused_link(coordinator, value)
    assert runtime.publish_calls == []
    assert store.get_platform_dispatch(ids["dispatch_id"])["status"] == "DEFINITE_NO_WRITE"
