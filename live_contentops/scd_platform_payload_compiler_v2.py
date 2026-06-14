"""Platform payload compiler v2 contract validators (SCD, 0174BN).

Local-only, deterministic, fail-closed. This is a NEW, parallel compiler aligned
with the grounded platform capability registry v2. It does not replace the
existing 0174AR compiler (scd_platform_payload_compiler.py); it expands coverage
from 5 to the 9 registry-approved platforms and routes payload shape by the
registry's current_repo_allowed_state semantics.

It NEVER connects to a platform, never calls a provider/LLM/network/API, never
uses a bot or sendMessage, never reads credentials or environment, never
schedules, and never enables live or public publishing. Forbidden-runtime and
secret detectors are single-sourced from the registry v2 module so detector
literals are never re-typed here.

Domain objects validated here:

    SCDPlatformConstraintProfileV2
    SCDPlatformPayloadCompilerV2Input
    SCDPlatformPayloadCompilerV2Output
    SCDPlatformPayloadCompileReportV2

Plus a deterministic local helper, compile_platform_payloads_v2(), that only
wraps supplied source text into per-platform candidates. It invents nothing:
no new citations, claims, links, hashtags, handles, or metrics; text is copied
verbatim; overflow is flagged, never silently truncated.

Validators return {"validation_state": <STATE>, "reasons": [...]}.
"""
from live_contentops.scd_domain_model import (
    PASS,
    BLOCKED,
    REVIEW_REQUIRED,
    UNKNOWN,
    _schema_ok,
)
from live_contentops.scd_platform_capability_registry_v2 import (
    APPROVED_PLATFORM_IDS_V2,
    _value,
    _state,
    _apply_declared_state,
    _rollup,
    _unsafe_runtime_hits,
    _secret_hits,
)

# Parity with the registry v2 approved platform set (9 platforms).
APPROVED_PLATFORMS_V2 = tuple(APPROVED_PLATFORM_IDS_V2)

# Deprecated / shorthand ids -> registry-canonical ids. The legacy 0174AR
# compiler keeps its own "newsletter" id unchanged; only v2 canonicalizes.
PLATFORM_ALIAS_V2 = {
    "x": "x_twitter",
    "twitter": "x_twitter",
    "x/twitter": "x_twitter",
    "newsletter": "substack_newsletter",
    "substack": "substack_newsletter",
}

# Advisory hard character maxima (constraint metadata, not live limits).
PLATFORM_HARD_MAX_V2 = {
    "telegram": 4096,
    "x_twitter": 280,
    "linkedin": 3000,
    "facebook_page": 63206,
    "instagram": 2200,
    "threads": 500,
    "tiktok": 2200,
    "substack_newsletter": 100000,
    "generic_manual": 100000,
}

# Symbolic content surfaces (advisory only).
PLATFORM_SURFACE_V2 = {
    "telegram": "channel_post",
    "x_twitter": "short_post",
    "linkedin": "professional_post",
    "facebook_page": "page_post",
    "instagram": "caption",
    "threads": "short_post",
    "tiktok": "video_caption",
    "substack_newsletter": "newsletter_section",
    "generic_manual": "manual_export",
}

# Only these platforms compile to manual_export now; everything else is a
# local dry_run preview. No platform compiles to live behavior of any kind.
MANUAL_EXPORT_PLATFORMS_V2 = ("substack_newsletter", "generic_manual")

# These platforms remain REVIEW_REQUIRED (future high-friction) even when no
# hostile condition is present.
HIGH_FRICTION_REVIEW_PLATFORMS_V2 = ("tiktok",)

# Allowed local payload shapes / modes. No live, dispatch, or posting shape.
ALLOWED_PAYLOAD_SHAPES_V2 = ("dry_run", "manual_export")

