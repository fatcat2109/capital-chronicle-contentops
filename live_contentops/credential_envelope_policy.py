"""Credential envelope and secret-handling policy design validator (Task 0082).

This module validates operator-supplied credential envelopes, policies, redaction
rules, and rotation checklists. It does NOT read environment variables, touch the
local keychain, load real credentials/tokens, make network calls, or call any
live API. It is design-only; any attempt to set `live_use_allowed_now` or
imply real token access will fail closed during validation.
"""

import json
import os
import re

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "..", "schemas")

def _load(name):
    p = os.path.join(SCHEMA_DIR, name)
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def load_record_schema():
    return _load("credential_envelope_record.schema.json")

def load_policy_schema():
    return _load("credential_policy_pack.schema.json")

def load_redaction_schema():
    return _load("credential_redaction_policy.schema.json")

def load_rotation_schema():
    return _load("credential_rotation_checklist.schema.json")


def validate_record(record):
    """Validate a single credential envelope record. Rejects any attempt
    to authorize live credential access, use true secrets, or read env vars.
    """
    errors = []
    if not isinstance(record, dict):
        return {"valid": False, "errors": ["record_not_object"]}

    pid = record.get("platform_id")
    if not pid:
        errors.append("missing:platform_id")

    # Security / authorization invariants must remain hard-blocked
    for fld in (
        "live_use_allowed_now",
        "credential_value_present",
        "credential_value_stored_in_repo",
        "credential_value_logged",
        "credential_accessed_by_repo",
        "env_read_performed",
        "network_accessed"
    ):
        if record.get(fld) is not False:
            errors.append("%s_must_be_false" % fld)

    # Naming conventions string-checks only; no env reads
    env_vars = record.get("env_var_names")
    if not isinstance(env_vars, list) or not env_vars:
        errors.append("missing:env_var_names")
    else:
        # Check standard uppercase naming convention
        for ev in env_vars:
            if not ev.isupper() or not re.match(r"^[A-Z0-9_]+$", ev):
                errors.append("invalid_env_var_name_format:%s" % ev)

    return {"valid": not errors, "errors": errors}




# ---------------------------------------------------------------------------
# Policy pack, Redaction and Rotation validation
# ---------------------------------------------------------------------------

def validate_policy_pack(pack):
    errors = []
    if not isinstance(pack, dict):
        return {"valid": False, "errors": ["pack_not_object"]}

    for fld in ("pack_id", "platforms", "global_secret_rules"):
        if not pack.get(fld):
            errors.append("missing:%s" % fld)

    if pack.get("no_runtime_credential_access") is not True:
        errors.append("no_runtime_credential_access_must_be_true")
    if pack.get("docs_runtime_authority") is not False:
        errors.append("docs_runtime_authority_must_be_false")

    return {"valid": not errors, "errors": errors}


def validate_redaction_policy(policy):
    errors = []
    if not isinstance(policy, dict):
        return {"valid": False, "errors": ["policy_not_object"]}

    for fld in ("redaction_policy_id", "secret_like_patterns", "replacement_token"):
        if not policy.get(fld):
            errors.append("missing:%s" % fld)

    if policy.get("audit_safe") is not True:
        errors.append("audit_safe_must_be_true")
    if policy.get("blocks_unredacted_secret") is not True:
        errors.append("blocks_unredacted_secret_must_be_true")
    if policy.get("fake_token_test_only") is not True:
        errors.append("fake_token_test_only_must_be_true")

    return {"valid": not errors, "errors": errors}


def validate_rotation_checklist(checklist):
    errors = []
    if not isinstance(checklist, dict):
        return {"valid": False, "errors": ["checklist_not_object"]}

    if not checklist.get("platform_id"):
        errors.append("missing:platform_id")

    if checklist.get("rotation_required_before_live") is not True:
        errors.append("rotation_required_before_live_must_be_true")
    if checklist.get("revocation_procedure_required_before_live") is not True:
        errors.append("revocation_procedure_required_before_live_must_be_true")

    return {"valid": not errors, "errors": errors}



# ---------------------------------------------------------------------------
# Redactor / Secret Checkers (synthetic-only)
# ---------------------------------------------------------------------------

def has_unredacted_secret(text, patterns):
    """Check if unredacted secret patterns exist in a text string.
    Patterns is a list of regex patterns.
    """
    if not isinstance(text, str):
        return False
    for pat in patterns:
        if re.search(pat, text, re.IGNORECASE):
            return True
    return False


def redact_text(text, patterns, replacement):
    """Redact secret-like patterns in a text string."""
    if not isinstance(text, str):
        return text
    redacted = text
    for pat in patterns:
        redacted = re.sub(pat, replacement, redacted, flags=re.IGNORECASE)
    return redacted

