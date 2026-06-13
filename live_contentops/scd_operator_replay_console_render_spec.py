"""Operator replay console render-spec / display-binding validators (SCD, 0174AW).

Local-only, deterministic, fail-closed. This module defines the CONTRACT and
VALIDATION for mapping a 0174AV read-only console view-model into future cockpit
display slots. It is a render-SPEC, not UI: no HTML/CSS/JS, no DOM, no browser,
no screenshots, no network, no providers, no credentials, no scheduler, no live
dispatch. The projection helper only transforms supplied local dictionaries.

Domain objects validated here:

    SCDOperatorReplayConsoleRenderSpec
    SCDReplayConsoleLayoutRegionSpec
    SCDReplayConsoleDisplaySlotBinding
    SCDReplayConsoleStatusTokenBinding
    SCDReplayConsoleRenderSpecReport

Validators return {"validation_state": <STATE>, "reasons": [...]}.
"""
from live_contentops.scd_domain_model import (
    PASS,
    BLOCKED,
    REVIEW_REQUIRED,
    UNKNOWN,
    FORBIDDEN_LANGUAGE,
    _schema_ok,
    _find_language,
    _scan_secrets,
    _result,
)
from live_contentops.scd_editorial_workbench import (
    INVENTED_AUTHORITY_PATTERNS,
    INVENTED_METRIC_PATTERNS,
)
from live_contentops.scd_platform_payload_compiler import TELEGRAM_API_PATTERNS
from live_contentops.scd_dispatch_gate import NETWORK_API_PATTERNS

# Recognized layout regions and the required subset for a PASS render spec.
RECOGNIZED_REGIONS = (
    "command_hero",
    "blocker_banner",
    "safety_banner",
    "stage_matrix",
    "evidence_rail",
    "copy_safe_export_panel",
    "current_truth_panel",
    "operator_next_action_panel",
)
REQUIRED_REGIONS = ("command_hero", "stage_matrix", "current_truth_panel")

# Readiness flags that must never be true on any 0174AW object.
FORBIDDEN_READY_FLAGS = ("public_ready", "live_ready", "executable_dispatch", "live_eligibility")

# UI-runtime flags that must be false on the render spec.
FORBIDDEN_UI_FLAGS = ("ui_runtime_required", "browser_required", "screenshot_required")

# Status -> (severity, semantic_color_role) canonical mapping.
STATUS_TOKEN_MAP = {
    PASS: ("pass", "pass"),
    BLOCKED: ("blocked", "danger"),
    REVIEW_REQUIRED: ("review", "review"),
    UNKNOWN: ("unknown", "unknown"),
}

# Extra HTML/CSS/JS/DOM implication patterns specific to this render-spec task.
UI_RUNTIME_PATTERNS = (
    "<script",
    "document.queryselector",
    "queryselector",
    "addeventlistener",
    "window.",
    "fetch(",
    "innerhtml",
    "<html",
    "<style",
)


def _scan(text, patterns):
    return _find_language(text, patterns)


def _all_unsafe_text(text):
    hits = []
    hits += [f"forbidden language: {h}" for h in _scan(text, FORBIDDEN_LANGUAGE)]
    hits += [f"invented authority: {h}" for h in _scan(text, INVENTED_AUTHORITY_PATTERNS)]
    hits += [f"invented metric: {h}" for h in _scan(text, INVENTED_METRIC_PATTERNS)]
    hits += [f"telegram/api implication: {h}" for h in _scan(text, TELEGRAM_API_PATTERNS)]
    hits += [f"network/api/oauth implication: {h}" for h in _scan(text, NETWORK_API_PATTERNS)]
    lowered = text.lower() if isinstance(text, str) else ""
    for pat in UI_RUNTIME_PATTERNS:
        if pat in lowered:
            hits.append(f"ui/runtime implication: {pat}")
    return hits


def _scan_all_strings(obj):
    found = []

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(k, str):
                    found.extend(_all_unsafe_text(k))
                walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, str):
            found.extend(_all_unsafe_text(node))

    walk(obj)
    return found


def _ready_flag_blocks(payload):
    return [f"{flag} must be false" for flag in FORBIDDEN_READY_FLAGS if payload.get(flag)]


def _common_display_blocks(payload):
    """Shared display-only invariants for render-spec objects."""
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
    return blocked


