"""CC-199: public timing and media proof from the existing live projection."""
import json

import pytest

from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.native_publication_latency_v1 import publication_timing
from live_contentops.publication_coordinator_v1 import normalize_readback_result


def timing_packet(*, status="PUBLISHED", media=True, observed="2026-11-06T08:14:00Z"):
    request_hash = "request"
    request = {"request_sha256": request_hash, "action": "PUBLISH", "destination": "substack",
        "dispatch_attempt_identity": "dispatch-1"}
    rows = [{"destination": "internal:native-neo-tool", "message_id": "request",
        "payload": json.dumps({"operation_id": "run", "request": request})}]
    for kind, value in [
        ("started", {"begun_at_utc": "2026-11-06T08:05:00Z"}),
        ("response", {"result": {"status": status, "native_tool_observation": {
            "dispatched_at_utc": "2026-11-06T08:10:00Z", "observed_at_utc": "2026-11-06T08:11:00Z"}}}),
    ]:
        rows.append({"destination": "internal:native-neo-tool",
            "message_id": "native-neo-" + sha256_of(["run", request_hash, kind]), "payload": json.dumps(value)})
    review = {"reviewer_ref": "NATIVE_DESKTOP_ARTICLE_REVIEW", "decision": "KEEP",
        "reviewed_at": "2026-11-06T08:00:00Z", "notes": json.dumps({"run_id": "run",
            "article_identity": "article", "text_revision_sha256": "text"})}
    destination = {"destination": "substack", "dispatch_id": "dispatch-1", "public_object_id": "42",
        "status": "DISPATCH_CONFIRMED", "reconciliation_status": "RECONCILED_CONFIRMED"}
    readback = {"dispatch_id": "dispatch-1", "read_at": "2026-11-06T08:45:00Z",
        "readback_data": json.dumps({"readback": {"verified": True, "identity_match": True,
            "observed_public_object_id": "42", "meaningful_media_visible": media, "observed_at_utc": observed}})}
    return rows, [review], [destination], [readback]


def report(packet):
    rows, reviews, destinations, readbacks = packet
    return publication_timing(rows, reviews, run_id="run", destinations=destinations, readbacks=readbacks)


def test_published_substack_return_and_delayed_submission_keep_actual_clocks():
    value = report(timing_packet())
    channel = value["channels"][0]
    assert channel["dispatched_at_utc"] == "2026-11-06T08:10:00Z"
    assert channel["first_verified_readback_at_utc"] == "2026-11-06T08:14:00+00:00"
    assert channel["within_target"] is True
    assert value["finished_piece_acceptance"]["all_destinations_with_image_readbacks_within_target"] is True


@pytest.mark.parametrize("defect", ["no_readback", "wrong_dispatch", "wrong_object", "unverified", "no_image", "late_image"])
def test_confirmed_dispatch_alone_cannot_pass_finished_piece_acceptance(defect):
    packet = timing_packet(media=defect != "no_image",
        observed="2026-11-06T08:40:00Z" if defect == "late_image" else "2026-11-06T08:14:00Z")
    readbacks = packet[-1]
    if defect == "no_readback":
        readbacks.clear()
    elif defect == "wrong_dispatch":
        readbacks[0]["dispatch_id"] = "another-dispatch"
    elif defect in {"wrong_object", "unverified"}:
        proof = json.loads(readbacks[0]["readback_data"])
        proof["readback"].update({"observed_public_object_id": "another"} if defect == "wrong_object" else {"verified": False})
        readbacks[0]["readback_data"] = json.dumps(proof)
    value = report(packet)
    assert value["channels"][0]["within_target"] is True
    assert value["finished_piece_acceptance"]["all_destinations_with_image_readbacks_within_target"] is False


def test_reconciled_ambiguous_send_uses_readback_upper_bound_without_backdating():
    packet = timing_packet(status="UNKNOWN_WRITE", observed="2026-11-06T08:20:00Z")
    value = report(packet)
    channel = value["channels"][0]
    assert channel["timing_basis"] == "VERIFIED_READBACK_UPPER_BOUND"
    assert channel["dispatched_at_utc"] == "2026-11-06T08:20:00+00:00"
    assert channel["within_target"] is None
    assert channel["finished_piece_within_30_minutes"] is True


def test_later_media_review_does_not_restart_the_original_approval_clock():
    packet = timing_packet(observed="2026-11-06T08:40:00Z")
    packet[1].append({**packet[1][0], "reviewed_at": "2026-11-06T08:20:00Z"})
    value = report(packet)
    assert value["text_approved_at_utc"] == "2026-11-06T08:00:00Z"
    assert value["channels"][0]["finished_piece_within_30_minutes"] is False


def test_threads_missing_image_retains_bounded_cause_without_raw_provider_data(monkeypatch):
    from live_contentops import threads_adapter_v6 as adapter
    monkeypatch.setattr(adapter, "_get_json", lambda *a, **k: {"id": "42", "text": "Approved text",
        "media_type": "TEXT_POST", "username": "official.capitalchronicle",
        "permalink": "https://www.threads.com/@official.capitalchronicle/post/test"})
    raw = adapter.readback_threads_post(post_id="42", expected_text="Approved text",
        expected_media_local_path="selected-image.png", access_token="controlled")
    raw["content_binding_checks"]["provider_message"] = "must never be retained"
    normalized = normalize_readback_result(raw, public_object_id="42", destination="threads")
    assert normalized["verified"] is False and normalized["identity_match"] is True
    assert normalized["content_binding_checks"]["text_match"] is True
    assert normalized["content_binding_checks"]["media_match"] is False
    assert normalized["meaningful_media_visible"] is False
    assert "provider_message" not in normalized["content_binding_checks"]
    assert "must never be retained" not in json.dumps(normalized)


def test_native_projection_consumes_exact_persisted_readbacks(tmp_path, monkeypatch):
    from test_native_desktop_publication_v1 import seeded, composed, finish
    store, binding, rollout, _, _ = seeded(tmp_path, monkeypatch)
    operation, executor, _ = composed(store, binding, rollout, monkeypatch)
    finish(operation, executor)
    value = operation.projection()
    channel = next(c for c in value["timing"]["channels"] if c["destination"] == "substack")
    assert channel["first_verified_readback_at_utc"]
    assert channel["image_verified_readback_at_utc"]
    assert value["timing"]["finished_piece_acceptance"]["target_minutes"] == 30
