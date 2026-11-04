"""CC-199 regressions through real coordinators/adapters in disposable stores."""
from datetime import datetime, timedelta, timezone
import json
import socket
import urllib.error

import pytest

from live_contentops import instagram_adapter_v6 as instagram
from live_contentops import live_telemetry_v6
from live_contentops.event_article_guard_v1 import PUBLIC_NOTICE
from live_contentops.linkedin_official_member_api_v1 import (
    LinkedInOfficialApiError, LinkedInOfficialMemberApiTransportV1,
)
from live_contentops.neo_destination_handoff_v1 import IDENTITIES, NeoDestinationHandoff
from live_contentops.publication_coordinator_v1 import (
    DEFINITE_NO_WRITE, DISPATCH_CONFIRMED, RECONCILED_CONFIRMED,
    UNKNOWN_WRITE, normalize_dispatch_result,
)
from test_publication_coordinator_v1 import FixtureTransport, _coordinator, _plan, _quality_plan, _sha
from test_linkedin_official_member_api_v1 import _metadata, _test_store


@pytest.fixture(autouse=True)
def no_live_telemetry(monkeypatch):
    monkeypatch.setattr(live_telemetry_v6, "classify_and_record_dispatch", lambda *_, **__: None)


@pytest.mark.parametrize("status", ["VALIDATION_FAILED", "SKIPPED_IMAGE_REQUIRED"])
def test_plan_or_validation_failure_is_not_an_ambiguous_write(status):
    result = normalize_dispatch_result(
        {"status": status, "validation_failures": ["media_manifest_hash_continuity_failed"]},
        destination="instagram_business", surface="INSTAGRAM_BUSINESS_POST", transport_type="META_GRAPH_API")
    assert result["status"] == DEFINITE_NO_WRITE
    assert "media_manifest_hash_continuity_failed" in result["safe_error_classification"]


def test_error_codes_survive_without_provider_message_or_request_material():
    result = normalize_dispatch_result(
        {"status": "FAILED_STEP_1", "definite_no_write": True, "error_code": 400,
         "error_response": {"error": {"code": 190, "error_subcode": 463,
                                      "message": "private-provider-message-do-not-persist"}},
         "error": "https://provider.test/?access_token=private-test-value"},
        destination="instagram_business", surface="INSTAGRAM_BUSINESS_POST", transport_type="META_GRAPH_API")
    assert result["status"] == DEFINITE_NO_WRITE
    assert "provider_code:190" in result["safe_error_classification"]
    assert "provider_error_subcode:463" in result["safe_error_classification"]
    assert "private" not in json.dumps(result)


@pytest.mark.parametrize("failed_stage", ["container", "publish"])
def test_instagram_tracks_the_public_publish_boundary(monkeypatch, failed_stage):
    monkeypatch.setattr(instagram, "validate_instagram_image_url", lambda _: [])
    monkeypatch.setattr(instagram, "_wait_for_instagram_container", lambda **_: {"ready": True})
    calls = []
    def post(url, payload):
        calls.append(url)
        if len(calls) == 1 and failed_stage != "container":
            return {"id": "container-1"}, 20
        raise TimeoutError("provider completion unknown")
    monkeypatch.setattr(instagram, "_post_form", post)
    raw = instagram.execute_instagram_post("fixture-account", "fixture-token",
                                           "https://example.test/image.png", "Reviewed text")
    result = normalize_dispatch_result(raw, destination="instagram_business",
        surface="INSTAGRAM_BUSINESS_POST", transport_type="META_GRAPH_API")
    assert raw["public_write_started"] is (failed_stage == "publish")
    assert result["status"] == (UNKNOWN_WRITE if failed_stage == "publish" else DEFINITE_NO_WRITE)
    assert len(calls) == (2 if failed_stage == "publish" else 1)


def test_repaired_validation_failure_keeps_recovering_until_the_live_consumer_posts(tmp_path):
    class ValidationThenSuccess(FixtureTransport):
        failures = 3
        def publish(self, *, destination, **kwargs):
            if destination == "instagram_business" and self.failures:
                self.failures -= 1
                self.publish_calls.append(destination)
                return {"status": "VALIDATION_FAILED", "validation_failures": ["image_url_unreachable"]}
            return super().publish(destination=destination, **kwargs)
    store, transport, coordinator = _coordinator(tmp_path, runtime=ValidationThenSuccess())
    plan = _quality_plan()
    coordinator.execute_plan("work-1", plan)
    for _ in range(3):
        coordinator.recover_pending()
    state = coordinator.publication_state("work-1", plan)
    assert state["per_destination"]["instagram_business"]["reconciliation_status"] == RECONCILED_CONFIRMED
    assert transport.publish_calls.count("instagram_business") == 4
    assert state["unknown_write_count"] == 0
    with store.get_read_only_connection() as conn:
        descriptions = [r[0] for r in conn.execute("SELECT description FROM incidents WHERE severity='DISPATCH_FAILURE'")]
    assert len(descriptions) == 3
    assert all("image_url_unreachable" in value for value in descriptions)
    assert coordinator.recover_pending()["publish_calls"] == 0


