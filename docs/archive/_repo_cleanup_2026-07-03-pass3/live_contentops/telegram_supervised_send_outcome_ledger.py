"""Telegram supervised-send OUTCOME LEDGER + REPLAY GUARD (LOCAL, NOT LIVE).

Task 0174UN/UO/UP. This is pure, deterministic, LOCAL core code on top of the
accepted Telegram supervised-send path (0174UK/UL/UM). It builds:

  1. A deterministic, redacted LEDGER ENTRY from a supervised-send evidence
     packet -- storing ONLY symbolic/redacted classes and checksums, NEVER a
     token, raw destination, raw chat/channel id, raw response, raw URL,
     headers, cookies, username, or raw provider body.
  2. Two deterministic REPLAY KEYS derived only from redacted, non-secret
     fields: an ``exact_run_replay_key`` (binds payload + destination + request
     + credential handle + method + provider + sequence/gate) and a
     ``stable_payload_replay_key`` (same, but excludes sequence + gate) so the
     system can detect "same payload/destination/request attempted under a new
     sequence".
  3. A REPLAY GUARD decision over an existing immutable ledger, fail-closed.
  4. A pure, immutable LEDGER APPEND helper that never mutates its input and
     never appends a duplicate entry or a non-cleared entry.

HARD GUARANTEES (enforced by tests + the reused fail-closed scanner):
  * Pure Python stdlib only. NO network / API / Telegram call. NO env / .env /
    keyring / browser-session / credential read. NO ``sendMessage``.
  * Importing this module performs NO writes and NO side effects. Artifacts are
    written ONLY when ``write_artifacts(...)`` is called explicitly.
  * The ledger/guard NEVER classifies anything as ``live_ready`` or
    auto-send-ready; a clear guard only means "not a replay" and STILL requires
    a fresh operator gate for the actual (separate) send path.
"""

import os.path

# Reuse the accepted adapter's scanners + deterministic checksum/serialize and
# its symbolic redacted vocab. No risky literal is re-declared here.
from live_contentops import telegram_local_adapter_contract as adapter

TASK_LABEL = (
    "TASK_CONTENTOPS_0174UN_UO_UP_TELEGRAM_OPERATOR_SUPERVISED_SEND_"
    "OUTCOME_LEDGER_AND_REPLAY_GUARD_BATCH_V0"
)
MODEL = "TELEGRAM_SUPERVISED_SEND_OUTCOME_LEDGER_0174UN_UO_UP"
MODEL_VERSION = "0174UN_UO_UP_TELEGRAM_SUPERVISED_SEND_OUTCOME_LEDGER_V1"

LEDGER_ENTRY_SCHEMA = "contentops.telegram_supervised_send_outcome_ledger_entry"
LEDGER_ENTRY_SCHEMA_VERSION = "0174UN_UO_UP_LEDGER_ENTRY_V1"
REPLAY_GUARD_SCHEMA = "contentops.telegram_supervised_send_replay_guard_state"
REPLAY_GUARD_SCHEMA_VERSION = "0174UN_UO_UP_REPLAY_GUARD_STATE_V1"
LEDGER_MANIFEST_SCHEMA = "contentops.telegram_supervised_send_ledger_manifest"
LEDGER_MANIFEST_SCHEMA_VERSION = "0174UN_UO_UP_LEDGER_MANIFEST_V1"
LEDGER_PACKET_SCHEMA = "contentops.telegram_supervised_send_outcome_ledger_packet"
LEDGER_PACKET_SCHEMA_VERSION = "0174UN_UO_UP_LEDGER_PACKET_V1"

SOURCE_BASELINE_COMMIT = "73161c0905a7d81d7d99014922d9635cdf16b264"

DOC_REL_DIR = os.path.join("docs", "automation", "0174UN_UO_UP")
PACKET_FILENAME = "telegram_supervised_send_outcome_ledger_packet.json"
DOC_FILENAME = "telegram_supervised_send_outcome_ledger.md"

