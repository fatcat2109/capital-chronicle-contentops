import json
from pathlib import Path

from live_contentops.telegram_live_authority_core import build_approval_event, build_outbox_candidate, build_payload_packet
from live_contentops.telegram_live_sendmessage_pilot import run_pilot

TOKEN = "123456:abcdefghijklmnopqrstuvwxyzABCDEF"
CHANNEL = "-1001234567890"
REL = "docs/automation/TELEGRAM_LIVE_WRITE_BATCH_C_MINIMAL_AUTHORITY/telegram_live_sendmessage_audit_redacted.json"


def _env(tmp_path: Path, kill="0"):
    (tmp_path / ".env.local").write_text(f"TELEGRAM_BOT_TOKEN={TOKEN}\nTELEGRAM_CHANNEL_ID={CHANNEL}\nCONTENTOPS_GLOBAL_KILL_SWITCH={kill}\n", encoding="utf-8")


def test_kill_switch_blocks_send(tmp_path: Path):
    _env(tmp_path, "on")
    calls = []
    audit = run_pilot(tmp_path, REL, True, lambda *args: calls.append(args) or ("http_2xx_json", {}))
    assert audit["kill_switch_state"] == "on_redacted"
    assert "contentops_global_kill_switch_on" in audit["blocked_reasons"]
    assert calls == []


def test_idempotency_suppresses_prior_success(tmp_path: Path):
    _env(tmp_path)
    task_dir = tmp_path / "docs/automation/TELEGRAM_LIVE_WRITE_BATCH_C_MINIMAL_AUTHORITY"
    task_dir.mkdir(parents=True)
    packet = build_payload_packet()
    approval = build_approval_event(packet)
    outbox = build_outbox_candidate(packet, approval)
    (task_dir / "prior.json").write_text(json.dumps({"status": "success", "idempotency_key_hash": outbox["idempotency_key_hash"]}), encoding="utf-8")
    calls = []
    audit = run_pilot(tmp_path, REL, True, lambda *args: calls.append(args) or ("http_2xx_json", {}))
    assert audit["idempotency_state"] == "prior_success_duplicate_suppressed"
    assert calls == []


def test_idempotency_blocks_prior_unknown(tmp_path: Path):
    _env(tmp_path)
    task_dir = tmp_path / "docs/automation/TELEGRAM_LIVE_WRITE_BATCH_C_MINIMAL_AUTHORITY"
    task_dir.mkdir(parents=True)
    packet = build_payload_packet()
    approval = build_approval_event(packet)
    outbox = build_outbox_candidate(packet, approval)
    (task_dir / "prior.json").write_text(json.dumps({"status": "unknown_requires_manual_reconciliation", "idempotency_key_hash": outbox["idempotency_key_hash"]}), encoding="utf-8")
    calls = []
    audit = run_pilot(tmp_path, REL, True, lambda *args: calls.append(args) or ("http_2xx_json", {}))
    assert audit["idempotency_state"] == "prior_unknown_requires_manual_reconciliation"
    assert calls == []