# "*_now" / readiness flags that must never be true on any v2 compiler object.
REQUIRED_FALSE_FLAGS_V2 = (
    "public_ready",
    "live_eligibility",
    "live_ready",
    "dispatch_ready",
    "live_api_enabled_now",
    "live_api_supported_now",
    "platform_api_allowed_now",
    "credential_read_allowed_now",
    "credentials_requested_now",
    "posting_enabled_now",
    "scheduler_enabled_now",
    "autonomous_replies_enabled_now",
    "dms_enabled_now",
    "scraping_enabled_now",
)

SCHEMA_BY_KIND_V2 = {
    "constraint_profile_v2": "scd_platform_constraint_profile_v2.schema.json",
    "compiler_v2_input": "scd_platform_payload_compiler_v2_input.schema.json",
    "compiler_v2_output": "scd_platform_payload_compiler_v2_output.schema.json",
    "compile_report_v2": "scd_platform_payload_compile_report_v2.schema.json",
}


def normalize_platform_id_v2(platform_id):
    """Map shorthand/deprecated ids to registry-canonical ids."""
    if not isinstance(platform_id, str):
        return platform_id
    key = platform_id.strip().lower()
    return PLATFORM_ALIAS_V2.get(key, key)


def shape_for_platform_v2(platform_id):
    """Return the only allowed local shape for a canonical platform id."""
    if platform_id in MANUAL_EXPORT_PLATFORMS_V2:
        return "manual_export"
    return "dry_run"


def _schema_state_v2(packet, kind):
    ok, message = _schema_ok(packet, SCHEMA_BY_KIND_V2[kind])
    if ok:
        return []
    return [f"schema:{message}"]


def _required_false_hits_v2(packet):
    hits = []
    for flag in REQUIRED_FALSE_FLAGS_V2:
        if _value(packet, flag) is True:
            hits.append(f"{flag}_must_be_false")
    return hits


# --- Validators ----------------------------------------------------------------------

def validate_platform_constraint_profile_v2(packet):
    blocked = _schema_state_v2(packet, "constraint_profile_v2")
    review = []
    unknown = []

    platform_id = _value(packet, "platform_id")
    if platform_id not in APPROVED_PLATFORMS_V2:
        unknown.append(f"platform_not_in_v2_registry:{platform_id}")

    if _value(packet, "manual_publish_only") is not True:
        blocked.append("manual_publish_only_must_be_true")

    shape = _value(packet, "payload_shape")
    if shape not in ALLOWED_PAYLOAD_SHAPES_V2:
        blocked.append(f"invalid_payload_shape:{shape}")
    elif platform_id in APPROVED_PLATFORMS_V2 and shape != shape_for_platform_v2(platform_id):
        blocked.append(f"payload_shape_mismatch:{platform_id}:{shape}")

    blocked.extend(_required_false_hits_v2(packet))
    blocked.extend(_unsafe_runtime_hits(packet))
    blocked.extend(_secret_hits(packet))

    if platform_id in HIGH_FRICTION_REVIEW_PLATFORMS_V2:
        review.append(f"high_friction_last_priority:{platform_id}")

    return _apply_declared_state(packet, _state(blocked, review, unknown))


def validate_platform_payload_compiler_v2_input(packet):
    blocked = _schema_state_v2(packet, "compiler_v2_input")
    review = []
    unknown = []

    if _value(packet, "operator_review_required") is not True:
        blocked.append("operator_review_required_must_be_true")

    blocked.extend(_required_false_hits_v2(packet))
    blocked.extend(_unsafe_runtime_hits(packet))
    blocked.extend(_secret_hits(packet))

    requested = _value(packet, "requested_platforms", []) or []
    for raw in requested:
        pid = normalize_platform_id_v2(raw)
        if pid not in APPROVED_PLATFORMS_V2:
            unknown.append(f"requested_platform_not_approved:{raw}")

    if not _value(packet, "canonical_post_id") or not _value(packet, "editorial_output_id"):
        unknown.append("missing_canonical_or_editorial_lineage")
    if not _value(packet, "source_text"):
        unknown.append("missing_source_text")
    if not requested:
        unknown.append("no_requested_platforms")

    if _value(packet, "source_citations") == []:
        review.append("source_citations_empty_confirm_none_required")
    if _value(packet, "source_limitations") == []:
        review.append("source_limitations_empty_confirm_none_required")

    return _apply_declared_state(packet, _state(blocked, review, unknown))


