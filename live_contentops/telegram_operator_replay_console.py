"""Telegram supervised-send REPLAY CONSOLE + OUTCOME RECONCILIATION (LOCAL).

Task 0174UT/UU/UV. This is the operator-facing, deterministic, LOCAL data
contract for the supervised remote operator loop. It DOES NOT call Telegram,
DOES NOT read ``.env`` / env / credentials, and DOES NOT send. It only reads
already-committed, redacted evidence/ledger packets and reduces them to:

  1. A normalized OPERATOR LEDGER VIEW (current count, manifest/entry checksums,
     last successful send summary, replay keys, reconciliation status).
  2. A RECONCILIATION classifier that proves the most recent live send proof was
     correctly appended into the immutable ledger (count incremented, manifest
     advanced, entry-checksum chain intact), fail-closed.
  3. A CANDIDATE REPLAY CONSOLE that, for a candidate evidence packet against the
     current ledger, reports the replay-guard decision and the single
     ``next_allowed_action`` the operator may take.
  4. A deterministic console PACKET + DOC summarizing all of the above with four
     worked candidate examples (exact replay / same-payload-no-gate /
     same-payload-fresh-gate / new payload).

HARD GUARANTEES (enforced by tests + the reused fail-closed scanners):
  * Pure Python stdlib only. NO network / API / Telegram call. NO env / .env /
    keyring / credential read. NO ``sendMessage``.
  * Importing this module performs NO writes and NO side effects. Artifacts are
    written ONLY when ``write_artifacts(...)`` is called explicitly.
  * NEVER classifies anything as ``live_ready`` or auto-send-ready. A ``clear``
    candidate console result only means "not a replay" and STILL requires a
    separate, manual operator supervised-send gate.
"""

import os.path

# Reuse the accepted ledger (replay keys + guard + scanners) and, through it,
# the adapter's redaction / financial-advice scanners + deterministic checksum.
from live_contentops import telegram_supervised_send_outcome_ledger as ledger
from live_contentops import telegram_local_adapter_contract as adapter

TASK_LABEL = (
    "TASK_CONTENTOPS_0174UT_UU_UV_TELEGRAM_SUPERVISED_SEND_LEDGER_REPLAY_"
    "CONSOLE_AND_OUTCOME_RECONCILIATION_BATCH_V0"
)
MODEL = "TELEGRAM_OPERATOR_REPLAY_CONSOLE_0174UT_UU_UV"
MODEL_VERSION = "0174UT_UU_UV_TELEGRAM_OPERATOR_REPLAY_CONSOLE_V1"

LEDGER_VIEW_SCHEMA = "contentops.telegram_operator_ledger_view"
LEDGER_VIEW_SCHEMA_VERSION = "0174UT_UU_UV_OPERATOR_LEDGER_VIEW_V1"
RECONCILIATION_SCHEMA = "contentops.telegram_send_ledger_reconciliation"
RECONCILIATION_SCHEMA_VERSION = "0174UT_UU_UV_RECONCILIATION_V1"
CANDIDATE_CONSOLE_SCHEMA = "contentops.telegram_candidate_replay_console"
CANDIDATE_CONSOLE_SCHEMA_VERSION = "0174UT_UU_UV_CANDIDATE_REPLAY_CONSOLE_V1"
CONSOLE_PACKET_SCHEMA = "contentops.telegram_operator_replay_console_packet"
CONSOLE_PACKET_SCHEMA_VERSION = "0174UT_UU_UV_OPERATOR_REPLAY_CONSOLE_PACKET_V1"

SOURCE_BASELINE_COMMIT = "d45fa67b1f8adf9e810ceb1fb9d833db6f44442a"

DOC_REL_DIR = os.path.join("docs", "automation", "0174UT_UU_UV")
PACKET_FILENAME = "telegram_operator_replay_console_packet.json"
DOC_FILENAME = "telegram_operator_replay_console.md"

# Default committed source packets (read-only) used by the packet builder.
PREVIOUS_LEDGER_PACKET_REL = os.path.join(
    "docs", "automation", "0174UN_UO_UP",
    "telegram_supervised_send_outcome_ledger_packet.json")
SEND_PROOF_PACKET_REL = os.path.join(
    "docs", "automation", "0174UQ_UR_US",
    "telegram_ledger_guarded_supervised_send_proof_packet.json")
ACCEPTED_SEND_PROOF_PACKET_REL = os.path.join(
    "docs", "automation", "0174UK_UL_UM",
    "telegram_single_supervised_sendmessage_proof_packet.json")

