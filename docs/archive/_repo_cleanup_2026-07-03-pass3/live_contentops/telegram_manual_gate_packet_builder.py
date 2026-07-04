"""Telegram supervised-send MANUAL GATE PACKET BUILDER + OPERATOR APPROVAL CAPTURE.

Task 0174VC/VD/VE. The next backend step after the static cockpit render
(0174UZ). The cockpit can render a "Prepare manual gate packet" affordance; this
module builds the ACTUAL redacted packet structure an operator must approve
before any future live supervised-send gate, and captures that approval as a
deterministic, redacted contract.

AUTHORITY MODEL (per the master plan): the deterministic LOCAL gate is the
dispatch authority. This module is LOCAL ONLY. It performs NO dispatch, NO
network, NO Telegram call, NO ``.env`` / env / credential read, and NO
``sendMessage``. A captured approval STILL does not dispatch and is NEVER
classified live-ready / auto-send-ready / valid-for-live-execution; it only
hands off to a SEPARATE operator send runner that must re-gate at send time.

It binds, for a candidate supervised send:
  * candidate evidence / request / send-text / destination-binding checksums;
  * the two redacted replay keys (stable payload + exact run);
  * the replay-guard outcome and the next-send precheck outcome (reusing the
    accepted read-model / replay-console / ledger modules);
  * a fresh operator gate id HASH + class (never the raw gate id);
  * the operator approval (approved flag, gate hash, symbolic note class,
    symbolic timestamp placeholder class, approved-payload + destination-binding
    checksums) -- never a raw note, raw gate id, token, destination, response,
    url, header, or cookie.

Importing this module performs NO writes and NO side effects. Artifacts are
written ONLY when ``write_artifacts(...)`` is called explicitly and the content
passes the reused fail-closed redaction + financial-advice scanners.
"""

import os.path
import re

# Reuse the accepted render / read-model / replay-console / ledger modules (and,
# through them, the adapter scanners + deterministic serialization/checksum +
# the redacted symbolic vocab). No risky literal is re-declared here.
from live_contentops import telegram_operator_cockpit_html_render as render
from live_contentops import telegram_operator_cockpit_read_model as readmodel
from live_contentops import telegram_operator_replay_console as console
from live_contentops import telegram_supervised_send_outcome_ledger as ledger

TASK_LABEL = (
    "TASK_CONTENTOPS_0174VC_VD_VE_TELEGRAM_MANUAL_GATE_PACKET_BUILDER_AND_"
    "OPERATOR_APPROVAL_CAPTURE_BATCH_V0"
)
MODEL = "TELEGRAM_MANUAL_GATE_PACKET_BUILDER_0174VC_VD_VE"
MODEL_VERSION = "0174VC_VD_VE_TELEGRAM_MANUAL_GATE_PACKET_BUILDER_V1"

CANDIDATE_SCHEMA = "contentops.telegram_manual_gate_candidate_packet"
CANDIDATE_SCHEMA_VERSION = "0174VC_VD_VE_MANUAL_GATE_CANDIDATE_V1"
APPROVAL_SCHEMA = "contentops.telegram_operator_approval_capture"
APPROVAL_SCHEMA_VERSION = "0174VC_VD_VE_OPERATOR_APPROVAL_CAPTURE_V1"
MANUAL_GATE_PACKET_SCHEMA = "contentops.telegram_manual_gate_packet"
MANUAL_GATE_PACKET_SCHEMA_VERSION = "0174VC_VD_VE_MANUAL_GATE_PACKET_V1"
ARTIFACT_PACKET_SCHEMA = "contentops.telegram_manual_gate_packet_builder_packet"
ARTIFACT_PACKET_SCHEMA_VERSION = "0174VC_VD_VE_MANUAL_GATE_BUILDER_PACKET_V1"

SOURCE_BASELINE_COMMIT = "9f6735b33208ccdfd015226b4fa08a5589aa4346"

DOC_REL_DIR = os.path.join("docs", "automation", "0174VC_VD_VE")
PACKET_FILENAME = "telegram_manual_gate_packet_builder_packet.json"
DOC_FILENAME = "telegram_manual_gate_packet_builder.md"

# Committed source packets (read-only) used by the repo-driven artifact builder.
RENDER_PACKET_REL = os.path.join(
    "docs", "automation", "0174UZ_VA_VB",
    "telegram_operator_cockpit_render_packet.json")
CONSOLE_PACKET_REL = os.path.join(
    "docs", "automation", "0174UT_UU_UV",
    "telegram_operator_replay_console_packet.json")

NEXT_RECOMMENDED_TASK = (
    "TASK_CONTENTOPS_0174VF_VG_VH_TELEGRAM_APPROVED_MANUAL_GATE_BACKED_FOURTH_"
    "SUPERVISED_SEND_RUNNER_BATCH_V0"
)

PROVIDER_TELEGRAM = readmodel.PROVIDER_TELEGRAM
METHOD_SUPERVISED_SEND = ledger.METHOD_SUPERVISED_SEND

# --------------------------------------------------------------------------- #
# Manual-gate candidate outcome classes
# --------------------------------------------------------------------------- #
CANDIDATE_WAITING = "manual_gate_candidate_waiting_for_candidate"
CANDIDATE_PRECHECK_CLEAR = "manual_gate_candidate_precheck_clear_for_approval"
CANDIDATE_BLOCKED = "manual_gate_candidate_blocked"
CANDIDATE_FAIL_CLOSED = "manual_gate_candidate_fail_closed_forbidden_value"

