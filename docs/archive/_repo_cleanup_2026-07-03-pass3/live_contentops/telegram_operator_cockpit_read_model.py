"""Telegram supervised-send OPERATOR COCKPIT READ MODEL + NEXT-SEND PRECHECK.

Task 0174UW/UX/UY. Deterministic, LOCAL, read-only backend data contract that a
future cockpit UI can render. It consumes the accepted 0174UT replay-console
packet (which already carries the reconciled ledger view + replay examples) and
reduces it to a screenshot/UI-ready read model plus a strict next-send precheck.

AUTHORITY MODEL (per the master plan): the deterministic LOCAL gate is the
dispatch authority. This module is purely a READ MODEL: it summarizes state and
reports the single next allowed action. It NEVER sends, NEVER calls Telegram,
NEVER reads ``.env`` / env / credentials, and NEVER classifies anything as
live-ready, auto-send-ready, or valid-for-live-execution.

Importing this module performs NO writes and NO side effects. Artifacts are
written ONLY when ``write_artifacts(...)`` is called explicitly and the content
passes the reused fail-closed redaction + financial-advice scanners.
"""

import os.path

# Reuse the accepted replay console (and, through it, the ledger + adapter
# scanners / deterministic checksum + the redacted symbolic vocab).
from live_contentops import telegram_operator_replay_console as console
from live_contentops import telegram_supervised_send_outcome_ledger as ledger

TASK_LABEL = (
    "TASK_CONTENTOPS_0174UW_UX_UY_TELEGRAM_SUPERVISED_SEND_OPERATOR_COCKPIT_"
    "READ_MODEL_AND_NEXT_SEND_PRECHECK_BATCH_V0"
)
MODEL = "TELEGRAM_OPERATOR_COCKPIT_READ_MODEL_0174UW_UX_UY"
MODEL_VERSION = "0174UW_UX_UY_TELEGRAM_OPERATOR_COCKPIT_READ_MODEL_V1"

READ_MODEL_SCHEMA = "contentops.telegram_operator_cockpit_read_model"
READ_MODEL_SCHEMA_VERSION = "0174UW_UX_UY_OPERATOR_COCKPIT_READ_MODEL_V1"
PRECHECK_SCHEMA = "contentops.telegram_next_send_precheck"
PRECHECK_SCHEMA_VERSION = "0174UW_UX_UY_NEXT_SEND_PRECHECK_V1"
COCKPIT_PACKET_SCHEMA = "contentops.telegram_operator_cockpit_read_model_packet"
COCKPIT_PACKET_SCHEMA_VERSION = "0174UW_UX_UY_OPERATOR_COCKPIT_READ_MODEL_PACKET_V1"

SOURCE_BASELINE_COMMIT = "ba9862afbe63468817ba6cea2404d70f42a471cd"

DOC_REL_DIR = os.path.join("docs", "automation", "0174UW_UX_UY")
PACKET_FILENAME = "telegram_operator_cockpit_read_model_packet.json"
DOC_FILENAME = "telegram_operator_cockpit_read_model.md"

# Committed source console packet (read-only) used by the repo-driven builder.
CONSOLE_PACKET_REL = os.path.join(
    "docs", "automation", "0174UT_UU_UV",
    "telegram_operator_replay_console_packet.json")

NEXT_RECOMMENDED_TASK = (
    "TASK_CONTENTOPS_0174UZ_VA_VB_TELEGRAM_SUPERVISED_SEND_OPERATOR_COCKPIT_"
    "HTML_RENDER_AND_MANUAL_GATE_HANDOFF_BATCH_V0"
)

PROVIDER_TELEGRAM = console.PROVIDER_TELEGRAM

# --------------------------------------------------------------------------- #
# Next-send precheck outcome classes (exact names mandated by the task)
# --------------------------------------------------------------------------- #
PRECHECK_CLEAR = "next_send_precheck_clear_for_manual_gate"
PRECHECK_REQUIRES_FRESH_GATE = "next_send_precheck_requires_fresh_operator_gate"
PRECHECK_BLOCKED_EXACT_REPLAY = "next_send_precheck_blocked_exact_replay"
PRECHECK_BLOCKED_MISSING_CANDIDATE = "next_send_precheck_blocked_missing_candidate"
PRECHECK_BLOCKED_UNRECONCILED = "next_send_precheck_blocked_unreconciled_ledger"
PRECHECK_FAIL_CLOSED = "next_send_precheck_fail_closed_forbidden_value"

