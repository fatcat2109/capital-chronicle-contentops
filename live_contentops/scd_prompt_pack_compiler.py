"""Deterministic prompt-pack compiler contract validators (SCD, 0174AZ).

Local-only, deterministic, fail-closed. This module defines the CONTRACT and
VALIDATION for turning a validated content-intent / brief packet into a bounded
writer prompt pack and a targeted repair prompt pack, WITHOUT calling any LLM
provider.

It NEVER calls a provider/LLM/API, never reads credentials or env, never
touches the network, never uses a Telegram bot / webhook / OAuth, never
schedules, never opens a browser, and never enables live or public posting. The
validators only inspect supplied local dictionaries; the compile helpers only
rearrange supplied local fields and invent nothing.

This operationalizes the 0174AY quota/retry discipline BEFORE any provider
gateway exists: quota is saved by making the first prompt strong (one canonical
generation) and by ensuring repair prompts patch only the failing section.

Domain objects validated here:

    SCDPromptPackInput
    SCDCanonicalWriterPromptPack
    SCDTargetedRepairPromptPack
    SCDPromptPackCacheKey
    SCDPromptPackValidationReport

A prompt-pack PASS means only "ready for future provider-call review" -- never
provider-ready, live-ready, or public-ready.

Validators return {"validation_state": <STATE>, "reasons": [...]}.
"""
import hashlib
import json

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
from live_contentops.scd_llm_quota_retry_policy import LOOP_LANGUAGE_PATTERNS

# Readiness flags that must never be true on any prompt-pack object: a prompt
# pack is never provider/live/public ready by itself.
FORBIDDEN_READY_FLAGS = ("provider_ready", "live_ready", "public_ready")

# Provider/network/credential flags that must be false on prompt-pack objects.
FORBIDDEN_PROVIDER_FLAGS = (
    "provider_api_allowed",
    "network_allowed",
    "credentials_required",
)

# Deterministic prompt-pack fields shared by canonical + repair packs.
REQUIRED_SAFETY_TRUE_FLAGS = (
    "non_signal_framing_required",
    "financial_advice_absent_required",
    "model_output_never_authority",
)

# Cache-key components required by the 0174AY quota policy contract.
REQUIRED_CACHE_KEY_FIELDS = (
    "brief_hash",
    "prompt_version",
    "source_packet_hash",
    "model_config",
    "quota_policy_id",
)

# Repair-pack preservation flags that must all be true.
REPAIR_PRESERVE_FLAGS = (
    "preserve_citations",
    "preserve_limitations",
    "preserve_source_refs",
    "preserve_claim_meaning",
    "preserve_non_signal_framing",
)


def _scan(text, patterns):
    return _find_language(text, patterns)


def _all_unsafe_text(text):
    """Return all forbidden/authority/metric/api/loop hits in a single string."""
    hits = []
    hits += [f"forbidden language: {h}" for h in _scan(text, FORBIDDEN_LANGUAGE)]
    hits += [f"invented authority: {h}" for h in _scan(text, INVENTED_AUTHORITY_PATTERNS)]
    hits += [f"invented metric: {h}" for h in _scan(text, INVENTED_METRIC_PATTERNS)]
    hits += [f"telegram/api implication: {h}" for h in _scan(text, TELEGRAM_API_PATTERNS)]
    hits += [f"network/api/oauth implication: {h}" for h in _scan(text, NETWORK_API_PATTERNS)]
    hits += [f"forbidden loop language: {h}" for h in _scan(text, LOOP_LANGUAGE_PATTERNS)]
    return hits


def _scan_all_strings(obj):
    """Recursively scan keys + string values for any unsafe language."""
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


def _provider_flag_blocks(payload):
    return [f"{flag} must be false" for flag in FORBIDDEN_PROVIDER_FLAGS if payload.get(flag)]


def _stable_hash(value):
    """Deterministic sha256 over canonical JSON of the supplied value."""
    blob = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _quota_summary_blocks(summary):
    """Enforce the embedded/referenced quota policy summary invariants.

    The prompt pack must reference a PASS SCDLLMQuotaRetryPolicy (embedded
    summary preferred): provider/network/credential flags false, exactly one
    canonical generation, and at most one targeted repair.
    """
    blocks = []
    if not summary:
        blocks.append("quota policy summary/reference missing")
        return blocks
    if summary.get("validation_state") != PASS:
        blocks.append("referenced quota policy is not PASS")
    for flag in FORBIDDEN_PROVIDER_FLAGS:
        if summary.get(flag):
            blocks.append(f"quota policy {flag} must be false")
    if summary.get("max_generation_attempts") != 1:
        blocks.append("quota policy max_generation_attempts must be 1")
    repair = summary.get("max_targeted_repair_attempts")
    if not isinstance(repair, int) or isinstance(repair, bool) or repair < 0 or repair > 1:
        blocks.append("quota policy max_targeted_repair_attempts must be 0 or 1")
    return blocks


