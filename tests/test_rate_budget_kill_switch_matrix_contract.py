import pytest
from urllib.parse import urlparse

from live_contentops import rate_budget_kill_switch_matrix_contract as contract
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit

def test_packet_builds_deterministically():
    packet1 = contract.build_rate_budget_kill_switch_packet()
    packet2 = contract.build_rate_budget_kill_switch_packet()
    assert packet1.packet_id == packet2.packet_id
    assert packet1.packet_hash == packet2.packet_hash
    assert len(packet1.rows) == 10


def test_every_requirement_has_official_doc_ref_and_allowed_domain():
    reqs = contract.build_default_requirements()
    for req in reqs:
        parsed = urlparse(req.official_doc_url)
        host = parsed.netloc.split(":")[0]
        assert host in contract.ALLOWED_DOMAINS
        assert req.official_domain == host


def test_unofficial_domain_input_fails_closed():
    with pytest.raises(ValueError):
        contract.RateBudgetRequirement(
            requirement_id="req_invalid",
            platform_id="x",
            requirement_kind="endpoint_rate_limit",
            requirement_name="Invalid Rate Limit",
            official_doc_ref_id="doc_invalid",
            official_doc_url="https://leakdocs.org/rate",  # Unofficial
            official_domain="leakdocs.org",
            claim_support_status="unsupported_by_cited_doc",
            exact_numeric_claim=True,
            exact_numeric_claim_has_direct_doc_proof=False,
            budget_or_quota_value_summary="unverified limits",
            request_budget_default=0,
            max_request_budget_allowed=0,
            retry_allowed=False,
            auto_retry_allowed=False,
            kill_switch_required=True,
            kill_switch_default_state="enabled",
            timeout_seconds_default=10,
            failure_mode="fail_closed_rate_limit_unknown",
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
        contract.RateBudgetRequirement(
            requirement_id="req_invalid",
            platform_id="x",
            requirement_kind="endpoint_rate_limit",
            requirement_name="Invalid Rate Limit",
            official_doc_ref_id="doc_invalid",
            official_doc_url="https://developer.x.com/rate",
            official_domain="developer.x.com",
            claim_support_status="supported_by_cited_doc",
            exact_numeric_claim=False,
            exact_numeric_claim_has_direct_doc_proof=False,
            budget_or_quota_value_summary="10 calls",
            request_budget_default=0,
            max_request_budget_allowed=0,
            retry_allowed=False,
            auto_retry_allowed=False,
            kill_switch_required=True,
            kill_switch_default_state="enabled",
            timeout_seconds_default=10,
            failure_mode="fail_closed_rate_limit_unknown",
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

    # auto_retry_allowed=True is also a safety violation
    with pytest.raises(ValueError):
         contract.RateBudgetRequirement(
            requirement_id="req_invalid",
            platform_id="x",
            requirement_kind="endpoint_rate_limit",
            requirement_name="Invalid Rate Limit",
            official_doc_ref_id="doc_invalid",
            official_doc_url="https://developer.x.com/rate",
            official_domain="developer.x.com",
            claim_support_status="supported_by_cited_doc",
            exact_numeric_claim=False,
            exact_numeric_claim_has_direct_doc_proof=False,
            budget_or_quota_value_summary="10 calls",
            request_budget_default=0,
            max_request_budget_allowed=0,
            retry_allowed=False,
            auto_retry_allowed=True,  # Safety violation
            kill_switch_required=True,
            kill_switch_default_state="enabled",
            timeout_seconds_default=10,
            failure_mode="fail_closed_rate_limit_unknown",
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


def test_exact_numeric_claim_without_direct_proof_degrades_row():
    # Construct a requirement with exact numeric claim = True but has proof = False
    unsupported_req = contract.RateBudgetRequirement(
        requirement_id="req_unsupported_test",
        platform_id="tiktok",
        requirement_kind="endpoint_rate_limit",
        requirement_name="Speculative TikTok App Limits",
        official_doc_ref_id="doc_evidence_ref_tiktok_posting",
        official_doc_url="https://developers.tiktok.com/",
        official_domain="developers.tiktok.com",
        claim_support_status="not_verified_current_docs",
        exact_numeric_claim=True,
        exact_numeric_claim_has_direct_doc_proof=False,  # No Proof!
        budget_or_quota_value_summary="1000 posts per day without proof",
        request_budget_default=0,
        max_request_budget_allowed=0,
        retry_allowed=False,
        auto_retry_allowed=False,
        kill_switch_required=True,
        kill_switch_default_state="enabled",
        timeout_seconds_default=10,
        failure_mode="needs_human_review",
        live_read_allowed=False,
        live_write_allowed=False,
        env_read=False,
        credential_hydrated=False,
        platform_api_called=False,
        evidence_refs=(),
        blocked_reasons=("tiktok_speculative_limit_unproven",),
        safety_flags=contract.safety_flags(),
        requirement_hash="",
        requirement_hash_algorithm="sha256",
    )
    # Re-calculate hash
    unsupported_req = contract.replace(
        unsupported_req,
        requirement_hash=contract._digest(contract._requirement_hash_basis(unsupported_req))
    )
    
    # Mix with other default requirements
    reqs = list(contract.build_default_requirements()) + [unsupported_req]
    rows = contract.build_default_rows(tuple(reqs))
    
    # The tiktok row must be degraded to rate_budget_gate_blocked
    tiktok_row = next(r for r in rows if r.platform_id == "tiktok")
    assert tiktok_row.gate_status == "rate_budget_gate_blocked"
    assert tiktok_row.gate_strength == "blocked"
    assert "unsupported_numeric_claims_present" in tiktok_row.blocked_reasons


def test_x_row_has_pay_per_use_and_does_not_clear_readiness():
    packet = contract.build_rate_budget_kill_switch_packet()
    x_row = next(r for r in packet.rows if r.platform_id == "x")
    
    assert x_row.gate_status == "needs_human_review"
    assert x_row.gate_strength == "partial_official_docs"
    assert "rate_limit_and_spend_gate_unresolved" in x_row.blocked_reasons
    assert x_row.readiness_cleared is False


def test_telegram_remote_operator_and_channel_are_distinct():
    packet = contract.build_rate_budget_kill_switch_packet()
    op_row = next(r for r in packet.rows if r.platform_id == "telegram_remote_operator")
    ch_row = next(r for r in packet.rows if r.platform_id == "telegram_channel_destination")
    
    assert op_row.row_id != ch_row.row_id
    assert op_row.platform_role != ch_row.platform_role
    
    # Telegram operator has zero arbitrary posting
    assert "no_arbitrary_dm_allowed" in op_row.blocked_reasons


def test_substack_is_manual_export_only_with_no_api_request_budget():
    packet = contract.build_rate_budget_kill_switch_packet()
    substack_row = next(r for r in packet.rows if r.platform_id == "substack_newsletter")
    
    assert substack_row.gate_status == "manual_export_no_api"
    assert substack_row.gate_strength == "weak_manual_policy"
    assert substack_row.request_budget_policy_summary == "No API request budget, manual copy-paste markdown only"
    assert substack_row.kill_switch_required is False
    assert substack_row.kill_switch_default_state == "manual_stop_policy"


def test_linkedin_meta_tiktok_rows_have_blockers_and_no_readiness():
    packet = contract.build_rate_budget_kill_switch_packet()
    for pid in ("linkedin", "threads", "instagram", "facebook_page", "tiktok"):
        row = next(r for r in packet.rows if r.platform_id == pid)
        assert row.gate_status == "needs_human_review"
        assert row.readiness_cleared is False


def test_youtube_row_has_supported_quota_no_stale_1600():
    packet = contract.build_rate_budget_kill_switch_packet()
    youtube_row = next(r for r in packet.rows if r.platform_id == "youtube")
    
    assert "100 calls per day" in youtube_row.daily_quota_summary
    assert "1 unit" in youtube_row.daily_quota_summary
    assert "1600" not in youtube_row.daily_quota_summary
    
    # Assert no stale youtube unit quota is referenced anywhere in packet or runbook
    runbook_content = contract.render_runbook(packet)
    assert "1600" not in runbook_content


def test_safety_invariants_and_all_live_counts_are_zero():
    packet = contract.build_rate_budget_kill_switch_packet()
    
    assert packet.live_read_allowed_count == 0
    assert packet.live_write_allowed_count == 0
    assert packet.env_read_count == 0
    assert packet.credential_hydrated_count == 0
    assert packet.platform_api_called_count == 0
    assert packet.readiness_cleared_count == 0
    assert packet.public_post_allowed_count == 0
    assert packet.retry_allowed_count == 0
    assert packet.auto_retry_allowed_count == 0
    
    for row in packet.rows:
        assert row.live_read_allowed is False
        assert row.live_write_allowed is False
        assert row.env_read is False
        assert row.credential_hydrated is False
        assert row.platform_api_called is False
        assert row.readiness_cleared is False
        assert row.public_post_allowed is False
        assert row.retry_allowed is False
        assert row.auto_retry_allowed is False


def test_kill_switch_required_for_all_non_manual_platforms():
    packet = contract.build_rate_budget_kill_switch_packet()
    for row in packet.rows:
        if row.platform_id == "substack_newsletter":
            assert row.kill_switch_required is False
        else:
            assert row.kill_switch_required is True


def test_u9_audit_entries_validate_cleanly():
    packet = contract.build_rate_budget_kill_switch_packet()
    assert len(packet.u9_audit_entry_ids) == 10
    assert all(f == "rate_budget_kill_switch_future" for f in packet.u9_audit_entry_families)
    
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
