import pytest

from live_contentops import approval_payload_hash as aph


def test_same_canonical_payload_creates_same_hash():
    input1 = aph.canonical_payload_hash_input(
        platform_id="x_profile",
        destination_binding_id="x_profile_default",
        credential_handle_id="x_bearer",
        payload_schema_version="v1",
        adapter_version="1.0.0",
        payload_class_id="x_short_post",
        payload_text="Macro update",
        platform_formatting="plain",
    )
    input2 = aph.canonical_payload_hash_input(
        platform_id="x_profile",
        destination_binding_id="x_profile_default",
        credential_handle_id="x_bearer",
        payload_schema_version="v1",
        adapter_version="1.0.0",
        payload_class_id="x_short_post",
        payload_text="Macro update",
        platform_formatting="plain",
    )
    assert aph.compute_payload_hash(input1) == aph.compute_payload_hash(input2)


def test_dict_key_order_does_not_change_hash():
    # Construct dicts with different ordering
    input1 = {
        "platform_id": "x_profile",
        "destination_binding_id": "x_profile_default",
        "credential_handle_id": "x_bearer",
        "payload_schema_version": "v1",
        "adapter_version": "1.0.0",
        "payload_class_id": "x_short_post",
        "payload_text": "Macro update",
        "platform_formatting": "plain",
    }
    input2 = {
        "payload_text": "Macro update",
        "platform_formatting": "plain",
        "platform_id": "x_profile",
        "destination_binding_id": "x_profile_default",
        "credential_handle_id": "x_bearer",
        "payload_schema_version": "v1",
        "adapter_version": "1.0.0",
        "payload_class_id": "x_short_post",
    }
    assert aph.compute_payload_hash(input1) == aph.compute_payload_hash(input2)


def test_changes_yield_different_hashes():
    base = {
        "platform_id": "x_profile",
        "destination_binding_id": "x_profile_default",
        "credential_handle_id": "x_bearer",
        "payload_schema_version": "v1",
        "adapter_version": "1.0.0",
        "payload_class_id": "x_short_post",
        "payload_text": "Macro update",
        "platform_formatting": "plain",
    }

    # Text changes hash
    c_text = dict(base, payload_text="Macro update delta")
    assert aph.compute_payload_hash(base) != aph.compute_payload_hash(c_text)

    # Platform changes hash
    c_platform = dict(base, platform_id="facebook_page")
    assert aph.compute_payload_hash(base) != aph.compute_payload_hash(c_platform)

    # Destination binding changes hash
    c_dest = dict(base, destination_binding_id="fb_page_default")
    assert aph.compute_payload_hash(base) != aph.compute_payload_hash(c_dest)

    # Credential handle changes hash
    c_cred = dict(base, credential_handle_id="meta_token")
    assert aph.compute_payload_hash(base) != aph.compute_payload_hash(c_cred)

    # Media manifest changes hash
    c_media = dict(base, media_manifest_hash="hashabc")
    assert aph.compute_payload_hash(base) != aph.compute_payload_hash(c_media)

    # Policy snapshot changes hash
    c_policy = dict(base, policy_snapshot_id="v2")
    assert aph.compute_payload_hash(base) != aph.compute_payload_hash(c_policy)

    # Adapter version changes hash
    c_adapter = dict(base, adapter_version="1.0.1")
    assert aph.compute_payload_hash(base) != aph.compute_payload_hash(c_adapter)

    # Payload schema version changes hash
    c_schema = dict(base, payload_schema_version="v2")
    assert aph.compute_payload_hash(base) != aph.compute_payload_hash(c_schema)


def test_secret_shaped_values_fail_closed():
    base = {
        "platform_id": "x_profile",
        "destination_binding_id": "x_profile_default",
        "credential_handle_id": "x_bearer",
        "payload_schema_version": "v1",
        "adapter_version": "1.0.0",
        "payload_class_id": "x_short_post",
        "payload_text": "Macro update with bot token 123456:AABBCCDDEEFFGGHHIIJJKKLLMMNNOOPPQQRR",
        "platform_formatting": "plain",
    }
    with pytest.raises(AssertionError):
        aph.compute_payload_hash(base)


def test_forbidden_hash_input_fields_fail_closed():
    # If any key is in FORBIDDEN_KEYWORDS
    bad_dict = {
        "platform_id": "x_profile",
        "destination_binding_id": "x_profile_default",
        "credential_handle_id": "x_bearer",
        "payload_schema_version": "v1",
        "adapter_version": "1.0.0",
        "payload_class_id": "x_short_post",
        "payload_text": "Macro update",
        "platform_formatting": "plain",
        "cookie": "some_cookie",
    }
    with pytest.raises(AssertionError):
        aph.compute_payload_hash(bad_dict)
