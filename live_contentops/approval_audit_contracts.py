"""Local-only approval ledger, kill-switch, and redacted audit contracts (Task 0079).

Authority READINESS only. This module performs NO network/search/provider/LLM/
platform/credential access. It defines the authority layer later tasks must pass
before any mock (0080) or live (future) publishing path. It NEVER posts, never
implements a mock/live transport, never reads credentials, and never enables
live posting. Audit events are evidence only, not authority to post.
"""

import json
import os
import re

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "..", "schemas")
APPROVAL_SCHEMA_PATH = os.path.join(SCHEMA_DIR, "approval_ledger_record.schema.json")
KILL_SWITCH_SCHEMA_PATH = os.path.join(SCHEMA_DIR, "publish_kill_switch_state.schema.json")
AUDIT_SCHEMA_PATH = os.path.join(SCHEMA_DIR, "redacted_audit_event.schema.json")

# Approval states. None implies live posting is currently enabled.
APPROVAL_STATES = {
    "draft_review_only",
    "platform_dry_run_ready",
    "operator_review_required",
    "operator_approved_for_mock_publish",
    "operator_approved_for_live_publish_later",
    "blocked",
    "revoked",
}

# States that fail closed for any downstream publish path.
FAIL_CLOSED_STATES = {"blocked", "revoked"}

# Synthetic secret-like detection patterns (used to redact/flag test strings).
# These are detection patterns only; this module stores no real secrets.
_SECRET_PATTERNS = [
    r"(?i)\bbearer\s+[A-Za-z0-9._\-]{8,}",
    r"(?i)\b(api[_-]?key|secret[_-]?key|client_secret|access[_-]?token|refresh[_-]?token)\b\s*[:=]\s*\S+",
    r"(?i)\bpassword\b\s*[:=]\s*\S+",
    r"(?i)\bbot_token\b\s*[:=]\s*\S+",
    r"sk-[A-Za-z0-9]{12,}",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
]

_REDACTION_PLACEHOLDER = "[REDACTED]"


def _load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_approval_schema():
    return _load(APPROVAL_SCHEMA_PATH)


def load_kill_switch_schema():
    return _load(KILL_SWITCH_SCHEMA_PATH)


def load_audit_schema():
    return _load(AUDIT_SCHEMA_PATH)


def _scan_secrets(text):
    """Return matched secret-like spans in text (detection only)."""
    hits = []
    for pat in _SECRET_PATTERNS:
        for m in re.finditer(pat, text or ""):
            hits.append(m.group(0))
    return hits


def redact_text(text):
    """Redact secret-like substrings. Returns (redacted_text, found_count)."""
    if not text:
        return text, 0
    redacted = text
    found = 0
    for pat in _SECRET_PATTERNS:
        redacted, n = re.subn(pat, _REDACTION_PLACEHOLDER, redacted)
        found += n
    return redacted, found



# ---------------------------------------------------------------------------
# Approval ledger
# ---------------------------------------------------------------------------

def validate_approval_record(record):
    """Deterministic validation of an approval ledger record.

    Returns {"valid": bool, "errors": [str]}. Never mutates input.
    """
    errors = []

    for field in (
        "approval_id", "source_post_id", "source_draft_packet_id",
        "approval_state", "operator_label", "approval_timestamp_utc",
    ):
        if not record.get(field):
            errors.append("missing_field:%s" % field)

    state = record.get("approval_state")
    if state not in APPROVAL_STATES:
        errors.append("invalid_approval_state:%s" % state)

    if not isinstance(record.get("platform_ids"), list):
        errors.append("platform_ids_must_be_list")

    if record.get("required_manual_review") is not True:
        errors.append("required_manual_review_must_be_true")
    if record.get("live_posting_enabled") is not False:
        errors.append("live_posting_enabled_must_be_false")
    if record.get("credential_accessed") is not False:
        errors.append("credential_accessed_must_be_false")
    if record.get("network_accessed") is not False:
        errors.append("network_accessed_must_be_false")

    if state == "revoked" and not record.get("revocation_of"):
        errors.append("revoked_requires_revocation_of")

    return {"valid": len(errors) == 0, "errors": errors}


def append_approval_record(ledger_path, record):
    """Append a validated approval record to a caller-supplied local JSONL path.

    Append-only. Performs no network access. Raises ValueError if invalid.
    Tests must pass a tmp_path; this module creates no committed runtime ledger.
    """
    result = validate_approval_record(record)
    if not result["valid"]:
        raise ValueError("invalid_approval_record:%s" % result["errors"])
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")
    return record


