"""Render golden-snapshot / binding-conformance validators (SCD, 0174AX).

Local-only, deterministic, fail-closed. This module defines the CONTRACT and
VALIDATION for freezing expected render-spec outputs (0174AW) into canonical-JSON
golden snapshots and verifying that actual render-spec output conforms to them.
It is a data contract, not UI: no HTML/CSS/JS, no DOM, no browser, no screenshots,
no network, no providers, no credentials, no scheduler, no live dispatch. The
helpers only compare/transform supplied local dictionaries.

Domain objects validated here:

    SCDRenderGoldenSnapshotInput
    SCDRenderGoldenSnapshot
    SCDRenderBindingConformanceResult
    SCDRenderGoldenSnapshotManifest
    SCDRenderGoldenSnapshotReport

Validators return {"validation_state": <STATE>, "reasons": [...]}.
"""
from live_contentops.scd_domain_model import (
    PASS,
    BLOCKED,
    REVIEW_REQUIRED,
    UNKNOWN,
    _schema_ok,
    _scan_secrets,
    _result,
)
# Reuse the established deterministic canonical hash helper (sorted keys, stable
# separators, UTF-8). Single source of hashing truth across the SCD chain.
from live_contentops.scd_dispatch_gate import canonical_json_sha256
# Reuse the 0174AW unsafe-string scanner (forbidden language, invented authority,
# telegram/api, network/oauth, html/css/js/dom/browser-runtime implications).
from live_contentops.scd_operator_replay_console_render_spec import _scan_all_strings

REQUIRED_REPLAY_STATES = (PASS, BLOCKED, REVIEW_REQUIRED, UNKNOWN)

# Readiness flags that must never be true on any 0174AX object.
FORBIDDEN_READY_FLAGS = ("public_ready", "live_ready", "executable_dispatch", "live_eligibility")

# Allow_* flags on the input packet; all must be false.
FORBIDDEN_ALLOW_FLAGS = (
    "allow_ui_runtime",
    "allow_browser",
    "allow_screenshot",
    "allow_html_css_js",
    "allow_network",
    "allow_credentials",
    "allow_platform_api",
    "allow_live_dispatch",
)

# UI-runtime requirement flags that must be false where present.
FORBIDDEN_UI_REQUIRED_FLAGS = (
    "ui_runtime_required",
    "browser_required",
    "screenshot_required",
    "html_css_js_required",
)

# Affirmative no_* assertions that must be true where present.
REQUIRED_NO_FLAGS = (
    "no_ui_runtime_required",
    "no_browser_required",
    "no_screenshot_required",
    "no_html_css_js_edits",
    "no_api_required",
)


def _ready_flag_blocks(payload):
    return [f"{flag} must be false" for flag in FORBIDDEN_READY_FLAGS if payload.get(flag)]


def _common_display_blocks(payload):
    """Shared display-only invariants for golden-snapshot objects."""
    blocked = []
    blocked += _ready_flag_blocks(payload)
    blocked += _scan_secrets(payload)
    blocked += _scan_all_strings(payload)
    if "display_only" in payload and payload.get("display_only") is not True:
        blocked.append("display_only must be true")
    if "action_enabled" in payload and payload.get("action_enabled"):
        blocked.append("action_enabled must be false")
    if "manual_publish_only" in payload and payload.get("manual_publish_only") is not True:
        blocked.append("manual_publish_only must be true")
    if "mock_only" in payload and payload.get("mock_only") is not True:
        blocked.append("mock_only must be true")
    if payload.get("api_gate_required"):
        blocked.append("api_gate_required must be false")
    for flag in FORBIDDEN_UI_REQUIRED_FLAGS:
        if flag in payload and payload.get(flag):
            blocked.append(f"{flag} must be false")
    for flag in REQUIRED_NO_FLAGS:
        if flag in payload and payload.get(flag) is not True:
            blocked.append(f"{flag} must be true")
    return blocked


