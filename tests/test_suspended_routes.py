"""Ops Product, 11 Nov 2026: a suspended account stops its own routes only."""
import json

from live_contentops import neo_destination_handoff_v1 as handoff


def test_no_file_and_the_live_file_under_pytest_suspend_nothing(tmp_path, monkeypatch):
    assert handoff.suspended_routes() == {}
    monkeypatch.setattr(handoff, "SUSPENDED_ROUTES_FILE", tmp_path / "absent.json")
    assert handoff.suspended_routes() == {}
    assert handoff._prohibited_write("substack") is None


def test_a_suspended_route_is_a_definite_no_write_and_other_routes_go_on(tmp_path, monkeypatch):
    control = tmp_path / "suspended_routes.json"
    control.write_text(json.dumps({"substack": "SUBSTACK_ACCOUNT_SUSPENDED",
                                   "substack_notes": "SUBSTACK_ACCOUNT_SUSPENDED"}), encoding="utf-8")
    monkeypatch.setattr(handoff, "SUSPENDED_ROUTES_FILE", control)
    for destination in ("substack", "substack_notes"):
        refused = handoff._prohibited_write(destination)
        assert refused["definite_no_write"] and refused["reason_code"] == "SUBSTACK_ACCOUNT_SUSPENDED"
        assert handoff.NeoDestinationHandoff().publish(destination=destination, intent={"work_item_id": "w"},
                                                       authorization_context={})["definite_no_write"]
    assert handoff._prohibited_write("x") is None
    assert "substack" not in handoff.NON_API_AUTOMATION_PROHIBITED
