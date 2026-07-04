"""Tests for X CDP exact live-click registry reconciliation."""
from __future__ import annotations

import json

from live_contentops.x_cdp_exact_live_click_execution_v6 import build_fixture_evidence_bundle as execution_bundle
from live_contentops.x_cdp_exact_live_click_registry_reconciliation_v6 import (
    APPENDED_STATUS,
    BLOCKED_STATUS,
    RECONCILED_EXISTING_STATUS,
    build_fixture_evidence_bundle,
    build_registry_row,
    main,
    reconcile_registry,
)


def _ready_execution():
    return execution_bundle()["cases"]["operator_confirmed_click_with_captured_public_url"]


def test_ready_execution_appends_one_registry_row(tmp_path):
    path = tmp_path / "registry.jsonl"
    packet = reconcile_registry(_ready_execution(), registry_path=path, append_registry=True)
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert packet["reconciliation_status"] == APPENDED_STATUS
    assert packet["registry_rows_written"] == 1
    assert len(rows) == 1
    assert rows[0]["public_url"] == "https://x.com/capitalchronicle/status/1234567890123456789"
    assert rows[0]["payload_hash"] == packet["payload_hash"]
    assert rows[0]["cookie_read_performed"] is False
    assert packet["public_url_verified_externally"] is False


def test_second_run_reconciles_existing_without_duplicate(tmp_path):
    path = tmp_path / "registry.jsonl"
    first = reconcile_registry(_ready_execution(), registry_path=path, append_registry=True)
    second = reconcile_registry(_ready_execution(), registry_path=path, append_registry=True)
    assert first["reconciliation_status"] == APPENDED_STATUS
    assert second["reconciliation_status"] == RECONCILED_EXISTING_STATUS
    assert second["idempotent_existing_match"] is True
    assert len(path.read_text(encoding="utf-8").splitlines()) == 1


def test_payload_hash_mismatch_blocks(tmp_path):
    bad = {**_ready_execution(), "operator_confirmed_payload_hash": "0" * 64}
    packet = reconcile_registry(bad, registry_path=tmp_path / "registry.jsonl", append_registry=True)
    assert packet["reconciliation_status"] == BLOCKED_STATUS
    assert "execution_packet_registry_validation" in packet["blocked_reasons"]


def test_url_mismatch_blocks(tmp_path):
    bad = {**_ready_execution(), "captured_public_x_url": "https://x.com/capitalchronicle"}
    packet = reconcile_registry(bad, registry_path=tmp_path / "registry.jsonl", append_registry=True)
    assert packet["reconciliation_status"] == BLOCKED_STATUS
    assert "execution_packet_registry_validation" in packet["blocked_reasons"]


def test_prior_registry_append_or_non_ready_blocks(tmp_path):
    prior = reconcile_registry({**_ready_execution(), "publication_registry_record_appended": True}, registry_path=tmp_path / "a.jsonl")
    not_ready = reconcile_registry({**_ready_execution(), "execution_status": "BLOCKED_EXACT_LIVE_CLICK_EXECUTION", "registry_append_ready": False}, registry_path=tmp_path / "b.jsonl")
    assert prior["reconciliation_status"] == BLOCKED_STATUS
    assert "registry_not_already_appended" in prior["blocked_reasons"]
    assert not_ready["reconciliation_status"] == BLOCKED_STATUS
    assert "execution_status_executed" in not_ready["blocked_reasons"]


def test_build_registry_row_is_stable_and_safe():
    first = build_registry_row(_ready_execution())
    second = build_registry_row(_ready_execution())
    assert first["registry_record_id"] == second["registry_record_id"]
    assert first["capture_method"] == "x_cdp_exact_live_click_execution_outcome"
    assert first["token_or_header_read_performed"] is False


def test_fixture_bundle_covers_append_and_blocked_cases():
    bundle = build_fixture_evidence_bundle()
    assert bundle["ready_case_registry_reconciled"] is True
    assert bundle["blocked_cases_blocked"] is True
    assert bundle["local_registry_reconciliation_only"] is True
    assert bundle["public_url_verified_externally"] is False


def test_cli_requires_dry_run(capsys):
    code = main(["--fixture-bundle"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 2
    assert payload["status"] == "blocked_dry_run_flag_required"
    assert payload["publication_registry_record_appended"] is False


def test_cli_writes_fixture_evidence(tmp_path, capsys):
    path = tmp_path / "evidence.json"
    code = main(["--dry-run", "--fixture-bundle", "--write-evidence", str(path)])
    printed = json.loads(capsys.readouterr().out)
    written = json.loads(path.read_text(encoding="utf-8"))
    assert code == 0
    assert written == printed
