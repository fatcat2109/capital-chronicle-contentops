"""Local-only deterministic real-artifact -> packet bridge with route guard (v0).

Determines whether a real-artifact intake envelope (from real_artifact_intake)
is eligible to become a local review packet input, and which route it must use.
Prevents synthetic/internal/future-placeholder artifacts from masquerading as
real approved Capital Chronicle artifacts.

Fixture-only: requires no real alpha artifacts now, reads/mutates NO Capital
Chronicle core repo. Performs NO network, provider, LLM, search, or platform
calls. Grants no approval, publish, platform, trading, forecast, or execution
authority. Every fixture/demo/synthetic output is NOT PUBLIC POSTABLE.
"""

from . import real_artifact_intake as ri

# Supported bridge routes.
SYNTHETIC_LOCAL_REVIEW_ROUTE = "SYNTHETIC_LOCAL_REVIEW_ROUTE"
INTERNAL_TEST_LOCAL_REVIEW_ROUTE = "INTERNAL_TEST_LOCAL_REVIEW_ROUTE"
FUTURE_REAL_ARTIFACT_PLACEHOLDER_ROUTE = "FUTURE_REAL_ARTIFACT_PLACEHOLDER_ROUTE"
APPROVED_REAL_ARTIFACT_CONTRACT_ROUTE = "APPROVED_REAL_ARTIFACT_CONTRACT_ROUTE"
BLOCKED_ROUTE = "BLOCKED_ROUTE"

SUPPORTED_ROUTES = [
    SYNTHETIC_LOCAL_REVIEW_ROUTE,
    INTERNAL_TEST_LOCAL_REVIEW_ROUTE,
    FUTURE_REAL_ARTIFACT_PLACEHOLDER_ROUTE,
    APPROVED_REAL_ARTIFACT_CONTRACT_ROUTE,
    BLOCKED_ROUTE,
]

# Allowed (non-blocked) route per artifact_origin.
_ORIGIN_ROUTE = {
    "synthetic_fixture": SYNTHETIC_LOCAL_REVIEW_ROUTE,
    "internal_test_fixture": INTERNAL_TEST_LOCAL_REVIEW_ROUTE,
    "future_real_artifact_placeholder": FUTURE_REAL_ARTIFACT_PLACEHOLDER_ROUTE,
    "approved_real_artifact": APPROVED_REAL_ARTIFACT_CONTRACT_ROUTE,
}


def _evaluate_synthetic_route_guard(envelope: dict, requested_route: str) -> dict:
    """Block synthetic/internal/placeholder artifacts from masquerading as real."""
    blockers = []
    origin = envelope.get("artifact_origin")

    # Synthetic/internal/future-placeholder must never use the approved-real route.
    if origin in ri.NON_PUBLIC_ORIGINS:
        if requested_route == APPROVED_REAL_ARTIFACT_CONTRACT_ROUTE:
            blockers.append(
                "origin '%s' attempted APPROVED_REAL_ARTIFACT_CONTRACT_ROUTE." % origin)
        if envelope.get("approved_for_contentops") or envelope.get("approval_granted"):
            blockers.append(
                "origin '%s' claims real/source/current authority." % origin)
        if envelope.get("publish_ready"):
            blockers.append("origin '%s' claims publish-ready." % origin)

    # Origin must not be hidden.
    if not origin:
        blockers.append("artifact_origin is hidden/missing.")

    # not_public_postable_reason must be present.
    if not envelope.get("not_public_postable_reason"):
        blockers.append("not_public_postable_reason was dropped.")

    # DQR/data sufficiency/proxy/missing/degraded status must not be dropped.
    for field in ("dqr_status", "data_sufficiency_status", "proxy_data_status",
                  "missing_data_status", "degradation_status"):
        if envelope.get(field) in (None, ""):
            blockers.append("status field '%s' was dropped/hidden." % field)

    status = "BLOCKED" if blockers else "PASS"
    return {"synthetic_route_guard_status": status, "guard_blockers": blockers}


def _determine_route(envelope: dict, gate: dict, guard: dict) -> tuple:
    """Return (route, route_blockers). Falls back to BLOCKED_ROUTE on any block."""
    blockers = []
    origin = envelope.get("artifact_origin")

    if gate.get("gate_status") == "BLOCKED":
        blockers.append("intake gate is BLOCKED; packet input not allowed.")
    if guard.get("synthetic_route_guard_status") == "BLOCKED":
        blockers.extend(guard.get("guard_blockers", []))

    expected = _ORIGIN_ROUTE.get(origin)
    if expected is None:
        blockers.append("unknown artifact_origin '%s'." % origin)

    # approved_real_artifact requires approval evidence and non-blocked gate.
    if origin == "approved_real_artifact":
        if not envelope.get("approval_source"):
            blockers.append("approved_real_artifact route requires approval_source.")

    if blockers:
        return BLOCKED_ROUTE, blockers
    return expected, blockers



