"""Tests for the platform payload compiler v2 (SCD, 0174BN).

Local-only, deterministic. Verifies registry-parity, per-platform shape routing,
invents-nothing helper semantics, fail-closed precedence, global no-live
invariants, alias mapping, and a data-driven hostile/degraded harness.
"""
import json
import os

import pytest

from live_contentops.scd_domain_model import (
    PASS,
    BLOCKED,
    REVIEW_REQUIRED,
    UNKNOWN,
)
from live_contentops.scd_platform_capability_registry_v2 import (
    APPROVED_PLATFORM_IDS_V2,
)
from live_contentops.scd_platform_payload_compiler_v2 import (
    APPROVED_PLATFORMS_V2,
    PLATFORM_ALIAS_V2,
    PLATFORM_HARD_MAX_V2,
    MANUAL_EXPORT_PLATFORMS_V2,
    HIGH_FRICTION_REVIEW_PLATFORMS_V2,
    PLATFORM_PAYLOAD_COMPILER_V2_VALIDATORS,
    normalize_platform_id_v2,
    shape_for_platform_v2,
    compile_platform_payloads_v2,
    rollup_compile_report_v2,
    validate_platform_constraint_profile_v2,
    validate_platform_payload_compiler_v2_input,
    validate_platform_payload_compiler_v2_output,
    validate_platform_payload_compile_report_v2,
)

FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "fixtures",
    "scd_platform_payload_compiler_v2",
)


def _load(name):
    with open(os.path.join(FIXTURE_DIR, name), "r", encoding="utf-8") as handle:
        return json.load(handle)


# --- Registry parity ----------------------------------------------------------------

def test_approved_platforms_match_registry():
    assert tuple(APPROVED_PLATFORMS_V2) == tuple(APPROVED_PLATFORM_IDS_V2)
    assert len(APPROVED_PLATFORMS_V2) == 9


def test_hard_max_table_covers_every_platform():
    assert set(PLATFORM_HARD_MAX_V2) == set(APPROVED_PLATFORMS_V2)


# --- Shape routing --------------------------------------------------------------------

@pytest.mark.parametrize("platform_id", MANUAL_EXPORT_PLATFORMS_V2)
def test_manual_export_platforms_route_manual(platform_id):
    assert shape_for_platform_v2(platform_id) == "manual_export"


@pytest.mark.parametrize(
    "platform_id",
    [p for p in APPROVED_PLATFORMS_V2 if p not in MANUAL_EXPORT_PLATFORMS_V2],
)
def test_non_manual_platforms_route_dry_run(platform_id):
    assert shape_for_platform_v2(platform_id) == "dry_run"


# --- Alias mapping --------------------------------------------------------------------

def test_newsletter_alias_maps_to_substack():
    assert normalize_platform_id_v2("newsletter") == "substack_newsletter"


def test_x_alias_maps_to_x_twitter():
    assert normalize_platform_id_v2("x") == "x_twitter"
    assert normalize_platform_id_v2("twitter") == "x_twitter"


def test_alias_table_targets_are_all_approved():
    for target in PLATFORM_ALIAS_V2.values():
        assert target in APPROVED_PLATFORMS_V2


# --- Constraint profiles --------------------------------------------------------------

def test_constraint_profiles_fixture_states():
    profiles = _load("constraint_profiles_v2_valid.json")
    by_id = {p["platform_id"]: p for p in profiles}
    assert set(by_id) == set(APPROVED_PLATFORMS_V2)
    for platform_id, profile in by_id.items():
        result = validate_platform_constraint_profile_v2(profile)
        if platform_id in HIGH_FRICTION_REVIEW_PLATFORMS_V2:
            assert result["validation_state"] == REVIEW_REQUIRED
        else:
            assert result["validation_state"] == PASS


# --- Valid input/output/report --------------------------------------------------------

def test_valid_all_platforms_input_passes():
    packet = _load("compiler_v2_input_valid_all_platforms.json")
    result = validate_platform_payload_compiler_v2_input(packet)
    assert result["validation_state"] in (PASS, REVIEW_REQUIRED)
    assert result["validation_state"] != BLOCKED


def test_alias_input_normalizes_without_unknown():
    packet = _load("compiler_v2_input_aliases_valid.json")
    result = validate_platform_payload_compiler_v2_input(packet)
    assert result["validation_state"] != UNKNOWN
    assert result["validation_state"] != BLOCKED


def test_valid_all_platforms_output_not_blocked():
    packet = _load("compiler_v2_output_valid_all_platforms.json")
    result = validate_platform_payload_compiler_v2_output(packet)
    assert result["validation_state"] != BLOCKED


