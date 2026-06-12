"""Platform payload compiler contract validators (SCD, 0174AR).

Local-only, deterministic, fail-closed. This module defines the CONTRACT and
VALIDATION for compiling a safe CanonicalSocialPost / editorial output into
per-platform payloads. It NEVER connects to a platform, never calls a
provider/LLM/network/API, never uses a Telegram bot or sendMessage, never reads
credentials, never schedules, and never enables live or public publishing.

Domain objects validated here:

    SCDPlatformConstraintProfile
    SCDPlatformPayloadCompilerInput
    SCDPlatformPayloadCompilerOutput
    SCDPlatformPayloadCompileReport

Plus a deterministic local helper, compile_platform_payloads(), that only wraps
supplied source text into per-platform candidates. It invents nothing.

Validators return {"validation_state": <STATE>, "reasons": [...]}.
"""
import re

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

# Approved platform registry for this task.
APPROVED_PLATFORMS = {
    "x_twitter",
    "linkedin",
    "telegram",
    "newsletter",
    "generic_manual",
}

# Hard character maxima per platform (constraint profiles, not live limits).
PLATFORM_HARD_MAX = {
    "x_twitter": 280,
    "linkedin": 3000,
    "telegram": 4096,
    "newsletter": 100000,
    "generic_manual": 100000,
}

# Telegram bot / live-API / network implication patterns -> BLOCKED.
TELEGRAM_API_PATTERNS = [
    r"\btelegram bot\b", r"\bbot[_-]?token\b", r"\bsendmessage\b",
    r"\bbot api\b", r"api\.telegram\.org", r"\.post\(", r"\bwebhook\b",
    r"\bgetupdates\b", r"\bchat_id\b",
]


def _scan(text, patterns):
    return _find_language(text, patterns)


def _all_unsafe(text):
    """Return all forbidden/authority/metric/telegram-api hits in text."""
    hits = []
    hits += [f"forbidden language: {h}" for h in _scan(text, FORBIDDEN_LANGUAGE)]
    hits += [f"invented authority: {h}" for h in _scan(text, INVENTED_AUTHORITY_PATTERNS)]
    hits += [f"invented metric: {h}" for h in _scan(text, INVENTED_METRIC_PATTERNS)]
    hits += [f"telegram/api implication: {h}" for h in _scan(text, TELEGRAM_API_PATTERNS)]
    return hits


