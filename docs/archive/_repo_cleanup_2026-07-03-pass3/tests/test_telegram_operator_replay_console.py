"""Tests for the 0174UT/UU/UV Telegram operator replay console + reconciliation.

Pure, LOCAL, deterministic. NO network / API / Telegram / env / credential read
and NO ``sendMessage``. The tests assert the reconciliation classifier against
the committed 0174UQ proof + 0174UN ledger, the candidate replay-console action
mapping, and full redaction + determinism of the console packet/doc.
"""

import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

console = importlib.import_module(
    "live_contentops.telegram_operator_replay_console")
ledger = importlib.import_module(
    "live_contentops.telegram_supervised_send_outcome_ledger")

PREV_LEDGER_PATH = ROOT / console.PREVIOUS_LEDGER_PACKET_REL
SEND_PROOF_PATH = ROOT / console.SEND_PROOF_PACKET_REL
ACCEPTED_PROOF_PATH = ROOT / console.ACCEPTED_SEND_PROOF_PACKET_REL


def _prev_ledger():
    return json.loads(PREV_LEDGER_PATH.read_text(encoding="utf-8"))


def _send_proof():
    return json.loads(SEND_PROOF_PATH.read_text(encoding="utf-8"))


def _accepted_proof():
    return json.loads(ACCEPTED_PROOF_PATH.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Import posture
# --------------------------------------------------------------------------- #
def test_import_has_no_side_effects():
    mod = importlib.reload(console)
    assert mod.TASK_LABEL.startswith("TASK_CONTENTOPS_0174UT_UU_UV")
    assert mod.METHOD_SUPERVISED_SEND == "sendMessage"


def test_committed_fixtures_exist():
    assert PREV_LEDGER_PATH.is_file()
    assert SEND_PROOF_PATH.is_file()
    assert ACCEPTED_PROOF_PATH.is_file()


# --------------------------------------------------------------------------- #
# Reconciliation: happy path against committed packets
# --------------------------------------------------------------------------- #
def test_reconciliation_ok_for_committed_uq_proof_against_un_ledger():
    res = console.reconcile_send_proof_with_ledger(_send_proof(), _prev_ledger())
    assert res["reconciliation_outcome_class"] == console.RECON_OK
    assert res["reconciled"] is True
    assert res["previous_ledger_entry_count"] == 1
    assert res["proof_ledger_entry_count"] == 2
    assert res["classified_live_ready"] is False


def test_reconciliation_manifest_relation_old_to_new():
    prev = _prev_ledger()
    proof = _send_proof()
    res = console.reconcile_send_proof_with_ledger(proof, prev)
    assert (res["proof_old_ledger_manifest_checksum"]
            == prev["ledger_manifest_checksum"])
    assert (res["proof_new_ledger_manifest_checksum"]
            != prev["ledger_manifest_checksum"])
    assert res["reconciliation_outcome_class"] == console.RECON_OK


# --------------------------------------------------------------------------- #
# Reconciliation: blocking branches
# --------------------------------------------------------------------------- #
def test_missing_proof_blocks():
    res = console.reconcile_send_proof_with_ledger({}, _prev_ledger())
    assert res["reconciliation_outcome_class"] == console.RECON_BLOCKED_MISSING_PROOF


def test_missing_previous_ledger_blocks():
    res = console.reconcile_send_proof_with_ledger(_send_proof(), {})
    assert (res["reconciliation_outcome_class"]
            == console.RECON_BLOCKED_MISSING_PREVIOUS_LEDGER)


def test_old_manifest_mismatch_blocks():
    prev = _prev_ledger()
    prev["ledger_manifest_checksum"] = "deadbeef_not_the_real_manifest"
    res = console.reconcile_send_proof_with_ledger(_send_proof(), prev)
    assert (res["reconciliation_outcome_class"]
            == console.RECON_BLOCKED_MANIFEST_NOT_ADVANCED)


def test_count_not_incremented_blocks():
    proof = _send_proof()
    proof["ledger_entry_count"] = 5  # not prev(1) + 1
    res = console.reconcile_send_proof_with_ledger(proof, _prev_ledger())
    assert (res["reconciliation_outcome_class"]
            == console.RECON_BLOCKED_MANIFEST_NOT_ADVANCED)


def test_not_appended_blocks():
    proof = _send_proof()
    proof["appended"] = False
    res = console.reconcile_send_proof_with_ledger(proof, _prev_ledger())
    assert (res["reconciliation_outcome_class"]
            == console.RECON_BLOCKED_MANIFEST_NOT_ADVANCED)


def test_previous_entry_checksum_mismatch_blocks():
    proof = _send_proof()
    proof["previous_ledger_entry_checksum"] = "wrong_previous_entry_checksum"
    res = console.reconcile_send_proof_with_ledger(proof, _prev_ledger())
    assert (res["reconciliation_outcome_class"]
            == console.RECON_BLOCKED_ENTRY_CHECKSUM_MISMATCH)


def test_new_entry_checksum_missing_blocks():
    proof = _send_proof()
    proof["new_ledger_entry_checksum"] = None
    res = console.reconcile_send_proof_with_ledger(proof, _prev_ledger())
    assert (res["reconciliation_outcome_class"]
            == console.RECON_BLOCKED_ENTRY_CHECKSUM_MISMATCH)


def test_new_entry_checksum_unchanged_blocks():
    prev = _prev_ledger()
    proof = _send_proof()
    proof["new_ledger_entry_checksum"] = prev["current_ledger_entry_checksum"]
    res = console.reconcile_send_proof_with_ledger(proof, prev)
    assert (res["reconciliation_outcome_class"]
            == console.RECON_BLOCKED_ENTRY_CHECKSUM_MISMATCH)


def test_response_checksum_missing_blocks():
    proof = _send_proof()
    proof["response_checksum"] = None
    res = console.reconcile_send_proof_with_ledger(proof, _prev_ledger())
    assert res["reconciliation_outcome_class"] == console.RECON_BLOCKED_MISSING_PROOF


def test_forbidden_raw_token_fail_closes_reconciliation():
    proof = _send_proof()
    proof["leaked_token"] = "123456789:AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQq00"
    res = console.reconcile_send_proof_with_ledger(proof, _prev_ledger())
    assert res["reconciliation_outcome_class"] == console.RECON_FAIL_CLOSED
    assert res["forbidden_fields_detected"] is True


def test_forbidden_raw_url_in_previous_ledger_fail_closes():
    prev = _prev_ledger()
    prev["leaked_url"] = "https://api.telegram.org/bot123456789:AaBbCc/sendMessage"
    res = console.reconcile_send_proof_with_ledger(_send_proof(), prev)
    assert res["reconciliation_outcome_class"] == console.RECON_FAIL_CLOSED


# --------------------------------------------------------------------------- #
# Operator ledger view
# --------------------------------------------------------------------------- #
def test_ledger_view_reflects_committed_state():
    view = console.build_operator_ledger_view(_send_proof(), _prev_ledger())
    assert view["ledger_entry_count"] == 2
    assert view["last_send_succeeded"] is True
    assert view["last_live_test_sequence"] == 3
    assert view["reconciliation_status"] == console.RECON_OK
    assert view["live_ready"] is False
    assert console.scan_for_leaks(view) == []


# --------------------------------------------------------------------------- #
# Candidate replay console action mapping
# --------------------------------------------------------------------------- #
def _entries():
    return console._ledger_entries_from_previous_packet(_prev_ledger())


def _same_candidate():
    return console.candidate_from_ledger_entry(_entries()[0])


def test_exact_replay_maps_to_blocked_do_not_send():
    entries = _entries()
    recorded_gate = entries[0].get("operator_gate_id")
    out = console.build_candidate_replay_console(
        _same_candidate(), entries, operator_gate_id=recorded_gate)
    assert out["replay_guard_outcome_class"] == ledger.REPLAY_BLOCKED_EXACT
    assert out["next_allowed_action"] == console.ACTION_BLOCKED_EXACT_REPLAY


def test_stable_duplicate_without_gate_maps_to_requires_fresh_gate():
    out = console.build_candidate_replay_console(
        _same_candidate(), _entries(), operator_gate_id=None)
    assert out["replay_guard_outcome_class"] == ledger.REPLAY_REQUIRES_FRESH_GATE
    assert out["next_allowed_action"] == console.ACTION_REQUIRES_FRESH_GATE


def test_stable_duplicate_with_fresh_gate_maps_to_clear_with_flag():
    out = console.build_candidate_replay_console(
        _same_candidate(), _entries(),
        operator_gate_id="operator_console_fresh_gate_distinct")
    assert out["replay_guard_outcome_class"] == ledger.REPLAY_CLEAR
    assert out["next_allowed_action"] == console.ACTION_CLEAR_FOR_MANUAL_SEND
    assert out["same_payload_under_fresh_gate"] is True


def test_new_payload_maps_to_clear_without_flag():
    entries = _entries()
    new_candidate = console.candidate_from_ledger_entry(entries[0])
    new_candidate["send_text_checksum"] = console.compute_checksum(
        {"kind": "new_payload_for_test"})
    new_candidate.pop("evidence_checksum", None)
    new_candidate["evidence_checksum"] = console.compute_checksum(new_candidate)
    out = console.build_candidate_replay_console(
        new_candidate, entries, operator_gate_id="operator_console_fresh_gate")
    assert out["replay_guard_outcome_class"] == ledger.REPLAY_CLEAR
    assert out["next_allowed_action"] == console.ACTION_CLEAR_FOR_MANUAL_SEND
    assert out["same_payload_under_fresh_gate"] is False


def test_invalid_candidate_maps_to_blocked_invalid():
    bad = {"provider": "telegram"}  # missing required checksums
    out = console.build_candidate_replay_console(
        bad, _entries(), operator_gate_id="g")
    assert (out["replay_guard_outcome_class"]
            == ledger.REPLAY_BLOCKED_MISSING_EVIDENCE)
    assert out["next_allowed_action"] == console.ACTION_BLOCKED_INVALID_CANDIDATE


def test_forbidden_candidate_maps_to_fail_closed():
    bad = console.candidate_from_ledger_entry(_entries()[0])
    bad["leaked_token"] = "123456789:AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQq00"
    out = console.build_candidate_replay_console(
        bad, _entries(), operator_gate_id="g")
    assert out["replay_guard_outcome_class"] == ledger.REPLAY_FAIL_CLOSED
    assert out["next_allowed_action"] == console.ACTION_FAIL_CLOSED


def test_console_never_classifies_live_ready():
    out = console.build_candidate_replay_console(
        _same_candidate(), _entries(),
        operator_gate_id="operator_console_fresh_gate")
    assert out["classified_live_ready"] is False
    assert out["classified_auto_send_ready"] is False
    assert out["requires_separate_operator_send_gate"] is True


# --------------------------------------------------------------------------- #
# Console packet + doc
# --------------------------------------------------------------------------- #
def _packet():
    return console.build_operator_console_packet(
        _send_proof(), _prev_ledger(),
        accepted_send_proof_packet=_accepted_proof())


def test_console_packet_is_deterministic():
    p1 = _packet()
    p2 = _packet()
    assert p1 == p2
    assert p1["console_packet_checksum"]


def test_console_packet_and_doc_scanner_clean():
    p = _packet()
    doc = console.build_operator_console_doc(p)
    assert console.scan_console(p, doc) == []


def test_console_packet_examples_cover_all_four_actions():
    p = _packet()
    ex = p["candidate_console_examples"]
    assert (ex["a_exact_replay_blocked"]["next_allowed_action"]
            == console.ACTION_BLOCKED_EXACT_REPLAY)
    assert (ex["b_same_payload_without_fresh_gate"]["next_allowed_action"]
            == console.ACTION_REQUIRES_FRESH_GATE)
    assert (ex["c_same_payload_with_fresh_gate"]["next_allowed_action"]
            == console.ACTION_CLEAR_FOR_MANUAL_SEND)
    assert (ex["c_same_payload_with_fresh_gate"]["same_payload_under_fresh_gate"]
            is True)
    assert (ex["d_new_payload_clear"]["next_allowed_action"]
            == console.ACTION_CLEAR_FOR_MANUAL_SEND)
    assert (ex["d_new_payload_clear"]["same_payload_under_fresh_gate"]
            is False)


def test_console_packet_records_reconciliation_and_counts():
    p = _packet()
    assert p["reconciliation_outcome_class"] == console.RECON_OK
    assert p["current_ledger_entry_count"] == 2
    assert p["current_ledger_manifest_checksum"]
    assert p["previous_ledger_manifest_checksum"]
    assert (p["current_ledger_manifest_checksum"]
            != p["previous_ledger_manifest_checksum"])


def test_console_packet_stores_no_secrets_and_not_live():
    p = _packet()
    blob = json.dumps(p)
    assert "api.telegram.org/bot" not in blob
    assert p["live_ready"] is False
    assert p["sendmessage_executed"] is False
    assert p["network_performed"] is False
    assert p["telegram_api_called"] is False
    assert p["credential_read"] is False
    assert p["env_read"] is False
    assert p["is_read_only_console"] is True


def test_build_from_repo_matches_explicit_packet():
    from_repo = console.build_console_packet_from_repo(ROOT)
    explicit = _packet()
    assert (from_repo["console_packet_checksum"]
            == explicit["console_packet_checksum"])


def test_write_artifacts_refuses_unsafe(tmp_path):
    import pytest
    p = _packet()
    doc = console.build_operator_console_doc(p)
    written = console.write_artifacts(tmp_path, p, doc)
    assert len(written) == 2
    bad = dict(p)
    bad["leaked"] = "123456789:AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQq00"
    with pytest.raises(RuntimeError):
        console.write_artifacts(tmp_path, bad, doc)
