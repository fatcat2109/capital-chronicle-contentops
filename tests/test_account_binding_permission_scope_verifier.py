import json

import pytest

from live_contentops import account_binding_permission_scope_verifier as verifier

REQUIRED_PLATFORMS = {
    "x_profile",
    "telegram_remote_operator_inbox",
    "telegram_channel_destination",
    "substack_newsletter",
    "linkedin_member_profile",
    "linkedin_organization_page",
    "threads_profile",
    "instagram_professional_account",
    "facebook_page",
    "tiktok_account",
    "youtube_channel",
}


def _ready_variant(proof):
    return verifier.DestinationBindingProof(
        **{
            **proof.as_dict(),
            "operator_confirmed": True,
            "confirmation_method": "operator_checked_symbolic",
            "permission_status": "permission_verified_symbolic",
            "scope_status": "scope_verified_symbolic",
            "account_binding_status": "symbolically_ready_but_live_write_forbidden",
            "wrong_account_detection_status": "wrong_account_not_detected_symbolic",
            "official_docs_status": "official_docs_checked_current",
            "last_verified_at": "2026-06-23T21:00:00Z",
            "blocked_reasons": ("live_write_forbidden_until_future_gate",),
        }
    )


def test_all_binding_proofs_exist_and_are_deterministic():
    first = verifier.account_binding_permission_scope_packet()
    second = verifier.account_binding_permission_scope_packet()
    assert first == second
    rows = verifier.build_symbolic_destination_binding_proofs()
    assert {row.platform_id for row in rows} == REQUIRED_PLATFORMS
    assert set(first["platform_ids"]) == REQUIRED_PLATFORMS
    assert first["all_platforms_covered"] is True
    json.dumps(first, sort_keys=True)


def test_all_default_bindings_are_fail_closed_no_live():
    rows = verifier.build_symbolic_destination_binding_proofs()
    verifier.assert_no_live_write_allowed(rows)
    for row in rows:
        assert row.live_write_allowed_now is False
        assert row.can_post_live_now is False
        assert row.dispatchable_now is False
        assert row.public_postable_now is False
        assert row.read_only_probe_performed is False
        assert row.read_only_probe_allowed_in_this_task is False
        assert row.credential_hydration_performed is False
        assert row.credential_hydration_allowed_in_this_task is False
        assert row.no_secret_output is True
        assert "operator_confirmation_missing" in row.blocked_reasons
        assert "live_write_forbidden_until_future_gate" in row.blocked_reasons


def test_missing_operator_confirmation_blocks():
    proof = verifier.bindings_by_platform_id()["x_profile"]
    assert verifier.derive_account_binding_status(
        operator_confirmed=False,
        permission_status="permission_verified_symbolic",
        scope_status="scope_verified_symbolic",
        wrong_account_detection_status="wrong_account_not_detected_symbolic",
        official_docs_status="official_docs_checked_current",
    ) == "operator_confirmation_missing_blocked"
    with pytest.raises(verifier.AccountBindingVerificationError):
        verifier.validate_destination_binding_proof(proof)


def test_missing_credential_permission_and_scope_block():
    proof = verifier.bindings_by_platform_id()["telegram_channel_destination"]
    missing_credential = verifier.DestinationBindingProof(**{**proof.as_dict(), "credential_handle_id": ""})
    blockers = verifier.explain_binding_blockers(missing_credential)
    assert "credential_handle_id_missing" in blockers
    assert "permission_unverified" in blockers
    assert "scope_unverified" in blockers
    with pytest.raises(verifier.AccountBindingVerificationError):
        verifier.validate_destination_binding_proof(missing_credential)


def test_wrong_account_detection_blocks_even_with_other_proofs():
    proof = _ready_variant(verifier.bindings_by_platform_id()["linkedin_member_profile"])
    wrong = verifier.DestinationBindingProof(
        **{
            **proof.as_dict(),
            "wrong_account_detection_status": "wrong_account_detected",
            "account_binding_status": "wrong_account_blocked",
        }
    )
    assert "wrong_account_detection_not_clear" in verifier.explain_binding_blockers(wrong)
    with pytest.raises(verifier.AccountBindingVerificationError):
        verifier.validate_destination_binding_proof(wrong)


def test_official_docs_not_current_blocks():
    proof = _ready_variant(verifier.bindings_by_platform_id()["facebook_page"])
    stale = verifier.DestinationBindingProof(
        **{
            **proof.as_dict(),
            "official_docs_status": "official_docs_stale_blocked",
            "account_binding_status": "official_docs_not_current_blocked",
        }
    )
    assert "official_docs_not_current" in verifier.explain_binding_blockers(stale)
    with pytest.raises(verifier.AccountBindingVerificationError):
        verifier.validate_destination_binding_proof(stale)


def test_destination_kind_mismatch_blocks():
    proof = _ready_variant(verifier.bindings_by_platform_id()["linkedin_organization_page"])
    wrong_kind = verifier.DestinationBindingProof(**{**proof.as_dict(), "destination_kind": "member_profile"})
    assert "destination_kind_mismatch" in verifier.explain_binding_blockers(wrong_kind)
    with pytest.raises(verifier.AccountBindingVerificationError):
        verifier.validate_destination_binding_proof(wrong_kind)


def test_ready_symbolic_binding_still_not_live_write_ready():
    proof = _ready_variant(verifier.bindings_by_platform_id()["youtube_channel"])
    checked = verifier.validate_destination_binding_proof(proof)
    assert checked.account_binding_status == "symbolically_ready_but_live_write_forbidden"
    assert checked.live_write_allowed_now is False
    assert checked.can_post_live_now is False
    assert "live_write_forbidden_until_future_gate" in checked.blocked_reasons


def test_approval_invalidation_fields_include_binding_and_platform_identity():
    fields = verifier.approval_invalidation_fields_for_binding("instagram_professional_account")
    assert "destination_binding_id" in fields
    assert "platform_id" in fields
    assert "platform_account_id_redacted" in fields
    assert "credential_handle_id" in fields
    assert "media_container_permission" in fields


def test_secret_shaped_material_is_blocked():
    with pytest.raises(verifier.AccountBindingVerificationError):
        verifier.assert_no_secret_shaped_material("123456789:ABCdefGHijkLMNopqRSTuvwXYZ123456789")
    verifier.assert_no_secret_shaped_material(verifier.account_binding_permission_scope_packet())