NEXT_RECOMMENDED_TASK = (
    "TASK_CONTENTOPS_0174UQ_UR_US_TELEGRAM_OPERATOR_SUPERVISED_SEND_LEDGER_"
    "BACKED_REPLAY_GUARDED_THIRD_SEND_GATE_BATCH_V0"
)

# Symbolic, deterministic timestamp placeholder (NEVER a real wall-clock value,
# so entries stay byte-for-byte deterministic for a given evidence packet).
TIMESTAMP_PLACEHOLDER_CLASS = "redacted_timestamp_placeholder_class"
OPERATOR_GATE_ABSENT_CLASS = "operator_gate_absent_class"
OPERATOR_GATE_PRESENT_CLASS = "operator_gate_present_class"

# Provider/method facts reused from the accepted adapter (symbolic only).
PROVIDER_TELEGRAM = adapter.PROVIDER_TELEGRAM
METHOD_SUPERVISED_SEND = adapter.METHOD_SUPERVISED_SEND

# Ledger-entry outcome classes.
LEDGER_ENTRY_OK = "telegram_supervised_send_ledger_entry_ok_not_live"
LEDGER_ENTRY_BLOCKED = "telegram_supervised_send_ledger_entry_blocked"
LEDGER_ENTRY_FAIL_CLOSED = (
    "telegram_supervised_send_ledger_entry_fail_closed_forbidden_value"
)

# Replay-guard decision classes (exact names mandated by the task).
REPLAY_CLEAR = "replay_guard_clear_for_new_operator_gate"
REPLAY_BLOCKED_EXACT = "replay_guard_blocked_exact_replay"
REPLAY_REQUIRES_FRESH_GATE = (
    "replay_guard_requires_fresh_operator_gate_for_same_payload"
)
REPLAY_FAIL_CLOSED = "replay_guard_fail_closed_forbidden_value"
REPLAY_BLOCKED_MISSING_EVIDENCE = (
    "replay_guard_blocked_missing_or_invalid_evidence"
)

# Append-helper status classes.
APPEND_OK = "telegram_supervised_send_ledger_append_ok_not_live"
APPEND_BLOCKED_GUARD_NOT_CLEAR = "ledger_append_blocked_replay_guard_not_clear"
APPEND_BLOCKED_DUPLICATE_ENTRY = "ledger_append_blocked_duplicate_entry_checksum"
APPEND_BLOCKED_INVALID_ENTRY = "ledger_append_blocked_invalid_entry"

# Blocked-reason classes.
BLOCK_FORBIDDEN_VALUE = "ledger_forbidden_value_detected"
BLOCK_FINANCIAL_ADVICE = "ledger_financial_advice_detected"
BLOCK_MISSING_EVIDENCE_CHECKSUM = "missing_source_evidence_checksum"
BLOCK_MISSING_REQUEST_CHECKSUM = "missing_request_checksum"
BLOCK_MISSING_RESPONSE_CHECKSUM = "missing_response_checksum"
BLOCK_MISSING_DESTINATION_BINDING_CHECKSUM = "missing_destination_binding_checksum"
BLOCK_MISSING_SEND_TEXT_CHECKSUM = "missing_send_text_checksum"
BLOCK_SOURCE_UNSAFE_BEHAVIOR = "source_evidence_unsafe_behavior_claimed"

# The redacted fields required for a valid, replay-guardable evidence packet.
REQUIRED_EVIDENCE_FIELDS = (
    ("evidence_checksum", BLOCK_MISSING_EVIDENCE_CHECKSUM),
    ("request_checksum", BLOCK_MISSING_REQUEST_CHECKSUM),
    ("response_checksum", BLOCK_MISSING_RESPONSE_CHECKSUM),
    ("destination_binding_checksum", BLOCK_MISSING_DESTINATION_BINDING_CHECKSUM),
    ("send_text_checksum", BLOCK_MISSING_SEND_TEXT_CHECKSUM),
)

# Source-evidence safety flags that, if present and not False, fail the guard.
_SOURCE_UNSAFE_FLAGS = (
    "stores_no_token",  # must be True; handled explicitly below
)


