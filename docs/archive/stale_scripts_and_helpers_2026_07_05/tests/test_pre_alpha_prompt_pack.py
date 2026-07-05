"""Tests for the local-only pre-alpha prompt pack + style profile layer (Task 0096).

Deterministic, repo-local. No network/provider/LLM/credential access.
"""

import json
import os

import pytest

from live_contentops import pre_alpha_prompt_pack as pp

FIX_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "pre_alpha_prompt_pack")


def _fix(name):
    return os.path.abspath(os.path.join(FIX_DIR, name))


# ---------------------------------------------------------------------------
# Schemas exist and are valid JSON
# ---------------------------------------------------------------------------

def test_schemas_exist_and_load():
    assert isinstance(pp.load_prompt_pack_schema(), dict)
    assert isinstance(pp.load_style_profile_schema(), dict)
    assert isinstance(pp.load_editorial_rubric_schema(), dict)


# ---------------------------------------------------------------------------
# Valid prompt packs pass
# ---------------------------------------------------------------------------

def test_valid_process_prompt_pack_passes():
    r = pp.validate_prompt_pack_file(_fix("valid_capital_chronicle_process_prompt_pack.json"))
    assert r["valid"] is True, r["errors"]
    assert r["errors"] == []


def test_valid_macro_education_prompt_pack_passes():
    r = pp.validate_prompt_pack_file(_fix("valid_macro_education_prompt_pack.json"))
    assert r["valid"] is True, r["errors"]


def test_valid_prompt_pack_aligns_with_0095_output_contract():
    with open(_fix("valid_capital_chronicle_process_prompt_pack.json"), encoding="utf-8") as f:
        pack = json.load(f)
    contract = pack["output_contract"]
    assert contract["produces"] in ("draft_candidate", "editorial_packet_input")
    assert contract["public_postable"] is False
    assert contract["requires_manual_review"] is True
    for pf in contract["platform_families"]:
        assert pf in pp.ALLOWED_PLATFORM_FAMILIES


# ---------------------------------------------------------------------------
# Invalid prompt packs block
# ---------------------------------------------------------------------------

def test_signal_service_framing_blocked():
    r = pp.validate_prompt_pack_file(_fix("invalid_signal_service_framing.json"))
    assert r["valid"] is False
    assert "prompt_forbidden_framing" in r["errors"]


def test_fake_alpha_prompt_blocked():
    r = pp.validate_prompt_pack_file(_fix("invalid_fake_alpha_prompt.json"))
    assert r["valid"] is False
    assert "prompt_implies_alpha_output" in r["errors"]
    assert "prompt_invents_data_or_claims" in r["errors"]


def test_public_postable_default_blocked():
    r = pp.validate_prompt_pack_file(_fix("invalid_public_postable_default.json"))
    assert r["valid"] is False
    assert "public_postable_default_must_be_false" in r["errors"]



# ---------------------------------------------------------------------------
# Style profile
# ---------------------------------------------------------------------------

def test_valid_style_profile_passes():
    r = pp.validate_style_profile_file(_fix("valid_build_in_public_style_profile.json"))
    assert r["valid"] is True, r["errors"]


def test_style_profile_requires_no_signal_service_framing_true():
    with open(_fix("valid_build_in_public_style_profile.json"), encoding="utf-8") as f:
        profile = json.load(f)
    profile["no_signal_service_framing"] = False
    r = pp.validate_style_profile(profile)
    assert r["valid"] is False
    assert "no_signal_service_framing_must_be_true" in r["errors"]


def test_style_profile_rejects_financial_advice_flag_false():
    with open(_fix("valid_build_in_public_style_profile.json"), encoding="utf-8") as f:
        profile = json.load(f)
    profile["no_financial_advice"] = False
    r = pp.validate_style_profile(profile)
    assert r["valid"] is False
    assert "no_financial_advice_must_be_true" in r["errors"]


def test_style_profile_rejects_unknown_platform_family():
    with open(_fix("valid_build_in_public_style_profile.json"), encoding="utf-8") as f:
        profile = json.load(f)
    profile["platform_family_adaptations"]["telegram"] = "not allowed here"
    r = pp.validate_style_profile(profile)
    assert r["valid"] is False
    assert any(e.startswith("platform_family_not_allowed:") for e in r["errors"])


# ---------------------------------------------------------------------------
# Editorial rubric
# ---------------------------------------------------------------------------

def test_valid_editorial_rubric_passes():
    r = pp.validate_editorial_rubric_file(_fix("valid_pre_alpha_editorial_rubric.json"))
    assert r["valid"] is True, r["errors"]


def test_editorial_rubric_rejects_public_postable_true():
    with open(_fix("valid_pre_alpha_editorial_rubric.json"), encoding="utf-8") as f:
        rubric = json.load(f)
    rubric["public_postable_until_manual_approval"] = True
    r = pp.validate_editorial_rubric(rubric)
    assert r["valid"] is False
    assert "public_postable_until_manual_approval_must_be_false" in r["errors"]


def test_editorial_rubric_requires_manual_review():
    with open(_fix("valid_pre_alpha_editorial_rubric.json"), encoding="utf-8") as f:
        rubric = json.load(f)
    rubric["requires_manual_review_before_publish"] = False
    r = pp.validate_editorial_rubric(rubric)
    assert r["valid"] is False
    assert "requires_manual_review_before_publish_must_be_true" in r["errors"]


# ---------------------------------------------------------------------------
# Summary posture
# ---------------------------------------------------------------------------

def test_summary_posture_is_safe():
    s = pp.summary()
    assert s["local_only"] is True
    assert s["provider_call_made"] is False
    assert s["provider_call_allowed_now"] is False
    assert s["network_call_made"] is False
    assert s["credential_read"] is False
    assert s["fake_alpha_output"] is False
    assert s["public_postable_output"] is False
    assert s["live_execution_allowed_now"] is False
    assert s["manual_review_required"] is True
    assert s["aligns_with_0095_output_contract"] is True