PRECHECK_OUTCOME_CLASSES = (
    PRECHECK_CLEAR,
    PRECHECK_REQUIRES_FRESH_GATE,
    PRECHECK_BLOCKED_EXACT_REPLAY,
    PRECHECK_BLOCKED_MISSING_CANDIDATE,
    PRECHECK_BLOCKED_UNRECONCILED,
    PRECHECK_FAIL_CLOSED,
)

# Machine-readable blocker codes (NOT prose blobs).
BLOCKER_UNRECONCILED_LEDGER = "precheck_blocker_unreconciled_ledger"
BLOCKER_MISSING_CANDIDATE = "precheck_blocker_missing_candidate"
BLOCKER_EXACT_REPLAY = "precheck_blocker_exact_replay"
BLOCKER_REQUIRES_FRESH_GATE = "precheck_blocker_requires_fresh_operator_gate"
BLOCKER_FORBIDDEN_VALUE = "precheck_blocker_forbidden_value"

# Deterministic precheck -> (next_allowed_action token, operator action label).
_PRECHECK_TO_ACTION = {
    PRECHECK_CLEAR: (
        console.ACTION_CLEAR_FOR_MANUAL_SEND,
        "Open the manual supervised send gate (a fresh operator gate is still "
        "required at send time)."),
    PRECHECK_REQUIRES_FRESH_GATE: (
        console.ACTION_REQUIRES_FRESH_GATE,
        "Provide a fresh operator gate id to proceed."),
    PRECHECK_BLOCKED_EXACT_REPLAY: (
        console.ACTION_BLOCKED_EXACT_REPLAY,
        "Do not send: this exact run is already recorded (exact replay blocked)."),
    PRECHECK_BLOCKED_MISSING_CANDIDATE: (
        console.ACTION_BLOCKED_INVALID_CANDIDATE,
        "Select or provide a candidate evidence packet to precheck."),
    PRECHECK_BLOCKED_UNRECONCILED: (
        console.ACTION_BLOCKED_INVALID_CANDIDATE,
        "Reconcile the ledger before any further supervised send."),
    PRECHECK_FAIL_CLOSED: (
        console.ACTION_FAIL_CLOSED,
        "Fail closed: a forbidden/leaky value was detected."),
}

_PRECHECK_TO_BLOCKERS = {
    PRECHECK_CLEAR: [],
    PRECHECK_REQUIRES_FRESH_GATE: [BLOCKER_REQUIRES_FRESH_GATE],
    PRECHECK_BLOCKED_EXACT_REPLAY: [BLOCKER_EXACT_REPLAY],
    PRECHECK_BLOCKED_MISSING_CANDIDATE: [BLOCKER_MISSING_CANDIDATE],
    PRECHECK_BLOCKED_UNRECONCILED: [BLOCKER_UNRECONCILED_LEDGER],
    PRECHECK_FAIL_CLOSED: [BLOCKER_FORBIDDEN_VALUE],
}


# --------------------------------------------------------------------------- #
# Scanning / serialization (reuse the accepted scanners)
# --------------------------------------------------------------------------- #
def scan_for_leaks(obj):
    """Return redaction violations for ``obj`` (delegates)."""
    return console.scan_for_leaks(obj)


def scan_for_financial_advice(obj):
    """Return financial-advice violations for ``obj`` (delegates)."""
    return console.scan_for_financial_advice(obj)


def serialize(obj):
    """Deterministic JSON (delegates)."""
    return console.serialize(obj)


def compute_checksum(obj):
    """SHA-256 of the deterministic serialization (delegates)."""
    return console.compute_checksum(obj)


def scan_cockpit(packet, doc):
    """Return combined redaction + financial-advice violations."""
    return (scan_for_leaks(packet) + scan_for_leaks(doc)
            + scan_for_financial_advice(packet)
            + scan_for_financial_advice(doc))