CANDIDATE_OUTCOME_CLASSES = (
    CANDIDATE_WAITING,
    CANDIDATE_PRECHECK_CLEAR,
    CANDIDATE_BLOCKED,
    CANDIDATE_FAIL_CLOSED,
)

# Machine-readable candidate blocker codes (NOT prose).
BLOCKER_MISSING_CANDIDATE = "manual_gate_blocker_missing_candidate"
BLOCKER_EXACT_REPLAY = "manual_gate_blocker_exact_replay"
BLOCKER_REQUIRES_FRESH_GATE = "manual_gate_blocker_requires_fresh_operator_gate"
BLOCKER_UNRECONCILED_LEDGER = "manual_gate_blocker_unreconciled_ledger"
BLOCKER_FORBIDDEN_VALUE = "manual_gate_blocker_forbidden_value"

# Deterministic map from precheck outcome -> (candidate outcome, blockers).
_PRECHECK_TO_CANDIDATE = {
    readmodel.PRECHECK_CLEAR: (CANDIDATE_PRECHECK_CLEAR, []),
    readmodel.PRECHECK_REQUIRES_FRESH_GATE: (
        CANDIDATE_BLOCKED, [BLOCKER_REQUIRES_FRESH_GATE]),
    readmodel.PRECHECK_BLOCKED_EXACT_REPLAY: (
        CANDIDATE_BLOCKED, [BLOCKER_EXACT_REPLAY]),
    readmodel.PRECHECK_BLOCKED_MISSING_CANDIDATE: (
        CANDIDATE_WAITING, [BLOCKER_MISSING_CANDIDATE]),
    readmodel.PRECHECK_BLOCKED_UNRECONCILED: (
        CANDIDATE_BLOCKED, [BLOCKER_UNRECONCILED_LEDGER]),
    readmodel.PRECHECK_FAIL_CLOSED: (
        CANDIDATE_FAIL_CLOSED, [BLOCKER_FORBIDDEN_VALUE]),
}

# --------------------------------------------------------------------------- #
# Operator-approval outcome classes (exact names mandated by the task)
# --------------------------------------------------------------------------- #
APPROVAL_WAITING = "operator_approval_waiting"
APPROVAL_CAPTURED = "operator_approval_captured"
APPROVAL_BLOCKED_MISSING_GATE = "operator_approval_blocked_missing_gate"
APPROVAL_BLOCKED_PAYLOAD_MISMATCH = (
    "operator_approval_blocked_payload_checksum_mismatch")
APPROVAL_BLOCKED_DESTINATION_MISMATCH = (
    "operator_approval_blocked_destination_binding_mismatch")
APPROVAL_BLOCKED_PRECHECK_NOT_CLEAR = (
    "operator_approval_blocked_precheck_not_clear")
APPROVAL_FAIL_CLOSED = "operator_approval_fail_closed_forbidden_value"

APPROVAL_OUTCOME_CLASSES = (
    APPROVAL_WAITING,
    APPROVAL_CAPTURED,
    APPROVAL_BLOCKED_MISSING_GATE,
    APPROVAL_BLOCKED_PAYLOAD_MISMATCH,
    APPROVAL_BLOCKED_DESTINATION_MISMATCH,
    APPROVAL_BLOCKED_PRECHECK_NOT_CLEAR,
    APPROVAL_FAIL_CLOSED,
)

# --------------------------------------------------------------------------- #
# Manual-gate packet allowed-next-step classes (exact names mandated)
# --------------------------------------------------------------------------- #
NEXT_STEP_WAITING_FOR_CANDIDATE = "manual_gate_waiting_for_candidate"
NEXT_STEP_WAITING_FOR_APPROVAL = "manual_gate_waiting_for_operator_approval"
NEXT_STEP_BLOCKED = "manual_gate_blocked"
NEXT_STEP_APPROVED_FOR_RUNNER = "manual_gate_approved_for_separate_send_runner"

ALLOWED_NEXT_STEPS = (
    NEXT_STEP_WAITING_FOR_CANDIDATE,
    NEXT_STEP_WAITING_FOR_APPROVAL,
    NEXT_STEP_BLOCKED,
    NEXT_STEP_APPROVED_FOR_RUNNER,
)

# Symbolic redacted classes (never raw operator text / ids).
OPERATOR_GATE_ABSENT_CLASS = "operator_gate_absent_class"
OPERATOR_GATE_PRESENT_CLASS = "operator_gate_present_class"
DEFAULT_NOTE_CLASS = "operator_note_present_redacted_class"
DEFAULT_TIMESTAMP_CLASS = "operator_approval_timestamp_placeholder_class"

# A safe symbolic class token: lowercase letters / digits / underscore only.
_SAFE_SYMBOL_RE = re.compile(r"^[a-z0-9_]{1,80}$")


# --------------------------------------------------------------------------- #
# Scanning / serialization (reuse the accepted scanners)
# --------------------------------------------------------------------------- #
def scan_for_leaks(obj):
    """Return redaction violations for ``obj`` (delegates)."""
    return render.scan_for_leaks(obj)


def scan_for_financial_advice(obj):
    """Return financial-advice violations for ``obj`` (delegates)."""
    return render.scan_for_financial_advice(obj)


def serialize(obj):
    """Deterministic JSON (delegates)."""
    return render.serialize(obj)


def compute_checksum(obj):
    """SHA-256 of the deterministic serialization (delegates)."""
    return render.compute_checksum(obj)


