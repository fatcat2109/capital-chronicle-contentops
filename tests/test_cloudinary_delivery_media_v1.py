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


def test_substack_adapter_has_no_delivery_only_contract_or_staging_failure():
    import live_contentops.edge_cdp_publishing_adapter_v1 as substack

    signature = inspect.signature(substack.publish_substack_article_via_edge)
    source = inspect.getsource(substack.publish_substack_article_via_edge)
    module_source = inspect.getsource(substack)

    assert "delivery_only_assets" not in signature.parameters
    assert "FAILED_SUBSTACK_DELIVERY_MEDIA_STAGING" not in source
    assert "_stage_and_remove_delivery_only_image" not in module_source