def validate_platform_payload_compiler_v2_output(packet):
    blocked = _schema_state_v2(packet, "compiler_v2_output")
    review = []
    unknown = []

    if _value(packet, "operator_review_required") is not True:
        blocked.append("operator_review_required_must_be_true")

    blocked.extend(_required_false_hits_v2(packet))
    blocked.extend(_unsafe_runtime_hits(packet))
    blocked.extend(_secret_hits(packet))

    payloads = _value(packet, "platform_payloads", []) or []
    if not payloads:
        unknown.append("no_platform_payloads")

    for pp in payloads:
        pid = _value(pp, "platform_id")
        if pid not in APPROVED_PLATFORMS_V2:
            unknown.append(f"payload_platform_not_approved:{pid}")
            continue

        expected_shape = shape_for_platform_v2(pid)
        shape = _value(pp, "payload_shape")
        mode = _value(pp, "mode")
        if shape != expected_shape:
            blocked.append(f"payload_shape_mismatch:{pid}:{shape}")
        if mode not in ALLOWED_PAYLOAD_SHAPES_V2:
            blocked.append(f"invalid_mode:{pid}:{mode}")
        elif mode != expected_shape:
            blocked.append(f"mode_must_match_shape:{pid}:{mode}")

        cmax = _value(pp, "character_limit_max")
        ccount = _value(pp, "character_count")
        if isinstance(cmax, int) and isinstance(ccount, int) and ccount > cmax:
            blocked.append(f"character_overflow:{pid}:{ccount}>{cmax}")
        hard = PLATFORM_HARD_MAX_V2.get(pid)
        if hard and isinstance(ccount, int) and ccount > hard:
            blocked.append(f"character_overflow_hard:{pid}:{ccount}>{hard}")

        for link in _value(pp, "links", []) or []:
            if isinstance(link, str) and link.strip():
                review.append(f"link_present_confirm_from_source:{pid}")

        if pid in HIGH_FRICTION_REVIEW_PLATFORMS_V2:
            review.append(f"high_friction_last_priority:{pid}")

    sub_fields = (
        "disclosure_preservation_result",
        "limitation_preservation_result",
        "citation_preservation_result",
        "character_limit_result",
        "claim_integrity_result",
        "platform_constraint_result",
    )
    sub_values = [_value(packet, f) for f in sub_fields]
    if BLOCKED in sub_values:
        blocked.append("sub_result_blocked")
    if UNKNOWN in sub_values:
        unknown.append("sub_result_unknown")
    if REVIEW_REQUIRED in sub_values:
        review.append("sub_result_review_required")

    if not _value(packet, "compiler_input_id"):
        unknown.append("compiler_input_id_missing")

    return _apply_declared_state(packet, _state(blocked, review, unknown))


