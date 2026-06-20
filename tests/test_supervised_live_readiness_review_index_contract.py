import pytest

from live_contentops import supervised_live_readiness_review_index_contract as contract
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit

def test_packet_builds_deterministically():
    packet1 = contract.build_supervised_live_readiness_review_packet()
    packet2 = contract.build_supervised_live_readiness_review_packet()
    assert packet1.packet_id == packet2.packet_id
    assert packet1.packet_hash == packet2.packet_hash
    assert len(packet1.readiness_rows) == 10


def test_required_platforms_represented():
    packet = contract.build_supervised_live_readiness_review_packet()
    platforms = {r.platform_id for r in packet.readiness_rows}
    expected = {
        "x", "telegram_remote_operator", "telegram_channel_destination",
        "substack_newsletter", "linkedin", "threads", "instagram",
        "facebook_page", "tiktok", "youtube"
    }
    assert platforms == expected


def test_global_readiness_semantics():
    packet = contract.build_supervised_live_readiness_review_packet()
    assert packet.global_readiness_status in ("not_ready", "review_only")
    assert packet.global_readiness_status != "ready"
    assert packet.all_platforms_blocked_or_manual_or_review is True

    for r in packet.readiness_rows:
        assert r.live_readiness_status in ("blocked", "manual_only", "needs_human_review", "symbolic_only")
        assert r.live_readiness_status != "ready"


def test_live_counters_remain_zero():
    packet = contract.build_supervised_live_readiness_review_packet()
    assert packet.live_read_allowed_count == 0
    assert packet.live_write_allowed_count == 0
    assert packet.env_read_allowed_count == 0
    assert packet.credential_hydrated_count == 0
    assert packet.platform_api_called_count == 0
    assert packet.public_post_allowed_count == 0
    assert packet.readiness_cleared_count == 0
    assert packet.scheduler_enabled_count == 0
    assert packet.browser_session_used_count == 0

    for r in packet.readiness_rows:
        assert r.live_read_allowed is False
        assert r.live_write_allowed is False
        assert r.env_read_allowed is False
        assert r.credential_hydrated is False
        assert r.platform_api_called is False
        assert r.public_post_allowed is False
        assert r.readiness_cleared is False
        assert r.scheduler_enabled is False
        assert r.browser_session_used is False


def test_platform_specific_blockers():
    packet = contract.build_supervised_live_readiness_review_packet()

    # X
    x_row = next(r for r in packet.readiness_rows if r.platform_id == "x")
    assert "rate_limit_and_spend_gate_unresolved" in x_row.blocked_reasons
    assert "x_api_gate_closed" in x_row.blocked_reasons

    # Telegram operator and channel destinations are distinct
    op_row = next(r for r in packet.readiness_rows if r.platform_id == "telegram_remote_operator")
    ch_row = next(r for r in packet.readiness_rows if r.platform_id == "telegram_channel_destination")
    assert op_row.row_id != ch_row.row_id
    assert "no_arbitrary_dm_allowed" in op_row.blocked_reasons
    assert "operator_inbox_chat_proof_required" in op_row.missing_proofs
    assert "channel_permission_proof_required" in ch_row.missing_proofs
    assert "bot_admin_gate_closed" in ch_row.blocked_reasons

    # Substack manual
    sub_row = next(r for r in packet.readiness_rows if r.platform_id == "substack_newsletter")
    assert sub_row.live_readiness_status == "manual_only"
    assert sub_row.live_readiness_strength == "manual_policy_only"
    assert "manual_export_first_no_api" in sub_row.missing_proofs

    # LinkedIn
    li_row = next(r for r in packet.readiness_rows if r.platform_id == "linkedin")
    assert "linkedin_organization_page_binding_missing" in li_row.missing_proofs

    # Threads / Instagram / Facebook Page
    for pid in ("threads", "instagram", "facebook_page"):
        meta_row = next(r for r in packet.readiness_rows if r.platform_id == pid)
        assert "meta_app_review_closed" in meta_row.blocked_reasons
        assert "meta_app_account_proof_required" in meta_row.missing_proofs

    # TikTok
    tiktok_row = next(r for r in packet.readiness_rows if r.platform_id == "tiktok")
    assert "tiktok_audit_closed" in tiktok_row.missing_proofs

    # YouTube
    yt_row = next(r for r in packet.readiness_rows if r.platform_id == "youtube")
    assert "quota_upload_gate_closed" in yt_row.missing_proofs
    assert "1600" not in contract.render_runbook(packet)


def test_u9_audit_entries_validate():
    packet = contract.build_supervised_live_readiness_review_packet()
    assert len(packet.u9_audit_entry_ids) == 10
    assert all(f == "supervised_live_readiness_review_future" for f in packet.u9_audit_entry_families)

    entries = contract.build_u9_audit_entries(packet.readiness_rows)
    chain = audit.build_ledger_chain(entries)
    validation = audit.validate_ledger_chain(chain)

    assert validation.validation_status == "pass"
    assert len(validation.blocked_reasons) == 0


def test_artifact_writer_enforces_directory_restriction(tmp_path):
    with pytest.raises(ValueError):
        contract.write_artifacts(repo_root=tmp_path, output_dir=tmp_path / "invalid_dir")


def test_invalid_platform_evidence_row_fails_closed():
    with pytest.raises(ValueError):
        contract.PlatformReadinessEvidenceRow(
            row_id="row_invalid",
            platform_id="invalid_platform_id",
            platform_role="role",
            account_binding_row_refs=(),
            credential_boundary_refs=(),
            official_docs_refs=(),
            permission_gate_refs=(),
            rate_budget_gate_refs=(),
            preflight_decision_refs=(),
            account_binding_status="status",
            credential_boundary_status="status",
            official_docs_status="status",
            permission_gate_status="status",
            app_review_status="status",
            rate_budget_status="status",
            kill_switch_status="status",
            preflight_status="status",
            manual_export_status="status",
            live_readiness_status="blocked",
            live_readiness_strength="strength",
            missing_proofs=(),
            blocked_reasons=(),
            next_required_evidence="evidence",
            live_read_allowed=False,
            live_write_allowed=False,
            env_read_allowed=False,
            credential_hydrated=False,
            platform_api_called=False,
            public_post_allowed=False,
            readiness_cleared=False,
            scheduler_enabled=False,
            browser_session_used=False,
            row_hash="hash",
            row_hash_algorithm="sha256",
        )
