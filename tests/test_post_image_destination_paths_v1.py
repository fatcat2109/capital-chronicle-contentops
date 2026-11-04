"""Image selection reaches the existing transports; every fixture is local."""
from hashlib import sha256
import json

import pytest
from PIL import Image

from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as pipeline
from live_contentops.destination_transport_registry_v1 import V1_REQUIRED_DERIVATIVE_DESTINATIONS
from live_contentops.neo_destination_handoff_v1 import _payload_binding


@pytest.fixture
def image_intent(tmp_path):
    assets, delivery = [], []
    for name, color in [("selected-chart", "navy"), ("old-card", "white")]:
        path = tmp_path / (name + ".png")
        Image.new("RGB", (160, 90), color).save(path)
        digest = sha256(path.read_bytes()).hexdigest()
        assets.append({"asset_id": name, "path": str(path), "sha256": digest})
        delivery.append({"media_asset_id": name, "absolute_local_source_path": str(path),
            "sha256": digest, "public_delivery_sha256": digest, "local_public_hash_continuity": True,
            "verified_public_delivery_url": "https://res.cloudinary.com/fixture/" + name + ".png"})
    article = {"title": "The employment release", "subtitle": "What the official release says.",
        "native_brief_layout": True, "substack_body_markdown": "The release reports employment. The next observation remains ahead."}
    (tmp_path / "run_context_v1.json").write_text(json.dumps({"article": article, "selection": {},
        "media": {"assets": assets}}))
    # The old public card comes first, reproducing the Instagram mismatch.
    (tmp_path / "delivery_media_manifest_v1.json").write_text(json.dumps({"assets": delivery[::-1]}))
    return {"output_dir": str(tmp_path), "work_item_id": "fixture", "attempt_identity": "fixture-attempt",
        "canonical_url": "https://capitalchronicle.substack.com/p/fixture",
        "destination_plan": {"destination": "instagram_business"},
        "native_payload": {"text": "Reviewed copy https://capitalchronicle.substack.com/p/fixture",
                           "media_asset_ids": [a["asset_id"] for a in assets]}}


@pytest.mark.parametrize("destination", V1_REQUIRED_DERIVATIVE_DESTINATIONS)
def test_hosted_image_is_the_same_selected_local_image_for_every_social_destination(image_intent, destination):
    image_intent["destination_plan"]["destination"] = destination
    data = pipeline._durable_intent_inputs(image_intent)
    assert data["local_media"].endswith("selected-chart.png")
    assert data["primary_media"]["sha256"] == data["media_assets"][0]["sha256"]
    assert data["public_image_url"].endswith("/selected-chart.png")
    assert data["payloads"][destination]["text"] == image_intent["native_payload"]["text"]


@pytest.mark.parametrize("destination", ["substack", "x", "linkedin", "youtube"])
def test_neo_request_contains_the_selected_binary_image_path(image_intent, destination):
    image_intent["destination_plan"]["destination"] = destination
    if destination == "substack":
        image_intent.pop("native_payload")
    _, binding = _payload_binding(image_intent, destination)
    assert binding["media_manifest"]
    assert binding["media_manifest"][0]["path"].endswith("selected-chart.png")
    assert binding["media_manifest"][0]["sha256"]


@pytest.mark.parametrize("destination", ["telegram", "discord", "facebook_page", "instagram_business", "threads"])
def test_api_destination_receives_selected_image_and_exact_canonical(image_intent, destination, monkeypatch):
    image_intent["destination_plan"]["destination"] = destination
    captured = {}
    def capture(**kwargs):
        captured.update(kwargs)
        return {"status": "FAILED_BEFORE_WRITE", "definite_no_write": True}
    if destination == "threads":
        import live_contentops.threads_adapter_v6 as threads
        monkeypatch.setattr(threads, "execute_threads_post", capture)
    else:
        monkeypatch.setattr(pipeline, {"telegram": "_publish_telegram_photo_verified",
            "discord": "_publish_discord_verified", "facebook_page": "_publish_facebook_photo_verified",
            "instagram_business": "_publish_instagram_media_verified"}[destination], capture)
    pipeline._publish_one_destination_from_durable_intent(destination=destination, intent=image_intent,
        authorization_context={"operating_mode": "AUTONOMOUS_DEFAULT", "dispatch_attempt_identity": "fixture-attempt"})
    if destination in {"telegram", "discord"}:
        assert captured["image_path"].endswith("selected-chart.png")
        assert captured["canonical_url"] == image_intent["canonical_url"]
    elif destination == "threads":
        assert captured["image_url"].endswith("/selected-chart.png")
    else:
        assert captured["media"]["verified_public_delivery_url"].endswith("/selected-chart.png")
        assert captured["canonical_url"] == image_intent["canonical_url"]
