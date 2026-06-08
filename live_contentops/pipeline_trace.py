"""Local-only deterministic end-to-end real-artifact pipeline trace (v0).

Connects the full fixture-only ContentOps path:
intake envelope -> readiness gate -> artifact packet bridge / synthetic route
guard -> packet input projection -> packet export shape -> audit/review queue ->
operator decision / review history -> registry / ledger -> dashboard / handoff.

Fixture-only: requires no real Capital Chronicle alpha artifacts now, reads and
mutates NO core repo. Performs NO network, provider, LLM, search, or platform
calls. Grants no approval/publish/platform/trading/forecast/execution authority.
Every fixture/demo/synthetic trace output is NOT PUBLIC POSTABLE.
"""

from . import real_artifact_intake as ri
from . import artifact_packet_bridge as apb

# Downstream stage status values (local trace only, no real pipeline mutation).
_STAGE_NOT_REACHED = "NOT_REACHED"
_STAGE_LOCAL_REVIEW = "LOCAL_REVIEW_ONLY"
_STAGE_BLOCKED = "BLOCKED"

# Markdown banners that must always appear in the report.
MARKDOWN_BANNERS = [
    "LOCAL ONLY",
    "ADVISORY ONLY",
    "FIXTURE ONLY",
    "REAL ALPHA ARTIFACTS NOT REQUIRED",
    "HUMAN REVIEW REQUIRED",
    "NOT PUBLIC POSTABLE",
    "NO PROVIDER CALL",
    "NO SEARCH CALL",
    "NO PLATFORM ACTION",
]


def _downstream_stage_statuses(bridge: dict) -> dict:
    """Compute deterministic downstream stage statuses from a bridge record.

    Allowed local-review traces reach all downstream stages as LOCAL_REVIEW_ONLY;
    blocked traces stop at the bridge and mark downstream stages NOT_REACHED.
    """
    if not bridge.get("packet_input_allowed"):
        return {
            "packet_export_status": _STAGE_NOT_REACHED,
            "audit_status": _STAGE_NOT_REACHED,
            "review_queue_status": _STAGE_NOT_REACHED,
            "operator_decision_status": _STAGE_NOT_REACHED,
            "review_history_status": _STAGE_NOT_REACHED,
            "registry_status": _STAGE_NOT_REACHED,
            "ledger_status": _STAGE_NOT_REACHED,
            "dashboard_handoff_status": _STAGE_NOT_REACHED,
        }
    return {
        "packet_export_status": _STAGE_LOCAL_REVIEW,
        "audit_status": _STAGE_LOCAL_REVIEW,
        "review_queue_status": _STAGE_LOCAL_REVIEW,
        "operator_decision_status": "PENDING_MANUAL_REVIEW",
        "review_history_status": _STAGE_LOCAL_REVIEW,
        "registry_status": _STAGE_LOCAL_REVIEW,
        "ledger_status": _STAGE_LOCAL_REVIEW,
        "dashboard_handoff_status": _STAGE_LOCAL_REVIEW,
    }


def build_pipeline_trace(artifact_input: dict) -> dict:
    """Build one deterministic end-to-end pipeline trace record."""
    envelope = ri.build_intake_envelope(artifact_input or {})
    gate = ri.evaluate_readiness_gate(envelope)
    bridge = apb.build_bridge_record(artifact_input or {})
    projection = apb.project_packet_input(bridge)
    stages = _downstream_stage_statuses(bridge)

    blockers = list(bridge.get("route_blockers", []))
    warnings = list(bridge.get("route_warnings", []))

    packet_input_allowed = bridge.get("packet_input_allowed", False)
    bundle_refresh_status = (_STAGE_LOCAL_REVIEW if packet_input_allowed
                             else _STAGE_NOT_REACHED)

    record = {
        "trace_id": "trace_%s" % envelope.get("intake_id", "fixture"),
        "intake_id": envelope.get("intake_id"),
        "artifact_id": envelope.get("artifact_id"),
        "artifact_family": envelope.get("artifact_family"),
        "artifact_type": envelope.get("artifact_type"),
        "artifact_origin": envelope.get("artifact_origin"),
        "intake_gate_status": gate.get("gate_status"),
        "bridge_route": bridge.get("bridge_route"),
        "bridge_status": bridge.get("bridge_status"),
        "packet_input_allowed": packet_input_allowed,
        "packet_input_projection": projection,
        "synthetic_route_guard_status": bridge.get("synthetic_route_guard_status"),
        "real_artifact_route_allowed": bridge.get("real_artifact_route_allowed"),
        "bundle_refresh_status": bundle_refresh_status,
        "blockers": blockers,
        "warnings": warnings,
        "lineage_refs": list(envelope.get("source_lineage_refs", [])),
        "source_artifact_ids": list(envelope.get("source_artifact_ids", [])),
        "freshness_as_of": envelope.get("freshness_as_of"),
        "limitation_summary": envelope.get("limitation_summary"),
        "dqr_status": envelope.get("dqr_status"),
        "data_sufficiency_status": envelope.get("data_sufficiency_status"),
        "forecast_readiness_status": envelope.get("forecast_readiness_status"),
        "proxy_data_status": envelope.get("proxy_data_status"),
        "missing_data_status": envelope.get("missing_data_status"),
        "degradation_status": envelope.get("degradation_status"),
        "not_public_postable_reason": envelope.get("not_public_postable_reason"),
        "local_only": True,
        "advisory_only": True,
        "fixture_only": True,
        "requires_real_alpha_artifacts_now": False,
        "human_review_required": True,
        "approval_granted": False,
        "publish_ready": False,
        "provider_call_allowed": False,
        "search_call_allowed": False,
        "platform_action_allowed": False,
    }
    record.update(stages)
    return record



