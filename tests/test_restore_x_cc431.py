"""Decision 112: restored consumer, current identity and exact no-write recovery."""
import json
from datetime import timedelta

import pytest

from live_contentops import neo_destination_handoff_v1 as neo, plan_status_posts_v1 as posts
from live_contentops.publication_coordinator_v1 import (
    DEFINITE_NO_WRITE, DISPATCH_CONFIRMED, UNKNOWN_WRITE, HOLD_FULL_V1_DISTRIBUTION_NOT_READY,
)
from test_plan_status_posts_cc306 import NOW, main_root, export as export_fixture  # noqa: F401
from test_plan_status_publication_cc306 import queued, no_real_snapshot, fake_host  # noqa: F401
from test_publication_coordinator_v1 import _coordinator, _quality_plan


# 52d7906f (CC-124, 21 Nov, "keep X identity checks local to the article copy") moved decision 112's
# X identity proof from the whole-article preflight to the X dispatch itself: a missing or pending
# X identity now holds X alone, and the other outlets send. These two tests follow that change;
# before it they asserted that X held every derivative (HOLD_FULL_V1_DISTRIBUTION_NOT_READY).
def test_missing_x_identity_holds_only_x(tmp_path):
    _, transport, coordinator = _coordinator(tmp_path, readiness={"x": "SESSION_UNAVAILABLE"})
    result = coordinator.execute_plan("work-1", _quality_plan())
    assert result["distribution_status"] != HOLD_FULL_V1_DISTRIBUTION_NOT_READY
    assert result["quality_preflight"]["readiness_blockers"] == []
    assert result["per_destination"]["x"]["status"] == "SESSION_UNAVAILABLE"
    assert result["per_destination"]["x"]["publish_called"] is False
    assert "x" not in transport.publish_calls
    assert transport.publish_calls[0] == "substack" and "telegram" in transport.publish_calls


def test_pending_x_identity_returns_its_request_on_the_x_result(tmp_path):
    from types import SimpleNamespace
    from live_contentops.native_neo_executor_v1 import NativeNeoInputRequired, PENDING

    _, transport, coordinator = _coordinator(tmp_path)
    request = {"action": "VERIFY_IDENTITY", "destination": "x"}
    def pending(surface):
        raise NativeNeoInputRequired(request)

    transport._neo_transport = SimpleNamespace(native_executor=SimpleNamespace(
        native_neo_protocol=True, readiness=pending))
    result = coordinator.execute_plan("work-1", _quality_plan())
    assert result["per_destination"]["x"]["status"] == PENDING
    assert result["per_destination"]["x"]["native_tool_request"] == request
    assert "x" not in transport.publish_calls


@pytest.mark.parametrize("ended,ambiguous", [(False, False), (True, False), (False, True)])
def test_prior_bar_no_write_resumes_only_a_current_active_plan(queued, monkeypatch, ended, ambiguous):
    store, transport, coordinator, keys, root = queued
    key = keys[("XAUUSD", "WAITING")]
    store.create_work_item(story_id=key, work_item_id=key, title="Prior status no-write", target_surface="MULTI_PLATFORM")
    plan = posts.prepare_post(store, key, root=root, host=fake_host, destinations=("x",))
    posts.scope_to_post(coordinator, key, plan)
    with monkeypatch.context() as barred:
        barred.setitem(neo.NON_API_AUTOMATION_PROHIBITED, "x", "X_NON_API_AUTOMATION_PROHIBITED")
        registered = coordinator.register_plan(key, plan)["registered"][0]
    message = store.get_outbox_message(registered["message_id"])
    frozen = message["payload"]
    payload = json.loads(store.get_outbox_message(key)["payload"])
    row = {"key": key, "plan_id": payload["plan_id"], "symbol": payload["symbol"],
           "to": "EXPIRED" if ended else payload["state"], "at_utc": payload["at_utc"],
           "plan": {"valid_until_utc": payload["levels"]["valid_until_utc"]}}
    monkeypatch.setattr(posts, "_current_rows", lambda now: [row])
    original = posts.require_active_x_restoration
    monkeypatch.setattr(posts, "require_active_x_restoration",
                        lambda s, i: original(s, i, now=NOW + timedelta(hours=2)))
    if ambiguous:
        store.set_dispatch_status(registered["dispatch_id"], UNKNOWN_WRITE)
    result = coordinator._dispatch_message(message, canonical_url=None)
    assert result["status"] == (UNKNOWN_WRITE if ambiguous else DEFINITE_NO_WRITE if ended else DISPATCH_CONFIRMED)
    assert transport.publish_calls == ([] if ended or ambiguous else ["x"])
    assert store.get_outbox_message(registered["message_id"])["payload"] == frozen
    coordinator._dispatch_message(store.get_outbox_message(registered["message_id"]), canonical_url=None)
    assert transport.publish_calls == ([] if ended or ambiguous else ["x"])


@pytest.mark.parametrize("cause,public_id,platform,allowed", [
    ("X_NON_API_AUTOMATION_PROHIBITED", None, "x", True),
    ("OTHER_NO_WRITE", None, "x", False),
    ("X_NON_API_AUTOMATION_PROHIBITED", "existing", "x", False),
    ("X_NON_API_AUTOMATION_PROHIBITED", None, "youtube", False),
])
def test_atomic_claim_accepts_only_the_exact_unwritten_x_bar(tmp_path, cause, public_id, platform, allowed):
    store, _, _ = _coordinator(tmp_path)
    store.register_outbox_message(message_id="message", work_item_id="work-1", destination=platform,
                                  payload="{}", status=DEFINITE_NO_WRITE)
    store.register_platform_dispatch(dispatch_id="dispatch_exact", message_id="message", platform=platform,
        status=DEFINITE_NO_WRITE, public_object_id=public_id)
    store.register_reconciliation(reconciliation_id="reconciliation_exact", work_item_id="work-1", status=cause)
    kwargs = dict(dispatch_id="dispatch_exact", message_id="message", platform=platform,
        expected_status=DEFINITE_NO_WRITE, policy_no_write_cause="X_NON_API_AUTOMATION_PROHIBITED")
    assert store.claim_platform_dispatch_attempt(**kwargs) is allowed
    if allowed:
        assert store.claim_platform_dispatch_attempt(**kwargs) is False


def test_x_weighted_length_and_reflow_preserve_all_frozen_words():
    from live_contentops.neo_destination_handoff_v1 import _x_thread_matches
    assert posts._x_length("•") == 2
    assert posts._x_length("数据") == 4
    assert posts._x_length("e\u0301") == posts._x_length("é") == 1
    assert posts._x_length("https://example.com/a-long-link") == 23
    text = "• Base case " + "unchanged words " * 35
    parts = posts._x_pack(text, 280)
    assert all(posts._x_length(part) <= 280 for part in parts)
    assert " ".join(" ".join(parts).split()) == " ".join(text.split())
    expected = ["Root condition 86.3 to 86.7.", "• Model estimate 55% alternative 35%.", "Invalidation above 88.35."]
    reflow = [expected[0], "• Model estimate 55%", "alternative 35%. " + expected[2]]
    thread = [{"public_object_id": str(i+1), "public_object_url": f"https://x.com/Capitalnicle/status/{i+1}",
               "observed_text": t} for i,t in enumerate(reflow)]
    binding = {"expected_thread_texts": expected}
    assert _x_thread_matches(binding, thread, [], "")
    thread[1]["observed_text"] = "• Model estimate 56%"
    assert not _x_thread_matches(binding, thread, [], "")
    thread[1]["observed_text"] = "• Model estimate"
    assert not _x_thread_matches(binding, thread, [], "")
