from live_contentops import local_content_governance_summary_mart_contract as mart


def test_build_mart_is_deterministic_and_review_only():
    first = mart.build_mart()
    second = mart.build_mart()

    assert first.packet_hash == second.packet_hash
    assert first.packet_hash_algorithm == mart.HASH_ALGORITHM
    assert first.mart_status == mart.STATUS_LOCAL_SUMMARY_READY
    assert first.all_rows_review_only is True
    assert first.public_postable_count == 0
    assert first.dispatch_ready_count == 0
    assert first.no_api_verification is True
    assert first.no_scraping is True
    assert first.no_auto_generation is True
    assert first.no_auto_publish is True
    assert first.no_dispatch is True
    assert first.no_public_claim_authorized is True
    assert first.next_required_gate == mart.NEXT_HEAVY_BATCH


def test_summary_row_preserves_governance_safety_flags():
    packet = mart.build_mart()
    assert len(packet.summary_rows) == 1
    row = packet.summary_rows[0]

    assert row.governance_status == mart.STATUS_LOCAL_SUMMARY_READY
    assert row.public_postable is False
    assert row.can_dispatch is False
    assert row.can_auto_generate_content is False
    assert row.can_approve is False
    assert row.can_publish_public_claim is False
    assert row.human_review_required is True
    assert row.blocked_reasons == ()
    assert row.safety_flags["local_summary_mart_only"] is True
    assert row.safety_flags["review_only"] is True
    for blocked_flag in (
        "platform_api_called",
        "telegram_api_called",
        "provider_api_called",
        "llm_provider_called",
        "credential_hydrated",
        "env_read",
        "network_performed",
        "scheduler_enabled",
        "scraping_performed",
        "browser_session_used",
        "dm_or_reply_automation_allowed",
        "ingestion_repo_mutated",
        "ui_generated",
    ):
        assert row.safety_flags[blocked_flag] is False


def test_platform_and_evidence_summaries_include_soft_caveat_not_blocker():
    packet = mart.build_mart()

    assert packet.blocked_reasons == ()
    assert packet.soft_caveats == (
        mart.SOFT_CAVEAT_0174UD_U9_UNKNOWN,
        mart.SOFT_CAVEAT_UPSTREAM_FUTURE_SEND,
    )
    assert packet.evidence_summary.u9_unknown_or_blocked_entry_count == 2
    assert packet.evidence_summary.u9_unknown_or_blocked_soft_caveat is True
    assert packet.evidence_summary.all_records_redacted is True
    assert packet.evidence_summary.audit_ledger_entry_count == 4
    assert packet.blocker_summaries == ()

    assert len(packet.platform_summaries) == 1
    platform = packet.platform_summaries[0]
    assert platform.summary_row_count == 1
    assert platform.manual_publish_record_count == 1
    assert platform.manual_metrics_record_count == 1
    assert platform.performance_review_count == 1
    assert platform.public_postable_count == 0
    assert platform.dispatch_ready_count == 0
    assert platform.review_only_count == 1
    assert platform.blocked_count == 0
    assert platform.soft_caveats == packet.soft_caveats


def test_render_runbook_and_artifact_writer_are_bounded(tmp_path):
    packet = mart.build_mart()
    runbook = mart.render_runbook(packet)

    assert mart.TASK_LABEL in runbook
    assert packet.packet_hash in runbook
    assert "unknown_or_blocked" in runbook

    outside = tmp_path / "outside"
    try:
        mart.write_artifacts(repo_root=tmp_path, output_dir=outside)
    except ValueError as exc:
        assert "artifact_writer_refuses_paths_outside_docs_automation_0174UE" in str(exc)
    else:
        raise AssertionError("writer accepted output outside docs/automation/0174UE")