NEXT_RECOMMENDED_TASK = (
    "TASK_CONTENTOPS_0174UW_UX_UY_TELEGRAM_SUPERVISED_SEND_OPERATOR_COCKPIT_"
    "READ_MODEL_AND_NEXT_SEND_PRECHECK_BATCH_V0"
)

PROVIDER_TELEGRAM = adapter.PROVIDER_TELEGRAM
METHOD_SUPERVISED_SEND = adapter.METHOD_SUPERVISED_SEND

# --------------------------------------------------------------------------- #
# Reconciliation outcome classes (exact names mandated by the task)
# --------------------------------------------------------------------------- #
RECON_OK = "ledger_reconciliation_ok_count_incremented"
RECON_BLOCKED_MISSING_PROOF = "ledger_reconciliation_blocked_missing_proof"
RECON_BLOCKED_MISSING_PREVIOUS_LEDGER = (
    "ledger_reconciliation_blocked_missing_previous_ledger")
RECON_BLOCKED_MANIFEST_NOT_ADVANCED = (
    "ledger_reconciliation_blocked_manifest_not_advanced")
RECON_BLOCKED_ENTRY_CHECKSUM_MISMATCH = (
    "ledger_reconciliation_blocked_entry_checksum_mismatch")
RECON_FAIL_CLOSED = "ledger_reconciliation_fail_closed_forbidden_value"

# Granular machine-readable reconciliation reason codes (not prose).
RECON_REASON_FORBIDDEN_VALUE = "recon_forbidden_value_detected"
RECON_REASON_PROOF_MISSING = "recon_proof_missing_or_empty"
RECON_REASON_PROOF_RESPONSE_CHECKSUM_MISSING = "recon_proof_response_checksum_missing"
RECON_REASON_PREVIOUS_LEDGER_MISSING = "recon_previous_ledger_missing_or_empty"
RECON_REASON_NOT_APPENDED = "recon_proof_not_appended"
RECON_REASON_COUNT_NOT_INCREMENTED = "recon_entry_count_not_incremented"
RECON_REASON_OLD_MANIFEST_MISMATCH = "recon_old_manifest_checksum_mismatch"
RECON_REASON_PREVIOUS_ENTRY_MISMATCH = "recon_previous_entry_checksum_mismatch"
RECON_REASON_NEW_ENTRY_CHECKSUM_MISSING = "recon_new_entry_checksum_missing"
RECON_REASON_NEW_ENTRY_CHECKSUM_UNCHANGED = "recon_new_entry_checksum_unchanged"

# --------------------------------------------------------------------------- #
# Candidate-console next-allowed-action classes (exact names mandated)
# --------------------------------------------------------------------------- #
ACTION_BLOCKED_EXACT_REPLAY = "blocked_exact_replay_do_not_send"
ACTION_REQUIRES_FRESH_GATE = "requires_fresh_operator_gate"
ACTION_CLEAR_FOR_MANUAL_SEND = "clear_for_manual_supervised_send_gate"
ACTION_BLOCKED_INVALID_CANDIDATE = "blocked_invalid_candidate"
ACTION_FAIL_CLOSED = "fail_closed_forbidden_value"

# Deterministic map from replay-guard outcome class -> next allowed action.
_GUARD_OUTCOME_TO_ACTION = {
    ledger.REPLAY_BLOCKED_EXACT: ACTION_BLOCKED_EXACT_REPLAY,
    ledger.REPLAY_REQUIRES_FRESH_GATE: ACTION_REQUIRES_FRESH_GATE,
    ledger.REPLAY_CLEAR: ACTION_CLEAR_FOR_MANUAL_SEND,
    ledger.REPLAY_BLOCKED_MISSING_EVIDENCE: ACTION_BLOCKED_INVALID_CANDIDATE,
    ledger.REPLAY_FAIL_CLOSED: ACTION_FAIL_CLOSED,
}

RECONCILIATION_OUTCOME_CLASSES = (
    RECON_OK,
    RECON_BLOCKED_MISSING_PROOF,
    RECON_BLOCKED_MISSING_PREVIOUS_LEDGER,
    RECON_BLOCKED_MANIFEST_NOT_ADVANCED,
    RECON_BLOCKED_ENTRY_CHECKSUM_MISMATCH,
    RECON_FAIL_CLOSED,
)
NEXT_ALLOWED_ACTION_CLASSES = (
    ACTION_BLOCKED_EXACT_REPLAY,
    ACTION_REQUIRES_FRESH_GATE,
    ACTION_CLEAR_FOR_MANUAL_SEND,
    ACTION_BLOCKED_INVALID_CANDIDATE,
    ACTION_FAIL_CLOSED,
)