def _safety_flags():
    """Hard non-live invariants attached to every 0174UW/UX/UY object."""
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
        "is_read_only_cockpit": True,
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
# Candidate resolution (console-result OR raw evidence packet)
# --------------------------------------------------------------------------- #
def _existing_entries_from_console(console_packet):
    """Reconstruct a minimal existing-entry list from the console packet.

    The replay guard only reads ``exact_run_replay_key`` +
    ``stable_payload_replay_key`` from existing entries, so the last successful
    send's two redacted keys are sufficient to reproduce replay decisions.
    """
    last = (console_packet or {}).get("last_successful_send") or {}
    exact = last.get("exact_run_replay_key")
    stable = last.get("stable_payload_replay_key")
    if not exact and not stable:
        return []
    return [{
        "exact_run_replay_key": exact,
        "stable_payload_replay_key": stable,
    }]


def resolve_candidate_console(console_packet, candidate, fresh_operator_gate_id):
    """Return a candidate-console-result dict (or ``None`` if no candidate).

    Accepts EITHER an already-built candidate-console result / committed example
    (it carries ``replay_guard_outcome_class``) OR a raw candidate evidence
    packet (which is run through the accepted replay console against the current
    ledger reconstructed from ``console_packet``).
    """
    if not candidate:
        return None
    if isinstance(candidate, dict) and candidate.get("replay_guard_outcome_class"):
        return candidate
    existing = _existing_entries_from_console(console_packet)
    return console.build_candidate_replay_console(
        candidate, existing, operator_gate_id=fresh_operator_gate_id)


# --------------------------------------------------------------------------- #
# 3. Next-send precheck
# --------------------------------------------------------------------------- #
def build_next_send_precheck(console_packet, candidate=None,
                             fresh_operator_gate_id=None):
    """Classify the single next allowed action before any future live send.

    Fail-closed precedence:
      1. forbidden/leaky console OR candidate => fail_closed_forbidden_value;
      2. console reconciliation not OK => blocked_unreconciled_ledger;
      3. no candidate => blocked_missing_candidate;
      4. candidate replay outcome:
         exact replay => blocked_exact_replay;
         requires fresh gate => requires_fresh_operator_gate;
         clear => clear_for_manual_gate;
         fail-closed guard => fail_closed_forbidden_value;
         otherwise (invalid/missing evidence) => blocked_missing_candidate.

    NEVER classifies live-ready, auto-send-ready, or valid-for-live-execution.
    """
    cp = console_packet or {}
    forbidden = bool(scan_for_leaks(cp) or scan_for_financial_advice(cp))
    if candidate is not None:
        forbidden = forbidden or bool(
            scan_for_leaks(candidate) or scan_for_financial_advice(candidate))

    reconciliation_class = cp.get("reconciliation_outcome_class")
    reconciliation_ok = reconciliation_class == console.RECON_OK

    resolved = resolve_candidate_console(cp, candidate, fresh_operator_gate_id)
    candidate_guard_class = (resolved or {}).get("replay_guard_outcome_class")
    candidate_action = (resolved or {}).get("next_allowed_action")

    if forbidden:
        outcome = PRECHECK_FAIL_CLOSED
    elif not reconciliation_ok:
        outcome = PRECHECK_BLOCKED_UNRECONCILED
    elif resolved is None:
        outcome = PRECHECK_BLOCKED_MISSING_CANDIDATE
    elif (candidate_guard_class == ledger.REPLAY_FAIL_CLOSED
          or candidate_action == console.ACTION_FAIL_CLOSED):
        outcome = PRECHECK_FAIL_CLOSED
    elif candidate_action == console.ACTION_BLOCKED_EXACT_REPLAY:
        outcome = PRECHECK_BLOCKED_EXACT_REPLAY
    elif candidate_action == console.ACTION_REQUIRES_FRESH_GATE:
        outcome = PRECHECK_REQUIRES_FRESH_GATE
    elif candidate_action == console.ACTION_CLEAR_FOR_MANUAL_SEND:
        outcome = PRECHECK_CLEAR
    else:
        outcome = PRECHECK_BLOCKED_MISSING_CANDIDATE

    next_action, action_label = _PRECHECK_TO_ACTION[outcome]
    blockers = list(_PRECHECK_TO_BLOCKERS[outcome])
    status = (console.adapter.Status.PASS if outcome == PRECHECK_CLEAR
              else (console.adapter.Status.FAIL_CLOSED
                    if outcome == PRECHECK_FAIL_CLOSED
                    else console.adapter.Status.BLOCKED))

    result = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "precheck_schema": PRECHECK_SCHEMA,
        "precheck_schema_version": PRECHECK_SCHEMA_VERSION,
        "status": status,
        "provider": cp.get("provider") or PROVIDER_TELEGRAM,
        "precheck_outcome_class": outcome,
        "next_allowed_action": next_action,
        "next_operator_action_label": action_label,
        # Candidate facts (redacted classes only).
        "candidate_present": resolved is not None,
        "candidate_status": (candidate_guard_class if resolved is not None
                             else "no_candidate_selected"),
        "candidate_replay_guard_outcome_class": candidate_guard_class,
        "fresh_operator_gate_present": bool(
            (resolved or {}).get("fresh_operator_gate_present")
            or fresh_operator_gate_id),
        # Reconciliation gate.
        "reconciliation_outcome_class": reconciliation_class,
        "reconciliation_ok": reconciliation_ok,
        # Static readiness rails (always required before any live send).
        "fresh_gate_required": True,
        "ledger_guard_required": True,
        "operator_approval_required": True,
        "payload_preview_required": True,
        "destination_binding_required": True,
        "credential_boundary_required": True,
        "blockers": blockers,
        "forbidden_fields_detected": forbidden,
        # Explicit non-live invariants.
        "classified_live_ready": False,
        "classified_auto_send_ready": False,
        "requires_separate_operator_send_gate": True,
        **_safety_flags(),
    }
    result["precheck_checksum"] = compute_checksum(result)
    return result