def validate_platform_payload_compile_report_v2(packet):
    blocked = _schema_state_v2(packet, "compile_report_v2")
    review = []
    unknown = []

    if _value(packet, "live_ready") is True:
        blocked.append("live_ready_must_be_false")
    if _value(packet, "dispatch_ready") is True:
        blocked.append("dispatch_ready_must_be_false")
    if _value(packet, "operator_review_required") is not True:
        blocked.append("operator_review_required_must_be_true")

    blocked.extend(_required_false_hits_v2(packet))
    blocked.extend(_unsafe_runtime_hits(packet))
    blocked.extend(_secret_hits(packet))

    per_platform = _value(packet, "per_platform_results", []) or []
    results = [_value(r, "result") for r in per_platform]
    rec = _value(packet, "final_recommendation")

    if rec not in (PASS, BLOCKED, REVIEW_REQUIRED, UNKNOWN):
        blocked.append(f"invalid_final_recommendation:{rec}")

    # Fail-closed precedence: a report cannot PASS unless every per-platform
    # result is PASS, and a declared PASS that contradicts the rolled-up state
    # is escalated to BLOCKED via _apply_declared_state below.
    if rec == PASS and not results:
        blocked.append("final_pass_requires_per_platform_results")
    if rec == PASS and any(r != PASS for r in results):
        blocked.append("final_pass_requires_all_per_platform_pass")
    if results:
        rolled = _rollup([r for r in results if r in (PASS, BLOCKED, REVIEW_REQUIRED, UNKNOWN)])
        if rec == PASS and rolled != PASS:
            blocked.append(f"final_recommendation_contradicts_rollup:{rolled}")

    if not per_platform:
        unknown.append("no_per_platform_results")
    if not _value(packet, "compiler_output_id"):
        unknown.append("compiler_output_id_missing")

    if rec == REVIEW_REQUIRED and not blocked:
        review.append("report_recommends_operator_review")

    return _apply_declared_state(packet, _state(blocked, review, unknown))


# --- Deterministic local compiler helper ---------------------------------------------

def compile_platform_payloads_v2(input_packet, constraint_profiles):
    """Deterministically wrap supplied source text into per-platform candidates.

    Invents nothing: no new citations, claims, links, hashtags, handles, or
    metrics. Only the supplied source_text/limitations/citations are carried
    forward verbatim. Shape is routed by platform (manual_export for
    substack_newsletter/generic_manual, dry_run otherwise). Overflow is flagged
    via character_count vs character_limit_max, never silently truncated. Every
    candidate keeps operator_review_required true and all live/public flags
    false. Returns a list of payload candidate dicts.
    """
    text = input_packet.get("source_text", "")
    limitations = list(input_packet.get("source_limitations", []) or [])
    citations = list(input_packet.get("source_citations", []) or [])
    profiles_by_id = {}
    for profile in constraint_profiles or []:
        profiles_by_id[normalize_platform_id_v2(profile.get("platform_id"))] = profile

    candidates = []
    for raw_pid in input_packet.get("requested_platforms", []) or []:
        pid = normalize_platform_id_v2(raw_pid)
        profile = profiles_by_id.get(pid)
        hard = PLATFORM_HARD_MAX_V2.get(pid)
        cmax = (profile or {}).get("character_limit_max", hard or 0)
        shape = shape_for_platform_v2(pid)
        candidates.append({
            "platform_id": pid,
            "requested_as": raw_pid,
            "content_surface": PLATFORM_SURFACE_V2.get(pid, "manual_export"),
            "text": text,
            "character_count": len(text),
            "character_limit_max": cmax,
            "payload_shape": shape,
            "mode": shape,
            "disclosure_fields": list((profile or {}).get("required_disclosure_fields", [])),
            "limitations": limitations,
            "citations": citations,
            "hashtags": [],
            "links": [],
            "unsupported_feature_flags": list((profile or {}).get("unsupported_features", [])),
            "operator_review_required": True,
            "public_ready": False,
            "live_eligibility": False,
        })
    return candidates


def rollup_compile_report_v2(per_platform_results):
    """Roll up per-platform result states into a fail-closed recommendation.

    PASS only if every per-platform result is PASS; otherwise BLOCKED > UNKNOWN
    > REVIEW_REQUIRED precedence applies. An empty result set is UNKNOWN.
    """
    states = [r for r in per_platform_results if r in (PASS, BLOCKED, REVIEW_REQUIRED, UNKNOWN)]
    if not states:
        return UNKNOWN
    return _rollup(states)


# --- Local-only builder API ----------------------------------------------------------