# --------------------------------------------------------------------------- #
# Scanning / serialization (reuse the accepted adapter)
# --------------------------------------------------------------------------- #
def scan_for_leaks(obj):
    """Return redaction violations for ``obj`` (delegates to the adapter)."""
    return adapter.scan_for_leaks(obj)


def scan_for_financial_advice(obj):
    """Return financial-advice violations for ``obj`` (delegates)."""
    return adapter.scan_for_financial_advice(obj)


def serialize(obj):
    """Deterministic JSON (delegates to the adapter)."""
    return adapter.serialize(obj)


def compute_checksum(obj):
    """SHA-256 of the deterministic serialization (delegates)."""
    return adapter.compute_checksum(obj)


def _safety_flags():
    """Hard invariants attached to every 0174UN/UO/UP object."""
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
        "stores_no_token": True,
        "stores_no_raw_destination": True,
        "stores_no_raw_chat_id": True,
        "stores_no_raw_response": True,
        "stores_no_raw_url": True,
        "stores_no_headers": True,
        "stores_no_cookies": True,
        "stores_no_username": True,
        "stores_no_raw_provider_body": True,
        "no_financial_advice_emitted": True,
    }


# --------------------------------------------------------------------------- #
# Replay keys (derived ONLY from redacted, non-secret fields)
# --------------------------------------------------------------------------- #
def _gate_class(operator_gate_id):
    return (OPERATOR_GATE_PRESENT_CLASS if operator_gate_id
            else OPERATOR_GATE_ABSENT_CLASS)


def compute_stable_payload_replay_key(evidence_packet):
    """Deterministic payload/destination/request key EXCLUDING sequence + gate.

    Lets the system detect "same approved payload + destination + request +
    credential handle attempted again", regardless of which supervised live
    sequence or operator gate produced it. Derived ONLY from redacted,
    non-secret fields; never a token, raw destination, raw chat id, or raw URL.
    """
    p = evidence_packet or {}
    return compute_checksum({
        "kind": "stable_payload_replay_key",
        "destination_binding_checksum": p.get("destination_binding_checksum"),
        "send_text_checksum": p.get("send_text_checksum"),
        "request_checksum": p.get("request_checksum"),
        "credential_handle_id": p.get("credential_handle_id"),
        "method_name": p.get("method_name") or METHOD_SUPERVISED_SEND,
        "provider": p.get("provider") or PROVIDER_TELEGRAM,
    })


def compute_exact_run_replay_key(evidence_packet, operator_gate_id=None):
    """Deterministic exact-run key INCLUDING sequence + operator gate.

    Two genuinely distinct supervised runs (different live_test_sequence and/or
    operator gate) produce different exact keys, while a byte-identical re-run
    of the same recorded outcome reproduces the same exact key (=> blocked as an
    exact replay). Derived ONLY from redacted, non-secret fields.
    """
    p = evidence_packet or {}
    return compute_checksum({
        "kind": "exact_run_replay_key",
        "destination_binding_checksum": p.get("destination_binding_checksum"),
        "send_text_checksum": p.get("send_text_checksum"),
        "request_checksum": p.get("request_checksum"),
        "credential_handle_id": p.get("credential_handle_id"),
        "method_name": p.get("method_name") or METHOD_SUPERVISED_SEND,
        "provider": p.get("provider") or PROVIDER_TELEGRAM,
        "live_test_sequence": p.get("live_test_sequence"),
        "operator_gate_id": operator_gate_id,
    })


def build_replay_keys(evidence_packet, operator_gate_id=None):
    """Return both deterministic replay keys for ``evidence_packet``."""
    return {
        "exact_run_replay_key": compute_exact_run_replay_key(
            evidence_packet, operator_gate_id=operator_gate_id),
        "stable_payload_replay_key": compute_stable_payload_replay_key(
            evidence_packet),
    }


