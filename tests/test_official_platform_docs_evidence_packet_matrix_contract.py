from pathlib import Path
import pytest

from live_contentops import official_platform_docs_evidence_packet_matrix_contract as contract
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit

EXPECTED_PLATFORMS = {
    "x",
    "telegram_remote_operator",
    "telegram_channel_destination",
    "substack_newsletter",
    "linkedin",
    "threads",
    "instagram",
    "facebook_page",
    "tiktok",
    "youtube",
}


def test_packet_builds_deterministically_from_static_refs():
    packet1 = contract.build_official_platform_docs_evidence_matrix_packet()
    packet2 = contract.build_official_platform_docs_evidence_matrix_packet()

    assert packet1.packet_hash == packet2.packet_hash
    assert packet1.packet_id == packet2.packet_id
    assert len(packet1.docs_rows) == 10
    assert set(packet1.rows_by_platform) == EXPECTED_PLATFORMS


def test_all_10_platforms_exist_in_matrix():
    packet = contract.build_official_platform_docs_evidence_matrix_packet()
    platform_ids = {row.platform_id for row in packet.docs_rows}
    assert platform_ids == EXPECTED_PLATFORMS
    assert len(packet.docs_rows) == 10


def test_every_official_doc_url_is_from_allowed_domain():
    refs = contract.build_default_evidence_refs()
    for ref in refs:
        assert ref.official_domain in contract.ALLOWED_DOMAINS
        from urllib.parse import urlparse
        parsed = urlparse(ref.official_doc_url)
        assert parsed.netloc.split(":")[0] == ref.official_domain

        parsed_final = urlparse(ref.final_doc_url)
        assert parsed_final.netloc.split(":")[0] in contract.ALLOWED_DOMAINS


def test_substack_is_manual_export_no_api_and_has_weak_strength():
    packet = contract.build_official_platform_docs_evidence_matrix_packet()
    substack_row = next(r for r in packet.docs_rows if r.platform_id == "substack_newsletter")
    
    assert substack_row.docs_status == "manual_export_no_api"
    assert substack_row.docs_evidence_strength == "weak"  # Downgraded proof
    assert substack_row.row_claim_support_status == "not_verified_current_docs"
    assert "no_substack_public_publish_api_gate" in substack_row.blocked_reasons
    assert "session_automation_blocked" in substack_row.blocked_reasons
    assert substack_row.credential_required_future is False
    assert "substack_newsletter" in packet.manual_export_no_api_platforms


def test_all_live_read_write_api_env_credential_counts_are_zero():
    packet = contract.build_official_platform_docs_evidence_matrix_packet()

    assert packet.live_read_allowed_count == 0
    assert packet.live_write_allowed_count == 0
    assert packet.platform_api_called_count == 0
    assert packet.env_read_count == 0
    assert packet.credential_hydrated_count == 0

    for row in packet.docs_rows:
        assert row.live_read_allowed is False
        assert row.live_write_allowed is False
        assert row.platform_api_called is False
        assert row.credential_hydrated is False
        assert row.env_read is False
        assert row.safety_flags["live_read_allowed"] is False
        assert row.safety_flags["live_write_allowed"] is False
        assert row.safety_flags["platform_api_called"] is False
        assert row.safety_flags["env_read"] is False
        assert row.safety_flags["credential_hydrated"] is False


def test_docs_coverage_does_not_clear_readiness():
    packet = contract.build_official_platform_docs_evidence_matrix_packet()
    
    # Verify that every platform remains blocked
    for row in packet.docs_rows:
        assert len(row.blocked_reasons) > 0
        assert row.safety_flags["dispatch_ready"] is False
        assert row.safety_flags["public_postable"] is False


def test_each_row_has_evidence_refs_and_caveats():
    packet = contract.build_official_platform_docs_evidence_matrix_packet()
    
    for row in packet.docs_rows:
        assert len(row.doc_refs) > 0
        assert len(row.evidence_refs) > 0
        assert row.rate_quota_spend_summary != ""
        assert row.auth_model_summary != ""


