from dataclasses import asdict

import pytest

from live_contentops import approval_ledger as ledger
from live_contentops import approval_payload_hash as aph
from live_contentops import approval_validator as validator


def test_validator_mismatch_fields_fail_closed():
    # Build payload_data
    payload_data = aph.canonical_payload_hash_input(
        platform_id="x_profile",
        destination_binding_id="x_profile_default",
        credential_handle_id="x_bearer",
        payload_schema_version="v1",
        adapter_version="1.0.0",
        payload_class_id="x_short_post",
        payload_text="Grounded macro insight",
        platform_formatting="plain",
        media_manifest_hash="hash1",
        policy_snapshot_id="v1",
    )
    p_hash = aph.compute_payload_hash(payload_data)

    # Correct approval event
    app_event = ledger.build_operator_approved_event(
        operator_id="jim_op",
        approval_channel="local_ui",
        challenge_id=None,
        payload_id="p1",
        payload_hash=p_hash,
        platform_id="x_profile",
        payload_class_id="x_short_post",
        destination_binding_id="x_profile_default",
        credential_handle_id="x_bearer",
        policy_snapshot_id="v1",
        media_manifest_hash="hash1",
    )

    # 1. Correct event validates cleanly
    assert not validator.validate_approval_event_against_payload(app_event, payload_data)
    assert validator.is_approval_current_for_payload([app_event], "p1", payload_data) is True

    # 2. Hash mismatch fails
    bad_payload = dict(payload_data, payload_text="Different text")
    blockers = validator.validate_approval_event_against_payload(app_event, bad_payload)
    assert "payload_hash_mismatch" in blockers

    # 3. Platform mismatch fails
    bad_payload_platform = dict(payload_data, platform_id="facebook_page")
    assert "platform_id_mismatch" in validator.validate_approval_event_against_payload(app_event, bad_payload_platform)

    # 4. Payload class mismatch fails
    bad_payload_class = dict(payload_data, payload_class_id="x_thread")
    assert "payload_class_id_mismatch" in validator.validate_approval_event_against_payload(app_event, bad_payload_class)

    # 5. Destination mismatch fails
    bad_payload_dest = dict(payload_data, destination_binding_id="different_dest")
    assert "destination_binding_id_mismatch" in validator.validate_approval_event_against_payload(app_event, bad_payload_dest)

    # 6. Credential mismatch fails
    bad_payload_cred = dict(payload_data, credential_handle_id="different_cred")
    assert "credential_handle_id_mismatch" in validator.validate_approval_event_against_payload(app_event, bad_payload_cred)

    # 7. Media manifest mismatch fails
    bad_payload_media = dict(payload_data, media_manifest_hash="different_media")
    assert "media_manifest_hash_mismatch" in validator.validate_approval_event_against_payload(app_event, bad_payload_media)

    # 8. Policy snapshot mismatch fails
    bad_payload_policy = dict(payload_data, policy_snapshot_id="different_policy")
    assert "policy_snapshot_id_mismatch" in validator.validate_approval_event_against_payload(app_event, bad_payload_policy)


def test_missing_operator_fails_closed():
    payload_data = aph.canonical_payload_hash_input(
        platform_id="x_profile",
        destination_binding_id="x_profile_default",
        credential_handle_id="x_bearer",
        payload_schema_version="v1",
        adapter_version="1.0.0",
        payload_class_id="x_short_post",
        payload_text="Grounded macro insight",
        platform_formatting="plain",
    )
    p_hash = aph.compute_payload_hash(payload_data)

    event = ledger.build_operator_approved_event(
        operator_id="jim_op",
        approval_channel="local_ui",
        challenge_id=None,
        payload_id="p1",
        payload_hash=p_hash,
        platform_id="x_profile",
        payload_class_id="x_short_post",
        destination_binding_id="x_profile_default",
        credential_handle_id="x_bearer",
        policy_snapshot_id="v1",
    )
    event_dict = asdict(event)
    event_dict["operator_id"] = ""

    blockers = validator.validate_approval_event_against_payload(event_dict, payload_data)
    assert "missing_operator_id" in blockers


def test_stale_approval_after_revocation_or_invalidation():
    payload_data = aph.canonical_payload_hash_input(
        platform_id="x_profile",
        destination_binding_id="x_profile_default",
        credential_handle_id="x_bearer",
        payload_schema_version="v1",
        adapter_version="1.0.0",
        payload_class_id="x_short_post",
        payload_text="Grounded macro insight",
        platform_formatting="plain",
    )
    p_hash = aph.compute_payload_hash(payload_data)

    app_event = ledger.build_operator_approved_event(
        operator_id="jim_op",
        approval_channel="local_ui",
        challenge_id=None,
        payload_id="p1",
        payload_hash=p_hash,
        platform_id="x_profile",
        payload_class_id="x_short_post",
        destination_binding_id="x_profile_default",
        credential_handle_id="x_bearer",
        policy_snapshot_id="v1",
    )

    # 1. Approval alone is approved_current
    history = [app_event]
    assert validator.derive_latest_approval_state(history, "p1", payload_data) == "approved_current"

    # 2. Revocation invalidates it
    rev_event = ledger.build_operator_revoked_event(
        operator_id="jim_op",
        payload_id="p1",
        payload_hash=p_hash,
        supersedes_event_id=app_event.ledger_event_id,
    )
    history.append(rev_event)
    assert validator.derive_latest_approval_state(history, "p1", payload_data) == "revoked"

    # 3. Edit invalidation invalidates it
    history2 = [app_event]
    inv_event = ledger.build_approval_invalidated_event(
        operator_id="jim_op",
        payload_id="p1",
        payload_hash=p_hash,
        invalidation_reason="edit",
        supersedes_event_id=app_event.ledger_event_id,
    )
    history2.append(inv_event)
    assert validator.derive_latest_approval_state(history2, "p1", payload_data) == "invalidated_by_edit"
