from dataclasses import replace
from pathlib import Path

from live_contentops import dispatch_outbox_revalidation_gate_contract as ub
from live_contentops import manual_publish_record_metrics_ledger_contract as uc
from live_contentops import redacted_immutable_audit_ledger_v2_contract as u9


def _fixture():
    candidate, result = uc.build_revalidation_fixture()
    record = uc.build_manual_publish_record(
        revalidation_result=result,
        candidate=candidate,
        operator_identity_ref="operator:jim:redacted",
        manually_published_at_epoch=1300,
        manual_publish_url="https://example.com/post/abc?token=SECRET&x=1",
        manual_publish_mode=uc.MODE_OPERATOR_PLATFORM,
        evidence_refs=("test:evidence",),
    )
    metrics = uc.build_manual_metrics_record(
        publish_record=record,
        metrics={"impressions": 10, "views": 8, "likes": 1, "notes": "email me test@example.com token=SECRET"},
        metric_observed_at_epoch=1400,
        metric_recorded_at_epoch=1500,
        operator_identity_ref="operator:jim:redacted",
        metric_source_class=uc.METRIC_SOURCE_PLATFORM_UI,
        metric_notes="test@example.com token=SECRET",
    )
    return candidate, result, record, metrics


def test_manual_publish_record_builds_deterministically_from_0174ub_fixture():
    candidate, result = uc.build_revalidation_fixture()
    first = uc.build_manual_publish_record(
        revalidation_result=result,
        candidate=candidate,
        operator_identity_ref="operator:jim:redacted",
        manually_published_at_epoch=1300,
        manual_publish_url="https://example.com/post/abc?token=SECRET",
        manual_publish_mode=uc.MODE_OPERATOR_PLATFORM,
    )
    second = uc.build_manual_publish_record(
        revalidation_result=result,
        candidate=candidate,
        operator_identity_ref="operator:jim:redacted",
        manually_published_at_epoch=1300,
        manual_publish_url="https://example.com/post/abc?token=SECRET",
        manual_publish_mode=uc.MODE_OPERATOR_PLATFORM,
    )
    assert first == second
    assert first.source_revalidation_result_id == result.revalidation_result_id
    assert first.manual_publish_record_status == uc.STATUS_RECORDED_REVIEW_ONLY


def test_manual_publish_preserves_exact_payload_platform_payload_class_destination_credential():
    candidate, _, record, _ = _fixture()
    assert record.source_payload_hash == candidate.candidate_payload_hash
    assert record.platform_id == candidate.platform_id
    assert record.payload_class_id == candidate.payload_class_id
    assert record.destination_binding_id == candidate.destination_binding_id
    assert record.credential_handle_id == candidate.credential_handle_id


def test_manual_publish_url_redacted_and_url_hash_deterministic():
    _, _, record, _ = _fixture()
    assert "token=" not in record.manual_publish_url_redacted
    assert "SECRET" not in record.manual_publish_url_redacted
    assert record.manual_publish_url_hash == uc.hash_url("https://example.com/post/abc?token=SECRET&x=1")
    assert record.manual_publish_url_hash_algorithm == "sha256"


def test_missing_payload_hash_blocks():
    candidate, result = uc.build_revalidation_fixture()
    broken = replace(candidate, candidate_payload_hash="")
    record = uc.build_manual_publish_record(
        revalidation_result=result,
        candidate=broken,
        operator_identity_ref="operator:jim:redacted",
        manually_published_at_epoch=1300,
        manual_publish_url="https://example.com/post/abc",
        manual_publish_mode=uc.MODE_OPERATOR_PLATFORM,
    )
    assert uc.BLOCK_MISSING_PAYLOAD_HASH in record.blocked_reasons
    assert record.manual_publish_record_status == uc.STATUS_BLOCKED_MISSING_PAYLOAD_HASH


def test_missing_url_hash_blocks():
    candidate, result = uc.build_revalidation_fixture()
    record = uc.build_manual_publish_record(
        revalidation_result=result,
        candidate=candidate,
        operator_identity_ref="operator:jim:redacted",
        manually_published_at_epoch=1300,
        manual_publish_url="",
        manual_publish_mode=uc.MODE_OPERATOR_PLATFORM,
    )
    assert uc.BLOCK_MISSING_URL_HASH in record.blocked_reasons
    assert record.manual_publish_record_status == uc.STATUS_BLOCKED_MISSING_URL_HASH


