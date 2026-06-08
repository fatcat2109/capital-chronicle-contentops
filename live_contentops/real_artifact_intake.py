"""Local-only deterministic real-artifact intake contract and readiness gate (v0).

Defines how FUTURE approved Capital Chronicle alpha artifacts will be accepted
into ContentOps once they exist. This module is fixture-only: it requires no real
alpha artifacts now, and reads/mutates NO Capital Chronicle core repo. Every
fixture/demo/synthetic artifact it handles is explicitly NOT PUBLIC POSTABLE.

Performs NO network, provider, LLM, search, or platform calls. It grants no
approval, publish, platform, trading, forecast, or execution authority.
"""

# Supported artifact families.
ARTIFACT_FAMILIES = [
    "data_sufficiency",
    "forecast_readiness",
    "failure_forensics",
    "build_in_public",
    "macro_education",
    "product_update",
    "market_note",
]

# Supported artifact origin/status values.
ARTIFACT_ORIGINS = [
    "synthetic_fixture",
    "internal_test_fixture",
    "future_real_artifact_placeholder",
    "approved_real_artifact",
]

# Origins that must always remain NOT PUBLIC POSTABLE in this fixture-only lane.
NON_PUBLIC_ORIGINS = [
    "synthetic_fixture",
    "internal_test_fixture",
    "future_real_artifact_placeholder",
]

# Families that require explicit source_artifact_ids (sourced/claim-bearing).
SOURCE_REQUIRED_FAMILIES = [
    "data_sufficiency",
    "forecast_readiness",
    "failure_forensics",
    "market_note",
]

# Families exempt from strict source IDs (general/product/process content).
SOURCE_EXEMPT_FAMILIES = [
    "build_in_public",
    "macro_education",
    "product_update",
]

# Forbidden finance/execution/marketing phrases (guardrail detection only).
FORBIDDEN_PHRASES = [
    "buy",
    "sell",
    "hold",
    "position sizing",
    "guaranteed",
    "signal service",
    "trading bot",
    "broker",
    "order routing",
    "execution engine",
    "bloomberg replacement",
]

GATE_STATUSES = ["BLOCKED", "NEEDS_OPERATOR_REVIEW", "READY_FOR_LOCAL_REVIEW_ONLY"]

# Blocking data-sufficiency / DQR states.
BLOCKING_DATA_STATES = ["BLOCKING", "INSUFFICIENT", "FAILED"]


def build_intake_envelope(artifact_input: dict) -> dict:
    """Build a deterministic intake envelope for a (future) approved artifact.

    Fixture-only: the input describes a synthetic/internal/placeholder artifact,
    or a contract-state approved_real_artifact. No real artifact is required.
    """
    artifact_input = artifact_input or {}
    origin = artifact_input.get("artifact_origin", "synthetic_fixture")

    # NOT PUBLIC POSTABLE reason is always present for fixture-only lanes.
    reason = artifact_input.get("not_public_postable_reason")
    if not reason:
        if origin in NON_PUBLIC_ORIGINS:
            reason = (
                "Local-only fixture-only intake; %s artifacts are never public "
                "postable in this lane." % origin)
        else:
            reason = (
                "Local-only contract state; requires human review and approval "
                "evidence before any future public use.")

    return {
        "intake_id": artifact_input.get("intake_id", "intake_fixture"),
        "artifact_id": artifact_input.get("artifact_id"),
        "artifact_family": artifact_input.get("artifact_family"),
        "artifact_type": artifact_input.get("artifact_type"),
        "artifact_origin": origin,
        "artifact_status": artifact_input.get("artifact_status", "DRAFT"),
        "approved_for_contentops": bool(artifact_input.get("approved_for_contentops", False)),
        "approval_source": artifact_input.get("approval_source"),
        "approval_timestamp": artifact_input.get("approval_timestamp"),
        "source_artifact_ids": list(artifact_input.get("source_artifact_ids", [])),
        "source_lineage_refs": list(artifact_input.get("source_lineage_refs", [])),
        "freshness_as_of": artifact_input.get("freshness_as_of"),
        "limitation_summary": artifact_input.get("limitation_summary"),
        "data_sufficiency_status": artifact_input.get("data_sufficiency_status", "UNKNOWN"),
        "dqr_status": artifact_input.get("dqr_status", "UNKNOWN"),
        "forecast_readiness_status": artifact_input.get("forecast_readiness_status", "NOT_READY"),
        "proxy_data_status": artifact_input.get("proxy_data_status", "NONE"),
        "missing_data_status": artifact_input.get("missing_data_status", "NONE"),
        "degradation_status": artifact_input.get("degradation_status", "NONE"),
        "educational_general_only": bool(artifact_input.get("educational_general_only", True)),
        "no_financial_advice": True,
        "not_public_postable_reason": reason,
        "raw_text": artifact_input.get("raw_text", ""),
        "local_only": True,
        "advisory_only": True,
        "human_review_required": True,
        "approval_granted": False,
        "publish_ready": False,
        "provider_call_allowed": False,
        "search_call_allowed": False,
        "platform_action_allowed": False,
    }