# --------------------------------------------------------------------------- #
# Scanning / serialization (reuse the accepted scanners)
# --------------------------------------------------------------------------- #
def scan_for_leaks(obj):
    """Return redaction violations for ``obj`` (delegates)."""
    return ledger.scan_for_leaks(obj)


def scan_for_financial_advice(obj):
    """Return financial-advice violations for ``obj`` (delegates)."""
    return ledger.scan_for_financial_advice(obj)


def serialize(obj):
    """Deterministic JSON (delegates to the adapter)."""
    return adapter.serialize(obj)


def compute_checksum(obj):
    """SHA-256 of the deterministic serialization (delegates)."""
    return adapter.compute_checksum(obj)


def scan_console(packet, doc):
    """Return the combined redaction + financial-advice violations."""
    return (scan_for_leaks(packet) + scan_for_leaks(doc)
            + scan_for_financial_advice(packet)
            + scan_for_financial_advice(doc))


def _safety_flags():
    """Hard invariants attached to every 0174UT/UU/UV object."""
    return {
        "network_performed": False,
        "platform_api_called": False,
        "telegram_api_called": False,
        "credential_hydrated": False,
        "credential_read": False,
        "env_read": False,
        "dotenv_read": False,
        "sendmessage_executed": False,
        "dispatch_performed": False,
        "scheduler_enabled": False,
        "auto_retry_allowed": False,
        "autonomous_reply_performed": False,
        "live_ready": False,
        "auto_send_ready": False,
        "valid_for_live_execution": False,
        "is_local_only": True,
        "is_read_only_console": True,
        "stores_no_token": True,
        "stores_no_raw_destination": True,
        "stores_no_raw_chat_id": True,
        "stores_no_raw_response": True,
        "stores_no_raw_url": True,
        "stores_no_headers": True,
        "stores_no_cookies": True,
        "stores_no_username": True,
        "no_financial_advice_emitted": True,
    }


# --------------------------------------------------------------------------- #
# Candidate evidence helpers (build a replay-guardable redacted candidate)
# --------------------------------------------------------------------------- #
def build_candidate_evidence(*, destination_binding_checksum, send_text_checksum,
                             request_checksum, credential_handle_id,
                             live_test_sequence, response_checksum=None,
                             method_name=METHOD_SUPERVISED_SEND,
                             provider=PROVIDER_TELEGRAM):
    """Build a minimal, redacted, replay-guardable candidate evidence packet.

    Carries ONLY redacted checksums/classes + symbolic markers (never a token,
    raw destination, raw chat id, raw URL, headers, cookies, or raw response).
    The ``response_checksum`` defaults to a deterministic non-secret placeholder
    so the candidate satisfies the guard's required-field check; it is NOT a
    provider response and does not affect either replay key.
    """
    if response_checksum is None:
        response_checksum = compute_checksum({
            "kind": "candidate_console_response_placeholder",
            "send_text_checksum": send_text_checksum,
            "request_checksum": request_checksum,
            "live_test_sequence": live_test_sequence,
            "method_name": method_name,
            "provider": provider,
        })
    packet = {
        "task_label": TASK_LABEL,
        "provider": provider,
        "method_name": method_name,
        "live_test_sequence": live_test_sequence,
        "credential_handle_id": credential_handle_id,
        "destination_binding_checksum": destination_binding_checksum,
        "send_text_checksum": send_text_checksum,
        "request_checksum": request_checksum,
        "response_checksum": response_checksum,
        "is_candidate_pre_send": True,
    }
    packet["evidence_checksum"] = compute_checksum(packet)
    return packet


def candidate_from_ledger_entry(entry, *, response_checksum=None):
    """Reconstruct a candidate evidence packet from a committed ledger entry.

    Uses ONLY the entry's redacted, replay-key-relevant fields so the rebuilt
    candidate reproduces the entry's stable (and, under the same gate, exact)
    replay keys. Never reads or copies any secret material.
    """
    e = entry or {}
    return build_candidate_evidence(
        destination_binding_checksum=e.get("destination_binding_checksum"),
        send_text_checksum=e.get("send_text_checksum"),
        request_checksum=e.get("request_checksum"),
        credential_handle_id=e.get("credential_handle_id"),
        live_test_sequence=e.get("live_test_sequence"),
        response_checksum=response_checksum,
        method_name=e.get("method_name") or METHOD_SUPERVISED_SEND,
        provider=e.get("provider") or PROVIDER_TELEGRAM)


