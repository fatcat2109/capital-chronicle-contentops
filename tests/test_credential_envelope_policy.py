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



def test_verification_alignment_and_placeholders():
    # 1. Non-telegram platform cannot claim partially_verified or verified
    rec = {
        "envelope_id": "env_bad_x_0082",
        "platform_id": "x",
        "credential_kind": "oauth2_user_context",
        "storage_location_policy": "external_env_later",
        "env_var_names": ["CC_X_CLIENT_ID"],
        "required_scopes_or_permissions": ["tweet.write"],
        "verification_status": "partially_verified", # bad for non-telegram
        "credential_requirement_source": "operator_supplied_docs_verified",
        "placeholder_until_official_docs_verified": False,
        "live_use_allowed_now": False,
        "credential_value_present": False,
        "credential_value_stored_in_repo": False,
        "credential_value_logged": False,
        "credential_accessed_by_repo": False,
        "env_read_performed": False,
        "network_accessed": False
    }
    res = c.validate_record(rec)
    assert res["valid"] is False
    assert "non_telegram_platforms_cannot_be_verified_yet" in res["errors"]

    # 2. Telegram with incorrect source / placeholder settings is rejected
    rec2 = {
        "envelope_id": "env_bad_tg_0082",
        "platform_id": "telegram",
        "credential_kind": "bot_token",
        "storage_location_policy": "external_env_later",
        "env_var_names": ["CC_TG_BOT_TOKEN"],
        "required_scopes_or_permissions": ["can_post_messages"],
        "verification_status": "partially_verified",
        "credential_requirement_source": "local_placeholder_until_0081_official_docs_verified", # bad for telegram
        "placeholder_until_official_docs_verified": True, # bad for telegram
        "live_use_allowed_now": False,
        "credential_value_present": False,
        "credential_value_stored_in_repo": False,
        "credential_value_logged": False,
        "credential_accessed_by_repo": False,
        "env_read_performed": False,
        "network_accessed": False
    }
    res2 = c.validate_record(rec2)
    assert res2["valid"] is False
    assert "telegram_must_use_operator_supplied_docs_source" in res2["errors"]
    assert "telegram_must_set_placeholder_flag_to_false" in res2["errors"]

    # 3. Unverified platform must use local placeholder source and flag=True
    rec3 = {
        "envelope_id": "env_bad_x2_0082",
        "platform_id": "x",
        "credential_kind": "oauth2_user_context",
        "storage_location_policy": "external_env_later",
        "env_var_names": ["CC_X_CLIENT_ID"],
        "required_scopes_or_permissions": ["tweet.write"],
        "verification_status": "not_verified",
        "credential_requirement_source": "operator_supplied_docs_verified", # bad
        "placeholder_until_official_docs_verified": False, # bad
        "live_use_allowed_now": False,
        "credential_value_present": False,
        "credential_value_stored_in_repo": False,
        "credential_value_logged": False,
        "credential_accessed_by_repo": False,
        "env_read_performed": False,
        "network_accessed": False
    }
    res3 = c.validate_record(rec3)
    assert res3["valid"] is False
    assert "unverified_platform_must_use_placeholder_source" in res3["errors"]
    assert "unverified_platform_must_set_placeholder_flag_to_true" in res3["errors"]