def validate_platform_constraint_profile(payload):
    ok, msg = _schema_ok(payload, "scd_platform_constraint_profile.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    if payload.get("manual_publish_only") is not True:
        blocked.append("manual_publish_only must be true")
    if payload.get("live_api_supported_future"):
        blocked.append("live_api_supported_future must be false in this task")
    if payload.get("credential_required_future"):
        blocked.append("credential_required_future must be false in this task")

    platform_id = payload.get("platform_id")
    if platform_id not in APPROVED_PLATFORMS:
        unknown.append(f"platform_id '{platform_id}' not in approved registry")

    # Telegram profile must not imply bot/API anywhere.
    for hit in _scan_secrets(payload):
        blocked.append(hit)
    for field in ("unsupported_features", "required_disclosure_fields"):
        for item in payload.get(field, []):
            for h in _scan(item, TELEGRAM_API_PATTERNS):
                blocked.append(f"telegram/api implication in {field}: {h}")

    hard = PLATFORM_HARD_MAX.get(platform_id)
    if hard and payload.get("character_limit_max", 0) > hard:
        review.append(
            f"character_limit_max {payload.get('character_limit_max')} exceeds known hard max {hard}"
        )

    return _result(blocked, review, unknown)


def validate_platform_payload_compiler_input(payload):
    ok, msg = _schema_ok(payload, "scd_platform_payload_compiler_input.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    if payload.get("public_ready"):
        blocked.append("public_ready must be false")
    if payload.get("live_eligibility"):
        blocked.append("live_eligibility must be false")
    if payload.get("operator_review_required") is not True:
        blocked.append("operator_review_required must be true")

    text = payload.get("source_text", "")
    for hit in _all_unsafe(text):
        blocked.append(hit)
    for hit in _scan_secrets(payload):
        blocked.append(hit)

    # Unknown platform handling.
    requested = payload.get("requested_platforms", []) or []
    for p in requested:
        if p not in APPROVED_PLATFORMS:
            unknown.append(f"requested platform '{p}' not in approved registry")

    # Lineage / source completeness.
    if not payload.get("canonical_post_id") or not payload.get("editorial_output_id"):
        unknown.append("missing canonical/editorial lineage")
    if not payload.get("source_text"):
        unknown.append("missing source_text; nothing to compile")
    if not requested:
        unknown.append("no requested_platforms")

    # Missing citations/limitations: review (recoverable) unless dropped later.
    if payload.get("source_citations") == []:
        review.append("source_citations empty; confirm none required")
    if payload.get("source_limitations") == []:
        review.append("source_limitations empty; confirm none required")

    return _result(blocked, review, unknown)


def _result_to_state(value):
    return value if value in (PASS, BLOCKED, REVIEW_REQUIRED, UNKNOWN) else None


def validate_platform_payload_compiler_output(payload):
    ok, msg = _schema_ok(payload, "scd_platform_payload_compiler_output.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    if payload.get("public_ready"):
        blocked.append("public_ready must be false")
    if payload.get("live_eligibility"):
        blocked.append("live_eligibility must be false")
    if payload.get("operator_review_required") is not True:
        blocked.append("operator_review_required must be true")

    for hit in _scan_secrets(payload):
        blocked.append(hit)

    payloads = payload.get("platform_payloads", []) or []
    if not payloads:
        unknown.append("no platform_payloads; nothing compiled")

    for pp in payloads:
        pid = pp.get("platform_id")
        text = pp.get("text", "")
        # Unsafe language / authority / metric / telegram-api implication.
        for hit in _all_unsafe(text):
            blocked.append(f"{pid}: {hit}")
        # Mode must be dry_run or mock_only.
        if pp.get("mode") not in ("dry_run", "mock_only"):
            blocked.append(f"{pid}: invalid mode '{pp.get('mode')}'")
        # Unknown platform.
        if pid not in APPROVED_PLATFORMS:
            unknown.append(f"{pid}: platform not in approved registry")
        # Hard character-limit overflow blocks.
        cmax = pp.get("character_limit_max")
        ccount = pp.get("character_count")
        if isinstance(cmax, int) and isinstance(ccount, int) and ccount > cmax:
            blocked.append(f"{pid}: character overflow {ccount} > {cmax}")
        hard = PLATFORM_HARD_MAX.get(pid)
        if hard and isinstance(ccount, int) and ccount > hard:
            blocked.append(f"{pid}: character overflow {ccount} > hard max {hard}")
        # Invented links/handles/hashtags are not permitted (links must be absent
        # unless they were in source; the compiler invents nothing).
        for link in pp.get("links", []) or []:
            if link.strip():
                review.append(f"{pid}: link present, confirm it came from source")

    # Sub-result fields: any BLOCKED forces output BLOCKED.
    sub_fields = [
        "disclosure_preservation_result",
        "limitation_preservation_result",
        "citation_preservation_result",
        "character_limit_result",
        "claim_integrity_result",
        "platform_constraint_result",
    ]
    sub_values = [payload.get(f) for f in sub_fields]
    if BLOCKED in sub_values:
        blocked.append("a preservation/constraint sub-result is BLOCKED")
    if UNKNOWN in sub_values:
        unknown.append("a preservation/constraint sub-result is UNKNOWN")
    if REVIEW_REQUIRED in sub_values:
        review.append("a preservation/constraint sub-result is REVIEW_REQUIRED")

    if not payload.get("compiler_input_id"):
        unknown.append("compiler_input_id missing; lineage unknown")

    return _result(blocked, review, unknown)


def validate_platform_payload_compile_report(payload):
    ok, msg = _schema_ok(payload, "scd_platform_payload_compile_report.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    # Live / dispatch readiness can never be granted by a compile report.
    if payload.get("live_ready"):
        blocked.append("live_ready must be false")
    if payload.get("dispatch_ready"):
        blocked.append("dispatch_ready must be false")
    if payload.get("operator_review_required") is not True:
        blocked.append("operator_review_required must be true")

    for hit in _scan_secrets(payload):
        blocked.append(hit)

    per_platform = payload.get("per_platform_results", []) or []
    results = [r.get("result") for r in per_platform]
    rec = payload.get("final_recommendation")

    # Fail-closed precedence: report cannot PASS if any platform is not PASS.
    if BLOCKED in results and rec == PASS:
        blocked.append("final PASS contradicts a BLOCKED per-platform result")
    if rec == PASS and any(r != PASS for r in results):
        blocked.append("final PASS requires all per-platform results to be PASS")

    if rec not in (PASS, BLOCKED, REVIEW_REQUIRED, UNKNOWN):
        blocked.append(f"invalid final_recommendation: {rec}")

    if not per_platform:
        unknown.append("no per_platform_results")
    if not payload.get("compiler_output_id"):
        unknown.append("compiler_output_id missing; lineage unknown")

    if rec == REVIEW_REQUIRED and not blocked:
        review.append("compile report recommends operator review")

    return _result(blocked, review, unknown)


# --- Deterministic local compiler helper ---------------------------------------------

def compile_platform_payloads(input_packet, constraint_profiles):
    """Deterministically wrap supplied source text into per-platform candidates.

    Invents nothing: no new citations, claims, links, hashtags, handles, or
    metrics. Only the supplied source_text/limitations/citations are carried
    forward. Every candidate is dry_run mode and overflow is flagged, never
    silently truncated. Returns a list of payload candidate dicts.
    """
    text = input_packet.get("source_text", "")
    limitations = list(input_packet.get("source_limitations", []) or [])
    citations = list(input_packet.get("source_citations", []) or [])
    profiles_by_id = {p.get("platform_id"): p for p in constraint_profiles}

    candidates = []
    for pid in input_packet.get("requested_platforms", []) or []:
        profile = profiles_by_id.get(pid)
        hard = PLATFORM_HARD_MAX.get(pid)
        cmax = (profile or {}).get("character_limit_max", hard or 0)
        candidates.append({
            "platform_id": pid,
            "text": text,
            "character_count": len(text),
            "character_limit_max": cmax,
            "disclosure_fields": list((profile or {}).get("required_disclosure_fields", [])),
            "limitations": limitations,
            "citations": citations,
            "hashtags": [],
            "links": [],
            "unsupported_feature_flags": list((profile or {}).get("unsupported_features", [])),
            "mode": "dry_run",
        })
    return candidates


# Registry of compiler validators, in choreography order.
COMPILER_VALIDATORS = {
    "platform_constraint_profile": validate_platform_constraint_profile,
    "platform_payload_compiler_input": validate_platform_payload_compiler_input,
    "platform_payload_compiler_output": validate_platform_payload_compiler_output,
    "platform_payload_compile_report": validate_platform_payload_compile_report,
}