# --------------------------------------------------------------------------- #
# 1. Normalized operator ledger view
# --------------------------------------------------------------------------- #
def build_operator_ledger_view(send_proof_packet, previous_ledger_packet,
                               reconciliation=None):
    """Reduce the latest send proof + previous ledger to a normalized view.

    All fields are redacted classes / checksums / booleans only. The
    ``reconciliation_status`` is taken from a supplied reconciliation result
    (or recomputed if not supplied).
    """
    proof = send_proof_packet or {}
    if reconciliation is None:
        reconciliation = reconcile_send_proof_with_ledger(
            send_proof_packet, previous_ledger_packet)
    view = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "ledger_view_schema": LEDGER_VIEW_SCHEMA,
        "ledger_view_schema_version": LEDGER_VIEW_SCHEMA_VERSION,
        "provider": proof.get("provider") or PROVIDER_TELEGRAM,
        "ledger_entry_count": proof.get("ledger_entry_count"),
        "last_ledger_manifest_checksum": proof.get("new_ledger_manifest_checksum"),
        "previous_ledger_manifest_checksum": proof.get(
            "old_ledger_manifest_checksum"),
        "current_ledger_entry_checksum": proof.get("new_ledger_entry_checksum"),
        "previous_ledger_entry_checksum": proof.get(
            "previous_ledger_entry_checksum"),
        "last_send_outcome_class": proof.get("send_outcome_class"),
        "last_send_succeeded": bool(proof.get("send_succeeded")),
        "last_live_test_sequence": proof.get("live_test_sequence"),
        "last_request_checksum": proof.get("request_checksum"),
        "last_response_checksum": proof.get("response_checksum"),
        "last_stable_payload_replay_key": proof.get("stable_payload_replay_key"),
        "last_exact_run_replay_key": proof.get("exact_run_replay_key"),
        "reconciliation_status": reconciliation.get("reconciliation_outcome_class"),
        **_safety_flags(),
    }
    view["ledger_view_checksum"] = compute_checksum(view)
    return view


# --------------------------------------------------------------------------- #
# 2. Reconciliation classifier
# --------------------------------------------------------------------------- #
def reconcile_send_proof_with_ledger(send_proof_packet, previous_ledger_packet):
    """Prove a live send proof was correctly appended to the immutable ledger.

    Fail-closed. Order of checks:
      1. forbidden/leaky proof OR previous ledger => fail_closed;
      2. proof missing/empty OR missing response_checksum => blocked_missing_proof;
      3. previous ledger missing/empty => blocked_missing_previous_ledger;
      4. proof not appended, count not incremented, or old manifest mismatch
         => blocked_manifest_not_advanced;
      5. previous-entry-checksum mismatch, or new-entry-checksum missing/unchanged
         => blocked_entry_checksum_mismatch;
      6. otherwise => ok_count_incremented.

    NEVER marks anything live-ready.
    """
    proof = send_proof_packet or {}
    prev = previous_ledger_packet or {}

    forbidden = bool(scan_for_leaks(proof) or scan_for_leaks(prev)
                     or scan_for_financial_advice(proof)
                     or scan_for_financial_advice(prev))
    if forbidden:
        return _reconciliation_result(
            RECON_FAIL_CLOSED, [RECON_REASON_FORBIDDEN_VALUE],
            forbidden=True, proof=proof, prev=prev)

    # Proof presence + completeness.
    if not proof:
        return _reconciliation_result(
            RECON_BLOCKED_MISSING_PROOF, [RECON_REASON_PROOF_MISSING],
            forbidden=False, proof=proof, prev=prev)
    if proof.get("response_checksum") in (None, ""):
        return _reconciliation_result(
            RECON_BLOCKED_MISSING_PROOF,
            [RECON_REASON_PROOF_RESPONSE_CHECKSUM_MISSING],
            forbidden=False, proof=proof, prev=prev)

    # Previous ledger presence.
    prev_count = prev.get("ledger_entry_count")
    prev_manifest = prev.get("ledger_manifest_checksum")
    prev_entry_checksum = prev.get("current_ledger_entry_checksum")
    if not prev or prev_count is None or not prev_manifest or not prev_entry_checksum:
        return _reconciliation_result(
            RECON_BLOCKED_MISSING_PREVIOUS_LEDGER,
            [RECON_REASON_PREVIOUS_LEDGER_MISSING],
            forbidden=False, proof=proof, prev=prev)

    # Manifest / count advancement.
    manifest_reasons = []
    if proof.get("appended") is not True:
        manifest_reasons.append(RECON_REASON_NOT_APPENDED)
    if proof.get("ledger_entry_count") != prev_count + 1:
        manifest_reasons.append(RECON_REASON_COUNT_NOT_INCREMENTED)
    if proof.get("old_ledger_manifest_checksum") != prev_manifest:
        manifest_reasons.append(RECON_REASON_OLD_MANIFEST_MISMATCH)
    if manifest_reasons:
        return _reconciliation_result(
            RECON_BLOCKED_MANIFEST_NOT_ADVANCED, manifest_reasons,
            forbidden=False, proof=proof, prev=prev)

    # Entry-checksum chain integrity.
    entry_reasons = []
    new_entry_checksum = proof.get("new_ledger_entry_checksum")
    if proof.get("previous_ledger_entry_checksum") != prev_entry_checksum:
        entry_reasons.append(RECON_REASON_PREVIOUS_ENTRY_MISMATCH)
    if not new_entry_checksum:
        entry_reasons.append(RECON_REASON_NEW_ENTRY_CHECKSUM_MISSING)
    elif new_entry_checksum == prev_entry_checksum:
        entry_reasons.append(RECON_REASON_NEW_ENTRY_CHECKSUM_UNCHANGED)
    if entry_reasons:
        return _reconciliation_result(
            RECON_BLOCKED_ENTRY_CHECKSUM_MISMATCH, entry_reasons,
            forbidden=False, proof=proof, prev=prev)

    return _reconciliation_result(
        RECON_OK, [], forbidden=False, proof=proof, prev=prev)