def scan_manual_gate(packet, doc):
    """Return the combined redaction + financial-advice violations."""
    return (scan_for_leaks(packet) + scan_for_leaks(doc)
            + scan_for_financial_advice(packet)
            + scan_for_financial_advice(doc))


def _safety_flags():
    """Hard non-live invariants attached to every 0174VC/VD/VE object."""
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
        "webhook_or_polling_enabled": False,
        "live_ready": False,
        "auto_send_ready": False,
        "valid_for_live_execution": False,
        "is_local_only": True,
        "is_manual_gate_contract": True,
        "requires_separate_operator_send_gate": True,
        "stores_no_token": True,
        "stores_no_raw_destination": True,
        "stores_no_raw_chat_id": True,
        "stores_no_raw_response": True,
        "stores_no_raw_url": True,
        "stores_no_headers": True,
        "stores_no_cookies": True,
        "stores_no_username": True,
        "stores_no_raw_operator_gate_id": True,
        "stores_no_raw_approval_note": True,
        "no_financial_advice_emitted": True,
    }


# --------------------------------------------------------------------------- #
# Symbolic helpers (never echo raw operator text / gate ids)
# --------------------------------------------------------------------------- #
def _gate_class(gate_id):
    return OPERATOR_GATE_PRESENT_CLASS if gate_id else OPERATOR_GATE_ABSENT_CLASS


def _gate_id_hash(gate_id):
    """Deterministic hash of an operator gate id (never the raw id)."""
    if not gate_id:
        return None
    return compute_checksum({
        "kind": "operator_gate_id_hash",
        "operator_gate_id": gate_id,
    })


def _safe_symbolic_class(value, default):
    """Pass through a safe symbolic class token, else fall back to ``default``.

    Guarantees the stored value is a short, lowercase, token-only symbol so no
    raw operator prose / url / id can leak through a "class" field.
    """
    if value is None:
        return default
    s = str(value)
    if _SAFE_SYMBOL_RE.match(s):
        return s
    return default


# --------------------------------------------------------------------------- #
# 1. Manual gate candidate packet
# --------------------------------------------------------------------------- #
def build_manual_gate_candidate_packet(cockpit_render_packet,
                                       candidate_evidence_packet=None,
                                       fresh_operator_gate_id=None,
                                       console_packet=None):
    """Build the redacted manual-gate CANDIDATE packet the operator must approve.

    Binds the candidate evidence to the cockpit render packet + the accepted
    read-model next-send precheck (run against the committed replay-console
    ledger context). When no candidate is supplied the packet is the default
    ``manual_gate_candidate_waiting_for_candidate`` state with the
    ``manual_gate_blocker_missing_candidate`` blocker; never dispatch, never
    live-ready, never send-ready.

    ``console_packet`` provides the reconciled ledger context for the precheck.
    When omitted it is loaded from the committed 0174UT replay-console packet so
    the default no-candidate state reconciles correctly.
    """
    rp = cockpit_render_packet or {}
    cp = console_packet if console_packet is not None else _load_committed_console_packet()

    # Fail-closed if any input is forbidden/leaky before doing anything else.
    forbidden = bool(
        scan_for_leaks(rp) or scan_for_financial_advice(rp)
        or scan_for_leaks(cp) or scan_for_financial_advice(cp))
    if candidate_evidence_packet is not None:
        forbidden = forbidden or bool(
            scan_for_leaks(candidate_evidence_packet)
            or scan_for_financial_advice(candidate_evidence_packet))

    precheck = readmodel.build_next_send_precheck(
        cp, candidate=candidate_evidence_packet,
        fresh_operator_gate_id=fresh_operator_gate_id)
    precheck_outcome = precheck.get("precheck_outcome_class")

    if forbidden:
        candidate_outcome = CANDIDATE_FAIL_CLOSED
        blockers = [BLOCKER_FORBIDDEN_VALUE]
    elif candidate_evidence_packet is None:
        candidate_outcome = CANDIDATE_WAITING
        blockers = [BLOCKER_MISSING_CANDIDATE]
    else:
        candidate_outcome, blockers = _PRECHECK_TO_CANDIDATE.get(
            precheck_outcome, (CANDIDATE_BLOCKED, [BLOCKER_MISSING_CANDIDATE]))
        blockers = list(blockers)

    # Candidate-derived redacted checksums + replay keys (never raw material).
    cand = candidate_evidence_packet or {}
    keys = (ledger.build_replay_keys(cand, operator_gate_id=fresh_operator_gate_id)
            if candidate_evidence_packet is not None else
            {"exact_run_replay_key": None, "stable_payload_replay_key": None})

    candidate_send_text_checksum = cand.get("send_text_checksum")

    status = (render.readmodel.console.adapter.Status.PASS
              if candidate_outcome == CANDIDATE_PRECHECK_CLEAR
              else (render.readmodel.console.adapter.Status.FAIL_CLOSED
                    if candidate_outcome == CANDIDATE_FAIL_CLOSED
                    else render.readmodel.console.adapter.Status.BLOCKED))

    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "candidate_schema": CANDIDATE_SCHEMA,
        "candidate_schema_version": CANDIDATE_SCHEMA_VERSION,
        "status": status,
        "provider": rp.get("provider") or cp.get("provider") or PROVIDER_TELEGRAM,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        # Binding to the cockpit render + upstream read model / console.
        "source_cockpit_render_checksum": rp.get("render_packet_checksum"),
        "source_render_model_checksum": rp.get("render_model_checksum"),
        "source_read_model_checksum": rp.get("source_read_model_checksum"),
        "source_handoff_contract_checksum": rp.get("handoff_contract_checksum"),
        "source_replay_console_checksum": cp.get("console_packet_checksum"),
        "source_reconciliation_outcome_class": cp.get(
            "reconciliation_outcome_class"),
        # Candidate facts (redacted classes / checksums only).
        "candidate_present": candidate_evidence_packet is not None,
        "manual_gate_candidate_outcome_class": candidate_outcome,
        "candidate_evidence_checksum": cand.get("evidence_checksum"),
        "candidate_request_checksum": cand.get("request_checksum"),
        "candidate_send_text_checksum": candidate_send_text_checksum,
        "destination_binding_checksum": cand.get("destination_binding_checksum"),
        "credential_handle_id": cand.get("credential_handle_id"),
        "live_test_sequence": cand.get("live_test_sequence"),
        "stable_payload_replay_key": keys.get("stable_payload_replay_key"),
        "exact_run_replay_key": keys.get("exact_run_replay_key"),
        # Precheck / replay-guard outcomes (from the accepted read-model module).
        "replay_guard_outcome_class": precheck.get(
            "candidate_replay_guard_outcome_class"),
        "next_send_precheck_outcome_class": precheck_outcome,
        "next_send_precheck_checksum": precheck.get("precheck_checksum"),
        "precheck_clear_for_manual_gate": (
            precheck_outcome == readmodel.PRECHECK_CLEAR),
        # Operator gate (hash + class only; never the raw id).
        "fresh_operator_gate_id_hash": _gate_id_hash(fresh_operator_gate_id),
        "fresh_operator_gate_class": _gate_class(fresh_operator_gate_id),
        "fresh_operator_gate_present": bool(fresh_operator_gate_id),
        # The approved payload checksum the operator must echo at approval time.
        "approved_payload_checksum_expected": candidate_send_text_checksum,
        # Hard requirement flags (mandated).
        "approved_payload_checksum_required": True,
        "destination_binding_required": True,
        "credential_boundary_required": True,
        "fresh_operator_gate_required": True,
        "replay_guard_must_be_clear": True,
        "blockers": sorted(set(blockers)),
        "forbidden_fields_detected": forbidden,
        # Explicit non-live invariants.
        "classified_live_ready": False,
        "classified_auto_send_ready": False,
        "candidate_outcome_classes": list(CANDIDATE_OUTCOME_CLASSES),
        **_safety_flags(),
    }
    packet["manual_gate_candidate_checksum"] = compute_checksum(packet)
    return packet


