"""ContentOps V1 lane, 4 Nov 2026: one test per root cause Jim reported.

Every fixture is local: no browser, provider, model or production-store write.
"""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

import pytest
from PIL import Image

from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as pipeline
from live_contentops.destination_transport_registry_v1 import V1_REQUIRED_DERIVATIVE_DESTINATIONS
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff, _payload_binding
from live_contentops.publication_coordinator_v1 import (
    CanonicalDestinationTransportRuntimeV1, _payload_media_ids,
)


def _png(path, color="navy"):
    Image.new("RGB", (160, 90), color).save(path)
    return sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def imageless_copy(tmp_path):
    """A reviewed piece with one chart whose frozen social copy selected no image (CPI, 3 Nov)."""
    path = tmp_path / "chart.png"
    digest = _png(path)
    asset = {"asset_id": "reviewed-chart", "path": str(path), "sha256": digest,
             "caption": "The reviewed chart.", "alt_text": "Chart alt text.",
             "placement_after": "What the release says", "modality": "documentary_photo"}
    article = {"title": "September CPI: two readings", "subtitle": "Monthly and annual readings differ.",
               "native_brief_layout": True, "news_item_kind": "NEWS",
               "substack_body_markdown": "The release reports two readings. Analysis, not financial advice."}
    (tmp_path / "run_context_v1.json").write_text(json.dumps({
        "article": article, "selection": {}, "media": {"assets": [asset]},
        "accepted_evidence_sha256": "a" * 64}))
    return {"output_dir": str(tmp_path), "work_item_id": "fixture", "attempt_identity": "fixture-attempt",
            "canonical_url": None, "destination_plan": {"destination": "telegram"},
            "native_payload": {"text": "Reviewed copy without an image.", "media_asset_ids": []}}


def test_payload_media_ids_reads_root_post_and_top_level():
    assert _payload_media_ids({"media_asset_ids": [], "posts": [{"media_asset_ids": ["a"]}, {}]}) == ["a"]
    assert _payload_media_ids({"media_asset_ids": []}) == []
    assert _payload_media_ids(None) == []


@pytest.mark.parametrize("destination", V1_REQUIRED_DERIVATIVE_DESTINATIONS)
def test_copy_frozen_without_image_is_finalized_with_one(imageless_copy, destination, monkeypatch):
    # The documentary photo needs no licence check in this fixture.
    import live_contentops.visual_asset_discovery_v1 as photos
    monkeypatch.setattr(photos, "validate_contextual_photo", lambda asset, **_: None)
    imageless_copy["destination_plan"]["destination"] = destination
    finalized = CanonicalDestinationTransportRuntimeV1().finalize_intent(
        destination=destination, intent=imageless_copy,
        canonical_url="https://capitalchronicle.substack.com/p/fixture")
    assert finalized.get("post_image_policy")
    assert _payload_media_ids(finalized["native_payload"])
    data = pipeline._durable_intent_inputs(finalized)
    assert data["media_assets"], "a finalized derivative must carry an image"
    assert data["payloads"][destination]["text"].startswith("Reviewed copy without an image.")


def test_copy_with_its_own_image_is_left_unchanged(imageless_copy):
    imageless_copy["native_payload"]["media_asset_ids"] = ["reviewed-chart"]
    finalized = CanonicalDestinationTransportRuntimeV1().finalize_intent(
        destination="telegram", intent=imageless_copy,
        canonical_url="https://capitalchronicle.substack.com/p/fixture")
    assert not finalized.get("post_image_policy")
    assert finalized["native_payload"]["media_asset_ids"] == ["reviewed-chart"]


def test_image_failure_never_blocks_the_post(imageless_copy, monkeypatch):
    import live_contentops.rolling_x_grounded_article_media_builder_v1 as builder
    def broken(*_args, **_kwargs):
        raise ValueError("POST_CARD_ADMITTED_ARTICLE_AND_EVIDENCE_REQUIRED")
    monkeypatch.setattr(builder, "post_image_view", broken)
    finalized = CanonicalDestinationTransportRuntimeV1().finalize_intent(
        destination="telegram", intent=imageless_copy,
        canonical_url="https://capitalchronicle.substack.com/p/fixture")
    assert "post_image_policy" not in finalized
    assert finalized["post_image_floor_failure"].startswith("ValueError:POST_CARD_ADMITTED")
    assert finalized["native_payload"]["text"].startswith("Reviewed copy without an image.")


