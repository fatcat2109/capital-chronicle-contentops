import pytest
from urllib.parse import urlparse

from live_contentops import platform_permission_scope_app_review_gate_matrix_contract as contract
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit

def test_packet_builds_deterministically():
    packet1 = contract.build_platform_permission_scope_app_review_gate_packet()
    packet2 = contract.build_platform_permission_scope_app_review_gate_packet()
    assert packet1.packet_id == packet2.packet_id
    assert packet1.packet_hash == packet2.packet_hash
    assert len(packet1.permission_gate_rows) == 10


def test_every_requirement_has_official_doc_ref_and_allowed_domain():
    reqs = contract.build_default_requirements()
    for req in reqs:
        parsed = urlparse(req.official_doc_url)
        host = parsed.netloc.split(":")[0]
        assert host in contract.ALLOWED_DOMAINS
        assert req.official_domain == host


def test_unofficial_domain_input_fails_closed():
    with pytest.raises(ValueError):
        contract.PermissionScopeRequirement(
            requirement_id="req_invalid",
            platform_id="x",
            requirement_kind="oauth_scope",
            requirement_name="Invalid OAuth Scope",
            official_doc_ref_id="doc_invalid",
            official_doc_url="https://leakdocs.org/scope",  # Unofficial domain
            official_domain="leakdocs.org",
            permission_status="symbolic_only",
            app_review_required=True,
            account_role_proof_required=False,
            credential_required_future=True,
            live_read_allowed=False,
            live_write_allowed=False,
            env_read=False,
            credential_hydrated=False,
            platform_api_called=False,
            evidence_refs=(),
            blocked_reasons=(),
            safety_flags=contract.safety_flags(),
            requirement_hash="",
            requirement_hash_algorithm="sha256",
        )

    # Mismatched domain should also fail closed
    with pytest.raises(ValueError):
        contract.PermissionScopeRequirement(
            requirement_id="req_invalid",
            platform_id="x",
            requirement_kind="oauth_scope",
            requirement_name="Invalid OAuth Scope",
            official_doc_ref_id="doc_invalid",
            official_doc_url="https://developer.x.com/scope",
            official_domain="developer.facebook.com",  # Mismatch
            permission_status="symbolic_only",
            app_review_required=True,
            account_role_proof_required=False,
            credential_required_future=True,
            live_read_allowed=False,
            live_write_allowed=False,
            env_read=False,
            credential_hydrated=False,
            platform_api_called=False,
            evidence_refs=(),
            blocked_reasons=(),
            safety_flags=contract.safety_flags(),
            requirement_hash="",
            requirement_hash_algorithm="sha256",
        )


def test_safety_violations_fail_closed():
    # If any live/write/read count is true, it should raise ValueError
    with pytest.raises(ValueError):
        contract.PermissionScopeRequirement(
            requirement_id="req_invalid",
            platform_id="x",
            requirement_kind="oauth_scope",
            requirement_name="Invalid OAuth Scope",
            official_doc_ref_id="doc_invalid",
            official_doc_url="https://developer.x.com/scope",
            official_domain="developer.x.com",
            permission_status="symbolic_only",
            app_review_required=True,
            account_role_proof_required=False,
            credential_required_future=True,
            live_read_allowed=True,  # Safety violation
            live_write_allowed=False,
            env_read=False,
            credential_hydrated=False,
            platform_api_called=False,
            evidence_refs=(),
            blocked_reasons=(),
            safety_flags=contract.safety_flags(),
            requirement_hash="",
            requirement_hash_algorithm="sha256",
        )


def test_x_row_does_not_clear_readiness_and_includes_blockers():
    packet = contract.build_platform_permission_scope_app_review_gate_packet()
    x_row = next(r for r in packet.permission_gate_rows if r.platform_id == "x")
    
    assert x_row.gate_status == "needs_human_review"
    assert x_row.gate_strength == "partial_official_docs"
    assert "rate_limit_and_spend_gate_unresolved" in x_row.blocked_reasons
    assert x_row.readiness_cleared is False


def test_telegram_remote_operator_and_channel_are_distinct():
    packet = contract.build_platform_permission_scope_app_review_gate_packet()
    op_row = next(r for r in packet.permission_gate_rows if r.platform_id == "telegram_remote_operator")
    ch_row = next(r for r in packet.permission_gate_rows if r.platform_id == "telegram_channel_destination")
    
    assert op_row.row_id != ch_row.row_id
    assert op_row.platform_role != ch_row.platform_role
    
    assert "bot_admin_gate_closed" in ch_row.blocked_reasons
    assert "not_public_destination" in op_row.blocked_reasons


