from __future__ import annotations

import inspect
import json
from pathlib import Path

from PIL import Image

import live_contentops.cloudinary_delivery_media_v1 as cloudinary
from live_contentops.media_manifest_authority_v1 import image_metadata_from_file, sha256_file


def _environment() -> dict[str, str]:
    return {
        "CLOUDINARY_CLOUD_NAME": "test-cloud",
        "CLOUDINARY_API_KEY": "test-key",
        "CLOUDINARY_API_SECRET": "test-secret",
    }


def _asset(tmp_path: Path) -> dict:
    path = tmp_path / "delivery.png"
    Image.new("RGB", (1350, 1080), "#07111f").save(path, format="PNG")
    return {
        "asset_id": "delivery_only_editorial_card",
        "media_role": "delivery_only",
        "path": str(path),
        "local_path": str(path),
        "absolute_local_source_path": str(path),
        "sha256": sha256_file(path),
        "provenance_status": "VERIFIED_SOURCE_METADATA_CONTENTOPS_RENDER",
        "rights_basis": "CONTENTOPS_OWNED_LAYOUT_SOURCE_METADATA_ONLY",
        "source_label": "Official source",
        "source_page_url": "https://official.example/source",
        "article_inclusion": False,
        "canonical_article_media": False,
        "delivery_only": True,
        **image_metadata_from_file(path),
    }


def test_reviewed_article_chart_uses_same_cloudinary_path_without_delivery_only_relabelling(tmp_path, monkeypatch):
    asset = {**_asset(tmp_path), "media_role": "editorial_data_journalism", "modality": "source_backed_chart",
             "underlying_source_rights_status": "public_domain", "source_reuse_basis": "Official public-domain series"}
    monkeypatch.setattr(cloudinary, "read_public_image_bytes", lambda _: Path(asset["path"]).read_bytes())
    monkeypatch.setattr(cloudinary, "_upload_asset", lambda **_: (_ for _ in ()).throw(AssertionError("reuse exact object")))
    result = cloudinary.prepare_cloudinary_delivery_media(work_item_id="reviewed-article", delivery_only_assets=[],
        article_assets=[asset], environment=_environment())
    assert result["status"] == cloudinary.READY and result["provider_calls"] == 0
    row = result["manifest"]["assets"][0]
    assert row["media_role"] == "editorial_data_journalism" and row["canonical_article_media"]
    assert row["article_inclusion"] and not row["delivery_only"]
    assert row["public_delivery_sha256"] == asset["sha256"]
    rejected = cloudinary.prepare_cloudinary_delivery_media(work_item_id="reviewed-article", delivery_only_assets=[],
        article_assets=[{**asset, "underlying_source_rights_status": "NOT_GRANTED"}], environment=_environment())
    assert rejected["status"] == "BLOCKED_CLOUDINARY_DELIVERY_MEDIA_PREPARATION"


def test_verified_snapshot_delivery_projection_sets_the_delivery_flag(tmp_path, monkeypatch):
    asset = {**_asset(tmp_path), "modality": "tradingview_chart_snapshot", "delivery_only": False}
    monkeypatch.setattr("live_contentops.tradingview_snapshot_v1.validate_snapshot_asset", lambda *a: None)
    row, blockers = cloudinary._validated_local_asset(asset)
    assert not blockers and row["delivery_only"] is True
    def changed_bytes(*args):
        raise ValueError("TRADINGVIEW_SOURCE_HASH_CHANGED")
    monkeypatch.setattr("live_contentops.tradingview_snapshot_v1.validate_snapshot_asset", changed_bytes)
    _, blockers = cloudinary._validated_local_asset(asset)
    assert any(b.startswith("tradingview_snapshot_invalid:") for b in blockers)


def test_credential_presence_and_missing_failure_never_serialize_values(tmp_path, monkeypatch):
    asset = _asset(tmp_path)
    monkeypatch.setattr(
        cloudinary,
        "_upload_asset",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("provider must not run")),
    )

    result = cloudinary.prepare_cloudinary_delivery_media(
        work_item_id="work-item-1",
        delivery_only_assets=[asset],
        environment={"CLOUDINARY_API_SECRET": "must-not-leak"},
    )

    assert result["status"] == "BLOCKED_CLOUDINARY_CREDENTIALS_MISSING"
    assert result["provider_calls"] == 0
    assert result["credential_presence"] == {
        "CLOUDINARY_CLOUD_NAME": False,
        "CLOUDINARY_API_KEY": False,
        "CLOUDINARY_API_SECRET": True,
    }
    assert "must-not-leak" not in json.dumps(result, sort_keys=True)