def validate_prompt_pack_input(payload):
    ok, msg = _schema_ok(payload, "scd_prompt_pack_input.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    blocked += _scan_secrets(payload)
    blocked += _scan_all_strings(payload)
    blocked += _provider_flag_blocks(payload)
    blocked += _ready_flag_blocks(payload)

    # Must reference a PASS quota policy (embedded summary preferred).
    blocked += _quota_summary_blocks(payload.get("quota_policy_summary"))

    # Lineage: missing source/brief hash -> UNKNOWN (fail-closed on lineage).
    if not payload.get("source_packet_hash"):
        unknown.append("source_packet_hash missing; source lineage unknown")
    if not payload.get("brief_hash"):
        unknown.append("brief_hash missing; brief lineage unknown")

    # Optional audience/voice -> REVIEW_REQUIRED when missing but otherwise safe.
    if not payload.get("audience_mode"):
        review.append("audience_mode missing; confirm audience framing")
    if not payload.get("voice_profile"):
        review.append("voice_profile missing; confirm editorial voice")

    return _result(blocked, review, unknown)


def validate_canonical_writer_prompt_pack(payload):
    ok, msg = _schema_ok(payload, "scd_canonical_writer_prompt_pack.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    blocked += _scan_secrets(payload)
    blocked += _scan_all_strings(payload)
    blocked += _provider_flag_blocks(payload)
    blocked += _ready_flag_blocks(payload)

    # Required safety flags.
    for flag in REQUIRED_SAFETY_TRUE_FLAGS:
        if payload.get(flag) is not True:
            blocked.append(f"{flag} must be true")

    # Exactly one canonical draft.
    if payload.get("canonical_draft_count") != 1:
        blocked.append("canonical_draft_count must be 1")

    # Platform variants cannot be requested before the canonical draft PASSes.
    if payload.get("platform_variants_requested"):
        blocked.append("platform_variants_requested must be false in canonical prompt pack")

    # Quota policy enforcement.
    blocked += _quota_summary_blocks(payload.get("quota_policy_summary"))

    # Deterministic identity fields.
    for field in ("prompt_version", "prompt_hash", "brief_hash", "model_config_ref"):
        if not payload.get(field):
            blocked.append(f"{field} missing; prompt pack not deterministic")

    if not payload.get("source_packet_hash"):
        unknown.append("source_packet_hash missing; source lineage unknown")

    return _result(blocked, review, unknown)


def validate_targeted_repair_prompt_pack(payload):
    ok, msg = _schema_ok(payload, "scd_targeted_repair_prompt_pack.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    blocked += _scan_secrets(payload)
    blocked += _scan_all_strings(payload)
    blocked += _provider_flag_blocks(payload)
    blocked += _ready_flag_blocks(payload)

    for flag in REQUIRED_SAFETY_TRUE_FLAGS:
        if payload.get(flag) is not True:
            blocked.append(f"{flag} must be true")

    # Preservation flags all required true.
    for flag in REPAIR_PRESERVE_FLAGS:
        if payload.get(flag) is not True:
            blocked.append(f"{flag} must be true")

    # Patch only the failing section; never full rewrite; never new claims.
    if payload.get("patch_only_failing_section") is not True:
        blocked.append("patch_only_failing_section must be true")
    if payload.get("allow_full_rewrite"):
        blocked.append("allow_full_rewrite must be false")
    if payload.get("allow_new_claims"):
        blocked.append("allow_new_claims must be false")

    # Must reference which validator failures it repairs.
    if not payload.get("validator_failure_refs"):
        blocked.append("validator_failure_refs missing; repair scope unknown")

    # Deterministic identity fields.
    for field in ("prompt_version", "prompt_hash", "model_config_ref"):
        if not payload.get(field):
            blocked.append(f"{field} missing; repair pack not deterministic")

    blocked += _quota_summary_blocks(payload.get("quota_policy_summary"))

    if not payload.get("source_packet_hash"):
        unknown.append("source_packet_hash missing; source lineage unknown")

    return _result(blocked, review, unknown)


def validate_prompt_pack_cache_key(payload):
    ok, msg = _schema_ok(payload, "scd_prompt_pack_cache_key.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    blocked += _scan_secrets(payload)
    blocked += _scan_all_strings(payload)
    blocked += _provider_flag_blocks(payload)

    # Every required cache-key component must be present (0174AY contract).
    for field in REQUIRED_CACHE_KEY_FIELDS:
        if not payload.get(field):
            blocked.append(f"cache key missing required component: {field}")

    # If a composite key + its hash are both present, the hash must be the
    # deterministic sha256 of the canonical components. Recomputed locally; no
    # provider call. Mismatch is a hard block (non-deterministic cache key).
    declared_hash = payload.get("composite_key_hash")
    if declared_hash:
        components = {f: payload.get(f) for f in REQUIRED_CACHE_KEY_FIELDS}
        expected = _stable_hash(components)
        if declared_hash != expected:
            blocked.append("composite_key_hash does not match deterministic recomputation")

    return _result(blocked, review, unknown)


def validate_prompt_pack_validation_report(payload):
    ok, msg = _schema_ok(payload, "scd_prompt_pack_validation_report.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    blocked += _scan_secrets(payload)
    blocked += _scan_all_strings(payload)
    blocked += _provider_flag_blocks(payload)
    blocked += _ready_flag_blocks(payload)

    # A report can only ever assert "ready for future provider-call review".
    if payload.get("operator_review_required") is not True:
        blocked.append("operator_review_required must be true")

    rec = payload.get("final_recommendation")
    if rec not in (PASS, BLOCKED, REVIEW_REQUIRED, UNKNOWN):
        blocked.append(f"invalid final_recommendation: {rec}")

    # Fail-closed roll-up over per-object results.
    per_object = payload.get("per_object_results", []) or []
    results = [r.get("result") for r in per_object]
    direct = [
        payload.get("input_result"),
        payload.get("canonical_result"),
        payload.get("repair_result"),
        payload.get("cache_key_result"),
    ]
    all_results = results + [r for r in direct if r is not None]

    if BLOCKED in all_results:
        expected = BLOCKED
    elif UNKNOWN in all_results:
        expected = UNKNOWN
    elif REVIEW_REQUIRED in all_results:
        expected = REVIEW_REQUIRED
    elif all_results:
        expected = PASS
    else:
        expected = None

    if rec == PASS and expected != PASS:
        blocked.append(f"final PASS contradicts roll-up (expected {expected})")
    if expected == BLOCKED and rec != BLOCKED:
        blocked.append("a sub-result is BLOCKED; final must be BLOCKED")

    if not all_results:
        unknown.append("no sub-results; report lineage unknown")
    if not payload.get("prompt_pack_input_ref"):
        unknown.append("prompt_pack_input_ref missing; report lineage unknown")

    if not blocked:
        if expected == UNKNOWN:
            unknown.append("a sub-result is UNKNOWN; final should be UNKNOWN")
        elif expected == REVIEW_REQUIRED:
            review.append("a sub-result is REVIEW_REQUIRED; final should be REVIEW_REQUIRED")

    return _result(blocked, review, unknown)


# --- Deterministic local compile helpers --------------------------------------------

def compile_prompt_pack_cache_key(components):
    """Build a deterministic cache key dict from supplied components.

    Invents nothing: only the supplied REQUIRED_CACHE_KEY_FIELDS are carried
    forward and hashed. No provider call, no network, no env read.
    """
    selected = {f: components.get(f) for f in REQUIRED_CACHE_KEY_FIELDS}
    composite = "|".join(f"{f}={selected.get(f, '')}" for f in REQUIRED_CACHE_KEY_FIELDS)
    return {
        "composite_key": composite,
        "composite_key_hash": _stable_hash(selected),
    }


def compute_prompt_hash(prompt_pack):
    """Deterministic sha256 over the canonical JSON of a prompt pack body.

    The pack's own prompt_hash field is excluded so the hash is stable across
    recomputation. Invents nothing and performs no provider call.
    """
    body = {k: v for k, v in (prompt_pack or {}).items() if k != "prompt_hash"}
    return _stable_hash(body)


# Registry of prompt-pack validators, in choreography order.
PROMPT_PACK_VALIDATORS = {
    "prompt_pack_input": validate_prompt_pack_input,
    "canonical_writer_prompt_pack": validate_canonical_writer_prompt_pack,
    "targeted_repair_prompt_pack": validate_targeted_repair_prompt_pack,
    "prompt_pack_cache_key": validate_prompt_pack_cache_key,
    "prompt_pack_validation_report": validate_prompt_pack_validation_report,
}
