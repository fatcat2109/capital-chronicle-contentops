"""Decisions 109/112/121: eight article derivatives and the remaining API routes."""
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


def test_full_article_and_repeated_recovery_use_eight_derivatives(tmp_path):
    store, transport, coordinator = _coordinator(tmp_path)
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    plan = _quality_plan()
    result = coordinator.execute_plan("work-1", plan)
    state = coordinator.publication_state("work-1", plan)
    assert state["derivative_confirmed_count"] == len(V1_REQUIRED_DERIVATIVE_DESTINATIONS)
    assert not state["recovery_required_destinations"]
    assert set(V1_REQUIRED_DERIVATIVE_DESTINATIONS) == {"telegram", "x", "discord", "linkedin", "facebook_page", "instagram_business", "threads", "youtube"}
    for _ in range(3):
        assert coordinator.recover_pending()["backlog_remaining"] == 0
    x = store.list_outbox_messages(destination="x")
    assert len(x) == 1 and x[0]["status"] == DISPATCH_CONFIRMED
    assert transport.publish_calls.count("x") == 1 and transport.readback_calls.count("x") == 1
    assert len([d for d in store.list_platform_dispatches() if d["platform"] == "x"]) == 1
    assert len(store.list_outbox_messages(destination="youtube")) == 1
    assert transport.publish_calls.count("youtube") == transport.readback_calls.count("youtube") == 1
    with store.get_read_only_connection() as conn:
        assert conn.execute("SELECT count(*) FROM incidents WHERE severity='DISPATCH_FAILURE'").fetchone()[0] == 0
    assert not any(r["status"] == "X_NON_API_AUTOMATION_PROHIBITED" for r in store.get_reconciliations_for_work_item("work-1"))


@pytest.mark.parametrize("status", [DISPATCH_CONFIRMED, UNKNOWN_WRITE])
@pytest.mark.parametrize("destination", ["youtube", "linkedin_company"])
def test_existing_identity_is_preserved_and_uncertainty_read_back(tmp_path, status, destination):
    store, transport, coordinator = _coordinator(tmp_path)
    plan = _quality_plan()
    registration = next(r for r in coordinator.register_plan("work-1", plan)["registered"]
        if r["destination"] == destination)
    store.register_platform_dispatch(dispatch_id=registration["dispatch_id"], message_id=registration["message_id"],
        platform=destination, status=status, public_object_id="existing-real-id", public_object_url="https://x.com/Capitalnicle/status/1")
    store.set_dispatch_status(registration["dispatch_id"], status)
    before = dict(store.get_platform_dispatch(registration["dispatch_id"]))
    recovery = coordinator.recover_pending()
    assert recovery["backlog_remaining"] == 0
    after = store.get_platform_dispatch(registration["dispatch_id"])
    assert after["public_object_id"] == before["public_object_id"]
    assert after["public_object_url"] == before["public_object_url"]
    assert destination not in transport.publish_calls
    assert transport.readback_calls.count(destination) == 1


@pytest.mark.parametrize("destination", ["youtube", "linkedin_company"])
def test_reopened_route_never_backfills_a_closed_policy_no_write(tmp_path, monkeypatch, destination):
    store, transport, coordinator = _coordinator(tmp_path)
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    plan = _quality_plan()
    cause = "YOUTUBE_NON_API_AUTOMATION_PROHIBITED" if destination == "youtube" else "LINKEDIN_NON_API_AUTOMATION_PROHIBITED"
    with monkeypatch.context() as old_policy:
        old_policy.setitem(neo.NON_API_AUTOMATION_PROHIBITED, destination, cause)
        registered = coordinator.register_plan("work-1", plan)["registered"]
        row = next(r for r in registered if r["destination"] == destination)
        coordinator._dispatch_message(store.get_outbox_message(row["message_id"]),
            canonical_url="https://capitalchronicle.substack.com/p/test")
    row = next(r for r in registered if r["destination"] == destination)
    before = dict(store.get_platform_dispatch(row["dispatch_id"]))
    assert before["status"] == DEFINITE_NO_WRITE
    message = store.get_outbox_message(row["message_id"])
    result = coordinator._dispatch_message(message, canonical_url="https://capitalchronicle.substack.com/p/test")
    coordinator.recover_pending()
    assert result["publish_called"] is False
    assert store.get_platform_dispatch(row["dispatch_id"]) == before
    assert destination not in transport.publish_calls + transport.readback_calls


def test_status_and_call_cards_do_not_add_company_or_youtube():
    from live_contentops import plan_call_cards_v1 as cards
    assert not {"linkedin_company", "youtube"} & set(posts.API_DESTINATIONS)
    assert not {"linkedin_company", "youtube"} & set(cards.API_DESTINATIONS)


def test_x_probes_and_status_agent_flags_are_restored():
    calls = []
    def probe(surface):
        calls.append(surface)
        return {"authenticated": True, "public_handle": "@Capitalnicle",
                "native_executor_bound": True, "proof_fresh": True, "observation_sha256": "a" * 64}
    manager = DestinationReadinessManager(neo_readiness_provider=probe)
    for surface in ("X_POST", "X_THREAD"):
        assert manager.probe_surface(surface)["readiness_state"] == "READY_AUTHENTICATED"
    assert calls == ["X_POST", "X_THREAD"]
    cli = Path(__file__).parents[1] / "scripts/plan_status_posts.py"
    result = subprocess.run([sys.executable, str(cli), "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert all(flag in result.stdout for flag in ("--pending-x", "--x-start", "--x-begin", "--x-submit",
                                                 "--pending-notes", "--notes-start"))