def test_filing_fact_card_reaches_url_transports_with_source_and_byte_checks(tmp_path, monkeypatch):
    from copy import deepcopy
    from test_post_visuals_v1 import packet
    from live_contentops.post_visuals_v1 import build_post_data_card, complete_post_visuals
    from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import _durable_intent_inputs

    article, claims, documents = packet()
    article["article_mode"] = "BREAKING_BRIEF"
    documents[0].pop("underlying_reuse_classification")
    documents[0].pop("rights_evidence_sha256")
    documents[0]["source_reuse_constraints"]["scope"] = "ATTRIBUTED_FILING_FACTS_ONLY_INDEPENDENT_PUBLIC_PARAPHRASE"
    card = build_post_data_card(article, claims, documents, output_dir=tmp_path)
    article, assets = complete_post_visuals(article, claims, documents, [], output_dir=tmp_path)
    article["native_destination_media"] = article["post_visual_destination_media"]
    monkeypatch.setattr(cloudinary, "read_public_image_bytes", lambda _: Path(card["path"]).read_bytes())
    monkeypatch.setattr(cloudinary, "_upload_asset", lambda **_: (_ for _ in ()).throw(AssertionError("reuse verified bytes")))
    kwargs = dict(work_item_id="filing-card", delivery_only_assets=[], article_assets=assets,
        article=article, source_documents=documents, environment=_environment())
    result = cloudinary.prepare_cloudinary_delivery_media(**kwargs)
    assert result["status"] == cloudinary.READY
    (tmp_path / "delivery_media_manifest_v1.json").write_text(json.dumps(result["manifest"]))
    (tmp_path / "run_context_v1.json").write_text(json.dumps({"article": article,
        "media": {"assets": assets}, "source_documents": documents, "selection": {}}))
    for destination in ("facebook_page", "instagram_business"):
        inputs = _durable_intent_inputs({"output_dir": str(tmp_path),
            "destination_plan": {"destination": destination},
            "canonical_url": "https://capitalchronicle.substack.com/p/controlled-card",
            "native_payload": {"text": "Controlled copy", "media_asset_ids": [card["asset_id"]]}})
        assert inputs["primary_media"]["public_delivery_sha256"] == card["sha256"]
        assert inputs["public_image_url"].startswith("https://res.cloudinary.com/")

    changed = deepcopy(documents)
    changed[0]["source_reuse_constraints"]["scope"] = "NO_PUBLIC_REUSE"
    for replacement in ({"source_documents": changed}, {"article": None},
                        {"article_assets": [{**card, "sha256": "0" * 64}]}):
        rejected = cloudinary.prepare_cloudinary_delivery_media(**{**kwargs, **replacement})
        assert rejected["status"] == "BLOCKED_CLOUDINARY_DELIVERY_MEDIA_PREPARATION"
        assert rejected["provider_calls"] == 0


def test_deterministic_identity_is_stable_for_same_work_item_and_sha(tmp_path):
    asset = _asset(tmp_path)
    first = cloudinary.deterministic_cloudinary_public_id(
        work_item_id="operator-requested-trigger-1", asset_sha256=asset["sha256"]
    )
    second = cloudinary.deterministic_cloudinary_public_id(
        work_item_id="operator-requested-trigger-1", asset_sha256=asset["sha256"]
    )

    assert first == second
    assert first == (
        "capital_chronicle/v1/delivery_only/operator-requested-trigger-1/"
        + asset["sha256"]
    )


def test_upload_promotes_only_exact_remote_bytes_and_persists_governed_fields(
    tmp_path, monkeypatch
):
    asset = _asset(tmp_path)
    remote_url = "https://res.cloudinary.com/test-cloud/image/upload/delivery.png"
    calls = []

    def upload(**kwargs):
        calls.append(kwargs)
        return {
            "public_id": kwargs["public_id"],
            "secure_url": remote_url,
            "asset_id": "provider-asset-1",
            "existing": False,
        }

    monkeypatch.setattr(cloudinary, "_upload_asset", upload)
    def read_remote(url):
        if url == remote_url:
            return Path(asset["path"]).read_bytes()
        raise FileNotFoundError("deterministic object not present before upload")

    monkeypatch.setattr(cloudinary, "read_public_image_bytes", read_remote)

    result = cloudinary.prepare_cloudinary_delivery_media(
        work_item_id="work-item-1",
        delivery_only_assets=[asset],
        environment=_environment(),
    )

    assert result["status"] == cloudinary.READY
    assert result["provider_calls"] == 1
    assert len(calls) == 1
    assert calls[0]["public_id"].endswith(asset["sha256"])
    row = result["manifest"]["assets"][0]
    assert row["verified_public_delivery_url"] == remote_url
    assert row["public_delivery_sha256"] == asset["sha256"]
    assert row["local_public_hash_continuity"] is True
    assert row["media_role"] == "delivery_only"
    assert row["article_inclusion"] is False
    assert row["canonical_article_media"] is False
    assert result["manifest"]["article_media_authority"] is False