def test_text_first_piece_reaches_all_destinations_despite_frozen_channel_skips(tmp_path):
    from live_contentops.native_text_first_v1 import POLICY_ID, _legacy_skipped_destinations
    store, transport, coordinator = _coordinator(tmp_path)
    plan = _quality_plan()
    plan.update(text_first={"policy_id": POLICY_ID, "article_mode": "BREAKING_BRIEF", "story_kind": "NEWS"},
                resolved_article_mode="BREAKING_BRIEF", media_asset_count=1,
                skipped_derivative_destinations=_legacy_skipped_destinations(has_image=True))
    result = coordinator.execute_plan("work-1", plan)
    assert result["derivative_confirmed_count"] == 8
    assert all(d in transport.publish_calls for d in ("substack", "facebook_page", "youtube", "instagram_business"))
    assert len({m["destination"] for m in store.list_outbox_messages()
                if not m["destination"].startswith("internal:")}) == 10


@pytest.mark.parametrize("reason", [socket.gaierror(-2, "fixture DNS failure"), ConnectionRefusedError()])
def test_linkedin_connection_failure_before_http_is_definite_no_write(tmp_path, reason):
    now = datetime.now(timezone.utc)
    token_store = _test_store(tmp_path)
    token_store.write({"access_token": "fixture", "refresh_token": None},
                      _metadata(expires_at=now + timedelta(days=30)))
    def provider(*_, **__):
        raise urllib.error.URLError(reason)
    transport = LinkedInOfficialMemberApiTransportV1(token_store=token_store, opener=provider)
    result = transport.publish(intent={"payload": "Exact reviewed copy"},
                               authorization_context={"operating_mode": "AUTONOMOUS_DEFAULT"})
    assert result["definite_no_write"] is True
    assert result["reason_code"] == "TRANSPORT_UNAVAILABLE"


def test_linkedin_preparation_failure_never_becomes_unknown(tmp_path, monkeypatch):
    calls = []
    transport = LinkedInOfficialMemberApiTransportV1(token_store=_test_store(tmp_path),
                                                     opener=lambda *_, **__: calls.append("network"))
    def unauthorized():
        raise LinkedInOfficialApiError("AUTH_EXPIRED_OR_REAUTH_REQUIRED")
    monkeypatch.setattr(transport, "_authorized", unauthorized)
    result = transport.publish(intent={"payload": "Reviewed copy"},
                               authorization_context={"operating_mode": "AUTONOMOUS_DEFAULT"})
    assert result["status"] == "FAILED_BEFORE_WRITE"
    assert result["reason_code"] == "AUTH_EXPIRED_OR_REAUTH_REQUIRED"
    assert calls == []


@pytest.mark.parametrize("defect", [None, "identity", "id", "url", "title", "notice"])
def test_edited_canonical_keeps_unchanged_derivatives_approved(tmp_path, defect):
    title = "A reviewed official release"
    class EditedCanonical(FixtureTransport):
        def readback(self, *, destination, public_object_id, public_object_url, intent):
            if destination != "substack":
                return super().readback(destination=destination, public_object_id=public_object_id,
                                        public_object_url=public_object_url, intent=intent)
            def observation(request):
                value = {"request_sha256": request["request_sha256"],
                         "observed_identity": IDENTITIES["substack"],
                         "public_object_id": public_object_id, "public_object_url": public_object_url,
                         "observed_text": title + " Updated photo credit. " + PUBLIC_NOTICE,
                         "content_verified": False}
                if defect == "identity": value["observed_identity"] = "wrong.example"
                if defect == "id": value["public_object_id"] = "different-post"
                if defect == "url": value["public_object_url"] = "https://capitalchronicle.substack.com/p/different"
                if defect == "title": value["observed_text"] = "Different title. " + PUBLIC_NOTICE
                if defect == "notice": value["observed_text"] = title
                return value
            return NeoDestinationHandoff(native_executor=observation).readback(
                destination=destination, intent=intent, public_object_id=public_object_id,
                public_object_url=public_object_url)
    store, transport, coordinator = _coordinator(tmp_path, runtime=EditedCanonical())
    plan = _plan("substack", "telegram")
    for item in plan["destinations"]:
        item["canonical_url"] = "https://capitalchronicle.substack.com/p/fixture-article-1"
        item["payload"] = item["payload"].replace("/p/test", "/p/fixture-article-1")
        item["payload_hash"] = _sha(item["payload"])
    canonical = plan["destinations"][0]
    canonical["payload"] = {"title": title, "body_markdown": "The exact original body. " + PUBLIC_NOTICE}
    canonical["payload_hash"] = _sha(str(canonical["payload"]))
    coordinator.register_plan("work-1", plan)
    originals = {m["message_id"]: m["payload"] for m in store.list_outbox_messages()}
    result = coordinator.execute_plan("work-1", plan)
    assert result["canonical_article_real_published"] is (defect is None)
    if defect is None:
        assert transport.publish_calls == ["substack", "telegram"]
        assert coordinator.publication_state("work-1", plan)["canonical_article_real_published"]
        ids = coordinator._ids("work-1", plan["plan_hash"], "substack")
        proof = json.loads(store.list_readbacks_for_dispatch(ids["dispatch_id"])[-1]["readback_data"])["readback"]
        assert proof["verified"] is True and proof["strict_content_verified"] is False
        assert proof["content_readback_limitation"] == "CANONICAL_PRESENT_TITLE_AND_PUBLIC_NOTICE_VERIFIED_COPY_CHANGED"
    else:
        assert "telegram" not in transport.publish_calls
    for message_id, payload in originals.items():
        assert store.get_outbox_message(message_id)["payload"] == payload