# --------------------------------------------------------------------------- #
# 2. State sections
# --------------------------------------------------------------------------- #
def _operational_truth_rail(console_packet):
    cp = console_packet or {}
    last = cp.get("last_successful_send") or {}
    return {
        "current_ledger_count": cp.get("current_ledger_entry_count"),
        "last_send_sequence": last.get("live_test_sequence"),
        "last_send_succeeded": bool(last.get("send_succeeded")),
        "reconciliation_status": cp.get("reconciliation_outcome_class"),
        "current_ledger_manifest_checksum": cp.get(
            "current_ledger_manifest_checksum"),
    }


def _replay_guard_panel(console_packet):
    cp = console_packet or {}
    examples = cp.get("candidate_console_examples") or {}

    def _action(key):
        return (examples.get(key) or {}).get("next_allowed_action")

    return {
        "exact_replay_example_outcome": _action("a_exact_replay_blocked"),
        "same_payload_no_gate_outcome": _action(
            "b_same_payload_without_fresh_gate"),
        "same_payload_fresh_gate_outcome": _action(
            "c_same_payload_with_fresh_gate"),
        "new_payload_outcome": _action("d_new_payload_clear"),
        "current_next_allowed_action": cp.get("next_recommended_action"),
    }


def _next_send_precheck_panel(precheck):
    pc = precheck or {}
    return {
        "candidate_status": pc.get("candidate_status"),
        "precheck_outcome_class": pc.get("precheck_outcome_class"),
        "fresh_gate_required": pc.get("fresh_gate_required"),
        "ledger_guard_required": pc.get("ledger_guard_required"),
        "operator_approval_required": pc.get("operator_approval_required"),
        "payload_preview_required": pc.get("payload_preview_required"),
        "destination_binding_required": pc.get("destination_binding_required"),
        "credential_boundary_required": pc.get("credential_boundary_required"),
        "blockers": list(pc.get("blockers") or []),
    }


def _evidence_chain_panel(console_packet):
    cp = console_packet or {}
    last = cp.get("last_successful_send") or {}
    return {
        "accepted_send_proof_checksum": cp.get(
            "accepted_send_proof_evidence_checksum"),
        "latest_ledger_proof_checksum": cp.get("send_proof_evidence_checksum"),
        "replay_console_checksum": cp.get("console_packet_checksum"),
        "last_response_checksum": last.get("response_checksum"),
        "last_request_checksum": last.get("request_checksum"),
    }


def _forbidden_affordance_panel():
    return {
        "no_auto_send": True,
        "no_scheduler": True,
        "no_retry_loop": True,
        "no_autonomous_reply": True,
        "no_webhook_polling": True,
        "no_live_ready_claim": True,
    }


