"""LLM quota / retry discipline policy validator (SCD, 0174AY).

Local-only, deterministic, fail-closed. This module defines the CONTRACT and
VALIDATION for the LLM quota/retry discipline policy that MUST be satisfied
before any real provider/LLM adapter is built.

It NEVER calls a provider/LLM/API, never reads credentials or env, never
touches the network, never schedules, never opens a browser, and never enables
live or public posting. The validator only inspects a supplied local policy
dictionary.

The codified architecture forbids the quota-burning rewrite loop:

    draft -> validator fails -> full rewrite -> fails -> full rewrite -> ...

and instead requires: validate locally first, compile a deterministic prompt
pack, run max 1 canonical generation, validate locally, allow max 1 targeted
repair for minor/localized failures only (preserving citations, limitations,
source refs, claim meaning, and non-signal framing), then route to
REVIEW_REQUIRED / BLOCKED for the operator. No full rewrite unless an explicit
operator override is present (and even then the policy can never be PASS).

Domain object validated here:

    SCDLLMQuotaRetryPolicy

Validator returns {"validation_state": <STATE>, "reasons": [...]}.
"""
from live_contentops.scd_domain_model import (
    PASS,
    BLOCKED,
    REVIEW_REQUIRED,
    UNKNOWN,
    _schema_ok,
    _find_language,
    _scan_secrets,
    _result,
)
from live_contentops.scd_platform_payload_compiler import TELEGRAM_API_PATTERNS
from live_contentops.scd_dispatch_gate import NETWORK_API_PATTERNS

# Forbidden retry/loop language -> BLOCKED. These phrases describe the exact
# quota-burning patterns the policy must never sanction.
LOOP_LANGUAGE_PATTERNS = [
    r"generate until (pass|it passes|success)",
    r"retry until (success|pass|it passes)",
    r"auto[- ]?regenerate",
    r"\bunbounded\b",
    r"rewrite (the )?entire draft repeatedly",
    r"repeatedly rewrite",
    r"infinite (retry|retries|loop)",
    r"loop until (pass|success|it passes)",
    r"keep (re)?generating",
    r"regenerate until",
    r"full rewrite loop",
]

# Flags that MUST be true for a compliant policy.
REQUIRED_TRUE_FLAGS = (
    "pre_llm_validation_required",
    "post_llm_validation_required",
    "deterministic_validator_primary",
    "llm_critique_optional_only",
    "platform_variants_require_canonical_pass",
    "targeted_repair_only_for_minor_failures",
    "preserve_citations_required",
    "preserve_limitations_required",
    "preserve_source_refs_required",
    "preserve_claim_meaning_required",
    "preserve_non_signal_framing_required",
    "review_required_after_second_failure",
    "block_after_major_safety_failure",
    "cache_key_required",
    "spend_tracking_required",
    "model_output_never_authority",
    "human_review_required_on_failure",
    "no_public_ready_claim",
    "no_live_dispatch",
)

# Flags that MUST be false (or absent/falsey) for a compliant policy.
REQUIRED_FALSE_FLAGS = (
    "provider_api_allowed",
    "network_allowed",
    "credentials_required",
    "allow_infinite_retry",
    "allow_full_rewrite_loop",
)

REQUIRED_CACHE_COMPONENTS = (
    "brief_hash",
    "prompt_version",
    "source_packet_hash",
    "model_config",
)

REQUIRED_SPEND_FIELDS = (
    "estimated_tokens",
    "actual_tokens",
    "estimated_cost",
    "actual_cost",
    "provider_name",
    "model_name",
)


def _scan(text, patterns):
    return _find_language(text, patterns)


def _scan_all_strings(obj, patterns):
    """Recursively scan keys and string values against the given patterns."""
    found = []

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(k, str):
                    found.extend(_scan(k, patterns))
                walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, str):
            found.extend(_scan(node, patterns))

    walk(obj)
    return found


def validate_llm_quota_retry_policy(payload):
    ok, msg = _schema_ok(payload, "scd_llm_quota_retry_policy.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    # Secret + provider/network/API + forbidden-loop language scans.
    blocked += _scan_secrets(payload)
    blocked += [f"network/api implication: {h}" for h in _scan_all_strings(payload, NETWORK_API_PATTERNS)]
    blocked += [f"telegram/api implication: {h}" for h in _scan_all_strings(payload, TELEGRAM_API_PATTERNS)]
    blocked += [f"forbidden loop language: {h}" for h in _scan_all_strings(payload, LOOP_LANGUAGE_PATTERNS)]

    # Flags that must be true.
    for flag in REQUIRED_TRUE_FLAGS:
        if payload.get(flag) is not True:
            blocked.append(f"{flag} must be true")

    # Flags that must be false/absent.
    for flag in REQUIRED_FALSE_FLAGS:
        if payload.get(flag):
            blocked.append(f"{flag} must be false")

    # Bounded generation: exactly one canonical generation.
    if payload.get("max_generation_attempts") != 1:
        blocked.append("max_generation_attempts must be 1")

    # Bounded targeted repair: at most one.
    repair = payload.get("max_targeted_repair_attempts")
    if not isinstance(repair, int) or isinstance(repair, bool) or repair < 0 or repair > 1:
        blocked.append("max_targeted_repair_attempts must be 0 or 1")

    # Full rewrite forbidden unless an explicit operator override is present, and
    # even then the policy can never be PASS (downgraded to REVIEW_REQUIRED).
    rewrite = payload.get("max_full_rewrite_attempts")
    if rewrite != 0:
        if payload.get("explicit_operator_override") is True:
            review.append("max_full_rewrite_attempts > 0 only via explicit operator override; cannot PASS")
        else:
            blocked.append("max_full_rewrite_attempts must be 0 unless explicit_operator_override")

    # Spend tracking field coverage (required -> BLOCKED if incomplete).
    spend_fields = payload.get("spend_fields_required", []) or []
    missing_spend = [f for f in REQUIRED_SPEND_FIELDS if f not in spend_fields]
    if missing_spend:
        blocked.append(f"spend_fields_required missing: {missing_spend}")

    # Cache-key component coverage. Missing/incomplete -> UNKNOWN (lineage), not a
    # hard block: the policy intent is present but the cache contract is unproven.
    components = payload.get("cache_key_components", []) or []
    missing_components = [c for c in REQUIRED_CACHE_COMPONENTS if c not in components]
    if not components:
        unknown.append("cache_key_components missing; cache key lineage unknown")
    elif missing_components:
        unknown.append(f"cache_key_components missing required: {missing_components}")

    # Optional LLM critique enabled but no budget -> REVIEW_REQUIRED (not primary safety).
    if payload.get("llm_critique_enabled") and not payload.get("llm_critique_budget"):
        review.append("llm_critique_enabled without llm_critique_budget")

    return _result(blocked, review, unknown)


# Registry of quota/retry policy validators.
LLM_QUOTA_RETRY_VALIDATORS = {
    "llm_quota_retry_policy": validate_llm_quota_retry_policy,
}