def test_substack_request_carries_reviewed_placement_caption_and_alt(imageless_copy):
    intent = dict(imageless_copy, destination_plan={"destination": "substack", "payload_hash": "h"},
                  canonical_url=None)
    intent.pop("native_payload")
    _, binding = _payload_binding(intent, "substack")
    row = binding["media_manifest"][0]
    assert row["placement_after"] == "What the release says"
    assert row["caption"] == "The reviewed chart." and row["alt_text"] == "Chart alt text."
    adapter = NeoDestinationHandoff()
    request = adapter.request(destination="substack", action="PUBLISH", intent=intent, authorization_context={
        "schema_version": "contentops.canonical_machine_authorization.v1", "operating_mode": "AUTONOMOUS_DEFAULT",
        "destination": "substack", "dispatch_attempt_identity": "a", "work_item_id": "fixture",
        "payload_hash": "h"})
    assert "placement_after" in request["substack_media_placement"]
    assert request["steps"][3] == request["substack_media_placement"]


# ---- Daily digest (Substack, 4 Nov) ----

def _digest_store(tmp_path):
    from live_contentops.published_content_v1 import canonical, append_record, SCHEMA
    from live_contentops.event_article_guard_v1 import PUBLIC_NOTICE
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    feed = tmp_path / "published.jsonl"
    feed.touch()
    value = dict(schema_version=SCHEMA, content_id="substack:1", type="ARTICLE",
        title="The Fed held", standfirst="A 10-2 vote kept the target range.",
        published_at_utc="2026-11-02T17:35:07Z", recorded_at_utc="2026-11-02T17:40:00Z",
        outlets=[{"name": "substack", "url": "https://capitalchronicle.substack.com/p/fed"}],
        event_id=None, conditional_calls=[], rights_class="CC_OWN_ANALYSIS", visibility="public",
        disclaimer=PUBLIC_NOTICE, conflicts_notice=None)
    value["content_sha256"] = sha256(canonical(value)).hexdigest()
    append_record(feed, value)
    # A live article the feed lacks (the 3 Nov midterm preview's case).
    out = tmp_path / "midterm"
    out.mkdir()
    (out / "article_manifest_v1.json").write_text(json.dumps({
        "title": "US midterms: the result that could surprise markets",
        "dek": "A Democratic sweep leads expectations."}))
    store.create_work_item(story_id="mid", work_item_id="mid", title="Reviewed Substack draft",
                           target_surface="SUBSTACK_ARTICLE")
    store.register_outbox_message(message_id="m-mid", work_item_id="mid", destination="substack",
        payload=json.dumps({"output_dir": str(out)}), status="DISPATCH_CONFIRMED")
    store.register_platform_dispatch(dispatch_id="d-mid", message_id="m-mid", platform="substack",
        status="DISPATCH_CONFIRMED", public_object_id="2",
        public_object_url="https://capitalchronicle.substack.com/p/us-midterms")
    store.register_readback(readback_id="r-mid", dispatch_id="d-mid", readback_data=json.dumps(
        {"readback": {"observed_published_at_utc": "2026-11-03T10:20:18.502000+00:00", "verified": False}}))
    return store, feed


def test_digest_names_the_day_lists_live_articles_and_summaries(tmp_path):
    from live_contentops.substack_daily_digest_v1 import prepare_daily_digest
    store, feed = _digest_store(tmp_path)
    packet = prepare_daily_digest(store, feed, now=datetime(2026, 11, 3, 12, 0, tzinfo=timezone.utc))["packet"]
    payload = packet["native_payload"]
    assert payload["title"] == "Capital Chronicle daily digest — November 3, 2026"
    assert [a["url"] for a in packet["articles"]] == [
        "https://capitalchronicle.substack.com/p/fed", "https://capitalchronicle.substack.com/p/us-midterms"]
    assert "A 10-2 vote kept the target range." in payload["body_markdown"]
    assert "A Democratic sweep leads expectations." in payload["body_markdown"]
    assert "articles" not in payload["subtitle"] and "The Fed held" in payload["subtitle"]
    card = packet["media_assets"][0]
    assert card["visual_type"] == "DIGEST_TITLES_CARD" and Path(card["path"]).is_file()
    assert card["digest_card_binding"]["titles"] == [a["title"] for a in packet["articles"]]
    assert card["placement_after"] == "lead"


