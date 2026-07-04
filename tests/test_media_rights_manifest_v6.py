import pytest

from live_contentops.media_rights_manifest_v6 import build_media_item, build_media_manifest, validate_media_manifest


def test_builds_ready_manifest_with_media_hash_and_no_live_claims():
    manifest = build_media_manifest()

    assert manifest["status"] == "READY_FOR_OPERATOR_MEDIA_REVIEW"
    assert manifest["media_manifest_hash"]
    assert manifest["exact_payload_hash"]
    assert manifest["media_required_for_platforms"] == []
    assert manifest["media_optional_for_platforms"] == ["substack", "discord", "x", "linkedin"]
    assert manifest["safety_flags"]["network_call_made"] is False
    assert manifest["safety_flags"]["image_provider_call_made"] is False
    assert manifest["safety_flags"]["download_performed"] is False
    validate_media_manifest(manifest)


def test_external_media_requires_rights_status():
    item = build_media_item(
        media_id="external_missing_rights",
        media_type="rights_checked_external_image",
        alt_text="External image candidate.",
        origin="external_metadata_only_no_fetch",
        attribution="Operator supplied attribution.",
        source_label="Operator supplied source.",
    )

    assert "external_media_rights_status_missing_or_invalid" in item["blockers"]


def test_external_media_requires_attribution_and_source():
    item = build_media_item(
        media_id="external_missing_attr",
        media_type="rights_checked_external_image",
        alt_text="External image candidate.",
        origin="external_metadata_only_no_fetch",
        rights_status="operator_supplied_rights_checked",
    )

    assert "external_media_attribution_missing" in item["blockers"]
    assert "external_media_source_label_missing" in item["blockers"]


def test_alt_text_required_for_media_items():
    item = build_media_item(
        media_id="missing_alt",
        media_type="hero_image_candidate",
        alt_text="",
        origin="internal_spec_only",
        rights_status="owned",
        attribution="Capital Chronicle",
        source_label="internal",
    )
    manifest = build_media_manifest(media_items=[item])

    assert "missing_alt:alt_text_missing" in manifest["blockers"]
    with pytest.raises(ValueError, match="alt_text_required"):
        validate_media_manifest(manifest)


def test_media_hash_participates_in_manifest_hash():
    manifest = build_media_manifest()
    tampered = {**manifest, "media_items": [{**manifest["media_items"][0], "media_hash": "tampered"}]}

    with pytest.raises(ValueError, match="media_hash_mismatch"):
        validate_media_manifest(tampered)


def test_non_media_platforms_do_not_require_media():
    manifest = build_media_manifest(selected_platforms=["discord"], media_items=[])

    assert manifest["media_required_for_platforms"] == []
    assert manifest["media_optional_for_platforms"] == ["discord"]
    assert manifest["status"] == "READY_FOR_OPERATOR_MEDIA_REVIEW"


def test_blocks_secret_like_keys():
    item = build_media_item(
        media_id="secret_item",
        media_type="hero_image_candidate",
        alt_text="Hero candidate.",
        origin="internal_spec_only",
        rights_status="owned",
        attribution="Capital Chronicle",
        source_label="internal",
        card_packet={"credential_handle": "redacted"},
    )

    assert "secret_like_key_blocked" in item["blockers"]
