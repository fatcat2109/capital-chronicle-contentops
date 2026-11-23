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


@pytest.mark.parametrize("status", ["SKIPPED_IMAGE_REQUIRED", "SKIPPED_PHOTOLESS_NEWS_POLICY", "SKIPPED_CHANNEL"])
def test_authorized_destination_skip_cannot_hide_missing_image_readback(status):
    packet = timing_packet()
    packet[2].append({"destination": "instagram_business", "status": status})
    value = report(packet)
    # The dispatch policy can retain its typed skip, but CC-199 still needs
    # the authorized destination's actual image and readback.
    assert value["all_channels_dispatched_within_target"] is True
    assert value["finished_piece_acceptance"]["all_destinations_with_image_readbacks_within_target"] is False


def test_explicit_platform_prohibition_excludes_only_its_definite_no_write(monkeypatch):
    monkeypatch.setattr("live_contentops.destination_transport_registry_v1.barred_browser_destinations",
        lambda: {"youtube": "CONTROLLED_JIM_DECISION_PROHIBITION"})
    packet = timing_packet()
    packet[2].append({"destination": "youtube", "status": "DEFINITE_NO_WRITE"})
    value = report(packet)
    channel = value["channels"][1]
    assert channel["excluded_from_timing_due_to"] == "CONTROLLED_JIM_DECISION_PROHIBITION"
    assert value["finished_piece_acceptance"]["all_destinations_with_image_readbacks_within_target"] is True


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


def reopened_packet():
    # The next sample uses the original text approval, not a later repair clock.
    rows, reviews, destinations, readbacks = timing_packet()
    rows = json.loads(json.dumps(rows).replace("2026-11-06T08:", "2026-11-15T19:"))
    reviews = json.loads(json.dumps(reviews).replace("2026-11-06T08:", "2026-11-15T19:"))
    readbacks = json.loads(json.dumps(readbacks).replace("2026-11-06T08:", "2026-11-15T19:"))
    destinations.append({"destination": "youtube", "status": "DEFINITE_NO_WRITE"})
    return rows, reviews, destinations, readbacks


def test_reopened_sample_excludes_only_named_youtube_suspension(tmp_path, monkeypatch):
    from live_contentops import neo_destination_handoff_v1 as handoff
    control = tmp_path / "suspended_routes.json"
    monkeypatch.setattr(handoff, "SUSPENDED_ROUTES_FILE", control)
    control.write_text(json.dumps({"youtube": "YOUTUBE_EXTERNAL_LINK_VERIFICATION_REQUIRED"}))
    packet = reopened_packet()
    value = report(packet)
    acceptance = value["finished_piece_acceptance"]
    assert acceptance["all_destinations_with_image_readbacks_within_target"] is True
    assert acceptance["required_destinations"] == ["substack"]
    assert acceptance["excluded_destinations"] == [{"destination": "youtube",
        "cause": "YOUTUBE_EXTERNAL_LINK_VERIFICATION_REQUIRED",
        "authority": "CC-199_OPS_PRODUCT_20261116_0125_GMT7"}]
    assert packet[2][-1]["status"] == "DEFINITE_NO_WRITE"
    # Clearing only this route restores its actual image/readback requirement.
    control.write_text("{}")
    acceptance = report(packet)["finished_piece_acceptance"]
    assert acceptance["all_destinations_with_image_readbacks_within_target"] is False
    assert acceptance["required_destinations"] == ["substack", "youtube"]


@pytest.mark.parametrize("case", ["old_approval", "different_youtube_cause", "other_route", "missing_image", "late_image"])
def test_youtube_exception_cannot_hide_other_missing_proof(monkeypatch, case):
    routes = {"youtube": "YOUTUBE_EXTERNAL_LINK_VERIFICATION_REQUIRED"}
    if case == "different_youtube_cause":
        routes["youtube"] = "YOUTUBE_PLATFORM_RESTRICTION"
    if case == "other_route":
        routes["linkedin_company"] = "LINKEDIN_IDENTITY_VERIFICATION_REQUIRED"
    monkeypatch.setattr("live_contentops.neo_destination_handoff_v1.suspended_routes", lambda: routes)
    packet = timing_packet() if case == "old_approval" else reopened_packet()
    if case == "old_approval":
        packet[2].append({"destination": "youtube", "status": "DEFINITE_NO_WRITE"})
    elif case == "other_route":
        packet[2].append({"destination": "linkedin_company", "status": "DEFINITE_NO_WRITE"})
    elif case in {"missing_image", "late_image"}:
        proof = json.loads(packet[3][0]["readback_data"])
        proof["readback"].update({"meaningful_media_visible": False} if case == "missing_image"
            else {"observed_at_utc": "2026-11-15T19:40:00Z"})
        packet[3][0]["readback_data"] = json.dumps(proof)
    assert report(packet)["finished_piece_acceptance"]["all_destinations_with_image_readbacks_within_target"] is False