def _reconciliation_result(outcome_class, reasons, *, forbidden, proof, prev):
    """Build a deterministic reconciliation result (pure value)."""
    if forbidden:
        status = adapter.Status.FAIL_CLOSED
    elif outcome_class == RECON_OK:
        status = adapter.Status.PASS
    else:
        status = adapter.Status.BLOCKED
    prev_count = (prev or {}).get("ledger_entry_count")
    result = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "reconciliation_schema": RECONCILIATION_SCHEMA,
        "reconciliation_schema_version": RECONCILIATION_SCHEMA_VERSION,
        "status": status,
        "reconciliation_outcome_class": outcome_class,
        "reconciled": outcome_class == RECON_OK,
        "provider": (proof or {}).get("provider") or PROVIDER_TELEGRAM,
        "previous_ledger_entry_count": prev_count,
        "expected_ledger_entry_count": (
            prev_count + 1 if isinstance(prev_count, int) else None),
        "proof_ledger_entry_count": (proof or {}).get("ledger_entry_count"),
        "previous_ledger_manifest_checksum": (prev or {}).get(
            "ledger_manifest_checksum"),
        "proof_old_ledger_manifest_checksum": (proof or {}).get(
            "old_ledger_manifest_checksum"),
        "proof_new_ledger_manifest_checksum": (proof or {}).get(
            "new_ledger_manifest_checksum"),
        "previous_ledger_entry_checksum": (prev or {}).get(
            "current_ledger_entry_checksum"),
        "proof_previous_ledger_entry_checksum": (proof or {}).get(
            "previous_ledger_entry_checksum"),
        "proof_new_ledger_entry_checksum": (proof or {}).get(
            "new_ledger_entry_checksum"),
        "proof_response_checksum_present": bool(
            (proof or {}).get("response_checksum")),
        "proof_appended": (proof or {}).get("appended"),
        "manifest_advanced": (
            outcome_class in (RECON_OK,)
            or (proof or {}).get("new_ledger_manifest_checksum")
            != (prev or {}).get("ledger_manifest_checksum")),
        "blocked_reasons": sorted(set(reasons)),
        "forbidden_fields_detected": forbidden,
        "classified_live_ready": False,
        **_safety_flags(),
    }
    result["reconciliation_checksum"] = compute_checksum(result)
    return result


# --------------------------------------------------------------------------- #
# 3. Candidate replay console
# --------------------------------------------------------------------------- #
def build_candidate_replay_console(candidate_evidence_packet,
                                   current_ledger_entries,
                                   operator_gate_id=None):
    """Report the replay decision + single next-allowed-action for a candidate.

    Delegates the decision to the accepted ledger replay guard, then maps the
    guard outcome to exactly one ``next_allowed_action``. NEVER marks anything
    live-ready: a clear result maps to ``clear_for_manual_supervised_send_gate``
    and STILL requires a separate manual operator gate.
    """
    entries = list(current_ledger_entries or [])
    guard = ledger.build_replay_guard_state(
        entries, candidate_evidence_packet, operator_gate_id=operator_gate_id)
    outcome_class = guard.get("replay_guard_outcome_class")
    next_action = _GUARD_OUTCOME_TO_ACTION.get(
        outcome_class, ACTION_BLOCKED_INVALID_CANDIDATE)

    console = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "candidate_console_schema": CANDIDATE_CONSOLE_SCHEMA,
        "candidate_console_schema_version": CANDIDATE_CONSOLE_SCHEMA_VERSION,
        "status": guard.get("status"),
        "provider": guard.get("provider") or PROVIDER_TELEGRAM,
        "replay_guard_outcome_class": outcome_class,
        "exact_run_replay_key": guard.get("exact_run_replay_key"),
        "stable_payload_replay_key": guard.get("stable_payload_replay_key"),
        "exact_replay_key_matched": bool(guard.get("exact_replay_key_matched")),
        "stable_payload_key_matched": bool(
            guard.get("stable_payload_key_matched")),
        "fresh_operator_gate_present": bool(
            guard.get("fresh_operator_gate_present")),
        "same_payload_under_fresh_gate": bool(
            guard.get("same_payload_under_fresh_gate")),
        "existing_entry_count": guard.get("existing_entry_count"),
        "operator_gate_class": guard.get("operator_gate_class"),
        "next_allowed_action": next_action,
        # Machine-readable explanation codes (NOT prose blobs).
        "explanation_codes": _explanation_codes(guard, next_action),
        "blocked_reasons": list(guard.get("blocked_reasons") or []),
        "forbidden_fields_detected": bool(
            guard.get("forbidden_fields_detected")),
        "requires_separate_operator_send_gate": True,
        "classified_live_ready": False,
        "classified_auto_send_ready": False,
        **_safety_flags(),
    }
    console["candidate_console_checksum"] = compute_checksum(console)
    return console