def _has_forbidden_language(envelope: dict) -> list:
    """Return forbidden finance/execution phrases found in the artifact text."""
    text = " ".join(str(envelope.get(f, "")) for f in
                     ("raw_text", "limitation_summary", "artifact_type")).lower()
    hits = []
    for phrase in FORBIDDEN_PHRASES:
        # Word-ish boundary check for short tokens to avoid false positives.
        if phrase in (" buy ", "buy", "sell", "hold"):
            padded = " %s " % text
            if (" %s " % phrase) in padded:
                hits.append(phrase)
        elif phrase in text:
            hits.append(phrase)
    return hits


def evaluate_readiness_gate(envelope: dict) -> dict:
    """Deterministic readiness gate for an intake envelope."""
    blockers = []
    warnings = []
    required_missing_fields = []
    authority_boundary_flags = []

    family = envelope.get("artifact_family")
    origin = envelope.get("artifact_origin")

    # Required identity.
    if not envelope.get("artifact_id"):
        required_missing_fields.append("artifact_id")
        blockers.append("artifact_id is missing.")

    # Source IDs required for sourced/claim-bearing families.
    if family in SOURCE_REQUIRED_FAMILIES and not envelope.get("source_artifact_ids"):
        required_missing_fields.append("source_artifact_ids")
        blockers.append("source_artifact_ids required for family '%s'." % family)

    # approved_real_artifact must carry approval evidence.
    if origin == "approved_real_artifact" and not envelope.get("approval_source"):
        blockers.append("approved_real_artifact claimed without approval_source.")

    # Synthetic/internal/placeholder fixtures must not claim real/public-ready.
    if origin in NON_PUBLIC_ORIGINS:
        if envelope.get("approved_for_contentops") or envelope.get("publish_ready") \
                or envelope.get("approval_granted"):
            blockers.append(
                "Fixture origin '%s' claims real/approved/public-ready status." % origin)

    # Forecast readiness cannot be claimed while DQR/data sufficiency is blocking.
    dqr = str(envelope.get("dqr_status", "")).upper()
    dsuff = str(envelope.get("data_sufficiency_status", "")).upper()
    forecast = str(envelope.get("forecast_readiness_status", "")).upper()
    if forecast in ("READY", "FORECAST_READY"):
        if dqr in BLOCKING_DATA_STATES or dsuff in BLOCKING_DATA_STATES:
            blockers.append(
                "forecast readiness claimed while DQR/data sufficiency is blocking.")

    # Missing/proxy/degraded data cannot be hidden: must be explicit, not UNKNOWN-hidden.
    for field in ("missing_data_status", "proxy_data_status", "degradation_status"):
        if envelope.get(field) in (None, ""):
            blockers.append("%s is hidden (must be explicit)." % field)

    # market_note posture requirements.
    if family == "market_note":
        if not envelope.get("freshness_as_of"):
            blockers.append("market_note missing freshness_as_of.")
        if not envelope.get("limitation_summary"):
            blockers.append("market_note missing limitation_summary.")
        if not envelope.get("educational_general_only"):
            blockers.append("market_note missing educational/general posture.")

    # Forbidden finance/execution language.
    hits = _has_forbidden_language(envelope)
    if hits:
        blockers.append("forbidden finance/execution language: %s" % ", ".join(sorted(set(hits))))

    # Authority must never be granted by intake.
    if envelope.get("publish_ready"):
        authority_boundary_flags.append("publish_ready")
        blockers.append("intake artifact sets publish_ready=true.")
    if envelope.get("approval_granted"):
        authority_boundary_flags.append("approval_granted")
        blockers.append("intake artifact sets approval_granted=true.")
    if envelope.get("platform_action_allowed"):
        authority_boundary_flags.append("platform_action_allowed")
        blockers.append("intake artifact sets platform_action_allowed=true.")

    # Determine gate status.
    if blockers:
        gate_status = "BLOCKED"
    elif origin == "future_real_artifact_placeholder" or not envelope.get("limitation_summary"):
        gate_status = "NEEDS_OPERATOR_REVIEW"
    else:
        gate_status = "READY_FOR_LOCAL_REVIEW_ONLY"

    if not envelope.get("limitation_summary") and gate_status != "BLOCKED":
        warnings.append("limitation_summary not provided; operator review required.")

    return {
        "gate_status": gate_status,
        "blockers": blockers,
        "warnings": warnings,
        "required_missing_fields": required_missing_fields,
        "authority_boundary_flags": authority_boundary_flags,
        "contentops_allowed": gate_status == "READY_FOR_LOCAL_REVIEW_ONLY",
        "not_public_postable": True,
        "publish_ready": False,
        "approval_granted": False,
        "platform_action_allowed": False,
    }




def build_summary() -> dict:
    """Deterministic CLI summary for the intake contract / readiness gate."""
    return {
        "status": "deterministic local real-artifact intake contract and readiness gate active",
        "local_only": True,
        "advisory_only": True,
        "real_artifact_intake_enabled": True,
        "readiness_gate_enabled": True,
        "fixture_only": True,
        "requires_real_alpha_artifacts_now": False,
        "human_review_required": True,
        "approval_granted": False,
        "publish_ready": False,
        "provider_call_allowed": False,
        "search_call_allowed": False,
        "platform_action_allowed": False,
        "supported_artifact_families": list(ARTIFACT_FAMILIES),
        "supported_artifact_origins": list(ARTIFACT_ORIGINS),
        "gate_rules_enabled": True,
        "all_fixture_outputs_not_public_postable": True,
    }
