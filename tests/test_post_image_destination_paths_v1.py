"""Image selection reaches the existing transports; every fixture is local."""
from hashlib import sha256
import json
from pathlib import Path

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


@pytest.mark.parametrize("destination", [*V1_REQUIRED_DERIVATIVE_DESTINATIONS, "linkedin_company"])
def test_hosted_image_is_the_same_selected_local_image_for_every_social_destination(image_intent, destination):
    image_intent["destination_plan"]["destination"] = destination
    data = pipeline._durable_intent_inputs(image_intent)
    assert data["local_media"].endswith("selected-chart.png")
    assert data["primary_media"]["sha256"] == data["media_assets"][0]["sha256"]
    assert data["public_image_url"].endswith("/selected-chart.png")
    assert data["payloads"][destination]["text"] == image_intent["native_payload"]["text"]


@pytest.mark.parametrize("destination", ["substack", "x", "linkedin", "linkedin_company", "youtube"])
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


@pytest.mark.parametrize("thread_only", [False, True])
def test_reviewed_order_wins_over_canonical_asset_order(image_intent, thread_only):
    # Both are valid files; the editor deliberately selects the second one first.
    selected = ["old-card", "selected-chart"]
    image_intent["native_payload"]["media_asset_ids"] = selected
    if thread_only:
        image_intent["native_payload"].pop("media_asset_ids")
        image_intent["native_payload"]["posts"] = [
            {"role": "root", "media_asset_ids": [selected[0]]},
            {"role": "reply", "media_asset_ids": [selected[1]]},
        ]
    data = pipeline._durable_intent_inputs(image_intent)
    assert [a["asset_id"] for a in data["media_assets"]] == selected
    assert data["local_media"].endswith("old-card.png")
    assert data["public_image_url"].endswith("/old-card.png")


@pytest.mark.parametrize("missing_kind", ["id", "file"])
def test_unresolved_reviewed_primary_never_uses_retained_card(image_intent, monkeypatch, missing_kind):
    if missing_kind == "id":
        image_intent["native_payload"]["media_asset_ids"] = ["unresolved-reviewed-chart"]
    else:
        Path(image_intent["output_dir"], "selected-chart.png").unlink()
    called = []
    monkeypatch.setattr(pipeline, "_publish_instagram_media_verified", lambda **kw: called.append(kw))
    result = pipeline._publish_one_destination_from_durable_intent(destination="instagram_business", intent=image_intent,
        authorization_context={"operating_mode": "AUTONOMOUS_DEFAULT", "dispatch_attempt_identity": "fixture-attempt"})
    assert called == []
    assert result["status"] == "FAILED_BEFORE_WRITE"
    assert result["definite_no_write"] is True
    assert result["reason_code"].startswith("reviewed_delivery_media_asset_unavailable:")


def test_unhosted_selected_chart_never_falls_back_to_hosted_old_card(image_intent):
    manifest = Path(image_intent["output_dir"], "delivery_media_manifest_v1.json")
    x = json.loads(manifest.read_text())
    x["assets"] = [a for a in x["assets"] if a["media_asset_id"] == "old-card"]
    manifest.write_text(json.dumps(x))
    data = pipeline._durable_intent_inputs(image_intent)
    assert data["local_media"].endswith("selected-chart.png")
    assert data["primary_media"] == {}
    assert data["public_image_url"] == ""


def test_actual_retained_cpi_chart_reaches_instagram_adapter(tmp_path, monkeypatch):
    fixture = Path(__file__).parent / "evidence/cc-142"
    retained = json.loads((fixture / "reader-chart-revision.json").read_text(encoding="utf-8"))
    article = retained["article"]
    # The retained article manifest is projected into the existing native brief transport.
    article["native_brief_layout"] = True
    current_review = json.loads((Path(__file__).parents[1] /
        "docs/publisher/CC-171/resume-20261104-1342/cpi-current-social-revision.json").read_text(encoding="utf-8"))
    article["native_destination_media"] = current_review["channel_media"]
    chart = fixture / "render-r3/media_assets/cpi-annual-history-r3.png"
    raw = chart.read_bytes()
    digest = sha256(raw).hexdigest()
    assert digest == "2e94bde55b4ba794b39c25cc31d4cd2a49a99359bb7545ec5d0305f6111617cc"
    assets = retained["media_assets"]
    for asset in assets:
        relative = asset["path"].replace("\\", "/").split("/tests/", 1)[1]
        asset["path"] = str(Path(__file__).parent / relative)
    (tmp_path / "run_context_v1.json").write_text(json.dumps({"article": article, "selection": {},
        "media": {"assets": assets}}))
    (tmp_path / "delivery_media_manifest_v1.json").write_text(json.dumps({"assets": [
        {"media_asset_id": "old-card", "sha256": "0" * 64, "public_delivery_sha256": "0" * 64,
         "local_public_hash_continuity": True, "verified_public_delivery_url": "https://res.cloudinary.com/fixture/old.png"},
        {"media_asset_id": "cpi-annual-history-r3", "sha256": digest, "public_delivery_sha256": digest,
         "local_public_hash_continuity": True, "verified_public_delivery_url": "https://res.cloudinary.com/fixture/cpi-annual-history-r3.png"}]}))
    intent = {"output_dir": str(tmp_path), "attempt_identity": "retained-cpi-fixture",
        "canonical_url": "https://capitalchronicle.substack.com/p/september-cpi-why-06-and-37-answer",
        "destination_plan": {"destination": "instagram_business"},
        "native_payload": {"text": article["social_lede"], "media_asset_ids": ["cpi-annual-history-r3"]}}
    captured = {}
    def capture(**kwargs):
        captured.update(kwargs)
        return {"status": "FAILED_BEFORE_WRITE", "definite_no_write": True}
    monkeypatch.setattr(pipeline, "_publish_instagram_media_verified", capture)
    pipeline._publish_one_destination_from_durable_intent(destination="instagram_business", intent=intent,
        authorization_context={"operating_mode": "AUTONOMOUS_DEFAULT", "dispatch_attempt_identity": "retained-cpi-fixture"})
    assert captured["media"]["sha256"] == digest
    assert captured["media"]["verified_public_delivery_url"].endswith("/cpi-annual-history-r3.png")