def test_notice_reaches_public_copy_and_fact_card():
    from live_contentops.fact_card_design_v1 import CardSpec
    assert PUBLIC_NOTICE == "Capital Chronicle offers analysis only, not financial advice or recommendations."
    check_publication_copy({"notice": PUBLIC_NOTICE})
    assert CardSpec.__dataclass_fields__["notice"].default == PUBLIC_NOTICE


def test_new_status_post_and_notes_keep_notice_within_platform_limits():
    # Already admitted public fields: no Main process or external source.
    row = {"symbol": "XAUUSD", "to": "WAITING", "at_utc": "2026-11-05T11:45:00Z",
        "plan": {"direction": "bullish", "zone_low": 4070, "zone_high": 4085,
            "invalidation_level": 4055, "valid_until_utc": "2026-11-06T12:45:00Z"}}
    output = posts.compose(row)
    if output.get("status") == "COMPOSED":
        payloads = posts.destination_payloads(output, card_id="bound-card")
        for destination in posts.API_DESTINATIONS:
            parts = payloads[destination].get("parts") or [payloads[destination]["full_text"]]
            assert PUBLIC_NOTICE in "\n".join(parts)
            assert all(len(part) <= posts.LIMITS[destination] for part in parts)
    else:
        pytest.fail(str(output))


def test_quality_pack_maps_eight_and_detects_a_missing_destination():
    from live_contentops.editorial_traceability_quality_pack_v1 import _derivative_mapping
    destinations = list(V1_REQUIRED_DERIVATIVE_DESTINATIONS)
    receipt = {"classification": "SHADOW_CONFIRMED", "derivative_shadow": {
        "count": len(destinations), "destinations": destinations}}
    packages = [{"destination": d, "payload_sha256": f"{i + 1:064x}", "public_write_performed": False}
        for i, d in enumerate(destinations)]
    mapping, blockers = _derivative_mapping(receipt, packages, ["claim"], ["a" * 64])
    assert not blockers and len(mapping) == len(V1_REQUIRED_DERIVATIVE_DESTINATIONS)
    _, blockers = _derivative_mapping(receipt, packages[:-1], ["claim"], ["a" * 64])
    assert "derivative_count_or_destination_mismatch" in blockers


@pytest.mark.parametrize("action", ["READBACK", "VERIFY_IDENTITY"])
def test_saved_x_browser_request_is_available_to_the_agent(tmp_path, action):
    from live_contentops.native_neo_executor_v1 import NativeNeoExecutor, SCHEMA
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    store, _, _ = _coordinator(tmp_path)
    executor = NativeNeoExecutor(store, operation_id="op", output_dir=tmp_path,
        native_invocation_id="controlled", allow_publish=True)
    request = {"destination": "x", "action": action, "work_item_id": "work-1"}
    key = request["request_sha256"] = sha256_of(request)
    executor._put(key, "request", {"schema_version": SCHEMA, "operation_id": "op", "request": request, "tool_request_sha256": key}, "work-1")
    assert [p["request"]["request_sha256"] for p in executor.pending()] == [key]
    assert executor.begin(key)["request"]["request_sha256"] == key
    assert executor._get(key, "started") is not None


def test_restored_x_uncertainty_requires_exact_readback():
    outcomes = {d: {"status": DISPATCH_CONFIRMED, "reconciliation_status": "RECONCILED_CONFIRMED",
        "public_object_id": d + "-real", "public_object_url": "https://capitalchronicle.substack.com/p/exact"}
        for d in V1_REQUIRED_PUBLICATION_DESTINATIONS}
    outcomes["x"] = {"status": UNKNOWN_WRITE, "public_object_id": "unchanged-id"}
    result = DurablePublicationCoordinator.publication_totals(outcomes)
    assert result["derivative_confirmed_count"] == len(V1_REQUIRED_DERIVATIVE_DESTINATIONS) - 1
    assert "x" in result["recovery_required_destinations"]
    assert result["retired_x_unknown_count"] == 0 and result["unknown_write_count"] == 1
    assert result["unknown_write_detected"]


def test_required_set_tracks_barred_transports_and_keeps_official_apis(monkeypatch):
    from dataclasses import replace
    from live_contentops import destination_transport_registry_v1 as registry
    assert registry.required_derivative_destinations() == ("telegram", "x", "discord", "linkedin", "facebook_page", "instagram_business", "threads", "youtube")
    assert "linkedin" not in registry.barred_browser_destinations()
    assert "instagram_business" not in registry.barred_browser_destinations()
    monkeypatch.setitem(registry.SURFACE_REGISTRY, "THREADS_POST",
        replace(registry.SURFACE_REGISTRY["THREADS_POST"], transport_type="BROWSEROS_NEO_MCP"))
    monkeypatch.setitem(neo.NON_API_AUTOMATION_PROHIBITED, "threads", "CONTROLLED_NEXT_PLATFORM_BAR")
    assert "threads" not in registry.required_derivative_destinations()
    assert registry.barred_browser_destinations()["threads"] == "CONTROLLED_NEXT_PLATFORM_BAR"