# --------------------------------------------------------------------------- #
# 1. Cockpit read model
# --------------------------------------------------------------------------- #
def build_operator_cockpit_read_model(console_packet, candidate_precheck=None):
    """Reduce the console packet + a precheck into the cockpit read model.

    When ``candidate_precheck`` is not supplied, a default precheck is built with
    NO candidate selected (=> ``blocked_missing_candidate``), which is the
    correct cockpit default state before the operator picks a candidate.
    """
    cp = console_packet or {}
    precheck = candidate_precheck or build_next_send_precheck(cp, candidate=None)

    operational_truth_rail = _operational_truth_rail(cp)
    replay_guard_panel = _replay_guard_panel(cp)
    next_send_precheck_panel = _next_send_precheck_panel(precheck)
    evidence_chain_panel = _evidence_chain_panel(cp)
    forbidden_affordance_panel = _forbidden_affordance_panel()

    readiness_rails = {
        "fresh_gate_required": precheck.get("fresh_gate_required"),
        "ledger_guard_required": precheck.get("ledger_guard_required"),
        "operator_approval_required": precheck.get("operator_approval_required"),
        "payload_preview_required": precheck.get("payload_preview_required"),
        "destination_binding_required": precheck.get(
            "destination_binding_required"),
        "credential_boundary_required": precheck.get(
            "credential_boundary_required"),
    }

    model = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "read_model_schema": READ_MODEL_SCHEMA,
        "read_model_schema_version": READ_MODEL_SCHEMA_VERSION,
        "status": console.adapter.Status.PASS,
        "provider": cp.get("provider") or PROVIDER_TELEGRAM,
        # Headline state.
        "current_ledger_count": cp.get("current_ledger_entry_count"),
        "current_ledger_manifest_checksum": cp.get(
            "current_ledger_manifest_checksum"),
        "previous_ledger_manifest_checksum": cp.get(
            "previous_ledger_manifest_checksum"),
        "last_successful_send": dict(cp.get("last_successful_send") or {}),
        "reconciliation_outcome": cp.get("reconciliation_outcome_class"),
        "candidate_replay_status": precheck.get("candidate_status"),
        "next_allowed_action": precheck.get("next_allowed_action"),
        "next_operator_action_label": precheck.get(
            "next_operator_action_label"),
        "precheck_outcome_class": precheck.get("precheck_outcome_class"),
        "blocker_stack": list(precheck.get("blockers") or []),
        "readiness_rails": readiness_rails,
        # Sections.
        "operational_truth_rail": operational_truth_rail,
        "replay_guard_panel": replay_guard_panel,
        "next_send_precheck_panel": next_send_precheck_panel,
        "evidence_chain_panel": evidence_chain_panel,
        "forbidden_affordance_panel": forbidden_affordance_panel,
        # Audit references.
        "audit_references": {
            "replay_console_checksum": cp.get("console_packet_checksum"),
            "reconciliation_checksum": cp.get("reconciliation_checksum"),
            "ledger_view_checksum": cp.get("ledger_view_checksum"),
            "accepted_send_proof_checksum": cp.get(
                "accepted_send_proof_evidence_checksum"),
            "latest_ledger_proof_checksum": cp.get(
                "send_proof_evidence_checksum"),
            "precheck_checksum": precheck.get("precheck_checksum"),
            "source_console_task_label": cp.get("task_label"),
        },
        "precheck_outcome_classes": list(PRECHECK_OUTCOME_CLASSES),
        "next_allowed_action_classes": cp.get("next_allowed_action_classes"),
        **_safety_flags(),
    }
    model["cockpit_read_model_checksum"] = compute_checksum(model)
    return model


# --------------------------------------------------------------------------- #
# 4. Candidate examples (feed the read model; never execute send)
# --------------------------------------------------------------------------- #
def build_precheck_examples(console_packet):
    """Build the four next-send precheck examples from the console packet.

    Feeds each committed candidate-console example back through the precheck so
    the cockpit can preview exactly what each candidate would resolve to. NEVER
    executes a send.
    """
    cp = console_packet or {}
    examples = cp.get("candidate_console_examples") or {}
    return {
        "exact_replay": build_next_send_precheck(
            cp, candidate=examples.get("a_exact_replay_blocked")),
        "same_payload_without_fresh_gate": build_next_send_precheck(
            cp, candidate=examples.get("b_same_payload_without_fresh_gate")),
        "same_payload_with_fresh_gate": build_next_send_precheck(
            cp, candidate=examples.get("c_same_payload_with_fresh_gate")),
        "new_payload": build_next_send_precheck(
            cp, candidate=examples.get("d_new_payload_clear")),
    }