# --------------------------------------------------------------------------- #
# 2. Operator approval capture
# --------------------------------------------------------------------------- #
def capture_operator_approval(manual_gate_candidate_packet,
                              operator_approval=None):
    """Capture (or reject) a LOCAL operator approval against a candidate packet.

    ``operator_approval`` is a local dict (NOT UI input), with:
      ``approved`` (bool), ``operator_gate_id`` (str), ``approval_note_class``
      (symbolic), ``approval_timestamp_placeholder_class`` (symbolic),
      ``approved_payload_checksum`` (str), ``destination_binding_checksum`` (str).

    Fail-closed precedence:
      1. forbidden/leaky candidate OR approval => fail_closed;
      2. no approval supplied or ``approved`` not True => waiting;
      3. candidate precheck not clear => blocked_precheck_not_clear;
      4. missing operator gate id => blocked_missing_gate;
      5. approved payload checksum mismatch => blocked_payload_checksum_mismatch;
      6. destination binding checksum mismatch => blocked_destination_binding_mismatch;
      7. otherwise => captured.

    A captured approval STILL does not dispatch and is NEVER live-ready. Only a
    symbolic note CLASS and a symbolic timestamp CLASS are stored (never raw
    note text), and the operator gate id is stored only as a hash + class.
    """
    candidate = manual_gate_candidate_packet or {}
    approval = operator_approval or None

    forbidden = bool(
        scan_for_leaks(candidate) or scan_for_financial_advice(candidate))
    if approval is not None:
        forbidden = forbidden or bool(
            scan_for_leaks(approval) or scan_for_financial_advice(approval))

    precheck_clear = bool(candidate.get("precheck_clear_for_manual_gate"))
    expected_payload = candidate.get("approved_payload_checksum_expected")
    expected_destination = candidate.get("destination_binding_checksum")

    gate_id = (approval or {}).get("operator_gate_id")
    approved_payload = (approval or {}).get("approved_payload_checksum")
    approval_destination = (approval or {}).get("destination_binding_checksum")

    if forbidden:
        outcome = APPROVAL_FAIL_CLOSED
    elif approval is None or approval.get("approved") is not True:
        outcome = APPROVAL_WAITING
    elif not precheck_clear:
        outcome = APPROVAL_BLOCKED_PRECHECK_NOT_CLEAR
    elif not gate_id:
        outcome = APPROVAL_BLOCKED_MISSING_GATE
    elif not approved_payload or approved_payload != expected_payload:
        outcome = APPROVAL_BLOCKED_PAYLOAD_MISMATCH
    elif not approval_destination or approval_destination != expected_destination:
        outcome = APPROVAL_BLOCKED_DESTINATION_MISMATCH
    else:
        outcome = APPROVAL_CAPTURED

    captured = outcome == APPROVAL_CAPTURED
    status = (render.readmodel.console.adapter.Status.PASS if captured
              else (render.readmodel.console.adapter.Status.FAIL_CLOSED
                    if outcome == APPROVAL_FAIL_CLOSED
                    else render.readmodel.console.adapter.Status.BLOCKED))

    # Symbolic-only redaction of note + timestamp; never raw text.
    note_class = _safe_symbolic_class(
        (approval or {}).get("approval_note_class"), DEFAULT_NOTE_CLASS) \
        if approval is not None else None
    timestamp_class = _safe_symbolic_class(
        (approval or {}).get("approval_timestamp_placeholder_class"),
        DEFAULT_TIMESTAMP_CLASS) if approval is not None else None

    result = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "approval_schema": APPROVAL_SCHEMA,
        "approval_schema_version": APPROVAL_SCHEMA_VERSION,
        "status": status,
        "provider": candidate.get("provider") or PROVIDER_TELEGRAM,
        "operator_approval_outcome_class": outcome,
        "approval_captured": captured,
        "approval_present": approval is not None,
        "operator_marked_approved": bool((approval or {}).get("approved")),
        # Bound candidate references (redacted).
        "source_manual_gate_candidate_checksum": candidate.get(
            "manual_gate_candidate_checksum"),
        "candidate_precheck_outcome_class": candidate.get(
            "next_send_precheck_outcome_class"),
        "candidate_precheck_clear": precheck_clear,
        # Operator gate (hash + class only; never raw id).
        "operator_gate_id_hash": _gate_id_hash(gate_id),
        "operator_gate_class": _gate_class(gate_id),
        "operator_gate_present": bool(gate_id),
        # Symbolic, redacted approval metadata (never raw note text / clock).
        "approval_note_class": note_class,
        "approval_timestamp_placeholder_class": timestamp_class,
        # Checksum reconciliation (checksums only; safe to store).
        "approved_payload_checksum": (
            approved_payload if captured else None),
        "expected_approved_payload_checksum": expected_payload,
        "approved_payload_checksum_matches": bool(
            approved_payload and approved_payload == expected_payload),
        "destination_binding_checksum": (
            approval_destination if captured else None),
        "expected_destination_binding_checksum": expected_destination,
        "destination_binding_checksum_matches": bool(
            approval_destination
            and approval_destination == expected_destination),
        "approval_outcome_classes": list(APPROVAL_OUTCOME_CLASSES),
        "forbidden_fields_detected": forbidden,
        # Explicit non-live invariants: a captured approval is NOT dispatch.
        "is_dispatch": False,
        "classified_live_ready": False,
        "classified_auto_send_ready": False,
        **_safety_flags(),
    }
    result["operator_approval_capture_checksum"] = compute_checksum(result)
    return result