def validate_operator_replay_console_render_spec(payload):
    ok, msg = _schema_ok(payload, "scd_operator_replay_console_render_spec.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []
    blocked += _common_display_blocks(payload)

    for flag in FORBIDDEN_UI_FLAGS:
        if payload.get(flag):
            blocked.append(f"{flag} must be false")

    regions = payload.get("layout_regions", []) or []
    for missing in REQUIRED_REGIONS:
        if missing not in regions:
            blocked.append(f"PASS render spec requires region {missing}")
    if not payload.get("display_slot_bindings"):
        blocked.append("PASS render spec requires display_slot_bindings")
    if not payload.get("status_token_bindings"):
        blocked.append("PASS render spec requires status_token_bindings")

    cvh = payload.get("current_vs_historical_truth_binding", {})
    if cvh.get("current_state_is_authoritative") is not True:
        blocked.append("current_state_is_authoritative must be true")
    if cvh.get("stale_or_historical_refs_separated") is not True:
        blocked.append("stale_or_historical_refs_separated must be true")

    if not payload.get("view_model_id"):
        unknown.append("missing view_model_id")
    if not payload.get("console_input_id"):
        unknown.append("missing console_input_id")

    return _result(blocked, review, unknown)


def validate_replay_console_layout_region_spec(payload):
    ok, msg = _schema_ok(payload, "scd_replay_console_layout_region_spec.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []
    blocked += _common_display_blocks(payload)

    if payload.get("region_name") not in RECOGNIZED_REGIONS:
        blocked.append(f"unrecognized region_name: {payload.get('region_name')}")
    if not payload.get("source_view_model_field"):
        unknown.append("missing source_view_model_field")
    if payload.get("region_order_index") is None:
        unknown.append("missing region_order_index")

    return _result(blocked, review, unknown)


def validate_replay_console_display_slot_binding(payload):
    ok, msg = _schema_ok(payload, "scd_replay_console_display_slot_binding.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []
    # Display slot binding has display_only/action_enabled but no mock/manual flags.
    blocked += _ready_flag_blocks(payload)
    blocked += _scan_secrets(payload)
    blocked += _scan_all_strings(payload)
    if payload.get("display_only") is not True:
        blocked.append("display_only must be true")
    if payload.get("action_enabled"):
        blocked.append("action_enabled must be false")

    if not payload.get("source_object"):
        unknown.append("missing source_object")
    if not payload.get("source_field"):
        unknown.append("missing source_field")

    # copy_safe_text slots must be marked copy_safe and never action-enabled.
    if payload.get("display_semantics") == "copy_safe_text" and payload.get("copy_safe") is not True:
        blocked.append("copy_safe_text slot must set copy_safe true")
    # evidence_ref slots should require redaction.
    if payload.get("display_semantics") == "evidence_ref" and payload.get("redaction_required") is not True:
        review.append("evidence_ref slot should set redaction_required true")

    return _result(blocked, review, unknown)


def validate_replay_console_status_token_binding(payload):
    ok, msg = _schema_ok(payload, "scd_replay_console_status_token_binding.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []
    blocked += _ready_flag_blocks(payload)
    blocked += _scan_secrets(payload)
    blocked += _scan_all_strings(payload)
    if payload.get("display_only") is not True:
        blocked.append("display_only must be true")
    if payload.get("action_enabled"):
        blocked.append("action_enabled must be false")
    if payload.get("api_gate_required"):
        blocked.append("api_gate_required must be false")

    status = payload.get("status")
    if status in STATUS_TOKEN_MAP:
        exp_sev, exp_color = STATUS_TOKEN_MAP[status]
        if payload.get("severity") != exp_sev:
            blocked.append(f"severity {payload.get('severity')} does not match status {status}")
        if payload.get("semantic_color_role") != exp_color:
            blocked.append(f"semantic_color_role {payload.get('semantic_color_role')} does not match status {status}")
    else:
        blocked.append(f"unrecognized status: {status}")

    return _result(blocked, review, unknown)


def validate_replay_console_render_spec_report(payload):
    ok, msg = _schema_ok(payload, "scd_replay_console_render_spec_report.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []
    blocked += _common_display_blocks(payload)

    # All no_* assertions must be true.
    for flag in ("no_ui_runtime_required", "no_browser_required", "no_screenshot_required",
                 "no_html_css_js_edits", "no_api_required"):
        if payload.get(flag) is not True:
            blocked.append(f"{flag} must be true")

    rec = payload.get("final_recommendation")
    missing_regions = payload.get("missing_required_regions", []) or []
    missing_slots = payload.get("missing_required_slots", []) or []
    blocked_bindings = payload.get("blocked_bindings", []) or []
    review_bindings = payload.get("review_required_bindings", []) or []
    unknown_bindings = payload.get("unknown_bindings", []) or []

    # Fail-closed precedence: BLOCKED > UNKNOWN > REVIEW_REQUIRED > PASS.
    if blocked_bindings:
        expected = BLOCKED
    elif missing_regions or missing_slots or unknown_bindings:
        expected = UNKNOWN
    elif review_bindings:
        expected = REVIEW_REQUIRED
    else:
        expected = PASS

    if rec == PASS and expected != PASS:
        blocked.append(f"final PASS contradicts binding roll-up (expected {expected})")
    if blocked_bindings and rec != BLOCKED:
        blocked.append("blocked bindings present; final must be BLOCKED")
    if rec == PASS and payload.get("display_contract_complete") is not True:
        blocked.append("final PASS requires display_contract_complete true")

    if rec not in (PASS, BLOCKED, REVIEW_REQUIRED, UNKNOWN):
        blocked.append(f"invalid final_recommendation: {rec}")

    if not payload.get("view_model_id"):
        unknown.append("missing view_model_id")

    if not blocked:
        if expected == UNKNOWN:
            unknown.append("missing required regions/slots or unknown bindings")
        elif expected == REVIEW_REQUIRED:
            review.append("non-blocking review-required bindings present")

    return _result(blocked, review, unknown)


# --- Deterministic local projection helpers ------------------------------------------

def build_layout_region_specs(render_spec_id):
    """Return the deterministic ordered required+core layout region specs."""
    regions = [
        ("command_hero", "headline_status", True),
        ("blocker_banner", "blocker_banner", False),
        ("safety_banner", "safety_banner", False),
        ("stage_matrix", "stage_status_chips", True),
        ("evidence_rail", "evidence_bundle_ref", False),
        ("copy_safe_export_panel", "copy_safe_export_bundle_ref", False),
        ("current_truth_panel", "current_vs_historical_truth", True),
        ("operator_next_action_panel", "operator_next_action", False),
    ]
    specs = []
    for idx, (name, field, required) in enumerate(regions):
        specs.append({
            "schema_version": "1.0",
            "layout_region_id": f"region_{idx}_{name}",
            "render_spec_id": render_spec_id,
            "region_name": name,
            "region_role": "display",
            "source_view_model_field": field,
            "region_order_index": idx,
            "required_for_pass": required,
            "collapsible": not required,
            "default_expanded": required,
            "density": "standard",
            "display_only": True,
            "action_enabled": False,
            "public_ready": False,
            "live_ready": False,
            "executable_dispatch": False,
            "api_gate_required": False,
            "validation_state": PASS,
        })
    return specs


def build_status_token_bindings(render_spec_id):
    """Return the four canonical status token bindings (PASS/BLOCKED/REVIEW/UNKNOWN)."""
    bindings = []
    for status, (sev, color) in STATUS_TOKEN_MAP.items():
        bindings.append({
            "schema_version": "1.0",
            "status_token_binding_id": f"token_{status.lower()}",
            "render_spec_id": render_spec_id,
            "status": status,
            "severity": sev,
            "semantic_color_role": color,
            "token_label": status,
            "token_description": f"Display token for {status} state.",
            "allowed_for_headline": True,
            "allowed_for_stage_chip": True,
            "action_enabled": False,
            "display_only": True,
            "public_ready": False,
            "live_ready": False,
            "executable_dispatch": False,
            "api_gate_required": False,
            "validation_state": PASS,
        })
    return bindings


def build_render_spec_from_view_model(view_model, evidence_bundle, copy_safe_export_bundle):
    """Project a 0174AV view model into a render-spec skeleton.

    Invents nothing: copies ids/refs from supplied packets and emits the
    deterministic region/token skeleton. No URLs, credentials, endpoints, tokens,
    DOM selectors, HTML/CSS/JS, browser requirements, or screenshots are created.
    """
    rsid = "rs_" + view_model.get("view_model_id", "unknown")
    regions = build_layout_region_specs(rsid)
    tokens = build_status_token_bindings(rsid)
    cvh = view_model.get("current_vs_historical_truth", {})
    return {
        "schema_version": "1.0",
        "render_spec_id": rsid,
        "view_model_id": view_model.get("view_model_id", ""),
        "console_input_id": view_model.get("console_input_id", ""),
        "evidence_bundle_id": (evidence_bundle or {}).get("evidence_bundle_id", ""),
        "copy_safe_export_bundle_id": (copy_safe_export_bundle or {}).get("copy_safe_export_bundle_id", ""),
        "render_mode": "display_spec_only",
        "target_surface": "future_operator_cockpit",
        "layout_regions": [r["region_name"] for r in regions],
        "display_slot_bindings": ["headline_status_slot", "stage_matrix_slot", "current_truth_slot"],
        "status_token_bindings": [t["status_token_binding_id"] for t in tokens],
        "copy_safe_action_bindings": ["copy_safe_text_slot"],
        "evidence_slot_bindings": ["evidence_ref_slot"],
        "current_vs_historical_truth_binding": {
            "current_replay_report_slot": "current_truth_slot",
            "historical_evidence_slot": "historical_truth_slot",
            "current_state_is_authoritative": cvh.get("current_state_is_authoritative", True) is True,
            "stale_or_historical_refs_separated": cvh.get("stale_or_historical_refs_separated", True) is True,
        },
        "display_only": True,
        "action_enabled": False,
        "ui_runtime_required": False,
        "browser_required": False,
        "screenshot_required": False,
        "manual_publish_only": True,
        "mock_only": True,
        "public_ready": False,
        "live_ready": False,
        "executable_dispatch": False,
        "api_gate_required": False,
        "validation_state": view_model.get("validation_state", UNKNOWN),
    }


# Registry of render-spec validators, in choreography order.
RENDER_SPEC_VALIDATORS = {
    "operator_replay_console_render_spec": validate_operator_replay_console_render_spec,
    "replay_console_layout_region_spec": validate_replay_console_layout_region_spec,
    "replay_console_display_slot_binding": validate_replay_console_display_slot_binding,
    "replay_console_status_token_binding": validate_replay_console_status_token_binding,
    "replay_console_render_spec_report": validate_replay_console_render_spec_report,
}