def test_missing_manifest_reuses_deterministic_existing_object_without_upload(
    tmp_path, monkeypatch
):
    asset = _asset(tmp_path)
    monkeypatch.setattr(
        cloudinary,
        "_upload_asset",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("must not duplicate")),
    )
    monkeypatch.setattr(
        cloudinary,
        "read_public_image_bytes",
        lambda _url: Path(asset["path"]).read_bytes(),
    )

    result = cloudinary.prepare_cloudinary_delivery_media(
        work_item_id="work-item-1",
        delivery_only_assets=[asset],
        existing_manifest={},
        environment=_environment(),
    )

    assert result["status"] == cloudinary.READY
    assert result["provider_calls"] == 0
    assert result["reused_asset_count"] == 1
    row = result["manifest"]["assets"][0]
    assert row["provider_object_reused"] is True
    assert row["verified_public_delivery_url"].endswith(asset["sha256"] + ".png")


def test_exact_persisted_object_is_reverified_and_reused_without_upload(
    tmp_path, monkeypatch
):
    asset = _asset(tmp_path)
    remote_url = "https://res.cloudinary.com/test-cloud/image/upload/delivery.png"
    monkeypatch.setattr(
        cloudinary,
        "_upload_asset",
        lambda **kwargs: {
            "public_id": kwargs["public_id"],
            "secure_url": remote_url,
            "asset_id": "provider-asset-1",
        },
    )
    monkeypatch.setattr(
        cloudinary, "read_public_image_bytes", lambda _url: Path(asset["path"]).read_bytes()
    )
    initial = cloudinary.prepare_cloudinary_delivery_media(
        work_item_id="work-item-1",
        delivery_only_assets=[asset],
        environment=_environment(),
    )
    monkeypatch.setattr(
        cloudinary,
        "_upload_asset",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("must reuse")),
    )

    reused = cloudinary.prepare_cloudinary_delivery_media(
        work_item_id="work-item-1",
        delivery_only_assets=[asset],
        existing_manifest=initial["manifest"],
        environment=_environment(),
    )

    assert reused["status"] == cloudinary.READY
    assert reused["provider_calls"] == 0
    assert reused["reused_asset_count"] == 1
    assert reused["manifest"]["assets"][0]["provider_object_reused"] is True


def test_remote_hash_mismatch_blocks_verified_url_promotion(tmp_path, monkeypatch):
    asset = _asset(tmp_path)
    other = tmp_path / "other.png"
    Image.new("RGB", (1350, 1080), "#ffffff").save(other, format="PNG")
    monkeypatch.setattr(
        cloudinary,
        "_upload_asset",
        lambda **kwargs: {
            "public_id": kwargs["public_id"],
            "secure_url": "https://res.cloudinary.com/test-cloud/image/upload/delivery.png",
        },
    )
    monkeypatch.setattr(cloudinary, "read_public_image_bytes", lambda _url: other.read_bytes())

    result = cloudinary.prepare_cloudinary_delivery_media(
        work_item_id="work-item-1",
        delivery_only_assets=[asset],
        environment=_environment(),
    )

    assert result["status"] == "BLOCKED_CLOUDINARY_DELIVERY_MEDIA_PREPARATION"
    assert any("cloudinary_remote_sha256_mismatch" in row for row in result["blockers"])
    assert "manifest" not in result