def test_review_required_report_state():
    packet = _load("compiler_v2_report_valid_review_required.json")
    result = validate_platform_payload_compile_report_v2(packet)
    assert result["validation_state"] == REVIEW_REQUIRED


def test_pass_manual_only_report_state():
    packet = _load("compiler_v2_report_valid_pass_manual_only.json")
    result = validate_platform_payload_compile_report_v2(packet)
    assert result["validation_state"] == PASS


# --- Invents-nothing helper -----------------------------------------------------------

def test_compile_helper_invents_nothing():
    profiles = _load("constraint_profiles_v2_valid.json")
    packet = _load("compiler_v2_input_valid_all_platforms.json")
    candidates = compile_platform_payloads_v2(packet, profiles)
    assert candidates
    for candidate in candidates:
        # text carried verbatim, nothing invented
        assert candidate["text"] == packet["source_text"]
        assert candidate["citations"] == list(packet["source_citations"])
        assert candidate["limitations"] == list(packet["source_limitations"])
        assert candidate["hashtags"] == []
        assert candidate["links"] == []
        # global flags never granted
        assert candidate["public_ready"] is False
        assert candidate["live_eligibility"] is False
        assert candidate["operator_review_required"] is True
        # shape routed by platform
        assert candidate["payload_shape"] == shape_for_platform_v2(candidate["platform_id"])
        assert candidate["mode"] == candidate["payload_shape"]


def test_compile_helper_overflow_flagged_not_truncated():
    profiles = _load("constraint_profiles_v2_valid.json")
    long_text = "x" * 5000
    packet = {
        "compiler_input_id": "cin_of",
        "canonical_post_id": "cp_of",
        "editorial_output_id": "eo_of",
        "source_text": long_text,
        "source_limitations": ["preliminary"],
        "source_citations": ["cite:ref-1"],
        "requested_platforms": ["x_twitter"],
        "operator_review_required": True,
    }
    candidates = compile_platform_payloads_v2(packet, profiles)
    x_candidate = next(c for c in candidates if c["platform_id"] == "x_twitter")
    # text not truncated; overflow visible via count vs limit
    assert x_candidate["text"] == long_text
    assert x_candidate["character_count"] == 5000
    assert x_candidate["character_count"] > x_candidate["character_limit_max"]


# --- Rollup precedence ----------------------------------------------------------------

def test_rollup_blocks_when_any_blocked():
    assert rollup_compile_report_v2([PASS, BLOCKED, PASS]) == BLOCKED


def test_rollup_unknown_over_review():
    assert rollup_compile_report_v2([REVIEW_REQUIRED, UNKNOWN]) == UNKNOWN


def test_rollup_empty_is_unknown():
    assert rollup_compile_report_v2([]) == UNKNOWN


def test_rollup_all_pass():
    assert rollup_compile_report_v2([PASS, PASS]) == PASS


# --- Global no-live invariants across all valid fixtures ------------------------------

def _iter_bool_flags(node):
    if isinstance(node, dict):
        for key, val in node.items():
            yield key, val
            yield from _iter_bool_flags(val)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_bool_flags(item)


@pytest.mark.parametrize(
    "fixture_name",
    [
        "compiler_v2_input_valid_all_platforms.json",
        "compiler_v2_input_aliases_valid.json",
        "compiler_v2_output_valid_all_platforms.json",
        "compiler_v2_report_valid_review_required.json",
        "compiler_v2_report_valid_pass_manual_only.json",
        "constraint_profiles_v2_valid.json",
    ],
)
def test_valid_fixtures_never_enable_live(fixture_name):
    data = _load(fixture_name)
    forbidden_true = {
        "public_ready",
        "live_eligibility",
        "live_ready",
        "dispatch_ready",
        "live_api_enabled_now",
        "platform_api_allowed_now",
        "credential_read_allowed_now",
        "credentials_requested_now",
        "posting_enabled_now",
        "scheduler_enabled_now",
        "autonomous_replies_enabled_now",
        "dms_enabled_now",
        "scraping_enabled_now",
    }
    for key, val in _iter_bool_flags(data):
        if key in forbidden_true:
            assert val is not True, f"{fixture_name}:{key} must not be true"


# --- Data-driven hostile / degraded harness ------------------------------------------

def test_hostile_cases_fail_closed():
    cases = _load("hostile_degraded_cases.json")["cases"]
    assert cases
    for case in cases:
        validator = PLATFORM_PAYLOAD_COMPILER_V2_VALIDATORS[case["kind"]]
        result = validator(case["packet"])
        assert result["validation_state"] == case["expected_state"], (
            f"{case['case_id']}: expected {case['expected_state']}, "
            f"got {result['validation_state']} ({result['reasons']})"
        )
        # a hostile case may never resolve to PASS
        assert result["validation_state"] != PASS