def _explanation_codes(guard, next_action):
    """Return a short list of machine-readable explanation codes."""
    codes = ["next_action:" + next_action,
             "guard:" + str(guard.get("replay_guard_outcome_class"))]
    if guard.get("exact_replay_key_matched"):
        codes.append("exact_replay_key_matched")
    if guard.get("stable_payload_key_matched"):
        codes.append("stable_payload_key_matched")
    if guard.get("fresh_operator_gate_present"):
        codes.append("fresh_operator_gate_present")
    else:
        codes.append("fresh_operator_gate_absent")
    if guard.get("same_payload_under_fresh_gate"):
        codes.append("same_payload_under_fresh_gate")
    return sorted(set(codes))


# --------------------------------------------------------------------------- #
# 4. Operator console packet + doc
# --------------------------------------------------------------------------- #
def _ledger_entries_from_previous_packet(previous_ledger_packet):
    """Return the immutable entry list reconstructed from the previous packet."""
    prev = previous_ledger_packet or {}
    entry = prev.get("current_ledger_entry")
    if isinstance(entry, dict) and entry.get("ledger_entry_checksum"):
        return [entry]
    return []


def build_candidate_console_examples(previous_ledger_packet):
    """Build the four worked candidate-console examples against the prev ledger.

    Uses the committed previous ledger entry to reconstruct a matching candidate
    so the examples are realistic: (a) exact replay under the recorded gate,
    (b) same payload with NO gate, (c) same payload under a fresh distinct gate,
    (d) a genuinely new payload under a fresh gate.
    """
    entries = _ledger_entries_from_previous_packet(previous_ledger_packet)
    base_entry = entries[0] if entries else {}
    recorded_gate = base_entry.get("operator_gate_id")
    fresh_gate = "operator_console_demo_fresh_gate"

    same_candidate = candidate_from_ledger_entry(base_entry)
    # A new payload: change the send-text checksum so the stable key differs.
    new_candidate = candidate_from_ledger_entry(base_entry)
    new_candidate["send_text_checksum"] = compute_checksum({
        "kind": "console_demo_new_payload_send_text",
        "base": base_entry.get("send_text_checksum"),
    })
    new_candidate.pop("evidence_checksum", None)
    new_candidate["evidence_checksum"] = compute_checksum(new_candidate)

    return {
        "a_exact_replay_blocked": build_candidate_replay_console(
            same_candidate, entries, operator_gate_id=recorded_gate),
        "b_same_payload_without_fresh_gate": build_candidate_replay_console(
            same_candidate, entries, operator_gate_id=None),
        "c_same_payload_with_fresh_gate": build_candidate_replay_console(
            same_candidate, entries, operator_gate_id=fresh_gate),
        "d_new_payload_clear": build_candidate_replay_console(
            new_candidate, entries, operator_gate_id=fresh_gate),
    }


