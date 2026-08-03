# -*- coding: utf-8 -*-
"""Tests for the operator-approved supervised live Daily ContentOps runner."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from live_contentops.operator_approved_supervised_live_daily_run_v0 import (
    CLASSIFICATION_BLOCKED,
    CLASSIFICATION_PARTIAL,
    REQUIRED_CAVEAT,
    run_operator_approved_supervised_live_daily_run,
)


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _exercise_historical_daily_run_mechanics(monkeypatch):
    import live_contentops.operator_approved_supervised_live_daily_run_v0 as legacy_runner

    monkeypatch.setattr(legacy_runner, "quarantine", lambda *_args, **_kwargs: None)


def test_runner_posts_telegram_with_existing_safe_adapter_and_skips_browser_paths(tmp_path):
    sent_messages: list[str] = []

    def fake_telegram_send(**kwargs):
        sent_messages.append(kwargs["message"])
        assert kwargs["dry_run"] is False
        assert kwargs["parse_mode"] == "HTML"
        assert REQUIRED_CAVEAT in kwargs["message"]
        assert kwargs["approval_context"]["operator_approval_marker"]["approved_public_dispatch"] is True
        return {
            "status": "SUCCESS",
            "platform": "telegram",
            "action": "post",
            "id": "123",
            "response": {"result": {"message_id": 123, "text": kwargs["message"]}},
        }

    result = run_operator_approved_supervised_live_daily_run(
        repo_root=ROOT,
        output_dir=tmp_path,
        duplicate_ledger_path=tmp_path / "duplicate_ledger.jsonl",
        operator_approved_live_run=True,
        max_send_attempts_per_platform=1,
        telegram_send_func=fake_telegram_send,
        current_head="491d5a9ed3f259108b01110a519cfd5d7221faa5",
        started_at="2026-07-10T00:00:00+00:00",
    )

    assert result["classification"] == CLASSIFICATION_PARTIAL
    assert sent_messages and REQUIRED_CAVEAT in sent_messages[0]
    dispatch = result["dispatch_results"]
    assert dispatch["attempted_platforms"] == ["telegram"]
    assert dispatch["successful_platforms"] == ["telegram"]
    assert sorted(dispatch["skipped_platforms"]) == ["substack", "x"]
    telegram = next(row for row in dispatch["per_platform_results"] if row["platform"] == "telegram")
    assert telegram["status"] == "POSTED"
    assert telegram["public_url_or_message_id_or_draft_id"] == "123"
    assert telegram["duplicate_guard_result"] == "PASS"
    assert telegram["caveat_present"] is True
    assert result["safety_review"]["duplicate_guard_passed"] is True
    assert result["readback"]["readback_overall_status"] == "PASS_TELEGRAM_MESSAGE_ID_RETURNED"
    assert (tmp_path / "live_run_plan_v0.json").exists()
    assert (tmp_path / "live_dispatch_results_v0.json").exists()
    assert (tmp_path / "live_readback_v0.json").exists()
    assert (tmp_path / "live_run_safety_review_v0.json").exists()
    assert (tmp_path / "run_evidence_v0.json").exists()

    ledger_rows = [
        json.loads(line)
        for line in (tmp_path / "duplicate_ledger.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(ledger_rows) == 1
    assert ledger_rows[0]["platform"] == "telegram"


def test_duplicate_guard_blocks_second_send_without_calling_adapter(tmp_path):
    def fake_success(**kwargs):
        return {
            "status": "SUCCESS",
            "platform": "telegram",
            "action": "post",
            "id": "777",
            "response": {"result": {"message_id": 777, "text": kwargs["message"]}},
        }

    ledger = tmp_path / "duplicate_ledger.jsonl"
    run_operator_approved_supervised_live_daily_run(
        repo_root=ROOT,
        output_dir=tmp_path / "first",
        duplicate_ledger_path=ledger,
        operator_approved_live_run=True,
        max_send_attempts_per_platform=1,
        telegram_send_func=fake_success,
        current_head="491d5a9ed3f259108b01110a519cfd5d7221faa5",
        started_at="2026-07-10T00:00:00+00:00",
    )

    def should_not_send(**kwargs):
        raise AssertionError("duplicate guard should block before adapter send")

    second = run_operator_approved_supervised_live_daily_run(
        repo_root=ROOT,
        output_dir=tmp_path / "second",
        duplicate_ledger_path=ledger,
        operator_approved_live_run=True,
        max_send_attempts_per_platform=1,
        telegram_send_func=should_not_send,
        current_head="491d5a9ed3f259108b01110a519cfd5d7221faa5",
        started_at="2026-07-10T00:01:00+00:00",
    )

    assert second["classification"] == CLASSIFICATION_BLOCKED
    telegram = next(row for row in second["dispatch_results"]["per_platform_results"] if row["platform"] == "telegram")
    assert telegram["status"] == "FAILED"
    assert telegram["duplicate_guard_result"] == "PUBLIC_DISPATCH_FROZEN"
    assert "duplicate_guard_blocked" in telegram["error_summary_redacted"]
    assert second["dispatch_results"]["attempted_platforms"] == []


def test_operator_approval_flag_is_required(tmp_path):
    result = run_operator_approved_supervised_live_daily_run(
        repo_root=ROOT,
        output_dir=tmp_path,
        duplicate_ledger_path=tmp_path / "duplicate_ledger.jsonl",
        operator_approved_live_run=False,
        max_send_attempts_per_platform=1,
        telegram_send_func=lambda **kwargs: (_ for _ in ()).throw(AssertionError("must not send")),
        current_head="491d5a9ed3f259108b01110a519cfd5d7221faa5",
        started_at="2026-07-10T00:00:00+00:00",
    )

    assert result["classification"] == CLASSIFICATION_BLOCKED
    assert "operator_approved_live_run_flag_missing" in result["run_evidence"]["blockers"]
    assert result["dispatch_results"]["attempted_platforms"] == []
    assert result["run_evidence"]["live_action_performed"] is False