def validate_pipeline_trace(trace: dict) -> dict:
    """Block/warn if a pipeline trace weakens guardrail posture."""
    blockers = []
    warnings = []
    origin = trace.get("artifact_origin")

    downstream = ("packet_export_status", "audit_status", "review_queue_status",
                  "operator_decision_status", "review_history_status",
                  "registry_status", "ledger_status", "dashboard_handoff_status")

    # Blocked intake/bridge must not allow downstream stages.
    if not trace.get("packet_input_allowed"):
        for stage in downstream:
            if trace.get(stage) not in (_STAGE_NOT_REACHED,):
                blockers.append("blocked trace marks downstream stage '%s' as reached." % stage)

    # Bridge route must match origin (or be BLOCKED_ROUTE).
    route = trace.get("bridge_route")
    if route != apb.BLOCKED_ROUTE and apb._ORIGIN_ROUTE.get(origin) != route:
        blockers.append("bridge_route '%s' contradicts origin '%s'." % (route, origin))

    # Synthetic/internal/placeholder must not use approved-real route.
    if origin in ri.NON_PUBLIC_ORIGINS and route == apb.APPROVED_REAL_ARTIFACT_CONTRACT_ROUTE:
        blockers.append("non-public origin '%s' on approved-real route." % origin)

    # Status fields must not be hidden.
    for field in ("dqr_status", "data_sufficiency_status", "proxy_data_status",
                  "missing_data_status", "degradation_status"):
        if trace.get(field) in (None, ""):
            blockers.append("status field '%s' hidden in trace." % field)

    # not_public_postable_reason must be present.
    if not trace.get("not_public_postable_reason"):
        blockers.append("not_public_postable_reason dropped from trace.")

    # Authority must never be granted.
    for flag in ("approval_granted", "publish_ready", "platform_action_allowed",
                 "provider_call_allowed", "search_call_allowed"):
        if trace.get(flag):
            blockers.append("trace grants authority flag '%s'." % flag)

    status = "BLOCKED" if blockers else ("WARNING" if warnings else "PASS")
    return {"status": status, "blockers": blockers, "warnings": warnings}


def build_summary() -> dict:
    """Deterministic CLI summary for the end-to-end pipeline trace."""
    from . import pipeline_trace_fixtures as ptf
    traces = ptf.build_all_traces()
    blocked = sum(1 for t in traces if not t["packet_input_allowed"])
    local_review = sum(1 for t in traces if t["packet_input_allowed"])
    return {
        "status": "deterministic local real-artifact pipeline trace active",
        "local_only": True,
        "advisory_only": True,
        "fixture_only": True,
        "requires_real_alpha_artifacts_now": False,
        "pipeline_trace_enabled": True,
        "intake_gate_enabled": True,
        "bridge_route_guard_enabled": True,
        "packet_projection_enabled": True,
        "review_pipeline_trace_enabled": True,
        "registry_ledger_trace_enabled": True,
        "dashboard_handoff_trace_enabled": True,
        "bundle_refresh_enabled": True,
        "human_review_required": True,
        "approval_granted": False,
        "publish_ready": False,
        "provider_call_allowed": False,
        "search_call_allowed": False,
        "platform_action_allowed": False,
        "scenario_count": len(traces),
        "blocked_scenario_count": blocked,
        "local_review_only_scenario_count": local_review,
        "all_fixture_outputs_not_public_postable": True,
        "validation_rules_enabled": True,
    }