def test_x_has_rate_spend_access_caveat_and_no_stale_exact_numeric_claim():
    packet = contract.build_official_platform_docs_evidence_matrix_packet()
    x_row = next(r for r in packet.docs_rows if r.platform_id == "x")
    
    # Stale claim "17 tweets per 24h" and Free/Basic/Pro tier wording removed
    assert "17 tweets" not in x_row.rate_quota_spend_summary
    assert "Free tier is write-only" not in x_row.rate_quota_spend_summary
    assert "Basic" not in x_row.rate_quota_spend_summary
    assert "Pro" not in x_row.rate_quota_spend_summary
    assert "pay-per-use" in x_row.rate_quota_spend_summary.lower()
    assert "endpoint-specific" in x_row.rate_quota_spend_summary.lower()
    assert x_row.docs_status == "partial_docs_grounded"
    assert x_row.exact_numeric_claims_present is False


def test_telegram_operator_and_channel_are_distinct_and_sendMessage_character_limit_is_verified():
    packet = contract.build_official_platform_docs_evidence_matrix_packet()
    op_row = next(r for r in packet.docs_rows if r.platform_id == "telegram_remote_operator")
    ch_row = next(r for r in packet.docs_rows if r.platform_id == "telegram_channel_destination")
    
    assert op_row.row_id != ch_row.row_id
    assert op_row.platform_role != ch_row.platform_role

    # Telegram Channel Destination has verified 4096 character numeric limit
    assert ch_row.exact_numeric_claims_present is True
    assert len(ch_row.unsupported_claims) == 0
    assert ch_row.docs_evidence_strength == "strong"
    assert ch_row.docs_status == "docs_grounded"

    # Operator inbox limits are not documented in Bot API main page, so rate limit limits is removed/downgraded
    assert "30 msg/sec" not in op_row.rate_quota_spend_summary


def test_linkedin_member_org_caveats_exist():
    packet = contract.build_official_platform_docs_evidence_matrix_packet()
    linkedin_row = next(r for r in packet.docs_rows if r.platform_id == "linkedin")
    
    assert "member profile" in linkedin_row.app_review_access_summary.lower()
    assert "organization page" in linkedin_row.app_review_access_summary.lower()


def test_meta_threads_instagram_facebook_rows_are_separate():
    packet = contract.build_official_platform_docs_evidence_matrix_packet()
    threads_row = next(r for r in packet.docs_rows if r.platform_id == "threads")
    insta_row = next(r for r in packet.docs_rows if r.platform_id == "instagram")
    fb_row = next(r for r in packet.docs_rows if r.platform_id == "facebook_page")
    
    assert threads_row.row_id != insta_row.row_id
    assert insta_row.row_id != fb_row.row_id
    
    assert "threads_content_publish" in threads_row.permission_scope_summary
    assert "instagram_content_publish" in insta_row.permission_scope_summary
    assert "pages_manage_posts" in fb_row.permission_scope_summary


def test_tiktok_and_youtube_video_upload_quota_caveats_exist():
    packet = contract.build_official_platform_docs_evidence_matrix_packet()
    tiktok_row = next(r for r in packet.docs_rows if r.platform_id == "tiktok")
    yt_row = next(r for r in packet.docs_rows if r.platform_id == "youtube")
    
    assert "video" in tiktok_row.media_constraint_summary or "MP4" in tiktok_row.media_constraint_summary

    # YouTube quota claims repaired
    assert "1600" not in yt_row.rate_quota_spend_summary
    assert "100 calls per day" in yt_row.rate_quota_spend_summary
    assert "1 unit" in yt_row.rate_quota_spend_summary
    assert yt_row.exact_numeric_claims_present is True
    assert yt_row.docs_evidence_strength == "strong"