def build_operator_console_packet(send_proof_packet, previous_ledger_packet,
                                  accepted_send_proof_packet=None):
    """Build the deterministic operator replay-console packet (redacted)."""
    proof = send_proof_packet or {}
    accepted = accepted_send_proof_packet or {}
    reconciliation = reconcile_send_proof_with_ledger(
        send_proof_packet, previous_ledger_packet)
    ledger_view = build_operator_ledger_view(
        send_proof_packet, previous_ledger_packet, reconciliation=reconciliation)
    examples = build_candidate_console_examples(previous_ledger_packet)

    next_action = ACTION_CLEAR_FOR_MANUAL_SEND if reconciliation.get(
        "reconciled") else ACTION_BLOCKED_INVALID_CANDIDATE

    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "console_packet_schema": CONSOLE_PACKET_SCHEMA,
        "console_packet_schema_version": CONSOLE_PACKET_SCHEMA_VERSION,
        "status": adapter.Status.PASS,
        "provider": PROVIDER_TELEGRAM,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        # Current accepted proof checksums.
        "send_proof_task_label": proof.get("task_label"),
        "send_proof_evidence_checksum": proof.get("evidence_checksum"),
        "send_proof_final_evidence_checksum": proof.get(
            "final_evidence_checksum"),
        "accepted_send_proof_task_label": accepted.get("task_label"),
        "accepted_send_proof_evidence_checksum": accepted.get(
            "evidence_checksum"),
        # Reconciliation.
        "reconciliation_outcome_class": reconciliation.get(
            "reconciliation_outcome_class"),
        "reconciliation_checksum": reconciliation.get("reconciliation_checksum"),
        "reconciliation_blocked_reasons": reconciliation.get("blocked_reasons"),
        # Ledger view.
        "operator_ledger_view": ledger_view,
        "ledger_view_checksum": ledger_view.get("ledger_view_checksum"),
        "current_ledger_entry_count": ledger_view.get("ledger_entry_count"),
        "current_ledger_manifest_checksum": ledger_view.get(
            "last_ledger_manifest_checksum"),
        "previous_ledger_manifest_checksum": ledger_view.get(
            "previous_ledger_manifest_checksum"),
        # Last successful send summary (redacted).
        "last_successful_send": {
            "send_outcome_class": ledger_view.get("last_send_outcome_class"),
            "send_succeeded": ledger_view.get("last_send_succeeded"),
            "live_test_sequence": ledger_view.get("last_live_test_sequence"),
            "request_checksum": ledger_view.get("last_request_checksum"),
            "response_checksum": ledger_view.get("last_response_checksum"),
            "stable_payload_replay_key": ledger_view.get(
                "last_stable_payload_replay_key"),
            "exact_run_replay_key": ledger_view.get(
                "last_exact_run_replay_key"),
        },
        # Candidate console worked examples.
        "candidate_console_examples": {
            key: {
                "next_allowed_action": ex.get("next_allowed_action"),
                "replay_guard_outcome_class": ex.get(
                    "replay_guard_outcome_class"),
                "same_payload_under_fresh_gate": ex.get(
                    "same_payload_under_fresh_gate"),
                "exact_replay_key_matched": ex.get("exact_replay_key_matched"),
                "stable_payload_key_matched": ex.get(
                    "stable_payload_key_matched"),
                "fresh_operator_gate_present": ex.get(
                    "fresh_operator_gate_present"),
                "candidate_console_checksum": ex.get(
                    "candidate_console_checksum"),
            }
            for key, ex in examples.items()
        },
        # Decision vocab (for the future cockpit UI).
        "reconciliation_outcome_classes": list(RECONCILIATION_OUTCOME_CLASSES),
        "next_allowed_action_classes": list(NEXT_ALLOWED_ACTION_CLASSES),
        "next_recommended_action": next_action,
        "next_recommended_task": NEXT_RECOMMENDED_TASK,
        **_safety_flags(),
    }
    packet["console_packet_checksum"] = compute_checksum(packet)
    return packet


