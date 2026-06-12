"""Bounded LLM editorial workbench contract validators (SCD, 0174AQ).

Local-only, deterministic, fail-closed. This module defines the CONTRACT and
VALIDATION for a bounded human-grade editorial workbench that sits AFTER the
ContentIntentPacket and BEFORE CanonicalSocialPost / PlatformPayload.

It NEVER calls a provider/LLM/API, never approves content, never enables live
or public posting. It only validates the shape and safety invariants of:

    SCDEditorialWorkbenchRequest
    SCDEditorialWorkbenchOutput
    SCDEditorialVoiceProfile
    SCDHookTaxonomyEntry
    SCDEditorialCritiquePacket

Validators return {"validation_state": <STATE>, "reasons": [...]}.
Reuses the deterministic guards from scd_domain_model (0174AP).
"""
import re

from live_contentops.scd_domain_model import (
    PASS,
    BLOCKED,
    REVIEW_REQUIRED,
    UNKNOWN,
    LANES_ALLOWED_NOW,
    LANES_ARTIFACT_GATED,
    FORBIDDEN_LANGUAGE,
    _schema_ok,
    _find_language,
    _scan_secrets,
    _result,
)

# Invented Capital Chronicle authority / hallucinated forecast claims -> BLOCKED
# unless real artifact authority is present (which is absent in fixtures).
INVENTED_AUTHORITY_PATTERNS = [
    r"capital chronicle alpha",
    r"our model (predicts|says|forecasts)",
    r"forecast[- ]ready",
    r"\bforecast readiness\b",
    r"data sufficiency (confirmed|met|passed)",
    r"\bour (verified )?artifact\b",
    r"\bproven track record\b",
    r"\bbacktested (returns|profit)\b",
    r"\bguaranteed\b",
]

# Invented metric/performance claims -> BLOCKED (numbers framed as results).
INVENTED_METRIC_PATTERNS = [
    r"\b\d+(\.\d+)?%\s+(return|gain|accuracy|win rate|profit)",
    r"\bsharpe\b", r"\balpha of\b", r"\bbeat the market\b",
    r"\b\d+x\s+(return|gain)",
]


def _scan(text, patterns):
    return _find_language(text, patterns)


def validate_editorial_voice_profile(payload):
    ok, msg = _schema_ok(payload, "scd_editorial_voice_profile.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    for flag in (
        "no_market_advice_required",
        "no_signal_language_required",
        "no_authority_invention_required",
    ):
        if payload.get(flag) is not True:
            blocked.append(f"{flag} must be true")

    # Forbidden tone must include hype/trader-bait style guards.
    forbidden_tone = " ".join(payload.get("forbidden_tone", [])).lower()
    for needed in ("hype", "trader-bait", "signal"):
        if needed not in forbidden_tone:
            review.append(f"forbidden_tone should explicitly bar '{needed}'")

    # Allowed phrasing examples must not themselves contain forbidden language.
    for ex in payload.get("allowed_phrasing_examples", []):
        for hit in _scan(ex, FORBIDDEN_LANGUAGE):
            blocked.append(f"allowed phrasing example contains forbidden language: {hit}")
        for hit in _scan(ex, INVENTED_AUTHORITY_PATTERNS):
            blocked.append(f"allowed phrasing example invents authority: {hit}")

    for hit in _scan_secrets(payload):
        blocked.append(hit)

    if not payload.get("allowed_tone"):
        unknown.append("allowed_tone empty; voice cannot be established")

    return _result(blocked, review, unknown)