# --------------------------------------------------------------------------- #
# 3. Manual gate packet
# --------------------------------------------------------------------------- #
def build_manual_gate_packet(candidate_packet, approval_capture):
    """Combine a candidate packet + approval capture into the manual-gate packet.

    Derives the single ``allowed_next_step`` deterministically:
      * no candidate              => manual_gate_waiting_for_candidate;
      * candidate blocked/failed   => manual_gate_blocked;
      * candidate clear, approval captured => manual_gate_approved_for_separate_send_runner;
      * candidate clear, approval not captured => manual_gate_waiting_for_operator_approval.

    NEVER dispatches and NEVER classifies live-ready / auto-send-ready /
    valid-for-live-execution; an approved packet only hands off to a SEPARATE
    operator send runner that must re-gate at send time.
    """
    candidate = candidate_packet or {}
    approval = approval_capture or {}

    candidate_outcome = candidate.get("manual_gate_candidate_outcome_class")
    approval_outcome = approval.get("operator_approval_outcome_class")
    precheck_clear = bool(candidate.get("precheck_clear_for_manual_gate"))
    approval_captured = approval.get("approval_captured") is True

    if candidate_outcome == CANDIDATE_WAITING:
        next_step = NEXT_STEP_WAITING_FOR_CANDIDATE
    elif candidate_outcome in (CANDIDATE_BLOCKED, CANDIDATE_FAIL_CLOSED):
        next_step = NEXT_STEP_BLOCKED
    elif precheck_clear and approval_captured:
        next_step = NEXT_STEP_APPROVED_FOR_RUNNER
    elif precheck_clear:
        next_step = NEXT_STEP_WAITING_FOR_APPROVAL
    else:
        next_step = NEXT_STEP_BLOCKED

    status = (render.readmodel.console.adapter.Status.PASS
              if next_step == NEXT_STEP_APPROVED_FOR_RUNNER
              else (render.readmodel.console.adapter.Status.FAIL_CLOSED
                    if candidate_outcome == CANDIDATE_FAIL_CLOSED
                    or approval_outcome == APPROVAL_FAIL_CLOSED
                    else render.readmodel.console.adapter.Status.BLOCKED))

    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "manual_gate_packet_schema": MANUAL_GATE_PACKET_SCHEMA,
        "manual_gate_packet_schema_version": MANUAL_GATE_PACKET_SCHEMA_VERSION,
        "status": status,
        "provider": candidate.get("provider") or PROVIDER_TELEGRAM,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        # Source chain checksums.
        "source_cockpit_render_checksum": candidate.get(
            "source_cockpit_render_checksum"),
        "source_read_model_checksum": candidate.get(
            "source_read_model_checksum"),
        "source_replay_console_checksum": candidate.get(
            "source_replay_console_checksum"),
        "source_handoff_contract_checksum": candidate.get(
            "source_handoff_contract_checksum"),
        # Candidate + precheck.
        "candidate_checksum": candidate.get("manual_gate_candidate_checksum"),
        "manual_gate_candidate_outcome_class": candidate_outcome,
        "precheck_checksum": candidate.get("next_send_precheck_checksum"),
        "next_send_precheck_outcome_class": candidate.get(
            "next_send_precheck_outcome_class"),
        "replay_guard_outcome_class": candidate.get(
            "replay_guard_outcome_class"),
        "precheck_clear_for_manual_gate": precheck_clear,
        # Approval.
        "approval_capture_checksum": approval.get(
            "operator_approval_capture_checksum"),
        "operator_approval_outcome_class": approval_outcome,
        "approval_captured": approval_captured,
        # Operator gate (class/hash only).
        "operator_gate_class": approval.get("operator_gate_class")
        or candidate.get("fresh_operator_gate_class"),
        "operator_gate_id_hash": approval.get("operator_gate_id_hash")
        or candidate.get("fresh_operator_gate_id_hash"),
        # Bound checksums (checksums only; safe).
        "approved_payload_checksum": approval.get("approved_payload_checksum"),
        "destination_binding_checksum": candidate.get(
            "destination_binding_checksum"),
        "stable_payload_replay_key": candidate.get("stable_payload_replay_key"),
        "exact_run_replay_key": candidate.get("exact_run_replay_key"),
        # The single allowed next step.
        "allowed_next_step": next_step,
        "allowed_next_steps": list(ALLOWED_NEXT_STEPS),
        "requires_separate_send_runner": True,
        # Explicit non-live invariants.
        "is_dispatch": False,
        "classified_live_ready": False,
        "classified_auto_send_ready": False,
        "next_recommended_task": NEXT_RECOMMENDED_TASK,
        **_safety_flags(),
    }
    packet["manual_gate_packet_checksum"] = compute_checksum(packet)
    return packet