# --------------------------------------------------------------------------- #
# 5. Artifact packet + doc
# --------------------------------------------------------------------------- #
def build_cockpit_packet(console_packet):
    """Build the deterministic operator cockpit read-model packet (redacted)."""
    cp = console_packet or {}
    # Default cockpit state: no candidate selected yet.
    default_precheck = build_next_send_precheck(cp, candidate=None)
    read_model = build_operator_cockpit_read_model(
        cp, candidate_precheck=default_precheck)
    precheck_examples = build_precheck_examples(cp)

    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "cockpit_packet_schema": COCKPIT_PACKET_SCHEMA,
        "cockpit_packet_schema_version": COCKPIT_PACKET_SCHEMA_VERSION,
        "status": console.adapter.Status.PASS,
        "provider": PROVIDER_TELEGRAM,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        # Headline references.
        "replay_console_checksum": cp.get("console_packet_checksum"),
        "reconciliation_outcome": cp.get("reconciliation_outcome_class"),
        "current_ledger_count": cp.get("current_ledger_entry_count"),
        "next_allowed_action": read_model.get("next_allowed_action"),
        "cockpit_read_model_checksum": read_model.get(
            "cockpit_read_model_checksum"),
        # Sections (mirrored at top level for easy UI binding).
        "operational_truth_rail": read_model.get("operational_truth_rail"),
        "replay_guard_panel": read_model.get("replay_guard_panel"),
        "next_send_precheck_panel": read_model.get("next_send_precheck_panel"),
        "evidence_chain_panel": read_model.get("evidence_chain_panel"),
        "forbidden_affordance_panel": read_model.get(
            "forbidden_affordance_panel"),
        # Full read model + precheck examples.
        "operator_cockpit_read_model": read_model,
        "precheck_outcome_classes": list(PRECHECK_OUTCOME_CLASSES),
        "precheck_examples": {
            key: {
                "precheck_outcome_class": ex.get("precheck_outcome_class"),
                "next_allowed_action": ex.get("next_allowed_action"),
                "candidate_status": ex.get("candidate_status"),
                "blockers": ex.get("blockers"),
                "precheck_checksum": ex.get("precheck_checksum"),
            }
            for key, ex in precheck_examples.items()
        },
        "next_recommended_task": NEXT_RECOMMENDED_TASK,
        **_safety_flags(),
    }
    packet["cockpit_packet_checksum"] = compute_checksum(packet)
    return packet