def build_bridge_record(artifact_input: dict) -> dict:
    """Build a deterministic bridge route record from an intake input."""
    envelope = ri.build_intake_envelope(artifact_input or {})
    gate = ri.evaluate_readiness_gate(envelope)
    origin = envelope.get("artifact_origin")

    requested_route = _ORIGIN_ROUTE.get(origin, BLOCKED_ROUTE)
    guard = _evaluate_synthetic_route_guard(envelope, requested_route)
    route, route_blockers = _determine_route(envelope, gate, guard)

    warnings = list(gate.get("warnings", []))
    packet_input_allowed = route != BLOCKED_ROUTE
    real_route_allowed = route == APPROVED_REAL_ARTIFACT_CONTRACT_ROUTE

    bridge_status = "BLOCKED" if route == BLOCKED_ROUTE else "ELIGIBLE_FOR_LOCAL_REVIEW"

    return {
        "bridge_id": "bridge_%s" % envelope.get("intake_id", "fixture"),
        "intake_id": envelope.get("intake_id"),
        "artifact_id": envelope.get("artifact_id"),
        "artifact_family": envelope.get("artifact_family"),
        "artifact_type": envelope.get("artifact_type"),
        "artifact_origin": origin,
        "intake_gate_status": gate.get("gate_status"),
        "bridge_route": route,
        "bridge_status": bridge_status,
        "route_blockers": route_blockers,
        "route_warnings": warnings,
        "synthetic_route_guard_status": guard.get("synthetic_route_guard_status"),
        "real_artifact_route_allowed": real_route_allowed,
        "packet_input_allowed": packet_input_allowed,
        "packet_input_mode": "LOCAL_REVIEW_ONLY" if packet_input_allowed else "NONE",
        "packet_content_type": envelope.get("artifact_type"),
        "source_artifact_ids": list(envelope.get("source_artifact_ids", [])),
        "source_lineage_refs": list(envelope.get("source_lineage_refs", [])),
        "limitation_summary": envelope.get("limitation_summary"),
        "freshness_as_of": envelope.get("freshness_as_of"),
        "dqr_status": envelope.get("dqr_status"),
        "data_sufficiency_status": envelope.get("data_sufficiency_status"),
        "forecast_readiness_status": envelope.get("forecast_readiness_status"),
        "proxy_data_status": envelope.get("proxy_data_status"),
        "missing_data_status": envelope.get("missing_data_status"),
        "degradation_status": envelope.get("degradation_status"),
        "not_public_postable_reason": envelope.get("not_public_postable_reason"),
        "local_only": True,
        "advisory_only": True,
        "human_review_required": True,
        "approval_granted": False,
        "publish_ready": False,
        "provider_call_allowed": False,
        "search_call_allowed": False,
        "platform_action_allowed": False,
    }


def project_packet_input(bridge_record: dict) -> dict:
    """Map a bridge record to a safe local packet-candidate shape.

    Never calls LLM/provider/search, never creates publish-ready content,
    never grants approval/platform authority.
    """
    return {
        "packet_candidate_id": "candidate_%s" % bridge_record.get("bridge_id"),
        "source_artifact_ids": list(bridge_record.get("source_artifact_ids", [])),
        "source_lineage_refs": list(bridge_record.get("source_lineage_refs", [])),
        "content_type": bridge_record.get("packet_content_type"),
        "limitation_summary": bridge_record.get("limitation_summary"),
        "freshness_as_of": bridge_record.get("freshness_as_of"),
        "bridge_route": bridge_record.get("bridge_route"),
        "bridge_status": bridge_record.get("bridge_status"),
        "artifact_origin": bridge_record.get("artifact_origin"),
        "synthetic_origin": bridge_record.get("artifact_origin") in ri.NON_PUBLIC_ORIGINS,
        "dqr_status": bridge_record.get("dqr_status"),
        "data_sufficiency_status": bridge_record.get("data_sufficiency_status"),
        "forecast_readiness_status": bridge_record.get("forecast_readiness_status"),
        "proxy_data_status": bridge_record.get("proxy_data_status"),
        "missing_data_status": bridge_record.get("missing_data_status"),
        "degradation_status": bridge_record.get("degradation_status"),
        "not_public_postable_reason": bridge_record.get("not_public_postable_reason"),
        "packet_input_allowed": bridge_record.get("packet_input_allowed"),
        "packet_input_mode": bridge_record.get("packet_input_mode"),
        "local_only": True,
        "advisory_only": True,
        "human_review_required": True,
        "approval_granted": False,
        "publish_ready": False,
        "provider_call_allowed": False,
        "search_call_allowed": False,
        "platform_action_allowed": False,
    }



