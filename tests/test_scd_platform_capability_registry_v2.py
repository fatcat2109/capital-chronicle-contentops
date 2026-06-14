"""Tests for the grounded platform capability registry v2 (SCD, 0174BL).

Local-only, deterministic, fail-closed. Verifies schema shape and per-object
validation states for official doc sources, the verification pack, capability
profiles v2, the future-only credential slot policy, live-gate checklists, the
dry-run payload policy matrix, and the compiler/readiness/redacted-audit
alignment reports.

These contracts model official-doc-backed platform capability metadata only.
They never call platform APIs, read credentials, build clients, schedule work,
dispatch content, scrape, or grant public/live/dispatch readiness. Every
"forbidden now" flag must stay false, and a declared PASS that contradicts the
computed state must fail closed to BLOCKED.

No network, providers, credentials, platform APIs, or live behavior.
"""
import json
import os
from pathlib import Path

from live_contentops import scd_platform_capability_registry_v2 as reg
from live_contentops.scd_platform_payload_compiler import APPROVED_PLATFORMS

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "scd_platform_capability_registry_v2"


def _load(name):
    with open(FIXTURE_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


# --- Official doc sources ---------------------------------------------------------

def test_official_doc_sources_each_pass():
    sources = _load("official_doc_sources_valid.json")
    assert len(sources) == len(reg.APPROVED_PLATFORM_IDS_V2)
    for src in sources:
        res = reg.validate_platform_official_doc_source(src)
        assert res["validation_state"] == reg.PASS, (src["platform_id"], res)


def test_official_doc_source_unofficial_domain_blocks():
    src = _load("official_doc_sources_valid.json")[1]
    src = dict(src)
    src["official_doc_url"] = "https://random-blog.example.net/howto"
    res = reg.validate_platform_official_doc_source(src)
    assert res["validation_state"] == reg.BLOCKED, res


def test_official_doc_source_stale_reviews():
    src = dict(_load("official_doc_sources_valid.json")[2])
    src["retrieved_date"] = "2024-01-01"
    # Declared state must match the computed REVIEW_REQUIRED, otherwise the
    # declared-PASS contradiction guard would (correctly) escalate to BLOCKED.
    src["validation_state"] = reg.REVIEW_REQUIRED
    res = reg.validate_platform_official_doc_source(src)
    assert res["validation_state"] == reg.REVIEW_REQUIRED, res


def test_official_doc_source_runtime_authority_blocks():
    src = dict(_load("official_doc_sources_valid.json")[0])
    src["runtime_authority"] = True
    res = reg.validate_platform_official_doc_source(src)
    assert res["validation_state"] == reg.BLOCKED, res


# --- Verification pack ------------------------------------------------------------

def test_verification_pack_pass():
    res = reg.validate_platform_official_docs_verification_pack(
        _load("official_docs_verification_pack_valid.json")
    )
    assert res["validation_state"] == reg.PASS, res


def test_verification_pack_must_be_advisory_only():
    pack = _load("official_docs_verification_pack_valid.json")
    pack["advisory_only"] = False
    res = reg.validate_platform_official_docs_verification_pack(pack)
    assert res["validation_state"] == reg.BLOCKED, res


def test_verification_pack_runtime_authority_blocks():
    pack = _load("official_docs_verification_pack_valid.json")
    pack["runtime_authority"] = True
    res = reg.validate_platform_official_docs_verification_pack(pack)
    assert res["validation_state"] == reg.BLOCKED, res


# --- Capability profiles v2 -------------------------------------------------------

def test_capability_profiles_states():
    profiles = _load("platform_capability_profiles_v2_valid.json")
    assert len(profiles) == len(reg.APPROVED_PLATFORM_IDS_V2)
    for prof in profiles:
        res = reg.validate_platform_capability_profile_v2(prof)
        # API-backed platforms remain future-gated (REVIEW_REQUIRED); manual-only
        # platforms (no API by design) settle at PASS.
        if prof["platform_id"] in ("substack_newsletter", "generic_manual"):
            assert res["validation_state"] == reg.PASS, (prof["platform_id"], res)
        else:
            assert res["validation_state"] == reg.REVIEW_REQUIRED, (prof["platform_id"], res)


def test_capability_profile_live_enabled_blocks():
    prof = dict(_load("platform_capability_profiles_v2_valid.json")[1])
    prof["live_api_enabled_now"] = True
    res = reg.validate_platform_capability_profile_v2(prof)
    assert res["validation_state"] == reg.BLOCKED, res


def test_capability_profile_public_ready_blocks():
    prof = dict(_load("platform_capability_profiles_v2_valid.json")[1])
    prof["public_ready"] = True
    res = reg.validate_platform_capability_profile_v2(prof)
    assert res["validation_state"] == reg.BLOCKED, res


def test_capability_profile_missing_docs_unknown():
    prof = dict(_load("platform_capability_profiles_v2_valid.json")[1])
    prof["official_doc_source_ids"] = []
    prof["validation_state"] = reg.UNKNOWN
    res = reg.validate_platform_capability_profile_v2(prof)
    assert res["validation_state"] == reg.UNKNOWN, res


def test_capability_profile_declared_pass_with_no_docs_blocks():
    prof = dict(_load("platform_capability_profiles_v2_valid.json")[1])
    prof["official_doc_source_ids"] = []
    prof["validation_state"] = reg.PASS
    res = reg.validate_platform_capability_profile_v2(prof)
    assert res["validation_state"] == reg.BLOCKED, res


# --- Credential slot policy -------------------------------------------------------

def test_credential_slot_policy_pass():
    res = reg.validate_platform_credential_slot_policy(_load("credential_slot_policy_valid.json"))
    assert res["validation_state"] == reg.PASS, res


def test_credential_slot_policy_requested_now_blocks():
    pol = _load("credential_slot_policy_valid.json")
    pol["platform_credential_slots"][0]["credential_requested_now"] = True
    res = reg.validate_platform_credential_slot_policy(pol)
    assert res["validation_state"] == reg.BLOCKED, res


def test_credential_slot_policy_secret_value_blocks():
    pol = _load("credential_slot_policy_valid.json")
    pol["platform_credential_slots"][0]["notes"] = "123456789:AAEhBP0abcdefghijklmnopqrstuvwxyz012345"
    res = reg.validate_platform_credential_slot_policy(pol)
    assert res["validation_state"] == reg.BLOCKED, res


# --- Live gate checklist ----------------------------------------------------------

def test_live_gate_checklist_pass():
    res = reg.validate_platform_live_gate_checklist(_load("live_gate_checklist_valid.json"))
    assert res["validation_state"] == reg.PASS, res


def test_live_gate_checklist_all_pass():
    for chk in _load("live_gate_checklist_all.json"):
        res = reg.validate_platform_live_gate_checklist(chk)
        assert res["validation_state"] == reg.PASS, (chk["platform_id"], res)


def test_live_gate_checklist_dispatch_ready_blocks():
    chk = _load("live_gate_checklist_valid.json")
    chk["dispatch_ready"] = True
    res = reg.validate_platform_live_gate_checklist(chk)
    assert res["validation_state"] == reg.BLOCKED, res


# --- Dry-run payload policy matrix ------------------------------------------------

def test_dry_run_payload_policy_matrix_pass():
    res = reg.validate_platform_dry_run_payload_policy_matrix(
        _load("dry_run_payload_policy_matrix_valid.json")
    )
    assert res["validation_state"] == reg.PASS, res


def test_dry_run_payload_policy_matrix_active_endpoint_blocks():
    matrix = _load("dry_run_payload_policy_matrix_valid.json")
    matrix["platform_policies"][0]["endpoint_family_names_symbolic"] = ["https://api.telegram.org/bot"]
    res = reg.validate_platform_dry_run_payload_policy_matrix(matrix)
    assert res["validation_state"] == reg.BLOCKED, res


# --- Alignment reports ------------------------------------------------------------

def test_registry_compiler_alignment_report_review_required():
    # Registry-only platforms (not yet in the compiler) require future expansion.
    res = reg.validate_platform_registry_compiler_alignment_report(
        _load("registry_compiler_alignment_report_valid.json")
    )
    assert res["validation_state"] == reg.REVIEW_REQUIRED, res


def test_registry_compiler_alignment_report_credential_allowed_blocks():
    rep = _load("registry_compiler_alignment_report_valid.json")
    rep["credential_allowed_now"] = True
    rep["contradictions"] = ["registry_credential_allowed_now"]
    res = reg.validate_platform_registry_compiler_alignment_report(rep)
    assert res["validation_state"] == reg.BLOCKED, res


def test_registry_only_platforms_are_those_outside_compiler():
    rep = _load("registry_compiler_alignment_report_valid.json")
    registry_only = set(rep["registry_only_platform_ids"])
    # Every registry-only platform is genuinely absent from the compiler's set.
    assert registry_only == set(reg.APPROVED_PLATFORM_IDS_V2) - set(APPROVED_PLATFORMS)
    assert registry_only, "expected at least one registry-only platform"


def test_publish_readiness_alignment_report_pass():
    res = reg.validate_platform_publish_readiness_alignment_report(
        _load("publish_readiness_alignment_report_valid.json")
    )
    assert res["validation_state"] == reg.PASS, res


def test_publish_readiness_alignment_report_contradiction_blocks():
    rep = _load("publish_readiness_alignment_report_valid.json")
    rep["forbidden_now_flags_confirmed_false"][0]["confirmed_false"] = False
    rep["contradiction_count"] = 1
    rep["contradictions"] = [rep["forbidden_now_flags_confirmed_false"][0]["flag"]]
    res = reg.validate_platform_publish_readiness_alignment_report(rep)
    assert res["validation_state"] == reg.BLOCKED, res


def test_redacted_audit_alignment_report_pass():
    res = reg.validate_platform_redacted_audit_alignment_report(
        _load("redacted_audit_alignment_report_valid.json")
    )
    assert res["validation_state"] == reg.PASS, res


def test_redacted_audit_alignment_report_api_called_blocks():
    rep = _load("redacted_audit_alignment_report_valid.json")
    rep["platform_api_called"] = True
    rep["contradiction_count"] = 1
    rep["contradictions"] = ["platform_api_called"]
    res = reg.validate_platform_redacted_audit_alignment_report(rep)
    assert res["validation_state"] == reg.BLOCKED, res


# --- Data-driven hostile / degraded cases -----------------------------------------

def test_hostile_degraded_cases_match_expected_states():
    cases = _load("hostile_degraded_cases.json")
    assert cases, "expected hostile fixture cases"
    for case in cases:
        validator = reg.PLATFORM_CAPABILITY_REGISTRY_V2_VALIDATORS[case["validator"]]
        res = validator(case["packet"])
        assert res["validation_state"] == case["expected_state"], (case["name"], res)


# --- Registry summary rollup ------------------------------------------------------

def test_registry_v2_summary_rolls_up_to_review_required():
    pack = _load("official_docs_verification_pack_valid.json")
    profiles = _load("platform_capability_profiles_v2_valid.json")
    cred_policy = _load("credential_slot_policy_valid.json")
    checklists = _load("live_gate_checklist_all.json")
    matrix = _load("dry_run_payload_policy_matrix_valid.json")
    reports = [
        _load("registry_compiler_alignment_report_valid.json"),
        _load("publish_readiness_alignment_report_valid.json"),
        _load("redacted_audit_alignment_report_valid.json"),
    ]
    summary = reg.build_platform_registry_v2_summary(
        pack, profiles, cred_policy, checklists, matrix, reports
    )
    # Future-gated profiles + registry-only compiler gap keep the rollup at
    # REVIEW_REQUIRED; nothing here may PASS outright or BLOCK.
    assert summary["validation_state"] == reg.REVIEW_REQUIRED, summary


# --- Global flag invariants -------------------------------------------------------

def test_no_profile_fixture_grants_forbidden_now_flags():
    for prof in _load("platform_capability_profiles_v2_valid.json"):
        for flag in reg.REQUIRED_DISABLED_FLAGS:
            assert prof.get(flag) is False, (prof["platform_id"], flag)


def test_no_fixture_file_contains_runtime_authority():
    for fname in os.listdir(FIXTURE_DIR):
        if not fname.endswith(".json"):
            continue
        data = _load(fname)
        nodes = data if isinstance(data, list) else [data]
        for node in nodes:
            if isinstance(node, dict) and "runtime_authority" in node:
                assert node["runtime_authority"] is False, fname
