"""Real coordinator envelopes feed weekly metrics without losing object identity."""
import json

import pytest

from live_contentops.channel_engagement_v1 import weekly_channel_engagement
from live_contentops.newsroom_coverage_v1 import weekly_newsroom_coverage


def inputs(change=None):
    dispatch = {"dispatch_id": "dispatch_a", "message_id": "message-a", "platform": "substack",
                "public_object_id": "123", "public_object_url": "https://capitalchronicle.substack.com/p/test",
                "status": "DISPATCH_CONFIRMED", "dispatched_at": "2026-10-30T10:00:00Z"}
    reconciliation = {"reconciliation_id": "reconciliation_a", "status": "RECONCILED_CONFIRMED"}
    envelope = {"destination": "substack", "dispatch_id": "dispatch_a", "readback": {
        "verified": True, "identity_match": True, "observed_public_object_id": "123",
        "observed_public_object_url": dispatch["public_object_url"]}}
    if change in {"destination", "dispatch_id"}:
        envelope[change] = "wrong"
    elif change:
        envelope["readback"][change] = False if change in {"verified", "identity_match"} else "wrong"
    payload = json.dumps(envelope)
    if change == "malformed":
        payload = "{"
    elif change == "not-an-object":
        payload = "[]"
    readback = {"dispatch_id": "dispatch_a", "readback_data": payload}
    observation = {"dispatch_id": "dispatch_a", "platform": "substack", "public_object_id": "123",
                   "collected_at_utc": "2026-10-30T11:00:00Z", "learning_eligible": 1,
                   "collection_status": "COLLECTED", "metrics_native_json": '{"views":42}',
                   "metric_availability_json": '{"views":"AVAILABLE"}'}
    return dispatch, reconciliation, readback, observation


@pytest.mark.parametrize("change", [None, "destination", "dispatch_id", "verified", "identity_match",
                                   "observed_public_object_id", "observed_public_object_url",
                                   "malformed", "not-an-object"])
def test_coordinator_envelope_reaches_both_weekly_consumers_only_for_the_same_object(change):
    dispatch, reconciliation, readback, observation = inputs(change)
    common = {"dispatches": [dispatch], "reconciliations": [reconciliation],
              "readbacks": [readback], "week_ending": "2026-10-30"}
    engagement = weekly_channel_engagement(**common, observations=[observation])
    channel = next(r for r in engagement["channels"] if r["channel"] == "substack")
    coverage = weekly_newsroom_coverage(**common, outbox=[])
    assert channel["native_counter_sums"] == ({"views": 42} if change is None else None)
    assert sum(day["unclassified_canonicals"] for day in coverage["daily"]) == (1 if change is None else 0)