def build_cockpit_doc(packet):
    """Render a deterministic, scanner-safe markdown cockpit doc."""
    rail = packet.get("operational_truth_rail") or {}
    replay = packet.get("replay_guard_panel") or {}
    precheck = packet.get("next_send_precheck_panel") or {}
    evidence = packet.get("evidence_chain_panel") or {}
    forbidden = packet.get("forbidden_affordance_panel") or {}
    examples = packet.get("precheck_examples") or {}

    def _ex_line(key):
        ex = examples.get(key) or {}
        return (f"- `{key}` -> `{ex.get('precheck_outcome_class')}` "
                f"(action `{ex.get('next_allowed_action')}`)\n")

    return (
        "# 0174UW/UX/UY Telegram Operator Cockpit Read Model + Next-Send Precheck"
        "\n\n"
        f"Task: `{packet['task_label']}`\n\n"
        f"Model: `{packet['model']}` version `{packet['model_version']}`\n\n"
        "## Purpose\n\n"
        "Deterministic, LOCAL, read-only backend data contract for a future "
        "operator cockpit UI. Summarizes ledger state, reconciliation, last "
        "send outcome, replay examples, and the single next allowed action "
        "before any future supervised send. No network, API, env, or credential "
        "read; never classifies anything as live-ready.\n\n"
        "## Operational truth rail\n\n"
        f"- Current ledger count: `{rail.get('current_ledger_count')}`\n"
        f"- Last send sequence: `{rail.get('last_send_sequence')}`\n"
        f"- Last send succeeded: `{rail.get('last_send_succeeded')}`\n"
        f"- Reconciliation status: `{rail.get('reconciliation_status')}`\n"
        f"- Current ledger manifest checksum: "
        f"`{rail.get('current_ledger_manifest_checksum')}`\n\n"
        "## Replay guard panel\n\n"
        f"- Exact replay example: `{replay.get('exact_replay_example_outcome')}`\n"
        f"- Same payload, no gate: `{replay.get('same_payload_no_gate_outcome')}`\n"
        f"- Same payload, fresh gate: "
        f"`{replay.get('same_payload_fresh_gate_outcome')}`\n"
        f"- New payload: `{replay.get('new_payload_outcome')}`\n"
        f"- Current next allowed action: "
        f"`{replay.get('current_next_allowed_action')}`\n\n"
        "## Next-send precheck panel\n\n"
        f"- Candidate status: `{precheck.get('candidate_status')}`\n"
        f"- Precheck outcome class: `{precheck.get('precheck_outcome_class')}`\n"
        f"- Fresh gate required: `{precheck.get('fresh_gate_required')}`\n"
        f"- Ledger guard required: `{precheck.get('ledger_guard_required')}`\n"
        f"- Operator approval required: "
        f"`{precheck.get('operator_approval_required')}`\n"
        f"- Payload preview required: "
        f"`{precheck.get('payload_preview_required')}`\n"
        f"- Destination binding required: "
        f"`{precheck.get('destination_binding_required')}`\n"
        f"- Credential boundary required: "
        f"`{precheck.get('credential_boundary_required')}`\n"
        f"- Blockers: `{precheck.get('blockers')}`\n\n"
        "## Next-send precheck examples\n\n"
        + _ex_line("exact_replay")
        + _ex_line("same_payload_without_fresh_gate")
        + _ex_line("same_payload_with_fresh_gate")
        + _ex_line("new_payload")
        + "\n## Evidence chain panel\n\n"
        f"- Accepted send proof checksum: "
        f"`{evidence.get('accepted_send_proof_checksum')}`\n"
        f"- Latest ledger proof checksum: "
        f"`{evidence.get('latest_ledger_proof_checksum')}`\n"
        f"- Replay console checksum: "
        f"`{evidence.get('replay_console_checksum')}`\n"
        f"- Last response checksum: `{evidence.get('last_response_checksum')}`\n"
        f"- Last request checksum: `{evidence.get('last_request_checksum')}`\n\n"
        "## Forbidden affordance panel\n\n"
        f"- No auto send: `{forbidden.get('no_auto_send')}`\n"
        f"- No scheduler: `{forbidden.get('no_scheduler')}`\n"
        f"- No retry loop: `{forbidden.get('no_retry_loop')}`\n"
        f"- No autonomous reply: `{forbidden.get('no_autonomous_reply')}`\n"
        f"- No webhook/polling: `{forbidden.get('no_webhook_polling')}`\n"
        f"- No live-ready claim: `{forbidden.get('no_live_ready_claim')}`\n\n"
        "## Safety proofs\n\n"
        f"- Network performed: `{packet['network_performed']}`\n"
        f"- Telegram API called: `{packet['telegram_api_called']}`\n"
        f"- Credential read: `{packet['credential_read']}`\n"
        f"- sendMessage executed: `{packet['sendmessage_executed']}`\n"
        f"- Read-only cockpit: `{packet['is_read_only_cockpit']}`\n"
        f"- Live ready: `{packet['live_ready']}`\n"
        f"- Valid for live execution: `{packet['valid_for_live_execution']}`\n\n"
        f"## Cockpit read model checksum\n\n"
        f"`{packet['cockpit_read_model_checksum']}`\n\n"
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


def build_cockpit_packet_from_repo(repo_root):
    """Load the committed console packet under ``repo_root`` and build the packet."""
    import pathlib
    root = pathlib.Path(repo_root)
    console_packet = load_packet(root / CONSOLE_PACKET_REL)
    return build_cockpit_packet(console_packet)


def write_artifacts(base_dir, packet, doc):
    """Write the cockpit packet + doc under ``base_dir`` ONLY if scanner-clean.

    Returns the list of written absolute paths. Raises ``RuntimeError`` if any
    scanner flags anything, so unsafe artifacts are never persisted. This is the
    ONLY function in this module that touches the filesystem.
    """
    import pathlib
    violations = scan_cockpit(packet, doc)
    if violations:
        raise RuntimeError(
            "refusing to write cockpit artifacts: scan found %d violation(s)"
            % len(violations))
    out_dir = pathlib.Path(base_dir) / DOC_REL_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    packet_path = out_dir / PACKET_FILENAME
    doc_path = out_dir / DOC_FILENAME
    packet_path.write_text(serialize(packet), encoding="utf-8", newline="\n")
    doc_path.write_text(doc, encoding="utf-8", newline="\n")
    return [str(packet_path), str(doc_path)]