def test_unofficial_domain_input_fails_closed():
    with pytest.raises(ValueError, match="unofficial_domain_not_allowed"):
        contract.OfficialDocsEvidenceRef(
            evidence_ref_id="doc_evidence_ref_illegal",
            platform_id="x",
            official_doc_title="Unverified Documentation",
            official_doc_url="https://unofficialblog.com/x-api-leak",
            official_domain="unofficialblog.com",
            doc_accessed_at_epoch=1781913600,
            doc_relevance=contract.DocRelevance(auth_model=True),
            cited_claim_summary="None",
            caveats="None",
            evidence_status="official_doc_cited",
            evidence_hash="dummy",
            evidence_hash_algorithm="sha256",
            final_doc_url="https://unofficialblog.com/x-api-leak",
            official_url_opened=True,
            source_support_level="direct_official_page",
            claim_support_status="supported_by_cited_doc",
            exact_numeric_claim=False,
            exact_numeric_claim_has_direct_doc_proof=False,
            claim_review_notes="Notes",
            doc_readback_basis={
                "official_doc_url": "https://unofficialblog.com/x-api-leak",
                "final_doc_url": "https://unofficialblog.com/x-api-leak",
                "official_doc_title": "Unverified Documentation",
                "current_claim_basis_summary": "None",
            }
        )

    # Domain mismatch should also fail closed
    with pytest.raises(ValueError, match="domain_mismatch"):
        contract.OfficialDocsEvidenceRef(
            evidence_ref_id="doc_evidence_ref_mismatch",
            platform_id="x",
            official_doc_title="Mismatched Domain",
            official_doc_url="https://developer.x.com/en/docs",
            official_domain="docs.x.com",
            doc_accessed_at_epoch=1781913600,
            doc_relevance=contract.DocRelevance(auth_model=True),
            cited_claim_summary="None",
            caveats="None",
            evidence_status="official_doc_cited",
            evidence_hash="dummy",
            evidence_hash_algorithm="sha256",
            final_doc_url="https://developer.x.com/en/docs",
            official_url_opened=True,
            source_support_level="direct_official_page",
            claim_support_status="supported_by_cited_doc",
            exact_numeric_claim=False,
            exact_numeric_claim_has_direct_doc_proof=False,
            claim_review_notes="Notes",
            doc_readback_basis={
                "official_doc_url": "https://developer.x.com/en/docs",
                "final_doc_url": "https://developer.x.com/en/docs",
                "official_doc_title": "Mismatched Domain",
                "current_claim_basis_summary": "None",
            }
        )


def test_missing_official_docs_fails_closed_or_needs_review():
    empty_refs = ()
    rows = contract.build_default_docs_rows(empty_refs)
    
    x_row = next(r for r in rows if r.platform_id == "x")
    assert x_row.docs_status == "blocked_missing_official_docs"
    assert x_row.docs_evidence_strength == "blocked"
    assert "missing_official_docs" in x_row.blocked_reasons


def test_u9_audit_entries_use_platform_docs_evidence_future_and_are_redacted():
    packet = contract.build_official_platform_docs_evidence_matrix_packet()
    entries = contract.build_u9_audit_entries(packet)
    
    assert len(entries) == 10
    assert all(e.entry_family == "platform_docs_evidence_future" for e in entries)
    
    chain = audit.build_ledger_chain(entries)
    validation = audit.validate_ledger_chain(chain)
    assert validation.validation_status == "pass"
    
    # Ensure they contain no secrets
    assert not audit.scan_for_forbidden_material([e.redacted_summary for e in entries])


