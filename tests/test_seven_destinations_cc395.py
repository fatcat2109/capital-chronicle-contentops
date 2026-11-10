"""Decision 109: exercise the coordinator, recovery and public copy consumers."""
import json
import subprocess
import sys
from pathlib import Path

import pytest
from live_contentops import neo_destination_handoff_v1 as neo
from live_contentops import plan_status_posts_v1 as posts
from live_contentops.destination_transport_registry_v1 import (DestinationReadinessManager,
    V1_REQUIRED_DERIVATIVE_DESTINATIONS, V1_REQUIRED_PUBLICATION_DESTINATIONS)
from live_contentops.event_article_guard_v1 import PUBLIC_NOTICE, check_publication_copy
from live_contentops.publication_coordinator_v1 import (DISPATCH_CONFIRMED, UNKNOWN_WRITE,
    DEFINITE_NO_WRITE, DurablePublicationCoordinator)
from test_publication_coordinator_v1 import _coordinator, _quality_plan, _set_mode, _plan


def fail(*args, **kwargs):
    pytest.fail("retired X route reached an external tool")


def test_full_article_and_repeated_recovery_use_seven_derivatives(tmp_path, monkeypatch):
    # Other destination permissions are simulated; X uses the real decision 109 policy.
    monkeypatch.setattr(neo, "NON_API_AUTOMATION_PROHIBITED", {"x": "X_NON_API_AUTOMATION_PROHIBITED"})
    store, transport, coordinator = _coordinator(tmp_path)
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    plan = _quality_plan()
    result = coordinator.execute_plan("work-1", plan)
    state = coordinator.publication_state("work-1", plan)
    assert state["derivative_confirmed_count"] == 7
    assert not state["recovery_required_destinations"]
    assert set(V1_REQUIRED_DERIVATIVE_DESTINATIONS) == {"telegram", "discord", "linkedin", "facebook_page", "instagram_business", "threads", "youtube"}
    for _ in range(3):
        assert coordinator.recover_pending()["backlog_remaining"] == 0
    x = store.list_outbox_messages(destination="x")
    assert len(x) == 1 and x[0]["status"] == DEFINITE_NO_WRITE
    assert "x" not in transport.publish_calls and "x" not in transport.readback_calls
    assert len([d for d in store.list_platform_dispatches() if d["platform"] == "x"]) == 1
    with store.get_read_only_connection() as conn:
        assert conn.execute("SELECT count(*) FROM incidents WHERE severity='DISPATCH_FAILURE'").fetchone()[0] == 0
    assert any(r["status"] == "X_NON_API_AUTOMATION_PROHIBITED" for r in store.get_reconciliations_for_work_item("work-1"))


@pytest.mark.parametrize("status", [DISPATCH_CONFIRMED, UNKNOWN_WRITE])
def test_existing_x_identity_and_uncertainty_survive_without_neo(tmp_path, status):
    store, transport, coordinator = _coordinator(tmp_path)
    plan = _plan("x")
    registration = coordinator.register_plan("work-1", plan)["registered"][0]
    store.register_platform_dispatch(dispatch_id=registration["dispatch_id"], message_id=registration["message_id"],
        platform="x", status=status, public_object_id="existing-real-id", public_object_url="https://x.com/Capitalnicle/status/1")
    store.set_dispatch_status(registration["dispatch_id"], status)
    before = dict(store.get_platform_dispatch(registration["dispatch_id"]))
    coordinator.recover_pending()
    after = store.get_platform_dispatch(registration["dispatch_id"])
    assert after == before
    assert not transport.publish_calls and not transport.readback_calls


def test_x_probes_readback_and_status_agent_route_are_retired():
    manager = DestinationReadinessManager(neo_readiness_provider=fail)
    for surface in ("X_POST", "X_THREAD"):
        assert manager.probe_surface(surface)["sanitized_detail"]["reason_code"] == "X_NON_API_AUTOMATION_PROHIBITED"
    assert neo.NeoDestinationHandoff(native_executor=fail).readback(destination="x", intent={}, public_object_id="1", public_object_url=None)["verified"] is False
    assert posts.pending_x(None) == []
    assert posts.start_x(None, "key", native_invocation_id="test")["x"]["reason_code"] == "X_NON_API_AUTOMATION_PROHIBITED"
    cli = Path(__file__).parents[1] / "scripts/plan_status_posts.py"
    result = subprocess.run([sys.executable, str(cli), "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert not any(flag in result.stdout for flag in ("--pending-x", "--x-start", "--x-begin", "--x-submit"))


def test_notice_reaches_public_copy_and_fact_card():
    from live_contentops.fact_card_design_v1 import CardSpec
    assert PUBLIC_NOTICE == "Capital Chronicle offers analysis only, not financial advice or recommendations."
    check_publication_copy({"notice": PUBLIC_NOTICE})
    assert CardSpec.__dataclass_fields__["notice"].default == PUBLIC_NOTICE