def test_web_confirmed_digest_does_not_hold_the_next_day(tmp_path):
    from live_contentops.substack_daily_digest_v1 import prepare_daily_digest, digest_status
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
    from live_contentops.published_content_v1 import canonical, append_record
    store, feed = _digest_store(tmp_path)
    first = prepare_daily_digest(store, feed, now=datetime(2026, 11, 3, 12, 0, tzinfo=timezone.utc))["packet"]
    later = json.loads(feed.read_text().splitlines()[0])
    later.update(content_id="substack:3", title="September jobs", published_at_utc="2026-11-04T05:42:26Z",
                 recorded_at_utc="2026-11-04T06:19:06Z",
                 outlets=[{"name": "substack", "url": "https://capitalchronicle.substack.com/p/jobs"}])
    later.pop("content_sha256")
    later["content_sha256"] = sha256(canonical(later)).hexdigest()
    append_record(feed, later)
    ids = DurablePublicationCoordinator._ids(first["digest_id"], first["plan"]["plan_hash"], "substack")
    store.register_outbox_message(message_id=ids["message_id"], work_item_id=first["digest_id"],
        destination="substack", payload="{}", status="DISPATCH_CONFIRMED")
    store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"],
        platform="substack", status="DISPATCH_CONFIRMED", public_object_id="9",
        public_object_url="https://capitalchronicle.substack.com/p/digest-9")
    store.register_reconciliation(reconciliation_id=ids["reconciliation_id"],
        work_item_id=first["digest_id"], status="RECONCILED_CONFIRMED")
    status = digest_status(store, first)
    assert status["web_confirmed"] and not status["email_confirmed"]
    second = prepare_daily_digest(store, feed, now=datetime(2026, 11, 4, 12, 0, tzinfo=timezone.utc))
    assert second["packet"]["digest_id"] == "cc143-digest-2026-11-04"
    assert [a["url"] for a in second["packet"]["articles"]] == ["https://capitalchronicle.substack.com/p/jobs"]


# ---- Instagram registration and the LinkedIn company page ----

def test_instagram_is_registered_even_when_the_plan_listed_no_image():
    from live_contentops.native_newsroom_volume_v1 import permitted_derivative_skips, registration_skips
    plan = {"image_optional_policy": "JIM_DECISION_39", "skipped_derivative_destinations": [
        {"destination": "instagram_business", "status": "SKIPPED_IMAGE_REQUIRED"}]}
    # The plan stays structurally valid, but Instagram is no longer left out (SEC, 4 Nov).
    assert permitted_derivative_skips(plan) == {"instagram_business"}
    assert registration_skips(plan) == set()


def test_linkedin_post_also_registers_the_company_page_copy(tmp_path):
    from test_publication_coordinator_v1 import _quality_plan
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    store.create_work_item(work_item_id="work", story_id="story", title="Test", target_surface="test")
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=None)
    plan = _quality_plan()
    result = coordinator.register_plan("work", plan)
    assert [r["destination"] for r in result["registered"]].count("linkedin_company") == 1
    ids = coordinator._ids("work", plan["plan_hash"], "linkedin_company")
    intent = json.loads(store.get_outbox_message(ids["message_id"])["payload"])
    assert intent["routine_company_copy"] is True and intent["attempt_identity"] == ids["dispatch_id"]
    assert intent["destination_plan"]["surface"] == "LINKEDIN_COMPANY_POST"
    assert intent["payload"] == next(d["payload"] for d in plan["destinations"] if d["destination"] == "linkedin")
    assert coordinator._intent_registration("linkedin_company", intent).surface == "LINKEDIN_COMPANY_POST"
    with pytest.raises(ValueError, match="LINKEDIN_COMPANY"):
        coordinator._intent_registration("linkedin_company", {**intent, "company_copy_of_message_id": "other"})
    # Registering the same plan again adds no second copy.
    coordinator.register_plan("work", plan)
    assert sum(m["destination"] == "linkedin_company" for m in store.list_outbox_messages()) == 1


def test_company_copy_uses_the_same_compiled_linkedin_copy(imageless_copy):
    imageless_copy.pop("native_payload")
    imageless_copy["destination_plan"]["destination"] = "linkedin_company"
    data = pipeline._durable_intent_inputs(imageless_copy)
    assert data["payloads"]["linkedin_company"] == data["payloads"]["linkedin"]
    assert data["payloads"]["linkedin_company"].get("text")
