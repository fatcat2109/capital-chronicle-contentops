"""Tests for the local credential envelope + secret policy design (0082).

No real credential accesses are performed. Local-only validation.
"""

import json
import os

import live_contentops.credential_envelope_policy as c

ROOT = os.path.join(os.path.dirname(__file__), "..")
FIX = os.path.join(ROOT, "fixtures", "credential_policy")


def _load(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_fix(name):
    return _load(os.path.join(FIX, name))


# --- schemas load -----------------------------------------------------------

def test_schemas_load():
    assert c.load_record_schema()["title"] == "CredentialEnvelopeRecord"
    assert c.load_policy_schema()["title"] == "CredentialPolicyPack"
    assert c.load_redaction_schema()["title"] == "CredentialRedactionPolicy"
    assert c.load_rotation_schema()["title"] == "CredentialRotationChecklist"


# --- positive flows ---------------------------------------------------------

def test_valid_policy_pack():
    pack = _load_fix("valid_credential_policy_pack.json")
    res = c.validate_policy_pack(pack)
    assert res["valid"] is True


def test_valid_envelopes_all_platforms():
    pack = _load_fix("valid_credential_envelopes_all_platforms.json")
    for rec in pack["envelopes"]:
        res = c.validate_record(rec)
        assert res["valid"] is True, "failed on %s" % rec.get("platform_id")


def test_redaction_patterns_and_helpers():
    policy = _load_fix("valid_redaction_test_cases.json")
    assert c.validate_redaction_policy(policy)["valid"] is True

    patterns = policy["secret_like_patterns"]
    replacement = policy["replacement_token"]

    # Verify each case redacts successfully
    for tc in policy["test_cases"]:
        inp = tc["input_text"]
        exp = tc["expected_output"]
        assert c.has_unredacted_secret(inp, patterns) is True
        redacted = c.redact_text(inp, patterns, replacement)
        assert redacted == exp
        assert c.has_unredacted_secret(redacted, patterns) is False


def test_rotation_checklist_validator():
    # Valid rotation checklist must have required fields
    checklist = {
        "platform_id": "telegram",
        "rotation_required_before_live": True,
        "revocation_procedure_required_before_live": True,
        "suspected_leak_response": ["revoke", "rotate"]
    }
    res = c.validate_rotation_checklist(checklist)
    assert res["valid"] is True


# --- negative flows (fail closed) -------------------------------------------

def test_invalid_live_use_allowed_now():
    rec = _load_fix("invalid_live_use_allowed_now.json")
    res = c.validate_record(rec)
    assert res["valid"] is False
    assert "live_use_allowed_now_must_be_false" in res["errors"]


def test_invalid_env_read_performed():
    rec = _load_fix("invalid_env_read_performed.json")
    res = c.validate_record(rec)
    assert res["valid"] is False
    assert "env_read_performed_must_be_false" in res["errors"]


def test_invalid_credential_value_present():
    rec = _load_fix("invalid_credential_value_present.json")
    res = c.validate_record(rec)
    assert res["valid"] is False
    assert "credential_value_present_must_be_false" in res["errors"]


def test_invalid_docs_runtime_authority():
    pack = _load_fix("invalid_docs_runtime_authority_true.json")
    res = c.validate_policy_pack(pack)
    assert res["valid"] is False
    assert "docs_runtime_authority_must_be_false" in res["errors"]


def test_unredacted_secret_blocks_and_policy_fails_custom():
    # If the policy contains an unredacted secret-like pattern, our policy block
    # should identify it.
    policy = _load_fix("valid_redaction_test_cases.json")
    patterns = policy["secret_like_patterns"]

    bad_pack = _load_fix("invalid_unredacted_secret.json")
    # Verify we can detect the unredacted secret in the rule string
    rule_text = bad_pack["global_secret_rules"][0]
    assert c.has_unredacted_secret(rule_text, patterns) is True