def test_unknown_platform_and_payload_class_block_fail_closed():
    candidate, result = uc.build_revalidation_fixture()
    broken = replace(candidate, platform_id="unknown_platform", payload_class_id="unknown_class")
    record = uc.build_manual_publish_record(
        revalidation_result=result,
        candidate=broken,
        operator_identity_ref="operator:jim:redacted",
        manually_published_at_epoch=1300,
        manual_publish_url="https://example.com/post/abc",
        manual_publish_mode=uc.MODE_OPERATOR_PLATFORM,
    )
    assert uc.BLOCK_UNKNOWN_PLATFORM in record.blocked_reasons
    assert uc.BLOCK_UNKNOWN_PAYLOAD_CLASS in record.blocked_reasons
    assert record.manual_publish_record_status == uc.STATUS_BLOCKED_UNKNOWN_PLATFORM


def test_unknown_manual_publish_mode_blocks_fail_closed():
    candidate, result = uc.build_revalidation_fixture()
    record = uc.build_manual_publish_record(
        revalidation_result=result,
        candidate=candidate,
        operator_identity_ref="operator:jim:redacted",
        manually_published_at_epoch=1300,
        manual_publish_url="https://example.com/post/abc",
        manual_publish_mode="automated_publish",
    )
    assert record.manual_publish_mode == uc.MODE_UNKNOWN
    assert uc.BLOCK_UNKNOWN_PUBLISH_MODE in record.blocked_reasons
    assert record.manual_publish_record_status == uc.STATUS_BLOCKED_UNKNOWN_PUBLISH_MODE


def test_revalidation_future_send_gate_preserved_and_record_never_dispatches():
    _, result, record, _ = _fixture()
    assert result.revalidation_status == ub.STATUS_LOCAL_REVALIDATED_FUTURE_GATE
    assert ub.BLOCK_FUTURE_SEND_GATE_REQUIRED in record.blocked_reasons
    assert record.source_revalidation_future_gate_required is True
    assert record.can_dispatch is False
    assert record.dispatch_ready is False
    assert record.public_postable is False
    assert record.public_claim_authorized is False


def test_publish_validation_passes_only_as_operator_attested_review_record():
    _, result, record, _ = _fixture()
    validation = uc.validate_manual_publish_record(record, result)
    assert validation.validation_status == uc.STATUS_RECORDED_REVIEW_ONLY
    assert validation.no_api_verification_claim is True
    assert validation.no_public_claim_authorized is True
    assert validation.no_dispatch is True
    assert validation.no_live_behavior is True
    assert validation.revalidation_future_gate_preserved is True


def test_manual_metrics_builds_deterministically_and_binds_to_publish_record():
    _, _, record, _ = _fixture()
    first = uc.build_manual_metrics_record(
        publish_record=record,
        metrics={"impressions": 10, "views": 8},
        metric_observed_at_epoch=1400,
        metric_recorded_at_epoch=1500,
        operator_identity_ref="operator:jim:redacted",
        metric_source_class=uc.METRIC_SOURCE_PLATFORM_UI,
    )
    second = uc.build_manual_metrics_record(
        publish_record=record,
        metrics={"impressions": 10, "views": 8},
        metric_observed_at_epoch=1400,
        metric_recorded_at_epoch=1500,
        operator_identity_ref="operator:jim:redacted",
        metric_source_class=uc.METRIC_SOURCE_PLATFORM_UI,
    )
    assert first == second
    assert first.source_manual_publish_record_id == record.manual_publish_record_id
    assert first.source_payload_hash == record.source_payload_hash
    assert first.platform_id == record.platform_id


def test_metrics_payload_and_platform_mismatch_block():
    _, _, record, _ = _fixture()
    metrics = uc.build_manual_metrics_record(
        publish_record=record,
        source_payload_hash="different_hash",
        platform_id="different_platform",
        metrics={"impressions": 1},
        metric_observed_at_epoch=1400,
        metric_recorded_at_epoch=1500,
        operator_identity_ref="operator:jim:redacted",
    )
    assert uc.BLOCK_PAYLOAD_HASH_MISMATCH in metrics.blocked_reasons
    assert uc.BLOCK_PLATFORM_MISMATCH in metrics.blocked_reasons


def test_metrics_invalid_time_order_blocks():
    _, _, record, _ = _fixture()
    metrics = uc.build_manual_metrics_record(
        publish_record=record,
        metrics={"impressions": 1},
        metric_observed_at_epoch=1200,
        metric_recorded_at_epoch=1100,
        operator_identity_ref="operator:jim:redacted",
    )
    validation = uc.validate_manual_metrics_record(metrics, record)
    assert uc.BLOCK_METRIC_TIME_ORDER in metrics.blocked_reasons
    assert validation.metric_time_order_valid is False