def test_substack_is_manual_export_only_without_fake_api_scope():
    packet = contract.build_platform_permission_scope_app_review_gate_packet()
    substack_row = next(r for r in packet.permission_gate_rows if r.platform_id == "substack_newsletter")
    
    assert substack_row.gate_status == "blocked_manual_export_only"
    assert substack_row.gate_strength == "weak_manual_policy"
    assert len(substack_row.required_oauth_scopes) == 0
    assert "manual_export_first_no_api" in substack_row.blocked_reasons


def test_linkedin_member_and_org_page_distinction_exists():
    packet = contract.build_platform_permission_scope_app_review_gate_packet()
    linkedin_row = next(r for r in packet.permission_gate_rows if r.platform_id == "linkedin")
    
    assert "w_member_social" in linkedin_row.required_oauth_scopes[0]
    assert "linkedin_organization_page_binding_missing" in linkedin_row.blocked_reasons
    assert "organization_page_proof_required" in linkedin_row.blocked_reasons


def test_meta_threads_instagram_facebook_rows_are_separate():
    packet = contract.build_platform_permission_scope_app_review_gate_packet()
    threads_row = next(r for r in packet.permission_gate_rows if r.platform_id == "threads")
    insta_row = next(r for r in packet.permission_gate_rows if r.platform_id == "instagram")
    fb_row = next(r for r in packet.permission_gate_rows if r.platform_id == "facebook_page")
    
    assert threads_row.row_id != insta_row.row_id
    assert insta_row.row_id != fb_row.row_id
    
    assert "threads_basic" in threads_row.required_oauth_scopes[0]
    assert "instagram_basic" in insta_row.required_oauth_scopes[0]
    assert "pages_read_engagement" in fb_row.required_oauth_scopes[0]


def test_tiktok_scopes_and_audit_blocker_exist():
    packet = contract.build_platform_permission_scope_app_review_gate_packet()
    tiktok_row = next(r for r in packet.permission_gate_rows if r.platform_id == "tiktok")
    
    assert "user.info.basic" in tiktok_row.required_oauth_scopes[0]
    assert "tiktok_audit_closed" in tiktok_row.blocked_reasons


def test_youtube_scopes_and_blocker_exist_no_stale_1600():
    packet = contract.build_platform_permission_scope_app_review_gate_packet()
    youtube_row = next(r for r in packet.permission_gate_rows if r.platform_id == "youtube")
    
    assert "youtube.upload" in youtube_row.required_oauth_scopes[0]
    assert "youtube_oauth_channel_proof_required" in youtube_row.blocked_reasons
    
    # Assert no stale youtube unit quota is referenced anywhere in matrix or runbook
    runbook_content = contract.render_runbook(packet)
    assert "1600" not in runbook_content


def test_safety_invariants_and_all_live_counts_are_zero():
    packet = contract.build_platform_permission_scope_app_review_gate_packet()
    
    assert packet.live_read_allowed_count == 0
    assert packet.live_write_allowed_count == 0
    assert packet.env_read_count == 0
    assert packet.credential_hydrated_count == 0
    assert packet.platform_api_called_count == 0
    assert packet.readiness_cleared_count == 0
    assert packet.public_post_allowed_count == 0
    
    for row in packet.permission_gate_rows:
        assert row.live_read_allowed is False
        assert row.live_write_allowed is False
        assert row.env_read is False
        assert row.credential_hydrated is False
        assert row.platform_api_called is False
        assert row.readiness_cleared is False
        assert row.public_post_allowed is False


def test_u9_audit_entries_validate_cleanly():
    packet = contract.build_platform_permission_scope_app_review_gate_packet()
    assert len(packet.u9_audit_entry_ids) == 10
    assert all(f == "permission_scope_gate_future" for f in packet.u9_audit_entry_families)
    
    # Verify we can build ledger chain and validate it using ledger logic
    entries = contract.build_u9_audit_entries(packet)
    chain = audit.build_ledger_chain(entries)
    validation = audit.validate_ledger_chain(chain)
    
    assert validation.validation_status == "pass"
    assert len(validation.blocked_reasons) == 0


def test_artifact_writer_enforces_directory_restriction(tmp_path):
    # Should raise ValueError if trying to write outside DOC_REL_DIR
    with pytest.raises(ValueError):
        contract.write_artifacts(repo_root=tmp_path, output_dir=tmp_path / "unauthorized_dir")