# --------------------------------------------------------------------------- #
# Worked-example helpers (deterministic, redacted; never execute a send)
# --------------------------------------------------------------------------- #
DEMO_FRESH_GATE_ID = "operator_demo_fresh_gate_for_manual_packet"


def build_demo_clear_candidate_evidence():
    """Build a deterministic, brand-new-payload candidate evidence packet.

    Against the committed ledger context this resolves to a NEW payload, so with
    a fresh operator gate the precheck is clear -- a safe worked example. Carries
    ONLY redacted checksums + symbolic classes (never a token/destination/url).
    """
    return console.build_candidate_evidence(
        destination_binding_checksum=compute_checksum(
            {"kind": "manual_gate_demo_destination_binding"}),
        send_text_checksum=compute_checksum(
            {"kind": "manual_gate_demo_send_text"}),
        request_checksum=compute_checksum(
            {"kind": "manual_gate_demo_request"}),
        credential_handle_id="operator_demo_credential_handle_class",
        live_test_sequence=4)


def build_demo_operator_approval(candidate_packet):
    """Build a deterministic, redacted operator-approval dict matching a candidate.

    Symbolic note + timestamp classes only; checksums echo the candidate's
    expected approved-payload + destination-binding checksums.
    """
    candidate = candidate_packet or {}
    return {
        "approved": True,
        "operator_gate_id": DEMO_FRESH_GATE_ID,
        "approval_note_class": DEFAULT_NOTE_CLASS,
        "approval_timestamp_placeholder_class": DEFAULT_TIMESTAMP_CLASS,
        "approved_payload_checksum": candidate.get(
            "approved_payload_checksum_expected"),
        "destination_binding_checksum": candidate.get(
            "destination_binding_checksum"),
    }