def validate_bridge_record(bridge: dict) -> dict:
    """Block/warn if the bridge record weakens guardrail posture."""
    blockers = []
    warnings = []
    origin = bridge.get("artifact_origin")
    route = bridge.get("bridge_route")

    # Intake gate BLOCKED must prevent packet input.
    if bridge.get("intake_gate_status") == "BLOCKED" and bridge.get("packet_input_allowed"):
        blockers.append("intake gate BLOCKED but packet input allowed.")

    # Route must match artifact_origin (or be BLOCKED_ROUTE).
    if route != BLOCKED_ROUTE and _ORIGIN_ROUTE.get(origin) != route:
        blockers.append("bridge_route '%s' does not match origin '%s'." % (route, origin))

    # Synthetic/internal/placeholder must not use approved-real route.
    if origin in ri.NON_PUBLIC_ORIGINS and route == APPROVED_REAL_ARTIFACT_CONTRACT_ROUTE:
        blockers.append("non-public origin '%s' on approved-real route." % origin)

    # approved_real_artifact route requires approval evidence (surfaced via blockers).
    if route == APPROVED_REAL_ARTIFACT_CONTRACT_ROUTE and not bridge.get("real_artifact_route_allowed"):
        blockers.append("approved-real route without real_artifact_route_allowed.")

    # Synthetic route guard status must be surfaced.
    if not bridge.get("synthetic_route_guard_status"):
        blockers.append("synthetic_route_guard_status not surfaced.")

    # Source IDs required for sourced families when packet input is allowed.
    if bridge.get("packet_input_allowed") and bridge.get("artifact_family") \
            in ri.SOURCE_REQUIRED_FAMILIES and not bridge.get("source_artifact_ids"):
        blockers.append("source_artifact_ids missing for family '%s'."
                        % bridge.get("artifact_family"))

    # market_note posture for eligible packet input.
    if bridge.get("packet_input_allowed") and bridge.get("artifact_family") == "market_note":
        if not bridge.get("freshness_as_of"):
            blockers.append("market_note missing freshness_as_of.")
        if not bridge.get("limitation_summary"):
            blockers.append("market_note missing limitation_summary.")

    # DQR/data sufficiency / missing / proxy / degraded must not be hidden.
    for field in ("dqr_status", "data_sufficiency_status", "proxy_data_status",
                  "missing_data_status", "degradation_status"):
        if bridge.get(field) in (None, ""):
            blockers.append("status field '%s' hidden in bridge record." % field)

    # not_public_postable_reason must be present.
    if not bridge.get("not_public_postable_reason"):
        blockers.append("not_public_postable_reason dropped from bridge record.")

    # Authority must never be granted.
    for flag in ("approval_granted", "publish_ready", "platform_action_allowed",
                 "provider_call_allowed", "search_call_allowed"):
        if bridge.get(flag):
            blockers.append("bridge grants authority flag '%s'." % flag)

    status = "BLOCKED" if blockers else ("WARNING" if warnings else "PASS")
    return {"status": status, "blockers": blockers, "warnings": warnings}


def build_summary() -> dict:
    """Deterministic CLI summary for the artifact->packet bridge / route guard."""
    return {
        "status": "deterministic local real-artifact to packet bridge and route guard active",
        "local_only": True,
        "advisory_only": True,
        "artifact_packet_bridge_enabled": True,
        "synthetic_route_guard_enabled": True,
        "fixture_only": True,
        "requires_real_alpha_artifacts_now": False,
        "human_review_required": True,
        "approval_granted": False,
        "publish_ready": False,
        "provider_call_allowed": False,
        "search_call_allowed": False,
        "platform_action_allowed": False,
        "supported_routes": list(SUPPORTED_ROUTES),
        "guard_rules_enabled": True,
        "all_fixture_outputs_not_public_postable": True,
    }