# --------------------------------------------------------------------------- #
# Ledger entry model
# --------------------------------------------------------------------------- #
def _validate_evidence(evidence_packet):
    """Return ``(forbidden, missing_reasons)`` for an evidence packet."""
    p = evidence_packet or {}
    forbidden = bool(scan_for_leaks(p) or scan_for_financial_advice(p))
    missing = []
    for field, reason in REQUIRED_EVIDENCE_FIELDS:
        if not p.get(field):
            missing.append(reason)
    # Re-derive unsafe-behavior truth from the source evidence flags (R1 style):
    # a tampered packet claiming network/credential/live behavior is rejected.
    unsafe = adapter.detect_unsafe_behavior_claims(p, "source_evidence")
    if unsafe:
        missing.append(BLOCK_SOURCE_UNSAFE_BEHAVIOR)
    return forbidden, sorted(set(missing))


def build_ledger_entry(evidence_packet, operator_gate_id=None):
    """Build a deterministic, redacted ledger entry. Fail-closed.

    Returns a pure value dict. On a forbidden/leaky packet the entry is
    ``LEDGER_ENTRY_FAIL_CLOSED``; on a packet missing a required checksum it is
    ``LEDGER_ENTRY_BLOCKED``; otherwise ``LEDGER_ENTRY_OK``. The entry stores
    ONLY redacted classes + checksums and NEVER a token, raw destination, raw
    chat id, raw response, raw URL, headers, cookies, username, or raw body.
    """
    p = evidence_packet or {}
    forbidden, missing = _validate_evidence(p)

    if forbidden:
        outcome = LEDGER_ENTRY_FAIL_CLOSED
        status = adapter.Status.FAIL_CLOSED
        blocked = [BLOCK_FORBIDDEN_VALUE]
    elif missing:
        outcome = LEDGER_ENTRY_BLOCKED
        status = adapter.Status.BLOCKED
        blocked = list(missing)
    else:
        outcome = LEDGER_ENTRY_OK
        status = adapter.Status.PASS
        blocked = []

    keys = build_replay_keys(p, operator_gate_id=operator_gate_id)
    entry = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "ledger_entry_schema": LEDGER_ENTRY_SCHEMA,
        "ledger_entry_schema_version": LEDGER_ENTRY_SCHEMA_VERSION,
        "status": status,
        "ledger_entry_outcome_class": outcome,
        "ledger_entry_ok": outcome == LEDGER_ENTRY_OK,
        "provider": p.get("provider") or PROVIDER_TELEGRAM,
        # Redacted source-evidence references (NO raw secrets).
        "source_task_label": p.get("task_label"),
        "source_evidence_checksum": p.get("evidence_checksum"),
        "send_outcome_class": p.get("send_outcome_class"),
        "send_succeeded": bool(p.get("send_succeeded")),
        "live_test_sequence": p.get("live_test_sequence"),
        "credential_source_class": p.get("credential_source_class"),
        "destination_source_class": p.get("destination_source_class"),
        "destination_binding_checksum": p.get("destination_binding_checksum"),
        "request_checksum": p.get("request_checksum"),
        "response_checksum": p.get("response_checksum"),
        "response_shape_checksum": p.get("response_shape_checksum"),
        "send_text_checksum": p.get("send_text_checksum"),
        "credential_handle_id": p.get("credential_handle_id"),
        "redacted_message_id_class": p.get("redacted_message_id_class"),
        "provider_status_code_class": p.get("provider_status_code_class"),
        "response_status_class": p.get("response_status_class"),
        "request_budget_used": p.get("request_budget_used"),
        "method_name": p.get("method_name") or METHOD_SUPERVISED_SEND,
        # Time is symbolic + deterministic (never a wall-clock value).
        "timestamp_placeholder_class": TIMESTAMP_PLACEHOLDER_CLASS,
        # Operator gate (id if supplied, plus a symbolic class).
        "operator_gate_id": operator_gate_id,
        "operator_gate_class": _gate_class(operator_gate_id),
        # Replay keys carried on the entry for future comparisons.
        "exact_run_replay_key": keys["exact_run_replay_key"],
        "stable_payload_replay_key": keys["stable_payload_replay_key"],
        "blocked_reasons": blocked,
        "forbidden_fields_detected": forbidden,
        **_safety_flags(),
    }
    entry["ledger_entry_checksum"] = compute_checksum(entry)
    return entry


