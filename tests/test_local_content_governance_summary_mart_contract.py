from dataclasses import replace
from live_contentops import local_content_governance_summary_mart_contract as mart
from live_contentops import manual_publish_record_metrics_ledger_contract as uc
from live_contentops import content_performance_review_editorial_feedback_contract as ud


def test_mart_builds_deterministically():
    first = mart.build_mart()
    second = mart.build_mart()
    assert first.packet_hash == second.packet_hash
    assert first.packet_hash_algorithm == mart.HASH_ALGORITHM
    assert first.overall_status == mart.STATUS_LOCAL_SUMMARY_READY
    assert first.mart_status == mart.STATUS_LOCAL_SUMMARY_READY
    assert first.next_required_gate == mart.NEXT_HEAVY_BATCH


def test_all_10_platform_rows_exist():
    packet = mart.build_mart()
    platforms = [ps.platform_id for ps in packet.platform_summaries]
    expected_platforms = [
        "x", "telegram_remote_operator", "telegram_channel_destination",
        "substack_newsletter", "linkedin", "threads", "instagram",
        "facebook_page", "tiktok", "youtube"
    ]
    assert sorted(platforms) == sorted(expected_platforms)
    # verify even count=0 rows are present
    youtube_summary = next(ps for ps in packet.platform_summaries if ps.platform_id == "youtube")
    assert youtube_summary.summary_row_count == 0


def test_evidence_rows_cover_all_10_families():
    packet = mart.build_mart()
    families = [es.evidence_family for es in packet.evidence_summaries]
    expected_families = [
        "idea_intent", "editorial_writer", "dry_run_preview", "ingestion_context",
        "artifact_eligibility", "redacted_audit_ledger", "approval_validity",
        "dispatch_revalidation", "manual_publish_metrics", "performance_feedback"
    ]
    assert sorted(families) == sorted(expected_families)


def test_pipeline_row_summarizes_all_13_states():
    packet = mart.build_mart()
    assert len(packet.summary_rows) > 0
    row = packet.summary_rows[0]
    assert row.idea_state == "source_needed"
    assert row.brief_state == "review_only"
    assert row.writer_state == "deterministic_fixture"
    assert row.preview_state == "platform_payload_preview"
    assert row.substack_export_state == "substack_manual_export"
    assert row.dry_run_state == "review_only_dry_run_valid"
    assert row.artifact_eligibility_state == "source_provided_context_only"
    assert row.approval_state == "dispatch_revalidation_required_future_0174UB"
    assert row.revalidation_state == "locally_revalidated_but_dispatch_future_gate"
    assert row.manual_publish_state == "recorded_review_only"
    assert row.metrics_state == "platform_ui_manual_read"
    assert row.performance_review_state == "operator_attested_only"
    assert row.editorial_feedback_state == "review_only_feedback_recorded"


def test_all_counts_are_zero():
    packet = mart.build_mart()
    assert packet.public_postable_count == 0
    assert packet.dispatch_ready_count == 0
    assert packet.approval_ready_count == 0
    assert packet.current_truth_promoted_count == 0
    assert packet.dqr_cleared_count == 0
    assert packet.readiness_cleared_count == 0


def test_forged_public_postable_blocks():
    uc_packet = uc.build_contract_packet()
    pub = uc_packet.manual_publish_records[0]
    pub_forged = replace(pub, public_postable=True)
    uc_forged_packet = replace(uc_packet, manual_publish_records=(pub_forged,))
    packet = mart.build_mart(uc_packet=uc_forged_packet)
    assert packet.mart_status == mart.STATUS_BLOCKED
    assert "forged_public_postable_blocked" in packet.hard_blockers


def test_forged_dispatch_ready_or_can_dispatch_blocks():
    uc_packet = uc.build_contract_packet()
    pub = uc_packet.manual_publish_records[0]
    pub_forged = replace(pub, dispatch_ready=True)
    uc_forged_packet = replace(uc_packet, manual_publish_records=(pub_forged,))
    packet = mart.build_mart(uc_packet=uc_forged_packet)
    assert packet.mart_status == mart.STATUS_BLOCKED
    assert "forged_dispatch_ready_blocked" in packet.hard_blockers

    pub_forged_2 = replace(pub, can_dispatch=True)
    uc_forged_packet_2 = replace(uc_packet, manual_publish_records=(pub_forged_2,))
    packet_2 = mart.build_mart(uc_packet=uc_forged_packet_2)
    assert packet_2.mart_status == mart.STATUS_BLOCKED
    assert "forged_can_dispatch_blocked" in packet_2.hard_blockers


def test_forged_can_approve_blocks():
    ud_packet = ud.build_contract_packet()
    rev = ud_packet.performance_reviews[0]
    rev_forged = replace(rev, can_create_approval=True)
    ud_forged_packet = replace(ud_packet, performance_reviews=(rev_forged,))
    packet = mart.build_mart(ud_packet=ud_forged_packet)
    assert packet.mart_status == mart.STATUS_BLOCKED
    assert "forged_can_approve_blocked" in packet.hard_blockers