# --------------------------------------------------------------------------- #
# 4. Artifact packet + doc
# --------------------------------------------------------------------------- #
def build_artifact_packet(cockpit_render_packet, console_packet):
    """Build the deterministic repo artifact packet (default + worked examples).

    Scenarios:
      * default no-candidate state (waiting for candidate);
      * one worked clear candidate (new payload under a fresh gate);
      * one captured approval example (redacted symbolic approval data).
    Never includes a raw token/destination/response/url/header/cookie/note.
    """
    rp = cockpit_render_packet or {}
    cp = console_packet or {}

    # Default state: no candidate selected.
    default_candidate = build_manual_gate_candidate_packet(rp, console_packet=cp)
    default_approval = capture_operator_approval(default_candidate, None)
    default_gate = build_manual_gate_packet(default_candidate, default_approval)

    # Worked clear candidate: new payload + fresh gate => precheck clear.
    clear_evidence = build_demo_clear_candidate_evidence()
    clear_candidate = build_manual_gate_candidate_packet(
        rp, candidate_evidence_packet=clear_evidence,
        fresh_operator_gate_id=DEMO_FRESH_GATE_ID, console_packet=cp)
    clear_waiting_approval = capture_operator_approval(clear_candidate, None)
    clear_waiting_gate = build_manual_gate_packet(
        clear_candidate, clear_waiting_approval)

    # Captured approval example over the clear candidate.
    captured_approval = capture_operator_approval(
        clear_candidate, build_demo_operator_approval(clear_candidate))
    approved_gate = build_manual_gate_packet(clear_candidate, captured_approval)

    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "artifact_packet_schema": ARTIFACT_PACKET_SCHEMA,
        "artifact_packet_schema_version": ARTIFACT_PACKET_SCHEMA_VERSION,
        "status": render.readmodel.console.adapter.Status.PASS,
        "provider": PROVIDER_TELEGRAM,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "source_cockpit_render_checksum": rp.get("render_packet_checksum"),
        "source_read_model_checksum": rp.get("source_read_model_checksum"),
        "source_replay_console_checksum": cp.get("console_packet_checksum"),
        "source_handoff_contract_checksum": rp.get("handoff_contract_checksum"),
        # Default no-candidate scenario.
        "default_state": {
            "manual_gate_candidate_outcome_class": default_candidate.get(
                "manual_gate_candidate_outcome_class"),
            "manual_gate_candidate_checksum": default_candidate.get(
                "manual_gate_candidate_checksum"),
            "operator_approval_outcome_class": default_approval.get(
                "operator_approval_outcome_class"),
            "approval_capture_checksum": default_approval.get(
                "operator_approval_capture_checksum"),
            "allowed_next_step": default_gate.get("allowed_next_step"),
            "manual_gate_packet_checksum": default_gate.get(
                "manual_gate_packet_checksum"),
        },
        # Worked clear candidate (awaiting operator approval).
        "worked_candidate_state": {
            "manual_gate_candidate_outcome_class": clear_candidate.get(
                "manual_gate_candidate_outcome_class"),
            "next_send_precheck_outcome_class": clear_candidate.get(
                "next_send_precheck_outcome_class"),
            "replay_guard_outcome_class": clear_candidate.get(
                "replay_guard_outcome_class"),
            "candidate_send_text_checksum": clear_candidate.get(
                "candidate_send_text_checksum"),
            "destination_binding_checksum": clear_candidate.get(
                "destination_binding_checksum"),
            "stable_payload_replay_key": clear_candidate.get(
                "stable_payload_replay_key"),
            "exact_run_replay_key": clear_candidate.get("exact_run_replay_key"),
            "fresh_operator_gate_id_hash": clear_candidate.get(
                "fresh_operator_gate_id_hash"),
            "fresh_operator_gate_class": clear_candidate.get(
                "fresh_operator_gate_class"),
            "manual_gate_candidate_checksum": clear_candidate.get(
                "manual_gate_candidate_checksum"),
            "operator_approval_outcome_class": clear_waiting_approval.get(
                "operator_approval_outcome_class"),
            "allowed_next_step": clear_waiting_gate.get("allowed_next_step"),
            "manual_gate_packet_checksum": clear_waiting_gate.get(
                "manual_gate_packet_checksum"),
        },
        # Captured approval scenario.
        "captured_approval_state": {
            "operator_approval_outcome_class": captured_approval.get(
                "operator_approval_outcome_class"),
            "approval_captured": captured_approval.get("approval_captured"),
            "operator_gate_class": captured_approval.get("operator_gate_class"),
            "operator_gate_id_hash": captured_approval.get(
                "operator_gate_id_hash"),
            "approval_note_class": captured_approval.get("approval_note_class"),
            "approval_timestamp_placeholder_class": captured_approval.get(
                "approval_timestamp_placeholder_class"),
            "approved_payload_checksum": captured_approval.get(
                "approved_payload_checksum"),
            "destination_binding_checksum": captured_approval.get(
                "destination_binding_checksum"),
            "approval_capture_checksum": captured_approval.get(
                "operator_approval_capture_checksum"),
            "allowed_next_step": approved_gate.get("allowed_next_step"),
            "manual_gate_packet_checksum": approved_gate.get(
                "manual_gate_packet_checksum"),
        },
        # Decision vocab (for the future cockpit UI).
        "candidate_outcome_classes": list(CANDIDATE_OUTCOME_CLASSES),
        "approval_outcome_classes": list(APPROVAL_OUTCOME_CLASSES),
        "allowed_next_steps": list(ALLOWED_NEXT_STEPS),
        "next_recommended_task": NEXT_RECOMMENDED_TASK,
        **_safety_flags(),
    }
    packet["artifact_packet_checksum"] = compute_checksum(packet)
    return packet