def _entry_is_ok(entry):
    e = entry or {}
    return (
        e.get("ledger_entry_outcome_class") == LEDGER_ENTRY_OK
        and e.get("ledger_entry_ok") is True
        and e.get("status") == adapter.Status.PASS
        and bool(e.get("ledger_entry_checksum"))
    )


# --------------------------------------------------------------------------- #
# Replay guard decision
# --------------------------------------------------------------------------- #
def build_replay_guard_state(existing_ledger_entries, candidate_evidence_packet,
                             operator_gate_id=None):
    """Decide whether a candidate supervised send is a replay. Fail-closed.

    Rules (in order):
      * forbidden / leaky candidate => ``replay_guard_fail_closed_forbidden_value``;
      * missing required checksum => ``replay_guard_blocked_missing_or_invalid_evidence``;
      * exact_run_replay_key already in the ledger => ``replay_guard_blocked_exact_replay``;
      * stable_payload_replay_key present but NO fresh operator gate =>
        ``replay_guard_requires_fresh_operator_gate_for_same_payload``;
      * stable_payload_replay_key present WITH a fresh operator gate => clear,
        flagged ``same_payload_under_fresh_gate=true``;
      * otherwise (new payload) => ``replay_guard_clear_for_new_operator_gate``.

    NEVER classifies anything as live-ready or auto-send-ready: a clear result
    only means "not a replay" and still requires the separate operator send gate.
    """
    entries = list(existing_ledger_entries or [])
    p = candidate_evidence_packet or {}
    forbidden, missing = _validate_evidence(p)

    keys = build_replay_keys(p, operator_gate_id=operator_gate_id)
    exact_key = keys["exact_run_replay_key"]
    stable_key = keys["stable_payload_replay_key"]

    existing_exact = {e.get("exact_run_replay_key") for e in entries
                      if isinstance(e, dict)}
    existing_stable = {e.get("stable_payload_replay_key") for e in entries
                       if isinstance(e, dict)}

    fresh_gate_present = bool(operator_gate_id)
    same_payload_under_fresh_gate = False
    blocked = []

    if forbidden:
        outcome = REPLAY_FAIL_CLOSED
        status = adapter.Status.FAIL_CLOSED
        blocked = [BLOCK_FORBIDDEN_VALUE]
        clear = False
    elif missing:
        outcome = REPLAY_BLOCKED_MISSING_EVIDENCE
        status = adapter.Status.BLOCKED
        blocked = list(missing)
        clear = False
    elif exact_key in existing_exact:
        outcome = REPLAY_BLOCKED_EXACT
        status = adapter.Status.BLOCKED
        clear = False
    elif stable_key in existing_stable and not fresh_gate_present:
        outcome = REPLAY_REQUIRES_FRESH_GATE
        status = adapter.Status.BLOCKED
        clear = False
    elif stable_key in existing_stable and fresh_gate_present:
        outcome = REPLAY_CLEAR
        status = adapter.Status.PASS
        clear = True
        same_payload_under_fresh_gate = True
    else:
        outcome = REPLAY_CLEAR
        status = adapter.Status.PASS
        clear = True

    state = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "replay_guard_schema": REPLAY_GUARD_SCHEMA,
        "replay_guard_schema_version": REPLAY_GUARD_SCHEMA_VERSION,
        "status": status,
        "replay_guard_outcome_class": outcome,
        "replay_guard_clear": clear,
        "provider": p.get("provider") or PROVIDER_TELEGRAM,
        "exact_run_replay_key": exact_key,
        "stable_payload_replay_key": stable_key,
        "operator_gate_id": operator_gate_id,
        "operator_gate_class": _gate_class(operator_gate_id),
        "fresh_operator_gate_present": fresh_gate_present,
        "same_payload_under_fresh_gate": same_payload_under_fresh_gate,
        "existing_entry_count": len(entries),
        "exact_replay_key_matched": exact_key in existing_exact,
        "stable_payload_key_matched": stable_key in existing_stable,
        "blocked_reasons": sorted(set(blocked)),
        "forbidden_fields_detected": forbidden,
        # Explicit non-live invariants.
        "classified_live_ready": False,
        "classified_auto_send_ready": False,
        "requires_separate_operator_send_gate": True,
        **_safety_flags(),
    }
    state["replay_guard_state_checksum"] = compute_checksum(state)
    return state