def build_constraint_profiles_from_registry_v2(platform_profiles):
    """Build one v2 constraint profile per approved registry platform.

    Takes registry v2 profile packets (symbolic capability descriptors) and
    emits schema-valid SCDPlatformConstraintProfileV2 dicts. Platform ids are
    normalized; substack_newsletter/generic_manual route to manual_export and
    every other approved platform routes to dry_run. All live/API/credential/
    scheduler/public/dispatch flags are forced false, manual_publish_only and
    operator_review_required are forced true, and only symbolic metadata is
    copied (no official URLs, no executable endpoints). Input profiles are never
    mutated. Unknown/unapproved platforms are skipped. Each returned profile is
    built to validate through validate_platform_constraint_profile_v2 (PASS, or
    REVIEW_REQUIRED for high-friction platforms such as tiktok).
    """
    built = []
    seen = set()
    for raw in platform_profiles or []:
        pid = normalize_platform_id_v2(_value(raw, "platform_id"))
        if pid not in APPROVED_PLATFORMS_V2 or pid in seen:
            continue
        seen.add(pid)
        shape = shape_for_platform_v2(pid)
        declared = REVIEW_REQUIRED if pid in HIGH_FRICTION_REVIEW_PLATFORMS_V2 else PASS
        built.append({
            "schema_version": "0174bn-v2",
            "profile_id": f"cp_v2_{pid}",
            "platform_id": pid,
            "label": f"{pid} ({shape} preview only)",
            "content_surface": PLATFORM_SURFACE_V2.get(pid, "manual_export"),
            "payload_shape": shape,
            "character_limit_max": PLATFORM_HARD_MAX_V2.get(pid, 0),
            "supports_links": False,
            "supports_hashtags": False,
            "supports_threading": False,
            "supports_media": False,
            "required_disclosure_fields": [],
            "required_limitation_fields": [],
            "unsupported_features": [],
            "registry_allowed_state": _value(raw, "current_repo_allowed_state", ""),
            "manual_publish_only": True,
            "public_ready": False,
            "live_eligibility": False,
            "live_ready": False,
            "dispatch_ready": False,
            "live_api_enabled_now": False,
            "platform_api_allowed_now": False,
            "credential_read_allowed_now": False,
            "scheduler_enabled_now": False,
            "validation_state": declared,
        })
    return built


def _payload_result_v2(payload):
    """Fail-closed per-platform result for a single compiler output payload.

    BLOCKED on forbidden flags/runtime/secret hits, shape/mode mismatch, or
    character overflow; UNKNOWN for unapproved/missing platform ids;
    REVIEW_REQUIRED for high-friction platforms (e.g. tiktok) otherwise; PASS
    only for clean, in-shape, in-limit payloads.
    """
    pid = _value(payload, "platform_id")
    if pid not in APPROVED_PLATFORMS_V2:
        return UNKNOWN

    blocked = []
    blocked.extend(_required_false_hits_v2(payload))
    blocked.extend(_unsafe_runtime_hits(payload))
    blocked.extend(_secret_hits(payload))

    expected_shape = shape_for_platform_v2(pid)
    if _value(payload, "payload_shape") != expected_shape:
        blocked.append("payload_shape_mismatch")
    mode = _value(payload, "mode")
    if mode not in ALLOWED_PAYLOAD_SHAPES_V2 or mode != expected_shape:
        blocked.append("invalid_mode")

    cmax = _value(payload, "character_limit_max")
    ccount = _value(payload, "character_count")
    if isinstance(cmax, int) and isinstance(ccount, int) and ccount > cmax:
        blocked.append("character_overflow")
    hard = PLATFORM_HARD_MAX_V2.get(pid)
    if hard and isinstance(ccount, int) and ccount > hard:
        blocked.append("character_overflow_hard")

    if blocked:
        return BLOCKED
    if pid in HIGH_FRICTION_REVIEW_PLATFORMS_V2:
        return REVIEW_REQUIRED
    return PASS