def test_unreachable_remote_object_fails_closed_without_secret_leak(tmp_path, monkeypatch):
    asset = _asset(tmp_path)
    monkeypatch.setattr(
        cloudinary,
        "_upload_asset",
        lambda **kwargs: {
            "public_id": kwargs["public_id"],
            "secure_url": "https://res.cloudinary.com/test-cloud/image/upload/delivery.png",
        },
    )
    monkeypatch.setattr(
        cloudinary,
        "read_public_image_bytes",
        lambda _url: (_ for _ in ()).throw(TimeoutError("secret-bearing-provider-text")),
    )

    result = cloudinary.prepare_cloudinary_delivery_media(
        work_item_id="work-item-1",
        delivery_only_assets=[asset],
        environment=_environment(),
    )

    assert result["status"] == "BLOCKED_CLOUDINARY_DELIVERY_MEDIA_PREPARATION"
    assert "secret-bearing-provider-text" not in json.dumps(result, sort_keys=True)


def test_wrong_mime_or_dimensions_blocks_hosted_media(tmp_path, monkeypatch):
    asset = _asset(tmp_path)
    jpeg = tmp_path / "delivery.jpg"
    Image.new("RGB", (900, 900), "#07111f").save(jpeg, format="JPEG")
    monkeypatch.setattr(cloudinary, "read_public_image_bytes", lambda _url: jpeg.read_bytes())

    verification = cloudinary._verify_remote_object(
        public_url="https://res.cloudinary.com/test-cloud/image/upload/delivery.jpg",
        expected_sha256=sha256_file(jpeg),
        expected_metadata=asset,
    )

    assert verification["status"] == "BLOCKED_CLOUDINARY_HOSTED_MEDIA_MISMATCH"
    assert "cloudinary_remote_mime_type_mismatch" in verification["blockers"]
    assert "cloudinary_remote_width_mismatch" in verification["blockers"]
    assert "cloudinary_remote_height_mismatch" in verification["blockers"]


def test_selected_card_never_silently_becomes_bare_text_before_url_delivery(tmp_path, monkeypatch):
    import live_contentops._eight_platform_substack_first_pipeline_impl_v1 as pipeline
    asset = _asset(tmp_path)
    for destination in ("facebook_page", "instagram_business", "threads"):
        data = {"media_assets": [asset], "primary_media": {}, "public_image_url": "",
            "payloads": {destination: {"text": "Controlled approved copy",
                "media_asset_ids": [asset["asset_id"]]}}}
        monkeypatch.setattr(pipeline, "_durable_intent_inputs", lambda _: data)
        result = pipeline._publish_one_destination_from_durable_intent(destination=destination,
            intent={"attempt_identity": "controlled"}, authorization_context={
                "operating_mode": "AUTONOMOUS_DEFAULT", "dispatch_attempt_identity": "controlled"})
        assert result["definite_no_write"] and result["public_write_performed"] is False
        assert result["reason_code"] == "SELECTED_IMAGE_PUBLIC_DELIVERY_REQUIRED:" + destination


def test_discord_uses_the_reviewed_local_card_without_needing_url_delivery(tmp_path, monkeypatch):
    import live_contentops._eight_platform_substack_first_pipeline_impl_v1 as pipeline
    asset = _asset(tmp_path)
    data = {"output_dir": tmp_path, "article": {"title": "Controlled filing"}, "selection": {},
        "media_assets": [asset], "delivery_only_assets": [], "primary_media": {}, "public_image_url": "",
        "local_media": asset["path"], "canonical_url": "https://capitalchronicle.substack.com/p/controlled",
        "payloads": {"discord": {"text": "Controlled approved copy", "media_asset_ids": [asset["asset_id"]]}}}
    monkeypatch.setattr(pipeline, "_durable_intent_inputs", lambda _: data)
    captured = []
    def publish(**kwargs):
        captured.append(kwargs)
        return {"status": "SUCCESS"}
    monkeypatch.setattr(pipeline, "_publish_discord_verified", publish)
    result = pipeline._publish_one_destination_from_durable_intent(destination="discord",
        intent={"attempt_identity": "controlled"}, authorization_context={
            "operating_mode": "AUTONOMOUS_DEFAULT", "dispatch_attempt_identity": "controlled"})
    assert result["status"] == "SUCCESS" and captured[0]["image_path"] == asset["path"]


def test_substack_adapter_has_no_delivery_only_contract_or_staging_failure():
    import live_contentops.edge_cdp_publishing_adapter_v1 as substack

    signature = inspect.signature(substack.publish_substack_article_via_edge)
    source = inspect.getsource(substack.publish_substack_article_via_edge)
    module_source = inspect.getsource(substack)

    assert "delivery_only_assets" not in signature.parameters
    assert "FAILED_SUBSTACK_DELIVERY_MEDIA_STAGING" not in source
    assert "_stage_and_remove_delivery_only_image" not in module_source