def validate_hook_taxonomy_entry(payload):
    ok, msg = _schema_ok(payload, "scd_hook_taxonomy_entry.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    # Safe hook example must be clean; blocked example is allowed to be unsafe
    # (it documents what NOT to do) and is not scanned as a violation.
    safe = payload.get("example_safe_hook", "")
    for hit in _scan(safe, FORBIDDEN_LANGUAGE):
        blocked.append(f"example_safe_hook contains forbidden language: {hit}")
    for hit in _scan(safe, INVENTED_AUTHORITY_PATTERNS):
        blocked.append(f"example_safe_hook invents authority: {hit}")
    for hit in _scan(safe, INVENTED_METRIC_PATTERNS):
        blocked.append(f"example_safe_hook invents metric: {hit}")

    for hit in _scan_secrets(payload):
        blocked.append(hit)

    allowed_lanes = set(payload.get("allowed_lanes", []))
    # artifact_backed_future hook must only target gated lanes.
    if payload.get("hook_type") == "artifact_backed_future":
        if allowed_lanes & LANES_ALLOWED_NOW:
            blocked.append("artifact_backed_future hook cannot target lanes A/B")
    if not allowed_lanes:
        unknown.append("allowed_lanes empty; hook applicability unknown")

    return _result(blocked, review, unknown)


def validate_editorial_workbench_request(payload):
    ok, msg = _schema_ok(payload, "scd_editorial_workbench_request.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    # Provider calls and public/live readiness are never allowed in this task.
    if payload.get("provider_call_allowed"):
        blocked.append("provider_call_allowed must be false")
    if payload.get("public_ready"):
        blocked.append("public_ready must be false")

    lane = payload.get("content_lane")
    text = " ".join(
        [payload.get("input_text", ""), payload.get("source_summary", "")]
    )
    for hit in _scan(text, FORBIDDEN_LANGUAGE):
        blocked.append(f"forbidden language: {hit}")
    for hit in _scan(text, INVENTED_AUTHORITY_PATTERNS):
        blocked.append(f"invented authority: {hit}")
    for hit in _scan(text, INVENTED_METRIC_PATTERNS):
        blocked.append(f"invented metric: {hit}")
    for hit in _scan_secrets(payload):
        blocked.append(hit)

    # Lane C-F gating: require real artifact authority.
    authority = payload.get("artifact_authority_state", "none")
    if lane in LANES_ARTIFACT_GATED and authority != "real_artifact_backed":
        blocked.append(
            f"lane {lane} requires real_artifact_backed authority (got '{authority}')"
        )
    if authority == "claimed_unverified":
        blocked.append("claimed_unverified artifact authority cannot be used")

    # UNKNOWN: missing source intent lineage / evidence basis.
    if not payload.get("source_intent_packet_id"):
        unknown.append("source_intent_packet_id missing; lineage unknown")

    # REVIEW_REQUIRED: operator review must be required for any editorial output.
    if payload.get("operator_review_required") is not True:
        review.append("operator_review_required should be true")
    if lane and lane not in LANES_ALLOWED_NOW and lane not in LANES_ARTIFACT_GATED:
        review.append(f"unrecognized lane '{lane}' needs human judgment")

    return _result(blocked, review, unknown)


def validate_editorial_workbench_output(payload):
    ok, msg = _schema_ok(payload, "scd_editorial_workbench_output.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    # System can never approve, and output can never be public/live ready.
    if payload.get("approved_by_system"):
        blocked.append("approved_by_system must be false; system cannot approve")
    if payload.get("public_ready"):
        blocked.append("public_ready must be false")
    if payload.get("operator_review_required") is not True:
        blocked.append("operator_review_required must be true for editorial output")

    text = payload.get("produced_text", "")
    for hit in _scan(text, FORBIDDEN_LANGUAGE):
        blocked.append(f"forbidden language: {hit}")
    for hit in _scan(text, INVENTED_AUTHORITY_PATTERNS):
        blocked.append(f"invented authority: {hit}")
    for hit in _scan(text, INVENTED_METRIC_PATTERNS):
        blocked.append(f"invented metric: {hit}")
    for hit in _scan_secrets(payload):
        blocked.append(hit)

    # Self-declared detector fields also force BLOCKED.
    if payload.get("market_call_risk_detected"):
        blocked.append("market_call_risk_detected is true")
    if payload.get("forbidden_language_detected"):
        blocked.append(f"forbidden_language_detected: {payload['forbidden_language_detected']}")
    if payload.get("authority_claims_detected"):
        blocked.append(f"authority_claims_detected: {payload['authority_claims_detected']}")
    if payload.get("hallucination_risk_flags"):
        blocked.append(f"hallucination_risk_flags: {payload['hallucination_risk_flags']}")

    # Cannot invent citations or add unsupported claims.
    if payload.get("citations_added"):
        blocked.append("citations cannot be invented/added by the editorial layer")
    claims_added = payload.get("claims_added", []) or []
    if claims_added:
        # New claims are only tolerable if every one is cited; here, fail closed.
        blocked.append(f"new material claims added without authority: {claims_added}")

    # Cannot remove required limitations: limitations_preserved must be non-empty.
    if not payload.get("limitations_preserved"):
        blocked.append("limitations not preserved (limitations_preserved empty)")

    # REVIEW_REQUIRED when citation completeness is ambiguous but not unsafe.
    if payload.get("citations_missing"):
        review.append(f"citations_missing present: {payload['citations_missing']}")

    # UNKNOWN when lineage is missing.
    if not payload.get("request_id"):
        unknown.append("request_id missing; output lineage unknown")

    return _result(blocked, review, unknown)


def validate_editorial_critique_packet(payload):
    ok, msg = _schema_ok(payload, "scd_editorial_critique_packet.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    # Critique can never approve or make content public.
    if payload.get("approved_by_system"):
        blocked.append("approved_by_system must be false; critique cannot approve")
    if payload.get("public_ready"):
        blocked.append("public_ready must be false")
    if payload.get("operator_review_required") is not True:
        blocked.append("operator_review_required must be true")

    for hit in _scan_secrets(payload):
        blocked.append(hit)

    # final_recommendation must be a valid review state, never an approval.
    rec = payload.get("final_recommendation")
    if rec not in (PASS, BLOCKED, REVIEW_REQUIRED, UNKNOWN):
        blocked.append(f"invalid final_recommendation: {rec}")

    # If any sub-result is BLOCKED, the recommendation cannot be PASS.
    sub_results = [
        payload.get("limitation_preservation_result"),
        payload.get("claim_preservation_result"),
        payload.get("citation_integrity_result"),
        payload.get("hallucination_check_result"),
        payload.get("forbidden_language_result"),
    ]
    if BLOCKED in sub_results and rec == PASS:
        blocked.append("final_recommendation PASS contradicts a BLOCKED sub-result")

    if not payload.get("output_id") or not payload.get("request_id"):
        unknown.append("critique lineage incomplete (missing output/request id)")

    if rec == REVIEW_REQUIRED and not blocked:
        review.append("critique recommends operator review")

    return _result(blocked, review, unknown)


# Registry of editorial validators, in choreography order.
EDITORIAL_VALIDATORS = {
    "editorial_voice_profile": validate_editorial_voice_profile,
    "hook_taxonomy_entry": validate_hook_taxonomy_entry,
    "editorial_workbench_request": validate_editorial_workbench_request,
    "editorial_workbench_output": validate_editorial_workbench_output,
    "editorial_critique_packet": validate_editorial_critique_packet,
}