def build_platform_payload_compile_report_v2(compiler_output):
    """Build a schema-valid compile report from a compiler v2 output packet.

    Validates the supplied output, derives a fail-closed per-platform result for
    each payload, and rolls them up (incorporating the overall output state so a
    non-PASS output can never yield a PASS report). live_ready, dispatch_ready,
    and every *_now flag are forced false; operator_review_required is forced
    true. The returned packet is built to validate through
    validate_platform_payload_compile_report_v2.
    """
    output_state = validate_platform_payload_compiler_v2_output(compiler_output)["validation_state"]
    payloads = _value(compiler_output, "platform_payloads", []) or []

    per_platform = []
    blocked_p, review_p, pass_p, unknown_p = [], [], [], []
    for payload in payloads:
        pid = _value(payload, "platform_id")
        result = _payload_result_v2(payload)
        per_platform.append({"platform_id": pid, "result": result})
        if result == BLOCKED:
            blocked_p.append(pid)
        elif result == REVIEW_REQUIRED:
            review_p.append(pid)
        elif result == UNKNOWN:
            unknown_p.append(pid)
        else:
            pass_p.append(pid)

    rollup_inputs = [r["result"] for r in per_platform]
    if output_state != PASS:
        rollup_inputs = rollup_inputs + [output_state]
    recommendation = rollup_compile_report_v2(rollup_inputs)

    output_id = _value(compiler_output, "compiler_output_id", "")
    return {
        "schema_version": "0174bn-v2",
        "compile_report_id": f"crep_v2_from_{output_id}" if output_id else "crep_v2_from_unknown",
        "compiler_input_id": _value(compiler_output, "compiler_input_id", ""),
        "compiler_output_id": output_id,
        "per_platform_results": per_platform,
        "blocked_platforms": blocked_p,
        "review_required_platforms": review_p,
        "pass_platforms": pass_p,
        "unknown_platforms": unknown_p,
        "final_recommendation": recommendation,
        "live_ready": False,
        "dispatch_ready": False,
        "platform_api_allowed_now": False,
        "credential_read_allowed_now": False,
        "credentials_requested_now": False,
        "posting_enabled_now": False,
        "scheduler_enabled_now": False,
        "autonomous_replies_enabled_now": False,
        "dms_enabled_now": False,
        "scraping_enabled_now": False,
        "public_ready": False,
        "live_eligibility": False,
        "operator_review_required": True,
        "validation_state": recommendation,
    }


def build_compiler_v2_summary(compiler_input, compiler_output, compile_report):
    """Build a pure in-memory summary of a v2 compile cycle.

    No filesystem writes, no network, no provider/platform/credential access.
    Returns normalized requested platforms, counts, the report's rolled-up
    recommendation/state, and per-platform non-PASS reasons. The live_ready,
    public_ready, and dispatch_ready booleans are hard-coded false and can never
    be granted by this function.
    """
    requested = [
        normalize_platform_id_v2(p)
        for p in _value(compiler_input, "requested_platforms", []) or []
    ]
    payloads = _value(compiler_output, "platform_payloads", []) or []
    reasons = []
    for entry in _value(compile_report, "per_platform_results", []) or []:
        result = _value(entry, "result")
        if result != PASS:
            reasons.append(f"{_value(entry, 'platform_id')}:{result}")

    return {
        "platform_count": len(requested),
        "requested_platforms": requested,
        "output_payload_count": len(payloads),
        "final_recommendation": _value(compile_report, "final_recommendation"),
        "validation_state": _value(compile_report, "validation_state"),
        "operator_review_required": True,
        "live_ready": False,
        "public_ready": False,
        "dispatch_ready": False,
        "live_eligibility": False,
        "reasons": reasons,
    }


# Registry of v2 compiler validators, keyed for data-driven hostile tests.
PLATFORM_PAYLOAD_COMPILER_V2_VALIDATORS = {
    "platform_constraint_profile_v2": validate_platform_constraint_profile_v2,
    "platform_payload_compiler_v2_input": validate_platform_payload_compiler_v2_input,
    "platform_payload_compiler_v2_output": validate_platform_payload_compiler_v2_output,
    "platform_payload_compile_report_v2": validate_platform_payload_compile_report_v2,
}