def validate_render_golden_snapshot_input(payload):
    ok, msg = _schema_ok(payload, "scd_render_golden_snapshot_input.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []
    blocked += _common_display_blocks(payload)

    for flag in FORBIDDEN_ALLOW_FLAGS:
        if payload.get(flag):
            blocked.append(f"{flag} must be false")

    if payload.get("expected_hash_algorithm") != "canonical_json_sha256":
        blocked.append("expected_hash_algorithm must be canonical_json_sha256")

    if payload.get("replay_state") not in REQUIRED_REPLAY_STATES:
        blocked.append(f"unrecognized replay_state: {payload.get('replay_state')}")

    # Missing source refs make conformance lineage unknown (fail-closed, not PASS).
    if not payload.get("golden_snapshot_ref"):
        unknown.append("missing golden_snapshot_ref")
    if not payload.get("actual_render_spec_ref"):
        unknown.append("missing actual_render_spec_ref")

    return _result(blocked, review, unknown)


def validate_render_golden_snapshot(payload):
    ok, msg = _schema_ok(payload, "scd_render_golden_snapshot.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []
    blocked += _common_display_blocks(payload)

    if payload.get("current_vs_historical_truth_binding_present") is not True:
        blocked.append("current_vs_historical_truth_binding_present must be true")

    # Hash must be present and equal the canonical hash of snapshot_payload.
    declared = payload.get("canonical_json_sha256")
    snapshot_payload = payload.get("snapshot_payload")
    if not declared:
        blocked.append("missing canonical_json_sha256")
    elif snapshot_payload is None:
        unknown.append("missing snapshot_payload; cannot verify hash")
    else:
        recomputed = canonical_json_sha256(snapshot_payload)
        if declared != recomputed:
            blocked.append("canonical_json_sha256 does not match snapshot_payload")

    if payload.get("replay_state") not in REQUIRED_REPLAY_STATES:
        blocked.append(f"unrecognized replay_state: {payload.get('replay_state')}")

    if not payload.get("render_spec_id"):
        unknown.append("missing render_spec_id")

    return _result(blocked, review, unknown)


def validate_render_binding_conformance_result(payload):
    ok, msg = _schema_ok(payload, "scd_render_binding_conformance_result.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []
    blocked += _common_display_blocks(payload)

    if payload.get("mutation_detected"):
        blocked.append("mutation_detected must be false")

    # Any divergence set being non-empty blocks the result.
    for field in ("missing_regions", "extra_regions", "missing_display_slots",
                  "extra_display_slots", "missing_status_tokens", "extra_status_tokens",
                  "mismatched_bindings"):
        if payload.get(field):
            blocked.append(f"{field} is non-empty")

    if payload.get("canonical_json_match") is not True:
        blocked.append("canonical_json_match must be true")
    if payload.get("structural_binding_match") is not True:
        blocked.append("structural_binding_match must be true")

    # If hashes are both present they must agree with the match claim.
    exp = payload.get("expected_canonical_json_sha256")
    act = payload.get("actual_canonical_json_sha256")
    if exp and act and (exp == act) is not bool(payload.get("canonical_json_match")):
        blocked.append("canonical_json_match contradicts expected/actual hashes")

    if not payload.get("golden_snapshot_id"):
        unknown.append("missing golden_snapshot_id")

    return _result(blocked, review, unknown)


def validate_render_golden_snapshot_manifest(payload):
    ok, msg = _schema_ok(payload, "scd_render_golden_snapshot_manifest.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []
    blocked += _common_display_blocks(payload)

    if payload.get("canonical_hash_algorithm") != "canonical_json_sha256":
        blocked.append("canonical_hash_algorithm must be canonical_json_sha256")
    if payload.get("mutation_after_freeze_detected"):
        blocked.append("mutation_after_freeze_detected must be true is forbidden")

    covered = payload.get("replay_states_covered", []) or []
    missing_states = [s for s in REQUIRED_REPLAY_STATES if s not in covered]
    if missing_states:
        blocked.append(f"missing required replay states: {missing_states}")
    if payload.get("all_required_states_covered") is not True:
        blocked.append("all_required_states_covered must be true")
    if payload.get("all_hashes_present") is not True:
        blocked.append("all_hashes_present must be true")

    # Evidence completeness is non-blocking review/unknown.
    if payload.get("evidence_complete") is not True:
        review.append("evidence_complete is not true")
    if payload.get("missing_evidence_refs"):
        review.append("missing_evidence_refs is non-empty")
    if not payload.get("snapshot_refs"):
        unknown.append("no snapshot_refs")

    return _result(blocked, review, unknown)


def validate_render_golden_snapshot_report(payload):
    ok, msg = _schema_ok(payload, "scd_render_golden_snapshot_report.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []
    blocked += _common_display_blocks(payload)

    rec = payload.get("final_recommendation")
    failed_hash = payload.get("failed_hash_matches", []) or []
    failed_struct = payload.get("failed_structural_matches", []) or []
    mutations = payload.get("mutation_detected_refs", []) or []
    blocked_results = payload.get("blocked_results", []) or []
    missing_states = payload.get("missing_required_replay_states", []) or []
    unknown_results = payload.get("unknown_results", []) or []
    review_results = payload.get("review_required_results", []) or []

    # Fail-closed precedence: BLOCKED > UNKNOWN > REVIEW_REQUIRED > PASS.
    if failed_hash or failed_struct or mutations or blocked_results:
        expected = BLOCKED
    elif missing_states or unknown_results:
        expected = UNKNOWN
    elif review_results:
        expected = REVIEW_REQUIRED
    else:
        expected = PASS

    if rec == PASS and expected != PASS:
        blocked.append(f"final PASS contradicts roll-up (expected {expected})")
    if expected == BLOCKED and rec != BLOCKED:
        blocked.append("blocking conditions present; final must be BLOCKED")
    if rec == PASS and payload.get("display_contract_locked") is not True:
        blocked.append("final PASS requires display_contract_locked true")
    if rec == PASS and payload.get("all_required_states_covered") is not True:
        blocked.append("final PASS requires all_required_states_covered true")
    if rec not in REQUIRED_REPLAY_STATES:
        blocked.append(f"invalid final_recommendation: {rec}")

    if not payload.get("golden_snapshot_manifest_id"):
        unknown.append("missing golden_snapshot_manifest_id")

    if not blocked:
        if expected == UNKNOWN:
            unknown.append("missing required states or unknown results")
        elif expected == REVIEW_REQUIRED:
            review.append("non-blocking review-required results present")

    return _result(blocked, review, unknown)


# --- Deterministic local helpers -----------------------------------------------------

def freeze_render_golden_snapshot(render_spec, replay_state, source_fixture_refs=None):
    """Freeze a render spec into a deterministic golden snapshot.

    Invents nothing: the snapshot_payload is the supplied render_spec, and the
    canonical hash is computed over it via the shared canonical_json_sha256.
    No I/O, no network, no UI/browser/screenshot requirement is created.
    """
    payload = render_spec
    return {
        "schema_version": "1.0",
        "golden_snapshot_id": "gs_" + render_spec.get("render_spec_id", "unknown"),
        "render_spec_id": render_spec.get("render_spec_id", ""),
        "view_model_id": render_spec.get("view_model_id", ""),
        "replay_state": replay_state,
        "snapshot_payload": payload,
        "canonical_json_sha256": canonical_json_sha256(payload),
        "frozen_at": "deterministic",
        "source_fixture_refs": list(source_fixture_refs or []),
        "render_spec_report_ref": "",
        "layout_region_count": len(render_spec.get("layout_regions", []) or []),
        "display_slot_binding_count": len(render_spec.get("display_slot_bindings", []) or []),
        "status_token_binding_count": len(render_spec.get("status_token_bindings", []) or []),
        "current_vs_historical_truth_binding_present": bool(
            render_spec.get("current_vs_historical_truth_binding")
        ),
        "display_only": True,
        "action_enabled": False,
        "ui_runtime_required": False,
        "browser_required": False,
        "screenshot_required": False,
        "html_css_js_required": False,
        "public_ready": False,
        "live_ready": False,
        "executable_dispatch": False,
        "api_gate_required": False,
        "validation_state": PASS,
    }


def compare_render_spec_to_golden_snapshot(actual_render_spec, golden_snapshot):
    """Compare an actual render spec against a frozen golden snapshot.

    Pure structural + canonical-hash comparison. Detects mutation by recomputing
    the canonical hash of the golden's stored payload and comparing to its frozen
    hash. Invents no refs, URLs, credentials, endpoints, tokens, or UI actions.
    """
    expected_hash = golden_snapshot.get("canonical_json_sha256", "")
    actual_hash = canonical_json_sha256(actual_render_spec)
    frozen_payload = golden_snapshot.get("snapshot_payload", {})
    recomputed = canonical_json_sha256(frozen_payload)
    mutation = recomputed != expected_hash

    def _set(spec, key):
        return set(spec.get(key, []) or [])

    exp_regions = _set(frozen_payload, "layout_regions")
    act_regions = _set(actual_render_spec, "layout_regions")
    exp_slots = _set(frozen_payload, "display_slot_bindings")
    act_slots = _set(actual_render_spec, "display_slot_bindings")
    exp_tokens = _set(frozen_payload, "status_token_bindings")
    act_tokens = _set(actual_render_spec, "status_token_bindings")

    missing_regions = sorted(exp_regions - act_regions)
    extra_regions = sorted(act_regions - exp_regions)
    missing_slots = sorted(exp_slots - act_slots)
    extra_slots = sorted(act_slots - exp_slots)
    missing_tokens = sorted(exp_tokens - act_tokens)
    extra_tokens = sorted(act_tokens - exp_tokens)

    structural_match = not (missing_regions or extra_regions or missing_slots
                            or extra_slots or missing_tokens or extra_tokens)
    canonical_match = (actual_hash == expected_hash) and not mutation

    return {
        "schema_version": "1.0",
        "conformance_result_id": "cr_" + golden_snapshot.get("golden_snapshot_id", "unknown"),
        "golden_snapshot_id": golden_snapshot.get("golden_snapshot_id", ""),
        "actual_render_spec_id": actual_render_spec.get("render_spec_id", ""),
        "replay_state": golden_snapshot.get("replay_state", UNKNOWN),
        "conformance_mode": "exact_canonical_json",
        "expected_canonical_json_sha256": expected_hash,
        "actual_canonical_json_sha256": actual_hash,
        "canonical_json_match": canonical_match,
        "structural_binding_match": structural_match,
        "missing_regions": missing_regions,
        "extra_regions": extra_regions,
        "missing_display_slots": missing_slots,
        "extra_display_slots": extra_slots,
        "missing_status_tokens": missing_tokens,
        "extra_status_tokens": extra_tokens,
        "mismatched_bindings": [],
        "mutation_detected": mutation,
        "display_only": True,
        "action_enabled": False,
        "ui_runtime_required": False,
        "browser_required": False,
        "screenshot_required": False,
        "html_css_js_required": False,
        "public_ready": False,
        "live_ready": False,
        "executable_dispatch": False,
        "api_gate_required": False,
        "validation_state": PASS if (canonical_match and structural_match) else BLOCKED,
    }


def build_golden_snapshot_manifest(snapshots, snapshot_set_version="v1"):
    """Build a deterministic manifest over a list of golden snapshots.

    Invents nothing: derives covered states and refs from the supplied snapshots.
    No I/O, no network, no UI/browser/screenshot requirement is created.
    """
    snapshot_refs = [s.get("golden_snapshot_id", "") for s in snapshots]
    hash_refs = [s.get("canonical_json_sha256", "") for s in snapshots]
    covered = sorted({s.get("replay_state") for s in snapshots if s.get("replay_state")})
    all_present = bool(snapshots) and all(hash_refs) and len(hash_refs) == len(snapshots)
    all_states = set(REQUIRED_REPLAY_STATES).issubset(set(covered))
    complete = all_states and all_present
    return {
        "schema_version": "1.0",
        "golden_snapshot_manifest_id": "gsm_" + snapshot_set_version,
        "snapshot_set_version": snapshot_set_version,
        "snapshot_refs": snapshot_refs,
        "replay_states_covered": covered,
        "snapshot_hash_refs": hash_refs,
        "fixture_refs": [],
        "validator_refs": ["validate_render_golden_snapshot"],
        "test_refs": ["tests/test_scd_render_golden_snapshot.py"],
        "canonical_hash_algorithm": "canonical_json_sha256",
        "all_required_states_covered": all_states,
        "all_hashes_present": all_present,
        "mutation_after_freeze_detected": False,
        "evidence_complete": complete,
        "missing_evidence_refs": [],
        "display_only": True,
        "action_enabled": False,
        "no_ui_runtime_required": True,
        "no_browser_required": True,
        "no_screenshot_required": True,
        "no_html_css_js_edits": True,
        "no_api_required": True,
        "validation_state": PASS if complete else UNKNOWN,
    }


def build_golden_snapshot_report(manifest, conformance_results):
    """Build a deterministic report rolling up supplied conformance results.

    Fail-closed precedence: BLOCKED > UNKNOWN > REVIEW_REQUIRED > PASS. Invents
    nothing: derives every roll-up array from the supplied results/manifest only.
    """
    def _ids(state):
        return [r.get("conformance_result_id", "") for r in conformance_results
                if r.get("validation_state") == state]

    pass_r = _ids(PASS)
    blocked_r = _ids(BLOCKED)
    review_r = _ids(REVIEW_REQUIRED)
    unknown_r = _ids(UNKNOWN)
    failed_hash = [r.get("conformance_result_id", "") for r in conformance_results
                   if r.get("canonical_json_match") is not True]
    failed_struct = [r.get("conformance_result_id", "") for r in conformance_results
                     if r.get("structural_binding_match") is not True]
    mutations = [r.get("conformance_result_id", "") for r in conformance_results
                 if r.get("mutation_detected")]
    covered = manifest.get("replay_states_covered", []) or []
    missing_states = [s for s in REQUIRED_REPLAY_STATES if s not in covered]

    if blocked_r or failed_hash or failed_struct or mutations:
        rec = BLOCKED
    elif missing_states or unknown_r:
        rec = UNKNOWN
    elif review_r:
        rec = REVIEW_REQUIRED
    else:
        rec = PASS
    locked = rec == PASS and not missing_states
    return {
        "schema_version": "1.0",
        "golden_snapshot_report_id": "gsr_" + manifest.get("snapshot_set_version", "v1"),
        "golden_snapshot_manifest_id": manifest.get("golden_snapshot_manifest_id", ""),
        "conformance_results": [r.get("conformance_result_id", "") for r in conformance_results],
        "pass_results": pass_r,
        "blocked_results": blocked_r,
        "review_required_results": review_r,
        "unknown_results": unknown_r,
        "missing_required_replay_states": missing_states,
        "failed_hash_matches": failed_hash,
        "failed_structural_matches": failed_struct,
        "mutation_detected_refs": mutations,
        "display_contract_locked": locked,
        "all_required_states_covered": not missing_states,
        "no_ui_runtime_required": True,
        "no_browser_required": True,
        "no_screenshot_required": True,
        "no_html_css_js_edits": True,
        "no_api_required": True,
        "final_recommendation": rec,
        "operator_next_action": "Review locked golden snapshots before any future UI implementation.",
        "display_only": True,
        "action_enabled": False,
        "manual_publish_only": True,
        "mock_only": True,
        "public_ready": False,
        "live_ready": False,
        "executable_dispatch": False,
        "api_gate_required": False,
        "validation_state": rec,
    }


# Registry of golden-snapshot validators, in choreography order.
RENDER_GOLDEN_SNAPSHOT_VALIDATORS = {
    "render_golden_snapshot_input": validate_render_golden_snapshot_input,
    "render_golden_snapshot": validate_render_golden_snapshot,
    "render_binding_conformance_result": validate_render_binding_conformance_result,
    "render_golden_snapshot_manifest": validate_render_golden_snapshot_manifest,
    "render_golden_snapshot_report": validate_render_golden_snapshot_report,
}