def read_approval_ledger(ledger_path):
    """Read all approval records from a local JSONL ledger path."""
    records = []
    if not os.path.exists(ledger_path):
        return records
    with open(ledger_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


# ---------------------------------------------------------------------------
# Kill switch
# ---------------------------------------------------------------------------

def default_kill_switch_state(operator_label="system_default"):
    """Return the safe default: disabled/blocking, fail-closed."""
    return {
        "kill_switch_id": "publish_kill_switch_default",
        "enabled": False,
        "blocks_mock_publish": True,
        "blocks_live_publish": True,
        "reason": "default safe state: publishing paths blocked until operator enables",
        "updated_timestamp_utc": "1970-01-01T00:00:00Z",
        "updated_by_operator_label": operator_label,
        "fail_closed": True,
    }


def validate_kill_switch_state(state):
    """Deterministic validation of a kill-switch state."""
    errors = []
    for field in (
        "kill_switch_id", "reason", "updated_timestamp_utc",
        "updated_by_operator_label",
    ):
        if not state.get(field):
            errors.append("missing_field:%s" % field)
    for field in ("enabled", "blocks_mock_publish"):
        if not isinstance(state.get(field), bool):
            errors.append("must_be_bool:%s" % field)
    if state.get("blocks_live_publish") is not True:
        errors.append("blocks_live_publish_must_be_true")
    if state.get("fail_closed") is not True:
        errors.append("fail_closed_must_be_true")
    return {"valid": len(errors) == 0, "errors": errors}


# ---------------------------------------------------------------------------
# Proceed checks (fail closed)
# ---------------------------------------------------------------------------

def can_proceed_to_mock_publish(approval_record, kill_switch_state):
    """Return {"allowed": bool, "reasons": [str]}.

    Allowed only when the approval record is valid and in state
    operator_approved_for_mock_publish AND the kill switch does not block mock.
    Fails closed on any missing/invalid/blocked/revoked input.
    """
    reasons = []

    av = validate_approval_record(approval_record or {})
    if not av["valid"]:
        reasons.append("approval_invalid")
        reasons.extend("approval:%s" % e for e in av["errors"])

    state = (approval_record or {}).get("approval_state")
    if state in FAIL_CLOSED_STATES:
        reasons.append("approval_state_fail_closed:%s" % state)
    elif state != "operator_approved_for_mock_publish":
        reasons.append("approval_state_not_mock_publish:%s" % state)

    kv = validate_kill_switch_state(kill_switch_state or {})
    if not kv["valid"]:
        reasons.append("kill_switch_invalid")
        reasons.extend("kill_switch:%s" % e for e in kv["errors"])

    if (kill_switch_state or {}).get("blocks_mock_publish") is not False:
        reasons.append("kill_switch_blocks_mock_publish")

    return {"allowed": len(reasons) == 0, "reasons": reasons}


def can_proceed_to_live_publish_later(approval_record=None, kill_switch_state=None):
    """Live publishing is NOT implemented or enabled in this task.

    Always returns allowed=false. This is intentional and unconditional.
    """
    return {
        "allowed": False,
        "reasons": ["live_publish_not_implemented_or_enabled_in_this_task"],
    }



# ---------------------------------------------------------------------------
# Redacted audit events
# ---------------------------------------------------------------------------

def build_redacted_audit_event(
    audit_event_id,
    event_type,
    source_post_id,
    decision,
    platform_id=None,
    approval_id=None,
    dry_run_payload_id=None,
    request_payload=None,
    response_payload=None,
    warnings=None,
    blocking_errors=None,
):
    """Build a redacted audit event. Secret-like strings are redacted, never stored raw.

    Evidence only; this never authorizes posting and never accesses network.
    """
    req_red, req_found = redact_text(request_payload) if request_payload else (None, 0)
    resp_red, resp_found = redact_text(response_payload) if response_payload else (None, 0)
    total_found = req_found + resp_found

    event = {
        "audit_event_id": audit_event_id,
        "event_type": event_type,
        "source_post_id": source_post_id,
        "decision": decision,
        "redaction_status": "redacted" if total_found else "clean_no_secret_found",
        "contains_secret": False,
        "raw_secret_detected": False,
        "credential_accessed": False,
        "network_accessed": False,
        "live_posting_enabled": False,
        "warnings": list(warnings or []),
        "blocking_errors": list(blocking_errors or []),
    }
    if platform_id is not None:
        event["platform_id"] = platform_id
    if approval_id is not None:
        event["approval_id"] = approval_id
    if dry_run_payload_id is not None:
        event["dry_run_payload_id"] = dry_run_payload_id
    if req_red is not None:
        event["request_payload_redacted"] = req_red
    if resp_red is not None:
        event["response_payload_redacted"] = resp_red
    return event


def validate_audit_event(event):
    """Deterministic validation of a redacted audit event.

    Fails closed if any persisted redacted payload still contains secret-like
    strings, or if any safety flag is wrong.
    """
    errors = []
    for field in (
        "audit_event_id", "event_type", "source_post_id", "decision",
        "redaction_status",
    ):
        if not event.get(field):
            errors.append("missing_field:%s" % field)

    if event.get("contains_secret") is not False:
        errors.append("contains_secret_must_be_false")
    if event.get("raw_secret_detected") is not False:
        errors.append("raw_secret_detected_must_be_false")
    if event.get("credential_accessed") is not False:
        errors.append("credential_accessed_must_be_false")
    if event.get("network_accessed") is not False:
        errors.append("network_accessed_must_be_false")
    if event.get("live_posting_enabled") is not False:
        errors.append("live_posting_enabled_must_be_false")

    # Persisted redacted payloads must not still contain secret-like strings.
    for field in ("request_payload_redacted", "response_payload_redacted"):
        val = event.get(field)
        if val and _scan_secrets(val):
            errors.append("unredacted_secret_in:%s" % field)

    return {"valid": len(errors) == 0, "errors": errors}


def summary():
    """Local authority-layer summary. No external calls."""
    return {
        "status": "ok",
        "local_only": True,
        "advisory_only": True,
        "approval_ledger_enabled": True,
        "kill_switch_enabled": True,
        "redacted_audit_enabled": True,
        "approval_states": sorted(APPROVAL_STATES),
        "kill_switch_default_blocks_mock": True,
        "kill_switch_default_blocks_live": True,
        "live_publish_possible_now": False,
        "mock_publish_flow_implemented": False,
        "credential_read_allowed_now": False,
        "network_accessed": False,
        "all_outputs_not_public_postable": True,
        "requires_operator_approval": True,
    }