def build_artifact_doc(packet):
    """Render a deterministic, scanner-safe markdown artifact doc."""
    default = packet.get("default_state") or {}
    worked = packet.get("worked_candidate_state") or {}
    captured = packet.get("captured_approval_state") or {}

    candidate_classes = "".join(
        "- `%s`\n" % c for c in (packet.get("candidate_outcome_classes") or []))
    approval_classes = "".join(
        "- `%s`\n" % c for c in (packet.get("approval_outcome_classes") or []))
    next_steps = "".join(
        "- `%s`\n" % c for c in (packet.get("allowed_next_steps") or []))

    return (
        "# 0174VC/VD/VE Telegram Manual Gate Packet Builder + Operator Approval "
        "Capture\n\n"
        f"Task: `{packet['task_label']}`\n\n"
        f"Model: `{packet['model']}` version `{packet['model_version']}`\n\n"
        "## Purpose\n\n"
        "LOCAL, deterministic backend contract that turns the cockpit "
        "\"Prepare manual gate packet\" affordance into a real redacted packet "
        "the operator must approve before any future supervised send gate. It "
        "binds candidate evidence, replay-guard outcome, next-send precheck, "
        "approved-payload + destination-binding checksums, a credential boundary "
        "requirement, an operator gate hash/class, and a symbolic approval "
        "timestamp placeholder. It never dispatches, never reads env or "
        "credentials, and never classifies anything live-ready.\n\n"
        "## Source chain\n\n"
        f"- Source baseline commit: `{packet['source_baseline_commit']}`\n"
        f"- Source cockpit render checksum: "
        f"`{packet['source_cockpit_render_checksum']}`\n"
        f"- Source read model checksum: "
        f"`{packet['source_read_model_checksum']}`\n"
        f"- Source replay console checksum: "
        f"`{packet['source_replay_console_checksum']}`\n"
        f"- Source handoff contract checksum: "
        f"`{packet['source_handoff_contract_checksum']}`\n\n"
        "## Default state (no candidate)\n\n"
        f"- Candidate outcome: "
        f"`{default.get('manual_gate_candidate_outcome_class')}`\n"
        f"- Approval outcome: "
        f"`{default.get('operator_approval_outcome_class')}`\n"
        f"- Allowed next step: `{default.get('allowed_next_step')}`\n"
        f"- Manual gate packet checksum: "
        f"`{default.get('manual_gate_packet_checksum')}`\n\n"
        "## Worked clear candidate (awaiting operator approval)\n\n"
        f"- Candidate outcome: "
        f"`{worked.get('manual_gate_candidate_outcome_class')}`\n"
        f"- Precheck outcome: "
        f"`{worked.get('next_send_precheck_outcome_class')}`\n"
        f"- Replay guard outcome: "
        f"`{worked.get('replay_guard_outcome_class')}`\n"
        f"- Candidate send text checksum: "
        f"`{worked.get('candidate_send_text_checksum')}`\n"
        f"- Destination binding checksum: "
        f"`{worked.get('destination_binding_checksum')}`\n"
        f"- Stable payload replay key: "
        f"`{worked.get('stable_payload_replay_key')}`\n"
        f"- Exact run replay key: `{worked.get('exact_run_replay_key')}`\n"
        f"- Fresh operator gate hash: "
        f"`{worked.get('fresh_operator_gate_id_hash')}`\n"
        f"- Approval outcome: "
        f"`{worked.get('operator_approval_outcome_class')}`\n"
        f"- Allowed next step: `{worked.get('allowed_next_step')}`\n"
        f"- Manual gate packet checksum: "
        f"`{worked.get('manual_gate_packet_checksum')}`\n\n"
        "## Captured approval (redacted, symbolic)\n\n"
        f"- Approval outcome: "
        f"`{captured.get('operator_approval_outcome_class')}`\n"
        f"- Approval captured: `{captured.get('approval_captured')}`\n"
        f"- Operator gate class: `{captured.get('operator_gate_class')}`\n"
        f"- Operator gate id hash: `{captured.get('operator_gate_id_hash')}`\n"
        f"- Approval note class: `{captured.get('approval_note_class')}`\n"
        f"- Approval timestamp class: "
        f"`{captured.get('approval_timestamp_placeholder_class')}`\n"
        f"- Approved payload checksum: "
        f"`{captured.get('approved_payload_checksum')}`\n"
        f"- Destination binding checksum: "
        f"`{captured.get('destination_binding_checksum')}`\n"
        f"- Allowed next step: `{captured.get('allowed_next_step')}`\n"
        f"- Manual gate packet checksum: "
        f"`{captured.get('manual_gate_packet_checksum')}`\n\n"
        "## Candidate outcome classes\n\n"
        f"{candidate_classes}\n"
        "## Operator approval outcome classes\n\n"
        f"{approval_classes}\n"
        "## Manual gate allowed next steps\n\n"
        f"{next_steps}\n"
        "## Safety proofs\n\n"
        f"- Network performed: `{packet['network_performed']}`\n"
        f"- Telegram API called: `{packet['telegram_api_called']}`\n"
        f"- Credential read: `{packet['credential_read']}`\n"
        f"- Env read: `{packet['env_read']}`\n"
        f"- sendMessage executed: `{packet['sendmessage_executed']}`\n"
        f"- Stores no raw operator gate id: "
        f"`{packet['stores_no_raw_operator_gate_id']}`\n"
        f"- Stores no raw approval note: "
        f"`{packet['stores_no_raw_approval_note']}`\n"
        f"- Live ready: `{packet['live_ready']}`\n"
        f"- Valid for live execution: `{packet['valid_for_live_execution']}`\n\n"
        f"## Artifact packet checksum\n\n`{packet['artifact_packet_checksum']}`"
        "\n\n"
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


def _repo_root_from_module():
    """Best-effort repo root (two levels up from this module file)."""
    import pathlib
    return pathlib.Path(__file__).resolve().parents[1]


def _load_committed_console_packet():
    """Load the committed 0174UT replay-console packet (reconciled ledger ctx)."""
    import pathlib
    root = _repo_root_from_module()
    return load_packet(pathlib.Path(root) / CONSOLE_PACKET_REL)


def build_artifact_from_repo(repo_root):
    """Load the committed render + console packets and build the artifact packet."""
    import pathlib
    root = pathlib.Path(repo_root)
    render_packet = load_packet(root / RENDER_PACKET_REL)
    console_packet = load_packet(root / CONSOLE_PACKET_REL)
    return build_artifact_packet(render_packet, console_packet)


def write_artifacts(base_dir, packet, doc):
    """Write the artifact packet + doc under ``base_dir`` ONLY if scanner-clean.

    Returns the list of written absolute paths. Raises ``RuntimeError`` if any
    scanner flags anything, so unsafe artifacts are never persisted. This is the
    ONLY function in this module that touches the filesystem.
    """
    import pathlib
    violations = scan_manual_gate(packet, doc)
    if violations:
        raise RuntimeError(
            "refusing to write manual gate artifacts: scan found %d "
            "violation(s)" % len(violations))
    out_dir = pathlib.Path(base_dir) / DOC_REL_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    packet_path = out_dir / PACKET_FILENAME
    doc_path = out_dir / DOC_FILENAME
    packet_path.write_text(serialize(packet), encoding="utf-8", newline="\n")
    doc_path.write_text(doc, encoding="utf-8", newline="\n")
    return [str(packet_path), str(doc_path)]