def test_negative_metrics_block():
    _, _, record, _ = _fixture()
    metrics = uc.build_manual_metrics_record(
        publish_record=record,
        metrics={"impressions": -1},
        metric_observed_at_epoch=1400,
        metric_recorded_at_epoch=1500,
        operator_identity_ref="operator:jim:redacted",
    )
    assert uc.BLOCK_NEGATIVE_METRIC in metrics.blocked_reasons
    assert uc.validate_manual_metrics_record(metrics, record).non_negative_metrics is False


def test_future_api_import_mode_blocks_and_no_api_verification_claim_allowed():
    _, _, record, _ = _fixture()
    metrics = uc.build_manual_metrics_record(
        publish_record=record,
        metrics={"impressions": 1},
        metric_observed_at_epoch=1400,
        metric_recorded_at_epoch=1500,
        operator_identity_ref="operator:jim:redacted",
        metric_source_class=uc.METRIC_SOURCE_FUTURE_API_BLOCKED,
        metric_values_are_api_verified=True,
        metric_values_are_scraped=True,
    )
    validation = uc.validate_manual_metrics_record(metrics, record)
    assert uc.BLOCK_FUTURE_API_IMPORT in metrics.blocked_reasons
    assert validation.api_verified_false is False
    assert validation.scraped_false is False


def test_metric_notes_are_redacted():
    _, _, _, metrics = _fixture()
    assert "test@example.com" not in metrics.metric_notes_redacted
    assert "SECRET" not in metrics.metric_notes_redacted
    assert "[REDACTED_EMAIL]" in metrics.metric_notes_redacted


def test_metrics_validation_passes_operator_attested_only_no_live_behavior():
    _, _, record, metrics = _fixture()
    validation = uc.validate_manual_metrics_record(metrics, record)
    assert validation.validation_status == uc.STATUS_RECORDED_REVIEW_ONLY
    assert validation.payload_hash_match is True
    assert validation.platform_match is True
    assert validation.operator_attested_only is True
    assert validation.api_verified_false is True
    assert validation.scraped_false is True
    assert validation.no_live_behavior is True


def test_packet_contains_u9_redacted_entries_and_is_deterministic():
    first = uc.build_contract_packet()
    second = uc.build_contract_packet()
    assert first == second
    assert first.packet_hash == second.packet_hash
    assert first.all_records_redacted is True
    assert first.no_api_verification is True
    assert first.no_scraping is True
    assert first.no_dispatch is True
    assert first.no_public_claim_authorized is True
    families = [entry.entry_family for entry in first.audit_ledger_entries]
    assert families == ["manual_publish_record_future_gate", "metrics_record_future_gate"]
    assert first.audit_ledger_entries[0].previous_entry_hash == u9.GENESIS_HASH
    assert first.audit_ledger_entries[1].previous_entry_hash == first.audit_ledger_entries[0].entry_hash


def test_packet_contains_no_raw_secret_or_email_material():
    raw = uc._json(uc.build_contract_packet())
    assert "raw-secret" not in raw
    assert "operator@example.com" not in raw
    assert "token=raw-secret" not in raw
    assert "credential_hydrated\":false" in raw
    assert "network_performed\":false" in raw


def test_artifact_writer_locked_to_docs_automation_0174uc(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    result = uc.write_artifacts(repo_root=repo)
    packet_path = Path(result["packet_path"])
    runbook_path = Path(result["runbook_path"])
    assert packet_path.relative_to(repo) == uc.DOC_REL_DIR / uc.PACKET_FILENAME
    assert runbook_path.relative_to(repo) == uc.DOC_REL_DIR / uc.RUNBOOK_FILENAME
    try:
        uc.write_artifacts(repo_root=repo, output_dir=tmp_path / "other")
    except ValueError as exc:
        assert "artifact_writer_refuses_paths_outside_docs_automation_0174UC" in str(exc)
    else:
        raise AssertionError("writer accepted out-of-scope path")


def test_new_module_static_forbidden_behavior_scan():
    text = Path(uc.__file__).read_text(encoding="utf-8")
    forbidden = [
        "import requests", "from requests", "import urllib", "from urllib",
        "import socket", "from socket", "os.environ", "dotenv",
        "playwright", "selenium", "telegram.Bot", "send_message",
        "BeautifulSoup", "subprocess", "webbrowser", "schedule.every",
    ]
    for needle in forbidden:
        assert needle not in text
    assert "platform_api_called\": False" in text
    assert "env_read\": False" in text
    assert "ingestion_repo_mutated\": False" in text


def test_next_heavy_batch_exact():
    packet = uc.build_contract_packet()
    assert packet.next_required_gate == "TASK_CONTENTOPS_0174UD_CONTENT_PERFORMANCE_REVIEW_AND_EDITORIAL_FEEDBACK_LOOP_CONTRACT_V0"