def _guard_is_clear(replay_guard_state):
    s = replay_guard_state or {}
    return (
        s.get("replay_guard_outcome_class") == REPLAY_CLEAR
        and s.get("replay_guard_clear") is True
        and s.get("status") == adapter.Status.PASS
    )


# --------------------------------------------------------------------------- #
# Immutable ledger append helper
# --------------------------------------------------------------------------- #
def compute_ledger_manifest_checksum(ledger_entries):
    """Deterministic manifest checksum over an ordered list of entries."""
    return compute_checksum({
        "ledger_manifest_schema": LEDGER_MANIFEST_SCHEMA,
        "ledger_manifest_schema_version": LEDGER_MANIFEST_SCHEMA_VERSION,
        "entry_count": len(ledger_entries or []),
        "entry_checksums": [
            (e or {}).get("ledger_entry_checksum")
            for e in (ledger_entries or [])
        ],
    })


def append_ledger_entry(existing_ledger, entry, replay_guard_state):
    """Pure, immutable append. NEVER mutates ``existing_ledger``.

    Appends ``entry`` ONLY when the replay guard is clear, the entry is a valid
    OK entry, and its ``ledger_entry_checksum`` is not already present. Returns
    a dict with ``append_status_class``, the resulting immutable ``ledger`` list
    (a new list), the ``ledger_manifest_checksum``, an ``appended`` boolean, and
    ``blocked_reasons``.
    """
    original = list(existing_ledger or [])
    entry = entry or {}
    blocked = []

    if not _guard_is_clear(replay_guard_state):
        blocked.append(APPEND_BLOCKED_GUARD_NOT_CLEAR)
    if not _entry_is_ok(entry):
        blocked.append(APPEND_BLOCKED_INVALID_ENTRY)

    entry_checksum = entry.get("ledger_entry_checksum")
    existing_checksums = {(e or {}).get("ledger_entry_checksum")
                          for e in original}
    is_duplicate = bool(entry_checksum) and entry_checksum in existing_checksums
    if is_duplicate:
        blocked.append(APPEND_BLOCKED_DUPLICATE_ENTRY)

    if blocked:
        # Do NOT append. Return the original list unchanged (a fresh copy).
        new_ledger = list(original)
        appended = False
        status_class = sorted(set(blocked))[0]
        status = adapter.Status.BLOCKED
    else:
        new_ledger = list(original) + [entry]
        appended = True
        status_class = APPEND_OK
        status = adapter.Status.PASS

    return {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "status": status,
        "append_status_class": status_class,
        "appended": appended,
        "ledger": new_ledger,
        "ledger_entry_count": len(new_ledger),
        "ledger_manifest_checksum": compute_ledger_manifest_checksum(new_ledger),
        "is_duplicate_entry": is_duplicate,
        "input_ledger_unchanged": True,
        "blocked_reasons": sorted(set(blocked)),
        **_safety_flags(),
    }