def test_forged_current_truth_promoted_blocks():
    uc_packet = uc.build_contract_packet()
    pub = uc_packet.manual_publish_records[0]
    sf = pub.safety_flags
    pub_forged = replace(pub, safety_flags={**sf, "current_truth_promoted": True})
    uc_forged_packet = replace(uc_packet, manual_publish_records=(pub_forged,))
    packet = mart.build_mart(uc_packet=uc_forged_packet)
    assert packet.mart_status == mart.STATUS_BLOCKED
    assert "forged_current_truth_promoted_blocked" in packet.hard_blockers


def test_forged_dqr_cleared_or_readiness_cleared_blocks():
    uc_packet = uc.build_contract_packet()
    pub = uc_packet.manual_publish_records[0]
    sf = pub.safety_flags
    pub_forged = replace(pub, safety_flags={**sf, "dqr_cleared": True})
    uc_forged_packet = replace(uc_packet, manual_publish_records=(pub_forged,))
    packet = mart.build_mart(uc_packet=uc_forged_packet)
    assert packet.mart_status == mart.STATUS_BLOCKED
    assert "forged_dqr_cleared_blocked" in packet.hard_blockers

    pub_forged_2 = replace(pub, safety_flags={**sf, "readiness_cleared": True})
    uc_forged_packet_2 = replace(uc_packet, manual_publish_records=(pub_forged_2,))
    packet_2 = mart.build_mart(uc_packet=uc_forged_packet_2)
    assert packet_2.mart_status == mart.STATUS_BLOCKED
    assert "forged_readiness_cleared_blocked" in packet_2.hard_blockers


def test_ud_u9_explicit_families_remove_default_soft_caveat():
    ud_packet = ud.build_contract_packet()
    families = [entry.entry_family for entry in ud_packet.audit_ledger_entries]
    assert families == ["content_performance_review", "editorial_feedback_signal", "editorial_feedback_loop"]
    assert "unknown_or_blocked" not in families

    packet = mart.build_mart(ud_packet=ud_packet)
    assert mart.SOFT_CAVEAT_0174UD_U9_UNKNOWN not in packet.soft_caveats
    assert packet.evidence_summary.u9_unknown_or_blocked_entry_count == 0
    performance_summary = next(es for es in packet.evidence_summaries if es.evidence_family == "performance_feedback")
    assert performance_summary.audit_ledger_entry_count == 3
    assert performance_summary.u9_unknown_or_blocked_entry_count == 0
    assert performance_summary.u9_unknown_or_blocked_soft_caveat is False
    assert packet.mart_status == mart.STATUS_LOCAL_SUMMARY_READY


def test_historical_ud_unknown_or_blocked_remains_soft_caveat_compatible():
    ud_packet = ud.build_contract_packet()
    legacy = replace(
        ud_packet.audit_ledger_entries[0],
        entry_family="unknown_or_blocked",
        blocked_reasons=("legacy_unknown_or_blocked_fail_closed",),
    )
    legacy_packet = replace(ud_packet, audit_ledger_entries=(legacy,))
    packet = mart.build_mart(ud_packet=legacy_packet)
    performance_summary = next(es for es in packet.evidence_summaries if es.evidence_family == "performance_feedback")
    assert mart.SOFT_CAVEAT_0174UD_U9_UNKNOWN in packet.soft_caveats
    assert packet.evidence_summary.u9_unknown_or_blocked_entry_count == 1
    assert performance_summary.audit_ledger_entry_count == 1
    assert performance_summary.u9_unknown_or_blocked_entry_count == 1
    assert performance_summary.u9_unknown_or_blocked_soft_caveat is True


def test_artifact_writer_refuses_outside_paths(tmp_path):
    outside = tmp_path / "outside"
    try:
        mart.write_artifacts(repo_root=tmp_path, output_dir=outside)
    except ValueError as exc:
        assert "artifact_writer_refuses_paths_outside_docs_automation_0174UE" in str(exc)
    else:
        raise AssertionError("artifact writer accepted outside path")


def test_no_live_behavior_exists():
    packet = mart.build_mart()
    for flag in (
        "live_dispatch_enabled", "platform_api_called", "telegram_api_called",
        "provider_api_called", "llm_provider_called", "credential_hydrated",
        "env_read", "network_performed", "scheduler_enabled",
        "autonomous_posting_allowed", "scraping_performed",
        "dm_or_reply_automation_allowed", "browser_session_used",
        "current_truth_promoted", "dqr_cleared", "readiness_cleared",
        "ingestion_repo_mutated"
    ):
        assert packet.safety_flags.get(flag) is False


def test_no_ingestion_repo_mutation_occurs():
    packet = mart.build_mart()
    assert packet.safety_flags.get("ingestion_repo_mutated") is False
