from datetime import datetime, timedelta, timezone
import json

import pytest

from live_contentops.audience_feedback_v1 import SCHEMA, STOP, project_audience, post_type, stopped_type_for_new_message
from tests.test_audience_collection_cc402 import seed

NOW = datetime(2026, 11, 12, 6, tzinfo=timezone.utc)


def history():
    dispatches, reconciliations, readbacks, observations, metadata = [], [], [], [], {}
    for i, days in enumerate((20, 13, 6)):
        dispatch = {"dispatch_id": f"dispatch_{i}", "platform": "threads", "public_object_id": str(i + 100),
            "public_object_url": f"https://example.test/{i}", "status": "DISPATCH_CONFIRMED",
            "dispatched_at": (NOW - timedelta(days=days)).isoformat()}
        dispatches.append(dispatch)
        reconciliations.append({"reconciliation_id": f"reconciliation_{i}", "status": "RECONCILED_CONFIRMED"})
        readbacks.append({"dispatch_id": dispatch["dispatch_id"], "readback_data": '{"verified":true}'})
        metadata[dispatch["dispatch_id"]] = "Note"
        observations.append({"observation_id": f"observation-{i}", "dispatch_id": dispatch["dispatch_id"],
            "work_item_id": f"work-{i}", "platform": "threads", "public_object_id": str(i + 100),
            "collected_at_utc": NOW.isoformat(), "collection_status": "COLLECTED",
            "metrics_native_json": '{"views":0}', "metric_availability_json": '{"views":"AVAILABLE"}'})
    return dict(dispatches=dispatches, reconciliations=reconciliations, readbacks=readbacks,
                observations=observations, metadata=metadata, now=NOW)


def test_three_complete_weeks_of_zero_readers_stop_type_and_keep_evidence():
    args = history()
    result = project_audience(**args)
    policy = result["post_type_policy"]["Note"]
    assert policy["state"] == "STOPPED" and policy["reason"] == STOP
    assert policy["weekly_objects"] == [1, 1, 1] and len(policy["observation_ids"]) == 3
    assert result["rows"][0]["median_views"] == 0
    assert result["hours"][0]["hour_et"] == 1
    # A stopped type does not silently restart when its old posts age out.
    later = project_audience(**{**args, "now": NOW + timedelta(days=30)}, previous=result)
    assert later["post_type_policy"]["Note"] == policy
    args["observations"][-1]["metrics_native_json"] = '{"views":1}'
    assert project_audience(**args, previous=result)["post_type_policy"]["Note"]["state"] == "CONTINUE"


@pytest.mark.parametrize("defect", ["missing_views", "positive_views", "positive_likes", "missing_week", "unknown_write", "future_clock"])
def test_missing_or_positive_data_never_becomes_three_weeks_without_readers(defect):
    args = history()
    row = args["observations"][0]
    if defect == "missing_views":
        row["metrics_native_json"], row["metric_availability_json"] = "{}", '{"views":"NOT_EXPOSED"}'
    elif defect == "positive_views":
        row["metrics_native_json"] = '{"views":1}'
    elif defect == "positive_likes":
        row["metrics_native_json"], row["metric_availability_json"] = '{"views":0,"likes":1}', '{"views":"AVAILABLE","likes":"AVAILABLE"}'
    elif defect == "missing_week":
        args["dispatches"].pop(0)
    elif defect == "unknown_write":
        args["dispatches"][0]["status"] = "UNKNOWN_WRITE"
    else:
        row["collected_at_utc"] = (NOW + timedelta(seconds=1)).isoformat()
    assert project_audience(**args)["post_type_policy"]["Note"]["state"] == "CONTINUE"


def test_shared_object_counts_once_in_desk_rows_and_keeps_et_publication_hour():
    args = history()
    args["dispatches"].append({**args["dispatches"][-1], "dispatch_id": "dispatch_shared"})
    args["reconciliations"].append({"reconciliation_id": "reconciliation_shared", "status": "RECONCILED_CONFIRMED"})
    args["readbacks"].append({"dispatch_id": "dispatch_shared", "readback_data": '{"verified":true}'})
    args["metadata"]["dispatch_shared"] = "Note"
    result = project_audience(**args)
    assert len(result["rows"][0]["posts"]) == 1


def test_export_writes_installed_desk_contract_with_platform_lines(tmp_path):
    from scripts.export_contentops_weekly_engagement import export_weekly_engagement
    store = seed(tmp_path)
    result = export_weekly_engagement(store.db_path, "2026-11-12", tmp_path / "weekly")
    desk = json.loads((tmp_path / "audience-weekly/latest.json").read_bytes())
    assert desk["schema_version"] == SCHEMA and len(desk["digest_lines"]) == 10
    assert result["desk"] == str(tmp_path / "audience-weekly/latest.json")
    assert {r["platform"] for r in desk["rows"]} == {"threads", "telegram"}


def test_fresh_message_uses_policy_but_issued_messages_keep_their_exact_recovery(tmp_path):
    store = seed(tmp_path)
    path = tmp_path / "audience-weekly/latest.json"
    path.parent.mkdir()
    policy = project_audience(**history())
    policy["input_store"] = str(store.db_path.resolve())
    path.write_text(json.dumps(policy), encoding="utf-8")
    intent = {"post_type": "Note"}
    assert stopped_type_for_new_message(store, {"created_at": (NOW + timedelta(seconds=1)).isoformat()}, intent)["reason_code"] == STOP
    assert stopped_type_for_new_message(store, {"created_at": NOW.isoformat()}, intent) is None
    assert stopped_type_for_new_message(store, {"created_at": (NOW - timedelta(seconds=1)).isoformat()}, intent) is None
    assert post_type({"plan_status_post": "source"}, {"kind": "setup"}) == "Call"


def test_coordinator_stops_fresh_type_before_transport_and_preserves_existing_attempt(tmp_path, monkeypatch):
    from tests.test_publication_coordinator_v1 import _coordinator, _plan
    from live_contentops import publication_coordinator_v1 as module
    store, runtime, coordinator = _coordinator(tmp_path)
    registered = coordinator.register_plan("work-1", _plan("threads"))["registered"][0]
    message = store.get_outbox_message(registered["message_id"])
    calls = []
    from live_contentops import audience_feedback_v1 as feedback
    monkeypatch.setattr(feedback, "stopped_type_for_new_message", lambda *args: calls.append(args) or {"reason_code": STOP})
    result = coordinator._dispatch_message(message, canonical_url=None)
    assert result["status"] == module.DEFINITE_NO_WRITE and result["reason_code"] == STOP
    assert runtime.publish_calls == [] and len(calls) == 1
    monkeypatch.setattr(feedback, "stopped_type_for_new_message", lambda *args: pytest.fail("existing dispatch must retain recovery"))
    coordinator._dispatch_message(message, canonical_url=None)