# --------------------------------------------------------------------------- #
# Ledger packet + doc (deterministic, scanner-clean)
# --------------------------------------------------------------------------- #
def build_ledger_packet(accepted_evidence_packet, *, operator_gate_id=None,
                        existing_ledger_entries=None):
    """Summarize the current accepted send as a ledger entry + replay policy.

    Builds the ledger entry from the accepted evidence packet, computes the
    replay-guard state for re-submitting the SAME packet (which must NOT be a
    fresh distinct run), appends into a fresh empty ledger, and records the
    replay policy. Contains ONLY redacted material.
    """
    existing = list(existing_ledger_entries or [])
    entry = build_ledger_entry(accepted_evidence_packet,
                               operator_gate_id=operator_gate_id)
    # Appending the accepted entry into the (initially empty) ledger.
    seed_guard = build_replay_guard_state(
        existing, accepted_evidence_packet, operator_gate_id=operator_gate_id)
    seed_append = append_ledger_entry(existing, entry, seed_guard)
    ledger_after = seed_append["ledger"]

    # Demonstrate the replay decisions as policy facts (no new entries kept):
    #   * exact re-submit of the SAME recorded run => blocked exact replay.
    exact_replay_guard = build_replay_guard_state(
        ledger_after, accepted_evidence_packet,
        operator_gate_id=operator_gate_id)
    #   * same payload WITHOUT a fresh gate => requires fresh operator gate.
    same_payload_no_gate_guard = build_replay_guard_state(
        ledger_after, accepted_evidence_packet, operator_gate_id=None)

    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "ledger_packet_schema": LEDGER_PACKET_SCHEMA,
        "ledger_packet_schema_version": LEDGER_PACKET_SCHEMA_VERSION,
        "status": adapter.Status.PASS,
        "provider": PROVIDER_TELEGRAM,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "accepted_source_task_label": (accepted_evidence_packet or {}).get(
            "task_label"),
        "accepted_source_evidence_checksum": (accepted_evidence_packet or {}).get(
            "evidence_checksum"),
        "current_ledger_entry": entry,
        "current_ledger_entry_checksum": entry.get("ledger_entry_checksum"),
        "exact_run_replay_key": entry.get("exact_run_replay_key"),
        "stable_payload_replay_key": entry.get("stable_payload_replay_key"),
        "seed_append_status_class": seed_append["append_status_class"],
        "ledger_manifest_checksum": seed_append["ledger_manifest_checksum"],
        "ledger_entry_count": seed_append["ledger_entry_count"],
        # Replay policy facts.
        "replay_policy": {
            "exact_resubmit_outcome_class": exact_replay_guard[
                "replay_guard_outcome_class"],
            "same_payload_without_fresh_gate_outcome_class":
                same_payload_no_gate_guard["replay_guard_outcome_class"],
            "clear_requires_new_distinct_run_or_fresh_gate": True,
            "never_classifies_live_ready": True,
            "never_classifies_auto_send_ready": True,
        },
        "replay_decision_classes": [
            REPLAY_CLEAR,
            REPLAY_BLOCKED_EXACT,
            REPLAY_REQUIRES_FRESH_GATE,
            REPLAY_FAIL_CLOSED,
            REPLAY_BLOCKED_MISSING_EVIDENCE,
        ],
        "next_recommended_task": NEXT_RECOMMENDED_TASK,
        **_safety_flags(),
    }
    packet["ledger_packet_checksum"] = compute_checksum(packet)
    return packet