def build_operator_console_doc(packet):
    """Render a deterministic, scanner-safe markdown console doc."""
    view = packet.get("operator_ledger_view") or {}
    last = packet.get("last_successful_send") or {}
    examples = packet.get("candidate_console_examples") or {}

    def _ex_line(key):
        ex = examples.get(key) or {}
        return (f"- `{key}` -> action `{ex.get('next_allowed_action')}`, "
                f"guard `{ex.get('replay_guard_outcome_class')}`, "
                f"same_payload_under_fresh_gate "
                f"`{ex.get('same_payload_under_fresh_gate')}`\n")

    return (
        "# 0174UT/UU/UV Telegram Operator Replay Console + Ledger Reconciliation"
        "\n\n"
        f"Task: `{packet['task_label']}`\n\n"
        f"Model: `{packet['model']}` version `{packet['model_version']}`\n\n"
        "## Purpose\n\n"
        "Operator-facing, LOCAL, read-only data contract for the supervised "
        "Telegram send loop. It reconciles the most recent live send proof into "
        "the immutable ledger and reports, for any candidate, the single next "
        "allowed action. No network, API, env, or credential read; never "
        "classifies anything as live-ready.\n\n"
        "## Reconciliation\n\n"
        f"- Outcome: `{packet['reconciliation_outcome_class']}`\n"
        f"- Blocked reasons: `{packet['reconciliation_blocked_reasons']}`\n"
        f"- Previous ledger manifest: "
        f"`{packet['previous_ledger_manifest_checksum']}`\n"
        f"- Current ledger manifest: "
        f"`{packet['current_ledger_manifest_checksum']}`\n"
        f"- Current ledger entry count: "
        f"`{packet['current_ledger_entry_count']}`\n\n"
        "## Operator ledger view (redacted)\n\n"
        f"- Provider: `{view.get('provider')}`\n"
        f"- Ledger entry count: `{view.get('ledger_entry_count')}`\n"
        f"- Last ledger manifest checksum: "
        f"`{view.get('last_ledger_manifest_checksum')}`\n"
        f"- Previous ledger manifest checksum: "
        f"`{view.get('previous_ledger_manifest_checksum')}`\n"
        f"- Current ledger entry checksum: "
        f"`{view.get('current_ledger_entry_checksum')}`\n"
        f"- Previous ledger entry checksum: "
        f"`{view.get('previous_ledger_entry_checksum')}`\n"
        f"- Reconciliation status: `{view.get('reconciliation_status')}`\n\n"
        "## Last successful send (redacted)\n\n"
        f"- Send outcome class: `{last.get('send_outcome_class')}`\n"
        f"- Send succeeded: `{last.get('send_succeeded')}`\n"
        f"- Live test sequence: `{last.get('live_test_sequence')}`\n"
        f"- Request checksum: `{last.get('request_checksum')}`\n"
        f"- Response checksum: `{last.get('response_checksum')}`\n"
        f"- Stable payload replay key: "
        f"`{last.get('stable_payload_replay_key')}`\n"
        f"- Exact run replay key: `{last.get('exact_run_replay_key')}`\n\n"
        "## Candidate replay console examples\n\n"
        + _ex_line("a_exact_replay_blocked")
        + _ex_line("b_same_payload_without_fresh_gate")
        + _ex_line("c_same_payload_with_fresh_gate")
        + _ex_line("d_new_payload_clear")
        + "\n## Safety proofs\n\n"
        f"- Network performed: `{packet['network_performed']}`\n"
        f"- Telegram API called: `{packet['telegram_api_called']}`\n"
        f"- Credential read: `{packet['credential_read']}`\n"
        f"- sendMessage executed: `{packet['sendmessage_executed']}`\n"
        f"- Read-only console: `{packet['is_read_only_console']}`\n"
        f"- Stores no token: `{packet['stores_no_token']}`\n"
        f"- Stores no raw destination: `{packet['stores_no_raw_destination']}`\n"
        f"- Live ready: `{packet['live_ready']}`\n\n"
        f"## Next recommended action\n\n`{packet['next_recommended_action']}`\n\n"
        f"## Next recommended task\n\n`{packet['next_recommended_task']}`\n")


# --------------------------------------------------------------------------- #
# Packet loading + artifact writing
# --------------------------------------------------------------------------- #
def load_packet(packet_path):
    """Load a committed JSON packet, returning ``{}`` on missing/invalid file."""
    import json
    import pathlib
    path = pathlib.Path(packet_path)
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {}


def build_console_packet_from_repo(repo_root):
    """Load the committed source packets under ``repo_root`` and build the packet."""
    import pathlib
    root = pathlib.Path(repo_root)
    previous_ledger = load_packet(root / PREVIOUS_LEDGER_PACKET_REL)
    send_proof = load_packet(root / SEND_PROOF_PACKET_REL)
    accepted_proof = load_packet(root / ACCEPTED_SEND_PROOF_PACKET_REL)
    return build_operator_console_packet(
        send_proof, previous_ledger,
        accepted_send_proof_packet=accepted_proof)


def write_artifacts(base_dir, packet, doc):
    """Write the console packet + doc under ``base_dir`` ONLY if scanner-clean.

    Returns the list of written absolute paths. Raises ``RuntimeError`` if any
    scanner flags anything, so unsafe artifacts are never persisted. This is the
    ONLY function in this module that touches the filesystem.
    """
    import pathlib
    violations = scan_console(packet, doc)
    if violations:
        raise RuntimeError(
            "refusing to write console artifacts: scan found %d violation(s)"
            % len(violations))
    out_dir = pathlib.Path(base_dir) / DOC_REL_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    packet_path = out_dir / PACKET_FILENAME
    doc_path = out_dir / DOC_FILENAME
    packet_path.write_text(serialize(packet), encoding="utf-8", newline="\n")
    doc_path.write_text(doc, encoding="utf-8", newline="\n")
    return [str(packet_path), str(doc_path)]