def test_artifact_writer_touches_only_docs_automation_0174ui(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    with pytest.raises(ValueError, match="artifact_writer_refuses_paths_outside_docs_automation_0174UI"):
        contract.write_artifacts(repo_root=repo_root, output_dir=tmp_path)


def test_exact_numeric_claims_require_direct_doc_proof():
    # Construct a reference with exact_numeric_claim=True but direct proof=False
    refs = [
        contract.OfficialDocsEvidenceRef(
            evidence_ref_id="doc_evidence_ref_numeric_test",
            platform_id="x",
            official_doc_title="X Numeric Test",
            official_doc_url="https://docs.x.com/overview",
            official_domain="docs.x.com",
            doc_accessed_at_epoch=1781913600,
            doc_relevance=contract.DocRelevance(auth_model=True),
            cited_claim_summary="100 tweets per day",
            caveats="None",
            evidence_status="official_doc_cited",
            evidence_hash="dummy",
            evidence_hash_algorithm="sha256",
            final_doc_url="https://docs.x.com/overview",
            official_url_opened=True,
            source_support_level="direct_official_page",
            claim_support_status="supported_by_cited_doc",
            exact_numeric_claim=True,
            exact_numeric_claim_has_direct_doc_proof=False,  # missing direct proof
            claim_review_notes="Notes",
            doc_readback_basis={
                "official_doc_url": "https://docs.x.com/overview",
                "final_doc_url": "https://docs.x.com/overview",
                "official_doc_title": "X Numeric Test",
                "current_claim_basis_summary": "100 tweets per day",
            }
        )
    ]
    rows = contract.build_default_docs_rows(tuple(refs))
    x_row = next(r for r in rows if r.platform_id == "x")

    assert x_row.exact_numeric_claims_present is True
    assert "stale_numeric_claim:doc_evidence_ref_numeric_test" in x_row.unsupported_claims
    assert x_row.row_claim_support_status == "unsupported_by_cited_doc"
    assert x_row.docs_evidence_strength == "weak"  # Degraded due to missing direct proof of numeric claim
    assert x_row.docs_status in {"needs_human_review", "partial_docs_grounded"}


def test_unsupported_claims_degrade_row_to_not_grounded():
    # Construct a reference with claim_support_status="unsupported_by_cited_doc"
    refs = [
        contract.OfficialDocsEvidenceRef(
            evidence_ref_id="doc_evidence_ref_unsupported_test",
            platform_id="telegram_channel_destination",
            official_doc_title="TG Unsupported Test",
            official_doc_url="https://core.telegram.org/bots/api",
            official_domain="core.telegram.org",
            doc_accessed_at_epoch=1781913600,
            doc_relevance=contract.DocRelevance(auth_model=True),
            cited_claim_summary="Unsupported claim summary",
            caveats="None",
            evidence_status="official_doc_cited",
            evidence_hash="dummy",
            evidence_hash_algorithm="sha256",
            final_doc_url="https://core.telegram.org/bots/api",
            official_url_opened=True,
            source_support_level="direct_official_page",
            claim_support_status="unsupported_by_cited_doc",  # unsupported status
            exact_numeric_claim=False,
            exact_numeric_claim_has_direct_doc_proof=False,
            claim_review_notes="Notes",
            doc_readback_basis={
                "official_doc_url": "https://core.telegram.org/bots/api",
                "final_doc_url": "https://core.telegram.org/bots/api",
                "official_doc_title": "TG Unsupported Test",
                "current_claim_basis_summary": "Unsupported claim summary",
            }
        )
    ]
    rows = contract.build_default_docs_rows(tuple(refs))
    tg_row = next(r for r in rows if r.platform_id == "telegram_channel_destination")

    assert tg_row.row_claim_support_status == "unsupported_by_cited_doc"
    assert tg_row.docs_evidence_strength == "weak"
    assert tg_row.docs_status != "docs_grounded"  # Degraded


def test_substack_generic_help_center_support_cannot_be_strong():
    packet = contract.build_official_platform_docs_evidence_matrix_packet()
    substack_row = next(r for r in packet.docs_rows if r.platform_id == "substack_newsletter")
    
    assert substack_row.docs_evidence_strength == "weak"
    assert substack_row.docs_status != "docs_grounded"


def test_doc_readback_basis_exists_and_validated_for_every_ref():
    refs = contract.build_default_evidence_refs()
    for ref in refs:
        assert isinstance(ref.doc_readback_basis, dict)
        assert set(ref.doc_readback_basis.keys()) == {
            "official_doc_url",
            "final_doc_url",
            "official_doc_title",
            "current_claim_basis_summary",
        }
        # Verify that validation fails when missing fields or malformed type
        with pytest.raises(ValueError):
            contract.OfficialDocsEvidenceRef(
                evidence_ref_id="doc_evidence_ref_invalid_readback",
                platform_id="x",
                official_doc_title="X Invalid Readback",
                official_doc_url="https://docs.x.com/overview",
                official_domain="docs.x.com",
                doc_accessed_at_epoch=1781913600,
                doc_relevance=contract.DocRelevance(auth_model=True),
                cited_claim_summary="None",
                caveats="None",
                evidence_status="official_doc_cited",
                evidence_hash="dummy",
                evidence_hash_algorithm="sha256",
                final_doc_url="https://docs.x.com/overview",
                official_url_opened=True,
                source_support_level="direct_official_page",
                claim_support_status="supported_by_cited_doc",
                exact_numeric_claim=False,
                exact_numeric_claim_has_direct_doc_proof=False,
                claim_review_notes="Notes",
                doc_readback_basis={
                    "official_doc_url": "https://docs.x.com/overview",
                    # missing keys
                }
            )