def build_ledger_doc(packet):
    """Render a deterministic, scanner-safe markdown doc for the packet."""
    entry = packet.get("current_ledger_entry") or {}
    policy = packet.get("replay_policy") or {}
    return (
        "# 0174UN/UO/UP Telegram Supervised Send Outcome Ledger + Replay Guard\n\n"
        f"Task: `{packet['task_label']}`\n\n"
        f"Model: `{packet['model']}` version `{packet['model_version']}`\n\n"
        "## Purpose\n\n"
        "Redacted immutable outcome ledger + replay guard for the supervised "
        "Telegram `sendMessage` path. Prevents accidental replay of the same "
        "approved payload/destination/request without a fresh operator gate. "
        "This is LOCAL only: no network, API, env, or credential read, and it "
        "NEVER classifies anything as live-ready or auto-send-ready.\n\n"
        "## Current accepted ledger entry (redacted)\n\n"
        f"- Source task: `{entry.get('source_task_label')}`\n"
        f"- Source evidence checksum: `{entry.get('source_evidence_checksum')}`\n"
        f"- Send outcome class: `{entry.get('send_outcome_class')}`\n"
        f"- Send succeeded: `{entry.get('send_succeeded')}`\n"
        f"- Live test sequence: `{entry.get('live_test_sequence')}`\n"
        f"- Credential source class: `{entry.get('credential_source_class')}`\n"
        f"- Destination source class: `{entry.get('destination_source_class')}`\n"
        f"- Destination binding checksum: "
        f"`{entry.get('destination_binding_checksum')}`\n"
        f"- Request checksum: `{entry.get('request_checksum')}`\n"
        f"- Response checksum: `{entry.get('response_checksum')}`\n"
        f"- Response shape checksum: `{entry.get('response_shape_checksum')}`\n"
        f"- Redacted message id class: "
        f"`{entry.get('redacted_message_id_class')}`\n"
        f"- Provider status code class: "
        f"`{entry.get('provider_status_code_class')}`\n"
        f"- Response status class: `{entry.get('response_status_class')}`\n"
        f"- Request budget used: `{entry.get('request_budget_used')}`\n"
        f"- Timestamp placeholder class: "
        f"`{entry.get('timestamp_placeholder_class')}`\n"
        f"- Operator gate class: `{entry.get('operator_gate_class')}`\n"
        f"- Ledger entry checksum: `{entry.get('ledger_entry_checksum')}`\n\n"
        "## Replay keys\n\n"
        f"- Exact run replay key: `{packet.get('exact_run_replay_key')}`\n"
        f"- Stable payload replay key: "
        f"`{packet.get('stable_payload_replay_key')}`\n\n"
        "## Replay policy\n\n"
        f"- Exact re-submit outcome: "
        f"`{policy.get('exact_resubmit_outcome_class')}`\n"
        f"- Same payload without fresh gate outcome: "
        f"`{policy.get('same_payload_without_fresh_gate_outcome_class')}`\n"
        f"- Never classifies live ready: "
        f"`{policy.get('never_classifies_live_ready')}`\n"
        f"- Never classifies auto-send ready: "
        f"`{policy.get('never_classifies_auto_send_ready')}`\n\n"
        "## Ledger manifest\n\n"
        f"- Ledger entry count: `{packet.get('ledger_entry_count')}`\n"
        f"- Ledger manifest checksum: "
        f"`{packet.get('ledger_manifest_checksum')}`\n"
        f"- Ledger packet checksum: `{packet.get('ledger_packet_checksum')}`\n\n"
        "## Safety proofs\n\n"
        f"- Network performed: `{packet.get('network_performed')}`\n"
        f"- Telegram API called: `{packet.get('telegram_api_called')}`\n"
        f"- Credential read: `{packet.get('credential_read')}`\n"
        f"- sendMessage executed: `{packet.get('sendmessage_executed')}`\n"
        f"- Stores no token: `{packet.get('stores_no_token')}`\n"
        f"- Stores no raw destination: "
        f"`{packet.get('stores_no_raw_destination')}`\n"
        f"- Stores no raw response: `{packet.get('stores_no_raw_response')}`\n"
        f"- Stores no raw URL: `{packet.get('stores_no_raw_url')}`\n"
        f"- Stores no headers: `{packet.get('stores_no_headers')}`\n"
        f"- Stores no cookies: `{packet.get('stores_no_cookies')}`\n"
        f"- Live ready: `{packet.get('live_ready')}`\n\n"
        f"## Next recommended task\n\n`{packet.get('next_recommended_task')}`\n")


def scan_packet_and_doc(packet, doc):
    """Return the combined redaction + financial-advice violations."""
    return (scan_for_leaks(packet) + scan_for_leaks(doc)
            + scan_for_financial_advice(packet)
            + scan_for_financial_advice(doc))


def write_artifacts(base_dir, packet, doc):
    """Write the ledger packet + doc under ``base_dir`` ONLY if scanner-clean.

    Returns the list of written absolute paths. Raises ``RuntimeError`` if any
    scanner flags anything, so unsafe artifacts are never persisted. This is the
    ONLY function in this module that touches the filesystem.
    """
    import pathlib
    violations = scan_packet_and_doc(packet, doc)
    if violations:
        raise RuntimeError(
            "refusing to write ledger artifacts: scan found %d violation(s)"
            % len(violations))
    out_dir = pathlib.Path(base_dir) / DOC_REL_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    packet_path = out_dir / PACKET_FILENAME
    doc_path = out_dir / DOC_FILENAME
    packet_path.write_text(serialize(packet), encoding="utf-8", newline="\n")
    doc_path.write_text(doc, encoding="utf-8", newline="\n")
    return [str(packet_path), str(doc_path)]