def test_native_projection_uses_reopened_exception_without_changing_dispatch(tmp_path, monkeypatch):
    from test_native_desktop_publication_v1 import seeded, composed, finish
    from live_contentops import native_publication_latency_v1 as latency
    from live_contentops import neo_destination_handoff_v1 as handoff
    store, binding, rollout, _, _ = seeded(tmp_path, monkeypatch)
    operation, executor, _ = composed(store, binding, rollout, monkeypatch)
    finish(operation, executor)
    monkeypatch.setattr(latency, "FINISHED_PIECE_YOUTUBE_EXCEPTION_AT", "2000-01-01T00:00:00Z")
    monkeypatch.setattr(handoff, "suspended_routes", lambda: {"youtube": "YOUTUBE_EXTERNAL_LINK_VERIFICATION_REQUIRED"})
    before = store.list_platform_dispatches()
    projection = operation.projection()
    acceptance = projection["timing"]["finished_piece_acceptance"]
    assert "youtube" not in acceptance["required_destinations"]
    assert {c["destination"] for c in acceptance["excluded_destinations"]} == {"youtube"}
    assert {"substack", "linkedin", "linkedin_company", "threads", "instagram_business"} <= set(acceptance["required_destinations"])
    assert store.list_platform_dispatches() == before


def test_manual_desk_routes_appear_in_live_timing_without_counting_as_public_delivery(monkeypatch):
    from live_contentops import neo_destination_handoff_v1 as handoff
    from live_contentops.native_desktop_publication_v1 import DESTINATION, publication_projection
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator

    monkeypatch.setattr(handoff, "suspended_routes", lambda: {
        "x": "JIM_POSTS_BY_HAND_20261123",
        "linkedin_company": "JIM_POSTS_BY_HAND_20261123",
        "linkedin": "NEO_SIGNED_IN_ACCOUNT_MISMATCH",
        "youtube": "YOUTUBE_EXTERNAL_LINK_VERIFICATION_REQUIRED",
    })
    _, reviews, _, _ = timing_packet()
    reviews[0]["reviewed_at"] = "2026-11-22T21:00:00Z"
    company = DurablePublicationCoordinator._ids("run", "plan", "linkedin_company")
    rows = [
        {"message_id": "binding", "destination": DESTINATION,
         "payload": json.dumps({"run_id": "run", "plan_hash": "plan"})},
        {"message_id": company["message_id"], "destination": "linkedin_company",
         "work_item_id": "run", "payload": "{}", "status": "READY"},
    ]
    timing = publication_projection(rows, [], [], run_id="run", reviews=reviews)["timing"]
    channels = {c["destination"]: c for c in timing["channels"]}
    assert channels["x"]["manual_handoff"]["authority"] == "CC-748"
    assert channels["linkedin_company"]["manual_handoff"]["cause"] == "JIM_POSTS_BY_HAND_20261123"
    assert channels["x"]["status"] == "NOT_DISPATCHED"
    assert channels["linkedin"]["finished_piece_required"] is True
    acceptance = timing["finished_piece_acceptance"]
    assert {"x", "linkedin_company"} <= set(acceptance["required_destinations"])
    assert {"x", "linkedin_company"}.isdisjoint(acceptance["automated_required_destinations"])
    assert "linkedin" in acceptance["automated_required_destinations"]


@pytest.mark.parametrize("before_handoff", [True, False])
def test_manual_desk_timing_keeps_original_approval_and_exact_public_proof(monkeypatch, before_handoff):
    from live_contentops import neo_destination_handoff_v1 as handoff

    monkeypatch.setattr(handoff, "suspended_routes", lambda: {
        "substack_notes": "JIM_POSTS_BY_HAND_20261123",
    })
    packet = tuple(json.loads(json.dumps(group).replace(
        "2026-11-06T08:", "2026-11-22T20:" if before_handoff else "2026-11-22T21:"
    )) for group in timing_packet())
    if before_handoff:
        packet[1].append({**packet[1][0], "reviewed_at": "2026-11-22T21:00:00Z"})
    packet[2].append({"destination": "substack_notes", "status": "NOT_DISPATCHED"})
    timing = report(packet)
    acceptance = timing["finished_piece_acceptance"]
    assert timing["all_channels_dispatched_within_target"] is (not before_handoff)
    assert acceptance["all_automated_destinations_with_image_readbacks_within_target"] is (not before_handoff)
    assert acceptance["all_destinations_with_image_readbacks_within_target"] is False
    assert acceptance["required_destinations"] == ["substack", "substack_notes"]