def test_queued_derivative_ages_from_canonical_and_later_readbacks_do_not_refresh_it(tmp_path):
    store, transport, coordinator = _coordinator(tmp_path)
    old = datetime(2026, 11, 1, tzinfo=timezone.utc)
    published = datetime(2026, 11, 5, tzinfo=timezone.utc)
    store._get_now = lambda: old
    plan = _plan("substack", "telegram")
    plan["resolved_article_mode"] = "FOLLOW_UP_UPDATE"
    coordinator.register_plan("work-1", plan)
    store._get_now = lambda: published
    coordinator._clock = lambda: published
    result = coordinator.execute_plan("work-1", plan)
    assert result["per_destination"]["telegram"]["status"] == DISPATCH_CONFIRMED
    assert transport.publish_calls == ["substack", "telegram"]
    ids = coordinator._ids("work-1", plan["plan_hash"], "telegram")
    message = store.get_outbox_message(ids["message_id"])
    intent = json.loads(message["payload"])
    coordinator._clock = lambda: published + timedelta(hours=23)
    assert not coordinator._message_is_stale(message, intent)
    canonical = coordinator._ids("work-1", plan["plan_hash"], "substack")
    store._get_now = lambda: published + timedelta(hours=23)
    coordinator.readback_existing_dispatch(canonical["dispatch_id"])
    coordinator._clock = lambda: published + timedelta(hours=24)
    assert coordinator._message_is_stale(message, intent)


def test_publication_after_credit_edit_feeds_the_published_corpus_and_record(tmp_path):
    from test_published_content_v1 import lifecycle, ORIGINAL
    from live_contentops.published_content_v1 import read_records
    from live_contentops.published_corpus_read_model_v1 import load_published_corpus
    store, transport, coordinator, plan, _, _ = lifecycle(tmp_path)
    original_readback = transport.readback
    def readback(**kwargs):
        value = original_readback(**kwargs)
        if kwargs["destination"] == "substack":
            value.update(verified=False, status="BLOCKED", write_exists=True,
                         canonical_publication_verified=True, published_at_utc=ORIGINAL,
                         content_binding_checks={"text_match": False, "media_match": True})
        if kwargs["destination"] == "discord":
            value["public_object_url"] = "https://discord.com/channels/111/222/333"
        return value
    transport.readback = readback
    result = coordinator.execute_plan("work-1", plan)
    assert result["published_content_record"]["status"] == "APPENDED", result["published_content_record"]
    assert len(load_published_corpus(store)["articles"]) == 1
    records = read_records(coordinator.published_content_path)
    assert len(records) == 1 and records[0]["published_at_utc"].startswith("2026-11-02T17:35:07.590")
    calls = list(transport.publish_calls)
    coordinator.execute_plan("work-1", plan)
    assert transport.publish_calls == calls
    assert len(read_records(coordinator.published_content_path)) == 1


@pytest.mark.parametrize("mode,hours", [("BREAKING_BRIEF", 6), ("FOLLOW_UP_UPDATE", 24),
    ("STANDARD_NEWS_ANALYSIS", 168), ("DATA_OR_DOCUMENT_LENS", 168), ("EVERGREEN_EXPLAINER", 168)])
def test_piece_type_horizon_and_absolute_event_expiry(tmp_path, mode, hours):
    _, _, coordinator = _coordinator(tmp_path)
    assert coordinator._freshness_horizon({"resolved_article_mode": mode}) == timedelta(hours=hours)
    coordinator._clock = lambda: datetime(2026, 11, 6, 13, 30, tzinfo=timezone.utc)
    assert coordinator._message_is_stale({"created_at": "2026-11-06T13:29:59Z"},
        {"resolved_article_mode": mode, "publication_window": {"expires_at_utc": "2026-11-06T13:30:00Z"}})
